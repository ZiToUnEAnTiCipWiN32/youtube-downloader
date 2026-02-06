# Tuto — Cookies (texte, mot de passe ou clé Fernet)

Ce tutoriel explique en détail comment fournir les **cookies YouTube** au script : en clair (`cookies.txt`), ou chiffrés avec un **mot de passe** ou une **clé Fernet** (`cookies.enc`).

---

## 1. À quoi servent les cookies ?

Les cookies permettent au script de s’identifier comme ton navigateur déjà connecté à YouTube. Sans eux, YouTube peut bloquer ou limiter les téléchargements (« Sign in to confirm you're not a bot », etc.).  
Le script accepte les cookies au **format Netscape** (un fichier texte avec des lignes `domaine\tflag\tchemin\tsecure\texpiration\tnom\tvaleur`).

Tu peux les stocker de trois façons :

| Méthode | Fichier | Secret | Avantage / inconvénient |
|--------|---------|--------|---------------------------|
| **Texte** | `cookies.txt` | Aucun | Simple, mais en clair sur le disque. |
| **Mot de passe** | `cookies.enc` | `YT_COOKIES_PASSWORD` | Chiffré ; tu retiens un mot de passe. |
| **Clé Fernet** | `cookies.enc` | `YT_COOKIES_KEY` | Chiffré ; clé longue pour scripts / CI. |

La suite détaille chaque méthode.

---

## 2. Exporter les cookies depuis le navigateur

Avant toute chose, il faut obtenir un fichier **cookies.txt** au format Netscape.

1. Ouvre **YouTube** dans ton navigateur et **connecte-toi** à ton compte.
2. Installe une extension d’export de cookies, par exemple :
   - **Get cookies.txt LOCALLY** (Chrome / Firefox)
   - **cookies.txt** (Chrome)
   - Ou toute extension qui exporte au **format Netscape**.
3. Sur la page **youtube.com**, lance l’export et enregistre le fichier sous le nom **`cookies.txt`** dans le **même dossier** que `telechargement.py`.

Tu dois avoir un fichier dont les lignes (hors commentaires) ressemblent à :

```
.youtube.com	TRUE	/	TRUE	1234567890	CONSENT	YES+...
```

Une fois ce fichier en place, tu peux soit l’utiliser en clair, soit le chiffrer (mot de passe ou clé Fernet).

---

## 3. Option A — Utiliser les cookies en clair (`cookies.txt`)

- Place **`cookies.txt`** (export Netscape) dans le dossier du script.
- Lance le script : `python telechargement.py`.  
  Aucune variable d’environnement à définir.

**Inconvénient** : le fichier est lisible par quiconque a accès au disque. Pour plus de confidentialité, utilise l’option B ou C.

---

## 4. Option B — Cookies chiffrés avec un mot de passe (`cookies.enc` + `YT_COOKIES_PASSWORD`)

Le script peut créer un fichier **`cookies.enc`** à partir de **`cookies.txt`**, en le chiffrant avec un **mot de passe**. Au lancement, tu fournis ce mot de passe (souvent via une variable d’environnement) et le script déchiffre les cookies à la volée.

### 4.1 Créer `cookies.enc` à partir de `cookies.txt`

1. Assure-toi d’avoir un **`cookies.txt`** valide (voir § 2).
2. Lance la commande :

   ```bash
   python telechargement.py --encrypt-cookies
   ```

3. Le script te demande un **mot de passe** :
   - Soit tu le saisis au clavier (la saisie est masquée).
   - Soit tu définis **avant** la variable d’environnement **`YT_COOKIES_PASSWORD`** (voir ci-dessous) ; dans ce cas, le script l’utilise sans demander.

4. Un fichier **`cookies.enc`** est créé dans le dossier du script.  
   Tu peux ensuite **supprimer** `cookies.txt` si tu veux (il ne sert plus qu’à la création de `cookies.enc`).

**Important** : avec le **mot de passe**, le script utilise un **salt aléatoire** (16 octets) stocké au début de `cookies.enc`. Il est donc impossible de retrouver les cookies sans ce mot de passe.

### 4.2 Définir le mot de passe pour l’utilisation

À chaque lancement de `python telechargement.py`, le script a besoin du **même mot de passe** pour déchiffrer `cookies.enc`. Tu peux le fournir via la variable d’environnement **`YT_COOKIES_PASSWORD`**.

**Windows (CMD)** :

```cmd
set YT_COOKIES_PASSWORD=ton_mot_de_passe
python telechargement.py
```

**Windows (PowerShell)** :

```powershell
$env:YT_COOKIES_PASSWORD = "ton_mot_de_passe"
python telechargement.py
```

**Linux / macOS (bash / zsh)** :

```bash
export YT_COOKIES_PASSWORD="ton_mot_de_passe"
python telechargement.py
```

Ou en une seule ligne (évite que le mot de passe reste dans l’historique du shell) :

```bash
YT_COOKIES_PASSWORD="ton_mot_de_passe" python telechargement.py
```

**Conseil** : ne mets pas d’espaces autour du `=`. Si ton mot de passe contient des caractères spéciaux, mets-le entre guillemets (comme ci-dessus).

### 4.3 Ce qui se passe à la volée

1. Au démarrage, si le script voit **`cookies.enc`** et **`YT_COOKIES_PASSWORD`**, il :
   - lit le fichier (16 premiers octets = salt, le reste = contenu chiffré),
   - dérive une clé Fernet à partir du mot de passe et du salt (PBKDF2, 480 000 itérations),
   - déchiffre le contenu,
   - écrit le résultat dans un **fichier temporaire**,
   - passe le chemin de ce fichier à yt-dlp.
2. À la fin de l’exécution, le script supprime ce fichier temporaire.

Les cookies en clair ne sont donc jamais écrits dans le dossier du projet une fois que tu utilises `cookies.enc`.

---

## 5. Option C — Cookies chiffrés avec une clé Fernet (`cookies.enc` + `YT_COOKIES_KEY`)

Avec la **clé Fernet**, tu chiffres toi-même le contenu avec une clé symétrique (base64). C’est pratique pour des scripts, de l’automatisation ou des environnements où tu préfères gérer une clé plutôt qu’un mot de passe.

### 5.1 Qu’est-ce qu’une clé Fernet ?

- **Fernet** est un schéma de chiffrement symétrique (bibliothèque **cryptography** en Python).
- La clé est une chaîne **base64** de 44 caractères (elle encode 32 octets).
- **Même clé** pour chiffrer et déchiffrer : celui qui a la clé peut déchiffrer les cookies.

Le script, lui, ne fait que **déchiffrer** : il attend un fichier **`cookies.enc`** qui contient **uniquement** le blob Fernet (pas de salt ; format différent du mot de passe).

### 5.2 Générer une clé Fernet

Dans un terminal, avec le venv du projet (ou un Python où `cryptography` est installé) :

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Tu obtiens une chaîne du type :

```
dGhpc19pc19hX2V4YW1wbGVfa2V5XzEyMzQ1Njc4OTA=
```

**Conserve cette clé** dans un endroit sûr (gestionnaire de mots de passe, variable d’environnement secrète, etc.). Sans elle, les cookies chiffrés sont inutilisables.

### 5.3 Créer `cookies.enc` avec la clé Fernet

Le script **ne** propose **pas** d’option `--encrypt-cookies` avec clé Fernet (seulement avec mot de passe). Tu dois donc créer **`cookies.enc`** toi-même à partir de **`cookies.txt`** et de ta clé.

**Exemple avec Python** (à lancer dans le dossier du script, avec `cookies.txt` présent) :

```python
from pathlib import Path
from cryptography.fernet import Fernet

# Remplace par ta clé (celle générée à l'étape 5.2)
KEY = b"dGhpc19pc19hX2V4YW1wbGVfa2V5XzEyMzQ1Njc4OTA="

cookies_txt = Path("cookies.txt")
cookies_enc = Path("cookies.enc")

plain = cookies_txt.read_bytes()
f = Fernet(KEY)
encrypted = f.encrypt(plain)
cookies_enc.write_bytes(encrypted)
print("cookies.enc créé.")
```

Ou en **une ligne** (remplace `TA_CLE_BASE64` par ta clé) :

```bash
python -c "from pathlib import Path; from cryptography.fernet import Fernet; Path('cookies.enc').write_bytes(Fernet(b'TA_CLE_BASE64').encrypt(Path('cookies.txt').read_bytes())); print('OK')"
```

**Format attendu par le script** : le fichier **`cookies.enc`** doit contenir **uniquement** le résultat de `Fernet(KEY).encrypt(contenu_cookies_txt)`. Pas de salt, pas d’en-tête : juste le blob Fernet.

### 5.4 Utiliser la clé au lancement du script

Définis la variable d’environnement **`YT_COOKIES_KEY`** avec ta clé (en base64, 44 caractères).

**Windows (CMD)** :

```cmd
set YT_COOKIES_KEY=dGhpc19pc19hX2V4YW1wbGVfa2V5XzEyMzQ1Njc4OTA=
python telechargement.py
```

**Windows (PowerShell)** :

```powershell
$env:YT_COOKIES_KEY = "dGhpc19pc19hX2V4YW1wbGVfa2V5XzEyMzQ1Njc4OTA="
python telechargement.py
```

**Linux / macOS** :

```bash
export YT_COOKIES_KEY="dGhpc19pc19hX2V4YW1wbGVfa2V5XzEyMzQ1Njc4OTA="
python telechargement.py
```

Si **`cookies.enc`** existe et **`YT_COOKIES_KEY`** est défini, le script déchiffre le **fichier entier** avec cette clé (sans salt), écrit le résultat dans un fichier temporaire, le passe à yt-dlp, puis supprime le temporaire à la sortie.

### 5.5 Priorité : mot de passe ou clé ?

Si **les deux** sont définis (`YT_COOKIES_PASSWORD` et `YT_COOKIES_KEY`), le script utilise **d’abord la clé** (`YT_COOKIES_KEY`). Donc pour utiliser uniquement le mot de passe, ne définis pas `YT_COOKIES_KEY`.

---

## 6. Récapitulatif des variables d’environnement

| Variable | Utilisation | Obligatoire si |
|---------|-------------|-----------------|
| **`YT_COOKIES_PASSWORD`** | Mot de passe pour déchiffrer `cookies.enc` (créé avec `--encrypt-cookies`). | Tu utilises `cookies.enc` chiffré au **mot de passe**. |
| **`YT_COOKIES_KEY`** | Clé Fernet (base64) pour déchiffrer `cookies.enc` (créé toi-même avec Fernet). | Tu utilises `cookies.enc` chiffré avec une **clé Fernet**. |

- Pour **`cookies.txt`** en clair : aucune variable.
- Pour **`cookies.enc`** : il faut **au moins une** des deux (mot de passe **ou** clé).

---

## 7. Sécurité et bonnes pratiques

- **Ne commite jamais** `cookies.txt` ni `cookies.enc` dans un dépôt Git. Ajoute-les au **`.gitignore`** (et éventuellement `YT_COOKIES_*` dans un fichier d’env non versionné).
- **Ne partage pas** tes cookies ni ta clé / mot de passe. Les cookies donnent accès à ton compte YouTube.
- **Variable d’environnement** : sous Windows, éviter de laisser le mot de passe en clair dans un script batch visible. Préférer une saisie au clavier ou un gestionnaire de secrets.
- **Renouveler les cookies** : YouTube peut invalider les cookies. Si le script indique des erreurs type « cookies invalides » ou « Sign in », réexporte **`cookies.txt`** depuis le navigateur, puis recrée **`cookies.enc`** si tu utilises le chiffrement.

---

## 8. Dépannage

| Problème | Piste de solution |
|----------|-------------------|
| « Cookies non utilisés » | Vérifier que **`cookies.txt`** est valide (format Netscape) ou que **`cookies.enc`** existe et que **`YT_COOKIES_PASSWORD`** ou **`YT_COOKIES_KEY`** est bien défini. |
| Erreur au déchiffrement (mot de passe) | Mauvais mot de passe, ou **`cookies.enc`** créé avec un autre outil / salt. Recrée **`cookies.enc`** avec `python telechargement.py --encrypt-cookies`. |
| Erreur au déchiffrement (clé) | **`cookies.enc`** doit contenir **uniquement** le blob Fernet (pas de salt). Vérifier que tu as bien chiffré avec `Fernet(KEY).encrypt(plain)` et rien d’autre. |
| Le script n’utilise pas mes cookies | Si **`cookies.txt`** et **`cookies.enc`** existent et qu’une variable est définie, le script privilégie **`cookies.enc`**. Pour forcer **`cookies.txt`**, renomme ou supprime **`cookies.enc`**. |

---

## 9. Résumé en trois cas

1. **Texte** : tu mets **`cookies.txt`** dans le dossier → aucun réglage.
2. **Mot de passe** : tu crées **`cookies.enc`** avec `python telechargement.py --encrypt-cookies`, puis tu définis **`YT_COOKIES_PASSWORD`** à chaque lancement.
3. **Clé Fernet** : tu génères une clé, tu chiffres **`cookies.txt`** en **`cookies.enc`** (uniquement le blob Fernet), puis tu définis **`YT_COOKIES_KEY`** à chaque lancement.

Pour plus d’infos sur l’utilisation générale du script, voir **[TUTO_UTILISATION.md](TUTO_UTILISATION.md)**.
