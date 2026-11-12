@echo off
setlocal
cd /d "%~dp0"
title YouTube Downloader

where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed. Install it from https://www.python.org/downloads/ and tick "Add Python to PATH".
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Setting up for first run...
    python -m venv .venv
    if errorlevel 1 (
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet --upgrade -r requirements.txt
if errorlevel 1 (
    pause
    exit /b 1
)

".venv\Scripts\python.exe" app.py %*
pause
