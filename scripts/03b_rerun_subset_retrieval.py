"""
Relance ciblée du benchmark retrieval sur un sous-ensemble fixe de
configurations (10 tuples) après correction du calcul de Recall@k / nDCG@k
au niveau document (déduplication des chunks projetés sur leur doc_id).

Sortie : results/benchmark_retrieval_subset.csv
"""
from __future__ import annotations

import sys
import time
from itertools import groupby
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.benchmark import load_test_set  # noqa: E402
from src.config import CHUNKING_CONFIGS, RESULTS_DIR, RETRIEVAL_CONFIGS  # noqa: E402
from src.evaluation.retrieval_metrics import compute_all as compute_retrieval_metrics  # noqa: E402
from src.retrieval import build_retriever, run_retrieval  # noqa: E402

# (chunking, embedding, retrieval)
CONFIGS: list[tuple[str, str, str]] = [
    # Top-5 retrieval cités dans §8a.2
    ("fixed-1024-128", "ada-002", "dense-k10"),
    ("fixed-1024-128", "ada-002", "dense-k5-thresh"),
    ("fixed-512-64", "qwen3-embed-8b", "hybrid-k5"),
    ("recursive-1024-128", "nomic-v2", "dense-k10"),
    ("recursive-512-64", "qwen3-embed-8b", "hybrid-k5"),
    # 5 configurations de la campagne génération (§8a.3)
    ("recursive-512-64", "ada-002", "hybrid-k5"),
    ("markdown-1200-50", "ada-002", "dense-k5-thresh"),
    ("markdown-1200-50", "ada-002", "dense-k5-neigh"),
    ("fixed-256-0", "minilm-l6", "dense-k5-neigh"),
    ("recursive-512-64", "e5-base-ml", "dense-k5-neigh"),
]


def main() -> None:
    test_set = load_test_set()
    ret_lookup = {r.name: r for r in RETRIEVAL_CONFIGS}
    chunk_names = {c.name for c in CHUNKING_CONFIGS}
    for ch, _, _ in CONFIGS:
        if ch not in chunk_names:
            raise SystemExit(f"Chunking inconnu : {ch}")
        # ret_lookup levera plus tard si besoin

    out_path = RESULTS_DIR / "benchmark_retrieval_subset.csv"
    rows: list[dict] = []

    # On regroupe par (chunking, embedding) pour mutualiser la construction du retriever
    grouped = sorted(CONFIGS, key=lambda x: (x[0], x[1]))
    for (ch_name, emb_name), group in groupby(grouped, key=lambda x: (x[0], x[1])):
        group = list(group)
        retriever_cache: dict[tuple, object] = {}
        for _, _, ret_name in group:
            ret_cfg = ret_lookup[ret_name]
            key = (ret_cfg.mode, getattr(ret_cfg, "alpha", None))
            retriever = retriever_cache.get(key)
            if retriever is None:
                print(f"→ Build retriever : {ch_name} | {emb_name} | {ret_name}")
                retriever = build_retriever(ch_name, emb_name, ret_cfg)
                retriever_cache[key] = retriever

            per_q: list[dict] = []
            for q in test_set:
                t0 = time.time()
                try:
                    retrieved = run_retrieval(
                        q["question"], ch_name, emb_name, ret_cfg, retriever=retriever
                    )
                except Exception as e:
                    per_q.append({"question_id": q["id"], "error": str(e)})
                    continue
                latency = time.time() - t0
                retrieved_ids = [r.chunk.chunk_id for r in retrieved]
                relevant_ids = q.get("relevant_chunk_ids") or q.get("relevant_doc_ids", [])
                level_used = "chunk" if q.get("relevant_chunk_ids") else "doc"
                metrics = compute_retrieval_metrics(
                    retrieved_ids, relevant_ids, ks=(1, 3, 5, 10), level=level_used
                )
                metrics.update(
                    {
                        "question_id": q["id"],
                        "latency_s": latency,
                        "n_retrieved": len(retrieved),
                    }
                )
                per_q.append(metrics)

            df_q = pd.DataFrame(per_q)
            agg = df_q.mean(numeric_only=True).to_dict()
            agg.update(
                {
                    "chunking": ch_name,
                    "embedding": emb_name,
                    "retrieval": ret_name,
                    "n_questions": len(test_set),
                }
            )
            rows.append(agg)
            pd.DataFrame(rows).to_csv(out_path, index=False)
            print(
                f"  ✓ {ch_name} | {emb_name} | {ret_name} → "
                f"MRR={agg.get('mrr', float('nan')):.3f} "
                f"Hit@5={agg.get('hit@5', float('nan')):.3f} "
                f"Recall@5={agg.get('recall@5', float('nan')):.3f} "
                f"nDCG@5={agg.get('ndcg@5', float('nan')):.3f}"
            )

    print(f"\n→ Résultats consolidés dans {out_path}")


if __name__ == "__main__":
    main()
