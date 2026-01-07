#!/bin/bash

echo "🚀 InstaSpotter Startup Script"

# Check if Python 3.11 is available
PYTHON_CMD=""

# Try multiple Python versions and locations
echo "🔍 Searching for Python..."

# Try python3.11 specifically
if command -v python3.11 &> /dev/null; then
    echo "✅ Found python3.11"
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    echo "✅ Found python3"
    PYTHON_CMD="python3"
else
    echo "🔍 Searching in system locations..."

    # Try Replit-specific locations
    for py_path in \
        "/home/runner/.pythonlibs/bin/python3.11" \
        "/home/runner/.pythonlibs/bin/python3" \
        "/opt/replit/python3.11/bin/python3.11" \
        "/opt/replit/python3.11/bin/python3" \
        "/usr/local/bin/python3.11" \
        "/usr/local/bin/python3" \
        "/usr/bin/python3.11" \
        "/usr/bin/python3"; do

        if [ -f "$py_path" ] && [ -x "$py_path" ]; then
            echo "✅ Found Python at: $py_path"
            PYTHON_CMD="$py_path"
            export PATH="$(dirname "$py_path"):$PATH"
            break
        fi
    done

    # If still not found, try to find any python3.x in the system
    if [ -z "$PYTHON_CMD" ]; then
        echo "🔍 Deep search for any Python 3.x..."
        FOUND_PY=$(find /usr /opt /home/runner -name "python3.*" -type f -executable 2>/dev/null | head -1)
        if [ -n "$FOUND_PY" ]; then
            echo "✅ Found Python (deep search): $FOUND_PY"
            PYTHON_CMD="$FOUND_PY"
            export PATH="$(dirname "$FOUND_PY"):$PATH"
        fi
    fi
fi

# Final check
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ No Python found!"
    echo "🔍 Available Python versions in system:"
    which python python3 python3.11 2>/dev/null || echo "No python commands in PATH"
    echo "🔍 Python files found:"
    find /usr/bin /usr/local/bin /opt -name "python*" -type f 2>/dev/null | head -10 || echo "No python files found in common locations"

    echo ""
    echo "💡 Try these solutions:"
    echo "1. Click 'Add Python 3.11 to the environment' in Replit (Tools menu)"
    echo "2. Wait a few moments after adding Python to the environment"
    echo "3. Try refreshing the page and running again"
    echo "4. Check Replit's system status"
    exit 1
fi

echo "🐍 Using Python: $PYTHON_CMD"

# Verify Python works
if ! "$PYTHON_CMD" --version &> /dev/null; then
    echo "❌ Python command not working"
    exit 1
fi

# Check if uvicorn is installed
if ! "$PYTHON_CMD" -c "import uvicorn" &> /dev/null; then
    echo "📦 Installing dependencies..."
    "$PYTHON_CMD" -m pip install --user -r requirements.txt
fi

# Run database migrations
echo "🗄️ Running database migrations..."
if [ -f "migrate.py" ]; then
    "$PYTHON_CMD" migrate.py
else
    echo "⚠️ migrate.py not found, skipping migrations"
fi

echo "🌐 Starting InstaSpotter..."
"$PYTHON_CMD" -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
