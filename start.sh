#!/bin/bash

echo "🚀 InstaSpotter Startup Script"

# Check if Python 3.11 is available
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found"
    PYTHON_CMD="python3"
else
    echo "⚠️  Python3 not found, trying to add it..."

    # Try to add Python 3.11 to environment (Replit specific)
    if [ -f "/home/runner/.pythonlibs/bin/python3" ]; then
        echo "✅ Found Python 3.11 in .pythonlibs"
        export PATH="/home/runner/.pythonlibs/bin:$PATH"
        PYTHON_CMD="/home/runner/.pythonlibs/bin/python3"
    elif [ -f "/opt/replit/python3.11/bin/python3" ]; then
        echo "✅ Found Python 3.11 in /opt/replit"
        export PATH="/opt/replit/python3.11/bin:$PATH"
        PYTHON_CMD="/opt/replit/python3.11/bin/python3"
    else
        echo "❌ Python 3.11 not found. Please use 'Add Python 3.11 to the environment' in Replit"
        echo "Then run this script again."
        exit 1
    fi
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
