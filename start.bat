@echo off
setlocal EnableDelayedExpansion
title CVAmp - Crude Viewer Amplifier

cd /d "%~dp0"

echo ===================================================
echo       CVAmp (Crude Viewer Amplifier) Launcher
echo ===================================================
echo.

REM 1. Find Python executable
set "PYTHON_EXE="

REM Try 'py -3'
py -3 -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXE=py -3"
    goto :PYTHON_FOUND
)

REM Try 'python'
python -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXE=python"
    goto :PYTHON_FOUND
)

REM Try 'py'
py -c "import sys" >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_EXE=py"
    goto :PYTHON_FOUND
)

REM Scan common Windows installation directories
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python310\python.exe"
) do (
    if exist %%D (
        set "PYTHON_EXE=%%~D"
        goto :PYTHON_FOUND
    )
)

:PYTHON_NOT_FOUND
echo [ERROR] Python was not found on your system!
echo.
echo Please download and install Python (3.10 - 3.12) from:
echo https://www.python.org/downloads/
echo.
echo [IMPORTANT] When installing, MAKE SURE to check:
echo  [x] "Add python.exe to PATH"
echo.
pause
exit /b 1

:PYTHON_FOUND
echo [INFO] Python detected:
!PYTHON_EXE! --version
echo.

REM 2. Create virtual environment if missing
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Setting up virtual environment (venv)...
    !PYTHON_EXE! -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment!
        echo Please ensure Python is installed with standard venv support.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created successfully.
    echo.
)

REM 3. Upgrade pip and install requirements
echo [INFO] Checking dependencies (requirements.txt)...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Failed to install required Python packages!
    pause
    exit /b 1
)
echo.

REM 4. Ensure Playwright Chromium browser binary is downloaded
echo [INFO] Checking Playwright Chromium browser...
venv\Scripts\python.exe -m playwright install chromium
if !errorlevel! neq 0 (
    echo [WARNING] Playwright browser installation finished with warnings.
)
echo.

REM 5. Ensure proxy directory and default file exist
if not exist "proxy" (
    mkdir "proxy"
)
if not exist "proxy\proxy_list.txt" (
    echo # Format: ip:port or ip:port:user:password > "proxy\proxy_list.txt"
    echo [INFO] Initialized default proxy\proxy_list.txt
)

REM 6. Run CVAmp
echo ===================================================
echo [INFO] Launching CVAmp GUI...
echo ===================================================
echo.
venv\Scripts\python.exe main_gui.py

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Application exited with error code !errorlevel!
)

echo.
echo ===================================================
echo Process finished.
echo ===================================================
pause
