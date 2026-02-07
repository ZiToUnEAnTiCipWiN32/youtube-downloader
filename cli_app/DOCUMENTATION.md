# YouTube Downloader — Documentation complète

Documentation unifiée du projet **YouTube Downloader** : présentation, utilisation, cookies (texte / mot de passe / clé Fernet), architecture technique et développement.

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Installation et démarrage rapide](#2-installation-et-démarrage-rapide)
3. [Utilisation](#3-utilisation)
4. [Cookies (détaillé)](#4-cookies-détaillé)
5. [Architecture et technique](#5-architecture-et-technique)
6. [Développement et contribution](#6-développement-et-contribution)
7. [Licence et responsabilité](#7-licence-et-responsabilité)
8. [Liens](#8-liens)

---

## 1. Présentation

### 1.1 Qu’est-ce que c’est ?

Script Python pour télécharger des vidéos YouTube **par chaîne** (onglets / playlists) ou **une vidéo** (coller l’URL). Utilise **yt-dlp** dans un environnement virtuel dédié, avec archive, cookies et logs.

| | |
|---|---|
| **Auteur** | ZiToUnEAnTiCipWiN32 |
| **Version** | 1.0.0 |
| **YouTube** | [@Zitoune-anticip-WIN32](https://www.youtube.com/@Zitoune-anticip-WIN32) |
| **Site** | [zitouneanticip.free.fr](http://zitouneanticip.free.fr) |
| **GitHub** | [ZiToUnEAnTiCipWiN32](https://github.com/ZiToUnEAnTiCipWiN32) |

### 1.2 Fonctionnalités

- **Mode chaîne** : analyse la chaîne (Vidéos, Shorts, Directs, playlists) puis choix des sections à télécharger.
- **Mode vidéo** : coller une URL YouTube pour télécharger une seule vidéo.
- **Archive** : évite de re-télécharger les vidéos déjà enregistrées (`archive.txt`).
- **Cookies** : support recommandé de `cookies.txt` (export navigateur) ou de **`cookies.enc`** (chiffré, déchiffré à la volée avec `YT_COOKIES_PASSWORD` ou `YT_COOKIES_KEY`) pour limiter les blocages.
- **Logs** : journal général + log par session.
- **Venv isolé** : yt-dlp, colorama, ffmpeg-python, cryptography installés automatiquement dans `yt_env/`.

### 1.3 Prérequis

- **Python 3.x** (3.10+ recommandé).
- **ffmpeg** (recommandé) : utilisé par yt-dlp pour fusionner audio et vidéo (format final mp4). Il faut installer le **binaire** ffmpeg (pas seulement le paquet Python `ffmpeg-python`) et l’ajouter au **PATH**. Sans ffmpeg dans le PATH, certains téléchargements peuvent échouer ou rester en audio seul.

  **Ajouter ffmpeg au PATH selon l’OS :**

  - **Windows**  
    1. Télécharger un build sur [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/) (ex. *release essentials* en .zip ou .7z).  
    2. Extraire l’archive dans un dossier fixe (ex. `C:\ffmpeg`).  
    3. Le dossier contenant `ffmpeg.exe` et `ffprobe.exe` est en général `ffmpeg-8.0.1-essentials_build\bin` (ou similaire).  
    4. Ajouter ce dossier au PATH : **Paramètres** → **Système** → **À propos** → **Paramètres système avancés** → **Variables d’environnement** → dans **Variables utilisateur**, éditer **Path** → **Nouveau** → coller le chemin complet du dossier `bin` (ex. `C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin`) → **OK**.  
    5. Fermer et rouvrir le terminal (PowerShell ou CMD), puis vérifier : `ffmpeg -version`.  
    *Alternative* : installer via un gestionnaire de paquets (ffmpeg est alors ajouté au PATH automatiquement) : `winget install Gyan.FFmpeg.Essentials --source winget` ou `choco install ffmpeg`.  
    **Désinstaller (winget)** : `winget uninstall Gyan.FFmpeg.Essentials`

  - **Linux**  
    1. Installer ffmpeg : `sudo apt install ffmpeg` (Debian/Ubuntu), `sudo dnf install ffmpeg` (Fedora), ou selon ta distribution.  
    2. En général, les paquets officiels placent déjà les binaires dans un répertoire du PATH (ex. `/usr/bin`). Vérifier : `ffmpeg -version`.  
    3. Si tu as installé un binaire manuel (ex. dans `~/bin`), ajouter au PATH dans `~/.bashrc` ou `~/.profile` : `export PATH="$HOME/bin:$PATH"`, puis `source ~/.bashrc`.

  - **macOS**  
    1. Avec **Homebrew** (recommandé) : `brew install ffmpeg`. Homebrew ajoute automatiquement les binaires au PATH.  
    2. Vérifier : `ffmpeg -version`.  
    3. Si tu as installé ffmpeg manuellement dans un dossier (ex. `/usr/local/bin`), ce dossier doit être dans ton PATH ; sinon ajouter dans `~/.zshrc` ou `~/.bash_profile` : `export PATH="/chemin/vers/bin:$PATH"`, puis rouvrir le terminal.

- **Deno** (runtime JavaScript requis par YouTube / yt-dlp pour les challenges) :
  - **Windows (PowerShell)** : `irm https://deno.land/install.ps1 | iex` — ou via winget : `winget install DenoLand.Deno --source winget`. **Désinstaller (winget)** : `winget uninstall DenoLand.Deno`
  - **Linux / macOS** : `curl -fsSL https://deno.land/install.sh | sh`  
  Puis fermer et rouvrir le terminal, et vérifier : `deno --version`.

### 1.4 Structure du projet

```
.
├── telechargement.py   # Script principal
├── requirements.txt   # Dépendances (référence ; le script installe dans yt_env/ au premier run)
├── .gitignore         # Fichiers à ne pas versionner (yt_env/, cookies, archive, downloads, logs)
├── cookies.txt        # (recommandé) Cookies YouTube au format Netscape
├── cookies.enc        # (recommandé) Cookies chiffrés ; déchiffrés via YT_COOKIES_PASSWORD / YT_COOKIES_KEY
├── archive.txt        # (créé) Liste des vidéos déjà téléchargées
├── yt_env/            # (créé) Environnement virtuel Python
├── downloads/         # (créé) Vidéos téléchargées
├── logs/              # (créé) Logs généraux et par session
├── DOCUMENTATION.md   # Ce fichier
├── TUTO_COOKIES.md    # Tutoriel dédié aux cookies (texte, mot de passe, clé Fernet)
└── README.md          # Point d’entrée (résumé + lien vers ce document)
```

---

## 2. Installation et démarrage rapide

1. **Cloner ou télécharger** le dépôt.
2. **(recommandé)** Placer un fichier **cookies.txt** (format Netscape) à la racine, ou **cookies.enc** (chiffré) et définir **YT_COOKIES_PASSWORD** ou **YT_COOKIES_KEY**. Voir [§ 4. Cookies](#4-cookies-détaillé) pour le détail.
3. **Lancer le script** :
   ```bash
   python telechargement.py
   ```
   (ou `python3 telechargement.py` selon ta config.)

**Premier lancement** : le script crée le dossier `yt_env/`, installe les dépendances (yt-dlp, colorama, cryptography, etc.) puis **se relance tout seul**. C’est normal. Ensuite le menu s’affiche.

### 2.2 Pourquoi un environnement virtuel (venv) ?

Le script utilise automatiquement un **environnement virtuel** (`yt_env/`) pour installer et exécuter ses dépendances. Voici les avantages :

- **Isolation** : les paquets (yt-dlp, colorama, cryptography, etc.) sont installés uniquement dans `yt_env/`, sans modifier ton Python système ni tes autres projets. Tu évites les conflits de versions entre différents logiciels.
- **Reproductibilité** : les versions des bibliothèques sont propres à ce projet ; un autre projet peut utiliser d’autres versions sans interférence.
- **Simplicité** : un seul environnement à maintenir pour ce script ; pas besoin d’installer yt-dlp ou colorama globalement sur ta machine.
- **Sécurité** : l’exécution se fait dans un contexte limité aux seules dépendances nécessaires au script.

Tu n’as rien à configurer : au premier lancement, le venv est créé et les dépendances sont installées automatiquement.

---

## 3. Utilisation

### 3.1 Choisir le mode

| Choix | Action |
|-------|--------|
| **1** (ou Entrée) | **Une chaîne** — travailler avec une chaîne YouTube (onglets + playlists). |
| **2** | **Une vidéo** — coller une seule URL de vidéo. |

### 3.2 Mode « Une vidéo » (choix 2)

1. Choisir **2**.
2. Quand le script demande **« URL de la vidéo »**, coller l’URL YouTube (ex. `https://www.youtube.com/watch?v=...` ou `https://youtu.be/...`).
3. Valider. Le téléchargement démarre.
4. La vidéo est enregistrée dans **`downloads/`**, avec le nom de l’uploader et le titre.

### 3.3 Mode « Une chaîne » (choix 1)

**Chaîne utilisée**

- Au début, la chaîne par défaut est celle de l’auteur du script.
- Quand le script demande **« Garder : Entrée | Changer : nom de chaîne ou URL »** :
  - **Entrée** = garder la chaîne affichée.
  - **Changer** = taper un handle (`@NomDeLaChaîne`) ou l’URL (`https://www.youtube.com/@NomDeLaChaîne`).

**Analyse**

Le script analyse la chaîne et affiche **« Contenu disponible »** : Vidéos (uploads), Shorts, Directs (Live), puis les playlists avec le nombre de vidéos.

**Que télécharger ?**

- **Un seul élément** : taper le numéro (ex. `1` pour « Vidéos »).
- **Plusieurs** : numéros séparés par des virgules ou espaces (ex. `1, 3, 5`).
- **Tout** : taper **`0`** pour tout télécharger (onglets + playlists).
- **Quitter sans télécharger** : taper **`q`**.

### 3.4 Pendant le téléchargement

- Les vidéos sont enregistrées dans **`downloads/`**, avec un sous-dossier par chaîne/uploader.
- **Barre de progression** et messages (✔ terminé, ⊙ déjà en archive, ✖ échec).
- Les vidéos déjà dans **`archive.txt`** sont ignorées (pas de doublon).
- **Ctrl+C** pour interrompre (certaines vidéos peuvent rester partiellement téléchargées).

### 3.5 Résumé et relance

À la fin : résumé (téléchargées, ignorées, échecs, taille de l’archive). Puis **« Relancer ? (Entrée = oui, q = quitter) »** — Entrée = nouveau tour, **q** = quitter.

### 3.6 Dossiers et fichiers importants

| Élément | Rôle |
|--------|------|
| **downloads/** | Vidéos téléchargées (organisées par chaîne/playlist). |
| **archive.txt** | Liste des vidéos déjà prises en compte ; évite les doublons. |
| **logs/** | Fichiers de log (général + un par session). Utiles en cas d’erreur. |
| **cookies.txt** / **cookies.enc** | Cookies YouTube (recommandé). À garder privé. |

### 3.7 Problèmes fréquents (utilisation)

| Problème | Piste de solution |
|----------|-------------------|
| **« Deno introuvable »** | Installer Deno (voir § 1.3) puis redémarrer le terminal. |
| **« Sign in to confirm you're not a bot »** | Ajouter ou mettre à jour les cookies (voir § 4). |
| **« Cookies expirés / invalides »** | Ré-exporter **cookies.txt** depuis le navigateur, puis recréer **cookies.enc** si besoin. |
| **Erreurs ou vidéos qui ne partent pas** | Consulter les fichiers dans **`logs/`** (notamment le log de la session). |

**Récap** : `python telechargement.py` → **1** (chaîne) ou **2** (vidéo) → suivre les questions. Les vidéos sont dans **`downloads/`**, l’archive dans **`archive.txt`**.

---

## 4. Cookies (détaillé)

Cette section explique comment fournir les **cookies YouTube** au script : en clair (`cookies.txt`), ou chiffrés avec un **mot de passe** ou une **clé Fernet** (`cookies.enc`).

### 4.1 À quoi servent les cookies ?

Ils permettent au script de s’identifier comme ton navigateur déjà connecté à YouTube. Sans eux, YouTube peut bloquer ou limiter les téléchargements (« Sign in to confirm you're not a bot », etc.). Le script accepte les cookies au **format Netscape**.

| Méthode | Fichier | Secret | Avantage / inconvénient |
|--------|---------|--------|---------------------------|
| **Texte** | `cookies.txt` | Aucun | Simple, mais en clair sur le disque. |
| **Mot de passe** | `cookies.enc` | `YT_COOKIES_PASSWORD` | Chiffré ; tu retiens un mot de passe. |
| **Clé Fernet** | `cookies.enc` | `YT_COOKIES_KEY` | Chiffré ; clé longue pour scripts / CI. |

### 4.2 Exporter les cookies depuis le navigateur

1. Ouvre **YouTube** dans ton navigateur et **connecte-toi**.
2. Installe une extension d’export au **format Netscape** (ex. **Get cookies.txt LOCALLY**, **cookies.txt**).
3. Sur la page **youtube.com**, lance l’export et enregistre le fichier sous le nom **`cookies.txt`** dans le **même dossier** que `telechargement.py`.

Les lignes (hors commentaires) ressemblent à : `domaine\tflag\tchemin\tsecure\texpiration\tnom\tvaleur`.

### 4.3 Option A — Cookies en clair (`cookies.txt`)

- Placer **`cookies.txt`** (export Netscape) dans le dossier du script.
- Lancer : `python telechargement.py`. Aucune variable d’environnement.

**Inconvénient** : fichier lisible par quiconque a accès au disque. Pour plus de confidentialité, utiliser l’option B ou C.

### 4.4 Option B — Cookies chiffrés avec un mot de passe (`cookies.enc` + `YT_COOKIES_PASSWORD`)

**Créer `cookies.enc`**

1. Avoir un **`cookies.txt`** valide (voir § 4.2).
2. Lancer : `python telechargement.py --encrypt-cookies`.
3. Saisir un **mot de passe** au clavier (masqué) ou définir **avant** la variable **`YT_COOKIES_PASSWORD`**.
4. Le fichier **`cookies.enc`** est créé. Tu peux ensuite supprimer **`cookies.txt`** si tu veux.

Avec le mot de passe, le script utilise un **salt aléatoire** (16 octets) stocké au début de `cookies.enc`. Sans ce mot de passe, les cookies ne sont pas récupérables.

**Définir le mot de passe pour l’utilisation**

À chaque lancement, fournir le **même mot de passe** via **`YT_COOKIES_PASSWORD`** :

- **Windows (CMD)** : `set YT_COOKIES_PASSWORD=ton_mot_de_passe` puis `python telechargement.py`
- **Windows (PowerShell)** : `$env:YT_COOKIES_PASSWORD = "ton_mot_de_passe"` puis `python telechargement.py`
- **Linux / macOS** : `export YT_COOKIES_PASSWORD="ton_mot_de_passe"` puis `python telechargement.py`  
  Ou en une ligne : `YT_COOKIES_PASSWORD="ton_mot_de_passe" python telechargement.py`

Conseil : pas d’espaces autour du `=`; guillemets si le mot de passe contient des caractères spéciaux.

**À la volée** : le script lit `cookies.enc` (16 premiers octets = salt, le reste = chiffré), dérive une clé Fernet (PBKDF2, 480 000 itérations), déchiffre, écrit dans un **fichier temporaire**, passe son chemin à yt-dlp, puis supprime ce fichier à la sortie. Les cookies en clair ne sont jamais écrits dans le dossier du projet.

### 4.5 Option C — Cookies chiffrés avec une clé Fernet (`cookies.enc` + `YT_COOKIES_KEY`)

**Qu’est-ce qu’une clé Fernet ?**

- Schéma de chiffrement symétrique (bibliothèque **cryptography**).
- Clé = chaîne **base64** de 44 caractères (32 octets). Même clé pour chiffrer et déchiffrer.
- Le script **déchiffre uniquement** : il attend un **`cookies.enc`** qui contient **uniquement** le blob Fernet (pas de salt).

**Générer une clé**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Conserver cette clé en lieu sûr (sans elle, les cookies chiffrés sont inutilisables).

**Créer `cookies.enc` avec la clé**

Le script ne propose pas `--encrypt-cookies` avec clé Fernet. Il faut créer **`cookies.enc`** toi-même :

```python
from pathlib import Path
from cryptography.fernet import Fernet

KEY = b"TA_CLE_BASE64_ICI"  # celle générée ci-dessus
plain = Path("cookies.txt").read_bytes()
Path("cookies.enc").write_bytes(Fernet(KEY).encrypt(plain))
```

Ou en une ligne (remplacer `TA_CLE_BASE64` par ta clé) :

```bash
python -c "from pathlib import Path; from cryptography.fernet import Fernet; Path('cookies.enc').write_bytes(Fernet(b'TA_CLE_BASE64').encrypt(Path('cookies.txt').read_bytes())); print('OK')"
```

Le fichier **`cookies.enc`** doit contenir **uniquement** le résultat de `Fernet(KEY).encrypt(contenu)`. Pas de salt.

**Utiliser la clé au lancement**

Définir **`YT_COOKIES_KEY`** avec la clé (base64) :

- **Windows (CMD)** : `set YT_COOKIES_KEY=ta_cle_base64` puis `python telechargement.py`
- **Windows (PowerShell)** : `$env:YT_COOKIES_KEY = "ta_cle_base64"` puis `python telechargement.py`
- **Linux / macOS** : `export YT_COOKIES_KEY="ta_cle_base64"` puis `python telechargement.py`

**Priorité** : si **les deux** sont définis (`YT_COOKIES_PASSWORD` et `YT_COOKIES_KEY`), le script utilise **d’abord la clé** (`YT_COOKIES_KEY`).

### 4.6 Récapitulatif des variables d’environnement (cookies)

| Variable | Utilisation | Obligatoire si |
|---------|-------------|-----------------|
| **`YT_COOKIES_PASSWORD`** | Mot de passe pour déchiffrer `cookies.enc` (créé avec `--encrypt-cookies`). | Tu utilises `cookies.enc` chiffré au **mot de passe**. |
| **`YT_COOKIES_KEY`** | Clé Fernet (base64) pour déchiffrer `cookies.enc` (créé toi-même avec Fernet). | Tu utilises `cookies.enc` chiffré avec une **clé Fernet**. |

- **`cookies.txt`** en clair : aucune variable.
- **`cookies.enc`** : il faut **au moins une** des deux (mot de passe **ou** clé).

### 4.7 Sécurité et bonnes pratiques (cookies)

- Ne **jamais** commiter `cookies.txt` ni `cookies.enc` (les ajouter au **`.gitignore`**).
- Ne **pas partager** cookies, clé ou mot de passe (accès au compte YouTube).
- Sous Windows, éviter le mot de passe en clair dans un script batch ; préférer saisie au clavier ou gestionnaire de secrets.
- **Renouveler** : si YouTube invalide les cookies, réexporter **`cookies.txt`** puis recréer **`cookies.enc`** si besoin.

### 4.8 Dépannage (cookies)

| Problème | Piste de solution |
|----------|-------------------|
| « Cookies non utilisés » | Vérifier que **`cookies.txt`** est valide (Netscape) ou que **`cookies.enc`** existe et que **`YT_COOKIES_PASSWORD`** ou **`YT_COOKIES_KEY`** est défini. |
| Erreur au déchiffrement (mot de passe) | Mauvais mot de passe ou `cookies.enc` créé autrement. Recréer avec `python telechargement.py --encrypt-cookies`. |
| Erreur au déchiffrement (clé) | **`cookies.enc`** doit contenir **uniquement** le blob Fernet (pas de salt). Vérifier le chiffrement avec `Fernet(KEY).encrypt(plain)`. |
| Le script n’utilise pas mes cookies | Si `cookies.txt` et `cookies.enc` existent et qu’une variable est définie, le script privilégie **`cookies.enc`**. Pour forcer **`cookies.txt`**, renommer ou supprimer **`cookies.enc`**. |

**Résumé en trois cas** : (1) **Texte** : `cookies.txt` dans le dossier → aucun réglage. (2) **Mot de passe** : `python telechargement.py --encrypt-cookies` puis **`YT_COOKIES_PASSWORD`** à chaque lancement. (3) **Clé Fernet** : générer une clé, chiffrer `cookies.txt` en `cookies.enc` (blob Fernet seul), puis **`YT_COOKIES_KEY`** à chaque lancement.

---

## 5. Architecture et technique

### 5.1 Logique applicative

**Flux principal**

1. **Démarrage** : vérification/création du venv → relance du script dans le venv → vérification de Deno → chargement de yt-dlp.
2. **Boucle par tour** : effacement de l’écran, réinitialisation des compteurs de session.
3. **Choix du mode** : **1** = une chaîne (analyse + menu), **2** = une vidéo (saisie d’URL).
4. **Mode chaîne** : saisie ou conservation de l’URL de chaîne → extraction à plat des onglets (Vidéos, Shorts, Directs) et des playlists → menu numéroté → l’utilisateur choisit un ou plusieurs numéros (ou 0 = tout).
5. **Construction de la liste d’URLs** : dédoublonnage, ordre préservé.
6. **Téléchargement** : un seul appel à `YoutubeDL().download(urls_to_download)` avec archive et progress hook.
7. **Résumé** : OK / ignorés (archive) / erreurs ; proposition de relancer ou quitter.

**Validation des entrées**

- **URL de chaîne** : `_normalize_channel_url()` — seuls les domaines YouTube (`youtube.com`, `www.youtube.com`, `youtu.be`) sont acceptés ; sinon retour à la chaîne par défaut.
- **URL de vidéo** : `_is_youtube_video_url()` — vérification du schéma (http/https), du host (même whitelist) et de la présence de path ou query. Toute autre URL est rejetée.

Les URLs ne sont jamais passées « en brut » à yt-dlp sans cette validation.

**Archive et doublons** : **archive.txt** (une ligne par ID de vidéo déjà téléchargée), géré par yt-dlp via `download_archive`. Les vidéos déjà présentes sont ignorées. Le script affiche « déjà en archive » / « déjà sur le disque » via un handler de log dédié.

**Extraction à plat** : pour compter les vidéos par onglet/playlist **sans télécharger**, le script utilise `extract_flat: "entries"` (métadonnées minimales uniquement). Réduit le temps et la bande passante au démarrage du mode chaîne.

**Logging** : logger général → `logs/yt_download.log` ; logger yt-dlp → fichier de session `logs/yt_YYYYMMDD_HHMMSS_<pid>.log` + handler terminal (une ligne pour les avertissements techniques) pour éviter le flood.

### 5.2 Performances

| Choix | Effet |
|-------|--------|
| **Extraction à plat** | Analyse des onglets/playlists sans télécharger les vidéos → démarrage rapide. |
| **Archive** (`download_archive`) | Évite de re-télécharger les vidéos déjà enregistrées. |
| **Reprise** (`continuedl: True`) | Reprise des téléchargements interrompus. |
| **Gestion des erreurs** (`ignoreerrors: True`) | Une vidéo en échec ne bloque pas le reste. |
| **Une ligne pour les warnings** | Terminal lisible, pas de scroll inutile. |
| **Venv dédié** | Dépendances isolées ; un seul environnement à maintenir. |

### 5.3 Technologies

| Domaine | Technologie | Rôle |
|---------|-------------|------|
| **Langage** | Python 3 | Script principal, types, `pathlib`, `logging`, `subprocess`, `urllib.parse`. |
| **Téléchargement** | **yt-dlp** | Extraction des métadonnées et téléchargement des flux (YouTube et compatibles). |
| **Runtime JS** | **Deno** | Exécution des défis JavaScript de YouTube (natif pour yt-dlp). |
| **Terminal** | **colorama** | Couleurs ANSI sous Windows (PowerShell/CMD). |
| **Environnement** | **venv** (stdlib) | Environnement virtuel `yt_env/`. |
| **Fusion média** | **ffmpeg** (via yt-dlp) | Merge audio/vidéo, format de sortie (ex. mp4). |
| **Composants distants** | **ejs** (ejs:npm, ejs:github) | Scripts utilisés par yt-dlp pour les mises à jour YouTube. |
| **Chiffrement cookies** | **cryptography** (Fernet) | Chiffrement/déchiffrement des cookies. |
| **Logs** | **logging** | Fichiers de log + handler personnalisé pour le terminal. |

### 5.4 Sécurité

| Mesure | Description |
|--------|-------------|
| **Whitelist de domaines** | Seuls `youtube.com`, `www.youtube.com`, `youtu.be` pour les URLs. Pas d’appel à des domaines arbitraires. |
| **Validation des URLs** | Parsing avec `urllib.parse` ; pas d’exécution de commandes construites à partir de la saisie utilisateur. |
| **Cookies** | Fichier local `cookies.txt` ou **`cookies.enc`** (chiffré, déchiffré à la volée). Le script ne fait que passer le **chemin** à yt-dlp. Contenu non loggé ni affiché. À ne pas commiter ni partager. |
| **Pas d’injection de commandes** | Les entrées (URL, numéros) servent à des listes d’URLs ou des index ; pas de concaténation dans des commandes shell. |
| **Venv isolé** | Dépendances dans `yt_env/` ; relance explicite dans le venv. |
| **Logs** | Peuvent contenir chemins et titres ; pas de contenu de cookies. À exclure du dépôt public (ex. `logs/` dans `.gitignore`). |

---

## 6. Développement et contribution

### 6.1 Vue d’ensemble

- **Langage** : Python 3 (annotations de types, `pathlib`, `logging`, etc.).
- **Dépendances principales** : yt-dlp, colorama, ffmpeg-python, cryptography.
- **Runtime externe** : Deno (requis par yt-dlp pour les défis YouTube).
- **Structure** : un seul script `telechargement.py` ; venv dédié `yt_env/` créé au premier run.

### 6.2 Environnement de développement

**Cloner le projet**

```bash
git clone https://github.com/ZiToUnEAnTiCipWiN32/<nom-du-repo>.git
cd <nom-du-repo>
```

**Venv** : le script crée et utilise **`yt_env/`**. Pour développer, activer ce venv :

- **Windows (PowerShell)** : `.\yt_env\Scripts\Activate.ps1`
- **Linux / macOS** : `source yt_env/bin/activate`

Puis `pip list` pour voir les paquets.

**Dépendances** : installées automatiquement au premier lancement. Pour les mettre à jour manuellement (venv activé) :

```bash
pip install -U "yt-dlp[default]" ffmpeg-python colorama cryptography
```

### 6.3 Structure du code (telechargement.py)

**Ordre général** : (1) En-tête, constantes, couleurs/terminal. (2) Venv : création puis relance du script dans le venv. (3) Deno : vérification. (4) Import yt_dlp. (5) Option `--encrypt-cookies`. (6) Dossiers, logging, cookies, progress hook, options yt-dlp (`extract_opts`, `ydl_opts`). (7) Boucle principale `main()` : mode → chaîne ou vidéo → analyse/menu si chaîne → téléchargement → résumé → relance.

**Constantes importantes** : `SCRIPT_DIR`, `VENV_DIR`, `VENV_PYTHON`, `LOG_DIR`, `OUTPUT_DIR`, `ARCHIVE_FILE`, `COOKIE_FILE`, `COOKIE_FILE_ENCRYPTED`, `DEFAULT_CHANNEL_URL`, `OUTPUT_TEMPLATE`, `REMOTE_COMPONENTS`, `UI_WIDTH`, `MENU_CONTENT_WIDTH`.

**Fonctions clés** : `_normalize_channel_url`, `_is_youtube_video_url`, `_cookies_file_valid`, `_get_cookiefile_path`, `_count_entries`, `_reset_session_state`, `progress_hook`.

### 6.4 Tester des changements

- **Exécution** : `python telechargement.py` ; tester les deux modes (chaîne + vidéo).
- **Sans grosses playlists** : mode 2 avec une courte vidéo ; mode 1 avec une chaîne peu fournie ou une seule section.
- **Logs** : `logs/yt_download.log` (résumé) ; `logs/yt_YYYYMMDD_HHMMSS_<pid>.log` (détail yt-dlp). Utiles pour déboguer (cookies, signature, etc.).

### 6.5 Points d’extension utiles

- **Options yt-dlp** : modifier **`ydl_opts`** (et éventuellement **`extract_opts`**). Doc : [yt-dlp options](https://github.com/yt-dlp/yt-dlp#usage-and-options).
- **Template de sortie** : adapter **`OUTPUT_TEMPLATE`** (variables yt-dlp : `%(title)s`, `%(uploader)s`, etc.).
- **Nouveau mode** (ex. playlist par URL) : ajouter un choix (ex. « 3 »), demander une URL, vérifier playlist, mettre l’URL dans `urls_to_download`.
- **Affichage du menu** : modifier **`_menu_line`**, **`BOX_TOP`**, **`BOX_BOT`**, **`_section_title`**, ou les constantes de couleurs.

### 6.6 Bonnes pratiques (développement)

- Ne **pas** commiter : `yt_env/`, `cookies.txt`, `cookies.enc`, `archive.txt`, `downloads/`, `logs/` (les ajouter au **`.gitignore`**).
- **Cookies** : ne jamais logger ni afficher le contenu des cookies.
- **Compatibilité** : le script gère Windows (Scripts/python.exe, colorama) et Linux/macOS (bin/python). Tester sur les OS cibles si tu modifies chemins ou terminal.
- **yt-dlp** : options et API peuvent évoluer ; en cas de régression, consulter les [releases yt-dlp](https://github.com/yt-dlp/yt-dlp/releases) et la doc.

**Résumé** : éditer `telechargement.py`, tester avec `python telechargement.py`, s’appuyer sur les logs dans **logs/**.

---

## 7. Licence et responsabilité

Ce projet est fourni à titre **éducatif**. L’utilisateur est seul responsable du respect des conditions d’utilisation de YouTube et du droit applicable (droits d’auteur, usage personnel, etc.).

---

## 8. Liens

- **YouTube** : [https://www.youtube.com/@Zitoune-anticip-WIN32](https://www.youtube.com/@Zitoune-anticip-WIN32)
- **Site** : [http://zitouneanticip.free.fr](http://zitouneanticip.free.fr)
- **GitHub** : [https://github.com/ZiToUnEAnTiCipWiN32](https://github.com/ZiToUnEAnTiCipWiN32)
