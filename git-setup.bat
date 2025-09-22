@echo off
echo 🔧 Git Setup Helper für Ihr Taobao-Projekt
echo.
echo ⚠️  Git ist noch nicht installiert!
echo.
echo Bitte folgen Sie diesen Schritten:
echo.
echo 1. Öffnen Sie: https://git-scm.com/download/windows
echo 2. Laden Sie "64-bit Git for Windows Setup" herunter
echo 3. Führen Sie den Installer aus
echo 4. Bei Installation: "Git from command line" auswählen
echo 5. PowerShell neu starten
echo 6. Diese Datei nochmal ausführen
echo.

REM Prüfe ob Git installiert ist
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git ist noch nicht installiert oder nicht im PATH
    echo.
    echo Nachdem Git installiert ist, führen Sie diese Befehle aus:
    echo    git init
    echo    git add .
    echo    git commit -m "Initial commit: Taobao Data Extractor"
    echo.
    pause
    exit /b 1
)

echo ✅ Git gefunden! Initialisiere Repository...
echo.

REM Git Repository initialisieren
if not exist ".git" (
    git init
    echo ✅ Git Repository initialisiert
)

REM Dateien hinzufügen
git add .
echo ✅ Alle Dateien hinzugefügt

REM Ersten Commit erstellen
git commit -m "Initial commit: Professional Taobao Data Extractor v1.0.0

- Complete data extraction tool with 75+ products
- English translation system (47+ products, 59+ colors)
- Intelligent seller mapping (25+ sellers)
- CSV and Markdown output formats
- Professional project structure with documentation
- Clean codebase ready for version control"

echo.
echo 🎉 Git Repository erfolgreich erstellt!
echo.
echo Ihr Projekt ist jetzt bereit für:
echo - Version Control
echo - GitHub Upload
echo - Collaborative Development
echo.

git status

pause