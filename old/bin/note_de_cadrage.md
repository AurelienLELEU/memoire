# Note de cadrage – Mémoire de fin d'études

**Étudiant** : A. LELEU  
**Entreprise d'accueil** : Bouygues Travaux Publics – Département P2S (Prévention Santé-Sécurité)  
**Directeur de cursus** : [Nom du directeur]  
**Date** : 3 novembre 2025

---

## 1. Contexte général du projet

Dans le cadre de mon alternance au sein du département P2S de Bouygues Travaux Publics, j'ai participé au développement de **ScribBERT**, un chatbot basé sur une architecture RAG (Retrieval-Augmented Generation) destiné à faciliter l'accès aux référentiels internes de santé-sécurité de l'entreprise.

Les modèles de langage de grande taille (LLMs) ont révolutionné la manière dont l'information est produite et exploitée, mais présentent des limites critiques : hallucinations, absence de traçabilité des sources, et difficultés d'actualisation des connaissances. Pour pallier ces défauts, l'approche RAG combine recherche documentaire sémantique et génération de texte contextualisée, permettant de produire des réponses ancrées dans des sources vérifiables.

Dans un contexte santé-sécurité où l'exactitude de l'information engage directement la sécurité des collaborateurs sur les chantiers, **l'évaluation rigoureuse de la fiabilité du système devient un enjeu majeur**.

---

## 2. Problématique de recherche

**Question centrale** :  
**« Comment évaluer la pertinence, la cohérence et la fiabilité d'un système RAG ? »**

Cette problématique se décline en plusieurs sous-questions :
- Comment garantir qu'un système RAG récupère les bons documents (pertinence du retrieval) ?
- Comment s'assurer que les réponses générées sont fidèles aux sources et exemptes de contradictions (cohérence et factualité) ?
- Quelles métriques permettent d'évaluer de manière reproductible et objective la qualité d'un système RAG ?
- Comment adapter ces métriques à un domaine spécialisé (santé-sécurité) avec un vocabulaire technique spécifique ?

---

## 3. Objectifs du mémoire

### Objectif principal
Proposer **une méthodologie d'évaluation complète, rigoureuse et reproductible** pour mesurer la pertinence, la cohérence et la fiabilité d'un système RAG.

### Objectifs secondaires
1. **Identifier et formaliser** des critères d'évaluation pertinents pour les systèmes RAG
2. **Explorer et comparer** différentes métriques d'évaluation (automatiques, humaines, hybrides)
3. **Étudier l'impact** des paramètres clés de la pipeline RAG (modèles d'embedding, stratégies de chunking, méthodes de retrieval, choix du LLM)
4. **Mettre en œuvre et tester** ce protocole sur un cas d'usage concret : ScribBERT
5. **Formuler des recommandations** généralisables à d'autres contextes documentaires et domaines d'application

---

## 4. Méthodologie envisagée

Le mémoire s'articule autour de **trois grandes parties** :

### Partie I – Cadre conceptuel et état de l'art
- Historique et évolution de la recherche documentaire vers la recherche sémantique
- Présentation des fondements théoriques et architecturaux du RAG
- Définition des notions de pertinence, cohérence et fiabilité
- Revue de la littérature académique récente sur l'évaluation des systèmes RAG

### Partie II – Méthodologie d'évaluation
- Analyse des modèles et paramètres influençant la performance (embedding, chunking, retrieval, génération)
- Construction d'un protocole d'évaluation : critères, métriques (automatiques et humaines), jeux de données
- Évaluation de la cohérence globale : métriques spécifiques et approches hybrides

### Partie III – Application pratique et étude de cas
- Description détaillée de l'architecture ScribBERT et du corpus de documents HSE
- Expérimentations comparatives : impact des différents paramètres sur la performance
- Analyse quantitative (métriques) et qualitative (erreurs, biais, cas limites)
- Discussion des résultats, limites méthodologiques et perspectives

---

## 5. Démarche scientifique

La démarche adoptée repose sur une **approche empirique et comparative** :

1. **Revue de littérature** : état de l'art sur les systèmes RAG et leurs méthodes d'évaluation
2. **Conception d'un protocole expérimental** : constitution d'un jeu de questions-réponses de référence, sélection de métriques
3. **Expérimentation** : tests comparatifs de différentes configurations du système (modèles, paramètres)
4. **Évaluation mixte** : combinaison de métriques automatiques (Precision, Recall, nDCG, BERTScore, LLM-as-judge) et d'évaluations humaines (grille standardisée, annotation experte)
5. **Analyse des résultats** : identification des configurations optimales, des limites et des pistes d'amélioration

---

## 6. Contributions attendues

