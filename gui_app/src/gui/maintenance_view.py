"""Onglet Maintenance : affichage des versions actuelles et disponibles (yt-dlp, gui_app) ; accès aux logs."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from typing import Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
    QFrame,
    QScrollArea,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QPalette, QColor

from src import __version__ as APP_VERSION
from src.core.paths import LOG_DIR
from src.gui.styles import (
    get_stylesheet,
    get_theme_preference,
    set_theme_preference,
    get_effective_theme,
    get_theme_colors,
    apply_button_palette,
)
from src.gui.about_dialog import show_about_dialog


# Repo GitHub pour vérifier les mises à jour de l'app (vide = pas de vérification).
GITHUB_REPO = "ZiToUnEAnTiCipWiN32/youtube-downloader"


def _get_yt_dlp_version() -> str:
    """Retourne la version installée de yt-dlp ou '—' si indisponible."""
    try:
        import yt_dlp.version as yt_dlp_version
        return getattr(yt_dlp_version, "__version__", "—")
    except Exception:
        try:
            import yt_dlp
            return getattr(yt_dlp, "__version__", "—")
        except Exception:
            return "—"


def _parse_version(s: str) -> tuple[int, ...]:
    """Convertit une chaîne de version en tuple d'entiers pour comparaison."""
    parts = []
    for x in s.strip().lstrip("v").split("."):
        try:
            parts.append(int(x))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def _is_newer(local: str, remote: str) -> bool:
    """True si remote est une version plus récente que local."""
    if not remote or remote == "—":
        return False
    return _parse_version(remote) > _parse_version(local)


