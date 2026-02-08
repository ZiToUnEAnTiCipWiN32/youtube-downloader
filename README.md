# 📥 YouTube Downloader

Télécharge facilement des vidéos YouTube depuis une **interface graphique (GUI)** ou en **ligne de commande (CLI)**. Utilise *yt-dlp* sous le capot, avec **support des chaînes**, **playlists**, **cookies**, **archivage** et **logs**.

Ce projet est fourni à titre **éducatif** : l’utilisateur est responsable du respect des conditions d’utilisation de YouTube et de la législation applicable.

---

## 📋 Les deux applications

| Application | Description |
|-------------|-------------|
| **[gui_app](gui_app/)** | Interface graphique (PySide6, Windows) : onglets Prérequis, Télécharger, Maintenance. Deno/ffmpeg via winget, cookies, thème clair/sombre. → [gui_app/README.md](gui_app/README.md) · [gui_app/DOCUMENTATION.md](gui_app/DOCUMENTATION.md) |
| **[cli_app](cli_app/)** | Script en ligne de commande (cross‑plateforme) : chaîne, vidéo seule, cookies txt/enc, archive. → [cli_app/README.md](cli_app/README.md) · [cli_app/DOCUMENTATION.md](cli_app/DOCUMENTATION.md) |

---

## 🚀 Fonctionnalités principales

### 🖥️ Interface graphique (GUI — Windows)

- Téléchargement par **chaîne / playlists** ou **URL vidéo**
- **Prérequis intégrés** : vérification et installation de *Deno* et *ffmpeg* via *winget*
- Gestion des **cookies YouTube** (cookies.txt, cookies.enc, **import depuis Firefox**)
- Progression, logs et historique
- Vérification des **mises à jour** de l’app et de *yt-dlp*
- Thème clair/sombre automatique ou manuel
- Génération d’un **exécutable Windows** (PyInstaller)

➡️ **Release prête à l’emploi** : [GitHub Releases](https://github.com/ZiToUnEAnTiCipWiN32/youtube-downloader/releases)

### 🧑‍💻 Ligne de commande (CLI — cross‑plateforme)

- Script Python pour télécharger **une vidéo** ou une **chaîne complète**
- Archive pour éviter les doublons (`archive.txt`)
- **Gestion des cookies** en texte ou chiffré (mot de passe ou clé Fernet)
- Environnement virtuel isolé (*venv*) créé automatiquement

---

## 📦 Prérequis

### Système

- **Python ≥ 3.10**
- **Windows** (GUI testée sous Windows) / **Linux / macOS** (CLI)

### Outils recommandés

| Outil | Pourquoi |
|-------|----------|
| **ffmpeg** | Fusion audio/vidéo par *yt-dlp* |
| **Deno** | Résolution des défis JavaScript YouTube (yt-dlp) |
| **Winget** (Windows) | Installation automatique de Deno/ffmpeg depuis la GUI |

---

## 🧠 Installation

Clone le dépôt :

```bash
git clone https://github.com/ZiToUnEAnTiCipWiN32/youtube-downloader.git
cd youtube-downloader
```

---

## 🖥️ Utiliser l’interface graphique (GUI)

### Version via release GitHub

1. Ouvre la [dernière release](https://github.com/ZiToUnEAnTiCipWiN32/youtube-downloader/releases)
2. Télécharge l’exécutable Windows
3. Lance l’application

*Recommandé si tu ne veux pas installer Python.*

### Version depuis les sources

```powershell
cd gui_app
python start.py
```

Au premier lancement, un **venv** est créé et les dépendances sont installées automatiquement.

---

## 🧑‍💻 Utiliser la ligne de commande (CLI)

```bash
cd cli_app
python telechargement.py
```

- Le script crée un **venv** (`yt_env/`) au premier lancement.
- Menu : **1 → Chaîne YouTube** · **2 → Vidéo seule**
- Téléchargements dans `cli_app/downloads/`. Archive `archive.txt` pour éviter les doublons.

---

## 🍪 Cookies (fortement recommandé)

Pour éviter les blocages type *bot* ou les restrictions :

- **cookies.txt** → format Netscape (export depuis le navigateur ou **import depuis Firefox** dans la GUI)
- **cookies.enc** → version chiffrée avec `YT_COOKIES_PASSWORD` ou `YT_COOKIES_KEY` (Fernet)

La GUI permet d’**importer depuis Firefox** (sous Windows seul Firefox est pris en charge), de chiffrer en cookies.enc et de gérer les fichiers. Voir [cli_app/TUTO_COOKIES.md](cli_app/TUTO_COOKIES.md) pour le CLI.

---

## 📁 Structure du dépôt

```
youtube-downloader/
├── gui_app/              ← Interface graphique (Windows)
│   ├── start.py           # Point d’entrée GUI
│   ├── README.md
│   ├── DOCUMENTATION.md
│   └── src/               # Code PySide6
├── cli_app/               ← Ligne de commande
│   ├── telechargement.py  # Script principal CLI
│   ├── README.md
│   ├── DOCUMENTATION.md
│   └── TUTO_COOKIES.md
├── LICENSE
└── README.md              ← Ce fichier
```

Les dossiers `downloads/`, `logs/`, `archive.txt` et les cookies sont créés **dans** `gui_app/` ou `cli_app/` selon l’application utilisée.

---

## 📘 Documentation détaillée

- **GUI** : [gui_app/README.md](gui_app/README.md) · [gui_app/DOCUMENTATION.md](gui_app/DOCUMENTATION.md)
- **CLI** : [cli_app/README.md](cli_app/README.md) · [cli_app/DOCUMENTATION.md](cli_app/DOCUMENTATION.md) · [cli_app/TUTO_COOKIES.md](cli_app/TUTO_COOKIES.md)

---

## 🛠️ Générer un exécutable Windows (GUI)

```powershell
cd gui_app
.\venv\Scripts\activate
pip install pyinstaller
pyinstaller --onefile --windowed --icon="icon.ico" --name "YouTube-Downloader" start.py
```

L’exécutable sera dans `gui_app/dist/`. Voir [gui_app/DOCUMENTATION.md](gui_app/DOCUMENTATION.md) pour le script PowerShell `build_exe.ps1`.

---

## 📝 Licence

MIT License — voir [LICENSE](LICENSE).

Ce projet est fourni à titre **éducatif**. L’utilisateur est responsable du respect des conditions d’utilisation de YouTube et des lois en vigueur.
