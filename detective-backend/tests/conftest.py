"""Shared pytest configuration ensuring detective-backend/ is importable."""
import os
import sys
from pathlib import Path

BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DETECTIVE_LAN_DISCOVERY", "0")
