"""Chemins et répertoires de l'application (relatifs au dossier gui_app)."""
from __future__ import annotations

import pathlib

# Dossier contenant start.py (gui_app)
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
LOG_DIR = SCRIPT_DIR / "logs"
OUTPUT_DIR = SCRIPT_DIR / "downloads"
ARCHIVE_FILE = SCRIPT_DIR / "archive.txt"
COOKIE_FILE = SCRIPT_DIR / "cookies.txt"
COOKIE_FILE_ENCRYPTED = SCRIPT_DIR / "cookies.enc"

OUTPUT_TEMPLATE = "%(uploader)s/%(playlist,Uploads)s/%(playlist_index)02d - %(title)s.%(ext)s"
REMOTE_COMPONENTS = ["ejs:npm", "ejs:github"]
DEFAULT_CHANNEL_URL = "https://www.youtube.com/@Zitoune-anticip-WIN32"


def ensure_dirs() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
