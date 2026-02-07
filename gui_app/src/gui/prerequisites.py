"""Onglet Prérequis : vérification Deno, ffmpeg, cookies ; installation depuis la GUI."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QGroupBox,
    QFrame,
    QMessageBox,
    QProgressDialog,
    QScrollArea,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMenu,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from src.core.paths import SCRIPT_DIR, ARCHIVE_FILE, COOKIE_FILE, COOKIE_FILE_ENCRYPTED
from src.core.cookies import (
    has_cookies_source,
    has_cookies_enc_only,
    cookies_file_valid,
    encrypt_cookies_to_file,
)


def check_deno() -> bool:
    return shutil.which("deno") is not None


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def check_cookies() -> bool:
    return has_cookies_source()


def check_winget() -> bool:
    """True si winget est disponible (installation via l'app)."""
    return shutil.which("winget") is not None


DENO_WINGET = 'winget install DenoLand.Deno --accept-source-agreements --accept-package-agreements'
FFMPEG_WINGET = 'winget install "FFmpeg (Essentials Build)" --accept-source-agreements --accept-package-agreements'

# Aide cookies : extensions par navigateur (format Netscape)
COOKIES_HELP_FIREFOX = "https://addons.mozilla.org/fr/firefox/addon/cookies-txt/"
COOKIES_HELP_CHROME = "https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
COOKIES_HELP_EDGE = "https://microsoftedge.microsoft.com/addons/detail/get-cookiestxt-locally/bhnfahfjghjkhaopjhnhjjjmgjkfhhhj"


class InstallWorker(QThread):
    """Thread pour lancer winget (ffmpeg) sans bloquer la GUI."""
    finished_signal = Signal(bool, str)

    def __init__(self, command: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._command = command

    def run(self) -> None:
        try:
            proc = subprocess.run(
                self._command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
                errors="replace",
            )
            self.finished_signal.emit(proc.returncode == 0, proc.stderr or proc.stdout or "")
        except subprocess.TimeoutExpired:
            self.finished_signal.emit(False, "Délai dépassé.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


def _status_badge(ok: bool) -> str:
    """Retourne un court libellé de statut pour affichage."""
    return "Installé" if ok else "Non trouvé"


class PrerequisitesWidget(QWidget):
    """Widget d'état des prérequis et actions (vérifier, installer)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: InstallWorker | None = None
        self._progress: QProgressDialog | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content = QWidget()
        content.setMinimumWidth(1200)
        layout = QVBoxLayout(content)
        layout.setSpacing(20)

        intro = QLabel(
            "Vérifiez que les outils recommandés sont installés. Deno et ffmpeg améliorent la compatibilité YouTube et la fusion audio/vidéo. "
            "L'installation via winget nécessite que winget soit installé (Windows 10/11)."
        )
        intro.setWordWrap(True)
        intro.setProperty("class", "muted")
        intro.setStyleSheet("font-size: 11px; padding: 4px 0;")
        layout.addWidget(intro)

        # Indicateur winget (pour les boutons « Installer via winget »)
        row_winget = QHBoxLayout()
        row_winget.addWidget(QLabel("winget :"))
        self._lbl_winget_status = QLabel()
        self._lbl_winget_status.setStyleSheet("font-weight: 600; min-width: 100px;")
        row_winget.addWidget(self._lbl_winget_status)
        row_winget.addStretch(1)
        layout.addLayout(row_winget)

        # Deno
        gb_deno = QGroupBox("Deno — runtime JavaScript pour YouTube")
        ly_deno = QVBoxLayout(gb_deno)
        ly_deno.setSpacing(10)
        row_deno = QHBoxLayout()
        self._lbl_deno_status = QLabel()
        self._lbl_deno_status.setStyleSheet("font-weight: 600; min-width: 80px;")
        self._lbl_deno = QLabel()
        self._lbl_deno.setWordWrap(True)
        self._lbl_deno.setProperty("class", "secondary")
        self._lbl_deno.setStyleSheet("font-size: 11px;")
        row_deno.addWidget(self._lbl_deno_status)
        row_deno.addWidget(self._lbl_deno, 1)
        ly_deno.addLayout(row_deno)
        h_deno = QHBoxLayout()
        btn_deno_check = QPushButton("Vérifier")
        btn_deno_check.clicked.connect(self._refresh_deno)
        self._btn_deno_install = QPushButton("Installer via winget")
        self._btn_deno_install.setProperty("class", "primary")
        self._btn_deno_install.clicked.connect(self._install_deno)
        self._btn_deno_install.setToolTip("Désactivé si winget n'est pas disponible.")
        h_deno.addWidget(btn_deno_check)
        h_deno.addWidget(self._btn_deno_install)
        ly_deno.addLayout(h_deno)
        layout.addWidget(gb_deno)

        # ffmpeg
        gb_ffmpeg = QGroupBox("ffmpeg — fusion audio/vidéo")
        ly_ffmpeg = QVBoxLayout(gb_ffmpeg)
        ly_ffmpeg.setSpacing(10)
        row_ffmpeg = QHBoxLayout()
        self._lbl_ffmpeg_status = QLabel()
        self._lbl_ffmpeg_status.setStyleSheet("font-weight: 600; min-width: 80px;")
        self._lbl_ffmpeg = QLabel()
        self._lbl_ffmpeg.setWordWrap(True)
        self._lbl_ffmpeg.setProperty("class", "secondary")
        self._lbl_ffmpeg.setStyleSheet("font-size: 11px;")
        row_ffmpeg.addWidget(self._lbl_ffmpeg_status)
        row_ffmpeg.addWidget(self._lbl_ffmpeg, 1)
        ly_ffmpeg.addLayout(row_ffmpeg)
        h_ffmpeg = QHBoxLayout()
        btn_ffmpeg_check = QPushButton("Vérifier")
        btn_ffmpeg_check.clicked.connect(self._refresh_ffmpeg)
        self._btn_ffmpeg_install = QPushButton("Installer via winget")
        self._btn_ffmpeg_install.setProperty("class", "primary")
        self._btn_ffmpeg_install.clicked.connect(self._install_ffmpeg)
        self._btn_ffmpeg_install.setToolTip("Désactivé si winget n'est pas disponible.")
        h_ffmpeg.addWidget(btn_ffmpeg_check)
        h_ffmpeg.addWidget(self._btn_ffmpeg_install)
        ly_ffmpeg.addLayout(h_ffmpeg)
        layout.addWidget(gb_ffmpeg)

        # Cookies
        gb_cookies = QGroupBox("Cookies YouTube (recommandé)")
        ly_cookies = QVBoxLayout(gb_cookies)
        ly_cookies.setSpacing(10)
        row_cookies = QHBoxLayout()
        self._lbl_cookies_status = QLabel()
        self._lbl_cookies_status.setStyleSheet("font-weight: 600; min-width: 80px;")
        self._lbl_cookies = QLabel()
        self._lbl_cookies.setWordWrap(True)
        self._lbl_cookies.setProperty("class", "secondary")
        self._lbl_cookies.setStyleSheet("font-size: 11px;")
        row_cookies.addWidget(self._lbl_cookies_status)
        row_cookies.addWidget(self._lbl_cookies, 1)
        ly_cookies.addLayout(row_cookies)
        row_btns = QHBoxLayout()
        btn_cookies = QPushButton("Vérifier")
        btn_cookies.clicked.connect(self._refresh_cookies)
        btn_cookies_help = QPushButton("Comment obtenir cookies.txt")
        btn_cookies_help.setProperty("class", "primary")
        btn_cookies_help.clicked.connect(self._show_cookies_help)
        btn_import_browser = QPushButton("Importer depuis le navigateur (beta)")
        btn_import_browser.clicked.connect(self._import_cookies_from_browser)
        # Menu « Gérer les cookies » pour alléger l’interface
        self._btn_manage_cookies = QPushButton("Gérer les cookies")
        self._btn_manage_cookies.setToolTip("Ouvrir l’emplacement, chiffrer, mot de passe, supprimer…")
        self._menu_cookies = QMenu(self)
        self._menu_cookies.addAction("Ouvrir l'emplacement pour cookies.txt", self._open_cookies_folder)
        self._menu_cookies.addAction("Chiffrer cookies.txt en cookies.enc", self._encrypt_cookies)
        self._act_password_enc = self._menu_cookies.addAction(
            "Définir le mot de passe pour cookies.enc", self._set_password_cookies_enc
        )
        self._menu_cookies.addSeparator()
        self._menu_cookies.addAction("Supprimer cookies.txt", self._on_delete_cookies_txt)
        self._menu_cookies.addAction("Supprimer cookies.enc", self._on_delete_cookies_enc)

        def _show_cookies_menu():
            self._menu_cookies.exec(self._btn_manage_cookies.mapToGlobal(self._btn_manage_cookies.rect().bottomLeft()))

        self._btn_manage_cookies.clicked.connect(_show_cookies_menu)
        row_btns.addWidget(btn_cookies)
        row_btns.addWidget(btn_cookies_help)
        row_btns.addWidget(btn_import_browser)
        row_btns.addWidget(self._btn_manage_cookies)
        ly_cookies.addLayout(row_btns)
        layout.addWidget(gb_cookies)

        # Archive (éviter les doublons)
        gb_archive = QGroupBox("Archive — éviter les doublons")
        ly_archive = QVBoxLayout(gb_archive)
        ly_archive.setSpacing(10)
        self._lbl_archive_path = QLabel()
        self._lbl_archive_path.setProperty("class", "secondary")
        self._lbl_archive_path.setStyleSheet("font-size: 11px;")
        self._lbl_archive_path.setText(str(ARCHIVE_FILE))
        self._lbl_archive_path.setWordWrap(True)
        ly_archive.addWidget(self._lbl_archive_path)
        row_archive = QHBoxLayout()
        self._lbl_archive_count = QLabel()
        self._lbl_archive_count.setProperty("class", "secondary")
        self._lbl_archive_count.setStyleSheet("font-size: 11px;")
        row_archive.addWidget(self._lbl_archive_count)
        row_archive.addStretch()
        ly_archive.addLayout(row_archive)
        btn_delete_archive = QPushButton("Supprimer archive.txt")
        btn_delete_archive.setToolTip("Réinitialiser l'archive : les prochains téléchargements pourront retélécharger des vidéos déjà enregistrées.")
        btn_delete_archive.clicked.connect(self._on_delete_archive)
        ly_archive.addWidget(btn_delete_archive)
        layout.addWidget(gb_archive)

        layout.addStretch(1)
        btn_refresh_all = QPushButton("Tout vérifier")
        btn_refresh_all.setProperty("class", "success")
        btn_refresh_all.setMinimumHeight(36)
        btn_refresh_all.clicked.connect(self.refresh_all)
        layout.addWidget(btn_refresh_all)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        self.refresh_all()

    def _refresh_winget(self) -> None:
        ok = check_winget()
        self._lbl_winget_status.setText("Disponible" if ok else "Non disponible")
        self._lbl_winget_status.setStyleSheet(
            f"font-weight: 600; min-width: 100px; color: {'#16a34a' if ok else '#ca8a04'};"
        )

    def _refresh_deno(self) -> None:
        ok = check_deno()
        self._lbl_deno_status.setText(_status_badge(ok))
        self._lbl_deno_status.setStyleSheet(
            f"font-weight: 600; min-width: 80px; color: {'#16a34a' if ok else '#ca8a04'};"
        )
        winget_ok = check_winget()
        self._btn_deno_install.setEnabled(not ok and winget_ok)
        if ok:
            self._lbl_deno.setText("Deno est disponible dans le PATH.")
        else:
            self._lbl_deno.setText(
                "YouTube peut en avoir besoin pour certains défis. Installez via winget ou manuellement, puis redémarrez l'application."
            )

    def _refresh_ffmpeg(self) -> None:
        ok = check_ffmpeg()
        self._lbl_ffmpeg_status.setText(_status_badge(ok))
        self._lbl_ffmpeg_status.setStyleSheet(
            f"font-weight: 600; min-width: 80px; color: {'#16a34a' if ok else '#ca8a04'};"
        )
        winget_ok = check_winget()
        self._btn_ffmpeg_install.setEnabled(not ok and winget_ok)
        if ok:
            self._lbl_ffmpeg.setText("ffmpeg est disponible dans le PATH.")
        else:
            self._lbl_ffmpeg.setText(
                "Sans ffmpeg, certains téléchargements peuvent échouer ou rester en audio seul. "
                "Installez via winget ou manuellement."
            )

    def _refresh_cookies(self) -> None:
        ok = check_cookies()
        enc_only = has_cookies_enc_only()
        if ok:
            status = "Configuré"
            color = "#16a34a"
            self._lbl_cookies.setText("Une source de cookies est configurée (cookies.txt ou cookies.enc).")
        elif enc_only:
            status = "Mot de passe requis"
            color = "#ca8a04"
            self._lbl_cookies.setText(
                "cookies.enc est présent. Définissez le mot de passe pour l'utiliser (bouton ci‑dessous)."
            )
        else:
            status = "Non configuré"
            color = "#ca8a04"
            self._lbl_cookies.setText(
                f"Placez cookies.txt (Netscape) dans : {SCRIPT_DIR} — ou cookies.enc avec YT_COOKIES_PASSWORD / YT_COOKIES_KEY."
            )
        self._lbl_cookies_status.setText(status)
        self._lbl_cookies_status.setStyleSheet(
            f"font-weight: 600; min-width: 80px; color: {color};"
        )
        self._act_password_enc.setVisible(enc_only)

    def _on_delete_cookies_txt(self) -> None:
        """Demande confirmation puis supprime cookies.txt."""
        if not COOKIE_FILE.exists():
            QMessageBox.information(self, "Cookies", "Le fichier cookies.txt n'existe pas.")
            return
        reply = QMessageBox.question(
            self,
            "Supprimer cookies.txt",
            "Supprimer cookies.txt ?\n\nLes téléchargements ne pourront plus utiliser ces cookies tant qu'une autre source (cookies.enc ou nouvel import) n'est pas configurée.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            COOKIE_FILE.unlink()
            self._refresh_cookies()
            QMessageBox.information(self, "Cookies", "cookies.txt a été supprimé.")
        except Exception as e:
            QMessageBox.warning(self, "Cookies", f"Impossible de supprimer le fichier : {e}")

    def _on_delete_cookies_enc(self) -> None:
        """Demande confirmation puis supprime cookies.enc."""
        if not COOKIE_FILE_ENCRYPTED.exists():
            QMessageBox.information(self, "Cookies", "Le fichier cookies.enc n'existe pas.")
            return
        reply = QMessageBox.question(
            self,
            "Supprimer cookies.enc",
            "Supprimer cookies.enc ?\n\nLes téléchargements ne pourront plus utiliser ces cookies tant qu'une autre source (cookies.txt ou nouvel import/chiffrement) n'est pas configurée.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            COOKIE_FILE_ENCRYPTED.unlink()
            if "YT_COOKIES_PASSWORD" in os.environ:
                del os.environ["YT_COOKIES_PASSWORD"]
            self._refresh_cookies()
            QMessageBox.information(self, "Cookies", "cookies.enc a été supprimé.")
        except Exception as e:
            QMessageBox.warning(self, "Cookies", f"Impossible de supprimer le fichier : {e}")

    def _open_cookies_folder(self) -> None:
        """Ouvre dans l'explorateur le dossier où placer cookies.txt (même dossier que l'exe en PyInstaller)."""
        path_str = str(SCRIPT_DIR)
        try:
            if not SCRIPT_DIR.exists():
                SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(path_str)
            elif sys.platform == "darwin":
                subprocess.run(["open", path_str], check=False)
            else:
                subprocess.run(["xdg-open", path_str], check=False)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Cookies",
                f"Impossible d'ouvrir le dossier : {e}",
            )

    def _set_password_cookies_enc(self) -> None:
        """Demande le mot de passe et définit YT_COOKIES_PASSWORD pour la session (cookies.enc déjà présent)."""
        if not COOKIE_FILE_ENCRYPTED.exists():
            QMessageBox.information(self, "Cookies", "Le fichier cookies.enc n'existe pas.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Définir le mot de passe pour cookies.enc")
        dialog.setMinimumWidth(380)
        layout_d = QVBoxLayout(dialog)
        form = QFormLayout()
        edit_pwd = QLineEdit()
        edit_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        edit_pwd.setPlaceholderText("Mot de passe utilisé pour chiffrer cookies.enc")
        form.addRow("Mot de passe :", edit_pwd)
        edit_confirm = QLineEdit()
        edit_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        edit_confirm.setPlaceholderText("Confirmer le mot de passe")
        form.addRow("Confirmer :", edit_confirm)
        layout_d.addLayout(form)
        note = QLabel(
            "Utilisez le mot de passe qui a servi à créer cookies.enc. Il sera enregistré pour cette session uniquement."
        )
        note.setWordWrap(True)
        note.setProperty("class", "muted")
        note.setStyleSheet("font-size: 10px;")
        layout_d.addWidget(note)
        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bbox.accepted.connect(dialog.accept)
        bbox.rejected.connect(dialog.reject)
        layout_d.addWidget(bbox)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        pwd = edit_pwd.text().strip()
        confirm = edit_confirm.text().strip()
        if not pwd:
            QMessageBox.warning(self, "Cookies", "Mot de passe vide.")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Cookies", "Les deux mots de passe ne correspondent pas.")
            return
        os.environ["YT_COOKIES_PASSWORD"] = pwd
        self._refresh_cookies()
        QMessageBox.information(
            self,
            "Cookies",
            "Mot de passe défini pour cette session.\n\nLes téléchargements utiliseront cookies.enc sans redémarrer l'application.\n"
            "Pour les prochains lancements, redéfinissez le mot de passe ici ou configurez YT_COOKIES_PASSWORD.",
        )

    def _refresh_archive(self) -> None:
        """Met à jour l'affichage du nombre d'entrées dans l'archive."""
        if not ARCHIVE_FILE.exists():
            self._lbl_archive_count.setText("Aucune entrée pour l'instant.")
            self._lbl_archive_count.setToolTip("Le fichier archive.txt est créé au premier téléchargement.")
            return
        self._lbl_archive_count.setToolTip("")
        try:
            text = ARCHIVE_FILE.read_text(encoding="utf-8")
            count = sum(1 for line in text.splitlines() if line.strip())
            self._lbl_archive_count.setToolTip("")
            self._lbl_archive_count.setText(f"{count} vidéo(s) en archive.")
        except Exception:
            self._lbl_archive_count.setToolTip("")
            self._lbl_archive_count.setText("Impossible de lire l'archive.")

    def _on_delete_archive(self) -> None:
        """Demande confirmation puis supprime archive.txt."""
        if not ARCHIVE_FILE.exists():
            QMessageBox.information(
                self,
                "Archive",
                "Le fichier archive.txt n'existe pas.",
            )
            return
        try:
            count = sum(1 for line in ARCHIVE_FILE.read_text(encoding="utf-8").splitlines() if line.strip())
        except Exception:
            count = 0
        msg = (
            "Supprimer l'archive ?\n\n"
            "Les prochains téléchargements pourront retélécharger des vidéos déjà enregistrées. "
            "Les fichiers déjà dans downloads/ ne seront pas supprimés."
        )
        if count > 0:
            msg = f"{count} vidéo(s) sont actuellement en archive.\n\n" + msg
        reply = QMessageBox.question(
            self,
            "Supprimer archive.txt",
            msg,
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            ARCHIVE_FILE.unlink()
            self._refresh_archive()
            QMessageBox.information(
                self,
                "Archive",
                "L'archive a été supprimée.",
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Archive",
                f"Impossible de supprimer le fichier : {e}",
            )

    def _install_deno(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._install_tool = "deno"
        self._progress = QProgressDialog("Installation de Deno via winget…", None, 0, 0, self)
        self._progress.setWindowTitle("Installation")
        self._progress.setMinimumDuration(0)
        self._progress.show()
        self._worker = InstallWorker(DENO_WINGET, self)
        self._worker.finished_signal.connect(self._on_install_finished)
        self._worker.start()

    def _install_ffmpeg(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._install_tool = "ffmpeg"
        self._progress = QProgressDialog("Installation de ffmpeg via winget…", None, 0, 0, self)
        self._progress.setWindowTitle("Installation")
        self._progress.setMinimumDuration(0)
        self._progress.show()
        self._worker = InstallWorker(FFMPEG_WINGET, self)
        self._worker.finished_signal.connect(self._on_install_finished)
        self._worker.start()

    def _on_install_finished(self, success: bool, message: str) -> None:
        if self._progress:
            self._progress.close()
            self._progress = None
        tool = getattr(self, "_install_tool", "ffmpeg")
        if success:
            QMessageBox.information(
                self,
                "Installation",
                f"{'Deno' if tool == 'deno' else 'ffmpeg'} a été installé (ou était déjà présent). Redémarrez l'application puis cliquez sur « Tout vérifier ».",
            )
        else:
            QMessageBox.warning(
                self,
                "Installation",
                f"L'installation a échoué ou a été annulée.\n\n{message}",
            )
        if tool == "deno":
            self._refresh_deno()
        else:
            self._refresh_ffmpeg()

    def _show_cookies_help(self) -> None:
        """Ouvre une fenêtre d'aide avec les liens par navigateur (Firefox, Chrome, Edge)."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Comment obtenir cookies.txt")
        dialog.setMinimumWidth(420)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        intro = QLabel(
            "Connectez-vous à YouTube dans votre navigateur, puis exportez les cookies au format Netscape. "
            "Selon votre navigateur, utilisez une des extensions ci-dessous (ou « Importer depuis le navigateur (beta)») :"
        )
        intro.setWordWrap(True)
        intro.setProperty("class", "secondary")
        intro.setStyleSheet("font-size: 11px;")
        layout.addWidget(intro)
        lbl_links = QLabel()
        lbl_links.setOpenExternalLinks(True)
        lbl_links.setWordWrap(True)
        lbl_links.setTextFormat(Qt.TextFormat.RichText)
        lbl_links.setText(
            "<b>Firefox</b> — <a href=\"" + COOKIES_HELP_FIREFOX + "\">cookies.txt</a> (export Netscape)<br>"
            "<b>Chrome</b> — <a href=\"" + COOKIES_HELP_CHROME + "\">Get cookies.txt LOCALLY</a><br>"
            "<b>Edge</b> — <a href=\"" + COOKIES_HELP_EDGE + "\">Get cookies.txt LOCALLY</a>"
        )
        lbl_links.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl_links)
        note = QLabel("Enregistrez le fichier sous le nom cookies.txt dans le dossier de l'application.")
        note.setWordWrap(True)
        note.setProperty("class", "muted")
        note.setStyleSheet("font-size: 10px;")
        layout.addWidget(note)
        btn_ok = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_ok.accepted.connect(dialog.accept)
        layout.addWidget(btn_ok)
        dialog.exec()

    def _encrypt_cookies(self) -> None:
        """Chiffre cookies.txt en cookies.enc (mot de passe) — équivalent CLI --encrypt-cookies."""
        if not cookies_file_valid(COOKIE_FILE):
            QMessageBox.warning(
                self,
                "Cookies",
                "cookies.txt absent ou invalide. Exportez d'abord vos cookies YouTube dans cookies.txt.",
            )
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Chiffrer cookies.txt en cookies.enc")
        dialog.setMinimumWidth(380)
        layout_d = QVBoxLayout(dialog)
        form = QFormLayout()
        edit_pwd = QLineEdit()
        edit_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        edit_pwd.setPlaceholderText("Mot de passe")
        form.addRow("Mot de passe :", edit_pwd)
        edit_confirm = QLineEdit()
        edit_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        edit_confirm.setPlaceholderText("Confirmer le mot de passe")
        form.addRow("Confirmer :", edit_confirm)
        layout_d.addLayout(form)
        note = QLabel(
            "Le mot de passe sera enregistré pour cette session : vous pourrez télécharger tout de suite sans redémarrer. "
            "Pour les prochains lancements, définissez YT_COOKIES_PASSWORD ou relancez le chiffrement ici."
        )
        note.setWordWrap(True)
        note.setProperty("class", "muted")
        note.setStyleSheet("font-size: 10px;")
        layout_d.addWidget(note)
        bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bbox.accepted.connect(dialog.accept)
        bbox.rejected.connect(dialog.reject)
        layout_d.addWidget(bbox)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        pwd = edit_pwd.text().strip()
        confirm = edit_confirm.text().strip()
        if not pwd:
            QMessageBox.warning(self, "Cookies", "Mot de passe vide.")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "Cookies", "Les deux mots de passe ne correspondent pas.")
            return
        err = encrypt_cookies_to_file(pwd)
        if err is None:
            # Définir le mot de passe dans le processus pour cette session : cookies.enc utilisable immédiatement
            os.environ["YT_COOKIES_PASSWORD"] = pwd
            # Supprimer cookies.txt après chiffrement (sécurité : ne pas garder le clair)
            try:
                if COOKIE_FILE.exists():
                    COOKIE_FILE.unlink()
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Cookies",
                    "Cookies chiffrés en cookies.enc, mais impossible de supprimer cookies.txt.\n\n"
                    f"Supprimez-le manuellement. ({e})",
                )
            else:
                QMessageBox.information(
                    self,
                    "Cookies",
                    "Cookies chiffrés enregistrés dans cookies.enc. cookies.txt a été supprimé.\n\n"
                    "Le mot de passe est défini pour cette session : vous pouvez télécharger tout de suite, sans redémarrage ni action manuelle.\n"
                    "Pour les prochains lancements, définissez YT_COOKIES_PASSWORD (variable d'environnement) ou utilisez « Définir le mot de passe pour cookies.enc » (Prérequis).",
                )
            self._refresh_cookies()
        else:
            QMessageBox.warning(self, "Cookies", f"Échec du chiffrement : {err}")

    def _import_cookies_from_browser(self) -> None:
        """Tente d'extraire les cookies YouTube du navigateur (Chrome, Firefox, Edge) et enregistre cookies.txt.
        Fusionne .youtube.com et .google.com pour avoir le même jeu de cookies que l'extension (auth Google)."""
        try:
            import browser_cookie3
        except ImportError:
            QMessageBox.information(
                self,
                "Import cookies",
                "Pour activer l'import depuis le navigateur, installez la dépendance recommandéle :\n\n"
                "pip install browser-cookie3\n\n"
                "Puis redémarrez l'application. Sinon, utilisez une extension (voir « Comment obtenir cookies.txt »).",
            )
            return
        from http.cookiejar import MozillaCookieJar

        out_path = SCRIPT_DIR / "cookies.txt"
        # Domaines utiles pour YouTube (auth Google + YouTube)
        youtube_domains = (".youtube.com", ".google.com", "youtube.com", "google.com")
        used = ""
        for name, loader in [
            ("Chrome", browser_cookie3.chrome),
            ("Firefox", browser_cookie3.firefox),
            ("Edge", browser_cookie3.edge),
        ]:
            try:
                # Charger sans filtre de domaine pour récupérer tous les cookies du navigateur
                cj = loader()
                if cj is None:
                    continue
                # Garder uniquement les cookies YouTube / Google (comme l'extension)
                seen = set()
                moz = MozillaCookieJar(out_path)
                for cookie in cj:
                    dom = getattr(cookie, "domain", "") or ""
                    if not any(d in dom for d in youtube_domains):
                        continue
                    key = (cookie.name, dom, getattr(cookie, "path", "/"))
                    if key in seen:
                        continue
                    seen.add(key)
                    try:
                        moz.set_cookie(cookie)
                    except Exception:
                        continue
                if len(seen) == 0:
                    continue
                moz.save(ignore_discard=True, ignore_expires=True)
                used = name
                break
            except Exception:
                continue
        else:
            if used == "":
                QMessageBox.warning(
                    self,
                    "Import cookies",
                    "Impossible d'extraire les cookies (Chrome, Firefox, Edge).\n\n"
                    "Vérifiez que vous êtes connecté à YouTube dans au moins un navigateur, "
                    "que le navigateur n'est pas en cours d'utilisation exclusive, et réessayez. "
                    "Sinon, utilisez une extension (voir « Comment obtenir cookies.txt »).",
                )
                return
        try:
            if used:
                self._refresh_cookies()
                QMessageBox.information(
                    self,
                    "Import cookies",
                    f"Cookies YouTube/Google extraits depuis {used} et enregistrés dans :\n{out_path}\n\n"
                    "Cliquez sur « Vérifier » pour confirmer. Si l'analyse de chaîne échoue, privilégiez l'extension.",
                )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Import cookies",
                f"Erreur lors de l'enregistrement : {e}\n\nUtilisez une extension (voir « Comment obtenir cookies.txt »).",
            )

    def refresh_all(self) -> None:
        self._refresh_winget()
        self._refresh_deno()
        self._refresh_ffmpeg()
        self._refresh_cookies()
        self._refresh_archive()
