"""Étape 2 : appliquer toutes les stratégies de chunking définies dans config.py.

Usage : python scripts/02_chunk.py
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunking import build_all_chunkings  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère les jeux de chunks demandés à partir des documents extraits."
    )
    parser.add_argument(
        "--chunkings",
        nargs="*",
        help="Liste de configs de chunking à générer. Sans option, génère tout.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Ignore les fichiers de chunks déjà présents au lieu de les regénérer.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_all_chunkings(chunking_names=args.chunkings, skip_existing=args.skip_existing)
