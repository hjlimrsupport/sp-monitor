@echo off
setlocal
title Splashtop Monitor Launcher

echo ------------------------------------------
echo Splashtop JP Monitoring System Starting...
echo ------------------------------------------

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed. 
        echo Please install Python from https://www.python.org/
        pause
        exit /b
    ) else (
        set PY=python3
    )
) else (
    set PY=python
)

:: 2. Install Dependencies
echo [*] Checking required libraries...
%PY% -m pip install -r requirements.txt --quiet

:: 3. Run Launcher
echo [*] Starting Analysis and Server...
%PY% launcher.py

pause
