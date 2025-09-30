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
import hashlib
from pinecone import Pinecone
from pydantic import BaseModel, Field
from introlix.config import PINECONE_KEY
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput, Tool
from introlix.tools.web_crawler import web_crawler, ScrapeResult
from introlix.tools.web_search import SearXNGClient, filter_agent, WebpageSnippet
from introlix.utils.text_chunker import TextChunker

class ExplorerAgentOutput(BaseModel):
    topic: str = Field(description="The topic of the research")
    title: list = Field(description="The list title of the web page")
    urls: list = Field(description="The list url of the web page")
    summary: str = Field(description="Summary of all the page according to the topic")
    relevance_score: float = Field(
        description="The score of the sources between 0.0 and 1.0"
    )
    source_type: str = Field(
        description="What is the type of the sources. e.g: academic, news, blog, government, commercial"
    )

INSTRUCTION = """
You are an explorer agent. Your task is to analyze the content from a website and return a summary of the page according to the user query.
The summary should contain the exact answer the user is looking for. The summary should be detailed and should answer the user query.
Make sure to use all the available sites content.

## CRITICAL: Output Format
You MUST respond with ONLY a valid JSON object. Follow these rules STRICTLY:
- NO markdown code blocks like ```json
- NO extra text before or after the JSON
- Just pure JSON

Required JSON structure:
{
    "topic": "The topic of the research",
    "title": "The title of the web page",
    "urls": "The url of the web page",
    "summary": "Detailed summary of the page according to the topic",
    "relevance_score": 0.85,
    "source_type": "academic"
}

## Field Definitions:
- topic (string): The research topic being explored
- title (list): The all webpage title
- urls (list): The all webpage URL  
- summary (string): Detailed summary answering the user's query (at least 2-3 sentences)
- relevance_score (number): Score between 0.0 and 1.0 indicating relevance
- source_type (string): Must be one of: academic, news, blog, government, commercial

## Special Cases:
- If no relevant content is found, return:
  {
    "topic": "provided topic",
    "title": ["No Data Found"],
    "urls": [""],
    "summary": "No Data Found",
    "relevance_score": 0.0,
    "source_type": "commercial"
  }

## REMEMBER: 
- Output ONLY the JSON object
- No additional text, explanations, or formatting
- Start your response with { and end with }
"""

class ExplorerAgent:
    def __init__(self, queries: list, get_answer: bool, get_multiple_answer: bool, max_results = 5):
        """
        Initializes the ExplorerAgent with configuration parameters.
        Args:
            queries (str): The search query or topic to explore.
            get_answer (bool): Whether to generate a final answer summary.
            get_multiple_answer (bool): Whether to return multiple answers based on different source or return one answer by summarizing the sources.
        """
        self.INSTRUCTION = INSTRUCTION
        self.queries = queries
        self.get_answer = get_answer
        self.get_multiple_answer = get_multiple_answer
        self.max_results = max_results

        self.pc = Pinecone(api_key=PINECONE_KEY)
        self.index_name = "explored-data-index"

        self.explorer_config = AgentInput(
            name="CrawlerAgent",
            description="Crawls Web pages",
            output_type=ExplorerAgentOutput,
        )

        self.explorer_agent = Agent(
            model="qwen/qwen3-235b-a22b:free",
            instruction=self.INSTRUCTION,
            output_model_class=ExplorerAgentOutput,
            config=self.explorer_config
        )

        self.search_tool = SearXNGClient(filter_agent=filter_agent)

        self._setup_index()
    
    def _setup_index(self):
        """Create Pinecone index if it doesn't exist"""
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map":{
                        "text": "chunk_text"
                    }
                }
            )
        
        self.index = self.pc.Index(self.index_name)
    
    async def run(self, retry: int = 0, max_retries: int = 5):
        if retry > max_retries:
            return ExplorerAgentOutput(
                topic="",
                title="",
                url="",
                summary="",
                relevance_score=0,
                source_type="",
                credibility_indicators=""
            )
        # checking if user asked for answer
        if self.get_answer or self.get_multiple_answer:
            results = []
            for query in self.queries:
                results_ = self.index.search(
                    namespace="explored-data",
                    query={
                        "top_k": 3,
                        "inputs": {
                            "text": query
                        }
                    }
                )
                for hit in results_['result']['hits']:
                    data = {
                            "_id" : hit['_id'],
                            "title": hit['fields']['title'],
                            "description": hit['fields']['description'],
                            "url": hit['fields']['url'],
                            "chunk_id": hit['fields']['chunk_id'],
                            "chunk_text": hit['fields']['chunk_text'],
                            "score": hit['_score']
                        }
                    results.append(data)
            if self.get_answer and not self.get_multiple_answer:
                user_prompt = f"""
                The user query:
                {query}
                The result to analyze:
                {results}
                """
                answer = await self.explorer_agent.run(user_prompt)

                if answer.result.summary == "No Data Found":
                    print("No data found")
                    await self.get_and_save_data()
                    await self.run(retry+1)

                return answer.result

            if self.get_answer and self.get_multiple_answer:
                answers = []
                for result in results:
                    user_prompt = f"""
                    The user query:
                    {query}
                    The result to analyze:
                    {result}
                    """
                    answer = await self.explorer_agent.run(user_prompt)
                    if not answer.result.summary == "No Data Found":
                        answers.append(answer.result)

                if len(answers) == 0:
                    await self.run(retry+1)
                    await self.get_and_save_data()
                return answers
        else:
            await self.get_and_save_data()

        # IF needed then run the verifier agent to verify the answer
        # If needed then return the one single answer or multiple answers based on the get_multiple_answer flag
        # If not answer needed then return the crawled result with source details

    async def get_and_save_data(self):
        records = []
        BATCH_SIZE = 96

        for query in self.queries:
            search_results = await self.search_tool.search(query=query, max_results=self.max_results)

            for result in search_results: # TODO: Run in parallel
                url = result.url
                if self.is_url_exists(url):
                    print("Url Already Exists")
                    continue

                crawled_result = await web_crawler(url=url) # TODO: Run in parallel

                # dividing the crawled_result into chunks
                chunker = TextChunker(chunk_size=400, overlap=50)
                chunks = chunker.chunk_text(crawled_result.text if isinstance(crawled_result, ScrapeResult) else crawled_result)

                # Save Chunks To Vector DB
                chunks = [
                    {
                        "_id" : f"{hashlib.md5(url.encode()).hexdigest()}_chunk_{chunk['chunk_id']}",
                        "title": crawled_result.title,
                        "description": crawled_result.description,
                        "url": crawled_result.url,
                        "chunk_id": chunk['chunk_id'],
                        "chunk_text": chunk['text']
                    }
                    for chunk in chunks
                ]
                records.extend(chunks)

        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i:i + BATCH_SIZE]
            self.index.upsert_records("explored-data", batch)
    
    def is_url_exists(self, url: str) -> bool:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        result = self.index.fetch(ids=[f"{url_hash}_chunk_0"])
        return len(result.vectors) > 0
            
if __name__ == "__main__":
    explorer_agent = ExplorerAgent(queries=["What was the first computer?"], get_answer=True, get_multiple_answer=False, max_results=5)
    result = asyncio.run(explorer_agent.run())
    print(result)