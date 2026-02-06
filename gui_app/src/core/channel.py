"""Analyse des chaînes YouTube (onglets / playlists) pour la GUI."""
from __future__ import annotations

import logging
from typing import Any

import yt_dlp  # type: ignore[import-untyped]

from .paths import LOG_DIR, REMOTE_COMPONENTS
from .cookies import get_cookiefile_path

# Logger pour l'analyse (fichier seul, pas de flood dans la GUI)
_extract_logger: logging.Logger | None = None


def _get_extract_logger() -> logging.Logger:
    global _extract_logger
    if _extract_logger is None:
        _extract_logger = logging.getLogger("yt_dlp_extract_gui")
        _extract_logger.setLevel(logging.DEBUG)
        _extract_logger.handlers.clear()
        _extract_logger.propagate = False
        log_file = LOG_DIR / "extract_gui.log"
        LOG_DIR.mkdir(exist_ok=True)
        fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(message)s"))
        _extract_logger.addHandler(fh)
    return _extract_logger


def _count_entries(ydl: Any, url: str) -> int:
    """Retourne le nombre d'entrées (vidéos) pour une URL playlist/onglet. -1 en cas d'erreur."""
    try:
        info = ydl.extract_info(url, download=False, process=False)
        if not info:
            return 0
        entries = info.get("entries")
        if entries is None:
            return 0
        return len(list(entries))
    except Exception:
        return -1


def get_channel_sections(channel_base: str) -> list[dict[str, Any]]:
    """
    Analyse la chaîne YouTube et retourne la liste des sections (onglets + playlists).
    Chaque section : {"label": str, "url": str, "count": int}.
    count = -1 en cas d'erreur d'extraction (ex. cookies invalides).
    """
    sections: list[dict[str, Any]] = []
    opts = {
        "extract_flat": "entries",
        "quiet": True,
        "no_warnings": True,
        "remote_components": REMOTE_COMPONENTS,
        "logger": _get_extract_logger(),
    }
    cookiefile_path = get_cookiefile_path()
    if cookiefile_path:
        opts["cookiefile"] = cookiefile_path

    base = channel_base.rstrip("/")

    with yt_dlp.YoutubeDL(opts) as ydl:
        for tab_label, path in [
            ("Vidéos (uploads, hors playlists)", "/videos"),
            ("Shorts", "/shorts"),
            ("Directs (Live)", "/streams"),
        ]:
            url = base + path
            n = _count_entries(ydl, url)
            sections.append({"label": tab_label, "url": url, "count": n})

        # Playlists personnalisées de la chaîne
        playlists_url = base + "/playlists"
        try:
            info = ydl.extract_info(playlists_url, download=False, process=False)
            entries = list(info.get("entries") or []) if info else []
            for entry in entries:
                if not entry or not isinstance(entry, dict):
                    continue
                pl_url = entry.get("url") or entry.get("id")
                if not pl_url:
                    continue
                if isinstance(pl_url, str) and not pl_url.startswith("http"):
                    pl_url = f"https://www.youtube.com/playlist?list={pl_url}"
                pl_title = (entry.get("title") or "Sans nom").strip() or "Sans nom"
                pl_count = _count_entries(ydl, pl_url)
                sections.append({"label": f'Playlist "{pl_title}"', "url": pl_url, "count": pl_count})
        except Exception:
            pass

    return sections
