"""
Auteur => ZiToUnEAnTiCipWiN32
Date => 04/02/2026
Version => 1.0.0

Script de téléchargement de vidéos YouTube par chaîne ou par URL.

Utilise yt-dlp dans un venv dédié, avec archive, cookies et logs.
Modes => une chaîne (onglets / playlists) ou une vidéo (coller l'URL).

Youtube => https://www.youtube.com/@Zitoune-anticip-WIN32
Site   => http://zitouneanticip.free.fr
GitHub => https://github.com/ZiToUnEAnTiCipWiN32
"""

from __future__ import annotations

import atexit
import base64
import datetime
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import urlparse

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent        # répertoire du script
VENV_DIR = SCRIPT_DIR / "yt_env"                            # répertoire du venv
# Windows: Scripts/python.exe | Linux/macOS: bin/python
VENV_BIN = "Scripts" if sys.platform == "win32" else "bin"
VENV_PYTHON = VENV_DIR / VENV_BIN / ("python.exe" if sys.platform == "win32" else "python")
LOG_DIR = SCRIPT_DIR / "logs"
OUTPUT_DIR = SCRIPT_DIR / "downloads"
ARCHIVE_FILE = SCRIPT_DIR / "archive.txt"
COOKIE_FILE = SCRIPT_DIR / "cookies.txt"
COOKIE_FILE_ENCRYPTED = SCRIPT_DIR / "cookies.enc"          # cookies chiffrés (recommandé)
# Variable d'environnement : YT_COOKIES_PASSWORD (mot de passe) ou YT_COOKIES_KEY (clé Fernet base64)

# Chaîne YouTube par défaut (l'utilisateur peut la changer au démarrage de chaque tour)
DEFAULT_CHANNEL_URL = "https://www.youtube.com/@Zitoune-anticip-WIN32"
# Liens affichés au démarrage et à la sortie (pub / crédit) 
SCRIPT_CHANNEL = "Youtube : https://www.youtube.com/@Zitoune-anticip-WIN32"
SCRIPT_WEBSITE = "Site   : http://zitouneanticip.free.fr"  
SCRIPT_GITHUB = "GitHub : https://github.com/ZiToUnEAnTiCipWiN32"  
# Affichage du bloc crédit : délai en secondes entre chaque ligne (0 = pas d'animation)
CREDIT_DELAY = 0.30             # 0.30 = 300ms entre chaque ligne
CREDIT_BOX_WIDTH = 72           # largeur du bloc crédit
OUTPUT_TEMPLATE = "%(uploader)s/%(playlist,Uploads)s/%(playlist_index)02d - %(title)s.%(ext)s"
# EJS : ejs:npm (Deno) = scripts à jour ; sinon ejs:github
REMOTE_COMPONENTS = ["ejs:npm", "ejs:github"]

LOG_FILE_GENERAL = LOG_DIR / "yt_download.log"
log_session = LOG_DIR / f"yt_{datetime.datetime.now():%Y%m%d_%H%M%S}_{os.getpid()}.log"

# Couleurs ANSI (compatibles Windows avec colorama plus bas)
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# Rendu utilisateur : largeur du cadre (ASCII pour alignement fiable sous Windows)
# Ligne max : ≈ 77 car. + marge
UI_WIDTH = 88
MENU_CONTENT_WIDTH = UI_WIDTH - 4  # entre les deux |, moins l'espace après [ et avant ] ; largeur du contenu du menu   
BOX_TOP = "+" + "-" * (UI_WIDTH - 2) + "+"      # bord supérieur du cadre
BOX_BOT = "+" + "-" * (UI_WIDTH - 2) + "+"      # bord inférieur du cadre
BOX_SIDE = "|"                                  # bord latéral du cadre
BOX_SEP = "+" + "-" * (UI_WIDTH - 2) + "+"      # bord séparateur du cadre


def _init_colors() -> None:
    """Active les couleurs ANSI sur Windows (PowerShell / CMD)."""
    try:
        import colorama
        colorama.init()
    except ImportError:
        pass


def _section_title(title: str) -> str:
    """Retourne une ligne de titre de section pour le terminal."""
    return f"\n{CYAN}{BOLD}  ▶ {title}{RESET}\n"


def _separator(char: str = "─", length: int = 50) -> str:
    """Ligne de séparation horizontale."""
    return f"  {DIM}{char * length}{RESET}"


# Domaines autorisés pour la chaîne (évite de passer des URLs arbitraires à yt-dlp)
_ALLOWED_CHANNEL_HOSTS = ("youtube.com", "www.youtube.com", "youtu.be")


