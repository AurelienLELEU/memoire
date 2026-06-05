"""
06_make_figures.py
==================

Génère les figures P1 (et quelques P2) du mémoire à partir des CSV présents
dans ``results/`` et des métadonnées de ``data/test_set.json``.

Chaque figure est sauvegardée en PNG (DPI=160) dans le dossier ``figures/``
sous un nom explicite (``fig_8_1_heatmap_mrr_modele_chunking.png``, etc.).

Utilisation
-----------
    py -3.11 scripts/06_make_figures.py
    py -3.11 scripts/06_make_figures.py --only 8.1 8.5 9.4
    py -3.11 scripts/06_make_figures.py --out-dir figures_v2

Le script est tolérant : chaque figure est encadrée par un try/except afin
qu'une erreur isolée n'interrompe pas le reste du pipeline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Chemins & constantes
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
DATA = ROOT / "data"

STABILITY_FILE = RESULTS / "stability__markdown-1200-50__ada-002__dense-k5-thresh__azure-gpt35.csv"
DETAIL_FILE = RESULTS / "generation_detail__recursive-512-64__ada-002__hybrid-k5__azure-gpt35.csv"

# Famille de modèles d'embedding pour la coloration (Fig 8.3).
EMBED_FAMILY = {
    "ada-002": "propriétaire",
    "embed-3-large": "propriétaire",
    "bge-m3": "multilingue OSS",
    "e5-small-ml": "multilingue OSS",
    "e5-base-ml": "multilingue OSS",
    "e5-large-ml": "multilingue OSS",
    "jina-v3": "multilingue OSS",
    "granite-311m-ml": "multilingue OSS",
    "nomic-v2": "multilingue OSS",
    "qwen3-embed-8b": "multilingue OSS",
    "gte-qwen2-7b": "multilingue OSS",
    "nv-embed-v2": "multilingue OSS",
    "minilm-l6": "généraliste EN",
    "mpnet-base": "généraliste EN",
    "jina-v2-base-en": "généraliste EN",
    "camembert-large": "francophone",
    "solon-large": "francophone",
    "bilingual-fr-en": "francophone",
}
FAMILY_COLORS = {
    "propriétaire": "#d62728",
    "multilingue OSS": "#1f77b4",
    "généraliste EN": "#2ca02c",
    "francophone": "#9467bd",
}

# Seuils utilisés pour la classification automatique des erreurs (Fig 9.1).
# Ils sont volontairement explicites en haut de fichier afin que tu puisses
# les recaler pour qu'ils collent au paragraphe § 9.2 de ton mémoire.
ERROR_THRESHOLDS = {
    "ctx_recall_fail": 0.30,        # échec récupération
    "ctx_precision_noise": 0.30,    # bruit
    "faith_contradiction": 0.30,    # contradiction (sous-cas de hallu)
    "faith_hallucination": 0.50,    # hallucination
    "answer_rel_omission": 0.50,    # omission
    "ctx_recall_ok_min": 0.50,      # seuil de couverture jugée "suffisante"
}
REFUSAL_PATTERNS = re.compile(
    r"(je\s+ne\s+(peux|sais)|aucune?\s+information|pas\s+(d['e]|de\s+l[ae])\s+information|"
    r"je\s+n['e ]ai\s+pas|sorry|i\s+(do\s+not|don't|cannot|can't))",
    flags=re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _save(fig: plt.Figure, name: str, out_dir: Path, dpi: int = 160) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {path.relative_to(ROOT)}")


def _config_label(row: pd.Series) -> str:
    """Étiquette unique pour les 5 configurations de génération.

    On inclut ``embedding`` car il suffit à lever l'ambiguïté entre les deux
    configurations Mistral local (qui partagent retrieval/generation mais
    diffèrent sur chunking + embedding).
    """
    return f"{row['embedding']} · {row['retrieval']}\n{row['generation']}"


def _config_label_oneline(row: pd.Series) -> str:
    return f"{row['embedding']} · {row['retrieval']} / {row['generation']}"


def _setup_style() -> None:
    sns.set_theme(context="notebook", style="whitegrid", palette="muted")
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 160,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_retrieval() -> pd.DataFrame:
    df = pd.read_csv(RESULTS / "benchmark_retrieval.csv")
    df = df[df["mrr"].notna()].copy()
    return df


def load_generation() -> pd.DataFrame:
    return pd.read_csv(RESULTS / "benchmark_generation.csv")


def load_stability() -> pd.DataFrame:
    return pd.read_csv(STABILITY_FILE)


def load_detail() -> pd.DataFrame:
    return pd.read_csv(DETAIL_FILE)


def load_test_set() -> pd.DataFrame:
    raw = json.loads((DATA / "test_set.json").read_text(encoding="utf-8"))
    df = pd.DataFrame(raw).rename(columns={"id": "question_id"})
    return df


# ---------------------------------------------------------------------------
# Figures Chapitre 8 — Résultats
# ---------------------------------------------------------------------------


def fig_8_1_heatmap_mrr_modele_chunking(out_dir: Path) -> None:
    df = load_retrieval()
    pivot = df.groupby(["embedding", "chunking"])["mrr"].mean().unstack()
    pivot = pivot.dropna(how="all")  # retire les modèles totalement absents
    # Tri par MRR global décroissant (modèles en lignes, chunkings en colonnes).
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]
    pivot = pivot[pivot.mean(axis=0).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(11, 7.5))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="viridis",
        vmin=0.30,
        vmax=0.75,
        cbar_kws={"label": "MRR moyen"},
        linewidths=0.4,
        linecolor="white",
        ax=ax,
    )
    ax.set_title(
        "Fig 8.1 — MRR moyen par modèle d'embedding et stratégie de chunking\n"
        "(moyenne sur les 6 variantes de récupération)"
    )
    ax.set_xlabel("Stratégie de chunking")
    ax.set_ylabel("Modèle d'embedding")
    plt.xticks(rotation=30, ha="right")
    _save(fig, "fig_8_1_heatmap_mrr_modele_chunking.png", out_dir)


def fig_8_2_barplot_mrr_par_variante_recuperation(out_dir: Path) -> None:
    df = load_retrieval()
    order = ["dense-k5", "dense-k10", "dense-k5-thresh", "dense-k5-neigh", "hybrid-k5", "dense-k20-rerank5"]
    order = [v for v in order if v in df["retrieval"].unique()]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        data=df, x="retrieval", y="mrr", order=order, ax=ax,
        hue="retrieval", palette="Set2", legend=False, showfliers=False,
    )
    sns.stripplot(
        data=df, x="retrieval", y="mrr", order=order, ax=ax,
        color="black", alpha=0.30, size=2.5, jitter=0.25,
    )
    means = df.groupby("retrieval")["mrr"].mean().reindex(order)
    for i, m in enumerate(means.values):
        ax.scatter(i, m, marker="D", color="red", s=55, zorder=5, label="moyenne" if i == 0 else "")
    ax.set_title(
        "Fig 8.2 — Distribution du MRR par variante de récupération\n"
        "(chaque point = une combinaison chunking × embedding)"
    )
    ax.set_xlabel("Variante de récupération")
    ax.set_ylabel("MRR")
    ax.legend(loc="lower left")
    plt.xticks(rotation=15, ha="right")
    _save(fig, "fig_8_2_barplot_mrr_par_variante_recuperation.png", out_dir)


def fig_8_3_scatter_pareto_mrr_vs_latence(out_dir: Path) -> None:
    df = load_retrieval()
    agg = (
        df.groupby("embedding")
        .agg(mrr_mean=("mrr", "mean"), lat_median=("latency_s", "median"))
        .dropna()
    )
    agg["family"] = agg.index.to_series().map(EMBED_FAMILY).fillna("autre")
    agg["lat_ms"] = agg["lat_median"] * 1000.0

    fig, ax = plt.subplots(figsize=(11, 7))
    for family, color in FAMILY_COLORS.items():
        sub = agg[agg["family"] == family]
        if sub.empty:
            continue
        ax.scatter(
            sub["lat_ms"], sub["mrr_mean"],
            s=130, alpha=0.85, color=color, label=family,
            edgecolor="black", linewidth=0.6,
        )
        for name, row in sub.iterrows():
            ax.annotate(
                name, (row["lat_ms"], row["mrr_mean"]),
                fontsize=8, xytext=(5, 5), textcoords="offset points",
            )

    # Front de Pareto : points non dominés (latence min, MRR max).
    sorted_pts = agg.sort_values("lat_ms").reset_index()
    front = []
    best = -np.inf
    for _, r in sorted_pts.iterrows():
        if r["mrr_mean"] > best:
            front.append((r["lat_ms"], r["mrr_mean"]))
            best = r["mrr_mean"]
    if front:
        fx, fy = zip(*front)
        ax.plot(fx, fy, "k--", alpha=0.55, linewidth=1.5, label="Front de Pareto")

    ax.set_xscale("log")
    ax.set_xlabel("Latence médiane de récupération (ms, échelle log)")
    ax.set_ylabel("MRR moyen (sur 9 chunkings × 6 retrievals)")
    ax.set_title("Fig 8.3 — Compromis MRR vs latence par modèle d'embedding")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    _save(fig, "fig_8_3_scatter_pareto_mrr_vs_latence.png", out_dir)


def fig_8_4_distribution_mrr(out_dir: Path) -> None:
    df = load_retrieval()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df["mrr"], bins=30, kde=True, color="#1f77b4", ax=ax, edgecolor="white")
    med = df["mrr"].median()
    q1, q3 = df["mrr"].quantile([0.25, 0.75])
    ax.axvline(med, color="red", linestyle="--", linewidth=1.5, label=f"médiane = {med:.2f}")
    ax.axvspan(q1, q3, color="red", alpha=0.08, label=f"IQR [{q1:.2f}; {q3:.2f}]")
    # Étiquettes des extrêmes.
    best = df.sort_values("mrr", ascending=False).iloc[0]
    worst = df.sort_values("mrr").iloc[0]
    ax.annotate(
        f"max : {best['embedding']} / {best['chunking']} / {best['retrieval']} = {best['mrr']:.2f}",
        xy=(best["mrr"], 5), xytext=(best["mrr"] - 0.05, 60),
        arrowprops=dict(arrowstyle="->", color="green"), fontsize=8, color="green",
        ha="right",
    )
    ax.annotate(
        f"min : {worst['embedding']} / {worst['chunking']} / {worst['retrieval']} = {worst['mrr']:.2f}",
        xy=(worst["mrr"], 5), xytext=(worst["mrr"] + 0.05, 40),
        arrowprops=dict(arrowstyle="->", color="darkred"), fontsize=8, color="darkred",
    )
    ax.set_title(f"Fig 8.4 — Distribution du MRR sur les {len(df)} configurations testées")
    ax.set_xlabel("MRR")
    ax.set_ylabel("Nombre de configurations")
    ax.legend()
    _save(fig, "fig_8_4_distribution_mrr.png", out_dir)


def fig_8_5_radar_ragas_5_configs(out_dir: Path) -> None:
    df = load_generation()
    metrics = ["ragas_faithfulness", "ragas_answer_relevancy",
               "ragas_context_precision", "ragas_context_recall"]
    labels = ["Faithfulness", "Answer\nRelevancy", "Context\nPrecision", "Context\nRecall"]
    n = len(metrics)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    colors = sns.color_palette("tab10", n_colors=len(df))
    for (idx, row), color in zip(df.iterrows(), colors):
        vals = [row[m] for m in metrics]
        vals += vals[:1]
        label = _config_label(row)
        ax.plot(angles, vals, linewidth=2, label=label, color=color)
        ax.fill(angles, vals, alpha=0.10, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8)
    ax.set_rlabel_position(180 / n)
    ax.set_title("Fig 8.5 — Profil RAGAS des 5 configurations de génération", pad=24)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=9, frameon=True)
    _save(fig, "fig_8_5_radar_ragas_5_configs.png", out_dir)


def fig_8_6_barplot_ragas_5_configs(out_dir: Path) -> None:
    df = load_generation()
    metrics = ["ragas_faithfulness", "ragas_answer_relevancy",
               "ragas_context_precision", "ragas_context_recall"]
    labels_map = {
        "ragas_faithfulness": "Faithfulness",
        "ragas_answer_relevancy": "Answer Relevancy",
        "ragas_context_precision": "Context Precision",
        "ragas_context_recall": "Context Recall",
    }
    df = df.copy()
    df["config"] = df.apply(_config_label_oneline, axis=1)
    melted = df.melt(id_vars="config", value_vars=metrics,
                     var_name="metric", value_name="score")
    melted["metric"] = melted["metric"].map(labels_map)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=melted, x="metric", y="score", hue="config", ax=ax, palette="tab10")
    ax.set_title("Fig 8.6 — Comparaison RAGAS des 5 configurations de génération")
    ax.set_ylim(0, 1)
    ax.set_xlabel("")
    ax.set_ylabel("Score RAGAS")
    ax.legend(title="Configuration", loc="upper center", bbox_to_anchor=(0.5, -0.12),
              ncol=2, fontsize=9)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", fontsize=7, padding=2)
    _save(fig, "fig_8_6_barplot_ragas_5_configs.png", out_dir)


def fig_8_7_boxplot_stabilite(out_dir: Path) -> None:
    df = load_stability()
    cols = {
        "ret_jaccard_mean": "Stability@retrieval",
        "cit_jaccard_mean": "Stability@citations",
        "ans_bertscore_f1_mean": "Stability@answer",
        "paraphrase_bertscore_f1": "Robustness@paraphrases",
    }
    melted = df[list(cols)].rename(columns=cols).melt(var_name="Indicateur", value_name="Score")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=melted, x="Indicateur", y="Score", ax=ax,
                hue="Indicateur", palette="Set2", legend=False, showfliers=False)
    sns.stripplot(data=melted, x="Indicateur", y="Score", ax=ax, color="black",
                  alpha=0.45, size=3, jitter=0.2)
    medians = melted.groupby("Indicateur")["Score"].median()
    for i, label in enumerate(list(cols.values())):
        ax.text(i, medians[label] + 0.025, f"med = {medians[label]:.2f}",
                ha="center", fontsize=8, color="darkblue", fontweight="bold")
    ax.set_title("Fig 8.7 — Distribution des 4 indicateurs de stabilité (50 questions)")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("")
    _save(fig, "fig_8_7_boxplot_stabilite.png", out_dir)


def fig_8_8_scatter_interruns_vs_paraphrases(out_dir: Path) -> None:
    df = load_stability()
    fig, ax = plt.subplots(figsize=(9, 8))
    ax.scatter(df["ans_bertscore_f1_mean"], df["paraphrase_bertscore_f1"],
               s=60, alpha=0.75, color="#1f77b4", edgecolor="black", linewidth=0.4)
    # Diagonale x = y.
    lo = min(df["ans_bertscore_f1_mean"].min(), df["paraphrase_bertscore_f1"].min()) - 0.02
    hi = max(df["ans_bertscore_f1_mean"].max(), df["paraphrase_bertscore_f1"].max()) + 0.02
    ax.plot([lo, hi], [lo, hi], "k--", alpha=0.5, label="x = y")
    # Étiquette des 5 plus instables (écart inter-runs vs paraphrases le plus grand).
    df = df.copy()
    df["gap"] = df["ans_bertscore_f1_mean"] - df["paraphrase_bertscore_f1"]
    extrema = pd.concat([df.nlargest(4, "gap"), df.nsmallest(2, "gap")])
    for _, row in extrema.iterrows():
        ax.annotate(row["question_id"],
                    (row["ans_bertscore_f1_mean"], row["paraphrase_bertscore_f1"]),
                    fontsize=8, xytext=(5, 5), textcoords="offset points",
                    color="darkred")
    ax.set_xlabel("BERTScore F1 — stabilité inter-runs (ans_bertscore_f1_mean)")
    ax.set_ylabel("BERTScore F1 — robustesse aux paraphrases (paraphrase_bertscore_f1)")
    ax.set_title("Fig 8.8 — Stabilité inter-runs vs robustesse aux paraphrases (par question)")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.legend(loc="lower right")
    _save(fig, "fig_8_8_scatter_interruns_vs_paraphrases.png", out_dir)


def fig_8_9_latence_endtoend_stacked(out_dir: Path) -> None:
    df = load_generation().copy()
    df["config"] = df.apply(_config_label, axis=1)
    df = df.sort_values("t_generation_s")
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(df))
    width = 0.65
    p1 = ax.bar(x, df["t_retrieval_s"], width, label="Récupération", color="#1f77b4")
    p2 = ax.bar(x, df["t_generation_s"], width, bottom=df["t_retrieval_s"],
                label="Génération", color="#ff7f0e")
    # Annotation totaux.
    totals = df["t_retrieval_s"] + df["t_generation_s"]
    for xi, total in zip(x, totals):
        ax.text(xi, total + 0.8, f"{total:.1f}s", ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df["config"], rotation=20, ha="right")
    ax.set_ylabel("Temps moyen par question (s)")
    ax.set_title("Fig 8.9 — Décomposition de la latence end-to-end (récupération + génération)")
    ax.legend(loc="upper left")
    _save(fig, "fig_8_9_latence_endtoend_stacked.png", out_dir)


# ---------------------------------------------------------------------------
# Figures Chapitre 9 — Discussion
# ---------------------------------------------------------------------------


def _error_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Masques booléens *non exclusifs* pour les 8 catégories d'erreur.

    Une même question peut tomber dans plusieurs catégories (ex. échec
    récupération + bruit récupération). Le total des masques peut donc
    excéder le nombre de questions, conformément au comptage du § 9.2.
    """
    hp = df["type"] == "hors_perimetre"
    faith = df["ragas_faithfulness"]
    ans_rel = df["ragas_answer_relevancy"]
    ctx_prec = df["ragas_context_precision"]
    ctx_rec = df["ragas_context_recall"]
    answer_len = df.get("answer", pd.Series([""] * len(df))).fillna("").str.split().str.len()

    return {
        "échec récupération": (ctx_rec < 0.30) & ~hp,
        "bruit récupération": (ctx_prec < 0.30),  # comme dans le § 9.2 : 9/50
        "hallucination factuelle": (faith < 0.50) & (ctx_rec >= 0.50) & ~hp,
        "omission d'exception": (faith >= 0.50) & (ans_rel < 0.50) & (ctx_rec >= 0.50) & ~hp,
        "contradiction silencieuse": (faith == 0) & (answer_len > 30) & (ctx_rec >= 0.50) & ~hp,
        "refus à tort": (ans_rel == 0) & (faith == 0) & (ctx_rec >= 0.50) & ~hp,
        "hors-périmètre accepté": hp & (faith > 0.30),
        "inversion modalité": pd.Series([False] * len(df), index=df.index),
    }


