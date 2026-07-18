# Plan de soutenance — Proposition B « Par dimensions »

**Format** : 14 slides, 20 min de présentation, angle multidimensionnel comme fil rouge.

**Cible orale** : ≈ 140 mots/minute en français soutenu-parlé. Les textes ci-dessous sont calibrés en conséquence.

**Recommandations transverses** :

- Slide de titre sobre, charte visuelle unique sur toute la présentation (bleu marine Bouygues + un accent orange, pas plus).
- Toutes les figures citées ci-dessous sont déjà générées et présentes dans `figures/` du dépôt.
- Prévoir une démo courte (vidéo ou capture animée en boucle) sur la slide 10. Éviter la démo live en réseau : risque trop élevé sur 20 min.
- Numérotation des slides visible en pied de page, avec le nom des 5 dimensions comme rappel visuel sur les slides 6 à 10.
- Les slides 4 et 5 sont pédagogiques : elles introduisent le RAG pour un jury qui n'a pas nécessairement lu le mémoire. Privilégier les schémas clairs sur le texte.

---

## Slide 1 — Titre & contexte (1 min)

**Contenu visuel** :

- Titre : « Évaluer la cohérence et la fiabilité d'un système RAG en contexte industriel critique »
- Sous-titre : « Le cas ScribBERT — Département Prévention Santé-Sécurité, Bouygues Travaux Publics »
- Nom, cursus (Mastère 2 IA, École Hexagone), date, tuteurs (Flavien Martin, Julien Larseneur)
- Deux logos discrets : École Hexagone + Bouygues Travaux Publics

**Ce que je dis** :

Bonjour à toutes et à tous. Je vous présente aujourd'hui mon mémoire de fin d'études, réalisé dans le cadre de mon alternance au département Prévention Santé-Sécurité de Bouygues Travaux Publics. Le sujet, c'est ScribBERT : un assistant conversationnel RAG que j'ai développé pour permettre aux collaborateurs d'interroger en langage naturel les référentiels santé-sécurité internes du groupe. Mais la vraie question, celle qui structure tout ce travail, n'est pas « comment construire un RAG », c'est plutôt « comment prouver qu'il est fiable ». Vingt minutes, cinq dimensions d'évaluation, un cas concret. On y va.

**Transition** : « Commençons par le problème auquel ScribBERT répond. »

---

## Slide 2 — Le problème à résoudre (1 min)

**Contenu visuel** :

- Trois chiffres en gros à gauche : **130 documents PDF**, **2 min 30 par recherche**, **≈ 40% FR / 60% EN**
- À droite : capture d'écran d'un SharePoint labyrinthique (floutée) OU icône « chantier » + « document » + « décision »
- Bandeau bas : « ScribBERT n'est pas un dispositif de sécurité. C'est un appui à la décision. »

**Ce que je dis** :

Le département P2S produit plus de 130 documents de référence — procédures, standards, guides — sur des sujets critiques comme le travail en hauteur ou les espaces confinés. Nos statistiques internes montrent qu'un collaborateur y passe en moyenne 2 minutes 30 par recherche, jusqu'à 10 minutes sur les cas complexes. Et ces recherches précèdent souvent des décisions opérationnelles.

Un point à poser d'entrée : ScribBERT n'est pas un dispositif de sécurité au sens technique. Il ne pilote pas un capteur, il ne déclenche pas d'arrêt d'urgence. C'est un outil documentaire qui alimente des décisions de prévention. Et c'est précisément ce qui fait l'enjeu : une réponse plausible mais fausse — une obligation restituée comme une simple recommandation, par exemple — peut orienter à tort un arbitrage. Ce n'est pas grave qu'un outil se trompe si on le sait ; c'est grave si on ne peut pas le mesurer.

**Transition** : « D'où la question centrale de mon travail. »

---

## Slide 3 — La thèse défendue (1 min)

**Contenu visuel** — slide manifeste, très épurée :

- Une seule phrase en grand, centrée :
  > **« La fiabilité d'un RAG n'est pas un score. C'est un faisceau de cinq dimensions qu'il faut mesurer séparément pour pouvoir diagnostiquer. »**
- En bas, cinq icônes en ligne (pertinence, fidélité, réponse, stabilité, traçabilité) déjà présentes comme teaser

**Ce que je dis** :

Ma problématique, c'est : comment évaluer la cohérence et la fiabilité d'un système RAG en contexte industriel critique ? Et la thèse que je défends dans ce mémoire tient en une phrase que vous voyez à l'écran : la fiabilité d'un RAG n'est pas un score global qu'on additionne à la fin, c'est un faisceau de cinq dimensions distinctes, qu'il faut mesurer séparément si on veut être capable de diagnostiquer où la chaîne échoue. Je vais vous montrer ces cinq dimensions, comment je les ai instrumentées, et ce qu'elles disent concrètement sur ScribBERT.

**Transition** : « Mais d'abord, 90 secondes pour poser ce qu'est un RAG et pourquoi son évaluation est plus délicate qu'il n'y paraît. »

---

## Slide 4 — Le RAG, en pratique (1,5 min)

**Contenu visuel** :

- Titre : « Le RAG, en pratique — combiner recherche et rédaction »
- Schéma central en 3 blocs horizontaux :
  1. **Question utilisateur**
  2. **[Recherche dans le corpus]** → passages pertinents retrouvés
  3. **[Rédaction par le LLM à partir des passages]** → réponse avec citations
- Contraste en bas de slide, en 2 encadrés côte à côte :
  - « **LLM seul** : peut inventer, pas de source »
  - « **Moteur de recherche classique** : trouve mais ne rédige pas »
- Bandeau bas : « Le RAG combine les deux : rédiger *à partir de* documents vérifiables. »

