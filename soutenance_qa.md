# Préparation questions/réponses — Soutenance ScribBERT

**Durée de la phase Q&A** : 20 min (cf. guide Hexagone)

**Consigne de posture** : écouter la question jusqu'au bout, reformuler si besoin (« si je comprends bien votre question… »), répondre avec structure (affirmation → justification → chiffre ou renvoi au mémoire). Si tu ne sais pas : « c'est une question pertinente que je n'ai pas traitée dans ce cadre, mais voici ma première intuition… ». Ne pas bluffer.

---

## RÉPONSES FLASH — 4 AXES DE VULNÉRABILITÉ PRÉVISIBLES

Ces quatre points sont ceux sur lesquels le jury a le plus de chances de tester la solidité méthodologique du mémoire. Objectif : répondre en 30 à 45 secondes, sans défendre l'indéfendable, puis montrer que la limite est identifiée, documentée et déjà traduite en plan d'action.

---

### 1. Taille du jeu de test — 50 questions, est-ce suffisant ?

**Vulnérabilité à anticiper** :

Le mémoire indique lui-même qu'en-dessous de 100 à 150 questions, les comparaisons fines entre configurations restent sensibles au bruit statistique. Or le benchmark retrieval repose sur 50 questions pour 750 cellules exploitables.

**Réponse courte** :

Non, 50 questions ne suffisent pas pour trancher de manière statistiquement décisive entre des configurations très proches. En revanche, elles suffisent pour une phase exploratoire, c'est-à-dire pour détecter des effets robustes, éliminer des familles de configurations faibles et faire émerger des interactions structurantes, par exemple entre modèle d'embedding et stratégie de chunking. C'est exactement le statut que je donne à mes résultats : des tendances solides pour orienter l'itération suivante, pas un verdict définitif. L'extension du jeu de test à 150-300 questions annotées par des experts P2S est d'ailleurs la priorité absolue de la trajectoire court terme, précisément pour consolider statistiquement ces conclusions avant gel de la configuration de production.

**Réponse express** :

J'assume clairement que 50 questions, c'est exploratoire et non décisif. Ça suffit pour faire apparaître des tendances et prioriser les leviers d'amélioration, mais pas pour départager proprement des écarts marginaux. La première action prévue, avant industrialisation complète, c'est de porter le jeu de test à 150-300 questions annotées par des experts métier.

---

### 2. Biais de longueur — le juge LLM sur-note-t-il les réponses verbeuses ?

**Vulnérabilité à anticiper** :

Le mémoire met en évidence une corrélation forte entre longueur de la réponse et score RAGAS : $r = +0,64$ pour la faithfulness et $r = +0,63$ pour l'answer relevancy. Cela suggère un biais de longueur inhérent au paradigme LLM-as-judge.

**Réponse courte** :

Oui, ce biais existe, et c'est précisément pour cela que je le documente au lieu de le masquer. Une partie de cette corrélation est mécanique — par exemple les refus courts sont notés bas par construction — mais une autre partie relève bien d'un length bias du juge, qui tend à récompenser des réponses plus développées parce qu'elles offrent davantage de matière à valider. Ma position n'est donc pas de traiter les scores RAGAS comme une vérité absolue, mais comme un signal à calibrer. Les deux mitigations prévues sont, d'une part, durcir la consigne de concision dans le prompt système pour éviter les réponses inutilement verbeuses, et d'autre part, calibrer systématiquement les scores RAGAS sur un échantillon expert annoté humainement, afin de vérifier que le juge ne survalorise pas la forme au détriment du fond.

**Réponse express** :

Oui, le biais de longueur est réel et je l'ai mesuré. Je n'utilise donc pas RAGAS comme un oracle, mais comme un indicateur à calibrer. Les deux correctifs prévus sont un prompt plus strict sur la concision et une calibration systématique sur un sous-échantillon expert annoté par l'humain.

---

### 3. Déséquilibre linguistique — pourquoi si peu de questions en anglais ?

**Vulnérabilité à anticiper** :

Le corpus contient environ 60 % de documents en anglais, mais le jeu de test ne comporte que 9 questions en anglais contre 41 en français. Cela fragilise la portée des conclusions sur le comportement cross-lingue.

**Réponse courte** :

Le déséquilibre vient de l'origine même des requêtes initiales : le jeu de test a été dérivé en grande partie des journaux d'usage et des besoins remontés par des équipes majoritairement francophones, ce qui explique la surreprésentation du français. C'est donc un biais d'échantillonnage, pas une propriété souhaitée du protocole. Je ne prétends pas, sur cette base, avoir validé complètement le comportement bilingue du système. Ce que je peux dire, c'est que le retrieval cross-lingue fonctionne dans les cas testés, mais que la validation empirique reste insuffisante, en particulier sur les documents anglais courts de type Safety Alert, qui posent déjà des difficultés spécifiques. L'équilibrage linguistique du jeu de test fait partie du chantier d'industrialisation, justement pour confirmer de manière robuste le comportement cross-lingue sur ces cas.

**Réponse express** :

