"""
Étape 3 : benchmark RETRIEVAL.
Itère sur tous les couples (chunking, embedding, retrieval) et calcule
Hit/Recall/Precision/MRR/nDCG@k sur le jeu de test.

Usage :
  python scripts/03_benchmark_retrieval.py
  python scripts/03_benchmark_retrieval.py --embeddings minilm-l6 e5-base-ml
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.benchmark import benchmark_retrieval  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chunkings", nargs="*", help="Liste de configs de chunking (sinon toutes)")
    p.add_argument("--embeddings", nargs="*", help="Liste de modèles d'embedding (sinon tous)")
    p.add_argument("--retrievals", nargs="*", help="Liste de configs de retrieval (sinon toutes)")
    p.add_argument("--level", choices=["chunk", "doc"], default="doc",
                   help="Niveau d'évaluation (doc par défaut si chunks de référence non annotés)")
    args = p.parse_args()

    df = benchmark_retrieval(
        chunkings=args.chunkings,
        embeddings=args.embeddings,
        retrievals=args.retrievals,
        level=args.level,
    )
    print("\n=== TOP 10 par Recall@5 ===")
    print(df.sort_values("recall@5", ascending=False).head(10).to_string())


if __name__ == "__main__":
    main()
