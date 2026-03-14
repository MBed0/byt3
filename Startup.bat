@echo off
chcp 65001 >nul 2>&1
title 👾 Byte Setup
color 0F
cls

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                                                      ║
echo  ║   ██████╗ ██╗   ██╗████████╗███████╗                ║
echo  ║   ██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔════╝                ║
echo  ║   ██████╔╝ ╚████╔╝    ██║   █████╗                  ║
echo  ║   ██╔══██╗  ╚██╔╝     ██║   ██╔══╝                  ║
echo  ║   ██████╔╝   ██║      ██║   ███████╗                 ║
echo  ║   ╚═════╝    ╚═╝      ╚═╝   ╚══════╝                 ║
echo  ║                                                      ║
echo  ║         Local AI Assistant  ·  Setup v3.1            ║
echo  ║                                                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  ─────────────────────────────────────────────────────
echo.

:: ── Check Python ───────────────────────────────────────────────────────────
echo  [1/4]  Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ╔══════════════════════════════════════╗
    echo  ║  ERROR: Python not found!            ║
    echo  ║                                      ║
    echo  ║  Download: python.org/downloads      ║
    echo  ║  Check "Add Python to PATH"          ║
    echo  ║  during installation!                ║
    echo  ╚══════════════════════════════════════╝
    echo.
    pause & exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo         OK  %%i
echo.

:: ── Install packages ───────────────────────────────────────────────────────
echo  [2/4]  Installing required packages...
echo         flask  requests  selenium
echo.
python -m pip install flask requests selenium --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  ╔══════════════════════════════════════╗
    echo  ║  WARNING: Some packages failed.     ║
    echo  ║  Check your internet connection.    ║
    echo  ╚══════════════════════════════════════╝
) else (
    echo         OK  Packages ready.
)
echo.

:: ── Create entry point ─────────────────────────────────────────────────────
echo  [3/4]  Creating byte command...
python "%~dp0setup.py"
if errorlevel 1 (
    echo  ╔══════════════════════════════════════╗
    echo  ║  WARNING: Setup partially failed.   ║
    echo  ╚══════════════════════════════════════╝
) else (
    echo         OK  Entry point created.
)
echo.

:: ── Version test ───────────────────────────────────────────────────────────
echo  [4/4]  Testing installation...
python "%~dp0byte.py" --version
echo.

:: ── Done ───────────────────────────────────────────────────────────────────
echo  ─────────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                                                      ║
echo  ║   OK  Setup Complete!                               ║
echo  ║                                                      ║
echo  ║   1. Close this window                               ║
echo  ║   2. Open a new CMD or PowerShell                    ║
echo  ║   3. Type:   byte                                    ║
echo  ║                                                      ║
echo  ║   Other commands:                                    ║
echo  ║      byte --cmd      direct chat                    ║
echo  ║      byte --web      web interface                  ║
echo  ║      byte --quick    one-shot question              ║
echo  ║      byte --setup    re-run onboarding              ║
echo  ║                                                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
pause
