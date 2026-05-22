# Mémoire — Évaluation de la cohérence et de la fiabilité d'un système RAG (cas d'usage : ScribBERT)

> Document de travail (version brouillon). Les éléments marqués **[À compléter]** sont des placeholders (chiffres, exemples internes, schémas, références exactes).

## Introduction

Les modèles de langage ont profondément changé notre rapport à l'information. En l'espace de quelques années, on est passé de systèmes incapables de produire une phrase cohérente à des modèles qui rédigent avec une aisance parfois troublante (assistants conversationnels, génération de contenu, recherche d'information intelligente). Le "boom de l'IA" n'est pas qu'un effet de mode : il transforme concrètement la manière dont on produit, partage et exploite la connaissance dans les organisations.

Mais cette puissance a un revers. Les **LLMs** (Large Language Models) souffrent de limites bien connues : ils **hallucinent** (c'est-à-dire qu'ils inventent des informations sans que rien ne le signale), ils ne citent pas leurs sources de façon fiable, et ils peinent à intégrer des connaissances récentes ou spécifiques à un domaine. Dans un contexte où la précision compte, et a fortiori quand elle engage la sécurité des personnes, ces défauts deviennent rédhibitoires.

C'est pour contourner ces limites qu'une approche hybride s'est imposée : le **Retrieval-Augmented Generation** (RAG), qui couple un mécanisme de **recherche documentaire** à un modèle génératif.[@Lewis2020] L'idée est simple sur le papier : plutôt que de laisser le modèle "inventer" à partir de sa mémoire interne, on lui fournit des extraits de documents pertinents, et on lui demande de s'y appuyer pour formuler sa réponse. En pratique, c'est nettement plus complexe qu'il n'y paraît, et c'est l'objet de ce mémoire.

ScribBERT est né de cette idée. C'est un chatbot RAG que j'ai développé pendant mon alternance au département P2S de Bouygues Travaux Publics, pour permettre aux collaborateurs d'interroger en langage naturel les référentiels santé-sécurité internes. Les premiers résultats ont eu un vrai effet "ouahou" : le système répondait de façon pertinente à des questions sur lesquelles un moteur de recherche classique aurait été inutile.

Seulement voilà : dans le domaine de la santé-sécurité, un effet "ouahou" ne suffit pas. La qualité de l'information transmise engage directement la sécurité des compagnons sur les chantiers. Une réponse plausible mais fausse, une procédure mal citée, une obligation transformée en simple recommandation. Les conséquences potentielles dépassent l'enjeu technique. Chaque réponse doit être exacte, fondée sur les bonnes sources, et vérifiable. Cette exigence m'a rapidement confronté à une question que j'ai trouvée à la fois passionnante et frustrante : **comment évaluer la cohérence et la fiabilité d'un système RAG ?**

La réponse n'est pas triviale. Évaluer un RAG, ce n'est pas comme évaluer un moteur de recherche classique (où l'on vérifie que les bons documents remontent), ni comme évaluer un LLM seul (où l'on juge la qualité du texte). C'est évaluer une **chaîne**, et les erreurs peuvent se situer à chaque maillon : mauvais découpage des documents, mauvaise recherche, mauvaise exploitation du contexte par le modèle. Comment savoir *où* ça déraille ?

L'objectif de ce mémoire est de proposer une méthode d'évaluation rigoureuse et reproductible pour mesurer la pertinence, la cohérence et la fiabilité d'un système RAG. Concrètement, il s'agit d'identifier des critères d'évaluation adaptés, d'explorer et comparer différentes métriques, d'étudier l'impact des paramètres de la pipeline RAG, et de mettre en œuvre ce protocole sur ScribBERT. L'ambition est que ce cadre puisse servir au-delà de ce cas d'usage, dans d'autres contextes documentaires.

La démarche s'organise en trois parties :

- **Partie I** — Cadre conceptuel et théorique : les fondements du RAG, l'histoire de la recherche d'information, et les notions de pertinence et de cohérence qui sous-tendent l'évaluation.
- **Partie II** — Méthodologie d'évaluation : construction du protocole, choix des métriques, conditions expérimentales.
- **Partie III** — Application et discussion : mise en œuvre sur ScribBERT, résultats, et recommandations.

\newpage

## Présentation du contexte : Bouygues Travaux Publics et le projet ScribBERT

Avant d'entrer dans le vif du sujet technique, il est nécessaire de poser le décor : l'entreprise, le département, et les contraintes concrètes qui ont façonné ce projet.

### Le groupe Bouygues et la branche Construction

Le **groupe Bouygues** est un groupe industriel français diversifié, fondé en 1952 par Francis Bouygues. Il s'organise aujourd'hui autour de plusieurs métiers : la construction (Bouygues Construction, Bouygues Immobilier, Colas), les médias (TF1), les télécommunications (Bouygues Telecom) et les services à l'énergie et à l'industrie (Equans, intégré au groupe en 2022). En 2024, le groupe employait environ **200 000 collaborateurs** dans plus de 80 pays.

Au sein de ce groupe, **Bouygues Construction** rassemble les activités de bâtiment, de travaux publics et d'énergies/services. Elle se décompose elle-même en plusieurs entités opérationnelles, dont **Bouygues Travaux Publics** (Bouygues TP), qui constitue le pôle de référence pour les ouvrages de génie civil complexes.

### Bouygues Travaux Publics : périmètre et activités

Bouygues Travaux Publics est la filiale du groupe spécialisée dans la réalisation de grandes infrastructures de génie civil : tunnels, ponts, ouvrages maritimes et fluviaux, centrales nucléaires. Elle compte environ 10 000 collaborateurs sur des chantiers en France et à l'international (Grand Paris Express, EPR de Hinkley Point C, projets en Asie, Amérique du Nord et Émirats arabes unis), avec un siège à Guyancourt.

Cette activité présente trois caractéristiques structurantes pour ce mémoire :

1. **Exposition aux risques élevée** : travaux en hauteur, en milieu confiné, à proximité d'engins lourds ou en environnement nucléaire, chacun associé à des procédures de sécurité spécifiques.
2. **Production documentaire hétérogène** : standards groupe, procédures filiales, modes opératoires chantier, normes externes (NF, EN, ISO), réglementations variables selon les pays.
3. **Organisation décentralisée** : chaque chantier dispose d'une équipe dédiée avec une certaine autonomie opérationnelle.

\newpage

### Le département P2S (Prévention Santé-Sécurité)

Au sein de Bouygues TP, le département **P2S (Prévention Santé-Sécurité)** est entre autres en charge de la définition, de la diffusion et du suivi de la politique santé-sécurité de l'entreprise. Ses missions couvrent notamment :

- la **rédaction et la maintenance des référentiels** (procédures, standards, référentiels) ;
- l'**accompagnement opérationnel** des équipes chantier (audits, visites) ;
- l'**analyse des accidents et presqu'accidents** ;
- le **reporting** et le pilotage des indicateurs santé-sécurité (taux de fréquence, taux de gravité, nombre d'heures travaillées, nombre d'accidents à haut potentiel (HiPo)) ;
- la **veille réglementaire** française et internationale.

L'enjeu opérationnel central est de **rendre l'information de sécurité accessible, exacte et applicable au bon moment**, c'est-à-dire dans le contexte de la situation de travail. Or les retours terrain montrent qu'une part significative des situations à risque ne provient pas d'une absence de référentiel, mais d'une **difficulté à retrouver/respecter la bonne information**. Les statistiques d'utilisation du SharePoint interne le confirment de façon assez parlante : le temps moyen passé par un utilisateur sur la plateforme documentaire est d'environ 2 minutes 30, ce qui correspond au temps nécessaire pour localiser et télécharger le bon document. La recherche ne s'arrête pas là : l'utilisateur poursuit ensuite dans le document téléchargé, souvent en croisant plusieurs sources, ce qui allonge considérablement l'effort total. Ceux qui peinent à identifier le bon document y passent plutôt autour de 10 minutes. C'est ce genre de friction qui a motivé le projet ScribBERT.

### Le projet ScribBERT

C'est de ce constat qu'est né **ScribBERT**. L'idée initiale vient d'Aurélie Janssens (mon ancienne tutrice) et de Flavien Martin (mon tuteur actuel au moment de la rédaction), qui cherchaient des cas d'usage concrets de l'IA appliquée à la santé-sécurité chez Bouygues TP. Le besoin originel était très opérationnel : simplifier la réponse aux appels d'offre. Les clients soumettent des questionnaires Santé-Sécurité détaillés qu'il faut remplir en s'appuyant sur les référentiels internes, un exercice chronophage qui consiste essentiellement à retrouver la bonne information dans les bons documents. L'idée d'un assistant capable de répondre à ces questions en langage naturel, en citant les passages pertinents, s'est imposée assez naturellement. De là, le périmètre s'est élargi : si le système peut répondre aux questions des clients, il peut tout aussi bien répondre aux questions des collaborateurs au quotidien. L'ambition est alors devenue celle d'un outil qui permette à n'importe quel collaborateur de poser une question et d'obtenir une réponse synthétique, sourcée, fondée sur les référentiels validés du département P2S.

\newpage

Techniquement, ScribBERT repose sur une architecture **RAG** (Retrieval-Augmented Generation). Les principes directeurs, posés dès le début du projet, étaient les suivants :

- **Ancrage strict** sur les documents internes validés (pas de réponse sans source) ;
- **Traçabilité** systématique des passages cités, avec lien vers le document d'origine ;
- **Confidentialité** : hébergement et traitement compatibles avec la sensibilité des documents internes ;
- **Évaluabilité** : conception du système pensée pour être mesurable, ce qui constitue précisément l'objet de ce mémoire.

Le projet a été développé dans le cadre des deux dernières années de mon alternance qui s'est déroulée sur trois ans au sein du département P2S. La supervision a été assurée conjointement par **Flavien Martin** (tuteur métier, santé-sécurité) et **Julien Larseneur** (tuteur technique, équipe Data/IA Bouygues TP). Cette complémentarité s'est révélée précieuse : Flavien formulait les besoins métier, Julien m'aidait à les théoriser et à les traduire en choix d'architecture. Le périmètre fonctionnel initial couvre l'ensemble des référentiels santé-sécurité du siège de Bouygues TP, soit environ 130 documents PDF internes. Ce chiffre monte à 190–200 documents si l'on intègre les référentiels clients et réglementaires (ENBRIDGE, PAS 91, OSHA, etc.) (cf. Ch. 7).

### Implications pour ce mémoire

La nature de l'entreprise et du département a directement influencé la problématique d'évaluation traitée ici. Quelques points méritent d'être soulignés car ils reviennent constamment dans la suite :

- La **criticité métier** impose des exigences de fiabilité importantes. Un assistant marketing/communication qui se trompe, c'est gênant ; un assistant santé-sécurité qui se trompe, c'est potentiellement dangereux.
- L'**hétérogénéité documentaire** rend les benchmarks publics insuffisants. On ne peut pas évaluer ScribBERT avec les jeux de données académiques classiques, il a fallu construire un corpus de test interne.
- Les **contraintes de confidentialité** orientent les choix techniques (préférence pour des modèles hébergeables en interne, ou disponible en espace sécurisé).
- Le caractère **opérationnel** du déploiement (avec des utilisateurs réels, dont certains enthousiastes et d'autres méfiants vis-à-vis de l'IA) impose de considérer non seulement la performance moyenne mais aussi la stabilité et la gestion des cas limites. Les premiers retours utilisateurs ont d'ailleurs confirmé ce point : tout le monde reconnaît l'intérêt de la solution, mais la peur de l'erreur reste présente, et légitime : en phase de POC, certaines réponses se sont avérées incorrectes ou incomplètes, ce qui a renforcé la nécessité d'un cadre d'évaluation solide avant tout déploiement élargi.

\newpage

# PARTIE I — Cadre conceptuel et état de l'art

Cette première partie replace les systèmes de **Retrieval-Augmented Generation (RAG)** dans l'histoire des méthodes de recherche d'information. Elle vise ensuite à formaliser les notions de **pertinence** et de **cohérence/fidélité** qui seront au cœur du protocole d'évaluation.

Deux constats structurent cette partie :

1. Un RAG n'est pas "un LLM + des documents". C'est une **chaîne de décision** (découpage, indexation, recherche, assemblage du contexte, génération) dont les erreurs/imprécisions s'additionnent parfois.
2. Les critères d'évaluation de l'IR (recherche d'information) classique et ceux des LLMs ne se recouvrent pas. On peut avoir un excellent score de retrieval et une réponse finale fausse.

## Chapitre 1 — De la recherche documentaire à la recherche sémantique

### 1.1. Brève histoire de la recherche d'information : du lexical au probabiliste

Avant de parler de RAG, il faut comprendre d'où vient la recherche d'information, parce que les systèmes RAG en héritent grandement, y compris dans leurs limites.

La recherche d'information (IR) s'est construite autour d'un problème en apparence simple : étant donné un besoin (une requête) et une collection de documents, comment ordonner ces documents par pertinence ?[@Manning2008] L'idée d'un accès mécanisé à l'information remonte à l'après-guerre, avec le concept de *Memex* imaginé par Vannevar Bush.[@Bush1945]

Les premières approches opérationnelles étaient **lexicales** : un document est un sac de mots, une requête est une contrainte sur ces mots. Le modèle booléen (AND/OR/NOT) est le plus élémentaire : explicable, contrôlable, mais il ne classe pas les résultats et ne gère pas bien les besoins "graduels".

L'IR moderne s'est ensuite structurée autour de la notion de **ranking** et d'évaluation systématique. Le paradigm de Cranfield a joué un rôle déterminant : constituer un corpus, un ensemble de requêtes, et des jugements de pertinence pour comparer des systèmes.[@Cleverdon1967] Plus tard, les campagnes TREC ont industrialisé cette logique d'évaluation à grande échelle.[@VoorheesHarman2005]

Les modèles vectoriels ont ensuite introduit une représentation plus graduelle : documents et requêtes sont représentés comme des vecteurs, et la similarité est souvent mesurée via un calcul de similarité cosinus. Une pondération bien connue est le TF-IDF, qui combine une mesure de fréquence locale (*term frequency*) et une mesure de rareté globale (*inverse document frequency*). Formellement :

$$\mathrm{tfidf}(t, d) = \mathrm{tf}(t,d) \times \log\left(\frac{N}{\mathrm{df}(t)}\right)$$

où $N$ est le nombre total de documents et $\mathrm{df}(t)$ le nombre de documents contenant le terme $t$.

L'idée d'IDF comme signal de discrimination d'un terme remonte à des travaux fondateurs sur le *term specificity*.[@SparckJones1972] Le **vector space model** (VSM) popularisé par Salton et al. a ensuite fourni un cadre pratique et encore omniprésent pour pondérer et comparer requêtes et documents.[@Salton1975]

À partir des années 1990-2000, les approches probabilistes (notamment **BM25**) se sont imposées comme standard industriel : elles offrent un excellent compromis performance/simplicité et une robustesse sur des corpus variés.[@RobertsonZaragoza2009] BM25 peut être vu comme une amélioration de TF-IDF qui normalise explicitement par la longueur du document et introduit des hyperparamètres supplémentaires.

$$\mathrm{BM25}(q, d) = \sum_{t \in q} \mathrm{idf}(t) \cdot \frac{\mathrm{tf}(t,d) \cdot (k_1+1)}{\mathrm{tf}(t,d) + k_1 \cdot \left(1-b + b\cdot \frac{|d|}{\mathrm{avgdl}}\right)}$$

avec $k_1$ et $b$ des paramètres de calibration, $|d|$ la longueur du document et $\mathrm{avgdl}$ la longueur moyenne.

Enfin, une autre famille importante, très utilisée en pratique, est celle des **modèles de langage pour l'IR**, où l'on estime la probabilité qu'un document génère une requête (approches *query likelihood*), et où l'on utilise des techniques de lissage et de feedback pseudo-pertinent.[@PonteCroft1998; @LavrenkoCroft2001]

Ces modèles "classiques" (BM25, query likelihood, variantes) restent extrêmement compétitifs, notamment sur des corpus techniques où les indices lexicaux (références, numéros de procédure, intitulés normatifs) apportent des signaux précieux.

#### 1.1.1. Évaluer un système de recherche : pourquoi les métriques comptent

Les pipelines RAG héritent directement de l'IR un point crucial : **l'évaluation dépend du protocole**. La performance d'un moteur ne peut pas être "résumée" par un seul score sans préciser la tâche, la définition de pertinence, le nombre de résultats considérés ($k$), et la nature binaire ou graduée des jugements.[@Manning2008; @BaezaYates2011; @Croft2010; @VoorheesHarman2005]

Dans sa forme la plus simple, on distingue :

- la **précision** (proportion de résultats pertinents parmi les résultats retournés),
- le **rappel** (proportion des résultats pertinents retrouvés parmi tous les pertinents existants).

En recherche classée, on utilise des métriques au rang : Precision@k, Recall@k, et des métriques de classement global comme **nDCG** (qui gère naturellement la pertinence graduée).[@JarvelinKekalainen2002]

Ce point est central pour le mémoire : si l'on change la définition de pertinence (thématique vs situationnelle), les scores de retrieval changent, et la qualité perçue aussi.

#### 1.1.2. Feedback, reformulation et learning-to-rank

Les systèmes IR peuvent aussi reformuler la requête pour améliorer les résultats. Le *relevance feedback* et ses variantes (pseudo-relevance feedback, expansion de requête) augmentent le rappel (*recall*) mais peuvent introduire du bruit.[@Rocchio1971] Dans un RAG, ce compromis est amplifié : une expansion mal calibrée risque de récupérer des passages thématiquement proches mais non applicables.

En parallèle, le **learning-to-rank** a permis d'apprendre des fonctions de classement à partir de données (clics, jugements), avec des approches *pointwise*, *pairwise* et *listwise*.[@Liu2009LTR] Les systèmes industriels combinent aujourd'hui un retrieval rapide, un reranking plus coûteux (souvent cross-encoder) et des signaux métier (popularité, fraîcheur). Le RAG s'insère dans cette logique multi-étage.

### 1.2. Limites du matching lexical

Les méthodes lexicales (booléen, TF-IDF, BM25) reposent sur une hypothèse forte : la pertinence est principalement capturable par la co-occurrence de termes entre requête et document. En pratique, cette hypothèse se heurte à des problèmes bien documentés, que j'ai pu observer directement lors des premières itérations de ScribBERT :

- **Synonymie** : deux textes peuvent décrire la même notion avec des termes différents. Dans notre corpus, "harnais antichute" et "EPI antichute" désignent la même chose, mais un matching lexical pur les traite comme des requêtes distinctes.
- **Polysémie** : un même terme peut renvoyer à des concepts différents selon le contexte (ex. "levage" en planification vs levage en opération terrain).
- **Morphologie et variations** : abréviations, variantes métier. Le jargon des chantiers est particulièrement riche en acronymes et en raccourcis que les référentiels n'utilisent pas toujours.
- **Requêtes complexes** : les utilisateurs posent rarement des mots-clés isolés. Ils expriment des intentions, des contraintes, des justifications ("que faire si…", "dans quel cas…", "quelles exceptions…"). Les signaux purement lexicaux sont mal équipés pour traiter ces formulations.

Dans un contexte technique et réglementaire, ces limites sont accentuées : le vocabulaire est spécialisé, la formulation est parfois normative, très théorique, et l'utilisateur peut utiliser un vocabulaire terrain différent de celui du référentiel.

Deux compléments sont importants pour comprendre pourquoi ces limites deviennent critiques dans un RAG :

- **Rappel vs précision** : un moteur lexical peut être très précis (peu de bruit) mais rater des passages formulés différemment ; inversement, il peut être rappelé mais ramener trop de textes "proches" sans être applicables. Le RAG transforme ce compromis en risque de génération : un passage légèrement hors-sujet peut suffire à entraîner une réponse erronée.
- **Correspondance d'intention** : la requête utilisateur exprime souvent une tâche (ex. "quels EPI obligatoires ?", "quelle procédure avant intervention ?"), et pas seulement un thème. Or les signaux lexicaux capturent mal la structure de tâche (conditions, exceptions, étapes).

### 1.3. Vers la recherche sémantique : représentations distribuées et embeddings

L'idée de dépasser le matching lexical n'est pas nouvelle. Dès les années 1990, l'**indexation sémantique latente** (LSI/LSA) projetait termes et documents dans un espace de dimension réduite via factorisation matricielle (SVD), dans l'espoir de capturer des corrélations entre termes et de réduire les problèmes de synonymie.[@Deerwester1990]

Le vrai tournant est venu avec les embeddings neuronaux. **Word2Vec** (Mikolov et al., 2013) a montré qu'on pouvait apprendre des représentations de mots denses, de faible dimension, où les mots apparaissant dans des contextes similaires se retrouvent proches dans l'espace vectoriel.[@Mikolov2013] GloVe a proposé une approche alternative combinant statistiques globales et optimisation locale.[@Pennington2014] Ces modèles avaient cependant une limite importante : un mot n'avait qu'un seul vecteur, indépendamment de la phrase. Le mot "levage" avait la même représentation qu'il désigne une opération de chantier ou une phase de planification.

Les modèles de type Transformers, et BERT en particulier, ont "résolu" ce problème en introduisant des **représentations contextualisées** : la représentation d'un token dépend désormais de la phrase entière.[@Vaswani2017; @Devlin2019] C'est ce qui a ouvert la voie à la recherche sémantique moderne.

Dans la pratique, l'usage IR/RAG requiert surtout des **embeddings de phrases/passages** (*sentence or passage embeddings*). Les approches de type **bi-encodeur** (ou dual-encoder) encodent requête et passage séparément, puis comparent leurs vecteurs (souvent cosinus ou produit scalaire). Sentence-BERT (SBERT) a été une contribution clé pour obtenir des embeddings de phrases efficaces via apprentissage contrastif et siamese networks.[@ReimersGurevych2019] Des travaux plus récents (ex. SimCSE) montrent que des schémas contrastifs simples peuvent déjà produire de très bons espaces d'embedding.[@Gao2021]

À l'inverse, les **cross-encoders** concatènent requête et passage et produisent un score de pertinence en tenant compte finement des interactions token-à-token, mais ils coûtent beaucoup plus cher à l'inférence. Ils sont souvent utilisés en **reranking** sur un petit nombre de candidats.[@NogueiraCho2019]

Enfin, des architectures intermédiaires (late interaction) comme **ColBERT** cherchent à concilier précision (interactions fines) et efficacité (indexation) via des représentations token-level compressées.[@KhattabZaharia2020]

### 1.4. Sparse, dense et hybride : familles de retrieval

En pratique, les systèmes de retrieval se rangent en trois grandes familles. Le *sparse retrieval* (BM25, TF-IDF), qui représente les documents dans un espace de très grande dimension. C'est rapide, et ça marche remarquablement bien sur des requêtes contenant des identifiants précis (numéros de procédure, références normatives). Le *dense retrieval* projette tout dans un espace compact d'embeddings, plus apte à capturer synonymie et paraphrase, mais plus "opaque". Et l'*hybride* combine les deux, ce qui est souvent la meilleure option quand le corpus mélange des requêtes techniques et des questions en langage naturel.

L'étape de retrieval peut également être suivie d'un *reranking* : on récupère d'abord un ensemble large de candidats (rapide), puis un modèle plus précis (souvent un cross-encoder) reclasse finement les passages. (J'y reviendrai au Chapitre 4)

Au-delà de cette typologie, un point technique essentiel pour les systèmes denses est l'indexation par recherche du **plus proche voisin approximatif** (Approximate Nearest Neighbor, ANN). À grande échelle, il est impossible de comparer une requête à tous les vecteurs. On utilise donc des structures (HNSW, IVF, PQ…) qui accélèrent la recherche au prix d'une approximation contrôlée.[@MalkovYashunin2018; @Johnson2019]

Cette approximation a une conséquence méthodologique : la performance de retrieval dépend non seulement du modèle d'embedding, mais aussi de la configuration de l'index (paramètres HNSW, quantization, etc.). Dans un protocole d'évaluation, il est donc important de distinguer :

- **erreur de représentation** (embedding inadapté),
- **erreur d'indexation** (approximation ANN),
- **erreur de formulation de requête** (query rewriting absent ou mal calibré).

### 1.5. Problématiques spécifiques à la sémantique en contexte technique

Tout ce qui précède s'applique à la recherche sémantique en général. Mais un corpus santé-sécurité pose des problèmes supplémentaires qui méritent d'être explicités.

La **criticité de l'erreur** est d'un autre ordre : une réponse plausible mais fausse n'est pas juste inutile, elle est potentiellement dangereuse. La **granularité** des sources est aussi un défi : un même thème peut être traité dans une règle générale groupe, une procédure filiale, et un mode opératoire chantier, avec des niveaux de détail et d'autorité différents (sans parler des documents clients et réglementaires).

Il faut ajouter des phénomènes fréquents dans les corpus internes et que les benchmarks académiques ne capturent pas : des procédures longues et composites où un chunk peut contenir les bons mots-clés mais être la mauvaise section ; des **niveaux d'obligation** subtils (la différence entre "recommandé" et "obligatoire", entre "interdit" et "déconseillé", peut avoir des conséquences très concrètes).

Tout cela fait que l'évaluation d'un RAG en contexte santé-sécurité ne peut pas se limiter à la proximité sémantique.

### 1.6. Limites des approches traditionnelles face aux LLMs

L'émergence des LLMs change la donne, et pas seulement du côté de la génération. Elle change aussi la nature des requêtes. L'utilisateur qui interroge un assistant comme ScribBERT n'écrit plus des mots-clés : il pose une question complète, souvent complexe et implicitement située dans un contexte ("que dois-je vérifier avant de commencer un travail en hauteur sur un échafaudage roulant ?"). Le système doit donc gérer des **intentions** (besoin d'explication, de comparaison, de décision) et pas seulement une adéquation thématique.

