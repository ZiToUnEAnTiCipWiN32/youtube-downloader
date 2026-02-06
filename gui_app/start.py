"""
Point d'entrée unique : tout se fait depuis ici (pas de script .bat).
- Exécutable PyInstaller : lancement direct de l'app (pas de venv).
- Sinon (python start.py) : si le venv n'existe pas ou qu'on n'est pas dedans,
  création du venv (gui_app/venv/), installation des dépendances (fenêtre Tkinter),
  puis relance dans le venv ; sinon lancement de l'application PySide6.
Windows uniquement.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
# Venv créé ici (à côté de start.py) : gui_app/venv/
VENV_DIR = SCRIPT_DIR / "venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
REQUIREMENTS = SCRIPT_DIR / "requirements.txt"


def _ensure_venv_and_restart() -> None:
    """Crée le venv, installe les deps, relance ce script avec le Python du venv."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        root = None
    else:
        root = tk.Tk()
        root.title("YouTube Downloader By ZiToUnE-AnTiCip-WiN32 — Premier lancement")
        root.geometry("420x140")
        root.resizable(False, False)
        ttk.Label(root, text="Création de l'environnement…", font=("Segoe UI", 12)).pack(pady=20)
        lbl = ttk.Label(root, text="Création du venv et installation des dépendances…")
        lbl.pack(pady=5)
        pb = ttk.Progressbar(root, mode="indeterminate", length=300)
        pb.pack(pady=15)
        pb.start(10)
        root.update()

    subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        check=True,
    )
    if root:
        lbl.config(text="Installation des paquets (PySide6, yt-dlp…)…")
        root.update()
    subprocess.run(
        [str(VENV_PYTHON), "-m", "pip", "install", "-q", "--upgrade", "pip"],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [str(VENV_PYTHON), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        check=True,
    )
    if root:
        pb.stop()
        lbl.config(text="Démarrage de l'application…")
        root.update()
        root.after(500, root.destroy)
        root.mainloop()

    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(SCRIPT_DIR / "start.py")])


def main() -> None:
    if sys.platform != "win32":
        print("Cette application est prévue pour Windows uniquement.")
        sys.exit(1)

    # Exécutable PyInstaller : pas de venv, tout est déjà dans l'exe → lancer l'app directement
    if getattr(sys, "frozen", False):
        from src.main import run_app
        run_app()
        return

    # On est dans le venv si sys.executable == VENV_PYTHON (ou équivalent)
    in_venv = (
        VENV_PYTHON.exists()
        and pathlib.Path(sys.executable).resolve() == VENV_PYTHON.resolve()
    )

    if not VENV_DIR.exists() or not in_venv:
        _ensure_venv_and_restart()
        return

    # Lancer l'app PySide6 (tout le reste se fait dans la GUI)
    from src.main import run_app
    run_app()


if __name__ == "__main__":
    main()