def _normalize_channel_url(user_input: str) -> str:
    """Convertit une saisie utilisateur (@handle, handle ou URL) en URL de base chaîne YouTube.
    Restreint aux domaines YouTube pour éviter les URLs arbitraires."""
    s = user_input.strip()
    if not s:
        return DEFAULT_CHANNEL_URL.rstrip("/")
    if s.startswith("http://") or s.startswith("https://"):
        url = s.rstrip("/")
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower().lstrip("www.")
            if not any(host == h or host.endswith("." + h) for h in _ALLOWED_CHANNEL_HOSTS):
                return DEFAULT_CHANNEL_URL.rstrip("/")
        except Exception:
            return DEFAULT_CHANNEL_URL.rstrip("/")
        return url
    if not s.startswith("@"):
        s = "@" + s
    return f"https://www.youtube.com/{s}"


def _is_youtube_video_url(url: str) -> bool:
    """True si l'URL est une URL YouTube valide (vidéo, short, live, etc.)."""
    s = (url or "").strip()
    if not s or not (s.startswith("http://") or s.startswith("https://")):
        return False
    try:
        parsed = urlparse(s)
        host = (parsed.netloc or "").lower().lstrip("www.")
        if not any(host == h or host.endswith("." + h) for h in _ALLOWED_CHANNEL_HOSTS):
            return False
        return bool(parsed.path or parsed.query)
    except Exception:
        return False


def _clear_terminal() -> None:
    """Efface l'écran du terminal (ANSI, compatible Windows 10+ avec colorama)."""
    print("\033[2J\033[H", end="")
    sys.stdout.flush()


def _print_credit() -> None:
    """Affiche le bloc chaîne / site / GitHub (pub) avec cadre et couleurs, recommandélement animé."""
    w = CREDIT_BOX_WIDTH
    top = f"  {CYAN}┌{'─' * (w - 2)}┐{RESET}"
    bot = f"  {CYAN}└{'─' * (w - 2)}┘{RESET}"
    side = f"  {CYAN}│{RESET}"

    def line(text: str, style: str) -> None:
        visible_len = len(re.sub(r"\033\[[0-9;]*m", "", text))
        pad = max(0, w - 4 - visible_len)
        print(f"  {CYAN}│{RESET} {style}{text}{' ' * pad}{RESET} {CYAN}│{RESET}")
        if CREDIT_DELAY > 0:
            time.sleep(CREDIT_DELAY)
        sys.stdout.flush()

    print(top)
    if CREDIT_DELAY > 0:
        time.sleep(CREDIT_DELAY)
        sys.stdout.flush()
    line(SCRIPT_CHANNEL, f"{CYAN}{BOLD}")
    line(SCRIPT_WEBSITE, GREEN)
    line(SCRIPT_GITHUB, YELLOW)
    print(bot)


def _menu_line(text: str, width: int = MENU_CONTENT_WIDTH) -> str:
    """Une ligne du menu avec padding pour aligner le bord droit (texte complet, pas de troncature)."""
    visible = re.sub(r"\033\[[0-9;]*m", "", text)
    pad = max(0, width - len(visible))
    return f"  {BOX_SIDE} {text}{' ' * pad} {BOX_SIDE}"

# ---------- VENV ----------
def _run_venv_cmd(args: list[str], step: str) -> None:
    """Exécute une commande (venv/pip) en mode silencieux ; en cas d'échec, affiche stderr et quitte."""
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        print(f"  {RED}✖ Échec : {step}{RESET}")
        if result.stderr:
            print(f"  {DIM}{result.stderr.strip()}{RESET}")
        if result.stdout and not result.stderr:
            print(f"  {DIM}{result.stdout.strip()}{RESET}")
        sys.exit(result.returncode)


if not VENV_PYTHON.exists():
    print(f"  {YELLOW}⚡ Création du venv en cours…{RESET}")
    _run_venv_cmd([sys.executable, "-m", "venv", str(VENV_DIR)], "création du venv")
    _run_venv_cmd([str(VENV_PYTHON), "-m", "pip", "install", "-q", "--upgrade", "pip"], "mise à jour de pip")
    _run_venv_cmd([str(VENV_PYTHON), "-m", "pip", "install", "-q", "-U", "--pre", "yt-dlp[default]", "ffmpeg-python", "colorama", "cryptography"], "installation des dépendances")
    print(f"  {GREEN}✔ Venv créé — relance du script{RESET}")

if pathlib.Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    try:
        subprocess.run([str(VENV_PYTHON), str(pathlib.Path(__file__).resolve())] + sys.argv[1:], check=True)
    except subprocess.CalledProcessError as e:
        # Propager le code de sortie de l'enfant sans traceback (ex. 1 = choix invalide, 130 = Ctrl+C)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        sys.exit(130)  # Ctrl+C dans le parent → pas de second message
    sys.exit(0)

