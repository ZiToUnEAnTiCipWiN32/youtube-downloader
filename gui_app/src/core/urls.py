"""Validation et normalisation des URLs YouTube."""
from __future__ import annotations

from urllib.parse import urlparse

from .paths import DEFAULT_CHANNEL_URL

_ALLOWED_HOSTS = ("youtube.com", "www.youtube.com", "youtu.be")


def normalize_channel_url(user_input: str) -> str:
    """Convertit @handle, handle ou URL en URL de base chaîne YouTube."""
    s = (user_input or "").strip()
    if not s:
        return DEFAULT_CHANNEL_URL.rstrip("/")
    if s.startswith("http://") or s.startswith("https://"):
        url = s.rstrip("/")
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower().lstrip("www.")
            if not any(host == h or host.endswith("." + h) for h in _ALLOWED_HOSTS):
                return DEFAULT_CHANNEL_URL.rstrip("/")
        except Exception:
            return DEFAULT_CHANNEL_URL.rstrip("/")
        return url
    if not s.startswith("@"):
        s = "@" + s
    return f"https://www.youtube.com/{s}"


def is_youtube_video_url(url: str) -> bool:
    """True si l'URL est une URL YouTube valide (vidéo, short, live, etc.)."""
    s = (url or "").strip()
    if not s or not (s.startswith("http://") or s.startswith("https://")):
        return False
    try:
        parsed = urlparse(s)
        host = (parsed.netloc or "").lower().lstrip("www.")
        if not any(host == h or host.endswith("." + h) for h in _ALLOWED_HOSTS):
            return False
        return bool(parsed.path or parsed.query)
    except Exception:
        return False
