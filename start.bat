@echo off
setlocal enabledelayedexpansion
title CVAmp - Crude Viewer Amplifier

cd /d "%~dp0"

echo ===================================================
echo       CVAmp (Crude Viewer Amplifier) Launcher
echo ===================================================
echo.

:: 1. Check Python installation
set "PYTHON_CMD="
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
) else (
    py -3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=py -3"
    ) else (
        py --version >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_CMD=py"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python is not installed or not found in system PATH!
    echo Please install Python 3.10, 3.11, or 3.12 from: https://www.python.org/downloads/
    echo IMPORTANT: Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [INFO] Found Python:
%PYTHON_CMD% --version
echo.

:: 2. Setup virtual environment (venv)
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment (venv)...
    %PYTHON_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created successfully.
)

:: 3. Activate venv
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

:: 4. Install dependencies
echo [INFO] Checking and installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install required Python packages!
    pause
    exit /b 1
)

:: 5. Install Playwright Chromium browser if missing
echo [INFO] Ensuring Playwright Chromium is installed...
python -m playwright install chromium
if !errorlevel! neq 0 (
    echo [WARNING] Playwright browser installation finished with warnings.
)

:: 6. Ensure proxy directory and file exist
if not exist "proxy" (
    mkdir "proxy"
)
if not exist "proxy\proxy_list.txt" (
    echo # Format: ip:port or ip:port:user:password > "proxy\proxy_list.txt"
    echo [INFO] Created default proxy\proxy_list.txt
)

:: 7. Launch CVAmp
echo.
echo [INFO] Starting CVAmp...
echo ===================================================
python main_gui.py

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)

deactivate >nul 2>&1
