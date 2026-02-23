## PARTIE I — Cadre conceptuel et état de l'art

### Chapitre 1 : De la recherche documentaire à la recherche sémantique
1. **Historique de la recherche d'information (Origine, modele booleen, TF-IDF, BM25, limites du matching lexical, etc.)**
2. **Passage à la recherche sémantique (embeddings avec cbow skip-gram, puis BERT, dense retrieval, sparse vs dense retreival, approche hybride, usage sur doc techniques et reglementaires)**
3. **Problématiques de sémantisation : similarité, contextualisation, ambiguïté, multilingue, vocabulaire spécifique TP**
4. **Limites des approches traditionnelles face aux LLMs : Requetes complexes, pas de compréhension contextuelle profonde, difficulte a extraire des informations implicites, manque dadaptation à des besoins spécifiques**
   
### Chapitre 2 : Les fondements du RAG (Retrieval-Augmented Generation)
1. **Principe général d'une pipeline RAG : Définition et origine du concept (Lewis et al., 2020), rag vs fine-tuning llm, use cases, rag dans l'IA gen, justification du choix pour scribbert**
2. **Architecture : ingestion, chunking, vectorisation, retrieval, génération**
   - **Schéma détaillé de l'architecture mise en place pour Scribbert**
3. **Les avantages du RAG : moins d'hallucinations, contextualisation avec sources traçables, connaissances privées sans exposition publique, actualisation facile sans réentrainement, contrôle des sources, auditabilité des réponses, cout réduit vs fine-tuning**
4. **Les défis du RAG : bruit documentaire, biais, cohérence globale, explicabilité, gestion des contradictions, latence induite, qualité?**

### Chapitre 3 : La question de la « pertinence » et de la « cohérence »
1. **Définir la pertinence (topicalité, exhaustivité, utilité)**
   - **Pertinence topique : adéquation thématique document-requête**
   - **Pertinence situationnelle : utilité pour l'utilisateur et son contexte**
   - **Exhaustivité : couverture complète de la question posée**
   - **Granularité : niveau de détail approprié**
   - **Actualité : fraîcheur de l'information**
   - **Autorité : fiabilité et crédibilité de la source**
   - **Spécificités du domaine HSE : criticité de la précision**
2. **Définir la cohérence (logique interne, fidélité à la source, stabilité)**
   - **Cohérence locale : fluidité entre phrases et paragraphes**
   - **Cohérence globale : structure argumentative logique**
   - **Fidélité factuelle : alignement avec les sources récupérées**
   - **Absence de contradictions internes**
   - **Stabilité : reproductibilité des réponses**
   - **Cohérence terminologique : usage consistant du vocabulaire métier**
   - **Cohérence réglementaire : respect des normes et procédures**
3. **Pertinence perçue vs. mesurée : les deux dimensions de l'évaluation**
   - **Retour d'expérience des utilisateurs de Scribbert**
   - **Méthodes mixtes : triangulation des approches d'évaluation**
4. **Revue des travaux académiques récents sur l'évaluation des RAG et des LLMs augmentés**
   - **Benchmarks existants : BEIR, MTEB, RAGAs**
   - **Métriques de factualité : FactScore, SAFE, TruthfulQA**
   - **Travaux sur l'évaluation de la cohérence : BERTScore, BLEURT**
   - **Évaluation LLM-as-judge : G-Eval, Prometheus**
   - **Frameworks d'évaluation : RAGAS, TruLens, LangSmith**
   - **Gaps identifiés dans la littérature**   
   - **Positionnement de la contribution du mémoire**

## PARTIE II — Méthodologie d'évaluation d'un système RAG

### Chapitre 4 : Modèles et paramètres influençant la performance
1. **Les modèles d'embedding : principes, diversité et évaluation intrinsèque**
   - **Typologie des modèles : BERT, sentence-transformers, OpenAI, Cohere**
   - **Modèles généralistes vs. spécialisés**
   - **Dimension des embeddings, compromis performance/coût**
   - **Multilinguisme : modèles français, multilingues**
   - **Métriques d'évaluation intrinsèque : MTEB, retrieval@k**
   - **Tests comparatifs réalisés pour Scribbert**   
   - **Critères de sélection : performance, coût, latence, confidentialité (open sourcé vs api)**
