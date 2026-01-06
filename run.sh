#!/usr/bin/env bash
# Exit on error
set -e

echo "🔍 Searching for Python in common locations..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    echo "✅ Found Python: python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
    echo "✅ Found Python: python"
else
    echo "❌ Python not found!"
    exit 1
fi

echo "🚀 Starting InstaSpotter with $PYTHON_CMD..."

# Set PYTHONPATH to include user packages directory (needed for --user installs on Replit)
export PYTHONPATH="$HOME/.local/lib/python3.9/site-packages:$HOME/.local/lib/python3.10/site-packages:$HOME/.local/lib/python3.11/site-packages:$PYTHONPATH"
echo "📍 PYTHONPATH set to include user packages"

# Install dependencies with better error handling
echo "📦 Installing dependencies..."
# Skip pip upgrade on Replit (permission issues)
# $PIP_CMD install --upgrade pip 2>/dev/null || echo "⚠️ Could not upgrade pip (normal on Replit)"
$PIP_CMD install --user -r requirements.txt 2>/dev/null || $PIP_CMD install -r requirements.txt

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."
$PYTHON_CMD -c "import sys; print('🐍 Python path:', sys.path[:3])"
$PYTHON_CMD -c "import fastapi; print('✅ FastAPI OK')" || (echo "❌ FastAPI missing - check PYTHONPATH"; exit 1)
$PYTHON_CMD -c "import uvicorn; print('✅ Uvicorn OK')" || (echo "❌ Uvicorn missing"; exit 1)
$PYTHON_CMD -c "import sqlalchemy; print('✅ SQLAlchemy OK')" || (echo "❌ SQLAlchemy missing"; exit 1)

# Check optional dependencies (don't fail if missing)
$PYTHON_CMD -c "import instagrapi; print('✅ InstaGrapi OK')" 2>/dev/null || echo "⚠️ InstaGrapi missing (Instagram bot disabled)"
$PYTHON_CMD -c "import playwright; print('✅ Playwright OK')" 2>/dev/null || echo "⚠️ Playwright missing (HTML rendering limited)"

# Run database migrations
echo "🗄️ Running database migrations..."
$PYTHON_CMD migrate.py

# Start the web server
echo "🌐 Starting web server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
