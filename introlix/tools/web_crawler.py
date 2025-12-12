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
- Robust error handling
- SSL/TLS support

Supported Content Types:
-----------------------
- HTML web pages
- PDF documents
"""

import aiohttp
import random
import asyncio
import ssl
import json
import re
import trafilatura
from urllib.parse import urlparse, urljoin
from typing import Union, List, Set
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pdfplumber
from io import BytesIO

# Multiple realistic user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

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

async def fetch_page_aiohttp(url: str) -> tuple[str, bool, int]:
    """
    Fetch content using aiohttp (fast, no JS execution).

    Args:
        url (str): The URL to fetch.
    
    Returns:
        tuple: (content, is_pdf, status_code)
    """
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        try:
            async with session.get(url, timeout=10) as response:
                status = response.status
                if status == 200:
                    content_type = response.headers.get("Content-Type", "").lower()
                    is_pdf = "application/pdf" in content_type
                    if is_pdf:
                        return await response.read(), is_pdf, status
                    return await response.text(), is_pdf, status
                return "", False, status
        except Exception as e:
            print(f"Aiohttp error for {url}: {str(e)}")
            return "", False, 0

async def inject_stealth_scripts(page):
    """
    Inject JavaScript to mask automation and appear as a real browser.
    """
    await page.add_init_script("""
        // Overwrite navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
        
        // Mock chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Mock battery API
        navigator.getBattery = () => Promise.resolve({
            charging: true,
            chargingTime: 0,
            dischargingTime: Infinity,
            level: 1.0,
        });
        
        // Mock connection API
        Object.defineProperty(navigator, 'connection', {
            get: () => ({
                effectiveType: '4g',
                downlink: 10,
                rtt: 50,
            }),
        });
    """)


async def fetch_page_playwright(url: str) -> tuple[str, bool]:
    """
    Fetch content using Playwright (handles JS, slower but more reliable).
    
    Returns:
        tuple: (content, is_pdf)
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--hide-scrollbars',
                    '--mute-audio',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                ]
            )
            # Create context with realistic settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(USER_AGENTS),
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                color_scheme='light',
                java_script_enabled=True,
                accept_downloads=False,
                has_touch=False,
                is_mobile=False,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                }
            )
            
            page = await context.new_page()
            
            # Inject stealth scripts
            await inject_stealth_scripts(page)
            
            # Random mouse movements
            await page.mouse.move(random.randint(50, 150), random.randint(50, 150))
            await page.mouse.move(random.randint(150, 250), random.randint(150, 250))
            
            # Try different wait strategies with ONE navigation
            response = None
            for wait_strategy in ['domcontentloaded', 'load']:
                try:
                    response = await page.goto(url, wait_until=wait_strategy, timeout=10000)
                    break  # Success, exit loop
                except Exception as e:
                    print(f"Failed with {wait_strategy}: {e}")
                    continue

            # If navigation failed completely
            if not response:
                raise Exception("Failed to load page")
            
            # Check if it's a PDF
            if response and 'application/pdf' in response.headers.get('content-type', '').lower():
                pdf_content = await response.body()
                await browser.close()
                return pdf_content, True
            
            # Scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            
            # Scroll back up
            await page.evaluate("window.scrollTo(0, 0);")
            
            # Get the fully rendered HTML
            html_content = await page.content()
            
            await browser.close()
            return html_content, False
    except Exception as e:
        print(f"Playwright error for {url}: {str(e)}")
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

    html_content, is_pdf, _ = await fetch_page_aiohttp(url)

    # Check for common JS framework indicators in HTML
    js_indicators = [
        'react', 'vue', 'angular', 'next.js', 
        '__NEXT_DATA__', 'ng-app', 'v-cloak',
        'data-reactroot', 'data-react-helmet'
    ]

    html_lower = html_content.lower()
    if any(indicator in html_lower for indicator in js_indicators):
        html_content, is_pdf = await fetch_page_playwright(url)
    if not html_content:
        html_content, is_pdf = await fetch_page_playwright(url)
        if not html_content:
            return f"Failed to fetch content from {url}"
    
    # For pdf
    if is_pdf:
        # Handle PDF content
        text, title, description = await extract_pdf_text(html_content)
    else:
        # For HTML web pages

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
    )

if __name__ == "__main__":
    result = asyncio.run(web_crawler("https://www.reddit.com/r/Nepal/comments/1nt9bc9/my_thoughts_directly_elected_pm_is_not_a_good/"))
    print(result)