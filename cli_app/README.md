# YouTube Downloader — Téléchargement par chaîne ou URL

Script Python pour télécharger des vidéos YouTube **par chaîne** (onglets / playlists) ou **une vidéo** (coller l’URL). Utilise **yt-dlp** dans un environnement virtuel dédié, avec archive, cookies et logs.

| | |
|---|---|
| **Auteur** | ZiToUnEAnTiCipWiN32 |
| **Version** | 1.0.0 |
| **YouTube** | [@Zitoune-anticip-WIN32](https://www.youtube.com/@Zitoune-anticip-WIN32) |
| **Site** | [zitouneanticip.free.fr](http://zitouneanticip.free.fr) |
| **GitHub** | [ZiToUnEAnTiCipWiN32](https://github.com/ZiToUnEAnTiCipWiN32) |

---

## Démarrage rapide

- **Prérequis** : Python 3.x (3.10+ recommandé), [ffmpeg](https://ffmpeg.org) (recommandé, binaire dans le PATH ; Windows : `winget install "FFmpeg (Essentials Build)"`), [Deno](https://deno.land) (Windows : `irm https://deno.land/install.ps1 | iex` ; Linux/macOS : `curl -fsSL https://deno.land/install.sh | sh`). Détail : [DOCUMENTATION.md § 1.3](DOCUMENTATION.md#13-prérequis).
- **Lancement** : `python telechargement.py`  
  Au premier run, le script crée le venv `yt_env/`, installe les dépendances puis se relance.
- **Cookies** (recommandé) : placer **`cookies.txt`** (format Netscape) à la racine, ou **`cookies.enc`** et définir **`YT_COOKIES_PASSWORD`** ou **`YT_COOKIES_KEY`**.

---

## Documentation complète

Toute la documentation (utilisation, cookies en détail, architecture, développement) est regroupée dans un **seul fichier** :

→ **[DOCUMENTATION.md](DOCUMENTATION.md)**

Pour un **tutoriel dédié aux cookies** (export, chiffrement mot de passe / clé Fernet) : **[TUTO_COOKIES.md](TUTO_COOKIES.md)**.

La documentation complète contient :

1. **Présentation** — Fonctionnalités, prérequis, structure du projet  
2. **Installation et démarrage rapide**  
3. **Utilisation** — Mode chaîne / vidéo, menu, téléchargement, résumé, dépannage  
4. **Cookies (détaillé)** — Texte, mot de passe (`YT_COOKIES_PASSWORD`), clé Fernet (`YT_COOKIES_KEY`), export navigateur, sécurité, dépannage  
5. **Architecture et technique** — Logique, performances, technologies, sécurité  
6. **Développement et contribution** — Venv, structure du code, tests, extensions, bonnes pratiques  
7. **Licence et responsabilité**  
8. **Liens** — YouTube, Site, GitHub  

---

## Licence et responsabilité

Ce projet est fourni à titre éducatif. L’utilisateur est seul responsable du respect des conditions d’utilisation de YouTube et du droit applicable (droits d’auteur, usage personnel, etc.).
