@echo off
if not defined IN_CMD (
    set IN_CMD=1
    cmd /k "%~f0" %*
    exit /b
)

title CVAmp Launcher
cd /d "%~dp0"

echo ===================================================
echo       CVAmp Viewer Amplifier Launcher
echo ===================================================
echo.

set PYTHON_EXE=

py -3 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=py -3
    goto PYTHON_FOUND
)

python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
    goto PYTHON_FOUND
)

py -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=py
    goto PYTHON_FOUND
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python314\python.exe" & goto PYTHON_FOUND
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python313\python.exe" & goto PYTHON_FOUND
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python312\python.exe" & goto PYTHON_FOUND
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python311\python.exe" & goto PYTHON_FOUND
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON_EXE="%LOCALAPPDATA%\Programs\Python\Python310\python.exe" & goto PYTHON_FOUND
if exist "C:\Python314\python.exe" set PYTHON_EXE="C:\Python314\python.exe" & goto PYTHON_FOUND
if exist "C:\Python313\python.exe" set PYTHON_EXE="C:\Python313\python.exe" & goto PYTHON_FOUND
if exist "C:\Python312\python.exe" set PYTHON_EXE="C:\Python312\python.exe" & goto PYTHON_FOUND
if exist "C:\Python311\python.exe" set PYTHON_EXE="C:\Python311\python.exe" & goto PYTHON_FOUND
if exist "C:\Python310\python.exe" set PYTHON_EXE="C:\Python310\python.exe" & goto PYTHON_FOUND

:PYTHON_NOT_FOUND
echo [ERROR] Python was not found!
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check Add python.exe to PATH during installation.
pause
exit /b 1

:PYTHON_FOUND
echo [INFO] Python detected:
%PYTHON_EXE% --version
echo.

if exist "venv\Scripts\python.exe" goto VENV_EXISTS

echo [INFO] Creating virtual environment venv...
%PYTHON_EXE% -m venv venv
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)
echo [INFO] Virtual environment created.
echo.

:VENV_EXISTS

echo [INFO] Installing dependencies from requirements.txt...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo.

echo [INFO] Installing Playwright Chromium browser...
venv\Scripts\python.exe -m playwright install chromium
echo.

if not exist "proxy" mkdir "proxy"
if not exist "proxy\proxy_list.txt" echo # Format: ip:port or ip:port:user:password > "proxy\proxy_list.txt"

echo ===================================================
echo [INFO] Launching CVAmp GUI
echo ===================================================
echo.
venv\Scripts\python.exe main_gui.py

echo.
echo ===================================================
echo Process finished.
echo ===================================================
pause
