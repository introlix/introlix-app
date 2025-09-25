"""
The Web Search Agent retrieves relevant information from the internet
using SearXNG and web crawling. It operates on multiple topics in parallel
and generates structured summaries for efficient downstream processing.

Input Format:
==============================================================================
RESEARCH_PLAN: <structured plan from Planner Agent with topics and keywords>
SEARCH_CONSTRAINTS: <optional limitations on sources, date ranges, languages>
==============================================================================

Output Format:
==============================================================================
SEARCH_RESULTS: [
    {
        "topic": "<research topic>",
        "sources_found": <number>,
        "summaries": [
            {
                "title": "<article title>",
                "url": "<source URL>",
                "summary": "<1-3 sentence summary>",
                "relevance_score": <0.0-1.0>,
                "publication_date": "<date>",
                "source_type": "<academic | news | blog | government | commercial>",
                "author": "<author if available>",
                "credibility_indicators": ["<peer_reviewed | established_publication | primary_source>"]
            }
        ]
    }
]
===========================================================================

Notes:
------
- Implement relevance_score algorithm based on keyword matching and content quality
- Track credibility_indicators to assist Verifier Agent
- Include source_type to help categorize information types
- Limit summaries to essential information to reduce processing overhead
- Flag potential academic sources for priority verification
"""

import asyncio
import json
from pydantic import BaseModel, Field
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput, Tool
from introlix.tools.web_crawler import web_crawler, ScrapeResult
from introlix.tools.web_search import SearXNGClient, filter_agent, WebpageSnippet
from introlix.utils.text_chunker import TextChunker


class ExplorerAgentOutput(BaseModel):
    topic: str = Field(description="The topic of the research")
    title: str = Field(description="The title of the web page")
    url: str = Field(description="The url of the web page")
    summary: str = Field(description="Summary of the page according to the topic")
    relevance_score: int = Field(
        description="The score of the source between 0.0 and 1.0"
    )
    source_type: str = Field(
        description="What is the type of the source. e.g: academic, news, blog, government, commercial"
    )
    credibility_indicators: str = Field(
        description="<peer_reviewed | established_publication | primary_source>"
    )

INSTRUCTION = f"""
You are a explorer agent. Your task it to analyze the content from a website. And return the summary of the page according to the user query.
The summary should contain exact answer what user are looking. The summary should not be very small and it should be very detailed and should answer user query.

## Required Output Structure
Respond with a JSON object containing:
{{
    "type": "final",
    "answer": JSON object with the following structure:
    {{
        "topic": "The topic of the research",
        "title": "The title of the web page",
        "url": "The url of the web page",
        "summary": "Summary of the page according to the topic",
        "relevance_score": "The score of the source between 0.0 and 1.0",
        "source_type": "What is the type of the source. e.g: academic, news, blog, government, commercial",
        "credibility_indicators": "<peer_reviewed | established_publication | primary_source>",
    }}
}}
"""

class ExplorerAgent:
    def __init__(self, queries: list, get_answer: bool, get_multiple_answer: bool, max_results = 5):
        """
        Initializes the ExplorerAgent with configuration parameters.
        Args:
            query (str): The search query or topic to explore.
            get_answer (bool): Whether to generate a final answer summary.
            get_multiple_answer (bool): Whether to return multiple answers based on different source or return one answer by summarizing the sources.
        """
        self.INSTRUCTION = INSTRUCTION
        self.queries = queries
        self.get_answer = get_answer
        self.self.get_multiple_answer = get_multiple_answer
        self.max_results = max_results

        self.explorer_config = AgentInput(
            name="CrawlerAgent",
            description="Crawls Web pages",
            output_type=ExplorerAgentOutput,
        )

        self.explorer_agent = Agent(
            model="qwen/qwen3-30b-a3b:free",
            instruction=self.INSTRUCTION,
            output_model_class=ExplorerAgentOutput,
            config=self.explorer_config
        )

        self.search_tool = SearXNGClient(filter_agent=filter_agent)

    async def run(self):
        for query in self.queries:
            search_results = await self.search_tool.search(query=query, max_results=self.max_results)

            for result in search_results: # TODO: Run in parallel
                url = result.url
                crawled_result = await web_crawler(url=url) # TODO: Run in parallel

                # dividing the crawled_result into chunks
                chunker = TextChunker(chunk_size=2000, overlap=50)
                chunks = chunker.chunk_text(crawled_result.text if isinstance(crawled_result, ScrapeResult) else crawled_result)

                # Save Chunks To Vector DB
                # If want one single answer by summarizing the sources then for each chunk run the agent to get answer and then summarize the answers to get one single answer.
                # If want multiple answers based on different source then for each chunk run the agent to get answer and return all the answers.

                # Vector DB search to get relevant chunks based on the query
                # Answer forming based on the relevant chunks
                # IF needed then run the verifier agent to verify the answer
                # If needed then return the one single answer or multiple answers based on the get_multiple_answer flag
                # If not answer needed then return the crawled result with source details

                print(f"Total Chunks: {len(chunks)}")
                user_prompt = f"""
                Original search query: {query}
            
                Search results to analyze:
                {crawled_result.model_dump() if isinstance(result, ScrapeResult) else crawled_result}
            
                Return {self.max_results} search results or less.
                """
                # agent_output = await self.explorer_agent.run(user_prompt)
                # return agent_output
            
            
if __name__ == "__main__":
    explorer_agent = ExplorerAgent(query="What is the fastest animal", max_results=1)
    result = asyncio.run(explorer_agent.run())
    print(result)