Le jeu de test reflète d'abord les usages observés des équipes francophones, d'où le 41/9. Je n'en fais donc pas une validation complète du bilinguisme. L'équilibrage linguistique est prévu dans la phase d'industrialisation pour tester correctement le cross-lingue, notamment sur les documents anglais courts.

---

### 4. Extrapolation de la stabilité — pourquoi une seule configuration ?

**Vulnérabilité à anticiper** :

Le protocole complet de stabilité — 10 runs par question plus paraphrases — n'a été exécuté que sur une seule configuration, alors que plusieurs variantes retrieval et génération existent dans le benchmark.

**Réponse courte** :

Oui, et c'est une limite de portée de la mesure, pas une erreur de protocole. J'ai choisi de lancer cette campagne complète sur la configuration la plus représentative du POC effectivement déployé, parce que le coût expérimental est élevé : dix exécutions par question plus les paraphrases font rapidement exploser le volume d'appels et le temps de traitement. L'objectif était d'abord de mesurer si la stabilité était un problème réel sur le système en usage, pas de cartographier exhaustivement toutes les variantes. Ce premier résultat a déjà une valeur forte puisqu'il montre un écart net entre stabilité inter-runs et robustesse aux paraphrases. En revanche, je n'extrapole pas abusivement ce score à toutes les configurations. La généralisation de ce protocole aux meilleures variantes identifiées — notamment hybrid-k5 et dense-k20-rerank5 — est planifiée avant le gel de la configuration de production.

**Réponse express** :

La campagne de stabilité complète a été menée sur la configuration la plus représentative du POC déployé, pour savoir si le problème existait réellement en usage. Le résultat est donc valide pour cette configuration, pas pour toutes. L'extension aux meilleures variantes, comme hybrid-k5 ou dense-k20-rerank5, est déjà prévue avant le choix final de production.

---

## PARTIE 1 — Questions sur la multimodalité de l'évaluation (focus jury)

Le jury est sensible à l'approche multi-dimensionnelle. S'attendre à ce qu'au moins 2 à 4 questions portent directement dessus. Préparer des réponses plus développées ici.

---

### Q1. Pourquoi cinq dimensions et pas trois, ou sept ? Comment avez-vous déterminé ce découpage ?

**Réponse** :

Le découpage est issu d'un raisonnement par les modes d'échec. J'ai d'abord listé les types de défaillances observés concrètement sur ScribBERT — passage non remonté, hallucination, omission d'exception, réponse variable, citation non vérifiable — puis je les ai regroupés par propriété qu'ils mettent en cause. Cinq propriétés se sont stabilisées naturellement : pertinence du retrieval, fidélité aux sources, pertinence de la réponse, stabilité, traçabilité.

Est-ce qu'on pourrait en ajouter ? Oui. On pourrait par exemple isoler la « préservation des modalités normatives » comme une sixième dimension dédiée, plutôt que de la rattacher à la fidélité. On pourrait aussi ajouter une dimension « coût opérationnel ». Mais à cinq, chaque dimension est adossée à au moins une famille de métriques instrumentables, ce qui est le critère que je me suis imposé. J'ai évité de multiplier les dimensions au-delà de ce qui est mesurable avec les outils disponibles — sinon, on crée des cases vides dans le tableau.

Le modèle n'est pas figé : il peut s'enrichir à mesure que les outils d'évaluation progressent. L'important, c'est le principe de décomposition, pas le chiffre cinq en lui-même.

---

### Q2. Les cinq étages de la chaîne RAG (slide 5) et les cinq dimensions d'évaluation, c'est la même chose ?

**Réponse** :

Non, et c'est un point que j'ai tenu à clarifier dans la présentation. Les cinq étages — ingestion, chunking, vectorisation, retrieval, génération — décrivent *où* dans la chaîne une erreur peut naître. Ce sont des positions structurelles. Les cinq dimensions — pertinence retrieval, fidélité, pertinence réponse, stabilité, traçabilité — décrivent *ce qu'on mesure* sur le résultat du système. Ce sont des propriétés.

Les deux grilles sont orthogonales. La stabilité, par exemple, est transverse à toute la chaîne : elle peut être affectée par la stochasticité du LLM (étage génération) mais aussi par l'approximation ANN de l'index (étage vectorisation/retrieval). La traçabilité est aussi transverse : elle dépend du format de citation (génération) mais aussi de la structure des métadonnées (ingestion/chunking).

C'est précisément le croisement des deux grilles qui rend l'analyse d'erreurs actionnable. Quand je dis en slide 11 « cette erreur relève de la dimension 2 (fidélité), elle est localisée à l'étage génération, donc l'action correctrice est un durcissement du prompt », j'utilise les deux grilles simultanément. Sans la grille des dimensions, je sais juste que la réponse est fausse. Sans la grille des étages, je sais qu'elle est infidèle mais je ne sais pas quoi corriger.

---

### Q3. Pourquoi ne pas utiliser un score composite unique (une note sur 100) plutôt que cinq scores séparés ?

**Réponse** :

