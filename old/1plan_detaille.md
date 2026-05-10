## Note de cadrage du plan (révisée — v2)

**Définition opératoire de la « fiabilité »** (terme central du titre) :
> *Fiabilité = pertinence du retrieval + fidélité aux sources (factualité) + stabilité/répétabilité de la réponse + traçabilité auditable.*
Cette définition structure les critères d'évaluation des Ch. 5 et 6.

**Principes anti-redondance** :
- **Ch. 2** (architecture RAG type, générique) ≠ **Ch. 7** (architecture ScribBERT, choix concrets et justifications uniquement).
- **Ch. 4** (catalogue théorique des leviers et compromis) ≠ **Ch. 7.3-7.4** (uniquement la configuration retenue + justification adossée à Ch. 4).
- **Ch. 5** (métriques + protocole) ≠ **Ch. 6** (recentré sur stabilité / répétabilité, dimension peu traitée dans Ch. 5).

---

## Volet liminaire — Présentation du contexte
- **Le groupe Bouygues, branche Construction**
- **Bouygues Travaux Publics : périmètre, projets emblématiques, organisation**
- **Le département P2S (Prévention Santé-Sécurité) : missions, enjeux documentaires**
- **Le projet ScribBERT : objectifs, principes directeurs, périmètre d'alternance**
- **Implications pour la problématique du mémoire**

## PARTIE I — Cadre conceptuel et état de l'art

### Chapitre 1 : De la recherche documentaire à la recherche sémantique
1. **Historique de la recherche d'information** (modèle booléen, TF-IDF, BM25, limites du matching lexical, évaluation Cranfield/TREC, learning-to-rank)
2. **Passage à la recherche sémantique** (LSA, Word2Vec CBOW/Skip-gram, BERT, sentence embeddings, dense retrieval, sparse vs dense vs hybride, ANN/HNSW)
3. **Problématiques de sémantisation** : similarité, contextualisation, ambiguïté, multilinguisme, vocabulaire technique HSE
4. **Limites des approches traditionnelles face aux LLMs** : requêtes complexes, intentions, raisonnement implicite

### Chapitre 2 : Les fondements du RAG (Retrieval-Augmented Generation)
1. **Principe général** : DrQA → ORQA → REALM → RAG (Lewis 2020) → FiD ; RAG vs fine-tuning ; mémoire paramétrique vs non-paramétrique
2. **Architecture type d'une pipeline RAG** (générique uniquement — l'instanciation ScribBERT est en Ch. 7)
3. **Avantages du RAG** : moins d'hallucinations, traçabilité, connaissances privées, actualisation, auditabilité
4. **Défis du RAG** : bruit, contradictions, dépendance au chunking, latence, cohérence ; multi-stage retrieval + reranking ; importance de la « source »

### Chapitre 3 : Pertinence, cohérence, fiabilité
1. **Définir la pertinence** (multi-dimensionnelle : topique, situationnelle, exhaustivité, granularité, actualité, autorité, interactive)
2. **Définir la cohérence** (textuelle, factualité, fidélité aux sources, terminologique, réglementaire)
3. **Définir la fiabilité** (synthèse opératoire pour ce mémoire — voir note de cadrage)
4. **Pertinence perçue vs mesurée** : triangulation des approches
5. **Travaux récents sur l'évaluation des RAG** : BEIR, MTEB, BERTScore/BLEURT, TruthfulQA, FactScore, RAGAS, TruLens, LLM-as-judge ; gaps en domaines critiques ; positionnement de la contribution

## PARTIE II — Méthodologie d'évaluation d'un système RAG

### Chapitre 4 : Catalogue des leviers techniques (vue théorique)
> **NB** : ce chapitre décrit les options *disponibles* et leurs compromis. Les *choix retenus* pour ScribBERT figurent en Ch. 7.

1. **Modèles d'embedding** : typologie, dimensions, multilinguisme, MTEB/BEIR, intrinsèque vs extrinsèque, grille de critères industriels
2. **Chunking et prétraitement** : stratégies (fixe, récursif, structurel, sémantique, custom), taille/overlap, métadonnées, nettoyage, cas des PDF techniques
3. **Stratégies de retrieval** : cosinus, hybride sparse+dense (combinaison de scores, RRF), reranking cross-encoder, filtrage métadonnées, top-k, query expansion (HyDE, multi-query, step-back)
4. **Composante de génération** : choix LLM (propriétaire vs open-weights), prompt engineering, fenêtre de contexte, paramètres de décodage, citations, guardrails HSE
5. **Synthèse : matrice leviers × métriques affectées**

### Chapitre 5 : Protocole d'évaluation
1. **Critères d'évaluation organisés par dimension de la fiabilité**
   - Retrieval : Recall@k, Precision@k, MRR, nDCG, Hit@k
   - Génération – fidélité : faithfulness, context support, attribution
   - Génération – pertinence réponse : answer relevance, completeness
   - End-to-end : utilité, refus contrôlé, citations correctes