L'autre problème, plus piègeux, est celui de l'**hallucination**. Les LLMs peuvent produire des textes *cohérents sur la forme* tout en étant incorrects sur le fond.[@Maynez2020; @Ji2023] En contexte santé-sécurité, ce phénomène devient un risque opérationnel à part entière. C'est cette tension entre qualité apparente et fiabilité réelle qui justifie l'existence du RAG, et la nécessité de l'évaluer.

### 1.7. Neural IR et dense retrieval

Avec les modèles Transformers, le **dense retrieval** a pris son essor. L'idée est d'encoder requêtes et passages avec un bi-encodeur (deux BERT indépendants) et de les comparer par similarité vectorielle. DPR (Karpukhin et al., 2020) a montré que cette approche pouvait surpasser BM25 sur des benchmarks de QA ouverts.[@Karpukhin2020] Les gains suivants ont surtout été obtenus via des stratégies d'entraînement avec *hard negatives* et des travaux comme ORQA[@Lee2019ORQA] et ANCE[@Xiong2020ANCE], que je ne détaille pas ici.

La question pratique pour un cas comme ScribBERT est directe : **un modèle entraîné sur des données web généraliste est-il adapté à un vocabulaire métier ?** Le benchmark BEIR a montré une dégradation significative des performances hors domaine d'entraînement.[@Thakur2021BEIR] Cette question sera traitée en Partie II.