# ---------- DENO (requis pour YouTube / EJS) ----------
if not shutil.which("deno"):
    print(f"  {RED}✖ Deno introuvable.{RESET}")
    print(f"  {YELLOW}YouTube nécessite Deno (runtime JS) pour les challenges.{RESET}")
    if sys.platform == "win32":
        print(f"  {CYAN}Installation (PowerShell) : irm https://deno.land/install.ps1 | iex{RESET}")
    else:
        print(f"  {CYAN}Installation : curl -fsSL https://deno.land/install.sh | sh{RESET}")
    print(f"  {DIM}Puis redémarre le terminal et relance le script.{RESET}")
    sys.exit(1)

import yt_dlp  # type: ignore[import-untyped]  # installé dans yt_env/ au premier run

_init_colors()

# ---------- Version yt-dlp  ----------
try:
    __yt_dlp_version__ = yt_dlp.version.__version__
except Exception:
    __yt_dlp_version__ = "?"
print(f"  {CYAN}yt-dlp version : {__yt_dlp_version__}{RESET}")
print(_separator())

# ---------- Créer dossiers ----------
LOG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------- LOGS ----------
general_logger = logging.getLogger("yt_general")
general_logger.setLevel(logging.INFO)
general_logger.handlers.clear()
gh = logging.FileHandler(LOG_FILE_GENERAL, mode="a", encoding="utf-8")
gh.setLevel(logging.INFO)
gh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s",
                                  datefmt="%Y-%m-%d %H:%M:%S"))
general_logger.addHandler(gh)
general_logger.propagate = False

# Une seule ligne pour les avertissements "techniques" (sig/EJS/runtime) → pas de flood
TERMINAL_ONE_LINE_WIDTH = 90
_filtered_warning_count: int = 0

# Messages courts pour éviter de polluer le terminal
BOT_COOKIE_MSG = "⚠ Bot/cookies : mettez à jour cookies.txt"
COOKIES_INVALID_MSG = "⚠ Cookies expirés/invalides : mettez à jour cookies.txt (export depuis le navigateur)"
NO_TITLE_MSG = "⚠ Métadonnées incomplètes (fallback titre)"

def _is_bot_cookie_error(msg: str) -> bool:
    """True si le message est l'erreur YouTube 'Sign in to confirm you're not a bot'."""
    return "Sign in" in msg and "bot" in msg.lower()

def _is_cookies_invalid_error(msg: str) -> bool:
    """True si le message indique que les cookies YouTube sont expirés/invalides (rotated)."""
    return "cookies are no longer valid" in msg or "rotated in the browser" in msg.lower()

def _is_no_title_warning(msg: str) -> bool:
    """True si le message est 'No title found in player responses; falling back...'."""
    return "No title found" in msg and "player responses" in msg

def _extract_already_downloaded_path(msg: str) -> str | None:
    """Si le message est '...path... has already been downloaded', retourne le chemin ; sinon None."""
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
    # Retirer les codes ANSI (ex. \033[0;32m...\033[0m)
    clean = re.sub(r"\033\[[0-9;]*m", "", after_prefix)
    clean = clean.strip()
    if not clean:
        return None
    # Format possible : "ID: Titre" ou "ID: " → afficher le titre si présent, sinon l'id
    if ": " in clean:
        _, rest = clean.split(":", 1)
        rest = rest.strip()
        return rest if rest else clean
    return clean

def _is_technical_warning(msg: str) -> bool:
    """True si le message doit s'afficher sur la ligne unique (sig/EJS/runtime/bot/cookies/métadonnées)."""
    if "sig function possibilities" in msg or "n challenge solving failed" in msg:
        return True
    if "Ensure you have a supported JavaScript runtime" in msg:
        return True
    if "refer to" in msg and "EJS" in msg:
        return True
    if _is_bot_cookie_error(msg):
        return True
    if _is_cookies_invalid_error(msg):
        return True
    if _is_no_title_warning(msg):
        return True
    return False

def _short_technical_line(msg: str, count: int) -> str:
    """Retourne la ligne courte à afficher (personnalisée selon le type)."""
    if _is_bot_cookie_error(msg):
        return f"{BOT_COOKIE_MSG} ({count})"[:TERMINAL_ONE_LINE_WIDTH]
    if _is_cookies_invalid_error(msg):
        return f"{COOKIES_INVALID_MSG} ({count})"[:TERMINAL_ONE_LINE_WIDTH]
    if _is_no_title_warning(msg):
        return f"{NO_TITLE_MSG} ({count})"[:TERMINAL_ONE_LINE_WIDTH]
    return f"⚠ yt-dlp ({count}) : {msg}"[:TERMINAL_ONE_LINE_WIDTH]

