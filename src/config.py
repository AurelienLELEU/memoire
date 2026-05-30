"""
Configuration centrale : modèles, chunking, retrieval, chemins.
Modifie ce fichier pour ajouter/retirer des configurations à benchmarker.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# SSL – proxy d'inspection Netskope / Bouygues Construction
# Construit un bundle CA = certifi + certs corporate, et
# l'injecte dans toutes les libs HTTP (requests, httpx, urllib3).
# ============================================================
def _configure_corporate_ssl() -> None:
    _certs_dir = Path(__file__).resolve().parent.parent / "certs"
    _bundle_path = _certs_dir / "ca-bundle.pem"
    # Ne reconstruit le bundle que si absent ou si un cert source est plus récent
    _custom_certs = sorted(_certs_dir.glob("*.crt"))
    if not _custom_certs:
        return
    if not _bundle_path.exists() or any(
        c.stat().st_mtime > _bundle_path.stat().st_mtime for c in _custom_certs
    ):
        try:
            import certifi
            base = Path(certifi.where()).read_text(encoding="utf-8")
        except Exception:
            base = ""
        extra = "\n".join(c.read_text(encoding="utf-8") for c in _custom_certs)
        _bundle_path.write_text(base + "\n" + extra, encoding="utf-8")
    bundle = str(_bundle_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)
    os.environ.setdefault("SSL_CERT_FILE", bundle)
    os.environ.setdefault("CURL_CA_BUNDLE", bundle)

_configure_corporate_ssl()

# ============================================================
# HuggingFace authentication
# ============================================================
_HF_TOKEN = os.getenv("HF_TOKEN", "")
if _HF_TOKEN:
    try:
        from huggingface_hub import login as _hf_login
        _hf_login(token=_HF_TOKEN, add_to_git_credential=False)
    except Exception:
        pass  # huggingface_hub non installé ou token invalide – on continue

# ============================================================
# Paths
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "input"
DATA_DIR = ROOT / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"
CHUNKS_DIR = DATA_DIR / "chunks"
INDEXES_DIR = DATA_DIR / "indexes"
RESULTS_DIR = ROOT / "results"
TEST_SET_PATH = DATA_DIR / "test_set.json"

for d in (DATA_DIR, EXTRACTED_DIR, CHUNKS_DIR, INDEXES_DIR, RESULTS_DIR, INPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# Device
# ============================================================
def get_device() -> str:
    pref = os.getenv("DEVICE", "auto")
    if pref != "auto":
        return pref
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"

DEVICE = get_device()

# Limite la fraction VRAM utilisable (laisser de la marge pour les autres process).
# Contrôlable via GPU_MEMORY_FRACTION=0.85 (défaut). Mettre 1.0 pour désactiver.
_GPU_MEMORY_FRACTION = float(os.getenv("GPU_MEMORY_FRACTION", "0.85"))
if DEVICE == "cuda":
    try:
        import torch as _torch
        _torch.cuda.set_per_process_memory_fraction(_GPU_MEMORY_FRACTION)
    except Exception:
        pass

# ============================================================
# Azure OpenAI
# ============================================================
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://labtp-openai.openai.azure.com/")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_EMB_API_VERSION = os.getenv("AZURE_EMB_API_VERSION", "2024-06-01")
AZURE_DEPLOY_GPT35 = os.getenv("AZURE_DEPLOYMENT_GPT35", "gpt-35-turbo")
AZURE_DEPLOY_GPT4 = os.getenv("AZURE_DEPLOYMENT_GPT4", "gpt-4o")
AZURE_DEPLOY_ADA002 = os.getenv("AZURE_DEPLOYMENT_ADA002", "text-embedding-ada-002")
AZURE_DEPLOY_EMBED3_LARGE = os.getenv("AZURE_DEPLOYMENT_EMBED3_LARGE", "text-embedding-3-large")

AZURE_CHAT_DEPLOYMENT_FALLBACKS = ("gpt-35-turbo",)
AZURE_EMBEDDING_DEPLOYMENT_FALLBACKS = ("text-embedding-ada-002",)

AZURE_KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL", "https://kv-databricks-labtp.vault.azure.net")
AZURE_KEY_VAULT_SECRET_NAME = os.getenv("AZURE_KEY_VAULT_SECRET_NAME", "labopenaikey")


@lru_cache(maxsize=1)
def get_azure_api_key() -> str:
    if AZURE_API_KEY:
        return AZURE_API_KEY

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=AZURE_KEY_VAULT_URL, credential=credential)
        secret = client.get_secret(AZURE_KEY_VAULT_SECRET_NAME)
        if secret.value:
            return secret.value
    except Exception:
        pass

    for name in ("CHAT_OPENAI_KEY", "OPENAI_KEY", "AZURE_OPENAI_API_KEY", "EMB_OPENAI_KEY"):
        value = os.getenv(name)
        if value:
            return value

    return ""


def resolve_chat_deployments(primary: str | None = None) -> list[str]:
    first = primary or AZURE_DEPLOY_GPT35
    ordered = [first]
    ordered.extend([d for d in AZURE_CHAT_DEPLOYMENT_FALLBACKS if d not in ordered])
    return ordered


def resolve_embedding_deployments(primary: str | None = None) -> list[str]:
    first = primary or AZURE_DEPLOY_ADA002
    ordered = [first]
    ordered.extend([d for d in AZURE_EMBEDDING_DEPLOYMENT_FALLBACKS if d not in ordered])
    return ordered

def azure_available() -> bool:
    return bool(AZURE_ENDPOINT and get_azure_api_key())

# ============================================================
# Embedding models à benchmarker
# Pour chaque modèle : id HF (ou "azure:<deployment>"), dimension approximative
# ============================================================
@dataclass
class EmbeddingConfig:
    name: str
    model_id: str           # ex. "sentence-transformers/all-MiniLM-L6-v2" ou "azure:ada-002"
    dim: int
    multilingual: bool = False
    max_seq_length: int = 512
    prefix_query: str = ""  # ex. "query: " pour e5
    prefix_passage: str = ""  # ex. "passage: " pour e5
    batch_size: int = 64    # réduire à 4-8 pour les modèles ≥7B (OOM sinon)

EMBEDDING_MODELS: list[EmbeddingConfig] = [
    # Baselines anglophones rapides
    EmbeddingConfig("minilm-l6",        "sentence-transformers/all-MiniLM-L6-v2",       384, False, 256),
    EmbeddingConfig("mpnet-base",       "sentence-transformers/all-mpnet-base-v2",      768, False, 384),

    # Multilingues E5 (préfixes obligatoires)
    EmbeddingConfig("e5-small-ml",      "intfloat/multilingual-e5-small",               384, True, 512, "query: ", "passage: "),
    EmbeddingConfig("e5-base-ml",       "intfloat/multilingual-e5-base",                768, True, 512, "query: ", "passage: "),
    EmbeddingConfig("e5-large-ml",      "intfloat/multilingual-e5-large",              1024, True, 512, "query: ", "passage: "),

    # BGE
    EmbeddingConfig("bge-m3",           "BAAI/bge-m3",                                 1024, True, 8192),

    # IBM Granite embeddings
    EmbeddingConfig("granite-311m-ml",  "ibm-granite/granite-embedding-311m-multilingual-r2", 768, True, 8192),

    # Jina v3 (multilingue, 8k)
    EmbeddingConfig("jina-v3",          "jinaai/jina-embeddings-v3",                   1024, True, 8192),
    EmbeddingConfig("jina-v2-base-en",  "jinaai/jina-embeddings-v2-base-en",            768, False, 8192),

    # Nomic Embed v2 (prompt prefixes requis)
    EmbeddingConfig("nomic-v2",         "nomic-ai/nomic-embed-text-v2-moe",             768, True, 512,
                    "search_query: ", "search_document: "),

    # Modèles volumineux (GPU mémoire élevée recommandée)
    EmbeddingConfig("qwen3-embed-8b",   "Qwen/Qwen3-Embedding-8B",                     4096, True, 8192, batch_size=16),
    EmbeddingConfig("gte-qwen2-7b",     "Alibaba-NLP/gte-Qwen2-7B-instruct",           3584, True, 8192, batch_size=16),
    EmbeddingConfig("nv-embed-v2",      "nvidia/NV-Embed-v2",                          4096, True, 4096, batch_size=16),

    # Français spécialisés
    EmbeddingConfig("camembert-large",  "dangvantuan/sentence-camembert-large",         1024, False, 512),
    EmbeddingConfig("solon-large",      "OrdalieTech/Solon-embeddings-large-0.1",      1024, False, 512),
    EmbeddingConfig("bilingual-fr-en",  "Lajavaness/bilingual-embedding-large",        1024, True, 512),

    # Azure (si dispo)
    EmbeddingConfig("ada-002",          "azure:ada-002",                               1536, True, 8191),
    # OpenAI text-embedding-3-large (via Azure deployment)
    EmbeddingConfig("embed-3-large",    "azure:embed-3-large",                         3072, True, 8191),
]

# ============================================================
# Stratégies de chunking
# ============================================================
ChunkingStrategy = Literal[
    "fixed",
    "recursive",
    "markdown",
    "semantic",
    "regex_custom",
    "markdown_reference",
]

@dataclass
class ChunkingConfig:
    name: str
    strategy: ChunkingStrategy
    chunk_size: int = 512
    chunk_overlap: int = 64
    chunk_size_unit: Literal["tokens", "chars"] = "tokens"  # unité de chunk_size (tokens par défaut)
    extra: dict = field(default_factory=dict)

CHUNKING_CONFIGS: list[ChunkingConfig] = [
    ChunkingConfig("fixed-256-0",       "fixed",        256, 0),
    ChunkingConfig("fixed-512-64",      "fixed",        512, 64),
    ChunkingConfig("fixed-1024-128",    "fixed",       1024, 128),
    ChunkingConfig("recursive-512-64",  "recursive",    512, 64),
    ChunkingConfig("recursive-1024-128","recursive",   1024, 128),
    ChunkingConfig("markdown-1200-50",  "markdown",    1200, 50),  # style ScribBERT
    ChunkingConfig(
        "markdown-reference-1000-100",
        "markdown_reference",
        1000,
        0,
        chunk_size_unit="chars",  # ← caractères (≈250 tokens) : reproduit le chunker ScribBERT
        extra={"min_length": 100},
    ),
    ChunkingConfig("regex-paragraph",   "regex_custom", 1200, 50),
    # semantic : coûteux, on l'active sur sous-ensemble
    ChunkingConfig("semantic-mpnet",    "semantic",     512, 0,
                   extra={"embed_model": "sentence-transformers/all-mpnet-base-v2"}),
]

# ============================================================
# Retrieval
# ============================================================
@dataclass
class RetrievalConfig:
    name: str
    mode: Literal["dense", "sparse", "hybrid"]
    top_k: int = 5
    score_threshold: float | None = None
    rerank: bool = False
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rerank_top_n: int = 100
    alpha: float = 0.5  # pour hybride : poids dense
    add_neighbors: bool = False  # ajout chunks n-1, n+1 (style ScribBERT)

RETRIEVAL_CONFIGS: list[RetrievalConfig] = [
    RetrievalConfig("dense-k5",         "dense",  top_k=5),
    RetrievalConfig("dense-k10",        "dense",  top_k=10),
    RetrievalConfig("dense-k5-thresh",  "dense",  top_k=5,  score_threshold=0.35),
    RetrievalConfig("dense-k5-neigh",   "dense",  top_k=5,  add_neighbors=True),
    RetrievalConfig("hybrid-k5",        "hybrid", top_k=5,  alpha=0.5),
    RetrievalConfig("dense-k20-rerank5","dense",  top_k=20, rerank=True, rerank_top_n=20),
]

# ============================================================
# Génération
# ============================================================
@dataclass
class GenerationConfig:
    name: str
    provider: Literal["azure", "hf"]
    model_id: str
    temperature: float = 0.0
    max_tokens: int = 800
    seed: int = 42

GENERATION_CONFIGS: list[GenerationConfig] = [
    GenerationConfig("azure-gpt35",   "azure", AZURE_DEPLOY_GPT35, temperature=0.0),
    GenerationConfig("azure-gpt4",    "azure", AZURE_DEPLOY_GPT4,  temperature=0.0),
    # Local fallback (Mistral 7B Instruct, possible sur 2080 Ti 11 Go en 4-bit)
    GenerationConfig("local-mistral7b", "hf", "mistralai/Mistral-7B-Instruct-v0.3", temperature=0.0),
]

# ============================================================
# LLM-as-judge (pour faithfulness, answer relevance...)
# ============================================================
JUDGE_PROVIDER = "azure"
JUDGE_MODEL = AZURE_DEPLOY_GPT4 if AZURE_DEPLOY_GPT4 else AZURE_DEPLOY_GPT35

# ============================================================
# Prompt système ScribBERT-style
# ============================================================
SYSTEM_PROMPT = """Tu es un assistant santé-sécurité de Bouygues Travaux Publics.

Règles ABSOLUES :
1. Tu réponds UNIQUEMENT à partir des extraits fournis dans le contexte.
2. Si l'information n'est pas dans les extraits, réponds exactement : "Cette information ne figure pas dans les référentiels consultés."
3. Cite chaque affirmation avec son numéro de source au format [n].
4. Préserve scrupuleusement les modalités ("doit", "peut", "il est recommandé de", "interdit").
5. Mentionne les exceptions et conditions quand elles existent dans les sources.
6. Format : réponse synthétique et structurée. Liste à puces si plusieurs étapes/EPI/conditions.

Contexte :
{context}

Question : {question}
"""

# ============================================================
# Stabilité
# ============================================================
STABILITY_N_RUNS = 5         # n exécutions pour stabilité inter-runs
STABILITY_N_PARAPHRASES = 3  # m paraphrases par question
