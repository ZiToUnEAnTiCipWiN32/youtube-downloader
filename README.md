# YouTube Downloader

Deux applications pour télécharger des vidéos YouTube : une **interface en ligne de commande** et une **interface graphique** (Windows).

| Application | Description |
|-------------|-------------|
| **[cli_app](cli_app/)** | Script Python en ligne de commande : chaîne, URL vidéo, cookies (txt/enc), archive. Voir [cli_app/README.md](cli_app/README.md) et [cli_app/DOCUMENTATION.md](cli_app/DOCUMENTATION.md). |
| **[gui_app](gui_app/)** | Application PySide6 (fenêtre) : onglets Prérequis, Télécharger, Maintenance ; cookies, Deno/ffmpeg via winget, thème clair/sombre. Voir [gui_app/README.md](gui_app/README.md) et [gui_app/DOCUMENTATION.md](gui_app/DOCUMENTATION.md). |

## Prérequis

- **Python 3.10+**
- **ffmpeg** (recommandé pour la fusion audio/vidéo)
- **Cookies** (recommandé pour éviter les blocages type bot) : format Netscape (`cookies.txt` ou `cookies.enc`)

## Démarrage rapide

**CLI** (depuis `cli_app/`) :
```powershell
cd cli_app
python telechargement.py
```

**GUI** (depuis `gui_app/`) :
```powershell
cd gui_app
python start.py
```

Au premier lancement de la GUI, un environnement virtuel est créé et les dépendances sont installées automatiquement.

## Licence

MIT License — voir [LICENSE](LICENSE).  
L’utilisateur est responsable du respect des conditions d’utilisation de YouTube et du droit applicable.