class _OneLineTerminalHandler(logging.StreamHandler):
    """Affiche au terminal : avertissements techniques (une ligne), « déjà sur disque », « déjà en archive », le reste en fichier."""
    def __init__(self, stream, counters: dict[str, int]) -> None:
        super().__init__(stream)
        self._counters = counters

    def emit(self, record: logging.LogRecord) -> None:
        global _filtered_warning_count
        try:
            msg = self.format(record)
            path = _extract_already_downloaded_path(msg)
            if path is not None:
                _flush_terminal_warning_line()
                display_name = _truncate_display_name(path, PROGRESS_FN_MAX + 20)
                print(f"  {CYAN}⊙ Vidéo déjà sur le disque : {display_name}{RESET}")
                return
            label = _extract_already_in_archive(msg)
            if label is not None:
                _flush_terminal_warning_line()
                self._counters["skipped"] += 1
                max_len = PROGRESS_FN_MAX + 20
                display = label if len(label) <= max_len else "..." + label[-max_len + 3 :]
                print(f"  {CYAN}⊙ Vidéo déjà en archive : {display}{RESET}")
                return
            if _is_technical_warning(msg):
                _filtered_warning_count += 1
                line = _short_technical_line(msg, _filtered_warning_count)
                self.stream.write(f"\r{line:<{TERMINAL_ONE_LINE_WIDTH}}\r")
                self.flush()
            # Les autres messages : fichier uniquement
        except Exception:
            self.handleError(record)

def _flush_terminal_warning_line() -> None:
    """Passe à la ligne après la ligne d'avertissement yt-dlp pour ne pas écraser le texte suivant."""
    sys.stderr.write("\n")
    sys.stderr.flush()

# ---------- COMPTEURS (avant création du handler qui les utilise) ----------
counters = {
    "ok": 0,
    "error": 0,
    "skipped": 0,  # vidéos ignorées cette session (déjà en archive)
}

# Nombre d'entrées dans l'archive au démarrage (pour le résumé final)
archive_total_at_start = 0
if ARCHIVE_FILE.exists():
    try:
        text = ARCHIVE_FILE.read_text(encoding="utf-8")
        archive_total_at_start = sum(1 for line in text.splitlines() if line.strip())
    except Exception:
        pass

file_logger = logging.getLogger("yt_dlp_file")
file_logger.setLevel(logging.DEBUG)
file_logger.handlers.clear()
fh = logging.FileHandler(log_session, mode="w", encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter("%(message)s"))
file_logger.addHandler(fh)
# Terminal : avertissements techniques + « déjà sur disque » ; le reste en fichier
sh = _OneLineTerminalHandler(sys.stderr, counters)
sh.setLevel(logging.DEBUG)  # DEBUG car yt-dlp logue "has already been downloaded" en DEBUG
sh.setFormatter(logging.Formatter("%(message)s"))
file_logger.addHandler(sh)
file_logger.propagate = False  # évite la double écriture vers le root logger

# Logger pour l'analyse uniquement (fichier seul → pas de flood dans le terminal)
extract_logger = logging.getLogger("yt_dlp_extract")
extract_logger.setLevel(logging.DEBUG)
extract_logger.handlers.clear()
extract_fh = logging.FileHandler(log_session, mode="a", encoding="utf-8")
extract_fh.setLevel(logging.DEBUG)
extract_fh.setFormatter(logging.Formatter("%(message)s"))
extract_logger.addHandler(extract_fh)
extract_logger.propagate = False

# ---------- COOKIES ----------
def _cookies_file_valid(path: pathlib.Path) -> bool:
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


# Cookies chiffrés : chemin du fichier temporaire (déchiffré à la volée), mis à jour une seule fois
_cookies_temp_path: pathlib.Path | None = None


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
    """Supprime le fichier temporaire de cookies (appelé à la sortie du script)."""
    global _cookies_temp_path
    if _cookies_temp_path is not None and _cookies_temp_path.exists():
        try:
            _cookies_temp_path.unlink()
        except Exception:
            pass
    _cookies_temp_path = None


def _get_cookiefile_path() -> str | None:
    """Retourne le chemin du fichier cookies à passer à yt-dlp (plain cookies.txt ou déchiffré à la volée)."""
    global _cookies_temp_path
    if COOKIE_FILE_ENCRYPTED.exists() and (os.environ.get("YT_COOKIES_PASSWORD") or os.environ.get("YT_COOKIES_KEY")):
        if _cookies_temp_path is None:
            _cookies_temp_path = _decrypt_cookies_to_temp()
        if _cookies_temp_path is not None and _cookies_temp_path.exists():
            if _cookies_file_valid(_cookies_temp_path):
                return str(_cookies_temp_path)
        return None
    if _cookies_file_valid(COOKIE_FILE):
        return str(COOKIE_FILE)
    return None


