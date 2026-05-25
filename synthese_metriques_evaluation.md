# Synthèse des métriques à évaluer — ScribBERT

## 1. Métriques de Retrieval (Dimension 1)

| Métrique | Définition | Paramètres à tester | Jeu de test |
|----------|-----------|---------------------|-------------|
| **Recall@k** | Proportion des passages pertinents retrouvés parmi les k résultats | k ∈ {5, 10} | ~20 questions (objectif : 150–300) avec passages de référence annotés |
| **MRR** | Rang inverse moyen du 1er passage pertinent | — | Idem |
| **nDCG@k** | Classement pondéré avec pertinence graduée | k ∈ {5, 10} | Idem (nécessite jugements gradués 0/1/2/3) |
| **Hit@k** | Au moins 1 passage pertinent dans le top-k (binaire) | k ∈ {5, 10} | Idem |
| **Precision@k** | Proportion de passages pertinents parmi les k retournés | k ∈ {5, 10} | Idem |

**Sur quoi ?** Les 48 configurations (12 modèles d'embedding × 4 combinaisons de paramètres).

**Paramètres variés (OFAT) :**
- Modèle d'embedding (12 modèles : Solon, sentence-CamemBERT, E5, BGE-M3, Jina, OpenAI text-embedding-3, Cohere, etc.)
- Taille de chunk : T ∈ {256, 512, 1024} tokens
- Overlap : O ∈ {0, 64, 128} tokens
- Top-k : k ∈ {3, 5, 10}
- Seuil de filtrage par score de similarité
- Type de retrieval : dense pur vs hybride (BM25+dense)
- Reranking : absent vs cross-encoder (ex. bge-reranker-v2-m3)

**Stratification de l'analyse :**
- Par type de question (factuelle, procédurale, conditionnelle, comparative, justificative, hors-périmètre)
- Par langue (FR vs EN vs cross-lingue)
- Par difficulté (facile / moyen / difficile)
- Par criticité métier (élevée / moyenne / faible)

---

## 2. Métriques de Fidélité / Faithfulness (Dimension 2)

| Métrique | Définition | Méthode |
|----------|-----------|---------|
| **Faithfulness (RAGAS)** | % de propositions atomiques de la réponse supportées par le contexte | LLM-juge (différent du générateur) |
| **NLI-based scoring** | Chaque phrase vérifiée par inférence textuelle vs contexte | Modèle NLI |
| **Citation faithfulness** | Le passage cité supporte-t-il réellement l'affirmation ? | LLM-juge |
| **Hallucination rate** | 1 − faithfulness | Dérivé |
| **Préservation des modalités** | "doit" vs "peut" vs "recommandé" conservé correctement | Vérification humaine ou LLM-juge avec instructions précises |

**Sur quoi ?** Configuration(s) retenue(s) après le benchmark retrieval. Rapporter médiane + IQR.

---

## 3. Métriques de Pertinence / Complétude de la réponse (Dimension 3)

| Métrique | Définition | Méthode |
|----------|-----------|---------|
| **Answer relevance (RAGAS)** | La réponse traite-t-elle bien la question posée ? | LLM-juge génère des questions hypothétiques, mesure similarité avec la question originale |
| **Complétude** | Proportion des éléments attendus (étapes, conditions, exceptions) présents | Comparaison à une réponse de référence annotée par expert |
| **Concision** | Réponse proportionnée à la complexité | Jugement humain ou ratio longueur/contenu |
| **Respect du format** | Check-list, numérotation, structure demandée respectée | Vérification automatique ou humaine |

---

## 4. Métriques de Stabilité / Répétabilité (Dimension 4)

| Métrique | Définition | Protocole |
|----------|-----------|-----------|
| **Stability@retrieval** | Jaccard moyen des ensembles de chunks entre paires de runs | n = 10 runs par question, seed fixe |
| **Stability@citations** | Jaccard moyen des chunks cités dans la réponse | Idem |
| **Stability@answer** | BERTScore moyen entre paires de réponses | Idem |
| **Flip rate** | % de questions où le verdict correct/incorrect change entre runs | Idem |
| **Robustesse aux paraphrases** | Consistance sémantique entre réponses à m = 5 paraphrases | LLM-juge évalue si même information factuelle |
| **Robustesse à l'ordre des passages** | Variation de réponse quand on permute l'ordre du contexte | Permutations du top-k |
| **Self-consistency** | Taux d'accord entre n réponses (température > 0) | n = 10–20 générations |

**Sous-jeu :** 30–60 questions critiques stratifiées par criticité.

**Tests adversariaux (stress-test) :**
- Fautes injectées (substitutions, omissions, accents)
- Reformulations adversariales (jargon chantier, anglicismes)
- Bruit dans le contexte (chunks non pertinents ajoutés)
- Contradictions injectées dans le corpus
- Questions pièges / hors-périmètre / présupposés faux

---

## 5. Métriques de Traçabilité / Auditabilité (Dimension 5)

| Métrique | Définition | Méthode |
|----------|-----------|---------|
| **Citation correctness** | Les passages cités existent, sont pertinents, et supportent l'affirmation | Vérification automatique + humaine |
| **Citation completeness** | Toutes les affirmations sourcées sont-elles effectivement citées ? | LLM-juge ou humain |
| **Diversité des sources** | La réponse s'appuie-t-elle sur plusieurs documents quand pertinent ? | Comptage automatique |

---

## 6. Coût opérationnel

| Métrique | Détail |
|----------|--------|
| **Latence P50 / P95** | Par étape : embedding requête, recherche ChromaDB, appel LLM, total |
| **Coût par requête (€)** | Selon le LLM retenu (tokens consommés) |
| **Taux de refus** | % de requêtes où le système répond "information non trouvée" |

---

## 7. Évaluation humaine — Grille d'annotation

| Critère | Échelle | Définition |
|---------|---------|------------|
| Pertinence | 0–3 | 0 = hors-sujet, 3 = répond exactement |
| Fidélité aux sources | 0–3 | 0 = invente, 3 = parfaitement supporté |
| Complétude | 0–3 | 0 = manquements importants, 3 = couvre exceptions |
| Modalité (santé-sécurité) | 0–2 | 0 = inversion obligation/recommandation, 2 = conservée |
| Sûreté opérationnelle | 0–3 | 0 = induirait un comportement dangereux, 3 = aligné |
| Citations | 0–2 | 0 = aucune/erronée, 2 = chaque affirmation citée |

**Conditions :** 2–3 annotateurs par item, annotation à l'aveugle, accord inter-annotateurs (Kappa de Cohen), profil mixte (experts métier + utilisateurs cibles).

---

## 8. Analyse croisée (end-to-end)

| Analyse | Objectif |
|---------|----------|
| Corrélation Recall@k ↔ Faithfulness | Un retrieval plus large dégrade-t-il la fidélité ? |
| Localisation des erreurs (retrieval vs génération) | Utiliser la typologie d'erreurs (8 catégories) |
| Courbe seuil de filtrage vs taux de refus / taux d'erreur | Trouver le point d'équilibre |
| Métriques par strate | Vérifier qu'aucune sous-population ne se dégrade |

---

## 9. Résumé du plan expérimental

| Étape | Quoi | Combien |
|-------|------|---------|
| Benchmark retrieval | 12 embeddings × 4 configs = 48 configurations | ~20 questions (étendre à 150+) |
| Évaluation génération | Configuration(s) retenue(s) | Faithfulness, answer relevance, complétude |
| Stabilité inter-runs | 30–60 questions × 10 runs | Jaccard, BERTScore, flip rate |
| Stabilité paraphrases | 30–60 questions × 5 paraphrases | Consistance sémantique |
| Tests adversariaux | 10–20 questions | Stress-test des garde-fous |
| Évaluation humaine | Sous-échantillon 10–30 questions critiques | Grille 6 critères, 2–3 annotateurs |
| Coût opérationnel | Toutes configurations | Latence, €/requête, taux de refus |

**Méthode statistique :** Test de Wilcoxon apparié, taille d'effet (Cohen's d), correction Bonferroni si comparaisons multiples. Rapporter médiane + IQR, pas seulement la moyenne.

