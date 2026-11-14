@echo off
title Penguin Protocol
chcp 65001 >nul
cd /d "%~dp0"

py -3 --version >nul 2>&1
if not errorlevel 1 (
    py -3 "penguin.py"
    goto end
)

python --version >nul 2>&1
if not errorlevel 1 (
    python "penguin.py"
    goto end
)

echo Install Python 3.10 or newer from the Microsoft Store or python.org

:end
pause
