"""
Métriques de retrieval : Hit@k, Recall@k, Precision@k, MRR, nDCG@k.

Convention :
- chaque question du test set contient `relevant_chunk_ids` : la liste des chunk_ids
  ou des `relevant_doc_ids` (fallback) jugés pertinents.
- chunk_id est de la forme "<doc_id>__<position>", on peut donc dégrader vers doc-level.
"""
from __future__ import annotations

import math
from typing import Sequence


def _to_doc_ids(chunk_ids: Sequence[str]) -> list[str]:
    return [cid.split("__")[0] for cid in chunk_ids]


def _project(ids: Sequence[str], level: str) -> list[str]:
    return _to_doc_ids(ids) if level == "doc" else list(ids)


def _dedupe_keep_order(ids: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def hit_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int, level: str = "chunk") -> float:
    if not relevant_ids:
        return float("nan")
    top = _dedupe_keep_order(_project(retrieved_ids, level))[:k]
    rel = set(_project(relevant_ids, level))
    return 1.0 if any(r in rel for r in top) else 0.0


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int, level: str = "chunk") -> float:
    if not relevant_ids:
        return float("nan")
    top = _dedupe_keep_order(_project(retrieved_ids, level))[:k]
    rel = set(_project(relevant_ids, level))
    return len([r for r in top if r in rel]) / len(rel)


def precision_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int, level: str = "chunk") -> float:
    if not relevant_ids or k == 0:
        return float("nan")
    top = _dedupe_keep_order(_project(retrieved_ids, level))[:k]
    rel = set(_project(relevant_ids, level))
    return len([r for r in top if r in rel]) / k


def mrr(retrieved_ids: list[str], relevant_ids: list[str], level: str = "chunk") -> float:
    if not relevant_ids:
        return float("nan")
    ret = _dedupe_keep_order(_project(retrieved_ids, level))
    rel = set(_project(relevant_ids, level))
    for i, r in enumerate(ret, 1):
        if r in rel:
            return 1.0 / i
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int, level: str = "chunk") -> float:
    if not relevant_ids:
        return float("nan")
    top = _dedupe_keep_order(_project(retrieved_ids, level))[:k]
    rel = set(_project(relevant_ids, level))
    dcg = sum((1.0 if r in rel else 0.0) / math.log2(i + 2) for i, r in enumerate(top))
    ideal_hits = min(len(rel), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


def compute_all(retrieved_ids: list[str], relevant_ids: list[str],
                ks: tuple[int, ...] = (1, 3, 5, 10),
                level: str = "chunk") -> dict:
    out = {"mrr": mrr(retrieved_ids, relevant_ids, level=level)}
    for k in ks:
        out[f"hit@{k}"] = hit_at_k(retrieved_ids, relevant_ids, k, level=level)
        out[f"recall@{k}"] = recall_at_k(retrieved_ids, relevant_ids, k, level=level)
        out[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k, level=level)
        out[f"ndcg@{k}"] = ndcg_at_k(retrieved_ids, relevant_ids, k, level=level)
    return out
