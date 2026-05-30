"""
Stratégies de chunking : fixed, recursive, markdown structural, semantic,
regex custom, et chunker markdown de référence.
Chaque stratégie retourne une liste de Chunk avec métadonnées.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from functools import lru_cache
from pathlib import Path
from typing import Callable

import tiktoken
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from tqdm import tqdm

from src.config import CHUNKING_CONFIGS, CHUNKS_DIR, ChunkingConfig
from src.ingestion import iter_documents
from src.markdown_chunker import chunk_markdown_text


# Encodeur tiktoken pour compter les tokens (cl100k = GPT-3.5/4, bonne approx)
_TOK = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_TOK.encode(text))


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    position: int           # ordre dans le document
    n_tokens: int
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# Splitters
# ============================================================
def split_fixed(text: str, size_tokens: int, overlap_tokens: int) -> list[str]:
    """Découpe au token près (cl100k)."""
    tokens = _TOK.encode(text)
    chunks = []
    step = max(1, size_tokens - overlap_tokens)
    for start in range(0, len(tokens), step):
        end = start + size_tokens
        chunk_tokens = tokens[start:end]
        if not chunk_tokens:
            break
        chunks.append(_TOK.decode(chunk_tokens))
        if end >= len(tokens):
            break
    return chunks


def split_recursive(text: str, size_tokens: int, overlap_tokens: int) -> list[str]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=size_tokens,
        chunk_overlap=overlap_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def split_markdown(text: str, size_tokens: int, overlap_tokens: int) -> list[str]:
    """
    Splitter structural : on segmente d'abord sur titres markdown,
    puis recursive splitter sur sections trop longues.
    """
    headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers, strip_headers=False)
    try:
        docs = md_splitter.split_text(text)
    except Exception:
        docs = [type("D", (), {"page_content": text, "metadata": {}})()]

    sub_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=size_tokens,
        chunk_overlap=overlap_tokens,
    )

    chunks: list[str] = []
    for d in docs:
        if count_tokens(d.page_content) <= size_tokens:
            chunks.append(d.page_content)
        else:
            chunks.extend(sub_splitter.split_text(d.page_content))
    return [c for c in chunks if c.strip()]


def split_regex_custom(text: str, size_tokens: int, overlap_tokens: int) -> list[str]:
    """
    Style ScribBERT : split sur titres markdown / paragraphes,
    fusion jusqu'à atteindre size_tokens.
    """
    # split sur titres ou doubles sauts de ligne
    parts = re.split(r"(?=^#{1,6}\s)|(?<=\n)\n+", text, flags=re.MULTILINE)
    parts = [p.strip() for p in parts if p.strip()]

    chunks: list[str] = []
    buffer = ""
    for part in parts:
        candidate = (buffer + "\n\n" + part).strip() if buffer else part
        if count_tokens(candidate) > size_tokens and buffer:
            chunks.append(buffer)
            buffer = part
        else:
            buffer = candidate
    if buffer:
        chunks.append(buffer)
    return chunks


def split_markdown_reference(
    text: str,
    size_chars: int,
    overlap_ignored: int,
    min_length: int = 100,
) -> list[str]:
    """
    Applique le chunker markdown de référence basé sur le parser PDF historique.
    size_chars : longueur max en CARACTÈRES (pas en tokens).
    overlap_ignored : ignoré (le chunker de référence ne gère pas l'overlap).
    """
    del overlap_ignored
    chunks = chunk_markdown_text(
        text,
        max_chunk_length=size_chars,
        min_length=min_length,
    )
    return [chunk["text"] for chunk in chunks if chunk.get("text", "").strip()]


@lru_cache(maxsize=4)
def _load_semantic_model(embed_model: str):
    from sentence_transformers import SentenceTransformer

    last_error: Exception | None = None
    for attempt in range(4):
        try:
            return SentenceTransformer(embed_model)
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if "client has been closed" not in msg and "connection reset" not in msg:
                raise
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Impossible de charger le modèle sémantique {embed_model}: {last_error}")


def split_semantic(text: str, size_tokens: int, overlap_tokens: int, embed_model: str = "sentence-transformers/all-mpnet-base-v2") -> list[str]:
    """
    Chunking sémantique : on découpe en phrases, on calcule les embeddings,
    et on coupe aux ruptures de similarité (technique Greg Kamradt).
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        return split_recursive(text, size_tokens, overlap_tokens)

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 3:
        return [text]

    try:
        model = _load_semantic_model(embed_model)
    except Exception as e:
        print(f"  ! semantic fallback to recursive for {embed_model}: {e}")
        return split_recursive(text, size_tokens, overlap_tokens)

    embs = model.encode(
        sentences,
        show_progress_bar=len(sentences) > 64,
        normalize_embeddings=True,
    )
    # similarités consécutives
    sims = [float(np.dot(embs[i], embs[i + 1])) for i in range(len(embs) - 1)]
    threshold = float(np.percentile(sims, 25))  # 25e percentile = ruptures

    chunks: list[str] = []
    current: list[str] = [sentences[0]]
    for i, sim in enumerate(sims):
        next_sent = sentences[i + 1]
        joined = " ".join(current + [next_sent])
        if sim < threshold or count_tokens(joined) > size_tokens:
            chunks.append(" ".join(current))
            current = [next_sent]
        else:
            current.append(next_sent)
    if current:
        chunks.append(" ".join(current))
    return chunks


# ============================================================
# Dispatch
# ============================================================
SPLITTERS: dict[str, Callable[..., list[str]]] = {
    "fixed": split_fixed,
    "recursive": split_recursive,
    "markdown": split_markdown,
    "markdown_reference": split_markdown_reference,
    "regex_custom": split_regex_custom,
    "semantic": split_semantic,
}


def chunk_corpus(cfg: ChunkingConfig) -> list[Chunk]:
    """Applique une stratégie sur tous les documents extraits."""
    splitter = SPLITTERS[cfg.strategy]
    # markdown_reference a des noms de paramètres distincts (size_chars, overlap_ignored)
    # car son unité est explicitement des caractères, pas des tokens.
    if cfg.strategy == "markdown_reference":
        kwargs: dict = dict(
            size_chars=cfg.chunk_size,
            overlap_ignored=cfg.chunk_overlap,
            min_length=cfg.extra.get("min_length", 100),
        )
    else:
        kwargs = dict(size_tokens=cfg.chunk_size, overlap_tokens=cfg.chunk_overlap)
        if cfg.strategy == "semantic":
            kwargs["embed_model"] = cfg.extra.get("embed_model", "sentence-transformers/all-mpnet-base-v2")

    all_chunks: list[Chunk] = []
    documents = iter_documents()
    if cfg.strategy == "semantic":
        documents = tqdm(documents, desc=f"docs:{cfg.name}", unit="doc")

    for doc_id, text, meta in documents:
        try:
            texts = splitter(text, **kwargs)
        except Exception as e:
            print(f"  ✗ {doc_id}: {e}")
            continue
        for pos, t in enumerate(texts):
            ch = Chunk(
                chunk_id=f"{doc_id}__{pos:04d}",
                doc_id=doc_id,
                text=t,
                position=pos,
                n_tokens=count_tokens(t),
                metadata={
                    "filename": meta.get("filename", doc_id),
                    "language": meta.get("language", "unknown"),
                    "chunking_strategy": cfg.name,
                },
            )
            all_chunks.append(ch)
    return all_chunks


def save_chunks(chunks: list[Chunk], cfg_name: str) -> Path:
    out = CHUNKS_DIR / f"{cfg_name}.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
    return out


def load_chunks(cfg_name: str) -> list[Chunk]:
    path = CHUNKS_DIR / f"{cfg_name}.jsonl"
    if not path.exists():
        return []
    chunks: list[Chunk] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            chunks.append(Chunk(**d))
    return chunks


def _summarize_chunks(cfg_name: str, chunks: list[Chunk]) -> dict:
    avg_tok = sum(c.n_tokens for c in chunks) / max(1, len(chunks))
    return {
        "config": cfg_name,
        "n_chunks": len(chunks),
        "avg_tokens": round(avg_tok, 1),
    }


def build_all_chunkings(
    chunking_names: list[str] | None = None,
    skip_existing: bool = False,
):
    """Génère les jeux de chunks demandés définis dans config.py."""
    cfg_lookup = {cfg.name: cfg for cfg in CHUNKING_CONFIGS}
    if chunking_names:
        unknown = [name for name in chunking_names if name not in cfg_lookup]
        if unknown:
            raise ValueError(f"Chunkings inconnus: {', '.join(unknown)}")
        selected_cfgs = [cfg_lookup[name] for name in chunking_names]
    else:
        selected_cfgs = CHUNKING_CONFIGS

    stats_path = CHUNKS_DIR / "_stats.json"
    stats_map: dict[str, dict] = {}
    if stats_path.exists():
        try:
            existing_stats = json.loads(stats_path.read_text(encoding="utf-8"))
            stats_map = {
                item["config"]: item
                for item in existing_stats
                if isinstance(item, dict) and item.get("config")
            }
        except Exception:
            stats_map = {}

    for cfg in selected_cfgs:
        print(f"→ Chunking : {cfg.name}")
        out_path = CHUNKS_DIR / f"{cfg.name}.jsonl"
        if skip_existing and out_path.exists():
            print("  ↷ déjà présent, génération ignorée")
            if cfg.name not in stats_map:
                stats_map[cfg.name] = _summarize_chunks(cfg.name, load_chunks(cfg.name))
            continue
        chunks = chunk_corpus(cfg)
        save_chunks(chunks, cfg.name)
        stats_map[cfg.name] = _summarize_chunks(cfg.name, chunks)
        avg_tok = stats_map[cfg.name]["avg_tokens"]
        print(f"  ✓ {len(chunks)} chunks (moy. {avg_tok:.0f} tokens)")

    stats = [stats_map[cfg.name] for cfg in CHUNKING_CONFIGS if cfg.name in stats_map]
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


if __name__ == "__main__":
    build_all_chunkings()