Parce qu'un score composite masque l'origine de l'erreur. Prenons un exemple : une configuration obtient 78/100. Une autre obtient aussi 78/100. Sont-elles équivalentes ? Peut-être pas du tout : la première peut avoir un excellent retrieval mais une fidélité médiocre, la seconde peut avoir le profil inverse. L'action correctrice est complètement différente — reranking dans un cas, durcissement du prompt dans l'autre — mais le score composite donne la même note.

En contexte santé-sécurité, c'est encore plus critique : un système qui a 95/100 en moyenne mais 0,50 de fidélité sur les questions conditionnelles « que faire si… » est dangereux, et le score composite ne remontera pas cette faiblesse localisée.

Un score composite peut avoir du sens en production (pour un tableau de bord synthétique, ou un seuil de déploiement), mais il ne sert pas à diagnostiquer. Mon protocole produit les scores par dimension, qui permettent le diagnostic ; la synthèse en score unique peut se faire dans un second temps, avec des pondérations adaptées au contexte métier.

---

### Q4. Comment articulez-vous évaluation automatique et évaluation humaine ? Quelle est la part de chacune ?

**Réponse** :

Le protocole est hybride, par construction. L'évaluation automatique — métriques IR classiques pour le retrieval, RAGAS pour la génération — couvre l'ensemble du jeu de test sur toutes les configurations. C'est le balayage large, qui sert à comparer et à identifier les tendances. L'évaluation humaine est ciblée : elle porte sur un sous-échantillon de 15 questions critiques, majoritairement conditionnelles et procédurales, de criticité élevée.

La logique, c'est la triangulation : une conclusion n'est retenue que si les deux approches convergent. Et quand elles divergent, c'est souvent les cas les plus instructifs — ceux où le LLM-juge RAGAS note 0,90 mais l'expert constate qu'une exception a été omise, ou inversement.

Sur les dimensions, la répartition est la suivante : les dimensions 1 (pertinence retrieval) et 4 (stabilité) sont presque entièrement automatisables. La dimension 2 (fidélité) l'est à 80% via RAGAS, mais la préservation des modalités normatives — « doit » vs « peut » — nécessite une vérification humaine. Les dimensions 3 (complétude) et 5 (traçabilité) sont les plus dépendantes de l'évaluation humaine ou d'un design applicatif contrôlé.

---

### Q5. Le LLM-as-judge, c'est fiable ? Vous ne risquez pas d'évaluer un LLM par un autre LLM ?

**Réponse** :

Le risque est réel et documenté dans le mémoire. Il y a trois biais identifiés. Le biais de longueur : le LLM-juge tend à mieux noter les réponses verbeuses, ce que j'ai d'ailleurs observé et quantifié — corrélation de Pearson de +0,64 entre longueur de la réponse et score de faithfulness, dont une part est légitime (les refus courts sont notés 0 par construction) mais une part est artificielle. Le biais d'auto-validation circulaire : si le même modèle génère et juge, il peut valider ses propres erreurs. Et le biais de format : les réponses structurées en listes sont systématiquement mieux notées.

Comment j'ai mitigé ça : premièrement, le LLM-juge est un modèle distinct du générateur (le juge RAGAS tourne sur GPT-4 via l'API, le générateur testé est GPT-3.5 ou Mistral-7B). Deuxièmement, les justifications du juge sont journalisées, pas seulement le score : on peut vérifier a posteriori pourquoi une proposition a été jugée « supportée ». Troisièmement, la calibration humaine sur le sous-échantillon de 15 questions critiques sert précisément à vérifier que les scores RAGAS ne dérivent pas de la perception experte.

Est-ce parfait ? Non. C'est pourquoi je ne me repose jamais sur une seule source d'évaluation, et c'est pourquoi la dimension « préservation des modalités » reste évaluée humainement — les juges LLM actuels ne sont pas fiables pour distinguer « doit » de « peut » dans un contexte normatif.

---

### Q6. La stabilité est votre dimension 4. Pourquoi la traiter comme une dimension à part entière plutôt que comme un indicateur secondaire ?

**Réponse** :

Parce que la stabilité a un double statut. C'est une dimension de qualité en soi : un utilisateur qui obtient deux réponses différentes à la même question perd confiance, et dans un contexte santé-sécurité, il peut prendre deux décisions différentes selon le moment. Mais c'est aussi une condition méthodologique : si la variance intra-configuration est élevée, comparer deux configurations sur une seule exécution n'a pas de sens statistique. La mesure de stabilité conditionne donc la robustesse de toutes les autres comparaisons.

C'est d'ailleurs ce que le résultat 0,94 vs 0,77 montre très concrètement : à requête identique, la variance est faible, les comparaisons tiennent. Mais si on considère la robustesse aux paraphrases — ce qui correspond au comportement réel de l'utilisateur — la variance est beaucoup plus élevée, ce qui signifie que les scores moyens par dimension sont eux aussi plus bruités qu'on ne le pense si on ne contrôle pas la formulation.

Je n'ai pas trouvé de framework qui traite ça explicitement. RAGAS, TruLens, LangSmith évaluent la qualité ponctuelle. La stabilité est un ajout spécifique de mon protocole, et c'est un des apports méthodologiques que je revendique dans ce mémoire.

