import os
import requests
import json
from introlix.config import HF_MODEL_URL, MODEL_SAVE_DIR


def download_hf_model(username: str, repo_id: str, branch_name: str, model_name: str, save_name: str = None):
    """
    Downloading model from huggingface.
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

    # Request headers (for resuming download if file partially exists)
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

        if r.status_code in (200, 206):  # 200 = full download, 206 = partial (resume)
            mode = "ab" if file_size > 0 else "wb"  # append if resuming
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