**Ce que je dis** :

Un mot rapide sur ce qu'est concrètement un RAG, parce que le terme est technique et je préfère m'assurer que tout le monde parte du même endroit. L'idée est en fait très intuitive.

Un modèle de langage seul, comme ChatGPT, peut produire un texte fluide sur à peu près n'importe quel sujet, mais il peut aussi inventer — c'est ce qu'on appelle une hallucination — et il ne cite pas ses sources. À l'inverse, un moteur de recherche classique vous trouve des documents mais ne rédige rien : à vous de les ouvrir, de les lire, de synthétiser.

Un RAG, c'est l'assemblage des deux. Pour reprendre une image que j'aime bien : c'est un modèle de langage à qui on impose de faire comme un bon préventeur — consulter la documentation avant de répondre. Concrètement, quand un utilisateur pose une question, le système commence par chercher dans le corpus documentaire les passages les plus pertinents, puis il les injecte dans le contexte du modèle de langage, et il lui demande de rédiger la réponse à partir de ces passages, avec les citations qui vont avec. On ancre la génération sur des documents vérifiables.

**Transition** : « Techniquement, cette chaîne se décompose en cinq étages — et c'est là que se cachent les vraies difficultés. »

---

## Slide 5 — Anatomie d'une chaîne RAG (1 min)

**Contenu visuel** :

- Titre : « Anatomie d'une chaîne RAG — les étages où l'erreur peut naître »
- Schéma horizontal en 5 étages : **Ingestion → Chunking → Vectorisation / Index → Retrieval → Génération**
- Sous chaque étage, un mini-icône rouge « ⚠ » avec un exemple d'erreur type (tableau perdu, règle coupée en deux, terme métier mal représenté, passage hors-contexte remonté, hallucination)
- Bandeau bas : « Chaque étage peut échouer indépendamment — et un score global les mélange. »

**Ce que je dis** :

Les cinq étages, en une phrase chacun. L'ingestion transforme les PDF en texte exploitable. Le chunking découpe ce texte en unités indexables. La vectorisation transforme chaque unité en un vecteur numérique qui capture son sens. La récupération retrouve, à chaque requête, les vecteurs les plus proches de la question. Et la génération assemble tout ça dans un prompt fourni au modèle de langage, qui rédige la réponse finale.

Le point clé, celui qui va justifier toute ma démarche d'évaluation, c'est que chaque étage a ses propres modes d'échec, souvent invisibles depuis la réponse finale. Un tableau perdu à l'ingestion, une règle coupée en deux au chunking, un passage thématiquement proche mais non applicable remonté au retrieval, une extrapolation à la génération. Un excellent score de récupération reste parfaitement compatible avec une réponse finale fausse. C'est ce qui rend nécessaire une évaluation décomposable, dimension par dimension.

**Transition** : « Première dimension, et la plus intuitive : la pertinence du retrieval. »

---

## Slide 6 — Dimension 1 : Pertinence du retrieval (2,5 min)

**Contenu visuel** :

- En-tête bandeau bleu : « **Dimension 1/5 — Pertinence du retrieval** »
- Sous-titre : « Le bon passage est-il dans le top-k ? »
- Métriques à gauche (en encart) : Recall@k, MRR, nDCG@k
- **Figure principale** : `figures/fig_8_2_heatmap_mrr_modele_chunking.png` (heatmap 16 modèles × 9 chunkings)
- Encart chiffré en bas à droite : **864 configurations testées · 750 exploitables · 50 questions annotées**

**Ce que je dis** :

Une précaution de vocabulaire avant d'aller plus loin. Ces étages que vous venez de voir, c'est *où* l'erreur peut naître — c'est la structure de la chaîne. Les cinq dimensions que je vais présenter maintenant, c'est *ce qu'on mesure* sur le système. Deux grilles différentes, qui se croisent — et c'est précisément ce croisement qui va rendre l'analyse d'erreurs actionnable, en fin de présentation.

Première dimension, donc : est-ce que le bon passage est bien dans le top-k renvoyé par la récupération ? On dispose ici de métriques classiques héritées de la recherche d'information — Recall@k, MRR, nDCG — que j'ai adaptées à un jeu de test que j'ai construit sur mesure : 50 questions annotées manuellement, stratifiées par type, difficulté, criticité métier et langue.

Sur ScribBERT, j'ai lancé un plan factoriel complet : 16 modèles de vectorisation croisés avec 9 stratégies de chunking et 6 variantes de récupération. Ça fait 864 configurations, dont 750 exploitables. Ce que vous voyez à l'écran, c'est la heatmap des scores MRR moyens : chaque case est une combinaison modèle-chunking.

Deux enseignements. D'abord, les huit meilleurs modèles se tiennent dans une bande de plus ou moins 3 centièmes de MRR : sur ce corpus, il n'y a pas de modèle miracle. Ada-002 d'OpenAI, embed-3-large, Nomic, Qwen3, Solon, E5, Jina : ils sont tous à égalité statistique. Ce qui veut dire que le choix se fait sur les critères pratiques — latence, coût, souveraineté — pas sur la MRR seule.

Ensuite, deuxième enseignement plus contre-intuitif : le chunking optimal dépend du modèle. Les gros modèles avec fenêtre de contexte large préfèrent des chunks de 1024 tokens. Les modèles francophones spécialisés préfèrent le chunking par paragraphe. Les modèles compacts sont pénalisés par les chunks longs. Autrement dit, on ne peut pas recommander « le meilleur chunking » dans l'abstrait — il faut le tester conjointement avec le modèle. C'est un vrai résultat, et c'est ce qui a justifié de garder tout le plan factoriel plutôt que de figer une stratégie a priori.

**Transition** : « Un bon retrieval est nécessaire, mais pas suffisant. Deuxième dimension : la fidélité aux sources. »

