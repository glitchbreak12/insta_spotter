#!/usr/bin/env python3
"""Execute RICREA_ADESSO.py via subprocess to avoid REPL blocking."""

import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Executing RICREA_ADESSO.py...")
result = subprocess.call([sys.executable, "RICREA_ADESSO.py"])
sys.exit(result)
