#!/bin/bash
# Auto push script for Windows PowerShell/Git Bash

cd "$(dirname "$0")"

echo "🚀 Committing changes..."
git add -A

git commit -m "fix(core): post_single_message image generation, daily_post_task carousel method, recreate info-cards defaults"

echo "📤 Pushing to origin/main..."
git push origin main

echo "✅ Done!"
