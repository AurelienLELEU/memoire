# Mémoire — Évaluation de la cohérence et de la fiabilité d’un système RAG (cas d’usage : ScribBERT)

> Document de travail (version brouillon). Les éléments marqués **[À compléter]** sont des placeholders (chiffres, exemples internes, schémas, références exactes).

## Introduction

L’essor des **modèles de langage** et plus largement le boom de l'IA transforment en profondeur la manière dont l’information est produite, partagée et exploitée. Ces modèles, sont désormais capables de générer du texte avec une prose quasi humaine, et ont par conséquent ouvert la voie à de nouveaux usages tels que des assistants conversationnels, génération automatique de contenu (que ce soit vidéo, images, sons, textes, codes), ou encore recherche d’information intelligente.  
Malgré leurs performances impressionnantes, les **LLMs** (Large Language Models, ou Models larges de langage en français) présentent encore des limites notables : **hallucinations**, manque de traçabilité des sources et difficulté à **actualiser leurs connaissances**. Ces faiblesses réduisent leur fiabilité dans des contextes où la précision est essentielle.
Pour répondre à ces limites, une approche hybride a émergé : le **Retrieval-Augmented Generation** (RAG), qui combine **recherche documentaire** et **génération linguistique** afin de produire des réponses contextualisées et ancrées dans des sources connues et vérifiables.[^Lewis2020] Cette approche, dont les fondements techniques et l’historique seront détaillés en Partie I, suscite aujourd’hui un intérêt croissant pour des applications liées à la gestion de la connaissance, à la conformité réglementaire et à la capitalisation d’expertise.

C’est dans ce contexte d’innovation autour des architectures RAG qu’a été conçu ScribBERT, un chatbot développé dans le cadre de mon alternance au sein du département P2S (Prévention santé-sécurité) de Bouygues Travaux Publics.
L’objectif de ce projet était de permettre un accès rapide et fiable aux référentiels internes de l’entreprise. ScribBERT repose sur une architecture RAG, intégrant donc des méthodes de **chunking**, de **vectorisation** et de **recherche documentaire dense**, afin de répondre avec précision aux questions des collaborateurs.

Dans le domaine de la santé-sécurité, la qualité de l’information transmise ne relève pas d’un simple enjeu d’efficacité : elle engage directement la sécurité des collaborateurs sur les chantiers.  
Chaque réponse doit donc être exacte et fondée sur les bonnes sources. Cette exigence de fiabilité a conduit à un travail de recherche approfondi sur la qualité de la **recherche sémantique** et la validation des réponses générées, rendant indispensable la mise en place d’un cadre d’évaluation rigoureux du système.

La question centrale qui guide ce travail peut ainsi être formulée comme suit : Comment évaluer la cohérence et la fiabilité d’un système RAG ?

Autrement dit, comment garantir qu’un système complexe récupère les bons documents et produise des réponses fidèles aux documents récupérés.

L’objectif principal de ce mémoire est de proposer une méthode d’évaluation complète, rigoureuse et reproductible pour mesurer la pertinence, la cohérence et la fiabilité d’un système RAG.  
Ce travail vise à identifier et formaliser des critères d’évaluation pertinents pour les systèmes RAG, explorer et comparer différentes métriques d’évaluation, étudier l’impact des paramètres clés de la **pipeline** RAG en elle-même et enfin mettre en oeuvre et tester ce protocole sur un cas d’usage concret : ScribBERT.
L’enjeu est d’établir un cadre d’analyse qui puisse être généralisé à d’autres contextes documentaires et à d’autres domaines d’application.

Pour répondre à cette question, la démarche adoptée dans ce mémoire repose sur trois axes principaux qui formeront les trois parties de ce mémoire :  

Partie 1 Cadre conceptuel et théorique : présentation des fondements du RAG, des différents types de recherche (sémantique, textuelle et autres) et des enjeux liés à la pertinence et à la cohérence. *(ask stats sur part des accidents sur référentiels non suivis)*  
Partie 2 Méthodologie d’évaluation : élaboration du cadre d’analyse, sélection des métriques et mise en place du protocole d’évaluation.  
Partie 3 Application expérimentale et discussion : implémentation du protocole sur ScribBERT, analyse des résultats et formulation de recommandations pour l’évaluation future des systèmes RAG.

---

## Présentation du contexte : Bouygues Travaux Publics et le projet ScribBERT

Avant d'entrer dans le cadre conceptuel, il convient de présenter brièvement l'entreprise au sein de laquelle s'inscrit ce mémoire ainsi que le département et le projet qui en constituent le terrain d'application. Cette présentation n'a pas pour objet de dresser un historique exhaustif, mais de poser les éléments nécessaires pour comprendre les contraintes opérationnelles, documentaires et organisationnelles qui ont structuré les choix techniques et méthodologiques de ce travail.

### Le groupe Bouygues et la branche Construction