def fig_9_1_distribution_categories_erreur(out_dir: Path) -> None:
    detail = load_detail()
    meta = load_test_set()[["question_id", "type"]]
    df = detail.merge(meta, on="question_id", how="left")
    masks = _error_masks(df)
    counts = pd.Series({cat: int(mask.sum()) for cat, mask in masks.items()})

    # OK = aucune catégorie d'erreur.
    any_err = pd.Series([False] * len(df), index=df.index)
    for mask in masks.values():
        any_err = any_err | mask
    counts["OK"] = int((~any_err).sum())

    order = list(masks.keys()) + ["OK"]
    counts = counts.reindex(order, fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 6))
    palette = sns.color_palette("Reds_r", n_colors=len(order) - 1) + ["#2ca02c"]
    bars = ax.barh(counts.index, counts.values, color=palette, edgecolor="black", linewidth=0.5)
    for bar, val in zip(bars, counts.values):
        ax.text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{int(val)} / {len(df)}", va="center", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Nombre de questions (comptage non-exclusif)")
    ax.set_title(
        "Fig 9.1 — Distribution des questions par catégorie d'erreur\n"
        "(config : recursive-512-64 / ada-002 / hybrid-k5 / azure-gpt35 ; classification automatique)"
    )
    ax.set_xlim(0, max(counts.values) * 1.18 + 1)
    _save(fig, "fig_9_1_distribution_categories_erreur.png", out_dir)


