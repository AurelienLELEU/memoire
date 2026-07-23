# Préparation questions/réponses — Soutenance ScribBERT

**Durée de la phase Q&A** : 20 min (cf. guide Hexagone)

**Consigne de posture** : écouter la question jusqu'au bout, reformuler si besoin (« si je comprends bien votre question… »), répondre avec structure (affirmation → justification → chiffre ou renvoi au mémoire). Si tu ne sais pas : « c'est une question pertinente que je n'ai pas traitée dans ce cadre, mais voici ma première intuition… ». Ne pas bluffer.

**Structure du document** :

- Partie A : référentiel des métriques mobilisées (formules, instanciation, interprétation).
- Partie B : réponses flash aux 4 axes de vulnérabilité les plus probables.
- Partie C : Q&A dans l'ordre logique des slides (slide 0 → slide 14).
- Partie D : questions transverses ou de repli (personnel, projet, pièges).

---

# PARTIE A — RÉFÉRENTIEL DES MÉTRIQUES MOBILISÉES

Regroupe l'ensemble des métriques citées dans la soutenance, par dimension. Pour chacune : où elle est instanciée (jeu de données, configuration), à quoi elle correspond, et sa formule. Sert de fiche antisèche technique si le jury demande « comment est calculée exactement telle métrique ? ».

## A.1 — Dimension 1 · Pertinence du retrieval (slide 6)

**Instanciation** : *benchmark* retrieval, **750 configurations exploitables** sur 864 (16 modèles × 9 chunkings × 6 variantes de récupération) × **50 questions annotées**. Comparaison au niveau document (dédoublonnage par `doc_id` avant intersection).

Notations : $Q$ = ensemble des questions, $\mathrm{Rel}(q)$ = passages pertinents pour $q$ (annotés), $\mathrm{TopK}(q)$ = $k$ premiers passages retournés par le système.

**Hit@k** — au moins un passage pertinent est-il dans le top-$k$ ? (binaire par question, moyenné sur $Q$).

$$\mathrm{Hit@k} = \frac{1}{|Q|}\sum_{q\in Q} \mathbb{1}\left[|\mathrm{Rel}(q) \cap \mathrm{TopK}(q)| \geq 1\right]$$

**Recall@k** — proportion des passages pertinents retrouvés dans le top-$k$.

$$\mathrm{Recall@k} = \frac{1}{|Q|}\sum_{q\in Q} \frac{|\mathrm{Rel}(q) \cap \mathrm{TopK}(q)|}{|\mathrm{Rel}(q)|}$$

**Precision@k** — proportion de passages pertinents parmi les $k$ retournés.

$$\mathrm{Precision@k} = \frac{1}{|Q|}\sum_{q\in Q} \frac{|\mathrm{Rel}(q) \cap \mathrm{TopK}(q)|}{k}$$

**MRR** (*Mean Reciprocal Rank*) — inverse moyen du rang du premier document pertinent. Métrique utile quand un unique passage décisif est attendu.

$$\mathrm{MRR} = \frac{1}{|Q|}\sum_{q\in Q} \frac{1}{\mathrm{rank}_q}$$

**nDCG@k** — pertinence graduée, pondérée par la position ; pénalise moins un document pertinent placé en tête qu'en fin de liste. Avec annotations binaires ($rel_i \in \{0,1\}$) :

$$\mathrm{DCG@k} = \sum_{i=1}^{k} \frac{\mathbb{1}[i \in \mathrm{Rel}(q)]}{\log_2(i+1)} \quad;\quad \mathrm{nDCG@k} = \frac{\mathrm{DCG@k}}{\mathrm{IDCG@k}}$$

$\mathrm{IDCG@k}$ est le DCG « idéal » obtenu en supposant tous les passages pertinents parfaitement classés en tête.

## A.2 — Dimensions 2 & 3 · Fidélité et pertinence de la réponse — RAGAS (slides 7, 8)

