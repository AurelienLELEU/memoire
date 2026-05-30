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
    p.add_argument(
        "--profile",
        choices=["azure", "local", "all"],
        default="azure",
        help="Jeu de configurations a executer",
    )
    p.add_argument(
        "--output",
        default="results/benchmark_generation.csv",
        help="Chemin du CSV resume de sortie",
    )
    args = p.parse_args()

    azure_selected = [
        {
            "chunking": "markdown-1200-50",
            "embedding": "ada-002",
            "retrieval": "dense-k5-thresh",
            "generation": "azure-gpt35",
        },
        {
            "chunking": "recursive-512-64",
            "embedding": "ada-002",
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

    local_selected = [
        {
            "chunking": "fixed-256-0",
            "embedding": "minilm-l6",
            "retrieval": "dense-k5-neigh",
            "generation": "local-mistral7b",
        },
        {
            "chunking": "recursive-512-64",
            "embedding": "e5-base-ml",
            "retrieval": "dense-k5-neigh",
            "generation": "local-mistral7b",
        },
    ]

    if args.profile == "azure":
        selected = azure_selected
    elif args.profile == "local":
        selected = local_selected
    else:
        selected = azure_selected + local_selected

    df = benchmark_generation(
        selected_configs=selected,
        use_ragas=not args.no_ragas,
        use_modality_judge=not args.no_judge,
        output_path=Path(args.output),
    )
    print("\n=== Résumé ===")
    print(df.to_string())


if __name__ == "__main__":
    main()