def _has_cookies_source() -> bool:
    """True si une source de cookies est disponible (cookies.txt valide ou cookies.enc + clé/mot de passe)."""
    if _cookies_file_valid(COOKIE_FILE):
        return True
    if COOKIE_FILE_ENCRYPTED.exists() and (os.environ.get("YT_COOKIES_PASSWORD") or os.environ.get("YT_COOKIES_KEY")):
        return True
    return False


if not _has_cookies_source():
    print(f"  {YELLOW}⚠ Cookies non utilisés (fichier absent ou vide). Exportez des cookies YouTube dans cookies.txt — ou chiffrez-les en cookies.enc avec --encrypt-cookies.{RESET}\n")

# ---------- Option --encrypt-cookies ----------
if "--encrypt-cookies" in sys.argv:
    if not _cookies_file_valid(COOKIE_FILE):
        print(f"  {RED}✖ cookies.txt absent ou invalide. Exportez d'abord vos cookies YouTube dans cookies.txt.{RESET}")
        sys.exit(1)
    password = os.environ.get("YT_COOKIES_PASSWORD", "").strip()
    if not password:
        try:
            import getpass
            password = getpass.getpass(f"  {YELLOW}Mot de passe pour chiffrer les cookies : {RESET}").strip()
        except Exception:
            print(f"  {RED}✖ Indiquez YT_COOKIES_PASSWORD ou exécutez dans un terminal pour saisir le mot de passe.{RESET}")
            sys.exit(1)
    if not password:
        print(f"  {RED}✖ Mot de passe vide.{RESET}")
        sys.exit(1)
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
        print(f"  {GREEN}✔ Cookies chiffrés enregistrés dans {COOKIE_FILE_ENCRYPTED.name}{RESET}")
        print(f"  {DIM}Définissez YT_COOKIES_PASSWORD (ou YT_COOKIES_KEY) pour les utiliser. Vous pouvez supprimer cookies.txt.{RESET}")
    except Exception as e:
        print(f"  {RED}✖ Échec du chiffrement : {e}{RESET}")
        sys.exit(1)
    sys.exit(0)

# ---------- PROGRESS HOOK ----------
# Longueur max affichée pour garder la barre sur une seule ligne (évite retours à la ligne)
PROGRESS_FN_MAX = 55
# Largeur fixe de la ligne de progression (padding pour que \r efface toute la ligne)
PROGRESS_LINE_WIDTH = 90
# Barre de progression : nombre de segments et palier de pourcentage (ex. 5 % → 4 segments sur 20)
PROGRESS_BAR_LENGTH = 20
PROGRESS_PERCENT_STEP = 5
# Clés déjà comptées comme "vidéo terminée" (yt-dlp n'envoie pas toujours "finished" pour le .mp4 après merge)
_finished_video_keys: set[str] = set()

def _video_base_key(fn: str | None) -> str | None:
    """Clé unique par vidéo : chemin sans suffixe .fXXX.ext ou .mp4/.m4a (évite double comptage merge)."""
    if not fn:
        return None
    # Enlève .mp4, .webm, .mkv, .m4a ou .f247.webm / .f140.m4a etc.
    key = re.sub(r"\.(f\d+\.)?(webm|mp4|mkv|m4a)$", "", fn, flags=re.IGNORECASE)
    return key or fn


def _is_video_output_path(fn: str | None) -> bool:
    """True si le chemin est une sortie vidéo/audio (fragment ou final), pas métadonnées (.info.json)."""
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


def _is_fragment_path(fn: str | None) -> bool:
    """True si le chemin est un fragment yt-dlp (ex. .f398.mp4, .f251.webm) avant merge."""
    if not fn:
        return False
    return bool(re.search(r"\.f\d+\.(webm|mp4|mkv|m4a)$", pathlib.Path(fn).name, re.IGNORECASE))

def _progress_label(fn: str | None) -> str:
    """Libellé court pour la barre de progression : 'vidéo' / 'audio' pour les fragments, sinon nom tronqué."""
    if not fn:
        return "?"
    name = pathlib.Path(fn).name
    if re.search(r"\.f\d+\.(mp4|mkv)$", name, re.IGNORECASE):
        return "vidéo"
    if re.search(r"\.f\d+\.(webm|m4a)$", name, re.IGNORECASE):
        return "audio"
    if len(name) > PROGRESS_FN_MAX:
        name = "..." + name[-PROGRESS_FN_MAX + 3:]
    return name

