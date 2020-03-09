# settings.py
from dotenv import load_dotenv
from pathlib import Path  # python3 only
import aiogram

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path, verbose=True)
