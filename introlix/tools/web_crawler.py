import aiohttp
import asyncio
import ssl
from urllib.parse import urlparse, urljoin
from typing import Union, List, Set
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup


class ScrapeResult(BaseModel):
    url: str = Field(description="The URL of the webpage")
    text: str = Field(description="The full text content of the webpage")
    title: str = Field(description="The title of the webpage")
    description: str = Field(description="A short description of the webpage")
    links: list = Field(
        description="List of links from the page that could be useful as it could be references, citations, or linked sources"
    )

ssl_context = ssl.create_default_context()

async def extract_link(html: str, base_url: str) -> tuple[List[str]]:
    """Extract urls from the page"""
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all('a', href=True):
        link = a['href']
        parsed = urlparse(link)
        if bool(parsed.scheme and parsed.netloc):
            links.add(link)
        else:
            link = urljoin(base_url, link)
            links.add(link)

    return links

async def fetch_page(url: str) -> str:
    """Fetch HTML content from a URL"""
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    headers = {
        "User-Agent": "IntrolixCrawler/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return "Error fetching page"


async def web_crawler(url: str) -> Union[List[ScrapeResult], str]:
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

    base_url = urlparse(url).netloc

    html_content = await fetch_page(url)
    if html_content:
        links = await extract_link(html_content, base_url)
        
        for link in links:
            with open("links.txt", 'a') as file:
                file.write(f"{link}\n")

if __name__ == "__main__":
    asyncio.run(web_crawler("https://en.wikipedia.org/wiki/Climate_change"))