---

### Q7. Comment pondérez-vous les cinq dimensions entre elles ? Sont-elles d'importance égale ?

**Réponse** :

Dans le protocole tel que je l'ai conçu, elles ne sont pas pondérées — elles sont reportées séparément. C'est un choix délibéré : la pondération relève d'un arbitrage métier qui dépend du contexte de déploiement.

Si je devais pondérer pour ScribBERT, je mettrais la fidélité aux sources en priorité 1, parce que c'est l'erreur la plus dangereuse en santé-sécurité (une affirmation non supportée par les sources peut induire une mauvaise décision). La traçabilité en priorité 2, parce qu'elle conditionne la confiance et la conformité réglementaire. Ensuite la stabilité, puis la pertinence retrieval, puis la pertinence réponse.

Mais cette hiérarchie ne serait pas la même pour un RAG juridique (où la traçabilité serait probablement en numéro 1) ou un RAG d'assistance commerciale (où la pertinence réponse primerait). Le cadre est pensé pour être instancié avec les pondérations du domaine cible.

---

### Q8. La dimension 5 (traçabilité) n'a pas de métrique quantitative. Ce n'est pas une faiblesse ?

**Réponse** :

C'est une caractéristique, pas une faiblesse. La traçabilité est une propriété de design, pas de performance statistique. Soit le système cite ses sources de manière vérifiable et journalisée, soit il ne le fait pas. On peut mesurer la *citation completeness* (toutes les affirmations sont-elles sourcées ?) et la *citation correctness* (les passages cités supportent-ils réellement l'affirmation ?), ce qui donne des métriques — mais la traçabilité au sens fort, c'est la chaîne complète : identifiant de chunk → document → page → PDF téléchargeable → audit trail horodaté.

Ce que la dimension 5 capture, c'est l'**auditabilité** du système : la capacité à reconstituer, a posteriori, le chemin complet d'une réponse. C'est ce que l'AI Act exige pour les systèmes à haut risque, et c'est ce que les utilisateurs terrain placent comme facteur numéro un d'acceptabilité dans les retours que j'ai collectés.

---

### Q9. Comment votre cadre se compare-t-il à RAGAS ? Est-ce une extension, un remplacement ?

**Réponse** :

Ni l'un ni l'autre exactement. RAGAS est un outil d'évaluation automatique que j'utilise dans mon protocole — c'est un des instruments, pas le cadre. Mon cadre est plus large : il ajoute la stabilité (absente de RAGAS), la traçabilité (absente de RAGAS), l'évaluation humaine structurée, et surtout le principe de décomposition diagnostique : localiser l'erreur dans la chaîne plutôt que constater un score global.

RAGAS est excellent pour produire des scores de faithfulness, context precision, answer relevancy, context recall. Je les utilise tels quels. Mais RAGAS ne dit pas *pourquoi* la faithfulness est basse — est-ce un problème de retrieval, de prompt, de chunking ? Mon protocole associe chaque score à une dimension, chaque dimension à une famille d'étages, et chaque croisement à une action correctrice. C'est ça le diagnostic.

---

### Q10. Si vous deviez ajouter une sixième dimension demain, ce serait laquelle ?

**Réponse** :

Probablement la **robustesse adversariale**. J'ai des tests hors-périmètre dans le jeu de test — 4 questions adversariales dont une dangereuse (court-circuiter un verrouillage de sécurité) — et le système les refuse correctement. Mais c'est un échantillon trop petit pour en faire une dimension. Une sixième dimension dédiée testerait systématiquement la résistance aux prompt injections, aux questions à présupposés faux, aux requêtes qui tentent de contourner les garde-fous. C'est un enjeu de sécurité du système lui-même, distinct de la sécurité du contenu.

Autre candidat : la **fraîcheur documentaire**, c'est-à-dire la capacité du système à détecter et à signaler qu'une source utilisée est obsolète (document de 2020 remplacé par une version 2025). Aujourd'hui, ScribBERT ne le fait pas.

---

## PARTIE 2 — Questions techniques (RAG, architecture, choix)

---

### Q11. Pourquoi RAG plutôt que fine-tuning ?

**Réponse** :

Trois raisons. La première, c'est la traçabilité : dans un RAG, les documents consultés sont identifiables et citables. Un modèle fine-tuné « sait » des choses mais ne peut pas dire d'où elles viennent — c'est rédhibitoire dans notre contexte. La deuxième, c'est la mise à jour : nos procédures évoluent régulièrement, et réentraîner un modèle à chaque révision documentaire serait trop coûteux et non traçable. Dans un RAG, on réindexe. La troisième, c'est empirique : une étude comparative récente d'Ovadia et al. (2024) montre que sur des tâches d'injection de connaissances nouvelles, le RAG surpasse systématiquement le fine-tuning supervisé, et plus encore quand l'information est rare ou évolutive.

Cela dit, les deux ne sont pas exclusifs. Un fine-tuning léger pour calibrer le ton ou la structure de réponse, couplé à un RAG pour l'accès aux connaissances, est une combinaison pertinente que je n'ai pas explorée dans ce mémoire mais qui figure dans les perspectives.

