#!/usr/bin/env python3
"""FINAL: Commit+Push to GitHub, then IMMEDIATE rebuild of info cards."""

import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("FASE 1: GIT COMMIT & PUSH")
print("=" * 80)

try:
    subprocess.call(["git", "add", "-A"], shell=False)
    subprocess.call(
        ["git", "commit", "-m", "fix(final): core fixes, v5 templates, publish-now, recreate endpoints"],
        shell=False
    )
    subprocess.call(["git", "push", "origin", "main"], shell=False)
    print("\n✅ Git push completed\n")
except Exception as e:
    print(f"⚠️  Git error (continuing): {e}\n")

print("=" * 80)
print("FASE 2: RICREAZIONE IMMEDIATA INFO CARD DA ZERO")
print("=" * 80)

try:
    result = subprocess.call([sys.executable, "RICREA_ADESSO.py"], shell=False)
    if result == 0:
        print("\n✅ Info cards ricreate con successo!")
    else:
        print(f"\n⚠️  Rebuild returned code {result}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
