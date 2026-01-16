@echo off
REM Auto push script for Windows CMD

cd /d "%~dp0"

echo 🚀 Committing changes...
git add -A

git commit -m "fix(core): post_single_message image generation, daily_post_task carousel method, recreate info-cards defaults"

echo 📤 Pushing to origin/main...
git push origin main

echo ✅ Done!
pause
