from platformdirs import user_data_dir
from pathlib import Path

APP_NAME = "introlix"
APP_AUTHOR = "introlix-ai"

MODEL_SAVE_DIR = Path(user_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR)) / "models"