class CheckUpdatesWorker(QThread):
    """Thread pour récupérer les versions disponibles (PyPI, GitHub) sans bloquer la GUI."""
    finished_signal = Signal(dict)  # yt_dlp, gui_app, yt_dlp_error, gui_app_error (indépendants)

    def __init__(self, github_repo: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._github_repo = (github_repo or "").strip()

    def run(self) -> None:
        result: dict[str, Any] = {"yt_dlp": None, "gui_app": None, "yt_dlp_error": None, "gui_app_error": None}
        try:
            # PyPI : dernière version de yt-dlp
            req = urllib.request.Request(
                "https://pypi.org/pypi/yt-dlp/json",
                headers={"User-Agent": "YouTube-Downloader-GUI"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                result["yt_dlp"] = data.get("info", {}).get("version")
        except Exception as e:
            result["yt_dlp_error"] = str(e)

        if self._github_repo:
            try:
                # GitHub API : dernier release
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{self._github_repo}/releases/latest",
                    headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "YouTube-Downloader-GUI"},
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    tag = data.get("tag_name", "")
                    result["gui_app"] = tag.lstrip("v") if tag else None
            except Exception as e:
                result["gui_app_error"] = str(e)

        self.finished_signal.emit(result)


class MaintenanceWidget(QWidget):
    """Widget minimal : versions actuelles et éventuellement disponibles."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: CheckUpdatesWorker | None = None
        self._build_ui()
        self._refresh_current()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)

        intro = QLabel(
            "Versions installées et dernières versions disponibles. Cliquez sur « Vérifier les mises à jour » pour actualiser."
        )
        intro.setWordWrap(True)
        intro.setProperty("class", "muted")
        intro.setStyleSheet("font-size: 11px; padding: 4px 0;")
        layout.addWidget(intro)

        # Thème d'affichage
        gb_theme = QGroupBox("Thème d'affichage")
        ly_theme = QVBoxLayout(gb_theme)
        ly_theme.setSpacing(8)
        row_theme = QHBoxLayout()
        row_theme.addWidget(QLabel("Thème :"))
        self._combo_theme = QComboBox()
        self._combo_theme.addItems(["Système", "Clair", "Sombre"])
        self._combo_theme.setCurrentIndex(self._theme_pref_to_index(get_theme_preference()))
        self._combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        self._apply_combo_theme_palette()
        row_theme.addWidget(self._combo_theme)
        row_theme.addStretch(1)
        ly_theme.addLayout(row_theme)
        layout.addWidget(gb_theme)

        # yt-dlp
        gb_ytdlp = QGroupBox("yt-dlp")
        ly_ytdlp = QVBoxLayout(gb_ytdlp)
        ly_ytdlp.setSpacing(8)
        row_cur = QHBoxLayout()
        row_cur.addWidget(QLabel("Version actuelle :"))
        self._lbl_ytdlp_current = QLabel("—")
        self._lbl_ytdlp_current.setStyleSheet("font-weight: 600;")
        row_cur.addWidget(self._lbl_ytdlp_current)
        row_cur.addStretch(1)
        ly_ytdlp.addLayout(row_cur)
        row_avail = QHBoxLayout()
        row_avail.addWidget(QLabel("Version disponible :"))
        self._lbl_ytdlp_available = QLabel("—")
        self._lbl_ytdlp_available.setProperty("class", "muted")
        row_avail.addWidget(self._lbl_ytdlp_available)
        row_avail.addStretch(1)
        ly_ytdlp.addLayout(row_avail)
        layout.addWidget(gb_ytdlp)

        # gui_app
        gb_app = QGroupBox("YouTube Downloader By ZiToUnE-AnTiCip-WiN32 (cette application)")
        ly_app = QVBoxLayout(gb_app)
        ly_app.setSpacing(8)
        row_cur = QHBoxLayout()
        row_cur.addWidget(QLabel("Version actuelle :"))
        self._lbl_app_current = QLabel(APP_VERSION)
        self._lbl_app_current.setStyleSheet("font-weight: 600;")
        row_cur.addWidget(self._lbl_app_current)
        row_cur.addStretch(1)
        ly_app.addLayout(row_cur)
        row_avail = QHBoxLayout()
        row_avail.addWidget(QLabel("Version disponible :"))
        self._lbl_app_available = QLabel("—" if not GITHUB_REPO else "…")
        self._lbl_app_available.setProperty("class", "muted")
        row_avail.addWidget(self._lbl_app_available)
        row_avail.addStretch(1)
        ly_app.addLayout(row_avail)
        if not GITHUB_REPO:
            note = QLabel("Configurez GITHUB_REPO dans maintenance_view.py pour vérifier les mises à jour.")
            note.setProperty("class", "muted")
            note.setStyleSheet("font-size: 10px;")
            ly_app.addWidget(note)
        layout.addWidget(gb_app)

        # Bouton
        btn_check = QPushButton("Vérifier les mises à jour")
        btn_check.setProperty("class", "primary")
        btn_check.clicked.connect(self._check_updates)
        layout.addWidget(btn_check)

        # Accès aux dossiers (logs)
        gb_folders = QGroupBox("Dossiers")
        ly_folders = QVBoxLayout(gb_folders)
        ly_folders.setSpacing(8)
        row_logs = QHBoxLayout()
        row_logs.addWidget(QLabel(f"Logs : {LOG_DIR}"))
        btn_open_logs = QPushButton("Ouvrir le dossier des logs")
        btn_open_logs.clicked.connect(self._open_logs_folder)
        row_logs.addWidget(btn_open_logs)
        row_logs.addStretch(1)
        ly_folders.addLayout(row_logs)
        layout.addWidget(gb_folders)

        # À propos
        btn_about = QPushButton("À propos de l'application")
        btn_about.clicked.connect(lambda: show_about_dialog(self))
        layout.addWidget(btn_about)

        self._lbl_status = QLabel()
        self._lbl_status.setProperty("class", "muted")
        self._lbl_status.setStyleSheet("font-size: 11px;")
        self._lbl_status.setWordWrap(True)
        layout.addWidget(self._lbl_status)

        layout.addStretch(1)
        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_combo_theme_palette()

    def _apply_combo_theme_palette(self) -> None:
        """Applique la palette du thème courant au combo Thème (lisibilité en mode clair)."""
        app = QApplication.instance()
        if not app:
            return
        theme = get_effective_theme(app, get_theme_preference())
        c = get_theme_colors(theme)
        p = self._combo_theme.palette()
        p.setColor(QPalette.ColorRole.Base, QColor(c["bg_input"]))
        p.setColor(QPalette.ColorRole.Text, QColor(c["text_primary"]))
        p.setColor(QPalette.ColorRole.Window, QColor(c["bg_input"]))
        p.setColor(QPalette.ColorRole.Button, QColor(c["bg_input"]))
        p.setColor(QPalette.ColorRole.ButtonText, QColor(c["text_primary"]))
        self._combo_theme.setPalette(p)

    @staticmethod
    def _theme_pref_to_index(pref: str) -> int:
        """Préférence -> index combo : system=0, light=1, dark=2."""
        p = (pref or "system").strip().lower()
        if p == "dark":
            return 2
        if p == "light":
            return 1
        return 0

    def _on_theme_changed(self) -> None:
        """Enregistre la préférence et réapplique le thème à toute l'app."""
        idx = self._combo_theme.currentIndex()
        pref = ("system", "light", "dark")[idx] if 0 <= idx <= 2 else "system"
        set_theme_preference(pref)
        app = QApplication.instance()
        if app is not None:
            theme = get_effective_theme(app, pref)
            app.setStyleSheet(get_stylesheet(theme))
            self._apply_combo_theme_palette()
            apply_button_palette(self.window(), theme)

    def _refresh_current(self) -> None:
        self._lbl_ytdlp_current.setText(_get_yt_dlp_version())
        self._lbl_app_current.setText(APP_VERSION)

    def _open_logs_folder(self) -> None:
        """Ouvre le dossier des logs dans l'explorateur du système."""
        path_str = str(LOG_DIR)
        if not LOG_DIR.exists():
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(path_str)
            elif sys.platform == "darwin":
                subprocess.run(["open", path_str], check=False)
            else:
                subprocess.run(["xdg-open", path_str], check=False)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Dossier",
                f"Impossible d'ouvrir le dossier : {e}",
            )

    def _check_updates(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._lbl_status.setText("Vérification en cours…")
        self._lbl_ytdlp_available.setText("…")
        if GITHUB_REPO:
            self._lbl_app_available.setText("…")
        self._worker = CheckUpdatesWorker(GITHUB_REPO, self)
        self._worker.finished_signal.connect(self._on_check_finished)
        self._worker.start()

    @Slot(dict)
    def _on_check_finished(self, result: dict) -> None:
        self._worker = None
        err_ytdlp = result.get("yt_dlp_error")
        err_app = result.get("gui_app_error")

        # yt-dlp : afficher la version disponible si on l'a, sinon "—" en cas d'erreur
        yt_dlp_remote = result.get("yt_dlp")
        if err_ytdlp:
            self._lbl_ytdlp_available.setText("—")
        elif yt_dlp_remote:
            yt_dlp_cur = _get_yt_dlp_version()
            if _is_newer(yt_dlp_cur, yt_dlp_remote):
                self._lbl_ytdlp_available.setText(f"{yt_dlp_remote} (mise à jour disponible)")
            else:
                self._lbl_ytdlp_available.setText(f"{yt_dlp_remote} (à jour)")
        else:
            self._lbl_ytdlp_available.setText("—")

        # App : afficher la version disponible si repo configuré et qu'on l'a, sinon "—"
        app_remote = result.get("gui_app")
        if GITHUB_REPO:
            if err_app:
                self._lbl_app_available.setText("—")
            elif app_remote:
                if _is_newer(APP_VERSION, app_remote):
                    self._lbl_app_available.setText(f"{app_remote} (mise à jour disponible)")
                else:
                    self._lbl_app_available.setText(f"{app_remote} (à jour)")
            else:
                self._lbl_app_available.setText("—")

        # Message de statut : erreurs éventuelles
        parts = []
        if err_ytdlp:
            parts.append(f"yt-dlp : {err_ytdlp}")
        if err_app:
            parts.append(f"App : {err_app}")
        self._lbl_status.setText(" ; ".join(parts) if parts else "Vérification terminée.")
