"""
The Explorer Agent retrieves and analyzes information from the internet using
SearXNG search and web crawling. It operates on multiple topics in parallel,
stores content in a vector database, and generates structured summaries for
efficient downstream processing.

Input Format:
==============================================================================
QUERIES: <list of search queries or research topics>
UNIQUE_ID: <workspace identifier for data isolation>
GET_ANSWER: <true | false - whether to generate summary answers>
GET_MULTIPLE_ANSWER: <true | false - return multiple answers or single consolidated>
MAX_RESULTS: <maximum number of search results per query>
MODEL: <LLM model identifier for content analysis>
==============================================================================

Output Format:
==============================================================================
EXPLORER_OUTPUT: {
    "topic": "<the research topic explored>",
    "title": ["<webpage title 1>", "<webpage title 2>"],
    "urls": ["<url 1>", "<url 2>"],
    "summary": "<detailed summary of content relevant to the topic>",
    "relevance_score": <0.0-1.0 score indicating content relevance>,
    "source_type": "<academic | news | blog | government | commercial>"
}
==============================================================================

Workflow:
---------
1. Search for relevant URLs using SearXNG
2. Crawl and extract content from web pages in parallel
3. Chunk content with semantic similarity filtering (threshold: 0.35)
4. Store chunks in Pinecone vector database with workspace isolation
5. Retrieve relevant chunks and generate LLM-powered summaries
6. Retry failed queries up to max_retries times

Notes:
------
- Uses Pinecone for vector storage with workspace (unique_id) isolation
- Processes queries in batches of 5 to avoid search tool timeouts
- Supports both single and multiple answer modes
- Implements semantic similarity filtering to store only relevant chunks
- Automatically retries queries that don't find sufficient data
- Embedding model: google/embeddinggemma-300m
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
    """
    Structured output from the Explorer Agent's web search and analysis.

    This model represents the analyzed and summarized information from web sources
    relevant to a specific research topic.

    Attributes:
        topic (str): The research topic that was explored.
        title (list): List of webpage titles from the sources.
        urls (list): List of webpage URLs that were analyzed.
        summary (str): Detailed summary of the content relevant to the topic.
        relevance_score (float): Score between 0.0 and 1.0 indicating content relevance.
        source_type (str): Type of source (academic, news, blog, government, commercial).
    """
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
    """
    The Explorer Agent retrieves and analyzes information from the internet.

    This agent performs web searches using SearXNG, crawls relevant pages, chunks the content,
    stores it in a Pinecone vector database, and generates structured summaries using an LLM.
    It supports parallel processing of multiple queries and workspace isolation.

    Key Features:
    1. Web search using SearXNG
    2. Parallel web crawling and content extraction
    3. Text chunking with semantic similarity filtering
    4. Vector storage in Pinecone with workspace isolation
    5. LLM-powered content summarization
    6. Retry logic for failed queries

    Workflow:
    - Search for relevant URLs using SearXNG
    - Crawl and extract content from web pages
    - Chunk content and filter by semantic similarity
    - Store chunks in Pinecone vector database
    - Retrieve relevant chunks and generate summaries

    Attributes:
        queries (list): List of search queries to process.
        unique_id (str): Workspace ID for data isolation.
        get_answer (bool): Whether to generate summary answers.
        get_multiple_answer (bool): Whether to return multiple answers per query.
        max_results (int): Maximum number of search results per query.
        model (str): LLM model identifier for summarization.
        pc (Pinecone): Pinecone client instance.
        index (Index): Pinecone index for vector storage.
        embedding_model (SentenceTransformer): Model for generating embeddings.
        explorer_agent (Agent): LLM agent for content analysis.
        search_tool (SearXNGClient): Web search client.
    """

    def __init__(self, queries: list, unique_id: str, get_answer: bool, get_multiple_answer: bool, max_results = 5, model="gemini-2.5-flash"):
        """
        Initializes the ExplorerAgent with configuration parameters.

        Args:
            queries (list): List of search queries or topics to explore.
            unique_id (str): Unique workspace ID to isolate data per workspace.
            get_answer (bool): Whether to generate final answer summaries.
            get_multiple_answer (bool): If True, returns multiple answers from different sources.
                                        If False, returns one consolidated answer.
            max_results (int): Maximum number of search results to process per query. Defaults to 5.
            model (str): LLM model identifier for content analysis. Defaults to "gemini-2.5-flash".
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
        """
        Creates the Pinecone index if it doesn't exist.

        This method initializes the vector database index with the appropriate
        configuration for storing and searching document chunks.
        """
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
        Executes the exploration workflow for the configured queries.

        This method orchestrates the entire process:
        1. Searches Pinecone for existing relevant content
        2. If no content found, fetches new data from the web
        3. Generates summaries using the LLM
        4. Retries failed queries up to max_retries times

        Args:
            retry (int): Current retry attempt count. Defaults to 0.
            max_retries (int): Maximum number of retry attempts. Defaults to 5.
            queries_to_process (list, optional): Specific queries to process (used in retries).
                                                 If None, processes all queries.

        Returns:
            Union[ExplorerAgentOutput, List[ExplorerAgentOutput], None]:
                - Single ExplorerAgentOutput if get_answer=True and get_multiple_answer=False
                - List of ExplorerAgentOutput if get_multiple_answer=True
                - None if get_answer=False (data collection only)
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
        Fetches data from the internet and saves it to the vector database.

        This method:
        1. Performs web searches for each query
        2. Crawls the resulting URLs in parallel
        3. Chunks the content and filters by semantic similarity
        4. Stores relevant chunks in Pinecone

        Queries are processed in batches to avoid overwhelming the search tool.

        Args:
            queries (list, optional): List of queries to process. If None, uses self.queries.
        """
        QUERY_BATCH_SIZE = 5  # Process 5 queries at a time
        BATCH_DELAY = 2  # Wait 2 seconds between batches
        queries_to_process = queries if queries else self.queries

        def save_records(records: list):
            """
            Persists records to Pinecone in batches.

            Args:
                records (list): List of chunk records to save.
            """
            if not records:
                return
            BATCH_SIZE = 96
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i:i + BATCH_SIZE]
                self.index.upsert_records(namespace="Search", records=batch)

        async def process_query(query: str):
            search_results = await self.search_tool.search(query=query, max_results=self.max_results)

            # Crawl URLs concurrently for this query
            crawl_tasks = []
            for result in search_results:
                url = result.url
                if self.is_url_exists(url):
                    continue
                crawl_tasks.append(self._crawl_and_chunk(query, url))

            if not crawl_tasks:
                return []

            flat_records = []
            for task in asyncio.as_completed(crawl_tasks):
                try:
                    rec_list = await task
                except Exception as e:
                    print(f"Error during crawling: {e}")
                    continue

                if isinstance(rec_list, list) and rec_list:
                    flat_records.extend(rec_list)
                    save_records(rec_list)
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
                if isinstance(q_res, Exception):
                    print(f"Error during query processing: {q_res}")
            
            # Wait before processing next batch (except for the last batch)
            if batch_end < total_queries:
                print(f"Waiting {BATCH_DELAY} seconds before next batch...")
                await asyncio.sleep(BATCH_DELAY)


    async def _crawl_and_chunk(self, query: str, url: str) -> list:
        """
        Crawls a URL, extracts content, chunks it, and filters by semantic similarity.

        This method:
        1. Crawls the webpage and extracts text content
        2. Divides content into chunks with overlap
        3. Generates embeddings for query and chunks
        4. Calculates similarity scores
        5. Filters chunks above similarity threshold (0.35)
        6. Returns formatted chunk records for Pinecone

        Args:
            query (str): The search query for similarity comparison.
            url (str): The URL to crawl and process.

        Returns:
            list: List of chunk records with metadata, or empty list on error.
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
        """
        Checks if a URL has already been crawled and stored for this workspace.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL exists for this unique_id, False otherwise.
        """
        url_hash = hashlib.md5(url.encode()).hexdigest()
        result = self.index.fetch(ids=[f"{url_hash}_chunk_0"])
        
        # ADDED: Also check if it belongs to current unique_id
        if len(result.vectors) > 0:
            vector = result.vectors.get(f"{url_hash}_chunk_0")
            if vector and vector.get('metadata', {}).get('unique_id') == self.unique_id:
                return True
        return False
    
    def delete_workspace_data(self):
        """
        Deletes all stored data for the current workspace.

        This removes all vectors and metadata associated with this unique_id
        from the Pinecone index.
        """
        self.index.delete(filter={"unique_id": self.unique_id})
            
if __name__ == "__main__":
    explorer_agent = ExplorerAgent(
        queries=["Who is CEO of OPENAI?"], 
        unique_id="68fe0850fc39fbc33364c7e1", 
        get_answer=True, 
        get_multiple_answer=False, 
        max_results=2,
        model="gemini-2.5-flash"
    )
    results = asyncio.run(explorer_agent.run())
    print(results)
    # for result in results:
    #     print(result.summary)