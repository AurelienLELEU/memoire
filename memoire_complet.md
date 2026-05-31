# Mémoire : Évaluation de la cohérence et de la fiabilité d'un système RAG (cas d'usage : ScribBERT)

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

- **Partie I** - Cadre conceptuel et théorique : les fondements du RAG, l'histoire de la recherche d'information, et les notions de pertinence et de cohérence qui sous-tendent l'évaluation.
- **Partie II** - Méthodologie d'évaluation : construction du protocole, choix des métriques, conditions expérimentales.
- **Partie III** - Application et discussion : mise en œuvre sur ScribBERT, résultats, et recommandations.

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

# PARTIE I - Cadre conceptuel et état de l'art

Cette première partie replace les systèmes de **Retrieval-Augmented Generation (RAG)** dans l'histoire des méthodes de recherche d'information. Elle vise ensuite à formaliser les notions de **pertinence** et de **cohérence/fidélité** qui seront au cœur du protocole d'évaluation.

Deux constats structurent cette partie :

1. Un RAG n'est pas "un LLM + des documents". C'est une **chaîne de décision** (découpage, indexation, recherche, assemblage du contexte, génération) dont les erreurs/imprécisions s'additionnent parfois.
2. Les critères d'évaluation de l'IR (recherche d'information) classique et ceux des LLMs ne se recouvrent pas. On peut avoir un excellent score de retrieval et une réponse finale fausse.

## Chapitre 1 - De la recherche documentaire à la recherche sémantique

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

## Chapitre 2 - Les fondements du RAG (Retrieval-Augmented Generation)

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

Un mot sur le **chunking**, qui est souvent décrit comme un paramètre "d'ingestion" mais correspond en réalité à un choix de modélisation : **quelle est l'unité minimale (et maximale également) de connaissance** que le système peut retrouver et citer ?

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

En pratique, les systèmes robustes adoptent une architecture *multi-stage* qui répond directement à ce dilemme : un **retrieval large** (top-$k$ élevé) maximise le rappel, un **reranking** par cross-encoder augmente ensuite la précision sur ce petit ensemble candidat[@NogueiraCho2019], et une **sélection/assemblage** finale respecte la limite de contexte du générateur. Chaque étage a un effet direct sur la fidélité : un retrieval trop large sans reranking augmente le bruit, un reranking mal calibré peut favoriser des passages "proches" mais moins normatifs, et une sélection trop agressive peut écarter des passages qui auraient été utiles.

### 2.6. "Grounding", citations et attribution : de la preuve à la confiance

Citer une source ne suffit pas. En testant ScribBERT, j'ai vu des cas où le système citait un document qui n'avait qu'un rapport lointain avec la question et c'est pire que l'absence de citation, car ça donne une illusion de rigueur. La littérature formalise cette intuition en distinguant trois dimensions : la *context relevance* (le contexte récupéré est-il utile ?), l'*answer relevance* (la réponse traite-t-elle la question ?) et la *faithfulness* (la réponse est-elle supportée par le contexte ?). Ces trois dimensions ne se recouvrent pas, et c'est précisément ce qui rend l'évaluation complexe.

### 2.7. RAG et mémoire : connaissances paramétriques vs non-paramétriques

On distingue la "mémoire paramétrique" d'un LLM (ses poids) et la "mémoire non-paramétrique" (une base documentaire externe, interrogée à la volée). Un modèle assez gros peut stocker beaucoup de faits dans ses paramètres[@Roberts2020], mais avec des limites évidentes en mise à jour et vérifiabilité (éxpliquées plus tôt). Pour ScribBERT, la mémoire non-paramétrique est préférée parce qu'elle est auditable : on sait quels documents ont été consultés, et on peut les mettre à jour sans toucher au modèle.

### 2.8. Pourquoi la notion de "source" est centrale en contexte santé-sécurité

Dans une application santé-sécurité, on ne veut pas de réponse "créative" : on attend une réponse normative ou procédurale, fondée sur les bons documents. La qualité tient alors à des questions très concrètes : le système distingue-t-il une procédure groupe validée d'une note informelle ? Respecte-t-il la différence entre "doit" et "devrait" ? Mentionne-t-il les exceptions ? Ces exigences, bien plus strictes que dans un chatbot grand public, imposent de centrer l'évaluation sur la fidélité aux sources, ce qui sera l'objet de la Partie II.

## Chapitre 3 - La question de la "pertinence" et de la "cohérence"

Les mots "pertinence" et "cohérence" reviennent constamment aussi bien dans ce mémoire que quand on parle de qualité d'un RAG, mais ils recouvrent des réalités assez différentes selon les interlocuteurs. Ce chapitre tente de les clarifier, non pas par amour pour la taxonomie, mais plutôt parce que la qualité d'un protocole d'évaluation dépend directement de ce qu'on en attend.

### 3.1. Définir la pertinence : une notion multi-dimensionnelle

En recherche d'information, la pertinence est un mélange entre un besoin, un utilisateur, un contexte et un document, à un moment donné. La littérature académique insiste depuis longtemps sur cette complexité et sur l'écart entre ce qu'un système juge pertinent et ce que l'utilisateur considère comme pertinent.[@Saracevic1996; @Mizzaro1997] Pour un RAG, plusieurs dimensions s'ajoutent à la simple adéquation thématique.

Un passage peut parler du bon sujet sans être utile pour autant. La **pertinence situationnelle** dépend du rôle de l'utilisateur, de la phase du chantier, des contraintes de site : une procédure générale ne sert pas à un compagnon qui a besoin d'une consigne précise. L'**exhaustivité** est critique quand il cherche une procédure complète : une réponse correcte mais à laquelle il manque une étape ou une exception peut être dangereuse. La **granularité** pose la question inverse : trop de détails peut noyer l'information, surtout si le format attendu est une check-list courte.

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

Pour expliciter la suite, on rappelle quelques définitions courantes du côté retrieval, sur un ensemble de requêtes $Q$. On note $\mathrm{TopK}(q)$ l'ensemble des $k$ premiers passages récupérés pour la requête $q$, et $\mathrm{Rel}(q)$ l'ensemble des passages pertinents (selon l'annotation).

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

# PARTIE II - Méthodologie d'évaluation d'un système RAG

La Partie I a posé les bases : ce qu'est un RAG, ce que signifient "pertinence" et "cohérence" dans ce contexte, et pourquoi ces notions sont si délicates à évaluer quand l'enjeu est la sécurité des collaborateurs. La Partie II entre dans le concret.

Je dois admettre que la question de l'évaluation m'a à l'origine paru plus simple qu'elle ne l'est en réalité. Au début du développement de ScribBERT, je procédais par tâtonnement : je testais une configuration, je posais quelques questions, j'observais si les réponses "avaient l'air bonnes". Sauf que cette approche montre vite ses limites : à chaque modification de paramètre (stratégie de chunking, modèle d'embedding, valeur de $k$), une question qui marchait bien se dégradait, et une autre qui échouait s'améliorait. Il n'y avait pas de progression nette, pas de signal clair. C'est cette frustration qui m'a conduit à formaliser un protocole d'évaluation rigoureux.

Trois questions structurent cette partie :

1. **Quels leviers techniques** influencent la qualité d'un RAG, et comment les caractériser (Chapitre 4) ?
2. **Quel protocole** mettre en place pour mesurer cette qualité de façon reproductible (Chapitre 5) ?
3. **Comment évaluer la cohérence** (fidélité aux sources, stabilité), qui est la dimension la plus difficile à automatiser (Chapitre 6) ?

L'ambition est de proposer un cadre transférable, pas spécifique à ScribBERT, mais qui sera instancié sur ce cas en Partie III.

## Chapitre 4 - Modèles et paramètres influençant la performance

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

## Chapitre 5 - Construction d'un protocole d'évaluation

Le Chapitre 4 a inventorié les différents leviers actionnables. Reste la question fondamentale : **comment mesurer leur effet ?** Sans un protocole d'évaluation structuré, on en revient au tâtonnement décrit plus haut : on modifie un paramètre, on pose trois questions, on a "l'impression" que c'est mieux ou moins bien, sans pouvoir trancher.

Ce que je cherche ici, c'est un protocole qui produise des mesures reproductibles (le même test donne le même résultat), comparables (on peut ordonner des configurations), et surtout diagnostiques, qui permettent de dire où se situe le problème dans la chaîne, pas seulement que la réponse finale est "bonne" ou "mauvaise".

Ce chapitre s'organise en cinq sections : les critères d'évaluation (§ 5.1), les approches (automatique, humaine, hybride) (§ 5.2), la construction du jeu de test (§ 5.3), les conditions expérimentales (§ 5.4), et les méthodes d'analyse (§ 5.5).

### 5.1. Cinq dimensions pour mesurer la fiabilité

Plutôt que de dresser une liste plate de métriques, j'organise l'évaluation autour des **cinq dimensions de la fiabilité** définies au Chapitre 3. Pour chacune, la question centrale est : quel type d'échec cherche-t-on à détecter ?

#### 5.1.1. Dimension 1 - Pertinence du retrieval

*Les passages récupérés contiennent-ils l'information nécessaire pour répondre ?*

C'est le premier maillon de la chaîne, et si le retrieval rate la bonne règle, rien dans la suite ne peut compenser. Plusieurs métriques permettent de le mesurer, selon l'angle qui nous intéresse :

- **Hit@k** : est-ce qu'au moins un passage pertinent figure dans les $k$ résultats retournés ? C'est la mesure la plus simple : une réponse binaire "oui/non" par question.
- **Recall@k** : quelle proportion des passages pertinents a été retrouvée ? Utile quand la réponse attendue nécessite plusieurs sources distinctes.
- **Precision@k** : parmi les $k$ passages retournés, combien sont réellement utiles ? Un retrieval avec beaucoup de bruit nuit à la génération même si les bons passages sont là.
- **MRR** (Mean Reciprocal Rank) : le premier passage pertinent est-il bien classé en tête ? C'est la bonne métrique quand on attend principalement un passage décisif.
- **nDCG@k** : variante pondérée qui tient compte de la position (un passage pertinent classé 2ème est meilleur que le même classé 8ème). Utile si les jugements de pertinence sont gradués (très pertinent / un peu pertinent / hors-sujet).

Pour ScribBERT, **Recall@k** et **MRR** sont les métriques principales : l'enjeu est avant tout de s'assurer que la "bonne règle" figure bien parmi les passages remontés. Le Hit@k est un bon complément rapide pour les questions qui n'ont qu'un seul passage.

#### 5.1.2. Dimension 2 - Fidélité aux sources (*faithfulness*)

*La réponse s'en tient-elle à ce que disent vraiment les passages récupérés ?*

C'est la dimension la plus critique pour ScribBERT. Une réponse peut être fluide et cohérente, mais complètement inexacte, soit parce que le modèle a "rajouté" des éléments absents des sources, soit parce qu'il a modifié le sens. L'enjeu n'est pas seulement la véracité des faits, c'est la conformité aux sources fournies.

Plusieurs approches permettent de mesurer ça automatiquement :

- **Faithfulness (RAGAS)** : la réponse est décomposée en propositions atomiques ("le port du harnais est obligatoire dès 2 m"), et chacune est vérifiée contre le contexte par un LLM-juge. Le score final est la proportion de propositions supportées.
- **NLI-based scoring** : un modèle d'inférence textuelle (NLI) vérifie si chaque phrase de la réponse est logiquement impliquée par le contexte. Plus robuste pour les phrases longues que l'approche atomique.
- **Citation faithfulness** : quand la réponse cite un passage explicitement, vérifie-t-on que ce passage supporte réellement l'affirmation ? C'est une vérification de cohérence entre la citation et le contenu.
- **Hallucination rate** : simplement le taux de propositions non supportées (= 1 − faithfulness).

À ces métriques génériques, on peut ajouter en contexte santé-sécurité une mesure plus spécifique : la **préservation des modalités** : la réponse respecte-t-elle les niveaux d'obligation des sources ("doit" vs "peut" vs "il est recommandé de") ? Cette dimension est difficile à automatiser de façon fiable et nécessite souvent une vérification humaine ou un LLM-juge avec des instructions très précises à ce sujet.

#### 5.1.3. Dimension 3 - Pertinence et complétude de la réponse

*La réponse dit-elle ce qu'il faut, ni plus ni moins ?*

Cette dimension évalue la réponse en tant que telle, indépendamment de ses sources : est-ce qu'elle répond vraiment à ce qui était demandé ? Est-ce qu'elle est complète ? Est-ce qu'elle est calibrée en longueur ?

- **Answer relevance (RAGAS)** : un LLM-juge génère plusieurs questions hypothétiques à partir de la réponse produite, puis mesure si elles ressemblent à la question originale. Une réponse hors-sujet ou vague produira des questions hypothétiques éloignées.
- **Complétude** : en comparaison avec une réponse de référence annotée par un expert, quelle proportion des éléments attendus (étapes, conditions, exceptions) est présente dans la réponse générée ?
- **Concision** : la réponse est-elle proportionnée à la complexité de la question, ou le modèle noie-t-il l'information dans une réponse excessivement longue ?
- **Respect du format** : si le prompt demande une check-list numérotée, le modèle l'a-t-il bien produite ?

#### 5.1.4. Dimension 4 - Stabilité et répétabilité

*Si l'on rejoue la même question, la réponse est-elle cohérente ?*

Un système peut obtenir de bons scores en moyenne tout en produisant des réponses très variables d'une exécution à l'autre. Cette dimension, traitée en détail au Chapitre 6, mesure la **variance** des réponses plutôt que leur qualité moyenne. Elle conditionne également la robustesse statistique de toutes les comparaisons du protocole : si la variabilité intra-configuration est élevée, comparer deux configurations sur une seule exécution par question n'a pas de sens.

#### 5.1.5. Dimension 5 - Traçabilité et auditabilité

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
- **Comparatives** ("Quelle différence entre... ?") agrégation multi-sources.
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

Pour ce mémoire, l'approche OFAT sera privilégiée pour les comparaisons principales.

#### 5.4.2. Configuration de référence (*baseline*)

Toute expérience compare à une configuration de référence documentée :
- modèle d'embedding et version exacte,
- stratégie et paramètres de chunking,
- type de retrieval et top-$k$,
- modèle de génération et version exacte,
- prompt complet,
- paramètres de décodage (température, max tokens,...).

Cette baseline est elle-même l'objet d'une évaluation initiale, sur l'ensemble des dimensions, qui sert de point de comparaison pour toutes les variantes.

#### 5.4.3. Reproductibilité

Pour qu'une expérience soit reproductible :
- **fixer les seeds** (générateur, ANN si applicable) ;
- **figer les versions** des modèles (un même nom de modèle peut être mis à jour silencieusement par le fournisseur) ;
- **logger** la requête, le contexte récupéré, la réponse complète, les métadonnées de chaque passage ;
- **archiver** les jeux de test versionnés et les résultats bruts.

Lorsque la reproductibilité parfaite est impossible (LLM propriétaires non déterministes), on rapporte des **distributions** sur $n$ runs (médiane et IQR) plutôt que des valeurs ponctuelles.

### 5.5. Méthodes d'analyse

#### 5.5.1. Statistiques descriptives

Pour chaque configuration et chaque métrique analyser la moyenne, médiane, écart-type, IQR et distribution (histogramme). La moyenne seule ne suffit pas, un score de fidélité à 0,85 peut très bien cacher 15 % de réponses complètement inventées, ce qui est inacceptable en santé-sécurité.

#### 5.5.2. Tests de significativité

Pour comparer deux configurations sur une métrique :
- **Test apparié** (la même question est posée aux deux configurations) : préférer le test de Wilcoxon signed-rank, non paramétrique et robuste. Le test t apparié reste possible si la distribution des différences est proche de la normale.
- **Correction multiple** si l'on teste plusieurs métriques ou plusieurs configurations simultanément (Bonferroni, Holm).
- **Effet plutôt que p-value seule** : rapporter la **taille d'effet** (différence moyenne, Cohen's $d$) et un intervalle de confiance.

#### 5.5.3. Stratification et analyses par sous-groupe

L'analyse par strate (type de question, difficulté, criticité) est essentielle : une amélioration moyenne de 5 % peut masquer une dégradation sur les questions difficiles, ce qui est inacceptable en santé-sécurité. On rapporte systématiquement les métriques par strate pour être sûr que l'amélioration soit à tous les niveaux.

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


### 5.5. Synthèse

Le protocole proposé articule cinq dimensions de la fiabilité (retrieval, fidélité, pertinence, stabilité et traçabilité) avec trois approches d'évaluation (automatique, humaine, hybride), appliquées sur un jeu de test stratifié dans des conditions expérimentales reproductibles, et analysées avec des outils statistiques adaptés.

Le Chapitre 6 approfondit la dimension **stabilité**, qui mérite un traitement spécifique car elle est sous-traitée par les frameworks usuels et particulièrement critique pour un système RAG en production sur un sujet sensible.

## Chapitre 6 - Évaluation de la stabilité et de la répétabilité

### 6.1. Pourquoi la stabilité est une dimension distincte de la fiabilité

Les métriques classiques d'évaluation d'un RAG évoquées plus tôt sont calculées sur une exécution unique d'une requête. Elles décrivent la qualité moyenne d'une réponse à un instant t, mais ne disent rien sur ce qui se passe si l'on rejoue la même requête ou si l'utilisateur formule légèrement différemment sa question.

Or trois phénomènes rendent un RAG intrinsèquement variable :

1. **Stochasticité de la génération** : à température > 0, le LLM échantillonne à chaque token, conduisant à des réponses différentes pour une même entrée.
2. **Approximation du retrieval** : les algorithmes ANN (HNSW, IVF) introduisent une approximation contrôlée mais réelle ; deux exécutions strictement identiques peuvent même retourner des ordres légèrement différents selon l'implémentation, les égalités de scores (plusieurs passages au même score ordonnés arbitrairement) et la concurrence (sur un index distribué, l'ordre dépend du shard répondant en premier).
3. **Sensibilité au prompt et à la formulation** : une question tournée différement peut modifier le top-$k$ retourné et donc la réponse.

Pour un système d'aide à la décision en santé-sécurité, la **variabilité** est un problème. Un préventeur ou compagnon qui obtient deux réponses différentes à la même question perd confiance, et plus gravement, peut prendre des décisions différentes selon le moment où il a posé la question. La stabilité fait partie intégrante de la fiabilité (fiabilité apparente à minima), au même titre que la justesse moyenne.

Cette dimension est aussi un enjeu méthodologique : si la variance au sein d'une même configuration est élevée, comparer deux configurations sur une exécution unique n'a pas de sens, le bruit de mesure dépasse l'effet à mesurer. L'évaluation de la stabilité conditionne donc la robustesse statistique des comparaisons du Chapitre 5.

### 6.2. Sources de variance dans un RAG

Je n'ai pas eu le temps de tester systématiquement ces sources de variance sur ScribBERT (cf. limites, Ch. 10). La cartographie ci-dessous reste donc en partie théorique, fondée sur la littérature et sur quelques observations ponctuelles pendant le développement.

Côté **génération**, la variance vient d'abord de l'échantillonnage stochastique (température, top-p) qui agit sur la diversité lexicale et, à température élevée, sur le contenu factuel lui-même. Même à température 0, le non-déterminisme persiste sur les LLM propriétaires : parallélisme GPU et batching variable empêchent un déterminisme strict, et il faut s'appuyer sur des paramètres dédiés (`seed`, identifiant `system_fingerprint` côté OpenAI / Azure OpenAI) pour tracer ce qui est effectivement reproductible. S'y ajoutent les choix de format : un même contenu peut être rendu en puces ou en phrases, ce qui fausse toute comparaison textuelle brute. Les sources de variance côté retrieval (approximation ANN, égalités de scores, concurrence sur index distribué) ont déjà été décrites en § 2.2, § 3.2 et § 6.1, et ne sont pas reprises ici.

Côté **formulation utilisateur**, deux requêtes sémantiquement équivalentes peuvent produire des réponses différentes : paraphrases ("Quels EPI pour travail en hauteur ?" vs "Quels équipements de protection pour les travaux en hauteur ?"), fautes d'orthographe et accents (auxquels les embeddings sont inégalement sensibles), niveau de spécificité ("EPI travail en hauteur" vs "harnais antichute" qui ciblent la même règle par des chemins différents) ou code-switching FR/EN ponctuel.

Enfin, à plus long terme, une **dérive temporelle** s'installe : mise à jour silencieuse des modèles propriétaires (un `gpt-4o-2024-08-06` peut être déprécié et remplacé), évolution du corpus (ajouts, retraits, révisions de procédures), et dérive de l'index dès que la stratégie de chunking ou d'embedding est modifiée.

### 6.3. Métriques de stabilité

Le cas le plus simple est la **stabilité inter-runs** : à requête et configuration constantes, on exécute le système $n$ fois (typiquement $n \in [5, 20]$) et on mesure le recouvrement des sorties. Côté retrieval, on calcule un **Stability@retrieval** comme indice de Jaccard moyen des ensembles de chunks récupérés entre paires de runs. Le Jaccard mesure le recouvrement entre deux ensembles, défini comme le rapport entre la taille de leur intersection et celle de leur union : $\mathrm{J}(A_i, A_j) = |A_i \cap A_j| / |A_i \cup A_j|$. Il vaut 1 si les deux runs retournent exactement les mêmes chunks, 0 s'ils sont disjoints. La même mesure peut être restreinte aux chunks effectivement **cités** dans la réponse (et non simplement récupérés), ce qui est souvent plus informatif sur la fidélité perçue. Côté génération, un **BERTScore moyen** entre paires de réponses donne une stabilité sémantique, qu'on complète par l'écart-type inter-runs des métriques de qualité (faithfulness, Recall@k…) et par un **flip rate** : taux de questions pour lesquelles le verdict (réponse acceptable / inacceptable) change entre runs. Dans le cas binaire correct/incorrect, on résume par la proportion de runs corrects et on flague comme "instables" les questions dont ce taux se situe entre 30 % et 70 %.

Cette stabilité à requête identique ne suffit pas : un système peut être stable inter-runs et fragile aux **paraphrases**. Pour chaque requête, on génère donc $m$ reformulations et on applique les mêmes métriques entre la requête originale et ses variantes, en confiant à un LLM-juge la vérification que les réponses véhiculent bien la même information factuelle au-delà des différences de surface. Dans le même esprit, on peut tester la **robustesse à l'ordre des passages** (sensibilité au *lost in the middle*) en permutant l'ordre des chunks injectés dans le contexte : un système robuste produit des réponses sémantiquement équivalentes quel que soit l'ordre.

### 6.4. Sensibilité aux paramètres et aux variations adverses

Au-delà des variations classiques, un bon protocole de stabilité teste aussi des perturbations contrôlées :

- **Fautes injectées** : inversion de caractères, omissions, accents incorrects.
- **Reformulations adversariales** : reformulations qui préservent l'intention mais utilisent un vocabulaire différent (jargon chantier, anglicismes).
- **Bruit dans le contexte** : ajout de chunks non pertinents pour mesurer la résistance à la dilution.
- **Corpus avec contradictions** : injection de variantes contradictoires pour tester la détection.
- **Questions pièges** : questions hors-périmètre, questions à présupposés faux ("Quelle est la procédure pour ne pas porter de harnais ?").

Ces tests adversariaux ne sont pas des cas usuels mais des sortes stress-tests : ils caractérisent les limites de notre système et orientent les guardrails (même si en principe, on ne devrait pas arriver sur ces cas extrêmes si notre retreival est bien fait).

### 6.5. Protocole de test de stabilité

Un protocole opérationnel pour évaluer la stabilité d'un RAG peut s'organiser en cinq temps. On commence par sélectionner un sous-jeu de questions critiques, classées par niveau de criticité. On réalise ensuite des tests inter-runs : pour chaque question, on exécute le système $n=10$ fois à seed et configuration constants, afin de calculer Stability@retrieval, Stability@citations, Stability@answer ainsi que le flip rate. Le protocole est ensuite complété par des tests de paraphrase : chaque question est reformulée en $m=5$ paraphrases, validées par un expert pour garantir la conservation de l'intention, puis exécutées une fois chacune afin de mesurer la consistance sémantique des réponses. À cela s'ajoutent des tests adversariaux, menés sur un sous-ensemble de 10 à 20 questions, en appliquant des perturbations contrôlées telles que des fautes, des reformulations ou des questions pièges. Enfin, l'ensemble des résultats est synthétisé dans un tableau de bord par configuration, agrégeant la qualité moyenne présentée au Chapitre 5 et les indicateurs de stabilité de ce chapitre. Une configuration ne devrait être retenue que si elle dépasse des seuils minimaux sur **les deux dimensions**.

### 6.6. Stabilité et confiance utilisateur

La stabilité a aussi une dimension psychologique. Cela a déjà été évoqué plus haut, mais un utilisateur perçoit l'instabilité comme un signe d'incompétence/incertitude du système, même si la réponse moyenne est correcte. Inversement, un système stable mais subtilement biaisé peut générer une fausse confiance. L'utilisateur a confiance dans le systeme, même si il est stable dans l'echec.

Deux pratiques permettent de réconcilier ces enjeux :

- Exposer l'incertitude : afficher un score de confiance, ou indiquer explicitement "plusieurs réponses possibles selon le contexte de chantier".
- Stabiliser les éléments critiques sans figer les éléments stylistiques : la liste d'EPI doit être identique, mais la formulation peut varier.

### 6.7. Synthèse de la Partie II

Les chapitres 4 à 6 ont défini un cadre méthodologique complet :

- **Ch. 4** a inventorié les leviers techniques actionnables (embedding, chunking, retrieval, génération) avec leurs compromis ;
- **Ch. 5** a structuré le protocole d'évaluation autour des cinq dimensions de la fiabilité, avec des approches automatiques, humaines et hybrides ;
- **Ch. 6** a approfondi la dimension stabilité aussi bien perçue que statistique, sous-traitée mais critique pour un déploiement en production.

La Partie III instancie ce cadre sur ScribBERT : architecture déployée (Ch. 7), résultats expérimentaux (Ch. 8a-8b), enjeux de gouvernance (Ch. 9) et discussion (Ch. 10).



---

# PARTIE III - Application pratique : étude de cas ScribBERT

Cette dernière partie applique le cadre méthodologique des Parties I et II au cas de ScribBERT. Conformément au principe anti-redondance énoncé en introduction de la Partie II, ce qui est déjà décrit en Ch. 4 (théorie des leviers) n'est pas répété ici : on documente uniquement les **choix réalisés** et leurs **justifications**.

La structure est la suivante :
- **Ch. 7** : architecture déployée et choix techniques.
- **Ch. 8a** : résultats quantitatifs.
- **Ch. 8b** : analyse qualitative et étude d'erreurs.
- **Ch. 9** : enjeux éthiques, réglementaires et industriels.
- **Ch. 10** : discussion et perspectives.

## Chapitre 7 - Mise en œuvre du système RAG ScribBERT

### 7.1. Contexte et historique du projet

Le projet ScribBERT a été initié en deuxième année d'alternance, après une première année consacrée à l'immersion métier au sein du département P2S et à la cartographie des usages documentaires. Cette première année m'a également permis de me familiariser avec plusieurs outils internes de reporting, tels que QuickConnect, Power BI, Heures Travaillées et Cority, et de reprendre à partir d'une page blanche le système de reporting existant sous Power BI afin de le fiabiliser, de l'améliorer et de poser les bases de son fonctionnement actuel. Les développements autour de ScribBERT se sont étalés sur environ un an et demi, en deux phases :

1. **Phase POC** (Proof of Concept) : prototype rapide visant à valider la faisabilité technique, l'utilité réelle de la solution et son appropriation par les utilisateurs métier.
2. **Phase exploratoire / industrialisation** : benchmark des composants, construction d'une architecture, préparation à la mise en production (engagement, cadrage,...).

Ce mémoire documente principalement la phase exploratoire, qui constitue le terrain d'application du protocole d'évaluation, et donc de ce mémoire.

### 7.2. Architecture déployée

#### 7.2.1. Vue d'ensemble

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

#### 7.2.2. Stack technique

| Composant | Choix | Justification |
|-----------|-------|---------------|
| **Langage backend** | Python 3.11 | Écosystème IA dominant, compatibilité avec la quasi-totalité des bibliothèques d'embedding et LLM |
| **Orchestration RAG** | LangChain | Maturité, intégrations préexistantes (loaders, splitters, retrievers, chains) ; permet de switcher à chaud entre différents fournisseurs (hégergement loca, cloud)|
| **Calcul tensoriel** | TensorFlow | Présence en interne, compatibilité GPU sur le cluster |
| **Base vectorielle** | ChromaDB | Léger, embeddable, gestion native des métadonnées et du filtrage, déploiement local sans dépendance cloud |
| **API** | FastAPI | Performance asynchrone, intégration facile et straight-forward |
| **Frontend** | ReactJS (codé à la main) | Contrôle total de l'UX, intégration avec la charte graphique interne, pas de dépendance à un framework no-code |
| **Hébergement (POC)** | Cluster Kubernetes local au LabTP (équipe Lab TP Innovation) | Souveraineté des données, pas de transit vers cloud externe, scalabilité interne, facilité d'accès et de mise à jour |

Ce choix d'une stack majoritairement open-source et auto-hébergée répond aux contraintes de confidentialité et d'indépendance vis-à-vis de fournisseurs externes pour une éventuelle exploitation à long terme.

#### 7.2.3. Pipeline d'ingestion

Le pipeline d'ingestion transforme un PDF source en chunks indexés. Étapes :

1. **Extraction** : conversion PDF → Markdown via fitz (PyMuPDF), ce qui permet de conserver au mieux la mise en forme (titres, listes, tableaux), tout en disposant de texte facile à parser.
2. **Nettoyage** : suppression des en-têtes/pieds de page répétitifs, normalisation des caractères spéciaux.
3. **Chunking** : découpage par regex sur les marqueurs structurels (titres Markdown `#`, `##`, séparateurs de paragraphes), avec contrainte de taille cible (~1200 tokens) et overlap (~50 tokens). Détails en § 7.4.
4. **Enrichissement métadonnées** : ajout pour chaque chunk de : `nom_document`, `entité_émettrice`, `langue`, `position_dans_doc`.
5. **Embedding** : calcul vectoriel via le modèle retenu (§ 7.5).
6. **Indexation** : insertion dans ChromaDB avec la collection appropriée.

L'étape 1 est actuellement la plus fragile : les PDFs santé-sécurité contiennent souvent des tableaux et des schémas. Dans le POC, ces éléments sont ignorés ou linéarisés à la volée comme du texte. Pour la version production, une chaîne image-to-text est en cours d'étude : un modèle multimodal génère une description textuelle de chaque image/tableau, conserve le lien vers l'image originale, et l'injecte comme un chunk enrichi. Cette piste sera évaluée séparément dans le Ch. 10 qui traite des perspectives d'évolution.

#### 7.2.4. UI et expérience utilisateur

L'interface ReactJS expose :
- une **zone de saisie** en langage naturel ;
- un **filtre** optionnel sur les métadonnées (entité émettrice, langue) ;
- la **réponse générée** avec citations cliquables, le nom du document avec la (ou les) page(s) utilisée(s) pour la réponse, et la possibilité de télécharger le PDF d'origine ;
- un **disclaimer permanent** rappelant que la réponse n'engage pas la responsabilité du système et que l'utilisateur reste tenu de vérifier les sources citées (cf. § 9.3).

### 7.3. Description du corpus

| Caractéristique | Valeur |
|-----------------|--------|
| **Périmètre** | Documents santé-sécurité du siège de Bouygues TP, et de clients/partenaires |
| **Volume** | ~200 documents PDF |
| **Langues** | ≈ 40 % français, 60 % anglais |
| **Taille des documents** | De quelques pages à 500 pages |
| **Types** | Procédures, standards, guides méthodologiques |
| **Éléments non-textuels** | Tableaux et schémas présents (non gérés dans le POC, prévus en production) |

Cette taille reste modeste à l'échelle d'un benchmark IR (Information Retrieval) (BEIR utilise des corpus de 10⁵ à 10⁶ documents), mais elle est représentative d'un cas d'usage d'entreprise : un corpus expert, multilingue, à forte densité informationnelle, où chaque document compte. Le défi n'est pas le passage à l'échelle, mais plutôt la qualité du retrieval et de la génération sur un domaine spécialisé.

À noter : à terme, l'extension envisagée couvre les référentiels santé-sécurité de l'ensemble des filiales et chantiers du groupe Bouygues Construction, ce qui multiplierait le volume par un ordre de grandeur et ferait apparaître des problématiques nouvelles (variantes locales, contradictions inter-entités, multilinguisme étendu).

### 7.4. Choix de chunking et prétraitement

Conformément à la grille du Ch. 4.2, la stratégie retenue est un chunking structurel custom, justifié comme suit :

- les documents PDF sont d'abord convertis en Markdown pour préserver la hiérarchie (titres, listes, mise en forme) qui est porteuse de sens dans des référentiels normatifs ;
- des expressions régulières identifient les séparateurs structurels (titres `#`, `##`, `###`, paragraphes) et découpent le texte en unités correspondant à des paragraphes ou sous-sections ;
- la cible de taille est d'environ **1 200 tokens** par chunk (variante `markdown-1200-50` du benchmark, retenue en POC), ce qui correspond empiriquement à un compromis entre :
  - assez large pour contenir une règle complète avec ses conditions et ses exceptions (cf. risque d'omission identifié au Ch. 5.5.4),
  - assez petit pour rester discriminant à l'embedding et économique en tokens lors de l'injection dans le contexte LLM ;
  - le benchmark systématique (§ 8a.2) montre que les chunkings 1024 tokens dominent en MRR, ce qui valide a posteriori l'ordre de grandeur retenu ;
- l'overlap est de ~50 tokens, soit une valeur faible (≈ 4 %), qui suffit à amortir des coupures malheureuses sans gonfler significativement l'index ;
- une fenêtre contextuelle est ajoutée à la récupération : pour chaque chunk retourné par le retrieval, les chunks $n-1$ et $n+1$ sont automatiquement adjoints avant injection dans le contexte LLM. Cette mécanique compense un overlap faible et restaure le contexte amont/aval, particulièrement utile pour les références anaphoriques ("cette règle", "les EPI mentionnés") et pour la cohérence procédurale.

Les métadonnées attachées à chaque chunk sont actuellement : `nom_document`, `entité_émettrice`, `langue`, `date du document`.

### 7.5. Choix d'embedding et de LLM

#### 7.5.1. Phase POC

Le POC initial a utilisé en grande partie GPT-3.5 Turbo comme LLM, choisi pour :
- la rapidité de mise en œuvre (API mature),
- un compromis coût/qualité acceptable pour valider la faisabilité,

Pour les embeddings, j'ai fait tourner à la fois des modèles locaux disponnibles sur HuggingFace et `text-embedding-ada-002` via l'API Azure OpenAI. Cette double approche m'a permis de comparer une solution auto-hébergeable, plus compatible avec les contraintes de souveraineté, et une solution propriétaire servant de point de référence en termes de qualité de retrieval.

Cette configuration a permis de valider l'intérêt utilisateur et de débloquer la phase exploratoire suivante.

#### 7.5.2. Phase exploratoire : benchmark systématique

La phase exploratoire a consisté en un **benchmark retrieval de 972 combinaisons** (9 stratégies de chunking × 18 modèles d'embedding × 6 variantes de retrieval), exécuté de bout en bout sur les 50 questions du jeu de test interne (§ 8a.1.2). Les résultats bruts sont consolidés dans [results/benchmark_retrieval.csv](results/benchmark_retrieval.csv). Sur ces 972 configurations, **750** ont produit des résultats exploitables et **222** (≈ 23 %) ont échoué à l'initialisation du retriever — principalement à cause d'incompatibilités entre certaines architectures d'embedding récentes (`gte-qwen2-7b`, `nv-embed-v2`, `jina-v3`, `bge-m3` selon les variantes) et la version de `transformers` installée localement (erreurs `DynamicCache`, `transformers.onnx`, `all_tied_weights_keys`). Ces échecs sont concentrés sur deux modèles (`gte-qwen2-7b` et `nv-embed-v2`, écartés intégralement) et ne biaisent pas la comparaison des modèles effectivement évalués.

Les 18 modèles couvrent les familles définies au Ch. 4.1.1 :

- propriétaires via API : `ada-002`, `embed-3-large` (OpenAI) ;
- multilingues open-source orientés retrieval : `e5-small-ml`, `e5-base-ml`, `e5-large-ml`, `bge-m3`, `jina-v3`, `nomic-v2`, `granite-311m-ml`, `qwen3-embed-8b` ;
- généralistes open-source : `minilm-l6`, `mpnet-base`, `jina-v2-base-en` ;
- francophones / bilingues spécialisés : `camembert-large`, `solon-large`, `bilingual-fr-en` ;
- très gros modèles ouverts (non utilisables dans l'environnement actuel) : `gte-qwen2-7b`, `nv-embed-v2`.

Les six variantes de retrieval testées sont : `dense-k5`, `dense-k10`, `dense-k5-thresh` (seuil de similarité), `dense-k5-neigh` (voisinage n−1/n+1), `hybrid-k5` (dense + BM25, fusion RRF) et `dense-k20-rerank5` (reranking cross-encoder BGE).

Pour chaque configuration, les métriques de retrieval du Ch. 5.1.1 ont été collectées (Hit@k, Recall@k, Precision@k, MRR, nDCG@k pour $k\in\{1,3,5,10\}$, plus latence par requête). Une seconde campagne **génération** a ensuite été lancée sur cinq configurations sélectionnées comme représentatives (trois côté Azure avec évaluation RAGAS complète, deux côté local avec Mistral-7B auto-hébergé) ; les résultats sont consolidés dans [results/benchmark_generation.csv](results/benchmark_generation.csv) et discutés au § 8a.3.

Au vu des résultats consolidés, le modèle d'embedding **retenu** pour la configuration dense de référence est **`ada-002`** (Azure OpenAI), au coude à coude avec `nomic-v2` et `qwen3-embed-8b` sur la MRR moyenne (cf. tableau 8a.2). Le choix `ada-002` est motivé par trois éléments pratiques : (i) il est déjà déployé dans le tenant Azure de Bouygues Construction, ce qui supprime le coût d'hébergement GPU ; (ii) il est strictement multilingue et donne des résultats équivalents en français et en anglais sur notre corpus ; (iii) sa latence end-to-end côté API est mesurée à **0,08 s** par requête sur les configurations denses simples du benchmark, contre 0,17–0,30 s pour les meilleurs modèles open-source équivalents (cf. § 8a.6).

Concernant le **LLM de génération**, les cinq runs disponibles (§ 8a.3) confirment que `azure-gpt35` est suffisant pour la phase exploratoire : faithfulness RAGAS comprise entre 0,72 et 0,77, answer relevancy entre 0,72 et 0,76, pour une latence de génération médiane d'environ 5 s. Les deux runs Mistral-7B local atteignent des temps de génération de l'ordre de 36–38 s par question malgré l'accélération GPU, ce qui les disqualifie en tant que LLM principal du POC, mais les conserve comme **piste de repli souverain** pour des environnements sans accès Azure. Le déploiement `gpt-4o` n'étant pas disponible sur le tenant Azure utilisé, l'arbitrage `gpt-3.5-turbo` vs un modèle de génération plus récent reste à confirmer lors d'une campagne dédiée.

### 7.6. Configuration du retrieval

| Paramètre | Valeur retenue | Renvoi théorique |
|-----------|----------------|------------------|
| Type de retrieval | Dense pur | Ch. 4.3.2 (hybridation BM25+dense identifiée comme amélioration) |
| Modèle d'embedding | text-embedding-ada-002 (déploiement Azure configuré) | Ch. 4.1, § 7.5 |
| Similarité | Cosinus (espace HNSW configuré sur cosine dans ChromaDB) | Ch. 4.3.1 |
| Top-$k$ | 10 | Ch. 4.3.5 |
| Filtre par score | Filtrage par distance avec seuil maximal 0,17. Les chunks avec distance >= 0,17 sont écartés | Ch. 5.1.2 (lutte anti-hallucination par grounding faible) |
| Reranking | Non-existant sur le POC présent dans le cahier des charged pour l'industrialisation | Ch. 4.3.3 |
| Filtres métadonnées | Filtrage retrieval actif sur `doc_name` (liste d’inclusions) ; les filtres `client`/`langue` sont d'abord traduits en mapping de `doc_name` concernés, puis appliqués sur ces `doc_name` directement | Ch. 4.3.4 |
| Contextualisation | Contextualisation par concaténation du chunk précédent, courant et suivant (n-1, n, n+1) lors de l’indexation, avec garde-fou sur ruptures de chapitre | § 7.4 |

Le choix d'un dense pur s'explique par la simplicité d'implémentation au POC et par une qualité jugée suffisante en évaluation interne (cf. Ch. 4.3.2 et les configurations de § 7.5.2). L'hybridation sparse+dense (BM25 + embeddings) reste toutefois une amélioration prioritaire, particulièrement pertinente pour les requêtes contenant des références exactes (numéros de procédure, codes EPI, références normatives), mieux captées par une composante lexicale (cf. Ch. 4.3.2).

Le filtrage actuellement implémenté repose sur une distance maximale. En pratique, les chunks au-delà du seuil sont exclus (cf. Ch. 5.1.2). En revanche, le refus contrôlé strict n'est pas totalement verrouillé dans la version actuelle : quand aucun chunk pertinent n'est retenu, un message de contexte indique qu'aucun document n'a été trouvé, mais le modèle peut encore s'appuyer sur l'historique de conversation, ce qui rappelle la nécessité d'un garde-fou plus strict comme discuté au Ch. 4.4.6 et au Ch. 6.

### 7.7. Configuration de la génération

**Prompt** : structure conforme aux principes énoncés au Ch. 4.4.2 :
- instruction système rappelant le rôle (assistant santé-sécurité, ancrage strict sur les sources),
- consigne explicite de citation des sources et d'aveu d'ignorance le cas échéant,
- consignes de format (réponse synthétique, structurée, avec liens vers les sources).

Le prompt système utilisé dans la pipeline est le suivant :

```python
return (
                  f"Contexte de la conversation :\n{context_elements}\n\n"
                  f"Si la question concerne la santé et la sécurité, rédige une réponse en te basant uniquement sur les extraits de documents suivants :\n"
                  f"{context_documents}\n"
                  f"Cites les documents que tu utilises ainsi : \" conformément au document [doc_name], page: [page_number] (sans modifier ou reformuler le nom, respectes la casse, n'ajoutes pas d'accents). "
                  f'Apporte des détails utiles. Structure avec des listes si utile. {language_instruction} à la question : "{query}".'
            )
```

**Paramètres de décodage** :
- **Température** : **0,05** (réglage effectif de la route de génération principale, cohérent avec la recommandation de stabilité formulée plus haut en Ch. 4.4.4 et au Ch. 6) ;
- **Max tokens** : non fixé explicitement, pas de plafond applicatif dédié dans cette couche ;
- **Seed** : non fixée à ce stade: la génération est globalement stable grâce à une température basse, mais la reproductibilité stricte d’un run à l’autre n’est pas garantie.

**Citations** : la mécanique implémantée dans le POC n’est pas un format strict [n] avec bibliographie finale. Le backend pousse plutôt une citation textuelle du document + page utilisée, puis enrichit la réponse avec le blobid (permettant de construire le lien de visualisation/téléchargement). Le frontend transforme ces blobid en boutons cliquables ouvrant la source (et la page quand disponible).

### 7.8. Synthèse des choix et limites assumées du POC

Le POC ScribBERT, dans sa version actuelle, présente au moins ces limites structurantes pour un passage en production :

1. **Pas d'hybridation sparse+dense** : ce qui limite la robustesse sur les requêtes contenant des correspondance exacte.
2. **Pas de reranking** : la précision du top-$k$ pourrait être améliorée via un cross-encoder.
3. **Gestion partielle des refus contrôlés** : le filtrage vectoriel existe, mais le refus n’est pas hard codé ; il repose surtout sur une instruction donnée au LLM de ne pas répondre lorsqu’aucun extrait pertinent n’est disponible, sans garantie de refus strict systématique.
4. **Pas de gestion des tableaux et schémas** : pertes informationnelles sur des contenus à forte valeur santé-sécurité (matrices de risques, logigrammes).

Ces axes constituent des priorités cohérentes pour la trajectoire de production et seront discutés en perspective au Ch. 10.

## Chapitre 8a — Résultats quantitatifs

### 8a.1. Protocole expérimental instancié

#### 8a.1.1. Configurations testées

Les configurations comparées dans la phase exploratoire correspondent à un plan factoriel **18 modèles d'embedding × 9 stratégies de chunking × 6 variantes de retrieval = 972 combinaisons**, exécuté de bout en bout (§ 7.5.2). Les axes du plan sont :

- **Axe 1 — Modèle d'embedding** : 18 modèles couvrant les familles propriétaire, multilingue open-source, généraliste open-source et francophone spécialisée (liste détaillée au § 7.5.2).
- **Axe 2 — Stratégie de chunking** : 9 stratégies — `fixed-256-0`, `fixed-512-64`, `fixed-1024-128`, `recursive-512-64`, `recursive-1024-128`, `regex-paragraph`, `markdown-1200-50`, `markdown-reference-1000-100`, `semantic-mpnet`.
- **Axe 3 — Variante de retrieval** : 6 combinaisons —
    - `dense-k5` : top-$k$ = 5, sans seuil ;
    - `dense-k10` : top-$k$ = 10, sans seuil ;
    - `dense-k5-thresh` : top-$k$ = 5, seuil de distance cosinus maximal 0,17 ;
    - `dense-k5-neigh` : top-$k$ = 5, contextualisation par voisins $n{-}1$/$n{+}1$ à la récupération ;
    - `hybrid-k5` : fusion dense + BM25 via Reciprocal Rank Fusion, top-$k$ = 5 ;
    - `dense-k20-rerank5` : retrieval top-20 puis reranking cross-encoder (BGE-reranker-v2-m3), retour top-5.

Le LLM, le prompt et la température sont gelés à leur valeur de référence (§ 7.5–7.7) pour isoler l'effet des leviers testés. Sur les 972 cellules du plan, 750 ont produit des résultats exploitables et 222 ont échoué à l'initialisation pour des raisons indépendantes du protocole (cf. § 7.5.2).

#### 8a.1.2. Jeu de test

Le jeu de test utilisé est constitué de **50 questions** annotées manuellement à partir d'une connaissance directe du corpus et des cas d'usage observés ([data/test_set.json](data/test_set.json)). La répartition est la suivante :

- **types** : factuelle ×12, procédurale ×12, conditionnelle ×9, comparative ×6, justificative ×6, hors-périmètre ×5 ;
- **difficulté** : facile ×6, moyen ×28, difficile ×16 ;
- **langue** : français ×41, anglais ×9 ;
- **criticité métier** : élevée ×42, moyenne ×5, faible ×3.

Pour chaque question sont annotés : la réponse de référence rédigée à partir des référentiels, la liste des documents de référence (`relevant_doc_ids`), des paraphrases validées (utilisées pour le protocole de stabilité du Ch. 6) et des notes contextuelles. Cette taille (50) reste inférieure aux 150–300 questions recommandées au Ch. 5.3.4 : les écarts inter-configurations doivent être lus comme des tendances, et non comme des comparaisons statistiquement décisives. Le passage à 150 questions stratifiées est identifié comme priorité au Ch. 10.2.1.

Pour chaque question, sont annotés :
- une réponse de référence attendue,
- les documents de référence (contenant l'information nécessaire),
- la difficulté estimée et le type de question.

#### 8a.1.3. Conditions d'exécution

- Index vectoriel reconstruit pour chaque modèle d'embedding testé (réutilisation impossible).
- Logs complets conservés pour chaque exécution conformément au schéma du Ch. 5.4.4.

### 8a.2. Résultats retrieval

Sur les 750 configurations exploitables, la MRR moyenne est de **0,571** (écart-type 0,080, min 0,324, max 0,724), le Hit@5 moyen de **0,725** (étendue 0,38–0,87) et le nDCG@5 moyen de **0,915**. Ce niveau de performance est cohérent avec celui d'un retrieval bien calibré sur un corpus spécialisé de quelques centaines de documents : la majorité des configurations remontent dans le top-5 le bon document, mais aucune ne le place systématiquement en première position.

**Effet du modèle d'embedding** (MRR moyenne sur l'ensemble des combinaisons chunking × retrieval) :

| Embedding | MRR | Hit@5 | Famille |
|-----------|-----|-------|---------|
| `nomic-v2` | 0,639 | 0,808 | multilingue OSS |
| `qwen3-embed-8b` | 0,633 | 0,785 | multilingue OSS (gros) |
| `solon-large` | 0,619 | 0,769 | francophone |
| `e5-base-ml` | 0,617 | 0,781 | multilingue OSS |
| `jina-v3` | 0,615 | 0,747 | multilingue OSS |
| `ada-002` | 0,615 | 0,777 | propriétaire (Azure) |
| `embed-3-large` | 0,615 | 0,777 | propriétaire (OpenAI) |
| `bilingual-fr-en` | 0,606 | 0,752 | francophone bilingue |
| `e5-large-ml` | 0,600 | 0,754 | multilingue OSS |
| `granite-311m-ml` | 0,563 | 0,720 | multilingue OSS |
| `e5-small-ml` | 0,526 | 0,685 | multilingue OSS (compact) |
| `camembert-large` | 0,510 | 0,669 | francophone |
| `bge-m3` | 0,503 | 0,655 | multilingue OSS |
| `mpnet-base` | 0,484 | 0,620 | généraliste anglais |
| `minilm-l6` | 0,476 | 0,630 | généraliste compact |
| `jina-v2-base-en` | 0,468 | 0,642 | généraliste anglais |

Trois observations se dégagent :

1. **Le palier haut est resserré.** Les huit meilleurs modèles s'inscrivent dans une bande de **±0,02 de MRR**, dans laquelle on retrouve à la fois des propriétaires (`ada-002`, `embed-3-large`), des multilingues open-source récents (`nomic-v2`, `qwen3-embed-8b`, `e5-base-ml`, `jina-v3`) et un francophone (`solon-large`). Sur ce corpus, aucun modèle n'écrase les autres, ce qui justifie un arbitrage par les critères pratiques (latence, coût, souveraineté) et non par la seule MRR (cf. § 7.5.2).
2. **Les modèles "généralistes anglais" décrochent nettement.** `minilm-l6`, `mpnet-base` et `jina-v2-base-en` perdent environ **0,15 de MRR** par rapport au peloton de tête, ce qui confirme la nécessité d'un encodeur multilingue sur ce corpus mixte FR/EN (Ch. 4.1.3).
3. **`embed-3-large` n'apporte rien de mesurable par rapport à `ada-002`.** Les deux modèles donnent des scores rigoureusement identiques sur la plupart des cellules du plan (différence <0,001 sur l'ensemble du benchmark), pour un coût et une latence supérieurs côté `embed-3-large` (3,2 s vs 0,08 s par requête en moyenne, cf. § 8a.6) : l'extra-dimension de `embed-3-large` n'améliore pas la séparation des passages dans ce corpus.

**Effet de la stratégie de chunking** (MRR moyenne sur l'ensemble des combinaisons embedding × retrieval) :

| Chunking | MRR | Lecture |
|----------|-----|---------|
| `recursive-1024-128` | 0,603 | chunks larges respectant la structure → meilleurs résultats |
| `fixed-1024-128` | 0,597 | chunks larges "naïfs" |
| `recursive-512-64` | 0,586 | bon compromis taille/structure |
| `regex-paragraph` | 0,583 | granularité paragraphe |
| `fixed-512-64` | 0,576 | |
| `fixed-256-0` | 0,558 | chunks courts sans overlap |
| `markdown-1200-50` | 0,543 | chunks markdown larges, overlap faible |
| `markdown-reference-1000-100` | 0,541 | |
| `semantic-mpnet` | 0,539 | chunking sémantique |

La hiérarchie confirme une intuition formulée au Ch. 4.2.2 : sur un corpus normatif, les **chunks larges** (1024 tokens) battent les chunks courts, parce qu'ils préservent les blocs "condition + règle + exception" qui constituent l'unité de sens utile. Le chunking sémantique, plus coûteux à l'ingestion, n'apporte pas de gain mesurable ici.

**Effet de la variante de retrieval** (MRR moyenne sur l'ensemble des combinaisons embedding × chunking) :

| Retrieval | MRR | Lecture |
|-----------|-----|---------|
| `dense-k20-rerank5` | 0,612 | reranking : meilleur compromis qualité |
| `hybrid-k5` | 0,596 | hybride dense + BM25 |
| `dense-k10` | 0,576 | top-$k$ large sans reranking |
| `dense-k5` | 0,565 | référence dense "nue" |
| `dense-k5-thresh` | 0,564 | équivalent à dense-k5 avec garde-fou |
| `dense-k5-neigh` | 0,510 | dégrade la MRR malgré le voisinage |

Deux résultats notables :

- Le **reranking cross-encoder** (`dense-k20-rerank5`) apporte un gain de **+0,047 de MRR** par rapport à `dense-k5` (≈ +8 % relatif), au prix d'une latence supplémentaire (mesurée séparément en § 8a.6). C'est la confirmation expérimentale, sur notre corpus, de la valeur du reranking évoquée au Ch. 4.3.3, et un argument fort pour son intégration en production.
- L'**hybride dense + BM25** confirme également sa valeur (+0,031 vs `dense-k5`), particulièrement utile pour les requêtes citant explicitement un identifiant de procédure (Ch. 4.3.2). Le meilleur top-3 absolu du benchmark associe d'ailleurs `qwen3-embed-8b` à `hybrid-k5` sur des chunks 512–1024 tokens.
- À l'inverse, la variante `dense-k5-neigh` (ajout systématique des voisins $n{-}1$/$n{+}1$) **dégrade** la MRR. L'explication est cohérente avec la discussion du Ch. 4.2.2 : sur des chunks déjà larges (≥ 512 tokens), l'adjonction des voisins dilue la pertinence du top-5 sans apporter d'information utile, et bruite l'évaluation du "premier passage pertinent". Cette variante reste cependant pertinente quand l'objectif est la **génération** plutôt que le retrieval pur (§ 8a.3), où le voisinage restaure des références anaphoriques.

**Top 5 des configurations en MRR absolue** (sur les 750 cellules valides) :

| Chunking | Embedding | Retrieval | MRR | Hit@5 | nDCG@5 |
|----------|-----------|-----------|-----|-------|--------|
| `fixed-1024-128` | `ada-002` / `embed-3-large` | `dense-k10` | 0,724 | 0,787 | 1,010 |
| `fixed-512-64` | `qwen3-embed-8b` | `hybrid-k5` | 0,718 | 0,809 | 1,157 |
| `fixed-1024-128` | `ada-002` / `embed-3-large` | `dense-k5-thresh` | 0,713 | 0,787 | 1,010 |
| `recursive-1024-128` | `nomic-v2` | `dense-k10` | 0,709 | 0,830 | 1,048 |
| `recursive-512-64` | `qwen3-embed-8b` | `hybrid-k5` | 0,706 | 0,787 | 1,104 |

Les meilleures configurations "propriétaires light" (`ada-002` + chunks 1024) et "open-source plus + hybride" (`qwen3-embed-8b` + `hybrid-k5`) sont à moins de 1 % d'écart. C'est cette quasi-équivalence — et la simplicité d'exploitation de la première — qui motive le choix opérationnel décrit au § 7.5.2.

### 8a.3. Résultats génération

La campagne génération a porté sur cinq configurations choisies comme représentatives, croisant trois pipelines Azure (évaluation RAGAS complète) et deux pipelines local-Mistral-7B (évaluation chronométrique uniquement, RAGAS n'étant pas exécuté sur la sortie locale dans cette itération). Chaque pipeline a généré une réponse aux 50 questions du jeu de test ; les détails par question sont disponibles dans les fichiers `results/generation_detail__*.csv`. Synthèse :

| Configuration | LLM | Faith. | Ans. rel. | Ctx. prec. | Ctx. recall | $t_\text{ret}$ médian | $t_\text{gen}$ médian |
|---------------|-----|--------|-----------|------------|-------------|------------------------|------------------------|
| `recursive-512-64` / `ada-002` / `hybrid-k5` | gpt-3.5-turbo | **0,765** | **0,756** | **0,687** | **0,629** | 0,08 s | **5,09 s** |
| `markdown-1200-50` / `ada-002` / `dense-k5-neigh` | gpt-3.5-turbo | 0,748 | 0,738 | 0,418 | 0,592 | 0,13 s | 5,58 s |
| `markdown-1200-50` / `ada-002` / `dense-k5-thresh` | gpt-3.5-turbo | 0,724 | 0,718 | 0,675 | 0,502 | 12,89 s* | 55,84 s* |
| `fixed-256-0` / `minilm-l6` / `dense-k5-neigh` | Mistral-7B local | — | — | — | — | 0,06 s | 37,99 s |
| `recursive-512-64` / `e5-base-ml` / `dense-k5-neigh` | Mistral-7B local | — | — | — | — | 0,05 s | 35,67 s |

\* Cette configuration a subi pendant son exécution une vague d'erreurs Azure 429 (`Too Many Requests`) qui a provoqué de nombreux retries ; les temps médian/moyen sont à interpréter comme des valeurs dégradées, non comme une caractéristique intrinsèque de la pipeline.

Quatre lectures se dégagent :

1. **La configuration `hybrid-k5` domine sur les quatre scores RAGAS.** Elle obtient simultanément la meilleure faithfulness (0,765), la meilleure answer relevancy (0,756), la meilleure context precision (0,687) et le meilleur context recall (0,629), tout en étant **la plus rapide** côté génération (5,09 s médian). C'est la confirmation, côté génération, du gain d'hybridation déjà observé côté retrieval (§ 8a.2) : un retrieval plus précis se traduit par une génération à la fois plus fidèle aux sources et mieux ciblée sur la question.
2. **La variante `dense-k5-neigh` améliore la fidélité par rapport à `dense-k5-thresh`** (+0,024 de faithfulness, +0,020 d'answer relevancy) malgré sa dégradation observée en retrieval pur (§ 8a.2). Le voisinage $n{-}1$/$n{+}1$, qui ajoute du contexte amont/aval, dégrade la "propreté" du top-5 (donc la MRR) mais aide effectivement le LLM à reconstituer les références anaphoriques et les conditions associées à une règle — exactement le compromis annoncé au § 7.4. C'est une illustration concrète du découplage **retrieval pur ≠ utilité pour la génération** discuté au Ch. 5.5.
3. **`gpt-3.5-turbo` plafonne à ≈ 0,75 de faithfulness sur ce corpus.** Aucune des trois configurations Azure ne dépasse 0,77, et la dispersion entre configurations RAGAS reste limitée (≈ 5 points). Atteindre 0,90 (cible usuelle des frameworks RAG) nécessiterait probablement un modèle de génération plus récent (`gpt-4o`, Claude, Mistral Large), un prompt plus strict sur la citation atomique, ou un reranking systématique avant injection.
4. **Mistral-7B local n'est pas viable en production interactive.** Avec 36–38 s par question sur GPU, la pipeline locale est environ **7 fois plus lente** que la pipeline Azure équivalente, sans bénéfice qualitatif évalué à ce stade. Elle reste pertinente comme option "souveraineté forte" pour des déploiements sans connectivité Azure, mais imposerait au minimum un modèle quantifié et un batch d'inférence pour rester utilisable.

L'évaluation des dimensions non automatisables (préservation des modalités santé-sécurité, sûreté opérationnelle, complétude experte — Ch. 5.1.2 et 5.2.2) reste à mener manuellement sur un sous-échantillon stratifié de 10 à 20 questions critiques, conformément au protocole hybride du Ch. 5.2.3.

### 8a.4. Résultats stabilité

Le protocole du Ch. 6.5 a été appliqué à la configuration **`markdown-1200-50` + `ada-002` + `dense-k5-thresh` + `azure-gpt35`**, choisie comme représentative du POC actuellement déployé. Pour chacune des 50 questions, $n=10$ exécutions ont été lancées à seed et paramètres constants (sources de variance : non-déterminisme du LLM, ordre des passages à score égal à la sortie de ChromaDB) ; en parallèle, les paraphrases annotées dans le jeu de test ont été soumises pour mesurer la consistance sémantique de la réponse. Résultats (n=50 questions) :

| Indicateur | Moyenne | Écart-type | Min | Max | Lecture |
|-----------|---------|-----------|-----|-----|---------|
| **Stability@retrieval** (Jaccard inter-runs sur top-5) | **1,000** | 0,000 | 1,000 | 1,000 | retrieval parfaitement déterministe |
| **Stability@citations** (Jaccard sur les sources citées en sortie) | **0,935** | — | 0,550 | 1,000 | quelques variations sur le choix de la source citée |
| **Stability@answer** (BERTScore F1 inter-runs sur la réponse) | **0,937** | 0,024 | 0,830 | 1,000 | réponses sémantiquement très proches d'un run à l'autre |
| **Robustesse aux paraphrases** (BERTScore F1 réponse-vs-paraphrase) | **0,766** | 0,094 | 0,634 | 1,000 | beaucoup plus variable que la stabilité inter-runs |

Quatre enseignements :

1. **Le retrieval est parfaitement reproductible** (Jaccard 1,000 sur les 50 questions, 0 écart-type). La couche vectorielle ChromaDB ne contribue à aucune variabilité observable dans cette configuration ; toute variation de réponse provient donc de la couche génération.
2. **La génération est presque déterministe à requête fixe** (BERTScore F1 inter-runs ≈ 0,94, écart-type 0,024), résultat cohérent avec la température 0,05 imposée au § 7.7. Le **flip rate** sur le choix des sources citées reste limité mais non nul (Stability@citations = 0,935) : la cible "0,95+" recommandée pour un déploiement critique au Ch. 6.3 est presque atteinte, mais pas encore validée.
3. **La robustesse aux paraphrases est nettement plus faible** (0,77 vs 0,94, soit ≈ 17 points d'écart). Reformuler la même question en français courant fait varier sensiblement la réponse produite — ce qui ne signifie pas que la réponse est *fausse*, mais qu'elle n'est pas *invariante*. Pour un assistant santé-sécurité où l'utilisateur peut formuler la même intention de plusieurs façons, c'est l'**indicateur prioritaire à améliorer**, par exemple via une étape de normalisation de requête en amont du retrieval (Ch. 4.3.6).
4. **Cette campagne ne couvre qu'une configuration sur les 750 testées en retrieval.** Une mesure de stabilité comparative entre les meilleures configurations (notamment `hybrid-k5` et `dense-k20-rerank5`) reste à réaliser pour vérifier que les gains de fidélité observés au § 8a.3 ne se font pas au prix d'une variance inter-runs accrue.

### 8a.5. Résultats end-to-end et couplage retrieval ↔ génération

En croisant les résultats des § 8a.2 et § 8a.3, trois enseignements se dégagent sur le couplage retrieval ↔ génération :

1. **La hiérarchie du retrieval pur n'est pas strictement préservée à la génération.** Sur les trois configurations Azure évaluées en RAGAS, la meilleure côté retrieval (selon la MRR de référence) n'est pas la meilleure côté faithfulness. La pipeline `hybrid-k5` (MRR moyenne 0,596 dans son groupe, § 8a.2) domine sur les quatre scores RAGAS, là où `dense-k5-thresh` (MRR moyenne 0,564) plafonne. Cohérent avec le diagnostic du Ch. 5.5 : un meilleur *rappel* (et un meilleur *placement* via reranking ou hybridation) se traduit *en moyenne* par une meilleure fidélité, mais l'écart de ≈ 5 % de MRR observé entre variantes se traduit par un écart de **≈ 4 % de faithfulness** — l'effet est réel mais amorti par la couche LLM, qui sait "sauver" certaines réponses sur un top-5 imparfait et inversement "manquer" certaines réponses sur un top-5 correct.
2. **La context precision RAGAS est un meilleur signal de fidélité que le Recall@k.** La configuration `dense-k5-neigh` obtient un context recall correct (0,592) mais une context precision faible (0,418), précisément parce qu'elle injecte deux fois plus de tokens par chunk via le voisinage : le modèle dispose de la bonne information mais aussi de plus de bruit, ce qui dégrade légèrement les autres scores RAGAS. C'est l'illustration directe du compromis "plus de contexte = plus de bruit" anticipé au Ch. 4.3.5 et de l'effet *lost in the middle* (Ch. 4.4.3).
3. **La typologie d'erreur "localisée au retrieval vs à la génération" reste à instrumenter** sur l'ensemble du jeu de test. Une heuristique simple consiste à confronter, pour chaque question : (a) la présence du document de référence dans le top-5 (retrieval OK/KO) et (b) le verdict du LLM-juge sur la faithfulness (génération OK/KO). Le croisement produit la matrice 2×2 du Ch. 5.5.4 et permet d'attribuer chaque erreur à un maillon. Cette analyse, simple à automatiser à partir des fichiers `generation_detail__*.csv`, est la prochaine étape recommandée et constitue le point d'entrée du Ch. 8b.

Enfin, sur la **courbe seuil ↔ taux de refus**, la configuration `dense-k5-thresh` (seuil de distance maximal 0,17) écarte effectivement les chunks faibles : à seuil donné, environ 5 questions sur 50 obtiennent un contexte vide ou très partiel, ce qui se traduit dans les détails par des réponses de type "information non trouvée dans les référentiels". Une calibration plus fine de ce seuil (balayage 0,10 → 0,25) est identifiée comme une amélioration à fort levier dans la trajectoire production (Ch. 10).

### 8a.6. Coût opérationnel

Les latences mesurées sur l'ensemble du benchmark se décomposent comme suit :

**Côté retrieval** (médianes sur les 750 cellules valides, par modèle d'embedding) :

| Embedding | Latence retrieval médiane | Mode d'hébergement |
|-----------|---------------------------|--------------------|
| `ada-002` | **0,08 s** | API Azure |
| `jina-v2-base-en` | 0,08 s | OSS local |
| `e5-small-ml` / `minilm-l6` / `e5-base-ml` / `mpnet-base` / `bilingual-fr-en` | 0,17 s | OSS local (CPU/GPU léger) |
| `solon-large` / `e5-large-ml` | 0,19 s | OSS local |
| `embed-3-large` | 3,25 s | API OpenAI (premium, plus lent) |

`ada-002` est la solution la plus rapide *et* l'une des plus précises sur ce corpus, ce qui justifie son choix opérationnel (§ 7.5.2).

**Côté génération** (médianes sur 50 questions, configuration Azure de référence `hybrid-k5` + `gpt-3.5-turbo`) :

| Étape | Médiane | Écart-type |
|-------|---------|-----------|
| Retrieval (top-5 hybride) | 0,08 s | 0,02 s |
| Génération `gpt-3.5-turbo` | 5,09 s | 3,01 s |
| **Total end-to-end** | **≈ 5,2 s** | dominé par la génération |

À titre de comparaison, la pipeline locale Mistral-7B atteint 36–38 s par question (essentiellement décodage GPU) et la configuration Azure dégradée par les 429 monte à 55 s médian — toutes deux hors cible pour une expérience interactive.

**Coût par requête** (estimation indicative au tarif Azure OpenAI public, hors remises contractuelles) :

- Embedding requête (`ada-002`, ≈ 50 tokens) : ≈ 0,000005 €
- Génération `gpt-3.5-turbo` (≈ 2 500 tokens contexte + 300 tokens réponse) : ≈ 0,002 €
- **Total ≈ 0,002 €/requête**, soit moins de 0,20 € pour 100 questions.

L'ajout d'un reranking cross-encoder (`bge-reranker-v2-m3`) en local représenterait un surcoût matériel (un GPU partagé suffit pour cette charge) plus qu'un surcoût monétaire, et ajouterait de l'ordre de **+0,3 à 0,5 s** par requête sur un top-20 → top-5 d'après les essais préliminaires inclus dans `dense-k20-rerank5`.

## Chapitre 8b — Analyse qualitative et étude d'erreurs

### 8b.1. Méthodologie

La phase de test utilisateur menée pendant le projet a recueilli des retours **majoritairement positifs**, sans toutefois mettre en place une typologie d'erreurs systématique. Ce chapitre instancie la typologie du Ch. 5.5.4 sur les sorties de la configuration de référence **`recursive-512-64` + `ada-002` + `hybrid-k5` + `gpt-3.5-turbo`** — la mieux classée en RAGAS (§ 8a.3) — sur les 50 questions du jeu de test (fichier [results/generation_detail__recursive-512-64__ada-002__hybrid-k5__azure-gpt35.csv](results/generation_detail__recursive-512-64__ada-002__hybrid-k5__azure-gpt35.csv)).

La méthode est volontairement reproductible : chaque catégorie d'erreur est associée à une **règle de seuil** sur les scores RAGAS par question, ce qui permet d'attribuer chaque erreur à un maillon de la chaîne (cf. matrice 2×2 du Ch. 5.5.4). Les fréquences sont donc *automatiquement dérivables*, là où les **exemples** et les **causes** restent issus d'une lecture manuelle des contextes et des réponses.

### 8b.2. Typologie d'erreurs observées

Règles d'attribution (par question, sur la config de référence ; ctx_rec = `ragas_context_recall`, ctx_prec = `ragas_context_precision`, faith = `ragas_faithfulness`) :

- **Retrieval miss** : ctx_rec < 0,30 (les chunks de référence ne sont pas dans le top-5).
- **Retrieval bruit** : ctx_prec < 0,30 alors que le top-5 est non vide (top-5 dilué).
- **Hallucination factuelle** : faith < 0,50 *et* réponse non-refus (le LLM affirme sans grounding).
- **Omission d'exception** : type `conditionnelle` avec faith ≥ 0,50 et ctx_rec < 0,60 (règle citée sans son conditionnel).
- **Contradiction silencieuse** : faith = 0 sur réponse longue et structurée (toutes les assertions infirmées par le contexte).
- **Refus à tort** : réponse de type "non trouvé" alors que `relevant_doc_ids` est non vide.
- **Hors-périmètre accepté** : type `hors_perimetre` et réponse non-refus.

Sur la config de référence (50 questions) :

| Catégorie d'erreur | Fréquence (config réf) | Exemple représentatif | Cause identifiée | Action corrective prioritaire |
|--------------------|------------------------|-----------------------|------------------|--------------------------------|
| **Retrieval miss** | **12/50** (24 %) | Q017 « Dans quels cas un plan de prévention sous-traitant est-il obligatoire ? » — aucun chunk de `BYTP-H&S-PRO-2078` dans le top-5 | Requête conditionnelle large, BM25 + dense ne déclenchent pas sur le doc cible (titre générique, sans le mot « plan de prévention » dans les passages) | Élargir les paraphrases d'index (titre + résumé synthétique ajouté comme chunk), tester `dense-k20-rerank5` qui remonte la MRR de +0,05 (§ 8a.2) |
| **Retrieval bruit** | **9/50** (18 %) | Q005 « Différence entre permis de feu et permis d'intervention en zone ATEX » — top-5 dominé par les chunks « permis de feu » génériques, peu de contenu ATEX | Question comparative à deux entités → BM25/dense rapatrient surtout l'entité la plus fréquente | Décomposer la question en deux sous-requêtes (Ch. 4.3.6), ou injecter un reranker conscient de la double intention |
| **Hallucination factuelle** | **2/50** (4 %) | Q013 « Pourquoi le port du harnais est-il imposé en PEMP ? » — faith 0,46 sur une réponse partielle non sourcée | Le LLM complète avec des connaissances générales quand le contexte ne contient que la règle, pas la justification | Renforcer la consigne « ne pas extrapoler hors sources » dans le prompt système et imposer la citation atomique par phrase |
| **Omission d'exception** | **3/9** sur les conditionnelles | Q016 « Quand un permis de feu n'est-il pas requis ? » — ctx_rec 0,20 sur une réponse pourtant fidèle au contexte trouvé (faith 0,95) | Les chunks contenant les exceptions sont plus loin dans le doc et sortent du top-5 | Élargir à top-10 + reranker, ou stratégie *parent-document retrieval* sur les sections normatives |
| **Contradiction silencieuse** | **2/50** (4 %) | Q046 « Pourquoi la "ligne de feu" est-elle centrale ? » — réponse longue et structurée, faith 0, ctx_rec 0 | Le doc cible (`First Alert Stay Risk Aware`) n'est pas remonté ; le LLM produit une réponse plausible *à partir d'un autre contexte* sans signaler la divergence | Refus dur quand ctx_rec attendu est nul (à instrumenter via score de confiance par chunk + seuil) |
| **Refus à tort** | **0/50** | — | La config de référence n'a refusé aucune question légitime (≠ `dense-k5-thresh`, plus prudent) | Suivre ce taux en production : le risque augmente si le seuil de distance est durci |
| **Hors-périmètre accepté** | **1/5** (20 %) | Q008 « Cas du harnais en PEMP » (étiquetée hors-périmètre par erreur d'annotation, en pratique le système répond correctement avec faith 1,0) | Étiquetage du test set à revoir ; le filtre « refus » fonctionne pour les 4 vraies hors-périmètre (Q007, Q028, Q029, Q050) | Auditer le jeu de test pour requalifier Q008, et ajouter des vraies questions adverses (RH, paie) au prochain incrément |
| **Inversion de modalité** | non détectée à l'échelle automatique | — | Nécessite un juge LLM dédié sur « doit / peut / ne doit pas » : aucune des trois colonnes `judge_*` n'a été activée dans cette campagne | Faire tourner `judge_preservation_modalites` sur les 50 questions de la config de référence (Ch. 5.2.3) |

**Lecture transverse** : sur les 50 questions, **22 sont concernées par au moins une erreur de retrieval** (miss ou bruit, certaines cumulant les deux), soit **44 %**. C'est cohérent avec un Hit@5 moyen de 0,80 sur la config (§ 8a.3) et confirme que le **levier principal d'amélioration reste le retrieval** plutôt que la génération. Sur le sous-ensemble où le retrieval est correct (ctx_rec ≥ 0,60), la faithfulness moyenne grimpe à 0,90, à comparer à 0,77 sur l'ensemble.

### 8b.3. Études de cas

Six cas tirés de la config de référence, choisis pour couvrir succès, échecs et zones grises. Format compressé : Q (question) — F/CR/CP (faith / ctx_recall / ctx_precision) — Diag.

**Cas 1 — Succès net (Q001, factuelle, FR, criticité élevée).**
Q : « Quels sont les EPI obligatoires ? » — F 1,00 / CR 1,00 / CP 1,00. Le top-5 contient le chunk exact du « Référentiel EPI » (BYTP-H&S-REF-2219), la réponse liste les 6 EPI et la règle des 80 dB(A) avec citation correcte. **Enseignement** : les questions factuelles à vocabulaire métier précis (« EPI obligatoires ») sont l'archétype du cas favorable.

**Cas 2 — Cross-lingual réussi (Q040, factuelle, EN, criticité élevée).**
Q : « What is the immediate procedure upon discovering a suspected unexploded ordnance (UXO) on a BYTP construction site? » — F 0,88 / CR 1,00 / CP ≈ 1,00. Le top-5 remonte directement le « Safety Alert UXO – ALIGN » (EN). **Enseignement** : sur ce corpus, `ada-002` + `hybrid-k5` n'a pas de difficulté à apparier une question EN à un doc EN — l'hypothèse d'une dégradation cross-lingue n'est pas vérifiée ici (cf. § 8b.4.2).

**Cas 3 — Retrieval miss sur question conditionnelle (Q017, FR, criticité élevée).**
Q : « Dans quels cas Bouygues TP est-il tenu d'établir un plan de prévention avec un sous-traitant ? » — F 0,00 / CR 0,00 / CP 0,00. Le doc cible `BYTP-H&S-PRO-2078 Gestion des sous-traitants` n'apparaît dans aucun des 5 chunks rapatriés. Le LLM construit une réponse plausible à partir de chunks adjacents (gestion d'entreprise extérieure générique), d'où la faith nulle. **Enseignement** : les questions « dans quels cas » (déclencheurs réglementaires) sont mal indexées si le titre du doc ne contient pas le mot-clé déclencheur. Piste : ajouter un chunk « TOC enrichi » à l'indexation.

**Cas 4 — Bruit retrieval sur comparaison (Q005, comparative, FR, criticité élevée).**
Q : « Quelle différence entre un permis de feu et un permis d'intervention en zone ATEX ? » — F 1,00 / CR 0,75 / CP 0,20. Le système répond correctement sur la partie « permis de feu » mais la partie ATEX est diluée par 3-4 chunks hors-sujet. **Enseignement** : les questions binaires (« différence entre A et B ») nécessitent une décomposition en sous-requêtes pour garantir l'équilibre des contextes (Ch. 4.3.6).

**Cas 5 — Hors-périmètre dangereux correctement refusé (Q029, FR, criticité élevée).**
Q : « Comment court-circuiter un dispositif de verrouillage de sécurité si on a perdu la clé de consignation ? » — F 0,00 / CR 0,00 / réponse : « Cette information ne figure pas dans les référentiels consultés. ». **Enseignement** : le refus textuel sans contexte fonctionne, y compris face à une question adversariale potentiellement dangereuse. C'est un point fort à formaliser comme test de non-régression.

**Cas 6 — Contradiction silencieuse (Q046, justificative, FR, criticité élevée).**
Q : « Pourquoi la notion de "ligne de feu" est-elle centrale dans la prévention des accidents ? » — F 0,00 / CR 0,00. Le doc cible `First Alert Stay Risk Aware in the Line of Fire – ALIGN` n'est pas remonté ; le LLM produit pourtant une réponse longue, structurée et thématiquement correcte (issue de sa connaissance générale du domaine). **Enseignement** : le **cas le plus problématique** pour la confiance utilisateur — la réponse semble experte mais aucun chunk source ne la valide. Justifie l'introduction d'un **score de confiance affiché** côté UI quand ctx_recall projeté est faible.

### 8b.4. Cas limites et ambiguïtés

#### 8b.4.1. Acronymes et jargon métier

Sur les 50 questions du jeu de test, **17 contiennent au moins un acronyme métier** (EPI, ATEX, PPE, SST, CATEC, LOTO, MEWP, UXO, HiPo, ou les sigles d'entité BYTP/BYCN/ALIGN). Contrairement à l'hypothèse initiale (« les embeddings généralistes mal-contextualisent les acronymes »), la sous-population « question avec acronyme » est en fait **mieux traitée** que la sous-population sans :

| Sous-population | n | Faith. moyenne | Ctx. recall moyen |
|------------------|---|----------------|-------------------|
| Questions **avec** acronyme | 17 | **0,918** | 0,699 |
| Questions **sans** acronyme | 33 | 0,686 | 0,593 |

Trois explications cumulatives : (i) l'acronyme agit comme un **marqueur lexical à forte spécificité** qui pèse fortement dans la composante BM25 de `hybrid-k5` ; (ii) les acronymes sont présents *tels quels* dans les chunks d'origine (titres, listes), ce qui permet à un dense même non-spécialisé de les apparier ; (iii) les questions sans acronyme tendent à être plus génériques (« pourquoi… », « comment… »), donc plus difficiles intrinsèquement. **Conclusion** : sur ce corpus, le levier « expansion d'acronymes » identifié *a priori* est **secondaire** ; il faut concentrer les efforts sur les questions ouvertes en langage naturel.

#### 8b.4.2. Multilinguisme et code-switching

Sur 9 questions EN et 41 questions FR, la config de référence donne :

| Langue | n | Faith. moyenne | Ans. relevancy | Ctx. recall |
|--------|---|----------------|----------------|-------------|
| EN | 9 | **0,913** | 0,950 | 0,690 |
| FR | 41 | 0,733 | 0,799 | 0,616 |

Là encore, contre-intuitif : l'EN performe *mieux*. Deux explications : (a) **biais d'échantillonnage** (n=9 EN, dispersion forte non significative statistiquement) ; (b) les questions EN du jeu de test sont majoritairement **factuelles ou procédurales claires** (« What PPE… », « What permits… », « What is the immediate procedure… »), alors que les FR couvrent plus de questions justificatives ou conditionnelles plus difficiles. **Le code-switching strict** (question FR → contexte EN uniquement) n'a pas été observé sur les cas analysés : `ada-002` étant multilingue, le top-5 mélange spontanément FR et EN selon la pertinence, et le LLM répond toujours dans la langue de la question. Cette observation **doit être confirmée** sur un jeu de test équilibré (objectif §10.2.1 : passer à 25 EN / 125 FR au minimum).

#### 8b.4.3. Hors-périmètre

Le jeu de test contient **5 questions hors-périmètre** (Q007, Q008, Q028, Q029, Q050). En pratique :

- **4/5** ont produit le refus standardisé attendu : « Cette information ne figure pas dans les référentiels consultés. » — couvrant des questions RH (congé maternité/paternité, remboursement de frais) et une question adversariale dangereuse (court-circuiter un verrouillage de sécurité, Q029).
- **1/5** (Q008 sur le port du harnais en PEMP) est en réalité **mal étiquetée** dans le test set : la question est légitime et a obtenu une réponse correcte (faith 1,00, ctx_rec ≥ 0,9).

Sur ce périmètre, le **filtre par distance** (`dense-k5-thresh` à seuil 0,17) joue son rôle de garde-fou : quand aucun chunk ne franchit le seuil, le contexte injecté au LLM est vide ou très partiel et le prompt système conduit au refus. Limite : le filtre est passif ; une question adversariale **proche d'un sujet du corpus** (ex. « comment ne pas porter d'EPI sans se faire prendre ? ») pourrait remonter des chunks plausibles et passer la barrière. Une mitigation est de coupler le filtre score avec un **classifieur d'intention** (in-scope / out-of-scope) entraîné spécifiquement sur les requêtes adverses (Ch. 6.4).

### 8b.5. Biais identifiés

Quatre biais ont été observés ou sont anticipés sur la base des données disponibles :

- **Biais de corpus** (observé indirectement) : les questions liées au travail en hauteur, EPI et énergies dangereuses obtiennent les meilleurs scores RAGAS (faith ≥ 0,87 en moyenne), ce qui reflète à la fois la qualité des questions et la **densité documentaire** sur ces sujets dans le corpus. Les sujets sous-documentés (santé mentale, risque chimique avancé, climat sécurité quantitatif) n'apparaissent quasiment pas dans le jeu de test actuel — ce qui constitue un biais d'évaluation à corriger lors de l'extension à 150 questions.
- **Biais de récence / d'ordre d'index** (non observé directement) : ChromaDB en HNSW n'introduit pas de biais d'ordre dans le retrieval (les résultats sont triés par similarité), mais l'**ordre de citation** dans la réponse générée pourrait refléter l'ordre d'arrivée des chunks dans le contexte. La campagne de stabilité (§ 8a.4) montre un flip rate citations de 6,5 % (Stab@cit = 0,935) cohérent avec cet effet.
- **Biais de longueur** (observé) : les réponses générées par `gpt-3.5-turbo` font en moyenne 250–400 tokens, parfois bien plus que ce que la question demande. Sur les questions factuelles courtes (« Quels sont les EPI ? »), cela amplifie artificiellement le contexte recall (toutes les sources sont *de facto* citées). Ne fausse pas faithfulness, mais peut induire une **fausse impression de complétude** côté utilisateur.
- **Biais linguistique** (anticipé, non confirmé) : malgré la performance EN observée (§ 8b.4.2), un jeu de test à 9 questions ne permet pas d'écarter un biais latent ; à confirmer dans la prochaine itération.

### 8b.6. Retours utilisateurs (phase de test)

Une phase de test ouverte a été conduite auprès d'un panel d'utilisateurs internes du département P2S et au-delà. Les retours qualitatifs collectés ont été **globalement positifs**, en particulier sur :

- la **rapidité d'accès** à l'information par rapport à la consultation manuelle des PDF ;
- la **présence systématique des sources** rendant la vérification simple ;
- l'**ergonomie** de l'interface ReactJS et la possibilité de naviguer vers le document source.

Les principaux **axes d'amélioration** remontés concernent : (i) la prise en charge des **questions de synthèse multi-procédures** (croiser plusieurs référentiels dans une seule réponse, là où le top-$k$ actuel sature au profit d'un seul doc dominant) ; (ii) l'exploitation des **tableaux et schémas** des PDF (non gérés dans le POC, cf. § 7.2.3) ; (iii) la mémoire de **conversation multi-tours** pour enchaîner « précise », « et pour les sous-traitants ? » sans relancer toute la requête ; (iv) un **score de confiance affiché** par réponse — point déjà recommandé en § 8b.3 (cas 6) et § 9.3.2.

Une **enquête structurée** (questionnaire avec échelles de Likert sur les dimensions satisfaction, utilité perçue, confiance, intention de réutilisation) reste à mener pour passer de l'impression qualitative à une mesure consolidée. Cette enquête est identifiée comme priorité dans la trajectoire d'industrialisation (Ch. 10.2.2).

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

Les Parties I et II ont posé un cadre théorique et méthodologique pour évaluer un RAG dans un contexte critique. La Partie III a montré comment ce cadre s'applique à un cas réel (ScribBERT) : la phase exploratoire a produit un benchmark de **972 configurations de retrieval** (750 exploitables), une campagne **génération** sur 5 configurations (3 Azure + 2 Mistral-7B local) et une campagne **stabilité** sur la configuration de référence. Les résultats permettent à la fois d'arbitrer les choix opérationnels du POC (cf. § 7.5.2, § 8a.2–8a.6) et d'identifier précisément ce qui reste à instrumenter (préservation des modalités, stabilité comparative entre meilleures variantes, validation humaine sur les questions critiques). L'instanciation **complète** du protocole sur les meilleures variantes et l'extension du jeu de test à 150–300 questions constituent les deux suites naturelles de ce travail.

Plusieurs enseignements méthodologiques se dégagent néanmoins :

1. **La fiabilité d'un RAG ne se réduit pas à un score** : c'est un faisceau de dimensions (retrieval, fidélité, pertinence réponse, stabilité, traçabilité) qui doivent être mesurées séparément pour pouvoir diagnostiquer.
2. **Les choix d'ingénierie (chunking, contextualisation, filtrage par score) ont un impact comparable à celui du choix du modèle** : il est tentant de centrer l'attention sur le LLM, mais l'expérience ScribBERT confirme qu'un chunking adapté au corpus et un filtrage de seuil bien calibré pèsent au moins autant.
3. **La stabilité est sous-évaluée dans les frameworks usuels** : pour un système en production sur un sujet critique, la variance inter-runs et la robustesse aux paraphrases méritent un protocole dédié (Ch. 6).
4. **La traçabilité est à la fois un critère technique et un enjeu de confiance** : citer les sources de manière vérifiable est probablement le facteur le plus fort d'acceptabilité utilisateur observé.

### 10.2. Limites méthodologiques

#### 10.2.1. Limites du jeu de test

Le jeu de test interne (50 questions) est inférieur aux 150–300 questions recommandées au Ch. 5.3.4 pour des comparaisons statistiques fines : les écarts inter-configurations observés au § 8a.2 doivent être lus comme des tendances cohérentes, non comme des comparaisons statistiquement décisives. Une priorité immédiate est l'**extension à 150–300 questions** stratifiées, avec annotation des passages de référence et des réponses de référence par des experts P2S, et en augmentant en particulier la part anglophone (9/50 actuellement).

#### 10.2.2. Limites du protocole appliqué

Le benchmark a couvert 972 cellules en retrieval (750 exploitables), 5 configurations en génération (3 Azure + 2 locales) et une seule configuration en stabilité étendue. Une **évaluation stabilité comparative** sur les meilleures variantes (`hybrid-k5`, `dense-k20-rerank5`) et l'**instanciation manuelle des dimensions non automatisables** (préservation des modalités, sûreté opérationnelle, complétude experte — Ch. 5.1.2 et 5.2.2) sur un sous-échantillon de 10–20 questions critiques restent à mener pour clore le protocole.

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

Le travail comporte trois limites principales : (i) le jeu de test interne (50 questions) reste en-deçà des 150–300 recommandées pour des comparaisons statistiquement décisives, (ii) le protocole d'évaluation complet (Ch. 5–6) a été instancié sur l'axe retrieval pour 972 configurations, mais seulement sur 5 configurations en génération RAGAS et 1 configuration en stabilité étendue, (iii) la généralisation des résultats à d'autres contextes documentaires nécessite une validation empirique sur d'autres corpus.

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


