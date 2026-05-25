"""
Étape 5 : test de STABILITÉ sur une configuration.
n_runs exécutions par question + tests sur paraphrases.

Usage :
  python scripts/05_benchmark_stability.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.benchmark import benchmark_stability  # noqa: E402


def main():
    config = {
        "chunking": "markdown-1200-50",
        "embedding": "e5-large-ml",
        "retrieval": "dense-k5-thresh",
        "generation": "azure-gpt35",
    }
    df = benchmark_stability(config, n_runs=5, use_paraphrases=True)
    print("\n=== Stabilité (médiane) ===")
    print(df.median(numeric_only=True).to_string())


if __name__ == "__main__":
    main()
