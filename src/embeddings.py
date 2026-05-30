"""
Wrappers d'embeddings : HuggingFace (sentence-transformers) + Azure OpenAI.
Interface unifiée : encode_queries / encode_passages -> numpy array (n, dim).
"""
from __future__ import annotations

import time
from functools import lru_cache
from typing import Any
from typing import Iterable

import numpy as np

from src.config import (
    DEVICE,
    AZURE_ENDPOINT,
    AZURE_API_VERSION,
    AZURE_EMB_API_VERSION,
    AZURE_DEPLOY_ADA002,
    AZURE_DEPLOY_EMBED3_LARGE,
    EmbeddingConfig,
    EMBEDDING_MODELS,
    azure_available,
    get_azure_api_key,
    resolve_embedding_deployments,
)


class BaseEmbedder:
    cfg: EmbeddingConfig

    def encode_queries(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        raise NotImplementedError

    def encode_passages(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        raise NotImplementedError


# ============================================================
# HuggingFace via sentence-transformers
# ============================================================
class HFEmbedder(BaseEmbedder):
    def __init__(self, cfg: EmbeddingConfig):
        from sentence_transformers import SentenceTransformer

        self.cfg = cfg
        kwargs: dict[str, Any] = {}
        # Certains modèles (bge-m3, jina v3, Lajavaness bilingual) nécessitent trust_remote_code.
        if any(
            x in cfg.model_id.lower()
            for x in ("bge-m3", "jina", "lajavaness", "nomic", "qwen", "nvidia", "granite", "gte-")
        ):
            kwargs["trust_remote_code"] = True

        # Résilience face aux erreurs réseau HF transitoires (connection reset,
        # client httpx fermé après retry interne, etc.).
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                self.model = SentenceTransformer(cfg.model_id, device=DEVICE, **kwargs)
                break
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                if "client has been closed" not in msg and "connection reset" not in msg:
                    raise
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"Impossible de charger le modèle HF {cfg.model_id}: {last_error}")

        try:
            self.model.max_seq_length = min(cfg.max_seq_length, self.model.max_seq_length)
        except Exception:
            pass

    def _encode(self, texts: list[str], prefix: str, batch_size: int) -> np.ndarray:
        if prefix:
            texts = [prefix + t for t in texts]
        embs = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 64,
        )
        return embs.astype(np.float32)

    def encode_queries(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        return self._encode(texts, self.cfg.prefix_query, batch_size)

    def encode_passages(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        return self._encode(texts, self.cfg.prefix_passage, batch_size)


# ============================================================
# Azure OpenAI
# ============================================================
class AzureEmbedder(BaseEmbedder):
    def __init__(self, cfg: EmbeddingConfig):
        from openai import AzureOpenAI

        if not azure_available():
            raise RuntimeError("Azure non configuré (.env)")

        self.cfg = cfg
        self.api_key = get_azure_api_key()
        self.client = AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=self.api_key,
            api_version=AZURE_EMB_API_VERSION,
            timeout=60.0,
            max_retries=2,
        )
        # cfg.model_id = "azure:ada-002" -> deployment name
        suffix = cfg.model_id.split(":", 1)[1]
        mapping = {
            "ada-002": AZURE_DEPLOY_ADA002,
            "embed-3-large": AZURE_DEPLOY_EMBED3_LARGE,
        }
        self.deployment = mapping.get(suffix, suffix)

    def _encode(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        deployments = resolve_embedding_deployments(self.deployment)
        out: list[list[float] | None] = []
        n_batches = (len(texts) + batch_size - 1) // batch_size
        show_bar = len(texts) > batch_size
        batches = range(0, len(texts), batch_size)
        if show_bar:
            from tqdm import tqdm as _tqdm
            batches = _tqdm(batches, total=n_batches, desc=f"  azure/{self.deployment}", leave=False)
        for i in batches:
            raw_batch = texts[i:i + batch_size]
            # Azure rejette les strings vides avec 400 $.input invalid — on les filtre
            non_empty_idx = [j for j, t in enumerate(raw_batch) if t.strip()]
            batch = [raw_batch[j] for j in non_empty_idx]
            if not batch:
                out.extend([None] * len(raw_batch))
                continue
            last_error = None
            resp = None
            for deployment in deployments:
                for attempt in range(3):
                    try:
                        resp = self.client.embeddings.create(
                            model=deployment, input=batch
                        )
                        break
                    except Exception as e:
                        last_error = e
                        if attempt == 2:
                            continue
                        time.sleep(2 ** attempt)
                if resp is not None:
                    break
            if resp is None:
                if last_error is not None:
                    raise last_error
                raise RuntimeError("Erreur inconnue lors de l'appel embeddings Azure")
            embs = [d.embedding for d in resp.data]
            # Réinjecter dans les bonnes positions ; les slots vides restent None
            slot: list[list[float] | None] = [None] * len(raw_batch)
            for k, j in enumerate(non_empty_idx):
                slot[j] = embs[k]
            out.extend(slot)

        # Construire la matrice finale : inférer la dim depuis le premier vecteur non-None
        dim = next((len(v) for v in out if v is not None), self.cfg.dim)
        arr = np.array(
            [v if v is not None else [0.0] * dim for v in out],
            dtype=np.float32,
        )
        # normalisation L2 (cosinus = dot product)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return arr / norms

    def encode_queries(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        return self._encode(texts, batch_size)

    def encode_passages(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        return self._encode(texts, batch_size)


# ============================================================
# Factory
# ============================================================
@lru_cache(maxsize=4)
def get_embedder(cfg_name: str) -> BaseEmbedder:
    cfg = next((c for c in EMBEDDING_MODELS if c.name == cfg_name), None)
    if cfg is None:
        raise ValueError(f"Embedding inconnu: {cfg_name}")
    if cfg.model_id.startswith("azure:"):
        return AzureEmbedder(cfg)
    return HFEmbedder(cfg)


def list_available_embedders() -> list[EmbeddingConfig]:
    """Filtre les Azure si non configuré."""
    out = []
    for c in EMBEDDING_MODELS:
        if c.model_id.startswith("azure:") and not azure_available():
            continue
        out.append(c)
    return out
