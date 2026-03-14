@echo off
title Byte Kurulum
color 0F
echo.
echo  ┌─────────────────────────┐
echo  │   Byte StartUp v1.0     │
echo  └─────────────────────────┘
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python Not Available!
    echo Downoald Python: https://www.python.org/downloads/
    echo Tick the "Add Python to PATH" option 

    pause & exit /b 1
)

echo [1/2]  StartingUp...
python "%~dp0setup.py"

echo.
echo [2/2] Test...
python "%~dp0byte.py" --version

echo.
echo  ┌──────────────────────────────────────┐
echo  │  StartUp Completed !                 │
echo  │                                      │
echo  │  Close this window and │ echo        │ 
echo  |  open a new CMD, type: byte          |
echo  └──────────────────────────────────────┘
echo.
pause
