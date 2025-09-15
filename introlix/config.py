import os
from platformdirs import user_data_dir
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# KEYS
OPEN_ROUTER_KEY = os.environ["OPEN_ROUTER_KEY"]
SEARCHXNG_HOST = os.environ["SEARCHXNG_HOST"]

# App Info
APP_NAME = "introlix"
APP_AUTHOR = "introlix-ai"

# model config
HF_MODEL_URL = "https://huggingface.co/{username}/{repo_id}/resolve/{branch_name}/{model_name}?download=true"
MODEL_SAVE_DIR = Path(user_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR)) / "models"