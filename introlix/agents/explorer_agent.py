"""
The Web Search Agent retrieves relevant information from the internet
using SearXNG and web crawling. It operates on multiple topics in parallel
and generates structured summaries for efficient downstream processing.
"""

import asyncio
import hashlib
from datetime import datetime
from pinecone import Pinecone
from pydantic import BaseModel, Field
from introlix.config import PINECONE_KEY
from introlix.agents.base_agent import Agent
from introlix.agents.baseclass import AgentInput, Tool
from introlix.tools.web_crawler import web_crawler, ScrapeResult
from introlix.tools.web_search import SearXNGClient
from introlix.utils.text_chunker import TextChunker
from sentence_transformers import SentenceTransformer

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

INSTRUCTION = f"""
You are an explorer agent. Your task is to analyze the content from a website and return a summary of the page according to the user query.
The summary should contain the exact answer the user is looking for. The summary should be detailed and should answer the user query.
Make sure to use all the available sites content.

Today's date is {datetime.now().strftime("%Y-%m-%d")}

## CRITICAL: Output Format
You MUST respond with ONLY a valid JSON object. Follow these rules STRICTLY:
- NO markdown code blocks like ```json
- NO extra text before or after the JSON
- Just pure JSON don't add any token like <｜begin▁of▁sentence｜>.

Required JSON structure:
{{
    "topic": "The topic of the research",
    "title": "The title of the web page",
    "urls": "The url of the web page",
    "summary": "Detailed summary of the page according to the topic",
    "relevance_score": 0.85,
    "source_type": "academic"
}}

## Field Definitions:
- topic (string): The research topic being explored
- title (list): The all webpage title
- urls (list): The all webpage URL  
- summary (string): Detailed summary answering the user's query (at least 2-3 sentences)
- relevance_score (number): Score between 0.0 and 1.0 indicating relevance
- source_type (string): Must be one of: academic, news, blog, government, commercial

## Special Cases:
- If no relevant content is found, return:
  {{
    "topic": "provided topic",
    "title": ["No Data Found"],
    "urls": [""],
    "summary": "No Data Found",
    "relevance_score": 0.0,
    "source_type": ""
  }}

## REMEMBER: 
- Output ONLY the JSON object
- No additional text, explanations, or formatting
- Start your response with {{ and end with }}

Note: Make sure the result is always upto date. If result is not up to date then again result same data when returning no relevent contnet is found in same json format.
Note: If the title of the website does not match or is not good then don't get data from that website and return again same no relevant json data.
"""