---

## Slide 7 — Dimension 2 : Fidélité aux sources (2,5 min)

**Contenu visuel** :

- En-tête bandeau : « **Dimension 2/5 — Fidélité aux sources (faithfulness)** »
- Sous-titre : « Ce que dit la réponse est-il réellement supporté par les passages ? »
- **Figure principale** : `figures/fig_8_4_radar_ragas_5_configs.png` (radar RAGAS 5 configs)
- Encart en bas à gauche : les 3 sous-métriques RAGAS mobilisées (Faithfulness, Context Precision, Answer Relevancy)
- Encart en bas à droite : « **Hybrid-k5 + GPT-3.5 : meilleur profil sur les 4 axes** »

**Ce que je dis** :

Deuxième dimension, et sans doute la plus critique pour un usage santé-sécurité : la fidélité aux sources. La question n'est plus « le bon passage est-il dans le contexte » mais « la réponse générée reste-t-elle vraiment fidèle à ce que disent ces passages, ou est-ce que le modèle a rajouté, extrapolé, inversé une modalité ? »

Pour la mesurer automatiquement, j'ai utilisé le framework RAGAS, qui décompose la réponse en propositions atomiques et vérifie chacune contre le contexte à l'aide d'un LLM-juge. Sur cinq configurations sélectionnées — trois côté Azure avec GPT-3.5, deux côté Mistral-7B local — vous voyez le profil complet à l'écran.

Trois observations. Premièrement, la configuration hybride retrieval — dense plus BM25 avec fusion RRF — domine sur les quatre axes simultanément : 0,77 de faithfulness, meilleure answer relevancy, meilleure context precision. Ça confirme, côté génération, ce qu'on avait déjà vu côté retrieval : une récupération plus précise se traduit par une génération plus fidèle. Deuxièmement, GPT-3.5 plafonne à environ 0,77 de faithfulness. Pour aller vers 0,90, cible des frameworks matures, il faudra passer à un modèle plus récent — GPT-4o, Claude Sonnet, Mistral Large — et durcir la consigne de citation.

Troisième point, plus délicat : Mistral-7B en local. En performance pure, il est en retrait — 0,68 de faithfulness dans sa meilleure configuration. Mais surtout, en latence, on est à 36 secondes par question contre 5 secondes pour Azure. Pas viable pour du temps réel. Il reste néanmoins pertinent comme voie de repli souverain, pour les chantiers en environnement isolé — nucléaire, militaire — où on ne peut pas sortir d'Internet.

**Transition** : « Troisième dimension, qui capture ce qu'aucune des deux premières ne voit : la pertinence de la réponse elle-même. »

---

## Slide 8 — Dimension 3 : Pertinence de la réponse (1,5 min)

**Contenu visuel** :

- En-tête bandeau : « **Dimension 3/5 — Pertinence & complétude de la réponse** »
- Sous-titre : « La réponse répond-elle à la question posée, ni plus ni moins ? »
- **Figure principale** : `figures/fig_9_2_ragas_par_type_question.png` (RAGAS par type de question)
- Encart bas : capture d'écran de la fonctionnalité **gap analysis** (comparaison entre deux corpus)

**Ce que je dis** :

Troisième dimension : est-ce que la réponse traite vraiment la question posée, avec la bonne complétude, sans dériver ? Une réponse peut être parfaitement fidèle à ses sources et complètement à côté de la question. On mesure ça avec l'answer relevancy de RAGAS, croisée avec la stratification par type de question.

Le graphe à l'écran montre les scores RAGAS par type. Les questions factuelles et procédurales performent très bien. Deux catégories décrochent : les conditionnelles — les fameuses « que faire si… » — parce que le système attrape la règle générale mais rate parfois l'exception ; et les comparatives — « quelle différence entre A et B » — parce que le top-5 se fait souvent dominer par l'entité la plus représentée dans le corpus.

C'est justement pour ce type de questions comparatives que j'ai développé une fonctionnalité de **gap analysis** dans ScribBERT, que vous voyez en bas à droite : l'utilisateur sélectionne deux sous-ensembles de documents, la même requête est exécutée sur chacun, et les écarts sont visibles directement. Au-delà du cas comparatif, cette fonctionnalité a aussi vocation à accélérer l'ouverture de chantiers dans un nouveau pays, en identifiant les écarts entre nos référentiels internes et les réglementations locales applicables.

**Transition** : « Quatrième dimension, celle qui est le plus souvent oubliée par les frameworks existants : la stabilité. »

---

## Slide 9 — Dimension 4 : Stabilité (2 min)

**Contenu visuel** :

- En-tête bandeau : « **Dimension 4/5 — Stabilité & répétabilité** »
- Sous-titre : « Si l'utilisateur reformule, la réponse reste-t-elle cohérente ? »
- **Figure principale** : `figures/fig_8_5_boxplot_stabilite.png` (boxplot 4 indicateurs)
- Encart chiffré à droite (grands chiffres) : **0,94 stabilité inter-runs** vs **0,77 robustesse aux paraphrases**
- Bandeau bas : « Le vrai point faible, ce n'est pas le hasard du modèle — c'est la manière dont l'utilisateur formule sa question. »

**Ce que je dis** :

Quatrième dimension : la stabilité. La plupart des frameworks d'évaluation la traitent comme un effet de bord — on lance une exécution, on prend le score. Mais un système qui donne une bonne réponse un jour et une réponse médiocre le lendemain sur la même question est bon en moyenne mais pas fiable. Pour un usage santé-sécurité, la variabilité fait partie intégrante de la fiabilité perçue.

