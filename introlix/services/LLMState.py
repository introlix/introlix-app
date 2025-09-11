import os
import asyncio
import gc
import requests
import json
from fastapi import HTTPException
from llama_cpp import Llama
from typing import Optional
from introlix.config import MODEL_SAVE_DIR, OPEN_ROUTER_KEY

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

    async def get_open_router(
        self, model_name: str, sys_prompt: str, user_prompt
    ):
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPEN_ROUTER_KEY}",
            },
            data=json.dumps(
                {
                    "model": model_name,  # Optional
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                }
            ),
        )

        return response

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
