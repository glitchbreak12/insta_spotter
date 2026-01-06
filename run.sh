#!/bin/bash

# Trova Python automaticamente con ricerca esaustiva
PYTHON_CMD=""

# Prima cerca nei percorsi comuni
echo "🔍 Searching for Python in common locations..."
for py in python3 python /usr/bin/python3 /usr/local/bin/python3 /opt/python3/bin/python3 /home/runner/.python3/bin/python3; do
    if command -v "$py" >/dev/null 2>&1; then
        PYTHON_CMD="$py"
        echo "✅ Found Python: $PYTHON_CMD"
        break
    fi
done

# Se non trovato, cerca in tutto il sistema
if [ -z "$PYTHON_CMD" ]; then
    echo "🔍 Python not found in common locations, searching system-wide..."
    PYTHON_PATH=$(find /usr /opt /home/runner -name "python3" -type f -executable 2>/dev/null | head -1)
    if [ -n "$PYTHON_PATH" ] && [ -x "$PYTHON_PATH" ]; then
        PYTHON_CMD="$PYTHON_PATH"
        echo "✅ Found Python via find: $PYTHON_CMD"
    fi
fi

# Ultimo tentativo: cerca python (senza 3)
if [ -z "$PYTHON_CMD" ]; then
    echo "🔍 Trying python (without version)..."
    if command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
        echo "✅ Found python: $PYTHON_CMD"
    fi
fi

# Verifica finale
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ ERROR: Python not found in any location!"
    echo "📋 Available commands:"
    which python python3 2>/dev/null || echo "No python commands found"
    echo "📋 Python files in system:"
    find /usr /opt /home/runner -name "*python*" -type f 2>/dev/null | head -5 || echo "No python files found"
    exit 1
fi

echo "🚀 Starting InstaSpotter with $PYTHON_CMD..."
$PYTHON_CMD app/main.py