J'ai construit un protocole dédié : pour chaque question, dix exécutions à seed constante, plus les paraphrases annotées dans le jeu de test. Quatre indicateurs mesurés : stabilité du retrieval, stabilité des citations, stabilité sémantique de la réponse, et robustesse aux paraphrases.

Le résultat central est à droite en gros : 0,94 de stabilité inter-runs, mais seulement 0,77 de robustesse aux paraphrases. Dix-sept points d'écart. Autrement dit : ScribBERT est stable quand on lui repose exactement la même question, mais dès que l'utilisateur reformule — ce qui est le comportement naturel — la réponse peut sensiblement varier. Ce n'est pas forcément faux, mais ce n'est pas invariant. C'est l'indicateur prioritaire à améliorer pour la production, probablement via une étape de normalisation de requête en amont du retrieval. Et c'est un résultat qu'aucune évaluation ponctuelle n'aurait pu remonter.

**Transition** : « Cinquième et dernière dimension, celle qui fait le lien avec les enjeux de conformité : la traçabilité. »

---

## Slide 10 — Dimension 5 : Traçabilité (1 min)

**Contenu visuel** :

- En-tête bandeau : « **Dimension 5/5 — Traçabilité & auditabilité** »
- Sous-titre : « Peut-on vérifier, a posteriori, l'origine de chaque affirmation ? »
- **Zone principale (gauche + centre)** : capture d'écran annotée de l'interface ScribBERT montrant une réponse avec citations cliquables (16:9, PNG, à insérer manuellement : `figures/fig_traceability_screenshot.png`)
- **Encart bas (trois points compacts, une ligne chacun)** :
  - Chaque citation → identifiant chunk (docID + page) journalisé
  - Clic ouvre le PDF à la page source
  - Audit trail horodaté + hash du chunk (preuve immuable)
- Petit encart bas-droit : mention « Prérequis conformité AI Act »

**Ce que je dis** :

Cinquième dimension : la traçabilité. Une réponse ne suffit pas ; il faut pouvoir prouver d'où elle vient. Dans un contexte santé-sécurité, et à plus forte raison avec l'entrée en application progressive de l'AI Act européen, c'est un prérequis non négociable.

Concrètement, dans ScribBERT — vous voyez à l'écran une démonstration — chaque affirmation est rattachée à un identifiant de chunk journalisé, lui-même relié au document d'origine et à la page. L'utilisateur clique sur la citation, le PDF s'ouvre à la bonne page. Rien de spectaculaire techniquement, mais c'est cette chaîne complète qui rend la réponse auditable, et c'est ce qui fait le plus la différence dans les retours utilisateurs qu'on a collectés pendant la phase de test : la présence systématique des sources vérifiables est le facteur numéro un d'acceptabilité.

Cette dimension n'est pas capturée par les métriques quantitatives : on la mesure par la complétude et la correction des citations, et surtout par un design volontariste — pas de réponse sans source, refus contrôlé si aucun chunk pertinent, avertissement permanent rappelant que l'utilisateur reste responsable de la vérification.

**Transition** : « Ces cinq dimensions, prises ensemble, permettent quelque chose que les scores globaux ne permettent pas : diagnostiquer où la chaîne échoue. »

---

## Slide 11 — Lire les échecs à travers les 5 dimensions (1,5 min)

**Contenu visuel** :

