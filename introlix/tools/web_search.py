import ssl
import json
import aiohttp
import asyncio
import time
import logging
from datetime import datetime
from typing import Optional, List
from pydantic import Field, BaseModel, ValidationError
from introlix.config import SEARCHXNG_HOST
from introlix.agents.baseclass import AgentInput, AgentOutput
from introlix.agents.base_agent import Agent


logger = logging.getLogger(__name__)

ssl_context = ssl.create_default_context()


class WebpageSnippet(BaseModel):
    url: str = Field(description="The URL of the webpage")
    title: str = Field(description="The title of the webpage")
    description: Optional[str] = Field(default=None, description="A short description of the webpage")


class SearchResults(BaseModel):
    results_list: List[WebpageSnippet]


FILTER_AGENT_INSTRUCTIONS = f"""
You are a search result filter. Today's date is {datetime.now().strftime("%Y-%m-%d")}.
Your task is to analyze a list of SearXNG search results and determine which ones are relevant
to the original query based on the link, title and snippet. Return only the relevant results in the specified format. 

- Remove any results that refer to entities that have similar names to the queried entity, but are not the same.
- E.g. if the query asks about a company "Amce Inc, acme.com", remove results with "acmesolutions.com" or "acme.net" in the link.

Note: All the results will be for a research agent. So, make sure to keep search results which are useful for research.

## Required Output Structure
Respond with a JSON object containing:
{{
    "type": "final",
    "answer": JSON object with the following structure:
        {{
            "results_list": [
                {{
                    "url": "The URL of the webpage",
                    "title": "The title of the webpage",
                    "description": "A short description of the webpage (required field, use empty string if no description available)"
                }}
            ]
        }}
}}

IMPORTANT: Every result in results_list MUST include all three fields: "url", "title", and "description". 
If a description is not available, use an empty string "" for the description field.
"""


def filter_agent_output_parser(raw_output: str) -> SearchResults:
    """Parse filter agent output and validate structure."""
    try:
        parsed_output = json.loads(raw_output)
        if parsed_output.get("type") == "final":
            if "answer" in parsed_output:
                answer = parsed_output["answer"]
            else:
                answer = parsed_output
            if isinstance(answer, str):
                answer = json.loads(answer)
            
            # Ensure all results have required fields, set defaults for missing optional fields
            if "results_list" in answer:
                normalized_results = []
                for result in answer["results_list"]:
                    normalized_result = {
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "description": result.get("description") if "description" in result else None
                    }
                    normalized_results.append(normalized_result)
                answer["results_list"] = normalized_results
            
            return SearchResults(**answer)
    except (json.JSONDecodeError, ValueError, ValidationError) as e:
        logger.error(f"Error parsing filter agent output: {e}")
        pass

    # Fallback for malformed output
    return SearchResults(
        results_list=[WebpageSnippet(url="", title="", description=None)]
    )


class SearXNGClient:
    def __init__(self, model: str, min_delay_between_requests: float = 5.0):
        self.host = SEARCHXNG_HOST
        self.model = model
        
        # CRITICAL: Add throttling
        self.min_delay = min_delay_between_requests  # Minimum seconds between requests
        self.last_request_time = 0
        self._lock = asyncio.Lock()  # Prevent concurrent requests

        if not self.host.endswith("/search"):
            self.host = (
                f"{self.host}/search"
                if not self.host.endswith("/")
                else f"{self.host}search"
            )

        self.config = AgentInput(
            name="FilterAgent",
            description="Filter For SearXNG results",
            output_type=SearchResults,
            output_parser=filter_agent_output_parser,
        )

        self.filter_agent = Agent(
            model=model,
            instruction=FILTER_AGENT_INSTRUCTIONS,
            config=self.config,
            output_model_class=SearchResults,
        )

    async def _throttled_request(self):
        """Ensure minimum delay between requests"""
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_delay:
                wait_time = self.min_delay - time_since_last
                logger.info(f"Throttling: waiting {wait_time:.2f}s before next search...")
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()

    async def search(
        self, query: str, max_results: int = 5, max_retries: int = 3
    ) -> List[WebpageSnippet]:
        """
        Perform web search using searXNG with throttling and retries
        """
        
        for attempt in range(max_retries):
            try:
                # Wait if needed
                await self._throttled_request()
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Authorization": "Bearer 12345678",
                }

                params = {
                    "q": query,
                    "format": "json",
                    "safesearch": "0",
                }
                
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    async with session.get(self.host, params=params, headers=headers) as response:
                        response.raise_for_status()
                        results = await response.json()

                results_list = [
                    WebpageSnippet(
                        url=result.get("url", ""),
                        title=result.get("title", ""),
                        description=result.get("content", ""),
                    )
                    for result in results.get("results", [])
                ]

                return (
                    await self._filter_results(results_list, query, max_results)
                    if results_list
                    else []
                )
                
            except asyncio.TimeoutError:
                logger.info(f"Timeout on attempt {attempt + 1}/{max_retries} for query: {query}")
                if attempt < max_retries - 1:
                    backoff_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    logger.info(f"Backing off for {backoff_time}s...")
                    await asyncio.sleep(backoff_time)
                else:
                    logger.info(f"Failed after {max_retries} attempts")
                    return []
                    
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                else:
                    return []

    async def _filter_results(
        self, results: List[WebpageSnippet], query: str, max_results: int = 5
    ) -> List[WebpageSnippet]:
        serialized_results = [
            result.model_dump() if isinstance(result, WebpageSnippet) else result
            for result in results
        ]    

        user_prompt = f"""
        Original search query: {query}
        
        Search results to analyze:
        {json.dumps(serialized_results, indent=2)}
        
        Return {max_results} search results or less.
        """

        try:
            agent_output = await self.filter_agent.run(user_prompt)
            if isinstance(agent_output, AgentOutput):
                result = agent_output.result
                if isinstance(result, SearchResults):
                    return result.results_list
            return []
        except Exception as e:
            logger.error("Error filtering results:", str(e))
            return results[:max_results]


if __name__ == "__main__":
    client = SearXNGClient(model="gemini-2.5-flash", min_delay_between_requests=6.0)
    results = asyncio.run(client.search(query="What is coding?"))
    print(results)