class ExplorerAgent:
    def __init__(self, queries: list, unique_id: str, get_answer: bool, get_multiple_answer: bool, max_results = 5, model="google/gemini-2.5-flash"):
        """
        Initializes the ExplorerAgent with configuration parameters.
        Args:
            queries (str): The search query or topic to explore.
            unique_id (str): Unique id (Workspace ID) to isolate data per workspace.
            get_answer (bool): Whether to generate a final answer summary.
            get_multiple_answer (bool): Whether to return multiple answers based on different source or return one answer by summarizing the sources.
        """
        self.INSTRUCTION = INSTRUCTION
        self.queries = queries
        self.unique_id = unique_id
        self.get_answer = get_answer
        self.get_multiple_answer = get_multiple_answer
        self.max_results = max_results
        self.model = model

        self.pc = Pinecone(api_key=PINECONE_KEY)
        self.index_name = "explored-data-index"

        self.embedding_model = SentenceTransformer("google/embeddinggemma-300m")

        self.explorer_config = AgentInput(
            name="CrawlerAgent",
            description="Crawls Web pages",
            output_type=ExplorerAgentOutput,
        )

        self.explorer_agent = Agent(
            model=model,
            instruction=self.INSTRUCTION,
            output_model_class=ExplorerAgentOutput,
            config=self.explorer_config
        )

        self.search_tool = SearXNGClient(model=model)

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
    
    async def run(self, retry: int = 0, max_retries: int = 5, queries_to_process: list = None):
        """
        Fixed version that handles each query independently
        
        Args:
            retry: Current retry count
            max_retries: Maximum number of retries
            queries_to_process: Specific queries to process (used in retries)
        """
        if retry > max_retries:
            return ExplorerAgentOutput(
                topic="",
                title=[],
                urls=[],
                summary="",
                relevance_score=0,
                source_type="",
            )
        
        # Use provided queries or default to all queries
        queries_to_search = queries_to_process if queries_to_process else self.queries
        
        # checking if user asked for answer
        if self.get_answer or self.get_multiple_answer:
            all_answers = []
            queries_needing_data = []  # Track which queries need new data
            
            # Process each query separately
            for query in queries_to_search:
                results = []
                try:
                    # ADDED: Filter by unique_id
                    results_ = self.index.search(
                        namespace="Search",
                        query={
                            "top_k": 3,
                            "inputs": {
                                "text": query
                            },
                            "filter": {
                                "unique_id": self.unique_id
                            }
                        }
                    )
                    
                    # Safely extract hits from search results
                    hits = results_.get('result', {}).get('hits', [])
                    for hit in hits:
                        try:
                            data = {
                                "_id": hit.get('_id', ''),
                                "title": hit.get('fields', {}).get('title', ''),
                                "description": hit.get('fields', {}).get('description', ''),
                                "url": hit.get('fields', {}).get('url', ''),
                                "chunk_id": hit.get('fields', {}).get('chunk_id', ''),
                                "chunk_text": hit.get('fields', {}).get('chunk_text', ''),
                                "score": hit.get('_score', 0.0)
                            }
                            results.append(data)
                        except Exception as e:
                            print(f"Error parsing search hit: {e}")
                            continue
                except Exception as e:
                    print(f"Error searching Pinecone for query '{query}': {e}")
                    # If search fails, mark query as needing data
                    queries_needing_data.append(query)
                    continue
                
                # Check if we found any results for this query
                if not results:
                    queries_needing_data.append(query)
                    continue
                
                if self.get_answer and not self.get_multiple_answer:
                    # Get single best answer for this query
                    user_prompt = f"""
                    The user query:
                    {query}
                    The result to analyze:
                    {results}
                    """
                    answer = await self.explorer_agent.run(user_prompt)
                    
                    if answer.result.summary != "No Data Found":
                        all_answers.append(answer.result)
                    else:
                        # Even though we had results, the LLM said "No Data Found"
                        queries_needing_data.append(query)
                
                elif self.get_answer and self.get_multiple_answer:
                    # Get multiple answers for this query
                    query_had_valid_answer = False
                    for result in results:
                        user_prompt = f"""
                        The user query:
                        {query}
                        The result to analyze:
                        {result}
                        """
                        answer = await self.explorer_agent.run(user_prompt)
                        if answer.result.summary != "No Data Found":
                            all_answers.append(answer.result)
                            query_had_valid_answer = True
                    
                    # If none of the results produced valid answers, mark for retry
                    if not query_had_valid_answer:
                        queries_needing_data.append(query)
            
            # If some queries need new data, fetch it and retry ONLY those queries
            if queries_needing_data:
                await self.get_and_save_data(queries_needing_data)
                
                # Wait a bit for data to be indexed
                await asyncio.sleep(2)
                
                # Recursively process only the queries that needed data
                retry_results = await self.run(
                    retry=retry + 1, 
                    max_retries=max_retries,
                    queries_to_process=queries_needing_data
                )
                
                # Combine results from successful queries and retried queries
                # Only add valid results (not error messages)
                if isinstance(retry_results, list):
                    # Filter out error results from the list
                    valid_results = [
                        r for r in retry_results 
                        if r.summary and r.summary != "No valid data found after retries" and r.summary != "No Data Found"
                    ]
                    all_answers.extend(valid_results)
                elif retry_results and retry_results.summary and retry_results.summary != "No valid data found after retries" and retry_results.summary != "No Data Found":
                    # Only add if it's a valid result (not an error)
                    all_answers.append(retry_results)
            
            # Return results based on mode
            if not all_answers:
                return ExplorerAgentOutput(
                    topic="",
                    title=[],
                    urls=[],
                    summary="No valid data found after retries",
                    relevance_score=0,
                    source_type="",
                )
            
            return all_answers
        else:
            # If not asking for answers, just crawl and save data
            await self.get_and_save_data(queries_to_search)
            return None
        
    async def get_and_save_data(self, queries: list = None):
        """
        Getting data from internet and saving it
        
        Args:
            queries: List of queries to process. If None, uses self.queries
        """
        records = []
        BATCH_SIZE = 96
        QUERY_BATCH_SIZE = 5  # Process 5 queries at a time
        BATCH_DELAY = 2  # Wait 2 seconds between batches
        queries_to_process = queries if queries else self.queries

        async def process_query(query: str):
            search_results = await self.search_tool.search(query=query, max_results=self.max_results)

            # Crawl URLs concurrently for this query
            crawl_tasks = []
            for result in search_results:
                url = result.url
                if self.is_url_exists(url):
                    continue
                crawl_tasks.append(self._crawl_and_chunk(query, url))

            query_records = await asyncio.gather(*crawl_tasks, return_exceptions=True)

            # Flatten and filter errors
            flat_records = []
            for rec_list in query_records:
                if isinstance(rec_list, list):
                    flat_records.extend(rec_list)
                elif isinstance(rec_list, Exception):
                    print(f"Error during crawling: {rec_list}")

            return flat_records

        # Process queries in batches of 5 to avoid search tool timeouts
        total_queries = len(queries_to_process)
        for batch_start in range(0, total_queries, QUERY_BATCH_SIZE):
            batch_end = min(batch_start + QUERY_BATCH_SIZE, total_queries)
            batch_queries = queries_to_process[batch_start:batch_end]
            
            print(f"Processing query batch {batch_start // QUERY_BATCH_SIZE + 1} ({len(batch_queries)} queries: {batch_start+1}-{batch_end} of {total_queries})")
            
            # Process current batch concurrently
            batch_results = await asyncio.gather(
                *[process_query(q) for q in batch_queries],
                return_exceptions=True
            )

            # Flatten batch records
            for q_res in batch_results:
                if isinstance(q_res, list):
                    records.extend(q_res)
                elif isinstance(q_res, Exception):
                    print(f"Error during query processing: {q_res}")
            
            # Wait before processing next batch (except for the last batch)
            if batch_end < total_queries:
                print(f"Waiting {BATCH_DELAY} seconds before next batch...")
                await asyncio.sleep(BATCH_DELAY)

        # Batch upsert to Pinecone
        if records:
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                # ADDED: Pass unique_id to upsert_records
                self.index.upsert_records(namespace="Search", records=batch)


    async def _crawl_and_chunk(self, query: str, url: str) -> list:
        """
        Helper method to crawl a URL and create chunks
        Returns a list of chunk records
        """
        try:
            crawled_result = await web_crawler(url=url)

            if isinstance(crawled_result, str):  # Error message returned
                print(f"Failed to crawl {url}: {crawled_result}")
                return []

            # dividing the crawled_result into chunks
            chunker = TextChunker(chunk_size=400, overlap=50)
            chunks = chunker.chunk_text(
                crawled_result.text if isinstance(crawled_result, ScrapeResult) else crawled_result
            )

            # Extract chunk texts for embedding
            chunk_texts = [chunk['text'] for chunk in chunks]

            # Generate embeddings
            query_embedding = self.embedding_model.encode_query(query)
            chunk_embeddings = self.embedding_model.encode_document(chunk_texts)

            # Calculate similarity scores
            similarities = self.embedding_model.similarity(query_embedding, chunk_embeddings)[0]

            # Filter chunks based on similarity threshold
            relevant_chunks = []
            similarity_threshold = 0.35

            for idx, chunk in enumerate(chunks):
                similarity_score = float(similarities[idx])

                if similarity_score >= similarity_threshold:
                    # Create chunk records
                    chunk_record = {
                        "_id": f"{hashlib.md5(url.encode()).hexdigest()}_chunk_{chunk['chunk_id']}",
                        "unique_id": self.unique_id,
                        "title": crawled_result.title,
                        "description": crawled_result.description,
                        "url": crawled_result.url,
                        "chunk_id": chunk['chunk_id'],
                        "chunk_text": chunk['text']
                    }
                    relevant_chunks.append(chunk_record)
            
            return relevant_chunks
        except Exception as e:
            print(f"Error processing {url}: {e}")
            return []
    
    def is_url_exists(self, url: str) -> bool:
        """Check if URL exists for this specific unique_id"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        result = self.index.fetch(ids=[f"{url_hash}_chunk_0"])
        
        # ADDED: Also check if it belongs to current unique_id
        if len(result.vectors) > 0:
            vector = result.vectors.get(f"{url_hash}_chunk_0")
            if vector and vector.get('metadata', {}).get('unique_id') == self.unique_id:
                return True
        return False
    
    def delete_workspace_data(self):
        """Delete all data for this workspace (unique_id)"""
        self.index.delete(filter={"unique_id": self.unique_id})
            
if __name__ == "__main__":
    explorer_agent = ExplorerAgent(
        queries=["Who is CEO of OPENAI?"], 
        unique_id="68fe0850fc39fbc33364c7e1", 
        get_answer=True, 
        get_multiple_answer=False, 
        max_results=2,
        model="moonshotai/kimi-k2:free"
    )
    results = asyncio.run(explorer_agent.run())
    print(results)
    # for result in results:
    #     print(result.summary)