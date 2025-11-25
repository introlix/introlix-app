"""
LLM State Management Service

This module provides a centralized service for managing Large Language Model (LLM) instances
and API interactions. It supports both local models (via llama.cpp) and cloud-based APIs
(Google AI Studio/Gemini and OpenRouter).

Key Features:
-------------
- Local model loading and management with llama.cpp
- GPU acceleration support with automatic memory management
- Cloud API integration (Google Gemini, OpenRouter)
- Streaming and non-streaming response support
- Thread-safe model loading/unloading with async locks
- Automatic format conversion between OpenAI and Gemini message formats

Supported Providers:
-------------------
- Local: llama.cpp models (GGUF format)
- Google AI Studio: Gemini models
- OpenRouter: Various cloud models
"""

import os
import asyncio
import gc
import requests
import json
from fastapi import HTTPException
from llama_cpp import Llama
from typing import Optional, AsyncGenerator, Union
from introlix.config import MODEL_SAVE_DIR, OPEN_ROUTER_KEY, GEMINI_API_KEY

class LLMState:
    """
    Manages LLM instances and API interactions for the application.

    This class provides a singleton-like state manager for LLMs, handling:
    - Loading and unloading of local llama.cpp models
    - API calls to Google Gemini and OpenRouter
    - Streaming and non-streaming responses
    - Memory management and GPU cache clearing

    Attributes:
        llm (Optional[Llama]): The currently loaded llama.cpp model instance.
        current_model_name (Optional[str]): Name of the currently loaded model.
        lock (asyncio.Lock): Async lock for thread-safe model operations.
    """

    def __init__(self):
        """
        Initialize the LLM state manager.
        """
        self.llm: Optional[Llama] = None
        self.current_model_name: Optional[str] = None
        self.lock = asyncio.Lock()

    async def load_model(
        self, model_name: str, n_ctx: int = 2048, n_gpu_layers: int = 0
    ):
        """
        Load a local llama.cpp model from disk.

        This method handles loading GGUF format models with automatic memory management.
        If a model is already loaded, it will be unloaded first. GPU memory is cleared
        when switching models.

        Args:
            model_name (str): Name of the model file (must be in MODEL_SAVE_DIR).
            n_ctx (int): Context window size. Defaults to 2048.
            n_gpu_layers (int): Number of layers to offload to GPU. 0 = CPU only. Defaults to 0.

        Returns:
            dict: Status message and model name.

        Raises:
            HTTPException: 400 if model name is invalid.
            HTTPException: 404 if model file not found.
            HTTPException: 500 if model loading fails.

        Example:
            >>> await llm_state.load_model("llama-2-7b.gguf", n_ctx=4096, n_gpu_layers=32)
            {"status": "Model loaded", "model_name": "llama-2-7b.gguf"}
        """
        model_path = os.path.join(MODEL_SAVE_DIR, model_name)

        if not os.path.basename(model_name) == model_name:
            raise HTTPException(status_code=400, detail="Invalid model name")
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=404, detail=f"Model file {model_name} not found"
            )

        if self.current_model_name == model_name:
            return {"status": "Model already loaded", "model_name": model_name}

        async with self.lock:
            # Unload existing model if any to free memory
            if self.llm is not None:
                del self.llm
                self.llm = None
                self.current_model_name = None
                gc.collect()  # Force garbage collection
                # Clear GPU memory if using GPU acceleration
                if n_gpu_layers > 0:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

            # Load new model
            try:
                self.llm = Llama(
                    model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers
                )
                self.current_model_name = model_name
                return {"status": "Model loaded", "model_name": model_name}
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Error loading model: {str(e)}"
                )
            
    async def get_ai_studio(
            self,
            model_name: str,
            messages: list,
            stream: bool = False
    ) -> Union[requests.Response, AsyncGenerator[str, None]]:
        """
        Get response from Google AI Studio (Gemini) API.

        This method automatically converts OpenAI-style messages to Gemini's format:
        - Separates system instructions from chat history
        - Converts 'user' and 'assistant' roles to Gemini's 'user' and 'model'
        - Handles both streaming and non-streaming responses

        Args:
            model_name (str): Gemini model name (e.g., "gemini-2.0-flash-exp").
            messages (list): List of message dicts with 'role' and 'content' keys.
            stream (bool): Whether to stream the response. Defaults to False.

        Returns:
            Union[requests.Response, AsyncGenerator[str, None]]:
                - Response object if stream=False
                - AsyncGenerator yielding text chunks if stream=True

        Example:
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant"},
            ...     {"role": "user", "content": "Hello!"}
            ... ]
            >>> response = await llm_state.get_ai_studio("gemini-2.0-flash-exp", messages)
        """
        
        # Separate System Prompt from Chat History
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "system":
                # As per your curl: "system_instruction": { "parts": [...] }
                system_instruction = {
                    "parts": [{"text": content}]
                }
            elif role == "user":
                gemini_contents.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
            elif role == "assistant":
                gemini_contents.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })

        # Build the request payload for Gemini API
        payload = {
            "contents": gemini_contents,
            # Optional: Safety settings or generation config can be added here
            # "generationConfig": {"temperature": 0.7}
        }

        # Add system instruction only if we found one in your messages list
        if system_instruction:
            payload["system_instruction"] = system_instruction

        # Prepare headers with API key
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }

        base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}"

        if stream:
            # Streaming endpoint with SSE (Server-Sent Events) for easier parsing
            url = f"{base_url}:streamGenerateContent?alt=sse"
            
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(payload),
                stream=True
            )
            return self._stream_gemini_response(response)
        else:
            # Standard endpoint
            url = f"{base_url}:generateContent"
            
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(payload)
            )
            return response

    async def _stream_gemini_response(self, response: requests.Response) -> AsyncGenerator[str, None]:
        """
        Parse Gemini's Server-Sent Events (SSE) stream format.

        This helper method processes the streaming response from Gemini API,
        extracting text content from the JSON chunks.

        Args:
            response (requests.Response): The streaming response object from Gemini API.

        Yields:
            str: Text chunks from the Gemini response.
        """
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                # Gemini SSE lines start with "data: " just like OpenAI
                if line.startswith('data: '):
                    data = line[6:] # Remove 'data: '
                    try:
                        chunk = json.loads(data)
                        # Extract text from Gemini's specific JSON structure
                        if "candidates" in chunk and len(chunk["candidates"]) > 0:
                            candidate = chunk["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                text = candidate["content"]["parts"][0].get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        continue


    async def get_open_router(
        self, 
        model_name: str, 
        messages: list,
        stream: bool = False
    ) -> Union[requests.Response, AsyncGenerator[str, None]]:
        """
        Get response from OpenRouter API
        
        Args:
            model_name: The model to use
            messages: List of message dicts
            stream: Whether to stream the response (default: False)
        
        Returns:
            Response object if stream=False, AsyncGenerator if stream=True
        """
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": stream
        }
        
        if not stream:
            # Non-streaming response
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPEN_ROUTER_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps(payload),
            )
            return response
        else:
            # Streaming response
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPEN_ROUTER_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps(payload),
                stream=True
            )
            return self._stream_response(response)

    async def _stream_response(self, response: requests.Response) -> AsyncGenerator[str, None]:
        """
        Process streaming response from OpenRouter
        
        Args:
            response: The streaming response object
            
        Yields:
            Content chunks from the stream
        """
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    async def unload_model(self):
        """
        Unload the current local model and free memory.

        This method safely unloads the llama.cpp model, performs garbage collection,
        and clears GPU memory if applicable.

        Returns:
            dict: Status message indicating success or if no model was loaded.

        Example:
            >>> await llm_state.unload_model()
            {"status": "Model unloaded"}
        """
        async with self.lock:
            if self.llm is None:
                return {"status": "No model loaded"}
            del self.llm
            self.llm = None
            self.current_model_name = None
            gc.collect()  # Force garbage collection
            # Clear GPU memory if used
            import torch

            if torch.cuda.is_available():

                torch.cuda.empty_cache()
            return {"status": "Model unloaded"}

    def get_llm(self):
        """
        Get the current LLM instance.

        Returns:
            Llama: The currently loaded llama.cpp model instance.

        Raises:
            HTTPException: 500 if no model is currently loaded.

        Example:
            >>> llm = llm_state.get_llm()
            >>> response = llm.create_completion("Hello world")
        """
        if self.llm is None:
            raise HTTPException(status_code=500, detail="No model loaded")
        return self.llm
