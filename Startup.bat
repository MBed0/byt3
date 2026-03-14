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
    echo [HATA] Python bulunamadi!
    echo Python yukle: https://www.python.org/downloads/
    echo Kurulurken "Add Python to PATH" secenegini isaretle!
    pause & exit /b 1
)

echo [1/2] Kurulum basliyor...
python "%~dp0setup.py"

echo.
echo [2/2] Test...
python "%~dp0byte.py" --version

echo.
echo  ┌──────────────────────────────────────┐
echo  │  Kurulum tamamlandi!                 │
echo  │                                      │
echo  │  Bu pencereyi KAPAT ve               │
echo  │  yeni bir CMD ac, yaz: byte          │
echo  └──────────────────────────────────────┘
echo.
pause
