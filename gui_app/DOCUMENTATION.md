# Documentation — YouTube Downloader (GUI)

Application Windows (PySide6) pour télécharger des vidéos YouTube par **chaîne** (onglets / playlists) ou par **URL vidéo**. Toute la configuration et les téléchargements se font depuis la fenêtre, sans ligne de commande.

---

## 1. Vue d’ensemble

- **Lancement** : depuis le dossier `gui_app`, exécuter `python start.py`.
- **Premier lancement** : une fenêtre « Premier lancement » crée un environnement virtuel (venv), installe les dépendances (PySide6, yt-dlp, cryptography, browser-cookie3), puis relance l’application.
- **Lancements suivants** : la fenêtre principale s’ouvre directement.
- **Thème** : l’interface suit par défaut le thème système (clair/sombre). La préférence peut être modifiée dans l’onglet Maintenance (Système / Clair / Sombre).

Aucun script `.bat` ou `.ps1` n’est nécessaire : tout est géré par `start.py` et par l’interface.

---

## 2. Prérequis système

- **Python 3.10+** installé sur la machine.
- **Windows** (recommandé ; l’app peut fonctionner sur macOS/Linux avec adaptations mineures).
- **winget** (Windows 10/11 avec App Installer) : requis pour les boutons « Installer via winget » de Deno et ffmpeg dans l’onglet Prérequis.
- **Deno** (recommandé pour certains défis YouTube) : vérifiable et installable depuis l’onglet Prérequis.
- **ffmpeg** (recommandé pour la fusion audio/vidéo) : vérifiable et installable depuis l’onglet Prérequis.
- **Cookies** (recommandé pour éviter les blocages type bot) : voir section 6.

---

## 3. Installation et lancement

### 3.1 Depuis les sources

```powershell
cd gui_app
python start.py
```

Au premier run, le venv est créé et les dépendances sont installées ; l’app se relance ensuite.

### 3.2 Dépendances (installées automatiquement)

- **PySide6** ≥ 6.6 (interface Qt ; thème système à partir de Qt 6.5).
- **yt-dlp** (téléchargements YouTube).
- **cryptography** (chiffrement des cookies en cookies.enc).
- **browser-cookie3** (optionnel ; pour « Importer depuis le navigateur »).

Elles sont listées dans `requirements.txt` et installées dans le venv au premier lancement.

---

## 4. Interface

### 4.1 Fenêtre principale

- **Titre** : « YouTube Downloader ».
- **Taille par défaut** : 1280×800 px ; largeur minimale 900 px. L’onglet Prérequis a une largeur minimale de contenu (1200 px) avec barre de défilement horizontale si la fenêtre est réduite.
- **Onglets** : Prérequis, Télécharger, Maintenance.
- **Barre de statut** : affiche le dossier de sortie des téléchargements.

### 4.2 Onglet « Prérequis »

Permet de vérifier et configurer les outils recommandés avant de télécharger.

| Élément | Description |
|--------|-------------|
| **winget** | Indicateur « Disponible » / « Non disponible ». Si winget est absent, les boutons « Installer via winget » (Deno, ffmpeg) sont désactivés. |
| **Deno** | Vérification dans le PATH ; bouton « Installer via winget » si Deno absent et winget disponible. |
| **ffmpeg** | Vérification dans le PATH ; bouton « Installer via winget » si ffmpeg absent et winget disponible. |
| **Cookies** | Statut : **Configuré** (cookies.txt ou cookies.enc + mot de passe), **Mot de passe requis** (cookies.enc présent sans variable d’environnement), ou **Non configuré**. Voir section 6. |
| **Boutons cookies** | « Vérifier », « Comment obtenir cookies.txt », « Importer depuis le navigateur (beta) », « Chiffrer cookies.txt en cookies.enc », « Définir le mot de passe pour cookies.enc » (visible uniquement quand cookies.enc existe sans mot de passe défini), « Supprimer cookies.txt », « Supprimer cookies.enc ». |
| **Archive** | Chemin de `archive.txt` et nombre d’entrées ; bouton « Supprimer archive.txt » pour réinitialiser les doublons. |
| **Tout vérifier** | Rafraîchit tous les indicateurs (Deno, ffmpeg, cookies, archive). |

