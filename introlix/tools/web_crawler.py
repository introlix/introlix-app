"""
Web Crawler Tool Module

This module provides asynchronous web scraping functionality for extracting content
from web pages and PDF documents. It uses trafilatura for main content extraction
and pdfplumber for PDF processing.

Key Features:
-------------
- Asynchronous HTTP requests with aiohttp
- HTML content extraction with trafilatura
- PDF text extraction with pdfplumber
- Automatic content type detection
- Link extraction and filtering (optional)
- Robust error handling
- SSL/TLS support

Supported Content Types:
-----------------------
- HTML web pages
- PDF documents
"""

import aiohttp
import asyncio
import ssl
import json
import re
import trafilatura
from urllib.parse import urlparse, urljoin
from typing import Union, List, Set
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
import pdfplumber
from io import BytesIO

class ScrapeResult(BaseModel):
    """
    Structured result from web scraping operation.

    Attributes:
        url (str): The URL of the scraped webpage or PDF.
        text (str): The full extracted text content.
        title (str): The title of the webpage or PDF.
        description (str): A short description or summary of the content.
    """
    url: str = Field(description="The URL of the webpage")
    text: str = Field(description="The full text content of the webpage")
    title: str = Field(description="The title of the webpage")
    description: str = Field(description="A short description of the webpage")

ssl_context = ssl.create_default_context()

async def extract_links(html: str, base_url: str) -> List[dict]:
    """
    Extract and filter useful links from an HTML page.

    This function parses HTML content and extracts meaningful links while filtering out
    common non-content links (login, signup, media files, etc.).

    Args:
        html (str): The HTML content to parse.
        base_url (str): The base URL for resolving relative links.

    Returns:
        List[dict]: List of link dictionaries containing:
            - url (str): The absolute URL
            - anchor (str): The link text

    Note:
        Filters out links to: login/signup pages, categories, tags, media files,
        and links with only single-word anchor text.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)

        # Normalize link
        parsed = urlparse(href)
        if parsed.netloc:  # absolute
            if not parsed.scheme:
                href = f"{urlparse(base_url).scheme}:{href}"
        else:  # relative
            href = urljoin(base_url, href)

        # FILTERING RULES
        if any(
            re.search(p, href, re.IGNORECASE)
            for p in [r"#", r"login", r"signup", r"category", r"tag",
                      r"about", r"contact", r"privacy", r"terms",
                      r"\.(jpg|png|gif|svg|css|js|mp4|pdf)$"]
        ):
            continue

        # Only keep meaningful links
        if text and len(text.split()) > 1:
            links.append({"url": href, "anchor": text})

    return links

async def fetch_page(url: str) -> tuple[str, bool]:
    """
    Fetch content from a URL (HTML or PDF).

    This function makes an asynchronous HTTP GET request with browser-like headers
    to fetch page content. It automatically detects PDF content.

    Args:
        url (str): The URL to fetch.

    Returns:
        tuple[str, bool]: A tuple containing:
            - Content (str or bytes): HTML text or PDF bytes
            - is_pdf (bool): True if content is PDF, False otherwise

    Note:
        - Uses 5-second timeout
        - Returns empty string and False on errors
        - Includes realistic browser headers to avoid blocking
    """
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "").lower()
                    is_pdf = "application/pdf" in content_type
                    if is_pdf:
                        return await response.read(), is_pdf
                    return await response.text(), is_pdf
                else:
                    print(f"HTTP {response.status} for {url}")
                    return "", False
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return "", False

async def extract_pdf_text(pdf_content: bytes) -> tuple[str, str, str]:
    """
    Extract text, title, and description from a PDF document.

    This function processes PDF bytes and extracts:
    - Full text from all pages
    - Title from metadata or first page
    - Description from first few lines

    Args:
        pdf_content (bytes): The PDF file content as bytes.

    Returns:
        tuple[str, str, str]: A tuple containing:
            - text (str): Full extracted text from all pages
            - title (str): Document title
            - description (str): First 200 chars from opening lines

    Note:
        Returns empty strings on extraction errors.
    """
    try:
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            # Extract text from all pages
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            # Extract title from metadata or first page
            title = pdf.metadata.get("Title", "") or ""
            if not title and pdf.pages:
                first_page_text = pdf.pages[0].extract_text() or ""
                # Use first non-empty line as title (common in arXiv PDFs)
                title_lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
                title = title_lines[0] if title_lines else ""
            # Use first few lines as description (if available)
            description_lines = [line.strip() for line in text.split("\n")[:5] if line.strip()]
            description = " ".join(description_lines[:3])[:200]  # Limit to 200 chars
        return text, title, description
    except Exception as e:
        print(f"Error extracting PDF content: {str(e)}")
        return "", "", ""
    
async def web_crawler(url: str) -> Union[ScrapeResult, str]:
    """
    Crawls the pages to gets important details and content from the page.

    Args:
        url: Url to scrape

    Returns:
        List of ScrapeResult:
            - url: The URL of the web page
            - title: The title of the web page
            - description: The description of the web page
            - text: The text content of the web page
            - links: List of links from the page
    """
    if not url:
        return "No URL to scrape"

    # Ensure URL has a protocol
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    html_content, is_pdf = await fetch_page(url)
    if not html_content:
         return "Error while crawling website"
    
    # For pdf
    if is_pdf:
        # Handle PDF content
        text, title, description = await extract_pdf_text(html_content)
        # PDFs typically don't have extractable links in this context
        links = []
    else:
        # For HTML web pages
        # Link extraction is currently disabled
        # links = await extract_links(html_content, url)

        # Extract main content using trafilatura
        title, description, text = "", "", ""
 
        data = trafilatura.extract(html_content, url=url, output_format="json", with_metadata=True)
        if data:
            parsed = json.loads(data)
            title = parsed.get("title") or ""
            description = parsed.get("description") or ""
            text = parsed.get("text") or ""
    
    return ScrapeResult(
        url=url,
        text=text,
        title=title,
        description=description,
        # links=links[:50]
    )

if __name__ == "__main__":
    result = asyncio.run(web_crawler("https://www.autodesk.com/products/fusion-360/blog/first-computer-around-century-ago/"))
    print(result)