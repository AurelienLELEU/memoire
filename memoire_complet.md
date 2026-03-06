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

### 3.3. Pertinence perçue vs pertinence mesurée

La qualité d’un système se mesure à deux niveaux :

- **Mesures automatiques** (métriques IR, similarité, scores de fidélité) : utiles pour comparer des variantes, mais parfois mal corrélées au jugement humain.
- **Perception utilisateur** (confiance, satisfaction, effort) : essentielle pour l’adoption, mais plus coûteuse et plus subjective.

Un protocole robuste combine souvent les deux (triangulation), en exploitant les métriques comme instruments de diagnostic, et l’évaluation humaine pour valider la pertinence réelle et la sécurité.

Sur le plan méthodologique, cela rejoint l’idée de séparer :

- **évaluation intrinsèque** : mesurer des propriétés internes (qualité des embeddings, séparation positives/négatives, rappel retrieval),
- **évaluation extrinsèque** : mesurer l’effet sur la tâche finale (qualité de réponse, temps de recherche, erreurs évitées).

### 3.4. Travaux récents sur l’évaluation des RAG et LLMs augmentés

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

#### 3.4.1. Formaliser quelques métriques retrieval (rappels utiles)

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

### 3.5. Positionnement de la contribution du mémoire

Dans ce mémoire, l’enjeu est de proposer un cadre d’évaluation qui :

- sépare clairement les erreurs de retrieval et les erreurs de génération,
- prend en compte les spécificités du contexte HSE (criticité, exceptions, autorité des sources),
- reste reproductible et applicable sur un corpus d’entreprise,
- fournit des diagnostics actionnables (quels paramètres améliorer : chunking, top-k, reranking, prompt, température, filtres).

La PARTIE II présentera la méthodologie et les métriques retenues, puis la PARTIE III appliquera ce protocole au cas ScribBERT.

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

