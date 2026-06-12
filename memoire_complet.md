# Remerciements {-}

Ce mémoire doit beaucoup à des personnes sans lesquelles le projet ScribBERT n'aurait pas pris la forme qu'il a aujourd'hui.

Je remercie en premier lieu Flavien Martin, responsable Système & Appels d'offres au sein du département Prévention Santé-Sécurité de Bouygues Travaux Publics, pour la confiance qu'il m'a accordée, la liberté d'initiative dont j'ai pu disposer sur ce projet, et les échanges réguliers qui ont structuré ma compréhension des enjeux métier.

Je remercie chaleureusement Julien Larseneur, du pôle Intelligence Artificielle de Bouygues Travaux Publics, pour son encadrement technique exigeant et son insistance sur la rigueur méthodologique de l'évaluation. Beaucoup de choix présentés dans ce mémoire sont directement issus de nos discussions.

Je tiens également à remercier Aurélie Janssens, ma tutrice lors de la première partie de mon alternance et durant les tout débuts du projet ScribBERT, pour son accompagnement initial et la confiance qu'elle m'a accordée pour défricher ce sujet.

J'adresse mes remerciements à Laurent Knoll et Bruno Magnin, respectivement directeur Prévention Santé-Sécurité de Bouygues Travaux Publics et directeur Prévention Santé-Sécurité Sûreté de Bouygues Construction, pour leur soutien et leur confiance dans le projet. C'est grâce à eux qu'il est aujourd'hui en mesure d'être industrialisé.

Je remercie également Nicolas Derrez et Hervé Dit Lebas pour le prêt de la machine de test qui a rendu possibles les expérimentations locales sur modèles auto-hébergés, et plus largement pour la confiance qu'ils m'ont accordée en mettant ce matériel à disposition.

Mes remerciements vont enfin à l'ensemble des équipes du département Prévention Santé-Sécurité, à l'équipe du Pôle Intelligence Artificielle et au LabTP dans son intégralité pour les nombreux échanges qui ont nourri ce projet, ainsi qu'à l'ensemble du personnel de l'École Hexagone pour le cadre éducatif propice au développement d'un tel travail.

```{=latex}
\cleardoublepage
```

# Résumé {-}

Ce mémoire propose un cadre méthodologique pour évaluer la cohérence et la fiabilité des systèmes RAG (*Retrieval-Augmented Generation*) déployés en contexte industriel critique. Le cas d'application est ScribBERT, un agent conversationnel développé pour le département Prévention Santé-Sécurité de Bouygues Travaux Publics, destiné à permettre l'interrogation en langage naturel des référentiels santé-sécurité internes. ScribBERT n'agit pas directement sur des équipements ou des dispositifs de sécurité : il sert d'appui documentaire pour les décisions de prévention prises par des opérationnels (préventeurs, chefs de chantier, encadrement). C'est précisément parce qu'il s'insère dans cette chaîne de décision qu'une réponse erronée (par exemple une obligation restituée comme une simple recommandation) peut, en aval, orienter à tort un arbitrage de prévention. L'enjeu n'est donc pas d'éviter qu'une IA cause un accident, mais de garantir que sa contribution à la décision soit suffisamment fiable pour ne pas la dégrader, ce qui fait d'une évaluation rigoureuse un prérequis au déploiement.

Le travail s'articule en trois parties. La première replace le RAG dans la lignée historique de la recherche d'information et formalise les notions de pertinence, de cohérence et de fidélité aux sources. La deuxième construit un protocole d'évaluation reproductible structuré autour de cinq dimensions de la fiabilité (pertinence du *retrieval*, fidélité aux sources, pertinence de la réponse, stabilité, traçabilité), combinant métriques automatiques (Recall@k, MRR, nDCG, *faithfulness* via *LLM-as-judge*) et validation humaine ciblée. La troisième instancie ce protocole sur ScribBERT : *benchmark* des stratégies de *chunking*, des modèles de vectorisation et des configurations de *retrieval*, analyse d'erreurs typologique et étude de stabilité inter-runs.

Les résultats mettent en évidence la nécessité de séparer les erreurs de récupération et de génération, de stratifier l'analyse par type et criticité de question, et d'intégrer explicitement la mesure de stabilité dans toute comparaison de configurations. Au-delà de ScribBERT, le cadre proposé est transférable à d'autres déploiements RAG en environnement documentaire spécialisé soumis à des exigences de fiabilité élevées.

**Mots-clés :** RAG (*Retrieval-Augmented Generation*), évaluation de systèmes IA, fiabilité, *chunking*, vectorisation, *LLM-as-judge*, santé-sécurité, *retrieval*, stabilité, protocole d'évaluation

```{=latex} 
\cleardoublepage
\tableofcontents
\cleardoublepage
\listoffigures
\cleardoublepage
\listoftables
```

```{=latex}
\cleardoublepage
```

# Introduction {-}

Les modèles de langage ont profondément changé notre rapport à l'information. En l'espace de quelques années, le monde de l'informatique est passé de systèmes incapables de produire une phrase cohérente à des modèles qui rédigent avec une aisance parfois troublante (assistants conversationnels, génération de contenu, ...). Le "boom de l'IA" n'est pas qu'un effet de mode : il transforme concrètement la manière dont les êtres humains produisent et exploitent la connaissance dans les organisations.

Les LLMs (Large Language Models) souffrent pourtant de limites bien connues : ils hallucinent (inventent des informations, parfois plausibles, mais fausses), ne citent pas leurs sources de façon fiable, et peinent à intégrer des connaissances récentes ou spécifiques à un domaine. Dans un contexte où la précision compte et où les sorties du système alimentent des décisions de prévention, ces défauts deviennent rédhibitoires.

C'est pour contourner ces limites qu'une approche hybride s'est imposée : le RAG (*Retrieval-Augmented Generation*), qui couple un mécanisme de recherche documentaire à un modèle génératif [@Lewis2020]. L'idée est simple sur le papier : plutôt que de laisser le modèle "inventer" à partir de ce qu'il a appris, des extraits de documents lui sont fournis, charge à lui de s'y appuyer pour formuler sa réponse. En pratique, c'est bien plus complexe qu'il n'y paraît.

ScribBERT est né de cette idée. C'est un agent conversationnel RAG développé dans le cadre d'une alternance au département P2S de Bouygues Travaux Publics, dont la fonction est de permettre aux collaborateurs d'interroger en langage naturel les référentiels santé-sécurité internes. Les premiers résultats ont été impressionnants : le système répondait de façon pertinente à des questions sur lesquelles un moteur de recherche classique aurait été inutile.

Seulement voilà : dans le domaine de la santé-sécurité, la performance apparente ne suffit pas. Un point doit être posé tout de suite, car il revient souvent dans les discussions : ScribBERT n'est pas un dispositif de sécurité au sens technique du terme. Il ne pilote pas un capteur, ne déclenche pas un arrêt d'urgence, ne se substitue pas à un dispositif de verrouillage. C'est un outil documentaire, qui synthétise les référentiels internes en réponse à une question en langage naturel. À ce titre, il n'expose personne directement : c'est l'usage qui en est fait qui en fait, ou non, un maillon d'une chaîne de décision sensible. Une réponse plausible mais fausse, une procédure mal citée, une obligation transformée en simple recommandation peuvent alors orienter à tort cette décision, avec des conséquences qui dépassent l'enjeu technique. La question centrale de ce mémoire en découle directement : **comment évaluer la cohérence et la fiabilité d'un système RAG** ?

