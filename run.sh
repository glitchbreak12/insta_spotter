#!/usr/bin/env bash
# Exit on error
set -e

echo "🔍 Searching for Python in common locations..."

# Try different Python commands and locations
PYTHON_CMD=""
PIP_CMD=""

# Function to test if Python works
test_python() {
    local cmd=$1
    if [ -x "$cmd" ] && "$cmd" --version >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Try python3 first (most common)
if test_python python3; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    echo "✅ Found Python: python3"
# Try python (fallback)
elif test_python python; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
    echo "✅ Found Python: python"
# Try direct paths (Replit/NixOS specific)
elif test_python "/home/runner/.python/bin/python3"; then
    PYTHON_CMD="/home/runner/.python/bin/python3"
    PIP_CMD="/home/runner/.python/bin/pip3"
    echo "✅ Found Python: /home/runner/.python/bin/python3"
elif test_python "/usr/bin/python3"; then
    PYTHON_CMD="/usr/bin/python3"
    PIP_CMD="/usr/bin/pip3"
    echo "✅ Found Python: /usr/bin/python3"
elif test_python "/usr/local/bin/python3"; then
    PYTHON_CMD="/usr/local/bin/python3"
    PIP_CMD="/usr/local/bin/pip3"
    echo "✅ Found Python: /usr/local/bin/python3"
# Try Replit-specific Python installations
elif test_python "/opt/replit/python3/bin/python3"; then
    PYTHON_CMD="/opt/replit/python3/bin/python3"
    PIP_CMD="/opt/replit/python3/bin/pip3"
    echo "✅ Found Python: /opt/replit/python3/bin/python3"
elif test_python "/opt/python/3.x/bin/python3"; then
    PYTHON_CMD="/opt/python/3.x/bin/python3"
    PIP_CMD="/opt/python/3.x/bin/pip3"
    echo "✅ Found Python: /opt/python/3.x/bin/python3"
# Try to find in Nix store (quick search)
else
    echo "🔍 Quick search in common Nix locations..."

    # Quick check of most common Nix locations
    for nix_path in "/nix/store"/*/bin/python3; do
        if [ -f "$nix_path" ] && test_python "$nix_path"; then
            PYTHON_CMD="$nix_path"
            nix_dir=$(dirname "$nix_path")
            if [ -x "$nix_dir/pip3" ]; then
                PIP_CMD="$nix_dir/pip3"
            else
                PIP_CMD="$PYTHON_CMD -m pip"
            fi
            echo "✅ Found Python: $PYTHON_CMD"
            break
        fi
    done

    # If still not found, try a faster find with timeout
    if [ -z "$PYTHON_CMD" ]; then
        echo "🔍 Faster search in Nix store..."
        # Use a more targeted find command with timeout
        timeout 10 find /nix/store -maxdepth 2 -name python3 -type f -executable 2>/dev/null | head -3 | while read -r nix_python; do
            if test_python "$nix_python"; then
                PYTHON_CMD="$nix_python"
                nix_dir=$(dirname "$nix_python")
                if [ -x "$nix_dir/pip3" ]; then
                    PIP_CMD="$nix_dir/pip3"
                else
                    PIP_CMD="$nix_python -m pip"
                fi
                echo "✅ Found Python: $PYTHON_CMD"
                break
            fi
        done
    fi

    # Emergency fallback - try direct python3 command again
    if [ -z "$PYTHON_CMD" ]; then
        echo "🔍 Emergency fallback..."
        if test_python python3 2>/dev/null; then
            PYTHON_CMD="python3"
            PIP_CMD="pip3"
            echo "✅ Found Python (emergency): python3"
        fi
    fi
fi

# Final check
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python not found!"
    echo "🔍 Debugging info:"
    echo "Current PATH: $PATH"
    echo "Available python commands:"
    compgen -c | grep -E "^python" || echo "No python commands in PATH"
    echo "Checking common locations:"
    for loc in /usr/bin/python* /usr/local/bin/python* /home/runner/.python/bin/python*; do
        if [ -f "$loc" ]; then
            echo "Found: $loc"
            if [ -x "$loc" ]; then
                echo "  - Executable: YES"
                "$loc" --version 2>/dev/null || echo "  - Version check failed"
            else
                echo "  - Executable: NO"
            fi
        fi
    done
    echo "Trying to find any python3 in system..."
    find /usr /nix/store -name python3 -type f -executable 2>/dev/null | head -3 || echo "No python3 found in system search"
    exit 1
fi

echo "🚀 Using Python: $PYTHON_CMD"
echo "📦 Using Pip: $PIP_CMD"

# Verify Python works
if ! "$PYTHON_CMD" --version >/dev/null 2>&1; then
    echo "❌ Python command found but not working!"
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
