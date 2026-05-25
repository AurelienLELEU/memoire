"""
Benchmark orchestrateur :
- itère sur (chunking, embedding, retrieval) -> métriques retrieval
- pour configurations retenues -> génération + métriques RAGAS + juge custom
- sauvegarde résultats CSV + JSON dans results/.
"""
from __future__ import annotations

import json
import time
from itertools import product
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from src.config import (
    CHUNKING_CONFIGS,
    EMBEDDING_MODELS,
    GENERATION_CONFIGS,
    RESULTS_DIR,
    RETRIEVAL_CONFIGS,
    TEST_SET_PATH,
    azure_available,
)
from src.embeddings import list_available_embedders
from src.evaluation.retrieval_metrics import compute_all as compute_retrieval_metrics
from src.generation import answer_question
from src.retrieval import run_retrieval


def load_test_set() -> list[dict]:
    if not TEST_SET_PATH.exists():
        raise FileNotFoundError(f"Test set introuvable : {TEST_SET_PATH}. Lance d'abord scripts/00_init_test_set.py")
    return json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))


# ============================================================
# Étape 1 : benchmark RETRIEVAL seul (rapide, sans LLM)
# ============================================================
def benchmark_retrieval(
    chunkings: list[str] | None = None,
    embeddings: list[str] | None = None,
    retrievals: list[str] | None = None,
    ks: tuple[int, ...] = (1, 3, 5, 10),
    level: str = "doc",  # 'doc' (recommandé si chunk_ids de référence absents) ou 'chunk'
) -> pd.DataFrame:
    test_set = load_test_set()
    chunkings = chunkings or [c.name for c in CHUNKING_CONFIGS]
    available_embs = [e.name for e in list_available_embedders()]
    embeddings = embeddings or available_embs
    retrievals = retrievals or [r.name for r in RETRIEVAL_CONFIGS]

    chunk_lookup = {c.name: c for c in CHUNKING_CONFIGS}
    ret_lookup = {r.name: r for r in RETRIEVAL_CONFIGS}

    rows = []
    combos = list(product(chunkings, embeddings, retrievals))
    print(f"→ {len(combos)} configurations × {len(test_set)} questions")

    for ch_name, emb_name, ret_name in tqdm(combos, desc="Configs"):
        ret_cfg = ret_lookup[ret_name]
        # skip combos invalides (sparse n'a pas besoin d'embedding mais on garde pour homogénéité)
        per_q_rows = []
        for q in test_set:
            try:
                t0 = time.time()
                retrieved = run_retrieval(q["question"], ch_name, emb_name, ret_cfg)
                latency = time.time() - t0
            except Exception as e:
                per_q_rows.append({"question_id": q["id"], "error": str(e)})
                continue

            retrieved_ids = [r.chunk.chunk_id for r in retrieved]
            relevant_ids = q.get("relevant_chunk_ids") or q.get("relevant_doc_ids", [])
            level_used = level if q.get("relevant_chunk_ids") else "doc"

            metrics = compute_retrieval_metrics(retrieved_ids, relevant_ids, ks=ks, level=level_used)
            metrics.update({
                "question_id": q["id"],
                "latency_s": latency,
                "n_retrieved": len(retrieved),
            })
            per_q_rows.append(metrics)

        df_q = pd.DataFrame(per_q_rows)
        agg = df_q.mean(numeric_only=True).to_dict()
        agg.update({
            "chunking": ch_name,
            "embedding": emb_name,
            "retrieval": ret_name,
            "n_questions": len(test_set),
        })
        rows.append(agg)

    df = pd.DataFrame(rows)
    out = RESULTS_DIR / "benchmark_retrieval.csv"
    df.to_csv(out, index=False)
    print(f"✓ Résultats retrieval -> {out}")
    return df


