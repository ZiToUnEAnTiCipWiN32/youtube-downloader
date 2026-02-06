"""Point d'entrée de l'application PySide6 (appelé par start.py après bootstrap)."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .gui.main_window import MainWindow
from .gui.styles import (
    get_stylesheet,
    get_theme_preference,
    get_effective_theme,
    apply_button_palette,
)


def run_app() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Downloader By ZiToUnE-AnTiCip-WiN32")
    app.setApplicationDisplayName("YouTube Downloader By ZiToUnE-AnTiCip-WiN32")
    app.setStyle("Fusion")
    pref = get_theme_preference()
    theme = get_effective_theme(app, pref)
    app.setStyleSheet(get_stylesheet(theme))
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = MainWindow()
    theme = get_effective_theme(app, get_theme_preference())
    apply_button_palette(window, theme)
    window.show()
    sys.exit(app.exec())