- Titre : « Analyse d'erreurs — 8 catégories, une dimension mise en cause »
- **Figure principale** : `figures/fig_9_1_distribution_categories_erreur.png` (distribution des catégories d'erreur)
- Tableau récapitulatif compact à droite : chaque catégorie d'erreur → dimension mise en cause → action correctrice type
  - Échec retrieval → Dim 1 → reranking / query rewriting
  - Bruit retrieval → Dim 1 → cross-encoder
  - Hallucination → Dim 2 → prompt + refus contrôlé
  - Omission exception → Dim 3 → parent-document retrieval
  - Contradiction silencieuse → Dim 2 → garde-fou applicatif
  - Refus à tort / hors-périmètre → Dim 5 → calibration seuil

**Ce que je dis** :

C'est ici que le cadre à cinq dimensions devient vraiment utile. Sur la configuration de référence, j'ai classé chaque erreur du jeu de test dans une typologie en huit catégories, à l'aide de seuils simples sur les scores RAGAS. Le résultat, c'est le graphe à l'écran.

Le bénéfice n'est pas seulement descriptif, il est actionnable : chaque catégorie d'erreur remonte à une dimension défaillante, et donc à une action correctrice précise. Un échec de retrieval, c'est la dimension 1 : la réponse est reranking. Une contradiction silencieuse — cas typique observé sur Mistral local pour une question hors-corpus — c'est la dimension 2 : la réponse est un garde-fou applicatif. Un refus à tort, c'est la dimension 5 : la réponse est une calibration de seuil.

Sur ScribBERT, ce diagnostic donne des priorités très claires : environ un quart des questions sont concernées par un problème de retrieval, ce qui fait de l'hybridation et du reranking les leviers numéro un pour la prochaine itération.

**Transition** : « Concrètement, qu'est-ce que ce diagnostic change pour ScribBERT ? »

---

## Slide 12 — Ce que ça change pour ScribBERT (1,5 min)

**Contenu visuel** :

- Titre : « De l'évaluation à la trajectoire d'industrialisation »
- Timeline horizontale à trois jalons :
  - **POC (2024-2025)** : dense pur, ada-002, GPT-3.5, 130 docs, département P2S BYTP
  - **Configuration cible (2026)** : hybrid retrieval, cross-encoder rerank, image-to-text tableaux, LLM récent
  - **Industrialisation groupe (2026-2027)** : extension aux filiales Bouygues Construction, multilinguisme étendu, gouvernance AI Act
- Encart en bas, très visible : « **Passage en industrialisation groupe validé — juillet 2026** »

**Ce que je dis** :

Le protocole d'évaluation ne sert pas juste à noter un système : il sert à décider quoi améliorer et dans quel ordre. Sur ScribBERT, la trajectoire est celle que vous voyez à l'écran.

Le POC actuel — dense pur, ada-002, GPT-3.5 — tourne en production interne au département P2S. Les priorités court terme identifiées par le diagnostic sont l'hybridation retrieval, l'ajout d'un reranker cross-encoder, et une chaîne image-to-text pour les tableaux et schémas, qui sont aujourd'hui perdus lors de l'ingestion. Chacune de ces briques est justifiée par un résultat précis du benchmark, pas par une intuition.

L'annonce que je peux faire aujourd'hui, et qui est pour moi la meilleure validation possible de ce travail : le projet vient d'être validé pour un passage en industrialisation à l'échelle du groupe Bouygues Construction. Ça veut dire une extension aux filiales, l'intégration des référentiels clients internationaux, un multilinguisme élargi, et surtout la mise en place d'une gouvernance conforme aux exigences AI Act. Le cadre d'évaluation développé dans ce mémoire va être directement réutilisé pour piloter cette montée en charge.

**Transition** : « Comme dans tout travail exploratoire, il reste des limites et des chantiers. »

---

## Slide 13 — Limites & perspectives (1 min)

**Contenu visuel** :

- Titre : « Limites assumées & perspectives »
- Deux colonnes :
  - **Limites** : jeu de test 50 questions (vs 150-300 recommandé), stabilité mesurée sur 1 seule configuration, corpus siège uniquement, validation humaine sur sous-échantillon
  - **Perspectives** : fine-tuning d'embedding sur corpus santé-sécurité, GraphRAG pour les questions multi-saut, RAG multimodal (schémas, photos chantier), agentic RAG pour la décomposition de questions complexes
- Bandeau bas : « Cadre transférable : juridique, RH, maintenance industrielle. »

**Ce que je dis** :

Je veux être honnête sur ce que ce travail ne fait pas. Le jeu de test est limité à 50 questions annotées — c'est cohérent pour une phase exploratoire, mais en-dessous des 150 à 300 questions qu'il faudrait pour des comparaisons statistiquement décisives. La campagne de stabilité n'a porté que sur une seule configuration ; il faudra la répliquer sur les meilleures variantes identifiées. Et la validation humaine reste ciblée : elle doit être élargie avant le passage en production.

Côté perspectives, quatre pistes ressortent : un fine-tuning d'embedding sur le corpus santé-sécurité pour combler l'absence de modèle spécialisé BTP, une variante GraphRAG pour les questions à raisonnement multi-saut, une extension multimodale pour intégrer les schémas et photos de chantier, et une architecture agentic pour décomposer automatiquement les questions complexes.

Un dernier point : le cadre méthodologique proposé ne dépend pas du corpus santé-sécurité. Il est réinstanciable sur d'autres domaines documentaires soumis à des exigences fortes — juridique, ressources humaines, maintenance industrielle. C'est un des apports que je revendique de ce travail.

**Transition** : « Pour conclure. »

---

## Slide 14 — Conclusion (30 s)

**Contenu visuel** — slide très épurée, retour à la thèse du début :

- Rappel de la phrase manifeste :
  > **« La fiabilité d'un RAG n'est pas un score. C'est un faisceau de cinq dimensions à mesurer, à gouverner, à éprouver. »**
- En bas : « Merci. Questions ? »
- Adresses / contacts si pertinent

**Ce que je dis** :

Je referme là où j'ai commencé. La fiabilité d'un système RAG en contexte critique n'est pas un score qu'on appose après coup, c'est une propriété systémique qu'il faut décomposer, instrumenter, éprouver et gouverner — au même titre que n'importe quel autre indicateur de performance industrielle. Ce mémoire aura cherché à en faire la démonstration sur un cas concret ; le passage à l'échelle groupe qui vient d'être validé en sera, je l'espère, la confirmation la plus utile.

Je vous remercie pour votre attention, et je suis à votre disposition pour vos questions.

---

## Récapitulatif temps

| Slide | Durée | Cumulé |
|-------|-------|--------|
| 1. Titre & contexte | 1'00 | 1'00 |
| 2. Le problème | 1'00 | 2'00 |
| 3. Thèse défendue | 1'00 | 3'00 |
| 4. Le RAG, en pratique | 1'30 | 4'30 |
| 5. Anatomie d'une chaîne RAG | 1'00 | 5'30 |
| 6. Dim 1 — Pertinence retrieval | 2'30 | 8'00 |
| 7. Dim 2 — Fidélité aux sources | 2'30 | 10'30 |
| 8. Dim 3 — Pertinence réponse | 1'30 | 12'00 |
| 9. Dim 4 — Stabilité | 2'00 | 14'00 |
| 10. Dim 5 — Traçabilité | 1'00 | 15'00 |
| 11. Analyse d'erreurs | 1'30 | 16'30 |
| 12. Trajectoire industrialisation | 1'30 | 18'00 |
| 13. Limites & perspectives | 1'00 | 19'00 |
| 14. Conclusion | 0'30 | 19'30 |
| **Marge / Questions** | ~0'30 | 20'00 |

---

## Anticipation des questions du jury

Petites notes de préparation, pas à mettre dans le PPT :

- **« Pourquoi RAG plutôt que fine-tuning ? »** → coût, traçabilité, mise à jour continue, absence de fine-tuning stable en santé-sécurité. Cf. Ch. 2.2.
- **« Pourquoi seulement 50 questions ? »** → phase exploratoire, budget expert P2S, écart assumé et documenté dans les limites.
- **« Comment garantir que l'utilisateur ne prendra pas la réponse pour argent comptant ? »** → avertissement permanent + traçabilité citations + refus contrôlé + supervision humaine (Ch. 10.3).
- **« AI Act, vous êtes prêts ? »** → classification en cours (probablement haut risque), protocole d'évaluation directement mobilisable pour la conformité (Ch. 10.1).
- **« La stabilité aux paraphrases à 0,77, c'est bloquant ? »** → non, c'est priorisé comme axe court terme (query rewriting), et déjà connu grâce au protocole. Point positif d'avoir mesuré plutôt que subi.
- **« Coût opérationnel ? »** → environ 0,002 €/requête sur Azure, benchmark exploratoire complet à moins de 15 €. Chiffres au § 8.6.
- **« Pourquoi ada-002 alors qu'il est ancien ? »** → à MRR égale (bande de ±0,03) avec les meilleurs, déjà déployé sur tenant Azure du groupe, latence acceptable, pas d'infra GPU à monter. Choix opérationnel documenté.

---

## Prompt Gamma — génération des slides

À copier-coller tel quel dans Gamma.app (mode « Créer avec l'IA »). Le prompt est en français puisque Gamma détecte la langue de sortie à partir de la langue d'entrée.

```text
Génère une présentation professionnelle de soutenance de mémoire de Master 2 en Intelligence Artificielle.

CONTEXTE : Défense d'un mémoire intitulé « Évaluer la cohérence et la fiabilité d'un système RAG en contexte industriel critique — le cas ScribBERT ». Le projet ScribBERT est un assistant conversationnel RAG (Retrieval-Augmented Generation) développé pour le département Prévention Santé-Sécurité de Bouygues Travaux Publics. Le jury attend une présentation structurée autour de cinq dimensions d'évaluation de la fiabilité d'un RAG : pertinence du retrieval, fidélité aux sources, pertinence de la réponse, stabilité, traçabilité. C'est le fil rouge central. Le jury n'a pas nécessairement lu le mémoire : deux slides pédagogiques d'introduction au RAG sont donc explicitement prévues (slides 4 et 5).

STYLE ET CHARTE VISUELLE :
- Ton professionnel, sobre, corporate. Registre technique et industriel, pas startup.
- Palette : bleu marine dominant (proche du bleu Bouygues), avec un accent orange discret pour les mises en avant. Fond blanc ou très légèrement gris.
- Typographie sans-serif moderne, lisible en salle.
- Pas d'emojis, pas d'illustrations décoratives inutiles. Icônes ligne minimalistes uniquement si utile.
- Pied de page discret sur chaque slide avec le numéro de slide et un rappel du titre du mémoire.
- Sur les slides 6 à 10, un bandeau supérieur bleu marine avec la mention « Dimension X/5 — [nom de la dimension] ».
- Prévoir explicitement des zones pour insérer des figures scientifiques (heatmaps, radars, boxplots, scatter plots) sur les slides indiquées ci-dessous.

STRUCTURE DEMANDÉE — 14 slides exactement, dans l'ordre :

1. TITRE : Slide de couverture. Titre : « Évaluer la cohérence et la fiabilité d'un système RAG en contexte industriel critique ». Sous-titre : « Le cas ScribBERT — Département Prévention Santé-Sécurité, Bouygues Travaux Publics ». Nom du candidat, Mastère 2 Intelligence Artificielle École Hexagone, tuteurs Flavien Martin et Julien Larseneur, date de soutenance. Deux logos discrets (École Hexagone, Bouygues Travaux Publics).

2. LE PROBLÈME À RÉSOUDRE : Trois chiffres en gros à gauche (130 documents PDF, 2 min 30 par recherche en moyenne, 40% FR / 60% EN). À droite, une illustration abstraite d'un labyrinthe documentaire ou d'une chaîne de décision. Bandeau bas très visible : « ScribBERT n'est pas un dispositif de sécurité. C'est un appui à la décision. »

3. THÈSE DÉFENDUE : Slide très épurée, quasi vide. Une seule citation centrée en très grande typographie : « La fiabilité d'un RAG n'est pas un score. C'est un faisceau de cinq dimensions qu'il faut mesurer séparément pour pouvoir diagnostiquer. » En bas, cinq petits blocs alignés horizontalement avec les noms des dimensions comme teaser (Pertinence retrieval, Fidélité, Pertinence réponse, Stabilité, Traçabilité).

4. LE RAG, EN PRATIQUE (slide pédagogique 1/2) : Titre : « Le RAG, en pratique — combiner recherche et rédaction ». Schéma central en 3 blocs horizontaux : Question utilisateur → [Recherche dans le corpus] → [Rédaction par le LLM à partir des passages] → Réponse avec citations. Contraste en bas de slide, en 2 encadrés côte à côte : « LLM seul : peut inventer, pas de source » et « Moteur de recherche classique : trouve mais ne rédige pas ». Bandeau bas : « Le RAG combine les deux : rédiger à partir de documents vérifiables. »

5. ANATOMIE D'UNE CHAÎNE RAG (slide pédagogique 2/2) : Titre : « Anatomie d'une chaîne RAG — les étages où l'erreur peut naître ». Schéma horizontal en 5 étages : Ingestion → Chunking → Vectorisation / Index → Retrieval → Génération. Sous chaque étage, un mini-encart rouge « ⚠ » avec un exemple d'erreur type (tableau perdu, règle coupée en deux, terme métier mal représenté, passage hors-contexte remonté, hallucination). Bandeau bas : « Chaque étage peut échouer indépendamment — et un score global les mélange. »

6. DIMENSION 1 — PERTINENCE DU RETRIEVAL : Bandeau supérieur bleu marine « Dimension 1/5 — Pertinence du retrieval ». Sous-titre : « Le bon passage est-il dans le top-k ? ». Zone dédiée à gauche pour un encart de métriques (Recall@k, MRR, nDCG@k). Zone principale à droite dédiée à une figure heatmap 16 modèles × 9 chunkings (à insérer manuellement). Encart chiffré en bas : « 864 configurations testées, 750 exploitables, 50 questions annotées ».

7. DIMENSION 2 — FIDÉLITÉ AUX SOURCES : Bandeau supérieur « Dimension 2/5 — Fidélité aux sources (faithfulness) ». Sous-titre : « Ce que dit la réponse est-il réellement supporté par les passages ? ». Zone principale pour un radar RAGAS à 4 axes comparant 5 configurations (à insérer manuellement). Encart bas-gauche listant les 3 sous-métriques RAGAS (Faithfulness, Context Precision, Answer Relevancy). Encart bas-droite très visible : « Hybrid-k5 + GPT-3.5 : meilleur profil sur les 4 axes ».

8. DIMENSION 3 — PERTINENCE DE LA RÉPONSE : Bandeau supérieur « Dimension 3/5 — Pertinence & complétude de la réponse ». Sous-titre : « La réponse répond-elle à la question posée, ni plus ni moins ? ». Zone principale pour un graphe RAGAS stratifié par type de question (à insérer manuellement). Encart bas dédié à une capture d'écran de la fonctionnalité « gap analysis » de ScribBERT.

9. DIMENSION 4 — STABILITÉ : Bandeau supérieur « Dimension 4/5 — Stabilité & répétabilité ». Sous-titre : « Si l'utilisateur reformule, la réponse reste-t-elle cohérente ? ». Zone principale pour un boxplot avec 4 indicateurs de stabilité (à insérer manuellement). Encart chiffré très visible à droite : « 0,94 stabilité inter-runs » vs « 0,77 robustesse aux paraphrases ». Bandeau bas : « Le vrai point faible, ce n'est pas le hasard du modèle — c'est la manière dont l'utilisateur formule sa question. »

10. DIMENSION 5 — TRAÇABILITÉ : Bandeau supérieur « Dimension 5/5 — Traçabilité & auditabilité ». Sous-titre : « Peut-on vérifier, a posteriori, l'origine de chaque affirmation ? ». Zone principale dédiée à une capture animée ou vidéo de l'interface ScribBERT (à insérer manuellement). Bandeau bas : « Chaque citation est un identifiant de chunk journalisé, lié au document et à la page. Audit trail complet. » Petit encart discret : « Prérequis conformité AI Act ».

11. ANALYSE D'ERREURS : Titre : « Analyse d'erreurs — 8 catégories, une dimension mise en cause ». Zone gauche pour un graphe de distribution des catégories d'erreur (à insérer manuellement). Zone droite : tableau compact à 3 colonnes (Catégorie d'erreur / Dimension mise en cause / Action correctrice type), 6 lignes minimum.

12. TRAJECTOIRE D'INDUSTRIALISATION : Titre : « De l'évaluation à la trajectoire d'industrialisation ». Timeline horizontale à 3 jalons : POC 2024-2025 (dense pur, ada-002, GPT-3.5, 130 docs) → Configuration cible 2026 (hybrid, reranking, image-to-text, LLM récent) → Industrialisation groupe 2026-2027 (filiales, multilinguisme, gouvernance AI Act). Encart bas très visible en accent orange : « Passage en industrialisation groupe validé — juillet 2026 ».

13. LIMITES & PERSPECTIVES : Titre : « Limites assumées & perspectives ». Deux colonnes équilibrées. Colonne gauche « Limites » (4 puces : jeu de test 50 questions, stabilité 1 configuration, corpus siège, validation humaine partielle). Colonne droite « Perspectives » (4 puces : fine-tuning embedding santé-sécurité, GraphRAG, RAG multimodal, agentic RAG). Bandeau bas : « Cadre transférable : juridique, RH, maintenance industrielle. »

14. CONCLUSION : Slide très épurée, symétrique de la slide 3. Rappel de la phrase-manifeste en grand : « La fiabilité d'un RAG n'est pas un score. C'est un faisceau de cinq dimensions à mesurer, à gouverner, à éprouver. » En bas : « Merci. Questions ? »

CONTRAINTES IMPORTANTES :
- Ne PAS générer de bullet points génériques. Chaque slide doit avoir un contenu précis et calibré comme décrit ci-dessus.
- Réserver explicitement des espaces pour les figures scientifiques (5 slides concernées : 6, 7, 8, 9, 11). Ne pas les remplacer par des illustrations génériques.
- Les slides 4 et 5 sont pédagogiques (introduction au RAG pour un jury qui n'a pas lu le mémoire) : privilégier les schémas clairs sur le texte, éviter la surcharge conceptuelle.
- Densité de texte modérée. Le contenu détaillé sera dans le discours oral, pas sur les slides. Chaque slide doit être lisible en 3-5 secondes.
- Cohérence visuelle absolue entre les 14 slides.
- Format 16:9.
```
```

---

### Option A — Deux prompts (7 + 7 slides)

Ci‑dessous : deux prompts prêts à coller dans Gamma.app (mode « Créer avec l'IA »). Chaque prompt génère 7 slides (7 + 7 = 14 au total). Conserver la charte visuelle et les contraintes indiquées plus haut.

Prompt 1 — Slides 1→7 :
```text
Génère une présentation professionnelle (7 slides, 16:9) pour la soutenance du mémoire « Évaluer la cohérence et la fiabilité d'un système RAG en contexte industriel critique — Le cas ScribBERT ». Ton : professionnel, sobre, charte bleu marine + accent orange. Pas d'emojis. Pied de page discret avec numéro de slide et rappel du titre.

Slides (strictement dans l'ordre) :
1) TITRE — Couverture : titre principal, sous-titre « Le cas ScribBERT — Département Prévention Santé‑Sécurité, Bouygues Travaux Publics », nom du candidat, Mastère 2 IA École Hexagone, tuteurs Flavien Martin & Julien Larseneur, date, deux logos discrets.
2) PROBLÈME — Trois chiffres gros à gauche (130 documents PDF · 2 min 30/recherche · ≈40% FR / 60% EN). À droite : illustration abstraite d'un labyrinthe documentaire. Bandeau bas : « ScribBERT n'est pas un dispositif de sécurité. C'est un appui à la décision. »
3) THÈSE — Slide manifeste très épurée : phrase centrée en très grand (« La fiabilité d'un RAG n'est pas un score... »). En bas, cinq petits blocs alignés (Pertinence retrieval, Fidélité, Pertinence réponse, Stabilité, Traçabilité).
4) RAG — Pédagogique 1/2 : schéma en 3 blocs (Question → Recherche → Rédaction par LLM → Réponse avec citations). Deux encadrés comparatifs en bas (LLM seul vs moteur de recherche). Bandeau bas explicatif.
5) ANATOMIE — Pédagogique 2/2 : schéma horizontal 5 étages (Ingestion → Chunking → Vectorisation/Index → Retrieval → Génération) avec mini-encarts d'erreur sous chaque étage. Bandeau bas : message sur l'indépendance des échecs.
6) DIM 1 — Pertinence retrieval : bandeau bleu «Dimension 1/5». Gauche : encart métriques (Recall@k, MRR, nDCG@k). Droite : zone réservée pour une heatmap (insérer manuellement [figures/fig_8_2_heatmap_mrr_modele_chunking.png]). Encart bas : «864 configurations testées · 750 exploitables · 50 questions annotées».
7) DIM 2 — Fidélité aux sources : bandeau bleu «Dimension 2/5». Zone principale : radar RAGAS (insérer manuellement [figures/fig_8_4_radar_ragas_5_configs.png]). Encart bas‑gauche : sous‑métriques RAGAS. Encart bas‑droite : conclusion chiffrée («Hybrid‑k5 + GPT‑3.5 : meilleur profil»).
```

Prompt 2 — Slides 8→14 :
```text
Génère une présentation professionnelle (7 slides, 16:9) — suite et fin — pour la même soutenance. Même charte visuelle et contraintes.

