@echo off
REM Setup script for Windows users

echo 🚀 Setting up Taobao HTML Data Extractor...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment if it doesn't exist
if not exist "extract_html" (
    echo 📦 Creating virtual environment...
    python -m venv extract_html
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call extract_html\Scripts\activate.bat

REM Install requirements
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Create data directory if it doesn't exist
if not exist "data" (
    echo 📁 Creating data directory...
    mkdir data
)

REM Create output directory if it doesn't exist
if not exist "output" (
    echo 📁 Creating output directory...
    mkdir output
)

echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Place your Taobao HTML file in: data\input.html
echo 2. Run: python extract_taobao.py
echo 3. Check results in: output\
echo.
echo For more information, see README.md
pause