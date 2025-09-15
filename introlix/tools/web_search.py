import requests
from typing import Optional, List
from pydantic import Field, BaseModel
from introlix.config import SEARCHXNG_HOST
from introlix.agents.baseclass import BaseAgent

class WebpageSnippet(BaseModel):
    url: str = Field(description="The URL of the webpage")
    title: str = Field(description="The title of the webpage")
    description: Optional[str] = Field(description="A short description of the webpage")

class SearXNGClient:
    def __init__(self, filter_agent: BaseAgent):
        self.filter_agent = filter_agent
        self.host = SEARCHXNG_HOST
        if not self.host.endswith("/search"):
            self.host = (
                f"{self.host}/search"
                if not self.host.endswith("/")
                else f"{self.host}search"
            )

    def search(self, query: str) -> List[WebpageSnippet]:  # Now synchronous
        """
        Perform web search using searXNG with requests
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",  # Mimics browser
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "max-age=0",
        }

        params = {
            "q": query,
            "format": "json",
            "safesearch": "0",  # Optional, but helps some instances
        }

        try:
            response = requests.get(self.host, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            results = response.json()

            results_list = [
                WebpageSnippet(
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    description=result.get("content", ""),
                )
                for result in results.get("results", [])
            ]
            return results_list if results_list else []
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"429 detected: {e.response.text}")  # Check for Cloudflare clues in text
            raise

if __name__ == "__main__":
    client = SearXNGClient(filter_agent=BaseAgent)
    results = client.search(query="What is coding?")  # No asyncio needed
    print(results)