Slides (strictement dans l'ordre) :
8) DIM 3 — Pertinence & complétude : bandeau bleu «Dimension 3/5». Zone principale : graphe RAGAS par type de question (insérer manuellement [figures/fig_9_2_ragas_par_type_question.png]). Encart bas : capture gap analysis.
9) DIM 4 — Stabilité : bandeau bleu «Dimension 4/5». Zone principale : boxplot 4 indicateurs (insérer manuellement [figures/fig_8_5_boxplot_stabilite.png]). Encart chiffré : «0,94 stabilité inter‑runs vs 0,77 robustesse aux paraphrases». Bandeau bas : remarque prioritaire.
10) DIM 5 — Traçabilité : bandeau bleu «Dimension 5/5». Zone principale : capture d'écran annotée de l'interface ScribBERT (insérer manuellement [figures/fig_traceability_screenshot.png]). Encart bas en 3 points (citation → chunk ID, clic ouvre PDF, audit trail horodaté). Mention AI Act.
11) ANALYSE D'ERREURS : titre + figure (insérer manuellement [figures/fig_9_1_distribution_categories_erreur.png]) à gauche. À droite : tableau compact 3 colonnes (Catégorie / Dimension mise en cause / Action correctrice) au moins 6 lignes.
12) TRAJECTOIRE INDUSTRIALISATION : timeline 3 jalons (POC 2024‑25 → config cible 2026 → industrialisation groupe 2026‑27). Encart bas orange : «Passage en industrialisation groupe validé — juillet 2026».
13) LIMITES & PERSPECTIVES : deux colonnes (Limites : 4 puces précises ; Perspectives : 4 puces précises). Bandeau bas : cadre transférable.
14) CONCLUSION — Slide épurée miroir de la thèse : phrase‑manifeste en grand + «Merci. Questions ?».

