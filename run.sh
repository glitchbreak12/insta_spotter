#!/usr/bin/env bash
# Exit on error
set -e

echo "🔍 Searching for Python in common locations..."

# Try different Python commands and locations
PYTHON_CMD=""
PIP_CMD=""

# Try python3 first
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    echo "✅ Found Python: python3"
# Try python
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
    echo "✅ Found Python: python"
# Try common Python locations on Replit/NixOS
elif [ -x "/home/runner/.python/bin/python3" ]; then
    PYTHON_CMD="/home/runner/.python/bin/python3"
    PIP_CMD="/home/runner/.python/bin/pip3"
    echo "✅ Found Python: /home/runner/.python/bin/python3"
elif [ -x "/nix/store/*/bin/python3" ]; then
    PYTHON_CMD=$(find /nix/store -name python3 -type f -executable 2>/dev/null | head -1)
    PIP_CMD=$(find /nix/store -name pip3 -type f -executable 2>/dev/null | head -1)
    echo "✅ Found Python: $PYTHON_CMD"
elif [ -x "/usr/bin/python3" ]; then
    PYTHON_CMD="/usr/bin/python3"
    PIP_CMD="/usr/bin/pip3"
    echo "✅ Found Python: /usr/bin/python3"
else
    echo "❌ Python not found in any location!"
    echo "🔍 Available commands:"
    which python python3 2>/dev/null || echo "No python commands found"
    echo "🔍 Checking common paths:"
    ls -la /usr/bin/python* 2>/dev/null || echo "No python in /usr/bin/"
    ls -la /nix/store/*/bin/python* 2>/dev/null | head -5 || echo "No python in /nix/store/"
    exit 1
fi

echo "🚀 Using Python: $PYTHON_CMD"
echo "📦 Using Pip: $PIP_CMD"

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