def fig_9_2_heatmap_question_ragas(out_dir: Path) -> None:
    df = load_detail().sort_values("question_id")
    metrics = ["ragas_faithfulness", "ragas_answer_relevancy",
               "ragas_context_precision", "ragas_context_recall"]
    short = ["faith", "ans_rel", "ctx_prec", "ctx_recall"]
    mat = df.set_index("question_id")[metrics]
    mat.columns = short

    fig, ax = plt.subplots(figsize=(7, 12))
    sns.heatmap(
        mat, annot=True, fmt=".2f", cmap="RdYlGn", vmin=0, vmax=1,
        cbar_kws={"label": "Score RAGAS"}, linewidths=0.3, linecolor="white",
        ax=ax, annot_kws={"size": 7},
    )
    ax.set_title("Fig 9.2 — Heatmap question × scores RAGAS (50 questions)")
    ax.set_xlabel("")
    ax.set_ylabel("Question")
    _save(fig, "fig_9_2_heatmap_question_ragas.png", out_dir)


def fig_9_3_ragas_par_type_question(out_dir: Path) -> None:
    detail = load_detail()
    meta = load_test_set()[["question_id", "type"]]
    df = detail.merge(meta, on="question_id", how="left")
    metrics = ["ragas_faithfulness", "ragas_answer_relevancy",
               "ragas_context_precision", "ragas_context_recall"]
    labels_map = {
        "ragas_faithfulness": "Faithfulness",
        "ragas_answer_relevancy": "Answer Rel.",
        "ragas_context_precision": "Context Prec.",
        "ragas_context_recall": "Context Recall",
    }
    melted = df.melt(id_vars=["question_id", "type"], value_vars=metrics,
                     var_name="metric", value_name="score")
    melted["metric"] = melted["metric"].map(labels_map)
    order_types = ["factuelle", "procédurale", "conditionnelle",
                   "comparative", "justificative", "hors_perimetre"]
    order_types = [t for t in order_types if t in melted["type"].unique()]

    fig, ax = plt.subplots(figsize=(13, 6))
    sns.barplot(
        data=melted, x="type", y="score", hue="metric",
        order=order_types, ax=ax, palette="Set2",
        errorbar=("ci", 95), capsize=0.08,
    )
    counts = df.groupby("type").size().reindex(order_types, fill_value=0)
    ax.set_xticks(range(len(order_types)))
    ax.set_xticklabels([f"{t}\n(n = {counts[t]})" for t in order_types])
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("")
    ax.set_ylabel("Score RAGAS (moyenne ± IC 95 %)")
    ax.set_title("Fig 9.3 — Stratification des scores RAGAS par type de question")
    ax.legend(title="Métrique", loc="upper center", bbox_to_anchor=(0.5, -0.13),
              ncol=4, fontsize=9)
    _save(fig, "fig_9_3_ragas_par_type_question.png", out_dir)


