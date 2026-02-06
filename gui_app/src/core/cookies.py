"""Gestion des cookies (cookies.txt, cookies.enc) pour yt-dlp."""
from __future__ import annotations

import atexit
import base64
import os
import pathlib
import tempfile

from .paths import COOKIE_FILE, COOKIE_FILE_ENCRYPTED

_cookies_temp_path: pathlib.Path | None = None


def encrypt_cookies_to_file(password: str) -> str | None:
    """
    Chiffre cookies.txt en cookies.enc avec le mot de passe (salt + PBKDF2 + Fernet).
    Même logique que le CLI --encrypt-cookies.
    Retourne None en cas de succès, ou un message d'erreur (str) en cas d'échec.
    """
    if not password or not password.strip():
        return "Mot de passe vide."
    if not cookies_file_valid(COOKIE_FILE):
        return "cookies.txt absent ou invalide. Exportez d'abord vos cookies YouTube dans cookies.txt."
    try:
        from cryptography.fernet import Fernet  # type: ignore[import-untyped]
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore[import-untyped]
        from cryptography.hazmat.primitives import hashes  # type: ignore[import-untyped]

        plain = COOKIE_FILE.read_bytes()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
        f = Fernet(key)
        encrypted = f.encrypt(plain)
        COOKIE_FILE_ENCRYPTED.write_bytes(salt + encrypted)
        return None
    except Exception as e:
        return str(e)


def cookies_file_valid(path: pathlib.Path) -> bool:
    """True si le fichier existe et contient au moins une ligne Netscape (non vide, non commentaire)."""
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            return False
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "\t" in line:
                return True
        return False
    except Exception:
        return False


def _decrypt_cookies_to_temp() -> pathlib.Path | None:
    """Déchiffre cookies.enc vers un fichier temporaire. Retourne le chemin ou None en cas d'échec."""
    global _cookies_temp_path
    if not COOKIE_FILE_ENCRYPTED.exists():
        return None
    password = os.environ.get("YT_COOKIES_PASSWORD", "").strip()
    key_b64 = os.environ.get("YT_COOKIES_KEY", "").strip()
    if not password and not key_b64:
        return None
    try:
        from cryptography.fernet import Fernet  # type: ignore[import-untyped]
        raw = COOKIE_FILE_ENCRYPTED.read_bytes()
        if key_b64:
            f = Fernet(key_b64.encode() if isinstance(key_b64, str) else key_b64)
            plain = f.decrypt(raw)
        else:
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore[import-untyped]
            from cryptography.hazmat.primitives import hashes  # type: ignore[import-untyped]
            if len(raw) < 16:
                return None
            salt, payload = raw[:16], raw[16:]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
            f = Fernet(key)
            plain = f.decrypt(payload)
        tmp = pathlib.Path(tempfile.gettempdir()) / f"yt_cookies_{os.getpid()}_{id(raw)}.txt"
        tmp.write_bytes(plain)
        _cookies_temp_path = tmp
        atexit.register(_cleanup_cookies_temp)
        return _cookies_temp_path
    except Exception:
        return None


def _cleanup_cookies_temp() -> None:
    """Supprime le fichier temporaire de cookies (appelé à la sortie)."""
    global _cookies_temp_path
    if _cookies_temp_path is not None and _cookies_temp_path.exists():
        try:
            _cookies_temp_path.unlink()
        except Exception:
            pass
    _cookies_temp_path = None


def get_cookiefile_path() -> str | None:
    """Retourne le chemin du fichier cookies à passer à yt-dlp (plain cookies.txt ou déchiffré à la volée)."""
    global _cookies_temp_path
    if COOKIE_FILE_ENCRYPTED.exists() and (os.environ.get("YT_COOKIES_PASSWORD") or os.environ.get("YT_COOKIES_KEY")):
        if _cookies_temp_path is None:
            _cookies_temp_path = _decrypt_cookies_to_temp()
        if _cookies_temp_path is not None and _cookies_temp_path.exists():
            if cookies_file_valid(_cookies_temp_path):
                return str(_cookies_temp_path)
        return None
    if cookies_file_valid(COOKIE_FILE):
        return str(COOKIE_FILE)
    return None


def has_cookies_source() -> bool:
    """True si une source de cookies est disponible (cookies.txt valide ou cookies.enc + clé/mot de passe)."""
    if cookies_file_valid(COOKIE_FILE):
        return True
    if COOKIE_FILE_ENCRYPTED.exists() and (os.environ.get("YT_COOKIES_PASSWORD") or os.environ.get("YT_COOKIES_KEY")):
        return True
    return False


def has_cookies_enc_only() -> bool:
    """True si cookies.enc existe mais qu'aucune variable d'environnement (mot de passe/clé) n'est définie."""
    if not COOKIE_FILE_ENCRYPTED.exists():
        return False
    return not (os.environ.get("YT_COOKIES_PASSWORD") or os.environ.get("YT_COOKIES_KEY"))
