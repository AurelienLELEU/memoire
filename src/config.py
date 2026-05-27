"""
Configuration centrale : modèles, chunking, retrieval, chemins.
Modifie ce fichier pour ajouter/retirer des configurations à benchmarker.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

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
# SSL / certificats d'entreprise
# ============================================================
def configure_ssl_certificates() -> None:
    """
    Configure un bundle CA explicite pour requests/httpx/huggingface_hub.
    Priorité:
      1) CUSTOM_CA_BUNDLE (env)
      2) certs/netskope_bundle.pem (repo)
    """
    custom_bundle = os.getenv("CUSTOM_CA_BUNDLE", "").strip()
    default_bundle = ROOT / "certs" / "netskope_bundle.pem"

    bundle_path = Path(custom_bundle).expanduser() if custom_bundle else default_bundle
    if not bundle_path.exists():
        return

    # Définit seulement si absent, pour respecter une config système explicite.
    os.environ.setdefault("SSL_CERT_FILE", str(bundle_path))
    os.environ.setdefault("REQUESTS_CA_BUNDLE", str(bundle_path))
    os.environ.setdefault("CURL_CA_BUNDLE", str(bundle_path))


configure_ssl_certificates()

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

# ============================================================
# Azure OpenAI
# ============================================================
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_DEPLOY_GPT35 = os.getenv("AZURE_DEPLOYMENT_GPT35", "gpt-35-turbo")
AZURE_DEPLOY_GPT4 = os.getenv("AZURE_DEPLOYMENT_GPT4", "gpt-4o")
AZURE_DEPLOY_ADA002 = os.getenv("AZURE_DEPLOYMENT_ADA002", "text-embedding-ada-002")
AZURE_DEPLOY_EMBED3_LARGE = os.getenv("AZURE_DEPLOYMENT_EMBED3_LARGE", "text-embedding-3-large")

def azure_available() -> bool:
    return bool(AZURE_ENDPOINT and AZURE_API_KEY)

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

    # Jina v3 (multilingue, 8k)
    EmbeddingConfig("jina-v3",          "jinaai/jina-embeddings-v3",                   1024, True, 8192),

    # Français spécialisés
    EmbeddingConfig("camembert-large",  "dangvantuan/sentence-camembert-large",         1024, False, 512),
    EmbeddingConfig("solon-large",      "OrdalieTech/Solon-embeddings-large-0.1",      1024, False, 512),
    EmbeddingConfig("bilingual-fr-en",  "Lajavaness/bilingual-embedding-large",        1024, True, 512),

    # Azure (si dispo)
    EmbeddingConfig("ada-002",          "azure:ada-002",                               1536, True, 8191),
    EmbeddingConfig("embed-3-large",    "azure:embed-3-large",                         3072, True, 8191),
]

# ============================================================
# Stratégies de chunking
# ============================================================
ChunkingStrategy = Literal["fixed", "recursive", "markdown", "semantic", "regex_custom"]

@dataclass
class ChunkingConfig:
    name: str
    strategy: ChunkingStrategy
    chunk_size: int = 512        # en tokens
    chunk_overlap: int = 64
    extra: dict = field(default_factory=dict)

CHUNKING_CONFIGS: list[ChunkingConfig] = [
    ChunkingConfig("fixed-256-0",       "fixed",        256, 0),
    ChunkingConfig("fixed-512-64",      "fixed",        512, 64),
    ChunkingConfig("fixed-1024-128",    "fixed",       1024, 128),
    ChunkingConfig("recursive-512-64",  "recursive",    512, 64),
    ChunkingConfig("recursive-1024-128","recursive",   1024, 128),
    ChunkingConfig("markdown-1200-50",  "markdown",    1200, 50),  # style ScribBERT
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
