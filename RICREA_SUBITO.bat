@echo off
title RICREA INFO CARD DA ZERO
cls
cd /d "%~dp0"

echo.
echo ========================================
echo CANCELLA E RICREA INFO CARD DA ZERO
echo ========================================
echo.

python DELETE_AND_RECREATE_NOW.py

echo.
echo Premi un tasto per chiudere...
pause >nul
