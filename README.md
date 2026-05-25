# Benchmark RAG — ScribBERT

Code Python pour évaluer systématiquement un pipeline RAG selon le protocole
défini dans le mémoire : retrieval, fidélité, pertinence, stabilité, traçabilité.

## Installation

```powershell
# 1. Environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Dépendances
pip install -r requirements.txt

# 3. Configuration Azure (optionnel mais recommandé pour RAGAS et juge)
copy .env.example .env
# puis édite .env avec tes credentials
```

> **GPU** : sur RTX 2080 Ti (11 Go), tous les embeddings du benchmark passent.
> Pour les LLM locaux (Mistral 7B), installer en plus `bitsandbytes` pour la quantization 4-bit.

## Workflow

```
input/*.pdf
   │
   ▼
[01_ingest]      → data/extracted/*.md
   │
   ▼
[02_chunk]       → data/chunks/{strategy}.jsonl
   │
   ▼
[03_benchmark_retrieval]
   │             → results/benchmark_retrieval.csv
   │               (Hit, Recall, Precision, MRR, nDCG @ k)
   │               pour chaque (chunking × embedding × retrieval)
   ▼
[04_benchmark_generation]
   │             → results/benchmark_generation.csv
   │               + results/generation_detail__*.csv
   │               (RAGAS faithfulness/answer_relevancy/context_*
   │                + juge custom : modalité, exceptions, sûreté)
   ▼
[05_benchmark_stability]
                 → results/stability__*.csv
                   (Jaccard@retrieval, BERTScore@answer, paraphrases)
```

## Étapes détaillées

### 0. Préparer le jeu de test

```powershell
python scripts/00_init_test_set.py
# édite data/test_set.json pour ajouter tes questions (objectif : 150–300)
```

Format de chaque question :
```json
{
  "id": "Q001",
  "question": "...",
  "language": "fr",
  "type": "factuelle | procédurale | conditionnelle | comparative | justificative | hors_perimetre",
  "difficulty": "facile | moyen | difficile",
  "criticality": "élevée | moyenne | faible",
  "ground_truth_answer": "...",
  "relevant_doc_ids": ["nom_pdf_sans_ext", ...],
  "relevant_chunk_ids": [],
  "paraphrases": ["...", "..."],
  "notes": "..."
}
```

### 1. Placer les PDFs

```powershell
copy *.pdf .\input\
python scripts/01_ingest.py
```

### 2. Générer tous les jeux de chunks

```powershell
python scripts/02_chunk.py
```

Stratégies par défaut (`src/config.py:CHUNKING_CONFIGS`) :
- `fixed-256-0`, `fixed-512-64`, `fixed-1024-128` (tailles fixes)
- `recursive-512-64`, `recursive-1024-128` (LangChain recursive)
- `markdown-1200-50` (structural, style ScribBERT)
- `regex-paragraph` (custom)
- `semantic-mpnet` (rupture sémantique, coûteux)

### 3. Benchmark retrieval

```powershell
# Tout (long : N chunkings × N embeddings × N retrievals)
python scripts/03_benchmark_retrieval.py

# Subset rapide pour tester
python scripts/03_benchmark_retrieval.py `
  --chunkings markdown-1200-50 `
  --embeddings minilm-l6 e5-base-ml bge-m3 `
  --retrievals dense-k5 hybrid-k5
```

Modèles d'embedding benchmarkés (`src/config.py:EMBEDDING_MODELS`) :
| Nom | Modèle | Dim | Langue |
|---|---|---|---|
| `minilm-l6` | all-MiniLM-L6-v2 | 384 | EN |
| `mpnet-base` | all-mpnet-base-v2 | 768 | EN |
| `e5-small-ml` | multilingual-e5-small | 384 | 100+ |
| `e5-base-ml` | multilingual-e5-base | 768 | 100+ |
| `e5-large-ml` | multilingual-e5-large | 1024 | 100+ |
| `bge-m3` | BAAI/bge-m3 | 1024 | 100+ |
| `jina-v3` | jina-embeddings-v3 | 1024 | 100+ |
| `camembert-large` | sentence-camembert-large | 1024 | FR |
| `solon-large` | Solon-embeddings-large | 1024 | FR |
| `bilingual-fr-en` | bilingual-embedding-large | 1024 | FR/EN |
| `ada-002` | text-embedding-ada-002 | 1536 | 100+ (Azure) |
| `embed-3-large` | text-embedding-3-large | 3072 | 100+ (Azure) |

### 4. Benchmark génération (RAGAS + juge custom)

```powershell
python scripts/04_benchmark_generation.py
```

Édite la liste `selected` dans `scripts/04_benchmark_generation.py` pour choisir
les configurations à évaluer (typiquement les meilleures de l'étape 3).

Métriques :
- **RAGAS** : `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`
- **Juge custom santé-sécurité** : `preservation_modalites`, `completude_exceptions`, `surete_operationnelle`

### 5. Benchmark stabilité

```powershell
python scripts/05_benchmark_stability.py
```

Métriques :
- `ret_jaccard_mean` : stabilité retrieval inter-runs
- `cit_jaccard_mean` : stabilité des citations
- `ans_bertscore_f1_mean` : similarité sémantique inter-runs des réponses
- `paraphrase_bertscore_f1` : robustesse aux paraphrases

## Personnalisation

Tout est dans [src/config.py](src/config.py) :
- `EMBEDDING_MODELS` : ajouter/retirer des modèles HuggingFace
- `CHUNKING_CONFIGS` : nouvelles stratégies / paramètres
- `RETRIEVAL_CONFIGS` : top-k, seuil, hybridation, reranking
- `GENERATION_CONFIGS` : Azure ou modèles HF locaux
- `SYSTEM_PROMPT` : prompt système ScribBERT

## Structure du projet

```
.
├── input/                 # PDFs à indexer (ignorés par git)
├── data/
│   ├── extracted/         # PDFs convertis en .md + meta.json
│   ├── chunks/            # 1 fichier .jsonl par stratégie
│   ├── indexes/chroma/    # bases vectorielles ChromaDB
│   └── test_set.json      # questions de référence
├── results/               # CSV de résultats par étape
├── src/
│   ├── config.py
│   ├── ingestion.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── retrieval.py
│   ├── generation.py
│   ├── benchmark.py
│   └── evaluation/
│       ├── retrieval_metrics.py
│       ├── generation_metrics.py    # RAGAS + juge custom
│       └── stability_metrics.py
└── scripts/
    ├── 00_init_test_set.py
    ├── 01_ingest.py
    ├── 02_chunk.py
    ├── 03_benchmark_retrieval.py
    ├── 04_benchmark_generation.py
    └── 05_benchmark_stability.py
```

## Notes pratiques

- **Coût Azure** : RAGAS appelle le LLM-judge plusieurs fois par sample. Sur 150
  questions et 3 configurations, prévoir ~2000 appels. Utilise GPT-3.5-turbo pour
  le juge ou limite le nombre de configs en génération.
- **Cache embeddings** : les index ChromaDB sont persistés. Une fois construit,
  un (chunking, embedding) n'est pas recalculé.
- **VRAM** : si saturation sur 2080 Ti avec `bge-m3` ou `embed-3-large`, réduire
  `batch_size` dans `src/retrieval.py:build_dense_index`.
- **GB10** : la machine ARM avec 256 Go peut faire tourner Mistral 7B (voire
  Llama 3.1 8B) sans quantization ; édite `GENERATION_CONFIGS`.