### Contribution théorique
- **Formalisation d'un cadre d'évaluation** structuré pour les systèmes RAG
- **Clarification des notions** de pertinence et cohérence dans le contexte des LLMs augmentés
- **Synthèse critique** des métriques existantes et de leurs limites

### Contribution méthodologique
- **Protocole d'évaluation reproductible** applicable à d'autres domaines
- **Comparaison empirique** des différentes stratégies de chunking, embedding et retrieval
- **Méthodologie mixte** combinant évaluation automatique et humaine

### Contribution pratique
- **Retour d'expérience concret** sur le déploiement d'un système RAG en entreprise
- **Recommandations opérationnelles** pour l'optimisation de systèmes RAG
- **Identification des bonnes pratiques** pour les applications HSE et réglementaires

---

## 7. Résultats attendus et livrables

### Résultats attendus
- Un **protocole d'évaluation validé** sur un cas d'usage réel (ScribBERT)
- Une **analyse comparative** des performances selon différentes configurations
- Une **grille de recommandations** pour le choix des paramètres et modèles
- Une **identification des limites** actuelles des systèmes RAG et des pistes de recherche futures

### Livrables
1. **Mémoire de recherche** (80-120 pages) structuré en 3 parties
2. **Présentation de soutenance** (support visuel et démonstration du système)
3. **Annexes techniques** : code d'évaluation, jeux de données, résultats détaillés

---

## 8. Calendrier prévisionnel

| Période | Activités principales |
|---------|----------------------|
| **Novembre 2025** | Finalisation de l'état de l'art, construction du protocole d'évaluation |
| **Décembre 2025** | Expérimentations comparatives (modèles, chunking, retrieval) |
| **Janvier 2026** | Évaluation humaine (annotation, grille), analyse des résultats |
| **Février 2026** | Rédaction des parties II et III, interprétation des résultats |
| **Mars 2026** | Finalisation de la rédaction, relecture, préparation de la soutenance |
| **Avril 2026** | Soutenance |

---

## 9. Positionnement académique et scientifique

Ce mémoire se situe au **croisement de plusieurs disciplines** :
- **Traitement automatique du langage naturel (NLP)** : modèles de langage, embeddings, génération de texte
- **Recherche d'information (IR)** : retrieval sémantique, ranking, évaluation de la pertinence
- **Intelligence artificielle appliquée** : déploiement de systèmes en production, évaluation de la qualité
- **Gestion des connaissances** : capitalisation documentaire, accès à l'information en entreprise

Le travail s'appuie sur des **références académiques récentes** (Lewis et al. 2020, frameworks RAGAS, BEIR, MTEB) tout en apportant une **contribution empirique originale** via l'étude de cas ScribBERT et l'adaptation des méthodes d'évaluation au domaine HSE.

---

## 10. Enjeux et portée du travail

### Enjeux opérationnels pour l'entreprise
- **Fiabilité et sécurité** : garantir l'exactitude des informations transmises aux collaborateurs
- **Efficacité opérationnelle** : améliorer l'accès aux référentiels internes
- **Conformité réglementaire** : assurer la traçabilité et l'auditabilité des réponses

### Enjeux scientifiques et techniques
- **Combler un gap méthodologique** : peu de travaux proposent une évaluation complète et reproductible des systèmes RAG
- **Généralisation** : établir un cadre applicable à d'autres domaines (juridique, médical, technique)
- **Contribution à la communauté** : protocole et métriques réutilisables par d'autres chercheurs et praticiens

---

## 11. Besoins et demandes

### Validation du cadrage
Je souhaite valider avec vous :
- La **pertinence de la problématique** et des objectifs
- L'**équilibre entre théorie et pratique** dans la structure proposée
- La **faisabilité du calendrier** compte tenu de l'ampleur des expérimentations
- Les **attentes académiques** en termes de profondeur d'analyse et de revue de littérature

### Points d'attention
- **Accès aux données** : certaines données de Bouygues TP sont confidentielles, je prévois d'anonymiser les exemples
- **Volume d'expérimentations** : je souhaite confirmer que le périmètre est réaliste dans les délais impartis
- **Positionnement scientifique** : comment maximiser la valeur académique tout en gardant une approche pratique ?

---

## 12. Conclusion

Ce mémoire vise à apporter une **contribution à la fois scientifique et opérationnelle** sur l'évaluation des systèmes RAG, en proposant une méthodologie rigoureuse testée sur un cas d'usage réel dans le domaine HSE. L'enjeu est de produire un travail qui puisse servir de **référence méthodologique** pour les futures implémentations de systèmes RAG en entreprise, tout en enrichissant la littérature académique sur ce sujet émergent.

Je reste à votre disposition pour échanger sur cette proposition et l'ajuster selon vos recommandations.

---

**Contact** :  
A. LELEU  
[email@exemple.com]  
[Numéro de téléphone]