def fig_9_4_scatter_longueur_ragas(out_dir: Path) -> None:
    df = load_detail().copy()
    df["n_words"] = df["answer"].fillna("").str.split().str.len()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    for ax, metric, title in [
        (axes[0], "ragas_faithfulness", "Faithfulness"),
        (axes[1], "ragas_answer_relevancy", "Answer Relevancy"),
    ]:
        sub = df[["n_words", metric]].dropna()
        ax.scatter(sub["n_words"], sub[metric], alpha=0.7,
                   color="#1f77b4", edgecolor="black", linewidth=0.4, s=55)
        # Régression linéaire simple.
        if len(sub) > 2:
            m, b = np.polyfit(sub["n_words"], sub[metric], 1)
            xs = np.linspace(sub["n_words"].min(), sub["n_words"].max(), 100)
            ax.plot(xs, m * xs + b, "r--", alpha=0.8, linewidth=1.5)
            r = float(np.corrcoef(sub["n_words"], sub[metric])[0, 1])
        else:
            r = float("nan")
        ax.set_title(f"{title}  (Pearson r = {r:+.2f})")
        ax.set_xlabel("Nombre de mots dans la réponse générée")
        ax.set_ylim(-0.05, 1.08)
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Score RAGAS")
    fig.suptitle(
        "Fig 9.4 — Biais de longueur sur les scores RAGAS\n"
        "(config : recursive-512-64 / ada-002 / hybrid-k5 / azure-gpt35)",
        fontsize=12, fontweight="bold",
    )
    fig.tight_layout()
    _save(fig, "fig_9_4_scatter_longueur_ragas.png", out_dir)


