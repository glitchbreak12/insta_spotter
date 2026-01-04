#!/usr/bin/env bash
# Exit on error
set -e

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python migrate.py

# Start the web server
uvicorn app.main:app --host 0.0.0.0 --port $PORT
