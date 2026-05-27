"""
Retrieval : dense (ChromaDB), sparse (BM25), hybride, reranking cross-encoder.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from tqdm import tqdm

from src.chunking import Chunk, load_chunks
from src.config import INDEXES_DIR, RetrievalConfig
from src.embeddings import get_embedder


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float
    rank: int


# ============================================================
# Index dense via ChromaDB (collection par couple chunking x embedding)
# ============================================================
def _collection_name(chunking_name: str, embed_name: str) -> str:
    safe = lambda s: s.replace("-", "_").replace(".", "_")
    return f"c_{safe(chunking_name)}__e_{safe(embed_name)}"


def build_dense_index(chunking_name: str, embed_name: str, batch_size: int = 64) -> str:
    """
    Construit (ou réutilise) un index ChromaDB pour un couple (chunking, embedding).
    Retourne le nom de la collection.
    """
    import chromadb
    from chromadb.utils.batch_utils import create_batches

    chunks = load_chunks(chunking_name)
    if not chunks:
        raise FileNotFoundError(f"Aucun chunk pour {chunking_name}. Lance build_all_chunkings.")

    coll_name = _collection_name(chunking_name, embed_name)
    persist_dir = INDEXES_DIR / "chroma"
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))

    existing = {c.name for c in client.list_collections()}
    if coll_name in existing:
        coll = client.get_collection(coll_name)
        if coll.count() == len(chunks):
            return coll_name
        client.delete_collection(coll_name)

    coll = client.create_collection(
        coll_name, metadata={"hnsw:space": "cosine"}
    )

    embedder = get_embedder(embed_name)
    texts = [c.text for c in chunks]
    ids = [c.chunk_id for c in chunks]
    metadatas = [{
        "doc_id": c.doc_id,
        "position": c.position,
        "filename": c.metadata.get("filename", ""),
        "language": c.metadata.get("language", "unknown"),
    } for c in chunks]
    print(f"  → Embedding {len(texts)} chunks avec {embed_name}...")
    embs = embedder.encode_passages(texts, batch_size=batch_size)

    # ChromaDB impose une taille maximale d'insertion par requete.
    for batch_ids, batch_embs, batch_metadatas, batch_documents in create_batches(
        api=client,
        ids=ids,
        embeddings=embs.tolist(),
        metadatas=metadatas,
        documents=texts,
    ):
        coll.add(
            ids=batch_ids,
            embeddings=batch_embs,
            documents=batch_documents,
            metadatas=batch_metadatas,
        )
    return coll_name


@lru_cache(maxsize=8)
def _get_chunk_lookup(chunking_name: str) -> dict[str, Chunk]:
    return {c.chunk_id: c for c in load_chunks(chunking_name)}


# ============================================================
# Retrievers
# ============================================================
class DenseRetriever:
    def __init__(self, chunking_name: str, embed_name: str):
        import chromadb
        self.chunking_name = chunking_name
        self.embed_name = embed_name
        coll_name = build_dense_index(chunking_name, embed_name)
        client = chromadb.PersistentClient(path=str(INDEXES_DIR / "chroma"))
        self.coll = client.get_collection(coll_name)
        self.embedder = get_embedder(embed_name)
        self.lookup = _get_chunk_lookup(chunking_name)

    def search(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        q_emb = self.embedder.encode_queries([query])[0].tolist()
        res = self.coll.query(query_embeddings=[q_emb], n_results=top_k)
        ids = res["ids"][0]
        # ChromaDB renvoie distances cosinus (1 - similarité)
        dists = res["distances"][0]
        out = []
        for rank, (cid, dist) in enumerate(zip(ids, dists)):
            chunk = self.lookup.get(cid)
            if chunk is None:
                continue
            score = 1.0 - dist
            out.append(RetrievedChunk(chunk=chunk, score=score, rank=rank))
        return out


class BM25Retriever:
    def __init__(self, chunking_name: str):
        from rank_bm25 import BM25Okapi
        self.chunking_name = chunking_name
        self.chunks = load_chunks(chunking_name)
        tokenized = [self._tokenize(c.text) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re
        return re.findall(r"\w+", text.lower())

    def search(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        scores = self.bm25.get_scores(self._tokenize(query))
        idx = np.argsort(-scores)[:top_k]
        return [
            RetrievedChunk(chunk=self.chunks[i], score=float(scores[i]), rank=r)
            for r, i in enumerate(idx)
        ]


class HybridRetriever:
    """Fusion par scores normalisés alpha*dense + (1-alpha)*sparse."""
    def __init__(self, chunking_name: str, embed_name: str, alpha: float = 0.5):
        self.dense = DenseRetriever(chunking_name, embed_name)
        self.sparse = BM25Retriever(chunking_name)
        self.alpha = alpha

    @staticmethod
    def _normalize(scored: list[RetrievedChunk]) -> dict[str, float]:
        if not scored:
            return {}
        scores = np.array([s.score for s in scored])
        if scores.max() == scores.min():
            return {s.chunk.chunk_id: 0.5 for s in scored}
        norm = (scores - scores.min()) / (scores.max() - scores.min())
        return {s.chunk.chunk_id: float(norm[i]) for i, s in enumerate(scored)}

    def search(self, query: str, top_k: int = 10) -> list[RetrievedChunk]:
        k_pool = max(top_k * 4, 20)
        d_results = self.dense.search(query, top_k=k_pool)
        s_results = self.sparse.search(query, top_k=k_pool)
        d_norm = self._normalize(d_results)
        s_norm = self._normalize(s_results)
        lookup = {r.chunk.chunk_id: r.chunk for r in d_results + s_results}
        combined = {}
        for cid in set(d_norm) | set(s_norm):
            combined[cid] = self.alpha * d_norm.get(cid, 0) + (1 - self.alpha) * s_norm.get(cid, 0)
        sorted_ids = sorted(combined, key=combined.get, reverse=True)[:top_k]
        return [
            RetrievedChunk(chunk=lookup[cid], score=combined[cid], rank=r)
            for r, cid in enumerate(sorted_ids)
        ]


# ============================================================
# Reranking
# ============================================================
@lru_cache(maxsize=2)
def get_reranker(model_id: str):
    from sentence_transformers import CrossEncoder
    from src.config import DEVICE
    return CrossEncoder(model_id, device=DEVICE)


def rerank(query: str, candidates: list[RetrievedChunk], model_id: str, top_n: int) -> list[RetrievedChunk]:
    if not candidates:
        return candidates
    ce = get_reranker(model_id)
    pairs = [(query, r.chunk.text) for r in candidates]
    scores = ce.predict(pairs, show_progress_bar=False)
    ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
    return [
        RetrievedChunk(chunk=r.chunk, score=float(s), rank=i)
        for i, (r, s) in enumerate(ranked[:top_n])
    ]


# ============================================================
# Adjonction des chunks voisins (style ScribBERT)
# ============================================================
def add_neighbors(retrieved: list[RetrievedChunk], chunking_name: str) -> list[RetrievedChunk]:
    chunks = load_chunks(chunking_name)
    by_doc: dict[str, dict[int, Chunk]] = {}
    for c in chunks:
        by_doc.setdefault(c.doc_id, {})[c.position] = c

    seen: set[str] = set()
    out: list[RetrievedChunk] = []
    for r in retrieved:
        for offset in (-1, 0, 1):
            pos = r.chunk.position + offset
            neighbor = by_doc.get(r.chunk.doc_id, {}).get(pos)
            if neighbor is None or neighbor.chunk_id in seen:
                continue
            seen.add(neighbor.chunk_id)
            out.append(RetrievedChunk(
                chunk=neighbor,
                score=r.score if offset == 0 else r.score * 0.9,
                rank=len(out),
            ))
    return out


# ============================================================
# Façade
# ============================================================
def build_retriever(chunking_name: str, embed_name: str, ret_cfg: RetrievalConfig):
    """Construit le retriever adapté à la configuration."""
    if ret_cfg.mode == "dense":
        return DenseRetriever(chunking_name, embed_name)
    if ret_cfg.mode == "sparse":
        return BM25Retriever(chunking_name)
    if ret_cfg.mode == "hybrid":
        return HybridRetriever(chunking_name, embed_name, alpha=ret_cfg.alpha)
    raise ValueError(ret_cfg.mode)


def run_retrieval(query: str, chunking_name: str, embed_name: str,
                  ret_cfg: RetrievalConfig,
                  retriever=None) -> list[RetrievedChunk]:
    retriever = retriever or build_retriever(chunking_name, embed_name, ret_cfg)
    k_initial = ret_cfg.rerank_top_n if ret_cfg.rerank else ret_cfg.top_k
    results = retriever.search(query, top_k=k_initial)

    if ret_cfg.rerank:
        results = rerank(query, results, ret_cfg.rerank_model, top_n=ret_cfg.top_k)

    if ret_cfg.score_threshold is not None:
        results = [r for r in results if r.score >= ret_cfg.score_threshold]

    if ret_cfg.add_neighbors:
        results = add_neighbors(results, chunking_name)

    return results
