@echo off
REM ESECUZIONE FINALE: Git push + Ricrea info cards

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ================================================================================
echo FASE 1: GIT COMMIT ^& PUSH
echo ================================================================================

git add -A
if errorlevel 1 goto error

git commit -m "fix(final): core fixes, v5 templates, publish-now, recreate endpoints"
if errorlevel 1 goto skip_push

git push origin main
if errorlevel 1 goto error

:skip_push
echo.
echo ✅ Git push completed
echo.

echo ================================================================================
echo FASE 2: RICREAZIONE IMMEDIATA INFO CARD DA ZERO
echo ================================================================================

python RICREA_ADESSO.py
if errorlevel 1 goto error

echo.
echo ✅ INFO CARDS RICREATE CON SUCCESSO!
echo.
pause
exit /b 0

:error
echo.
echo ❌ ERRORE durante l'esecuzione
echo.
pause
exit /b 1
