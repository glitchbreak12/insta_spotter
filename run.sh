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

# Install dependencies with better error handling
echo "📦 Installing dependencies..."
$PIP_CMD install --upgrade pip
$PIP_CMD install -r requirements.txt

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."
$PYTHON_CMD -c "import fastapi; print('✅ FastAPI OK')" || (echo "❌ FastAPI missing"; exit 1)
$PYTHON_CMD -c "import uvicorn; print('✅ Uvicorn OK')" || (echo "❌ Uvicorn missing"; exit 1)
$PYTHON_CMD -c "import sqlalchemy; print('✅ SQLAlchemy OK')" || (echo "❌ SQLAlchemy missing"; exit 1)

# Run database migrations
echo "🗄️ Running database migrations..."
$PYTHON_CMD migrate.py

# Start the web server
echo "🌐 Starting web server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
