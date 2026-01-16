#!/usr/bin/env python3
"""Auto push helper: stage all, commit with message, and push to origin main.
Usage: python scripts/auto_push.py "commit message"
"""
import sys
import subprocess

if len(sys.argv) < 2:
    print("Usage: python scripts/auto_push.py \"commit message\"")
    sys.exit(1)

message = sys.argv[1]

try:
    subprocess.check_call(["git", "add", "-A"])
    subprocess.check_call(["git", "commit", "-m", message])
    subprocess.check_call(["git", "push", "origin", "main"])
    print("✅ Changes pushed to origin/main")
except subprocess.CalledProcessError as e:
    print("Error during git operation:", e)
    sys.exit(1)
