@echo off
title Speed Runner - Keyboard Edition
echo Starting Speed Runner...

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%~dp0game.py"
    goto end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py "%~dp0game.py"
    goto end
)

python "%~dp0game.py"

:end
pause

