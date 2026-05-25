"""
Stabilité : Jaccard@retrieval, Jaccard@citations, BERTScore@answer, flip rate,
robustesse aux paraphrases.
"""
from __future__ import annotations

import re
from itertools import combinations
from statistics import mean, stdev


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def stability_retrieval(runs_retrieved_ids: list[list[str]]) -> dict:
    """
    runs_retrieved_ids : liste de listes d'ids retournés à chaque run.
    Mesure : Jaccard moyen entre paires de runs.
    """
    if len(runs_retrieved_ids) < 2:
        return {"jaccard_mean": float("nan"), "jaccard_std": float("nan"), "n_pairs": 0}
    sets = [set(r) for r in runs_retrieved_ids]
    pairs = list(combinations(sets, 2))
    js = [jaccard(a, b) for a, b in pairs]
    return {
        "jaccard_mean": mean(js),
        "jaccard_std": stdev(js) if len(js) > 1 else 0.0,
        "n_pairs": len(js),
    }


def extract_citation_ids(answer: str) -> set[int]:
    """Extrait les numéros [n] cités dans la réponse."""
    return {int(m) for m in re.findall(r"\[(\d+)\]", answer)}


def stability_citations(runs_answers: list[str]) -> dict:
    if len(runs_answers) < 2:
        return {"jaccard_mean": float("nan"), "n_pairs": 0}
    sets = [extract_citation_ids(a) for a in runs_answers]
    pairs = list(combinations(sets, 2))
    js = [jaccard(a, b) for a, b in pairs]
    return {
        "jaccard_mean": mean(js) if js else float("nan"),
        "n_pairs": len(js),
    }


def stability_answer_bertscore(runs_answers: list[str], lang: str = "fr") -> dict:
    """BERTScore moyen entre paires de réponses."""
    if len(runs_answers) < 2:
        return {"bertscore_f1_mean": float("nan"), "n_pairs": 0}
    try:
        from bert_score import score as bertscore_fn
    except ImportError:
        return {"bertscore_f1_mean": float("nan"), "error": "bert-score non installé"}

    pairs = list(combinations(range(len(runs_answers)), 2))
    cands = [runs_answers[i] for i, _ in pairs]
    refs = [runs_answers[j] for _, j in pairs]
    _, _, f1 = bertscore_fn(cands, refs, lang=lang, verbose=False)
    return {
        "bertscore_f1_mean": float(f1.mean()),
        "bertscore_f1_std": float(f1.std()),
        "n_pairs": len(pairs),
    }


def flip_rate(verdicts: list[bool]) -> dict:
    """Verdicts par run (correct/incorrect). Flip = au moins un changement."""
    if not verdicts:
        return {"flip_rate": float("nan")}
    n_correct = sum(verdicts)
    return {
        "p_correct": n_correct / len(verdicts),
        "flipped": 0 < n_correct < len(verdicts),
        "n_runs": len(verdicts),
    }