Après une installation via winget (Deno ou ffmpeg), un message indique de redémarrer l’application puis de cliquer sur « Tout vérifier ».

### 4.3 Onglet « Télécharger »

- **Mode Chaîne** : saisir l’URL ou le @handle de la chaîne → « Analyser la chaîne » → liste des sections (onglets / playlists) avec cases à cocher → « Télécharger la sélection ».
- **Mode Vidéo** : saisir l’URL d’une vidéo → « Télécharger la sélection » (sans analyse).
- **Progression** : barre de progression et journal (une ligne « ✔ Vidéo terminée : [nom] » par vidéo).
- **Bouton « Ouvrir le dossier des téléchargements »** : ouvre le dossier `downloads/` dans l’explorateur Windows.
- **Résumé** : affiché après le téléchargement ; en cas d’erreur, un message en français avec **conseil** selon le type (cookies, bot, etc.).

Les vidéos sont enregistrées dans `gui_app/downloads/` avec un sous-dossier par chaîne / playlist. L’archive (`archive.txt`) évite les doublons.

### 4.4 Fenêtre « À propos »

Accessible depuis **Aide → À propos** (menu en haut) ou **Maintenance → À propos de l'application**. Affiche le titre (YouTube-Downloader By ZiToUnE-AnTiCip-WiN32), la version, l’auteur, les liens (Site, GitHub, YouTube, Twitch), © 2026 et la licence MIT.

### 4.5 Onglet « Maintenance »

| Élément | Description |
|--------|-------------|
| **Thème d’affichage** | Liste déroulante : **Système** (suit le thème Windows), **Clair**, **Sombre**. La préférence est enregistrée et appliquée immédiatement. |
| **yt-dlp** | Version actuelle (lue depuis le module) et version disponible (PyPI) ; bouton « Vérifier les mises à jour ». |
| **Application** | Version actuelle et version disponible (GitHub si `GITHUB_REPO` est configuré et qu’au moins une **Release** existe) ; bouton « Vérifier les mises à jour ». |
| **Dossiers** | Lien vers le dossier des logs ; bouton « Ouvrir le dossier des logs » pour ouvrir `gui_app/logs/` dans l’explorateur. |

---

## 5. Thème d’affichage

- **Détection système** : à partir de PySide6 6.6 (Qt 6.5+), le thème système (clair/sombre) est détecté au démarrage.
- **Préférence utilisateur** : dans Maintenance → « Thème d’affichage », choix **Système**, **Clair** ou **Sombre**. La valeur est stockée (QSettings) et réappliquée à chaque lancement.
- **Styles** : définis dans `src/gui/styles.py` (palettes clair/sombre pour boutons, listes, champs, onglets, etc.).

---

## 6. Cookies

Les cookies YouTube (format Netscape) permettent d’éviter les blocages type bot et d’accéder à du contenu restreint. L’application gère deux formes : **cookies.txt** (clair) et **cookies.enc** (chiffré).

### 6.1 États affichés (onglet Prérequis)

- **Configuré** : une source de cookies est utilisable (cookies.txt valide, ou cookies.enc présent avec `YT_COOKIES_PASSWORD` ou `YT_COOKIES_KEY` définie).
- **Mot de passe requis** : cookies.enc est présent mais aucune variable d’environnement n’est définie ; le bouton « Définir le mot de passe pour cookies.enc » permet de saisir le mot de passe pour la session en cours.
- **Non configuré** : ni cookies.txt valide ni cookies.enc utilisable.

### 6.2 Obtenir des cookies

- **Extensions navigateur** : « Comment obtenir cookies.txt » ouvre une aide avec des liens (Firefox, Chrome, Edge) pour exporter les cookies au format Netscape.
- **Importer depuis le navigateur (beta)** : tente d’extraire les cookies YouTube depuis Chrome, Firefox ou Edge (nécessite `browser-cookie3`). Enregistre `cookies.txt` dans le dossier de l’app.