### 1.8. Du dense retrieval au RAG : la convergence historique

La trajectoire décrite dans ce chapitre, du lexical aux embeddings puis au dense retrieval, mène assez naturellement à l'idée de coupler un retriever dense à un modèle génératif. Rétrospectivement, la filiation paraît évidente ; sur le moment, chaque étape a nécessité des contributions distinctes.

Le paradigme *retriever-reader* a d'abord été popularisé par **DrQA** (Chen et al., 2017), puis ORQA[@Lee2019ORQA] et REALM[@Guu2020] ont progressivement intégré le retriever dans la boucle d'apprentissage.

**RAG** (Lewis et al., 2020) couplait un générateur BART à un retriever DPR, avec deux variantes (RAG-Sequence et RAG-Token).[@Lewis2020] **Fusion-in-Decoder** (Izacard & Grave, 2021) a ensuite montré qu'en injectant davantage de passages dans le décodeur, on pouvait encore améliorer les résultats.[@IzacardGrave2021]

Le RAG n'est pas une invention isolée mais l'aboutissement d'une lignée de recherche en IR.

## Chapitre 2 — Les fondements du RAG (Retrieval-Augmented Generation)

### 2.1. Principe général : génération augmentée par récupération

Le RAG, dans son principe, est assez intuitif : au lieu de laisser un modèle de langage répondre "de tête", on lui fournit des documents pertinents et on lui demande de s'en servir. Autrement dit, on le fait travailler comme le ferait un bon préventeur, en consultant la documentation avant de répondre.

Plus formellement, le Retrieval-Augmented Generation désigne une famille d'architectures où un modèle génératif produit une réponse en s'appuyant sur un contexte documentaire récupéré dynamiquement. C'est un entre-deux :

- un **moteur de recherche** retrouve des documents, mais ne produit pas de réponse rédigée ;
- un **LLM seul** rédige, mais peut inventer ou s'appuyer sur des connaissances obsolètes.

Le RAG combine les deux. Historiquement, cette idée s'inscrit dans la lignée des systèmes **retriever-reader** (DrQA, ORQA) où un module récupère des passages et un second les exploite.[@Chen2017DrQA; @Karpukhin2020]

Sur le plan formel, le RAG peut se modéliser comme un problème de génération conditionnelle où les passages récupérés jouent un rôle intermédiaire :

$$p(y\mid x)=\sum_z p(y\mid x,z)\,p(z\mid x)$$

où :
- $x$ est la **requête** de l'utilisateur,
- $z$ est un **passage** issu du corpus (variable latente : on ne l'observe pas directement, on l'infère),
- $y$ est la **réponse** générée.

La formule se lit ainsi : pour obtenir une réponse $y$ à la question $x$, on somme sur tous les passages $z$ possibles le produit de deux probabilités : celle que $z$ soit un bon passage pour cette question $p(z\mid x)$, et celle que le modèle génère $y$ à partir de ce passage $p(y\mid x,z)$.

En pratique, on ne peut pas parcourir tous les passages du corpus : on approxime cette somme en ne retenant qu'un petit nombre de passages (le top-$k$). C'est ce qui rend les choix de retrieval si importants : si le "bon" passage n'apparaît pas parmi les $k$ retenus, le modèle génère sa réponse sans l'information nécessaire.

### 2.2. RAG vs fine-tuning : choix méthodologiques

La question "pourquoi un RAG plutôt qu'un fine-tuning ?" est revenue plusieurs fois dans les discussions autour de ScribBERT, et le choix s'est fait assez naturellement, mais il mérite d'être explicité.

Le **fine-tuning** consiste à adapter les poids d'un modèle sur des données spécifiques. On obtient un modèle qui "sait" les choses directement, sans avoir besoin de consulter des documents au moment de la requête. En théorie ça a l'air cool. En pratique, dans un contexte comme le nôtre, c'est difficilement tenable : nos procédures évoluent régulièrement, et réentraîner un modèle à chaque mise à jour documentaire serait trop coûteux et non traçable (on ne saurait pas quelles sources le modèle utilise pour répondre).

Le **RAG**, à l'inverse, conserve un modèle généraliste et injecte du contexte documentaire à la volée. Pour mettre à jour un document, il "suffit" de réindexer. Et pour avoir d'où vient une réponse, il "suffit" d'inspecter les passages récupérés. 

Cela dit, le RAG ne nous interdit pas de faire du fine-tunning. Un fine-tuning léger peut servir à calibrer le ton, tandis que le RAG gère l'accès aux connaissances. La littérature récente insiste d'ailleurs sur cette complémentarité.[@Gao2024RAGSurvey]

### 2.3. Architecture type d'une pipeline RAG

Une pipeline RAG se décompose généralement en cinq étapes :

1. **Ingestion** : collecte des documents (nos référentiels, procédures, ...), extraction de texte, normalisation.
2. **Chunking** : découpage en segments (chunks).
3. **Vectorisation / indexation** : calcul d'embeddings pour chaque chunk et insertion dans un index (base vectorielle).
4. **Retrieval / reranking** : récupération de $k$ passages pertinents (qui peuvent être dans un second temps reclassés par un modèle plus fin(reranking)).
5. **Génération** : construction d'un prompt complet avec la requête + contexte, puis génération d'une réponse.

Pour ScribBERT, cette architecture se décline avec des choix d'implémentation qui seront décrits en PARTIE III.

#### 2.3.1. Chunking : segmentation, unités de preuve et compromis

Le chunking est souvent décrit comme un paramètre "d'ingestion", mais il correspond en réalité à un choix de modélisation : **quelle est l'unité minimale (et maximale également) de connaissance** que le système peut retrouver et citer ?

On peut distinguer plusieurs logiques de segmentation :

- **Segmentation structurelle** (titres, sections, listes) : adaptée aux procédures et aux référentiels, car elle suit la logique documentaire.
- **Segmentation à longueur fixe** : robuste et simple, mais peut casser des définitions ou séparer condition/exception.
- **Segmentation thématique** (topic segmentation) : vise à découper selon des ruptures de sujet ; des approches classiques existent (ex. TextTiling).[@Hearst1997]

Le chunking influence directement :

