"""Onglet Téléchargement : mode chaîne / vidéo, analyse, sélection, progression."""
from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Any

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPalette, QColor

from src.core.paths import LOG_DIR, OUTPUT_DIR, ARCHIVE_FILE
from src.gui.styles import get_effective_theme, get_theme_preference, get_theme_colors
from src.core.urls import normalize_channel_url, is_youtube_video_url
from src.core.channel import get_channel_sections
from src.core.download import run_download, DownloadResult, get_error_advice

# Codes ANSI à retirer pour l'affichage (au cas où)
_ANSI_RE = re.compile(r"\033\[[0-9;]+m|\x1b\[[0-9;]+m|\[[0-9;]+m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text).strip()


def _is_progress_line(text: str) -> bool:
    """True si la ligne ressemble à une progression (ex. "0.1% — ..." ou "  0.1% — chemin")."""
    t = text.strip()
    return bool(t and re.match(r"^\s*[\d.,]+\s*%?\s*[—\-]\s*", t))


class AnalyzeWorker(QThread):
    """Thread pour analyser la chaîne sans bloquer la GUI."""
    finished_signal = Signal(list, str)  # sections, error_message (vide si ok)

    def __init__(self, channel_base: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._channel_base = channel_base

    def run(self) -> None:
        try:
            sections = get_channel_sections(self._channel_base)
            self.finished_signal.emit(sections, "")
        except Exception as e:
            self.finished_signal.emit([], str(e))


class DownloadWorker(QThread):
    """Thread pour lancer le téléchargement sans bloquer la GUI."""
    progress_signal = Signal(str, float, str)  # message, percent, status
    finished_signal = Signal(object)  # DownloadResult

    def __init__(
        self,
        urls: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._urls = urls

    def run(self) -> None:
        def callback(msg: str, pct: float, status: str) -> None:
            self.progress_signal.emit(msg, pct, status)

        result = run_download(self._urls, progress_callback=callback)
        self.finished_signal.emit(result)

    @property
    def urls(self) -> list[str]:
        return self._urls


class DownloadViewWidget(QWidget):
    """Widget principal : mode, URL, analyse, liste, téléchargement, progression."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sections: list[dict[str, Any]] = []
        self._worker: DownloadWorker | None = None
        self._analyze_worker: AnalyzeWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)

        # —— Étape 1 : Mode et source ——
        gb_mode = QGroupBox("1. Mode et source")
        ly_mode = QVBoxLayout(gb_mode)
        ly_mode.setSpacing(12)
        row_mode = QHBoxLayout()
        self._group_mode = QButtonGroup(self)
        self._rb_channel = QRadioButton("Chaîne YouTube (onglets / playlists)")
        self._rb_video = QRadioButton("Une vidéo (URL)")
        self._rb_channel.setChecked(True)
        self._group_mode.addButton(self._rb_channel)
        self._group_mode.addButton(self._rb_video)
        row_mode.addWidget(self._rb_channel)
        row_mode.addWidget(self._rb_video)
        ly_mode.addLayout(row_mode)
        layout.addWidget(gb_mode)

        # Bloc chaîne (URL + Analyser)
        gb_channel = QGroupBox("Chaîne")
        ly_channel = QVBoxLayout(gb_channel)
        row_channel = QHBoxLayout()
        lbl_channel = QLabel("URL ou @handle :")
        lbl_channel.setMinimumWidth(100)
        self._edit_channel = QLineEdit()
        self._edit_channel.setPlaceholderText("https://www.youtube.com/@... ou @NomDeLaChaîne")
        self._btn_analyze = QPushButton("Analyser la chaîne")
        self._btn_analyze.setProperty("class", "primary")
        self._btn_analyze.clicked.connect(self._on_analyze)
        row_channel.addWidget(lbl_channel)
        row_channel.addWidget(self._edit_channel, 1)
        row_channel.addWidget(self._btn_analyze)
        ly_channel.addLayout(row_channel)
        layout.addWidget(gb_channel)

        # Bloc vidéo (URL seule)
        gb_video = QGroupBox("Vidéo")
        gb_video.setEnabled(False)
        ly_video = QVBoxLayout(gb_video)
        row_video = QHBoxLayout()
        lbl_video = QLabel("URL de la vidéo :")
        lbl_video.setMinimumWidth(100)
        self._edit_video = QLineEdit()
        self._edit_video.setPlaceholderText("https://www.youtube.com/watch?v=...")
        row_video.addWidget(lbl_video)
        row_video.addWidget(self._edit_video, 1)
        ly_video.addLayout(row_video)
        layout.addWidget(gb_video)

        def toggle_mode() -> None:
            is_channel = self._rb_channel.isChecked()
            gb_channel.setEnabled(is_channel)
            gb_video.setEnabled(not is_channel)

        self._rb_channel.toggled.connect(toggle_mode)
        toggle_mode()

        # —— Étape 2 : Contenu disponible ——
        gb_content = QGroupBox("2. Contenu à télécharger")
        ly_content = QVBoxLayout(gb_content)
        ly_content.setSpacing(10)
        self._list_sections = QListWidget()
        self._list_sections.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list_sections.setMinimumHeight(140)
        self._apply_list_palette()
        ly_content.addWidget(self._list_sections)
        ly_sel = QHBoxLayout()
        self._btn_select_all = QPushButton("Tout sélectionner")
        self._btn_select_all.clicked.connect(self._select_all_sections)
        self._btn_deselect_all = QPushButton("Tout désélectionner")
        self._btn_deselect_all.clicked.connect(self._deselect_all_sections)
        ly_sel.addWidget(self._btn_select_all)
        ly_sel.addWidget(self._btn_deselect_all)
        ly_sel.addStretch()
        ly_content.addLayout(ly_sel)
        layout.addWidget(gb_content)

        # —— Bouton principal Télécharger ——
        ly_dl = QHBoxLayout()
        ly_dl.addStretch()
        self._btn_download = QPushButton("Télécharger la sélection")
        self._btn_download.setProperty("class", "success")
        self._btn_download.setMinimumHeight(40)
        self._btn_download.setMinimumWidth(220)
        self._btn_download.clicked.connect(self._on_download)
        ly_dl.addWidget(self._btn_download)
        ly_dl.addStretch()
        layout.addLayout(ly_dl)

        # —— Progression et log ——
        gb_progress = QGroupBox("Progression")
        ly_progress = QVBoxLayout(gb_progress)
        ly_progress.setSpacing(10)
        row_output = QHBoxLayout()
        row_output.addWidget(QLabel(f"Dossier : {OUTPUT_DIR}"))
        self._btn_open_folder = QPushButton("Ouvrir le dossier des téléchargements")
        self._btn_open_folder.clicked.connect(self._open_output_folder)
        row_output.addWidget(self._btn_open_folder)
        row_output.addStretch(1)
        ly_progress.addLayout(row_output)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setFormat("%p%")
        ly_progress.addWidget(self._progress_bar)
        log_label = QLabel("Journal :")
        log_label.setProperty("class", "muted")
        log_label.setStyleSheet("font-size: 11px;")
        ly_progress.addWidget(log_label)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(120)
        self._log.setMaximumHeight(200)
        ly_progress.addWidget(self._log)
        layout.addWidget(gb_progress)

        # —— Résumé (affiché après téléchargement) ——
        self._summary_frame = QFrame()
        self._summary_frame.setProperty("class", "summary")
        self._summary_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        ly_summary = QVBoxLayout(self._summary_frame)
        ly_summary.setContentsMargins(16, 12, 16, 12)
        ly_summary.setSpacing(8)
        summary_title = QLabel("Résumé du téléchargement")
        summary_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        ly_summary.addWidget(summary_title)
        self._lbl_summary = QLabel()
        self._lbl_summary.setWordWrap(True)
        self._lbl_summary.setProperty("class", "secondary")
        self._lbl_summary.setStyleSheet("font-size: 12px;")
        ly_summary.addWidget(self._lbl_summary)
        self._summary_frame.hide()
        layout.addWidget(self._summary_frame)

        layout.addStretch(1)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_list_palette()

    def _apply_list_palette(self) -> None:
        """Applique la palette du thème courant à la liste des sections (lisibilité en mode clair)."""
        app = QApplication.instance()
        if not app:
            return
        theme = get_effective_theme(app, get_theme_preference())
        c = get_theme_colors(theme)
        p = self._list_sections.palette()
        p.setColor(QPalette.ColorRole.Base, QColor(c["bg_input"]))
        p.setColor(QPalette.ColorRole.Text, QColor(c["text_primary"]))
        p.setColor(QPalette.ColorRole.Window, QColor(c["bg_input"]))
        self._list_sections.setPalette(p)

    def _open_output_folder(self) -> None:
        """Ouvre le dossier des téléchargements dans l'explorateur du système."""
        path_str = str(OUTPUT_DIR)
        if not OUTPUT_DIR.exists():
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
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

    def _on_analyze(self) -> None:
        url_or_handle = self._edit_channel.text().strip()
        if not url_or_handle:
            QMessageBox.warning(
                self,
                "Chaîne",
                "Saisissez une URL ou un @handle de chaîne YouTube.",
            )
            return
        channel_base = normalize_channel_url(url_or_handle)
        self._edit_channel.setText(channel_base)
        self._log.append(f"Analyse de la chaîne : {channel_base}…")
        self._btn_analyze.setEnabled(False)
        self._list_sections.clear()
        self._sections = []
        self._analyze_worker = AnalyzeWorker(channel_base, self)
        self._analyze_worker.finished_signal.connect(self._on_analyze_finished)
        self._analyze_worker.start()

    @Slot(list, str)
    def _on_analyze_finished(self, sections: list, error: str) -> None:
        self._analyze_worker = None
        self._btn_analyze.setEnabled(True)
        if error:
            self._log.append(f"Erreur : {error}")
            QMessageBox.warning(self, "Analyse", f"Erreur lors de l'analyse : {error}")
            return
        self._sections = sections
        for s in self._sections:
            count_str = f"{s['count']} vidéo(s)" if s["count"] >= 0 else "?"
            item = QListWidgetItem(f"{s['label']} — {count_str}")
            item.setData(Qt.ItemDataRole.UserRole, s)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._list_sections.addItem(item)
        self._log.append(f"Analyse terminée : {len(self._sections)} section(s).")
        # Avertissement comme dans la CLI : analyse échouée (ex. cookies invalides)
        if len(sections) >= 3 and all(s.get("count", 0) < 0 for s in sections[:3]):
            log_path = LOG_DIR / "extract_gui.log"
            QMessageBox.warning(
                self,
                "Analyse",
                "Problème lors de l'analyse (cookies invalides ? Deno ?).\n\n"
                f"Détails : {log_path}",
            )

    def _select_all_sections(self) -> None:
        for i in range(self._list_sections.count()):
            self._list_sections.item(i).setCheckState(Qt.CheckState.Checked)

    def _deselect_all_sections(self) -> None:
        for i in range(self._list_sections.count()):
            self._list_sections.item(i).setCheckState(Qt.CheckState.Unchecked)

    def _get_selected_urls(self) -> list[str]:
        urls: list[str] = []
        if self._rb_video.isChecked():
            url = self._edit_video.text().strip()
            if is_youtube_video_url(url):
                urls.append(url)
            return urls
        for i in range(self._list_sections.count()):
            item = self._list_sections.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                s = item.data(Qt.ItemDataRole.UserRole)
                if s and isinstance(s, dict) and "url" in s:
                    urls.append(s["url"])
        return urls

    def _on_download(self) -> None:
        urls = self._get_selected_urls()
        if not urls:
            if self._rb_video.isChecked():
                QMessageBox.warning(
                    self,
                    "Téléchargement",
                    "Saisissez une URL YouTube valide.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Téléchargement",
                    "Sélectionnez au moins une section (ou une vidéo en mode « Une vidéo »).",
                )
            return
        if self._worker and self._worker.isRunning():
            return
        self._summary_frame.hide()
        self._log.clear()
        self._log.append(f"Dossier de sortie : {OUTPUT_DIR}")
        self._log.append(f"Archive : {ARCHIVE_FILE}")
        self._log.append(f"{len(urls)} groupe(s) sélectionné(s). Démarrage…")
        self._progress_bar.setValue(0)
        self._progress_bar.setRange(0, 0)  # mode indéterminé pendant le dl
        self._btn_download.setEnabled(False)
        self._worker = DownloadWorker(urls, self)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_download_finished)
        self._worker.start()

    @Slot(str, float, str)
    def _on_progress(self, message: str, percent: float, status: str) -> None:
        # Retirer les codes ANSI résiduels pour l'affichage GUI
        clean = _strip_ansi(message)
        if status == "downloading":
            if percent >= 0:
                self._progress_bar.setRange(0, 100)
                # Arrondir pour que la barre bouge dès 0.5% (sinon 0.1%..0.9% = 0)
                self._progress_bar.setValue(round(percent))
            # Une seule ligne de progression (comme en CLI), pas des centaines de lignes
            if _is_progress_line(clean):
                # Afficher une décimale pour que 0.1%, 0.2%... soient visibles (sinon bloqué à 0%)
                pct_str = f"{percent:.1f}%" if percent >= 0 else "…"
                self._replace_last_log_line(f"  {pct_str} — téléchargement en cours…")
                # Forcer le rafraîchissement de l'UI (comme en CLI : mise à jour visible en direct)
                QApplication.processEvents()
                return
        if status == "finished":
            # Ne pas inonder le journal avec chaque chemin "finished" (fragments + merge)
            return
        if status == "video_done":
            # Une vidéo complète vient de se terminer (comme « ✔ Vidéo terminée » en CLI)
            self._log.append(clean)
            QApplication.processEvents()
            return
        if status == "already_on_disk":
            # Vidéo déjà présente dans downloads/ (pas dans l'archive) — comme en CLI
            self._log.append(clean)
            QApplication.processEvents()
            return
        if status == "already_in_archive":
            # Vidéo déjà dans archive.txt (éviter doublons) — comme en CLI
            self._log.append(clean)
            QApplication.processEvents()
            return
        if status == "error":
            # Erreur yt-dlp (échec d'une vidéo) : afficher dans le journal
            self._log.append("✖ Erreur : " + clean if clean else "✖ Erreur (voir résumé)")
            QApplication.processEvents()
            return
        self._log.append(clean)

    def _replace_last_log_line(self, new_line: str) -> None:
        """Remplace la dernière ligne du log par la nouvelle ligne de progression."""
        doc = self._log.document()
        last_block = doc.lastBlock()
        last_text = last_block.text().strip()
        if not last_text:
            self._log.append(new_line)
            return
        if not _is_progress_line(last_text):
            self._log.append(new_line)
            return
        cursor = self._log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.movePosition(cursor.MoveOperation.StartOfLine, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(new_line)
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()

    @Slot(object)
    def _on_download_finished(self, result: DownloadResult) -> None:
        self._worker = None
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(100)
        self._btn_download.setEnabled(True)
        # N'afficher "Téléchargement terminé" que si des vidéos ont été traitées (évite en cas d'erreur type cookies)
        if result.ok > 0 or result.skipped > 0 or result.error > 0:
            self._log.append("--- Téléchargement terminé ---")
        # Toujours afficher l'erreur dans le journal si présente (cookies invalides, bot, etc.)
        last_error = getattr(result, "last_error", "")
        if last_error:
            self._log.append("")
            self._log.append("⚠ Erreur : " + last_error)
            advice = get_error_advice(last_error)
            if advice:
                self._log.append(advice)
        try:
            archive_count = sum(
                1 for line in ARCHIVE_FILE.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ) if ARCHIVE_FILE.exists() else 0
        except Exception:
            archive_count = 0
        lines = [
            f"✔ Téléchargées : {result.ok}",
            f"⊙ En archive (session) : {result.skipped}",
            f"✖ Échecs : {result.error}",
            f"En archive (total) : {archive_count}",
        ]
        if result.ok == 0 and result.error == 0 and result.skipped == 0 and last_error:
            lines.append("")
            lines.append(f"⚠ Erreur : {last_error}")
            advice = get_error_advice(last_error)
            if advice:
                lines.append("")
                lines.append(advice)
        self._lbl_summary.setText("\n".join(lines))
        self._summary_frame.show()
