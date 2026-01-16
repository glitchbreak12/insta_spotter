# Execute all tasks: git push + rebuild
cd $PSScriptRoot

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📤 Step 1: Git commit and push" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

git add -A
Write-Host "✅ Staged changes" -ForegroundColor Green

git commit -m "fix(core): image generation, carousel method, card_info v5 style, recreate endpoints"
Write-Host "✅ Committed" -ForegroundColor Green

git push origin main
Write-Host "✅ Pushed to origin/main" -ForegroundColor Green

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🔄 Step 2: Rebuild INFO cards with v5 style" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

python quick_rebuild.py

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "✅ ALL DONE!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
