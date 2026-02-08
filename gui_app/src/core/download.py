"""Téléchargement des vidéos via yt-dlp (avec progression et résultat)."""
from __future__ import annotations

import logging
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Callable

import yt_dlp  # type: ignore[import-untyped]

from .paths import (
    ARCHIVE_FILE,
    LOG_DIR,
    OUTPUT_DIR,
    OUTPUT_TEMPLATE,
    REMOTE_COMPONENTS,
    ensure_dirs,
    ensure_windows_path_in_env,
)
from .cookies import get_cookiefile_path

# Messages utilisateur pour les erreurs gérées (comme dans cli_app)
BOT_COOKIE_MSG = "Bot/cookies : mettez à jour cookies.txt (ou « Importer depuis Firefox » dans Prérequis)."
COOKIES_INVALID_MSG = "Cookies expirés/invalides : mettez à jour cookies.txt (export depuis le navigateur ou import depuis Firefox)."
NO_TITLE_MSG = "Métadonnées incomplètes (fallback titre)."
SIG_EJS_RUNTIME_MSG = "Problème technique yt-dlp (signature/EJS/runtime). Vérifiez Deno et mettez à jour yt-dlp."


def _is_bot_cookie_error(msg: str) -> bool:
    """True si le message est l'erreur YouTube 'Sign in to confirm you're not a bot'."""
    return "Sign in" in msg and "bot" in msg.lower()


def _is_cookies_invalid_error(msg: str) -> bool:
    """True si le message indique que les cookies YouTube sont expirés/invalides (rotated)."""
    return "cookies are no longer valid" in msg or "rotated in the browser" in msg.lower()


def _is_no_title_warning(msg: str) -> bool:
    """True si le message est 'No title found in player responses; falling back...'."""
    return "No title found" in msg and "player responses" in msg


def _is_sig_ejs_runtime(msg: str) -> bool:
    """True si le message concerne sig/EJS/runtime (Deno, challenge)."""
    if "sig function possibilities" in msg or "challenge solving failed" in msg:
        return True
    if "Ensure you have a supported JavaScript runtime" in msg:
        return True
    if "refer to" in msg and "EJS" in msg:
        return True
    return False


def _user_friendly_error(msg: str) -> str:
    """Retourne un message utilisateur en français pour les erreurs connues (bot, cookies, etc.)."""
    if not msg:
        return ""
    if _is_bot_cookie_error(msg):
        return BOT_COOKIE_MSG
    if _is_cookies_invalid_error(msg):
        return COOKIES_INVALID_MSG
    if _is_no_title_warning(msg):
        return NO_TITLE_MSG
    if _is_sig_ejs_runtime(msg):
        return SIG_EJS_RUNTIME_MSG
    return msg


def get_error_advice(error_msg: str) -> str:
    """
    Retourne une ligne « Conseil : ... » selon le type d'erreur (comme en CLI / DOCUMENTATION).
    Vide si l'erreur n'est pas reconnue.
    """
    if not error_msg:
        return ""
    if _is_bot_cookie_error(error_msg) or error_msg.strip() == BOT_COOKIE_MSG:
        return "Conseil : ajoutez ou mettez à jour les cookies (onglet Prérequis → « Importer depuis Firefox » ou « Comment obtenir cookies.txt »)."
    if _is_cookies_invalid_error(error_msg) or error_msg.strip() == COOKIES_INVALID_MSG:
        return "Conseil : ré-exportez cookies.txt depuis le navigateur (connecté à YouTube), puis remplacez le fichier dans le dossier de l'app."
    if _is_no_title_warning(error_msg) or error_msg.strip() == NO_TITLE_MSG:
        return "Conseil : souvent lié aux cookies. Mettez à jour cookies.txt ou utilisez « Importer depuis Firefox » (onglet Prérequis)."
    if _is_sig_ejs_runtime(error_msg) or error_msg.strip() == SIG_EJS_RUNTIME_MSG:
        return "Conseil : installez Deno (voir onglet Prérequis) et mettez à jour yt-dlp (pip install -U yt-dlp)."
    return ""


@dataclass
class DownloadResult:
    """Résultat d'un run de téléchargement."""
    ok: int
    skipped: int
    error: int
    last_error: str = ""


def _video_base_key(fn: str | None) -> str | None:
    """Clé unique par vidéo (évite double comptage merge : fragment .m4a et .mp4 final = même clé)."""
    if not fn:
        return None
    key = re.sub(r"\.(f\d+\.)?(webm|mp4|mkv|m4a)$", "", fn, flags=re.IGNORECASE)
    return key or fn


def _is_fragment_path(fn: str | None) -> bool:
    """True si le chemin est un fragment yt-dlp avant merge."""
    if not fn:
        return False
    return bool(re.search(r"\.f\d+\.(webm|mp4|mkv|m4a)$", fn, re.IGNORECASE))