help

memoire/
├── input/                    # tes PDFs ici
├── data/                     # extraits, chunks, indexes, test_set.json
├── results/                  # CSV de résultats
├── src/
│   ├── config.py             # 🎛 modèles, chunkings, retrievals, prompt
│   ├── ingestion.py          # PDF → markdown (pymupdf)
│   ├── chunking.py           # 5 stratégies (fixed, recursive, markdown, regex, semantic)
│   ├── embeddings.py         # 12 modèles HF + Azure ada-002 / embed-3-large
│   ├── retrieval.py          # dense (ChromaDB), BM25, hybride, reranking, neighbors
│   ├── generation.py         # Azure GPT-3.5/4 ou HF local (Mistral 7B 4-bit)
│   ├── benchmark.py          # orchestrateur
│   └── evaluation/
│       ├── retrieval_metrics.py    # Hit/Recall/Precision/MRR/nDCG @ k
│       ├── generation_metrics.py   # RAGAS + juge custom modalité santé-sécurité
│       └── stability_metrics.py    # Jaccard, BERTScore, paraphrases
├── scripts/
│   ├── 00_init_test_set.py   # template test set avec 8 questions exemples
│   ├── 01_ingest.py
│   ├── 02_chunk.py
│   ├── 03_benchmark_retrieval.py
│   ├── 04_benchmark_generation.py
│   └── 05_benchmark_stability.py
├── .env.example  /  .gitignore  /  requirements.txt  /  README.md

python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env       # remplis tes credentials Azure

python scripts/00_init_test_set.py    # crée data/test_set.json (à éditer)
copy *.pdf .\input\
python scripts/01_ingest.py            # PDF -> markdown
python scripts/02_chunk.py             # 8 jeux de chunks
python scripts/03_benchmark_retrieval.py   # 8 chunkings × 12 embeddings × 6 retrievals
python scripts/04_benchmark_generation.py  # RAGAS + juge santé-sécurité
python scripts/05_benchmark_stability.py   # 5 runs + paraphrases

Points d'attention
relevant_doc_ids dans test_set.json : utilise les noms de PDF sans extension. Si tu annotes au niveau document seulement, l'évaluation tombe automatiquement sur level="doc".
Premier 02_chunk : semantic-mpnet télécharge un modèle (~400 Mo). Tu peux le commenter dans CHUNKING_CONFIGS si tu veux tester vite.