def fig_9_5_ragas_par_langue_criticite(out_dir: Path) -> None:
    detail = load_detail()
    meta = load_test_set()[["question_id", "language", "criticality"]]
    df = detail.merge(meta, on="question_id", how="left")
    metrics = ["ragas_faithfulness", "ragas_answer_relevancy",
               "ragas_context_precision", "ragas_context_recall"]
    labels_map = {
        "ragas_faithfulness": "Faithfulness",
        "ragas_answer_relevancy": "Answer Rel.",
        "ragas_context_precision": "Context Prec.",
        "ragas_context_recall": "Context Recall",
    }
    melted = df.melt(id_vars=["question_id", "language", "criticality"],
                     value_vars=metrics, var_name="metric", value_name="score")
    melted["metric"] = melted["metric"].map(labels_map)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)

    # Sous-figure A : par langue.
    lang_order = [l for l in ["fr", "en"] if l in melted["language"].unique()]
    sns.boxplot(
        data=melted, x="metric", y="score", hue="language",
        ax=axes[0], hue_order=lang_order, palette="Set1", showfliers=False,
    )
    counts_lang = df.groupby("language").size()
    handles, labs = axes[0].get_legend_handles_labels()
    new_labs = [f"{l} (n = {counts_lang.get(l, 0)})" for l in labs]
    axes[0].legend(handles, new_labs, title="Langue", loc="lower left", fontsize=9)
    axes[0].set_title("(a) Stratification par langue")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Score RAGAS")

    # Sous-figure B : par criticité.
    crit_order = [c for c in ["élevée", "moyenne", "faible"] if c in melted["criticality"].unique()]
    sns.boxplot(
        data=melted, x="metric", y="score", hue="criticality",
        ax=axes[1], hue_order=crit_order, palette="Set2", showfliers=False,
    )
    counts_crit = df.groupby("criticality").size()
    handles, labs = axes[1].get_legend_handles_labels()
    new_labs = [f"{c} (n = {counts_crit.get(c, 0)})" for c in labs]
    axes[1].legend(handles, new_labs, title="Criticité", loc="lower left", fontsize=9)
    axes[1].set_title("(b) Stratification par criticité")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("")

    for ax in axes:
        ax.set_ylim(0, 1.05)
        ax.tick_params(axis="x", labelrotation=10)

    fig.suptitle("Fig 9.5 — Scores RAGAS stratifiés par langue et par criticité",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "fig_9_5_ragas_par_langue_criticite.png", out_dir)