def _is_video_output_path(fn: str | None) -> bool:
    """True si le chemin correspond à une sortie vidéo/audio (fragment ou fichier final), pas aux métadonnées (.info.json, etc.)."""
    if not fn:
        return False
    fn_lower = fn.lower()
    if fn_lower.endswith(".info.json") or ".info.json" in fn_lower:
        return False
    if re.search(r"\.f\d+\.(webm|mp4|mkv|m4a)$", fn, re.IGNORECASE):
        return True
    if any(fn_lower.endswith(ext) for ext in (".mp4", ".webm", ".mkv", ".m4a")):
        return True
    return False


def _extract_already_downloaded_path(msg: str) -> str | None:
    """Si le message est '[download] ... has already been downloaded', retourne le chemin ; sinon None."""
    if " has already been downloaded" not in msg:
        return None
    prefix = "[download] "
    if not msg.startswith(prefix):
        return None
    path = msg[len(prefix) : msg.index(" has already been downloaded")].strip()
    return path if path else None


def _extract_already_in_archive(msg: str) -> str | None:
    """Si le message est '[download] ... has already been recorded in the archive', retourne un libellé pour l'affichage."""
    if " has already been recorded in the archive" not in msg:
        return None
    prefix = "[download] "
    if prefix not in msg:
        return None
    after_prefix = msg[msg.index(prefix) + len(prefix) : msg.index(" has already been recorded in the archive")].strip()
    clean = re.sub(r"\033\[[0-9;]*m", "", after_prefix).strip()
    if not clean:
        return None
    # Format possible : "ID: Titre" ou "ID: " → afficher le titre si présent, sinon l'id
    if ": " in clean:
        _, rest = clean.split(":", 1)
        rest = rest.strip()
        return rest if rest else clean
    return clean


def _short_display_name(fn: str | None, max_len: int = 55) -> str:
    """Nom court pour le journal (comme en CLI : fichier final .mp4 après merge)."""
    if not fn:
        return "?"
    p = pathlib.Path(fn)
    # Pour les fragments (.f247.webm etc.), le fichier final sera .mp4
    base_key = _video_base_key(fn)
    if base_key:
        p_base = pathlib.Path(base_key)
        name = p_base.name + ".mp4" if not p_base.suffix else p_base.name
    else:
        name = p.name
    if len(name) > max_len:
        name = "..." + name[-max_len + 3 :]
    return name