### 6.3 Chiffrer cookies.txt en cookies.enc

1. Placer ou importer **cookies.txt** dans le dossier `gui_app`.
2. Cliquer sur **« Chiffrer cookies.txt en cookies.enc »**.
3. Saisir un **mot de passe** (et le confirmer). Aucun critère de complexité n’est imposé (longueur, caractères spéciaux, etc.) ; c’est à la liberté de l’utilisateur.
4. Valider : `cookies.enc` est créé, **cookies.txt est supprimé automatiquement** (sécurité), et **`YT_COOKIES_PASSWORD` est défini dans le processus** pour la session en cours.
5. **Aucune action manuelle ni redémarrage** : les téléchargements utilisent immédiatement cookies.enc via le mot de passe en mémoire.

Pour les **prochains lancements** : définir la variable d’environnement `YT_COOKIES_PASSWORD` (ou `YT_COOKIES_KEY`) avec le même mot de passe, ou utiliser « Définir le mot de passe pour cookies.enc » dans l’onglet Prérequis (si cookies.enc existe déjà).

### 6.4 Définir le mot de passe pour cookies.enc (sans chiffrer)

Quand **cookies.enc** existe mais qu’aucune variable d’environnement n’est définie (par exemple après un redémarrage ou sur une autre machine), le statut affiche **« Mot de passe requis »** et le bouton **« Définir le mot de passe pour cookies.enc »** apparaît. En cliquant dessus, on saisit le mot de passe (celui qui a servi à chiffrer) ; il est enregistré dans le processus pour la session. Les téléchargements peuvent alors utiliser cookies.enc sans redémarrer l’app.

### 6.5 Suppression

- **Supprimer cookies.txt** : supprime le fichier en clair (avec confirmation).
- **Supprimer cookies.enc** : supprime le fichier chiffré et retire `YT_COOKIES_PASSWORD` du processus (avec confirmation).

### 6.6 Utilisation au téléchargement

Au moment du téléchargement, l’app appelle `get_cookiefile_path()` (module `src/core/cookies.py`) :

- Si **cookies.enc** existe et que `YT_COOKIES_PASSWORD` ou `YT_COOKIES_KEY` est défini : déchiffrement à la volée vers un fichier temporaire ; ce chemin est passé à yt-dlp.
- Sinon, si **cookies.txt** est valide : son chemin est passé à yt-dlp.
- Sinon : aucun cookie n’est transmis.

---

## 7. Dossiers et fichiers

| Chemin (relatif à `gui_app`) | Rôle |
|------------------------------|------|
| `downloads/` | Vidéos téléchargées (créé automatiquement). |
| `logs/` | Fichiers de log (extract_gui, yt_session, etc.). |
| `archive.txt` | Liste des vidéos déjà téléchargées (évite les doublons). |
| `cookies.txt` | Cookies Netscape en clair (optionnel ; supprimé après chiffrement si on utilise « Chiffrer cookies.txt en cookies.enc »). |
| `cookies.enc` | Cookies chiffrés (optionnel ; utilisé si `YT_COOKIES_PASSWORD` ou `YT_COOKIES_KEY` est défini). |

Les chemins sont définis dans `src/core/paths.py` (SCRIPT_DIR = dossier contenant `start.py`).

---

## 8. Structure du projet