Contraintes identiques : pas de listes génériques, texte modéré, 16:9.
```


## Après génération Gamma — checklist

Une fois les slides générées :

1. **Insérer manuellement les figures** aux emplacements réservés (6 figures à récupérer depuis `figures/`) :
   - Slide 6 → `fig_8_2_heatmap_mrr_modele_chunking.png`
   - Slide 7 → `fig_8_4_radar_ragas_5_configs.png`
   - Slide 8 → `fig_9_2_ragas_par_type_question.png`
   - Slide 9 → `fig_8_5_boxplot_stabilite.png`
   - Slide 10 → `fig_traceability_screenshot.png` (capture annotée de l'interface ScribBERT avec réponse + citations, format 16:9, 1200–1600 px large)
   - Slide 11 → `fig_9_1_distribution_categories_erreur.png`
2. **Vérifier la cohérence de la charte** (Gamma peut varier légèrement d'une slide à l'autre, harmoniser si besoin).
3. **Préparer la capture annotée Slide 10** : une screenshot de ScribBERT montrant (1) une question posée, (2) la réponse avec citations en évidence, (3) optionnel : annotation pointant le lien cliquable vers le PDF. Format PNG, 16:9, lisible depuis la salle.
4. **Répéter à voix haute avec chrono** — les textes ci-dessus sont calibrés à ± 10 secondes de la cible, mais l'oral peut dériver. Nouveau timing cible : 19'30 + marge 0'30 = 20'00.
5. **Prévoir un backup PDF** de la présentation, cas où la connexion Gamma serait instable le jour J.
