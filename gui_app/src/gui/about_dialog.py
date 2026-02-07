"""Fenêtre « À propos » : auteur, liens, licence."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt

from src import __version__ as APP_VERSION

ABOUT_TITLE = "YouTube-Downloader By ZiToUnE-AnTiCip-WiN32"
ABOUT_LINKS = [
    ("Site", "http://zitouneanticip.free.fr/"),
    ("GitHub", "https://github.com/ZiToUnEAnTiCipWiN32"),
    ("YouTube", "https://www.youtube.com/@Zitoune-anticip-WIN32"),
    ("Twitch", "https://www.twitch.tv/zitouneanticip"),
]
ABOUT_YEAR = "© 2026"
ABOUT_LICENSE = "MIT License"


def show_about_dialog(parent=None) -> None:
    """Affiche la fenêtre À propos (auteur, version, liens, licence)."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("À propos")
    dialog.setMinimumWidth(420)
    layout = QVBoxLayout(dialog)
    layout.setSpacing(12)

    title = QLabel(ABOUT_TITLE)
    title.setStyleSheet("font-weight: 700; font-size: 14px;")
    title.setWordWrap(True)
    layout.addWidget(title)

    version = QLabel(f"Version {APP_VERSION}")
    version.setProperty("class", "muted")
    version.setStyleSheet("font-size: 11px;")
    layout.addWidget(version)

    links_html = " · ".join(
        f'<a href="{url}">{label}</a>' for label, url in ABOUT_LINKS
    )
    links = QLabel(links_html)
    links.setOpenExternalLinks(True)
    links.setTextFormat(Qt.TextFormat.RichText)
    links.setWordWrap(True)
    links.setStyleSheet("font-size: 11px;")
    layout.addWidget(links)

    year = QLabel(ABOUT_YEAR)
    year.setProperty("class", "muted")
    year.setStyleSheet("font-size: 11px;")
    layout.addWidget(year)

    license_lbl = QLabel(ABOUT_LICENSE)
    license_lbl.setProperty("class", "muted")
    license_lbl.setStyleSheet("font-size: 10px;")
    layout.addWidget(license_lbl)

    bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    bbox.accepted.connect(dialog.accept)
    layout.addWidget(bbox)

    dialog.exec()
