# NOTE DE CADRAGE – MÉMOIRE DE FIN D'ÉTUDES

---

**Titre du projet :**  
Évaluation de la pertinence, de la cohérence et de la fiabilité d'un système RAG (Retrieval-Augmented Generation) : Application à ScribBERT, chatbot dédié aux référentiels HSE de Bouygues Travaux Publics

**Nom / Prénom étudiant :**  
[À compléter]

**Tuteur entreprise :**  
[À compléter]

**Tuteur école :**  
[À compléter]

---

## 1. Contexte et problématique

### Contexte de l'entreprise et environnement

Bouygues Travaux Publics est l'un des leaders mondiaux du secteur de la construction et des travaux publics, intervenant sur des projets d'infrastructure de grande envergure. Dans ce contexte, le département P2S (Prévention Santé-Sécurité) joue un rôle crucial pour garantir la sécurité des collaborateurs sur les chantiers. L'entreprise dispose de référentiels internes volumineux (normes, procédures, guides techniques) qui constituent une base documentaire essentielle mais difficile à exploiter efficacement. L'accès rapide et fiable à ces informations est un enjeu majeur, tant pour l'efficacité opérationnelle que pour la sécurité des équipes. C'est dans ce cadre qu'a été développé ScribBERT, un chatbot basé sur une architecture RAG (Retrieval-Augmented Generation), visant à faciliter l'accès contextualisé et précis aux connaissances internes.
Dans le domaine santé-sécurité, la qualité de l'information transmise engage directement la sécurité des collaborateurs. Chaque réponse doit être exacte, cohérente et fondée sur les bonnes sources. L'entreprise doit donc s'assurer que le système RAG déployé répond à des standards élevés de fiabilité et de traçabilité. Les modèles de langage (LLMs) présentent des limites notables : hallucinations, manque de traçabilité des sources et difficulté à actualiser leurs connaissances. Le RAG émerge comme solution hybride combinant recherche documentaire et génération linguistique. Toutefois, la question de l'évaluation rigoureuse de ces systèmes reste ouverte et constitue un défi académique majeur.
La question centrale autour de laquelle va s'articuler le mémoire peut donc se formuler ainsi : Comment évaluer la pertinence, la cohérence et la fiabilité d'un système RAG dans un contexte professionnel critique ? Autrement dit, comment garantir qu'un système complexe récupère les bons documents et produise des réponses fidèles aux sources, tout en assurant une cohérence globale et une stabilité des réponses ?
Les travaux récents sur l'évaluation des RAG (benchmarks BEIR, MTEB, frameworks RAGAS, TruLens) proposent des métriques variées mais rarement adaptées aux contextes métier spécifiques. Ce mémoire s'inscrit dans la continuité de ces recherches en proposant un cadre d'évaluation complet, rigoureux et reproductible, appliqué à un cas d'usage réel dans le domaine HSE. Il vise à combler les gaps identifiés dans la littérature en articulant évaluation automatique et humaine, et en prenant en compte les spécificités du domaine technique et réglementaire.

---

## 2. Objectifs du mémoire

### Objectifs professionnels (pour l'entreprise)