# ============================================================
# Étape 2 : génération + RAGAS sur configurations retenues
# ============================================================
def benchmark_generation(
    selected_configs: list[dict],  # [{chunking, embedding, retrieval, generation}, ...]
    use_ragas: bool = True,
    use_modality_judge: bool = True,
) -> pd.DataFrame:
    test_set = load_test_set()
    ret_lookup = {r.name: r for r in RETRIEVAL_CONFIGS}

    all_rows = []
    for cfg in selected_configs:
        ch, emb, ret, gen = cfg["chunking"], cfg["embedding"], cfg["retrieval"], cfg["generation"]
        ret_cfg = ret_lookup[ret]
        print(f"→ Génération : {ch} | {emb} | {ret} | {gen}")

        samples = []
        per_q = []
        for q in tqdm(test_set, desc="  questions"):
            try:
                t0 = time.time()
                retrieved = run_retrieval(q["question"], ch, emb, ret_cfg)
                t_retrieval = time.time() - t0
                t0 = time.time()
                answer = answer_question(q["question"], retrieved, gen)
                t_gen = time.time() - t0
            except Exception as e:
                per_q.append({"question_id": q["id"], "error": str(e)})
                continue

            contexts = [r.chunk.text for r in retrieved]
            samples.append({
                "question": q["question"],
                "answer": answer,
                "contexts": contexts,
                "ground_truth": q.get("ground_truth_answer", ""),
            })
            per_q.append({
                "question_id": q["id"],
                "answer": answer,
                "n_ctx": len(contexts),
                "t_retrieval_s": t_retrieval,
                "t_generation_s": t_gen,
            })

        df_q = pd.DataFrame(per_q)

        # RAGAS
        if use_ragas and azure_available() and samples:
            try:
                from src.evaluation.generation_metrics import evaluate_with_ragas
                ragas_scores = evaluate_with_ragas(samples)
                for key, vals in ragas_scores.items():
                    if key in df_q.columns or len(vals) != len(df_q):
                        continue
                    df_q[f"ragas_{key}"] = vals
            except Exception as e:
                print(f"  ⚠ RAGAS échoué : {e}")

        # Juge modalité santé-sécurité
        if use_modality_judge and azure_available() and samples:
            from src.evaluation.generation_metrics import judge_safety_modality
            verdicts = []
            for s in tqdm(samples, desc="  modality-judge"):
                v = judge_safety_modality(s["question"], s["answer"], s["contexts"])
                verdicts.append(v)
            for key in ("preservation_modalites", "completude_exceptions", "surete_operationnelle"):
                df_q[f"judge_{key}"] = [v.get(key) for v in verdicts]

        # agrégation
        agg = df_q.mean(numeric_only=True).to_dict()
        agg.update({**cfg, "n_questions": len(test_set)})
        all_rows.append(agg)

        # détail par question
        df_q["chunking"] = ch
        df_q["embedding"] = emb
        df_q["retrieval"] = ret
        df_q["generation"] = gen
        detail_path = RESULTS_DIR / f"generation_detail__{ch}__{emb}__{ret}__{gen}.csv"
        df_q.to_csv(detail_path, index=False)

    df_summary = pd.DataFrame(all_rows)
    out = RESULTS_DIR / "benchmark_generation.csv"
    df_summary.to_csv(out, index=False)
    print(f"✓ Résultats génération -> {out}")
    return df_summary


# ============================================================
# Étape 3 : stabilité (n runs + paraphrases)
# ============================================================
def benchmark_stability(
    config: dict,  # {chunking, embedding, retrieval, generation}
    n_runs: int = 5,
    use_paraphrases: bool = True,
) -> pd.DataFrame:
    from src.config import STABILITY_N_RUNS
    from src.evaluation.stability_metrics import (
        stability_retrieval,
        stability_citations,
        stability_answer_bertscore,
    )

    test_set = load_test_set()
    ret_cfg = next(r for r in RETRIEVAL_CONFIGS if r.name == config["retrieval"])

    rows = []
    for q in tqdm(test_set, desc="Stabilité"):
        questions_to_run = [q["question"]]
        if use_paraphrases:
            questions_to_run.extend(q.get("paraphrases", []))

        # runs sur question originale
        ids_runs, ans_runs = [], []
        for _ in range(n_runs):
            try:
                retrieved = run_retrieval(q["question"], config["chunking"], config["embedding"], ret_cfg)
                ids_runs.append([r.chunk.chunk_id for r in retrieved])
                ans_runs.append(answer_question(q["question"], retrieved, config["generation"]))
            except Exception as e:
                print(f"  ✗ {q['id']}: {e}")

        stab_ret = stability_retrieval(ids_runs)
        stab_cit = stability_citations(ans_runs)
        stab_ans = stability_answer_bertscore(ans_runs, lang=q.get("language", "fr"))

        row = {"question_id": q["id"], **{f"ret_{k}": v for k, v in stab_ret.items()},
               **{f"cit_{k}": v for k, v in stab_cit.items()},
               **{f"ans_{k}": v for k, v in stab_ans.items()}}

        # paraphrases : 1 run par paraphrase, compare aux runs original
        if use_paraphrases and q.get("paraphrases"):
            para_answers = []
            for para in q["paraphrases"]:
                try:
                    retrieved = run_retrieval(para, config["chunking"], config["embedding"], ret_cfg)
                    para_answers.append(answer_question(para, retrieved, config["generation"]))
                except Exception:
                    pass
            if para_answers and ans_runs:
                para_stab = stability_answer_bertscore([ans_runs[0]] + para_answers, lang=q.get("language", "fr"))
                row["paraphrase_bertscore_f1"] = para_stab.get("bertscore_f1_mean")

        rows.append(row)

    df = pd.DataFrame(rows)
    out = RESULTS_DIR / f"stability__{config['chunking']}__{config['embedding']}__{config['retrieval']}__{config['generation']}.csv"
    df.to_csv(out, index=False)
    print(f"✓ Stabilité -> {out}")
    return df
