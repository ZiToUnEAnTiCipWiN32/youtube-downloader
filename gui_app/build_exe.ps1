# Script de construction de l'executable YouTube-Downloader (PyInstaller)
# a lancer depuis le dossier gui_app ou depuis n'importe où (le script se place dans gui_app).

$ErrorActionPreference = "Stop"
$GuiAppDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

Set-Location $GuiAppDir
Write-Host "Dossier de travail : $GuiAppDir" -ForegroundColor Cyan

# Creer le venv s'il n'existe pas
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Creation du venv..." -ForegroundColor Yellow
    python -m venv venv
}

# Mettre a jour pip et installer les dependances
Write-Host "Installation des dependances..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .\venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
& .\venv\Scripts\python.exe -m pip install pyinstaller --quiet

# Arguments PyInstaller (icône si presente)
$pyinstallerArgs = @("--onefile", "--windowed", "--name", "YouTube-Downloader", "start.py")
if (Test-Path "icon.ico") {
    $pyinstallerArgs = @("--onefile", "--windowed", "--icon", "icon.ico", "--add-data", "icon.ico;.", "--name", "YouTube-Downloader", "start.py")
} else {
    Write-Host "Attention : icon.ico absent dans gui_app. L'exe et la fenetre n'auront pas d'icône personnalisee." -ForegroundColor Yellow
}

# Lancer PyInstaller
Write-Host "Construction de l'exe avec PyInstaller..." -ForegroundColor Yellow
& .\venv\Scripts\pyinstaller.exe @pyinstallerArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "Termine. Executable : $GuiAppDir\dist\YouTube-Downloader.exe" -ForegroundColor Green
} else {
    Write-Host "Erreur lors de la construction." -ForegroundColor Red
    exit 1
}
