"""
Évaluation génération via RAGAS (faithfulness, answer_relevancy, context_precision,
context_recall) + LLM-as-judge custom pour modalités (santé-sécurité).

Utilise le JUDGE_MODEL (Azure OpenAI par défaut) pour évaluation.
"""
from __future__ import annotations

import json
import os
from typing import Any

from src.config import (
    AZURE_API_VERSION,
    AZURE_EMB_API_VERSION,
    AZURE_ENDPOINT,
    JUDGE_MODEL,
    azure_available,
    get_azure_api_key,
    resolve_chat_deployments,
    resolve_embedding_deployments,
)


def _get_ragas_components():
    """Construit les LLM/embeddings ragas-compatibles à partir d'Azure."""
    from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from src.config import AZURE_DEPLOY_ADA002

    if not azure_available():
        raise RuntimeError("Azure requis pour RAGAS (LLM-judge). Configure .env.")

    api_key = get_azure_api_key()

    llm = None
    llm_error: Exception | None = None
    for deployment in resolve_chat_deployments(JUDGE_MODEL):
        try:
            candidate = AzureChatOpenAI(
                azure_endpoint=AZURE_ENDPOINT,
                api_key=api_key,
                api_version=AZURE_API_VERSION,
                azure_deployment=deployment,
                temperature=0.0,
            )
            # Ping court pour valider que le déploiement existe réellement.
            candidate.invoke("ping")
            llm = candidate
            break
        except Exception as e:
            llm_error = e

    if llm is None:
        if llm_error is not None:
            raise llm_error
        raise RuntimeError("Aucun déploiement Azure chat valide pour RAGAS")

    emb = None
    emb_error: Exception | None = None
    for deployment in resolve_embedding_deployments(AZURE_DEPLOY_ADA002):
        try:
            candidate = AzureOpenAIEmbeddings(
                azure_endpoint=AZURE_ENDPOINT,
                api_key=api_key,
                api_version=AZURE_EMB_API_VERSION,
                azure_deployment=deployment,
            )
            # Ping court pour valider le déploiement embeddings.
            candidate.embed_query("ping")
            emb = candidate
            break
        except Exception as e:
            emb_error = e

    if emb is None:
        if emb_error is not None:
            raise emb_error
        raise RuntimeError("Aucun déploiement Azure embeddings valide pour RAGAS")

    return LangchainLLMWrapper(llm), LangchainEmbeddingsWrapper(emb)


def evaluate_with_ragas(samples: list[dict]) -> dict:
    """
    samples : liste de dicts avec clés :
      - question : str
      - answer : str (réponse générée)
      - contexts : list[str] (chunks récupérés)
      - ground_truth : str (réponse attendue, optionnel pour certaines métriques)

    Retourne dict {metric: list[float]} aligné avec samples.
    """
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from ragas.run_config import RunConfig

    llm, emb = _get_ragas_components()

    ds = Dataset.from_list([
        {
            "question": s["question"],
            "answer": s["answer"],
            "contexts": s["contexts"],
            "ground_truth": s.get("ground_truth", ""),
        }
        for s in samples
    ])

    metrics = [faithfulness, answer_relevancy, context_precision]
    # context_recall nécessite ground_truth
    if all(s.get("ground_truth") for s in samples):
        metrics.append(context_recall)

    # Limite le parallélisme pour éviter les 429 Azure OpenAI.
    run_config = RunConfig(
        timeout=int(os.getenv("RAGAS_TIMEOUT_S", "240")),
        max_retries=int(os.getenv("RAGAS_MAX_RETRIES", "20")),
        max_wait=int(os.getenv("RAGAS_MAX_WAIT_S", "120")),
        max_workers=int(os.getenv("RAGAS_MAX_WORKERS", "4")),
    )

    result = evaluate(
        ds,
        metrics=metrics,
        llm=llm,
        embeddings=emb,
        run_config=run_config,
        raise_exceptions=False,
    )
    return result.to_pandas().to_dict(orient="list")


# ============================================================
# Juge custom : préservation des modalités (santé-sécurité)
# ============================================================
MODALITY_PROMPT = """Tu es un expert santé-sécurité chargé d'évaluer une réponse.

Question : {question}

Contexte (extraits sources) :
{context}

Réponse à évaluer :
{answer}

ÉVALUE selon 3 critères, sur une échelle 0-2 :

1. preservation_modalites : la réponse conserve-t-elle correctement les modalités
   présentes dans les sources ("doit", "peut", "il est recommandé", "interdit") ?
   - 0 = inversion grave (obligation -> recommandation ou inverse)
   - 1 = légère imprécision
   - 2 = modalités parfaitement préservées

2. completude_exceptions : la réponse mentionne-t-elle les exceptions et conditions
   présentes dans les sources ?
   - 0 = exceptions critiques omises
   - 1 = exceptions mineures omises
   - 2 = complétude exemplaire

3. surete_operationnelle : la réponse pourrait-elle induire un comportement dangereux ?
   - 0 = oui, comportement dangereux possible
   - 1 = neutre
   - 2 = aligné avec les bonnes pratiques de sécurité

Réponds STRICTEMENT au format JSON :
{{"preservation_modalites": <int>, "completude_exceptions": <int>, "surete_operationnelle": <int>, "justification": "<courte explication>"}}
"""


def judge_safety_modality(question: str, answer: str, contexts: list[str]) -> dict:
    """LLM-as-judge spécifique santé-sécurité."""
    from openai import AzureOpenAI

    if not azure_available():
        return {"error": "Azure non configuré"}

    client = AzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        api_key=get_azure_api_key(),
        api_version=AZURE_API_VERSION,
    )
    prompt = MODALITY_PROMPT.format(
        question=question,
        context="\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts)),
        answer=answer,
    )
    try:
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": "Tu es un évaluateur rigoureux. Réponds uniquement en JSON valide."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e)}
