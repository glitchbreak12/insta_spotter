#!/bin/bash

# Trova Python automaticamente
PYTHON_CMD=""
for py in python3 python /usr/bin/python3 /usr/local/bin/python3; do
    if command -v "$py" >/dev/null 2>&1; then
        PYTHON_CMD="$py"
        echo "Using Python: $PYTHON_CMD"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "ERROR: Python not found!"
    exit 1
fi

# Avvia l'app
echo "Starting InstaSpotter..."
$PYTHON_CMD app/main.py
