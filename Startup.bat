@echo off
title Byte Setup
color 0F
cls

echo.
echo  =========================================================
echo   BYTE v3.1 - Local AI Assistant - Setup
echo  =========================================================
echo.

:: Check Python
echo  [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found!
    echo  Download: https://python.org/downloads
    echo  Make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo         OK: %%i
echo.

:: Install packages
echo  [2/4] Installing packages...
python -m pip install flask requests selenium --quiet --disable-pip-version-check
echo         OK: flask requests selenium
echo.

:: Write correct byte.bat launcher
echo  [3/4] Creating byte launcher...

:: Get python path and byte.py path
for /f "tokens=*" %%P in ('python -c "import sys; print(sys.executable)"') do set PYEXE=%%P
set BYTEPY=%~dp0byte.py

:: Write to Scripts folder
for /f "tokens=*" %%S in ('python -c "import sys,os; print(os.path.join(sys.prefix,'Scripts'))"') do set SCRIPTS=%%S

echo @echo off > "%SCRIPTS%\byte.bat"
echo "%PYEXE%" "%BYTEPY%" %%* >> "%SCRIPTS%\byte.bat"

:: Also write next to python.exe as backup
for /f "tokens=*" %%D in ('python -c "import sys,os; print(os.path.dirname(sys.executable))"') do set PYDIR=%%D

echo @echo off > "%PYDIR%\byte.bat"
echo "%PYEXE%" "%BYTEPY%" %%* >> "%PYDIR%\byte.bat"

echo         OK: %SCRIPTS%\byte.bat
echo         OK: %PYDIR%\byte.bat
echo.
echo         Python : %PYEXE%
echo         byte.py: %BYTEPY%
echo.

:: Test
echo  [4/4] Testing...
python "%~dp0byte.py" --version
if errorlevel 1 (
    echo  ERROR: byte.py not found at: %~dp0byte.py
    echo  Make sure Startup.bat is in the same folder as byte.py
    echo.
    pause
    exit /b 1
)
echo.

echo  =========================================================
echo   Setup Complete!
echo  =========================================================
echo.
echo   1. Close this window
echo   2. Open a NEW CMD window
echo   3. Type:  byte
echo.
echo   Commands:
echo     byte            - menu
echo     byte --cmd      - direct chat
echo     byte --web      - web interface
echo     byte --quick Q  - one-shot answer
echo     byte --setup    - re-run onboarding
echo.
pause
