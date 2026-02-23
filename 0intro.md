# Mémoire de fin d’études  


## Introduction

L’essor des modèles de langage transforme en profondeur la manière dont l’information est produite, partagée et exploitée. Ces modèles, sont désormais capables de générer du texte avec une prose quasi humaine, et ont par conséquent ouvert la voie à de nouveaux usages : assistants conversationnels, génération automatique de contenu, ou encore recherche d’information intelligente.  
Malgré leurs performances impressionnantes, les LLMs (Large Language Models, ou Models larges de langage en français) présentent encore des limites notables : hallucinations, manque de traçabilité des sources et difficulté à actualiser leurs connaissances. Ces faiblesses réduisent leur fiabilité dans des contextes où la précision est essentielle.
Pour répondre à ces limites, une approche hybride a émergé : le Retrieval-Augmented Generation (RAG). Formalisé pour la première fois en 2020 par Patrick Lewis et ses co-auteurs chez Facebook AI Research (Meta AI), UCL (University College London) et NYU (New York University), le RAG proposait de coupler un générateur séquence-à-séquence (BART) (modèle de langage) à un récupérateur dense (DPR) (retrieval via embeddings vectoriels). Ce couplage permettait d’ancrer les réponses du modèle sur des passages documentaires externes, établissant ainsi une nouvelle référence dans le domaine des questions-réponses ouvertes, présentée à la conférence NeurIPS 2020.
Le RAG combine donc la recherche documentaire et la génération linguistique afin de produire des réponses contextualisées et ancrées dans des sources connues et vérifiables. Cette approche suscite aujourd’hui un intérêt croissant pour des applications liées à la gestion de la connaissance, à la conformité réglementaire et à la capitalisation d’expertise.

C’est dans ce contexte d’innovation autour des architectures RAG qu’a été conçu ScribBERT, un chatbot développé dans le cadre de mon alternance au sein du département P2S (Prévention santé-sécurité) de Bouygues Travaux Publics.
L’objectif de ce projet était de permettre un accès rapide, fiable et contextualisé aux référentiels internes de l’entreprise. ScribBERT repose sur une architecture RAG, intégrant donc des méthodes de chunking, de vectorisation et de recherche documentaire dense, afin de répondre avec précision aux questions des collaborateurs.

Dans le domaine de la santé-sécurité, la qualité de l’information transmise ne relève pas d’un simple enjeu d’efficacité : elle engage directement la sécurité des collaborateurs sur les chantiers.  
Chaque réponse doit être exacte, cohérente et fondée sur les bonnes sources. Cette exigence de fiabilité a conduit à un travail de recherche approfondi sur la qualité de la recherche sémantique et la validation des réponses générées, rendant indispensable la mise en place d’un cadre d’évaluation rigoureux du système.

La question centrale qui guide ce travail peut ainsi être formulée comme suit : Comment évaluer la pertinence, la cohérence et la fiabilité d’un système RAG ?

Autrement dit, comment garantir qu’un système complexe récupère les bons documents et produise des réponses fidèles aux sources.

L’objectif principal de ce mémoire est de proposer une méthode d’évaluation complète, rigoureuse et reproductible pour mesurer la pertinence, la cohérence et la fiabilité d’un système RAG.  
Ce travail vise à identifier et formaliser des critères d’évaluation pertinents pour les systèmes RAG, explorer et comparer différentes métriques d’évaluation, étudier l’impact des paramètres clés de la pipeline RAG en elle-même et enfin mettre en oeuvre et tester ce protocole sur un cas d’usage concret : ScribBERT.
L’enjeu est d’établir un cadre d’analyse qui puisse être généralisé à d’autres contextes documentaires et à d’autres domaines d’application.

Pour répondre à cette question, la démarche adoptée dans ce mémoire repose sur trois axes principaux qui formeront les trois parties de ce mémoire :  

Partie 1 Cadre conceptuel et théorique : présentation des fondements du RAG, de la recherche sémantique et des enjeux liés à la pertinence et à la cohérence.  
Partie 2 Méthodologie d’évaluation : élaboration du cadre d’analyse, sélection des métriques et mise en place du protocole d’évaluation.
Partie 3 Application expérimentale et discussion : implémentation du protocole sur ScribBERT, analyse des résultats et formulation de recommandations pour l’évaluation future des systèmes RAG.

---
### Transition :
Avant d’élaborer une méthodologie d’évaluation et de présenter les résultats expérimentaux, il est essentiel d’ancrer ce travail sur des bases claires.
La première partie de ce mémoire vise ainsi à retracer l’évolution des approches de recherche documentaire vers la recherche sémantique, à présenter les fondements techniques et architecturaux du RAG, et à clarifier les notions de pertinence, de cohérence et de fiabilité qui en constituent les piliers.  
Cette base théorique servira de socle à la construction du protocole d’évaluation présenté dans la suite du mémoire.
