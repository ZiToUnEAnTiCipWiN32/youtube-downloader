"""Feuille de style globale pour une interface cohérente (thème clair ou sombre)."""
from __future__ import annotations

from typing import Any

try:
    from PySide6.QtWidgets import QApplication, QPushButton
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import QObject
except ImportError:
    QApplication = None  # type: ignore[misc, assignment]
    QPushButton = None  # type: ignore[misc, assignment]
    QPalette = None  # type: ignore[misc, assignment]
    QColor = None  # type: ignore[misc, assignment]
    QObject = None  # type: ignore[misc, assignment]

# Palettes par thème (clé → valeur CSS)
THEME_LIGHT: dict[str, str] = {
    "primary": "#2563eb",
    "success": "#16a34a",
    "warning": "#ca8a04",
    "error": "#dc2626",
    "bg_window": "#ffffff",
    "bg_card": "#f8fafc",
    "bg_input": "#ffffff",
    "bg_log": "#ffffff",
    "bg_button": "#e2e8f0",
    "bg_button_hover": "#cbd5e1",
    "bg_button_pressed": "#94a3b8",
    "bg_button_disabled": "#f1f5f9",
    "bg_list_hover": "#f1f5f9",
    "bg_progress": "#f1f5f9",
    "bg_menu_selected": "#e2e8f0",
    "bg_tab": "#e2e8f0",
    "bg_tab_hover": "#cbd5e1",
    "border": "#e2e8f0",
    "border_summary": "#cbd5e1",
    "text_primary": "#0f172a",
    "text_secondary": "#334155",
    "text_muted": "#64748b",
    "text_disabled": "#94a3b8",
    "radio_border": "#94a3b8",
    "radio_bg": "white",
}

THEME_DARK: dict[str, str] = {
    "primary": "#3b82f6",
    "success": "#22c55e",
    "warning": "#eab308",
    "error": "#ef4444",
    "bg_window": "#0f172a",
    "bg_card": "#1e293b",
    "bg_input": "#334155",
    "bg_log": "#1e293b",
    "bg_button": "#475569",
    "bg_button_hover": "#64748b",
    "bg_button_pressed": "#94a3b8",
    "bg_button_disabled": "#334155",
    "bg_list_hover": "#334155",
    "bg_progress": "#334155",
    "bg_menu_selected": "#475569",
    "bg_tab": "#334155",
    "bg_tab_hover": "#475569",
    "border": "#475569",
    "border_summary": "#64748b",
    "text_primary": "#f1f5f9",
    "text_secondary": "#e2e8f0",
    "text_muted": "#94a3b8",
    "text_disabled": "#64748b",
    "radio_border": "#64748b",
    "radio_bg": "#334155",
}


