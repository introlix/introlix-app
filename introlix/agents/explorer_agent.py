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
MAX_RESULTS: <maximum number of search results per query>
MODEL: <LLM model identifier for content analysis>
==============================================================================

Output Format:
==============================================================================
EXPLORER_OUTPUT: [{
    "title": ["<webpage title 1>", "<webpage title 2>"],
    "description": ["<webpage description 1>", "<webpage description 2>"],
    "url": "<url>",
    "chunk_text": "<detailed summary of content relevant to the topic>",
    "score": <0.0-1.0 score indicating content relevance>,
}[]
==============================================================================

Workflow:
---------
1. Search for relevant URLs using SearXNG
2. Crawl and extract content from web pages in parallel
3. Chunk content with semantic similarity filtering (threshold: 0.35)
4. Store chunks in Pinecone vector database with workspace isolation
5. Retrieve relevant chunks
6. Retry failed queries up to max_retries times

Notes:
------
- Uses Pinecone for vector storage with workspace (unique_id) isolation
- Processes queries in batches of 5 to avoid search tool timeouts
- Implements semantic similarity filtering to store only relevant chunks
- Automatically retries queries that don't find sufficient data
- Embedding model: google/embeddinggemma-300m or all-MiniLM-L6-v2
"""

import asyncio

import hashlib
from typing import List, Union
from pinecone import Pinecone
from pydantic import BaseModel, Field
from introlix.config import PINECONE_KEY
from introlix.tools.web_crawler import web_crawler, ScrapeResult
from introlix.tools.web_search import SearXNGClient
from introlix.utils.text_chunker import TextChunker
from sentence_transformers import SentenceTransformer


class ExplorerAgentOutput(BaseModel):
    title: str = Field(description="The list title of the web page")
    description: str = Field(description="The list description of the web page")
    url: str = Field(description="The list url of the web page")
    chunk_text: str = Field(description="Chunk of the web page according to the topic")
    score: float = Field(
        description="The score of the sources between 0.0 and 1.0"
    )


class ExplorerAgent:
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_KEY)
        self.index_name = "explored-data-index"
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.MAX_CONCURRENT_URLS = 30
        self._setup_index()

    def _setup_index(self):
        existing_indexes = [index.name for index in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "chunk_text"},
                },
            )

        self.index = self.pc.Index(self.index_name)

    async def run(
        self,
        queries: list,
        unique_id: str,
        get_answer: bool,
        max_results=5,
        model="gemini-2.5-flash",
        retry: int = 0,
        max_retries: int = 5,
        queries_to_process: list = None
    ) -> Union[ExplorerAgentOutput, List[ExplorerAgentOutput], None]:
        self.queries = queries
        self.unique_id = unique_id
        self.get_answer = get_answer
        self.max_results = max_results
        self.model = model
        self.search_tool = SearXNGClient(model=model)

        if retry > max_retries:
            return ExplorerAgentOutput(
                topic="",
                title=[],
                urls=[],
                summary="",
                relevance_score=0,
                source_type="",
            )

        queries_to_search = queries_to_process if queries_to_process else self.queries

        if self.get_answer:
            all_answers = []
            queries_needing_data = []

            tasks = [self.process_single_query(q) for q in queries_to_search]
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in task_results:
                if isinstance(result, Exception):
                    print(f"Error processing query: {result}")
                    continue
                _, new_queries_needing_data, new_all_answers = result

                queries_needing_data.extend(new_queries_needing_data)
                all_answers.extend(new_all_answers)

            if queries_needing_data:
                await self.get_and_save_data(queries_needing_data)
                
                retry_results = await self.run(
                    queries=queries,
                    unique_id=unique_id,
                    get_answer=get_answer,
                    max_results=max_results,
                    model=model,
                    retry=retry + 1,
                    max_retries=max_retries,
                    queries_to_process=queries_needing_data,
                )

                if isinstance(retry_results, list):
                    valid_results = [
                        r
                        for retry_result in retry_results
                        for r in retry_result
                        if r.chunk_text and len(r.chunk_text) > 0
                    ]
                    all_answers.extend(valid_results)
                elif (
                    retry_results
                    and retry_results.chunk_text
                    and len(retry_results.chunk_text) > 0
                ):
                    all_answers.append(retry_results)

            if not all_answers:
                return ExplorerAgentOutput(
                    output=[]
                )

            return all_answers
        else:
            await self.get_and_save_data(queries_to_search)
            return None

    async def process_single_query(
        self,
        query: str
    ) -> tuple:
        results = []
        queries_needing_data = []
        all_answers = []
        try:
            results_ = self.index.search(
                namespace="Search",
                query={
                    "top_k": 3,
                    "inputs": {"text": query},
                    "filter": {"unique_id": self.unique_id},
                },
            )

            hits = results_.get("result", {}).get("hits", [])

            threshold = 0.50
            filtered_hits = [
                hit for hit in hits 
                if hit.get("_score", 0) >= threshold
            ]
            for hit in filtered_hits:
                try:
                    data = {
                        "_id": hit.get("_id", ""),
                        "title": hit.get("fields", {}).get("title", ""),
                        "description": hit.get("fields", {}).get("description", ""),
                        "url": hit.get("fields", {}).get("url", ""),
                        "chunk_text": hit.get("fields", {}).get("chunk_text", ""),
                        "score": hit.get("_score", 0.0),
                    }
                    if not data["chunk_text"]:
                        continue

                    data = ExplorerAgentOutput(**data)
                    results.append(data)
                except Exception as e:
                    print(f"Error parsing search hit: {e}")
                    continue
        except Exception as e:
            print(f"Error searching Pinecone for query '{query}': {e}")
            queries_needing_data.append(query)
            return results, queries_needing_data, all_answers

        if not results:
            queries_needing_data.append(query)
            return None, queries_needing_data, all_answers

        if self.get_answer:
                all_answers.append(results)

        return results, queries_needing_data, all_answers

    async def get_and_save_data(self, queries: list = None):
        QUERY_BATCH_SIZE = 10
        queries_to_process = queries if queries else self.queries

        def save_records(records: list):
            if not records:
                return
            BATCH_SIZE = 96
            for i in range(0, len(records), BATCH_SIZE):
                batch = records[i : i + BATCH_SIZE]
                self.index.upsert_records(namespace="Search", records=batch)
        

        async def process_query(query: str):
            search_results = await self.search_tool.search(
                query=query, max_results=self.max_results
            )

            crawl_tasks = []

            async def filter_existing_urls(result):
                if not self.is_url_exists(result.url):
                    return result.url
                return None
            
            tasks = [filter_existing_urls(result) for result in search_results]
            task_results = await asyncio.gather(*tasks, return_exceptions=True)


            url_semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_URLS)

            async def crawl_with_limit(url):
                async with url_semaphore:
                    return await self._crawl_and_chunk(query, url)

            for url in task_results:
                if isinstance(url, Exception):
                    print(f"Error checking URL existence: {url}")
                    continue
                if url:
                    crawl_tasks.append(crawl_with_limit(url))

            if not crawl_tasks:
                return []

            flat_records = []
            for task in asyncio.as_completed(crawl_tasks):
                try:
                    rec_list = await task
                except Exception as e:
                    continue

                if isinstance(rec_list, list) and rec_list:
                    flat_records.extend(rec_list)
                    save_records(rec_list)
                elif isinstance(rec_list, Exception):
                    print(f"Error during crawling: {rec_list}")

            return flat_records

        total_queries = len(queries_to_process)
        for batch_start in range(0, total_queries, QUERY_BATCH_SIZE):
            batch_end = min(batch_start + QUERY_BATCH_SIZE, total_queries)
            batch_queries = queries_to_process[batch_start:batch_end]

            batch_results = await asyncio.gather(
                *[process_query(q) for q in batch_queries], return_exceptions=True
            )

            for q_res in batch_results:
                if isinstance(q_res, Exception):
                    print(f"Error during query processing: {q_res}")

    async def _crawl_and_chunk(self, query: str, url: str) -> list:
        try:
            crawled_result = await web_crawler(url=url)

            if isinstance(crawled_result, str):
                return []

            chunker = TextChunker(chunk_size=400, overlap=50)
            chunks = chunker.chunk_text(
                crawled_result.text
                if isinstance(crawled_result, ScrapeResult)
                else crawled_result
            )

            chunk_texts = [chunk["text"] for chunk in chunks]

            query_embedding = self.embedding_model.encode_query(query)
            chunk_embeddings = self.embedding_model.encode_document(chunk_texts, batch_size=32)

            similarities = self.embedding_model.similarity(
                query_embedding, chunk_embeddings
            )[0]

            relevant_chunks = []
            similarity_threshold = 0.40

            for idx, chunk in enumerate(chunks):
                similarity_score = float(similarities[idx])

                if similarity_score >= similarity_threshold:
                    chunk_record = {
                        "_id": f"{hashlib.md5(url.encode()).hexdigest()}_chunk_{chunk['chunk_id']}",
                        "unique_id": self.unique_id,
                        "title": crawled_result.title,
                        "description": crawled_result.description,
                        "url": crawled_result.url,
                        "chunk_id": chunk["chunk_id"],
                        "chunk_text": chunk["text"],
                    }
                    relevant_chunks.append(chunk_record)

            return relevant_chunks
        except Exception as e:
            print(f"Error processing {url}: {e}")
            return []

    def is_url_exists(self, url: str) -> bool:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        result = self.index.fetch(ids=[f"{url_hash}_chunk_0"])

        if len(result.vectors) > 0:
            vector = result.vectors.get(f"{url_hash}_chunk_0")
            if vector and vector.get("metadata", {}).get("unique_id") == self.unique_id:
                return True
        return False

    def delete_workspace_data(self):
        self.index.delete(filter={"unique_id": self.unique_id})


if __name__ == "__main__":
    explorer_agent = ExplorerAgent()
    results = asyncio.run(explorer_agent.run(
        queries=["PM of Nepal"],
        unique_id="test2",
        get_answer=True,
        max_results=2
    ))
    print(results)