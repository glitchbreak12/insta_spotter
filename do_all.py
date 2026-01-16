#!/usr/bin/env python3
"""Execute git commit and push, then run rebuild_info_cards."""

import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("📤 Step 1: Git commit and push")
print("=" * 80)

try:
    subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
    print("✅ Staged changes")
    
    subprocess.run(
        ["git", "commit", "-m", "fix(core): image generation, carousel method, card_info v5 style, recreate endpoints"],
        check=True,
        capture_output=True
    )
    print("✅ Committed")
    
    subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
    print("✅ Pushed to origin/main")
except subprocess.CalledProcessError as e:
    print(f"⚠️  Git error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("🔄 Step 2: Rebuild INFO cards with v5 style")
print("=" * 80 + "\n")

try:
    subprocess.run([sys.executable, "quick_rebuild.py"], check=True)
except Exception as e:
    print(f"❌ Rebuild error: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ ALL DONE!")
print("=" * 80)
