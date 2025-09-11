from typing import Union, List, Set
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup

class ScrapeResult(BaseModel):
    url: str = Field(description="The URL of the webpage")
    text: str = Field(description="The full text content of the webpage")
    title: str = Field(description="The title of the webpage")
    description: str = Field(description="A short description of the webpage")
    links: list = Field(description="List of links from the page that could be useful as it could be references, citations, or linked sources")

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
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url