def _build_stylesheet(c: dict[str, str]) -> str:
    """Construit la feuille de style à partir d'un dictionnaire de couleurs."""
    return f"""
    /* Fenêtre et fond */
    QMainWindow, QWidget {{
        background-color: {c["bg_window"]};
    }}

    /* Labels par défaut (suit le thème) */
    QLabel {{
        color: {c["text_primary"]};
    }}
    QLabel[class="muted"] {{
        color: {c["text_muted"]};
    }}
    QLabel[class="secondary"] {{
        color: {c["text_secondary"]};
    }}

    /* Menu contextuel */
    QMenu {{
        background: {c["bg_window"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        color: {c["text_primary"]};
    }}
    QMenu::item:selected {{
        background: {c["bg_menu_selected"]};
        color: {c["text_primary"]};
    }}

    /* Onglets */
    QTabWidget::pane {{
        border: 1px solid {c["border"]};
        border-radius: 8px;
        top: -1px;
        padding: 16px;
        background: {c["bg_card"]};
    }}
    QTabBar::tab {{
        background: {c["bg_tab"]};
        color: {c["text_muted"]};
        padding: 10px 20px;
        margin-right: 4px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background: {c["bg_card"]};
        color: {c["primary"]};
        border: 1px solid {c["border"]};
        border-bottom: none;
    }}
    QTabBar::tab:hover:!selected {{
        background: {c["bg_tab_hover"]};
    }}

    /* GroupBox */
    QGroupBox {{
        font-weight: 600;
        font-size: 11px;
        color: {c["text_muted"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        background: {c["bg_card"]};
        color: {c["text_secondary"]};
    }}
    QGroupBox QRadioButton {{
        color: {c["text_primary"]};
    }}
    QGroupBox QLabel {{
        color: {c["text_secondary"]};
    }}

    /* Boutons */
    QPushButton {{
        background: {c["bg_button"]};
        color: {c["text_secondary"]};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background: {c["bg_button_hover"]};
    }}
    QPushButton:pressed {{
        background: {c["bg_button_pressed"]};
    }}
    QPushButton:disabled {{
        background: {c["bg_button_disabled"]};
        color: {c["text_disabled"]};
    }}
    QPushButton[class="primary"] {{
        background: {c["primary"]};
        color: white;
    }}
    QPushButton[class="primary"]:hover {{
        background: #1d4ed8;
        color: white;
    }}
    QPushButton[class="primary"]:pressed {{
        background: #1e40af;
        color: white;
    }}
    QPushButton[class="success"] {{
        background: {c["success"]};
        color: white;
    }}
    QPushButton[class="success"]:hover {{
        background: #15803d;
        color: white;
    }}
    QPushButton[class="success"]:pressed {{
        background: #166534;
        color: white;
    }}

    /* Champs de saisie */
    QLineEdit {{
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 8px 12px;
        background: {c["bg_input"]};
        color: {c["text_primary"]};
        selection-background-color: {c["primary"]};
        selection-color: white;
        font-size: 11px;
    }}
    QLineEdit:focus {{
        border-color: {c["primary"]};
    }}

    /* Combo (thème, etc.) */
    QComboBox {{
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 8px 12px;
        background: {c["bg_input"]};
        color: {c["text_primary"]};
        font-size: 11px;
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {c["border"]};
    }}
    QComboBox::drop-down {{
        border: none;
        background: transparent;
    }}
    QComboBox QAbstractItemView {{
        background: {c["bg_input"]};
        color: {c["text_primary"]};
        selection-background-color: {c["bg_list_hover"]};
        selection-color: {c["text_primary"]};
        padding: 4px;
        border: 1px solid {c["border"]};
        border-radius: 6px;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 8px 12px;
        background: {c["bg_input"]};
        color: {c["text_primary"]};
        min-height: 24px;
    }}
    QComboBox QAbstractItemView::item:selected {{
        background: {c["bg_list_hover"]};
        color: {c["text_primary"]};
    }}

    /* Liste */
    QListWidget {{
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 4px;
        background: {c["bg_input"]};
        color: {c["text_primary"]};
        font-size: 11px;
    }}
    QListWidget::item {{
        padding: 8px;
        border-radius: 4px;
        background: {c["bg_input"]};
        color: {c["text_primary"]};
    }}
    QListWidget::item:hover {{
        background: {c["bg_list_hover"]};
        color: {c["text_primary"]};
    }}
    QListWidget::item:selected {{
        background: {c["bg_list_hover"]};
        color: {c["text_primary"]};
    }}
    QListWidget::item:checked {{
        background: {c["bg_list_hover"]};
        color: {c["text_primary"]};
    }}

    /* Barre de progression */
    QProgressBar {{
        border: 1px solid {c["border"]};
        border-radius: 6px;
        text-align: center;
        background: {c["bg_progress"]};
        height: 24px;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c["primary"]}, stop:1 #60a5fa);
        border-radius: 5px;
    }}

    /* Zone de log */
    QTextEdit {{
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 10px;
        background: {c["bg_log"]};
        color: {c["text_primary"]};
        font-family: "Consolas", "Cascadia Code", "Segoe UI", monospace;
        font-size: 11px;
    }}

    /* Radio */
    QRadioButton {{
        spacing: 8px;
        color: {c["text_primary"]};
        font-weight: 500;
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 2px solid {c["radio_border"]};
        background: {c["radio_bg"]};
    }}
    QRadioButton::indicator:checked {{
        border: 2px solid {c["primary"]};
        background: {c["primary"]};
    }}

    /* StatusBar */
    QStatusBar {{
        background: {c["bg_card"]};
        color: {c["text_muted"]};
        border-top: 1px solid {c["border"]};
        padding: 4px 8px;
    }}

    /* Frame résumé */
    QFrame[class="summary"] {{
        background: {c["bg_card"]};
        border: 1px solid {c["border_summary"]};
        border-left: 4px solid {c["success"]};
        border-radius: 6px;
        padding: 14px 16px;
    }}
    QFrame[class="summary"] QLabel {{
        color: {c["text_secondary"]};
        font-size: 12px;
    }}

    /* Boîtes de dialogue */
    QMessageBox {{
        background: {c["bg_window"]};
    }}
    QMessageBox QLabel {{
        color: {c["text_primary"]};
        font-size: 12px;
        min-width: 320px;
    }}
    QMessageBox QPushButton {{
        min-width: 80px;
    }}
"""


