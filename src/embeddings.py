"""
Wrappers d'embeddings : HuggingFace (sentence-transformers) + Azure OpenAI.
Interface unifiée : encode_queries / encode_passages -> numpy array (n, dim).
"""
from __future__ import annotations

import time
from functools import lru_cache
from typing import Iterable

import numpy as np

from src.config import (
    DEVICE,
    AZURE_ENDPOINT,
    AZURE_API_KEY,
    AZURE_API_VERSION,
    AZURE_DEPLOY_ADA002,
    AZURE_DEPLOY_EMBED3_LARGE,
    EmbeddingConfig,
    EMBEDDING_MODELS,
    azure_available,
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
        kwargs = {}
        # bge-m3, jina v3 nécessitent trust_remote_code
        if any(x in cfg.model_id.lower() for x in ("bge-m3", "jina")):
            kwargs["trust_remote_code"] = True
        self.model = SentenceTransformer(cfg.model_id, device=DEVICE, **kwargs)
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
        self.client = AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION,
        )
        # cfg.model_id = "azure:ada-002" -> deployment name
        suffix = cfg.model_id.split(":", 1)[1]
        mapping = {
            "ada-002": AZURE_DEPLOY_ADA002,
            "embed-3-large": AZURE_DEPLOY_EMBED3_LARGE,
        }
        self.deployment = mapping.get(suffix, suffix)

    def _encode(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        out = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for attempt in range(3):
                try:
                    resp = self.client.embeddings.create(
                        model=self.deployment, input=batch
                    )
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    time.sleep(2 ** attempt)
            out.extend([d.embedding for d in resp.data])
        arr = np.asarray(out, dtype=np.float32)
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
