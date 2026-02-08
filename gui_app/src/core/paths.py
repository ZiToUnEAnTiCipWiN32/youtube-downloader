"""Chemins et répertoires de l'application (relatifs au dossier gui_app ou à l'exe)."""
from __future__ import annotations

import os
import pathlib
import sys

# Dossier où placer cookies.txt, etc. : en exe PyInstaller = dossier de l'exe, sinon = gui_app
if getattr(sys, "frozen", False):
    SCRIPT_DIR = pathlib.Path(sys.executable).resolve().parent
else:
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


def get_windows_system_path() -> str | None:
    """Sur Windows, retourne le PATH système + utilisateur (registre).
    Permet de détecter Deno/ffmpeg installés par winget sans redémarrer l'app."""
    if sys.platform != "win32":
        return None
    try:
        import winreg
        path_parts: list[str] = []
        for root, subkey in [
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER, r"Environment"),
        ]:
            try:
                with winreg.OpenKey(root, subkey) as key:
                    path, _ = winreg.QueryValueEx(key, "Path")
                    if path and isinstance(path, str):
                        path_parts.append(os.path.expandvars(path))
            except OSError:
                pass
        if path_parts:
            return os.pathsep.join(path_parts)
    except Exception:
        pass
    return None


def ensure_windows_path_in_env() -> None:
    """Sur Windows, fusionne le PATH du registre en tête de os.environ pour que les sous-processus
    (ex. Deno lancé par yt-dlp) trouvent les outils installés par winget sans redémarrer l'app."""
    system_path = get_windows_system_path()
    if not system_path or not system_path.strip():
        return
    current = os.environ.get("PATH", "")
    os.environ["PATH"] = system_path.strip() + os.pathsep + current