- le **rappel** (chunks trop gros : moins d'unités, risque de dilution ; chunks trop petits : manque de contexte),
- la **citabilité** (capacité à relier une affirmation à un extrait précis),
- la **gestion des contradictions** (contradictions détectables si les unités sont comparables).

Ces aspects seront étudiés dans la PARTIE III (comparaisons de chunking).

### 2.4. Les avantages du RAG

Le premier bénéfice est la réduction des hallucinations : en fournissant au modèle des passages explicites, on contraint sa génération et on limite les inventions. En pratique, c'est plus nuancé (le modèle peut toujours halluciner malgré le contexte), mais le gain est réel. Surtout, le RAG rend la réponse traçable : on peut revenir aux passages utiliséset c'est cette auditabilité qui fait la différence dans un cadre industriel.

Les autres avantages sont plus opérationnels : les connaissances peuvent être mises à jour sans réentraîner le modèle (on réindexe les documents modifiés), le corpus interne reste privé (pas besoin de l'envoyer dans un service cloud pour du fine-tuning), et le coût global est moindre qu'un entraînement dédié.

### 2.5. Les défis du RAG : bruit, contradictions et cohérence

Pour autant, le RAG n'est pas une solution magique. Il introduit ses propres difficultés :

Le **bruit documentaire** est probablement le problème le plus fréquent : le retrieval ramène des chunks qui sont sémantiquement proches de la requête mais qui ne sont pas applicables au cas précis. Dans notre corpus, c'est relativement fréquent avec des procédures qui partagent une terminologie commune mais s'appliquent à des situations différentes.

Les **contradictions** entre documents sont un autre défi, et celui-ci est souvent sous-estimé. Quand un corpus contient à la fois un document de 2020 et sa mise à jour de 2026, que se passe-t-il si le retrieval remonte les deux ? Le modèle peut produire une réponse incohérente, ou pire, choisir silencieusement la mauvaise version.

La **dépendance au chunking** est un problème plus subtil mais réel : une mauvaise segmentation peut couper une règle en deux, ou séparer une condition de son exception, et le modèle génère alors une réponse incomplète sans qu'on puisse facilement diagnostiquer la cause.

Enfin, la **cohérence globale** de la réponse reste fragile : même avec de bons passages, le modèle peut oublier une exception critique ou généraliser.

Ces difficultés justifient une évaluation à deux niveaux (qualité du retrieval *et* qualité de la génération), car un bon score sur l'un ne garantit pas un bon résultat sur l'autre (bien qu'un mauvais retrieval ne facilitera pas une bonne génération évidemment).

Plusieurs variantes architecturales cherchent à répondre à ces défis : le RAG "classique" de Lewis et al.[@Lewis2020], REALM qui intègre le retrieval dans la pré-formation[@Guu2020], ou encore Fusion-in-Decoder (FiD) qui concatène de nombreux passages et laisse le décodeur fusionner l'information.[@IzacardGrave2021] Toutes illustrent un même dilème : donner plus de passages au LLM augmente le rappel potentiel, mais aussi le risque de contradictions, de dilution, et augmente le coût.

#### 2.5.1. Multi-étage retrieval + reranking : un standard pratique

En pratique, les systèmes robustes adoptent souvent une architecture *multi-stage* :

1. un **retrieval large** (top-$k$ élevé) pour maximiser le rappel,
2. un **reranking** (souvent cross-encoder) pour augmenter la précision des passages retenus,
3. une **sélection/assemblage** finale pour respecter la limite de contexte du modèle de génération.

Le reranking de passages avec BERT a montré très tôt qu'un cross-encoder en deuxième étape améliore fortement la qualité des premiers résultats, au prix d'un coût d'inférence qui reste acceptable si on ne reranke qu'un petit ensemble candidat.[@NogueiraCho2019]

Dans un RAG, ces choix ont un effet direct sur la fidélité :

- un retrieval trop large sans reranking augmente le bruit,
- un reranking mal calibré peut favoriser des passages "proches" mais moins normatifs,
- une sélection trop agressive peut oublier d'autres passages qui auraient pu être pertinents.

### 2.6. "Grounding", citations et attribution : de la preuve à la confiance

Citer une source ne suffit pas. En testant ScribBERT, j'ai vu des cas où le système citait un document qui n'avait qu'un rapport lointain avec la question et c'est pire que l'absence de citation, car ça donne une illusion de rigueur. La littérature formalise cette intuition en distinguant trois dimensions : la *context relevance* (le contexte récupéré est-il utile ?), l'*answer relevance* (la réponse traite-t-elle la question ?) et la *faithfulness* (la réponse est-elle supportée par le contexte ?). Ces trois dimensions ne se recouvrent pas, et c'est précisément ce qui rend l'évaluation complexe.

### 2.7. RAG et mémoire : connaissances paramétriques vs non-paramétriques

On distingue la "mémoire paramétrique" d'un LLM (ses poids) et la "mémoire non-paramétrique" (une base documentaire externe, interrogée à la volée). Un modèle assez gros peut stocker beaucoup de faits dans ses paramètres[@Roberts2020], mais avec des limites évidentes en mise à jour et vérifiabilité (éxpliquées plus tôt). Pour ScribBERT, la mémoire non-paramétrique est préférée parce qu'elle est auditable : on sait quels documents ont été consultés, et on peut les mettre à jour sans toucher au modèle.

### 2.8. Pourquoi la notion de "source" est centrale en contexte santé-sécurité

Dans une application santé-sécurité, on ne veut pas de réponse "créative" : on attend une réponse normative ou procédurale, fondée sur les bons documents. La qualité tient alors à des questions très concrètes : le système distingue-t-il une procédure groupe validée d'une note informelle ? Respecte-t-il la différence entre "doit" et "devrait" ? Mentionne-t-il les exceptions ? Ces exigences, bien plus strictes que dans un chatbot grand public, imposent de centrer l'évaluation sur la fidélité aux sources, ce qui sera l'objet de la Partie II.

## Chapitre 3 — La question de la "pertinence" et de la "cohérence"

Les mots "pertinence" et "cohérence" reviennent constamment aussi bien dans ce mémoire que quand on parle de qualité d'un RAG, mais ils recouvrent des réalités assez différentes selon les interlocuteurs. Ce chapitre tente de les clarifier, non pas par amour pour la taxonomie, mais plutôt parce que la qualité d'un protocole d'évaluation dépend directement de ce qu'on en attend.

### 3.1. Définir la pertinence : une notion multi-dimensionnelle

En recherche d'information, la pertinence est un mélange entre un besoin, un utilisateur, un contexte et un document, à un moment donné. La littérature académique insiste depuis longtemps sur cette complexité et sur l'écart entre ce qu'un système juge pertinent et ce que l'utilisateur considère comme pertinent.[@Saracevic1996; @Mizzaro1997] Pour un RAG, plusieurs dimensions s'ajoutent à la simple adéquation thématique.

Un passage peut parler du bon sujet sans être utile pour autant. La **pertinence situationnelle** dépend du rôle de l'utilisateur, de la phase du chantier, des contraintes de site — une procédure générale ne sert pas à un compagnon qui a besoin d'une consigne précise. L'**exhaustivité** est critique quand il cherche une procédure complète : une réponse correcte mais à laquelle il manque une étape ou une exception peut être dangereuse. La **granularité** pose la question inverse : trop de détails peut noyer l'information, surtout si le format attendu est une check-list courte.

L'**actualité** et l'**autorité de la source** sont deux dimensions souvent négligées mais centrales dans un corpus d'entreprise vivant. Un passage peut être thématiquement pertinent mais obsolète. Une procédure groupe validée n'a pas la même force qu'une note informelle. Notre SharePoint contient des documents de niveaux de normativité très différents, et le système doit être capable de les hiérarchiser.

Enfin, les évaluations purement offline ignorent souvent la **pertinence interactive** : l'utilisateur reformule, lit les sources, change de stratégie, et l'utilité dépend de ce processus.[@IngwersenJarvelin2005; @Borlund2003] Pour ScribBERT, cela suggère de compléter les métriques automatiques par des signaux d'usage : taux de reformulation, temps pour obtenir une réponse utile, cas où l'utilisateur doit escalader vers un expert.

### 3.2. Définir la cohérence : du texte à la fidélité aux sources

Dans le contexte des LLMs, la cohérence est souvent abordée sous l'angle de la fluidité textuelle. Pour un RAG, cette définition est insuffisante : une réponse peut être très fluide mais fausse.

Il est utile de distinguer trois notions proches mais différentes :

- **Cohérence textuelle** : le texte "se tient" linguistiquement.
- **Factualité** : les propositions sont vraies dans le cadre documentaire.
- **Fidélité / groundedness** : les propositions sont justifiées par les sources fournies.

Dans un RAG, la fidélité aux sources est souvent plus importante que la factualité absolue : on attend que le système ne dépasse pas ce que le corpus permet d'affirmer.

La **cohérence textuelle** a une dimension locale (connecteurs, anaphores, absence de contradictions phrase-à-phrase) et une dimension globale (fil directeur sur l'ensemble de la réponse). Les LLMs modernes maîtrisent généralement bien la première ; la seconde est plus fragile, surtout lorsque le contexte contient des passages hétérogènes ou que le prompt impose un format strict.

La **fidélité factuelle aux sources** (*faithfulness/groundedness*) est la dimension centrale en RAG : les affirmations de la réponse doivent être supportées par les passages récupérés. Elle peut être compromise par une récupération partielle, une mauvaise attribution, une paraphrase qui modifie le sens normatif, ou une sur-généralisation. Une difficulté spécifique aux textes normatifs est la **modalité** : une reformulation peut transformer un "doit" en "peut", ou l'inverse. Dans une évaluation, cela implique de vérifier non seulement les faits, mais aussi la conformité des modalités et conditions.

La **stabilité / reproductibilité** est un enjeu à la fois opérationnel et méthodologique. À requête identique et à corpus constant, le système doit produire des réponses proches, surtout en contexte santé-sécurité où la variabilité est perçue comme un manque de fiabilité. Si l'output varie fortement, on ne peut pas comparer des variantes (chunking, top-$k$) sans multiplier les répétitions et rapporter des distributions de scores. La stabilité dépend de la stochasticité du modèle (température), du retrieval (approximation ANN) et d'éventuelles reformulations.

La **cohérence terminologique et réglementaire** complète ce tableau : la réponse doit utiliser un vocabulaire métier stable, éviter les formulations ambiguës, et respecter les contraintes réglementaires et internes sans inventer des obligations.

### 3.3. Définir la fiabilité : une synthèse opératoire

Le titre de ce mémoire associe "cohérence" et "fiabilité". La cohérence a été définie ci-dessus. Mais la fiabilité est un concept plus englobant : c'est la propriété d'un système à produire de manière constante des réponses dignes de confiance. Un système peut donner une excellente réponse un jour et une réponse médiocre le lendemain sur la même question : il est ponctuellement bon mais pas fiable.

Pour ce mémoire, j'adopte la définition opératoire suivante :

> **Fiabilité d'un RAG = pertinence du retrieval + fidélité aux sources (factualité) + stabilité/répétabilité des réponses + traçabilité auditable.**

Cette définition présente trois intérêts :

1. Elle **décompose la fiabilité en dimensions mesurables**, ce qui permet d'organiser le protocole d'évaluation (Chapitre 5) autour de chacune.
2. Elle **distingue la cohérence (propriété intrinsèque d'une réponse) de la fiabilité (propriété systémique)** : une réponse peut être cohérente une fois et incohérente la suivante ; un système n'est fiable que si ses réponses sont cohérentes de manière répétée.
3. Elle **inclut explicitement la traçabilité**, dimension non couverte par les métriques classiques mais essentielle (auditabilité, conformité).

### 3.4. Pertinence perçue vs pertinence mesurée

Il y a un écart, parfois considérable, entre ce que les métriques disent et ce que l'utilisateur ressent. Parfois, des configurations avec de "bons" scores de retrieval produisaient des réponses qui parfois étaient trop vagues ou mal ciblées. Et inversement, des réponses jugées utiles ne correspondaient pas toujours à un Recall@k élevé.

Ce décalage impose de travailler sur les deux fronts : les **mesures automatiques** (utiles pour comparer des variantes, diagnostiquer, itérer) et la **perception utilisateur** (confiance, effort, satisfaction). Un protocole robuste combine les deux, ce que la littérature appelle triangulation.

Sur le plan méthodologique, cela rejoint l'idée de séparer **évaluation intrinsèque** (mesurer des propriétés internes) et **évaluation extrinsèque** (mesurer l'effet sur la tâche finale).

### 3.5. Travaux récents sur l'évaluation des RAG et LLMs augmentés

L'évaluation des systèmes RAG s'est structurée autour de plusieurs axes :

1. **Évaluation retrieval** : métriques classiques (Recall@k, nDCG, MRR) sur des jeux de test annotés.[@JarvelinKekalainen2002]
2. **Évaluation génération** : métriques de similarité (BLEU/ROUGE) peu adaptées à la QA ouverte ; métriques sémantiques (BERTScore, BLEURT) ; métriques de factualité (ex. TruthfulQA, FactScore) visant à quantifier l'alignement factuel des sorties.[@Lin2021TruthfulQA; @Min2023FactScore]
3. **Évaluation "end-to-end"** : frameworks dédiés au RAG (ex. RAGAS, TruLens, LangSmith) qui tentent de décomposer la qualité en sous-scores (context relevance, answer relevance, faithfulness, citation, etc.).
4. **LLM-as-judge** : utiliser un LLM pour noter des réponses selon une grille (G-Eval, Prometheus). Puissant mais nécessite une gouvernance stricte (biais, fuite d'informations, reproductibilité).

Les benchmarks de retrieval généralistes (BEIR) et les *leaderboards* d'embeddings (MTEB) ont également contribué à standardiser la comparaison de modèles et à clarifier l'écart entre performance sur des tâches "web" et performance sur des corpus spécialisés.[@Thakur2021BEIR; @Muennighoff2023MTEB]

Pour la génération, plusieurs métriques basées sur des modèles pré-entraînés se sont imposées :

- **BERTScore** pour mesurer une similarité sémantique token-level.[@Zhang2020BERTScore]
- **BLEURT** comme score appris de similarité/qualité.[@Sellam2020BLEURT]

Cependant, ces métriques ne suffisent pas à capturer la fidélité aux sources. C'est pourquoi des travaux récents sur la factualité/hallucination (ex. en résumé) sont souvent mobilisés comme base conceptuelle.[@Maynez2020; @Ji2023]

Un point récurrent dans la littérature est l'écart entre :

- la performance IR (retrieval correct) et
- la performance de génération (usage correct des sources).

Autrement dit, un bon retrieval ne garantit pas une réponse fidèle, et une réponse fluide ne garantit pas qu'elle soit vraie.

Dans le cas d'un RAG, l'évaluation pertinente doit idéalement être **décomposable** : elle doit permettre de dire *où* se situe l'échec (retrieval, reranking, prompt, génération) et pas seulement constater que l'output final est "bon" ou "mauvais".

#### 3.5.1. Formaliser quelques métriques retrieval (rappels utiles)

Pour expliciter la suite, on rappelle des définitions courantes sur un ensemble de requêtes $Q$. On note $\mathrm{TopK}(q)$ l'ensemble des $k$ premiers passages récupérés pour la requête $q$, et $\mathrm{Rel}(q)$ l'ensemble des passages pertinents (selon l'annotation).

- **Recall@k** :

$$\mathrm{Recall@k} = \frac{1}{|Q|}\sum_{q\in Q} \frac{|\mathrm{Rel}(q) \cap \mathrm{TopK}(q)|}{|\mathrm{Rel}(q)|}$$

- **MRR** (Mean Reciprocal Rank), utile quand on attend *au moins un bon passage* parmi les premiers résultats :

$$\mathrm{MRR} = \frac{1}{|Q|}\sum_{q\in Q} \frac{1}{\mathrm{rank}_q}$$

où $\mathrm{rank}_q$ est le rang du premier document pertinent.

- **nDCG@k** (pertinence graduée), qui pénalise moins fortement un document pertinent placé en position 2 qu'en position 20 :

$$\mathrm{DCG@k} = \sum_{i=1}^{k} \frac{2^{rel_i}-1}{\log_2(i+1)}\quad;\quad \mathrm{nDCG@k}=\frac{\mathrm{DCG@k}}{\mathrm{IDCG@k}}$$

Ces métriques sont au cœur de l'IR évaluative moderne.[@JarvelinKekalainen2002]

L'intérêt pour le RAG est de relier ces scores à la qualité finale : par exemple, un Recall@k faible limite mécaniquement la fidélité, car la preuve n'entre jamais dans le contexte.

### 3.6. Positionnement de la contribution du mémoire

Ce que ce mémoire cherche à apporter, concrètement, c'est un cadre d'évaluation qui permette de :

- **séparer** les erreurs de retrieval et les erreurs de génération, parce qu'on ne corrige pas les unes de la même façon que les autres,
- **intégrer** les spécificités santé-sécurité (criticité, exceptions) que les benchmarks généralistes ignorent,
- rester **reproductible** et applicable sur un corpus d'entreprise,
- produire des **diagnostics actionnables** : pas seulement "c'est bon" ou "c'est pas bon", mais *quoi* améliorer (le chunking, le top-k, le reranking, le prompt, la température).

La Partie II présente la méthodologie retenue, et la Partie III l'applique à ScribBERT.

---

# PARTIE II — Méthodologie d'évaluation d'un système RAG

La Partie I a posé les bases : ce qu'est un RAG, ce que signifient "pertinence" et "cohérence" dans ce contexte, et pourquoi ces notions sont si délicates à évaluer quand l'enjeu est la sécurité des collaborateurs. La Partie II entre dans le concret.

Je dois admettre que la question de l'évaluation m'a à l'origine paru plus simple qu'elle ne l'est en réalité. Au début du développement de ScribBERT, je procédais par tâtonnement : je testais une configuration, je posais quelques questions, j'observais si les réponses "avaient l'air bonnes". Sauf que cette approche montre vite ses limites : à chaque modification de paramètre (stratégie de chunking, modèle d'embedding, valeur de $k$), une question qui marchait bien se dégradait, et une autre qui échouait s'améliorait. Il n'y avait pas de progression nette, pas de signal clair. C'est cette frustration qui m'a conduit à formaliser un protocole d'évaluation rigoureux.

Trois questions structurent cette partie :

1. **Quels leviers techniques** influencent la qualité d'un RAG, et comment les caractériser (Chapitre 4) ?
2. **Quel protocole** mettre en place pour mesurer cette qualité de façon reproductible (Chapitre 5) ?
3. **Comment évaluer la cohérence** (fidélité aux sources, stabilité), qui est la dimension la plus difficile à automatiser (Chapitre 6) ?

L'ambition est de proposer un cadre transférable, pas spécifique à ScribBERT, mais qui sera instancié sur ce cas en Partie III.

## Chapitre 4 — Modèles et paramètres influençant la performance

Un système RAG n'est pas une boîte noire à un seul bouton. C'est un assemblage de composants, chacun avec ses propres réglages, et la qualité finale dépend de l'ensemble. Le problème (et je l'ai vécu de façon assez directe), c'est que modifier un paramètre peut améliorer certains cas et en dégrader d'autres. Pour sortir du tâtonnement, il faut d'abord cartographier ces leviers et comprendre comment ils interagissent.

Ce chapitre passe en revue quatre familles :

1. les **modèles d'embedding**, qui déterminent comment requêtes et documents sont représentés dans l'espace vectoriel,
2. le **chunking et le prétraitement**, qui fixent la granularité des unités indexées,
3. les **stratégies de retrieval** (comment on récupère et classe les passages candidats),
4. la **composante de génération** (le LLM, le prompt et les paramètres associés).

### 4.1. Les modèles d'embedding

Le modèle d'embedding est la base d'un RAG dense. C'est lui qui détermine la géométrie de l'espace dans lequel requêtes et passages sont comparés, et si cette géométrie est mal adaptée au domaine, aucune astuce en aval ne pourra compenser.

#### 4.1.1. Typologie des modèles disponibles

Le paysage des modèles d'embedding évolue rapidement. Au moment de l'écriture, on peut distinguer plusieurs familles :

- **Modèles open-source dérivés de BERT et SBERT** : famille `sentence-transformers` (`all-MiniLM-L6-v2`, `all-mpnet-base-v2`, etc.), qui constitue une référence open-source largement utilisée.[@ReimersGurevych2019]
- **Modèles multilingues open-source** : `multilingual-e5` (Microsoft), `BGE-M3` (BAAI), `Jina embeddings v3`, qui visent à couvrir un grand nombre de langues avec un seul modèle.
- **Modèles français ou multilingues spécialisés** : `Solon` (Lajavaness), `CamemBERT`-based encoders, `Sentence-CamemBERT`, utiles pour la composante française du corpus ; mais le corpus de Bouygues TP étant bilingue (cf. 4.1.3), un modèle multilingue couvrant aussi bien le français que l'anglais reste souvent préférable.
- **Modèles propriétaires accessibles par API** : `text-embedding-3-small/large` (OpenAI), `embed-multilingual-v3` (Cohere), `voyage-3` (Voyage AI), `gemini-embedding` (Google). Performants mais soulèvent des questions de coût, latence et confidentialité.
- **Modèles spécialisés par domaine** : `LegalBERT`, `BioBERT`, `SciBERT`, etc. À ce jour, aucun modèle d'embedding open-source spécialisé santé-sécurité/BTP n'est librement disponible, ce qui constitue à la fois une limite et une opportunité (fine-tuning interne envisageable).

#### 4.1.2. Dimensions d'embedding : compromis qualité / coût

La dimension de sortie d'un modèle d'embedding ($d \in \{384, 512, 768, 1024, 1536, 3072\}$ pour les plus courants) influence trois aspects :

- **la qualité représentationnelle** : à modèle donné, une dimension plus élevée *peut* mieux séparer les concepts, mais ce n'est pas systématique ;
- **le coût de stockage** : un index de $N$ chunks en `float32` occupe $4 \cdot N \cdot d$ octets (ex. : 1 M chunks en dim. 1024 ≈ 4 Go) ;
- **la latence de recherche** : croît linéairement avec $d$ pour la similarité, et indirectement via la taille de l'index ANN.

Les **embeddings "Matryoshka"** (Matryoshka Representation Learning) permettent de tronquer la dimension a posteriori avec une perte limitée, offrant un curseur qualité/coût ajustable sans réindexation complète.

#### 4.1.3. Multilinguisme et adaptation au français technique

Le corpus de ScribBERT est bilingue : les référentiels internes Bouygues TP mélangent éxistent aussi bien en français qu'en anglais, et la documentation client (ENBRIDGE, PAS 91, OSHA, etc.) est majoritairement en anglais. Le système doit donc gérer les deux langues de façon homogène. Deux stratégies sont envisageables :

1. **Modèle multilingue généraliste** : robuste sur plusieurs langues, mais souvent moins fin sur les nuances techniques d'une langue donnée.
2. **Modèle multilingue de grande taille avec instruction tuning** : E5, BGE, qui combine couverture linguistique et qualité.

Le benchmark **MTEB** (Massive Text Embedding Benchmark) fournit une comparaison standardisée entre modèles, mais il faut se rappeler que les performances **MTEB ne se transposent pas mécaniquement** à un domaine spécialisé.[@Muennighoff2023MTEB] Le benchmark **BEIR** a clairement montré la dégradation hors-domaine des retrievers entraînés sur du web généraliste.[@Thakur2021BEIR]

#### 4.1.4. Évaluation intrinsèque vs extrinsèque

On distingue deux niveaux d'évaluation pour un modèle d'embedding :

- **Intrinsèque** : qualité de la séparation paires positives / négatives (STS, retrieval@k sur jeux annotés, alignement avec jugements humains)
- **Extrinsèque** : impact sur la tâche aval (qualité de la réponse RAG finale)

Les deux ne coïncident pas toujours : un embedding qui remonte "les bons documents" peut tout de même conduire à une mauvaise réponse si le générateur exploite mal le contexte. C'est une raison supplémentaire pour évaluer les composants **et** la chaîne complète (cf. Chapitre 5).

#### 4.1.5. Critères de sélection en contexte industriel

En contexte d'entreprise, le choix d'un modèle d'embedding ne se résume pas à un score sur un benchmark. Une grille de décision multi-critères est nécessaire :

| Critère | Question |
|---------|----------|
| **Qualité retrieval** | Recall@k sur le corpus de test interne |
| **Couverture linguistique** | Le modèle gère-t-il le français et l'anglais ? |
| **Coût** | API payante (OpenAI, Cohere) ou auto-hébergé (GPU) ? |
| **Latence** | Temps d'inférence acceptable pour une expérience temps réel ? |
| **Confidentialité** | Le modèle peut-il être hébergé en interne ? Avons-nous des contrats avec clauses de confidentialité ? |
| **Maintenance** | Stabilité, fréquence des mises à jour |
| **Fine-tunabilité** | Possibilité d'adapter le modèle au domaine santé-sécurité si nécessaire |

Ces critères seront appliqués à ScribBERT en Partie III.

### 4.2. Le rôle du chunking et du prétraitement textuel

Le chunking est probablement le sujet sur lequel j'ai passé le plus de temps à tâtonner. Il est souvent présenté comme un "détail d'ingestion" dans les tutoriels, mais c'est en réalité un choix de modélisation à part entière, et ses effets se propagent à toute la chaîne.

#### 4.2.1. Stratégies de chunking

Plusieurs approches existent, chacune avec ses compromis :

- **Chunking à taille fixe** (nombre tokens ou caractères) : simple, prévisible, mais aveugle à la structure. Risque majeur : couper une règle au milieu d'une phrase, ou séparer une condition de son exception.
- **Chunking récursif** (*recursive character text splitter*) : tente de découper d'abord sur des séparateurs "forts" (`\n\n`, `\n`, `. `, ` `) avant de tomber sur du caractère brut. Bon compromis par défaut, implémenté dans LangChain/LlamaIndex.
- **Chunking structurel** : exploite la hiérarchie documentaire (titres, sections, listes, tableaux). Particulièrement adapté aux référentiels et normes qui ont une structure claire.
- **Chunking sémantique** : utilise un modèle (souvent un embedder) pour détecter des ruptures de sujet et grouper les phrases sémantiquement proches. Plus coûteux en ingestion, gain variable.
- **Chunking custom (regex / parser dédié)** : pour des formats spécifiques (procédures avec format imposé, fiches sécurité), un parser dédié peut extraire des unités cohérentes (un § = une règle).

Pour un corpus santé-sécurité, les stratégies structurelle, récursive et custom sont souvent les plus pertinentes, car les règles ont une granularité naturelle (article, paragraphe numéroté, étape de procédure).

#### 4.2.2. Taille des chunks et overlap

Deux paramètres clés interagissent :

- **Taille du chunk** ($T$, en tokens) : trop petit ⇒ perte de contexte, ambiguïté, perte de l'antécédent ("il", "cette règle") ; trop grand ⇒ dilution sémantique, *embedding* moins discriminant, contexte LLM saturé.
- **Overlap** ($O$, généralement 10–20 % de $T$) : permet d'amortir les coupures malheureuses au prix d'une redondance dans l'index.

L'optimum dépend du type de question : les questions factuelles courtes tolèrent des chunks petits, tandis que les questions procédurales ("comment faire X ?") requièrent souvent des chunks plus larges qui capturent une séquence d'étapes. C'est ce genre de tension que j'ai observée lors du développement : en réduisant la taille des chunks, je gagnais en précision sur certaines questions, mais je cassais la cohérence des réponses sur d'autres. Un protocole rigoureux **teste plusieurs configurations** ($T \in \{256, 512, 1024\}$, $O \in \{0, 64, 128\}$) et mesure l'impact end-to-end. C'est ce que nous ferons en Partie III.

#### 4.2.3. Préservation de la structure et des métadonnées

Un chunk "brut" (texte seul) perd des informations critiques : section d'origine, niveau hiérarchique, type de document, date de validité, autorité émettrice. Or ces métadonnées :

- enrichissent les **filtres de retrieval** ("uniquement les docs en français" / "documents BYTP seulement") ;
- permettent de **citer correctement** la source dans la réponse ;
- aident à **arbitrer les contradictions** (préférer le plus haut niveau d'autorité, le document qui traite la question en sujet principal et pas en secondaire dans un petit paragraphe).

Un schéma de métadonnées robuste pour ScribBERT pourrait inclure : `document_id`, `titre`, `type` (procédure, standard, guide), `autorité` (groupe / filiale / chantier / client), `date`, `langue`.

#### 4.2.4. Nettoyage et normalisation

Le prétraitement comprend :

- **Extraction texte** depuis PDF. Les PDFs techniques posent des problèmes spécifiques : tableaux, schémas avec légendes, en-têtes/pieds de page répétitifs. Des outils comme `Unstructured`, `pdfplumber`, `pymupdf` ou `Marker` ont des compromis différents.
- **Suppression du bruit** : numéros de page, en-têtes répétés, watermarks.
- **Normalisation** : unification des guillemets, des espaces insécables, des tirets ; éventuellement passage en minuscules pour le sparse retrieval (mais pas pour les embeddings, qui sont généralement *case-sensitive*).
- **Conservation du formatage utile** : listes à puces, numérotation hiérarchique, gras pour les termes-clés.

Un point souvent négligé : les **tableaux** et les **schémas**. Linéariser un tableau en texte brut détruit sa structure. Des stratégies plus avancées (extraction structurée, légendes générées par un VLM (Vision Language Model), tableaux convertis en markdown) peuvent être étudiées.

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

Pour ScribBERT, l'hypothèse forte est qu'un utilisateur citant explicitement "PR-SST-042" doit retrouver ce document, ce que BM25 garantit mais qu'un dense pur peut manquer. Cette hypothèse sera testée en Partie III.

#### 4.3.3. Reranking par cross-encoder

Le reranking consiste à appliquer un modèle plus précis (et plus coûteux) à un petit ensemble de candidats déjà récupérés. Les cross-encoders (ex. `ms-marco-MiniLM`, `bge-reranker-v2-m3`, `Cohere Rerank`) lisent **conjointement** la requête et le passage et produisent un score de pertinence.[@NogueiraCho2019]

Pipeline typique :

1. Retrieval initial → top-100 candidats (rapide, $O(\log N)$ sur HNSW),
2. Reranking → top-10 (lent : 100 inférences cross-encoder, $\sim$ 100–500 ms),
3. Génération sur top-10 (ou top-5).

Le gain de qualité est souvent **substantiel** mais le coût en latence est non négligeable. Le compromis dépend de la criticité de l'application.

#### 4.3.4. Filtrage par métadonnées

Le filtrage permet de restreindre la recherche selon des contraintes structurelles :

- **Pré-filtrage** : appliquer le filtre **avant** la recherche vectorielle (ex. uniquement les documents en Anglais, uniquement les procédures).
- **Post-filtrage** : récupérer puis filtrer (plus simple, mais peut vider le top-k et empêcher d'autres documents pertinents de remonter).

Un filtrage trop strict peut éliminer les bons passages au même titre qu'un post-filtrage gaspille du calcul. Les bases vectorielles modernes (Qdrant, Weaviate, Pinecone) optimisent le pré-filtrage. ChromaDB, utilisé pour le POC de ScribBERT, supporte le pré-filtrage par métadonnées, bien qu'il soit davantage adapté au développement local et aux petits corpus.

Pour ScribBERT, des filtres pertinents incluent : provenance du document (groupe vs client), type de document (procédure, standard, guide), langue (français vs anglais).

#### 4.3.5. Choix de $k$ : compromis rappel / bruit / coût

La valeur du top-$k$ retourné au générateur a un effet en U inversé :

- $k$ trop petit : la "bonne" preuve n'est pas dans le contexte ⇒ génération erronée ou "je ne sais pas".
- $k$ trop grand : dilution, bruit, coûts élevés (tokens consommés, latence), risque de **lost in the middle** (le LLM ignore les passages au milieu du contexte).

Valeurs typiques : $k \in [3, 10]$ après reranking. La valeur optimale dépend du modèle de génération (les LLMs récents avec contexte long tolèrent mieux $k$ élevé) et du type de question.

#### 4.3.6. Query expansion et reformulation

Plusieurs techniques visent à enrichir ou reformuler la requête :

- **HyDE** (*Hypothetical Document Embeddings*) : faire générer par un LLM une réponse hypothétique à la requête, puis utiliser son embedding pour la recherche. Améliore le rappel sur des questions complexes.
- **Multi-query** : générer plusieurs reformulations de la requête, lancer plusieurs recherches, fusionner les résultats.
- **Step-back prompting** : reformuler la requête en une question plus générale, qui peut mieux matcher des passages introductifs.
- **Query rewriting via LLM** : corriger les fautes, expanser les acronymes ("EPI" → "équipement de protection individuelle"), normaliser le vocabulaire.

Ces techniques améliorent généralement le rappel mais ajoutent de la latence, augmentent les coûts et peuvent introduire du **drift sémantique** (la reformulation s'éloigne de l'intention initiale). Un protocole d'évaluation rigoureux doit mesurer le gain net.

### 4.4. La composante de génération

Une fois les passages sélectionnés, la génération transforme le contexte en réponse. Plusieurs leviers conditionnent la qualité.

#### 4.4.1. Choix du LLM

Les options se classent en trois catégories :

- **LLMs propriétaires (API)** : GPT-4 / GPT-4o (OpenAI), Claude 3.5/4 (Anthropic), Gemini (Google), Mistral Large. Excellente qualité, coût marginal par requête/token, dépendance à un fournisseur externe et contraintes de confidentialité.
- **LLMs open-weights auto-hébergés** : Llama 3, Mistral / Mixtral, Qwen, DeepSeek, Gemma. Contrôle total des données, coût d'infrastructure (GPU).
- **LLMs spécialisés** : modèles plus petits fine-tunés sur un domaine (ex. modèles biomédicaux). À ce jour, pas d'option santé-sécurité/BTP.

Pour ScribBERT, l'absence d'infrastructure GPU chez Bouygues TP a rendu les modèles auto-hébergés peu viables : les tests en local sur mon poste de travail n'ont permis de faire tourner que des modèles de petite taille, et même ceux-ci se sont révélés trop lents pour être exploitables. Le choix s'est porté sur un LLM propriétaire via **Azure OpenAI**, dans le cadre d'un contrat-cadre Bouygues Construction garantissant la confidentialité des données. 

#### 4.4.2. Engineering du prompt

Le prompt système est le contrat passé entre le développeur et le modèle. Un prompt RAG contient généralement quatre éléments : les instructions système (rôle, contraintes, règles de comportement), la requête utilisateur, le contexte récupéré (passages formatés et numérotés), et le format de sortie attendu.

Dans la pratique, quelques principes font consensus. Le *grounding explicite* est essentiel : il faut dire au modèle de ne répondre que sur la base des extraits fournis, et de l'indiquer clairement si l'information n'y figure pas. Les citations obligatoires ("cite chaque affirmation avec le numéro de la source") améliorent la traçabilité. Et surtout, il faut autoriser le modèle à dire "je ne sais pas". C'est contre-intuitif (on veut des réponses), mais c'est ce qui réduit le plus efficacement les hallucinations. (On peut aussi ajouter un ou deux exemples (*few-shot*) de paires question/réponse pour calibrer le style)

#### 4.4.3. Gestion de la fenêtre de contexte

Le budget de tokens est une contrainte structurante. Quand on a 10 passages de 500 tokens chacun et un modèle qui accepte 8k tokens en contexte, il faut faire des choix. La stratégie la plus simple est la troncature (couper les passages les moins bien classés). On peut aussi compresser les chunks longs avant injection, ou remplir le contexte par ordre de pertinence jusqu'à un seuil. Les LLMs récents acceptent des contextes de 128k tokens et plus, mais attention au phénomène *lost in the middle* expliqué plus tôt : le modèle tend à moins bien exploiter les passages placés au milieu d'un gros contexte, ce qui peut fausser les réponses.

#### 4.4.4. Paramètres de décodage

- **Température** : 0 pour la reproductibilité (cas critiques santé-sécurité), 0.2–0.5 pour un compromis qualité/diversité, ≥ 0.7 pour la créativité (peu pertinent ici).
- **Top-p / top-k sampling** : alternative à la température, plus rarement utilisée en RAG.
- **Max tokens** : borne haute pour éviter les réponses interminables.
- **Repetition / presence penalty** : utile si le modèle "bégaie" sur des termes techniques.

Pour ScribBERT, une température faible est recommandée afin de garantir la stabilité des réponses (cf. Chapitre 6).

#### 4.4.5. Citations et traçabilité

La citation peut prendre plusieurs formes : inline ("Selon [1], le port du harnais est obligatoire dès 2 m"), en fin de réponse (liste des sources), ou avec reproduction littérale des passages clés.

L'important, au-delà du format, est que la traçabilité soit *machine-vérifiable*. Chaque citation doit pointer vers un identifiant de chunk loggé, lui-même relié au document d'origine. Sans cette chaîne, on a de la traçabilité en surface, utile pour l'utilisateur mais insuffisante pour l'audit et pour la mesure de fidélité (cf. Chapitre 6).

#### 4.4.6. Garde-fous pour le contexte santé-sécurité

En contexte critique, il faut prévoir des garde-fous explicites. Le plus important est le **refus contrôlé** : quand le retrieval ne trouve rien de suffisamment pertinent, mieux vaut répondre "je n'ai pas trouvé cette information dans les référentiels" plutôt que d'improviser. De même, si plusieurs sources se contredisent, le système devrait le signaler plutôt que d'arbitrer en silence. Pour les questions hors périmètre santé-sécurité, un mesage de refus est préférable à une réponse approximative.

### 4.5. Synthèse des leviers et matrice d'expérimentation

L'ensemble des leviers présentés peut être résumé dans une matrice qui guidera la conception du protocole expérimental (Chapitre 5) :

| Composant | Leviers principaux | Métriques affectées en priorité |
|-----------|-------------------|-------------------------------|
| Embedding | Modèle, dimension, langue, fine-tuning | Recall@k, MRR, nDCG |
| Chunking | Stratégie, taille, overlap, métadonnées | Recall@k, citabilité, fidélité |
| Retrieval | Sparse / dense / hybride, filtres, $k$ | Recall@k, précision contexte |
| Reranking | Présence, modèle, top-$n$ | Precision@k, fidélité |
| Query processing | Expansion, reformulation, HyDE | Recall@k (gain), latence (perte) |
| Génération (LLM) | Choix du modèle, taille | Fluidité, fidélité, latence |
| Génération (prompt) | Instructions, few-shot, format | Fidélité, format, refus contrôlé |
| Génération (décodage) | Température, max tokens | Stabilité, longueur |

L'expérimentation menée en Partie III ne pourra pas tester toutes les combinaisons (explosion combinatoire). Elle adoptera une approche **OFAT** (One-Factor-At-a-Time) sur un sous-ensemble de paramètres jugés les plus impactants, complétée par quelques expériences factorielles ciblées.

Le Chapitre 5 présente le protocole d'évaluation lui-même : jeux de test, métriques, conditions d'expérimentation.

## Chapitre 5 — Construction d'un protocole d'évaluation

Le Chapitre 4 a inventorié les différents leviers actionnables. Reste la question fondamentale : **comment mesurer leur effet ?** Sans un protocole d'évaluation structuré, on en revient au tâtonnement décrit plus haut : on modifie un paramètre, on pose trois questions, on a "l'impression" que c'est mieux ou moins bien, sans pouvoir trancher.

Ce que je cherche ici, c'est un protocole qui produise des mesures reproductibles (le même test donne le même résultat), comparables (on peut ordonner des configurations), et surtout diagnostiques, qui permettent de dire où se situe le problème dans la chaîne, pas seulement que la réponse finale est "bonne" ou "mauvaise".

Ce chapitre s'organise en cinq sections : les critères d'évaluation (§ 5.1), les approches (automatique, humaine, hybride) (§ 5.2), la construction du jeu de test (§ 5.3), les conditions expérimentales (§ 5.4), et les méthodes d'analyse (§ 5.5).

### 5.1. Cinq dimensions pour mesurer la fiabilité

Plutôt que de dresser une liste plate de métriques, j'organise l'évaluation autour des **cinq dimensions de la fiabilité** définies au Chapitre 3. Pour chacune, la question centrale est : quel type d'échec cherche-t-on à détecter ?

#### 5.1.1. Dimension 1 — Pertinence du retrieval

*Les passages récupérés contiennent-ils l'information nécessaire pour répondre ?*

C'est le premier maillon de la chaîne, et si le retrieval rate la bonne règle, rien dans la suite ne peut compenser. Plusieurs métriques permettent de le mesurer, selon l'angle qui nous intéresse :

- **Hit@k** : est-ce qu'au moins un passage pertinent figure dans les $k$ résultats retournés ? C'est la mesure la plus simple : une réponse binaire "oui/non" par question.
- **Recall@k** : quelle proportion des passages pertinents a été retrouvée ? Utile quand la réponse attendue nécessite plusieurs sources distinctes.
- **Precision@k** : parmi les $k$ passages retournés, combien sont réellement utiles ? Un retrieval avec beaucoup de bruit nuit à la génération même si les bons passages sont là.
- **MRR** (Mean Reciprocal Rank) : le premier passage pertinent est-il bien classé en tête ? C'est la bonne métrique quand on attend principalement un passage décisif.
- **nDCG@k** : variante pondérée qui tient compte de la position (un passage pertinent classé 2ème est meilleur que le même classé 8ème). Utile si les jugements de pertinence sont gradués (très pertinent / un peu pertinent / hors-sujet).

Pour ScribBERT, **Recall@k** et **MRR** sont les métriques principales : l'enjeu est avant tout de s'assurer que la "bonne règle" figure bien parmi les passages remontés. Le Hit@k est un bon complément rapide pour les questions qui n'ont qu'un seul passage.

#### 5.1.2. Dimension 2 — Fidélité aux sources (*faithfulness*)

*La réponse s'en tient-elle à ce que disent vraiment les passages récupérés ?*

C'est la dimension la plus critique pour ScribBERT. Une réponse peut être fluide et cohérente, mais complètement inexacte, soit parce que le modèle a "rajouté" des éléments absents des sources, soit parce qu'il a modifié le sens. L'enjeu n'est pas seulement la véracité des faits, c'est la conformité aux sources fournies.

Plusieurs approches permettent de mesurer ça automatiquement :

- **Faithfulness (RAGAS)** : la réponse est décomposée en propositions atomiques ("le port du harnais est obligatoire dès 2 m"), et chacune est vérifiée contre le contexte par un LLM-juge. Le score final est la proportion de propositions supportées.
- **NLI-based scoring** : un modèle d'inférence textuelle (NLI) vérifie si chaque phrase de la réponse est logiquement impliquée par le contexte. Plus robuste pour les phrases longues que l'approche atomique.
- **Citation faithfulness** : quand la réponse cite un passage explicitement, vérifie-t-on que ce passage supporte réellement l'affirmation ? C'est une vérification de cohérence entre la citation et le contenu.
- **Hallucination rate** : simplement le taux de propositions non supportées (= 1 − faithfulness).

À ces métriques génériques, on peut ajouter en contexte santé-sécurité une mesure plus spécifique : la **préservation des modalités** : la réponse respecte-t-elle les niveaux d'obligation des sources ("doit" vs "peut" vs "il est recommandé de") ? Cette dimension est difficile à automatiser de façon fiable et nécessite souvent une vérification humaine ou un LLM-juge avec des instructions très précises à ce sujet.

#### 5.1.3. Dimension 3 — Pertinence et complétude de la réponse

*La réponse dit-elle ce qu'il faut, ni plus ni moins ?*

Cette dimension évalue la réponse en tant que telle, indépendamment de ses sources : est-ce qu'elle répond vraiment à ce qui était demandé ? Est-ce qu'elle est complète ? Est-ce qu'elle est calibrée en longueur ?

- **Answer relevance (RAGAS)** : un LLM-juge génère plusieurs questions hypothétiques à partir de la réponse produite, puis mesure si elles ressemblent à la question originale. Une réponse hors-sujet ou vague produira des questions hypothétiques éloignées.
- **Complétude** : en comparaison avec une réponse de référence annotée par un expert, quelle proportion des éléments attendus (étapes, conditions, exceptions) est présente dans la réponse générée ?
- **Concision** : la réponse est-elle proportionnée à la complexité de la question, ou le modèle noie-t-il l'information dans une réponse excessivement longue ?
- **Respect du format** : si le prompt demande une check-list numérotée, le modèle l'a-t-il bien produite ?

#### 5.1.4. Dimension 4 — Stabilité et répétabilité

*Si l'on rejoue la même question, la réponse est-elle cohérente ?*

Un système peut obtenir de bons scores en moyenne tout en produisant des réponses très variables d'une exécution à l'autre. Cette dimension, traitée en détail au Chapitre 6, mesure la **variance** des réponses plutôt que leur qualité moyenne. Elle conditionne également la robustesse statistique de toutes les comparaisons du protocole : si la variabilité intra-configuration est élevée, comparer deux configurations sur une seule exécution par question n'a pas de sens.

#### 5.1.5. Dimension 5 — Traçabilité et auditabilité

*Peut-on vérifier, a posteriori, l'origine de chaque affirmation de la réponse ?*

Il ne suffit pas que la réponse soit juste  il faut pouvoir le prouver. Cette dimension mesure la qualité de la chaîne de traçabilité entre chaque affirmation et son passage source :

- **Citation correctness** : les passages cités existent-ils, sont-ils pertinents, et supportent-ils réellement l'affirmation ?
- **Citation completeness** : toutes les affirmations qui devraient être sourcées le sont-elles ?
- **Diversité des sources** : la réponse s'appuie-t-elle sur plusieurs documents, ou paraphrase-t-elle toujours la même source ? Un signal d'agrégation est une bonne chose sur les questions transverses/multi-documents.

Ces métriques ne sont utiles que si le prompt impose un format de citation machine-vérifiable (identifiants de chunks, pas juste des titres de documents).

#### 5.1.6. Coût opérationnel

Ces cinq dimensions décrivent la qualité du système. En production, on y ajoute des métriques de coût qui conditionnent la viabilité opérationnelle :

- **Latence** de la chaîne complète (retrieval + reranking + génération). En pratique, un percentile P95 est plus significatif que la moyenne pour mesurer l'expérience utilisateur réelle.
- **Coût par requête** si le LLM ou l'embedder est facturé à l'usage.
- **Taux de refus** : proportion de requêtes pour lesquelles le système répond "je ne sais pas" faute de sources suffisantes. C'est une métrique à double lecture : un taux trop bas suggère que le système improvise (hallucine), un taux trop élevé indique une expérience utilisateur dégradée.

### 5.2. Approches d'évaluation : automatique, humaine, hybride

#### 5.2.1. Évaluation automatique

Les métriques automatiques se classent en trois familles :

- **Lexicales** (BLEU, ROUGE, METEOR, exact match) : peu adaptées à la QA générative car elles pénalisent la paraphrase légitime. Utiles uniquement pour des réponses très courtes et factuelles.
- **Vectorielles** (BERTScore, BLEURT, similarité cosinus d'embeddings de réponse) : capturent mieux la similarité sémantique. Limitation : peuvent juger "proches" deux réponses dont l'une contient une erreur factuelle subtile.[@Zhang2020BERTScore; @Sellam2020BLEURT]
- **LLM-based / LLM-as-judge** : un LLM note la réponse selon une grille (G-Eval, Prometheus, RAGAS, TruLens). Approche dominante pour le RAG aujourd'hui : flexible, capable de juger la fidélité, la complétude, la modalité.

**Avantages** : scalabilité (millions de requêtes), reproductibilité (à seed et prompt fixés), coût marginal réduit.

**Limites** :
- corrélation imparfaite avec le jugement humain expert (surtout en domaine spécialisé comme dans notre cas) ;
- biais du LLM-juge (préférence pour les réponses verbeuses, biais de longueur, biais de formatage) ;
- risque de sur-évaluation si le même LLM sert de générateur et de juge (auto-validation circulaire) ;
- difficulté à juger les modalités, les exceptions, les conditions implicites.

**Bonnes pratiques** :
- Utiliser un LLM-juge différent du générateur évalué.
- Si possible, "calibrer" le LLM-juge sur un échantillon annoté humainement (quelques exemples).
- Logger les justifications du juge, pas seulement le scorve.
- Mesurer la stabilité du juge lui-même (même prompt, $n$ exécutions).

#### 5.2.2. Évaluation humaine

Constitue le **gold standard**, particulièrement pour les dimensions difficiles à automatiser (modalités, sécurité, exceptions).

**Conception d'une grille d'évaluation** :

| Critère | Échelle | Définition |
|---------|---------|------------|
| Pertinence | 0–3 | 0 = hors-sujet, 3 = répond exactement à la question |
| Fidélité aux sources | 0–3 | 0 = invente, 3 = parfaitement supporté par les sources fournies |
| Complétude | 0–3 | 0 = manquemants importants, 3 = couvre toutes les exceptions |
| Modalité (santé-sécurité) | 0–2 | 0 = transforme une obligation en recommandation ou inverse, 2 = modalité conservée |
| Sûreté opérationnelle | 0–3 | 0 = induirait un comportement dangereux, 3 = aligné avec les bonnes pratiques |
| Citations | 0–2 | 0 = aucune ou erronée, 2 = chaque affirmation citée correctement |

**Bonnes pratiques** :
- **Plusieurs annotateurs** par item (idéalement 2–3) pour mesurer l'accord inter-annotateurs (Kappa de Cohen, $\alpha$ de Krippendorff).
- **Annotation à l'aveugle** sur la configuration testée (l'annotateur ne sait pas quel système a produit la réponse).
- **Profil mixte** d'annotateurs : experts métiers et utilisateurs cibles, pour capturer expertise et utilisabilité.
- **Charte d'annotation** documentée et exemples gold pour calibrer.

**Limites** : coût, temps, subjectivité résiduelle, fatigue de l'annotateur, scalabilité.

#### 5.2.3. Approche hybride : screening automatique + validation humaine

L'idée est de combiner les deux approches pour que chacune compense les limites de l'autre :

1. **Screening automatique** d'abord, sur l'ensemble du jeu de test : toutes configurations, toutes questions. C'est rapide, ça donne des tendances, et ça permet de dégrossir avant d'y passer plus de temps.
2. **Sélection ciblée** d'un sous-ensemble pour annotation humaine : par exemple, les cas où le juge automatique et le score utilisateur divergent le plus (top-30 par exemple), plus une sélection de cas critiques santé-sécurité.
3. **Calibration** : l'échantillon annoté à la main sert à corriger les biais identifiés dans le LLM-juge, et à mieux interpréter ses scores sur le reste.
4. **Triangulation** : on ne conclut qu'en cas de convergence des deux approches. Les divergences ne sont pas jetées, elles valent souvent la peine d'être analysées.

### 5.3. Construction du jeu de test

La qualité du jeu de test conditionne la validité de toute l'évaluation. Cette section décrit la démarche méthodologique générique. L'instanciation pour ScribBERT figurera en Partie III.
\newpage
#### 5.3.1. Sources des questions

Quatre sources complémentaires :

1. **Questions "naturelles" issues de l'usage** : extraites des logs. Avantage : représentativité des intentions réelles.
2. **Questions générées par experts** : un panel d'experts santé-sécurité rédige des questions couvrant systématiquement les domaines, niveaux de risque, types de procédures.
3. **Questions générées par LLM à partir des documents** : pour chaque chunk pertinent, un LLM génère une question dont la réponse est dans le chunk. Permet une couverture exhaustive du corpus mais introduit un biais (questions trop bien formées).
4. **Questions adversariales** : questions hors-périmètre, ambiguës, formulations terrain (jargon, fautes), questions à réponses contradictoires dans le corpus. Test des garde-fous.

#### 5.3.2. Typologie des questions

Pour un protocole diagnostique, on stratifie le jeu de test selon plusieurs axes :

**Par type d'intention** :
- **Factuelles** ("Quelle est la hauteur minimale pour port du harnais ?") réponse courte, vérifiable.
- **Procédurales** ("Quelle est la procédure avant intervention en espace confiné ?") réponse multi-étapes.
- **Conditionnelles** ("Que faire si... ?") gestion des exceptions.
- **Comparatives** ("Quelle différence entre EPI niveau 1 et niveau 2 ?") agrégation multi-sources.
- **Justificatives** ("Pourquoi cette mesure est-elle requise ?") explication d'une norme.
- **Hors-périmètre** (test du refus contrôlé).

**Par niveau de difficulté** :
- **Facile** : la réponse est dans un seul passage explicite.
- **Moyen** : nécessite 2–3 passages.
- **Difficile** : exception ou condition à identifier, modalité subtile ou contradiction apparente à arbitrer.

**Par criticité métier** :
- **Élevée** : erreur potentiellement dangereuse (port d'EPI vital, procédure de mise en sécurité).
- **Moyenne** : erreur procédurale sans conséquence vitale immédiate.
- **Faible** : information administrative ou organisationnelle.

#### 5.3.3. Annotation

Pour chaque question, on annote :

- **réponse de référence** rédigée par un expert (idéalement validée par un second expert, mais time-consuming).
- **Passages de référence** : identifiants des chunks contenant l'information nécessaire et suffisante.
- **Métadonnées** : type, difficulté, criticité, document(s) source(s).
- **Variantes acceptables** (paraphrases de la réponse de référence, formats alternatifs).

#### 5.3.4. Volume et représentativité

Un ordre de grandeur utile pour un RAG d'entreprise est d'environ 150 à 300 questions annotées, créées selon les axes évoqués ci-dessus. Cela permet :

- des estimations stables des métriques globales (intervalle de confiance acceptable),
- des analyses par groupe (par type, par difficulté),
- la détection d'effets significatifs entre configurations.

En-deçà de 100 questions, les comparaisons entre configurations sont sujettes à un fort bruit statistique.

#### 5.3.5. Versioning

Le jeu de test évolue (corrections, ajouts, retraits). On versionne :
- le contenu (questions, réponses de référence, passages de référence),
- le corpus de référence (documents, chunks, embeddings) : un jeu de test n'a de sens que pour une version donnée du corpus,
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

Pour chaque configuration et chaque métrique : moyenne, médiane, écart-type, IQR, distribution (histogramme). Toujours rapporter la **distribution** et pas seulement la moyenne, particulièrement important pour la fidélité, où une moyenne à 0.85 peut masquer une queue de réponses gravement fausses.

#### 5.5.2. Tests de significativité

Pour comparer deux configurations sur une métrique :
- **Test apparié** (la même question est posée aux deux configurations) : Wilcoxon signed-rank (non paramétrique, robuste) ou test t apparié si distribution proche normale.
- **Correction multiple** si l'on teste plusieurs métriques ou plusieurs configurations simultanément (Bonferroni, Holm).
- **Effet plutôt que p-value seule** : rapporter la **taille d'effet** (différence moyenne, Cohen's $d$) et un intervalle de confiance.

#### 5.5.3. Stratification et analyses par sous-groupe

L'analyse par strate (type de question, difficulté, criticité) est essentielle : une amélioration moyenne de 5 % peut masquer une dégradation sur les questions difficiles, ce qui est inacceptable en santé-sécurité. On rapporte systématiquement les métriques par strate.

#### 5.5.4. Analyse d'erreurs typologique

Pour les cas d'échec, on construit une **typologie d'erreurs** raffinée à partir des observations :

| Catégorie | Description | Localisation probable |
|-----------|-------------|----------------------|
| Retrieval miss | Aucun passage pertinent dans le top-$k$ | Embedding / chunking / $k$ |
| Retrieval bruit | Passages tentants mais non applicables | Embedding / reranking |
| Hallucination factuelle | Affirmation non supportée | Génération / prompt |
| Omission d'exception | Règle correcte mais condition oubliée | Génération / contexte tronqué |
| Inversion de modalité | "doit" devenu "peut" | Génération / prompt |
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

Pour un système d'aide à la décision en santé-sécurité, la **variabilité** est un problème en soi : un préventeur qui obtient deux réponses différentes à la même question perd confiance, et plus gravement, peut prendre des décisions différentes selon le moment où il a posé la question. **La stabilité fait partie intégrante de la fiabilité**, au même titre que la justesse moyenne.

Cette dimension est aussi un **enjeu méthodologique** : si la variance intra-configuration est élevée, comparer deux configurations sur une exécution unique n'a pas de sens, le bruit de mesure dépasse l'effet à mesurer. L'évaluation de la stabilité conditionne donc la robustesse statistique des comparaisons du Chapitre 5.

### 6.2. Sources de variance dans un RAG

Je n'ai pas eu le temps de tester systématiquement toutes ces sources de variance sur ScribBERT (cf. limites, Ch. 10). La cartographie ci-dessous reste donc en partie théorique, fondée sur la littérature et sur quelques observations ponctuelles pendant le développement.

#### 6.2.1. Variance liée à la génération

- **Échantillonnage stochastique** (température, top-p) : effet direct sur la diversité lexicale ; à température élevée, le contenu factuel peut aussi varier.
- **Non-déterminisme des LLM propriétaires** : même à température 0, certaines API ne garantissent pas le déterminisme strict (parallélisme GPU, batching variable). OpenAI propose un paramètre `seed` et un identifiant `system_fingerprint` pour tracer le déterminisme effectif.
- **Choix de format** : le LLM peut produire des tournures différentes (puces vs phrases) à structure équivalente, ce qui inflige des comparaisons textuelles brutes.

#### 6.2.2. Variance liée au retrieval

- **ANN approximatif** : HNSW est généralement déterministe à structure d'index donnée, mais des reconstructions d'index produisent des graphes différents.
- **Égalités de scores** : plusieurs passages avec le même score peuvent être ordonnés arbitrairement.
- **Concurrence** : sur une base distribuée, l'ordre peut dépendre du shard répondant en premier.

#### 6.2.3. Variance liée à la formulation utilisateur

- **Paraphrases équivalentes** : "Quels EPI pour travail en hauteur ?" vs "Quels équipements de protection pour les travaux en hauteur ?".
- **Fautes typographiques et accents** : sensibilité variable des embeddings.
- **Niveau de spécificité** : "EPI travail en hauteur" vs "harnais antichute" ciblent la même règle mais avec des chemins de retrieval différents.
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

Cas binaire (réponse correcte/incorrecte) : on peut résumer par la **proportion de runs corrects** et signaler les questions avec un taux entre 30 % et 70 % comme "instables".

#### 6.3.2. Robustesse aux paraphrases (sensibilité linguistique)

Pour chaque requête $q$, on génère $m$ paraphrases (par LLM ou manuellement) et on mesure :

- **Stability@paraphrase** : variantes des métriques ci-dessus, mais entre la requête originale et ses paraphrases.
- **Answer consistency** : un LLM-juge évalue si les réponses aux paraphrases véhiculent la *même information factuelle* (au-delà des différences de surface).

Cette mesure est complémentaire : un système peut être stable inter-runs (à requête identique) mais fragile aux paraphrases.

#### 6.3.3. Robustesse à l'ordre des passages

Sensibilité au **lost-in-the-middle** : on permute l'ordre des passages dans le contexte et on mesure la variation de la réponse. Un système robuste produit des réponses sémantiquement équivalentes quel que soit l'ordre.

#### 6.3.4. Self-consistency (cohérence interne)

Méthode popularisée par Wang et al. (2022) : on génère $n$ réponses à température > 0, on extrait la réponse "majoritaire" par vote ou agrégation. Le **taux d'accord** entre les $n$ réponses est un indicateur de confiance interne du modèle.[@Wang2022SelfConsistency] Si l'accord est faible, c'est un signal de difficulté ou d'ambiguïté.

### 6.4. Sensibilité aux paramètres et aux variations adverses

Au-delà des variations "normales", un protocole de stabilité robuste teste des perturbations contrôlées :

- **Fautes injectées** : substitutions de caractères, omissions, accents incorrects.
- **Reformulations adversariales** : reformulations qui préservent l'intention mais utilisent un vocabulaire différent (jargon chantier, anglicismes).
- **Bruit dans le contexte** : ajout de chunks non pertinents pour mesurer la résistance à la dilution.
- **Corpus avec contradictions** : injection de variantes contradictoires pour tester la détection.
- **Questions pièges** : questions hors-périmètre, questions à présupposés faux ("Quelle est la procédure pour ne pas porter de harnais ?").

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

- **Exposer l'incertitude** : afficher un score de confiance, ou indiquer explicitement "plusieurs réponses possibles selon le contexte de chantier".
- **Stabiliser les éléments critiques** sans figer les éléments stylistiques : la liste d'EPI doit être identique, mais la formulation peut varier.

Ces principes seront discutés en Partie III à la lumière des résultats observés sur ScribBERT.

### 6.7. Synthèse de la Partie II

Les chapitres 4 à 6 ont défini un cadre méthodologique complet :

- **Ch. 4** a inventorié les leviers techniques actionnables (embedding, chunking, retrieval, génération) avec leurs compromis ;
- **Ch. 5** a structuré le protocole d'évaluation autour des cinq dimensions de la fiabilité, avec des approches automatiques, humaines et hybrides ;
- **Ch. 6** a approfondi la dimension stabilité, sous-traitée mais critique pour un déploiement en production.

La Partie III instancie ce cadre sur ScribBERT : architecture déployée (Ch. 7), résultats expérimentaux (Ch. 8a-8b), enjeux de gouvernance (Ch. 9) et discussion (Ch. 10).



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

Ce choix d'une stack majoritairement open-source et auto-hébergée répond aux contraintes de **confidentialité** (les référentiels santé-sécurité peuvent contenir des informations sensibles sur les sites et les procédures) et d'**indépendance** vis-à-vis de fournisseurs externes pour une éventuelle exploitation à long terme.

#### 7.2.3. Pipeline d'ingestion

Le pipeline d'ingestion transforme un PDF source en chunks indexés. Étapes :

1. **Extraction** : conversion PDF → Markdown via **[À compléter : outil retenu, ex. pymupdf, marker, unstructured]**, choix qui préserve mieux la mise en forme (titres, listes, tableaux) que l'extraction texte brut.
2. **Nettoyage** : suppression des en-têtes/pieds de page répétitifs, normalisation des caractères spéciaux.
3. **Chunking** : découpage par regex sur les marqueurs structurels (titres Markdown `#`, `##`, séparateurs de paragraphes), avec contrainte de taille cible (~1200 tokens) et overlap (~50 tokens). Détails en § 7.4.
4. **Enrichissement métadonnées** : ajout pour chaque chunk de : `nom_document`, `entité_émettrice`, `langue`, `position_dans_doc`.
5. **Embedding** : calcul vectoriel via le modèle retenu (§ 7.5).
6. **Indexation** : insertion dans ChromaDB avec la collection appropriée.

L'étape 1 est actuellement la plus fragile : les PDFs santé-sécurité comportent souvent des **tableaux** (tableaux de risques, matrices RACI, tableaux d'EPI par activité) et des **schémas** (logigrammes de procédure, schémas d'installation). Dans le POC, ces éléments sont **ignorés** ou linéarisés grossièrement. Pour la version production, une chaîne **image-to-text contextualisée** est en cours d'étude : un modèle multimodal génère une description textuelle de chaque image/tableau, conserve le lien vers l'image originale, et l'injecte comme un chunk enrichi. Cette piste sera évaluée séparément (Ch. 10, perspectives).

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

À noter : à terme, l'extension envisagée couvre les référentiels santé-sécurité de l'ensemble des filiales et chantiers de Bouygues TP, ce qui multiplierait le volume par un ordre de grandeur et ferait apparaître des problématiques nouvelles (variantes locales, contradictions inter-entités, multilinguisme étendu).

### 7.4. Choix de chunking et prétraitement

Conformément à la grille du Ch. 4.2, la stratégie retenue est un **chunking structurel custom**, justifié comme suit :

- les documents PDF sont d'abord convertis en **Markdown** pour préserver la hiérarchie (titres, listes, mise en forme) qui est porteuse de sens dans des référentiels normatifs ;
- des **expressions régulières** identifient les séparateurs structurels (titres `#`, `##`, `###`, paragraphes) et découpent le texte en unités correspondant à des **paragraphes ou sous-sections** ;
- la cible de taille est d'**environ 1200 tokens** par chunk, ce qui correspond empiriquement à un compromis entre :
  - assez large pour contenir une règle complète avec ses conditions et ses exceptions (cf. risque d'omission identifié au Ch. 5.5.4),
  - assez petit pour rester discriminant à l'embedding et économique en tokens lors de l'injection dans le contexte LLM ;
- l'**overlap est de ~50 tokens**, soit une valeur faible (≈ 4 %), qui suffit à amortir des coupures malheureuses sans gonfler significativement l'index ;
- une **fenêtre contextuelle** est ajoutée à la récupération : pour chaque chunk retourné par le retrieval, les chunks $n-1$ et $n+1$ sont automatiquement adjoints avant injection dans le contexte LLM. Cette mécanique compense un overlap faible et restaure le contexte amont/aval, particulièrement utile pour les références anaphoriques ("cette règle", "les EPI mentionnés") et pour la cohérence procédurale.

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

Le **filtrage par score** est une garde-fou simple mais efficace : si aucun chunk ne dépasse le seuil, le système retourne un message "information non trouvée dans les référentiels" plutôt que de générer une réponse non ancrée. Cela répond directement à l'exigence de **refus contrôlé** (Ch. 4.4.6).

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
3. **Pas de gestion des tableaux et schémas** : pertes informationnelles sur des contenus à forte valeur santé-sécurité (matrices de risques, logigrammes).

Ces trois axes constituent les priorités pour le passage en production, et seront discutés en perspective au Ch. 10.

## Chapitre 8a — Résultats quantitatifs

> **Note méthodologique** : les retours utilisateurs collectés lors de la phase de test ont été qualitatifs et globalement positifs. Aucun protocole d'évaluation automatisé selon le cadre des Ch. 5 et 6 n'a été instancié de bout en bout au moment de la rédaction. Je préfère être transparent là-dessus plutôt que de présenter des résultats incomplets comme s'ils étaient définitifs. Ce chapitre est donc structuré comme un **plan d'évaluation à exécuter**, avec des emplacements `[À compléter]` pour les valeurs à mesurer.

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
- une réponse de référence attendue,
- les passages de référence (chunks contenant l'information nécessaire),
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
| Modality preservation (santé-sécurité) | [...] |

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
- proportion d'erreurs "localisées au retrieval" vs "localisées à la génération" (typologie Ch. 5.5.4) ;
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
- **réponse de référence** attendue ;
- **Diagnostic** (succès, type d'échec, localisation dans la chaîne) ;
- **Enseignement** transverse pour le système.

### 8b.4. Cas limites et ambiguïtés

Trois familles de cas limites identifiées dès la phase POC :

#### 8b.4.1. Acronymes et jargon métier

Les utilisateurs santé-sécurité emploient des acronymes (EPI, ATEX, EPC, PDP, etc.) que les embeddings généralistes peuvent mal contextualiser. **[À compléter : observations spécifiques sur la sensibilité du système retenu]**.

#### 8b.4.2. Multilinguisme et code-switching

Le corpus étant ~50 % anglophone, les questions FR peuvent attendre une réponse appuyée sur des passages EN (et vice-versa). **[À compléter : qualité observée sur les requêtes cross-lingue]**.

#### 8b.4.3. Hors-périmètre

Questions sortant du périmètre santé-sécurité ("Quel est le congé maternité ?", "Combien gagne un chef de chantier ?"). Le système doit refuser ; observer si le filtre par score est suffisant ou si des cas se faufilent. **[À compléter]**.

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
- **Qualité des données d'entraînement** : moins applicable ici (RAG, pas de fine-tuning), mais la **qualité du corpus** est un équivalent fonctionnel.
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
3. **Traçabilité des décisions** : si une décision opérationnelle (ex. report d'une intervention) s'appuie sur une réponse de ScribBERT, la trace doit être conservée, avec la version du modèle, la version du corpus et la réponse exacte, pour permettre une analyse a posteriori.

### 9.3. Responsabilité en contexte santé-sécurité

#### 9.3.1. La question de la responsabilité

En cas d'accident sur chantier, si une décision de prévention s'appuie sur une réponse erronée de ScribBERT, qui est responsable ? Plusieurs niveaux d'analyse :

- **Responsabilité juridique** : l'employeur reste responsable de la sécurité de ses salariés (Code du travail français). L'outil IA n'est qu'un moyen.
- **Responsabilité du système** : l'éditeur (ici Bouygues TP en tant que développeur interne) doit pouvoir documenter ses choix et ses tests (cf. AI Act).
- **Responsabilité de l'utilisateur** : le préventeur reste tenu de son devoir de vérification, ce qui justifie le **disclaimer affiché**.

#### 9.3.2. Le disclaimer comme mesure de mitigation

ScribBERT affiche actuellement un **disclaimer permanent** rappelant que :
- la responsabilité de la qualité des réponses n'incombe pas au système ;
- l'utilisateur doit faire appel à son **esprit critique** et **vérifier les documents sources** avant toute action opérationnelle.

Ce disclaimer est une mesure nécessaire mais **non suffisante** : la jurisprudence européenne sur les outils d'aide à la décision tend à considérer qu'un disclaimer ne dégage pas l'éditeur de toute responsabilité, particulièrement si l'outil est présenté comme "expert" ou "fiable". Les renforcements possibles incluent :

- afficher un **score de confiance** par réponse, pour calibrer la vigilance ;
- **mettre en avant les sources** plus que la réponse synthétisée, l'utilisateur étant ainsi systématiquement renvoyé au document validé ;
- pour les réponses critiques (port d'EPI vital, mises en sécurité), recommander explicitement la **consultation d'un référent santé-sécurité** humain.

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
- **Comité de gouvernance** réunissant IT, métier, juridique, sécurité, décisionnaire sur les évolutions majeures.

### 9.5. Acceptabilité et conduite du changement

La meilleure technologie échoue si les utilisateurs ne l'adoptent pas. Trois facteurs ont été identifiés comme déterminants pour ScribBERT :

1. **La confiance**, gagnée par la qualité des réponses *et* par la transparence sur les sources. Les retours utilisateurs (§ 8b.6) confirment que la présence systématique des citations est un facteur clé d'adoption.
2. **L'utilité perçue** par rapport à l'alternative (recherche manuelle dans les PDF, demande à un expert). ScribBERT doit faire gagner du temps **sans dégrader la qualité de la décision**.
3. **L'accompagnement** : formation initiale, communication interne, identification d'**ambassadeurs** dans les équipes pour porter l'outil.

Une perspective intéressante est de considérer ScribBERT non pas comme un **substitut** à l'expert santé-sécurité, mais comme un **amplificateur** : il permet aux préventeurs de répondre plus vite aux questions répétitives, libérant du temps pour les sujets complexes qui requièrent un jugement humain.

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

Le jeu de test interne (~20 questions) est insuffisant pour des comparaisons statistiques fines (cf. Ch. 5.3.4). Une priorité immédiate est l'**extension à 150–300 questions** stratifiées, avec annotation des passages de référence et réponses de référence par des experts P2S.

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

- **Fine-tuning d'un modèle d'embedding sur le corpus santé-sécurité** (apprentissage contrastif sur paires question/passage), pour combler le manque de modèles spécialisés santé-sécurité/BTP identifié au Ch. 4.1.1.
- **GraphRAG** : exploiter une représentation en graphe des entités santé-sécurité (procédures, EPI, risques, situations) pour des requêtes nécessitant un raisonnement multi-saut.
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

À court terme, ScribBERT bénéficiera de l'application complète du protocole d'évaluation, de l'extension du jeu de test, et de l'intégration des améliorations identifiées (hybrid retrieval, reranking, gestion des tableaux). À moyen terme, le fine-tuning d'un modèle d'embedding sur le corpus santé-sécurité et l'exploration de variantes (GraphRAG, agentic RAG, RAG multimodal) constituent des axes de recherche pertinents. Le cadre méthodologique proposé est par ailleurs transférable à d'autres domaines réglementaires et techniques.

### Mot de la fin

L'industrialisation des systèmes RAG dans des contextes critiques est une réalité opérationnelle croissante, mais leur évaluation rigoureuse reste un chantier ouvert. Ce mémoire entend y contribuer en proposant un cadre transférable, en assumant que la fiabilité d'un système d'IA n'est pas un attribut binaire à proclamer, mais une propriété multi-dimensionnelle à mesurer, à éprouver, et à gouverner dans le temps.

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
| **Hallucination** | Génération par un LLM d'informations plausibles mais factuellement incorrectes ou non supportées par les sources. Risque majeur en contexte RAG et santé-sécurité. |
| **Hard negatives** | Exemples négatifs (passages non pertinents) sémantiquement proches de la requête, utilisés pour entraîner des retrievers denses à mieux discriminer les passages réellement pertinents. |
| **HNSW** (*Hierarchical Navigable Small World*) | Structure d'index pour la recherche approximative du plus proche voisin, basée sur des graphes navigables hiérarchiques. Utilisée dans FAISS, Qdrant, etc. |
| **santé-sécurité** (*Hygiène, Sécurité, Environnement*) | Domaine de la prévention des risques professionnels et de la sécurité au travail. Contexte métier du cas d'usage ScribBERT. |
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

---

## Bibliographie

::: {#refs}
:::


