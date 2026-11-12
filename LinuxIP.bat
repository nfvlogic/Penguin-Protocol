@echo off
title LinuxIP
chcp 65001 >nul
cd /d "%~dp0"

py -3 --version >nul 2>&1
if not errorlevel 1 (
    py -3 "linux_13.4.py"
    goto end
)

python --version >nul 2>&1
if not errorlevel 1 (
    python "linux_13.4.py"
    goto end
)

echo Install Python 3 from the Microsoft Store or python.org

:end
pause