**Instanciation** : campagne génération, **5 configurations** (3 Azure + 2 Mistral-7B local) × **50 questions**, évaluation via le *framework* RAGAS avec [*LLM-as-judge*](memoire_complet.md#gloss-llm-as-judge). Radar Fig. 8.4 pour la comparaison inter-configurations, stratification par type de question Fig. 9.2.

**Faithfulness** — proportion de propositions atomiques de la réponse effectivement supportées par le contexte. La réponse est décomposée en assertions atomiques par un LLM, chacune vérifiée contre les [*chunks*](memoire_complet.md#gloss-chunk) récupérés.

$$\mathrm{Faithfulness} = \frac{|\text{propositions supportées par le contexte}|}{|\text{propositions totales de la réponse}|}$$

**Context Precision** — proportion de passages récupérés effectivement utiles, pondérée par le rang (les passages utiles doivent être en tête).

$$\mathrm{ContextPrecision@k} = \frac{\sum_{i=1}^{k} \mathrm{Precision@i} \cdot v_i}{|\{i : v_i = 1\}|}$$

où $v_i \in \{0,1\}$ indique si le passage au rang $i$ est jugé pertinent par le [*LLM-juge*](memoire_complet.md#gloss-llm-as-judge).

**Context Recall** — proportion des affirmations de la réponse de référence couvertes par le contexte récupéré.

$$\mathrm{ContextRecall} = \frac{|\text{affirmations de la référence trouvables dans le contexte}|}{|\text{affirmations totales de la référence}|}$$

**Answer Relevancy** — un LLM génère $n$ questions hypothétiques à partir de la réponse produite ; on mesure la similarité cosinus moyenne entre leurs vectorisations et celle de la question originale.

$$\mathrm{AnswerRelevancy} = \frac{1}{n}\sum_{i=1}^{n} \cos(\mathbf{e}_{q_{\text{gen},i}}, \mathbf{e}_{q_{\text{orig}}})$$

**Résultat central slide 7** : configuration `hybrid-k5` + `gpt-3.5-turbo` domine sur les 4 axes (0,765 · 0,756 · 0,687 · 0,629). Mistral-7B local plafonne à 0,681 en faithfulness.

## A.3 — Dimension 4 · Stabilité et répétabilité (slide 9)

**Instanciation** : campagne stabilité, **1 configuration** (`markdown-1200-50` + `ada-002` + `dense-k5-thresh` + `azure-gpt35`) × **50 questions** × **10 runs** à seed constante, plus paraphrases annotées.

Toutes les mesures de recouvrement d'ensembles utilisent l'**indice de Jaccard** :

$$\mathrm{J}(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

Il vaut 1 si les ensembles sont identiques, 0 s'ils sont disjoints.

**Stability@retrieval** — Jaccard moyen entre paires de runs sur les [*chunks*](memoire_complet.md#gloss-chunk) du top-5 récupéré. Résultat : **1,000** (récupération parfaitement déterministe sur ChromaDB avec cette configuration).

$$\mathrm{Stab@ret} = \frac{2}{n(n-1)}\sum_{i<j} \mathrm{J}(\mathrm{TopK}_i, \mathrm{TopK}_j)$$

**Stability@citations** — même formule appliquée aux sources effectivement citées dans la réponse. Résultat : **0,935** (6,5 % de variation moyenne d'un run à l'autre sur le choix des sources citées).

**Stability@answer** — BERTScore F1 moyen entre paires de réponses inter-runs. BERTScore compare les vectorisations contextualisées token par token :

$$\mathrm{BERTScore\text{-}F1} = 2 \cdot \frac{P \cdot R}{P + R} \quad \text{avec} \quad P = \frac{1}{|\hat{y}|}\sum_{\hat{t} \in \hat{y}} \max_{t \in y} \cos(\mathbf{e}_{\hat{t}}, \mathbf{e}_{t})$$

et $R$ symétriquement, sur les [*tokens*](memoire_complet.md#gloss-token) des deux textes comparés. Résultat : **0,937**.

**Robustness@paraphrases** — BERTScore F1 entre réponse à la question originale et réponse à chaque paraphrase annotée. **Chiffre-clé slide 9 : 0,766** — l'écart de 17 points avec la stabilité inter-runs (0,94) est le principal enseignement de la campagne.

## A.4 — Dimension 5 · Traçabilité et auditabilité (slide 10)

**Instanciation** : configuration de référence × 50 questions, essentiellement qualitatif (validation humaine ciblée). Deux métriques quantifiables :

**Citation correctness** — proportion de citations dont le passage cité existe et supporte réellement l'affirmation.

$$\mathrm{CitCorrect} = \frac{|\text{citations valides et supportantes}|}{|\text{citations totales}|}$$

**Citation completeness** — proportion d'affirmations nécessitant une source qui sont effectivement citées.

$$\mathrm{CitComplete} = \frac{|\text{affirmations avec citation}|}{|\text{affirmations nécessitant une source}|}$$

**Le reste** relève du design applicatif : identifiant de [*chunk*](memoire_complet.md#gloss-chunk) journalisé → `doc_name` + page → PDF cliquable → *audit trail* horodaté. Prérequis AI Act pour les systèmes haut risque.

## A.5 — Analyse d'erreurs · Seuils RAGAS (slide 11)

**Instanciation** : configuration de référence × 50 questions. Classification **non-exclusive** en 8 catégories à partir de seuils simples sur les scores RAGAS par question (Ch. 9.2 du mémoire). Une même question peut relever de plusieurs catégories, la somme des barres peut donc dépasser 50 (annoté sur la Fig. 9.1).

| Catégorie | Règle de seuil | Dimension mise en cause |
|---|---|---|
| Échec récupération | `context_recall < 0,30` | Dim 1 |
| Bruit récupération | `context_precision < 0,30` | Dim 1 |
| Hallucination factuelle | `faithfulness < 0,50` sur réponse non-refus | Dim 2 |
| Omission d'exception | `faithfulness ≥ 0,50` ET `context_recall ≥ 0,50` ET `answer_relevancy < 0,50` | Dim 3 |
| Contradiction silencieuse | `faithfulness = 0` sur réponse longue et structurée | Dim 2 |
| Refus à tort | réponse « info non trouvée » avec `relevant_doc_ids` non vide | Dim 5 |
| Hors-périmètre accepté | question annotée hors-périmètre sans refus | Dim 5 |
| Inversion modalité | vérification manuelle (non détectable par RAGAS) | Dim 3 |

## A.6 — Métriques opérationnelles (slides 7, 8, 12)

**Instanciation** : campagne complète, agrégées en médiane et écart-type.

**Latence de vectorisation** (mesurée côté Python autour de l'appel *embedding* seul, aller-retour réseau inclus pour les API) :

- `minilm-l6`, `e5-small-ml` : ~7 ms (local GPU)
- `ada-002` : **~80 ms** (API Azure)
- `qwen3-embed-8b` : ~260 ms (local GPU)
- `embed-3-large` : ~3 300 ms (API Azure)

**Latence de génération** (temps LLM médian) : **~5 s** pour `gpt-3.5-turbo` Azure, **~36–38 s** pour Mistral-7B local. Domine la latence *end-to-end* dans tous les cas (88–99 %).

**Coût par requête** :

- Vectorisation `ada-002` (~50 tokens) : ~0,000005 €
- Génération `gpt-3.5-turbo` (2 500 tokens contexte + 300 tokens réponse) : ~0,002 €
- Total : **~0,002 €/requête**

**Coût de la campagne exploratoire complète** (indexation + 750 configs retrieval + 5 configs génération + 1 config stabilité + évaluation RAGAS) : **~10–15 €**. Le facteur limitant est le temps machine, pas la facture API.

## A.7 — Récapitulatif des chiffres cités à l'oral

| Slide | Métrique / chiffre | Valeur |
|---|---|---|
| 2 | Temps moyen de recherche documentaire manuelle | 2 min 30 |
| 2 | Volume documentaire POC | 130 PDF (≈200 avec clients) |
| 2 | Répartition linguistique corpus | ~40 % FR / 60 % EN |
| 6 | Configurations testées / exploitables | 864 / 750 |
| 6 | Questions annotées | 50 |
| 6 | Bande MRR des 8 meilleurs modèles | ±0,03 |
| 6 | Meilleure MRR observée | 0,724 (`fixed-1024-128` + `ada-002` + `dense-k10`) |
| 7 | Meilleure faithfulness RAGAS | 0,765 (`hybrid-k5` + `gpt-3.5-turbo`) |
| 7 | Latence génération Azure vs Mistral local | 5 s vs 36 s |
| 9 | Stabilité inter-runs (BERTScore F1) | 0,937 |
| 9 | Robustesse aux paraphrases | 0,766 |
| 9 | Écart stabilité − robustesse | 17 points |
| 11 | Questions touchées par un problème retrieval | ~1/4 (13/50) |
| 12 | Coût par requête | ~0,002 € |
| 12 | Coût *benchmark* exploratoire complet | ~10–15 € |

---

# PARTIE B — RÉPONSES FLASH · 4 AXES DE VULNÉRABILITÉ PRÉVISIBLES

Ces quatre points sont ceux sur lesquels le jury a le plus de chances de tester la solidité méthodologique. Objectif : répondre en 30 à 45 secondes, sans défendre l'indéfendable, puis montrer que la limite est identifiée, documentée et déjà traduite en plan d'action.

## B.1 — Taille du jeu de test · 50 questions, est-ce suffisant ?

**Vulnérabilité à anticiper** : le mémoire indique lui-même qu'en-dessous de 100 à 150 questions, les comparaisons fines entre configurations restent sensibles au bruit statistique. Or le *benchmark* retrieval repose sur 50 questions pour 750 cellules exploitables.

**Réponse courte** : non, 50 questions ne suffisent pas pour trancher de manière statistiquement décisive entre des configurations très proches. En revanche, elles suffisent pour une phase exploratoire, c'est-à-dire pour détecter des effets robustes, éliminer des familles de configurations faibles et faire émerger des interactions structurantes, par exemple entre modèle d'embedding et stratégie de chunking. C'est exactement le statut que je donne à mes résultats : des tendances solides pour orienter l'itération suivante, pas un verdict définitif. L'extension du jeu de test à 150-300 questions annotées par des experts P2S est d'ailleurs la priorité absolue de la trajectoire court terme, précisément pour consolider statistiquement ces conclusions avant gel de la configuration de production.

**Réponse express** : j'assume clairement que 50 questions, c'est exploratoire et non décisif. Ça suffit pour faire apparaître des tendances et prioriser les leviers d'amélioration, mais pas pour départager proprement des écarts marginaux. La première action prévue, avant industrialisation complète, c'est de porter le jeu de test à 150-300 questions annotées par des experts métier.

## B.2 — Biais de longueur · le juge LLM sur-note-t-il les réponses verbeuses ?

**Vulnérabilité à anticiper** : le mémoire met en évidence une corrélation forte entre longueur de la réponse et score RAGAS ($r = +0{,}64$ pour la *faithfulness*, $r = +0{,}63$ pour l'*answer relevancy*). Cela suggère un biais de longueur inhérent au paradigme [*LLM-as-judge*](memoire_complet.md#gloss-llm-as-judge).

**Réponse courte** : oui, ce biais existe, et c'est précisément pour cela que je le documente au lieu de le masquer. Une partie de cette corrélation est mécanique — par exemple les refus courts sont notés bas par construction — mais une autre partie relève bien d'un *length bias* du juge, qui tend à récompenser des réponses plus développées parce qu'elles offrent davantage de matière à valider. Ma position n'est donc pas de traiter les scores RAGAS comme une vérité absolue, mais comme un signal à calibrer. Les deux mitigations prévues sont, d'une part, durcir la consigne de concision dans le *prompt* système pour éviter les réponses inutilement verbeuses, et d'autre part, calibrer systématiquement les scores RAGAS sur un échantillon expert annoté humainement, afin de vérifier que le juge ne survalorise pas la forme au détriment du fond.

**Réponse express** : oui, le biais de longueur est réel et je l'ai mesuré. Je n'utilise donc pas RAGAS comme un oracle, mais comme un indicateur à calibrer. Les deux correctifs prévus sont un *prompt* plus strict sur la concision et une calibration systématique sur un sous-échantillon expert annoté par l'humain.

## B.3 — Déséquilibre linguistique · pourquoi si peu de questions en anglais ?

**Vulnérabilité à anticiper** : le corpus contient environ 60 % de documents en anglais, mais le jeu de test ne comporte que 9 questions en anglais contre 41 en français. Cela fragilise la portée des conclusions sur le comportement cross-lingue.

**Réponse courte** : le déséquilibre vient de l'origine même des requêtes initiales : le jeu de test a été dérivé en grande partie des journaux d'usage et des besoins remontés par des équipes majoritairement francophones, ce qui explique la surreprésentation du français. C'est donc un biais d'échantillonnage, pas une propriété souhaitée du protocole. Je ne prétends pas, sur cette base, avoir validé complètement le comportement bilingue du système. Ce que je peux dire, c'est que le retrieval cross-lingue fonctionne dans les cas testés, mais que la validation empirique reste insuffisante, en particulier sur les documents anglais courts de type *Safety Alert*, qui posent déjà des difficultés spécifiques. L'équilibrage linguistique du jeu de test fait partie du chantier d'industrialisation, justement pour confirmer de manière robuste le comportement cross-lingue sur ces cas.

**Réponse express** : le jeu de test reflète d'abord les usages observés des équipes francophones, d'où le 41/9. Je n'en fais donc pas une validation complète du bilinguisme. L'équilibrage linguistique est prévu dans la phase d'industrialisation pour tester correctement le cross-lingue, notamment sur les documents anglais courts.

## B.4 — Extrapolation de la stabilité · pourquoi une seule configuration ?

**Vulnérabilité à anticiper** : le protocole complet de stabilité — 10 runs par question plus paraphrases — n'a été exécuté que sur une seule configuration, alors que plusieurs variantes retrieval et génération existent dans le *benchmark*.

**Réponse courte** : oui, et c'est une limite de portée de la mesure, pas une erreur de protocole. J'ai choisi de lancer cette campagne complète sur la configuration la plus représentative du POC effectivement déployé, parce que le coût expérimental est élevé : dix exécutions par question plus les paraphrases font rapidement exploser le volume d'appels et le temps de traitement. L'objectif était d'abord de mesurer si la stabilité était un problème réel sur le système en usage, pas de cartographier exhaustivement toutes les variantes. Ce premier résultat a déjà une valeur forte puisqu'il montre un écart net entre stabilité inter-runs et robustesse aux paraphrases. En revanche, je n'extrapole pas abusivement ce score à toutes les configurations. La généralisation de ce protocole aux meilleures variantes identifiées — notamment `hybrid-k5` et `dense-k20-rerank5` — est planifiée avant le gel de la configuration de production.

**Réponse express** : la campagne de stabilité complète a été menée sur la configuration la plus représentative du POC déployé, pour savoir si le problème existait réellement en usage. Le résultat est donc valide pour cette configuration, pas pour toutes. L'extension aux meilleures variantes, comme `hybrid-k5` ou `dense-k20-rerank5`, est déjà prévue avant le choix final de production.

---

# PARTIE C — Q&A DANS L'ORDRE DES SLIDES

Chaque section correspond à une slide (ou à un bloc de slides) et regroupe les questions les plus probables. Les réponses restent orales : structure affirmation → justification → chiffre / renvoi mémoire.

---

## C.0 — Slide 0 · Accroche

*Slide manifeste, aucune question technique directement rattachée. Prévoir simplement une reprise si le jury pose une question générique du type « pourquoi commencer par cette provocation ? ».*

### Q0.1 — Pourquoi choisir une accroche aussi frontale sur la déception vis-à-vis de l'IA générative ?

Parce que le sujet est trop souvent abordé sous l'angle de la performance apparente — « ChatGPT est bluffant » — et pas de la fiabilité. Or c'est précisément l'écart entre ces deux plans qui structure tout mon mémoire. La provocation initiale sert à installer immédiatement le fait que la fluidité d'une réponse n'est pas une preuve de sa validité, et que c'est exactement ce que le protocole d'évaluation cherche à instrumenter.

---

## C.1 — Slide 1 · Titre et contexte

### Q1.1 — Pourquoi ce nom, ScribBERT ?

C'est un clin d'œil aux origines techniques du projet — BERT, l'architecture Transformer qui a démocratisé les représentations contextualisées de texte et sur laquelle reposent la plupart des modèles de vectorisation utilisés — associé à « Scribe », qui évoque la fonction documentaire de l'assistant : consigner, restituer, citer. Le nom a été adopté dès le POC et est resté.

### Q1.2 — Trois ans d'alternance, mais un mémoire uniquement sur ScribBERT ?

Non, l'alternance a duré trois ans. La première année a été consacrée à l'immersion métier au département P2S et à la reprise du système d'indicateurs Power BI. La deuxième et la troisième années ont couvert le POC puis la phase exploratoire de ScribBERT, qui est ce que documente ce mémoire. Le sujet est cadré parce que c'est celui qui présente le plus d'intérêt méthodologique et qui a produit un volume de résultats exploitables suffisant pour être rapporté rigoureusement.

---

## C.2 — Slide 2 · Le problème à résoudre

### Q2.1 — Les 2 min 30 par recherche, d'où viennent ces chiffres ?

Ils viennent des statistiques d'usage du SharePoint interne du département P2S et des retours utilisateurs recueillis pendant la phase d'immersion en première année d'alternance. Ce ne sont pas des chiffres d'une étude externe, ce sont des mesures internes. Les 10 minutes évoquées pour les cas complexes viennent des mêmes sources — recherches multi-documents, cas où l'utilisateur doit ouvrir plusieurs PDF pour croiser des références.

### Q2.2 — Vous dites que ScribBERT n'est pas un dispositif de sécurité. Ce n'est pas une manière de vous dédouaner ?

Non, c'est un cadrage juridique et fonctionnel précis. Un dispositif de sécurité, au sens des référentiels santé-sécurité, désigne un équipement technique validé — un harnais, un interlock, un détecteur de gaz. ScribBERT n'est rien de tout cela : c'est un outil documentaire qui facilite l'accès au bon référentiel. La responsabilité juridique de la sécurité des travailleurs reste celle de l'employeur, quelle que soit la technologie utilisée. Mais je ne me dédouane pas pour autant : dès lors qu'un outil alimente une décision de prévention, la qualité de sa contribution doit être mesurée. C'est précisément l'objet du mémoire.

### Q2.3 — 130 documents, c'est peu pour parler de RAG ?

C'est peu à l'échelle d'un *benchmark* académique — BEIR utilise des corpus de 100 000 à 1 million de documents — mais c'est représentatif d'un cas d'usage d'entreprise sur un périmètre spécialisé. Le défi n'est pas la scalabilité de l'index, c'est la qualité de la récupération et de la génération sur un corpus dense, normatif et bilingue. Sur ce type de corpus, l'ajout de documents ne résout pas les problèmes d'omission d'exception ou d'inversion de modalité qui structurent l'évaluation. L'extension à ~200 documents (référentiels clients : ENBRIDGE, PAS 91, OSHA) est déjà en cours, et la trajectoire d'industrialisation prévoit le passage à l'échelle groupe.

---

## C.3 — Slide 3 · La thèse défendue

### Q3.1 — Pourquoi cinq dimensions et pas trois, ou sept ? Comment avez-vous déterminé ce découpage ?

Le découpage est issu d'un raisonnement par les modes d'échec. J'ai d'abord listé les types de défaillances observés concrètement sur ScribBERT — passage non remonté, hallucination, omission d'exception, réponse variable, citation non vérifiable — puis je les ai regroupés par propriété qu'ils mettent en cause. Cinq propriétés se sont stabilisées naturellement : pertinence du retrieval, fidélité aux sources, pertinence de la réponse, stabilité, traçabilité.

Est-ce qu'on pourrait en ajouter ? Oui. On pourrait par exemple isoler la « préservation des modalités normatives » comme une sixième dimension dédiée, plutôt que de la rattacher à la fidélité. On pourrait aussi ajouter une dimension « coût opérationnel ». Mais à cinq, chaque dimension est adossée à au moins une famille de métriques instrumentables, ce qui est le critère que je me suis imposé. J'ai évité de multiplier les dimensions au-delà de ce qui est mesurable avec les outils disponibles — sinon, on crée des cases vides dans le tableau.

Le modèle n'est pas figé : il peut s'enrichir à mesure que les outils d'évaluation progressent. L'important, c'est le principe de décomposition, pas le chiffre cinq en lui-même.

### Q3.2 — Pourquoi ne pas utiliser un score composite unique (une note sur 100) plutôt que cinq scores séparés ?

Parce qu'un score composite masque l'origine de l'erreur. Prenons un exemple : une configuration obtient 78/100. Une autre obtient aussi 78/100. Sont-elles équivalentes ? Peut-être pas du tout : la première peut avoir un excellent retrieval mais une fidélité médiocre, la seconde peut avoir le profil inverse. L'action correctrice est complètement différente — reranking dans un cas, durcissement du prompt dans l'autre — mais le score composite donne la même note.

En contexte santé-sécurité, c'est encore plus critique : un système qui a 95/100 en moyenne mais 0,50 de fidélité sur les questions conditionnelles « que faire si… » est dangereux, et le score composite ne remontera pas cette faiblesse localisée.

Un score composite peut avoir du sens en production (pour un tableau de bord synthétique, ou un seuil de déploiement), mais il ne sert pas à diagnostiquer. Mon protocole produit les scores par dimension, qui permettent le diagnostic ; la synthèse en score unique peut se faire dans un second temps, avec des pondérations adaptées au contexte métier.

### Q3.3 — Comment pondérez-vous les cinq dimensions entre elles ? Sont-elles d'importance égale ?

Dans le protocole tel que je l'ai conçu, elles ne sont pas pondérées — elles sont reportées séparément. C'est un choix délibéré : la pondération relève d'un arbitrage métier qui dépend du contexte de déploiement.

Si je devais pondérer pour ScribBERT, je mettrais la fidélité aux sources en priorité 1, parce que c'est l'erreur la plus dangereuse en santé-sécurité (une affirmation non supportée par les sources peut induire une mauvaise décision). La traçabilité en priorité 2, parce qu'elle conditionne la confiance et la conformité réglementaire. Ensuite la stabilité, puis la pertinence retrieval, puis la pertinence réponse.

Mais cette hiérarchie ne serait pas la même pour un RAG juridique (où la traçabilité serait probablement en numéro 1) ou un RAG d'assistance commerciale (où la pertinence réponse primerait). Le cadre est pensé pour être instancié avec les pondérations du domaine cible.

### Q3.4 — Comment votre cadre se compare-t-il à RAGAS ? Est-ce une extension, un remplacement ?

Ni l'un ni l'autre exactement. RAGAS est un outil d'évaluation automatique que j'utilise dans mon protocole — c'est un des instruments, pas le cadre. Mon cadre est plus large : il ajoute la stabilité (absente de RAGAS), la traçabilité (absente de RAGAS), l'évaluation humaine structurée, et surtout le principe de décomposition diagnostique : localiser l'erreur dans la chaîne plutôt que constater un score global.

RAGAS est excellent pour produire des scores de *faithfulness*, *context precision*, *answer relevancy*, *context recall*. Je les utilise tels quels. Mais RAGAS ne dit pas *pourquoi* la *faithfulness* est basse — est-ce un problème de retrieval, de prompt, de chunking ? Mon protocole associe chaque score à une dimension, chaque dimension à une famille d'étages, et chaque croisement à une action correctrice. C'est ça le diagnostic.

### Q3.5 — Si vous deviez ajouter une sixième dimension demain, ce serait laquelle ?

Probablement la **robustesse adversariale**. J'ai des tests hors-périmètre dans le jeu de test — 4 questions adversariales dont une dangereuse (court-circuiter un verrouillage de sécurité) — et le système les refuse correctement. Mais c'est un échantillon trop petit pour en faire une dimension. Une sixième dimension dédiée testerait systématiquement la résistance aux *prompt injections*, aux questions à présupposés faux, aux requêtes qui tentent de contourner les garde-fous. C'est un enjeu de sécurité du système lui-même, distinct de la sécurité du contenu.

Autre candidat : la **fraîcheur documentaire**, c'est-à-dire la capacité du système à détecter et à signaler qu'une source utilisée est obsolète (document de 2020 remplacé par une version 2025). Aujourd'hui, ScribBERT ne le fait pas.

---

## C.4 — Slides 4 et 5 · Fondamentaux RAG (pédagogique)

### Q4.1 — Pourquoi RAG plutôt que *fine-tuning* ?

Trois raisons. La première, c'est la traçabilité : dans un RAG, les documents consultés sont identifiables et citables. Un modèle fine-tuné « sait » des choses mais ne peut pas dire d'où elles viennent — c'est rédhibitoire dans notre contexte. La deuxième, c'est la mise à jour : nos procédures évoluent régulièrement, et réentraîner un modèle à chaque révision documentaire serait trop coûteux et non traçable. Dans un RAG, on réindexe. La troisième, c'est empirique : une étude comparative récente d'Ovadia et al. (2024) montre que sur des tâches d'injection de connaissances nouvelles, le RAG surpasse systématiquement le *fine-tuning* supervisé, et plus encore quand l'information est rare ou évolutive.

Cela dit, les deux ne sont pas exclusifs. Un *fine-tuning* léger pour calibrer le ton ou la structure de réponse, couplé à un RAG pour l'accès aux connaissances, est une combinaison pertinente que je n'ai pas explorée dans ce mémoire mais qui figure dans les perspectives.

### Q4.2 — Les cinq étages de la chaîne RAG (slide 5) et les cinq dimensions d'évaluation, c'est la même chose ?

Non, et c'est un point que j'ai tenu à clarifier dans la présentation. Les cinq étages — ingestion, chunking, vectorisation, retrieval, génération — décrivent *où* dans la chaîne une erreur peut naître. Ce sont des positions structurelles. Les cinq dimensions — pertinence retrieval, fidélité, pertinence réponse, stabilité, traçabilité — décrivent *ce qu'on mesure* sur le résultat du système. Ce sont des propriétés.

Les deux grilles sont orthogonales. La stabilité, par exemple, est transverse à toute la chaîne : elle peut être affectée par la stochasticité du LLM (étage génération) mais aussi par l'approximation ANN de l'index (étage vectorisation/retrieval). La traçabilité est aussi transverse : elle dépend du format de citation (génération) mais aussi de la structure des métadonnées (ingestion/chunking).

C'est précisément le croisement des deux grilles qui rend l'analyse d'erreurs actionnable. Quand je dis en slide 11 « cette erreur relève de la dimension 2 (fidélité), elle est localisée à l'étage génération, donc l'action correctrice est un durcissement du prompt », j'utilise les deux grilles simultanément. Sans la grille des dimensions, je sais juste que la réponse est fausse. Sans la grille des étages, je sais qu'elle est infidèle mais je ne sais pas quoi corriger.

### Q4.3 — Qu'est-ce qui distingue votre approche des architectures Advanced RAG dont on parle beaucoup ?

Les architectures *Advanced RAG* documentées dans la littérature (Gao et al., 2024) empilent plusieurs étages : récupération large, filtrage, reranking, génération conditionnée, parfois avec boucles de réflexion. Ce sont des architectures. Mon apport, ce n'est pas d'inventer une nouvelle architecture, c'est de proposer un cadre d'évaluation qui fonctionne indépendamment de l'architecture choisie. Sur ScribBERT, la configuration testée est encore assez simple (dense pur ou hybride) parce que c'est le POC ; le cadre d'évaluation, lui, serait le même si on passait à une architecture *agentic* ou à du *GraphRAG*.

---

## C.5 — Slide 6 · Dimension 1 · Pertinence du retrieval

*Métriques et formules : voir Partie A.1. Les questions ci-dessous portent sur les choix d'implémentation et l'interprétation.*

### Q5.1 — Pourquoi `ada-002` alors qu'il est ancien ?

Parce que sur ce corpus, il n'y a pas de gain mesurable à passer à un modèle plus récent ou plus gros. `ada-002` est dans la bande de ±0,03 de MRR avec les huit meilleurs modèles testés, y compris `embed-3-large` d'OpenAI qui a trois fois plus de dimensions — et sur mon corpus, les deux donnent des scores rigoureusement identiques, à moins de 0,001 près, pour une latence de 80 ms contre 3 300 ms.

Le choix s'est fait sur les critères pratiques : `ada-002` est déjà déployé dans le *tenant* Azure de Bouygues Construction, ce qui supprime le coût d'hébergement GPU et le délai de mise en place. Il est multilingue et gère aussi bien le français que l'anglais sur le corpus testé. Et sa latence reste négligeable devant celle de la génération LLM (5 secondes pour GPT-3.5). C'est un choix documenté et opérationnel, pas un choix par défaut.

### Q5.2 — Pourquoi ChromaDB et pas Qdrant, Pinecone, Weaviate ?

ChromaDB est le choix du POC, pas le choix définitif. Il s'est imposé par sa simplicité d'intégration, son déploiement local sans dépendance cloud, et le fait qu'il était suffisant pour un corpus de 200 documents. Pour la mise en production à l'échelle groupe, la question sera réévaluée : Qdrant ou Weaviate offrent des garanties de scalabilité, de filtrage optimisé et de gestion distribuée que ChromaDB n'offre pas. C'est dans le cahier des charges de l'industrialisation.

### Q5.3 — Le chunking par regex sur les marqueurs Markdown, c'est fragile ?

C'est spécifique au corpus, pas fragile. Les référentiels du corpus ScribBERT partagent la même charte de mise en forme — c'est une propriété du processus documentaire de Bouygues TP. Les titres, numérotations, structures de paragraphe sont suffisamment homogènes pour qu'une regex bien ciblée les capture proprement. C'est d'ailleurs plus rapide à exécuter et plus prévisible qu'un chunking sémantique, qui n'a d'ailleurs pas montré de gain mesurable sur ce corpus dans le *benchmark* — il finit dernier des neuf stratégies testées en MRR moyenne.

Cela dit, pour le passage à l'échelle avec les documents des filiales et des clients, la regex devra être adaptée ou complétée par un *parser* plus robuste, parce que les formats seront moins homogènes. C'est un risque identifié.

### Q5.4 — L'hybridation BM25 + dense : pourquoi n'est-elle pas déjà en production ?

Parce que le POC a été construit pour valider la faisabilité et l'utilité avant d'optimiser. Le dense pur était plus simple à implémenter et suffisant pour les premiers retours utilisateurs. L'hybridation est apparue comme priorité numéro un dans les résultats du *benchmark* — +0,031 de MRR, et la meilleure configuration absolue utilise `hybrid-k5`. Elle est dans le cahier des charges de la version cible 2026. En pratique, l'implémentation est assez directe : BM25 sur le texte brut des chunks, récupération dense en parallèle, fusion par *Reciprocal Rank Fusion*.

### Q5.5 — Pourquoi une approche OFAT (un facteur à la fois) plutôt qu'un plan factoriel complet ?

En réalité, j'ai fait un plan factoriel complet côté retrieval : 16 modèles × 9 chunkings × 6 variantes = 864 cellules. C'est plus qu'un OFAT. En revanche, côté génération, j'ai testé 5 configurations seulement, parce que chaque *run* génération coûte en temps et en appels API, et qu'il fallait arbitrer.

L'OFAT est plutôt la logique de lecture des résultats : pour interpréter l'effet d'un facteur (par exemple le chunking), on marginalise sur les autres (en moyennant sur tous les modèles et toutes les variantes de retrieval). C'est une simplification, qui ne capture pas les interactions — mais les interactions sont visibles dans la heatmap complète (slide 6), et le tableau des meilleurs chunkings par modèle montre bien qu'elles existent.

### Q5.6 — Vous testez `dense-k5-neigh` (ajout des voisins n−1/n+1) et la MRR baisse. Pourquoi la conserver alors ?

Parce que la MRR mesure la pureté du top-5 récupéré, alors que la génération bénéficie du contexte élargi. Concrètement, l'ajout des voisins ajoute des chunks qui restaurent les références anaphoriques (« cette règle », « les EPI mentionnés »), ce qui aide le LLM à produire une réponse mieux ancrée. La campagne génération confirme cet effet : `dense-k5-neigh` donne une meilleure *faithfulness* que `dense-k5-thresh` malgré une MRR retrieval plus basse. C'est exactement l'illustration du découplage « pureté retrieval ≠ utilité génération ».

### Q5.7 — Le [*cross-encoder*](memoire_complet.md#gloss-cross-encoder) apporte +0,047 de MRR mais coûte cher. Comment arbitrez-vous ?

En production, l'arbitrage est nettement en faveur du reranking. Les 300-500 ms ajoutées à la latence sont négligeables devant les 5 secondes de la génération LLM (moins de 10 % de surcoût), et le gain de 8 % relatif sur la MRR — plus important sur la *faithfulness* en aval — justifie clairement le coût. Le reranking est inscrit comme priorité 2 dans la trajectoire d'industrialisation, juste après l'hybridation BM25.

---

## C.6 — Slide 7 · Dimension 2 · Fidélité aux sources

*Métriques RAGAS et formules : voir Partie A.2.*

### Q6.1 — Le [*LLM-as-judge*](memoire_complet.md#gloss-llm-as-judge), c'est fiable ? Vous ne risquez pas d'évaluer un LLM par un autre LLM ?

Le risque est réel et documenté dans le mémoire. Il y a trois biais identifiés. Le biais de longueur : le LLM-juge tend à mieux noter les réponses verbeuses, ce que j'ai d'ailleurs observé et quantifié — corrélation de Pearson de +0,64 entre longueur de la réponse et score de *faithfulness*, dont une part est légitime (les refus courts sont notés 0 par construction) mais une part est artificielle. Le biais d'auto-validation circulaire : si le même modèle génère et juge, il peut valider ses propres erreurs. Et le biais de format : les réponses structurées en listes sont systématiquement mieux notées.

Comment j'ai mitigé ça : premièrement, le LLM-juge est un modèle distinct du générateur (le juge RAGAS tourne sur GPT-4 via l'API, le générateur testé est GPT-3.5 ou Mistral-7B). Deuxièmement, les justifications du juge sont journalisées, pas seulement le score : on peut vérifier a posteriori pourquoi une proposition a été jugée « supportée ». Troisièmement, la calibration humaine sur le sous-échantillon de 15 questions critiques sert précisément à vérifier que les scores RAGAS ne dérivent pas de la perception experte.

Est-ce parfait ? Non. C'est pourquoi je ne me repose jamais sur une seule source d'évaluation, et c'est pourquoi la dimension « préservation des modalités » reste évaluée humainement — les juges LLM actuels ne sont pas fiables pour distinguer « doit » de « peut » dans un contexte normatif.

### Q6.2 — Pourquoi GPT-3.5 et pas GPT-4 ou Claude ?

Deux raisons pragmatiques : le coût et la vitesse. Le *benchmark* exploratoire a nécessité environ 750 appels LLM (5 configurations × 50 questions × 3 campagnes), et GPT-3.5 a permis de faire tourner l'ensemble pour moins de 15 € tout en maintenant des temps de réponse médians de 5 secondes. GPT-4, à l'époque des premiers tests, était environ 20 fois plus cher et 3 à 5 fois plus lent.

Est-ce que GPT-3.5 est le LLM optimal ? Non. Le plafond de *faithfulness* observé à 0,77 est presque certainement imputable à la taille du modèle. La cible pour la production est un modèle plus récent — GPT-4o, Claude Sonnet 4, Mistral Large — et le *benchmark* de sélection est prévu dans la trajectoire d'industrialisation. GPT-3.5 a été le bon choix pour la phase exploratoire, il ne sera pas le choix de production.

### Q6.3 — Mistral-7B en local à 36 secondes, ce n'est pas viable. Pourquoi l'avoir testé alors ?

Pour deux raisons. D'abord, pour valider quantitativement l'écart avec la voie Azure et le documenter — ce qu'un discours d'intuition n'aurait pas suffi à établir. Ensuite, parce que Bouygues Construction opère sur des chantiers en environnement totalement isolé — sites militaires, installations nucléaires, certains chantiers offshore — où toute connexion à un service externe est exclue. Sur ces cas, une chaîne 100 % auto-hébergée est la seule option possible, et il fallait établir un point de référence sur ce que ça donne aujourd'hui. Le résultat est clair : 0,68 de *faithfulness* et 36 s de latence, ce qui n'est pas viable en temps réel mais peut être acceptable en mode batch pour un préventeur qui prépare une intervention à l'avance. C'est une piste conservée, pas la voie principale.

### Q6.4 — Les scores RAGAS sont-ils comparables entre configurations qui n'ont pas les mêmes chunks dans le contexte ?

C'est une subtilité importante. Le *context recall* RAGAS mesure la couverture de la réponse de référence par le contexte récupéré. Si deux configurations utilisent des chunkings différents, les chunks ne sont pas les mêmes, et le *context recall* n'est pas directement comparable au grain du chunk — il l'est au grain du document de référence, qui est commun.

Pour la *faithfulness* et l'*answer relevancy*, le problème est moindre : elles portent sur la réponse générée vs le contexte effectivement fourni, donc chaque score est cohérent avec sa propre configuration. La comparaison entre configurations reste valide si on compare des scores calculés dans des conditions homogènes (même jeu de questions, même LLM, même *prompt*).

C'est d'ailleurs pour ça que j'ai gelé le LLM, le *prompt* et la température lors des comparaisons retrieval : isoler l'effet du facteur testé.

---

## C.7 — Slide 8 · Dimension 3 · Pertinence de la réponse

### Q7.1 — Comment articulez-vous évaluation automatique et évaluation humaine ? Quelle est la part de chacune ?

Le protocole est hybride, par construction. L'évaluation automatique — métriques IR classiques pour le retrieval, RAGAS pour la génération — couvre l'ensemble du jeu de test sur toutes les configurations. C'est le balayage large, qui sert à comparer et à identifier les tendances. L'évaluation humaine est ciblée : elle porte sur un sous-échantillon de 15 questions critiques, majoritairement conditionnelles et procédurales, de criticité élevée.

La logique, c'est la triangulation : une conclusion n'est retenue que si les deux approches convergent. Et quand elles divergent, c'est souvent les cas les plus instructifs — ceux où le [*LLM-juge*](memoire_complet.md#gloss-llm-as-judge) RAGAS note 0,90 mais l'expert constate qu'une exception a été omise, ou inversement.

Sur les dimensions, la répartition est la suivante : les dimensions 1 (pertinence retrieval) et 4 (stabilité) sont presque entièrement automatisables. La dimension 2 (fidélité) l'est à 80% via RAGAS, mais la préservation des modalités normatives — « doit » vs « peut » — nécessite une vérification humaine. Les dimensions 3 (complétude) et 5 (traçabilité) sont les plus dépendantes de l'évaluation humaine ou d'un design applicatif contrôlé.

### Q7.2 — Comment fonctionne la fonctionnalité *gap analysis* que vous mentionnez ?

Concrètement, l'utilisateur sélectionne dans l'interface deux sous-ensembles de documents à comparer — par exemple « procédures Bouygues TP » vs « exigences client ENBRIDGE ». Il pose sa question, et le système exécute la même requête sur chaque sous-corpus séparément, avec deux appels retrieval + génération. Les deux réponses s'affichent côte à côte, ce qui rend les écarts directement lisibles sans que le LLM ait à « choisir » ou synthétiser en amont.

C'est né d'un besoin métier concret : les questions comparatives « quelle différence entre A et B » saturent souvent le *top-k* avec l'entité la plus représentée dans le corpus, ce qui donne des réponses déséquilibrées. En isolant les sources en amont, on garantit une comparaison sur base équivalente. Au-delà de cet usage, la même fonctionnalité sert à accélérer l'ouverture de chantiers dans un nouveau pays : on peut identifier rapidement les écarts entre nos référentiels internes et les réglementations locales applicables. C'est un développement que je n'ai pas trouvé dans les outils RAG existants.

### Q7.3 — Les questions conditionnelles décrochent (`context_recall` moyen 0,42). Comment envisagez-vous de corriger ça ?

Deux leviers. D'abord, le *parent-document retrieval* : on remonte le chunk pertinent mais on injecte aussi son contexte paragraphe parent, ce qui a de fortes chances de capturer l'exception qui suit souvent la règle. Ensuite, le *query rewriting* : reformuler la question pour expliciter la condition, par exemple « Que faire si X et si Y ? » en deux sous-requêtes distinctes lancées en parallèle. Ces deux leviers font partie des priorités court terme de la trajectoire d'industrialisation.

---

## C.8 — Slide 9 · Dimension 4 · Stabilité

*Métriques et formules : voir Partie A.3.*

### Q8.1 — La stabilité est votre dimension 4. Pourquoi la traiter comme une dimension à part entière plutôt que comme un indicateur secondaire ?

Parce que la stabilité a un double statut. C'est une dimension de qualité en soi : un utilisateur qui obtient deux réponses différentes à la même question perd confiance, et dans un contexte santé-sécurité, il peut prendre deux décisions différentes selon le moment. Mais c'est aussi une condition méthodologique : si la variance intra-configuration est élevée, comparer deux configurations sur une seule exécution n'a pas de sens statistique. La mesure de stabilité conditionne donc la robustesse de toutes les autres comparaisons.

C'est d'ailleurs ce que le résultat 0,94 vs 0,77 montre très concrètement : à requête identique, la variance est faible, les comparaisons tiennent. Mais si on considère la robustesse aux paraphrases — ce qui correspond au comportement réel de l'utilisateur — la variance est beaucoup plus élevée, ce qui signifie que les scores moyens par dimension sont eux aussi plus bruités qu'on ne le pense si on ne contrôle pas la formulation.

Je n'ai pas trouvé de *framework* qui traite ça explicitement. RAGAS, TruLens, LangSmith évaluent la qualité ponctuelle. La stabilité est un ajout spécifique de mon protocole, et c'est un des apports méthodologiques que je revendique dans ce mémoire.

### Q8.2 — Comment envisagez-vous de corriger l'écart robustesse aux paraphrases de 0,77 ?

Le levier principal est une étape de normalisation de requête en amont du retrieval, via un LLM léger qui reformule la question en canonique — expansion des acronymes, correction des fautes, standardisation du vocabulaire métier. Cela ferait converger différentes formulations vers la même représentation avant l'étape d'embedding, et devrait ramener la robustesse plus près de la stabilité inter-runs. C'est mesurable directement avec le protocole actuel : rejouer les paraphrases avec le module de normalisation en amont et comparer le BERTScore F1. C'est une expérimentation prévue court terme.

### Q8.3 — La température est à 0,05 dans le POC. Pourquoi pas 0 strict ?

Une température strictement nulle produit parfois des sorties répétitives ou des artefacts sur certains modèles (redondance lexicale, boucles). Une valeur de 0,05 conserve un déterminisme quasi complet — la stabilité inter-runs mesurée à 0,94 le confirme — tout en évitant ces artefacts. En pratique, la variance résiduelle observée est presque entièrement due à la non-reproductibilité GPU côté Azure, pas à la température.

### Q8.4 — Vous n'avez pas fixé de seed. Ce n'est pas problématique pour la reproductibilité ?

Si, et c'est une limite identifiée. Pour la version production, la seed sera fixée systématiquement et les identifiants `system_fingerprint` renvoyés par Azure OpenAI journalisés, pour tracer les rares cas où un même appel donnerait un résultat différent après mise à jour silencieuse du modèle côté fournisseur. Sur le POC, la stabilité mesurée à 0,94 sans seed est déjà satisfaisante pour l'usage actuel, mais la reproductibilité stricte reste un prérequis pour la conformité AI Act.

---

## C.9 — Slide 10 · Dimension 5 · Traçabilité

*Métriques et formules : voir Partie A.4.*

### Q9.1 — La dimension 5 (traçabilité) n'a pas de métrique quantitative principale. Ce n'est pas une faiblesse ?

C'est une caractéristique, pas une faiblesse. La traçabilité est une propriété de design, pas de performance statistique. Soit le système cite ses sources de manière vérifiable et journalisée, soit il ne le fait pas. On peut mesurer la *citation completeness* (toutes les affirmations sont-elles sourcées ?) et la *citation correctness* (les passages cités supportent-ils réellement l'affirmation ?), ce qui donne des métriques — mais la traçabilité au sens fort, c'est la chaîne complète : identifiant de chunk → document → page → PDF téléchargeable → *audit trail* horodaté.

Ce que la dimension 5 capture, c'est l'**auditabilité** du système : la capacité à reconstituer, a posteriori, le chemin complet d'une réponse. C'est ce que l'AI Act exige pour les systèmes à haut risque, et c'est ce que les utilisateurs terrain placent comme facteur numéro un d'acceptabilité dans les retours que j'ai collectés.

### Q9.2 — Pourquoi un seuil de distance fixe (0,17) plutôt qu'un seuil adaptatif ?

Par simplicité, et parce qu'il est empiriquement efficace : les 4 questions hors-périmètre sont correctement refusées, et le taux de refus à tort sur la configuration avec seuil est de 6 sur 46 questions in-scope — tolérable mais perfectible. Un seuil adaptatif — par exemple basé sur l'écart entre le score du premier et du cinquième chunk — serait plus robuste et fait partie des pistes d'amélioration identifiées. Il existe aussi la possibilité de calibrer le seuil par famille de question (factuelle vs procédurale), ce qui n'a pas été testé.

### Q9.3 — Le refus contrôlé, comment fonctionne-t-il exactement ?

Il repose sur deux mécanismes complémentaires. D'abord, un filtrage par distance à la récupération : les chunks au-delà d'un seuil de similarité cosinus (distance 0,17) sont exclus avant d'atteindre le LLM. Ensuite, une consigne stricte dans le *prompt* système : « si aucun extrait pertinent, réponds exactement "Cette information ne figure pas dans les référentiels consultés" ». Sur la configuration de référence Azure avec GPT-3.5, ces deux mécanismes fonctionnent bien : les 4 questions adversariales déclenchent toutes le refus attendu, y compris la question la plus dangereuse du jeu de test.

En revanche, le mécanisme n'est pas verrouillé au niveau applicatif : rien n'empêche théoriquement le LLM de bavarder à partir de sa connaissance générale si le *prompt* est mal calibré. Sur les *chaînes* Mistral-7B local, on a observé exactement ce cas (Q046). Un garde-fou plus strict — refus forcé applicatif si le contexte injecté est vide — est prévu pour la version production.

---

## C.10 — Slide 11 · Analyse d'erreurs

*Seuils RAGAS et catégories : voir Partie A.5.*

### Q10.1 — Le comptage des erreurs est non-exclusif. Est-ce que ça ne rend pas les proportions difficiles à interpréter ?

Au contraire, c'est ce qui rend l'analyse actionnable. Une même question peut être touchée simultanément par un problème de retrieval et un problème de génération — c'est même le cas fréquent. Si je forçais l'exclusivité, il faudrait choisir arbitrairement la catégorie « dominante », ce qui masquerait la coexistence des causes. Le graphe indique clairement en légende que la somme peut dépasser 50, et l'axe X est étiqueté sans normaliser à 100 %. Ce qui compte, c'est la cardinalité par catégorie prise indépendamment, parce que chaque catégorie renvoie à une action correctrice ciblée.

### Q10.2 — Sur les 8 catégories, laquelle vous paraît la plus préoccupante en priorité ?

La contradiction silencieuse, sans hésitation. Sur la configuration de référence Azure, elle est à zéro, ce qui est rassurant. Mais elle apparaît sur les *chaînes* Mistral-7B local — Q046, sur la « ligne de feu ». Le modèle a produit une réponse longue, structurée, thématiquement plausible, fabriquée à partir de sa connaissance générale sans aucun ancrage documentaire. C'est le pire scénario en santé-sécurité : le fond de la réponse est peut-être correct, mais rien ne le prouve, et l'utilisateur n'a aucun moyen de le savoir. C'est ce qui justifie le garde-fou applicatif prévu pour la voie Mistral : si `faithfulness` estimée est nulle et que la réponse dépasse un seuil de longueur, forcer un refus.

Ensuite viennent les échecs de récupération (10/50), qui sont le levier le plus rapide à améliorer via l'hybridation et le reranking.

### Q10.3 — Q003 sur le seuil O2 en espace confiné — vous dites que le bon chunk sort du top-5. Vous avez la preuve que le chunk est bien indexé ?

Oui, vérification manuelle faite. Le chunk contenant le seuil 19,5 % existe bien dans l'index (référentiel `REF-2223`), il apparaît dans les résultats du retrieval au rang 8 sur la configuration de référence, donc dans le *top-10* mais pas dans le *top-5* effectivement injecté au LLM. C'est un cas typique où passer à `dense-k20-rerank5` corrigerait probablement le problème : le *cross-encoder* remonterait le chunk normatif court et dense au-dessus des chunks longs plus verbeux qui parlent en général de la ventilation. C'est aussi pour ça que le reranking est priorisé.

---

## C.11 — Slide 12 · Trajectoire d'industrialisation

### Q11.1 — Coût opérationnel · c'est viable en production ?

Très confortablement. Environ 0,002 € par requête en configuration Azure (vectorisation `ada-002` + génération GPT-3.5). Le *benchmark* exploratoire complet — 864 configurations de retrieval, 5 configurations de génération, 1 campagne de stabilité, évaluation RAGAS — a coûté moins de 15 € en appels API. Même avec un modèle plus récent (GPT-4o, environ 5-10x plus cher que GPT-3.5 au token), on resterait sous les 0,02 € par requête.

Le facteur limitant n'est pas le coût financier, c'est le temps machine pour les modèles locaux (36 secondes par question sur Mistral-7B, non viable en temps réel) et la latence en rafale (saturation des quotas Azure quand on enchaîne 50 questions en *benchmark*).

### Q11.2 — AI Act · vous êtes prêts ?

En cours de qualification. ScribBERT relève potentiellement de la catégorie « haut risque » au sens de l'annexe III du règlement, dès lors qu'il contribue à la gestion des risques pour la sécurité des travailleurs. Si cette classification est confirmée, les obligations principales sont : un système de gestion des risques documenté, une documentation technique détaillée, la transparence envers les utilisateurs, le contrôle humain, et un niveau de robustesse et d'exactitude documenté.

Le protocole d'évaluation développé dans ce mémoire contribue directement à plusieurs de ces exigences : la mesure de fiabilité (cinq dimensions), la traçabilité des sources, la documentation des choix techniques, le versioning du jeu de test et des résultats. C'est un des arguments opérationnels du cadre : il n'a pas été conçu pour l'AI Act, mais il en remplit les prérequis.

### Q11.3 — Qui est responsable si une décision de prévention s'appuie sur une réponse erronée ?

Juridiquement, l'employeur reste responsable de la sécurité de ses salariés, quelle que soit la technologie utilisée. ScribBERT est un outil d'aide, pas un substitut au jugement humain. L'avertissement permanent le rappelle.

Mais la question est plus nuancée dans la pratique. En tant que développeur interne du POC, Bouygues TP — puis Bouygues Construction après industrialisation — doit pouvoir documenter ses choix, ses tests, et le niveau de fiabilité atteint. C'est exactement le rôle du protocole d'évaluation. Si un jour un audit ou un incident demande de justifier la qualité du système, les résultats documentés (750 configurations testées, scores de *faithfulness*, campagne de stabilité, analyse d'erreurs typologique) constituent un dossier solide.

### Q11.4 — Le projet est validé pour l'industrialisation. Concrètement, c'est quoi la suite ?

L'industrialisation va être portée par Bouygues Construction (niveau groupe, pas filiale). Concrètement, ça veut dire : extension du corpus aux référentiels de toutes les filiales (pas seulement BYTP), intégration des réglementations internationales, passage à un LLM de production (GPT-4o ou équivalent, *benchmark* dédié à venir), mise en place d'une gouvernance conforme à l'AI Act (versioning, *audit trail*, tests automatisés en CI/CD avant chaque déploiement), et déploiement à un public utilisateur beaucoup plus large. Le cadre d'évaluation de ce mémoire va servir directement à piloter cette montée en charge : chaque nouvelle brique sera validée sur le protocole cinq dimensions avant mise en production.

### Q11.5 — Comment gérez-vous les tableaux et les schémas dans les PDF ?

Honnêtement, pour l'instant, mal. La version POC linéarise les tableaux en texte brut, ce qui détruit leur structure, et ignore les schémas. C'est la troisième priorité dans la trajectoire d'industrialisation, après l'hybridation et le reranking.

La piste étudiée est une chaîne image-to-text : un modèle multimodal (VLM) génère une description textuelle de chaque image ou tableau, conserve le lien vers l'image originale, et injecte le résultat comme un chunk enrichi. Les matrices de risques et les logigrammes décisionnels présents dans les référentiels contiennent une information de haute valeur santé-sécurité qui est actuellement perdue, et c'est un vrai manque.

---

## C.12 — Slide 13 · Limites et perspectives

### Q12.1 — 50 questions, c'est suffisant ?

Pour une phase exploratoire, oui. Pour des conclusions statistiquement décisives, non. Je le dis explicitement dans les limites : l'écart entre configurations doit être lu comme une tendance, pas comme un verdict. Avec 50 questions stratifiées, on peut identifier des effets de taille large (les modèles généralistes anglais décrochent clairement) et des interactions (le chunking optimal dépend du modèle), mais on ne peut pas trancher sur des écarts de 1 à 2 % de MRR.

L'objectif court terme est de passer à 150-300 questions, en impliquant directement des experts P2S dans l'annotation, et en augmentant la part anglophone (9/50 actuellement, ce qui est trop peu pour conclure sur le multilinguisme).

### Q12.2 — Les questions sont annotées par une seule personne (vous). Ça ne pose pas un problème de biais ?

Si, et c'est assumé dans les limites. L'annotation par un seul annotateur introduit un biais de subjectivité sur les réponses de référence et sur les jugements de pertinence des passages. L'idéal serait au moins deux annotateurs indépendants avec mesure de l'accord inter-juges (Kappa de Cohen ≥ 0,7). C'est prévu dans la trajectoire d'industrialisation, avec des experts P2S métier comme annotateurs.

Cela dit, la plupart des questions sont factuelles ou procédurales, et les réponses de référence sont directement extraites des référentiels, ce qui réduit la marge d'interprétation. Le biais est plus problématique sur les questions justificatives ou conditionnelles, où la « bonne réponse » est moins univoque.

### Q12.3 — Le corpus est bilingue FR/EN. Est-ce que le système ne risque pas de répondre en anglais à une question en français ?

Non, le LLM répond systématiquement dans la langue de la question — c'est contrôlé par la consigne de langue dans le *prompt* (cf. Ch. 7.7 du mémoire). Le retrieval, en revanche, est cross-lingue : une question en français peut remonter des chunks en anglais, et inversement. C'est voulu, parce que la documentation client est majoritairement en anglais et il ne faut pas la rater.

Le cas limite observé, c'est l'asymétrie de longueur : un document anglais très court (un *Safety Alert* d'une page) peut être mal apparié avec une requête française plus longue, non pas à cause de la langue mais parce que le vecteur du chunk court est dominé par quelques tokens spécialisés et s'éloigne dans l'espace vectoriel. C'est un biais structurel identifié, pas un biais linguistique au sens strict.

### Q12.4 — GraphRAG, RAG multimodal, agentic RAG — pourquoi ne pas les avoir déjà testés ?

Question de priorisation. Le POC devait d'abord démontrer que l'architecture de base fonctionne et que le protocole d'évaluation tient. Les variantes architecturales augmentent la surface expérimentale et compliquent le diagnostic — c'est plus utile une fois qu'on a un système de référence stable et un jeu de test dimensionné. La trajectoire d'industrialisation prévoit ces explorations moyen terme, mais le pré-requis est l'extension du jeu de test à 200+ questions pour pouvoir mesurer un vrai gain.

Le RAG multimodal est probablement le plus prioritaire des trois, à cause du manque actuel sur les tableaux et les schémas (Q11.5). *GraphRAG* et *agentic RAG* sont des paris de plus long terme.

### Q12.5 — Vous parlez de *fine-tuning* d'embedding sur le corpus. Comment vous y prendriez-vous concrètement ?

Apprentissage contrastif sur les paires question–passage annotées du jeu de test. Concrètement : pour chaque question annotée, on a une paire positive (le chunk contenant la réponse) et on génère des négatifs difficiles (*hard negatives*) en prenant les chunks thématiquement proches mais qui ne répondent pas à la question — typiquement les chunks qui remontent aujourd'hui dans le *top-k* mais ne sont pas les bons. On entraîne un modèle de type SBERT à rapprocher la question du positif et l'éloigner des négatifs. Le gain attendu est surtout sur les cas où le vocabulaire métier BTP diverge du vocabulaire d'entraînement des modèles généralistes. C'est une piste chiffrable et rapide à tester dès qu'on aura 200 questions annotées.

---

## C.13 — Slide 14 · Conclusion

### Q13.1 — Quelle est votre contribution personnelle vs ce qui existait déjà ?

Les outils existaient (LangChain, ChromaDB, RAGAS, sentence-transformers). L'architecture RAG n'est pas nouvelle. Ma contribution est à trois niveaux.

Premier niveau, méthodologique : la définition opératoire de la fiabilité en cinq dimensions mesurables, le protocole de stabilité dédié (absent des *frameworks* existants), et le principe de diagnostic croisé (dimension × étage → action correctrice). Ce n'est pas un assemblage de métriques connues, c'est un cadre structuré qui dit comment les articuler.

Deuxième niveau, applicatif : ScribBERT est un système complet — extraction, chunking, vectorisation, retrieval, génération, interface, déploiement — développé de bout en bout, avec une UI React codée à la main, une API FastAPI, et une fonctionnalité de *gap analysis* que je n'ai pas trouvée dans les outils existants.

Troisième niveau, expérimental : le *benchmark* de 750 configurations sur un corpus santé-sécurité réel, avec un jeu de test stratifié construit manuellement. C'est un volume d'expérimentation significatif qui n'existait pas avant ce travail.

### Q13.2 — Si un concurrent déployait un RAG santé-sécurité demain, est-ce qu'il pourrait utiliser votre protocole ?

Oui, et c'est voulu. Le cadre méthodologique — les cinq dimensions, le principe de décomposition, le protocole de stabilité, l'approche hybride d'évaluation — est publié dans ce mémoire et n'est pas spécifique à ScribBERT. Évidemment, le jeu de test, le corpus, et les choix d'implémentation sont propres à Bouygues TP. Mais un concurrent pourrait parfaitement instancier le même cadre sur son propre corpus, avec son propre jeu de test, et bénéficier du même pouvoir diagnostique. C'est un des apports du mémoire que je revendique : la transférabilité du cadre.

### Q13.3 — Avec les progrès rapides des LLMs, votre cadre ne sera-t-il pas obsolète dans deux ans ?

Le cadre est conçu pour être indépendant du modèle. Les cinq dimensions (pertinence retrieval, fidélité, pertinence réponse, stabilité, traçabilité) restent pertinentes quel que soit le LLM utilisé — un GPT-6 ou un Claude 5 hallucineront peut-être moins, mais la fidélité restera à mesurer. La stabilité restera un enjeu tant que la génération sera stochastique. La traçabilité restera un prérequis réglementaire.

Ce qui évoluera, ce sont les instruments de mesure : les [*LLM-as-judge*](memoire_complet.md#gloss-llm-as-judge) deviendront plus fiables, les métriques automatiques couvriront peut-être la préservation des modalités, et de nouveaux *benchmarks* spécialisés apparaîtront. Le cadre est prévu pour intégrer ces évolutions sans changer sa structure.

---

# PARTIE D — QUESTIONS TRANSVERSES ET DE REPLI

Questions qui ne se rattachent pas à une slide unique mais qui peuvent surgir à tout moment. Regroupées ici pour ne pas alourdir la partie C.

## D.1 — Garanties utilisateur et acceptabilité

### QD.1 — Comment garantir que l'utilisateur ne prendra pas la réponse pour argent comptant ?

Quatre garde-fous. Premièrement, un avertissement permanent affiché en bas de l'écran, rappelant que la responsabilité de vérification incombe à l'utilisateur. Deuxièmement, les citations systématiques et cliquables, qui renvoient au PDF source : l'interface est conçue pour que la source soit plus visible que la réponse synthétisée. Troisièmement, le refus contrôlé : quand aucun chunk pertinent n'est trouvé, le système répond « Cette information ne figure pas dans les référentiels consultés » plutôt que d'improviser. Quatrièmement, la supervision humaine : une revue périodique des journaux par l'équipe P2S, avec procédure d'escalade pour signaler une réponse erronée.

Au-delà de ces mesures techniques, un axe de travail tout aussi important est la formation des utilisateurs : bonnes pratiques de formulation, lecture critique des réponses, vérification systématique des sources. L'outil ne peut fonctionner correctement que si l'utilisateur comprend ce qu'il peut attendre — et ce qu'il ne doit pas en attendre.

### QD.2 — ScribBERT pourrait-il remplacer un préventeur ?

Non, et ce n'est pas son objectif. ScribBERT est un amplificateur, pas un substitut. Il fait gagner du temps sur la phase de recherche documentaire — passer de 2 min 30 à quelques secondes pour trouver l'information — mais le jugement, l'interprétation du contexte chantier, l'adaptation de la règle à la situation concrète, restent du ressort du professionnel. Le système ne connaît pas le chantier, ne voit pas les conditions réelles, ne porte pas de jugement sur les risques. Il cite des référentiels.

L'avertissement permanent et le design de l'interface sont construits pour maintenir cette frontière. Si un jour un utilisateur cesse de vérifier les sources parce qu'il « fait confiance au système », c'est un signal d'alerte, pas un signe de succès.

### QD.3 — Votre système a-t-il déjà produit une réponse dangereuse ?

Pas de réponse « dangereuse » au sens fort — aucune instruction qui aurait pu mettre quelqu'un en danger si elle avait été suivie. En revanche, pendant la phase de prototypage (avant la formalisation du protocole), j'ai observé des réponses incomplètes — par exemple une procédure d'espace confiné citée correctement mais sans l'exception qui s'y rattache — et des réponses hors-périmètre quand le *prompt* était trop permissif (la première version du *prompt* système de ScribBERT, littéralement, pouvait sortir des recettes de cookies). C'est exactement ce qui a motivé le durcissement du *prompt* et la formalisation du protocole.

Sur la configuration de référence testée dans le mémoire, les 4 questions adversariales (dont une demandant comment court-circuiter un verrouillage de sécurité) ont toutes été correctement refusées.

## D.2 — Parcours projet et posture

### QD.4 — Quel a été le moment le plus difficile du projet ?

Le tâtonnement initial sur l'évaluation. Pendant les premières semaines de la phase exploratoire, j'essayais de juger la qualité du système en posant quelques questions et en regardant si les réponses « avaient l'air bonnes ». C'est exactement ce que je critique dans le mémoire, mais c'est par là que je suis passé. Le déclic est venu des échanges avec Julien Larseneur, qui ne jurait que par les métriques et qui m'a poussé à comprendre pourquoi un seul score ne suffisait pas. La formalisation du cadre à cinq dimensions est directement issue de cette frustration initiale.

### QD.5 — Si vous aviez 6 mois de plus, que feriez-vous en priorité ?

Trois choses. D'abord, passer le jeu de test à 200 questions avec annotation multi-annotateurs, pour valider statistiquement les tendances observées. Ensuite, implémenter et *benchmarker* l'hybridation BM25 + dense avec reranking [*cross-encoder*](memoire_complet.md#gloss-cross-encoder), qui est la priorité numéro un identifiée par les résultats. Enfin, lancer un *fine-tuning* contrastif d'un modèle de vectorisation sur les paires question-passage santé-sécurité du jeu de test, pour mesurer le gain d'un modèle de vectorisation spécialisé vs un modèle généraliste.

### QD.6 — Quelle est la limite dont vous êtes le plus conscient et que vous n'avez pas encore résolue ?

L'écart entre stabilité inter-runs (0,94) et robustesse aux paraphrases (0,77). C'est le résultat qui m'a le plus surpris et qui a le plus de conséquences opérationnelles : ça veut dire que deux utilisateurs qui posent la même question avec des mots différents peuvent avoir des réponses sensiblement différentes. C'est mesuré, c'est documenté, une piste de correction est identifiée (normalisation de requête en amont), mais ce n'est pas encore corrigé. Tant que ce n'est pas fait, la reproductibilité perçue par l'utilisateur reste inférieure à ce que la reproductibilité technique laisse espérer.
