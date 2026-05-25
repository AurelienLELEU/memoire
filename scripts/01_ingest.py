"""Étape 1 : extraire les PDFs de input/ vers data/extracted/.

Usage : python scripts/01_ingest.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion import ingest_all  # noqa: E402

if __name__ == "__main__":
    ingest_all()