```
gui_app/
├── start.py              # Point d'entrée : venv + deps au premier run, puis lancement app
├── requirements.txt      # Dépendances Python
├── README.md             # Résumé et lancement
├── DOCUMENTATION.md      # Cette documentation
├── logs/                 # Logs (créé à l'usage)
├── downloads/            # Vidéos (créé à l'usage)
├── archive.txt           # Archive doublons (créé à l'usage)
├── cookies.txt           # Optionnel
├── cookies.enc            # Optionnel
└── src/
    ├── main.py           # Lancement QApplication, thème, fenêtre
    ├── core/             # Logique métier
    │   ├── paths.py       # Chemins (SCRIPT_DIR, LOG_DIR, OUTPUT_DIR, ARCHIVE_FILE, cookies)
    │   ├── urls.py        # Normalisation URLs chaîne / vidéo
    │   ├── channel.py     # Analyse de chaîne (sections, playlists)
    │   ├── cookies.py     # cookies.txt / cookies.enc, chiffrement, get_cookiefile_path
    │   └── download.py    # run_download (yt-dlp), messages d'erreur utilisateur
    └── gui/
        ├── main_window.py      # Fenêtre principale, onglets, barre de statut
        ├── styles.py           # Thèmes clair/sombre, palette, apply_button_palette
        ├── prerequisites.py   # Onglet Prérequis (winget, Deno, ffmpeg, cookies, archive)
        ├── download_view.py   # Onglet Télécharger (chaîne/vidéo, analyse, liste, progression)
        ├── maintenance_view.py # Onglet Maintenance (versions, thème, logs)
        └── about_dialog.py     # Fenêtre À propos (auteur, liens, licence)
```

---

## 9. Génération d’un exécutable (PyInstaller)

Pour produire un `.exe` Windows (optionnel) :

```powershell
cd gui_app
.\venv\Scripts\activate
pip install pyinstaller
pyinstaller --onefile --windowed --icon="C:\chemin\vers\icone.ico" --name "YouTube-Downloader" start.py
```

Remplacez `C:\chemin\vers\icone.ico` par le chemin de votre fichier `.ico` (ex. `C:\Users\olivi\Downloads\img_gta\unnamed.ico`).

Le binaire se trouve dans `dist/`. Deno et ffmpeg restent recommandés ; l’utilisateur peut les installer via winget depuis l’onglet Prérequis (si winget est disponible) ou manuellement.

**Icône de l’exécutable** : pour une icône personnalisée sur le `.exe`, fournir un fichier `.ico` et utiliser l’option PyInstaller :

```powershell
pyinstaller --onefile --windowed --icon="C:\chemin\vers\icone.ico" --name "YouTube-Downloader" start.py
```

L’icône de la **fenêtre** (barre de titre) peut être définie dans le code avec `QMainWindow.setWindowIcon(QIcon("chemin/vers/icone.ico"))` au démarrage (fichier `.ico` à placer dans le dossier de l’app ou en ressource).

---

## 10. Vérification des mises à jour (app)

Pour que le bouton **« Vérifier les mises à jour »** affiche une version disponible pour l’application, le dépôt GitHub doit avoir **au moins une Release** avec un tag (ex. `v1.0.0`). L’app interroge l’API GitHub `releases/latest` et utilise le `tag_name` (sans le préfixe `v`).

**Créer une Release sur GitHub :**

1. Sur la page du dépôt : **Releases** → **Create a new release**.
2. **Choose a tag** : créer un tag, ex. `v1.0.0` (cohérent avec `gui_app/src/__init__.py` → `__version__ = "1.0.0"`).
3. **Release title** : ex. « v1.0.0 » ou « Version 1.0.0 ».
4. **Description** (optionnel) : résumé des changements.
5. **Publish release**.

Après publication, « Vérifier les mises à jour » dans l’onglet Maintenance affichera cette version (ex. 1.0.0) comme « Version disponible » pour l’application.

---

## 11. Dépannage et conseils

- **« Non configuré » alors que cookies.enc existe** : utiliser « Définir le mot de passe pour cookies.enc » (onglet Prérequis) pour définir le mot de passe pour la session.
- **Erreur type bot / cookies expirés** : mettre à jour les cookies (ré-exporter depuis le navigateur, ré-importer ou re-chiffrer).
- **Deno / ffmpeg non trouvés après installation** : redémarrer l’application (le PATH est lu au démarrage), puis cliquer sur « Tout vérifier ».
- **Thème** : si la détection système ne fonctionne pas, vérifier PySide6 ≥ 6.6 (Qt 6.5+). Sinon, choisir « Clair » ou « Sombre » dans Maintenance.

---

## 12. Licence

À titre éducatif. L’utilisateur est responsable du respect des conditions d’utilisation de YouTube et du droit applicable.
