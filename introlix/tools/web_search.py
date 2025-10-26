import ssl
import json
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, List
from pydantic import Field, BaseModel
from introlix.config import SEARCHXNG_HOST
from introlix.agents.baseclass import AgentInput, AgentOutput
from introlix.agents.base_agent import Agent

ssl_context = ssl.create_default_context()


class WebpageSnippet(BaseModel):
    url: str = Field(description="The URL of the webpage")
    title: str = Field(description="The title of the webpage")
    description: Optional[str] = Field(description="A short description of the webpage")


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
                    "description": "A short description of the webpage"
                }}
            ]
        }}
}}
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
            return SearchResults(**answer)
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback for malformed output
    return SearchResults(
        results_list=[WebpageSnippet(url="", title="", description="")]
    )


config = AgentInput(
    name="FilterAgent",
    description="Filter For SearXNG results",
    output_type=SearchResults,
    output_parser=filter_agent_output_parser,
)

filter_agent = Agent(
    model="google/gemini-2.5-flash",
    instruction=FILTER_AGENT_INSTRUCTIONS,
    config=config,
    output_model_class=SearchResults,
)


class SearXNGClient:
    def __init__(self, filter_agent: Agent):
        self.filter_agent = filter_agent
        self.host = SEARCHXNG_HOST
        if not self.host.endswith("/search"):
            self.host = (
                f"{self.host}/search"
                if not self.host.endswith("/")
                else f"{self.host}search"
            )

    async def search(
        self, query: str, max_results: int = 5
    ) -> List[WebpageSnippet]:  # Now synchronous
        """
        Perform web search using searXNG with requests
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Authorization": "Bearer 12345678",
        }

        params = {
            "q": query,
            "format": "json",
            "safesearch": "0",  # Optional, but helps some instances
        }
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            params = {
                "q": query,
                "format": "json",
            }

            async with session.get(self.host, params=params) as response:
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
            agent_output = await filter_agent.run(user_prompt)
            if isinstance(agent_output, AgentOutput):
                result = agent_output.result
                if isinstance(result, SearchResults):
                    return result.results_list
            return []
        except Exception as e:
            print("Error filtering results:", str(e))
            return results[:max_results]


if __name__ == "__main__":
    client = SearXNGClient(filter_agent=filter_agent)
    results = asyncio.run(client.search(query="What is coding?"))
    print(results)
