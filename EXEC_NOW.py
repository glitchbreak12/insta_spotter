#!/usr/bin/env python3
"""Subprocess wrapper to execute DELETE_AND_RECREATE_NOW.py."""
import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
exit(subprocess.call([sys.executable, "DELETE_AND_RECREATE_NOW.py"]))
