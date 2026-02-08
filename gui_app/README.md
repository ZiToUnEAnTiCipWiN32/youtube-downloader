# YouTube Downloader — Version GUI (PySide6)

Application Windows pour télécharger des vidéos YouTube par **chaîne** (onglets / playlists) ou par **URL vidéo**. Tout se fait depuis la fenêtre : pas de script de démarrage séparé.

## Lancement

Depuis le dossier `gui_app` :

```powershell
python start.py
```

- **Premier lancement** : une fenêtre « Premier lancement » apparaît brièvement (création du venv et installation des dépendances : PySide6, yt-dlp, cryptography, browser-cookie3). Puis l’application se relance et la fenêtre principale s’ouvre.
- **Lancements suivants** : la fenêtre principale s’ouvre directement.
- **Thème** : l’interface suit le thème système (clair ou sombre) : si Windows est en mode sombre, l’application s’affiche en thème sombre. La détection du thème système est prise en charge à partir de **PySide6 6.6** (Qt 6.5+) ; sinon l’application reste en thème clair.

Aucun script `.bat` ou `.ps1` n’est nécessaire : tout est géré par `start.py` et par la GUI.

## Prérequis (vérifiables depuis l’onglet « Prérequis »)

- **Python 3.10+** (installé sur la machine).
- **Deno** (recommandé pour YouTube) : l’onglet « Prérequis » permet de vérifier, d’installer et de désinstaller via **winget** (Windows).
- **ffmpeg** (recommandé pour fusion audio/vidéo) : l’onglet « Prérequis » permet de vérifier, d’installer et de désinstaller via **winget** (Windows).
- **winget** doit être disponible (Windows 10/11 avec App Installer) pour que les boutons « Installer via winget » et « Supprimer » de Deno et ffmpeg soient actifs. Sur Windows, après une installation via winget, pas besoin de redémarrer l’app : la détection et les téléchargements utilisent le PATH du registre.
- **Cookies** (recommandé) : placer `cookies.txt` (format Netscape) dans le dossier `gui_app`, ou `cookies.enc` avec `YT_COOKIES_PASSWORD` / `YT_COOKIES_KEY`. Depuis l’onglet Prérequis : **« Importer depuis Firefox »** (sous Windows seul Firefox est pris en charge ; Chrome/Edge sont chiffrés) — génère un `cookies.txt` compatible Netscape/yt-dlp (domaines YouTube/Google uniquement, format normalisé) ; **« Chiffrer cookies.txt en cookies.enc »** ; **« Supprimer cookies.txt »** / **« Supprimer cookies.enc »**, **« Comment obtenir cookies.txt »** (liens vers les extensions, utile si l'import échoue). L’état est affiché dans « Prérequis ».

## Utilisation

1. **Onglet « Prérequis »** : indicateur **winget** (Disponible / Non disponible) ; vérifier Deno, ffmpeg, cookies ; installer ou **supprimer** **Deno** / **ffmpeg** via winget (boutons désactivés si winget absent ou outil non installé) ; « Importer depuis Firefox », « Chiffrer cookies.txt en cookies.enc », « Supprimer cookies.txt » / « Supprimer cookies.enc », « Comment obtenir cookies.txt » ; « Tout vérifier » pour rafraîchir.
2. **Onglet « Télécharger »** :
   - **Mode Chaîne** : saisir l’URL ou le @handle de la chaîne → « Analyser la chaîne » → cocher les sections à télécharger → « Télécharger la sélection ».
   - **Mode Vidéo** : saisir l’URL de la vidéo → « Télécharger la sélection ».
   - **Progression** : barre et journal (une ligne « ✔ Vidéo terminée : [nom] » par vidéo) ; bouton **« Ouvrir le dossier des téléchargements »** pour ouvrir `downloads/` dans l’explorateur.
3. En cas d’erreur (bot, cookies expirés, métadonnées incomplètes, etc.), l’app affiche un message en français dans le journal et le résumé, avec un **conseil** selon le type d’erreur (mettre à jour les cookies, installer Deno, etc.).
4. **Onglet « Maintenance »** : affichage des **versions actuelles** (yt-dlp, application) et **« Vérifier les mises à jour »** (PyPI pour yt-dlp ; GitHub pour l’app si `GITHUB_REPO` est configuré) ; **« Ouvrir le dossier des logs »** pour ouvrir `gui_app/logs/` dans l’explorateur.

Les vidéos sont enregistrées dans `gui_app/downloads/`. L’archive (éviter les doublons) est dans `gui_app/archive.txt`.

## Structure

- `start.py` : point d’entrée unique ; crée le venv et installe les deps au premier run, puis lance l’app PySide6.
- `src/main.py` : lancement de l’application Qt.
- `src/core/` : logique métier (chemins, URLs, cookies, analyse de chaîne, téléchargement yt-dlp ; sur Windows, PATH du registre pour Deno/ffmpeg).
- `src/gui/` : fenêtre principale, styles (thème clair/sombre selon le système), onglet Prérequis (winget, Deno, ffmpeg — vérifier, installer, supprimer — cookies, archive), onglet Téléchargement (mode, analyse, liste, progression, ouvrir dossier téléchargements), onglet Maintenance (versions, mises à jour, ouvrir dossier logs).

## Exécutable (PyInstaller)

Pour générer un `.exe` Windows :

```powershell
.\venv\Scripts\activate
pip install pyinstaller
pyinstaller --onefile --windowed --name "YouTube-Downloader" start.py
```

Le binaire sera dans `dist/`. Deno et ffmpeg restent recommandés ; l’utilisateur peut les installer via winget depuis l’onglet « Prérequis » (si winget est disponible) ou manuellement.

## Licence

À titre éducatif. L’utilisateur est responsable du respect des conditions d’utilisation de YouTube et du droit applicable.
