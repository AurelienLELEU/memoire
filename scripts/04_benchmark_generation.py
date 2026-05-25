"""
Étape 4 : benchmark GÉNÉRATION + RAGAS + juge modalités.
Sur un sous-ensemble de configurations (sélectionnées après l'étape 3 idéalement).

Usage :
  python scripts/04_benchmark_generation.py
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.benchmark import benchmark_generation  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--no-ragas", action="store_true")
    p.add_argument("--no-judge", action="store_true")
    args = p.parse_args()

    # Sélection par défaut : 2-3 configurations représentatives
    selected = [
        {
            "chunking": "markdown-1200-50",
            "embedding": "e5-large-ml",
            "retrieval": "dense-k5-thresh",
            "generation": "azure-gpt35",
        },
        {
            "chunking": "recursive-512-64",
            "embedding": "bge-m3",
            "retrieval": "hybrid-k5",
            "generation": "azure-gpt35",
        },
        {
            "chunking": "markdown-1200-50",
            "embedding": "ada-002",
            "retrieval": "dense-k5-neigh",
            "generation": "azure-gpt35",
        },
    ]

    df = benchmark_generation(
        selected_configs=selected,
        use_ragas=not args.no_ragas,
        use_modality_judge=not args.no_judge,
    )
    print("\n=== Résumé ===")
    print(df.to_string())


if __name__ == "__main__":
    main()