2. **Le rôle du chunking et du prétraitement textuel**
   - **Stratégies de chunking : fixe, sémantique, récursif, basé sur la structure, custom avec regex...**
   - **Impact taille des chunks, overlap, préservation de la structure documentaire, gestion des métadonnées, nettoyage et normalisation**
   - **Expérimentations menées : comparaison de différentes approches**
3. **Les stratégies de retrieval (cosine similarity, hybrid search, reranking, etc.)**
   - **Similarité cosinus : principe et limitations**
   - **Hybrid search : combinaison sparse + dense retrieval**
   - **Reranking : modèles de cross-encoders**   
   - **Filtrage par métadonnées et contraintes**
   - **Nombre de documents récupérés (top-k) : impact sur qualité et coût**
   - **Query expansion et reformulation**
   - **Implémentation dans Scribbert et choix techniques**
4. **La composante de génération : modèles, prompts, gestion du contexte, intégration des sources, paramètres de génération, guardrails et filtres de sécurité pour le contexte HSE**

### Chapitre 5 : Construction d'un protocole d'évaluation
1. **Les critères d'évaluation (précision, rappel, nDCG, MRR, factualité, cohérence)**
2. **Les approches d'évaluation**
   - **Automatique (métriques vectorielles, lexicales, LLM-based)** :
     - **Métriques hybrides : combinaison de plusieurs approches**
     - **Avantages : scalabilité, reproductibilité, coût réduit**
     - **Inconvénients : corrélation imparfaite avec jugement humain**
   - **Humaine (annotation, grille d'évaluation, perception de la cohérence)** :
     - **Évaluation qualitative : erreurs, biais, cas limites**
     - **Avantages : gold standard, nuances contextuelles**
     - **Inconvénients : coût, subjectivité, non-scalabilité**
3. **Protocole expérimental : jeux de données, corpus, tâches cibles**
4. **Méthodes d'analyse : évaluation comparative, statistiques**

### Chapitre 6 : Évaluation de la cohérence globale
1. **Cohérence locale vs cohérence discursive**
2. **Métriques cohérence** 
3. **Approches hybrides** 
4. **Mesure stabilité/répétabilité** 

## PARTIE III — Application pratique et étude de cas

### Chapitre 7 : Mise en œuvre du système RAG étudié
1. **Description de l'architecture mise en place (pipeline, technologies, choix de design)**
   - **Vue d'ensemble de l'architecture Scribbert**
   - **Stack technologique, choix d'hébergement, architecture de la base vectorielle, pipeline d'ingestion, UI, considérations de sécurité et conformité RGPD, coûts opérationnels et ROI**
2. **Description du corpus (typologie, taille, structure, contraintes)**
3. **Méthodes de chunking et de vectorisation employées**
   - **Stratégies de chunking testées : comparaison détaillée, méthode retenue et justification, taille optimale des chunks identifiée, gestion de l'overlap et des métadonnées**
   - **Prétraitement spécifique**
   - **Modèle d'embedding sélectionné : comparaison et benchmark**
   - **Configuration de l'indexation vectorielle**
4. **Modèles de langage et d'embedding testés**
   - **Critères de comparaison emb** : performance retrieval, latence, coût, langue
   - **Critères de sélection llm** : qualité, coût, latence, confidentialité
   - **Résultats des benchmarks et décision finale**
     
### Chapitre 8 : Expérimentations et résultats
1. **Protocole d'expérimentation, Analyse des résultats selon différents paramètres, Mesures de pertinence, Mesures de cohérence, Analyse qualitative**

### Chapitre 9 : Discussion et perspectives
1. **Interprétation des résultats**
2. **Identification des limites méthodologiques**
3. **Apports du travail à la compréhension des RAG**
4. **Recommandations pour les futures évaluations**
5. **Ouverture vers d'autres applications (domaines réglementaires, techniques, etc.)**

### Conclusion générale
- **Synthèse des résultats et des apports**
- **Limites du travail**
- **Perspectives de recherche**
- **Implications pour l'industrialisation des RAG**