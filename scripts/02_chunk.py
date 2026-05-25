"""Étape 2 : appliquer toutes les stratégies de chunking définies dans config.py.

Usage : python scripts/02_chunk.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunking import build_all_chunkings  # noqa: E402

if __name__ == "__main__":
    build_all_chunkings()