# ---------------------------------------------------------------------------
# Registre & entrée principale
# ---------------------------------------------------------------------------

FIGURES = {
    "8.1": fig_8_1_heatmap_mrr_modele_chunking,
    "8.2": fig_8_2_barplot_mrr_par_variante_recuperation,
    "8.3": fig_8_3_scatter_pareto_mrr_vs_latence,
    "8.4": fig_8_4_distribution_mrr,
    "8.5": fig_8_5_radar_ragas_5_configs,
    "8.6": fig_8_6_barplot_ragas_5_configs,
    "8.7": fig_8_7_boxplot_stabilite,
    "8.8": fig_8_8_scatter_interruns_vs_paraphrases,
    "8.9": fig_8_9_latence_endtoend_stacked,
    "9.1": fig_9_1_distribution_categories_erreur,
    "9.2": fig_9_2_heatmap_question_ragas,
    "9.3": fig_9_3_ragas_par_type_question,
    "9.4": fig_9_4_scatter_longueur_ragas,
    "9.5": fig_9_5_ragas_par_langue_criticite,
}


def main(selected: Iterable[str] | None, out_dir: Path) -> int:
    _setup_style()
    targets = list(FIGURES) if not selected else [k for k in selected if k in FIGURES]
    if selected:
        unknown = [k for k in selected if k not in FIGURES]
        if unknown:
            print(f"[WARN] Figures inconnues ignorées : {unknown}", file=sys.stderr)

    print(f"Génération de {len(targets)} figure(s) dans : {out_dir}\n")
    errors = []
    for key in targets:
        func = FIGURES[key]
        print(f"[..] Fig {key} — {func.__name__}")
        try:
            func(out_dir)
        except Exception as exc:  # noqa: BLE001
            errors.append((key, exc))
            print(f"  [KO] {exc}\n{traceback.format_exc()}", file=sys.stderr)

    print(f"\nTerminé. {len(targets) - len(errors)} OK / {len(errors)} erreur(s).")
    return 1 if errors else 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="+", metavar="ID",
                        help=f"Liste de figures à générer parmi : {', '.join(FIGURES)}")
    parser.add_argument("--out-dir", default=str(ROOT / "figures"),
                        help="Dossier de sortie (défaut : figures/)")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(main(args.only, Path(args.out_dir)))