---

### Q12. Pourquoi ada-002 alors qu'il est ancien ?

**Réponse** :

Parce que sur ce corpus, il n'y a pas de gain mesurable à passer à un modèle plus récent ou plus gros. Ada-002 est dans la bande de ±0,03 de MRR avec les huit meilleurs modèles testés, y compris embed-3-large d'OpenAI qui a trois fois plus de dimensions — et sur mon corpus, les deux donnent des scores rigoureusement identiques, à moins de 0,001 près, pour une latence de 80 ms contre 3 300 ms.

Le choix s'est fait sur les critères pratiques : ada-002 est déjà déployé dans le tenant Azure de Bouygues Construction, ce qui supprime le coût d'hébergement GPU et le délai de mise en place. Il est multilingue et gère aussi bien le français que l'anglais sur le corpus testé. Et sa latence reste négligeable devant celle de la génération LLM (5 secondes pour GPT-3.5). C'est un choix documenté et opérationnel, pas un choix par défaut.

---

### Q13. Pourquoi ChromaDB et pas Qdrant, Pinecone, Weaviate ?

**Réponse** :

ChromaDB est le choix du POC, pas le choix définitif. Il s'est imposé par sa simplicité d'intégration, son déploiement local sans dépendance cloud, et le fait qu'il était suffisant pour un corpus de 200 documents. Pour la mise en production à l'échelle groupe, la question sera réévaluée : Qdrant ou Weaviate offrent des garanties de scalabilité, de filtrage optimisé et de gestion distribuée que ChromaDB n'offre pas. C'est dans le cahier des charges de l'industrialisation.

---

### Q14. Pourquoi GPT-3.5 et pas GPT-4 ou Claude ?

**Réponse** :

Deux raisons pragmatiques : le coût et la vitesse. Le benchmark exploratoire a nécessité environ 750 appels LLM (5 configurations × 50 questions × 3 campagnes), et GPT-3.5 a permis de faire tourner l'ensemble pour moins de 15 € tout en maintenant des temps de réponse médians de 5 secondes. GPT-4, à l'époque des premiers tests, était environ 20 fois plus cher et 3 à 5 fois plus lent.

Est-ce que GPT-3.5 est le LLM optimal ? Non. Le plafond de faithfulness observé à 0,77 est presque certainement imputable à la taille du modèle. La cible pour la production est un modèle plus récent — GPT-4o, Claude Sonnet 4, Mistral Large — et le benchmark de sélection est prévu dans la trajectoire d'industrialisation. GPT-3.5 a été le bon choix pour la phase exploratoire, il ne sera pas le choix de production.

---

### Q15. Le chunking par regex sur les marqueurs Markdown, c'est fragile ?

**Réponse** :

C'est spécifique au corpus, pas fragile. Les référentiels du corpus ScribBERT partagent la même charte de mise en forme — c'est une propriété du processus documentaire de Bouygues TP. Les titres, numérotations, structures de paragraphe sont suffisamment homogènes pour qu'une regex bien ciblée les capture proprement. C'est d'ailleurs plus rapide à exécuter et plus prévisible qu'un chunking sémantique, qui n'a d'ailleurs pas montré de gain mesurable sur ce corpus dans le benchmark — il finit dernier des neuf stratégies testées en MRR moyenne.

Cela dit, pour le passage à l'échelle avec les documents des filiales et des clients, la regex devra être adaptée ou complétée par un parser plus robuste, parce que les formats seront moins homogènes. C'est un risque identifié.

---

### Q16. L'hybridation BM25 + dense : pourquoi n'est-elle pas déjà en production ?

**Réponse** :

Parce que le POC a été construit pour valider la faisabilité et l'utilité avant d'optimiser. Le dense pur était plus simple à implémenter et suffisant pour les premiers retours utilisateurs. L'hybridation est apparue comme priorité numéro un dans les résultats du benchmark — +0,031 de MRR, et la meilleure configuration absolue utilise hybrid-k5. Elle est dans le cahier des charges de la version cible 2026. En pratique, l'implémentation est assez directe : BM25 sur le texte brut des chunks, récupération dense en parallèle, fusion par Reciprocal Rank Fusion.

---

### Q17. Comment gérez-vous les tableaux et les schémas dans les PDF ?

**Réponse** :

Honnêtement, pour l'instant, mal. La version POC linéarise les tableaux en texte brut, ce qui détruit leur structure, et ignore les schémas. C'est la troisième priorité dans la trajectoire d'industrialisation, après l'hybridation et le reranking.

La piste étudiée est une chaîne image-to-text : un modèle multimodal (VLM) génère une description textuelle de chaque image ou tableau, conserve le lien vers l'image originale, et injecte le résultat comme un chunk enrichi. Les matrices de risques et les logigrammes décisionnels présents dans les référentiels contiennent une information de haute valeur santé-sécurité qui est actuellement perdue, et c'est un vrai manque.

---

### Q18. Pourquoi un seuil de distance fixe (0,17) plutôt qu'un seuil adaptatif ?

**Réponse** :

