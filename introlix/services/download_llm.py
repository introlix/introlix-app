"""
Hugging Face Model Download Service

This module provides functionality for downloading large language models from Hugging Face
repositories with support for resume capability and progress tracking.

Features:
---------
- Streaming downloads with progress updates
- Resume capability for interrupted downloads
- JSON-formatted progress reporting
- Automatic directory creation
- File size validation

The download function yields JSON progress updates that can be streamed to clients
for real-time download status monitoring.
"""

import os
import requests
import json
from introlix.config import HF_MODEL_URL, MODEL_SAVE_DIR



def download_hf_model(username: str, repo_id: str, branch_name: str, model_name: str, save_name: str = None):
    """
    Download a model from Hugging Face with resume capability and progress tracking.

    This function downloads GGUF model files from Hugging Face repositories with support
    for resuming interrupted downloads. It yields JSON-formatted progress updates that
    can be streamed to clients.

    Args:
        username (str): Hugging Face username or organization name.
        repo_id (str): Repository identifier on Hugging Face.
        branch_name (str): Branch name (usually "main").
        model_name (str): Name of the model file to download.
        save_name (str, optional): Custom name to save the file as. If None, uses model_name.

    Yields:
        str: JSON-formatted progress updates containing:
            - status (str): "downloading", "downloaded", or "failed"
            - progress (float): Download progress percentage (0-100)
            - downloaded_bytes (int): Number of bytes downloaded
            - total_bytes (int): Total file size in bytes
            - message (str): Human-readable status message

    Example:
        >>> for update in download_hf_model(
        ...     username="unsloth",
        ...     repo_id="Qwen3-4B-GGUF",
        ...     branch_name="main",
        ...     model_name="model.gguf"
        ... ):
        ...     print(update)
        {"status": "downloading", "progress": 25.5, ...}
        {"status": "downloading", "progress": 50.0, ...}
        {"status": "downloaded", "progress": 100, ...}

    Note:
        - Downloads are saved to MODEL_SAVE_DIR configured in settings
        - Supports HTTP 206 (Partial Content) for resume capability
        - Uses 8KB chunks for efficient memory usage
    """
    MODEL_URL = HF_MODEL_URL.format(
        username=username,
        repo_id=repo_id,
        branch_name=branch_name,
        model_name=model_name,
    )

    if not os.path.isdir(MODEL_SAVE_DIR):
        os.makedirs(MODEL_SAVE_DIR)

    file_size = 0

    if save_name:
        model_name = save_name

    MODEL_PATH = os.path.join(MODEL_SAVE_DIR, model_name)
    if os.path.exists(MODEL_PATH):
        file_size = os.path.getsize(MODEL_PATH)

    # Set up resume headers if file partially exists
    headers = {"Range": f"bytes={file_size}-"} if file_size > 0 else {}

    # Start the request
    with requests.get(MODEL_URL, headers=headers, stream=True) as r:
        total_size = int(r.headers.get("Content-Length", 0)) + file_size

        if file_size >= total_size:
            yield json.dumps(
                {
                    "status": "downloaded",
                    "progress": 100,
                    "downloaded_bytes": total_size,
                    "total_bytes": total_size,
                    "message": f"downloaded {os.path.basename(MODEL_PATH)}",
                }
            ) + "\n"
            return

        if r.status_code in (200, 206):  # 200 = full download, 206 = partial content (resume)
            mode = "ab" if file_size > 0 else "wb"  # Append mode if resuming, write mode otherwise
            downloaded = file_size
            with open(MODEL_PATH, mode) as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (
                            (downloaded / total_size) * 100 if total_size > 0 else 0
                        )

                        yield json.dumps(
                            {
                                "status": "downloading",
                                "progress": round(progress, 2),
                                "downloaded_bytes": downloaded,
                                "total_bytes": total_size,
                                "message": f"Downloading {os.path.basename(MODEL_PATH)}",
                            }
                        ) + "\n"
        else:
            if file_size < 0:
                yield json.dumps(
                    {
                        "status": "failed",
                        "progress": 0,
                        "downloaded_bytes": 0,
                        "total_bytes": 0,
                        "message": "failed to download",
                    }
                ) + "\n"
                return
            else:
                yield json.dumps(
                    {
                        "status": "downloaded",
                        "progress": 100,
                        "downloaded_bytes": total_size,
                        "total_bytes": total_size,
                        "message": f"downloaded {os.path.basename(MODEL_PATH)}",
                    }
                ) + "\n" 
                return


if __name__ == "__main__":
    for update in download_hf_model(
        username="unsloth",
        repo_id="Qwen3-4B-Thinking-2507-GGUF",
        branch_name="main",
        model_name="Qwen3-4B-Thinking-2507-Q4_K_M.gguf",
    ):
        print(update)