- Valider la fiabilité et la pertinence de ScribBERT avant son déploiement à grande échelle
- Identifier les paramètres optimaux de configuration du système RAG (modèles d'embedding, stratégies de chunking, retrieval, génération)
- Proposer des recommandations concrètes pour améliorer la qualité des réponses et la traçabilité des sources
- Établir un cadre d'évaluation réutilisable pour d'autres applications RAG au sein de Bouygues

### Objectifs académiques (analyse, recherche, contribution)

- Formaliser des critères d'évaluation pertinents pour les systèmes RAG dans des contextes métier critiques
- Explorer et comparer différentes métriques d'évaluation (automatiques, humaines, hybrides)
- Étudier l'impact des paramètres clés de la pipeline RAG (chunking, embedding, retrieval, génération) sur la performance globale
- Contribuer à l'état de l'art en proposant une méthodologie d'évaluation reproductible et généralisable à d'autres domaines d'application

---

## 3. Méthodologie envisagée

### Démarche prévue

1. **Revue de littérature approfondie :** État de l'art sur le RAG, la recherche sémantique, les métriques d'évaluation des LLMs et des systèmes de recherche d'information
2. **Benchmark des modèles et paramètres :** Tests comparatifs de modèles d'embedding, stratégies de chunking, méthodes de retrieval (cosine similarity, hybrid search, reranking)
3. **Construction du protocole d'évaluation :** Définition de critères, sélection de métriques (précision, rappel, nDCG, MRR, factualité, cohérence), élaboration de grilles d'évaluation humaine
4. **Expérimentation sur ScribBERT :** Application du protocole sur un corpus de documents HSE, analyse quantitative et qualitative des résultats
5. **Analyse statistique et interprétation :** Identification des configurations optimales, analyse des limites, formulation de recommandations

### Données / outils utilisés

- **Corpus :** Référentiels internes Bouygues TP (guides HSE, procédures, normes techniques)
- **Modèles d'embedding testés :** BERT, sentence-transformers, modèles OpenAI/Cohere, modèles spécialisés français
- **Modèles de langage :** LLMs open source et propriétaires
- **Outils d'évaluation :** Frameworks RAGAS, TruLens, métriques custom
- **Technologies :** Base vectorielle, pipeline d'ingestion, interface utilisateur, infrastructure cloud
- **Méthodologie d'évaluation :** Approches automatiques (métriques vectorielles, lexicales, LLM-based) et humaines (annotation, grilles qualitatives)

---

## 4. Hypothèses de travail et résultats attendus

### Pistes de réflexion

- Les stratégies de chunking adaptées au contexte documentaire (préservation de la structure, métadonnées) améliorent significativement la pertinence du retrieval
- Les approches hybrides (sparse + dense retrieval, reranking) surpassent les méthodes simples de similarité cosinus
- Les modèles d'embedding spécialisés ou multilingues sont plus performants que les modèles généralistes pour des corpus techniques en français
- La fidélité factuelle des réponses générées peut être mesurée de manière fiable par des approches LLM-as-judge combinées à l'évaluation humaine
- La stabilité et la reproductibilité des réponses constituent des indicateurs clés de la fiabilité du système

### Livrables attendus

1. **Cadre méthodologique formalisé :** Protocole d'évaluation complet, réutilisable et documenté
2. **Benchmark détaillé :** Comparaison des configurations testées avec recommandations chiffrées
3. **Rapport d'évaluation de ScribBERT :** Analyse quantitative et qualitative, identification des points forts et axes d'amélioration
4. **Recommandations stratégiques :** Guide de bonnes pratiques pour l'évaluation et l'optimisation de systèmes RAG
5. **Mémoire académique :** Contribution théorique et empirique à l'état de l'art sur l'évaluation des RAG

---

## 5. Plan prévisionnel

Le calendrier s'inscrit dans les attendus de l'école et suit la structure suivante :

### PARTIE I — Cadre conceptuel et état de l'art (Mois 1-2)
- **Chapitre 1 :** De la recherche documentaire à la recherche sémantique
- **Chapitre 2 :** Les fondements du RAG
- **Chapitre 3 :** La question de la pertinence et de la cohérence

### PARTIE II — Méthodologie d'évaluation d'un système RAG (Mois 3-4)
- **Chapitre 4 :** Modèles et paramètres influençant la performance
- **Chapitre 5 :** Construction d'un protocole d'évaluation
- **Chapitre 6 :** Évaluation de la cohérence globale

### PARTIE III — Application pratique et étude de cas (Mois 4-6)
- **Chapitre 7 :** Mise en œuvre du système RAG étudié (ScribBERT)
- **Chapitre 8 :** Expérimentations et résultats
- **Chapitre 9 :** Discussion et perspectives

### Jalons clés
- **Fin Mois 2 :** Revue de littérature achevée, cadre théorique validé
- **Fin Mois 4 :** Protocole d'évaluation finalisé, début des expérimentations
- **Fin Mois 5 :** Expérimentations terminées, analyse des résultats
- **Fin Mois 6 :** Rédaction finale, soutenance

---

## 6. Moyens et contraintes

### Accès aux données
- Accès aux référentiels internes HSE de Bouygues TP (corpus documentaire complet)
- Accès à l'infrastructure technique de ScribBERT (base vectorielle, logs, métriques d'usage)
- Retours d'expérience des utilisateurs de ScribBERT

### Confidentialité
- Données sensibles et propriétaires : nécessité d'anonymisation pour certaines illustrations
- Respect du RGPD et des politiques de sécurité de l'information de Bouygues
- Potentiellement, non-divulgation de certains choix techniques spécifiques

### Outils
- Infrastructure cloud pour hébergement et tests
- Licences de modèles propriétaires (OpenAI, Cohere, etc.) si nécessaire
- Frameworks open source (LangChain, RAGAS, TruLens)
- Environnement de développement et d'expérimentation

### Disponibilité tuteurs
- Points réguliers avec le tuteur entreprise (hebdomadaire ou bimensuel)
- Échanges avec le tuteur école selon le calendrier académique
- Support technique de l'équipe P2S et de l'équipe IT de Bouygues

### Contraintes opérationnelles
- Alternance entre missions opérationnelles et travail de recherche
- Délais d'expérimentation conditionnés par l'accès aux ressources de calcul
- Nécessité de validation interne avant publication de résultats sensibles

---

## 7. Signatures

**Étudiant :**  
Date : ____________________  
Signature :

**Tuteur entreprise :**  
Date : ____________________  
Signature :

**Tuteur école :**  
Date : ____________________  
Signature :