Par simplicité, et parce qu'il est empiriquement efficace : les 4 questions hors-périmètre sont correctement refusées, et le taux de refus à tort sur la configuration avec seuil est de 6 sur 46 questions in-scope — tolérable mais perfectible. Un seuil adaptatif — par exemple basé sur l'écart entre le score du premier et du cinquième chunk — serait plus robuste et fait partie des pistes d'amélioration identifiées. Il existe aussi la possibilité de calibrer le seuil par famille de question (factuelle vs procédurale), ce qui n'a pas été testé.

---

## PARTIE 3 — Questions méthodologiques (protocole, jeu de test, stats)

---

### Q19. 50 questions, c'est suffisant ?

**Réponse** :

Pour une phase exploratoire, oui. Pour des conclusions statistiquement décisives, non. Je le dis explicitement dans les limites : l'écart entre configurations doit être lu comme une tendance, pas comme un verdict. Avec 50 questions stratifiées, on peut identifier des effets de taille large (les modèles généralistes anglais décrochent clairement) et des interactions (le chunking optimal dépend du modèle), mais on ne peut pas trancher sur des écarts de 1 à 2% de MRR.

L'objectif court terme est de passer à 150-300 questions, en impliquant directement des experts P2S dans l'annotation, et en augmentant la part anglophone (9/50 actuellement, ce qui est trop peu pour conclure sur le multilinguisme).

---

### Q20. Les questions sont annotées par une seule personne (vous). Ça ne pose pas un problème de biais ?

**Réponse** :

Si, et c'est assumé dans les limites. L'annotation par un seul annotateur introduit un biais de subjectivité sur les réponses de référence et sur les jugements de pertinence des passages. L'idéal serait au moins deux annotateurs indépendants avec mesure de l'accord inter-juges (Kappa de Cohen ≥ 0,7). C'est prévu dans la trajectoire d'industrialisation, avec des experts P2S métier comme annotateurs.

Cela dit, la plupart des questions sont factuelles ou procédurales, et les réponses de référence sont directement extraites des référentiels, ce qui réduit la marge d'interprétation. Le biais est plus problématique sur les questions justificatives ou conditionnelles, où la « bonne réponse » est moins univoque.

---

### Q21. Pourquoi une approche OFAT (un facteur à la fois) plutôt qu'un plan factoriel complet ?

**Réponse** :

En réalité, j'ai fait un plan factoriel complet côté retrieval : 16 modèles × 9 chunkings × 6 variantes = 864 cellules. C'est plus qu'un OFAT. En revanche, côté génération, j'ai testé 5 configurations seulement, parce que chaque run génération coûte en temps et en appels API, et qu'il fallait arbitrer.

L'OFAT est plutôt la logique de lecture des résultats : pour interpréter l'effet d'un facteur (par exemple le chunking), on marginalise sur les autres (en moyennant sur tous les modèles et toutes les variantes de retrieval). C'est une simplification, qui ne capture pas les interactions — mais les interactions sont visibles dans la heatmap complète (slide 6), et le tableau des meilleurs chunkings par modèle montre bien qu'elles existent.

---

### Q22. Les scores RAGAS sont-ils comparables entre configurations qui n'ont pas les mêmes chunks dans le contexte ?

**Réponse** :

C'est une subtilité importante. Le context recall RAGAS mesure la couverture de la réponse de référence par le contexte récupéré. Si deux configurations utilisent des chunking différents, les chunks ne sont pas les mêmes, et le context recall n'est pas directement comparable au grain du chunk — il l'est au grain du document de référence, qui est commun.

Pour la faithfulness et l'answer relevancy, le problème est moindre : elles portent sur la réponse générée vs le contexte effectivement fourni, donc chaque score est cohérent avec sa propre configuration. La comparaison entre configurations reste valide si on compare des scores calculés dans des conditions homogènes (même jeu de questions, même LLM, même prompt).

C'est d'ailleurs pour ça que j'ai gelé le LLM, le prompt et la température lors des comparaisons retrieval : isoler l'effet du facteur testé.

---

## PARTIE 4 — Questions métier et réglementaires

---

### Q23. Comment garantir que l'utilisateur ne prendra pas la réponse pour argent comptant ?

**Réponse** :

Quatre garde-fous. Premièrement, un avertissement permanent affiché en bas de l'écran, rappelant que la responsabilité de vérification incombe à l'utilisateur. Deuxièmement, les citations systématiques et cliquables, qui renvoient au PDF source : l'interface est conçue pour que la source soit plus visible que la réponse synthétisée. Troisièmement, le refus contrôlé : quand aucun chunk pertinent n'est trouvé, le système répond « Cette information ne figure pas dans les référentiels consultés » plutôt que d'improviser. Quatrièmement, la supervision humaine : une revue périodique des journaux par l'équipe P2S, avec procédure d'escalade pour signaler une réponse erronée.

Au-delà de ces mesures techniques, un axe de travail tout aussi important est la formation des utilisateurs : bonnes pratiques de formulation, lecture critique des réponses, vérification systématique des sources. L'outil ne peut fonctionner correctement que si l'utilisateur comprend ce qu'il peut attendre — et ce qu'il ne doit pas en attendre.