def _truncate_display_name(fn: str | None, max_len: int = PROGRESS_FN_MAX) -> str:
    """Retourne le nom du fichier tronqué pour l'affichage."""
    name = pathlib.Path(fn).name if fn else "?"
    if len(name) > max_len:
        name = "..." + name[-max_len + 3:]
    return name

# Clé pour laquelle on a reçu un "finished" (fragment) mais pas encore affiché "Vidéo terminée"
_pending_finished_key: str | None = None

def _emit_video_finished(key: str) -> None:
    """Affiche une fois 'Vidéo terminée' et log pour la clé donnée."""
    if not key or key in _finished_video_keys:
        return
    _finished_video_keys.add(key)
    counters["ok"] += 1
    _flush_terminal_warning_line()
    final_display = str(pathlib.Path(key).with_suffix(".mp4"))
    display_fn = _truncate_display_name(final_display, PROGRESS_FN_MAX + 20)
    print(f"  {GREEN}✔ Vidéo terminée : {display_fn}{RESET}")
    general_logger.info(f"OK | {final_display}")

def progress_hook(d: dict[str, Any]) -> None:
    global _pending_finished_key
    status = d.get("status")
    fn = d.get("filename", "?")
    key = _video_base_key(fn)

    if status == "downloading":
        # Si on passe à une autre vidéo, la précédente (pending) est complète
        if _pending_finished_key is not None and key != _pending_finished_key:
            _emit_video_finished(_pending_finished_key)
            _pending_finished_key = None
        percent = (d.get("_percent_str") or "0.0%").strip()
        try:
            pct = int(float(percent.replace("%", "").replace(",", ".")) // PROGRESS_PERCENT_STEP)
        except (ValueError, TypeError):
            pct = 0
        filled = min(pct, PROGRESS_BAR_LENGTH)
        bar = "█" * filled + "░" * (PROGRESS_BAR_LENGTH - filled)
        # Fragments : afficher "1/2" puis "2/2" pour éviter deux lignes "100% audio" (webm + m4a)
        if _is_fragment_path(fn):
            label = "2/2" if _pending_finished_key == key else "1/2"
        else:
            label = _progress_label(fn)
        line_content = f"  ⏳ [{bar}] {percent}  {label}"
        line_content = (line_content[:PROGRESS_LINE_WIDTH]).ljust(PROGRESS_LINE_WIDTH)
        print(f"\r{CYAN}{line_content}{RESET}", end="")
        sys.stdout.flush()

    elif status == "finished":
        if key is None or key in _finished_video_keys:
            return
        if not _is_video_output_path(fn):
            return
        if _is_fragment_path(fn):
            # Fragment (vidéo ou audio) : afficher "Vidéo terminée" seulement après le dernier fragment
            if _pending_finished_key == key:
                _emit_video_finished(key)
                _pending_finished_key = None
            else:
                # Premier fragment terminé : toujours passer à la ligne pour garder la 1re étape visible.
                # (Sinon, si le flux vidéo est en .webm, on n'ajoutait pas de newline et "100% audio" écrasait "100% vidéo"/"100% audio".)
                print()
                _pending_finished_key = key
        else:
            # Fichier final (.mp4 etc.) : si pending a la même clé, c'est le fragment de cette vidéo → ne compter qu'une fois
            if _pending_finished_key is not None:
                if _pending_finished_key == key:
                    _pending_finished_key = None
                else:
                    _emit_video_finished(_pending_finished_key)
                    _pending_finished_key = None
            _emit_video_finished(key)

    elif status == "error":
        _flush_terminal_warning_line()
        print(f"  {RED}✖ Échec : {_truncate_display_name(fn)}{RESET}")
        counters["error"] += 1
        general_logger.warning(f"ERREUR | {fn}")

# ---------- YT-DLP OPTIONS ----------
# Options pour l'extraction (analyse sans télécharger)
extract_opts = {
    "extract_flat": "entries",
    "quiet": True,
    "no_warnings": True,
    "remote_components": REMOTE_COMPONENTS,
    "logger": extract_logger,  # fichier seul → pas de messages dans le terminal
}
# cookiefile ajouté à la volée via _get_cookiefile_path() au moment de l'utilisation

def _archive_entry_count() -> int:
    """Retourne le nombre d'entrées dans l'archive (fichier archive.txt)."""
    if not ARCHIVE_FILE.exists():
        return 0
    try:
        text = ARCHIVE_FILE.read_text(encoding="utf-8")
        return sum(1 for line in text.splitlines() if line.strip())
    except Exception:
        return 0


def _count_entries(ydl: Any, url: str) -> int:
    """Retourne le nombre d'entrées (vidéos) pour une URL playlist/onglet."""
    try:
        info = ydl.extract_info(url, download=False, process=False)
        if not info:
            return 0
        entries = info.get("entries")
        if entries is None:
            return 0
        return len(list(entries))
    except Exception:
        return -1  # erreur (cookies, etc.)


def _reset_session_state() -> None:
    """Réinitialise l'état d'une session (compteurs, clés vidéo, archive) pour une nouvelle itération en boucle."""
    global archive_total_at_start, _filtered_warning_count, _pending_finished_key
    counters["ok"] = 0
    counters["error"] = 0
    counters["skipped"] = 0
    _finished_video_keys.clear()
    _pending_finished_key = None
    _filtered_warning_count = 0
    archive_total_at_start = 0
    if ARCHIVE_FILE.exists():
        try:
            text = ARCHIVE_FILE.read_text(encoding="utf-8")
            archive_total_at_start = sum(1 for line in text.splitlines() if line.strip())
        except Exception:
            pass


# ---------- BOUCLE PRINCIPALE ----------
def main() -> None:
    """Point d'entrée : mode (chaîne / une vidéo), choix, téléchargement, résumé, relance."""
    try:
        channel_base = DEFAULT_CHANNEL_URL.rstrip("/")
        first_round = True
        # Tour par tour : effacer → mode → (chaîne + analyse + menu ou URL) → téléchargement → résumé → relance ?
        while True:
            _clear_terminal()
            _reset_session_state()

            if first_round:
                _print_credit()
                print()
                first_round = False

            urls_to_download: list[str] | None = None

            # ---------- Choix du mode : chaîne ou une vidéo ----------
            print(_section_title("Mode"))
            print(f"  {BOX_TOP}")
            print(_menu_line(f"{CYAN}[ 1]{RESET} Une chaîne (onglets / playlists)"))
            print(_menu_line(f"{CYAN}[ 2]{RESET} Une vidéo (coller l'URL)"))
            print(f"  {BOX_BOT}\n")
            try:
                mode = input(f"  {YELLOW}Votre choix (Entrée = 1) : {RESET}").strip() or "1"
            except EOFError:
                print(f"\n  {CYAN}Annulé.{RESET}")
                sys.exit(0)
            if mode == "2":
                while urls_to_download is None:
                    try:
                        url_input = input(f"  {YELLOW}URL de la vidéo (ou Entrée pour annuler) : {RESET}").strip()
                    except EOFError:
                        break
                    if not url_input:
                        print(f"  {DIM}Annulé.{RESET}\n")
                        break
                    if _is_youtube_video_url(url_input):
                        urls_to_download = [url_input]
                        print(f"  {GREEN}→ URL enregistrée.{RESET}\n")
                        break
                    print(f"  {RED}✖ URL non valide (YouTube uniquement). Réessayez ou Entrée pour annuler.{RESET}\n")

            # ---------- Mode chaîne : choix de la chaîne + analyse + menu ----------
            if urls_to_download is None:
                print(_section_title("Chaîne"))
                print(f"  {DIM}{channel_base}{RESET}")
                try:
                    change = input(f"  {YELLOW}Garder : Entrée  |  Changer : nom de chaîne (ex. @MaChaîne) ou URL : {RESET}").strip()
                except EOFError:
                    change = ""
                if change:
                    channel_base = _normalize_channel_url(change)
                    print(f"  {GREEN}→ Chaîne : {channel_base}{RESET}\n")

                print(_section_title("Analyse de la chaîne"))
                print(f"  {DIM}{channel_base}{RESET}\n")
                sections = []  # liste de {"label": str, "url": str, "count": int}

                opts_extract = dict(extract_opts)
                cookiefile_path = _get_cookiefile_path()
                if cookiefile_path:
                    opts_extract["cookiefile"] = cookiefile_path
                with yt_dlp.YoutubeDL(opts_extract) as ydl:
                    # Onglets principaux
                    for tab_label, path in [
                        ("Vidéos (uploads, hors playlists)", "/videos"),
                        ("Shorts", "/shorts"),
                        ("Directs (Live)", "/streams"),
                    ]:
                        url = channel_base + path
                        n = _count_entries(ydl, url)
                        sections.append({"label": tab_label, "url": url, "count": n})

                    # Playlists personnalisées de la chaîne
                    playlists_url = channel_base + "/playlists"
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
                    except Exception as e:
                        extract_logger.debug("Playlists non récupérées : %s", e)

                # Message unique si l'analyse a échoué (ex. cookies invalides)
                if sections and all(s["count"] < 0 for s in sections[:3]):
                    print(f"  {YELLOW}⚠ Problème lors de l'analyse (cookies invalides ?). Détails : {log_session}{RESET}\n")

                # ---------- MENU DE SÉLECTION (réaffiché en cas de choix invalide) ----------
                urls_to_download = []
                while not urls_to_download:
                    print(_section_title("Contenu disponible"))
                    print(f"  {BOX_TOP}")
                    for i, s in enumerate(sections, start=1):
                        count_str = f"{s['count']} vidéo(s)" if s["count"] >= 0 else "?"
                        print(_menu_line(f"{CYAN}[{i:2}]{RESET} {s['label']}  {DIM}({count_str}){RESET}"))
                    print(f"  {BOX_SEP}")
                    print(_menu_line(f"{CYAN}[ 0]{RESET} Tout télécharger (onglets + playlists)"))
                    print(_menu_line(f"{CYAN}[ q]{RESET} Quitter sans télécharger"))
                    print(f"  {BOX_BOT}\n")
                    print(f"  {DIM}Ex. : 1   ou   1,3   ou   0 pour tout{RESET}\n")

                    try:
                        choice = input(f"  {YELLOW}Votre choix : {RESET}").strip().lower()
                    except EOFError:
                        print(f"\n  {CYAN}Annulé.{RESET}")
                        sys.exit(0)
                    if choice == "q" or choice == "":
                        print(f"\n  {CYAN}Annulé.{RESET}")
                        sys.exit(0)

                    # Construire la liste des URL à télécharger
                    if choice == "0":
                        urls_to_download = [s["url"] for s in sections]
                    else:
                        for part in choice.replace(",", " ").split():
                            part = part.strip()
                            if not part.isdigit():
                                continue
                            idx = int(part)
                            if 1 <= idx <= len(sections):
                                urls_to_download.append(sections[idx - 1]["url"])

                    # Dédoublonnage (ex. choix "1, 1, 2") en préservant l'ordre
                    urls_to_download = list(dict.fromkeys(urls_to_download))

                    if not urls_to_download:
                        print(f"\n  {RED}✖ Aucune sélection valide. Indiquez un ou plusieurs numéros (ex. 1 ou 1,2).{RESET}\n")

            # ---------- YT-DLP OPTIONS (téléchargement) ----------
            ydl_opts = {
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
            cookiefile_path = _get_cookiefile_path()
            if cookiefile_path:
                ydl_opts["cookiefile"] = cookiefile_path

            # ---------- EXECUTION ----------
            general_logger.info(f"Début | URLs={urls_to_download}")
            print(_section_title("Téléchargement"))
            print(f"  {GREEN}●{RESET} {len(urls_to_download)} groupe(s) sélectionné(s)")
            print(f"  {DIM}Dossier : {OUTPUT_DIR}{RESET}")
            print(f"  {DIM}Archive : {ARCHIVE_FILE}{RESET}\n")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download(urls_to_download)

            general_logger.info("Fin | ok=%d skipped=%d error=%d", counters["ok"], counters["skipped"], counters["error"])

            # ---------- RÉSUMÉ FINAL ----------
            archive_total_current = _archive_entry_count()
            _flush_terminal_warning_line()  # finalise la ligne d'avertissement yt-dlp
            if _filtered_warning_count > 0:
                print(f"  {YELLOW}⚠ {_filtered_warning_count} avertissement(s) yt-dlp — détails : {log_session}{RESET}\n")
            print(_separator("═", 50))
            print(_section_title("Résumé"))
            print(f"  {GREEN}✔ Téléchargées :{RESET}  {counters['ok']}")
            print(f"  {YELLOW}⊙ En archive (session) :{RESET}  {counters['skipped']}")
            print(f"  {RED}✖ Échecs :{RESET}  {counters['error']}")
            print(f"  {DIM}En archive (total actuel) :{RESET}  {archive_total_current}")
            print(_separator("═", 50))
            print(f"\n  {GREEN}Terminé.{RESET}  {DIM}Log : {LOG_FILE_GENERAL}  |  Session : {log_session}{RESET}\n")

            try:
                again = input(f"  {YELLOW}Relancer ? (Entrée = oui, q = quitter) : {RESET}").strip().lower()
            except EOFError:
                again = "q"
            if again == "q":
                break

        print(f"\n  {CYAN}Fin.{RESET}")
        _print_credit()
        print()
    except KeyboardInterrupt:
        print(f"\n  {YELLOW}Interrompu (Ctrl+C).{RESET}")
        sys.exit(130)
    except Exception as e:
        general_logger.exception("Erreur inattendue : %s", e)
        print(f"\n  {RED}✖ Erreur : {e}{RESET}")
        print(f"  {DIM}Détails : {log_session}  |  {LOG_FILE_GENERAL}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
