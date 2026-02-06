"""Fenêtre principale : onglets Prérequis et Téléchargement."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStatusBar,
    QLabel,
    QFrame,
    QMenuBar,
    QMenu,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction

from src.core.paths import OUTPUT_DIR
from .prerequisites import PrerequisitesWidget
from .download_view import DownloadViewWidget
from .maintenance_view import MaintenanceWidget
from .about_dialog import show_about_dialog


class MainWindow(QMainWindow):
    """Fenêtre principale avec onglets Prérequis et Téléchargement."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("YouTube Downloader By ZiToUnE-AnTiCip-WiN32")
        self.setMinimumSize(900, 720)
        self.resize(1280, 800)

        # Menu Aide → À propos
        menu_bar = QMenuBar(self)
        menu_aide = QMenu("Aide", self)
        action_about = QAction("À propos", self)
        action_about.triggered.connect(lambda: show_about_dialog(self))
        menu_aide.addAction(action_about)
        menu_aide.aboutToHide.connect(self._restore_status_message)
        menu_bar.addMenu(menu_aide)
        self.setMenuBar(menu_bar)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # En-tête discret
        header = QFrame()
        header.setFrameShape(QFrame.Shape.NoFrame)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        title = QLabel("YouTube Downloader By ZiToUnE-AnTiCip-WiN32")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        subtitle = QLabel("Téléchargez des vidéos par chaîne Youtube ou par URL")
        subtitle.setProperty("class", "muted")
        subtitle.setStyleSheet("font-size: 11px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(PrerequisitesWidget(self), "  Prérequis  ")
        tabs.addTab(DownloadViewWidget(self), "  Télécharger  ")
        tabs.addTab(MaintenanceWidget(self), "  Maintenance  ")
        layout.addWidget(tabs)

        self._status_message = f"Dossier de sortie : {OUTPUT_DIR}"
        status = QStatusBar()
        status.showMessage(self._status_message)
        self.setStatusBar(status)

    def _restore_status_message(self) -> None:
        """Réaffiche le message de la barre de statut (après fermeture du menu Aide)."""
        if self.statusBar():
            self.statusBar().showMessage(self._status_message)