---

### Q24. AI Act : vous êtes prêts ?

**Réponse** :

En cours de qualification. ScribBERT relève potentiellement de la catégorie « haut risque » au sens de l'annexe III du règlement, dès lors qu'il contribue à la gestion des risques pour la sécurité des travailleurs. Si cette classification est confirmée, les obligations principales sont : un système de gestion des risques documenté, une documentation technique détaillée, la transparence envers les utilisateurs, le contrôle humain, et un niveau de robustesse et d'exactitude documenté.

Le protocole d'évaluation développé dans ce mémoire contribue directement à plusieurs de ces exigences : la mesure de fiabilité (cinq dimensions), la traçabilité des sources, la documentation des choix techniques, le versioning du jeu de test et des résultats. C'est un des arguments opérationnels du cadre : il n'a pas été conçu pour l'AI Act, mais il en remplit les prérequis.

---

### Q25. Qui est responsable si une décision de prévention s'appuie sur une réponse erronée ?

**Réponse** :

Juridiquement, l'employeur reste responsable de la sécurité de ses salariés, quelle que soit la technologie utilisée. ScribBERT est un outil d'aide, pas un substitut au jugement humain. L'avertissement permanent le rappelle.

Mais la question est plus nuancée dans la pratique. En tant que développeur interne du POC, Bouygues TP — puis Bouygues Construction après industrialisation — doit pouvoir documenter ses choix, ses tests, et le niveau de fiabilité atteint. C'est exactement le rôle du protocole d'évaluation. Si un jour un audit ou un incident demande de justifier la qualité du système, les résultats documentés (750 configurations testées, scores de faithfulness, campagne de stabilité, analyse d'erreurs typologique) constituent un dossier solide.

---

### Q26. Le corpus est bilingue FR/EN. Est-ce que le système ne risque pas de répondre en anglais à une question en français ?

**Réponse** :

Non, le LLM répond systématiquement dans la langue de la question — c'est contrôlé par la consigne de langue dans le prompt (cf. Ch. 7.7 du mémoire). Le retrieval, en revanche, est cross-lingue : une question en français peut remonter des chunks en anglais, et inversement. C'est voulu, parce que la documentation client est majoritairement en anglais et il ne faut pas la rater.

Le cas limite observé, c'est l'asymétrie de longueur : un document anglais très court (un Safety Alert d'une page) peut être mal apparié avec une requête française plus longue, non pas à cause de la langue mais parce que le vecteur du chunk court est dominé par quelques tokens spécialisés et s'éloigne dans l'espace vectoriel. C'est un biais structurel identifié, pas un biais linguistique au sens strict.

---

### Q27. Coût opérationnel : c'est viable en production ?

**Réponse** :

Très confortablement. Environ 0,002 € par requête en configuration Azure (vectorisation ada-002 + génération GPT-3.5). Le benchmark exploratoire complet — 864 configurations de retrieval, 5 configurations de génération, 1 campagne de stabilité, évaluation RAGAS — a coûté moins de 15 € en appels API. Même avec un modèle plus récent (GPT-4o, environ 5-10x plus cher que GPT-3.5 au token), on resterait sous les 0,02 € par requête.

Le facteur limitant n'est pas le coût financier, c'est le temps machine pour les modèles locaux (36 secondes par question sur Mistral-7B, non viable en temps réel) et la latence en rafale (saturation des quotas Azure quand on enchaîne 50 questions en benchmark).

---

## PARTIE 5 — Questions sur le projet personnel et l'alternance

---

### Q28. Quel a été le moment le plus difficile du projet ?

**Réponse** :

Le tâtonnement initial sur l'évaluation. Pendant les premières semaines de la phase exploratoire, j'essayais de juger la qualité du système en posant quelques questions et en regardant si les réponses « avaient l'air bonnes ». C'est exactement ce que je critique dans le mémoire, mais c'est par là que je suis passé. Le déclic est venu des échanges avec Julien Larseneur, qui ne jurait que par les métriques et qui m'a poussé à comprendre pourquoi un seul score ne suffisait pas. La formalisation du cadre à cinq dimensions est directement issue de cette frustration initiale.

---

### Q29. Quelle est votre contribution personnelle vs ce qui existait déjà ?

**Réponse** :

Les outils existaient (LangChain, ChromaDB, RAGAS, sentence-transformers). L'architecture RAG n'est pas nouvelle. Ma contribution est à trois niveaux.

Premier niveau, méthodologique : la définition opératoire de la fiabilité en cinq dimensions mesurables, le protocole de stabilité dédié (absent des frameworks existants), et le principe de diagnostic croisé (dimension × étage → action correctrice). Ce n'est pas un assemblage de métriques connues, c'est un cadre structuré qui dit comment les articuler.

Deuxième niveau, applicatif : ScribBERT est un système complet — extraction, chunking, vectorisation, retrieval, génération, interface, déploiement — développé de bout en bout, avec une UI React codée à la main, une API FastAPI, et une fonctionnalité de gap analysis que je n'ai pas trouvée dans les outils existants.

Troisième niveau, expérimental : le benchmark de 750 configurations sur un corpus santé-sécurité réel, avec un jeu de test stratifié construit manuellement. C'est un volume d'expérimentation significatif qui n'existait pas avant ce travail.

---

### Q30. Si vous aviez 6 mois de plus, que feriez-vous en priorité ?

**Réponse** :

Trois choses. D'abord, passer le jeu de test à 200 questions avec annotation multi-annotateurs, pour valider statistiquement les tendances observées. Ensuite, implémenter et benchmarker l'hybridation BM25 + dense avec reranking cross-encoder, qui est la priorité numéro un identifiée par les résultats. Enfin, lancer un fine-tuning contrastif d'un modèle de vectorisation sur les paires question-passage santé-sécurité du jeu de test, pour mesurer le gain d'un modèle d'embedding spécialisé vs un modèle généraliste.

---

### Q31. Le projet est validé pour l'industrialisation. Concrètement, c'est quoi la suite ?

**Réponse** :

L'industrialisation va être portée par Bouygues Construction (niveau groupe, pas filiale). Concrètement, ça veut dire : extension du corpus aux référentiels de toutes les filiales (pas seulement BYTP), intégration des réglementations internationales, passage à un LLM de production (GPT-4o ou équivalent, benchmark dédié à venir), mise en place d'une gouvernance conforme à l'AI Act (versioning, audit trail, tests automatisés en CI/CD avant chaque déploiement), et déploiement à un public utilisateur beaucoup plus large. Le cadre d'évaluation de ce mémoire va servir directement à piloter cette montée en charge : chaque nouvelle brique sera validée sur le protocole cinq dimensions avant mise en production.

---

## PARTIE 6 — Questions pièges / inattendues

---

### Q32. ScribBERT pourrait-il remplacer un préventeur ?

**Réponse** :

Non, et ce n'est pas son objectif. ScribBERT est un amplificateur, pas un substitut. Il fait gagner du temps sur la phase de recherche documentaire — passer de 2 min 30 à quelques secondes pour trouver l'information — mais le jugement, l'interprétation du contexte chantier, l'adaptation de la règle à la situation concrète, restent du ressort du professionnel. Le système ne connaît pas le chantier, ne voit pas les conditions réelles, ne porte pas de jugement sur les risques. Il cite des référentiels.

L'avertissement permanent et le design de l'interface sont construits pour maintenir cette frontière. Si un jour un utilisateur cesse de vérifier les sources parce qu'il « fait confiance au système », c'est un signal d'alerte, pas un signe de succès.

---

### Q33. Votre système a-t-il déjà produit une réponse dangereuse ?

**Réponse** :

Pas de réponse « dangereuse » au sens fort — aucune instruction qui aurait pu mettre quelqu'un en danger si elle avait été suivie. En revanche, pendant la phase de prototypage (avant la formalisation du protocole), j'ai observé des réponses incomplètes — par exemple une procédure d'espace confiné citée correctement mais sans l'exception qui s'y rattache — et des réponses hors-périmètre quand le prompt était trop permissif (la première version du prompt système de ScribBERT, littéralement, pouvait sortir des recettes de cookies). C'est exactement ce qui a motivé le durcissement du prompt et la formalisation du protocole.

Sur la configuration de référence testée dans le mémoire, les 4 questions adversariales (dont une demandant comment court-circuiter un verrouillage de sécurité) ont toutes été correctement refusées.

---

### Q34. Si un concurrent déployait un RAG santé-sécurité demain, est-ce qu'il pourrait utiliser votre protocole ?

**Réponse** :

Oui, et c'est voulu. Le cadre méthodologique — les cinq dimensions, le principe de décomposition, le protocole de stabilité, l'approche hybride d'évaluation — est publié dans ce mémoire et n'est pas spécifique à ScribBERT. Évidemment, le jeu de test, le corpus, et les choix d'implémentation sont propres à Bouygues TP. Mais un concurrent pourrait parfaitement instancier le même cadre sur son propre corpus, avec son propre jeu de test, et bénéficier du même pouvoir diagnostique. C'est un des apports du mémoire que je revendique : la transférabilité du cadre.

---

### Q35. Avec les progrès rapides des LLMs, votre cadre ne sera-t-il pas obsolète dans deux ans ?

**Réponse** :

Le cadre est conçu pour être indépendant du modèle. Les cinq dimensions (pertinence retrieval, fidélité, pertinence réponse, stabilité, traçabilité) restent pertinentes quel que soit le LLM utilisé — un GPT-6 ou un Claude 5 hallucineront peut-être moins, mais la fidélité restera à mesurer. La stabilité restera un enjeu tant que la génération sera stochastique. La traçabilité restera un prérequis réglementaire.

Ce qui évoluera, ce sont les instruments de mesure : les LLM-as-judge deviendront plus fiables, les métriques automatiques couvriront peut-être la préservation des modalités, et de nouveaux benchmarks spécialisés apparaîtront. Le cadre est prévu pour intégrer ces évolutions sans changer sa structure.
