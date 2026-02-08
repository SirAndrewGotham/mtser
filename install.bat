@echo off
REM install.bat
echo Installing MTSer - MTS Link Webinar Downloader

REM Check Python version
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install httpx tqdm moviepy numpy

echo.
echo ✅ Installation complete!
echo.
echo To use mtser:
echo   1. Activate virtual environment: venv\Scripts\activate.bat
echo   2. Run: python mtser.py --interactive
echo.
pause