def get_stylesheet(theme: str = "light") -> str:
    """Retourne la feuille de style pour le thème demandé (« light » ou « dark »)."""
    if theme == "dark":
        return _build_stylesheet(THEME_DARK)
    return _build_stylesheet(THEME_LIGHT)


def get_theme_colors(theme: str = "light") -> dict[str, str]:
    """Retourne le dictionnaire de couleurs du thème (pour palette, etc.)."""
    if theme == "dark":
        return dict(THEME_DARK)
    return dict(THEME_LIGHT)


def get_system_theme(app: Any) -> str:
    """
    Retourne « dark » si le thème système est sombre, sinon « light ».
    Nécessite que QApplication soit déjà créée (Qt 6.5+ pour colorScheme).
    """
    try:
        from PySide6.QtCore import Qt
        hints = app.styleHints()
        if hints is not None and hasattr(hints, "colorScheme"):
            if hints.colorScheme() == Qt.ColorScheme.Dark:
                return "dark"
    except Exception:
        pass
    return "light"


def get_theme_preference() -> str:
    """Retourne la préférence utilisateur : « system », « light » ou « dark » (QSettings)."""
    try:
        from PySide6.QtCore import QSettings
        return (QSettings().value("theme", "system") or "system").strip().lower()
    except Exception:
        return "system"


def set_theme_preference(value: str) -> None:
    """Enregistre la préférence thème (« system », « light » ou « dark »)."""
    try:
        from PySide6.QtCore import QSettings
        v = (value or "system").strip().lower()
        if v not in ("system", "light", "dark"):
            v = "system"
        QSettings().setValue("theme", v)
    except Exception:
        pass


def get_effective_theme(app: Any, preference: str) -> str:
    """Retourne le thème effectif : si preference est « system », suit le système ; sinon light/dark."""
    if (preference or "").strip().lower() == "dark":
        return "dark"
    if (preference or "").strip().lower() == "light":
        return "light"
    return get_system_theme(app)


def apply_button_palette(root: Any, theme: str) -> None:
    """
    Applique la palette (couleur de texte) aux boutons primary/success pour éviter
    le texte doublé en mode sombre (Fusion dessine une fois avec la palette).
    """
    if QPushButton is None or QPalette is None or QColor is None or root is None:
        return
    try:
        c = get_theme_colors(theme)
        white = QColor("#ffffff")
        for btn in root.findChildren(QPushButton):
            cls = (btn.property("class") or "").strip()
            if cls == "primary":
                p = btn.palette()
                p.setColor(QPalette.ColorRole.Button, QColor(c["primary"]))
                p.setColor(QPalette.ColorRole.ButtonText, white)
                btn.setPalette(p)
            elif cls == "success":
                p = btn.palette()
                p.setColor(QPalette.ColorRole.Button, QColor(c["success"]))
                p.setColor(QPalette.ColorRole.ButtonText, white)
                btn.setPalette(p)
    except Exception:
        pass


# Rétrocompatibilité : thème clair par défaut
APP_STYLESHEET = get_stylesheet("light")