Le **groupe Bouygues** est un groupe industriel français diversifié, fondé en 1952 par Francis Bouygues. Il s'organise aujourd'hui autour de plusieurs métiers : la construction (Bouygues Construction, Bouygues Immobilier, Colas), les médias (TF1), les télécommunications (Bouygues Telecom) et les services à l'énergie et à l'industrie (Equans, intégré au groupe en 2022). En 2024, le groupe employait environ **200 000 collaborateurs** dans plus de 80 pays **[À compléter : chiffre exact d'effectifs et chiffre d'affaires de l'année de référence]**.

Au sein de ce groupe, **Bouygues Construction** rassemble les activités de bâtiment, de travaux publics et d'énergies/services. Elle se décompose elle-même en plusieurs entités opérationnelles, dont **Bouygues Travaux Publics** (Bouygues TP), qui constitue le pôle de référence pour les ouvrages de génie civil complexes.

### Bouygues Travaux Publics : périmètre et activités

Bouygues Travaux Publics est la filiale du groupe spécialisée dans la conception et la réalisation de **grandes infrastructures de génie civil** :

- ouvrages souterrains (tunnels routiers, ferroviaires, métros, galeries hydrauliques) ;
- ouvrages d'art (ponts, viaducs) ;
- infrastructures de transport (autoroutes, lignes ferroviaires à grande vitesse) ;
- ouvrages maritimes et fluviaux (ports, digues, écluses) ;
- ouvrages industriels et énergétiques (centrales nucléaires, barrages, terminaux GNL).

L'entreprise est notamment impliquée dans des projets emblématiques tels que le **Grand Paris Express** (plusieurs lots de tunnels et de gares pour les nouvelles lignes de métro), la centrale nucléaire **EPR de Hinkley Point C** au Royaume-Uni, ou encore divers projets internationaux en Asie, en Afrique et en Amérique du Nord. Elle compte environ **[À compléter : effectif Bouygues TP]** collaborateurs répartis sur des chantiers en France et à l'international, avec un siège social à **Guyancourt (Yvelines)**.

Cette typologie d'ouvrages présente trois caractéristiques structurantes pour le sujet de ce mémoire :

1. **Une exposition aux risques élevée** : travaux en hauteur, en souterrain, à proximité d'engins lourds, en milieu confiné, à proximité d'eau, en environnement nucléaire, etc. Chaque chantier mobilise un volume important de procédures de sécurité spécifiques.
2. **Une production documentaire considérable et hétérogène** : standards groupe, procédures filiales, modes opératoires chantier, plans de prévention, retours d'expérience (REX), normes externes (NF, EN, ISO), réglementations nationales variables selon les pays d'intervention.
3. **Une organisation projet décentralisée** : chaque chantier dispose d'une équipe dédiée et d'une certaine autonomie opérationnelle, ce qui complique la diffusion uniforme des bonnes pratiques et la consultation rapide des référentiels.

### Le département P2S (Prévention Santé-Sécurité)

Au sein de Bouygues TP, le département **P2S — Prévention Santé-Sécurité** est en charge de la définition, de la diffusion et du suivi de la politique santé-sécurité de l'entreprise. Ses missions couvrent notamment :

- la **rédaction et la maintenance des référentiels** (procédures, standards, instructions) ;
- l'**accompagnement opérationnel** des équipes chantier (audits, visites, formations) ;
- l'**analyse des accidents et presqu'accidents**, et la capitalisation des retours d'expérience ;
- le **reporting** et le pilotage des indicateurs santé-sécurité (taux de fréquence, taux de gravité, **[À compléter : indicateurs internes BTP]**) ;
- la **veille réglementaire** française et internationale.

L'enjeu opérationnel central est de **rendre l'information de sécurité accessible, exacte et applicable au bon moment**, c'est-à-dire dans le contexte de la situation de travail. Or les retours terrain montrent qu'une part significative des situations à risque ne provient pas d'une absence de référentiel, mais d'une **difficulté à retrouver rapidement la bonne information** dans un corpus volumineux et fragmenté **[À compléter : statistique interne ou étude sectorielle sur la part des écarts liés à la non-consultation des référentiels]**.

### Le projet ScribBERT

C'est dans ce contexte qu'a été initié le projet **ScribBERT**, un assistant conversationnel interne basé sur une architecture de **Retrieval-Augmented Generation**. L'objectif fonctionnel se résume en une phrase : *permettre à un collaborateur de poser une question en langage naturel sur les règles santé-sécurité et obtenir une réponse synthétique, sourcée et auditable, fondée sur les référentiels validés du département P2S*.

Les principes directeurs du projet ont été les suivants :

- **Ancrage strict** sur les documents internes validés (pas de réponse sans source) ;
- **Traçabilité** systématique des passages cités, avec lien vers le document d'origine ;
- **Confidentialité** : hébergement et traitement compatibles avec la sensibilité des documents internes **[À compléter : précisions sur l'architecture d'hébergement, on-prem vs cloud souverain]** ;
- **Évaluabilité** : conception du système pensée pour être mesurable, ce qui constitue précisément l'objet de ce mémoire.

Le projet a été développé dans le cadre de mon **alternance de trois ans** au sein du département P2S, dont **un an et demi** consacré à ScribBERT à partir de la deuxième année. La supervision a été assurée conjointement par **Flavien Martin** (tuteur métier, santé-sécurité) et **Julien Larseneur** (tuteur technique, software). Le périmètre fonctionnel initial couvre l'ensemble des référentiels santé-sécurité du siège de Bouygues TP, soit environ une centaine de documents PDF (cf. Ch. 7).

### Implications pour ce mémoire

La nature de l'entreprise et du département a directement influencé la problématique d'évaluation traitée dans ce mémoire :

- la **criticité métier** (santé et sécurité des personnes) impose des exigences de fiabilité plus strictes que celles que l'on retrouve dans un cas d'usage généraliste (assistant marketing, FAQ produit) ;
- l'**hétérogénéité documentaire** rend les benchmarks publics insuffisants pour évaluer le système et impose la construction d'un corpus de test interne ;
- les **contraintes de confidentialité** orientent les choix de modèles (préférence pour des modèles ouverts ou hébergeables) et limitent la possibilité de publier certains résultats bruts ;
- enfin, le caractère **opérationnel** du déploiement (utilisateurs réels, conséquences concrètes) impose de considérer non seulement la performance moyenne, mais également la **stabilité** et la **gestion des cas limites**.

Ces éléments justifient le choix d'un protocole d'évaluation rigoureux et reproductible, qui constitue la contribution centrale de ce travail.

---

# PARTIE I — Cadre conceptuel et état de l'art

Cette première partie vise à replacer les systèmes de **Retrieval-Augmented Generation (RAG)** dans l’histoire des méthodes de recherche d’information (Information Retrieval, IR), puis à formaliser les notions de **pertinence** et de **cohérence/fidélité** qui seront au cœur du protocole d’évaluation proposé.

Deux idées structurent l’ensemble :

1. Un RAG n’est pas « un LLM + des documents », mais une **chaîne de décision** (indexation, retrieval, assemblage du contexte, génération) dont les erreurs s’additionnent et parfois se masquent.
2. Les critères d’évaluation classiques de l’IR et ceux des LLMs ne se recouvrent pas entièrement : un système peut obtenir un bon score de retrieval et produire une réponse incorrecte, ou l’inverse (réponse plausible mais non sourcée).

L’objectif de cette partie est donc (i) de clarifier les mécanismes techniques qui amènent à la recherche sémantique moderne, (ii) de situer les architectures RAG par rapport aux alternatives (moteurs de recherche, fine-tuning, QA extractive), et (iii) d’installer un vocabulaire rigoureux pour la suite.

## Chapitre 1 — De la recherche documentaire à la recherche sémantique

### 1.1. Brève histoire de la recherche d’information : du lexical au probabiliste

La recherche d’information s’est construite autour d’un objectif central : **ordonner** (ranker) des documents en fonction d’un besoin informationnel, dans un contexte où l’utilisateur n’exprime qu’une approximation de ce besoin via une requête.[^Manning2008] Dès l’après-guerre, l’idée d’un accès mécanisé à l’information a été popularisée avec le concept de *Memex*.[^Bush1945]

Les premières approches opérationnelles reposent sur des représentations **lexicales** : un document est vu comme un ensemble de termes et une requête comme une contrainte sur ces termes. Le **modèle booléen** (AND/OR/NOT) est explicable et contrôlable, mais il ne produit pas naturellement de classement, et il rend difficile l’expression de besoins « graduels » (plus ou moins pertinents).

L’IR moderne s’est ensuite structurée autour de la notion de **ranking** et d’évaluation systématique. Le *Cranfield paradigm* a joué un rôle déterminant : constituer un corpus, un ensemble de requêtes, et des jugements de pertinence pour comparer des systèmes.[^Cleverdon1967] Plus tard, les campagnes TREC ont industrialisé cette logique d’évaluation à grande échelle.[^VoorheesHarman2005]

Les modèles vectoriels ont ensuite introduit une représentation plus graduelle : documents et requêtes sont représentés comme des vecteurs de poids, et la similarité est souvent mesurée par le cosinus. Une pondération emblématique est le TF-IDF, qui combine une mesure de fréquence locale (*term frequency*) et une mesure de rareté globale (*inverse document frequency*). Formellement :

$$\mathrm{tfidf}(t, d) = \mathrm{tf}(t,d) \times \log\left(\frac{N}{\mathrm{df}(t)}\right)$$

où $N$ est le nombre total de documents et $\mathrm{df}(t)$ le nombre de documents contenant le terme $t$.

L’idée d’IDF comme signal de discrimination d’un terme remonte à des travaux fondateurs sur le *term specificity*.[^SparckJones1972] Le **vector space model** (VSM) popularisé par Salton et al. a ensuite fourni un cadre pratique et encore omniprésent pour pondérer et comparer requêtes et documents.[^Salton1975]

À partir des années 1990-2000, les approches probabilistes (notamment **BM25**) se sont imposées comme standard industriel : elles offrent un excellent compromis performance/simplicité et une robustesse sur des corpus variés.[^RobertsonZaragoza2009] BM25 peut être vu comme une amélioration de TF-IDF qui normalise explicitement par la longueur du document et introduit des hyperparamètres de saturation.

$$\mathrm{BM25}(q, d) = \sum_{t \in q} \mathrm{idf}(t) \cdot \frac{\mathrm{tf}(t,d) \cdot (k_1+1)}{\mathrm{tf}(t,d) + k_1 \cdot \left(1-b + b\cdot \frac{|d|}{\mathrm{avgdl}}\right)}$$

avec $k_1$ et $b$ des paramètres de calibration, $|d|$ la longueur du document et $\mathrm{avgdl}$ la longueur moyenne.

Enfin, une autre famille importante — très utilisée en pratique — est celle des **modèles de langage pour l’IR**, où l’on estime la probabilité qu’un document génère une requête (approches *query likelihood*), et où l’on utilise des techniques de lissage et de feedback pseudo-pertinent.[^PonteCroft1998][^LavrenkoCroft2001]

Ces modèles « classiques » (BM25, query likelihood, variantes) restent extrêmement compétitifs, notamment sur des corpus techniques où les indices lexicaux (références, numéros de procédure, intitulés normatifs) apportent des signaux précieux.

#### 1.1.1. Évaluer un système de recherche : pourquoi les métriques comptent

Les pipelines RAG héritent directement de l’IR un point crucial : **l’évaluation dépend du protocole**. La performance d’un moteur ne peut pas être « résumée » par un seul score sans préciser (i) la tâche, (ii) la définition de pertinence, (iii) le nombre de résultats considérés ($k$), et (iv) la nature binaire ou graduée des jugements.[^Manning2008][^BaezaYates2011][^Croft2010][^VoorheesHarman2005]

Dans sa forme la plus simple, on distingue :

- la **précision** (proportion de résultats pertinents parmi les résultats retournés),
- le **rappel** (proportion des résultats pertinents retrouvés parmi tous les pertinents existants).

En recherche classée, on utilise des métriques au rang : Precision@k, Recall@k, et des métriques de classement global comme **nDCG** (qui gère naturellement la pertinence graduée).[^JarvelinKekalainen2002]

Ce point est central pour le mémoire : si l’on change la définition de pertinence (thématique vs situationnelle), les scores de retrieval changent — et la qualité perçue aussi.

#### 1.1.2. Feedback, reformulation et *query expansion*

Un système IR n’est pas seulement un scoreur : il peut aussi **adapter la requête**. Le *relevance feedback* (et ses variantes) formalise l’idée qu’à partir de documents jugés pertinents, on peut déplacer la requête vers une meilleure représentation du besoin. L’algorithme de Rocchio est souvent présenté comme une forme canonique dans le cadre vectoriel.[^Rocchio1971]

En pratique, la reformulation automatique (pseudo-relevance feedback, expansion) vise à augmenter le rappel, mais elle peut introduire du bruit. Dans un RAG, cette question se re-formule : une expansion peut améliorer le retrieval, tout en augmentant le risque de récupérer des passages « proches mais non applicables ».

#### 1.1.3. Learning-to-rank : apprendre le ranking à partir de signaux

La phase suivante de l’IR moderne consiste à apprendre une fonction de classement à partir de données (clics, jugements, paires). C’est le domaine du **learning-to-rank**, avec des approches *pointwise*, *pairwise* et *listwise*.[^Liu2009LTR]

Des travaux fondateurs ont montré qu’on pouvait apprendre à ordonner directement des documents pour une requête avec des méthodes à marge (ex. RankSVM).[^Joachims2002]

Aujourd’hui, la plupart des systèmes industriels combinent :

1. un **retrieval rapide** (souvent sparse et/ou dense),
2. un **reranking** plus coûteux (souvent cross-encoder),
3. des signaux métier (popularité, fraîcheur, autorité).

Le RAG s’insère naturellement dans cette logique multi-étage.

### 1.2. Limites du matching lexical

Les méthodes lexicales (booléen, TF-IDF, BM25) reposent sur une hypothèse forte : la pertinence est principalement capturable par la co-occurrence de termes entre requête et document. Or, cette hypothèse se heurte à plusieurs problèmes bien documentés :

- **Synonymie** : deux textes peuvent décrire la même notion avec des termes différents (ex. « harnais antichute » vs « EPI antichute »).
- **Polysémie** : un même terme peut renvoyer à des concepts différents selon le contexte (ex. « levage » en planification vs levage en opération terrain).
- **Morphologie et variations** : flexions, abréviations, variantes métier.
- **Requêtes complexes** : demandes qui expriment une intention, une contrainte, ou une justification (« que faire si… », « dans quel cas… », « quelles exceptions… ») plutôt qu’une simple liste de mots-clés.

Dans un contexte technique et réglementaire, ces limites sont accentuées : le vocabulaire est spécialisé, la formulation est parfois normative, et l’utilisateur peut utiliser un vocabulaire terrain différent de celui du référentiel.

Deux compléments sont importants pour comprendre pourquoi ces limites deviennent critiques dans un RAG :

- **Rappel vs précision** : un moteur lexical peut être très précis (peu de bruit) mais rater des passages formulés différemment ; inversement, il peut être rappelé mais ramener trop de textes « proches » sans être applicables. Le RAG transforme ce compromis en risque de génération : *un passage légèrement hors-sujet peut suffire à entraîner une réponse erronée*.
- **Correspondance d’intention** : la requête utilisateur exprime souvent une tâche (ex. « quels EPI obligatoires ? », « quelle procédure avant intervention ? »), et pas seulement un thème. Or les signaux lexicaux capturent mal la structure de tâche (conditions, exceptions, étapes).

### 1.3. Vers la recherche sémantique : représentations distribuées et embeddings

La recherche sémantique vise à dépasser le *matching* lexical en exploitant des représentations continues (embeddings) qui capturent des régularités sémantiques. Historiquement, cette idée s’inscrit dans une lignée allant de l’indexation latente et des modèles distributionnels jusqu’aux embeddings neuronaux.

Une étape importante est l’**indexation sémantique latente** (LSI/LSA), qui projette le terme-document dans un espace latent à plus faible dimension via une factorisation (SVD). L’objectif est de capturer des corrélations entre termes et de réduire la synonymie/polysémie purement lexicale.[^Deerwester1990]

Les modèles d’embeddings neuronaux ont ensuite popularisé l’apprentissage de représentations distribuées à grande échelle. Les modèles de type **Word2Vec** (CBOW et Skip-gram) apprennent des vecteurs de mots à partir des contextes d’apparition : des mots apparaissant dans des contextes similaires auront des vecteurs proches.[^Mikolov2013] D’autres variantes comme **GloVe** combinent statistiques globales de co-occurrence et optimisation locale.[^Pennington2014]

Cependant, ces représentations sont **context-free** : un mot a un seul vecteur, quel que soit son sens dans la phrase. Les modèles de type Transformers (ex. BERT) ont ensuite introduit des **représentations contextualisées** : la représentation d’un token dépend de la phrase, ce qui permet de mieux gérer la polysémie et la structure linguistique.

L’arrivée des Transformers a constitué un tournant majeur : l’architecture « attention-only » a permis une modélisation efficace de dépendances longues et une pré-formation à grande échelle.[^Vaswani2017] BERT, en particulier, a popularisé la pré-formation auto-supervisée avec masquage de tokens et a servi de base à une grande partie des approches de recherche sémantique modernes.[^Devlin2019]

Dans la pratique, l’usage IR/RAG requiert surtout des **embeddings de phrases/passages** (*sentence or passage embeddings*). Les approches de type **bi-encodeur** (ou dual-encoder) encodent requête et passage séparément, puis comparent leurs vecteurs (souvent cosinus ou produit scalaire). Sentence-BERT (SBERT) a été une contribution clé pour obtenir des embeddings de phrases efficaces via apprentissage contrastif et siamese networks.[^ReimersGurevych2019] Des travaux plus récents (ex. SimCSE) montrent que des schémas contrastifs simples peuvent déjà produire de très bons espaces d’embedding.[^Gao2021]

À l’inverse, les **cross-encoders** concatènent requête et passage et produisent un score de pertinence en tenant compte finement des interactions token-à-token, mais ils coûtent beaucoup plus cher à l’inférence. Ils sont souvent utilisés en **reranking** sur un petit nombre de candidats.[^NogueiraCho2019]

Enfin, des architectures intermédiaires (late interaction) comme **ColBERT** cherchent à concilier précision (interactions fines) et efficacité (indexation) via des représentations token-level compressées.[^KhattabZaharia2020]

### 1.4. Sparse, dense et hybride : familles de retrieval

On distingue classiquement :

- **Sparse retrieval** : représentation de grande dimension mais très creuse (BM25, TF-IDF), efficace et interprétable.
- **Dense retrieval** : représentation dense de faible dimension (embeddings), plus apte à capturer synonymie et paraphrase.
- **Hybride** : combinaison des signaux sparse et dense, souvent utile sur des corpus hétérogènes et sur des requêtes variées.

De plus, l’étape de *retrieval* peut être complétée par un **reranking** : on récupère d’abord un ensemble candidat (rapide), puis un modèle plus coûteux (souvent un cross-encoder) classe finement les passages.

Au-delà de cette typologie, un point technique essentiel pour les systèmes denses est l’indexation par recherche du **plus proche voisin approximatif** (Approximate Nearest Neighbor, ANN). À grande échelle, il est impossible de comparer une requête à tous les vecteurs. On utilise donc des structures (HNSW, IVF, PQ…) qui accélèrent la recherche au prix d’une approximation contrôlée.[^MalkovYashunin2018][^Johnson2019]

Cette approximation a une conséquence méthodologique : la performance de retrieval dépend non seulement du modèle d’embedding, mais aussi de la configuration de l’index (paramètres HNSW, quantization, etc.). Dans un protocole d’évaluation, il est donc important de distinguer :

- **erreur de représentation** (embedding inadapté),
- **erreur d’indexation** (approximation ANN),
- **erreur de formulation de requête** (query rewriting absent ou mal calibré).

### 1.5. Problématiques spécifiques à la sémantisation en contexte technique / HSE

Dans le cas d’un usage HSE (santé-sécurité), la recherche sémantique doit composer avec des contraintes supplémentaires :

- **Criticité de l’erreur** : une réponse plausible mais fausse est plus dangereuse que l’absence de réponse.
- **Vocabulaire métier et acronymes** : variations inter-équipes, jargon chantier.
- **Granularité des sources** : règles générales vs procédures locales, exceptions, cas particuliers.
- **Multilinguisme et variations de registre** : documents internes, fournisseurs, normes, etc.

Ces éléments motivent la nécessité d’évaluer non seulement la « capacité à retrouver quelque chose de proche », mais la capacité à retrouver **les bons passages** et à générer une réponse **fidèle** aux sources.

On peut ajouter des phénomènes fréquemment observés dans des corpus internes :

- **Documents composites** : procédures longues contenant plusieurs sous-thèmes ; un chunk peut contenir de « bons mots-clés » mais être la mauvaise section.
- **Niveaux de normativité** : ce qui est « recommandé » vs « obligatoire », ce qui est « interdit » vs « déconseillé ». La nuance linguistique peut être critique.
- **Conflits de version** : documents périmés encore présents, doublons, ou versions locales.

Ces caractéristiques font que l’évaluation end-to-end doit intégrer des notions comme l’**autorité** et l’**actualité** des sources, au-delà de la simple proximité sémantique.

### 1.6. Limites des approches traditionnelles face aux LLMs

L’émergence des LLMs change la nature des requêtes : l’utilisateur n’écrit plus seulement des mots-clés, mais formule des questions complexes, situées, parfois implicites. Deux conséquences majeures :

1. La recherche doit gérer des **intentions** (besoin d’explication, de comparaison, de décision) et non uniquement une adéquation thématique.
2. Le système doit réduire le risque d’**hallucination**, notamment lorsque les documents sont incomplets, contradictoires, ou quand la requête induit un raisonnement.

Les LLMs peuvent aussi reformuler des requêtes, enrichir le contexte, ou synthétiser des informations. Mais sans ancrage explicite dans des sources, ils restent vulnérables aux erreurs factuelles et à la non-traçabilité. C’est précisément l’espace que viennent occuper les architectures RAG.

De plus, les LLMs peuvent produire des textes *hautement cohérents sur la forme* tout en étant incorrects sur le fond (hallucinations). Ce phénomène a été largement étudié dans la génération neuronale, notamment en résumé et en QA.[^Maynez2020][^Ji2023] En contexte HSE, il devient un risque opérationnel, d’où l’importance de critères d’évaluation centrés sur la **fidélité** aux sources.

### 1.7. Neural IR et « dense retrieval » : un bref état de l’art

Avant les RAG, la recherche a connu une transition majeure : passer de la recherche lexicalement pondérée à des modèles neuronaux de ranking. On peut citer :

- Les premiers modèles de *semantic matching* (ex. DSSM) qui apprennent à rapprocher requête et document dans un espace latent.[^Huang2013]
- Des modèles interactionnels (ex. DRMM) qui exploitent explicitement des signaux de correspondance au niveau des termes.[^Guo2016]

Avec la montée en puissance des Transformers, le **dense retrieval** s’est structuré autour de bi-encodeurs entraînés sur des tâches de question-réponse, typiquement en utilisant des passages positifs/négatifs. DPR (Dense Passage Retrieval) est devenu une référence : il a montré qu’un encodage dense bien entraîné pouvait surpasser les approches classiques sur des benchmarks de QA ouverts.[^Karpukhin2020]

Au-delà de DPR, une grande partie des gains récents provient de stratégies d’entraînement avec **hard negatives** (négatifs difficiles) et d’itérations retrieval-training ; ANCE est un exemple influent de ce type d’approche pour améliorer la qualité du dense retrieval à grande échelle.[^Xiong2020ANCE]

Une étape intermédiaire importante est **ORQA** (Open-Retrieval Question Answering), proposé par Lee et al. en 2019, qui a montré qu'un retriever pré-entraîné de manière non supervisée (via *Inverse Cloze Task*) pouvait déjà améliorer les systèmes de QA ouverts sans nécessiter de paires question-passage annotées manuellement.[^Lee2019ORQA] Ce travail a posé les bases méthodologiques qui ont conduit à DPR et aux architectures RAG.

Ces méthodes s'appuient aussi fortement sur des datasets de grande taille (ex. MS MARCO) qui structurent l'apprentissage du ranking moderne.[^Nguyen2016]

Dans un contexte d'entreprise, cela crée une question pratique : **un modèle entraîné sur des données web généralistes est-il adapté à un vocabulaire métier et à des documents normatifs ?** Des travaux sur l'adaptation de domaine (*domain adaptation*) pour le dense retrieval montrent que les performances se dégradent significativement lorsqu'un modèle est évalué hors de son domaine d'entraînement, ce que le benchmark BEIR a mis en évidence de manière systématique.[^Thakur2021BEIR] Cette question sera traitée dans la PARTIE II via le choix et l'évaluation des modèles d'embedding.

### 1.8. Du dense retrieval au RAG : la convergence historique

La trajectoire décrite dans ce chapitre — du lexical au probabiliste, du probabiliste aux embeddings, des embeddings au dense retrieval — converge naturellement vers l'idée de **coupler un retriever dense à un modèle génératif**.

Plusieurs jalons ont marqué cette convergence :

1. **DrQA** (Chen et al., 2017) a popularisé le paradigme *retriever-reader* pour la QA ouverte : un retrieval TF-IDF suivi d'un lecteur neuronal. Le principe d'un pipeline en deux étapes (retrouver puis répondre) était posé, mais les deux composantes n'étaient pas entraînées conjointement.[^Chen2017DrQA]

2. **ORQA** (Lee et al., 2019) a introduit le pré-entraînement non supervisé du retriever, montrant que l'on pouvait apprendre à retrouver des passages pertinents sans annotations, ouvrant la voie à des pipelines entièrement neuronales.[^Lee2019ORQA]

3. **REALM** (Guu et al., 2020) a formalisé l'intégration du retrieval dans l'objectif de pré-formation du modèle de langage, traitant les passages récupérés comme des variables latentes optimisées de bout en bout.[^Guu2020]

4. **RAG** (Lewis et al., 2020) a constitué la formalisation la plus influente de cette approche. Proposé par Patrick Lewis et ses co-auteurs chez Meta AI, University College London et New York University, le RAG couplait un **générateur séquence-à-séquence** (BART) à un **récupérateur dense** (DPR, basé sur des embeddings vectoriels). Ce couplage permettait d'ancrer les réponses du modèle de langage sur des passages documentaires externes, établissant une nouvelle référence sur les benchmarks de questions-réponses ouvertes (Natural Questions, TriviaQA, WebQuestions). L'article distinguait deux variantes : **RAG-Sequence** (un même passage conditionne toute la réponse) et **RAG-Token** (chaque token peut s'appuyer sur un passage différent). Présenté à la conférence **NeurIPS 2020**, ce travail a donné son nom à toute la famille d'architectures.[^Lewis2020]

5. **Fusion-in-Decoder** (Izacard & Grave, 2021) a ensuite montré qu'en concaténant de nombreux passages récupérés et en laissant le décodeur fusionner l'information, on pouvait améliorer significativement la QA multi-passage, au prix d'un coût de calcul accru.[^IzacardGrave2021]

Cette progression montre que le RAG n'est pas une invention isolée mais l'aboutissement d'une ligne de recherche qui, depuis les premiers systèmes d'IR lexicaux, cherche à relier **accès à l'information** et **production de connaissances**. Le chapitre suivant détaille l'architecture et les enjeux spécifiques de ces systèmes.

## Chapitre 2 — Les fondements du RAG (Retrieval-Augmented Generation)

### 2.1. Principe général : génération augmentée par récupération

Le Retrieval-Augmented Generation (RAG) désigne une famille d’architectures où un modèle génératif produit une réponse en s’appuyant sur un contexte documentaire récupéré dynamiquement au moment de la requête. Conceptuellement, le RAG se situe entre :

- Un **moteur de recherche** classique : performant pour retrouver des documents, mais ne produit pas une réponse rédigée.
- Un **LLM** utilisé seul : capable de rédiger, mais dont les réponses peuvent être non sourcées, et dont les connaissances peuvent être obsolètes.

Le schéma RAG répond à un objectif : **ancrer** la génération dans des passages pertinents, traçables et contrôlables.

D’un point de vue historique, les architectures RAG s’inscrivent dans la continuité des systèmes **retriever-reader** d’open-domain QA : un premier module récupère des passages, un second extrait ou produit la réponse. DrQA a popularisé cette décomposition (retrieval TF-IDF + reader neural) et a mis en évidence l’importance d’un pipeline end-to-end.[^Chen2017DrQA] Les approches plus récentes ont ensuite remplacé les composantes lexicales par du dense retrieval et ont fait évoluer le « reader » vers des générateurs plus puissants.[^Karpukhin2020]

Un point clé est que le RAG formalise implicitement un problème de **modélisation conditionnelle avec variable latente** : les passages récupérés jouent le rôle de variables latentes $z$ (chunks/documents), et la réponse $y$ est générée conditionnellement à la requête $x$ et à $z$.

On peut le représenter schématiquement par :

$$p(y\mid x)=\sum_z p(y\mid x,z)\,p(z\mid x)$$

En pratique, on approxime cette somme en ne considérant qu’un petit nombre de passages (top-$k$), ce qui rend les choix de retrieval cruciaux : si le « bon » passage n’apparaît pas dans le top-$k$, la génération est contrainte par un contexte incomplet.

### 2.2. RAG vs fine-tuning : choix méthodologiques

Deux stratégies sont souvent opposées :

- **Fine-tuning** : adapter le modèle sur des données spécifiques. Avantages : style et comportements mieux contrôlés ; limites : coût, maintenance, risque de sur-apprentissage, difficulté à intégrer rapidement de nouvelles connaissances.
- **RAG** : conserver un modèle (souvent généraliste) et injecter du contexte à la demande. Avantages : mise à jour facile (on met à jour le corpus), meilleure traçabilité, séparation entre connaissances et génération.

Dans un contexte d’entreprise et de documents internes, le RAG présente des avantages opérationnels évidents : actualisation sans réentraînement, gouvernance des sources, auditabilité.

On peut toutefois noter que les approches ne s’excluent pas :

- **fine-tuning léger** (ou instruction tuning) pour adapter le style de réponse, les formats (check-list HSE), ou des comportements (refus, prudence),
- **RAG** pour l’accès aux connaissances factuelles et la traçabilité.

La littérature récente insiste d’ailleurs sur cette complémentarité et sur les compromis entre retrieval, parametric memory et adaptation.[^Gao2024RAGSurvey]

### 2.3. Architecture type d’une pipeline RAG

Une pipeline RAG se décompose généralement en cinq étapes :

1. **Ingestion** : collecte des documents (PDF, Word, pages wiki, procédures internes), extraction de texte, normalisation.
2. **Chunking** : découpage en segments (chunks) pour équilibrer granularité et rappel.
3. **Vectorisation / indexation** : calcul d’embeddings pour chaque chunk et insertion dans un index (base vectorielle).
4. **Retrieval / reranking** : récupération de $k$ passages pertinents, éventuellement reclassés par un modèle plus fin.
5. **Génération** : construction d’un prompt avec la requête + contexte, puis génération d’une réponse (souvent accompagnée de citations).

Dans le cas étudié (ScribBERT), cette architecture se décline avec des choix d’implémentation qui seront décrits en PARTIE III (**[À compléter : stack, type d’index, paramètres de chunking, stratégie de retrieval/reranking, contraintes RGPD]**).

Deux points méritent déjà d’être soulignés car ils ont un impact direct sur la qualité :

- **le chunking** n’est pas un détail d’ingénierie. Il détermine l’unité de preuve (ce qui peut être cité), la granularité du retrieval et la capacité à capturer une règle complète.
- **la construction du contexte** (prompt) conditionne la manière dont le modèle utilise les sources : ordre des passages, nombre maximum de tokens, règles de citation, consignes de non-invention.

#### 2.3.1. Chunking : segmentation, unités de preuve et compromis

Le chunking est souvent décrit comme un paramètre « d’ingestion », mais il correspond en réalité à un choix de modélisation : **quelle est l’unité minimale de connaissance** que le système peut retrouver et citer ?

On peut distinguer plusieurs logiques de segmentation :

- **Segmentation structurelle** (titres, sections, listes) : adaptée aux procédures et aux référentiels, car elle suit la logique documentaire.
- **Segmentation à longueur fixe** : robuste et simple, mais peut casser des définitions ou séparer condition/exception.
- **Segmentation thématique** (topic segmentation) : vise à découper selon des ruptures de sujet ; des approches classiques existent (ex. TextTiling).[^Hearst1997]

Le chunking influence directement :

- le **rappel** (chunks trop gros : moins d'unités, risque de dilution ; chunks trop petits : manque de contexte),
- la **citabilité** (capacité à relier une affirmation à un extrait précis),
- la **gestion des contradictions** (contradictions détectables si les unités sont comparables).

Ces aspects seront étudiés empiriquement dans la PARTIE III (comparaisons de chunking).

### 2.4. Les avantages du RAG

Les bénéfices attendus d’un RAG en contexte documentaire sont généralement :

- **Réduction des hallucinations** : le modèle est incité à s’appuyer sur des sources explicites.
- **Traçabilité** : possibilité de fournir des extraits et références de documents.
- **Connaissances privées** : exploitation d’un corpus interne sans l’exposer publiquement.
- **Actualisation simple** : mise à jour de l’index documentaire plutôt que réentraînement.
- **Auditabilité** : compréhension a posteriori de *pourquoi* une réponse a été produite (via les passages récupérés).
- **Coût** : souvent inférieur à un fine-tuning complet, notamment si l’on optimise le retrieval.

Au niveau des usages, un RAG est particulièrement adapté quand :

- les connaissances évoluent (mises à jour de procédures),
- la source doit être **traçable** (audit, conformité),
- le corpus est **privé** (contraintes de confidentialité),
- l’utilisateur attend une réponse synthétisée, pas seulement des liens.

### 2.5. Les défis du RAG : bruit, contradictions et cohérence

Malgré ses avantages, le RAG introduit des difficultés propres :

- **Bruit documentaire** : chunks hors-sujet mais lexicalement proches, ou sémantiquement proches mais non applicables.
- **Contradictions** : documents obsolètes vs documents à jour, variantes locales, exceptions.
- **Dépendance au chunking** : une mauvaise segmentation peut casser le sens ou disperser une règle sur plusieurs passages.
- **Latence** : l’étape de retrieval/reranking ajoute du temps.
- **Cohérence globale** : même avec de bons passages, la réponse peut être incohérente, trop générale, ou omettre une exception critique.

Ces points justifient une évaluation qui couvre à la fois la **qualité du retrieval** et la **qualité de la réponse générée** (fidélité, cohérence, couverture).

Plusieurs variantes d’architectures ont été proposées pour adresser ces défis :

- **RAG “classique”** (Lewis et al.) qui couple un retriever dense et un générateur seq2seq.[^Lewis2020]
- **REALM** (retrieval pré-entraîné) qui intègre la récupération dans l’objectif de pré-formation.[^Guu2020]
- **Fusion-in-Decoder (FiD)** qui concatène plusieurs passages et laisse le décodeur fusionner l’information, améliorant souvent la QA multi-passage.[^IzacardGrave2021]

Ces travaux illustrent une même tension : plus on donne de passages au générateur, plus on augmente le rappel potentiel, mais plus on augmente aussi le risque de **contradictions**, de **dilution** du contexte et de coûts/latence.

#### 2.5.1. Multi-étage retrieval + reranking : un standard pratique

En pratique, les systèmes robustes adoptent souvent une architecture *multi-stage* :

1. un **retrieval large** (top-$k$ élevé) pour maximiser le rappel,
2. un **reranking** (souvent cross-encoder) pour augmenter la précision des passages retenus,
3. une **sélection/assemblage** finale pour respecter la limite de contexte du modèle de génération.

Le reranking de passages avec BERT a montré très tôt qu’un cross-encoder en second étage améliore fortement la qualité des premiers résultats, au prix d’un coût d’inférence qui reste acceptable si on ne reranke qu’un petit ensemble candidat.[^NogueiraCho2019]

Dans un RAG, ces choix ont un effet direct sur la fidélité :

- un retrieval trop large sans reranking augmente le bruit,
- un reranking mal calibré peut favoriser des passages « proches » mais moins normatifs,
- une sélection trop agressive peut omettre une exception critique.

#### 2.5.2. Contradictions documentaires : versioning, autorité et arbitrage

Les contradictions ne sont pas uniquement un artefact de génération : elles peuvent refléter la réalité du corpus (versions, variantes, documents obsolètes). Un RAG doit donc être évalué sur sa capacité à :

- **identifier** les contradictions (ou au moins ne pas les masquer),
- **arbitrer** selon des règles (autorité, date, périmètre),
- **rendre visible** l’incertitude (citer plusieurs sources, demander clarification, ou refuser).

Cette dimension est particulièrement importante en HSE, où une réponse erronée « tranchée » est souvent plus dangereuse qu’une réponse prudente.

### 2.6. « Grounding », citations et attribution : de la preuve à la confiance

Dans un RAG industriel, la présence de sources n’est utile que si :

1. les passages cités sont réellement pertinents (sinon, *fausse* traçabilité),
2. la réponse est fidèle aux passages (sinon, *citation décorative*),
3. la granularité de citation permet une vérification (chunk trop grand, difficile à auditer).

Cela amène à distinguer :

- **context relevance** : le contexte récupéré est-il pertinent pour répondre ?
- **answer relevance** : la réponse répond-elle à la question ?
- **faithfulness / groundedness** : la réponse est-elle supportée par le contexte ?

Ces dimensions se retrouvent dans plusieurs propositions de métriques et frameworks d’évaluation dédiés au RAG (voir Chapitre 3).

### 2.7. RAG et mémoire : connaissances paramétriques vs non-paramétriques

Une manière utile de situer le RAG est d’opposer deux formes de « mémoire » :

- **mémoire paramétrique** : connaissances stockées dans les poids du modèle (LLM utilisé seul),
- **mémoire non-paramétrique** : connaissances stockées dans une base externe (documents + index), interrogée à la volée (RAG).

Des travaux sur le *closed-book QA* ont montré qu’un modèle pouvait emmagasiner une quantité significative de connaissances factuelles dans ses paramètres, mais avec des limites en actualisation et en vérifiabilité.[^Roberts2020]

Les approches retrieval-augmented existent aussi au niveau du pré-entraînement : RETRO, par exemple, introduit une récupération de voisins textuels pendant la génération, ce qui améliore certaines capacités tout en posant des enjeux d’ingénierie et de gouvernance des sources.[^Borgeaud2022]

Dans un cadre industriel, le RAG est souvent préféré précisément parce qu’il rend la « mémoire » **auditable** et **mise à jour** sans réentraînement.

### 2.8. Pourquoi la notion de « source » est centrale en contexte HSE

Dans une application HSE, l’utilisateur attend rarement une réponse « créative » : il attend une réponse **normative** (ce qui est exigé) ou **procédurale** (ce qu’il faut faire). La qualité dépend donc fortement :

- de la capacité du système à privilégier les documents à **autorité** (procédure validée vs note informelle),
- de la capacité à respecter les **modalités** (obligation/recommandation/interdiction),
- de la capacité à expliciter les **conditions** (cas où la règle s’applique).

Ce cadre motive une évaluation centrée sur la fidélité aux sources et sur la gestion des exceptions.

## Chapitre 3 — La question de la « pertinence » et de la « cohérence »

Ce chapitre propose un cadre conceptuel pour clarifier les notions qui seront opérationnalisées dans la PARTIE II. Dans un RAG, la qualité perçue par l’utilisateur dépend d’un enchaînement de décisions : (i) quels passages sont récupérés, (ii) comment ils sont assemblés, (iii) comment le modèle les utilise pour produire une réponse.

### 3.1. Définir la pertinence : une notion multi-dimensionnelle

En recherche d’information, la pertinence n’est pas une propriété absolue d’un document : c’est une relation entre **un besoin**, **un utilisateur**, **un contexte**, **un document** (ou passage), à un moment donné. La littérature insiste depuis longtemps sur le caractère multi-facette de la pertinence et sur l’écart entre pertinence « système » et pertinence « utilisateur ».[^Saracevic1996][^Mizzaro1997]

On peut distinguer plusieurs dimensions utiles pour un système RAG :

#### 3.1.1. Pertinence topique (thématique)

Il s’agit de l’adéquation entre le sujet de la requête et celui du passage récupéré. Un passage peut être topiquement pertinent mais insuffisant pour répondre (ex. introduction générale à une procédure).

#### 3.1.2. Pertinence situationnelle (utilité)

Elle mesure si l’information est actionnable pour l’utilisateur dans son contexte. En HSE, le contexte (chantier, rôle, phase de travaux, contraintes de site) modifie fortement l’utilité.

#### 3.1.3. Exhaustivité / couverture

Une réponse peut être correcte mais incomplète : omission d’une étape, d’une exception, ou d’une condition de sécurité. L’exhaustivité est centrale lorsque l’utilisateur cherche une procédure ou une règle complète.

#### 3.1.4. Granularité

Le niveau de détail doit être adapté : trop général (risque d’ambiguïté), trop détaillé (risque de noyer l’information critique). La granularité dépend aussi du format attendu (résumé, check-list, procédure pas-à-pas).

#### 3.1.5. Actualité

Dans un corpus vivant (procédures mises à jour, retours d’expérience, normes), l’actualité doit être prise en compte : un passage peut être pertinent mais obsolète.

#### 3.1.6. Autorité / fiabilité de la source

Les documents n’ont pas la même force normative : procédure entreprise validée, note interne, support de formation, document fournisseur, etc. Cette dimension est clé pour la gouvernance et pour la confiance.

#### 3.1.7. Pertinence « interactive » : rôle de l’utilisateur et du contexte

Une limite des évaluations purement offline est qu’elles ignorent souvent l’interaction : l’utilisateur reformule, lit les sources, change de stratégie, et l’utilité dépend de ce processus. Les approches d’**Interactive Information Retrieval (IIR)** mettent l’accent sur le contexte et la situation d’usage, et proposent des protocoles centrés sur les tâches plutôt que sur des jugements isolés.[^IngwersenJarvelin2005][^Borlund2003]

Pour un assistant de type ScribBERT, cela suggère de compléter l’évaluation automatique par des signaux d’usage : taux de reformulation, temps pour obtenir une réponse utile, confiance perçue, et cas où l’utilisateur doit escalader vers un expert.

### 3.2. Définir la cohérence : du texte à la fidélité aux sources

Dans le contexte des LLMs, la cohérence est souvent abordée sous l’angle de la fluidité textuelle. Pour un RAG, cette définition est insuffisante : une réponse peut être très fluide mais factuellement fausse.

Il est utile de distinguer trois notions proches mais différentes :

- **Cohérence textuelle** : le texte « se tient » linguistiquement.
- **Factualité** : les propositions sont vraies dans le monde (ou au moins dans le cadre documentaire).
- **Fidélité / groundedness** : les propositions sont justifiées par les sources fournies.

Dans un RAG, la fidélité aux sources est souvent plus importante que la factualité absolue : on attend que le système ne dépasse pas ce que le corpus permet d’affirmer.

On propose de distinguer :

#### 3.2.1. Cohérence locale (linguistique)

La réponse doit être lisible et enchaînée correctement : connecteurs, anaphores, absence de contradictions phrase-à-phrase. Cette cohérence est généralement bien maîtrisée par les LLMs modernes.

La cohérence locale peut néanmoins se dégrader lorsque : (i) le contexte contient des passages hétérogènes, (ii) le prompt impose un format strict (check-list) ou (iii) la longueur de réponse augmente. Des travaux sur la cohérence discursive (ex. entity grid) ont montré que la cohérence peut être modélisée et évaluée explicitement, même si ces approches ne se transposent pas directement au RAG moderne.[^BarzilayLapata2008]

#### 3.2.2. Cohérence globale (discursive)

La réponse doit suivre une structure logique : poser le cadre, donner la règle, préciser les conditions, exceptions, et conclure par une recommandation. La cohérence globale est plus fragile, notamment pour des réponses longues.

La cohérence globale renvoie aussi à des notions de **structure discursive** (relations entre segments : élaboration, contraste, justification). Des cadres comme la *Rhetorical Structure Theory (RST)* proposent une formalisation de ces relations et constituent un arrière-plan théorique pour penser la structure d’un texte.[^MannThompson1988]

Au niveau linguistique, on peut aussi distinguer la cohérence (organisation du sens) de la **cohésion** (marqueurs linguistiques : connecteurs, reprises, référents), classiquement discutée dans les travaux de linguistique textuelle.[^HallidayHasan1976]

#### 3.2.3. Fidélité factuelle aux sources (faithfulness / groundedness)

Dimension centrale en RAG : les affirmations de la réponse doivent être supportées par les passages récupérés. Une réponse est dite *grounded* si l’on peut relier ses éléments à des extraits du corpus.

Cette fidélité peut être compromise par :

- une récupération partielle (manque d’un passage critique),
- une mauvaise attribution (la réponse mélange deux sources),
- une paraphrase qui modifie le sens normatif,
- une sur-généralisation à partir d’un cas particulier.

Une difficulté spécifique aux textes normatifs est la **modalité** : une reformulation peut transformer un « doit » en « peut », ou une recommandation en obligation. Dans une évaluation, cela implique de vérifier non seulement les faits, mais aussi la conformité des modalités et conditions.

#### 3.2.4. Stabilité / reproductibilité

À requête identique, et à corpus constant, le système doit produire des réponses proches (ou au moins cohérentes), surtout en contexte HSE où la variabilité peut être perçue comme un manque de fiabilité. La stabilité dépend de la stochasticité du modèle (température), du retrieval (approximation ANN) et d’éventuelles reformulations.

La stabilité est aussi un enjeu méthodologique : si l’output varie fortement, on peut difficilement comparer des variantes (chunking, top-$k$) sans multiplier les répétitions et rapporter des distributions de scores.

#### 3.2.5. Cohérence terminologique et réglementaire

La réponse doit utiliser un vocabulaire métier stable et éviter les formulations ambiguës. Elle doit aussi respecter les contraintes réglementaires et internes (normes, procédures, interdictions), sans inventer des obligations.

### 3.3. Définir la fiabilité : une synthèse opératoire

Le titre de ce mémoire associe les notions de **cohérence** et de **fiabilité**. Si la cohérence vient d'être définie ci-dessus, la fiabilité mérite une clarification spécifique car elle est plus large : c'est la **propriété d'un système à produire de manière constante des réponses dignes de confiance**.

Pour les besoins de ce mémoire, on adopte la définition opératoire suivante :

> **Fiabilité d'un RAG = pertinence du retrieval + fidélité aux sources (factualité) + stabilité/répétabilité des réponses + traçabilité auditable.**

Cette définition présente trois intérêts :

1. Elle **décompose la fiabilité en dimensions mesurables**, ce qui permet d'organiser le protocole d'évaluation (Chapitre 5) autour de chacune.
2. Elle **distingue la cohérence (propriété intrinsèque d'une réponse) de la fiabilité (propriété systémique)** : une réponse peut être cohérente une fois et incohérente la suivante ; un système n'est fiable que si ses réponses sont cohérentes *de manière reproductible*.
3. Elle **inclut explicitement la traçabilité**, dimension non couverte par les métriques classiques mais essentielle dans un cadre industriel (auditabilité, conformité).

Le Chapitre 5 instancie cette définition sous forme de critères d'évaluation, et le Chapitre 6 traite spécifiquement la dimension **stabilité/répétabilité**, peu couverte par les métriques d'évaluation usuelles.

### 3.4. Pertinence perçue vs pertinence mesurée

La qualité d’un système se mesure à deux niveaux :

- **Mesures automatiques** (métriques IR, similarité, scores de fidélité) : utiles pour comparer des variantes, mais parfois mal corrélées au jugement humain.
- **Perception utilisateur** (confiance, satisfaction, effort) : essentielle pour l’adoption, mais plus coûteuse et plus subjective.

Un protocole robuste combine souvent les deux (triangulation), en exploitant les métriques comme instruments de diagnostic, et l’évaluation humaine pour valider la pertinence réelle et la sécurité.

Sur le plan méthodologique, cela rejoint l’idée de séparer :

- **évaluation intrinsèque** : mesurer des propriétés internes (qualité des embeddings, séparation positives/négatives, rappel retrieval),
- **évaluation extrinsèque** : mesurer l’effet sur la tâche finale (qualité de réponse, temps de recherche, erreurs évitées).

### 3.5. Travaux récents sur l’évaluation des RAG et LLMs augmentés

L’évaluation des systèmes RAG s’est structurée autour de plusieurs axes :

1. **Évaluation retrieval** : métriques classiques (Recall@k, nDCG, MRR) sur des jeux de test annotés.[^JarvelinKekalainen2002]
2. **Évaluation génération** : métriques de similarité (BLEU/ROUGE) peu adaptées à la QA ouverte ; métriques sémantiques (BERTScore, BLEURT) ; métriques de factualité (ex. TruthfulQA, FactScore) visant à quantifier l’alignement factuel des sorties.[^Lin2021TruthfulQA][^Min2023FactScore]
3. **Évaluation « end-to-end »** : frameworks dédiés au RAG (ex. RAGAS, TruLens, LangSmith) qui tentent de décomposer la qualité en sous-scores (context relevance, answer relevance, faithfulness, citation, etc.).
4. **LLM-as-judge** : utiliser un LLM pour noter des réponses selon une grille (G-Eval, Prometheus). Puissant mais nécessite une gouvernance stricte (biais, fuite d’informations, reproductibilité).

Les benchmarks de retrieval généralistes (BEIR) et les *leaderboards* d’embeddings (MTEB) ont également contribué à standardiser la comparaison de modèles et à clarifier l’écart entre performance sur des tâches « web » et performance sur des corpus spécialisés.[^Thakur2021BEIR][^Muennighoff2023MTEB]

Pour la génération, plusieurs métriques basées sur des modèles pré-entraînés se sont imposées :

- **BERTScore** pour mesurer une similarité sémantique token-level.[^Zhang2020BERTScore]
- **BLEURT** comme score appris de similarité/qualité.[^Sellam2020BLEURT]

Cependant, ces métriques ne suffisent pas à capturer la fidélité aux sources. C’est pourquoi des travaux récents sur la factualité/hallucination (ex. en résumé) sont souvent mobilisés comme base conceptuelle.[^Maynez2020][^Ji2023]

Un point récurrent dans la littérature est l’écart entre :

- la performance IR (retrieval correct) et
- la performance de génération (usage correct des sources).

Autrement dit, un bon retrieval ne garantit pas une réponse fidèle, et une réponse fluide ne garantit pas qu’elle soit vraie.

Dans le cas d’un RAG, l’évaluation pertinente doit idéalement être **décomposable** : elle doit permettre de dire *où* se situe l’échec (retrieval, reranking, prompt, génération) et pas seulement constater que l’output final est « bon » ou « mauvais ».

#### 3.5.1. Formaliser quelques métriques retrieval (rappels utiles)

Pour expliciter la suite, on rappelle des définitions courantes sur un ensemble de requêtes $Q$. On note $\mathrm{TopK}(q)$ l’ensemble des $k$ premiers passages récupérés pour la requête $q$, et $\mathrm{Rel}(q)$ l’ensemble des passages pertinents (selon l’annotation).

- **Recall@k** :

$$\mathrm{Recall@k} = \frac{1}{|Q|}\sum_{q\in Q} \frac{|\mathrm{Rel}(q) \cap \mathrm{TopK}(q)|}{|\mathrm{Rel}(q)|}$$

- **MRR** (Mean Reciprocal Rank), utile quand on attend *au moins un bon passage* parmi les premiers résultats :

$$\mathrm{MRR} = \frac{1}{|Q|}\sum_{q\in Q} \frac{1}{\mathrm{rank}_q}$$

où $\mathrm{rank}_q$ est le rang du premier document pertinent.

- **nDCG@k** (pertinence graduée), qui pénalise moins fortement un document pertinent placé en position 2 qu’en position 20 :

$$\mathrm{DCG@k} = \sum_{i=1}^{k} \frac{2^{rel_i}-1}{\log_2(i+1)}\quad;\quad \mathrm{nDCG@k}=\frac{\mathrm{DCG@k}}{\mathrm{IDCG@k}}$$

Ces métriques sont au cœur de l’IR évaluative moderne.[^JarvelinKekalainen2002]

L’intérêt pour le RAG est de relier ces scores à la qualité finale : par exemple, un Recall@k faible limite mécaniquement la fidélité, car la preuve n’entre jamais dans le contexte.

### 3.6. Positionnement de la contribution du mémoire

Dans ce mémoire, l’enjeu est de proposer un cadre d’évaluation qui :

- sépare clairement les erreurs de retrieval et les erreurs de génération,
- prend en compte les spécificités du contexte HSE (criticité, exceptions, autorité des sources),
- reste reproductible et applicable sur un corpus d’entreprise,
- fournit des diagnostics actionnables (quels paramètres améliorer : chunking, top-k, reranking, prompt, température, filtres).

La PARTIE II présentera la méthodologie et les métriques retenues, puis la PARTIE III appliquera ce protocole au cas ScribBERT.

---

# PARTIE II — Méthodologie d'évaluation d'un système RAG

La Partie I a posé le cadre conceptuel : qu'est-ce qu'un RAG, qu'est-ce que la pertinence, qu'est-ce que la cohérence, et pourquoi ces notions sont particulièrement délicates en contexte HSE. La Partie II opérationnalise ce cadre en répondant à trois questions :

1. **Quels sont les leviers techniques** qui influencent la qualité d'un RAG, et comment les caractériser indépendamment du cas d'usage (Chapitre 4) ?
2. **Quel protocole d'évaluation** mettre en place pour mesurer cette qualité de manière reproductible et diagnostique (Chapitre 5) ?
3. **Comment évaluer spécifiquement la cohérence** (au sens de fidélité aux sources et de stabilité), qui constitue la dimension la plus difficile à automatiser (Chapitre 6) ?

L'ambition est méthodologique : proposer un cadre transférable, qui ne soit pas spécifique à ScribBERT mais qui sera instancié sur ce cas en Partie III.

## Chapitre 4 — Modèles et paramètres influençant la performance

Un système RAG n'est pas une « boîte noire » à un seul réglage : c'est un assemblage de composants dont chacun expose des leviers (modèles, hyperparamètres, stratégies). Pour évaluer un RAG de manière utile, il faut d'abord cartographier ces leviers, comprendre leurs effets attendus, et identifier ceux qui méritent d'être testés expérimentalement.

Quatre familles de leviers structurent ce chapitre :

1. les **modèles d'embedding** (représentation des chunks et requêtes),
2. le **chunking et le prétraitement** (granularité et qualité des unités indexées),
3. les **stratégies de retrieval** (méthode de récupération et de reclassement),
4. la **composante de génération** (modèle de langage, prompt, paramètres de décodage).

### 4.1. Les modèles d'embedding

Le modèle d'embedding est la pierre angulaire d'un RAG dense : c'est lui qui détermine la géométrie de l'espace dans lequel requêtes et passages sont comparés. Un mauvais embedding ne peut pas être compensé en aval.

#### 4.1.1. Typologie des modèles disponibles

On peut grouper les modèles d'embedding actuellement disponibles en plusieurs familles :

- **Modèles open-source dérivés de BERT et SBERT** : famille `sentence-transformers` (`all-MiniLM-L6-v2`, `all-mpnet-base-v2`, etc.), qui constitue une référence open-source largement utilisée.[^ReimersGurevych2019]
- **Modèles multilingues open-source** : `multilingual-e5` (Microsoft), `BGE-M3` (BAAI), `Jina embeddings v3`, qui visent à couvrir un grand nombre de langues avec un seul modèle.
- **Modèles français ou multilingues spécialisés** : `Solon` (Lajavaness), `CamemBERT`-based encoders, `Sentence-CamemBERT`, particulièrement pertinents pour un corpus francophone comme celui de Bouygues TP.
- **Modèles propriétaires accessibles par API** : `text-embedding-3-small/large` (OpenAI), `embed-multilingual-v3` (Cohere), `voyage-3` (Voyage AI), `gemini-embedding` (Google). Performants mais soulèvent des questions de coût, latence et confidentialité.
- **Modèles spécialisés par domaine** : `LegalBERT`, `BioBERT`, `SciBERT`, etc. À ce jour, **aucun modèle d'embedding open-source spécialisé HSE/BTP** n'est librement disponible, ce qui constitue à la fois une limite et une opportunité (fine-tuning interne envisageable).

#### 4.1.2. Dimensions d'embedding : compromis qualité / coût

La dimension de sortie d'un modèle d'embedding ($d \in \{384, 512, 768, 1024, 1536, 3072\}$ pour les plus courants) influence trois aspects :

- **la qualité représentationnelle** : à modèle donné, une dimension plus élevée *peut* mieux séparer les concepts, mais ce n'est pas systématique ;
- **le coût de stockage** : un index de $N$ chunks en `float32` occupe $4 \cdot N \cdot d$ octets (ex. : 1 M chunks en dim. 1024 ≈ 4 Go) ;
- **la latence de recherche** : croît linéairement avec $d$ pour la similarité, et indirectement via la taille de l'index ANN.

Les **embeddings « Matryoshka »** (Matryoshka Representation Learning) permettent de tronquer la dimension a posteriori avec une perte limitée, offrant un curseur qualité/coût ajustable sans réindexation complète.

#### 4.1.3. Multilinguisme et adaptation au français technique

Le corpus de ScribBERT est essentiellement francophone, avec des passages en anglais (normes, fournisseurs internationaux). Trois stratégies sont envisageables :

1. **Modèle français pur** : meilleure qualité sur le français standard, mais limité sur le code-switching et les termes anglais.
2. **Modèle multilingue généraliste** : robuste sur plusieurs langues, mais souvent moins fin sur les nuances techniques d'une langue donnée.
3. **Modèle multilingue de grande taille avec instruction tuning** : tendance récente (E5, BGE), qui combine couverture linguistique et qualité.

Le benchmark **MTEB** (Massive Text Embedding Benchmark) fournit une comparaison standardisée entre modèles, mais il faut se rappeler que les performances **MTEB ne se transposent pas mécaniquement** à un domaine spécialisé.[^Muennighoff2023MTEB] Le benchmark **BEIR** a clairement montré la dégradation hors-domaine des retrievers entraînés sur du web généraliste.[^Thakur2021BEIR]

#### 4.1.4. Évaluation intrinsèque vs extrinsèque

On distingue deux niveaux d'évaluation pour un modèle d'embedding :

- **Intrinsèque** : qualité de la séparation paires positives / négatives (STS, retrieval@k sur jeux annotés, alignement avec jugements humains) ;
- **Extrinsèque** : impact sur la tâche aval (qualité de la réponse RAG finale).

Les deux ne coïncident pas toujours : un embedding qui remonte « les bons documents » peut tout de même conduire à une mauvaise réponse si le générateur exploite mal le contexte. C'est une raison supplémentaire pour évaluer les composants **et** la chaîne complète (cf. Chapitre 5).

#### 4.1.5. Critères de sélection en contexte industriel

En contexte d'entreprise, le choix d'un modèle d'embedding ne se résume pas à un score sur un benchmark. Une grille de décision multi-critères est nécessaire :

| Critère | Question |
|---------|----------|
| **Qualité retrieval** | Recall@k sur le corpus de test interne |
| **Couverture linguistique** | Le modèle gère-t-il le français technique et l'anglais normatif ? |
| **Coût** | API payante (OpenAI, Cohere) ou auto-hébergé (GPU) ? Coût marginal par requête ? |
| **Latence** | Temps d'inférence acceptable pour une expérience temps réel (< 200 ms cible) |
| **Confidentialité** | Le modèle peut-il être hébergé en interne ? Les requêtes peuvent-elles sortir du SI ? |
| **Maintenance** | Stabilité du fournisseur, fréquence des mises à jour, risques de breaking changes |
| **Fine-tunabilité** | Possibilité d'adapter le modèle au domaine HSE si nécessaire |

Ces critères seront opérationnalisés sur ScribBERT en Partie III.

### 4.2. Le rôle du chunking et du prétraitement textuel

Comme évoqué au Chapitre 2, le chunking est un choix de modélisation déguisé en choix d'ingénierie. Cette section approfondit les leviers concrets.

#### 4.2.1. Stratégies de chunking

On peut classer les approches en quatre familles :

- **Chunking à taille fixe** (par tokens ou caractères) : simple, prévisible, mais aveugle à la structure. Risque majeur : couper une règle au milieu d'une phrase, ou séparer une condition de son exception.
- **Chunking récursif** (*recursive character text splitter*) : tente de découper d'abord sur des séparateurs « forts » (`\n\n`, `\n`, `. `, ` `) avant de tomber sur du caractère brut. Bon compromis par défaut, implémenté dans LangChain/LlamaIndex.
- **Chunking structurel** : exploite la hiérarchie documentaire (titres, sections, listes, tableaux). Particulièrement adapté aux référentiels normatifs qui ont une structure claire.
- **Chunking sémantique** : utilise un modèle (souvent un embedder) pour détecter des ruptures de sujet et grouper les phrases sémantiquement proches. Plus coûteux en ingestion, gain variable.
- **Chunking custom (regex / parser dédié)** : pour des formats spécifiques (procédures avec format imposé, fiches sécurité), un parser dédié peut extraire des unités cohérentes (un § = une règle).

Pour un corpus HSE, la stratégie structurelle ou custom est souvent la plus pertinente, car les règles ont une granularité naturelle (article, paragraphe numéroté, étape de procédure).

#### 4.2.2. Taille des chunks et overlap

Deux paramètres clés interagissent :

- **Taille du chunk** ($T$, en tokens) : trop petit ⇒ perte de contexte, ambiguïté, perte de l'antécédent (« il », « cette règle ») ; trop grand ⇒ dilution sémantique, *embedding* moins discriminant, contexte LLM saturé.
- **Overlap** ($O$, généralement 10–20 % de $T$) : permet d'amortir les coupures malheureuses au prix d'une redondance dans l'index.

L'optimum dépend du type de question : les questions factuelles tolèrent des chunks petits, les questions procédurales (« comment faire X ? ») requièrent souvent des chunks plus larges. Un protocole rigoureux **teste plusieurs configurations** ($T \in \{256, 512, 1024\}$, $O \in \{0, 64, 128\}$) et mesure l'impact end-to-end.

#### 4.2.3. Préservation de la structure et des métadonnées

Un chunk « brut » (texte seul) perd des informations critiques : section d'origine, niveau hiérarchique, type de document, date de validité, autorité émettrice. Or ces métadonnées :

- enrichissent les **filtres de retrieval** (« uniquement procédures validées » / « documents postérieurs à 2023 ») ;
- permettent de **citer correctement** la source dans la réponse ;
- aident à **arbitrer les contradictions** (préférer la version la plus récente, le plus haut niveau d'autorité).

Un schéma de métadonnées robuste pour ScribBERT pourrait inclure : `document_id`, `titre`, `section`, `niveau_hierarchique`, `type` (procédure, standard, REX, support), `autorité` (groupe / filiale / chantier), `date_validation`, `date_obsolescence`, `langue`, `périmètre_geographique`.

#### 4.2.4. Nettoyage et normalisation

Le prétraitement comprend :

- **Extraction texte** depuis PDF (couches texte natives, OCR pour scans), Word, HTML. Les PDFs techniques posent des problèmes spécifiques : multi-colonnes, tableaux, schémas avec légendes, en-têtes/pieds de page répétitifs. Des outils comme `Unstructured`, `pdfplumber`, `pymupdf` ou `Marker` ont des compromis différents.
- **Suppression du bruit** : numéros de page, en-têtes répétés, watermarks, références internes type « voir page 12 ».
- **Normalisation** : unification des guillemets, des espaces insécables, des tirets ; éventuellement passage en minuscules pour le sparse retrieval (mais pas pour les embeddings, qui sont généralement *case-sensitive*).
- **Conservation du formatage utile** : listes à puces, numérotation hiérarchique, gras pour les termes-clés.

Un point souvent négligé : les **tableaux** et les **schémas**. Linéariser un tableau en texte brut détruit sa structure. Des stratégies plus avancées (extraction structurée, légendes générées par un VLM, tableaux convertis en markdown) peuvent être étudiées **[À développer en Partie III selon les choix faits sur ScribBERT]**.

### 4.3. Les stratégies de retrieval

Une fois l'index constitué, le retrieval comporte plusieurs leviers : choix de la similarité, hybridation sparse/dense, reranking, filtrage, expansion de requête, valeur de $k$.

#### 4.3.1. Similarité cosinus et alternatives

La similarité cosinus est la mesure par défaut pour comparer deux embeddings :

$$\mathrm{sim}(q, d) = \frac{\mathbf{e}_q \cdot \mathbf{e}_d}{\|\mathbf{e}_q\| \cdot \|\mathbf{e}_d\|}$$

Elle suppose que **seule la direction** des vecteurs porte le sens (pas la norme). La plupart des modèles modernes sont entraînés sous cette hypothèse (vecteurs L2-normalisés), ce qui rend cosinus et produit scalaire équivalents.

Limites : le cosinus est une mesure **isotrope** qui ne tient pas compte de la structure locale de l'espace. Des travaux sur les *anisotropic embeddings* montrent que certains modèles concentrent leurs vecteurs dans un cône étroit, ce qui dégrade la séparation.

#### 4.3.2. Hybrid search : combiner sparse et dense

L'hybridation BM25 + dense est devenue un standard de fait. Deux stratégies :

- **Combinaison de scores** : $\mathrm{score} = \alpha \cdot \mathrm{score}_{\text{dense}} + (1-\alpha) \cdot \mathrm{score}_{\text{sparse}}$, avec $\alpha \in [0,1]$ à régler.
- **Reciprocal Rank Fusion (RRF)** : $\mathrm{RRF}(d) = \sum_i \frac{1}{k + r_i(d)}$, qui combine les rangs et non les scores (plus robuste à des échelles hétérogènes).

L'hybridation est particulièrement utile sur des corpus techniques où :
- le **dense** capture les paraphrases et l'intention,
- le **sparse** garantit le rappel sur des **identifiants exacts** (numéros de procédure, codes EPI, références normatives).

Pour ScribBERT, l'hypothèse forte est qu'un utilisateur citant explicitement « PR-SST-042 » doit retrouver ce document, ce que BM25 garantit mais qu'un dense pur peut manquer. Cette hypothèse sera testée en Partie III.

#### 4.3.3. Reranking par cross-encoder

Le reranking consiste à appliquer un modèle plus précis (et plus coûteux) à un petit ensemble de candidats déjà récupérés. Les cross-encoders (ex. `ms-marco-MiniLM`, `bge-reranker-v2-m3`, `Cohere Rerank`) lisent **conjointement** la requête et le passage et produisent un score de pertinence finement calibré.[^NogueiraCho2019]

Pipeline typique :

1. Retrieval initial → top-100 candidats (rapide, $O(\log N)$ sur HNSW),
2. Reranking → top-10 (lent : 100 inférences cross-encoder, $\sim$ 100–500 ms),
3. Génération sur top-10 (ou top-5).

Le gain de qualité est souvent **substantiel** mais le coût en latence est non négligeable. Le compromis dépend de la criticité de l'application.

#### 4.3.4. Filtrage par métadonnées

Le filtrage permet de restreindre la recherche selon des contraintes structurelles :

- **Pré-filtrage** : appliquer le filtre **avant** la recherche vectorielle (ex. uniquement les documents validés et postérieurs à 2023).
- **Post-filtrage** : récupérer puis filtrer (plus simple, mais peut vider le top-k).

Un pré-filtrage trop strict peut éliminer les bons passages ; un post-filtrage trop tardif gaspille du calcul. Les bases vectorielles modernes (Qdrant, Weaviate, Pinecone) optimisent le pré-filtrage.

Pour ScribBERT, des filtres pertinents incluent : périmètre géographique (chantier France vs international), niveau d'autorité (groupe vs filiale), type de document (procédure vs REX vs formation).

#### 4.3.5. Choix de $k$ : compromis rappel / bruit / coût

La valeur du top-$k$ retourné au générateur a un effet en U inversé :

- $k$ trop petit : la « bonne » preuve n'est pas dans le contexte ⇒ génération erronée ou « je ne sais pas ».
- $k$ trop grand : dilution, bruit, coûts ↑ (tokens consommés, latence), risque de **lost in the middle** (le LLM ignore les passages au milieu du contexte).

Valeurs typiques : $k \in [3, 10]$ après reranking. La valeur optimale dépend du modèle de génération (les LLMs récents avec contexte long tolèrent mieux $k$ élevé) et du type de question.

#### 4.3.6. Query expansion et reformulation

Plusieurs techniques visent à enrichir ou reformuler la requête :

- **HyDE** (*Hypothetical Document Embeddings*) : faire générer par un LLM une réponse hypothétique à la requête, puis utiliser son embedding pour la recherche. Améliore le rappel sur des questions complexes.
- **Multi-query** : générer plusieurs reformulations de la requête, lancer plusieurs recherches, fusionner les résultats.
- **Step-back prompting** : reformuler la requête en une question plus générale, qui peut mieux matcher des passages introductifs.
- **Query rewriting via LLM** : corriger les fautes, expanser les acronymes (« EPI » → « équipement de protection individuelle »), normaliser le vocabulaire.

Ces techniques améliorent généralement le rappel mais ajoutent de la latence et peuvent introduire du **drift sémantique** (la reformulation s'éloigne de l'intention initiale). Un protocole d'évaluation rigoureux doit mesurer le gain net.

### 4.4. La composante de génération

Une fois les passages sélectionnés, la génération transforme le contexte en réponse. Plusieurs leviers conditionnent la qualité.

#### 4.4.1. Choix du LLM

Les options se classent en trois catégories :

- **LLMs propriétaires (API)** : GPT-4 / GPT-4o (OpenAI), Claude 3.5/4 (Anthropic), Gemini (Google), Mistral Large. Excellente qualité, coût marginal par requête, dépendance à un fournisseur externe et contraintes de confidentialité.
- **LLMs open-weights auto-hébergés** : Llama 3, Mistral / Mixtral, Qwen, DeepSeek, Gemma. Contrôle total des données, coût d'infrastructure (GPU), qualité en progression rapide.
- **LLMs spécialisés** : modèles plus petits fine-tunés sur un domaine (ex. modèles biomédicaux). À ce jour, peu d'options HSE/BTP.

Pour un cas d'usage interne avec contraintes de confidentialité, les LLMs auto-hébergés sont souvent privilégiés. Le compromis est qualité ↔ coût ↔ contrôle.

#### 4.4.2. Engineering du prompt

Un prompt RAG contient classiquement quatre éléments :

1. **Instructions système** : rôle, contraintes (« tu es un assistant santé-sécurité »), règles de comportement (« ne réponds que sur la base des sources fournies »).
2. **Requête utilisateur** : la question telle que posée (éventuellement reformulée).
3. **Contexte récupéré** : les passages, formatés et numérotés pour permettre la citation.
4. **Format de sortie attendu** : style de réponse, format des citations, longueur, langue.

Quelques principes empiriques bien établis :

- **Grounding explicite** : « Réponds UNIQUEMENT sur la base des extraits ci-dessous. Si l'information n'y figure pas, indique-le. »
- **Citations obligatoires** : « Cite chaque affirmation avec [n°] correspondant à la source. »
- **Refus explicite** : autoriser le LLM à dire « je ne sais pas », ce qui réduit drastiquement les hallucinations.
- **Few-shot** : donner 1-3 exemples de paires question/réponse de qualité.

#### 4.4.3. Gestion de la fenêtre de contexte

Le budget de tokens est une contrainte structurante. Stratégies :

- **Troncature** : couper les chunks ou les passages les moins bien classés.
- **Compression** : résumer les chunks longs avant injection (ex. avec un petit LLM).
- **Sélection adaptative** : remplir le contexte jusqu'à un seuil de tokens, par ordre de pertinence.
- **Long context** : exploiter les LLMs à très large contexte (128k+) ; attention au phénomène *lost in the middle*.

#### 4.4.4. Paramètres de décodage

- **Température** : 0 pour la reproductibilité (cas critiques HSE), 0.2–0.5 pour un compromis qualité/diversité, ≥ 0.7 pour la créativité (peu pertinent ici).
- **Top-p / top-k sampling** : alternative à la température, plus rarement utilisée en RAG.
- **Max tokens** : borne haute pour éviter les réponses interminables.
- **Repetition / presence penalty** : utile si le modèle bégaie sur des termes techniques.

Pour ScribBERT, une **température faible (0–0.2)** est recommandée afin de garantir la **stabilité** des réponses (cf. Chapitre 6).

#### 4.4.5. Citations et traçabilité

La citation des sources peut être :

- **Inline** : « Selon [1], le port du harnais est obligatoire dès 2 m. »
- **En fin de réponse** : liste numérotée des sources utilisées.
- **Avec extraits** : reproduire littéralement les passages clés (gain d'auditabilité, perte de fluidité).

La traçabilité doit être **machine-vérifiable** : chaque citation doit pointer vers un identifiant de chunk loggé, lui-même lié à un document d'origine. Cette chaîne est essentielle pour l'audit et pour la mesure de fidélité (Chapitre 6).

#### 4.4.6. Guardrails pour le contexte HSE

En contexte critique, des garde-fous explicites sont nécessaires :

- **Refus contrôlé** : si la confiance retrieval est faible (scores < seuil), répondre « information non trouvée dans les référentiels » plutôt que d'inventer.
- **Détection de contradictions** : si plusieurs sources donnent des réponses incompatibles, signaler la contradiction plutôt que d'arbitrer silencieusement.
- **Avertissements de domaine** : pour des questions sortant du périmètre HSE, rediriger.
- **Filtres de toxicité / sensibilité** : moins critique en HSE qu'en grand public, mais utile pour des cas limites.

### 4.5. Synthèse des leviers et matrice d'expérimentation

L'ensemble des leviers présentés peut être résumé dans une matrice qui guidera la conception du protocole expérimental (Chapitre 5) :

| Composant | Leviers principaux | Métriques affectées en priorité |
|-----------|-------------------|-------------------------------|
| Embedding | Modèle, dimension, langue, fine-tuning | Recall@k, MRR, nDCG |
| Chunking | Stratégie, taille, overlap, métadonnées | Recall@k, citabilité, fidélité |
| Retrieval | Sparse / dense / hybride, filtres, $k$ | Recall@k, précision contexte |
| Reranking | Présence, modèle, top-$n$ | Precision@k, fidélité |
| Query processing | Expansion, reformulation, HyDE | Recall@k (gain), latence (perte) |
| Génération – LLM | Choix du modèle, taille | Fluidité, fidélité, latence |
| Génération – prompt | Instructions, few-shot, format | Fidélité, format, refus contrôlé |
| Génération – décodage | Température, max tokens | Stabilité, longueur |

L'expérimentation menée en Partie III ne pourra pas tester toutes les combinaisons (explosion combinatoire). Elle adoptera une approche **OFAT** (One-Factor-At-a-Time) sur un sous-ensemble de paramètres jugés les plus impactants, complétée par quelques expériences factorielles ciblées.

Le Chapitre 5 présente le protocole d'évaluation lui-même : jeux de test, métriques, conditions d'expérimentation.

## Chapitre 5 — Construction d'un protocole d'évaluation

Le Chapitre 4 a inventorié les leviers techniques d'un RAG. Pour décider quels leviers actionner et dans quelle direction, encore faut-il disposer d'un **protocole d'évaluation** capable de produire des mesures (i) reproductibles, (ii) comparables et (iii) **diagnostiques**, c'est-à-dire qui permettent de localiser la source des erreurs dans la chaîne plutôt que de juger globalement le système.

Ce chapitre propose un tel protocole, organisé en cinq sections : (5.1) les critères d'évaluation, organisés selon la définition opératoire de la fiabilité (§ 3.3) ; (5.2) les approches d'évaluation (automatique, humaine, hybride) ; (5.3) la construction du jeu de test ; (5.4) les conditions expérimentales et la reproductibilité ; (5.5) les méthodes d'analyse.

### 5.1. Critères d'évaluation organisés par dimension de la fiabilité

Plutôt qu'une liste de métriques, on adopte une **organisation par dimension de la fiabilité**, qui permet de relier chaque mesure à une question opérationnelle.

#### 5.1.1. Dimension 1 — Pertinence du retrieval

Question : *les passages récupérés contiennent-ils l'information nécessaire pour répondre ?*

| Métrique | Définition | Quand l'utiliser |
|----------|------------|------------------|
| **Hit@k** | $\mathbb{1}\{\mathrm{Rel}(q) \cap \mathrm{TopK}(q) \neq \emptyset\}$ | Vérifier la présence d'au moins un passage pertinent |
| **Recall@k** | Proportion des passages pertinents dans le top-$k$ | Si plusieurs passages or attendus |
| **Precision@k** | Proportion de pertinents parmi les $k$ retournés | Si l'on veut limiter le bruit dans le contexte LLM |
| **MRR** | Inverse moyen du rang du premier pertinent | Cas où l'utilisateur attend *un* bon passage en tête |
| **nDCG@k** | Gain cumulé normalisé avec pertinence graduée | Si plusieurs niveaux de pertinence sont annotés |
| **Context precision** (RAGAS) | Position moyenne des passages pertinents dans le top-$k$ | Évalue la qualité du *ranking* (pas seulement la présence) |

Pour ScribBERT, **Recall@k** et **MRR** sont les métriques principales : on veut s'assurer que la « bonne règle » figure parmi les passages remontés. Le Hit@k constitue un complément utile pour les questions à passage-or unique.

#### 5.1.2. Dimension 2 — Fidélité aux sources (factualité, *faithfulness*)

Question : *la réponse générée est-elle effectivement supportée par les passages récupérés ?*

C'est la dimension la plus critique en HSE. Plusieurs métriques opérationnalisent cette notion :

- **Faithfulness (RAGAS)** : décomposition de la réponse en propositions atomiques, vérification individuelle de chacune contre le contexte par un LLM-juge. Score = proportion de propositions supportées.
- **FactScore** : variante de l'approche atomique, validée sur des tâches biographiques et adaptable.[^Min2023FactScore]
- **NLI-based scoring** : utiliser un modèle d'inférence textuelle (NLI) entraîné pour vérifier si chaque phrase de la réponse est *entailed* par le contexte (`roberta-large-mnli`, `DeBERTa-v3-NLI`).
- **AttrScore / Citation Faithfulness** : vérifier que les passages explicitement cités supportent réellement les affirmations attribuées.
- **Hallucination rate** : taux de propositions non supportées (1 − faithfulness).

Pour le contexte HSE, on peut introduire une métrique métier : **modality preservation** = la réponse respecte-t-elle les modalités des sources (« doit » vs « peut » vs « ne doit pas ») ? Cette métrique nécessite généralement une évaluation humaine ou un LLM-juge spécialement instruit.

#### 5.1.3. Dimension 3 — Pertinence et utilité de la réponse

Question : *la réponse répond-elle à la question, complètement et au bon niveau de granularité ?*

- **Answer Relevance (RAGAS)** : un LLM-juge génère $n$ questions hypothétiques à partir de la réponse, puis on calcule la similarité moyenne avec la question originale. Élevée si la réponse est ciblée.
- **Completeness / Coverage** : proportion des éléments attendus de la réponse-or présents dans la réponse générée. Nécessite une réponse-or annotée.
- **Conciseness** : longueur relative à la complexité de la question, pénalité pour le verbiage.
- **Format adherence** : respect du format attendu (check-list, étapes numérotées, citation des sources).

#### 5.1.4. Dimension 4 — Stabilité et répétabilité

Question : *à requête identique (ou paraphrasée), le système produit-il des réponses cohérentes entre exécutions ?*

Cette dimension est traitée en détail au Chapitre 6. Elle complète les précédentes en mesurant la **variance** des réponses, et non leur qualité moyenne.

#### 5.1.5. Dimension 5 — Traçabilité et auditabilité

Question : *peut-on, a posteriori, justifier chaque affirmation de la réponse par un passage de source identifié ?*

- **Citation correctness** : proportion des affirmations portant une citation valide (passage existant, pertinent, et supportant l'affirmation).
- **Citation completeness** : proportion des affirmations qui *devraient* être citées et le sont effectivement.
- **Source diversity** : nombre de sources distinctes effectivement citées (signal d'agrégation vs paraphrase d'une seule source).

Ces métriques nécessitent que le prompt impose un format de citation machine-vérifiable.

#### 5.1.6. Métriques de coût opérationnel

Pour l'industrialisation, on ajoute :

- **Latence** (P50, P95, P99 ms) sur la chaîne complète.
- **Coût par requête** (€) si le modèle est facturé à l'usage.
- **Empreinte carbone** estimée (optionnel mais en progression dans les exigences ESG).
- **Taux de refus** (proportion de requêtes pour lesquelles le système refuse de répondre faute de preuve suffisante) — métrique à double tranchant : un taux nul peut indiquer des hallucinations, un taux trop élevé une frustration utilisateur.

### 5.2. Approches d'évaluation : automatique, humaine, hybride

#### 5.2.1. Évaluation automatique

Les métriques automatiques se classent en trois familles :

- **Lexicales** (BLEU, ROUGE, METEOR, exact match) : peu adaptées à la QA générative car elles pénalisent la paraphrase légitime. Utiles uniquement pour des réponses très courtes et factuelles.
- **Vectorielles** (BERTScore, BLEURT, similarité cosinus d'embeddings de réponse) : capturent mieux la similarité sémantique. Limitation : peuvent juger « proches » deux réponses dont l'une contient une erreur factuelle subtile.[^Zhang2020BERTScore][^Sellam2020BLEURT]
- **LLM-based / LLM-as-judge** : un LLM note la réponse selon une grille (G-Eval, Prometheus, RAGAS, TruLens). Approche dominante pour le RAG aujourd'hui : flexible, capable de juger la fidélité, la complétude, la modalité.

**Avantages** : scalabilité (millions de requêtes), reproductibilité (à seed et prompt fixés), coût marginal réduit.

**Limites** :
- corrélation imparfaite avec le jugement humain expert (notamment en domaine spécialisé) ;
- biais du LLM-juge (préférence pour les réponses verbeuses, biais de longueur, biais de formatage) ;
- risque de **fuite** si le même LLM sert de générateur et de juge (auto-validation circulaire) ;
- difficulté à juger les modalités, les exceptions, les conditions implicites.

**Bonnes pratiques** :
- Utiliser un LLM-juge **différent** du générateur évalué.
- **Calibrer** le LLM-juge sur un échantillon annoté humainement (quelques dizaines d'exemples).
- Logger les justifications du juge, pas seulement le score.
- Mesurer la stabilité du juge lui-même (même prompt, $n$ exécutions).

#### 5.2.2. Évaluation humaine

Constitue le **gold standard**, particulièrement pour les dimensions difficiles à automatiser (modalités, sécurité, exceptions).

**Conception d'une grille d'évaluation** :

| Critère | Échelle | Définition |
|---------|---------|------------|
| Pertinence | 0–3 | 0 = hors-sujet, 3 = répond exactement à la question |
| Fidélité aux sources | 0–3 | 0 = invente, 3 = parfaitement supporté par les sources fournies |
| Complétude | 0–3 | 0 = lacunes critiques, 3 = couvre toutes les exceptions |
| Modalité (HSE) | 0–2 | 0 = transforme une obligation en recommandation, 2 = modalité conservée |
| Sûreté opérationnelle | 0–3 | 0 = induirait un comportement dangereux, 3 = aligné avec les bonnes pratiques |
| Citations | 0–2 | 0 = aucune ou erronée, 2 = chaque affirmation citée correctement |

**Bonnes pratiques** :
- **Plusieurs annotateurs** par item (idéalement 2–3) pour mesurer l'**accord inter-annotateurs** (Kappa de Cohen, $\alpha$ de Krippendorff).
- **Annotation à l'aveugle** sur la configuration testée (l'annotateur ne sait pas quel système a produit la réponse).
- **Profil mixte** d'annotateurs : experts métier (HSE) et utilisateurs cibles (préventeurs chantier), pour capturer expertise et utilisabilité.
- **Charte d'annotation** documentée et exemples gold pour calibrer.

**Limites** : coût, temps, subjectivité résiduelle, fatigue de l'annotateur, scalabilité.

#### 5.2.3. Approche hybride : *screening* automatique + validation humaine

Compromis pragmatique adopté par la plupart des équipes industrielles :

1. **Screening automatique** sur l'ensemble du jeu de test (toutes configurations, toutes questions) → métriques de tendance.
2. **Échantillonnage stratifié** des cas litigieux ou critiques pour annotation humaine (ex. : top-30 cas à plus fort désaccord juge ↔ score utilisateur, plus 30 cas critiques HSE).
3. **Calibration croisée** : utiliser l'échantillon annoté humainement pour corriger les biais du LLM-juge.
4. **Triangulation** : conclure uniquement si les deux approches convergent ; investiguer les divergences.

### 5.3. Construction du jeu de test

La qualité du jeu de test conditionne la validité de toute l'évaluation. Cette section décrit la démarche méthodologique générique ; l'instanciation pour ScribBERT figurera en Partie III.

#### 5.3.1. Sources des questions

Quatre sources complémentaires :

1. **Questions « naturelles » issues de l'usage** : extraites des logs si le système est déjà déployé (ScribBERT v0), ou collectées via des enquêtes auprès des utilisateurs cibles. Avantage : représentativité des intentions réelles.
2. **Questions générées par experts** : un panel d'experts HSE rédige des questions couvrant systématiquement les domaines, niveaux de risque, types de procédures.
3. **Questions générées par LLM à partir des documents** : pour chaque chunk pertinent, un LLM génère une question dont la réponse est dans le chunk. Permet une couverture exhaustive du corpus mais introduit un biais (questions « trop bien formées »).
4. **Questions adversariales** : questions hors-périmètre, ambiguës, formulations terrain (jargon, fautes), questions à réponses contradictoires dans le corpus. Test des garde-fous.

#### 5.3.2. Typologie des questions

Pour un protocole diagnostique, on stratifie le jeu de test selon plusieurs axes :

**Par type d'intention** :
- **Factuelles** (« Quelle est la hauteur minimale pour port du harnais ? ») — réponse courte, vérifiable.
- **Procédurales** (« Quelle est la procédure avant intervention en espace confiné ? ») — réponse multi-étapes.
- **Conditionnelles** (« Que faire si... ? ») — gestion des exceptions.
- **Comparatives** (« Quelle différence entre EPI niveau 1 et niveau 2 ? ») — agrégation multi-sources.
- **Justificatives** (« Pourquoi cette mesure est-elle requise ? ») — explication d'une norme.
- **Hors-périmètre** (test du refus contrôlé).

**Par niveau de difficulté** :
- **Facile** : la réponse est dans un seul passage explicite.
- **Moyen** : nécessite l'agrégation de 2–3 passages.
- **Difficile** : exception ou condition à identifier, modalité subtile, contradiction apparente à arbitrer.

**Par criticité métier** :
- **Élevée** : erreur potentiellement dangereuse (port d'EPI vital, procédure de mise en sécurité).
- **Moyenne** : erreur procédurale sans conséquence vitale immédiate.
- **Faible** : information administrative ou organisationnelle.

#### 5.3.3. Annotation

Pour chaque question, on annote :

- **Réponse-or** rédigée par un expert (idéalement validée par un second expert).
- **Passages-or** : identifiants des chunks contenant l'information nécessaire et suffisante.
- **Métadonnées** : type, difficulté, criticité, document(s) source(s), date de validité.
- **Variantes acceptables** (paraphrases de la réponse-or, formats alternatifs).
- **Pièges connus** (passages tentants mais non applicables, à utiliser pour vérifier la précision).

#### 5.3.4. Volume et représentativité

Un ordre de grandeur **utile** pour un RAG d'entreprise est de **150–300 questions** annotées, stratifiées selon les axes ci-dessus. Cela permet :

- des estimations stables des métriques globales (intervalle de confiance acceptable),
- des analyses par strate (par type, par difficulté),
- la détection d'effets significatifs entre configurations.

En-deçà de 100 questions, les comparaisons entre configurations sont sujettes à un fort bruit statistique.

#### 5.3.5. Prévention de la contamination

Le RAG étant *zero-shot* (pas d'entraînement sur le jeu de test), le risque de contamination est moindre que pour un modèle fine-tuné. Trois précautions restent utiles :

- ne pas exposer les questions du jeu de test au LLM-juge avant l'évaluation ;
- vérifier qu'aucune question n'a été utilisée pour la conception du système (overfitting au jeu de test par les développeurs) ;
- conserver un **jeu de test « caché »** (held-out), non utilisé pendant la phase d'optimisation, pour la validation finale.

#### 5.3.6. Versioning

Le jeu de test évolue (corrections, ajouts, retraits). On versionne :
- le contenu (questions, réponses-or, passages-or),
- le corpus de référence (documents, chunks, embeddings) — un jeu de test n'a de sens que pour une version donnée du corpus,
- les annotations (qui, quand, sur quelle base).

### 5.4. Conditions expérimentales et reproductibilité

#### 5.4.1. Isolation des facteurs

Étant donnée l'explosion combinatoire des leviers (Ch. 4), on adopte typiquement deux stratégies :

- **OFAT** (*One-Factor-At-a-Time*) : faire varier un paramètre à la fois autour d'une configuration de référence. Simple, interprétable, mais ne capture pas les interactions.
- **Plans factoriels (réduits)** : tester les combinaisons d'un sous-ensemble de facteurs (plans fractionnels, designs orthogonaux). Capture les interactions au prix d'un volume d'expériences plus important.

Pour ce mémoire, l'approche OFAT sera privilégiée pour les comparaisons principales, complétée par 2–3 expériences factorielles ciblées sur des couples d'intérêt (ex. taille de chunk × top-$k$, embedding × reranking).

#### 5.4.2. Configuration de référence (*baseline*)

Toute expérience compare à une **configuration de référence** documentée :
- modèle d'embedding et version exacte,
- stratégie et paramètres de chunking,
- type de retrieval et top-$k$,
- modèle de génération et version exacte,
- prompt complet,
- paramètres de décodage (température, max tokens, seed).

Cette baseline est elle-même l'objet d'une évaluation initiale, sur l'ensemble des dimensions, qui sert de point de comparaison pour toutes les variantes.

#### 5.4.3. Reproductibilité

Pour qu'une expérience soit reproductible :
- **fixer les seeds** (générateur, ANN si applicable) ;
- **figer les versions** des modèles (un même nom de modèle peut être mis à jour silencieusement par le fournisseur) ;
- **logger** la requête, le contexte récupéré, la réponse complète, les métadonnées de chaque passage ;
- **archiver** les jeux de test versionnés et les résultats bruts.

Lorsque la reproductibilité parfaite est impossible (LLM propriétaires non déterministes), on rapporte des **distributions** sur $n$ runs (médiane et IQR) plutôt que des valeurs ponctuelles.

#### 5.4.4. Logging et observabilité

Pour chaque exécution, on enregistre :

```
{
  "query_id": ..., "query_text": ..., "config_id": ...,
  "retrieved_chunks": [{"id": ..., "score": ..., "rank": ...}],
  "reranked_chunks": [...],
  "prompt_full": ...,
  "response": ..., "citations": [...],
  "latency_ms": {"retrieval": ..., "rerank": ..., "generation": ...},
  "timestamp": ..., "seed": ..., "model_versions": {...}
}
```

Cette trace permet l'analyse a posteriori (*post-mortem* d'erreurs, audit, recalcul de métriques avec des juges différents).

### 5.5. Méthodes d'analyse

#### 5.5.1. Statistiques descriptives

Pour chaque configuration et chaque métrique : moyenne, médiane, écart-type, IQR, distribution (histogramme). Toujours rapporter la **distribution** et pas seulement la moyenne — particulièrement important pour la fidélité, où une moyenne à 0.85 peut masquer une queue de réponses gravement fausses.

#### 5.5.2. Tests de significativité

Pour comparer deux configurations sur une métrique :
- **Test apparié** (la même question est posée aux deux configurations) : Wilcoxon signed-rank (non paramétrique, robuste) ou test t apparié si distribution proche normale.
- **Correction multiple** si l'on teste plusieurs métriques ou plusieurs configurations simultanément (Bonferroni, Holm).
- **Effet plutôt que p-value seule** : rapporter la **taille d'effet** (différence moyenne, Cohen's $d$) et un intervalle de confiance.

#### 5.5.3. Stratification et analyses par sous-groupe

L'analyse par strate (type de question, difficulté, criticité) est essentielle : une amélioration moyenne de 5 % peut masquer une dégradation sur les questions difficiles, ce qui est inacceptable en HSE. On rapporte systématiquement les métriques par strate.

#### 5.5.4. Analyse d'erreurs typologique

Pour les cas d'échec, on construit une **typologie d'erreurs** raffinée à partir des observations :

| Catégorie | Description | Localisation probable |
|-----------|-------------|----------------------|
| Retrieval miss | Aucun passage pertinent dans le top-$k$ | Embedding / chunking / $k$ |
| Retrieval bruit | Passages tentants mais non applicables | Embedding / reranking |
| Hallucination factuelle | Affirmation non supportée | Génération / prompt |
| Omission d'exception | Règle correcte mais condition oubliée | Génération / contexte tronqué |
| Inversion de modalité | « doit » devenu « peut » | Génération / prompt |
| Contradiction silencieuse | Sources divergentes non signalées | Prompt / corpus |
| Refus à tort | Refuse alors que l'info est dans le contexte | Prompt / seuils |
| Réponse hors-périmètre acceptée | Aurait dû refuser | Prompt / guardrails |

Cette typologie sert de grille pour l'analyse qualitative en Partie III et oriente les améliorations.

#### 5.5.5. Études de cas

Pour illustrer les résultats agrégés, sélectionner 5–10 cas représentatifs (succès exemplaires, échecs typiques, cas limites), avec narratif expliquant la chaîne de décision et le lien avec les métriques.

### 5.6. Synthèse

Le protocole proposé articule **cinq dimensions de la fiabilité** (retrieval, fidélité, pertinence réponse, stabilité, traçabilité) avec **trois approches d'évaluation** (automatique, humaine, hybride), appliquées sur un **jeu de test stratifié** dans des **conditions expérimentales reproductibles**, et analysées avec des outils statistiques adaptés.

Le Chapitre 6 approfondit la dimension **stabilité**, qui mérite un traitement spécifique car elle est sous-traitée par les frameworks usuels et particulièrement critique pour un système RAG en production sur un sujet sensible.

## Chapitre 6 — Évaluation de la stabilité et de la répétabilité

### 6.1. Pourquoi la stabilité est une dimension distincte de la fiabilité

Les métriques classiques d'évaluation d'un RAG (Recall@k, faithfulness, answer relevance) sont calculées **sur une exécution unique** par requête. Elles décrivent la qualité moyenne d'une réponse à un instant donné, mais ne disent rien sur ce qui se passe **si l'on rejoue la même requête** ou **si l'utilisateur formule légèrement différemment** sa question.

Or trois phénomènes rendent un RAG intrinsèquement variable :

1. **Stochasticité de la génération** : à température > 0, le LLM échantillonne à chaque token, conduisant à des réponses différentes pour une même entrée.
2. **Approximation du retrieval** : les algorithmes ANN (HNSW, IVF) introduisent une approximation contrôlée mais réelle ; deux exécutions strictement identiques peuvent même retourner des ordres légèrement différents selon l'implémentation et la concurrence.
3. **Sensibilité au prompt et à la formulation** : une reformulation marginale de la question peut modifier le top-$k$ retourné et donc la réponse.

Pour un système d'aide à la décision en HSE, la **variabilité** est un problème en soi : un préventeur qui obtient deux réponses différentes à la même question perd confiance, et plus gravement, peut prendre des décisions différentes selon le moment où il a posé la question. **La stabilité fait partie intégrante de la fiabilité**, au même titre que la justesse moyenne.

Cette dimension est aussi un **enjeu méthodologique** : si la variance intra-configuration est élevée, comparer deux configurations sur une exécution unique n'a pas de sens — le bruit de mesure dépasse l'effet à mesurer. L'évaluation de la stabilité conditionne donc la robustesse statistique des comparaisons du Chapitre 5.

### 6.2. Sources de variance dans un RAG

Cartographier les sources de variance permet de cibler les contre-mesures.

#### 6.2.1. Variance liée à la génération

- **Échantillonnage stochastique** (température, top-p) : effet direct sur la diversité lexicale ; à température élevée, le contenu factuel peut aussi varier.
- **Non-déterminisme des LLM propriétaires** : même à température 0, certaines API ne garantissent pas le déterminisme strict (parallélisme GPU, batching variable). OpenAI propose un paramètre `seed` et un identifiant `system_fingerprint` pour tracer le déterminisme effectif.
- **Choix de format** : le LLM peut produire des tournures différentes (puces vs phrases) à structure équivalente, ce qui inflige des comparaisons textuelles brutes.

#### 6.2.2. Variance liée au retrieval

- **ANN approximatif** : HNSW est généralement déterministe à structure d'index donnée, mais des reconstructions d'index produisent des graphes différents.
- **Égalités de scores** : plusieurs passages avec le même score peuvent être ordonnés arbitrairement.
- **Concurrence** : sur une base distribuée, l'ordre peut dépendre du shard répondant en premier.

#### 6.2.3. Variance liée à la formulation utilisateur

- **Paraphrases équivalentes** : « Quels EPI pour travail en hauteur ? » vs « Quels équipements de protection pour les travaux en hauteur ? ».
- **Fautes typographiques et accents** : sensibilité variable des embeddings.
- **Niveau de spécificité** : « EPI travail en hauteur » vs « harnais antichute » ciblent la même règle mais avec des chemins de retrieval différents.
- **Code-switching FR/EN** : présence ponctuelle d'anglais.

#### 6.2.4. Dérive temporelle (dimension longue)

- **Mise à jour silencieuse des modèles propriétaires** (modèle versioné `gpt-4o-2024-08-06` peut être déprécié et remplacé).
- **Mise à jour du corpus** : ajouts, retraits, révisions de procédures.
- **Dérive de l'index** si la stratégie de chunking ou d'embedding est modifiée.

### 6.3. Métriques de stabilité

#### 6.3.1. Stabilité inter-runs (même requête, plusieurs exécutions)

Pour chaque requête $q$, on exécute le système $n$ fois (typiquement $n \in [5, 20]$) et on mesure :

- **Stability@retrieval** : Jaccard moyen des ensembles de chunks récupérés entre paires de runs. $\mathrm{J}(A_i, A_j) = |A_i \cap A_j| / |A_i \cup A_j|$.
- **Stability@citations** : Jaccard moyen des ensembles de chunks effectivement cités dans la réponse.
- **Stability@answer (sémantique)** : BERTScore moyen entre paires de réponses.
- **Variance des métriques** : écart-type inter-runs de la faithfulness, du Recall@k, etc.
- **Flip rate** : taux de questions pour lesquelles le verdict (réponse acceptable / inacceptable) change entre runs.

Cas binaire (réponse correcte/incorrecte) : on peut résumer par la **proportion de runs corrects** et signaler les questions avec un taux entre 30 % et 70 % comme « instables ».

#### 6.3.2. Robustesse aux paraphrases (sensibilité linguistique)

Pour chaque requête $q$, on génère $m$ paraphrases (par LLM ou manuellement) et on mesure :

- **Stability@paraphrase** : variantes des métriques ci-dessus, mais entre la requête originale et ses paraphrases.
- **Answer consistency** : un LLM-juge évalue si les réponses aux paraphrases véhiculent la *même information factuelle* (au-delà des différences de surface).

Cette mesure est complémentaire : un système peut être stable inter-runs (à requête identique) mais fragile aux paraphrases.

#### 6.3.3. Robustesse à l'ordre des passages

Sensibilité au **lost-in-the-middle** : on permute l'ordre des passages dans le contexte et on mesure la variation de la réponse. Un système robuste produit des réponses sémantiquement équivalentes quel que soit l'ordre.

#### 6.3.4. Self-consistency (cohérence interne)

Méthode popularisée par Wang et al. (2022) : on génère $n$ réponses à température > 0, on extrait la réponse « majoritaire » par vote ou agrégation. Le **taux d'accord** entre les $n$ réponses est un indicateur de confiance interne du modèle.[^Wang2022SelfConsistency] Si l'accord est faible, c'est un signal de difficulté ou d'ambiguïté.

### 6.4. Sensibilité aux paramètres et aux variations adverses

Au-delà des variations « normales », un protocole de stabilité robuste teste des perturbations contrôlées :

- **Fautes injectées** : substitutions de caractères, omissions, accents incorrects.
- **Reformulations adversariales** : reformulations qui préservent l'intention mais utilisent un vocabulaire différent (jargon chantier, anglicismes).
- **Bruit dans le contexte** : ajout de chunks non pertinents pour mesurer la résistance à la dilution.
- **Corpus avec contradictions** : injection de variantes contradictoires pour tester la détection.
- **Questions pièges** : questions hors-périmètre, questions à présupposés faux (« Quelle est la procédure pour ne pas porter de harnais ? »).

Ces tests *adversariaux* ne sont pas des cas usuels mais des stress-tests : ils caractérisent les **limites** du système et orientent les guardrails.

### 6.5. Protocole de test de stabilité

Un protocole opérationnel pour évaluer la stabilité d'un RAG :

**Étape 1 — Sélection d'un sous-jeu de questions critiques** (30–60 questions, stratifiées par criticité).

**Étape 2 — Tests inter-runs** : pour chaque question, $n=10$ exécutions à seed et configuration constants. Calcul de Stability@retrieval, Stability@citations, Stability@answer, flip rate.

**Étape 3 — Tests de paraphrase** : pour chaque question, génération de $m=5$ paraphrases (validées par expert pour préserver l'intention). Une exécution par paraphrase. Mesure de la consistance sémantique des réponses.

**Étape 4 — Tests adversariaux** : pour un sous-ensemble (10–20 questions), application des perturbations (fautes, reformulations, questions pièges).

**Étape 5 — Synthèse** : tableau de bord par configuration, agrégeant qualité moyenne (Ch. 5) et stabilité (Ch. 6). Une configuration n'est retenue que si elle dépasse des seuils minimaux sur **les deux dimensions**.

### 6.6. Stabilité et confiance utilisateur

La stabilité a une dimension **psychologique** au-delà de sa dimension statistique. Un utilisateur perçoit l'instabilité comme un signe d'incompétence du système, même si la réponse moyenne est correcte. Inversement, un système stable mais subtilement biaisé peut générer une **fausse confiance**.

Deux pratiques permettent de réconcilier ces enjeux :

- **Exposer l'incertitude** : afficher un score de confiance, ou indiquer explicitement « plusieurs réponses possibles selon le contexte de chantier ».
- **Stabiliser les éléments critiques** sans figer les éléments stylistiques : la liste d'EPI doit être identique, mais la formulation peut varier.

Ces principes seront discutés en Partie III à la lumière des résultats observés sur ScribBERT.

### 6.7. Synthèse de la Partie II

Les chapitres 4 à 6 ont défini un cadre méthodologique complet :

- **Ch. 4** a inventorié les leviers techniques actionnables (embedding, chunking, retrieval, génération) avec leurs compromis ;
- **Ch. 5** a structuré le protocole d'évaluation autour des cinq dimensions de la fiabilité, avec des approches automatiques, humaines et hybrides ;
- **Ch. 6** a approfondi la dimension stabilité, sous-traitée mais critique pour un déploiement en production.

La Partie III instancie ce cadre sur ScribBERT : architecture déployée (Ch. 7), résultats expérimentaux (Ch. 8a-8b), enjeux de gouvernance (Ch. 9) et discussion (Ch. 10).

---

## Références (PARTIE I)

[^BarzilayLapata2008]: Barzilay, R., & Lapata, M. (2008). Modeling local coherence: An entity-based approach. *Computational Linguistics*, 34(1), 1–34. [https://doi.org/10.1162/coli.2008.34.1.1](https://doi.org/10.1162/coli.2008.34.1.1)

[^Bush1945]: Bush, V. (1945). As We May Think. *The Atlantic*. [https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/](https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/)

[^Cleverdon1967]: Cleverdon, C. W. (1967). The Cranfield tests on index language devices. *Aslib Proceedings*, 19(6), 173–194. [https://doi.org/10.1108/eb050097](https://doi.org/10.1108/eb050097)

[^Deerwester1990]: Deerwester, S., Dumais, S. T., Furnas, G. W., Landauer, T. K., & Harshman, R. (1990). Indexing by latent semantic analysis. *Journal of the American Society for Information Science*, 41(6), 391–407. [https://doi.org/10.1002/(SICI)1097-4571(199009)41:6<391::AID-ASI1>3.0.CO;2-9](https://doi.org/10.1002/(SICI)1097-4571(199009)41:6%3C391::AID-ASI1%3E3.0.CO;2-9)

[^Devlin2019]: Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. *NAACL-HLT*. [https://doi.org/10.18653/v1/N19-1423](https://doi.org/10.18653/v1/N19-1423)

[^Gao2021]: Gao, T., Yao, X., & Chen, D. (2021). SimCSE: Simple Contrastive Learning of Sentence Embeddings. *EMNLP*. [https://doi.org/10.18653/v1/2021.emnlp-main.552](https://doi.org/10.18653/v1/2021.emnlp-main.552)

[^Gao2024RAGSurvey]: Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J., Guo, Q., Wang, M., & Wang, H. (2024). Retrieval-Augmented Generation for Large Language Models: A Survey. *arXiv preprint*. [https://arxiv.org/abs/2312.10997](https://arxiv.org/abs/2312.10997)

[^Guu2020]: Guu, K., Lee, K., Tung, Z., Pasupat, P., & Chang, M.-W. (2020). REALM: Retrieval-Augmented Language Model Pre-Training. *ICML*. [https://arxiv.org/abs/2002.08909](https://arxiv.org/abs/2002.08909)

[^Guo2016]: Guo, J., Fan, Y., Ai, Q., & Croft, W. B. (2016). A Deep Relevance Matching Model for Ad-hoc Retrieval. *CIKM*. [https://doi.org/10.1145/2983323.2983769](https://doi.org/10.1145/2983323.2983769)

[^Huang2013]: Huang, P.-S., He, X., Gao, J., Deng, L., Acero, A., & Heck, L. (2013). Learning Deep Structured Semantic Models for Web Search using Clickthrough Data. *CIKM*. [https://doi.org/10.1145/2505515.2505665](https://doi.org/10.1145/2505515.2505665)

[^IzacardGrave2021]: Izacard, G., & Grave, E. (2021). Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering. *EACL*. [https://doi.org/10.18653/v1/2021.eacl-main.74](https://doi.org/10.18653/v1/2021.eacl-main.74)

[^JarvelinKekalainen2002]: Järvelin, K., & Kekäläinen, J. (2002). Cumulated gain-based evaluation of IR techniques. *ACM Transactions on Information Systems*, 20(4), 422–446. [https://doi.org/10.1145/582415.582418](https://doi.org/10.1145/582415.582418)

[^Ji2023]: Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A., & Fung, P. (2023). Survey of Hallucination in Natural Language Generation. *ACM Computing Surveys*, 55(12), 1–38. [https://doi.org/10.1145/3571730](https://doi.org/10.1145/3571730)

[^Johnson2019]: Johnson, J., Douze, M., & Jégou, H. (2019). Billion-scale similarity search with GPUs. *IEEE Transactions on Big Data*, 7(3), 535–547. [https://doi.org/10.1109/TBDATA.2019.2921572](https://doi.org/10.1109/TBDATA.2019.2921572)

[^Karpukhin2020]: Karpukhin, V., Oguz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W.-t. (2020). Dense Passage Retrieval for Open-Domain Question Answering. *EMNLP*. [https://doi.org/10.18653/v1/2020.emnlp-main.550](https://doi.org/10.18653/v1/2020.emnlp-main.550)

[^KhattabZaharia2020]: Khattab, O., & Zaharia, M. (2020). ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT. *SIGIR*. [https://doi.org/10.1145/3397271.3401075](https://doi.org/10.1145/3397271.3401075)

[^LavrenkoCroft2001]: Lavrenko, V., & Croft, W. B. (2001). Relevance-based language models. *SIGIR*. [https://doi.org/10.1145/383952.383972](https://doi.org/10.1145/383952.383972)

[^Lee2019ORQA]: Lee, K., Chang, M.-W., & Toutanova, K. (2019). Latent Retrieval for Weakly Supervised Open Domain Question Answering. *ACL*. [https://doi.org/10.18653/v1/P19-1612](https://doi.org/10.18653/v1/P19-1612)

[^Lewis2020]: Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS*. [https://arxiv.org/abs/2005.11401](https://arxiv.org/abs/2005.11401)

[^MalkovYashunin2018]: Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs. *IEEE TPAMI*, 42(4), 824–836. [https://doi.org/10.1109/TPAMI.2018.2889473](https://doi.org/10.1109/TPAMI.2018.2889473)

[^Manning2008]: Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press. [https://nlp.stanford.edu/IR-book/](https://nlp.stanford.edu/IR-book/)

[^Maynez2020]: Maynez, J., Narayan, S., Bohnet, B., & McDonald, R. (2020). On Faithfulness and Factuality in Abstractive Summarization. *ACL*. [https://doi.org/10.18653/v1/2020.acl-main.173](https://doi.org/10.18653/v1/2020.acl-main.173)

[^Mikolov2013]: Mikolov, T., Sutskever, I., Chen, K., Corrado, G., & Dean, J. (2013). Distributed Representations of Words and Phrases and their Compositionality. *NeurIPS*. [https://arxiv.org/abs/1310.4546](https://arxiv.org/abs/1310.4546)

[^Mizzaro1997]: Mizzaro, S. (1997). Relevance: The whole history. *Journal of the American Society for Information Science*, 48(9), 810–832. [https://doi.org/10.1002/(SICI)1097-4571(199709)48:9<810::AID-ASI6>3.0.CO;2-U](https://doi.org/10.1002/(SICI)1097-4571(199709)48:9%3C810::AID-ASI6%3E3.0.CO;2-U)

[^Muennighoff2023MTEB]: Muennighoff, N., Tazi, N., Magne, L., & Reimers, N. (2023). MTEB: Massive Text Embedding Benchmark. *arXiv preprint*. [https://arxiv.org/abs/2210.07316](https://arxiv.org/abs/2210.07316)

[^Nguyen2016]: Nguyen, T., Rosenberg, M., Song, X., Gao, J., Tiwary, S., Majumder, R., & Deng, L. (2016). MS MARCO: A Human Generated Machine Reading Comprehension Dataset. *CoRR/arXiv*. [https://arxiv.org/abs/1611.09268](https://arxiv.org/abs/1611.09268)

[^NogueiraCho2019]: Nogueira, R., & Cho, K. (2019). Passage Re-ranking with BERT. *arXiv preprint*. [https://arxiv.org/abs/1901.04085](https://arxiv.org/abs/1901.04085)

[^Pennington2014]: Pennington, J., Socher, R., & Manning, C. D. (2014). GloVe: Global Vectors for Word Representation. *EMNLP*. [https://doi.org/10.3115/v1/D14-1162](https://doi.org/10.3115/v1/D14-1162)

[^PonteCroft1998]: Ponte, J. M., & Croft, W. B. (1998). A language modeling approach to information retrieval. *SIGIR*. [https://doi.org/10.1145/290941.291008](https://doi.org/10.1145/290941.291008)

[^ReimersGurevych2019]: Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP-IJCNLP*. [https://doi.org/10.18653/v1/D19-1410](https://doi.org/10.18653/v1/D19-1410)

[^RobertsonZaragoza2009]: Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333–389. [https://doi.org/10.1561/1500000019](https://doi.org/10.1561/1500000019)

[^Salton1975]: Salton, G., Wong, A., & Yang, C. S. (1975). A vector space model for automatic indexing. *Communications of the ACM*, 18(11), 613–620. [https://doi.org/10.1145/361219.361220](https://doi.org/10.1145/361219.361220)

[^Saracevic1996]: Saracevic, T. (1996). Relevance reconsidered. *Proceedings of CoLIS*, 201–218.

[^Sellam2020BLEURT]: Sellam, T., Das, D., & Parikh, A. P. (2020). BLEURT: Learning Robust Metrics for Text Generation. *ACL*. [https://doi.org/10.18653/v1/2020.acl-main.704](https://doi.org/10.18653/v1/2020.acl-main.704)

[^SparckJones1972]: Spärck Jones, K. (1972). A statistical interpretation of term specificity and its application in retrieval. *Journal of Documentation*, 28(1), 11–21. [https://doi.org/10.1108/eb026526](https://doi.org/10.1108/eb026526)

[^Thakur2021BEIR]: Thakur, N., Reimers, N., Daxenberger, J., & Gurevych, I. (2021). BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. *NeurIPS Datasets and Benchmarks*. [https://arxiv.org/abs/2104.08663](https://arxiv.org/abs/2104.08663)

[^Vaswani2017]: Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention Is All You Need. *NeurIPS*. [https://arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762)

[^Wang2022SelfConsistency]: Wang, X., Wei, J., Schuurmans, D., Le, Q., Chi, E., Narang, S., Chowdhery, A., & Zhou, D. (2022). Self-Consistency Improves Chain of Thought Reasoning in Language Models. *arXiv preprint*. [https://arxiv.org/abs/2203.11171](https://arxiv.org/abs/2203.11171)

[^VoorheesHarman2005]: Voorhees, E. M., & Harman, D. (Eds.). (2005). *TREC: Experiment and Evaluation in Information Retrieval*. MIT Press.

[^Joachims2002]: Joachims, T. (2002). Optimizing Search Engines Using Clickthrough Data. *KDD*. [https://doi.org/10.1145/775047.775067](https://doi.org/10.1145/775047.775067)

[^Liu2009LTR]: Liu, T.-Y. (2009). *Learning to Rank for Information Retrieval*. Foundations and Trends in Information Retrieval, 3(3), 225–331. [https://doi.org/10.1561/1500000016](https://doi.org/10.1561/1500000016)

[^Rocchio1971]: Rocchio, J. J. (1971). Relevance feedback in information retrieval. In *The SMART Retrieval System* (G. Salton, Ed.). Prentice-Hall.

[^Borgeaud2022]: Borgeaud, S., Mensch, A., Hoffmann, J., Cai, T., Rutherford, E., Millican, K., van den Driessche, G., Lespiau, J.-B., Damoc, B., Clark, A., de Las Casas, D., Guy, A., Menick, J., Ring, R., Hennigan, T., Huang, S., Brock, A., Fawzi, A., & Simonyan, K. (2022). Improving language models by retrieving from trillions of tokens. *ICML*. [https://arxiv.org/abs/2112.04426](https://arxiv.org/abs/2112.04426)

[^Borlund2003]: Borlund, P. (2003). The IIR evaluation model: a framework for evaluation of interactive information retrieval systems. *Information Research*, 8(3). [https://informationr.net/ir/8-3/paper152.html](https://informationr.net/ir/8-3/paper152.html)

[^Chen2017DrQA]: Chen, D., Fisch, A., Weston, J., & Bordes, A. (2017). Reading Wikipedia to Answer Open-Domain Questions. *ACL*. [https://doi.org/10.18653/v1/P17-1171](https://doi.org/10.18653/v1/P17-1171)

[^HallidayHasan1976]: Halliday, M. A. K., & Hasan, R. (1976). *Cohesion in English*. Longman.

[^Hearst1997]: Hearst, M. A. (1997). TextTiling: Segmenting text into multi-paragraph subtopic passages. *Computational Linguistics*, 23(1), 33–64. [https://aclanthology.org/J97-1003/](https://aclanthology.org/J97-1003/)

[^IngwersenJarvelin2005]: Ingwersen, P., & Järvelin, K. (2005). *The Turn: Integration of Information Seeking and Retrieval in Context*. Springer. [https://doi.org/10.1007/1-4020-3851-8](https://doi.org/10.1007/1-4020-3851-8)

[^MannThompson1988]: Mann, W. C., & Thompson, S. A. (1988). Rhetorical Structure Theory: Toward a functional theory of text organization. *Text*, 8(3), 243–281. [https://doi.org/10.1515/text.1.1988.8.3.243](https://doi.org/10.1515/text.1.1988.8.3.243)

[^Roberts2020]: Roberts, A., Raffel, C., & Shazeer, N. (2020). How Much Knowledge Can You Pack Into the Parameters of a Language Model? *EMNLP*. [https://doi.org/10.18653/v1/2020.emnlp-main.437](https://doi.org/10.18653/v1/2020.emnlp-main.437)

[^BaezaYates2011]: Baeza-Yates, R., & Ribeiro-Neto, B. (2011). *Modern Information Retrieval: The Concepts and Technology behind Search* (2nd ed.). Addison-Wesley.

[^Croft2010]: Croft, W. B., Metzler, D., & Strohman, T. (2010). *Search Engines: Information Retrieval in Practice*. Addison-Wesley.

[^Lin2021TruthfulQA]: Lin, S., Hilton, J., & Evans, O. (2021). TruthfulQA: Measuring How Models Mimic Human Falsehoods. *arXiv preprint*. [https://arxiv.org/abs/2109.07958](https://arxiv.org/abs/2109.07958)

[^Min2023FactScore]: Min, S., Krishna, K., Lewis, M., Zettlemoyer, L., & Hajishirzi, H. (2023). FactScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. *EMNLP*. [https://arxiv.org/abs/2305.14251](https://arxiv.org/abs/2305.14251)

[^Xiong2020ANCE]: Xiong, L., Xiong, C., Li, Y., Tang, K.-F., Liu, J., Bennett, P., Ahmed, J., & Overwijk, A. (2020). Approximate Nearest Neighbor Negative Contrastive Learning for Dense Text Retrieval. *ICLR*. [https://arxiv.org/abs/2007.00808](https://arxiv.org/abs/2007.00808)

[^Zhang2020BERTScore]: Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q., & Artzi, Y. (2020). BERTScore: Evaluating Text Generation with BERT. *ICLR*. [https://arxiv.org/abs/1904.09675](https://arxiv.org/abs/1904.09675)

---

# PARTIE III — Application pratique : étude de cas ScribBERT

Cette dernière partie applique le cadre méthodologique des Parties I et II au cas de ScribBERT. Conformément au principe anti-redondance énoncé en introduction de la Partie II, ce qui est déjà décrit en Ch. 4 (théorie des leviers) n'est pas répété ici : on documente uniquement les **choix réalisés** et leurs **justifications**.

La structure est la suivante :
- **Ch. 7** : architecture déployée et choix techniques.
- **Ch. 8a** : résultats quantitatifs.
- **Ch. 8b** : analyse qualitative et étude d'erreurs.
- **Ch. 9** : enjeux éthiques, réglementaires et industriels.
- **Ch. 10** : discussion et perspectives.

## Chapitre 7 — Mise en œuvre du système RAG ScribBERT

### 7.1. Contexte et historique du projet

Le projet ScribBERT a été initié en deuxième année d'alternance, après une première année consacrée à l'immersion métier au sein du département P2S et à la cartographie des usages documentaires. Le développement s'est étalé sur **environ un an et demi**, en deux phases :

1. **Phase POC** (Proof of Concept) : prototype rapide visant à valider la faisabilité technique et l'appétence des utilisateurs métier.
2. **Phase exploratoire / industrialisation** : benchmark systématique des composants, durcissement de l'architecture, préparation à la mise en production.

Ce mémoire documente principalement la phase exploratoire, qui constitue le terrain d'application du protocole d'évaluation.

### 7.2. Architecture déployée

#### 7.2.1. Vue d'ensemble

ScribBERT suit l'architecture RAG canonique décrite au Ch. 2.3, instanciée comme suit :

```
[Documents PDF]
      ↓ (extraction + conversion)
[Documents .md]
      ↓ (chunking custom regex)
[Chunks + métadonnées]
      ↓ (embedding)
[Index vectoriel ChromaDB]
                                ┌─────────────────┐
[Requête utilisateur] ─────────►│ FastAPI backend │
                                │   - retrieval   │
                                │   - filtres     │◄─── [UI ReactJS]
                                │   - assemblage  │
                                │   - prompt LLM  │
                                └─────────────────┘
                                        ↓
                                  [Réponse + sources]
```

#### 7.2.2. Stack technique

| Composant | Choix | Justification |
|-----------|-------|---------------|
| **Langage backend** | Python 3.x | Écosystème IA dominant, compatibilité avec les bibliothèques d'embedding et LLM |
| **Orchestration RAG** | LangChain | Maturité, intégrations préexistantes (loaders, splitters, retrievers, chains) ; permet de pivoter rapidement entre fournisseurs |
| **Calcul tensoriel** | TensorFlow | Présence en interne, compatibilité GPU sur le cluster |
| **Base vectorielle** | ChromaDB | Léger, embeddable, gestion native des métadonnées et du filtrage, déploiement local sans dépendance cloud |
| **API** | FastAPI | Performance asynchrone, OpenAPI auto-généré, intégration naturelle avec Pydantic |
| **Frontend** | ReactJS (codé à la main) | Contrôle total de l'UX, intégration avec la charte graphique interne, pas de dépendance à un framework no-code |
| **Hébergement (POC)** | Cluster Kubernetes local au **LabTP** (équipe Lab TP Innovation) | Souveraineté des données, pas de transit vers cloud externe, scalabilité interne |

Ce choix d'une stack majoritairement open-source et auto-hébergée répond aux contraintes de **confidentialité** (les référentiels HSE peuvent contenir des informations sensibles sur les sites et les procédures) et d'**indépendance** vis-à-vis de fournisseurs externes pour une éventuelle exploitation à long terme.

#### 7.2.3. Pipeline d'ingestion

Le pipeline d'ingestion transforme un PDF source en chunks indexés. Étapes :

1. **Extraction** : conversion PDF → Markdown via **[À compléter : outil retenu, ex. pymupdf, marker, unstructured]**, choix qui préserve mieux la mise en forme (titres, listes, tableaux) que l'extraction texte brut.
2. **Nettoyage** : suppression des en-têtes/pieds de page répétitifs, normalisation des caractères spéciaux.
3. **Chunking** : découpage par regex sur les marqueurs structurels (titres Markdown `#`, `##`, séparateurs de paragraphes), avec contrainte de taille cible (~1200 tokens) et overlap (~50 tokens). Détails en § 7.4.
4. **Enrichissement métadonnées** : ajout pour chaque chunk de : `nom_document`, `entité_émettrice`, `langue`, `position_dans_doc`.
5. **Embedding** : calcul vectoriel via le modèle retenu (§ 7.5).
6. **Indexation** : insertion dans ChromaDB avec la collection appropriée.

L'étape 1 est actuellement la plus fragile : les PDFs HSE comportent souvent des **tableaux** (tableaux de risques, matrices RACI, tableaux d'EPI par activité) et des **schémas** (logigrammes de procédure, schémas d'installation). Dans le POC, ces éléments sont **ignorés** ou linéarisés grossièrement. Pour la version production, une chaîne **image-to-text contextualisée** est en cours d'étude : un modèle multimodal génère une description textuelle de chaque image/tableau, conserve le lien vers l'image originale, et l'injecte comme un chunk enrichi. Cette piste sera évaluée séparément (Ch. 10, perspectives).

#### 7.2.4. UI et expérience utilisateur

L'interface ReactJS expose :
- une **zone de saisie** en langage naturel ;
- un **filtre** optionnel sur les métadonnées (entité émettrice, langue) ;
- la **réponse générée** avec citations cliquables ;
- pour chaque citation, un **panneau latéral** affichant l'extrait source, le nom du document et la possibilité de télécharger le PDF d'origine ;
- un **disclaimer permanent** rappelant que la réponse n'engage pas la responsabilité du système et que l'utilisateur reste tenu de vérifier les sources (cf. § 9.3).

### 7.3. Description du corpus

| Caractéristique | Valeur |
|-----------------|--------|
| **Périmètre** | Documents santé-sécurité du siège de Bouygues TP |
| **Volume** | ~100 documents PDF |
| **Langues** | ≈ 50 % français, 50 % anglais |
| **Taille des documents** | De quelques pages à 80 pages |
| **Types** | Procédures, standards, guides méthodologiques, fiches sécurité |
| **Mise à jour** | Annuelle environ |
| **Éléments non-textuels** | Tableaux et schémas présents (non gérés dans le POC, prévus en production) |

Cette taille reste modeste à l'échelle d'un benchmark IR (BEIR utilise des corpus de 10⁵–10⁶ documents), mais elle est **représentative** d'un cas d'usage d'entreprise : un corpus expert, multilingue, à forte densité informationnelle, où chaque document compte. Le défi n'est pas le passage à l'échelle, mais la **qualité fine** du retrieval et de la génération sur un domaine spécialisé.

À noter : à terme, l'extension envisagée couvre les référentiels HSE de l'ensemble des filiales et chantiers de Bouygues TP, ce qui multiplierait le volume par un ordre de grandeur et ferait apparaître des problématiques nouvelles (variantes locales, contradictions inter-entités, multilinguisme étendu).

### 7.4. Choix de chunking et prétraitement

Conformément à la grille du Ch. 4.2, la stratégie retenue est un **chunking structurel custom**, justifié comme suit :

- les documents PDF sont d'abord convertis en **Markdown** pour préserver la hiérarchie (titres, listes, mise en forme) qui est porteuse de sens dans des référentiels normatifs ;
- des **expressions régulières** identifient les séparateurs structurels (titres `#`, `##`, `###`, paragraphes) et découpent le texte en unités correspondant à des **paragraphes ou sous-sections** ;
- la cible de taille est d'**environ 1200 tokens** par chunk, ce qui correspond empiriquement à un compromis entre :
  - assez large pour contenir une règle complète avec ses conditions et ses exceptions (cf. risque d'omission identifié au Ch. 5.5.4),
  - assez petit pour rester discriminant à l'embedding et économique en tokens lors de l'injection dans le contexte LLM ;
- l'**overlap est de ~50 tokens**, soit une valeur faible (≈ 4 %), qui suffit à amortir des coupures malheureuses sans gonfler significativement l'index ;
- une **fenêtre contextuelle** est ajoutée à la récupération : pour chaque chunk retourné par le retrieval, les chunks $n-1$ et $n+1$ sont automatiquement adjoints avant injection dans le contexte LLM. Cette mécanique compense un overlap faible et restaure le contexte amont/aval, particulièrement utile pour les références anaphoriques (« cette règle », « les EPI mentionnés ») et pour la cohérence procédurale.

Les métadonnées attachées à chaque chunk sont actuellement : `nom_document`, `entité_émettrice`, `langue`. Une extension du schéma (ajout de `date_validation`, `niveau_autorité`, `section_titre`) est identifiée comme amélioration prioritaire pour la version production.

### 7.5. Choix d'embedding et de LLM

#### 7.5.1. Phase POC

Le POC initial a utilisé **GPT-3.5 Turbo** comme générateur, choisi pour :
- la rapidité de mise en œuvre (API mature),
- un compromis coût/qualité acceptable pour valider la faisabilité,
- l'absence de contrainte forte de confidentialité à ce stade exploratoire.

Le modèle d'embedding du POC était **[À compléter : modèle d'embedding utilisé en POC, probablement `text-embedding-ada-002` ou un sentence-transformer]**.

Cette configuration a permis de valider l'intérêt utilisateur et de débloquer la phase exploratoire suivante.

#### 7.5.2. Phase exploratoire — benchmark systématique

La phase exploratoire a consisté en un **benchmark de 48 configurations** : **12 modèles d'embedding** distincts évalués chacun sous **4 combinaisons de paramètres** (taille de chunk, top-$k$, présence/absence de filtre par score, **[À compléter : axe précis du plan factoriel]**).

Les modèles évalués couvrent les familles suivantes (cf. Ch. 4.1.1) :
- **[À compléter : liste des 12 modèles testés]** — intégrant typiquement des modèles open-source francophones (ex. famille Solon, sentence-CamemBERT), multilingues (E5, BGE-M3, Jina), et propriétaires (OpenAI text-embedding-3, Cohere) à titre de référence.

Pour chaque configuration, les métriques suivantes ont été collectées sur le jeu de test interne (§ 8a.2) :
- métriques de retrieval (Recall@k, MRR), conformément au Ch. 5.1.1 ;
- évaluation qualitative des réponses générées, sur la grille définie au Ch. 5.2.2.

**[À compléter : modèle d'embedding finalement retenu et critères ayant emporté la décision (qualité brute, coût d'inférence, possibilité d'auto-hébergement, taille de l'index résultant)].**

**[À compléter : LLM retenu pour la phase exploratoire / production, et justification — choix entre conservation de GPT-3.5/4 via Azure OpenAI FR, basculement vers un modèle open-weights auto-hébergé (Mistral, Llama 3) au LabTP, ou modèle souverain].**

### 7.6. Configuration du retrieval

| Paramètre | Valeur retenue | Renvoi théorique |
|-----------|----------------|------------------|
| Type de retrieval | Dense pur | Ch. 4.3.2 (hybridation BM25+dense identifiée comme amélioration) |
| Modèle d'embedding | **[À compléter]** | Ch. 4.1, § 7.5 |
| Similarité | Cosinus (par défaut ChromaDB) | Ch. 4.3.1 |
| Top-$k$ | **[À compléter, typiquement 5–10]** | Ch. 4.3.5 |
| Filtre par score | Oui — seuil minimal sur le score de similarité, en dessous duquel le chunk est écarté | Ch. 5.1.2 (lutte anti-hallucination par grounding faible) |
| Reranking | Non (POC) — étude en cours pour la production | Ch. 4.3.3 |
| Filtres métadonnées | Disponibles via ChromaDB sur : `nom`, `entité`, `langue` | Ch. 4.3.4 |
| Contextualisation | Adjonction des chunks $n-1$ et $n+1$ pour chaque chunk retourné | § 7.4 |

Le choix d'un **dense pur** s'explique par la simplicité d'implémentation au POC et par la qualité jugée suffisante en évaluation interne. L'**hybridation sparse+dense** (BM25 + embeddings) reste une amélioration prioritaire, d'autant plus pertinente que le corpus contient de nombreuses **références exactes** (numéros de procédure, codes EPI, références normatives) que BM25 capture mieux que les embeddings (cf. analyse Ch. 4.3.2).

Le **filtrage par score** est une garde-fou simple mais efficace : si aucun chunk ne dépasse le seuil, le système retourne un message « information non trouvée dans les référentiels » plutôt que de générer une réponse non ancrée. Cela répond directement à l'exigence de **refus contrôlé** (Ch. 4.4.6).

### 7.7. Configuration de la génération

**Prompt** : structure conforme aux principes énoncés au Ch. 4.4.2 :
- instruction système rappelant le rôle (assistant santé-sécurité, ancrage strict sur les sources),
- consigne explicite de citation des sources et d'aveu d'ignorance le cas échéant,
- consignes de format (réponse synthétique, structurée, avec liens vers les sources).

**[À compléter : texte intégral du prompt système, ou au moins les consignes-clés]**.

**Paramètres de décodage** :
- **Température** : **[À compléter, recommandation : 0 ou 0.1 pour stabilité maximale, conformément à Ch. 4.4.4]** ;
- **Max tokens** : **[À compléter]** ;
- **Seed** : fixé pour reproductibilité.

**Citations** : format inline `[n]` renvoyant à une liste numérotée en fin de réponse, chaque entrée pointant vers le document source via un identifiant unique. Le frontend ReactJS rend ces citations cliquables et affiche l'extrait dans un panneau latéral.

### 7.8. Synthèse des choix et limites assumées du POC

Le POC ScribBERT, dans sa version actuelle, présente trois limites assumées qui orientent les pistes d'amélioration :

1. **Pas d'hybridation sparse+dense** : limite identifiée pour les requêtes contenant des références exactes.
2. **Pas de reranking** : la précision du top-$k$ pourrait être améliorée via un cross-encoder.
3. **Pas de gestion des tableaux et schémas** : pertes informationnelles sur des contenus à forte valeur HSE (matrices de risques, logigrammes).

Ces trois axes constituent les priorités pour le passage en production, et seront discutés en perspective au Ch. 10.

## Chapitre 8a — Résultats quantitatifs

> **Note méthodologique** : les retours utilisateurs collectés lors de la phase de test ont été qualitatifs et globalement positifs. Aucun protocole d'évaluation automatisé selon le cadre des Ch. 5 et 6 n'a été instancié de bout en bout au moment de la rédaction. Ce chapitre est donc structuré comme un **plan d'évaluation à exécuter**, avec des emplacements `[À compléter]` pour les valeurs à mesurer. Il constitue le **mode d'emploi du protocole** appliqué à ScribBERT.

### 8a.1. Protocole expérimental instancié

#### 8a.1.1. Configurations testées

Les configurations comparées dans la phase exploratoire correspondent au plan factoriel **12 modèles d'embedding × 4 jeux de paramètres = 48 configurations**, déjà évoqué en § 7.5.2. Les axes du plan factoriel sont :

- **Axe 1 — Modèle d'embedding** : 12 modèles couvrant les familles francophone, multilingue, propriétaire (cf. § 7.5.2).
- **Axe 2 — Combinaisons de paramètres** : **[À compléter — 4 combinaisons portant typiquement sur top-$k$, taille de chunk, seuil de filtrage par score]**.

Les autres composants (LLM, prompt, type de retrieval) sont **gelés** à leur valeur de référence (§ 7.5–7.7) pour isoler l'effet des paramètres testés.

#### 8a.1.2. Jeu de test

Le jeu de test utilisé dans la phase exploratoire compte **environ 20 questions de référence**, construites manuellement à partir d'une connaissance directe du corpus et des cas d'usage observés. Ces questions couvrent **[À compléter — répartition par type : factuelles, procédurales, conditionnelles ; et par langue]**.

Cette taille est inférieure aux 150–300 questions recommandées au Ch. 5.3.4 pour une analyse statistique robuste : les comparaisons entre configurations doivent donc être lues avec prudence et complétées par une **extension du jeu de test** selon les recommandations du Ch. 10.

Pour chaque question, sont annotés (lorsque disponibles) :
- une réponse-or attendue,
- les passages-or (chunks contenant l'information nécessaire),
- la difficulté estimée et le type de question.

#### 8a.1.3. Conditions d'exécution

- Index vectoriel reconstruit pour chaque modèle d'embedding testé (réutilisation impossible).
- Seed fixe pour reproductibilité.
- Logs complets conservés pour chaque exécution conformément au schéma du Ch. 5.4.4.

### 8a.2. Résultats retrieval

**[À compléter]** — Tableau de Recall@k, MRR, nDCG par configuration :

| Modèle d'embedding | Recall@5 | Recall@10 | MRR | nDCG@10 |
|--------------------|----------|-----------|-----|---------|
| Modèle 1 | [...] | [...] | [...] | [...] |
| Modèle 2 | [...] | [...] | [...] | [...] |
| ... | | | | |

**Observations à formuler** :
- Effet du modèle d'embedding (modèles francophones spécialisés vs multilingues vs propriétaires).
- Effet de la taille de chunk et du top-$k$.
- Comportement spécifique sur les questions FR vs EN.
- Identification des questions systématiquement échouées par toutes les configurations (problèmes de corpus ou de formulation, plutôt que de modèle).

### 8a.3. Résultats génération

**[À compléter]** — Pour la (les) configuration(s) retenue(s), métriques de Ch. 5.1.2 et 5.1.3 :

| Métrique | Valeur (médiane, IQR) |
|----------|------------------------|
| Faithfulness | [...] |
| Answer relevance | [...] |
| Completeness | [...] |
| Citation correctness | [...] |
| Modality preservation (HSE) | [...] |

L'évaluation s'appuie sur :
- un **LLM-juge** distinct du générateur, instruit selon la grille définie au Ch. 5.2.1 ;
- une **validation humaine** sur un sous-échantillon stratifié (10–20 questions critiques), avec accord inter-annotateurs mesuré.

### 8a.4. Résultats stabilité

**[À compléter]** — Application du protocole du Ch. 6.5 :

- Stability@retrieval (Jaccard inter-runs sur top-$k$) : [...]
- Stability@answer (BERTScore inter-runs) : [...]
- Flip rate (proportion de questions où le verdict change entre runs) : [...]
- Robustesse aux paraphrases : [...]

À ce stade, la température étant fixée à une valeur faible (cf. § 7.7), on s'attend à une stabilité élevée. Les sources de variance résiduelle proviennent principalement de :
- l'éventuel non-déterminisme du LLM,
- l'ordre des passages égaux en score à la sortie de ChromaDB,
- la sensibilité aux paraphrases de la requête.

### 8a.5. Résultats end-to-end et couplage retrieval ↔ génération

**[À compléter]** — Analyse croisée :

- corrélation entre Recall@k et faithfulness final (un retrieval plus large dégrade-t-il la génération ?) ;
- proportion d'erreurs « localisées au retrieval » vs « localisées à la génération » (typologie Ch. 5.5.4) ;
- effet ROC : courbe seuil de filtrage par score vs taux de refus / taux d'erreur.

### 8a.6. Coût opérationnel

**[À compléter]** — Latence P50/P95 par étape (extraction métadonnées, embedding requête, recherche ChromaDB, appel LLM, post-traitement) ; coût par requête en € selon le LLM retenu.

## Chapitre 8b — Analyse qualitative et étude d'erreurs

### 8b.1. Méthodologie

La phase de test utilisateur menée pendant le projet a recueilli des retours **majoritairement positifs**, sans toutefois mettre en place une typologie d'erreurs systématique. Ce chapitre propose une grille d'analyse qualitative à appliquer sur les sorties du protocole § 8a, structurée selon la typologie d'erreurs définie au Ch. 5.5.4.

### 8b.2. Typologie d'erreurs observées (template)

| Catégorie d'erreur | Fréquence observée | Exemple représentatif | Cause identifiée | Action corrective |
|--------------------|--------------------|-----------------------|------------------|-------------------|
| Retrieval miss | [À compléter] | [À compléter] | [À compléter] | [À compléter] |
| Retrieval bruit | [À compléter] | [À compléter] | [À compléter] | [À compléter] |
| Hallucination factuelle | [À compléter] | [À compléter] | [À compléter] | [À compléter] |
| Omission d'exception | [À compléter] | [À compléter] | [À compléter] | [À compléter] |
| Inversion de modalité | [À compléter] | [À compléter] | [À compléter] | [À compléter] |
| Contradiction silencieuse | [À compléter] | [À compléter] | [À compléter] | [À compléter] |
| Refus à tort | [À compléter] | [À compléter] | [À compléter] | [À compléter] |
| Hors-périmètre accepté | [À compléter] | [À compléter] | [À compléter] | [À compléter] |

### 8b.3. Études de cas

**[À compléter]** — Sélection de 5 à 10 cas représentatifs, chacun documenté selon le format :

- **Question** posée (FR ou EN) ;
- **Top-$k$ retourné** (identifiants chunks, scores, extraits clés) ;
- **Réponse générée** ;
- **Réponse-or** attendue ;
- **Diagnostic** (succès, type d'échec, localisation dans la chaîne) ;
- **Enseignement** transverse pour le système.

### 8b.4. Cas limites et ambiguïtés

Trois familles de cas limites identifiées dès la phase POC :

#### 8b.4.1. Acronymes et jargon métier

Les utilisateurs HSE emploient des acronymes (EPI, ATEX, EPC, PDP, etc.) que les embeddings généralistes peuvent mal contextualiser. **[À compléter : observations spécifiques sur la sensibilité du système retenu]**.

#### 8b.4.2. Multilinguisme et code-switching

Le corpus étant ~50 % anglophone, les questions FR peuvent attendre une réponse appuyée sur des passages EN (et vice-versa). **[À compléter : qualité observée sur les requêtes cross-lingue]**.

#### 8b.4.3. Hors-périmètre

Questions sortant du périmètre HSE (« Quel est le congé maternité ? », « Combien gagne un chef de chantier ? »). Le système doit refuser ; observer si le filtre par score est suffisant ou si des cas se faufilent. **[À compléter]**.

### 8b.5. Biais identifiés

**[À compléter]** — Pistes à investiguer :

- **Biais de corpus** : sur-représentation de certains domaines (ex. travail en hauteur très documenté vs risque chimique sous-documenté).
- **Biais de récence** : favorisation des documents récemment ajoutés (selon ordre dans l'index).
- **Biais de longueur** : tendance des LLMs à produire des réponses verbeuses, ce qui peut surestimer la complétude.
- **Biais linguistique** : qualité différentielle entre FR et EN selon le modèle d'embedding retenu.

### 8b.6. Retours utilisateurs (phase de test)

Une phase de test ouverte a été conduite auprès d'un panel d'utilisateurs internes du département P2S et au-delà. Les retours qualitatifs collectés ont été **globalement positifs**, en particulier sur :

- la **rapidité d'accès** à l'information par rapport à la consultation manuelle des PDF ;
- la **présence systématique des sources** rendant la vérification simple ;
- l'**ergonomie** de l'interface ReactJS et la possibilité de naviguer vers le document source.

Les axes d'amélioration remontés par les utilisateurs incluent **[À compléter — par exemple : meilleure gestion des questions de synthèse multi-procédures, traitement des tableaux, ajout d'un historique de conversation, recherche multi-tours]**.

Une **enquête structurée** (questionnaire avec échelles de Likert sur les dimensions de satisfaction, utilité, confiance) reste à mener pour passer de l'impression qualitative à une mesure consolidée.

## Chapitre 9 — Enjeux éthiques, réglementaires et industriels

L'industrialisation d'un RAG dans un domaine critique comme la santé-sécurité soulève des questions qui dépassent la performance technique : conformité réglementaire, responsabilité, gouvernance, acceptabilité. Ce chapitre les traite spécifiquement, ce qui était demandé par la nature du sujet et la maturité croissante du cadre européen sur l'IA.

### 9.1. Le cadre réglementaire européen : l'AI Act

#### 9.1.1. Classification du système

L'**AI Act européen** (Règlement UE 2024/1689), entré en vigueur en août 2024 avec une application progressive jusqu'à 2027, classe les systèmes d'IA selon leur niveau de risque. ScribBERT, en tant qu'assistant d'aide à la décision dans un contexte santé-sécurité, peut être analysé selon cette grille :

- **Risque inacceptable** : non concerné (pas de manipulation, pas de notation sociale).
- **Haut risque** : potentiellement concerné si l'on considère que le système contribue à la **gestion des risques pour la sécurité des travailleurs**, ce qui correspond aux usages listés dans l'annexe III du règlement (notamment dans le domaine de l'emploi et de la gestion des travailleurs). **[À approfondir avec le service juridique : qualification finale]**.
- **Risque limité** : concerné par les obligations de **transparence** (l'utilisateur doit savoir qu'il interagit avec une IA).
- **Risque minimal** : non applicable ici.

#### 9.1.2. Obligations applicables (en hypothèse haut risque)

Si ScribBERT est classifié haut risque, les obligations principales sont :

- **Système de gestion des risques** documenté et tenu à jour.
- **Qualité des données d'entraînement** — moins applicable ici (RAG, pas de fine-tuning), mais la **qualité du corpus** est un équivalent fonctionnel.
- **Documentation technique** détaillée et journaux d'événements.
- **Transparence** envers les utilisateurs (information claire sur la nature IA du système).
- **Contrôle humain** : possibilité d'intervention humaine, et fait que le système ne se substitue pas à un avis d'expert.
- **Robustesse, exactitude et cybersécurité** : niveau de performance documenté.

Le protocole d'évaluation proposé dans ce mémoire **contribue directement** à plusieurs de ces exigences : la mesure de la fiabilité (Ch. 5–6), la traçabilité des sources, la documentation des choix techniques (Ch. 7), constituent des éléments mobilisables pour la conformité.

#### 9.1.3. Articulation avec d'autres référentiels

ScribBERT relève également d'autres cadres susceptibles de s'appliquer :

- **Norme ISO/IEC 42001** sur les systèmes de management de l'IA ;
- **Norme ISO/IEC 23894** sur la gestion des risques en IA ;
- **Recommandations CNIL** sur l'IA (cycle 2023-2024) pour la partie données personnelles éventuelles.

### 9.2. RGPD et données internes

Bien que ScribBERT ne traite pas de données personnelles dans son corpus (référentiels de procédures), trois points RGPD méritent attention :

1. **Logs des requêtes utilisateurs** : si une requête contient des données personnelles (nom d'un collaborateur, identifiant chantier), elle est journalisée à des fins d'amélioration. Il faut définir une **durée de conservation**, les **finalités** précises, et garantir un **droit d'accès / suppression**.
2. **Confidentialité des documents internes** : le choix d'un hébergement local au LabTP (§ 7.2.2) garantit la non-exposition à des fournisseurs cloud externes pour le POC. La bascule éventuelle vers un LLM API (OpenAI, Anthropic) en production exigerait une analyse complémentaire, idéalement via Azure OpenAI EU/FR avec contrats DPA appropriés.
3. **Traçabilité des décisions** : si une décision opérationnelle (ex. report d'une intervention) s'appuie sur une réponse de ScribBERT, la trace doit être conservée — avec la version du modèle, la version du corpus et la réponse exacte — pour permettre une analyse a posteriori.

### 9.3. Responsabilité en contexte HSE

#### 9.3.1. La question de la responsabilité

En cas d'accident sur chantier, si une décision de prévention s'appuie sur une réponse erronée de ScribBERT, qui est responsable ? Plusieurs niveaux d'analyse :

- **Responsabilité juridique** : l'employeur reste responsable de la sécurité de ses salariés (Code du travail français). L'outil IA n'est qu'un moyen.
- **Responsabilité du système** : l'éditeur (ici Bouygues TP en tant que développeur interne) doit pouvoir documenter ses choix et ses tests (cf. AI Act).
- **Responsabilité de l'utilisateur** : le préventeur reste tenu de son devoir de vérification, ce qui justifie le **disclaimer affiché**.

#### 9.3.2. Le disclaimer comme mesure de mitigation

ScribBERT affiche actuellement un **disclaimer permanent** rappelant que :
- la responsabilité de la qualité des réponses n'incombe pas au système ;
- l'utilisateur doit faire appel à son **esprit critique** et **vérifier les documents sources** avant toute action opérationnelle.

Ce disclaimer est une mesure nécessaire mais **non suffisante** : la jurisprudence européenne sur les outils d'aide à la décision tend à considérer qu'un disclaimer ne dégage pas l'éditeur de toute responsabilité, particulièrement si l'outil est présenté comme « expert » ou « fiable ». Les renforcements possibles incluent :

- afficher un **score de confiance** par réponse, pour calibrer la vigilance ;
- **mettre en avant les sources** plus que la réponse synthétisée, l'utilisateur étant ainsi systématiquement renvoyé au document validé ;
- pour les réponses critiques (port d'EPI vital, mises en sécurité), recommander explicitement la **consultation d'un référent HSE** humain.

#### 9.3.3. Supervision humaine

Le principe de **human-in-the-loop** est central pour les systèmes IA en domaine critique. Pour ScribBERT, cela peut prendre plusieurs formes :

- **Revue périodique des logs** par l'équipe P2S, avec analyse des questions récurrentes et des cas d'erreur détectés ;
- **Procédure d'escalade** : un canal pour signaler une réponse erronée, avec mise à jour du corpus ou du système ;
- **Validation experte** des évolutions majeures (changement de modèle, mise à jour massive du corpus) avant déploiement.

### 9.4. Gouvernance d'un RAG d'entreprise

L'industrialisation impose une discipline de gouvernance que le POC peut tolérer, mais que la production exige :

- **Versioning** : chaque mise en production identifie sans ambiguïté la version du modèle d'embedding, du LLM, du corpus, du prompt et du code applicatif.
- **Pipeline CI/CD avec tests d'évaluation automatisés** : avant tout déploiement, le jeu de test est passé sur la nouvelle configuration et les métriques sont comparées à la baseline.
- **Audit trail** : chaque réponse produite est logguée avec l'ensemble des éléments permettant de la rejouer (cf. Ch. 5.4.4).
- **Plan de gestion de l'obsolescence** : les modèles propriétaires sont régulièrement dépréciés ; un plan de migration doit exister.
- **Politique de mise à jour du corpus** : workflow de validation pour l'ajout / la modification d'un document, avec invalidation et reconstruction de l'index.
- **Comité de gouvernance** réunissant IT, métier, juridique, sécurité — décisionnaire sur les évolutions majeures.

### 9.5. Acceptabilité et conduite du changement

La meilleure technologie échoue si les utilisateurs ne l'adoptent pas. Trois facteurs ont été identifiés comme déterminants pour ScribBERT :

1. **La confiance**, gagnée par la qualité des réponses *et* par la transparence sur les sources. Les retours utilisateurs (§ 8b.6) confirment que la présence systématique des citations est un facteur clé d'adoption.
2. **L'utilité perçue** par rapport à l'alternative (recherche manuelle dans les PDF, demande à un expert). ScribBERT doit faire gagner du temps **sans dégrader la qualité de la décision**.
3. **L'accompagnement** : formation initiale, communication interne, identification d'**ambassadeurs** dans les équipes pour porter l'outil.

Une perspective intéressante est de considérer ScribBERT non pas comme un **substitut** à l'expert HSE, mais comme un **amplificateur** : il permet aux préventeurs de répondre plus vite aux questions répétitives, libérant du temps pour les sujets complexes qui requièrent un jugement humain.

## Chapitre 10 — Discussion et perspectives

### 10.1. Interprétation des résultats et synthèse des enseignements

Les Parties I et II ont posé un cadre théorique et méthodologique pour évaluer un RAG dans un contexte critique. La Partie III a montré comment ce cadre s'applique à un cas réel (ScribBERT), tout en soulignant que **l'évaluation systématique selon ce protocole reste à finaliser** : la phase exploratoire a produit un benchmark de 48 configurations sur un jeu de test interne de ~20 questions, et une phase de test utilisateur a recueilli des retours qualitatifs positifs. L'instanciation complète du protocole (Ch. 5–6) sur ScribBERT constitue la suite naturelle de ce travail.

Plusieurs enseignements méthodologiques se dégagent néanmoins :

1. **La fiabilité d'un RAG ne se réduit pas à un score** : c'est un faisceau de dimensions (retrieval, fidélité, pertinence réponse, stabilité, traçabilité) qui doivent être mesurées séparément pour pouvoir diagnostiquer.
2. **Les choix d'ingénierie (chunking, contextualisation, filtrage par score) ont un impact comparable à celui du choix du modèle** : il est tentant de centrer l'attention sur le LLM, mais l'expérience ScribBERT confirme qu'un chunking adapté au corpus et un filtrage de seuil bien calibré pèsent au moins autant.
3. **La stabilité est sous-évaluée dans les frameworks usuels** : pour un système en production sur un sujet critique, la variance inter-runs et la robustesse aux paraphrases méritent un protocole dédié (Ch. 6).
4. **La traçabilité est à la fois un critère technique et un enjeu de confiance** : citer les sources de manière vérifiable est probablement le facteur le plus fort d'acceptabilité utilisateur observé.

### 10.2. Limites méthodologiques

#### 10.2.1. Limites du jeu de test

Le jeu de test interne (~20 questions) est insuffisant pour des comparaisons statistiques fines (cf. Ch. 5.3.4). Une priorité immédiate est l'**extension à 150–300 questions** stratifiées, avec annotation des passages-or et réponses-or par des experts P2S.

#### 10.2.2. Limites du protocole appliqué

Le benchmark des 48 configurations a porté sur des métriques de retrieval et une évaluation qualitative. Une instanciation complète du Ch. 5 (faithfulness via RAGAS, NLI ou LLM-juge ; stability via le protocole Ch. 6.5) reste à mener.

#### 10.2.3. Limites du périmètre

Le corpus actuel se limite aux documents du siège, en français et anglais. L'extension aux filiales et chantiers internationaux fera émerger des défis nouveaux (variantes locales, contradictions inter-entités, langues additionnelles).

#### 10.2.4. Précautions d'interprétation

Les retours utilisateurs positifs de la phase de test sont un signal important mais ne se substituent pas à une évaluation systématique. **L'effet de nouveauté** et l'**enthousiasme métier** peuvent biaiser les retours initiaux ; une évaluation à 6 et 12 mois post-déploiement serait nécessaire pour mesurer l'usage stable.

### 10.3. Apports du travail

#### 10.3.1. Apports théoriques

- Une **définition opératoire de la fiabilité** d'un RAG (Ch. 3.3) qui décompose le concept en cinq dimensions mesurables.
- Une **clarification du rôle de la stabilité** comme dimension à part entière de la fiabilité, méritant un protocole d'évaluation dédié (Ch. 6).
- Une **lecture critique des frameworks d'évaluation existants** (RAGAS, TruLens, LLM-as-judge), avec mise en évidence de leurs limites en domaine critique.

#### 10.3.2. Apports méthodologiques

- Un **catalogue structuré des leviers techniques** d'un RAG avec leurs compromis (Ch. 4), réutilisable pour tout projet RAG d'entreprise.
- Un **protocole d'évaluation diagnostique** (Ch. 5) organisé par dimension, qui permet de localiser l'origine des erreurs plutôt que de juger globalement.
- Un **protocole de stabilité** (Ch. 6) directement applicable.

#### 10.3.3. Apports industriels (cas ScribBERT)

- Une architecture RAG fonctionnelle et **adaptée aux contraintes de Bouygues TP** (souveraineté des données, multilinguisme FR/EN, corpus normatif).
- Une **identification claire des limites du POC** (hybridation, reranking, gestion des tableaux) et un plan d'amélioration priorisé.

### 10.4. Recommandations pour évaluer un RAG en contexte critique

Synthèse des bonnes pratiques pour un futur projet :

1. **Commencer par définir la fiabilité opérationnellement** dans le contexte du domaine, avec ses dimensions critiques.
2. **Construire un jeu de test représentatif et stratifié dès le début** (≥ 150 questions, par type, difficulté, criticité).
3. **Évaluer chaque composant avant l'évaluation end-to-end** pour permettre le diagnostic.
4. **Tester systématiquement la stabilité** (pas seulement la qualité moyenne).
5. **Combiner LLM-as-judge et validation humaine** sur un échantillon, pour calibrer.
6. **Mesurer le coût opérationnel** (latence, €) en parallèle de la qualité.
7. **Versionner et logger** tout, dès le POC : on ne peut pas reproduire ce qui n'est pas tracé.
8. **Anticiper la conformité AI Act et les enjeux de responsabilité** dès la conception, pas après le déploiement.

### 10.5. Perspectives

#### 10.5.1. Améliorations techniques court terme (ScribBERT)

- **Hybridation BM25 + dense** pour améliorer le rappel sur les références exactes.
- **Reranker cross-encoder** pour la précision du top-$k$ injecté.
- **Image-to-text contextualisé** pour intégrer tableaux et schémas.
- **Enrichissement des métadonnées** (date de validation, niveau d'autorité, section).
- **Évaluation systématique** selon le protocole Ch. 5–6.

#### 10.5.2. Pistes de recherche moyen terme

- **Fine-tuning d'un modèle d'embedding sur le corpus HSE** (apprentissage contrastif sur paires question/passage), pour combler le manque de modèles spécialisés HSE/BTP identifié au Ch. 4.1.1.
- **GraphRAG** : exploiter une représentation en graphe des entités HSE (procédures, EPI, risques, situations) pour des requêtes nécessitant un raisonnement multi-saut.
- **Agentic RAG** : pour les questions complexes, décomposer en sous-questions, lancer plusieurs retrievals, agréger.
- **RAG multimodal** : intégrer images, schémas, vidéos de formation comme sources de premier niveau.

#### 10.5.3. Généralisation à d'autres domaines

Le cadre méthodologique proposé est **transférable à d'autres domaines réglementaires et techniques** : juridique (jurisprudence, contrats), médical (recommandations, protocoles), conformité (LCB-FT, ESG), maintenance industrielle (procédures, modes opératoires). Les adaptations principales concernent :

- la définition opérationnelle de la fiabilité dans le domaine cible (quelles dimensions sont critiques ?) ;
- la construction du jeu de test (qui annote ? selon quels critères ?) ;
- les contraintes réglementaires spécifiques (RGPD santé, secret professionnel juridique, etc.).

#### 10.5.4. Enjeux éthiques et de responsabilité à long terme

L'évolution des cadres réglementaires (AI Act, normes ISO 42001) et la jurisprudence à venir sur la responsabilité des systèmes IA en domaine critique vont préciser les exigences. Les systèmes RAG d'entreprise devront probablement, à terme :

- être audités par des tiers ;
- exposer des **garanties documentées** de fiabilité ;
- intégrer la supervision humaine non comme option mais comme exigence.

L'investissement méthodologique fait dans ce mémoire sur l'évaluation rigoureuse anticipe ces évolutions et positionne ScribBERT comme un cas d'usage exemplaire d'**IA industrielle responsable** dans le secteur de la construction.

---

## Conclusion générale

### Synthèse

Ce mémoire a abordé la question : *Comment évaluer la cohérence et la fiabilité d'un système RAG ?*

La réponse proposée s'articule en trois temps. En **Partie I**, le RAG a été replacé dans la lignée historique de la recherche d'information et formalisé comme une chaîne de décision dont les notions de pertinence, de cohérence et de fiabilité doivent être clarifiées et décomposées. En **Partie II**, un cadre méthodologique a été construit : catalogue des leviers techniques (Ch. 4), protocole d'évaluation diagnostique organisé selon cinq dimensions de la fiabilité (Ch. 5), et protocole spécifique de stabilité (Ch. 6) souvent négligé par les frameworks existants. En **Partie III**, ce cadre a été instancié sur ScribBERT, un assistant RAG développé pour le département P2S de Bouygues Travaux Publics, en documentant l'architecture déployée, les choix techniques justifiés, le plan d'évaluation à exécuter, ainsi que les enjeux éthiques et réglementaires associés.

### Apports

L'apport principal est **méthodologique** : une définition opératoire de la fiabilité, un cadre d'évaluation diagnostique et reproductible, et la mise en évidence de la stabilité comme dimension à part entière. L'apport **applicatif** consiste en une architecture RAG fonctionnelle adaptée aux contraintes d'un grand groupe de BTP (souveraineté, multilinguisme, criticité), et une identification claire des prochaines étapes d'industrialisation.

### Limites

Le travail comporte trois limites principales : (i) le jeu de test interne (~20 questions) est insuffisant pour des comparaisons statistiques robustes, (ii) le protocole d'évaluation complet (Ch. 5–6) reste à exécuter intégralement sur ScribBERT, et (iii) la généralisation des résultats à d'autres contextes documentaires nécessite une validation empirique sur d'autres corpus.

### Perspectives

À court terme, ScribBERT bénéficiera de l'application complète du protocole d'évaluation, de l'extension du jeu de test, et de l'intégration des améliorations identifiées (hybrid retrieval, reranking, gestion des tableaux). À moyen terme, le fine-tuning d'un modèle d'embedding sur le corpus HSE et l'exploration de variantes (GraphRAG, agentic RAG, RAG multimodal) constituent des axes de recherche pertinents. Le cadre méthodologique proposé est par ailleurs transférable à d'autres domaines réglementaires et techniques.

### Mot de la fin

L'industrialisation des systèmes RAG dans des contextes critiques est une réalité opérationnelle croissante, mais leur évaluation rigoureuse reste un chantier ouvert. Ce mémoire entend y contribuer en proposant un cadre transférable, en assumant que la fiabilité d'un système d'IA n'est pas un attribut binaire à proclamer, mais une **propriété multi-dimensionnelle à mesurer, à éprouver, et à gouverner dans le temps**.

---

## Glossaire des termes techniques

| Terme | Définition |
|-------|------------|
| **ANN** (*Approximate Nearest Neighbor*) | Algorithme de recherche du plus proche voisin approximatif, utilisé pour accélérer la recherche dans des espaces vectoriels de grande dimension (ex. HNSW, IVF, FAISS). |
| **BART** | Modèle de langage pré-entraîné de type séquence-à-séquence (encoder-decoder), développé par Meta AI, utilisé comme générateur dans l'architecture RAG originale. |
| **BERT** (*Bidirectional Encoder Representations from Transformers*) | Modèle Transformer pré-entraîné par masquage de tokens, produisant des représentations contextualisées des mots. Base de nombreux modèles d'embedding et de reranking. |
| **BERTScore** | Métrique d'évaluation de génération de texte mesurant la similarité sémantique token-à-token entre une réponse générée et une référence, à l'aide d'embeddings BERT. |
| **Bi-encodeur** (*Dual-encoder*) | Architecture où la requête et le passage sont encodés séparément en vecteurs denses, puis comparés par similarité (cosinus, produit scalaire). Rapide mais moins fin qu'un cross-encoder. |
| **BM25** (*Best Matching 25*) | Fonction de scoring probabiliste pour la recherche d'information, améliorant TF-IDF par normalisation de la longueur du document et saturation des fréquences de termes. Standard industriel. |
| **Chunk / Chunking** | Segment de texte issu du découpage d'un document. Le *chunking* est l'opération de segmentation qui détermine la granularité des unités indexées et récupérables dans un RAG. |
| **Cohérence** | Propriété d'un texte dont les idées s'enchaînent logiquement. En RAG, on distingue cohérence locale (linguistique), cohérence globale (discursive) et cohérence terminologique. |
| **Cohésion** | Marqueurs linguistiques (connecteurs, anaphores, référents) qui assurent la continuité formelle d'un texte. Distincte de la cohérence (organisation du sens). |
| **Cosinus (similarité)** | Mesure de similarité entre deux vecteurs, calculée comme le cosinus de l'angle entre eux. Valeur entre -1 et 1 ; utilisée pour comparer embeddings. |
| **Cross-encoder** | Architecture où la requête et le passage sont concaténés et traités ensemble par un Transformer, permettant des interactions fines token-à-token. Plus précis mais plus coûteux qu'un bi-encodeur. Utilisé en reranking. |
| **Dense retrieval** | Recherche de passages par comparaison de vecteurs denses (embeddings) représentant requêtes et documents. Capte synonymie et paraphrase, par opposition au sparse retrieval. |
| **DPR** (*Dense Passage Retrieval*) | Méthode de dense retrieval entraînée sur des paires question-passage, utilisant des bi-encodeurs BERT. Référence fondamentale du retrieval dense pour la QA ouverte. |
| **Embedding** | Représentation vectorielle continue (dense) d'un mot, d'une phrase ou d'un passage, apprise par un réseau de neurones. Capture des régularités sémantiques dans un espace géométrique. |
| **End-to-end** | Désigne un système ou une évaluation qui considère la chaîne complète (de la requête utilisateur à la réponse finale), par opposition à l'évaluation de composants isolés. |
| **Faithfulness / Groundedness** | Fidélité de la réponse générée par rapport aux sources récupérées. Une réponse est *grounded* si chacune de ses affirmations est justifiable par un passage du contexte. |
| **Fine-tuning** | Adaptation d'un modèle pré-entraîné à une tâche ou un domaine spécifique par entraînement supplémentaire sur des données ciblées. |
| **Hallucination** | Génération par un LLM d'informations plausibles mais factuellement incorrectes ou non supportées par les sources. Risque majeur en contexte RAG et HSE. |
| **Hard negatives** | Exemples négatifs (passages non pertinents) sémantiquement proches de la requête, utilisés pour entraîner des retrievers denses à mieux discriminer les passages réellement pertinents. |
| **HNSW** (*Hierarchical Navigable Small World*) | Structure d'index pour la recherche approximative du plus proche voisin, basée sur des graphes navigables hiérarchiques. Utilisée dans FAISS, Qdrant, etc. |
| **HSE** (*Hygiène, Sécurité, Environnement*) | Domaine de la prévention des risques professionnels et de la sécurité au travail. Contexte métier du cas d'usage ScribBERT. |
| **IDF** (*Inverse Document Frequency*) | Mesure de la rareté d'un terme dans un corpus. Plus un terme est rare, plus son IDF est élevé, et plus il est discriminant pour la recherche. |
| **IR** (*Information Retrieval*) | Recherche d'information : discipline visant à retrouver des documents ou passages pertinents en réponse à un besoin informationnel. |
| **LLM** (*Large Language Model*) | Modèle de langage de grande taille (milliards de paramètres), pré-entraîné sur de vastes corpus textuels, capable de générer du texte, répondre à des questions, résumer, etc. Ex. : GPT-4, Claude, Llama. |
| **LLM-as-judge** | Méthode d'évaluation utilisant un LLM pour noter la qualité des réponses d'un autre système selon une grille de critères prédéfinie. |
| **MRR** (*Mean Reciprocal Rank*) | Métrique IR mesurant en moyenne l'inverse du rang du premier résultat pertinent. Utile pour évaluer si *au moins un bon passage* apparaît tôt dans les résultats. |
| **nDCG** (*normalized Discounted Cumulative Gain*) | Métrique IR gérant la pertinence graduée, qui pénalise les documents pertinents placés à des rangs éloignés et normalise par le score idéal. |
| **Pipeline** | Chaîne de traitement séquentiel. En RAG, la pipeline comprend typiquement : ingestion, chunking, vectorisation, retrieval, reranking et génération. |
| **Precision@k** | Proportion de résultats pertinents parmi les *k* premiers résultats retournés par un système de recherche. |
| **Prompt** | Texte d'entrée fourni au LLM, comprenant la requête utilisateur et le contexte documentaire récupéré, éventuellement accompagné de consignes (format, citation, non-invention). |
| **QA** (*Question Answering*) | Tâche consistant à répondre automatiquement à une question, soit en extrayant un passage (QA extractive), soit en générant une réponse (QA générative). |
| **Query expansion** | Technique d'enrichissement automatique d'une requête avec des termes supplémentaires (synonymes, termes liés) pour améliorer le rappel de la recherche. |
| **RAG** (*Retrieval-Augmented Generation*) | Architecture combinant un système de recherche documentaire (retriever) et un modèle génératif (LLM) pour produire des réponses ancrées dans des sources externes. |
| **RAG-Sequence / RAG-Token** | Deux variantes de l'architecture RAG originale : RAG-Sequence utilise un même passage pour toute la réponse ; RAG-Token permet à chaque token de s'appuyer sur un passage différent. |
| **Rappel** (*Recall*) | Proportion des documents pertinents existants effectivement retrouvés par le système. |
| **Recall@k** | Proportion des documents pertinents retrouvés parmi les *k* premiers résultats. |
| **Reranking** | Étape de reclassement d'un ensemble de résultats candidats par un modèle plus fin (souvent un cross-encoder), après un premier retrieval rapide. |
| **Retrieval** | Phase de récupération de passages ou documents pertinents à partir d'un index, en réponse à une requête. |
| **Sparse retrieval** | Recherche basée sur des représentations creuses (haute dimension, beaucoup de zéros), comme BM25 ou TF-IDF. Interprétable et efficace sur les signaux lexicaux. |
| **TF-IDF** (*Term Frequency – Inverse Document Frequency*) | Pondération combinant la fréquence locale d'un terme dans un document (TF) et sa rareté dans le corpus (IDF). Base historique du scoring lexical en IR. |
| **Token** | Unité élémentaire de texte traitée par un modèle de langage (mot, sous-mot ou caractère selon le tokenizer). |
| **Transformer** | Architecture de réseau de neurones basée sur le mécanisme d'attention (*self-attention*), introduite en 2017. Fondement de BERT, GPT, BART et de la majorité des LLMs modernes. |
| **Vectorisation** | Processus de transformation d'un texte (mot, phrase, passage) en un vecteur numérique (embedding) via un modèle d'encodage. |

