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
    def __init__(self):
        self.llm: Optional[Llama] = None
        self.current_model_name: Optional[str] = None
        self.lock = asyncio.Lock()

    async def load_model(
        self, model_name: str, n_ctx: int = 2048, n_gpu_layers: int = 0
    ):
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
            # Unload existing model if any
            if self.llm is not None:
                del self.llm
                self.llm = None
                self.current_model_name = None
                gc.collect()  # Force garbage collection
                # If using GPU, ensure CUDA context is cleared (handled by llama.cpp)
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
        Get response from Google AI Studio API using the structure from your curl command.
        Automatically converts OpenAI 'messages' list to Gemini 'contents' and 'system_instruction'.
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

        # Build the Payload
        payload = {
            "contents": gemini_contents,
            # Optional: Safety settings or generation config can go here
            # "generationConfig": {"temperature": 0.7} 
        }

        # Add system instruction only if we found one in your messages list
        if system_instruction:
            payload["system_instruction"] = system_instruction

        # Prepare Headers (Using x-goog-api-key as requested)
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
        Helper to parse Gemini's SSE stream format
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
        """Unload the current model and free memory."""
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
        """Get the current LLM instance or raise an error if not loaded."""
        if self.llm is None:
            raise HTTPException(status_code=500, detail="No model loaded")
        return self.llm
