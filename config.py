# config.py
from pathlib import Path
import os

# Set PROJECT_ROOT to the directory containing this file (the project directory)
PROJECT_ROOT = Path(__file__).resolve().parent

# canonical path to data/global_data (the only one we use)
DATA_GLOBAL = PROJECT_ROOT / "data" / "global_data"
DATA_GLOBAL.mkdir(parents=True, exist_ok=True)

# audio directory in data/audio
AUDIO_DIR = PROJECT_ROOT / "data" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