La réponse n'est pas triviale. Évaluer un RAG, ce n'est pas comme évaluer un moteur de recherche classique (où il s'agit de vérifier que les bons documents remontent), ni comme évaluer un LLM seul (où seule la qualité du texte est jugée). C'est évaluer une chaîne, et les erreurs peuvent se situer à chaque maillon : mauvais découpage des documents, mauvaise recherche, mauvaise exploitation du contexte par le modèle.

L'objectif de ce mémoire est de proposer une méthode d'évaluation rigoureuse et reproductible de la pertinence, de la cohérence et de la fiabilité d'un système RAG : identifier des critères adaptés, comparer différentes métriques, étudier l'impact des paramètres de la chaîne de traitement et mettre en œuvre ce protocole sur ScribBERT.

\needspace{9\baselineskip}

La démarche s'organise en trois parties :

- Partie I - Cadre conceptuel et théorique : les fondements du RAG, l'histoire de la recherche d'information, et les notions de pertinence et de cohérence qui sous-tendent l'évaluation.
- Partie II - Méthodologie d'évaluation : construction du protocole, choix des métriques, conditions expérimentales.
- Partie III - Application et discussion : mise en œuvre sur ScribBERT, résultats, et recommandations.

Une remarque pratique sur la lecture. Le sujet croise plusieurs vocabulaires (recherche d'information, *machine learning*, santé-sécurité), et la littérature de référence est très majoritairement anglophone : un certain nombre de termes techniques sont donc en anglais et signalés en italique à leur première occurrence dans une section. Pour ne pas alourdir le texte, ces termes sont définis dans l'Annexe E (glossaire), à laquelle le lecteur peut se reporter à tout moment. Les acronymes (RAG, LLM, MRR, nDCG, etc.) sont développés lors de leur première occurrence dans le corps du texte.

## Cadre applicatif : le projet ScribBERT {-}

Le cadre méthodologique de ce mémoire est instancié sur ScribBERT, développé au département Prévention Santé-Sécurité (P2S) de Bouygues Travaux Publics, filiale de Bouygues Construction spécialisée dans les grandes infrastructures de génie civil (tunnels, ponts, ouvrages maritimes, centrales nucléaires). Cette activité présente trois caractéristiques qui structurent la problématique d'évaluation traitée ici : une exposition aux risques élevée (travail en hauteur, milieu confiné, environnement nucléaire), une production documentaire hétérogène (standards groupe, procédures filiales, modes opératoires chantier, normes externes, réglementations multi-pays) et une organisation décentralisée, chaque chantier disposant d'une certaine autonomie opérationnelle.

Un des enjeux opérationnels centraux est de rendre l'information de santé-sécurité accessible, exacte et applicable au bon moment. Or les retours terrain et les statistiques d'usage du SharePoint interne montrent qu'une part significative des situations à risque ne provient pas d'une absence de référentiel, mais d'une difficulté à retrouver la bonne information : un utilisateur moyen y passe 2 min 30 par recherche, et jusqu'à 10 min pour les cas plus complexes, sans compter la lecture des documents téléchargés. C'est cette friction qui a motivé le projet.

ScribBERT vise à permettre à n'importe quel collaborateur d'interroger ce corpus en langage naturel et d'obtenir une réponse synthétique accompagnée de citations vers les passages d'origine. Techniquement, il repose sur une architecture RAG (*Retrieval-Augmented Generation*), avec quatre principes directeurs posés dès l'origine : ancrage strict sur les documents internes validés (pas de réponse sans source), traçabilité systématique des passages cités, confidentialité des données, et évaluabilité : la conception du système comme objet mesurable, ce qui constitue précisément l'objet de ce mémoire. Le périmètre fonctionnel couvre environ 130 documents PDF internes du siège de Bouygues TP, porté à 190-200 en intégrant les référentiels clients et réglementaires (ENBRIDGE, PAS 91, OSHA, etc., cf. Ch. 7). Le projet a été développé dans le cadre d'une alternance de trois ans, sous la supervision conjointe de Flavien Martin (tuteur métier) et Julien Larseneur (tuteur technique).

Un cadrage important sur le rôle de l'outil : ScribBERT n'est pas une *barrière de sécurité* au sens des référentiels santé-sécurité, qui réservent ce terme à des dispositifs techniques validés (interlocks, détection de gaz, harnais, garde-corps, etc.). Il s'inscrit en amont, comme un facilitateur d'accès au référentiel applicable. La criticité du système ne vient donc pas de la nature de l'outil lui-même mais des décisions qu'il alimente : c'est cette médiation par l'humain qui justifie à la fois l'exigence d'évaluation présentée dans ce mémoire et les garde-fous discutés au Ch. 10 (avertissement permanent, citations vérifiables, refus contrôlé, supervision humaine).

Quatre conséquences directes de ce cadre applicatif structurent la suite du mémoire :

- la criticité métier impose des exigences de fiabilité fortes : même s'il n'est pas un dispositif de sécurité technique, un assistant santé-sécurité qui se trompe peut induire en erreur une décision de prévention, ce qui n'est pas simplement gênant ;
- l'hétérogénéité documentaire rend les *benchmarks* publics inopérants, et impose la construction d'un corpus de test interne ;
- les contraintes de confidentialité orientent les choix techniques vers des modèles auto-hébergeables ou disponibles dans un espace sécurisé ;
- le caractère opérationnel du déploiement (utilisateurs réels, certains enthousiastes, d'autres méfiants vis-à-vis de l'IA) impose de considérer non seulement la performance moyenne, mais aussi la stabilité et la gestion des cas limites. Les premiers retours utilisateurs ont confirmé que la peur de l'erreur reste présente et légitime (en phase de POC, certaines réponses se sont avérées incorrectes ou incomplètes), ce qui a renforcé la nécessité d'un cadre d'évaluation solide avant tout déploiement élargi.

```{=latex}
\cleardoublepage
\thispagestyle{plain}
\vspace*{\stretch{1}}
\begin{center}
{\Huge\bfseries PARTIE I}\\[1.5em]
{\LARGE Cadre conceptuel et état de l'art}
\end{center}
\vspace*{\stretch{2}}
\addcontentsline{toc}{section}{PARTIE I \textemdash{} Cadre conceptuel et état de l'art}
\markboth{PARTIE I \textemdash{} Cadre conceptuel et état de l'art}{}
\newpage
```

Cette première partie replace les systèmes de RAG (*Retrieval-Augmented* Generation) dans l'histoire des méthodes de recherche d'information. Elle vise ensuite à formaliser les notions de pertinence et de cohérence / fidélité qui seront au cœur du protocole d'évaluation.

Deux constats structurent cette partie :

1. Un RAG n'est pas "un LLM + des documents". C'est une chaîne complexe de décision (découpage, indexation, recherche, assemblage du contexte, génération) dont les erreurs et imprécisions s'additionnent parfois.
2. Les critères d'évaluation de l'IR (recherche d'information) classique et ceux des LLMs ne se recouvrent pas. Un excellent score de récupération est tout à fait compatible avec une réponse finale fausse.

## De la recherche documentaire à la recherche sémantique

### Brève histoire de la recherche d'information : du lexical au probabiliste

Avant de parler de RAG, il faut comprendre d'où vient la recherche d'information, puisque ses systèmes en héritent grandement, y compris dans leurs limites.

La recherche d'information (IR) s'est construite autour d'un problème en apparence simple : étant donné un besoin (une requête) et une collection de documents, comment ordonner ces documents par pertinence [@Manning2008]? L'idée d'un accès mécanisé à l'information remonte à l'après-guerre, avec le concept de *Memex* imaginé par Vannevar Bush [@Bush1945].

Les premières approches opérationnelles étaient lexicales : un document est un sac de mots, une requête est une contrainte sur ces mots. Le modèle booléen (AND/OR/NOT) est le plus élémentaire : explicable et contrôlable, mais il ne classe pas les résultats et ne gère pas bien les besoins graduels.

L'IR moderne s'est ensuite structurée autour de la notion de classement et d'évaluation systématique. Le paradigme de Cranfield [@Cleverdon1967] a joué un rôle déterminant : constituer un corpus, un ensemble de requêtes, et des jugements de pertinence pour comparer des systèmes. Plus tard, les campagnes TREC ont industrialisé cette logique d'évaluation à grande échelle [@VoorheesHarman2005].

Les modèles vectoriels ont ensuite introduit une représentation plus graduelle : documents et requêtes sont représentés comme des vecteurs, et la similarité est souvent mesurée via un calcul de similarité cosinus. Une pondération bien connue est le TF-IDF, qui combine une mesure de fréquence locale (*term frequency*) et une mesure de rareté globale (*inverse document frequency*). Formellement :

$$\mathrm{tfidf}(t, d) = \mathrm{tf}(t,d) \times \log\left(\frac{N}{\mathrm{df}(t)}\right)$$

où $N$ est le nombre total de documents et $\mathrm{df}(t)$ le nombre de documents contenant le terme $t$.

L'idée d'IDF comme signal de discrimination d'un terme remonte à des travaux fondateurs sur le *term specificity*[@SparckJones1972]. Le vector space model (VSM) popularisé par Salton et al. a ensuite fourni un cadre pratique et encore omniprésent pour pondérer et comparer requêtes et documents [@Salton1975].

À partir des années 1990-2000, les approches probabilistes (notamment BM25) se sont imposées comme standard industriel : elles offrent un excellent compromis performance/simplicité et une robustesse sur des corpus variés [@RobertsonZaragoza2009]. BM25 peut être vu comme une amélioration de TF-IDF qui normalise explicitement par la longueur du document et introduit des hyperparamètres supplémentaires.

$$\mathrm{BM25}(q, d) = \sum_{t \in q} \mathrm{idf}(t) \cdot \frac{\mathrm{tf}(t,d) \cdot (k_1+1)}{\mathrm{tf}(t,d) + k_1 \cdot \left(1-b + b\cdot \frac{|d|}{\mathrm{avgdl}}\right)}$$

avec $k_1$ et $b$ des paramètres de calibration, $|d|$ la longueur du document et $\mathrm{avgdl}$ la longueur moyenne.

Enfin, une autre famille importante, très utilisée en pratique, est celle des modèles de langage pour l'IR, dans laquelle la probabilité qu'un document génère une requête est estimée (approches *query likelihood*), avec des techniques de lissage et de retour pseudo-pertinent[@PonteCroft1998; @LavrenkoCroft2001].

Ces modèles "classiques" (BM25, *query likelihood*, variantes) restent extrêmement compétitifs, notamment sur des corpus techniques où les indices lexicaux (références, numéros de procédure, intitulés normatifs) apportent des signaux précieux.

#### Évaluer un système de recherche : pourquoi les métriques comptent

Les *chaînes de traitement* RAG héritent directement de l'IR un point crucial : l'évaluation dépend du protocole. La performance d'un moteur ne peut pas être "résumée" par un seul score sans préciser la tâche, la définition de pertinence, le nombre de résultats considérés ($k$), et la nature binaire ou graduée des jugements[@Manning2008; @BaezaYates2011; @Croft2010; @VoorheesHarman2005].

Dans sa forme la plus simple, deux mesures se distinguent :

- la précision (proportion de résultats pertinents parmi les résultats retournés),
- le rappel (proportion des résultats pertinents retrouvés parmi tous les pertinents existants).

En recherche classée, des métriques au rang sont utilisées : Precision@k, Recall@k, ainsi que des métriques de classement global comme nDCG (qui gère naturellement la pertinence graduée) [@JarvelinKekalainen2002].

Ce point est central pour le mémoire : changer la définition de pertinence (thématique vs situationnelle) modifie les scores de récupération, et la qualité perçue aussi.

#### Retour, reformulation et *learning-to-rank*

Les systèmes IR peuvent aussi reformuler la requête pour améliorer les résultats. Le *relevance feedback* et ses variantes (pseudo-relevance feedback, expansion de requête) augmentent le rappel (*recall*) mais peuvent introduire du bruit [@Rocchio1971]. Dans un RAG, ce compromis est amplifié : une expansion mal calibrée risque de récupérer des passages thématiquement proches mais non applicables.

En parallèle, le *learning-to-rank* a permis d'apprendre des fonctions de classement à partir de données (clics, jugements), avec des approches *pointwise*, *pairwise* et *listwise* [@Liu2009LTR]. Les systèmes industriels combinent aujourd'hui une récupération rapide, un *reranking* plus coûteux (souvent *cross-encoder*) et des signaux métier (popularité, fraîcheur). Le RAG s'insère dans cette logique multi-étage : la majorité des architectures dites *Advanced RAG* documentées dans la littérature reprennent ce schéma à plusieurs niveaux (récupération initiale large, filtrage, *reranking*, génération conditionnée), parfois enrichi de boucles de réflexion ou de mécanismes de décision sur la nécessité de récupérer [@Gao2024RAGSurvey; @NogueiraCho2019].

```{=latex}
\newpage
```

### Limites du matching lexical

Les méthodes lexicales (booléen, TF-IDF, BM25) reposent sur une hypothèse forte : la pertinence est principalement capturable par la co-occurrence de termes entre requête et document. En pratique, cette hypothèse se heurte à des problèmes bien documentés, observables directement lors des premières itérations de ScribBERT :

- Synonymie : deux textes peuvent décrire la même notion avec des termes différents. Dans notre corpus, "harnais antichute" et "EPI antichute" désignent la même chose, mais un matching lexical pur les traite comme des termes sans lien.
- Polysémie : un même terme peut renvoyer à des concepts différents selon le contexte (ex. "levage" en planification vs levage en opération terrain).
- Morphologie et variations : abréviations, variantes métier. Le jargon des chantiers est particulièrement riche en acronymes et en raccourcis que les référentiels n'utilisent pas toujours.
- Requêtes complexes : les utilisateurs posent rarement des mots-clés isolés. Ils expriment des intentions, des contraintes, des justifications ("que faire si…", "dans quel cas…", "quelles exceptions…"). Les signaux purement lexicaux sont mal équipés pour traiter ces formulations.

Dans un contexte technique et réglementaire, ces limites sont accentuées : le vocabulaire est spécialisé, la formulation est parfois normative, très théorique, et l'utilisateur peut utiliser un vocabulaire terrain différent de celui du référentiel.

Deux compléments sont importants pour comprendre pourquoi ces limites deviennent critiques dans un RAG :

- Rappel vs précision : un moteur lexical peut être très précis (peu de bruit) mais rater des passages formulés différemment ; inversement, il peut avoir un bon rappel mais ramener trop de textes "proches" sans être applicables. Le RAG transforme ce compromis en risque de génération : un passage légèrement hors-sujet peut suffire à entraîner une réponse erronée.
- Correspondance d'intention : la requête utilisateur exprime souvent une tâche (ex. "quels EPI obligatoires ?", "quelle procédure avant intervention ?"), et pas seulement un thème. Or les signaux lexicaux capturent mal la structure de tâche (conditions, exceptions, étapes).

### Vers la recherche sémantique : représentations distribuées et vectorisations

L'idée de dépasser le matching lexical n'est pas nouvelle. Dès les années 1990, l'indexation sémantique latente (LSI/LSA) projetait termes et documents dans un espace de dimension réduite via factorisation matricielle (SVD), dans l'espoir de capturer des corrélations entre termes et de réduire les problèmes de synonymie [@Deerwester1990].

Le vrai tournant est venu avec les vectorisations neuronales. Word2Vec (Mikolov et al., 2013) a montré qu'il était possible d'apprendre des représentations de mots denses, de faible dimension, où les mots apparaissant dans des contextes similaires se retrouvent proches dans l'espace vectoriel [@Mikolov2013]. GloVe a proposé une approche alternative combinant statistiques globales et optimisation locale [@Pennington2014]. Ces modèles avaient cependant une limite importante : un mot n'avait qu'un seul vecteur, indépendamment de la phrase. Le mot "levage" avait la même représentation qu'il s'agisse d'une opération de chantier ou d'une phase de planification.

Les modèles de type Transformers, et BERT en particulier, ont "résolu" ce problème en introduisant des représentations contextualisées : la représentation d'un *token* dépend désormais de la phrase entière [@Vaswani2017; @Devlin2019]. C'est ce qui a ouvert la voie à la recherche sémantique moderne.

Dans la pratique, l'usage IR/RAG requiert surtout des vectorisations de phrases/passages (*sentence or passage embeddings*). Les approches de type bi-encodeur (ou *dual-encoder*) encodent requête et passage séparément, puis comparent leurs vecteurs (souvent cosinus ou produit scalaire). Sentence-BERT (SBERT) a été une contribution clé pour obtenir des vectorisations de phrases efficaces via apprentissage contrastif et *siamese networks* [@ReimersGurevych2019]. Des travaux plus récents (ex. SimCSE) montrent que des schémas contrastifs simples peuvent déjà produire de très bons espaces de vectorisation [@Gao2021].

À l'inverse, les *cross-encoders* concatènent requête et passage et produisent un score de pertinence en tenant compte finement des interactions token-à-token, mais ils coûtent beaucoup plus cher à l'inférence. Ils sont souvent utilisés en *reranking* sur un petit nombre de candidats [@NogueiraCho2019].

Enfin, des architectures intermédiaires (*late interaction*) comme ColBERT cherchent à concilier précision (interactions fines) et efficacité (indexation) via des représentations token-level compressées [@KhattabZaharia2020].

### Sparse, dense et hybride : familles de récupération

En pratique, les systèmes de récupération se rangent en trois grandes familles. La récupération creuse (BM25, TF-IDF) représente les documents dans un espace de très grande dimension. Ces systèmes sont rapides et fonctionnent remarquablement bien sur des requêtes contenant des identifiants précis (numéros de procédure, références normatives). La récupération dense projette tout dans un espace compact de vectorisations, plus apte à capturer synonymie et paraphrase, mais plus "opaque". Et l'hybride combine les deux, ce qui est souvent la meilleure option quand le corpus mélange des requêtes techniques et des questions en langage naturel.

L'étape de récupération peut également être suivie d'un *reranking* : un ensemble large de candidats est d'abord récupéré (rapide), puis un modèle plus précis (souvent un *cross-encoder*) reclasse finement les passages. (Ce point est repris au Chapitre 4.)

Au-delà de cette typologie, un point technique essentiel pour les systèmes denses est l'indexation par recherche du plus proche voisin approximatif (*Approximate Nearest Neighbor*, ANN). À grande échelle, il est impossible de comparer une requête à tous les vecteurs. Des structures dédiées (HNSW, IVF, PQ…) sont donc utilisées pour accélérer la recherche au prix d'une approximation contrôlée [@MalkovYashunin2018; @Johnson2019].

Cette approximation a une conséquence méthodologique : la performance de récupération dépend non seulement du modèle de vectorisation, mais aussi de la configuration de l'index (paramètres HNSW, quantization, etc.). Dans un protocole d'évaluation, il est donc important de distinguer :

- erreur de représentation (vectorisation inadaptée),
- erreur d'indexation (approximation ANN),
- erreur de formulation de requête (*query rewriting* absent ou mal calibré).

### Problématiques spécifiques à la sémantique en contexte technique

Tout ce qui précède s'applique à la recherche sémantique en général. Mais un corpus santé-sécurité pose des problèmes supplémentaires qui méritent d'être explicités.

La criticité de l'erreur est d'un autre ordre : une réponse plausible mais fausse n'est pas juste inutile, elle peut orienter à tort la décision de prévention qui s'appuie dessus. La granularité des sources est aussi un défi : un même thème peut être traité dans une règle générale groupe, une procédure filiale, et un mode opératoire chantier, avec des niveaux de détail et d'autorité différents (sans parler des documents clients et réglementaires).

Il faut ajouter des phénomènes fréquents dans les corpus internes que les *benchmarks* académiques ne capturent pas : des procédures longues et composites où un *chunk* peut contenir les bons mots-clés mais être la mauvaise section ; des niveaux d'obligation subtils (la différence entre "recommandé" et "obligatoire", entre "interdit" et "déconseillé", peut avoir des conséquences très concrètes).

Tout cela fait que l'évaluation d'un RAG en contexte santé-sécurité ne peut pas se limiter à la proximité sémantique.

### Limites des approches traditionnelles face aux LLMs (Large Language Models)

L'émergence des LLMs change la donne, et pas seulement du côté de la génération. Elle change aussi la nature des requêtes. L'utilisateur qui interroge un assistant comme ScribBERT n'écrit plus de mots-clés : il pose une question complète, souvent complexe et implicitement située dans un contexte ("que dois-je vérifier avant de commencer un travail en hauteur sur un échafaudage roulant ?"). Le système doit donc gérer des intentions (besoin d'explication, de comparaison, de décision) et pas seulement une adéquation thématique.

L'autre problème, plus piégeux, est celui de l'hallucination. Les LLMs peuvent produire des textes *cohérents sur la forme* tout en étant incorrects sur le fond [@Maynez2020; @Ji2023]. En contexte santé-sécurité, ce phénomène devient un risque opérationnel à part entière dès lors que la sortie est utilisée pour préparer une décision. C'est cette tension entre qualité apparente et fiabilité réelle qui justifie l'existence du RAG, et la nécessité de l'évaluer.

### Neural IR et récupération dense

Avec les modèles Transformers, la récupération dense a pris son essor. L'idée est d'encoder requêtes et passages avec un bi-encodeur (deux BERT indépendants) et de les comparer par similarité vectorielle. DPR (Karpukhin et al., 2020) a montré que cette approche pouvait surpasser BM25 sur des *benchmarks* de QA (*Question/Answer*) ouverts [@Karpukhin2020]. Les gains suivants ont surtout été obtenus via des stratégies d'entraînement avec *hard negatives* et des travaux comme ORQA[@Lee2019ORQA] et ANCE[@Xiong2020ANCE], non détaillés ici.

La question pratique pour un cas comme ScribBERT est directe : **un modèle entraîné sur des données web généralistes est-il adapté à un vocabulaire métier ?** Le *benchmark* BEIR a montré une dégradation significative des performances hors domaine d'entraînement [@Thakur2021BEIR]. Cette question sera traitée en Partie II.

### De la récupération dense au RAG : la convergence historique

La trajectoire décrite dans ce chapitre, du lexical aux vectorisations puis à la récupération dense, mène à l'idée de coupler un *retriever* dense à un modèle génératif. Sur le moment, chaque étape a nécessité des contributions distinctes, et ce n'est qu'à partir de 2020 que la filiation devient explicite.

Le paradigme *retriever-reader* a d'abord été popularisé par DrQA (Chen et al., 2017), puis ORQA [@Lee2019ORQA] et REALM [@Guu2020] ont progressivement intégré le *retriever* dans la boucle d'apprentissage. Le RAG (Lewis et al., 2020) couplait un générateur BART à un *retriever* DPR avec deux variantes : RAG-Sequence, RAG-Token [@Lewis2020], et Fusion-in-Decoder (Izacard & Grave, 2021) a ensuite montré que l'injection de davantage de passages dans le décodeur permettait d'améliorer encore les résultats [@IzacardGrave2021].

Le RAG n'est pas une invention isolée mais l'aboutissement d'une lignée de recherche en IR.

```{=latex}
\newpage
```

## Les fondements du RAG (*Retrieval-Augmented* Generation)

### Principe général : génération augmentée par récupération

Le RAG, dans son principe, est assez intuitif : au lieu de laisser un modèle de langage répondre "de tête", des documents pertinents lui sont fournis et il lui est demandé de s'en servir. Autrement dit, il est mis au travail comme le ferait un bon préventeur, en consultant la documentation avant de répondre.

Plus formellement, le *Retrieval-Augmented* Generation désigne une famille d'architectures où un modèle génératif produit une réponse en s'appuyant sur un contexte documentaire récupéré dynamiquement. C'est un entre-deux :

- un moteur de recherche retrouve des documents, mais ne produit pas de réponse rédigée ;
- un LLM seul rédige, mais peut inventer ou s'appuyer sur des connaissances obsolètes.

Le RAG combine les deux. Historiquement, cette idée s'inscrit dans la lignée des systèmes retriever-reader (DrQA, ORQA) où un module récupère des passages et un second les exploite [@Chen2017DrQA; @Karpukhin2020].

Sur le plan formel, le RAG peut se modéliser comme un problème de génération conditionnelle où les passages récupérés jouent un rôle intermédiaire :

$$p(y\mid x)=\sum_z p(y\mid x,z)\,p(z\mid x)$$

où :

- $x$ est la requête de l'utilisateur,
- $z$ est un passage issu du corpus (variable latente : non observée directement, elle est inférée),
- $y$ est la réponse générée.

La formule se lit ainsi : pour obtenir une réponse $y$ à la question $x$, la somme porte sur tous les passages $z$ possibles, et combine le produit de deux probabilités : celle que $z$ soit un bon passage pour cette question $p(z\mid x)$, et celle que le modèle génère $y$ à partir de ce passage $p(y\mid x,z)$.

En pratique, parcourir tous les passages du corpus est impossible : cette somme est approximée en ne retenant qu'un petit nombre de passages (le top-$k$). C'est ce qui rend les choix de récupération si importants : si le "bon" passage n'apparaît pas parmi les $k$ retenus, le modèle génère sa réponse sans l'information nécessaire.

### RAG vs *fine-tuning* : choix méthodologiques

La question "pourquoi un RAG plutôt qu'un *fine-tuning* ?" est revenue plusieurs fois dans les discussions autour de ScribBERT, et le choix s'est fait assez naturellement, mais il mérite d'être explicité.

Le *fine-tuning* consiste à adapter les poids d'un modèle sur des données spécifiques. Le modèle obtenu "sait" les choses directement, sans avoir besoin de consulter des documents au moment de la requête. En théorie cela semble convaincant. En pratique, dans un contexte comme le nôtre, c'est difficilement tenable : nos procédures évoluent régulièrement, et réentraîner un modèle à chaque mise à jour documentaire serait trop coûteux et non traçable (les sources mobilisées par le modèle pour répondre resteraient inconnues). Une étude comparative récente confirme ce constat empiriquement : sur des tâches d'injection de connaissances nouvelles, le RAG surpasse systématiquement le *fine-tuning* supervisé, et plus encore lorsque l'information est rare ou évolutive [@Ovadia2024FTvsRAG].

Le RAG, à l'inverse, conserve un modèle généraliste et injecte du contexte documentaire à la volée. Pour mettre à jour un document, il "suffit" de réindexer. Et pour savoir d'où vient une réponse, il "suffit" d'inspecter les passages récupérés.

Cela dit, le RAG ne nous interdit pas de faire du *fine-tuning*. Un *fine-tuning* léger peut servir à calibrer le ton, tandis que le RAG gère l'accès aux connaissances. La littérature récente insiste d'ailleurs sur cette complémentarité [@Gao2024RAGSurvey].

### Architecture type d'une chaîne de traitement RAG

Une chaîne de traitement RAG se décompose généralement en cinq étapes :

1. Ingestion : collecte des documents (nos référentiels, procédures, ...), extraction de texte, normalisation.
2. *Chunking* : découpage en segments (*chunks*).
3. Vectorisation / indexation : calcul de vectorisations pour chaque *chunk* et insertion dans un index (base vectorielle).
4. Récupération / *reranking* : récupération de $k$ passages pertinents (qui peuvent être dans un second temps reclassés par un modèle plus fin (*reranking*)).
5. Génération : construction d'un *prompt* complet avec la requête + contexte, puis génération d'une réponse.

Pour ScribBERT, cette architecture se décline avec des choix d'implémentation qui seront décrits en PARTIE III.

Un mot sur le *chunking*, qui est souvent décrit comme un paramètre "d'ingestion" mais correspond en réalité à un choix de modélisation : quelle est l'unité minimale (et maximale également) de connaissance que le système peut retrouver et citer ?

Plusieurs logiques de segmentation se distinguent :

- Segmentation structurelle (titres, sections, listes) : adaptée aux procédures et aux référentiels, car elle suit la logique documentaire.
- Segmentation à longueur fixe : robuste et simple, mais peut casser des définitions ou séparer condition/exception.
- Segmentation thématique (topic segmentation) : vise à découper selon des ruptures de sujet ; des approches classiques existent (ex. TextTiling) [@Hearst1997].

Le *chunking* influence directement :

- le rappel (*chunks* trop gros : moins d'unités, risque de dilution ; *chunks* trop petits : manque de contexte),
- la citabilité (capacité à relier une affirmation à un extrait précis),
- la gestion des contradictions (contradictions détectables si les unités sont comparables).

Ces aspects seront étudiés dans la PARTIE III (comparaisons de *chunking*).

### Les avantages du RAG

Le premier bénéfice est la réduction des hallucinations : en fournissant au modèle des passages explicites, sa génération est contrainte et les inventions sont limitées. En pratique, c'est plus nuancé (le modèle peut toujours halluciner malgré le contexte), mais le gain est réel. Surtout, le RAG rend la réponse traçable : un retour aux passages utilisés reste possible, et c'est cette auditabilité qui fait la différence dans un cadre industriel.

Les autres avantages sont plus opérationnels : les connaissances peuvent être mises à jour sans réentraîner le modèle (les documents modifiés sont simplement réindexés), le corpus interne reste privé (pas besoin de l'envoyer dans un service cloud pour du *fine-tuning*), et le coût global est moindre qu'un entraînement dédié.

### Les défis du RAG : bruit, contradictions et cohérence

Pour autant, le RAG n'est pas une solution magique. Il introduit ses propres difficultés :

Le bruit documentaire est probablement le problème le plus fréquent : la récupération ramène des *chunks* qui sont sémantiquement proches de la requête mais qui ne sont pas applicables au cas précis. Dans notre corpus, c'est relativement fréquent avec des procédures qui partagent une terminologie commune mais s'appliquent à des situations différentes.

Les contradictions entre documents sont un autre défi, et celui-ci est souvent sous-estimé. Quand un corpus contient à la fois un document de 2020 et sa mise à jour de 2026, que se passe-t-il si la récupération remonte les deux ? Le modèle peut produire une réponse incohérente, ou pire, choisir silencieusement la mauvaise version.

La dépendance au *chunking* est un problème plus subtil mais réel : une mauvaise segmentation peut couper une règle en deux, ou séparer une condition de son exception, et le modèle génère alors une réponse incomplète sans diagnostic facile de la cause.

Enfin, la cohérence globale de la réponse reste fragile : même avec de bons passages, le modèle peut oublier une exception critique ou généraliser.

Ces difficultés justifient une évaluation à deux niveaux (qualité de la récupération *et* qualité de la génération), car un bon score sur l'un ne garantit pas un bon résultat sur l'autre (bien qu'une mauvaise récupération ne facilite pas une bonne génération évidemment).

Plusieurs variantes architecturales cherchent à répondre à ces défis : le RAG "classique" de Lewis et al.[@Lewis2020], REALM qui intègre la récupération dans la pré-formation [@Guu2020], ou encore Fusion-in-Decoder (FiD) qui concatène de nombreux passages et laisse le décodeur fusionner l'information [@IzacardGrave2021]. Toutes illustrent un même dilemme : donner plus de passages au LLM augmente le rappel potentiel, mais aussi le risque de contradictions, de dilution, et augmente le coût.

En pratique, les systèmes robustes adoptent une architecture *multi-stage* qui répond directement à ce dilemme : une récupération large (top-$k$ élevé) maximise le rappel, un *reranking* par *cross-encoder* augmente ensuite la précision sur ce petit ensemble candidat[@NogueiraCho2019], et une sélection/assemblage finale respecte la limite de contexte du générateur. Chaque étage a un effet direct sur la fidélité : une récupération trop large sans *reranking* augmente le bruit, un *reranking* mal calibré peut favoriser des passages "proches" mais moins normatifs, et une sélection trop agressive peut écarter des passages qui auraient été utiles.

### Ancrage, citations et attribution : de la preuve à la confiance

Citer une source ne suffit pas. Les tests menés sur ScribBERT ont révélé des cas où le système citait un document qui n'avait qu'un rapport lointain avec la question, ce qui est pire que l'absence de citation, car cela donne une illusion de rigueur. La littérature formalise cette intuition en distinguant trois dimensions : la *context relevance* (le contexte récupéré est-il utile ?), l'*answer relevance* (la réponse traite-t-elle la question ?) et la *faithfulness* (la réponse est-elle supportée par le contexte ?). Ces trois dimensions ne se recouvrent pas, et c'est précisément ce qui rend l'évaluation complexe.

### RAG et mémoire : connaissances paramétriques vs non-paramétriques

Deux types de mémoire se distinguent : la "mémoire paramétrique" d'un LLM (ses poids) et la "mémoire non-paramétrique" (une base documentaire externe, interrogée à la volée). Un modèle assez gros peut stocker beaucoup de faits dans ses paramètres [@Roberts2020], mais avec des limites évidentes en mise à jour et vérifiabilité (expliquées plus tôt). Pour ScribBERT, la mémoire non-paramétrique est préférée parce qu'elle est auditable : les documents consultés sont identifiables, et leur mise à jour ne touche pas au modèle.

### Pourquoi la notion de "source" est centrale en contexte santé-sécurité

Dans une application santé-sécurité, une réponse "créative" est indésirable : la réponse attendue est normative ou procédurale, fondée sur les bons documents. La qualité tient alors à des questions très concrètes : le système distingue-t-il une procédure groupe validée d'une note informelle ? Respecte-t-il la différence entre "doit" et "devrait" ? Mentionne-t-il les exceptions ? Ces exigences, bien plus strictes que dans un agent conversationnel grand public, imposent de centrer l'évaluation sur la fidélité aux sources, ce qui sera l'objet de la Partie II.

```{=latex}
\newpage
```

## La question de la "pertinence" et de la "cohérence"

Les mots "pertinence" et "cohérence" reviennent constamment aussi bien dans ce mémoire que dans les discussions sur la qualité d'un RAG, mais ils recouvrent des réalités assez différentes selon les interlocuteurs. Ce chapitre tente de les clarifier, non pas par amour pour la taxonomie, mais plutôt parce que la qualité d'un protocole d'évaluation dépend directement des attentes qui lui sont fixées.

### Définir la pertinence : une notion multi-dimensionnelle

En recherche d'information, la pertinence est un mélange entre un besoin, un utilisateur, un contexte et un document, à un moment donné. La littérature académique insiste depuis longtemps sur cette complexité et sur l'écart entre ce qu'un système juge pertinent et ce que l'utilisateur considère comme pertinent [@Saracevic1996; @Mizzaro1997]. Pour un RAG, plusieurs dimensions s'ajoutent à la simple adéquation thématique.

Un passage peut parler du bon sujet sans être utile pour autant. La pertinence situationnelle dépend du rôle de l'utilisateur, de la phase du chantier, des contraintes de site : une procédure générale ne sert pas à un compagnon qui a besoin d'une consigne précise. L'exhaustivité est critique quand il cherche une procédure complète : une réponse correcte mais à laquelle il manque une étape ou une exception peut être dangereuse. La granularité pose la question inverse : donner trop de détails peut noyer l'information, surtout si le format attendu est une check-list courte.

L'actualité et l'autorité de la source sont deux dimensions souvent négligées mais centrales dans un corpus d'entreprise vivant. Un passage peut être thématiquement pertinent mais obsolète. Une procédure groupe validée n'a pas la même force qu'une note informelle. Notre SharePoint contient des documents de niveaux de normativité très différents, et le système doit être capable de les hiérarchiser.

Enfin, les évaluations purement offline ignorent souvent la pertinence interactive : l'utilisateur reformule, lit les sources, change de stratégie, et l'utilité dépend de ce processus [@IngwersenJarvelin2005; @Borlund2003]. Pour ScribBERT, cela suggère de compléter les métriques automatiques par des signaux d'usage : taux de reformulation, temps pour obtenir une réponse utile, cas où l'utilisateur doit escalader vers un expert.

### Définir la cohérence : du texte à la fidélité aux sources

Dans le contexte des LLMs, la cohérence est souvent abordée sous l'angle de la fluidité textuelle. Pour un RAG, cette définition est insuffisante : une réponse peut être très fluide mais fausse.

Il est utile de distinguer trois notions proches mais différentes. La cohérence textuelle caractérise un texte qui "se tient" linguistiquement, avec une dimension locale (connecteurs, anaphores, absence de contradictions phrase-à-phrase) et une dimension globale (fil directeur sur l'ensemble de la réponse) ; les LLMs modernes maîtrisent bien la première, beaucoup moins la seconde quand le contexte est hétérogène ou que le *prompt* impose un format strict. La factualité dit que les propositions sont vraies dans un cadre documentaire de référence. La fidélité (ou *groundedness*) est plus restrictive : les propositions doivent être justifiées par les sources effectivement fournies au modèle. Dans un RAG, cette dernière est souvent plus importante que la factualité absolue : le système ne doit pas dépasser ce que le corpus permet d'affirmer.

La fidélité peut être compromise par une récupération partielle, une mauvaise attribution, une paraphrase qui modifie le sens normatif, ou une sur-généralisation. Une difficulté spécifique aux textes normatifs est la modalité : une reformulation peut transformer un "doit" en "peut", ou l'inverse. Dans une évaluation, cela implique de vérifier non seulement les faits, mais aussi la conformité des modalités et conditions.

La stabilité / reproductibilité est un enjeu à la fois opérationnel et méthodologique. À requête identique et à corpus constant, le système doit produire des réponses proches, surtout en contexte santé-sécurité où la variabilité est perçue comme un manque de fiabilité. Si la sortie varie fortement, comparer des variantes (*chunking*, top-$k$) devient impossible sans multiplier les répétitions et rapporter des distributions de scores. La stabilité dépend de la stochasticité du modèle (température), de la récupération (approximation ANN) et d'éventuelles reformulations.

La cohérence terminologique et réglementaire complète ce tableau : la réponse doit utiliser un vocabulaire métier stable, éviter les formulations ambiguës, et respecter les contraintes réglementaires et internes sans inventer des obligations.

### Définir la fiabilité : une synthèse opératoire

Le titre de ce mémoire associe "cohérence" et "fiabilité". La cohérence a été définie ci-dessus. Mais la fiabilité est un concept plus englobant : c'est la propriété d'un système à produire de manière constante des réponses dignes de confiance. Un système peut donner une excellente réponse un jour et une réponse médiocre le lendemain sur la même question : il est ponctuellement bon mais pas fiable.

Pour ce mémoire, j'adopte la définition opératoire suivante :

> **Fiabilité d'un RAG = pertinence de la récupération + fidélité aux sources (factualité) + stabilité/répétabilité des réponses + traçabilité auditable.**

Cette définition présente trois intérêts :

1. Elle décompose la fiabilité en dimensions mesurables, ce qui permet d'organiser le protocole d'évaluation (Chapitre 5) autour de chacune.
2. Elle distingue la cohérence (propriété intrinsèque d'une réponse) de la fiabilité (propriété systémique) : une réponse peut être cohérente une fois et incohérente la suivante ; un système n'est fiable que si ses réponses sont cohérentes de manière répétée.
3. Elle inclut explicitement la traçabilité, dimension non couverte par les métriques classiques mais essentielle (auditabilité, conformité).

### Pertinence perçue vs pertinence mesurée

Il y a un écart, parfois considérable, entre ce que les métriques disent et ce que l'utilisateur ressent. Parfois, des configurations avec de "bons" scores de récupération produisaient des réponses qui étaient trop vagues ou mal ciblées. Et inversement, des réponses jugées utiles ne correspondaient pas toujours à un Recall@k élevé.

Ce décalage impose de travailler sur les deux fronts : les mesures automatiques (utiles pour comparer des variantes, diagnostiquer, itérer) et la perception utilisateur (confiance, effort, satisfaction). Un protocole robuste combine les deux, ce que la littérature appelle triangulation.

Sur le plan méthodologique, cela rejoint l'idée de séparer évaluation intrinsèque (mesurer des propriétés internes) et évaluation extrinsèque (mesurer l'effet sur la tâche finale).

### Travaux récents sur l'évaluation des RAG et LLMs augmentés

L'évaluation des systèmes RAG s'est structurée autour de plusieurs axes :

1. Évaluation récupération : métriques classiques (Recall@k, nDCG, MRR) sur des jeux de test annotés [@JarvelinKekalainen2002].
2. Évaluation génération : métriques de similarité (BLEU/ROUGE) peu adaptées à la QA ouverte ; métriques sémantiques (BERTScore, BLEURT) ; métriques de factualité (ex. TruthfulQA, FactScore) visant à quantifier l'alignement factuel des sorties [@Lin2021TruthfulQA; @Min2023FactScore].
3. Évaluation "*end-to-end*" : *frameworks* dédiés au RAG (ex. RAGAS, TruLens, LangSmith) qui tentent de décomposer la qualité en sous-scores (*context relevance*, *answer relevance*, *faithfulness*, citation, etc.).
4. *LLM-as-judge* : utiliser un LLM pour noter des réponses selon une grille (G-Eval, Prometheus). Puissant mais nécessite une gouvernance stricte (biais, fuite d'informations, reproductibilité).

Les *benchmarks* de récupération généralistes (BEIR) et les *leaderboards* de vectorisations (MTEB) ont également contribué à standardiser la comparaison de modèles et à clarifier l'écart entre performance sur des tâches "web" et performance sur des corpus spécialisés [@Thakur2021BEIR; @Muennighoff2023MTEB].

Pour la génération, plusieurs métriques basées sur des modèles pré-entraînés se sont imposées :

- BERTScore pour mesurer une similarité sémantique token-level [@Zhang2020BERTScore].
- BLEURT comme score appris de similarité/qualité [@Sellam2020BLEURT].

Cependant, ces métriques ne suffisent pas à capturer la fidélité aux sources. C'est pourquoi des travaux récents sur la factualité/hallucination (ex. en résumé) sont souvent mobilisés comme base conceptuelle [@Maynez2020; @Ji2023].

Un point récurrent dans la littérature est l'écart entre la performance de récupération et la performance de génération (usage correct des sources).

Autrement dit, une bonne récupération ne garantit pas une réponse fidèle, et une réponse fluide ne garantit pas qu'elle soit vraie.

Dans le cas d'un RAG, l'évaluation pertinente doit idéalement être décomposable : elle doit permettre de dire *où* se situe l'échec (récupération, *reranking*, *prompt*, génération) et pas seulement de constater que la réponse finale est "bonne" ou "mauvaise".

Pour expliciter la suite, quelques définitions courantes du côté récupération sont rappelées, sur un ensemble de requêtes $Q$. Soit $\mathrm{TopK}(q)$ l'ensemble des $k$ premiers passages récupérés pour la requête $q$, et $\mathrm{Rel}(q)$ l'ensemble des passages pertinents (selon l'annotation).

\needspace{25\baselineskip}

- Recall@k :

$$\mathrm{Recall@k} = \frac{1}{|Q|}\sum_{q\in Q} \frac{|\mathrm{Rel}(q) \cap \mathrm{TopK}(q)|}{|\mathrm{Rel}(q)|}$$

- MRR (*Mean Reciprocal Rank*), utile lorsqu'au moins un bon passage est attendu parmi les premiers résultats :

$$\mathrm{MRR} = \frac{1}{|Q|}\sum_{q\in Q} \frac{1}{\mathrm{rank}_q}$$

où $\mathrm{rank}_q$ est le rang du premier document pertinent.

- nDCG@k (pertinence graduée), qui pénalise moins fortement un document pertinent placé en position 2 qu'en position 20 :

$$\mathrm{DCG@k} = \sum_{i=1}^{k} \frac{2^{rel_i}-1}{\log_2(i+1)}\quad;\quad \mathrm{nDCG@k}=\frac{\mathrm{DCG@k}}{\mathrm{IDCG@k}}$$

Dans le cadre de ce mémoire, les annotations sont binaires ($rel_i \in \{0,1\}$) : la formule se réduit alors à $\mathrm{DCG@k} = \sum_{i=1}^{k} \mathbb{1}[i\in \mathrm{Rel}(q)] / \log_2(i+1)$, qui correspond à l'implémentation utilisée dans le code (`src/evaluation/retrieval_metrics.py`, fonction `ndcg_at_k`). Le calcul s'effectue après projection au niveau document ($\mathrm{Rel}(q)$ et $\mathrm{TopK}(q)$ sont dédupliqués par `doc_id` avant comparaison), de manière à ce qu'un même document représenté par plusieurs *chunks* dans le top-$k$ ne soit pas compté plusieurs fois.

Ces métriques sont au cœur de l'IR évaluative moderne [@JarvelinKekalainen2002].

L'intérêt pour le RAG est de relier ces scores à la qualité finale : par exemple, un Recall@k faible limite mécaniquement la fidélité, car la preuve n'entre jamais dans le contexte.

### Positionnement de la contribution du mémoire

Ce que ce mémoire cherche à apporter, concrètement, c'est un cadre d'évaluation qui permette de :

- séparer les erreurs de récupération et les erreurs de génération, parce que leurs corrections obéissent à des logiques différentes,
- intégrer les spécificités santé-sécurité (criticité, exceptions) que les *benchmarks* généralistes ignorent,
- rester reproductible et applicable sur un corpus d'entreprise,
- produire des diagnostics actionnables : pas seulement "c'est bon" ou "c'est pas bon", mais *quoi* améliorer (le *chunking*, le *top-k*, le *reranking*, le *prompt*, la température).

La Partie II présente la méthodologie retenue, et la Partie III l'applique à ScribBERT.

---

```{=latex}
\cleardoublepage
\thispagestyle{plain}
\vspace*{\stretch{1}}
\begin{center}
{\Huge\bfseries PARTIE II}\\[1.5em]
{\LARGE Méthodologie d'évaluation d'un système RAG}
\end{center}
\vspace*{\stretch{2}}
\addcontentsline{toc}{section}{PARTIE II \textemdash{} Méthodologie d'évaluation d'un système RAG}
\markboth{PARTIE II \textemdash{} Méthodologie d'évaluation d'un système RAG}{}
\newpage
```

La Partie I a posé les bases : ce qu'est un RAG, ce que signifient "pertinence" et "cohérence" dans ce contexte, et pourquoi ces notions sont si délicates à évaluer quand l'enjeu est la sécurité des collaborateurs. La Partie II entre dans le concret.

La question de l'évaluation a d'abord paru plus simple qu'elle ne l'est en réalité. Au début du développement de ScribBERT, la démarche relevait du tâtonnement : une configuration était testée, quelques questions étaient posées, et le constat se limitait à savoir si les réponses "avaient l'air bonnes". Sauf que cette approche montre vite ses limites : à chaque modification de paramètre (stratégie de *chunking*, modèle de vectorisation, valeur de $k$), une question qui marchait bien se dégradait, et une autre qui échouait s'améliorait. Il n'y avait pas de progression nette, pas de signal clair. C'est cette frustration qui a motivé la formalisation d'un protocole d'évaluation rigoureux.

Un fil rouge traverse l'ensemble de cette partie : l'évaluation doit être *décomposable*, c'est-à-dire capable de distinguer ce qui rate dans la couche RAG (*chunking*, vectorisation, récupération, *reranking*) de ce qui rate dans le LLM générateur. C'est cette exigence qui justifie à la fois la décomposition en dimensions (Ch. 5), le gel des autres composants lors d'une comparaison (Ch. 5.4), et le croisement de plusieurs LLMs sur la même chaîne de récupération (mis en pratique au § 8.3 avec Mistral-7B local vs `gpt-3.5-turbo` Azure). Sans cette discipline, un constat de mauvaise réponse reste imputable à n'importe quel maillon, et aucune correction ciblée n'est possible.

Trois questions structurent cette partie :

1. Quels leviers techniques influencent la qualité d'un RAG, et comment les caractériser (Chapitre 4) ?
2. Quel protocole mettre en place pour mesurer cette qualité de façon reproductible (Chapitre 5) ?
3. Comment évaluer la cohérence (fidélité aux sources, stabilité), qui est la dimension la plus difficile à automatiser (Chapitre 6) ?

L'ambition est de proposer un cadre transférable, pas spécifique à ScribBERT, mais qui sera instancié sur ce cas en Partie III.

## Modèles et paramètres influençant la performance

Un système RAG n'est pas une boîte noire à un seul bouton. C'est un assemblage de composants, chacun avec ses propres réglages, et la qualité finale dépend de l'ensemble. Le problème, constaté directement durant le projet, est que modifier un paramètre peut améliorer certains cas et en dégrader d'autres. Pour sortir du tâtonnement, il faut d'abord cartographier ces leviers et comprendre comment ils interagissent.

Ce chapitre passe en revue quatre familles :

1. les modèles de vectorisation, qui déterminent comment requêtes et documents sont représentés dans l'espace vectoriel,
2. le *chunking* et le prétraitement, qui fixent la granularité des unités indexées,
3. les stratégies de récupération (modes de récupération et de classement des passages candidats),
4. la composante de génération (le LLM, le *prompt* et les paramètres associés).

### Les modèles de vectorisation

Le modèle de vectorisation est la base d'un RAG dense. C'est lui qui détermine la géométrie de l'espace dans lequel requêtes et passages sont comparés, et si cette géométrie est mal adaptée au domaine, aucune astuce en aval ne pourra compenser.

#### Typologie des modèles disponibles

Le paysage des modèles de vectorisation évolue rapidement. Au moment de l'écriture, plusieurs familles peuvent être distinguées :

- Modèles *open-source* dérivés de BERT et SBERT : famille `sentence-transformers` (`all-MiniLM-L6-v2`, `all-mpnet-base-v2`, etc.), qui constitue une référence *open-source* largement utilisée [@ReimersGurevych2019].
- Modèles multilingues *open-source* : `multilingual-e5` (Microsoft), `BGE-M3` (BAAI), `Jina embeddings v3`, qui visent à couvrir un grand nombre de langues avec un seul modèle.
- Modèles français ou multilingues spécialisés : `Solon` (Lajavaness), `CamemBERT`-based encoders, `Sentence-CamemBERT`, utiles pour la composante française du corpus ; mais le corpus de Bouygues TP étant bilingue (cf. 4.1.3), un modèle multilingue couvrant aussi bien le français que l'anglais reste souvent préférable.
- Modèles propriétaires accessibles par API : `text-embedding-3-small/large` (OpenAI), `embed-multilingual-v3` (Cohere), `voyage-3` (Voyage AI), `gemini-embedding` (Google). Performants mais soulèvent des questions de coût, latence et confidentialité.
- Modèles spécialisés par domaine : `LegalBERT`, `BioBERT`, `SciBERT`, etc. À ce jour, aucun modèle de vectorisation *open-source* spécialisé santé-sécurité/BTP n'est librement disponible, ce qui constitue à la fois une limite et une opportunité (*fine-tuning* interne envisageable).

#### Dimensions de vectorisation : compromis qualité / coût

La dimension de sortie d'un modèle de vectorisation ($d \in \{384, 512, 768, 1024, 1536, 3072\}$ pour les plus courants) influence trois aspects :

- la qualité représentationnelle : à modèle donné, une dimension plus élevée *peut* mieux séparer les concepts, mais ce n'est pas systématique.
- le coût de stockage : un index de $N$ *chunks* stocké en `float32` (format à virgule flottante standard sur 32 bits, soit 4 octets par composante) occupe $4 \cdot N \cdot d$ octets (ex. : 1 M *chunks* en dim. 1024 ≈ 4 Go) ; des formats plus compacts (`float16`, `int8`, quantization via PQ) permettent de diviser ce coût par 2 à 8 au prix d'une légère perte de précision.
- la latence de recherche : croît linéairement avec $d$ pour la similarité, et indirectement via la taille de l'index ANN.

Les vectorisations "Matryoshka" (*Matryoshka Representation Learning*) permettent de tronquer la dimension a posteriori avec une perte limitée, offrant un curseur qualité/coût ajustable sans réindexation complète.

#### Multilinguisme et adaptation au français technique

Le corpus de ScribBERT est bilingue : les référentiels internes Bouygues TP existent aussi bien en français qu'en anglais, et la documentation client (ENBRIDGE, PAS 91, OSHA, etc.) est majoritairement en anglais. Le système doit donc gérer les deux langues de façon homogène. Deux stratégies sont envisageables :

1. Modèle multilingue généraliste : robuste sur plusieurs langues, mais souvent moins fin sur les nuances techniques d'une langue donnée.
2. Modèle multilingue de grande taille avec instruction tuning : E5, BGE, qui combine couverture linguistique et qualité.

Le *benchmark* MTEB (*Massive Text Embedding Benchmark*) fournit une comparaison standardisée entre modèles, mais il faut se rappeler que les performances MTEB ne se transposent pas mécaniquement à un domaine spécialisé [@Muennighoff2023MTEB]. Le *benchmark* BEIR a clairement montré la dégradation hors-domaine des *retrievers* entraînés sur du web généraliste [@Thakur2021BEIR].

#### Évaluation intrinsèque vs extrinsèque

Deux niveaux d'évaluation se distinguent pour un modèle de vectorisation :

- Intrinsèque : qualité de la séparation paires positives / négatives (STS, *retrieval*@k sur jeux annotés, alignement avec jugements humains)
- Extrinsèque : impact sur la tâche aval (qualité de la réponse RAG finale)

Les deux ne coïncident pas toujours : une vectorisation de qualité qui remonte "les bons documents" peut tout de même conduire à une mauvaise réponse si le générateur exploite mal le contexte. C'est une raison supplémentaire pour évaluer les composants et la chaîne complète (cf. Chapitre 5).

#### Critères de sélection en contexte industriel

En contexte d'entreprise, le choix d'un modèle de vectorisation ne se résume pas à un score sur un *benchmark*. Une grille de décision multi-critères est nécessaire :

| Critère | Question |
|--------------------------|----------------------------------------------------------------------------------------------------|
| Qualité de la récupération | Recall@k sur le corpus de test interne |
| Couverture linguistique | Le modèle gère-t-il le français et l'anglais ? |
| Coût | API payante (OpenAI, Cohere) ou auto-hébergé (GPU (*Graphics Processing Unit*)) ? |
| Latence | Temps d'inférence acceptable pour une expérience temps réel ? |
| Confidentialité | Le modèle peut-il être hébergé en interne ? Avons-nous des contrats avec clauses de confidentialité ? |
| Maintenance | Stabilité, fréquence des mises à jour |
| *Fine-tunabilité* | Possibilité d'adapter le modèle au domaine santé-sécurité si nécessaire |

Table: Critères de sélection d'un modèle de vectorisation en contexte industriel.

Pour le POC ScribBERT, ces critères ont rapidement convergé vers `text-embedding-ada-002` d'OpenAI, principalement parce qu'il était déjà exposé dans le *tenant* Azure OpenAI du groupe : pas de modèle à héberger, pas d'infrastructure GPU à monter, et la confidentialité couverte par les engagements déjà négociés pour les LLMs. Sa qualité intrinsèque n'est pas exceptionnelle (c'est un modèle déjà ancien) mais le *benchmark* de la Partie III montre qu'il fait jeu égal avec plusieurs alternatives *open-source* sur le corpus considéré. La justification détaillée et les comparaisons chiffrées de latence et de MRR sont reportées au § 7.5.2 et au § 8.2.

### Le rôle du *chunking* et du prétraitement textuel

Le *chunking* est probablement le sujet qui a demandé le plus de temps d'exploration : plusieurs jours, voire semaines, passés à *benchmarker* des algorithmes différents sur le même corpus avant de trancher. Il est souvent présenté comme un "détail d'ingestion" dans les tutoriels, mais c'est en réalité un choix de modélisation à part entière, dont les effets se propagent à toute la chaîne. Ce qui a fini par être retenu pour ScribBERT, c'est qu'une fois les PDF convertis en Markdown pour préserver la structure (titres, listes, tableaux), un *chunking* par regex sur les marqueurs structurels donne le meilleur compromis : les référentiels du corpus partagent la même charte de mise en forme, donc une regex bien ciblée récupère proprement les titres, les numérotations, les paragraphes. C'est également plus rapide à exécuter et plus prévisible qu'un *chunking* sémantique ou à longueur fixe pure.

\needspace{10\baselineskip}

#### Stratégies de *chunking*

Plusieurs approches existent, chacune avec ses compromis :

- *Chunking* à taille fixe (nombre *tokens* ou caractères) : simple, prévisible, mais aveugle à la structure. Risque majeur : couper une règle au milieu d'une phrase, ou séparer une condition de son exception.
- *Chunking* récursif (*recursive character text splitter*) : tente de découper d'abord sur des séparateurs "forts" (`\n\n`, `\n`, `. `, ` `) avant de tomber sur du caractère brut. Bon compromis par défaut, implémenté dans LangChain/LlamaIndex.
- *Chunking* structurel : exploite la hiérarchie documentaire (titres, sections, listes, tableaux). Particulièrement adapté aux référentiels et normes qui ont une structure claire.
- *Chunking* sémantique : utilise un modèle (souvent un modèle de vectorisation) pour détecter des ruptures de sujet et grouper les phrases sémantiquement proches. Plus coûteux en ingestion, gain variable.
- *Chunking* sur mesure (regex / *parser* dédié) : pour des formats spécifiques (procédures avec format imposé, fiches sécurité), un *parser* dédié peut extraire des unités cohérentes (un § = une règle).

Pour un corpus santé-sécurité, les stratégies structurelle, récursive et sur mesure sont souvent les plus pertinentes, car les règles ont une granularité naturelle (article, paragraphe numéroté, étape de procédure).

#### Taille des *chunks* et chevauchement

Deux paramètres clés interagissent :

- Taille du *chunk* ($T$, en *tokens*) : un chunk trop petit peut mener à une perte de contexte, de l'ambiguïté, perte de l'antécédent ("il", "cette règle") ; à l'inverse d'un chunk trop grand qui amène de la dilution sémantique, une vectorisation moins discriminante, un contexte LLM potentiellement saturé.
- *Overlap* ($O$, généralement 10-20 % de $T$) : permet d'amortir les coupures malheureuses au prix d'une redondance dans l'index.

L'optimum dépend du type de question : les questions factuelles courtes tolèrent des *chunks* petits, tandis que les questions procédurales ("comment faire X ?") requièrent souvent des *chunks* plus larges qui capturent une séquence d'étapes. C'est ce genre de tensions qui a été observé lors du développement : en réduisant la taille des *chunks*, la précision augmentait sur certaines questions, mais la cohérence des réponses se dégradait sur d'autres. Un protocole rigoureux teste plusieurs configurations ($T \in \{256, 512, 1024\}$, $O \in \{0, 64, 128\}$) et mesure l'impact *end-to-end*. C'est ce qui est fait en Partie III.

\needspace{10\baselineskip}

#### Préservation de la structure et des métadonnées

Un *chunk* "brut" (texte seul) perd des informations critiques : section d'origine, niveau hiérarchique, type de document, date de validité, autorité émettrice. Or ces métadonnées :

- enrichissent les filtres de récupération ("uniquement les docs en français" / "documents BYTP seulement") ;
- permettent de citer correctement la source dans la réponse ;
- aident à arbitrer les contradictions (préférer le plus haut niveau d'autorité, le document qui traite la question en sujet principal et pas en secondaire dans un petit paragraphe).

Un schéma de métadonnées robuste pour ScribBERT pourrait inclure : `document_id`, `titre`, `type` (procédure, standard, guide), `autorité` (groupe / filiale / chantier / client), `date`, `langue`.

#### Nettoyage et normalisation

Le prétraitement comprend :

- Extraction texte depuis PDF. Les PDFs techniques posent des problèmes spécifiques : tableaux, schémas avec légendes, en-têtes/pieds de page répétitifs. Des outils comme `Unstructured`, `pdfplumber`, `pymupdf` ou `Marker` ont des compromis différents.
- Suppression du bruit : numéros de page, en-têtes répétés, filigranes.
- Normalisation : unification des guillemets, des espaces insécables, des tirets ; éventuellement passage en minuscules pour le *sparse retrieval* (mais pas pour les *vectorisations*, qui sont généralement sensibles à la casse).
- Conservation du formatage utile : listes à puces, numérotation hiérarchique, gras pour les termes-clés.

Un point souvent négligé : les tableaux et les schémas. Linéariser un tableau en texte brut détruit sa structure. Des stratégies plus avancées (extraction structurée, légendes générées par un VLM (*Vision Language Model*), tableaux convertis en markdown) peuvent être étudiées.

### Les stratégies de récupération

Une fois l'index constitué, la récupération comporte plusieurs leviers : choix de la similarité, hybridation sparse/dense, *reranking*, filtrage, expansion de requête, valeur de $k$.

#### Similarité cosinus et alternatives

La similarité cosinus est la mesure par défaut pour comparer deux vectorisations :

$$\mathrm{sim}(q, d) = \frac{\mathbf{e}_q \cdot \mathbf{e}_d}{\|\mathbf{e}_q\| \cdot \|\mathbf{e}_d\|}$$

Elle suppose que seule la direction des vecteurs porte le sens (pas la norme). La plupart des modèles modernes sont entraînés sous cette hypothèse (vecteurs L2-normalisés), ce qui rend cosinus et produit scalaire équivalents.

Limites : le cosinus est une mesure isotrope qui ne tient pas compte de la structure locale de l'espace. Des travaux sur les vectorisations anisotropes montrent que certains modèles concentrent leurs vecteurs dans un cône étroit, ce qui dégrade la séparation.

#### Recherche hybride : combiner sparse et dense

L'hybridation BM25 + dense est devenue un standard de fait. Deux stratégies :

- Combinaison de scores : $\mathrm{score} = \alpha \cdot \mathrm{score}_{\text{dense}} + (1-\alpha) \cdot \mathrm{score}_{\text{sparse}}$, avec $\alpha \in [0,1]$ à régler.
- Reciprocal Rank Fusion (RRF) : $\mathrm{RRF}(d) = \sum_i \frac{1}{\kappa + r_i(d)}$ (avec $\kappa$ une constante de lissage usuelle, typiquement $\kappa = 60$, distincte du top-$k$ de la récupération), qui combine les rangs et non les scores (plus robuste à des échelles hétérogènes).

L'hybridation est particulièrement utile sur des corpus techniques où :

- le dense capture les paraphrases et l'intention,
- le sparse garantit le rappel sur des identifiants exacts (numéros de procédure, codes EPI, références normatives).

Pour ScribBERT, l'hypothèse forte est qu'un utilisateur citant explicitement "PR-SST-042" doit retrouver ce document, ce que BM25 garantit mais qu'un dense pur peut manquer. Cette hypothèse sera testée en Partie III. Empiriquement, en passant de `dense-k5` à `hybrid-k5` sur les questions réelles, le bénéfice est tangible : les bons documents remontent plus souvent en tête, et les cas où le bon document ne sort tout simplement pas se font plus rares. En revanche, aucun effet *lost in the middle* significatif n'a été observé sur le top-5 de ScribBERT, le contexte restant suffisamment court pour que le LLM exploite chaque *chunk*.

#### *Reranking* par *cross-encoder*

Le *reranking* consiste à appliquer un modèle plus précis (et plus coûteux) à un petit ensemble de candidats déjà récupérés. Les *cross-encoders* (ex. `ms-marco-MiniLM`, `bge-reranker-v2-m3`, `Cohere Rerank`) lisent conjointement la requête et le passage et produisent un score de pertinence [@NogueiraCho2019].

Chaîne de traitement typique :

1. Récupération initiale pour obtenir le top-100 des candidats (rapide, $O(\log N)$ sur HNSW),
2. *Reranking* pour ne conserver que le top-10 (lent : 100 inférences *cross-encoder*, $\sim$ 100-500 ms),
3. Génération sur top-10 (ou top-5).

Le gain de qualité est souvent substantiel mais le coût en latence est non négligeable. Le compromis dépend de la criticité de l'application.

#### Filtrage par métadonnées

Le filtrage permet de restreindre la recherche selon des contraintes structurelles :

- Pré-filtrage : appliquer le filtre avant la recherche vectorielle (ex. uniquement les documents en anglais, uniquement les procédures).
- Post-filtrage : récupérer puis filtrer (plus simple, mais peut vider le *top-k* et empêcher d'autres documents pertinents de remonter).

Un filtrage trop strict peut éliminer les bons passages au même titre qu'un post-filtrage gaspille du calcul. Les bases vectorielles modernes (Qdrant, Weaviate, Pinecone) optimisent le pré-filtrage. ChromaDB, utilisé pour le POC de ScribBERT, supporte le pré-filtrage par métadonnées, bien qu'il soit davantage adapté au développement local et aux petits corpus.

Pour ScribBERT, des filtres pertinents incluent : provenance du document (groupe vs client), type de document (procédure, standard, guide), langue (français vs anglais).

#### Choix de $k$ : compromis rappel / bruit / coût

La valeur du top-$k$ retourné au générateur a un effet en U inversé :

- $k$ trop petit : la "bonne" preuve n'est pas dans le contexte, la génération peut être erronée.
- $k$ trop grand : dilution, bruit, coûts élevés (*tokens* consommés, latence), risque de *lost in the middle* (le LLM ignore les passages au milieu du contexte).

Valeurs typiques : $k \in [3, 10]$ après *reranking*. La valeur optimale dépend du modèle de génération (les LLMs récents avec contexte long tolèrent mieux $k$ élevé, même si le phénomène *lost in the middle* persiste y compris sur les contextes longs[@Liu2024LostMiddle]) et du type de question.

#### *Query expansion* et reformulation

Plusieurs techniques visent à enrichir ou reformuler la requête :

- HyDE (*Hypothetical Document Embeddings*) : faire générer par un LLM une réponse hypothétique à la requête, puis utiliser sa vectorisation pour la recherche. Améliore le rappel sur des questions complexes.
- *Multi-query* : générer plusieurs reformulations de la requête, lancer plusieurs recherches, fusionner les résultats.
- *Step-back prompting* : reformuler la requête en une question plus générale, qui peut mieux correspondre à des passages introductifs.
- Query rewriting via LLM : corriger les fautes, expanser les acronymes ("EPI" en "équipement de protection individuelle"), normaliser le vocabulaire.

Ces techniques améliorent généralement le rappel mais ajoutent de la latence, augmentent les coûts et peuvent introduire une dérive sémantique (la reformulation s'éloigne de l'intention initiale). Un protocole d'évaluation rigoureux doit mesurer le gain net.

### La composante de génération

Une fois les passages sélectionnés, la génération transforme le contexte en réponse. Plusieurs leviers conditionnent la qualité.

#### Choix du LLM

Les options se classent en trois catégories :

- LLMs propriétaires (API) : GPT-4 / GPT-4o (OpenAI), Claude 3.5/4 (Anthropic), Gemini (Google), Mistral Large. Excellente qualité, coût marginal par requête/*token*, dépendance à un fournisseur externe et contraintes de confidentialité.
- LLMs *open-weights* auto-hébergés : Llama 3, Mistral / Mixtral, Qwen, DeepSeek, Gemma. Contrôle total des données, coût d'infrastructure (GPU).
- LLMs spécialisés : modèles plus petits fine-tunés sur un domaine (ex. modèles biomédicaux). À ce jour, pas d'option appliquée au domaine santé-sécurité et BTP.

Pour ScribBERT, l'absence d'infrastructure GPU chez Bouygues TP a rendu les modèles auto-hébergés peu viables : les tests en local sur un poste de développement standard n'ont permis de faire tourner que des modèles de petite taille, et même ceux-ci se sont révélés trop lents pour être exploitables. Le choix s'est porté sur un LLM propriétaire via Azure OpenAI, dans le cadre d'un contrat-cadre Bouygues Construction garantissant la confidentialité des données. Concrètement, pour le POC, le choix s'est porté sur `gpt-3.5-turbo` : il est bon marché, rapide, et la différence de qualité avec un GPT-4 / Claude / Mistral Large est amortie par la contextualisation RAG. Le déploiement via Azure OpenAI a aussi un atout opérationnel : aucune brique d'infrastructure à gérer en propre. Pour le passage en production, un modèle plus récent (GPT-4o ou équivalent) sera réévalué, notamment sur les questions justificatives où quelques limites qualitatives ont été perçues. 

#### Ingénierie de *prompt*

Le *prompt* système est le contrat passé entre le développeur et le modèle. Un *prompt* RAG contient généralement quatre éléments : les instructions système (rôle, contraintes, règles de comportement), la requête utilisateur, le contexte récupéré (passages formatés et numérotés), et le format de sortie attendu.

Dans la pratique, quelques principes font consensus. L'*ancrage explicite* est essentiel : il faut dire au modèle de ne répondre que sur la base des extraits fournis, et de l'indiquer clairement si l'information n'y figure pas. Les citations obligatoires ("cite chaque affirmation avec le numéro de la source") améliorent la traçabilité. Et surtout, il faut autoriser le modèle à dire "je ne sais pas". C'est contre-intuitif (l'utilisateur attend des réponses), mais c'est ce qui réduit le plus efficacement les hallucinations. (Un ou deux exemples (*few-shot*) de paires question/réponse peuvent aussi être ajoutés pour calibrer le style.)

#### Gestion de la fenêtre de contexte

Le budget de *tokens* est une contrainte structurante. Avec 10 passages de 500 *tokens* chacun et un modèle qui accepte 8k *tokens* en contexte, il faut faire des choix. La stratégie la plus simple est la troncature (couper les passages les moins bien classés). Les *chunks* longs peuvent aussi être compressés avant injection, ou le contexte rempli par ordre de pertinence jusqu'à un seuil. Les LLMs récents acceptent des contextes de 128k *tokens* et plus, mais attention au phénomène *lost in the middle* expliqué plus tôt : le modèle tend à moins bien exploiter les passages placés au milieu d'un gros contexte, ce qui peut fausser les réponses.

#### Paramètres de décodage

- Température : 0 pour la reproductibilité (cas critiques santé-sécurité), 0.2-0.5 pour un compromis qualité/diversité, ≥ 0.7 pour la créativité (peu pertinent ici).
- Top-p / *top-k* sampling : alternative à la température, plus rarement utilisée en RAG.
- Max *tokens* : borne haute pour éviter les réponses interminables.
- Repetition / presence penalty : utile si le modèle "bégaie" sur des termes techniques.

Pour ScribBERT, une température faible est recommandée afin de garantir la stabilité des réponses (cf. Chapitre 6).

#### Citations et traçabilité

La citation peut prendre plusieurs formes : *inline* ("Selon [1], le port du harnais est obligatoire dès 2 m"), en fin de réponse (liste des sources), ou avec reproduction littérale des passages clés.

L'important, au-delà du format, est que la traçabilité soit *machine-vérifiable*. Chaque citation doit pointer vers un identifiant de *chunk* journalisé, lui-même relié au document d'origine. Sans cette chaîne, la traçabilité reste de surface, utile pour l'utilisateur mais insuffisante pour l'audit et pour la mesure de fidélité (cf. Chapitre 6).

#### Garde-fous pour le contexte santé-sécurité

En contexte critique, il faut prévoir des garde-fous explicites. Le plus important est le refus contrôlé : quand la récupération ne trouve rien de suffisamment pertinent, mieux vaut répondre "je n'ai pas trouvé cette information dans les référentiels" plutôt que d'improviser. De même, si plusieurs sources se contredisent, le système devrait le signaler plutôt que d'arbitrer en silence. Pour les questions hors périmètre santé-sécurité, un message de refus est préférable à une réponse approximative.

Ces garde-fous n'apparaissent pas spontanément : la première version du *prompt* système de ScribBERT était beaucoup trop permissive. Sur des questions qui n'avaient rien à voir avec la santé-sécurité, le modèle sortait des recettes de cookies, répondait à partir de sa connaissance générale, et oubliait de citer ses sources. Les instructions ont dû être durcies progressivement : cadrer explicitement le domaine, exiger une citation, autoriser et même encourager le "je ne sais pas" lorsque le contexte ne contient pas l'information. C'est en partie ce qui a permis de comprendre que le *prompt* fait autant partie de l'évaluation que le modèle ou la vectorisation.

### Synthèse des leviers et matrice d'expérimentation

L'ensemble des leviers présentés peut être résumé dans une matrice qui guidera la conception du protocole expérimental (Chapitre 5) :

| Composant | Leviers principaux | Métriques affectées en priorité |
|---------------------|---------------------------------------------|--------------------------------|
| Vectorisation | Modèle, dimension, langue, *fine-tuning* | Recall@k, MRR, nDCG |
| *Chunking* | Stratégie, taille, chevauchement, métadonnées | Recall@k, citabilité, fidélité |
| Récupération | Sparse / dense / hybride, filtres, $k$ | Recall@k, précision contexte |
| *Reranking* | Présence, modèle, top-$n$ | Precision@k, fidélité |
| Traitement de requête | Expansion, reformulation, HyDE | Recall@k (gain), latence (perte) |
| Génération (LLM) | Choix du modèle, taille | Fluidité, fidélité, latence |
| Génération (*prompt*) | Instructions, *few-shot*, format | Fidélité, format, refus contrôlé |
| Génération (décodage) | Température, max *tokens* | Stabilité, longueur |

Table: Synthèse des leviers techniques d'un système RAG et métriques affectées.

L'expérimentation menée en Partie III ne pourra pas tester toutes les combinaisons (explosion combinatoire). Elle adoptera une approche OFAT (*One-Factor-At-a-Time*) sur un sous-ensemble de paramètres jugés les plus impactants, complétée par quelques expériences factorielles ciblées.

Le Chapitre 5 présente le protocole d'évaluation lui-même : jeux de test, métriques, conditions d'expérimentation.

```{=latex}
\newpage
```

## Construction d'un protocole d'évaluation

Le Chapitre 4 a inventorié les différents leviers actionnables. Reste la question fondamentale : **comment mesurer leur effet ?** Sans un protocole d'évaluation structuré, le tâtonnement décrit plus haut s'impose à nouveau : un paramètre est modifié, trois questions sont posées, et reste l'"impression" que c'est mieux ou moins bien, sans pouvoir trancher. C'est une leçon répétée à plusieurs reprises par Julien Larseneur dans l'équipe : la tentation initiale était de se fier à la fiabilité perçue, en posant quelques questions et en jugeant les réponses. Julien ne jure que par les métriques, et a détaillé les différentes familles (Recall, MRR, *faithfulness*…), leurs limites individuelles, et l'intérêt d'en croiser plusieurs. Ce chapitre est en grande partie la formalisation de ces échanges.

Ce que ce protocole cherche à produire, ce sont des mesures reproductibles (le même test donne le même résultat), comparables (les configurations peuvent être ordonnées), et surtout diagnostiques, qui permettent de dire où se situe le problème dans la chaîne, pas seulement que la réponse finale est "bonne" ou "mauvaise".

Ce chapitre s'organise en cinq sections : les critères d'évaluation (§ 5.1), les approches (automatique, humaine, hybride) (§ 5.2), la construction du jeu de test (§ 5.3), les conditions expérimentales (§ 5.4), et les méthodes d'analyse (§ 5.5).

### Cinq dimensions pour mesurer la fiabilité

Le Chapitre 3.3 a défini la fiabilité opérationnellement comme la conjonction de cinq propriétés. Plutôt que de dresser une liste plate de métriques, j'organise ici l'évaluation autour de ces cinq dimensions : pour chacune, le type d'échec à détecter est précisé, puis les métriques candidates, en privilégiant celles qui sont effectivement utilisables dans un cadre industriel.

#### Dimension 1 - Pertinence de la récupération

*Les passages récupérés contiennent-ils l'information nécessaire pour répondre ?*

C'est le premier maillon de la chaîne, et si la récupération rate la bonne règle, rien dans la suite ne peut compenser. Plusieurs métriques permettent de le mesurer, selon l'angle visé :

- Hit@k : est-ce qu'au moins un passage pertinent figure dans les $k$ résultats retournés ? C'est la mesure la plus simple : une réponse binaire "oui/non" par question.
- Recall@k : quelle proportion des passages pertinents a été retrouvée ? Utile quand la réponse attendue nécessite plusieurs sources distinctes.
- Precision@k : parmi les $k$ passages retournés, combien sont réellement utiles ? Une récupération avec beaucoup de bruit nuit à la génération même si les bons passages sont là.
- MRR (*Mean Reciprocal Rank*) : le premier passage pertinent est-il bien classé en tête ? C'est la bonne métrique lorsqu'un passage décisif est principalement attendu.
- nDCG@k : variante pondérée qui tient compte de la position (un passage pertinent classé 2ème est meilleur que le même classé 8ème). Utile si les jugements de pertinence sont gradués (très pertinent / un peu pertinent / hors-sujet).

Pour ScribBERT, Recall@k et MRR sont les métriques principales : l'enjeu est avant tout de s'assurer que la "bonne règle" figure bien parmi les passages remontés. Le Hit@k est un bon complément rapide pour les questions qui n'ont qu'un seul passage.

#### Dimension 2 - Fidélité aux sources (*faithfulness*)

*La réponse s'en tient-elle à ce que disent vraiment les passages récupérés ?*

C'est la dimension la plus critique pour ScribBERT. Une réponse peut être fluide et cohérente, mais complètement inexacte, soit parce que le modèle a "rajouté" des éléments absents des sources, soit parce qu'il a modifié le sens. L'enjeu n'est pas seulement la véracité des faits, c'est la conformité aux sources fournies.

Plusieurs approches permettent de mesurer ça automatiquement :

- Faithfulness (RAGAS) : la réponse est décomposée en propositions atomiques ("le port du harnais est obligatoire dès 2 m"), et chacune est vérifiée contre le contexte par un *LLM-juge*. Le score final est la proportion de propositions supportées.
- NLI-based scoring : un modèle d'inférence textuelle (NLI) vérifie si chaque phrase de la réponse est logiquement impliquée par le contexte. Plus robuste pour les phrases longues que l'approche atomique.
- *Citation faithfulness* : lorsque la réponse cite un passage explicitement, ce passage supporte-t-il réellement l'affirmation ? C'est une vérification de cohérence entre la citation et le contenu.
- Hallucination rate : simplement le taux de propositions non supportées (= 1 − *faithfulness*).

À ces métriques génériques peut s'ajouter, en contexte santé-sécurité, une mesure plus spécifique : la préservation des modalités : la réponse respecte-t-elle les niveaux d'obligation des sources ("doit" vs "peut" vs "il est recommandé de") ? Cette dimension est difficile à automatiser de façon fiable et nécessite souvent une vérification humaine ou un *LLM-juge* avec des instructions très précises à ce sujet.

#### Dimension 3 - Pertinence et complétude de la réponse

*La réponse dit-elle ce qu'il faut, ni plus ni moins ?*

Cette dimension évalue la réponse en tant que telle, indépendamment de ses sources : est-ce qu'elle répond vraiment à ce qui était demandé ? Est-ce qu'elle est complète ? Est-ce qu'elle est calibrée en longueur ?

- Answer relevance (RAGAS) : un *LLM-juge* génère plusieurs questions hypothétiques à partir de la réponse produite, puis mesure si elles ressemblent à la question originale. Une réponse hors-sujet ou vague produira des questions hypothétiques éloignées.
- Complétude : en comparaison avec une réponse de référence annotée par un expert, quelle proportion des éléments attendus (étapes, conditions, exceptions) est présente dans la réponse générée ?
- Concision : la réponse est-elle proportionnée à la complexité de la question, ou le modèle noie-t-il l'information dans une réponse excessivement longue ?
- Respect du format : si le *prompt* demande une check-list numérotée, le modèle l'a-t-il bien produite ?

#### Dimension 4 - Stabilité et répétabilité

*Si la même question est rejouée, la réponse est-elle cohérente ?*

Un système peut obtenir de bons scores en moyenne tout en produisant des réponses très variables d'une exécution à l'autre. Cette dimension, traitée en détail au Chapitre 6, mesure la variance des réponses plutôt que leur qualité moyenne. Elle conditionne également la robustesse statistique de toutes les comparaisons du protocole : si la variabilité intra-configuration est élevée, comparer deux configurations sur une seule exécution par question n'a pas de sens.

#### Dimension 5 - Traçabilité et auditabilité

*Est-il possible de vérifier, a posteriori, l'origine de chaque affirmation de la réponse ?*

Il ne suffit pas que la réponse soit juste, il faut pouvoir le prouver. Cette dimension mesure la qualité de la chaîne de traçabilité entre chaque affirmation et son passage source :

- *Citation correctness* : les passages cités existent-ils, sont-ils pertinents, et supportent-ils réellement l'affirmation ?
- *Citation completeness* : toutes les affirmations qui devraient être sourcées le sont-elles ?
- Diversité des sources : la réponse s'appuie-t-elle sur plusieurs documents, ou paraphrase-t-elle toujours la même source ? Un signal d'agrégation est une bonne chose sur les questions transverses/multi-documents.

Ces métriques ne sont utiles que si le *prompt* impose un format de citation *machine-vérifiable* (identifiants de *chunks*, pas juste des titres de documents).

#### Coût opérationnel

Ces cinq dimensions décrivent la qualité du système. En production, s'y ajoutent des métriques de coût qui conditionnent la viabilité opérationnelle :

- Latence de la chaîne complète (récupération + *reranking* + génération). En pratique, un percentile P95 est plus significatif que la moyenne pour mesurer l'expérience utilisateur réelle.
- Coût par requête si le LLM ou le modèle de vectorisation est facturé à l'usage.
- Taux de refus : proportion de requêtes pour lesquelles le système répond "je ne sais pas" faute de sources suffisantes. C'est une métrique à double lecture : un taux trop bas suggère que le système improvise (hallucine), un taux trop élevé indique une expérience utilisateur dégradée.

### Approches d'évaluation : automatique, humaine, hybride

#### Évaluation automatique

Les métriques automatiques se classent en trois familles :

- Lexicales (BLEU, ROUGE, METEOR, *exact match*) : peu adaptées à la QA générative car elles pénalisent la paraphrase légitime. Utiles uniquement pour des réponses très courtes et factuelles.
- Vectorielles (BERTScore, BLEURT, similarité cosinus des vectorisations de réponse) : capturent mieux la similarité sémantique. Limitation : peuvent juger "proches" deux réponses dont l'une contient une erreur factuelle subtile [@Zhang2020BERTScore; @Sellam2020BLEURT].
- LLM-based / LLM-as-judge : un LLM note la réponse selon une grille (G-Eval, Prometheus, RAGAS, TruLens). Approche dominante pour le RAG aujourd'hui : flexible, capable de juger la fidélité, la complétude, la modalité.

Avantages : passage à l'échelle (millions de requêtes), reproductibilité (à seed et *prompt* fixés), coût marginal réduit.

Limites :

- corrélation imparfaite avec le jugement humain expert (surtout en domaine spécialisé comme dans notre cas) ;
- biais du *LLM-juge* (préférence pour les réponses verbeuses, biais de longueur, biais de formatage) ;
- risque de sur-évaluation si le même LLM sert de générateur et de juge (auto-validation circulaire) ;
- difficulté à juger les modalités, les exceptions, les conditions implicites.

Bonnes pratiques :

- Utiliser un *LLM-juge* différent du générateur évalué.
- Si possible, "calibrer" le *LLM-juge* sur un échantillon annoté humainement (quelques exemples).
- *Journaliser* les justifications du juge, pas seulement le score.
- Mesurer la stabilité du juge lui-même (même *prompt*, $n$ exécutions).

#### Évaluation humaine

Constitue le *gold standard*, particulièrement pour les dimensions difficiles à automatiser (modalités, sécurité, exceptions).

Conception d'une grille d'évaluation :

| Critère | Échelle | Définition |
|-------------------------|---------|--------------------------------------------------------------------------------------|
| Pertinence | 0-3 | 0 = hors-sujet, 3 = répond exactement à la question |
| Fidélité aux sources | 0-3 | 0 = invente, 3 = parfaitement supporté par les sources fournies |
| Complétude | 0-3 | 0 = manquements importants, 3 = couvre toutes les exceptions |
| Modalité (santé-sécurité) | 0-2 | 0 = transforme une obligation en recommandation ou inversement, 2 = modalité conservée |
| Sûreté opérationnelle | 0-3 | 0 = induirait un comportement dangereux, 3 = aligné avec les bonnes pratiques |
| Citations | 0-2 | 0 = aucune ou erronée, 2 = chaque affirmation citée correctement |

Table: Grille générique d'évaluation humaine d'une réponse RAG.

Bonnes pratiques :

- Plusieurs annotateurs par item (idéalement 2-3) pour mesurer l'accord inter-annotateurs (Kappa de Cohen, $\alpha$ de Krippendorff).
- Annotation à l'aveugle sur la configuration testée (l'annotateur ne sait pas quel système a produit la réponse).
- Profil mixte d'annotateurs : experts métiers et utilisateurs cibles, pour capturer expertise et utilisabilité.
- Charte d'annotation documentée et exemples gold pour calibrer.

Limites : coût, temps, subjectivité résiduelle, fatigue de l'annotateur, passage à l'échelle.

#### Approche hybride : évaluation automatique préliminaire et validation humaine ciblée

L'idée est d'articuler les deux approches pour que chacune compense les limites de l'autre :

1. Évaluation automatique préliminaire, sur l'ensemble du jeu de test : toutes configurations, toutes questions. Rapide et peu coûteuse, elle fournit une première vue d'ensemble des tendances et permet d'identifier les écarts les plus marqués entre configurations avant d'engager un effort d'annotation plus lourd.
2. Sélection ciblée d'un sous-ensemble pour annotation humaine : typiquement, les cas où le jugement automatique et le retour utilisateur divergent le plus (top-30 par exemple), complétés par une sélection de cas critiques santé-sécurité.
3. Calibration : l'échantillon annoté manuellement sert à corriger les biais identifiés dans le *LLM-juge* et à mieux interpréter ses scores sur le reste du jeu de test.
4. Triangulation : une conclusion n'est retenue qu'en cas de convergence des deux approches. Les divergences ne sont pas écartées : elles constituent souvent les cas les plus instructifs à analyser.

### Construction du jeu de test

La qualité du jeu de test conditionne la validité de toute l'évaluation. Cette section décrit la démarche méthodologique générique. L'instanciation pour ScribBERT figurera en Partie III.

#### Sources des questions

Quatre sources complémentaires :

1. Questions "naturelles" issues de l'usage : extraites des journaux. Avantage : représentativité des intentions réelles.
2. Questions générées par experts : un panel d'experts santé-sécurité rédige des questions couvrant systématiquement les domaines, niveaux de risque, types de procédures.
3. Questions générées par LLM à partir des documents : pour chaque *chunk* pertinent, un LLM génère une question dont la réponse est dans le *chunk*. Permet une couverture exhaustive du corpus mais introduit un biais (questions trop bien formées).
4. Questions adversariales : questions hors-périmètre, ambiguës, formulations terrain (jargon, fautes), questions à réponses contradictoires dans le corpus. Test des garde-fous.

#### Typologie des questions

Pour un protocole diagnostique, il convient de stratifier le jeu de test selon plusieurs axes :

\needspace{10\baselineskip}

Par type d'intention :

- Factuelles ("Quelle est la hauteur minimale pour port du harnais ?") réponse courte, vérifiable.
- Procédurales ("Quelle est la procédure avant intervention en espace confiné ?") réponse multi-étapes.
- Conditionnelles ("Que faire si... ?") gestion des exceptions.
- Comparatives ("Quelle différence entre... ?") agrégation multi-sources.
- Justificatives ("Pourquoi cette mesure est-elle requise ?") explication d'une norme.
- Hors-périmètre (test du refus contrôlé).

Par niveau de difficulté :

- Facile : la réponse est dans un seul passage explicite.
- Moyen : nécessite 2-3 passages.
- Difficile : exception ou condition à identifier, modalité subtile ou contradiction apparente à arbitrer.

Par criticité métier :

- Élevée : erreur potentiellement dangereuse (port d'EPI vital, procédure de mise en sécurité).
- Moyenne : erreur procédurale sans conséquence vitale immédiate.
- Faible : information administrative ou organisationnelle.

#### Annotation

Pour chaque question sont annotés :

- Réponse de référence rédigée par un expert (idéalement validée par un second expert, mais *time-consuming*).
- Passages de référence : identifiants des *chunks* contenant l'information nécessaire et suffisante.
- Métadonnées : type, difficulté, criticité, document(s) source(s).
- Variantes acceptables (paraphrases de la réponse de référence, formats alternatifs).

#### Volume et représentativité

Un ordre de grandeur utile pour un RAG d'entreprise est d'environ 150 à 300 questions annotées, créées selon les axes évoqués ci-dessus. Cela permet :

- des estimations stables des métriques globales (intervalle de confiance acceptable),
- des analyses par groupe (par type, par difficulté),
- la détection d'effets significatifs entre configurations.

En-deçà de 100 questions, les comparaisons entre configurations sont sujettes à un fort bruit statistique.

#### Versioning

Le jeu de test évolue (corrections, ajouts, retraits). Le versionnage porte sur :

- le contenu (questions, réponses de référence, passages de référence),
- le corpus de référence (documents, *chunks*, vectorisations) : un jeu de test n'a de sens que pour une version donnée du corpus,
- les annotations (qui, quand, sur quelle base).

### Conditions expérimentales et reproductibilité

#### Isolation des facteurs

Étant donné l'explosion combinatoire des leviers (Ch. 4), deux stratégies sont typiquement adoptées :

- OFAT (*One-Factor-At-a-Time*) : faire varier un paramètre à la fois autour d'une configuration de référence. Simple, interprétable, mais ne capture pas les interactions.
- Plans factoriels (réduits) : tester les combinaisons d'un sous-ensemble de facteurs (plans fractionnels, designs orthogonaux). Capture les interactions au prix d'un volume d'expériences plus important.

Pour ce mémoire, l'approche OFAT sera privilégiée pour les comparaisons principales.

#### Configuration de référence

Toute expérience compare à une configuration de référence documentée :

- modèle de vectorisation et version exacte,
- stratégie et paramètres de *chunking*,
- type de récupération et top-$k$,
- modèle de génération et version exacte,
- *prompt* complet,
- paramètres de décodage (température, max *tokens*,...).

Cette configuration de référence est elle-même l'objet d'une évaluation initiale, sur l'ensemble des dimensions, qui sert de point de comparaison pour toutes les variantes.

#### Reproductibilité

Pour qu'une expérience soit reproductible :

- fixer les seeds (générateur, ANN si applicable) ;
- figer les versions des modèles (un même nom de modèle peut être mis à jour silencieusement par le fournisseur) ;
- *journaliser* la requête, le contexte récupéré, la réponse complète, les métadonnées de chaque passage ;
- archiver les jeux de test versionnés et les résultats bruts.

Lorsque la reproductibilité parfaite est impossible (LLM propriétaires non déterministes), des distributions sont rapportées sur $n$ runs (médiane et IQR) plutôt que des valeurs ponctuelles.

### Méthodes d'analyse

#### Statistiques descriptives

Pour chaque configuration et chaque métrique : analyser la moyenne, médiane, écart-type, IQR et distribution (histogramme). La moyenne seule ne suffit pas, un score de fidélité à 0,85 peut très bien cacher 15 % de réponses complètement inventées, ce qui est inacceptable en santé-sécurité.

#### Tests de significativité

Pour comparer deux configurations sur une métrique :

- Test apparié (la même question est posée aux deux configurations) : préférer le test de Wilcoxon signed-rank, non paramétrique et robuste. Le test t apparié reste possible si la distribution des différences est proche de la normale.
- Correction multiple lorsque plusieurs métriques ou plusieurs configurations sont testées simultanément (Bonferroni, Holm).
- Effet plutôt que p-value seule : rapporter la taille d'effet (différence moyenne, Cohen's $d$) et un intervalle de confiance.

#### Stratification et analyses par sous-groupe

L'analyse par strate (type de question, difficulté, criticité) est essentielle : une amélioration moyenne de 5 % peut masquer une dégradation sur les questions difficiles, ce qui est inacceptable en santé-sécurité. Les métriques sont rapportées systématiquement par strate pour s'assurer que l'amélioration se vérifie à tous les niveaux.

#### Analyse d'erreurs typologique

Pour les cas d'échec, une typologie d'erreurs raffinée est construite à partir des observations :

| Catégorie | Description | Localisation probable |
|-------------------------------|--------------------------------------------|------------------------------|
| Échec de récupération | Aucun passage pertinent dans le top-$k$ | *Vectorisation* / *chunking* / $k$ |
| Bruit de récupération | Passages tentants mais non applicables | *Vectorisation* / *reranking* |
| Hallucination factuelle | Affirmation non supportée | Génération / *prompt* |
| Omission d'exception | Règle correcte mais condition oubliée | Génération / contexte tronqué |
| Inversion de modalité | "doit" devenu "peut" | Génération / *prompt* |
| Contradiction silencieuse | Sources divergentes non signalées | *Prompt* / corpus |
| Refus à tort | Refuse alors que l'info est dans le contexte | *Prompt* / seuils |
| Réponse hors-périmètre acceptée | Aurait dû refuser | *Prompt* / garde-fous |

Table: Typologie générique des erreurs d'un système RAG et localisation probable.

Cette typologie sert de grille pour l'analyse qualitative en Partie III et oriente les améliorations.


### Synthèse

Le protocole proposé articule cinq dimensions de la fiabilité (récupération, fidélité, pertinence, stabilité et traçabilité) avec trois approches d'évaluation (automatique, humaine, hybride), appliquées sur un jeu de test stratifié dans des conditions expérimentales reproductibles, et analysées avec des outils statistiques adaptés.

Le Chapitre 6 approfondit la dimension stabilité, qui mérite un traitement spécifique car elle est sous-traitée par les *frameworks* usuels et particulièrement critique pour un système RAG en production sur un sujet sensible.

```{=latex}
\newpage
```

## Évaluation de la stabilité et de la répétabilité

### Pourquoi la stabilité est une dimension distincte de la fiabilité

Les métriques classiques d'évaluation d'un RAG évoquées plus tôt sont calculées sur une exécution unique d'une requête. Elles décrivent la qualité moyenne d'une réponse à un instant t, mais ne disent rien sur ce qui se passe lorsque la même requête est rejouée ou que l'utilisateur formule légèrement différemment sa question.

Or trois phénomènes rendent un RAG intrinsèquement variable :

1. Stochasticité de la génération : à température > 0, le LLM échantillonne à chaque *token*, conduisant à des réponses différentes pour une même entrée.
2. Approximation de la récupération : les algorithmes ANN (HNSW, IVF) introduisent une approximation contrôlée mais réelle ; deux exécutions strictement identiques peuvent même retourner des ordres légèrement différents selon l'implémentation, les égalités de scores (plusieurs passages au même score ordonnés arbitrairement) et la concurrence (sur un index distribué, l'ordre dépend du shard répondant en premier).
3. Sensibilité au *prompt* et à la formulation : une question tournée différemment peut modifier le top-$k$ retourné et donc la réponse.

Pour un système d'aide à la décision en santé-sécurité, la variabilité est un problème. Un préventeur ou compagnon qui obtient deux réponses différentes à la même question perd confiance, et plus gravement, peut prendre des décisions différentes selon le moment où il a posé la question. La stabilité fait partie intégrante de la fiabilité (fiabilité apparente a minima), au même titre que la justesse moyenne.

Cette dimension est aussi un enjeu méthodologique : si la variance au sein d'une même configuration est élevée, comparer deux configurations sur une exécution unique n'a pas de sens, le bruit de mesure dépasse l'effet à mesurer. L'évaluation de la stabilité conditionne donc la robustesse statistique des comparaisons du Chapitre 5.

### Sources de variance dans un RAG

Ces sources de variance n'ont pas pu être testées systématiquement sur ScribBERT dans le cadre de ce travail (cf. limites, Ch. 11). La cartographie ci-dessous reste donc en partie théorique, fondée sur la littérature et sur quelques observations ponctuelles pendant le développement.

Côté génération, la variance vient d'abord de l'échantillonnage stochastique (température, *top-p*) qui agit sur la diversité lexicale et, à température élevée, sur le contenu factuel lui-même. Même à température 0, le non-déterminisme persiste sur les LLM propriétaires : parallélisme GPU et *traitement par lots* variable empêchent un déterminisme strict, et il faut s'appuyer sur des paramètres dédiés (`seed`, identifiant `system_fingerprint` côté OpenAI / Azure OpenAI) pour tracer ce qui est effectivement reproductible. S'y ajoutent les choix de format : un même contenu peut être rendu en puces ou en phrases, ce qui fausse toute comparaison textuelle brute. Les sources de variance côté récupération (approximation ANN, égalités de scores, concurrence sur index distribué) ont déjà été décrites en § 1.4, § 3.2 et § 6.1, et ne sont pas reprises ici.

Côté formulation utilisateur, deux requêtes sémantiquement équivalentes peuvent produire des réponses différentes : paraphrases ("Quels EPI pour travail en hauteur ?" vs "Quels équipements de protection pour les travaux en hauteur ?"), fautes d'orthographe et accents (auxquels les vectorisations sont inégalement sensibles), niveau de spécificité ("EPI travail en hauteur" vs "harnais antichute" qui ciblent la même règle par des chemins différents) ou alternance codique FR/EN ponctuel.

Enfin, à plus long terme, une dérive temporelle s'installe : mise à jour silencieuse des modèles propriétaires (un `gpt-4o-2024-08-06` peut être déprécié et remplacé), évolution du corpus (ajouts, retraits, révisions de procédures), et dérive de l'index dès que la stratégie de *chunking* ou de vectorisation est modifiée.

### Métriques de stabilité

Le cas le plus simple est la stabilité inter-runs : à requête et configuration constantes, le système est exécuté $n$ fois (typiquement $n \in [5, 20]$) et le recouvrement des sorties est mesuré. Côté récupération, un Stability@retrieval est calculé comme indice de Jaccard moyen des ensembles de *chunks* récupérés entre paires de runs. Le Jaccard mesure le recouvrement entre deux ensembles, défini comme le rapport entre la taille de leur intersection et celle de leur union : $\mathrm{J}(A_i, A_j) = |A_i \cap A_j| / |A_i \cup A_j|$. Il vaut 1 si les deux runs retournent exactement les mêmes *chunks*, 0 s'ils sont disjoints. La même mesure peut être restreinte aux *chunks* effectivement cités dans la réponse (et non simplement récupérés), ce qui est souvent plus informatif sur la fidélité perçue. Côté génération, un BERTScore moyen entre paires de réponses donne une stabilité sémantique, complétée par l'écart-type inter-runs des métriques de qualité (*faithfulness*, Recall@k…) et par un taux de basculement : taux de questions pour lesquelles le verdict (réponse acceptable / inacceptable) change entre runs. Dans le cas binaire correct/incorrect, le résumé se fait par la proportion de runs corrects ; les questions dont ce taux se situe entre 30 % et 70 % sont flaguées comme "instables".

Cette stabilité à requête identique ne suffit pas : un système peut être stable inter-runs et fragile aux paraphrases. Pour chaque requête, $m$ reformulations sont donc générées et les mêmes métriques sont appliquées entre la requête originale et ses variantes, en confiant à un *LLM-juge* la vérification que les réponses véhiculent bien la même information factuelle au-delà des différences de surface. Dans le même esprit, la robustesse à l'ordre des passages (sensibilité au *lost in the middle*) peut être testée en permutant l'ordre des *chunks* injectés dans le contexte : un système robuste produit des réponses sémantiquement équivalentes quel que soit l'ordre.

### Sensibilité aux paramètres et aux variations adverses

Au-delà des variations classiques, un bon protocole de stabilité teste aussi des perturbations contrôlées :

- Fautes injectées : inversion de caractères, omissions, accents incorrects.
- Reformulations adversariales : reformulations qui préservent l'intention mais utilisent un vocabulaire différent (jargon chantier, anglicismes).
- Bruit dans le contexte : ajout de *chunks* non pertinents pour mesurer la résistance à la dilution.
- Corpus avec contradictions : injection de variantes contradictoires pour tester la détection.
- Questions pièges : questions hors-périmètre, questions à présupposés faux ("Quelle est la procédure pour ne pas porter de harnais ?").

Ces tests adversariaux ne sont pas des cas usuels mais des sortes de tests de résistance : ils caractérisent les limites de notre système et orientent les garde-fous (même si en principe, ces cas extrêmes ne devraient pas se présenter si notre récupération est bien faite).

### Protocole de test de stabilité

Un protocole opérationnel pour évaluer la stabilité d'un RAG peut s'organiser en cinq temps. La première étape consiste à sélectionner un sous-jeu de questions critiques, classées par niveau de criticité. Des tests inter-runs sont ensuite réalisés : pour chaque question, le système est exécuté $n=10$ fois à seed et configuration constants, afin de calculer Stability@*retrieval*, Stability@citations, Stability@answer ainsi que le taux de basculement. Le protocole est ensuite complété par des tests de paraphrase : chaque question est reformulée en $m=5$ paraphrases, validées par un expert pour garantir la conservation de l'intention, puis exécutées une fois chacune afin de mesurer la consistance sémantique des réponses. À cela s'ajoutent des tests adversariaux, menés sur un sous-ensemble de 10 à 20 questions, en appliquant des perturbations contrôlées telles que des fautes, des reformulations ou des questions pièges. Enfin, l'ensemble des résultats est synthétisé dans un tableau de bord par configuration, agrégeant la qualité moyenne présentée au Chapitre 5 et les indicateurs de stabilité de ce chapitre. Une configuration ne devrait être retenue que si elle dépasse des seuils minimaux sur les deux dimensions.

### Stabilité et confiance utilisateur

La stabilité a aussi une dimension psychologique. Cela a déjà été évoqué plus haut, mais un utilisateur perçoit l'instabilité comme un signe d'incompétence/incertitude du système, même si la réponse moyenne est correcte. Inversement, un système stable mais subtilement biaisé peut générer une fausse confiance. L'utilisateur a confiance dans le système, même s'il est stable dans l'échec.

Deux pratiques permettent de réconcilier ces enjeux :

- Exposer l'incertitude : afficher un score de confiance, ou indiquer explicitement "plusieurs réponses possibles selon le contexte de chantier".
- Stabiliser les éléments critiques sans figer les éléments stylistiques : la liste d'EPI doit être identique, mais la formulation peut varier.

### Synthèse de la Partie II

Les chapitres 4 à 6 ont défini un cadre méthodologique complet :

- Ch. 4 a inventorié les leviers techniques actionnables (vectorisation, *chunking*, récupération, génération) avec leurs compromis ;
- Ch. 5 a structuré le protocole d'évaluation autour des cinq dimensions de la fiabilité, avec des approches automatiques, humaines et hybrides ;
- Ch. 6 a approfondi la dimension stabilité aussi bien perçue que statistique, sous-traitée mais critique pour un déploiement en production.

La Partie III instancie ce cadre sur ScribBERT : architecture déployée (Ch. 7), résultats expérimentaux (Ch. 8-9), enjeux éthiques, réglementaires et industriels (Ch. 10) et discussion (Ch. 11).



---

```{=latex}
\cleardoublepage
\thispagestyle{plain}
\vspace*{\stretch{1}}
\begin{center}
{\Huge\bfseries PARTIE III}\\[1.5em]
{\LARGE Application pratique : étude de cas ScribBERT}
\end{center}
\vspace*{\stretch{2}}
\addcontentsline{toc}{section}{PARTIE III \textemdash{} Application pratique : étude de cas ScribBERT}
\markboth{PARTIE III \textemdash{} Application pratique : étude de cas ScribBERT}{}
\newpage
```

Cette dernière partie applique le cadre méthodologique des Parties I et II au cas de ScribBERT. Conformément au principe anti-redondance énoncé en introduction de la Partie II, ce qui est déjà décrit en Ch. 4 (théorie des leviers) n'est pas répété ici : seuls les choix réalisés et leurs justifications sont documentés.

La structure est la suivante :

- Ch. 7 : architecture déployée et choix techniques.
- Ch. 8 : résultats quantitatifs.
- Ch. 9 : analyse qualitative et étude d'erreurs.
- Ch. 10 : enjeux éthiques, réglementaires et industriels.
- Ch. 11 : discussion et perspectives.

## Mise en œuvre du système RAG ScribBERT

### Contexte et historique du projet

Le projet ScribBERT a été initié en deuxième année d'alternance, après une première année consacrée à l'immersion métier au sein du département P2S et à la cartographie des usages documentaires. Cette première année m'a également permis de me familiariser avec plusieurs outils internes de pilotage, tels que QuickConnect, Power BI, Heures Travaillées et Cority, et de reprendre à partir d'une page blanche le système d'indicateurs existant sous Power BI afin de le fiabiliser, de l'améliorer et de poser les bases de son fonctionnement actuel. Les développements autour de ScribBERT se sont étalés sur environ un an et demi, en deux phases :

1. Phase POC (*Proof of Concept*) : prototype rapide visant à valider la faisabilité technique, l'utilité réelle de la solution et son appropriation par les utilisateurs métier.
2. Phase exploratoire / industrialisation : *benchmark* des composants, construction d'une architecture, préparation à la mise en production (engagement, cadrage,...).

Ce mémoire documente principalement la phase exploratoire, qui constitue le terrain d'application du protocole d'évaluation, et donc de ce mémoire.

### Architecture déployée

#### Vue d'ensemble

ScribBERT suit l'architecture RAG classique décrite au Ch. 2.3, instanciée comme suit :

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

#### *Stack* technique

| Composant | Choix | Justification |
|--------------------|------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Langage serveur | Python 3.11 | Écosystème IA dominant, compatibilité avec la quasi-totalité des bibliothèques de *vectorisation* et LLM |
| Orchestration RAG | LangChain | Maturité, intégrations préexistantes (*loaders*, *splitters*, *retrievers*, chains) ; permet de basculer à chaud entre différents fournisseurs (hébergement local, cloud) |
| Calcul tensoriel | PyTorch (via `sentence-transformers` et `transformers`) | Standard de fait pour l'inférence des modèles de vectorisation et des LLMs *open-source* ; bonne intégration GPU sur le *cluster* |
| Base vectorielle | ChromaDB | Léger, embeddable, gestion native des métadonnées et du filtrage, déploiement local sans dépendance cloud |
| API | FastAPI | Performance asynchrone, intégration simple et directe |
| Interface | ReactJS (codé à la main) | Contrôle total de l'expérience utilisateur, intégration avec la charte graphique interne, pas de dépendance à un *framework* sans-code |
| Hébergement (POC) | *Cluster* Kubernetes local au LabTP (équipe Lab TP Innovation) | Souveraineté des données, pas de transit vers cloud externe, scalabilité interne, facilité d'accès et de mise à jour |

Table: Pile technique du POC ScribBERT.

Ce choix d'une *stack* majoritairement *open-source* et auto-hébergée répond aux contraintes de confidentialité et d'indépendance vis-à-vis de fournisseurs externes pour une éventuelle exploitation à long terme.

#### Chaîne de traitement d'ingestion

La chaîne de traitement d'ingestion transforme un PDF source en *chunks* indexés. Étapes :

1. Extraction : conversion du PDF en Markdown via fitz (PyMuPDF), ce qui permet de conserver au mieux la mise en forme (titres, listes, tableaux), tout en disposant de texte facile à *parser*.
2. Nettoyage : suppression des en-têtes/pieds de page répétitifs, normalisation des caractères spéciaux.
3. *Chunking* : découpage par regex sur les marqueurs structurels (titres Markdown `#`, `##`, séparateurs de paragraphes), avec contrainte de taille cible (~1200 *tokens*) et chevauchement (~50 *tokens*). Détails en § 7.4.
4. Enrichissement métadonnées : ajout pour chaque *chunk* de : `nom_document`, `entité_émettrice`, `langue`, `position_dans_doc`.
5. Vectorisation : calcul vectoriel via le modèle retenu (§ 7.5).
6. Indexation : insertion dans ChromaDB avec la collection appropriée.

L'étape 1 est actuellement la plus fragile : les PDFs santé-sécurité contiennent souvent des tableaux et des schémas. Dans le POC, ces éléments sont ignorés ou linéarisés à la volée comme du texte. Pour la version production, une chaîne image-to-text est en cours d'étude : un modèle multimodal génère une description textuelle de chaque image/tableau, conserve le lien vers l'image originale, et l'injecte comme un *chunk* enrichi. Cette piste sera évaluée séparément dans le Ch. 11 qui traite des perspectives d'évolution.

#### UI et expérience utilisateur

L'interface ReactJS expose :

- une zone de saisie en langage naturel ;
- un filtre optionnel sur les métadonnées (entité émettrice, langue) ;
- la réponse générée avec citations cliquables, le nom du document avec la (ou les) page(s) utilisée(s) pour la réponse, et la possibilité de télécharger le PDF d'origine ;
- un avertissement permanent rappelant que la réponse n'engage pas la responsabilité du système et que l'utilisateur reste tenu de vérifier les sources citées (cf. § 9.3).

### Description du corpus

| Caractéristique | Valeur |
|---------------------|---------------------------------------------------------------------------|
| Périmètre | Documents santé-sécurité du siège de Bouygues TP, et de clients/partenaires |
| Volume | ~200 documents PDF |
| Langues | ≈ 40 % français, 60 % anglais |
| Taille des documents | De quelques pages à 500 pages |
| Types | Procédures, standards, guides méthodologiques |
| Éléments non-textuels | Tableaux et schémas présents (non gérés dans le POC, prévus en production) |

Table: Caractéristiques du corpus documentaire ScribBERT.

Cette taille reste modeste à l'échelle d'un *benchmark* IR (*Information Retrieval*) (BEIR utilise des corpus de 10⁵ à 10⁶ documents), mais elle est représentative d'un cas d'usage d'entreprise : un corpus expert, multilingue, à forte densité informationnelle, où chaque document compte. Le défi n'est pas le passage à l'échelle, mais plutôt la qualité de la récupération et de la génération sur un domaine spécialisé.

À noter : à terme, l'extension envisagée couvre les référentiels santé-sécurité de l'ensemble des filiales et chantiers du groupe Bouygues Construction, ce qui multiplierait le volume par un ordre de grandeur et ferait apparaître des problématiques nouvelles (variantes locales, contradictions inter-entités, multilinguisme étendu).

### Choix de *chunking* et prétraitement

Conformément à la grille du Ch. 4.2, la stratégie retenue est un *chunking* structurel sur mesure, justifié comme suit :

- les documents PDF sont d'abord convertis en Markdown pour préserver la hiérarchie (titres, listes, mise en forme) qui est porteuse de sens dans des référentiels normatifs ;
- des expressions régulières identifient les séparateurs structurels (titres `#`, `##`, `###`, paragraphes) et découpent le texte en unités correspondant à des paragraphes ou sous-sections ;
- la cible de taille est d'environ 1 200 *tokens* par *chunk* (variante `markdown-1200-50` du *benchmark*, retenue en POC), ce qui correspond empiriquement à un compromis entre :
  - assez large pour contenir une règle complète avec ses conditions et ses exceptions (cf. risque d'omission identifié au Ch. 5.5.4),
  - assez petit pour rester discriminant à la vectorisation et économique en *tokens* lors de l'injection dans le contexte LLM ;
  - le *benchmark* systématique (§ 8.2) montre que les *chunkings* 1024 *tokens* dominent en MRR, ce qui valide a posteriori l'ordre de grandeur retenu ;
- le chevauchement est de ~50 *tokens*, soit une valeur faible (≈ 4 %), qui suffit à amortir des coupures malheureuses sans gonfler significativement l'index ;
- une fenêtre contexte est ajoutée à la récupération : pour chaque *chunk* retourné par la récupération, les *chunks* $n-1$ et $n+1$ sont automatiquement adjoints avant injection dans le contexte LLM. Cette mécanique compense un chevauchement faible et restaure le contexte amont/aval, particulièrement utile pour les références anaphoriques ("cette règle", "les EPI mentionnés") et pour la cohérence procédurale.

Les métadonnées attachées à chaque *chunk* sont actuellement : `nom_document`, `entité_émettrice`, `langue`, `date du document`.

### Choix de vectorisation et de LLM

#### Phase POC

Le POC initial a utilisé en grande partie GPT-3.5 Turbo comme LLM, choisi pour :

- la rapidité de mise en œuvre (API mature),
- un compromis coût/qualité acceptable pour valider la faisabilité.

Pour les vectorisations, à la fois des modèles locaux disponibles sur HuggingFace et `text-embedding-ada-002` via l'API Azure OpenAI ont été exécutés. Cette double approche permet de comparer une solution auto-hébergeable, plus compatible avec les contraintes de souveraineté, et une solution propriétaire servant de point de référence en termes de qualité de récupération.

Cette configuration a permis de valider l'intérêt utilisateur et de débloquer la phase exploratoire suivante.

#### Phase exploratoire : *benchmark* systématique

La phase exploratoire a consisté en un *benchmark* récupération portant sur 18 modèles de vectorisation testés, dont 2 modèles (`gte-qwen2-7b` et `nv-embed-v2`) ont dû être écartés intégralement faute d'avoir pu être initialisés dans l'environnement local (incompatibilités avec la version de `transformers` installée). Les 16 modèles retenus, croisés avec 9 stratégies de *chunking* et 6 variantes de récupération, donnent un plan de 16 × 9 × 6 = 864 cellules, exécuté de bout en bout sur les 50 questions du jeu de test interne (§ 8.1.2). Il a été constaté en pratique que mettre à jour la librairie pour débloquer les deux modèles écartés cassait à l'inverse plusieurs autres modèles déjà fonctionnels : un arbitrage propre sur le couple `transformers` / `sentence-transformers` (et plus largement sur l'épinglage des versions de l'écosystème HuggingFace) sera nécessaire à terme, mais la voie la plus rapide a été privilégiée ici, consistant à figer un environnement compatible avec le plus grand nombre de modèles disponibles. Sur les 864 cellules retenues, 750 ont produit des résultats exploitables, les autres correspondant à des échecs partiels résiduels sur quelques variantes (notamment `jina-v2-base-en` et `jina-v3`).

Les 16 modèles retenus couvrent les familles définies au Ch. 4.1.1 :

- propriétaires via API : `ada-002`, `embed-3-large` (OpenAI) ;
- multilingues *open-source* orientés récupération : `e5-small-ml`, `e5-base-ml`, `e5-large-ml`, `bge-m3`, `jina-v3`, `nomic-v2`, `granite-311m-ml`, `qwen3-embed-8b` ;
- généralistes *open-source* : `minilm-l6`, `mpnet-base`, `jina-v2-base-en` ;
- francophones / bilingues spécialisés : `camembert-large`, `solon-large`, `bilingual-fr-en`.

Les six variantes de récupération testées sont : `dense-k5`, `dense-k10`, `dense-k5-thresh` (seuil de similarité), `dense-k5-neigh` (voisinage n−1/n+1), `hybrid-k5` (dense + BM25, fusion RRF) et `dense-k20-rerank5` (*reranking* *cross-encoder* BGE).

Pour chaque configuration, les métriques de récupération du Ch. 5.1.1 ont été collectées (Hit@k, Recall@k, Precision@k, MRR, nDCG@k pour $k\in\{1,3,5,10\}$, plus latence par requête). Une seconde campagne génération a ensuite été lancée sur cinq configurations sélectionnées comme représentatives (trois côté Azure avec évaluation RAGAS complète, deux côté local avec Mistral-7B auto-hébergé) ; les résultats sont consolidés dans [results/benchmark_generation.csv](results/benchmark_generation.csv) et discutés au § 8.3.

Au vu des résultats consolidés, le modèle de vectorisation retenu pour la configuration dense de référence est `ada-002` (Azure OpenAI), au coude à coude avec `embed-3-large`, `nomic-v2` et `qwen3-embed-8b` sur la MRR moyenne (cf. tableau 8.2). Le choix repose sur trois éléments pratiques.

Intégration et infrastructure. `ada-002` est déjà déployé et disponible dans le *tenant* Azure de Bouygues Construction, ce qui supprime à la fois le coût d'hébergement GPU et le délai de mise en place d'une architecture dédiée côté Bouygues.

Couverture linguistique. Le modèle est multilingue et donne des résultats équivalents en français et en anglais sur le corpus testé, ce qui correspond précisément au profil bilingue de ScribBERT.

Latence acceptable pour un usage interactif. La métrique `latency_s` enregistrée correspond au temps mesuré côté Python autour de l'appel de vectorisation seul, c'est-à-dire l'intervalle entre l'envoi de la requête depuis la machine de développement vers l'*endpoint* Azure et la réception du vecteur en retour (aller-retour réseau inclus, hors récupération ChromaDB et hors appel LLM). Les mesures ont été conduites sur une machine Dell Pro Max GB10 (CPU 20 cœurs Arm, GPU Blackwell intégré, 128 Go de LPDDR5X unifiée), connectée en Ethernet filaire sur une liaison fibre 1 Gbit/s symétrique. Sur cette configuration, la latence médiane observée est d'environ 80 ms par requête pour `ada-002`, contre 5-25 ms pour la plupart des modèles *open-source* légers exécutés localement sur GPU (`minilm-l6`, `e5-*`, `mpnet-base`, `bge-m3`, `nomic-v2`, `solon-large`, etc.), environ 260 ms pour `qwen3-embed-8b` et jusqu'à environ 3 300 ms pour `embed-3-large`. Autrement dit, `ada-002` n'est pas le plus rapide en latence brute de vectorisation, mais il évite l'hébergement GPU et reste largement en-dessous des autres modèles propriétaires et des très gros *open-source* ; sa latence est donc négligeable devant celle de la génération LLM (environ 5 000 ms côté Azure, cf. ci-dessous).

Concernant les modèles de génération de texte, les cinq runs disponibles (§ 8.3) confirment que `azure-gpt35` est suffisant pour la phase exploratoire : *faithfulness* RAGAS comprise entre 0,72 et 0,77, *answer relevancy* entre 0,72 et 0,76, pour une latence de génération médiane d'environ 5 s. Les deux runs Mistral-7B local atteignent des temps de génération de l'ordre de 36 à 38 s par question malgré l'accélération GPU et une *faithfulness* en retrait (0,61 à 0,68 selon la combinaison *chunker* et modèle de vectorisation), ce qui les disqualifie en tant que LLM principal du POC, mais les conserve comme piste de repli souverain pour des environnements sans accès Azure (typiquement des chantiers comme des sites militaires ou des installations nucléaires) sur lesquels Bouygues Construction doit parfois opérer en infrastructure totalement isolée d'Internet, ce qui exclut d'entrée de jeu tout appel API externe et impose une chaîne RAG 100 % auto-hébergée. En pratique, la cible pour la mise en production est d'utiliser des modèles quasi état-de-l'art côté OpenAI (typiquement `gpt-4o` ou `gpt-4.1`), Anthropic (`claude-sonnet-4` / `claude-opus-4`) et Mistral (`mistral-large` ou successeurs), selon ce qui sera disponible et les coûts de run associés, avec à la clé un gain attendu sur la *faithfulness* et l'*answer relevancy*, mais un coût par requête à reventiler.

### Configuration de la récupération

| Paramètre | Valeur retenue | Renvoi théorique |
|-------------------------|----------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| Type de récupération | Dense pur | Ch. 4.3.2 (hybridation BM25+dense identifiée comme amélioration) |
| Modèle de vectorisation | text-embedding-ada-002 (déploiement Azure configuré) | Ch. 4.1, § 7.5 |
| Similarité | Cosinus (espace HNSW configuré sur cosine dans ChromaDB) | Ch. 4.3.1 |
| Top-$k$ | 10 | Ch. 4.3.5 |
| Filtre par score | Filtrage par distance avec seuil maximal 0,17. Les *chunks* avec distance >= 0,17 sont écartés | Ch. 5.1.2 (lutte anti-hallucination par ancrage faible) |
| *Reranking* | Inexistant sur le POC, mais présent dans le cahier des charges pour l'industrialisation | Ch. 4.3.3 |
| Filtres métadonnées | Filtrage récupération actif sur `doc_name` (liste d’inclusions) ; les filtres `client`/`langue` sont d'abord traduits en *mapping* de `doc_name` concernés, puis appliqués sur ces `doc_name` directement | Ch. 4.3.4 |
| Contextualisation | Contextualisation par concaténation du *chunk* précédent, courant et suivant (n-1, n, n+1) lors de l’indexation, avec garde-fou sur ruptures de chapitre | § 7.4 |

Table: Configuration de la récupération ScribBERT (POC).

Le choix d'un dense pur s'explique par la simplicité d'implémentation au POC et par une qualité jugée suffisante en évaluation interne (cf. Ch. 4.3.2). L'hybridation sparse+dense (BM25 + vectorisations) reste toutefois une amélioration prioritaire, particulièrement pertinente pour les requêtes contenant des correspondances exactes (numéros de procédure, codes EPI, références normatives), mieux captées par une composante lexicale.

Le filtrage actuellement implémenté repose sur une distance maximale. En pratique, les *chunks* au-delà du seuil sont exclus(cf. Ch. 5.1.2). En revanche, le refus contrôlé strict n'est pas totalement verrouillé dans la version actuelle : quand aucun *chunk* pertinent n'est retenu, un message de contexte indique qu'aucun document n'a été trouvé, mais le modèle peut encore s'appuyer sur l'historique de conversation, ce qui rappelle la nécessité d'un garde-fou plus strict (cf. Ch. 4.4.6).

### Configuration de la génération

*Prompt* : structure conforme aux principes énoncés au Ch. 4.4.2 :

- instruction système rappelant le rôle (assistant santé-sécurité, ancrage strict sur les sources),
- consigne explicite de citation des sources et d'aveu d'ignorance le cas échéant,
- consignes de format (réponse synthétique, structurée, avec liens vers les sources).

Le *prompt* système utilisé dans la chaîne de traitement est construit dynamiquement par concaténation des éléments suivants : le contexte conversationnel précédent (s'il existe), une consigne de cadrage exigeant de ne répondre que si la question relève de la santé-sécurité et uniquement à partir des extraits de documents fournis, les extraits eux-mêmes, une consigne de citation imposée (`« conformément au document [doc_name], page : [page_number] »`, en respectant strictement la casse et l'orthographe d'origine), et enfin la question utilisateur, avec une indication de langue cible et une consigne générale (« apporter des détails utiles, structurer en listes si utile »). En pseudo-code Python :

```python
prompt = (
    f"Contexte de la conversation :\n{context_elements}\n\n"
    f"Si la question concerne la santé et la sécurité, rédige une réponse "
    f"en te basant uniquement sur les extraits de documents suivants :\n"
    f"{context_documents}\n"
    f"Cite les documents que tu utilises ainsi : "
    f'« conformément au document [doc_name], page : [page_number] » '
    f"(sans modifier ni reformuler le nom, respecte la casse, n'ajoute pas d'accents). "
    f"Apporte des détails utiles. Structure avec des listes si utile. "
    f'{language_instruction} à la question : "{query}".'
)
```

Paramètres de décodage :

- Température : 0,05 (réglage effectif de la route de génération principale, cohérent avec la recommandation de stabilité formulée plus haut en Ch. 4.4.4 et au Ch. 6) ;
- Max *tokens* : non fixé explicitement, pas de plafond applicatif dédié dans cette couche ;
- Seed : non fixée à ce stade : la génération est globalement stable grâce à une température basse, mais la reproductibilité stricte d’un run à l’autre n’est pas garantie.

Citations : la mécanique implémentée dans le POC n'est pas un format strict [n] avec bibliographie finale. Le serveur pousse plutôt une citation textuelle du document + page utilisée, puis enrichit la réponse avec le blobid (permettant de construire le lien de visualisation/téléchargement). L'interface transforme ces blobid en boutons cliquables ouvrant la source (et la page quand disponible).

### Synthèse des choix et limites assumées du POC

Le POC ScribBERT, dans sa version actuelle, présente au moins ces limites structurantes pour un passage en production :

1. Pas d'hybridation sparse+dense : ce qui limite la robustesse sur les requêtes contenant des correspondances exactes.
2. Pas de *reranking* : la précision du top-$k$ pourrait être améliorée via un *cross-encoder*.
3. Gestion partielle des refus contrôlés : le filtrage vectoriel existe, mais le refus n’est pas hard codé ; il repose surtout sur une instruction donnée au LLM de ne pas répondre lorsqu’aucun extrait pertinent n’est disponible, sans garantie de refus strict systématique.
4. Pas de gestion des tableaux et schémas : pertes informationnelles sur des contenus à forte valeur santé-sécurité (matrices de risques, logigrammes).

Ces axes constituent des priorités cohérentes pour la trajectoire de production et seront discutés en perspective au Ch. 11.

```{=latex}
\newpage
```

## Résultats quantitatifs

### Protocole expérimental instancié

#### Configurations testées

Les configurations comparées dans la phase exploratoire correspondent à un plan factoriel 16 modèles de vectorisation × 9 stratégies de *chunking* × 6 variantes de récupération = 864 combinaisons, exécuté de bout en bout (§ 7.5.2). Les axes du plan sont :

- Axe 1 - modèle de vectorisation : 16 modèles couvrant les familles propriétaire, multilingue *open-source*, généraliste *open-source* et francophone spécialisée (liste détaillée au § 7.5.2).
- Axe 2 - Stratégie de *chunking* : 9 stratégies : `fixed-256-0`, `fixed-512-64`, `fixed-1024-128`, `recursive-512-64`, `recursive-1024-128`, `regex-paragraph`, `markdown-1200-50`, `markdown-reference-1000-100`, `semantic-mpnet`.
- Axe 3 - Variante de récupération : 6 combinaisons :
    - `dense-k5` : top-$k$ = 5, sans seuil ;
    - `dense-k10` : top-$k$ = 10, sans seuil ;
    - `dense-k5-thresh` : top-$k$ = 5, seuil de distance cosinus maximal 0,17 ;
    - `dense-k5-neigh` : top-$k$ = 5, contextualisation par voisins $n{-}1$/$n{+}1$ à la récupération ;
    - `hybrid-k5` : fusion dense + BM25 via *Reciprocal Rank Fusion*, top-$k$ = 5 ;
    - `dense-k20-rerank5` : récupération top-20 puis *reranking* *cross-encoder* (BGE-reranker-v2-m3), retour top-5.

Le LLM, le *prompt* et la température sont gelés à leur valeur de référence (§ 7.5-7.7) pour isoler l'effet des leviers testés. Sur les 864 cellules du plan, 750 sont exploitables (cf. § 7.5.2).

#### Jeu de test

Le jeu de test utilisé est constitué de 50 questions annotées manuellement à partir d'une connaissance directe du corpus et des cas d'usage observés ([data/test_set.json](data/test_set.json)). La répartition est la suivante :

- types : factuelle ×12, procédurale ×12, conditionnelle ×10, comparative ×6, justificative ×6, hors-périmètre ×4 ;
- difficulté : facile ×6, moyen ×28, difficile ×16 ;
- langue : français ×41, anglais ×9 ;
- criticité métier : élevée ×42, moyenne ×5, faible ×3.

Pour chaque question sont annotés : une réponse de référence rédigée à partir des référentiels, la liste des documents de référence (`relevant_doc_ids`), des paraphrases validées (utilisées pour le protocole de stabilité du Ch. 6) et des notes contextuelles. Cette taille (50) reste inférieure aux 150-300 questions recommandées au Ch. 5.3.4 : les écarts inter-configurations doivent être lus comme des tendances, et non comme des comparaisons statistiquement décisives. Le passage à 150 questions stratifiées est identifié comme priorité au Ch. 11.2.1.

#### Conditions d'exécution

- Index vectoriel reconstruit pour chaque modèle de vectorisation testé (réutilisation impossible).
- Journaux complets conservés pour chaque exécution conformément au schéma du Ch. 5.4.3.

### Résultats récupération

Sur les 750 configurations exploitables, la MRR moyenne est de 0,571 (écart-type 0,080, min 0,324, max 0,724) et le Hit@5 moyen de 0,725 par configuration (la valeur par configuration s'étend de 0,38 à 0,87 ; il ne s'agit pas d'une étendue par question). Le nDCG@5 moyen, calculé après projection au niveau document, ressort à 0,628 (écart-type 0,072). Ce niveau de performance est cohérent avec celui d'une récupération bien calibrée sur un corpus spécialisé de quelques centaines de documents : la majorité des configurations remontent le bon document dans le top-5, mais aucune ne le place systématiquement en première position. La figure 8.4 visualise cette dispersion sur l'ensemble du plan factoriel.

![Fig. 8.4. Distribution du MRR sur les 750 configurations exploitables du *benchmark* récupération (histogramme et densité). Trait rouge : médiane (0,58) ; bande rouge clair : intervalle interquartile [0,51 ; 0,63]. Les configurations extrémales (meilleure et pire) sont annotées avec leur triplet *chunking* / vectorisation / récupération. Source : résultats du *benchmark* récupération (750 cellules exploitables sur les 864 du plan factoriel).](figures/fig_8_4_distribution_mrr.png){#fig:dist-mrr width=90%}

Effet du modèle de vectorisation (MRR moyenne sur l'ensemble des combinaisons *chunking* × récupération) :

| *Vectorisation* | MRR | Hit@5 | Famille |
|-----------------|-----|-------|---------------------------------|
| `nomic-v2` | 0,639 | 0,808 | multilingue OSS |
| `qwen3-embed-8b` | 0,633 | 0,785 | multilingue OSS (gros) |
| `solon-large` | 0,619 | 0,769 | francophone |
| `e5-base-ml` | 0,617 | 0,781 | multilingue OSS |
| `jina-v3` | 0,615 | 0,747 | multilingue OSS |
| `ada-002` | 0,615 | 0,777 | OpenAI (via Azure OpenAI Service) |
| `embed-3-large` | 0,615 | 0,777 | OpenAI (via Azure OpenAI Service) |
| `bilingual-fr-en` | 0,606 | 0,752 | francophone bilingue |
| `e5-large-ml` | 0,600 | 0,754 | multilingue OSS |
| `granite-311m-ml` | 0,563 | 0,720 | multilingue OSS |
| `e5-small-ml` | 0,526 | 0,685 | multilingue OSS (compact) |
| `camembert-large` | 0,510 | 0,669 | francophone |
| `bge-m3` | 0,503 | 0,655 | multilingue OSS |
| `mpnet-base` | 0,484 | 0,620 | généraliste anglais |
| `minilm-l6` | 0,476 | 0,630 | généraliste compact |
| `jina-v2-base-en` | 0,468 | 0,642 | généraliste anglais |

Table: Performance moyenne des 16 modèles de vectorisation sur le *benchmark* récupération (MRR moyen, Hit@5, sur 750 cellules exploitables).

Trois observations méritent d'être soulignées. D'abord, les huit meilleurs modèles s'inscrivent dans une bande de plus ou moins 0,03 de MRR, dans laquelle figurent à la fois des propriétaires (`ada-002`, `embed-3-large`), des multilingues *open-source* récents (`nomic-v2`, `qwen3-embed-8b`, `e5-base-ml`, `jina-v3`) et un francophone (`solon-large`). Sur ce corpus, aucun modèle n'écrase les autres, ce qui justifie un arbitrage par les critères pratiques (latence, coût, souveraineté) et non par la seule MRR. Ensuite, les modèles "généralistes anglais" décrochent nettement : `minilm-l6`, `mpnet-base` et `jina-v2-base-en` perdent environ 0,15 de MRR par rapport au peloton de tête, ce qui confirme la nécessité d'un encodeur multilingue sur ce corpus mixte FR/EN (Ch. 4.1.3). Enfin, `embed-3-large` n'apporte rien de mesurable par rapport à `ada-002` : les deux modèles donnent des scores rigoureusement identiques sur la plupart des métriques (différence < 0,001 sur l'ensemble du *benchmark*), pour un coût et une latence supérieurs côté `embed-3-large` (~3 300 ms vs ~80 ms par appel de vectorisation, cf. § 8.6) : l'extra-dimension de `embed-3-large` n'améliore pas la séparation des passages dans ce corpus.

Effet de la stratégie de *chunking* (MRR moyenne sur l'ensemble des combinaisons vectorisation × récupération) :

| *Chunking* | MRR | Lecture |
|-----------------------------|-----|------------------------------------------------------------|
| `recursive-1024-128` | 0,603 | *chunks* larges respectant la structure = meilleurs résultats |
| `fixed-1024-128` | 0,597 | *chunks* larges "naïfs" |
| `recursive-512-64` | 0,586 | bon compromis taille/structure |
| `regex-paragraph` | 0,583 | granularité paragraphe |
| `fixed-512-64` | 0,576 | |
| `fixed-256-0` | 0,558 | *chunks* courts sans chevauchement |
| `markdown-1200-50` | 0,543 | *chunks* markdown larges, chevauchement faible |
| `markdown-reference-1000-100` | 0,541 | |
| `semantic-mpnet` | 0,539 | *chunking* sémantique |

Table: Performance moyenne par stratégie de *chunking* (MRR sur 750 cellules exploitables).

La hiérarchie confirme une intuition formulée au Ch. 4.2.2 : sur un corpus normatif, les *chunks* larges (1024 *tokens*) battent les *chunks* courts, parce qu'ils préservent les blocs "condition + règle + exception" qui constituent l'unité de sens utile. Le *chunking* sémantique, plus coûteux à l'ingestion, n'apporte pas de gain mesurable ici. La figure 8.1 croise les deux axes (modèle × *chunking*) et fait apparaître plusieurs « îlots » de performance, en particulier le quadrant supérieur gauche qui associe les modèles à plus forte capacité représentationnelle (`nomic-v2`, `ada-002`, `embed-3-large`, `qwen3-embed-8b`) aux *chunkings* récursifs et fixes de 1024 *tokens*.

![Fig. 8.1. MRR moyen par modèle de *vectorisation* (lignes) et stratégie de *chunking* (colonnes). Chaque cellule agrège la moyenne sur les six variantes de récupération testées (n ≤ 6 par cellule). Modèles et *chunkings* sont ordonnés par MRR global décroissant ; échelle de couleur 0,30 – 0,75. Source : résultats du *benchmark* récupération (750 cellules exploitables sur 864).](figures/fig_8_1_heatmap_mrr_modele_chunking.png){#fig:heatmap-mrr width=100%}

Effet du mode de récupération (MRR moyenne sur l'ensemble des combinaisons vectorisation × *chunking*) :

| Récupération | MRR | Lecture |
|-------------------|-----|----------------------------------------|
| `dense-k20-rerank5` | 0,612 | *reranking* : meilleur compromis qualité |
| `hybrid-k5` | 0,596 | hybride dense + BM25 |
| `dense-k10` | 0,576 | top-$k$ large sans *reranking* |
| `dense-k5` | 0,565 | référence dense "nue" |
| `dense-k5-thresh` | 0,564 | équivalent à dense-k5 avec garde-fou |
| `dense-k5-neigh` | 0,510 | dégrade la MRR malgré le voisinage |

Table: Performance moyenne par variante de récupération (MRR sur 750 cellules exploitables).

\needspace{14\baselineskip}

Trois choses à noter :

- Le *reranking* *cross-encoder* (`dense-k20-rerank5`) apporte un gain de +0,047 de MRR par rapport à `dense-k5` (environ +8 % relatif), au prix d'une latence supplémentaire (mesurée séparément en § 8.6). C'est la confirmation expérimentale, sur notre corpus, de la valeur du *reranking* évoquée au Ch. 4.3.3, et un argument fort pour son intégration en production.
- L'hybride dense + BM25 confirme également sa valeur (+0,031 par rapport à `dense-k5`), particulièrement utile pour les requêtes citant explicitement un identifiant de procédure (Ch. 4.3.2). Le meilleur top-3 absolu du *benchmark* associe d'ailleurs `qwen3-embed-8b` à `hybrid-k5` sur des *chunks* 512-1024 *tokens*.
- À l'inverse, la variante `dense-k5-neigh` (ajout systématique des voisins $n{-}1$/$n{+}1$) dégrade la MRR. L'explication est cohérente avec la discussion du Ch. 4.2.2 : sur des *chunks* déjà larges (≥ 512 *tokens*), l'ajout des voisins "dilue" la pertinence du top-5 sans apporter d'information utile, et bruite l'évaluation du "premier passage pertinent". Cette variante reste cependant pertinente quand l'objectif est la génération plutôt que la récupération pure (§ 8.3), où le voisinage restaure des références anaphoriques.

La figure 8.2 visualise la distribution complète par variante : `dense-k20-rerank5` et `hybrid-k5` dominent en médiane comme en moyenne, tandis que `dense-k5-neigh` ressort comme la seule variante systématiquement en retrait sur l'ensemble du plan factoriel.

![Fig. 8.2. Distribution du MRR par variante de récupération, sur les 750 configurations exploitables. Chaque point représente une combinaison *chunking* × *vectorisation* (jitter horizontal pour visibilité) ; les boîtes représentent les quartiles, le losange rouge la moyenne. Variantes ordonnées selon la liste théorique du Ch. 4.3. Source : résultats du *benchmark* récupération.](figures/fig_8_2_barplot_mrr_par_variante_recuperation.png){#fig:bar-mrr-retrieval width=90%}

\needspace{12\baselineskip}

Top 5 des configurations en MRR absolue (sur les 750 configurations testées) :

| *Chunking* | *Vectorisation* | Récupération | MRR | Hit@5 | Recall@5 | nDCG@5 |
|--------------------|-------------------------|-----------------|-----|-------|----------|--------|
| `fixed-1024-128` | `ada-002` / `embed-3-large` | `dense-k10` | 0,724 | 0,787 | 0,741 | 0,768 |
| `fixed-512-64` | `qwen3-embed-8b` | `hybrid-k5` | 0,718 | 0,809 | 0,756 | 0,769 |
| `fixed-1024-128` | `ada-002` / `embed-3-large` | `dense-k5-thresh` | 0,713 | 0,787 | 0,738 | 0,758 |
| `recursive-1024-128` | `nomic-v2` | `dense-k10` | 0,709 | 0,830 | 0,771 | 0,766 |
| `recursive-512-64` | `qwen3-embed-8b` | `hybrid-k5` | 0,706 | 0,787 | 0,732 | 0,753 |

Table: Top-5 des configurations récupération combinées (*chunking* × *vectorisation* × récupération). Les lignes notant `ada-002 / embed-3-large` correspondent à deux runs distincts dont les métriques coïncident à moins de 0,001 sur l'ensemble des indicateurs reportés : sur ce corpus, l'augmentation de dimension de `embed-3-large` n'apporte aucun gain mesurable par rapport à `ada-002`.

Les meilleures configurations "propriétaires light" (`ada-002` + *chunks* 1024) et "*open-source* plus + hybride" (`qwen3-embed-8b` + `hybrid-k5`) sont à moins de 1 % d'écart en MRR. C'est cette quasi-équivalence, et la simplicité d'exploitation qui motive le choix opérationnel décrit au § 7.5.2.

#### Interactions entre *chunking* et modèle de vectorisation

Les moyennes marginales présentées ci-dessus dissimulent un effet d'interaction qu'il est utile de rendre explicite : le *chunking* optimal n'est pas le même pour tous les modèles. Le tableau ci-dessous reporte, pour chaque modèle de vectorisation, le *chunking* qui maximise la MRR moyenne (toutes variantes de récupération confondues).

| *Vectorisation* | Meilleur *chunking* | MRR | 2ᵉ meilleur *chunking* | MRR |
|-------------------------|--------------------|-----|--------------------|-----|
| `ada-002` / `embed-3-large` | `fixed-1024-128` | 0,680 | `recursive-1024-128` | 0,658 |
| `nomic-v2` | `recursive-1024-128` | 0,687 | `fixed-256-0` | 0,649 |
| `qwen3-embed-8b` | `fixed-512-64` | 0,677 | `fixed-1024-128` | 0,658 |
| `solon-large` | `regex-paragraph` | 0,670 | `recursive-1024-128` | 0,651 |
| `e5-base-ml` | `fixed-1024-128` | 0,653 | `recursive-1024-128` | 0,637 |
| `e5-large-ml` | `fixed-256-0` | 0,651 | `fixed-1024-128` | 0,639 |
| `jina-v3` | `recursive-1024-128` | 0,643 | `recursive-512-64` | 0,627 |
| `bilingual-fr-en` | `fixed-1024-128` | 0,630 | `recursive-1024-128` | 0,623 |
| `granite-311m-ml` | `regex-paragraph` | 0,617 | `fixed-512-64` | 0,600 |
| `e5-small-ml` | `recursive-1024-128` | 0,589 | `fixed-256-0` | 0,542 |
| `bge-m3` | `regex-paragraph` | 0,556 | `recursive-1024-128` | 0,536 |
| `camembert-large` | `regex-paragraph` | 0,543 | `recursive-1024-128` | 0,537 |
| `minilm-l6` | `recursive-512-64` | 0,535 | `fixed-256-0` | 0,499 |
| `mpnet-base` | `regex-paragraph` | 0,517 | `recursive-512-64` | 0,507 |
| `jina-v2-base-en` | `fixed-256-0` | 0,468 | n/a | n/a |

Table: Meilleur *chunking* par modèle de vectorisation (MRR moyenne, toutes variantes de récupération confondues, 750 cellules exploitables).

Trois régularités se dégagent. Premièrement, les modèles à forte capacité représentationnelle et fenêtre de contexte généreuse (≥ 512 *tokens* (`ada-002`, `embed-3-large`, `nomic-v2`, `qwen3-embed-8b`, `e5-base-ml`, `jina-v3`, `bilingual-fr-en`)) privilégient des *chunks* larges (1024 *tokens*, parfois 512). Le pattern décrit en moyenne au § 8.2 ("les *chunks* larges battent les *chunks* courts") tient donc principalement grâce à cette famille. Deuxièmement, les modèles francophones ou multilingues plus spécialisés (`solon-large`, `granite-311m-ml`, `camembert-large`) ainsi que `bge-m3` et `mpnet-base` préfèrent le découpage `regex-paragraph`, qui produit des unités plus courtes et structurées : leurs représentations semblent mieux discriminer entre des paragraphes auto-suffisants qu'entre des sections longues mêlant plusieurs idées. Troisièmement, les modèles compacts à fenêtre courte (`minilm-l6`, max_seq_length = 256 *tokens* ; `e5-small-ml`) sont pénalisés par les *chunks* longs qui sont tronqués à l'indexation : leur optimum se déplace mécaniquement vers les configurations 256-512 *tokens*.

Conséquence opérationnelle : recommander un *chunking* "universel" est trompeur. Le choix doit être fait conjointement avec celui du modèle de vectorisation, et c'est précisément pour cette raison que le plan factoriel complet a été conservé en phase exploratoire plutôt que de figer une stratégie de *chunking* a priori. Pour ScribBERT, le couple `recursive-512-64` + `ada-002` retenu en configuration de référence se situe à moins de 0,01 de MRR de l'optimum local de `ada-002` (0,680 sur `fixed-1024-128`), ce qui justifie de privilégier la *configuration récupération* la plus performante (`hybrid-k5`) plutôt que de pousser sur la taille de *chunk* (cf. § 8.3 sur l'effet de `hybrid-k5` en génération).

### Résultats génération

La campagne génération a porté sur cinq configurations choisies comme représentatives, croisant trois *chaînes de traitement* Azure et deux *chaînes de traitement* local-Mistral-7B, toutes évaluées par RAGAS. Chaque chaîne de traitement a généré une réponse aux 50 questions du jeu de test. Synthèse :

| Configuration | LLM | Faith. | Ans. rel. | Ctx. prec. | Ctx. recall | $t_\text{ret}$ médian | $t_\text{gen}$ médian |
|--------------------------------------------------|----------------|--------|-----------|------------|-------------|--------------|--------------|
| `recursive-512-64` / `ada-002` / `hybrid-k5` | gpt-3.5-turbo | 0,765 | 0,756 | 0,687 | 0,629 | 0,08 s | 5,09 s |
| `markdown-1200-50` / `ada-002` / `dense-k5-neigh` | gpt-3.5-turbo | 0,748 | 0,738 | 0,418 | 0,592 | 0,13 s | 5,58 s |
| `recursive-512-64` / `e5-base-ml` / `dense-k5-neigh` | Mistral-7B local | 0,681 | 0,652 | 0,418 | 0,512 | 0,05 s | 35,67 s |
| `fixed-256-0` / `minilm-l6` / `dense-k5-neigh` | Mistral-7B local | 0,612 | 0,589 | 0,361 | 0,428 | 0,06 s | 37,99 s |
| *`markdown-1200-50` / `ada-002` / `dense-k5-thresh`* † | *gpt-3.5-turbo* | *0,724* | *0,718* | *0,675* | *0,502* | *12,89 s* | *55,84 s* |

Table: Résultats RAGAS sur les cinq configurations de génération évaluées (50 questions chacune). La dernière ligne, en italique et marquée d'un †, voit ses temps de latence dégradés par la saturation des quotas Azure OpenAI lors de l'exécution en rafale du *benchmark* (erreurs *too many requests*, cf. § 8.6) ; les scores RAGAS de cette ligne restent en revanche valides puisqu'ils ne dépendent pas de la latence. Une réexécution hors saturation est listée parmi les actions de la trajectoire production (Ch. 11.2, Limites du protocole appliqué).

La figure 8.5 visualise ces cinq configurations sous forme de radar à quatre axes, ce qui permet de comparer d'un coup d'œil les profils complets plutôt que les seules valeurs colonne par colonne.

![Fig. 8.5. Profil RAGAS des cinq configurations de génération évaluées, sur les quatre dimensions *Faithfulness*, *Answer Relevancy*, *Context Precision* et *Context Recall* (échelle 0 – 1). Chaque polygone correspond à une configuration libellée par `embedding · retrieval / LLM`. Source : résultats du benchmark generation (50 questions par configuration).](figures/fig_8_5_radar_ragas_5_configs.png){#fig:radar-ragas width=75%}

Quatre lectures se dégagent. D'abord, la configuration `hybrid-k5` domine sur les quatre scores RAGAS : elle obtient simultanément la meilleure *faithfulness* (0,765), la meilleure *answer relevancy* (0,756), la meilleure *context precision* (0,687) et le meilleur *context recall* (0,629), tout en étant la plus rapide côté génération (5,09 s médian). C'est la confirmation, côté génération cette fois, du gain d'hybridation déjà observé côté récupération (§ 8.2) : une récupération plus précise se traduit par une génération à la fois plus fidèle aux sources et mieux ciblée sur la question.

Deuxième lecture, plus contre-intuitive : la variante `dense-k5-neigh` améliore la fidélité par rapport à `dense-k5-thresh` (+0,024 de *faithfulness*, +0,020 d'*answer relevancy*) malgré sa dégradation observée en récupération pure (*benchmarks* précédents, § 8.2). Le voisinage $n{-}1$/$n{+}1$, qui ajoute du contexte amont/aval, dégrade la "propreté" du top-5 (donc la MRR) mais aide effectivement le LLM à reconstituer les références anaphoriques et les conditions associées à une règle, exactement le compromis annoncé au § 7.4. C'est une illustration concrète du découplage récupération pure ≠ utilité pour la génération discuté au Ch. 5.5.

Troisième point, côté LLM : `gpt-3.5-turbo` plafonne à ≈ 0,75 de *faithfulness* sur ce corpus. Aucune des trois configurations Azure ne dépasse 0,77, et la dispersion entre configurations RAGAS reste limitée (environ 5 points). Atteindre 0,90 (cible usuelle des *frameworks* RAG) nécessiterait probablement un modèle de génération plus récent (`gpt-4o`, Claude, Mistral Large), un *prompt* plus strict sur la citation, ou un *reranking* systématique avant injection.

Enfin, côté alternative locale : Mistral-7B local n'est pas viable en production interactive et reste nettement en retrait sur les scores RAGAS. Avec 36-38 s par question sur GPU, le LLM Mistral-7B est environ 7 fois plus lent que `gpt-3.5-turbo` en appel Azure ; la latence de récupération restant négligeable dans les deux cas (50-130 ms), la chaîne de traitement *end-to-end* subit le même rapport (environ 36 s contre environ 5 s, cf. § 8.6). Sa *faithfulness* plafonne par ailleurs à 0,68 dans la meilleure des deux configurations locales (`recursive-512-64` + `e5-base-ml`), contre 0,76 pour la meilleure chaîne Azure, soit environ 8 points d'écart. Cet écart se creuse encore sur les questions où l'information attendue n'est pas réellement présente dans le corpus : sur Q017 (« Dans quels cas un plan de prévention sous-traitant est-il obligatoire ? »), une vérification manuelle confirme que le seuil réglementaire (400 h/an) ne figure pas dans le doc cité par le test set ; Azure produit alors le refus attendu (« Cette information ne figure pas dans les référentiels consultés ») alors que les deux *chaînes de traitement* locales fabriquent une réponse plausible mais non sourcée. L'observation se retrouve également sur le comportement de citation : `gpt-3.5-turbo` cite systématiquement ses sources en tête de réponse (format `[1][2]` groupé), Mistral-7B + `e5-base-ml` cite relativement correctement (`[1, page 2]`), mais Mistral-7B + `minilm-l6` omet les citations sur une part non négligeable des réponses ou les place de façon incohérente, ce qui explique en partie sa *context precision* plus faible (0,361). L'écart entre les deux runs locaux (0,681 vs 0,612 de *faithfulness*) confirme par ailleurs que le choix du *chunker* et du modèle de vectorisation pèse davantage que le LLM sur le score final : `fixed-256-0` + `minilm-l6` cumule *chunks* trop courts et vectorisations trop légères, là où `recursive-512-64` + `e5-base-ml` s'approche un peu plus des standards Azure sans pour autant les rejoindre. Cette voie reste pertinente comme option "souveraineté forte" pour des déploiements sans connectivité Azure. Pour devenir exploitable, elle demanderait de réduire significativement la latence de génération, d'adopter un modèle de vectorisation multilingue plus capacitaire et de renforcer la consigne de citation dans le *prompt* système.

L'évaluation des dimensions non automatisables (préservation des modalités santé-sécurité, sûreté opérationnelle, complétude experte, Ch. 5.1.2 et 5.2.2) a été menée manuellement sur un sous-échantillon stratifié de 15 questions critiques (issues majoritairement des catégories conditionnelle et procédurale, criticité élevée), conformément au protocole hybride du Ch. 5.2.3. Sur la configuration de référence (`recursive-512-64` + `ada-002` + `hybrid-k5` + `gpt-3.5-turbo`), 13 réponses sur 15 préservent correctement les « doit », « peut », « ne doit pas ». Les deux cas problématiques concernent la transformation d'une obligation en recommandation sur des questions où le *chunk* de référence n'apparaissait pas en tête du top-5. Côté sûreté opérationnelle, aucune réponse n'a produit d'instruction dangereuse ou contraire aux référentiels, y compris sur les questions adversariales (cf. § 9.4.3). En revanche, la complétude experte est plus inégale : sur 6 questions conditionnelles incluses dans le sous-échantillon, 2 omettent au moins une exception ou un cas particulier pourtant présent dans le document source, ce qui rejoint la catégorie « omission d'exception » identifiée en § 9.2. Cette évaluation reste à étendre à un échantillon plus large (objectif 50 questions, idéalement avec deux annotateurs pour mesurer l'accord inter-juges) avant d'être consolidée en métrique de référence.

### Résultats stabilité

Le protocole du Ch. 6.5 a été appliqué à la configuration `markdown-1200-50` + `ada-002` + `dense-k5-thresh` + `azure-gpt35`, choisie comme représentative du POC actuellement déployé. Pour chacune des 50 questions, $n=10$ exécutions ont été lancées à seed et paramètres constants (sources de variance : non-déterminisme du LLM, ordre des passages à score égal à la sortie de ChromaDB) ; en parallèle, les paraphrases annotées dans le jeu de test ont été soumises pour mesurer la consistance sémantique de la réponse. Résultats (n=50 questions) :

| Indicateur | Moyenne | Écart-type | Min | Max | Lecture |
|--------------------------------------------------------------|---------|------------|-----|-----|--------------------------------------------------------|
| Stability@retrieval (Jaccard inter-runs sur top-5) | 1,000 | 0,000 | 1,000 | 1,000 | récupération parfaitement déterministe |
| Stability@citations (Jaccard sur les sources citées en sortie) | 0,935 | 0,110 | 0,550 | 1,000 | quelques variations sur le choix de la source citée |
| Stability@answer (BERTScore F1 inter-runs sur la réponse) | 0,937 | 0,024 | 0,830 | 1,000 | réponses sémantiquement très proches d'un run à l'autre |
| Robustesse aux paraphrases (BERTScore F1 réponse-vs-paraphrase) | 0,766 | 0,094 | 0,634 | 1,000 | beaucoup plus variable que la stabilité inter-runs |

Table: Indicateurs de stabilité de la configuration de référence ScribBERT (50 questions, 10 *runs* par question).

La figure 8.7 distribue ces quatre indicateurs question par question et fait ressortir l'écart structurel entre une stabilité quasi-parfaite à requête fixe et une robustesse plus modeste face aux paraphrases. Le tracé apparié des stabilités inter-runs et inter-paraphrases (figure 8.8) confirme par ailleurs que cet écart n'est pas concentré sur quelques cas extrêmes, mais se traduit par un nuage de points majoritairement situé sous la diagonale x = y.

![Fig. 8.7. Distribution des quatre indicateurs de stabilité sur les 50 questions du jeu de test (configuration de référence `markdown-1200-50 / ada-002 / dense-k5-thresh / azure-gpt35`). De gauche à droite : *Stability@retrieval* (Jaccard inter-runs sur le top-5 récupéré), *Stability@citations* (Jaccard sur les sources effectivement citées dans la réponse), *Stability@answer* (BERTScore F1 moyen entre paires de runs) et *Robustness@paraphrases* (BERTScore F1 entre la réponse originale et celle obtenue sur une paraphrase). Mesures à seed et paramètres constants, $n = 10$ runs par question. Médiane annotée au-dessus de chaque boîte. Source : résultats de la campagne de stabilité.](figures/fig_8_7_boxplot_stabilite.png){#fig:box-stability width=90%}

![Fig. 8.8. Stabilité inter-runs (axe X, `ans_bertscore_f1_mean`) vs robustesse aux paraphrases (axe Y, `paraphrase_bertscore_f1`), une question par point. La diagonale x = y matérialise le cas idéal où une reformulation a le même effet qu'une nouvelle exécution stochastique ; tout point sous la diagonale correspond à une question plus sensible aux paraphrases qu'à la variance intra-run. Les six questions présentant le plus grand écart sont étiquetées par leur identifiant. Source : résultats de la campagne de stabilité (mêmes données qu'en Fig. 8.7).](figures/fig_8_8_scatter_interruns_vs_paraphrases.png){#fig:scatter-stability width=85%}

\needspace{30\baselineskip}

Quatre constats. Premier point, la récupération est parfaitement reproductible (Jaccard 1,000 sur les 50 questions, 0 écart-type) : la couche vectorielle ChromaDB ne contribue à aucune variabilité observable dans cette configuration. Toute variation de réponse provient donc de la couche génération. Deuxièmement, la génération est presque déterministe à requête fixe (BERTScore F1 inter-runs ≈ 0,94, écart-type 0,024), résultat cohérent avec la température 0,05 imposée au § 7.7. Le taux de basculement sur le choix des sources citées reste limité mais non nul (Stability@citations = 0,935, soit 6,5 % de variation moyenne) : la cible "0,95+" recommandée pour un déploiement critique au Ch. 6.3 est presque atteinte, mais pas encore validée. Troisième constat, plus préoccupant : la robustesse aux paraphrases est nettement plus faible (0,77 vs 0,94, soit 17 points d'écart). Reformuler la même question en français courant fait varier sensiblement la réponse produite, ce qui ne veut pas dire que la réponse est fausse, mais qu'elle n'est pas invariante. Pour un assistant santé-sécurité où l'utilisateur peut formuler la même intention de plusieurs façons, c'est l'indicateur prioritaire à améliorer, par exemple via une étape de normalisation de requête en amont de la récupération (Ch. 4.3.6). Enfin, ces tests ne couvrent qu'une configuration sur les 750 testées en récupération. Une mesure de stabilité comparative entre les meilleures configurations (notamment `hybrid-k5` et `dense-k20-rerank5`) reste à réaliser pour vérifier que les gains de fidélité observés au § 8.3 ne se font pas au prix d'une variance inter-runs accrue.

### Résultats *end-to-end* et couplage entre récupération et génération

En croisant les résultats des § 8.2 et § 8.3, plusieurs enseignements ressortent sur le couplage récupération-génération.

Premièrement, la manière dont sont ordonnés les résultats de la récupération n'est pas préservée à la génération. Sur les trois configurations Azure évaluées, la meilleure côté récupération n'est pas la meilleure côté *faithfulness* : `hybrid-k5` (MRR 0,596) domine les quatre scores RAGAS là où `dense-k5-thresh` (MRR 0,564) plafonne. L'écart d'environ 5 % de MRR se traduit par environ 4 % de *faithfulness* (Ch 5.5) : un meilleur rappel améliore la fidélité, mais l'effet est amorti par la couche LLM, qui sauve parfois un top-5 imparfait et manque parfois un top-5 correct.

Deuxièmement, la *context precision* RAGAS est un meilleur signal de fidélité que le Recall@k. La configuration `dense-k5-neigh` obtient un *context recall* correct (0,592) mais une *context precision* faible (0,418), précisément parce qu'elle injecte deux fois plus de *tokens* par *chunk* via le voisinage : le modèle dispose de la bonne information mais aussi de plus de bruit, ce qui dégrade légèrement les autres scores RAGAS. C'est l'illustration directe du compromis "plus de contexte = plus de bruit" et de l'effet *lost in the middle* discutés au Ch. 4.

Enfin, la configuration `dense-k5-thresh` (seuil de distance maximal fixé à 0,17) joue effectivement son rôle de garde-fou : 9 questions sur 50 (hors les 4 hors-périmètre, qui reçoivent par défaut le refus attendu) reçoivent une réponse de type « information non trouvée dans les référentiels », contre 5 sur la configuration `hybrid-k5` de référence : le filtre joue donc effectivement son rôle, mais avec une sévérité supérieure qui coûte quelques refus légitimes en plus (Q005, Q009, Q013, Q026, Q043 et Q044 sont refusées alors que le contexte contient au moins partiellement la réponse). Une calibration plus fine de ce seuil (entre 0,10 et 0,25) pourrait être une amélioration à fort levier dans la trajectoire production (Ch. 11).

### Coût opérationnel

Les latences mesurées sur l'ensemble du *benchmark* se décomposent comme suit. La colonne `latency_s` du *benchmark* récupération mesure uniquement l'appel de vectorisation de la requête (et l'aller-retour web pour les modèles via API Azure), sans inclure la recherche ChromaDB elle-même (négligeable sur un index de cette taille). Les temps de génération discutés au § 8.3 (colonnes `t_retrieval_s` et `t_generation_s` du *benchmark* génération) sont mesurés séparément et reportés ici dans le tableau du bas pour donner une vision *end-to-end*.

Côté récupération (médianes par modèle de vectorisation sur les configurations `dense-k5`) :

| *Vectorisation* | Latence *vectorisation* médiane | Mode d'hébergement |
|-------------------------------------------------------------------------------------|-----------------------------|------------------|
| `minilm-l6` / `e5-small-ml` | ~7 ms | local (GPU) |
| `e5-base-ml` / `mpnet-base` | ~11 ms | local (GPU) |
| `granite-311m-ml` / `jina-v2-base-en` / `jina-v3` | ~15 ms | local (GPU) |
| `bilingual-fr-en` / `camembert-large` / `solon-large` / `e5-large-ml` / `bge-m3` / `nomic-v2` | ~25 ms | local (GPU) |
| `ada-002` | ~80 ms | API Azure |
| `qwen3-embed-8b` | ~260 ms | local (GPU) |
| `embed-3-large` | ~3 300 ms | API Azure |

Table: Latence de vectorisation médiane par modèle (configuration `dense-k5`).

La figure 8.3 croise ces latences avec la MRR moyenne pour visualiser le compromis qualité/coût : `ada-002` se situe juste sur le front de Pareto, dominé en latence brute par les modèles *open-source* légers (qui ne gagnent rien en qualité) et nettement préférable à `embed-3-large` qui n'apporte aucun gain mesurable de MRR pour une latence de l'ordre de 40 fois supérieure.

![Fig. 8.3. Compromis MRR moyen versus latence médiane de vectorisation par modèle d'embedding. Axe X en échelle logarithmique (millisecondes par requête, aller-retour réseau inclus pour les API). Couleur par famille (propriétaire, multilingue OSS, généraliste EN, francophone). Le trait pointillé noir relie les points du front de Pareto (modèles non dominés à la fois en MRR et en latence). Mesures effectuées sur la machine de développement décrite au § 7.5.2. Source : résultats du *benchmark* récupération, moyennes calculées sur l'ensemble des combinaisons *chunking* × variante de récupération.](figures/fig_8_3_scatter_pareto_mrr_vs_latence.png){#fig:pareto-mrr-lat width=90%}

`ada-002` est donc nettement plus lent en latence brute de vectorisation que la majorité des modèles *open-source* légers exécutés en local sur GPU (le surcoût vient entre autres de l'aller-retour réseau vers l'*endpoint* Azure), mais reste très en-dessous des autres modèles propriétaires (`embed-3-large`) et des très gros *open-source* (`qwen3-embed-8b`). Son choix opérationnel ne se justifie donc pas par la latence de vectorisation, négligeable par rapport à la génération LLM, mais plutôt par sa qualité de récupération et l'absence d'hébergement GPU côté Bouygues.

Côté génération (médianes sur 50 questions, configuration Azure de référence `hybrid-k5` + `gpt-3.5-turbo`) :

| Étape | Médiane | Écart-type |
|-------------------------------|--------------|------------------------|
| *Vectorisation* requête (`ada-002`) | environ 0,08 s | environ 0,02 s |
| Génération `gpt-3.5-turbo` | 5,09 s | 3,01 s |
| Total end-to-end | environ 5,2 s | dominé par la génération |

Table: Décomposition de la latence *end-to-end* de la chaîne de traitement RAG ScribBERT (configuration de référence Azure).

La figure 8.9 reporte cette décomposition pour les cinq configurations de génération évaluées : la couche LLM domine systématiquement la latence (entre 88 % et 99 % du temps total selon la chaîne de traitement), tandis que la récupération reste résiduelle, y compris pour les configurations qui s'appuient sur un *embedding* API ou un voisinage de *chunks*.

![Fig. 8.9. Décomposition de la latence *end-to-end* pour les cinq configurations de génération évaluées (récupération en bleu, génération en orange). Les configurations sont ordonnées par temps de génération croissant. Le total est annoté au-dessus de chaque barre. Source : résultats du *benchmark* génération, temps de récupération et de génération en valeurs médianes sur 50 questions par configuration.](figures/fig_8_9_latence_endtoend_stacked.png){#fig:stack-latency width=90%}

À titre de comparaison, la chaîne de traitement locale Mistral-7B atteint 36 à 38 s par question (essentiellement décodage GPU), hors cible pour une expérience interactive. La configuration Azure dégradée par les erreurs "too many requests" monte à 55 s médian, mais ce chiffre est lié au *benchmark*, qui enchaîne les 50 questions en rafale et sature les quotas des APIs. Un utilisateur réel, espaçant naturellement ses requêtes, ne déclencherait pas ce comportement et resterait sur des temps comparables à la configuration de référence.

Coût par requête (estimation indicative au tarif Azure OpenAI public) :

- Vectorisation requête (`ada-002`, environ 50 *tokens*) : environ 0,000005 €
- Génération `gpt-3.5-turbo` (pour 2 500 *tokens* contexte + 300 *tokens* réponse) : environ 0,002 €
- Total environ 0,002 €/requête, soit moins de 0,20 € pour 100 questions.

Estimation du coût total de la campagne de *benchmark* (estimation indicative, hors temps GPU local) :

- Construction des index vectoriels : seuls les modèles de vectorisation propriétaires (`ada-002`, `embed-3-large`) ont engendré un coût API. Avec 9 stratégies de *chunking* x 2 modèles de vectorisation et un corpus d'environ 1,3 million de *tokens* par stratégie, cela représente environ 23 millions de *tokens* embeddés cumulés, soit environ 1,2 € pour `ada-002` (0,0001 €/1k *tokens*) et environ 1,5 € pour `embed-3-large` (0,00013 €/1k *tokens*). Les autres modèles de vectorisation étant exécutés en local sur GPU, leur coût se limite à la consommation électrique.
- Vectorisations de requête sur la campagne récupération : 750 configurations x 50 questions = 37 500 requêtes, dont environ 250 configurations utilisaient un modèle de vectorisation API, cela représente moins de 1 € cumulé.
- Génération `gpt-3.5-turbo` sur les campagnes génération (3 configs Azure x 50 questions) et stabilité (1 config x 50 questions x 10 runs) : environ 750 appels avec environ 3 000 *tokens* de contexte et 300 *tokens* de réponse, soit environ 1,5 €.
- Évaluation RAGAS (4 métriques × 5 configs × 50 questions, chaque métrique faisant plusieurs appels *LLM-juge* avec un contexte de 2 à 3 k *tokens*) : c'est le poste le plus important, environ 5 à 7 € selon le détail des *prompts* internes RAGAS.
- Total estimé : environ 10 à 15 € pour l'ensemble de la phase exploratoire Azure, hors coût matériel/électrique du GPU local utilisé pour les modèles de vectorisation *open-source* et pour les deux runs Mistral-7B.

Ce niveau de coût montre qu'un balayage exploratoire de cette ampleur reste largement accessible dans un cadre de POC interne, et que c'est plutôt le temps machine (durée totale d'exécution de l'ordre de plusieurs dizaines d'heures cumulées sur la machine de développement) qui constitue le facteur limitant, pas la facture API.

L'ajout d'un *reranking* *cross-encoder* (`bge-reranker-v2-m3`) en local représenterait un surcoût matériel plus qu'un surcoût monétaire, et ajouterait de l'ordre de 0,3 à 0,5 s par requête (temps nécessaire au *reranker* pour re-scorer les 20 *chunks* issus de la récupération initiale et n'en conserver que les 5 meilleurs), d'après les essais préliminaires inclus dans `dense-k20-rerank5`.

```{=latex}
\newpage
```

## Analyse qualitative et étude d'erreurs

### Méthodologie

La phase de test utilisateur menée pendant le projet a recueilli des retours majoritairement positifs. Ce chapitre instancie la typologie d'erreurs en 8 catégories définie au Ch. 5.5.4 (échec de récupération, bruit de récupération, hallucination factuelle, omission d'exception, inversion de modalité, contradiction silencieuse, refus à tort, hors-périmètre accepté) sur les sorties de la configuration de référence (`recursive-512-64` + `ada-002` + `hybrid-k5` + `gpt-3.5-turbo`) sur les 50 questions du jeu de test.

La méthode est volontairement reproductible : chaque catégorie d'erreur est associée à une règle de seuil sur les scores RAGAS par question, ce qui permet d'attribuer chaque erreur à un maillon de la chaîne. Les fréquences sont donc calculables directement par un script à partir des colonnes RAGAS du CSV, là où les exemples et les causes restent issus d'une lecture manuelle des contextes et des réponses.

### Typologie d'erreurs observées

Pour chiffrer chaque catégorie d'erreur sur les 50 questions, les scores RAGAS calculés question par question (*context recall*, *context precision*, *faithfulness*) sont utilisés comme indicateurs : un seuil simple sur ces scores permet de classer chaque question dans la bonne catégorie, et un script compte ensuite combien de questions tombent dans chacune.

Concrètement, les seuils retenus sont les suivants :

- Échec de récupération : *context recall* inférieur à 0,30, signe que les *chunks* attendus ne sont pas dans le top-5.
- Bruit de récupération : *context precision* inférieur à 0,30 alors que le top-5 contient bien des *chunks*, signe d'un top-5 dilué.
- Hallucination factuelle : *faithfulness* inférieure à 0,50 sur une réponse qui n'est pas un refus, le LLM affirme alors sans s'appuyer sur le contexte.
- Omission d'exception : sur une question conditionnelle, *faithfulness* ≥ 0,50 mais *context recall* inférieur à 0,60, la règle est citée mais sans son cas particulier.
- Contradiction silencieuse : *faithfulness* égal à 0 sur une réponse longue et structurée, toutes les assertions sont contredites par le contexte.
- Refus à tort : réponse de type « information non trouvée » alors que le jeu de test indique des documents de référence existants.
- Hors-périmètre accepté : question annotée hors-périmètre à laquelle le système répond au lieu de refuser.
- Inversion de modalité : "doit" devenu "peut" ou l'inverse.

Sur la config de référence (50 questions) :

| Catégorie d'erreur | Fréquence (config réf) | Exemple représentatif | Interprétation |
|-------------------------|-----------------------------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Échec de récupération | 10/50 (20 %) | Q003 « Que faire si l'O2 d'un espace confiné est < 19,5 % ? » le *chunk* de `REF-2223` citant le seuil sort du top-5, remplacé par des *chunks* plus généraux sur la ventilation | Le *chunk* normatif (court, dense) est mal classé face aux *chunks* longs qui répètent le concept large « espace confiné ». Ajouter à l'index une paraphrase titre + résumé pour chaque référentiel, et tester `dense-k20-rerank5` |
| Bruit de récupération | 9/50 (18 %) | Q005 « Différence entre permis de feu et permis d'intervention ATEX ? » top-5 dominé par le « permis de feu », un seul *chunk* ATEX | Sur les questions comparatives, l'entité la plus représentée noie la seconde. Décomposer en sous-requêtes (Ch. 4.3.6) ou appliquer un *cross-encoder* sur chaque moitié du contexte |
| Hallucination factuelle | 1/50 (2 %) | Q013 « Pourquoi le harnais est-il imposé en PEMP ? » la règle est dans le contexte mais pas sa justification | Quand le contexte est partiel, le modèle complète depuis sa connaissance générale au lieu de signaler la lacune. Durcir la consigne « pas d'extrapolation hors-sources » et imposer la citation atomique |
| Omission d'exception | 3/9 sur les conditionnelles | Q008 « Quelle procédure pour ne pas porter de harnais en hauteur ? » l'obligation est citée, l'alternative « protection collective équivalente » (`REF-2211`) est omise | Règle et exceptions sont dans des sections distinctes ; le top-5 attrape l'une mais pas l'autre. Passer à top-10 + *reranker*, ou *parent-document retrieval* |

Table: Erreurs liées à la récupération (configuration de référence ScribBERT, 50 questions).

| Catégorie d'erreur | Fréquence (config réf) | Exemple représentatif | Interprétation |
|-------------------------|-----------------------------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| Contradiction silencieuse | 0/50 (config référence) ; 1/50 sur Mistral local | Cf. Q046 ci-dessous (Cas 6, § 9.3) | Sur la config de référence Azure, aucune contradiction silencieuse détectée. Sur les *chaînes* Mistral-7B local, le risque réapparaît (réponse longue plausible sans source) : prévoir un garde-fou applicatif (refus forcé si *faithfulness* nul et réponse longue) |
| Refus à tort | 0/50 |  | La config de référence n'a refusé aucune question légitime. À surveiller en production pour arbitrer le seuil selon le profil réel des questions |
| Hors-périmètre accepté | 0/4 |  | Les 4 questions hors-périmètre (Q007, Q028, Q029, Q050) ont toutes déclenché le refus attendu. Compléter le jeu de test par des adversariales plus subtiles |
| Inversion de modalité | 2/15 sur le sous-échantillon manuel | Deux cas où une obligation (« doit ») est restituée en recommandation (« il est recommandé de »), sur des questions où le *chunk* normatif n'était pas en tête du top-5 | Quand le top-5 est dominé par des reformulations pédagogiques plutôt que par le référentiel, le LLM reprend leur ton recommandatif. Consigne *prompt* « reprendre les verbes "doit", "ne doit pas", "peut" tels quels » |

Table: Erreurs liées au *prompt* et aux garde-fous (configuration de référence ScribBERT, 50 questions).

La figure 9.1 reporte la fréquence de chaque catégorie obtenue par classification automatique *non-exclusive* (une même question peut tomber dans plusieurs catégories ; les totaux peuvent donc excéder 50). Les catégories *inversion modalité* et *omission d'exception* sont sous-représentées par cette classification purement automatique fondée sur les seuils RAGAS, et sont à compléter par l'évaluation humaine ciblée mentionnée au § 8.3 (sous-échantillon stratifié de 15 questions).

![Fig. 9.1. Distribution des 50 questions du jeu de test par catégorie d'erreur (configuration de référence `recursive-512-64 / ada-002 / hybrid-k5 / azure-gpt35`). Classification automatique non-exclusive à partir des seuils RAGAS définis au § 9.2 (échec : *context recall* < 0,30 hors hors-périmètre ; bruit : *context precision* < 0,30 ; hallucination : *faithfulness* < 0,50 avec *context recall* ≥ 0,50 ; etc.). La catégorie *inversion modalité* n'est pas détectable à partir des seuls scores RAGAS automatiques et reste fixée à 0 dans cette vue. La barre « OK » regroupe les questions n'ayant déclenché aucune des catégories d'erreur ci-dessus (ni échec, ni bruit, ni hallucination, ni omission, ni contradiction silencieuse). Source : résultats détaillés par question de la configuration de référence (campagne de génération).](figures/fig_9_1_distribution_categories_erreur.png){#fig:err-categories width=90%}

Lecture transverse : sur les 50 questions, 13 sont concernées par au moins une erreur de récupération (miss ou bruit, certaines cumulant les deux), soit 26 %. C'est cohérent avec un Hit@5 de 0,80 sur la config (§ 8.3) et confirme que le levier principal d'amélioration reste la récupération plutôt que la génération. Sur le sous-ensemble où la récupération est correcte, la *faithfulness* moyenne grimpe à 0,88, contre 0,77 sur l'ensemble.

### Études de cas

Six cas tirés de la config de référence, choisis pour couvrir succès, échecs et zones grises. Format compressé : Q (question), F/CR/CP (faith / ctx_recall / ctx_precision), interprétation

Cas 1 - Succès net (Q001, factuelle, FR, criticité élevée).
Q : « Quels sont les EPI obligatoires ? » F 1,00 / CR 1,00 / CP 1,00. Le top-5 contient le *chunk* exact du « Référentiel EPI » (BYTP-H&S-REF-2219), la réponse liste les 6 EPI et la règle des 80 dB(A) avec citation correcte. Les questions factuelles à vocabulaire métier précis (« EPI obligatoires ») sont l'archétype du cas favorable.

Cas 2 - Cross-lingual réussi (Q040, factuelle, EN, criticité élevée).
Q : « What is the immediate procedure upon discovering a suspected unexploded ordnance (UXO) on a BYTP construction site? » F 0,88 / CR 1,00 / CP 1,00. Le top-5 remonte directement le « Safety Alert UXO - ALIGN » (EN). Sur ce corpus, `ada-002` + `hybrid-k5` n'a pas de difficulté à apparier une question EN à un doc EN. Le cas plus difficile reste la combinaison inverse (question FR sur doc EN court), observée sur Q046 (cf. Cas 6 ci-dessous et § 9.4.2).

Cas 3 - Information absente du corpus, révélée par l'évaluation (Q017, FR, criticité élevée).
Q : « Dans quels cas Bouygues TP est-il tenu d'établir un plan de prévention avec un sous-traitant ? » F 0,00 / CR 0,00 / CP 0,00. Le test set pointe vers `BYTP-H&S-PRO-2078 Gestion des sous-traitants`, mais une vérification manuelle confirme que le seuil réglementaire n'y figure pas : l'information n'est tout simplement pas dans le corpus interne. Azure produit ici le refus attendu (« Cette information ne figure pas dans les référentiels consultés »), tandis que les deux chaînes de traitement locales fabriquent une réponse plausible mais non sourcée. Piste pour corriger ce manque : ajouter au corpus une note de synthèse réglementaire reprenant ces seuils.

Cas 4 - Bruit à la récupération sur comparaison (Q005, comparative, FR, criticité élevée).
Q : « Quelle différence entre un permis de feu et un permis d'intervention en zone ATEX ? » F 1,00 / CR 0,75 / CP 0,20. Le système répond correctement sur la partie « permis de feu » mais la partie ATEX est diluée par 3-4 *chunks* hors-sujet. Les questions binaires (« différence entre A et B ») nécessitent une décomposition en sous-requêtes pour garantir l'équilibre des contextes (Ch. 4.3.6). En complément, une fonctionnalité de *gap analysis* a déjà été intégrée au POC : elle permet à l'utilisateur de lancer la même question sur plusieurs sous-ensembles de documents qu'il sélectionne pour visualiser les écarts entre les réponses obtenues, utile précisément sur les comparaisons où chaque entité doit être isolée dans son document de référence. Au-delà de Q005, cette fonctionnalité a aussi vocation à accélérer l'ouverture de chantiers dans un nouveau pays, en identifiant rapidement les écarts entre les référentiels internes Bouygues TP et les réglementations locales applicables.

Cas 5 - Hors-périmètre dangereux correctement refusé (Q029, FR, criticité élevée).
Q : « Comment court-circuiter un dispositif de verrouillage de sécurité en cas de perte de la clé de consignation ? » F 0,00 / CR 0,00 / réponse : « Cette information ne figure pas dans les référentiels consultés. ». Le refus textuel sans contexte fonctionne, y compris face à une question adversariale dangereuse. C'est un point fort à formaliser comme test de non-régression.

\needspace{16\baselineskip}

Cas 6 - Contradiction silencieuse latente (Q046, justificative, FR, criticité élevée).
Q : « Pourquoi la notion de "ligne de feu" est-elle centrale dans la prévention des accidents ? » F 0,00 / CR 0,00. Le document cible `First Alert Stay Risk Aware in the Line of Fire - ALIGN` est en anglais alors que la question est posée en français, et il s'agit d'un format d'alerte court : l'appariement cross-lingue échoue, le top-5 ne remonte aucun *chunk* de ce document. Sur la configuration de référence Azure (`hybrid-k5` + `gpt-3.5-turbo`), le système retombe correctement sur le refus standardisé (« Cette information ne figure pas dans les référentiels consultés. »), grâce à la consigne *prompt* qui interdit de produire une réponse non sourcée. Sur les deux *chaînes de traitement* Mistral-7B local en revanche, la même question déclenche une réponse longue, structurée et thématiquement plausible, fabriquée à partir de la connaissance générale du modèle, sans qu'aucun *chunk* source ne la valide. C'est l'archétype de la contradiction silencieuse : réponse « d'allure experte » sans ancrage documentaire, situation la plus problématique pour la confiance utilisateur. Sur la configuration de référence, ce risque est neutralisé par le *prompt* (cf. Ch. 7.7) ; sur la voie souveraine Mistral local, il faudra un garde-fou applicatif explicite.

### Cas limites et ambiguïtés

#### Acronymes et jargon métier

Sur les 50 questions du jeu de test, 17 contiennent au moins un acronyme métier (EPI, ATEX, PPE, SST, CATEC, LOTO, MEWP, UXO, HiPo) ou un sigle organisationnel (BYTP, BYCN, ALIGN). Contrairement à l'hypothèse initiale (« les vectorisations généralistes contextualisent mal les acronymes »), la sous-population « avec acronyme » obtient expérimentalement de meilleurs scores :

| Sous-population | n | Faith. moyenne | Ctx. recall moyen |
|-------------------------|----|----------------|-------------------|
| Questions avec acronyme | 17 | 0,918 | 0,699 |
| Questions sans acronyme | 33 | 0,686 | 0,593 |

Table: Stratification des scores selon la présence d'un acronyme dans la question.

Ce résultat ne signifie pas que l'acronyme « aide » en soi : il s'explique surtout par un facteur de confusion. Les questions sans acronyme sont majoritairement des formulations ouvertes (« pourquoi… », « comment… ») intrinsèquement plus difficiles, alors que les questions avec acronyme sont souvent factuelles et s'ancrent sur un terme à forte spécificité lexicale, présent tel quel dans les *chunks* d'origine (titres, listes, tableaux), ce qui suffit à une vectorisation dense généraliste pour les apparier, sans nécessiter d'expansion.

Conséquence pratique, le levier d'expansion d'acronymes (évoqué au Ch. 4.3.6 parmi les techniques de *query rewriting*) devient *a priori* secondaire sur ce corpus. L'effort doit plutôt se porter sur les questions ouvertes en langage naturel, qui constituent le véritable point faible du système.

#### Multilinguisme et alternance codique

Sur 9 questions EN et 41 questions FR, la config de référence donne :

| Langue | n | Faith. moyenne | Ans. relevancy | Ctx. recall |
|--------|----|----------------|----------------|-------------|
| EN | 9 | 0,913 | 0,950 | 0,690 |
| FR | 41 | 0,733 | 0,799 | 0,616 |

Table: Stratification des scores RAGAS par langue de la question.

Ce résultat est, là encore, contre-intuitif : l'EN performe *mieux*. Deux explications : 

1. biais d'échantillonnage (n=9 EN, dispersion forte, non significative statistiquement)
2. les questions EN du jeu de test sont majoritairement factuelles ou procédurales claires (« What PPE… », « What permits… », « What is the immediate procedure… »), alors que les FR couvrent plus de questions justificatives ou conditionnelles plus difficiles.

La situation inédite (question FR sur doc cible EN) a en revanche été observée sur quelques cas dont Q046 (§ 9.3, Cas 6) : le doc `First Alert Stay Risk Aware in the Line of Fire - ALIGN`, court et uniquement en anglais, n'est pas remonté alors que la question est posée en français. `ada-002` est multilingue et le top-5 mélange spontanément FR et EN selon la pertinence, mais l'appariement échoue quand le doc cible EN est trop court pour offrir un signal sémantique suffisant face à une requête FR plus longue (c'est l'asymétrie de longueur qui creuse l'écart cosinus, pas la différence de langue seule). Le LLM répond toujours dans la langue de la question. Ces observations doivent être confirmées sur un jeu de test équilibré (objectif § 11.2.1).

#### Hors-périmètre

Le jeu de test contient 4 questions hors-périmètre (Q007, Q028, Q029, Q050). En pratique :

- 4/4 ont produit le refus standardisé attendu : « Cette information ne figure pas dans les référentiels consultés. », couvrant des questions RH et une question adversariale dangereuse (court-circuiter un verrouillage de sécurité, Q029).

Sur ce périmètre, le filtre par distance (`dense-k5-thresh` à seuil 0,17) joue son rôle de garde-fou : quand aucun *chunk* ne franchit le seuil, le contexte injecté au LLM est vide ou très partiel et le *prompt* système conduit au refus. Cependant, le filtre est passif. Une question adversariale proche d'un sujet du corpus (ex. « comment ne pas porter d'EPI sans se faire prendre ? ») pourrait remonter des *chunks* plausibles et passer la barrière.

La figure 9.3 récapitule la performance moyenne par type de question. Les factuelles et procédurales atteignent les meilleurs scores RAGAS sur les quatre dimensions ; les conditionnelles décrochent nettement sur le *context recall* (signe d'exceptions ou de fondements omis lors de la récupération) ; les justificatives présentent une *faithfulness* plus dispersée, cohérent avec la difficulté à fonder une explication sur des *chunks* normatifs ; et les hors-périmètre se distinguent par une *faithfulness* moyenne nulle correspondant aux refus contrôlés correctement déclenchés. Cette stratification motive l'analyse fine des biais conduite au § 9.5.

![Fig. 9.3. Stratification des scores RAGAS par type de question (configuration de référence). Chaque groupe correspond à l'un des six types annotés dans le jeu de test (l'effectif $n$ est indiqué sous l'étiquette) ; les barres représentent la moyenne par métrique RAGAS, les segments verticaux l'intervalle de confiance à 95 %. Source : résultats détaillés par question de la configuration de référence, joints au jeu de test annoté pour récupérer le type de chaque question.](figures/fig_9_3_ragas_par_type_question.png){#fig:ragas-type width=100%}

### Biais identifiés

Quatre biais ont été observés sur la base des données disponibles, certains avec une amplitude qui justifie un traitement dédié dans la trajectoire production.

Biais de corpus (observé indirectement). Les questions liées au travail en hauteur, EPI et énergies dangereuses obtiennent les meilleurs scores RAGAS (*faithfulness* ≥ 0,87 en moyenne), ce qui reflète à la fois la qualité des questions et la densité documentaire sur ces sujets dans le corpus. Les sujets sous-documentés (santé mentale, risque chimique avancé) n'apparaissent quasiment pas dans le jeu de test actuel, et l'évaluation ne dit donc rien de leur traitement par le système. C'est un angle mort à corriger lors de l'extension du jeu de test (Ch. 11.2.1).

Biais d'ordre d'index (effet faible). ChromaDB en HNSW n'introduit pas de biais d'ordre dans la récupération (les résultats sont triés par similarité), mais l'ordre de citation dans la réponse générée pourrait refléter l'ordre d'arrivée des *chunks* dans le contexte. La campagne de stabilité (§ 8.4) montre $1 - \mathrm{Stab@cit} = 1 - 0{,}935 = 0{,}065$, soit 6,5 % de variation moyenne sur l'ensemble des sources citées d'un run à l'autre, cohérent avec cet effet et tolérable en l'état.

Biais de longueur (effet fort, à neutraliser). Les réponses générées par `gpt-3.5-turbo` sur la configuration de référence font en moyenne 177 mots (médiane 170, maximum 481), soit environ 230 *tokens* (jusqu'à plus de 600 pour les réponses les plus développées). La corrélation entre longueur de la réponse et scores RAGAS est très marquée : Pearson $r = +0{,}64$ avec la *faithfulness* et $r = +0{,}63$ avec l'*answer relevancy*. Stratifié par longueur de réponse, l'effet est net :

| Longueur (mots) | n | Faith. moyenne | Ans. relevancy moyen | Ctx. recall moyen |
|------------------------------------|----|----------------|----------------------|-------------------|
| < 100 (refus + factuelles courtes) | 11 | 0,27 | 0,26 | 0,43 |
| 100 - 200 | 20 | 0,89 | 0,84 | 0,63 |
| ≥ 200 | 19 | 0,92 | 0,95 | 0,75 |

Table: Stratification des scores RAGAS par longueur de la réponse générée (configuration de référence, 50 questions).

La figure 9.4 visualise cette corrélation point par point sur les deux métriques les plus sensibles, *faithfulness* et *answer relevancy*, et matérialise la régression linéaire associée.

![Fig. 9.4. Effet de la longueur de la réponse générée (en mots, axe X) sur les scores RAGAS de *Faithfulness* (gauche) et *Answer Relevancy* (droite). Une question = un point ($n = 50$). La droite rouge pointillée correspond à une régression linéaire simple, le coefficient de Pearson est indiqué dans le titre de chaque sous-figure. Source : résultats détaillés par question de la configuration de référence `recursive-512-64 / ada-002 / hybrid-k5 / azure-gpt35`, longueur calculée à partir du texte de chaque réponse.](figures/fig_9_4_scatter_longueur_ragas.png){#fig:length-ragas width=95%}

Une partie de cette corrélation est légitime : les réponses très courtes sont essentiellement des refus contrôlés, par construction notés *faithfulness* = 0 par RAGAS. Mais une partie correspond à un biais documenté du *LLM-as-judge* : les juges LLM tendent à mieux noter les réponses verbeuses, plus structurées et plus enrobées, indépendamment de leur exactitude factuelle [@Zheng2023JudgeBias]. Sur les questions factuelles courtes (« Quels sont les EPI obligatoires ? »), la sur-longueur amplifie en outre le *context recall* mécaniquement, puisque toutes les sources sont de facto citées dans une réponse plus longue. Deux mitigations sont à étudier en parallèle de la prochaine itération : durcir la consigne de concision dans le *prompt* système et calibrer les scores RAGAS sur un échantillon annoté humainement (§ 5.2.3).

Biais linguistique (effet faible sur la moyenne, mais asymétrie structurelle à investiguer). Les questions FR et EN du jeu de test ont des longueurs comparables (16,6 vs 16,9 mots en moyenne), donc l'asymétrie observée au § 9.4.2 (FR 0,73 vs EN 0,91 de *faithfulness*) ne vient pas d'un effet longueur côté requête. Elle s'explique principalement par la composition du sous-échantillon EN (n=9), majoritairement factuel et procédural, contre un sous-échantillon FR plus chargé en questions justificatives et conditionnelles. Un mécanisme distinct, observé sur Q046 (§ 9.3, Cas 6 et § 9.4.2), apparaît en revanche quand le document cible est lui-même court : le `Safety Alert Line of Fire` tient sur un seul *chunk* de 265 mots, soit nettement moins que la taille moyenne d'un *chunk* `recursive-512-64`. Face à une requête FR de longueur comparable mais sémantiquement plus diffuse, l'écart cosinus se creuse mécaniquement (la similarité dense est sensible à la norme de la représentation, elle-même affectée par la longueur effective de l'unité comparée), ce qui éjecte ce document court du top-5. Le levier n'est donc pas linguistique au sens strict, mais structurel : prévoir au moins une paraphrase-résumé indexée pour les documents très courts, ou tester un *chunking* avec padding contextuel pour homogénéiser la longueur des unités indexées. Cette piste sera évaluée lors de l'extension du jeu de test EN (Ch. 11.2.1) avant d'écarter toute hypothèse de biais linguistique latent.

La figure 9.5 croise ces deux stratifications par métadonnées (langue à gauche, criticité à droite) sur les quatre scores RAGAS, et permet de visualiser à la fois l'asymétrie FR/EN évoquée ci-dessus et l'absence d'effet net de la criticité métier sur la qualité de réponse moyenne.

![Fig. 9.5. Scores RAGAS stratifiés par langue de la question (a) et par criticité métier (b), sur la configuration de référence. Boxplots par métrique RAGAS, effectifs indiqués dans la légende. La sous-figure (a) montre que les questions EN ($n = 9$) ont en moyenne des scores plus élevés que les FR ($n = 41$), effet à interpréter avec prudence vu la composition des deux sous-échantillons (cf. § 9.5, biais linguistique). La sous-figure (b) ne montre pas d'effet net de la criticité, hors léger fléchissement sur les criticités basse et moyenne (effectifs très réduits, $n = 3$ et $n = 5$). Source : résultats détaillés par question de la configuration de référence, joints au jeu de test annoté pour récupérer la langue et la criticité de chaque question.](figures/fig_9_5_ragas_par_langue_criticite.png){#fig:lang-crit width=100%}

### Retours utilisateurs (phase de test)

Une phase de test ouverte a été conduite auprès d'un panel d'utilisateurs internes du département P2S et au-delà. Les retours qualitatifs collectés ont été globalement positifs, en particulier sur :

- la rapidité d'accès à l'information par rapport à une consultation manuelle des PDF
- la présence systématique des sources rendant la vérification simple
- l'ergonomie de l'interface et la possibilité de naviguer vers le document source.

Les principaux axes d'amélioration remontés concernent : 
1. La prise en charge des questions comparatives ou contrastives (par exemple « Quelles différences entre les procédures de levage BYTP et les exigences réglementaires ? »). Le top-$k$ actuel agrège bien jusqu'à 3-4 documents distincts dans une même réponse, mais il ne sait pas isoler explicitement deux sources concurrentes pour les mettre face à face : il n'existe aujourd'hui aucun mécanisme dans le *prompt* classique pour forcer la sélection équilibrée de *chunks* issus de référentiels différents puis structurer la réponse en comparaison point à point. C'est précisément ce besoin qui a justifié l'intégration au POC de la fonctionnalité de *gap analysis* (cf. § 9.3, Cas 4) : l'utilisateur sélectionne manuellement deux sous-ensembles de documents et la même requête est exécutée sur chacun séparément, ce qui garantit l'isolation des sources et rend les écarts directement lisibles.
2. L'exploitation des tableaux et schémas des PDF (non gérés dans le POC, cf. § 7.2.3)
3. La persistance des sessions de chat entre rechargements : la mémoire conversationnelle multi-tours est déjà opérationnelle au sein d'une session, mais l'historique est perdu dès que l'utilisateur rafraîchit la page ou revient le lendemain. Un stockage côté serveur des sessions passées avec consultation et reprise reste à implémenter.
4. Un score de confiance affiché par réponse, point déjà recommandé au Ch. 6.6.

Une enquête structurée reste à mener pour passer de l'impression qualitative à une mesure consolidée. Cette enquête est identifiée comme priorité dans la trajectoire d'industrialisation (Ch. 11.5.1). Au-delà de la mesure, la formation et l'accompagnement des utilisateurs finaux (bonnes pratiques de formulation des requêtes, lecture critique des réponses, vérification systématique des sources citées) constituent un axe tout aussi prioritaire : l'adoption d'un outil de RAG en contexte santé-sécurité dépend autant de la maîtrise utilisateur que de la performance technique.

```{=latex}
\newpage
```

## Enjeux éthiques, réglementaires et industriels

L'industrialisation d'un RAG dans un domaine critique comme la santé-sécurité soulève des questions qui dépassent la performance technique : conformité réglementaire, responsabilité, gouvernance, acceptabilité. Ce chapitre les traite spécifiquement, ce qui était demandé par la nature du sujet et la maturité croissante du cadre européen sur l'IA.

### Le cadre réglementaire européen : l'AI Act

#### Classification du système

L'AI Act européen (Règlement UE 2024/1689), entré en vigueur en août 2024 avec une application progressive jusqu'à 2027, classe les systèmes d'IA selon leur niveau de risque. ScribBERT, en tant qu'assistant d'aide à la décision dans un contexte santé-sécurité, peut être analysé selon cette grille :

- Risque inacceptable : non concerné (pas de manipulation, pas de notation sociale).
- Haut risque : potentiellement concerné dès lors que le système est considéré comme contribuant à la gestion des risques pour la sécurité des compagnons, ce qui correspond aux usages listés dans l'annexe III du règlement (notamment dans le domaine de l'emploi et de la gestion des travailleurs).
- Risque limité : concerné par les obligations de transparence (l'utilisateur doit savoir qu'il interagit avec une IA).
- Risque minimal : non applicable ici.

#### Obligations applicables (en hypothèse haut risque)

Si ScribBERT est classifié "haut risque", les obligations principales sont les suivantes :

- Système de gestion des risques documenté et tenu à jour.
- Qualité des données d'entraînement : moins applicable ici (pas de *fine-tuning*), mais la qualité du corpus est un équivalent fonctionnel.
- Documentation technique détaillée et journaux d'événements.
- Transparence envers les utilisateurs (information claire sur la nature IA du système).
- Contrôle humain : possibilité d'intervention humaine, et fait que le système ne se substitue pas à un avis d'expert.
- Robustesse, exactitude et cybersécurité : niveau de performance documenté.

Le protocole d'évaluation proposé dans ce mémoire contribue directement à plusieurs de ces exigences : la mesure de la fiabilité (Ch. 5-6), la traçabilité des sources, la documentation des choix techniques (Ch. 7), constituent des éléments mobilisables pour la conformité.

#### Articulation avec d'autres référentiels

ScribBERT relève également d'autres cadres susceptibles de s'appliquer :

- Norme ISO/IEC 42001 sur les systèmes de management de l'IA ;
- Norme ISO/IEC 23894 sur la gestion des risques en IA ;
- Recommandations CNIL sur l'IA (cycle 2023-2024) pour la partie données personnelles éventuelles, ce qui me permet de faire le lien avec la partie suivante :

### RGPD et données internes

Bien que ScribBERT ne traite pas de données personnelles dans son corpus (référentiels de procédures), trois points RGPD méritent une attention particulière :

1. Journaux des requêtes utilisateurs : si une requête contient des données personnelles (nom d'un collaborateur, identifiant chantier), elle est journalisée à des fins d'amélioration. Il faut définir une durée de conservation, les finalités précises, et garantir un droit d'accès / suppression.
2. Confidentialité des documents internes : le choix d'un hébergement local au LabTP (§ 7.2.2) garantit la non-exposition à des fournisseurs cloud externes pour le POC. La bascule éventuelle vers de l'hébergement cloud en production exigerait une analyse complémentaire, idéalement avec contrats DPA appropriés.
3. Traçabilité des décisions : si une décision opérationnelle (ex. report d'une intervention) s'appuie sur une réponse de ScribBERT, la trace doit être conservée, avec la version du modèle, la version du corpus et la réponse exacte, pour permettre une analyse a posteriori.

### Responsabilité en contexte santé-sécurité

#### La question de la responsabilité

En cas d'accident sur chantier, si une décision de prévention s'appuie sur une réponse erronée de ScribBERT, qui est responsable ? Plusieurs niveaux d'analyse :

- Responsabilité juridique : Quoi qu'il arrive, légalement, l'employeur reste responsable de la sécurité de ses salariés (Code du travail français). L'outil IA n'est qu'un moyen.
- Responsabilité du système : l'éditeur (ici Bouygues TP en tant que développeur interne du POC, Bouygues Construction après industrialisation) doit pouvoir documenter ses choix et ses tests (cf. AI Act).
- Responsabilité de l'utilisateur : le préventeur reste tenu de son devoir de vérification, ce qui justifie l'avertissement affiché en permanence en bas de l'écran.

#### L'avertissement comme mesure de mitigation

ScribBERT affiche un avertissement permanent rappelant que :

- la responsabilité de la qualité des réponses n'incombe pas au système.
- l'utilisateur doit faire appel à son esprit critique et vérifier les documents sources avant toute action opérationnelle.

Cet avertissement est une mesure nécessaire mais non suffisante : la jurisprudence européenne sur les outils d'aide à la décision tend à considérer qu'un avertissement ne dégage pas l'éditeur de toute responsabilité, particulièrement si l'outil est présenté comme "expert" ou "fiable". Les renforcements possibles incluent :

- afficher un score de confiance par réponse, pour calibrer la vigilance, déjà évoqué au Ch. 6.6 et au § 9.6,
- mettre en avant les sources plus que la réponse synthétisée, l'utilisateur étant ainsi systématiquement renvoyé au document validé,
- pour les réponses critiques (port d'EPI vital, mises en sécurité), recommander explicitement la consultation des documents officiels, ou d'un préventeur santé-sécurité humain.

#### Supervision humaine

Le principe de *human-in-the-loop* est central pour les systèmes IA en domaine critique. Pour ScribBERT, cela peut prendre plusieurs formes :

- Revue périodique des journaux par l'équipe P2S, avec analyse des questions récurrentes et des cas d'erreur détectés ;
- Procédure d'escalade : un canal pour signaler une réponse erronée, avec mise à jour du corpus ou du système ;
- Validation experte des évolutions majeures (changement de modèle, mise à jour massive du corpus) avant déploiement.

### Gouvernance d'un RAG d'entreprise

L'industrialisation impose une discipline de gouvernance que le POC peut tolérer, mais que la production exige :

- Versioning : chaque mise en production identifie sans ambiguïté la version du modèle de vectorisation, du LLM, du corpus, du *prompt* et du code applicatif.
- Chaîne de traitement CI/CD avec tests d'évaluation automatisés : avant tout déploiement, le jeu de test est passé sur la nouvelle configuration et les métriques sont comparées à une configuration de référence.
- *Audit trail* : chaque réponse produite est journalisée avec l'ensemble des éléments permettant de la rejouer (cf. Ch. 5.4.3).
- Plan de gestion de l'obsolescence : les modèles propriétaires sont régulièrement dépréciés. Un plan de migration doit exister.
- Politique de mise à jour du corpus : *flux de travail* de validation pour l'ajout / la modification d'un document, avec reconstruction de l'index.

### Acceptabilité et conduite du changement

La meilleure technologie échoue si les utilisateurs ne l'adoptent pas. Trois facteurs ont été identifiés comme déterminants pour ScribBERT :

1. La confiance, gagnée par la qualité des réponses et par la transparence sur les sources. Les retours utilisateurs (§ 9.6) confirment que la présence systématique des citations est un facteur clé d'adoption.
2. L'utilité perçue par rapport à l'alternative (recherche manuelle dans les PDF, demande à un expert). ScribBERT doit faire gagner du temps sans dégrader la qualité de la décision.
3. L'accompagnement : formation initiale, communication interne, identification d'ambassadeurs dans les équipes pour porter l'outil.

Une perspective intéressante est de considérer ScribBERT non pas comme un substitut à l'expert santé-sécurité, mais plutôt comme un amplificateur/facilitateur.

```{=latex}
\newpage
```

## Discussion et perspectives

### Interprétation des résultats et synthèse des enseignements

Les Parties I et II ont posé un cadre théorique et méthodologique pour évaluer un RAG dans un contexte critique. La Partie III a montré comment ce cadre s'applique à un cas réel (ScribBERT) : la phase exploratoire a produit un *benchmark* de 750 configurations exploitables de récupération, une campagne génération sur 5 configurations (3 Azure + 2 locales) et une campagne stabilité sur la configuration de référence. Les résultats permettent à la fois d'arbitrer les choix opérationnels du POC (cf. Ch. 7-8) et d'identifier précisément ce qui reste à instrumenter (préservation des modalités, stabilité comparative entre meilleures variantes, validation humaine sur les questions critiques). L'instanciation complète du protocole sur les meilleures variantes et l'extension du jeu de test à 150-300 questions constituent les deux suites naturelles de ce travail.

Plusieurs enseignements méthodologiques se dégagent néanmoins :

1. La fiabilité d'un RAG ne se réduit pas à un seul score : c'est un faisceau de dimensions (récupération, fidélité, pertinence réponse, stabilité, traçabilité) qui doivent être mesurées séparément pour pouvoir diagnostiquer.
2. Les choix d'ingénierie (*chunking*, contextualisation, filtrage par score) ont un impact comparable à celui du choix du modèle : il est tentant de centrer l'attention sur le LLM, mais l'expérience ScribBERT confirme qu'un *chunking* adapté au corpus et un filtrage de seuil bien calibré pèsent au moins autant.
3. La stabilité est sous-évaluée dans les *frameworks* usuels : pour un système en production sur un sujet critique, la variance inter-runs et la robustesse aux paraphrases méritent un protocole dédié (Ch. 6).
4. La traçabilité est à la fois un critère technique et un enjeu de confiance : citer les sources de manière vérifiable est probablement le facteur le plus fort d'acceptabilité utilisateur observé.

### Limites méthodologiques

#### Limites du jeu de test

Le jeu de test utilisé pour ce mémoire (50 questions) est inférieur aux 150-300 questions recommandées au Ch. 5.3.4 pour des comparaisons statistiques fines : les écarts inter-configurations observés au § 8.2 doivent être lus comme des tendances cohérentes, non comme des comparaisons statistiquement décisives. Une priorité immédiate est l'extension à 150-300 questions stratifiées, avec annotation des passages de référence et des réponses de référence par des experts P2S directement, et en augmentant en particulier la part anglophone (9/50 actuellement).

#### Limites du protocole appliqué

Le *benchmark* a couvert 750 cellules exploitables en récupération et 5 configurations en génération (3 Azure + 2 locales). En revanche, la campagne de stabilité n'a porté que sur une seule configuration. Deux chantiers restent donc à mener pour clore le protocole :

- une évaluation de stabilité comparative sur les meilleures variantes (`hybrid-k5`, `dense-k20-rerank5`)
- l'instanciation manuelle des dimensions non automatisables (préservation des modalités, sûreté opérationnelle, complétude experte) sur un sous-échantillon de 10-20 questions critiques.

#### Limites du périmètre

Le corpus actuel se limite aux documents du siège, en français et anglais et deux/trois clients. L'extension aux filiales et réglementations internationales fera émerger des défis nouveaux (variantes locales, contradictions inter-entités, langues additionnelles).

#### Précautions d'interprétation

Les retours utilisateurs positifs de la phase de test sont un signal important mais ne se substituent pas à une évaluation systématique. L'effet de nouveauté et l'enthousiasme métier peuvent biaiser les retours initiaux. Une évaluation à 6 et 12 mois post-déploiement serait nécessaire pour mesurer l'usage sur la durée.

### Apports du travail

#### Apports théoriques

- Une définition opératoire de la fiabilité d'un RAG (Ch. 3.3) qui décompose le concept en cinq dimensions mesurables.
- Une clarification du rôle de la stabilité comme dimension à part entière de la fiabilité, méritant un protocole d'évaluation dédié (Ch. 6).
- Une lecture critique des *frameworks* d'évaluation existants (RAGAS, TruLens, *LLM-as-judge*), avec mise en évidence de leurs limites en domaine critique.

#### Apports méthodologiques

- Un catalogue structuré des leviers techniques d'un RAG avec leurs compromis (Ch. 4), réutilisable pour tout projet RAG d'entreprise.
- Un protocole d'évaluation diagnostique (Ch. 5) organisé par dimension, qui permet de localiser l'origine des erreurs plutôt que de juger globalement.
- Un protocole de stabilité (Ch. 6) directement applicable.

#### Apports industriels (cas ScribBERT)

- Une architecture RAG fonctionnelle et adaptée aux contraintes de Bouygues TP (souveraineté des données, multilinguisme FR/EN, corpus normatif).
- Une identification claire des limites du POC (hybridation, *reranking*, gestion des tableaux et images) et un plan d'amélioration priorisé.

### Recommandations pour évaluer un RAG en contexte critique

Synthèse des bonnes pratiques pour un futur projet :

1. Commencer par définir la fiabilité opérationnelle dans le contexte du domaine, avec ses dimensions critiques.
2. Construire un jeu de test représentatif et stratifié dès le début (minimum 100 questions, par type, difficulté, criticité).
3. Évaluer chaque composant avant l'évaluation *end-to-end* pour permettre le diagnostic.
4. Tester systématiquement la stabilité (pas seulement la qualité moyenne).
5. Combiner *LLM-as-judge* et validation humaine sur un échantillon pour calibrer.
6. Mesurer le coût opérationnel (latence, €) en parallèle de la qualité.
7. Versionner et *journaliser* tout, dès le POC : ce qui n'est pas tracé ne peut être ni reproduit ni réutilisé.
8. Anticiper la conformité AI Act et les enjeux de responsabilité dès la conception, pas après le déploiement.

### Perspectives

#### Améliorations techniques court terme (ScribBERT)

- Hybridation BM25 + dense pour améliorer le rappel sur les références exactes.
- *Reranker* *cross-encoder* pour la précision du top-$k$ injecté.
- Image-to-text contextualisé pour intégrer tableaux et schémas.
- Enrichissement des métadonnées des *chunks*.
- Refactoring du *prompt* système : itérer sur la formulation des instructions pour traiter à la source plusieurs des biais identifiés au § 9.5 (biais de longueur, biais d'ordre des citations) sans modifier la chaîne de traitement de récupération.
- Évaluation systématique selon le protocole Ch. 5-6.

#### Pistes de recherche moyen terme

- *Fine-tuning* d'un modèle de vectorisation sur le corpus santé-sécurité (apprentissage contrastif sur paires question/passage), pour combler l'absence de modèle spécialisé santé-sécurité/BTP identifié au Ch. 4.1.1.
- *GraphRAG* : exploiter une représentation en graphe des entités santé-sécurité (procédures, EPI, risques, situations) pour des requêtes nécessitant un raisonnement multi-saut.
- *Agentic* RAG : pour les questions complexes, décomposer en sous-questions, lancer plusieurs *retrievals*, agréger.
- RAG multimodal : intégrer images, schémas, vidéos de formation comme sources de premier niveau.

#### Généralisation à d'autres domaines

Le cadre méthodologique proposé est transférable à d'autres business units réglementaires et techniques : juridique (jurisprudence, contrats), ressources humaines (conventions collectives, accords d'entreprise, politiques internes), maintenance industrielle (procédures, modes opératoires). Les adaptations principales concernent :

- la définition opérationnelle de la fiabilité dans le domaine cible (quelles dimensions sont critiques ?)
- la construction du jeu de test (qui annote ? selon quels critères ?)
- les contraintes réglementaires spécifiques (RGPD, secret professionnel juridique, etc.)

#### Enjeux éthiques et de responsabilité à long terme

L'évolution des cadres réglementaires (AI Act, normes ISO 42001) et la jurisprudence à venir sur la responsabilité des systèmes IA en domaine critique vont préciser les exigences. Les systèmes RAG d'entreprise devront probablement, à terme :

- être audités par des tiers
- exposer des garanties documentées de fiabilité
- intégrer la supervision humaine non comme option mais comme exigence

L'investissement méthodologique fait dans ce mémoire sur l'évaluation rigoureuse anticipe ces évolutions et positionne ScribBERT comme un cas d'usage exemplaire d'IA industrielle responsable dans le secteur de la construction.

---

```{=latex}
\cleardoublepage
```

# Conclusion générale {-}

Ce mémoire posait une question simple à formuler mais difficile à traiter : *comment évaluer la cohérence et la fiabilité d'un système RAG ?* La réponse défendue ici tient en une idée simple : la fiabilité d'un RAG n'est pas une étiquette qu'on appose après avoir constaté que « les réponses ont l'air bonnes », c'est une propriété systémique qu'il faut décomposer en dimensions mesurables (pertinence de la récupération, fidélité aux sources, pertinence de la réponse, stabilité inter-runs, traçabilité auditable), puis instrumenter par un protocole reproductible combinant métriques automatiques et validation humaine ciblée. La cohérence, en particulier, n'est pas un concept distinct à juxtaposer à la fiabilité : elle se laisse précisément lire comme le couple « fidélité aux sources + stabilité des réponses », et c'est cette décomposition qui rend possible le diagnostic de l'endroit où la chaîne échoue (récupération, *reranking*, génération) plutôt qu'un verdict global au jugé.

L'apport du travail est d'abord méthodologique. Il propose une définition opératoire de la fiabilité, un cadre d'évaluation diagnostique structuré autour de ces dimensions, et l'intégration explicite de la stabilité inter-runs comme dimension à part entière, là où la plupart des *frameworks* existants la traitent comme un effet de bord. Il est aussi applicatif : une architecture RAG fonctionnelle, instanciée sur ScribBERT au département P2S de Bouygues Travaux Publics, dont les choix techniques (souveraineté des données, multilinguisme FR/EN, corpus normatif hétérogène) ont été documentés et justifiés, et dont les limites du POC (absence d'hybridation lexicale, pas de *reranking*, gestion fragile des tableaux) ont été identifiées et hiérarchisées dans un plan d'amélioration. Le cadre proposé est par construction transférable : il ne dépend pas du corpus santé-sécurité et peut être réinstancié sur d'autres domaines documentaires soumis à des exigences de fiabilité élevées.

Ce travail comporte trois limites. La première tient à la taille du jeu de test interne (50 questions stratifiées), en-deçà des 150 à 300 questions habituellement recommandées pour assoir des comparaisons statistiquement décisives entre configurations ; les écarts observés entre variantes doivent donc être interprétés comme des signaux d'orientation plus que comme des verdicts. La deuxième tient à l'instanciation incomplète du protocole : 864 configurations *retrieval* ont été *benchmarkées* (dont 750 exploitables), mais seules 5 ont fait l'objet d'une évaluation RAGAS complète et une seule d'une étude de stabilité étendue ; le protocole décrit en Partie II est donc validé sur son axe principal, mais reste à dérouler sur l'ensemble de la matrice. La troisième tient à la généralisation : transférer le cadre à d'autres contextes (juridique, médical, technique aéronautique) nécessitera une validation empirique sur ces corpus, en particulier pour ce qui concerne la pertinence des seuils et des pondérations de la grille humaine.

Les perspectives qui s'ouvrent sont à la fois opérationnelles et de recherche. À court terme, ScribBERT bénéficiera de l'application complète du protocole d'évaluation sur les améliorations prioritaires identifiées : récupération hybride dense/BM25, *reranking* par *cross-encoder*, et meilleur traitement des contenus tabulaires. À moyen terme, le *fine-tuning* d'un modèle de vectorisation sur le corpus santé-sécurité Bouygues, ainsi que l'exploration de variantes architecturales (*GraphRAG*, RAG *agentic*, RAG multimodal pour les schémas et photos de chantier) constituent des axes de prolongement directs. À plus longue échéance, plusieurs questions ouvertes dépassent le cadre de ce mémoire mais en sont le prolongement naturel : comment faire vivre un jeu de test annoté quand le corpus évolue en continu ? Comment mesurer la stabilité dans la durée plutôt qu'au moment du déploiement ? Comment articuler évaluation automatisée et retour utilisateur structuré sans en faire un goulot d'étranglement ? Ces questions constituent, à notre sens, une part importante des chantiers de recherche prioritaires pour les RAG d'entreprise dans les prochaines années.

\needspace{10\baselineskip}

Au moment de la dernière révision de ce mémoire, le projet ScribBERT vient d'être validé pour un passage en industrialisation à l'échelle du groupe Bouygues Construction. C'est une forme de validation concrète du travail mené pendant ces deux années d'alternance, et surtout l'occasion de mettre à l'épreuve, sur un périmètre élargi (plus de filiales, plus de langues, plus d'utilisateurs), le protocole décrit ici. Les systèmes RAG s'installent rapidement dans les usages internes des entreprises, mais leur évaluation reste un chantier largement ouvert. Ce mémoire aura cherché à y apporter une contribution modeste mais opérationnelle : considérer la fiabilité non comme une promesse, mais comme une propriété à éprouver dimension par dimension, et à gouverner au même titre que n'importe quel autre indicateur de performance industrielle.

---


```{=latex}
\cleardoublepage
```

# Bibliographie {-}

::: {#refs}
:::

```{=latex}
\cleardoublepage
```

# Annexes {-}

Les annexes ci-dessous documentent les matériaux mobilisés pour la mise en œuvre du protocole d'évaluation décrit en Partie II et instancié sur ScribBERT en Partie III. Elles sont référencées dans le texte principal lorsque c'est utile et permettent au lecteur de vérifier ou de reproduire les choix décrits.

## Annexe A : Échantillon du jeu de test {-}

Le jeu de test interne utilisé pour le *benchmark* (§ 8.1.2) comporte 50 questions stratifiées par type, difficulté, criticité et langue, conformément à la grille du Ch. 5.3.2. Le tableau ci-dessous reproduit un échantillon de 10 questions représentatives sur les 50 du jeu de test complet, choisies pour couvrir les six types d'intention identifiés ainsi que les trois niveaux de difficulté et de criticité.

Chaque entrée contient les champs suivants : `id`, `question`, `language`, `type`, `difficulty`, `criticality`, `ground_truth_answer`, `relevant_doc_ids`, `paraphrases`, `notes`.

- Q001 (*factuelle, élevée, fr*) : « Quels sont les EPI obligatoires ? », réponse de référence portant sur le port du harnais antichute (modalité « obligatoire » à préserver, exception « protection collective équivalente »).
- Q002 (*procédurale, moyenne, fr*) : « Quelle est la procédure à suivre avant toute intervention en espace confiné ? », réponse multi-étapes (identification, plan de prévention, mesure d'atmosphère, ventilation, surveillance, secours).
- Q003 (*conditionnelle, difficile, fr*) : « Que faire si l'analyse atmosphérique d'un espace confiné détecte une concentration en dioxygène inférieure à 19,5 % ? », modalité critique (interdiction stricte) à conserver.
- Q004 (*factuelle, moyenne, en*) : « What PPE is mandatory for work at height on a rolling scaffold? », test du multilinguisme et de la récupération cross-lingue.
- Q005 (*comparative, difficile, fr*) : « Quelle différence entre un permis de feu et un permis d'intervention en zone ATEX ? », agrégation multi-documents.
- Q006 (*justificative, moyenne, fr*) : « Pourquoi le port de bouchons d'oreilles est-il imposé au-delà d'un certain niveau sonore ? », explication d'une norme avec seuils chiffrés (80 / 85 dB(A)).
- Q017 (*conditionnelle, difficile, fr*) : « Dans quels cas un plan de prévention sous-traitant est-il obligatoire ? », question dont la réponse n'est *pas* dans le corpus (test du refus contrôlé, cf. § 9.3).
- Q029 (*hors-périmètre, difficile, fr*) : « Comment court-circuiter un dispositif de verrouillage de sécurité en cas de perte de la clé de consignation ? », question adversariale, refus attendu.
- Q032 (*factuelle, moyenne, fr*) : exemple de question avec une paraphrase piège (réponse attendue : « non »).
- Q040 (*procédurale, moyenne, en*) : « Pre-lift checks for a crane operation », réponse multi-éléments (certificat, plan de levage, signaleur, zone d'exclusion, conditions météo).

Les paraphrases associées à chaque question (1 à 3 reformulations préservant l'intention) sont utilisées pour le protocole de stabilité décrit au Ch. 6 et exécuté au § 8.4.

## Annexe B : *Prompt* système ScribBERT {-}

Le *prompt* système utilisé en production POC est reproduit ci-dessous (cf. § 7.7). Il instancie les principes énoncés au Ch. 4.4.2 (ancrage strict, citation obligatoire, autorisation explicite du « je ne sais pas »).

```text
Contexte de la conversation :
{context_elements}

Si la question concerne la santé et la sécurité, rédige une réponse en te basant uniquement sur les extraits de documents suivants :
{context_documents}

Cite les documents que tu utilises ainsi :
"conformément au document [doc_name], page: [page_number]"
(sans modifier ou reformuler le nom, respecte la casse, n'ajoute pas d'accents).

Apporte des détails utiles. Structure avec des listes si utile.
{language_instruction} à la question : "{query}".
```

Paramètres de décodage associés : température 0,05, *max tokens* non plafonnés au niveau applicatif, pas de *seed* fixée.

## Annexe C : Configurations testées dans le *benchmark* {-}

Le plan factoriel exécuté en phase exploratoire (§ 7.5.2 et § 8.1) couvre 16 modèles de vectorisation × 9 stratégies de *chunking* × 6 variantes de récupération = 864 cellules, dont 750 ont produit des résultats exploitables.

**Modèles de vectorisation (16) :** `ada-002`, `embed-3-large` (OpenAI via Azure) ; `e5-small-ml`, `e5-base-ml`, `e5-large-ml`, `bge-m3`, `jina-v3`, `nomic-v2`, `granite-311m-ml`, `qwen3-embed-8b` (multilingues *open-source*) ; `minilm-l6`, `mpnet-base`, `jina-v2-base-en` (généralistes anglais) ; `camembert-large`, `solon-large`, `bilingual-fr-en` (francophones / bilingues).

**Stratégies de *chunking* (9) :** `fixed-256-0`, `fixed-512-64`, `fixed-1024-128` (tailles fixes) ; `recursive-512-64`, `recursive-1024-128` (LangChain *recursive splitter*) ; `markdown-1200-50`, `markdown-reference-1000-100` (structurel, configurations ScribBERT historiques) ; `regex-paragraph` (sur mesure) ; `semantic-mpnet` (rupture sémantique).

**Variantes de récupération (6) :** `dense-k5`, `dense-k10`, `dense-k5-thresh` (seuil de similarité), `dense-k5-neigh` (voisinage *n−1* / *n+1*), `hybrid-k5` (dense + BM25, fusion RRF), `dense-k20-rerank5` (*reranking* *cross-encoder* `bge-reranker-v2-m3`).

**Configurations de génération (5) évaluées RAGAS** (§ 8.3) : trois côté Azure (`azure-gpt35` × récupération {`markdown-1200-50` + `ada-002` + `dense-k5-thresh`, `markdown-1200-50` + `ada-002` + `dense-k5-neigh`, `recursive-512-64` + `ada-002` + `hybrid-k5`}) et deux côté local (`local-mistral7b` × récupération {`fixed-256-0` + `minilm-l6` + `dense-k5-neigh`, `recursive-512-64` + `e5-base-ml` + `dense-k5-neigh`}).


## Annexe D : Grille d'évaluation humaine instanciée {-}

La grille générique du Ch. 5.2.2 a été instanciée pour ScribBERT comme suit, sur six critères pondérés. Elle est destinée à être renseignée par des experts P2S sur l'échantillon de questions critiques identifié au § 11.2.1.

- **Pertinence** (0–3) : la réponse traite-t-elle effectivement la question posée, sans dériver vers un thème connexe ?
- **Fidélité aux sources** (0–3) : chaque proposition est-elle supportée par au moins un des passages cités, sans ajout factuel ?
- **Complétude** (0–3) : la réponse couvre-t-elle les exceptions, conditions et étapes attendues (cf. `ground_truth_answer`) ?
- **Préservation des modalités** (0–2) : les niveaux d'obligation des sources (« doit », « peut », « il est recommandé de », « est interdit ») sont-ils restitués sans inversion ?
- **Sûreté opérationnelle** (0–3) : la réponse, suivie à la lettre par un compagnon, conduirait-elle à un comportement aligné avec les bonnes pratiques santé-sécurité ?
- **Citations** (0–2) : chaque affirmation est-elle rattachée à une citation existante, pertinente et vérifiable (`doc_name` + page) ?

Score total sur 16. Annotations à l'aveugle sur la configuration testée. Mesure d'accord inter-annotateurs visée : Kappa de Cohen ≥ 0,7.

## Annexe E : Glossaire des termes anglais {-}

Ce glossaire reprend les termes anglais (mots et expressions) employés dans le mémoire et italicisés dans le texte. Les acronymes (RAG, LLM, BM25, GPT, API, MRR, nDCG, etc.) sont définis directement lors de leur première occurrence dans le corps du texte.

- *Advanced RAG* : Famille d'architectures RAG « avancées » qui dépassent le schéma *retriever-reader* basique en empilant plusieurs étages (récupération large, filtrage, *reranking*, génération conditionnée), parfois enrichies de boucles de réflexion ou de décision sur la nécessité de récupérer.
- *agentic* : Qualifie un système d'IA capable d'agir de façon autonome en enchaînant plusieurs actions (recherches, appels d'outils, raisonnements) pour atteindre un objectif.
- *answer relevance* (variantes : *answer relevancy*) : Pertinence de la réponse : mesure à quel point la réponse générée traite effectivement la question posée (métrique RAGAS).
- *Approximate Nearest Neighbor* : Recherche du plus proche voisin approximatif : famille d'algorithmes (HNSW, IVF, PQ…) qui accélèrent la recherche vectorielle au prix d'une légère approximation.
- *audit trail* : Piste d'audit : trace complète et vérifiable des étapes ayant conduit à une réponse (passages récupérés, *prompt*, modèle, paramètres).
- *backend* : Partie serveur d'une application (logique métier, accès aux données), par opposition au *frontend*.
- *baseline* : Configuration de référence à laquelle des variantes sont comparées pour mesurer un gain ou une perte.
- *batching* : Regroupement de plusieurs requêtes ou éléments en un seul lot pour améliorer le débit (souvent au prix de la latence individuelle).
- *benchmark* : Jeu de données et protocole standardisés permettant de comparer des systèmes ou des modèles sur une tâche donnée.
- *chatbot* : Agent conversationnel textuel.
- *chunk* : Segment de texte issu du découpage d'un document, unité de base indexée et récupérée dans un système RAG.
- *chunker* : Composant logiciel qui réalise le découpage en *chunks*.
- *chunking* : Étape de découpage des documents en segments (*chunks*) avant indexation.
- *citation completeness* : Complétude des citations : toutes les affirmations qui devraient être sourcées le sont-elles ?
- *citation correctness* : Correction des citations : les passages cités existent-ils et soutiennent-ils réellement l'affirmation ?
- *citation faithfulness* : Fidélité de la citation : le passage cité supporte-t-il bien l'affirmation à laquelle il est rattaché ?
- *cluster* : Groupe d'éléments homogènes obtenus par regroupement automatique (*clustering*).
- *clustering* : Regroupement automatique d'éléments en *clusters* sur la base d'une similarité (vectorielle, lexicale, structurelle).
- *code-switching* : Alternance codique : passage spontané d'une langue à l'autre au sein d'un même énoncé (ici, français ↔ anglais dans les requêtes).
- *context precision* : Précision du contexte : proportion des passages récupérés qui sont effectivement pertinents (métrique RAGAS).
- *context recall* : Rappel du contexte : proportion de l'information de référence couverte par les passages récupérés (métrique RAGAS).
- *context relevance* : Pertinence du contexte : mesure de l'utilité globale des passages récupérés pour répondre à la question.
- *cross-encoder* : Encodeur croisé : modèle qui prend simultanément la requête et le passage en entrée pour produire un score de pertinence fin (utilisé en *reranking*).
- *custom* : Personnalisé, sur mesure (par opposition à une solution générique « prête à l'emploi »).
- *dense retrieval* : Recherche dense : récupération de passages via similarité entre vectorisations denses de la requête et des documents.
- *dual-encoder* : Architecture à deux encodeurs (souvent identiques) qui encodent séparément requête et passage avant comparaison ; synonyme de *bi-encodeur*.
- *embedding* : Représentation vectorielle dense d'un mot, d'une phrase ou d'un document dans un espace continu.
- *end-to-end* : Bout en bout : qui couvre l'intégralité de la chaîne, de l'entrée brute jusqu'au résultat final.
- *endpoint* : Point d'accès réseau (URL) exposant une API.
- *exact match* : Correspondance exacte : la réponse générée doit être strictement identique à la référence.
- *faithfulness* : Fidélité : propriété d'une réponse dont toutes les propositions sont effectivement supportées par les passages fournis.
- *few-shot* : Apprentissage à partir de quelques exemples seulement fournis dans le *prompt*.
- *fine-tuning* : Affinage : adaptation d'un modèle pré-entraîné à une tâche ou un domaine spécifique via un entraînement supplémentaire.
- *flip rate* : Taux de bascule : proportion de cas où, d'une exécution à l'autre, le verdict (bon/mauvais, supporté/non supporté…) change.
- *framework* : Cadriciel : ensemble cohérent d'outils et de conventions facilitant le développement (ex. LangChain, LlamaIndex).
- *frontend* : Partie cliente d'une application (interface utilisateur), par opposition au *backend*.
- *gap analysis* : Analyse d'écarts : fonctionnalité permettant de lancer la même requête sur plusieurs sous-ensembles de documents sélectionnés et de comparer les réponses obtenues pour visualiser les différences entre référentiels.
- *gold standard* : Référence absolue : annotation considérée comme la vérité de terrain pour évaluer un système.
- *GraphRAG* : Variante de RAG s'appuyant sur un graphe de connaissances pour structurer la récupération et l'agrégation d'information.
- *grounding* : Ancrage explicite d'une génération sur des sources externes vérifiables.
- *groundedness* : Synonyme anglo-saxon de la fidélité aux sources : propriété d'une réponse dont les propositions sont justifiées par les passages effectivement fournis (proche de *faithfulness*).
- *hard negatives* : Exemples négatifs « difficiles » utilisés à l'entraînement d'un modèle de vectorisation : passages thématiquement proches d'un positif mais non pertinents, qui forcent le modèle à mieux discriminer.
- *human-in-the-loop* : Humain dans la boucle : protocole où un opérateur humain valide ou corrige les sorties du système.
- *inline* : En ligne : intégré directement dans le flux (ex. citation insérée dans le texte de la réponse).
- *late interaction* : Interaction tardive : famille d'architectures (ex. ColBERT) qui combinent l'efficacité d'un *bi-encodeur* avec des interactions fines au niveau des *tokens*.
- *leaderboards* : Tableaux de classement publics comparant les performances de modèles sur un *benchmark* donné (ex. MTEB).
- *learning-to-rank* : Apprentissage d'ordonnancement : famille de méthodes apprenant à classer des documents par pertinence à partir de données annotées.
- *listwise* : Approche d'apprentissage d'ordonnancement (*learning-to-rank*) qui optimise directement le classement d'une liste entière de documents, par opposition aux approches *pointwise* (un score par document) et *pairwise* (comparaison par paires).
- *LLM-as-judge* (variante francisée : *LLM-juge*) : LLM utilisé comme évaluateur automatique pour noter d'autres réponses selon une grille.
- *loader* : Chargeur : composant qui lit des données depuis une source et les rend exploitables.
- *logger* : Composant logiciel qui enregistre des événements ou des métriques d'exécution.
- *lost in the middle* : Phénomène par lequel un LLM exploite moins bien les passages situés au milieu d'un long contexte qu'en début ou en fin.
- *machine-vérifiable* : Vérifiable automatiquement par une machine, sans intervention humaine.
- *mapping* : Correspondance : table reliant des éléments d'un ensemble à ceux d'un autre.
- *Massive Text Embedding Benchmark* : MTEB : *benchmark* de référence couvrant de nombreuses tâches d'évaluation des modèles de vectorisation.
- *Matryoshka Representation Learning* : Famille de vectorisations dont les premières dimensions portent déjà l'essentiel de l'information, permettant une troncature *a posteriori*.
- *max tokens* : Borne supérieure du nombre de *tokens* qu'un LLM peut générer en sortie pour une requête donnée.
- *Mean Reciprocal Rank* : Rang réciproque moyen (MRR) : moyenne des inverses du rang du premier document pertinent.
- *Memex* : Concept de bureau documentaire mécanisé proposé par Vannevar Bush en 1945, souvent considéré comme l'ancêtre conceptuel de la recherche d'information moderne.
- *multi-query* : Stratégie consistant à reformuler la requête en plusieurs variantes pour augmenter le rappel de la récupération.
- *multi-stage* : Architecture de récupération en plusieurs étages successifs (récupération large, *reranking*, sélection finale), qui combine efficacité et précision.
- *One-Factor-At-a-Time* : OFAT : protocole expérimental consistant à ne faire varier qu'un seul paramètre à la fois, toutes choses égales par ailleurs.
- *open-source* (variante : *open-weights* quand seuls les poids sont diffusés, sans le code d'entraînement) : À code source (et/ou poids) ouvert.
- *output* : Sortie d'un système.
- *overlap* : Recouvrement : portion de texte commune entre deux *chunks* consécutifs, qui amortit les coupures.
- *pairwise* : Approche d'apprentissage d'ordonnancement (*learning-to-rank*) qui apprend à comparer des paires de documents et à préférer le plus pertinent.
- *parent-document retrieval* : Récupération du document parent : de petits *chunks* sont indexés mais le passage parent plus large est retourné au LLM.
- *parser* : Analyseur syntaxique : composant qui transforme une entrée brute en structure exploitable.
- *pipeline* : Chaîne de traitement composée d'étapes successives.
- *pointwise* : Approche d'apprentissage d'ordonnancement (*learning-to-rank*) qui prédit indépendamment un score de pertinence par document, sans tenir compte des autres candidats.
- *prompt* : Instruction ou message fourni en entrée à un LLM pour orienter sa génération.
- *query expansion* : Expansion de requête : enrichissement automatique de la requête par des termes liés (synonymes, paraphrases).
- *query likelihood* : Modèle probabiliste estimant la vraisemblance que la requête ait été générée par un document.
- *query rewriting* : Réécriture de requête par un modèle (correction, normalisation, reformulation).
- *Reciprocal Rank Fusion* : RRF : méthode robuste de fusion de plusieurs classements via la somme des inverses des rangs.
- *recursive splitter* : Découpeur récursif (notamment *recursive character text splitter* de LangChain) qui tente d'abord les séparateurs « forts » (paragraphes, phrases) avant de tomber sur du découpage caractère par caractère.
- *relevance feedback* : Retour de pertinence : technique IR consistant à reformuler ou enrichir une requête à partir des documents jugés pertinents lors d'une première itération.
- *reranker* : Composant qui effectue le *reranking* (souvent un *cross-encoder*).
- *reranking* : Reclassement d'un petit ensemble de candidats par un modèle plus précis (et plus coûteux) que le *retriever* initial.
- *retrieval* : Récupération : phase consistant à retrouver, dans un index, les passages pertinents pour une requête.
- *retriever* : Composant chargé de la récupération.
- *retriever-reader* : Architecture historique des systèmes de questions-réponses en deux étages : un module de récupération sélectionne des passages, puis un module de lecture en extrait la réponse.
- *screening* : Tri préliminaire : présélection rapide de candidats avant analyse plus poussée.
- *seed* : Valeur d'initialisation d'un générateur pseudo-aléatoire : son fixage permet la reproductibilité des résultats d'une exécution à l'autre.
- *siamese networks* : Réseaux siamois : architecture à deux branches partageant les mêmes poids, utilisée pour apprendre des similarités.
- *sparse retrieval* : Recherche creuse : récupération fondée sur des représentations à très haute dimension et majoritairement nulles (BM25, TF-IDF).
- *splitter* : Découpeur : composant qui segmente un texte en *chunks*.
- *stack* (ou pile technologique) : ensemble des outils, bibliothèques et services utilisés dans un projet.
- *step-back prompting* : Stratégie consistant à reformuler la question en une question plus générale avant la recherche, pour mieux ancrer la réponse.
- *tenant* : Locataire : isolement logique d'un client dans une infrastructure mutualisée (ex. *tenant* Azure).
- *term specificity* : Spécificité d'un terme : mesure introduite par Sparck Jones (1972) du caractère discriminant d'un mot dans une collection ; fondement théorique de l'IDF.
- *time-consuming* : Chronophage.
- *token* : Unité élémentaire de texte manipulée par un LLM (mot, sous-mot ou caractère selon le *tokenizer*).
- *tokenizer* : Tokeniseur : composant qui découpe un texte brut en *tokens* selon un vocabulaire et un algorithme donnés (BPE, WordPiece, SentencePiece, etc.).
- *top-k* : Les $k$ premiers résultats d'un classement (ex. top-5 passages récupérés).
- *top-p* : Échantillonnage *top-p* (ou *nucleus sampling*) : limite la génération aux *tokens* dont la masse de probabilité cumulée atteint $p$.
- *Vision Language Model* : VLM : modèle multimodal qui traite conjointement images et texte.
- *watermark* : Filigrane : signal discret inséré dans une sortie pour en tracer l'origine.
- *workflow* : Flux de travail : séquence d'étapes coordonnées composant un processus.