def run_download(
    urls: list[str],
    *,
    progress_callback: Callable[[str, float, str], None] | None = None,
) -> DownloadResult:
    """
    Lance le téléchargement des URLs avec yt-dlp.
    progress_callback(msg, percent, status) est appelé pour la progression (status = "downloading" | "finished" | "error").
    Retourne DownloadResult(ok, skipped, error, last_error).
    """
    ensure_windows_path_in_env()
    ensure_dirs()
    counters: dict[str, Any] = {"ok": 0, "skipped": 0, "error": 0}
    last_error: list[str] = []
    finished_keys: set[str] = set()
    pending_finished_key: str | None = None

    # Messages utilisateur collectés depuis les logs yt-dlp (bot, cookies invalides, etc.)
    collected_hints: list[str] = []

    # Logger : compte "déjà en archive" + affiche dans le journal (comme en CLI) + "déjà sur disque" + collecte les erreurs
    class _ArchiveCounter(logging.Handler):
        def __init__(self, callback: Callable[[str, float, str], None] | None) -> None:
            super().__init__()
            self._callback = callback

        def emit(self, record: logging.LogRecord) -> None:
            msg = self.format(record)
            if " has already been recorded in the archive" in msg:
                counters["skipped"] += 1
                label = _extract_already_in_archive(msg)
                if label and self._callback:
                    display = label if len(label) <= 55 else "..." + label[-52:]
                    self._callback("⊙ Vidéo déjà en archive : " + display, 0.0, "already_in_archive")
            friendly = _user_friendly_error(msg)
            if friendly and friendly != msg and friendly not in collected_hints:
                collected_hints.append(friendly)

    class _AlreadyOnDiskHandler(logging.Handler):
        """Affiche « ⊙ Vidéo déjà sur le disque : ... » dans la GUI (comme en CLI)."""

        def __init__(self, callback: Callable[[str, float, str], None] | None) -> None:
            super().__init__()
            self._callback = callback

        def emit(self, record: logging.LogRecord) -> None:
            msg = self.format(record)
            path = _extract_already_downloaded_path(msg)
            if path and self._callback:
                self._callback(
                    "⊙ Vidéo déjà sur le disque : " + _short_display_name(path),
                    0.0,
                    "already_on_disk",
                )

    file_logger = logging.getLogger("yt_dlp_gui")
    file_logger.setLevel(logging.DEBUG)
    file_logger.handlers.clear()
    file_logger.propagate = False
    LOG_DIR.mkdir(exist_ok=True)
    fh = logging.FileHandler(LOG_DIR / "yt_session.log", mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(message)s"))
    file_logger.addHandler(fh)
    file_logger.addHandler(_ArchiveCounter(progress_callback))
    file_logger.addHandler(_AlreadyOnDiskHandler(progress_callback))

    def progress_hook(d: dict[str, Any]) -> None:
        nonlocal pending_finished_key
        status = d.get("status")
        fn = d.get("filename", "?")
        key = _video_base_key(fn)
        # Pourcentage : _percent (numérique) ou _percent_str, sinon calcul depuis downloaded_bytes (fragments)
        pct = d.get("_percent")
        if pct is None:
            percent_str = (d.get("_percent_str") or "0.0%").strip()
            try:
                pct = float(percent_str.replace("%", "").replace(",", "."))
            except (ValueError, TypeError):
                pct = 0.0
            # Fallback : yt-dlp (fragments) peut ne pas remplir _percent_str ; calcul depuis bytes
            if d.get("downloaded_bytes") is not None:
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total and total > 0:
                    pct = min(100.0, 100.0 * d["downloaded_bytes"] / total)
        if pct is None or pct < 0:
            pct = 0.0

        if status == "downloading":
            if pending_finished_key is not None and key != pending_finished_key:
                if pending_finished_key not in finished_keys:
                    finished_keys.add(pending_finished_key)
                    counters["ok"] += 1
                    if progress_callback:
                        progress_callback(
                            "✔ Vidéo terminée : " + _short_display_name(pending_finished_key),
                            100.0,
                            "video_done",
                        )
                pending_finished_key = None
            if progress_callback:
                percent_str = f"{pct:.1f}%"
                msg = f"  {percent_str} — {fn}"
                progress_callback(msg, pct, "downloading")

        elif status == "finished":
            if key is None or key in finished_keys:
                return
            if not _is_video_output_path(fn):
                return
            if _is_fragment_path(fn):
                if pending_finished_key == key:
                    finished_keys.add(key)
                    counters["ok"] += 1
                    if progress_callback:
                        progress_callback(
                            "✔ Vidéo terminée : " + _short_display_name(fn),
                            100.0,
                            "video_done",
                        )
                    pending_finished_key = None
                else:
                    pending_finished_key = key
            else:
                # Fichier final (.mp4 etc.) : si pending a la même clé, c'est le fragment de cette vidéo → ne compter qu'une fois
                if pending_finished_key is not None:
                    if pending_finished_key == key:
                        # Même vidéo (fragment audio/vidéo + merge) : ne pas compter le pending, seulement le fichier final
                        pending_finished_key = None
                    else:
                        if pending_finished_key not in finished_keys:
                            finished_keys.add(pending_finished_key)
                            counters["ok"] += 1
                            if progress_callback:
                                progress_callback(
                                    "✔ Vidéo terminée : " + _short_display_name(pending_finished_key),
                                    100.0,
                                    "video_done",
                                )
                        pending_finished_key = None
                finished_keys.add(key)
                counters["ok"] += 1
                if progress_callback:
                    progress_callback(
                        "✔ Vidéo terminée : " + _short_display_name(fn),
                        100.0,
                        "video_done",
                    )
            if progress_callback:
                progress_callback(fn, 100.0, "finished")

        elif status == "error":
            counters["error"] += 1
            last_error.append(str(d.get("message", fn)))
            if progress_callback:
                progress_callback(str(d.get("message", fn)), -1.0, "error")

    ydl_opts: dict[str, Any] = {
        "outtmpl": (OUTPUT_DIR / OUTPUT_TEMPLATE).as_posix(),
        "remote_components": REMOTE_COMPONENTS,
        "progress_hooks": [progress_hook],
        "yes_playlist": True,
        "ignoreerrors": True,
        "continuedl": True,
        "download_archive": str(ARCHIVE_FILE),
        "embed_metadata": True,
        "embed_thumbnail": True,
        "merge_output_format": "mp4",
        "quiet": True,
        "logger": file_logger,
    }
    cookiefile_path = get_cookiefile_path()
    if cookiefile_path:
        ydl_opts["cookiefile"] = cookiefile_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)

    # Message d'erreur utilisateur : priorité aux hints collectés (bot, cookies, etc.), sinon last_error normalisé
    raw_error = last_error[-1] if last_error else ""
    display_error = (collected_hints[0] if collected_hints else "") or _user_friendly_error(raw_error) or raw_error

    return DownloadResult(
        ok=counters["ok"],
        skipped=counters["skipped"],
        error=counters["error"],
        last_error=display_error,
    )