2. **Approches d'évaluation** : automatique (lexical, vectoriel, LLM-based), humaine (grille standardisée), comparaison
3. **Construction du jeu de test** : sources, types de questions (factuelles, procédurales, comparatives, conditionnelles, hors-périmètre), niveaux de difficulté, annotation des passages-or, prévention de la contamination, versioning
4. **Conditions expérimentales et reproductibilité** : isolation des facteurs (OFAT vs factoriel), seeding, gel des modèles/index, logging
5. **Méthodes d'analyse** : tests statistiques de significativité, analyse d'erreurs typologique, études de cas

### Chapitre 6 : Évaluation de la stabilité et de la répétabilité
> **Recentrage** : ce chapitre traite spécifiquement de la *stabilité*, dimension de la fiabilité peu couverte par les métriques classiques de Ch. 5.

1. **Pourquoi la stabilité est une dimension distincte de la fiabilité**
2. **Sources de variance dans un RAG** : décodage stochastique, ANN approximatif, ordre des passages, sensibilité au prompt, dérive du corpus
3. **Métriques de stabilité** : self-consistency, accord inter-runs (Jaccard sur citations, similarité BERTScore inter-réponses), variance des scores, taux de retournement (*flip rate*)
4. **Sensibilité à la formulation** : robustesse aux paraphrases de requête, aux fautes, à l'ordre des chunks
5. **Protocole de test de stabilité** : N runs, seeds variés, paraphrases automatiques, *adversarial probing*

## PARTIE III — Application pratique et étude de cas

### Chapitre 7 : Mise en œuvre du système RAG ScribBERT
> **NB** : ne reprend pas les généralités de Ch. 2/4 ; documente uniquement les choix faits et leur justification (renvoi à Ch. 4 pour la théorie).

1. **Architecture déployée** : stack technique, hébergement, base vectorielle, pipeline d'ingestion, UI, sécurité/RGPD
2. **Corpus** : typologie, taille, structure, contraintes (langue, formats, qualité)
3. **Choix de chunking et prétraitement** : stratégie retenue + justification (renvoi Ch. 4.2)
4. **Choix d'embedding et de LLM** : modèles testés, modèles retenus + justification (renvoi Ch. 4.1 et 4.4)
5. **Configuration retrieval/reranking/prompt** : valeurs retenues + justification (renvoi Ch. 4.3 et 4.4)

### Chapitre 8a : Résultats quantitatifs
1. **Protocole expérimental instancié** (jeu de test interne, conditions)
2. **Résultats retrieval** : Recall@k, MRR, nDCG selon embedding / chunking / hybridation / reranking
3. **Résultats génération** : faithfulness, answer relevance, citations
4. **Résultats stabilité** (Ch. 6 appliqué) : variance inter-runs, robustesse aux paraphrases
5. **Résultats end-to-end** et analyse du couplage retrieval ↔ génération

### Chapitre 8b : Analyse qualitative et étude d'erreurs
1. **Typologie des erreurs observées** (retrieval miss, hallucination, omission d'exception, contradiction non détectée, refus à tort)
2. **Études de cas commentées** (5–10 exemples représentatifs)
3. **Cas limites et ambiguïtés** (acronymes, multi-versions, hors-périmètre)
4. **Biais identifiés** dans le système et le corpus

### Chapitre 9 : Enjeux éthiques, réglementaires et industriels
> **Nouveau chapitre** : auparavant noyé dans la discussion ; mérite un traitement dédié.

1. **AI Act européen** : classification du système, obligations applicables (transparence, supervision humaine, gestion des risques), implications pour ScribBERT
2. **RGPD et données internes** : statut des documents, traces utilisateur, droit à l'explication
3. **Responsabilité en contexte HSE** : qui est responsable d'une réponse erronée ? rôle du disclaimer, rôle de la supervision humaine
4. **Gouvernance d'un RAG d'entreprise** : versioning des modèles et corpus, processus de validation des changements, audit trail
5. **Acceptabilité et conduite du changement** : adoption par les utilisateurs terrain, formation, signal de confiance

### Chapitre 10 : Discussion et perspectives
1. **Interprétation des résultats** et synthèse des enseignements
2. **Limites méthodologiques** (corpus, métriques, protocole)
3. **Apports à la compréhension des RAG** (théoriques et méthodologiques)
4. **Recommandations** pour évaluer les RAG en contexte critique
5. **Perspectives** : multimodalité, agentic RAG, GraphRAG, fine-tuning d'embedding sur domaine HSE, généralisation à d'autres domaines réglementaires

### Conclusion générale
- **Synthèse des résultats et des apports**
- **Limites du travail**
- **Perspectives de recherche**
- **Implications pour l'industrialisation des RAG en contexte critique**
