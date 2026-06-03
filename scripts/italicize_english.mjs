// Script: italicise tous les termes anglais (mots/expressions, PAS les acronymes)
// dans memoire_complet.md, et génère un glossaire à la fin.
//
// Règles :
//  - Préserve : blocs de code ``` ```, code inline `...`, math $$...$$, math $...$,
//    citations Pandoc [@xxx; @yyy], liens markdown [texte](url), images ![alt](url),
//    blocs Pandoc ::: ... :::, balises raw \newpage etc.
//  - Pour chaque terme T de la liste :
//      **T** -> ***T***
//      bare T (entouré de séparateurs non-*) -> *T*
//  - Toutes les occurrences sont touchées (choix utilisateur).
//  - Évite de toucher les T déjà en *T* ou ***T***.
//
// Usage : node scripts/italicize_english.mjs

import { readFileSync, writeFileSync, copyFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

const SRC = resolve(process.cwd(), "memoire_complet.md");
const BACKUP = resolve(process.cwd(), "memoire_complet.backup.md");

// ---------- Liste des termes anglais à italiciser ----------
// Ordre IMPORTANT : les expressions multi-mots et les formes longues d'abord,
// pour éviter qu'un mot court ne mange une expression plus longue.
// PAS d'acronymes (RAG, LLM, API, BM25, GPT, etc.) — choix utilisateur.
// PAS de termes ambigus avec le français (paraphrase, hybride, multimodal,
//   hallucination, contraste, version, score, transformeur, etc.).
const TERMS = [
  // ----- expressions multi-mots (à traiter en premier) -----
  "Approximate Nearest Neighbor",
  "Hypothetical Document Embeddings",
  "Massive Text Embedding Benchmark",
  "Matryoshka Representation Learning",
  "One-Factor-At-a-Time",
  "Proof Of Concept",
  "Proof of Concept",
  "Reciprocal Rank Fusion",
  "Vision Language Model",
  "anisotropic embeddings",
  "answer relevance",
  "answer relevancy",
  "audit trail",
  "case-sensitive",
  "citation completeness",
  "citation correctness",
  "citation faithfulness",
  "code-switching",
  "context precision",
  "context recall",
  "context relevance",
  "cross-encoder",
  "cross-encoders",
  "dense retrieval",
  "dual-encoder",
  "end-to-end",
  "exact match",
  "few-shot",
  "fine-tunabilité",
  "fine-tunable",
  "fine-tune",
  "fine-tuned",
  "fine-tunes",
  "fine-tuning",
  "flip rate",
  "GAP analysis",
  "gold standard",
  "grounding explicite",
  "hard match",
  "hard negatives",
  "Hit rate",
  "hit ratio",
  "human-in-the-loop",
  "Hypothetical Document Embedding",
  "in-context learning",
  "instruction tuning",
  "inverse document frequency",
  "knowledge base",
  "knowledge cutoff",
  "knowledge distillation",
  "knowledge graph",
  "late interaction",
  "late-interaction",
  "learning-to-rank",
  "LLM-as-a-judge",
  "LLM-as-judge",
  "LLM-juge",
  "lost in the middle",
  "machine-vérifiable",
  "Mean Reciprocal Rank",
  "multi-query",
  "multi-stage",
  "open source",
  "open weights",
  "open-source",
  "open-weights",
  "parent-document retrieval",
  "passage embeddings",
  "pre-training",
  "pretraining",
  "prompt engineering",
  "query expansion",
  "query likelihood",
  "query rewriting",
  "recursive character text splitter",
  "relevance feedback",
  "Reciprocal Rank",
  "sentence embeddings",
  "siamese networks",
  "sparse retrieval",
  "step-back prompting",
  "term frequency",
  "term specificity",
  "text splitter",
  "time-consuming",
  "top-k",
  "top-n",
  "top-p",
  "vector store",
  "vector stores",
  "zero-shot",

  // ----- mots simples -----
  "agentic",
  "baseline",
  "baselines",
  "batching",
  "backend",
  "benchmark",
  "benchmarker",
  "benchmarking",
  "benchmarks",
  "chatbot",
  "chatbots",
  "chunk",
  "chunker",
  "chunkers",
  "chunking",
  "chunks",
  "cluster",
  "clustering",
  "clusters",
  "custom",
  "dataset",
  "datasets",
  "deployable",
  "drift",
  "embedder",
  "embedders",
  "embedding",
  "embeddings",
  "endpoint",
  "endpoints",
  "faithfulness",
  "framework",
  "frameworks",
  "frontend",
  "GraphRAG",
  "groundedness",
  "grounding",
  "hallucinate",
  "hallucinated",
  "hallucinates",
  "hallucinating",
  "hub",
  "inline",
  "input",
  "inputs",
  "leaderboard",
  "leaderboards",
  "listwise",
  "loader",
  "loaders",
  "logger",
  "loggers",
  "mapping",
  "Memex",
  "mining",
  "output",
  "outputs",
  "overlap",
  "pairwise",
  "parser",
  "parsers",
  "pipeline",
  "pipelines",
  "pointwise",
  "prompt",
  "prompting",
  "prompts",
  "ranker",
  "rerank",
  "reranked",
  "reranker",
  "rerankers",
  "reranking",
  "retrieval",
  "retrievals",
  "retriever",
  "retrievers",
  "sampling",
  "screening",
  "splitter",
  "splitters",
  "stack",
  "standby",
  "tenant",
  "token",
  "tokenization",
  "tokenizer",
  "tokenizers",
  "tokens",
  "watermark",
  "watermarks",
  "watermarking",
  "workflow",
  "workflows",
];

// ---------- Définitions FR pour le glossaire ----------
// (clé = forme canonique en minuscule sans tirets pour matcher les variantes)
// Définitions concises, ciblées RAG / IR / NLP.
const DEFS = {
  "agentic": "Qualifie un système d'IA capable d'agir de façon autonome en enchaînant plusieurs actions (recherches, appels d'outils, raisonnements) pour atteindre un objectif.",
  "Approximate Nearest Neighbor": "Recherche du plus proche voisin approximatif : famille d'algorithmes (HNSW, IVF, PQ…) qui accélèrent la recherche vectorielle au prix d'une légère approximation.",
  "anisotropic embeddings": "Embeddings dits « anisotropes » dont les vecteurs se concentrent dans un cône étroit de l'espace, ce qui dégrade la séparation par similarité cosinus.",
  "answer relevance": "Pertinence de la réponse : mesure à quel point la réponse générée traite effectivement la question posée (métrique RAGAS).",
  "answer relevancy": "Synonyme d'*answer relevance*.",
  "audit trail": "Piste d'audit : trace complète et vérifiable des étapes ayant conduit à une réponse (passages récupérés, prompt, modèle, paramètres).",
  "backend": "Partie serveur d'une application (logique métier, accès aux données), par opposition au *frontend*.",
  "baseline": "Configuration de référence à laquelle on compare des variantes pour mesurer un gain ou une perte.",
  "batching": "Regroupement de plusieurs requêtes ou éléments en un seul lot pour améliorer le débit (souvent au prix de la latence individuelle).",
  "benchmark": "Jeu de données et protocole standardisés permettant de comparer des systèmes ou des modèles sur une tâche donnée.",
  "benchmarking": "Action de comparer systématiquement plusieurs systèmes ou configurations sur un *benchmark*.",
  "case-sensitive": "Sensible à la casse : qui distingue majuscules et minuscules.",
  "chatbot": "Agent conversationnel textuel.",
  "chunk": "Segment de texte issu du découpage d'un document, unité de base indexée et récupérée dans un système RAG.",
  "chunker": "Composant logiciel qui réalise le découpage en *chunks*.",
  "chunking": "Étape de découpage des documents en segments (*chunks*) avant indexation.",
  "citation completeness": "Complétude des citations : toutes les affirmations qui devraient être sourcées le sont-elles ?",
  "citation correctness": "Correction des citations : les passages cités existent-ils et soutiennent-ils réellement l'affirmation ?",
  "citation faithfulness": "Fidélité de la citation : le passage cité supporte-t-il bien l'affirmation à laquelle il est rattaché ?",
  "cluster": "Groupe d'éléments homogènes obtenus par regroupement automatique (*clustering*).",
  "clustering": "Regroupement non supervisé d'éléments similaires en classes (*clusters*).",
  "code-switching": "Alternance codique : passage spontané d'une langue à l'autre au sein d'un même énoncé (ici, français ↔ anglais dans les requêtes).",
  "context precision": "Précision du contexte : proportion des passages récupérés qui sont effectivement pertinents (métrique RAGAS).",
  "context recall": "Rappel du contexte : proportion de l'information de référence couverte par les passages récupérés (métrique RAGAS).",
  "context relevance": "Pertinence du contexte : mesure de l'utilité globale des passages récupérés pour répondre à la question.",
  "cross-encoder": "Encodeur croisé : modèle qui prend simultanément la requête et le passage en entrée pour produire un score de pertinence fin (utilisé en *reranking*).",
  "custom": "Personnalisé, sur mesure (par opposition à une solution générique « prête à l'emploi »).",
  "dataset": "Jeu de données structuré utilisé pour entraîner ou évaluer un modèle.",
  "dense retrieval": "Recherche dense : récupération de passages via similarité entre embeddings denses de la requête et des documents.",
  "drift": "Dérive : écart progressif entre la distribution des données vues à l'entraînement et celles vues en production, ou décalage sémantique introduit par une reformulation.",
  "dual-encoder": "Architecture à deux encodeurs (souvent identiques) qui encodent séparément requête et passage avant comparaison ; synonyme de *bi-encodeur*.",
  "embedder": "Modèle qui produit des *embeddings*.",
  "embedding": "Représentation vectorielle dense d'un mot, d'une phrase ou d'un document dans un espace continu.",
  "end-to-end": "Bout en bout : qui couvre l'intégralité de la chaîne, de l'entrée brute jusqu'au résultat final.",
  "endpoint": "Point d'accès réseau (URL) exposant une API.",
  "exact match": "Correspondance exacte : la réponse générée doit être strictement identique à la référence.",
  "faithfulness": "Fidélité : propriété d'une réponse dont toutes les propositions sont effectivement supportées par les passages fournis.",
  "few-shot": "Apprentissage à partir de quelques exemples seulement fournis dans le *prompt*.",
  "fine-tuning": "Affinage : adaptation d'un modèle pré-entraîné à une tâche ou un domaine spécifique via un entraînement supplémentaire.",
  "fine-tune": "Affiner (un modèle) sur des données spécifiques (verbe) ; cf. *fine-tuning*.",
  "fine-tunable": "Qui peut faire l'objet d'un *fine-tuning*.",
  "flip rate": "Taux de bascule : proportion de cas où, d'une exécution à l'autre, le verdict (bon/mauvais, supporté/non supporté…) change.",
  "framework": "Cadriciel : ensemble cohérent d'outils et de conventions facilitant le développement (ex. LangChain, LlamaIndex).",
  "frontend": "Partie cliente d'une application (interface utilisateur), par opposition au *backend*.",
  "GAP analysis": "Analyse d'écart : identification de la différence entre un état actuel et un état cible attendu.",
  "gold standard": "Référence absolue : annotation considérée comme la vérité de terrain pour évaluer un système.",
  "GraphRAG": "Variante de RAG s'appuyant sur un graphe de connaissances pour structurer la récupération et l'agrégation d'information.",
  "groundedness": "Ancrage : degré auquel une réponse est effectivement justifiée par les sources fournies ; proche de *faithfulness*.",
  "grounding": "Ancrage explicite d'une génération sur des sources externes vérifiables.",
  "grounding explicite": "Consigne explicite donnée au LLM de ne répondre que sur la base des extraits fournis.",
  "hallucinate": "Halluciner : produire une affirmation plausible mais non supportée par les sources (ou fausse).",
  "hard negatives": "Exemples négatifs difficiles : passages superficiellement proches d'un positif mais incorrects, utilisés pour entraîner des modèles de retrieval plus discriminants.",
  "hard match": "Correspondance stricte (souvent lexicale et exacte).",
  "Hit rate": "Taux de présence d'au moins un passage pertinent dans le top-k retourné.",
  "hit ratio": "Synonyme de *Hit rate*.",
  "hub": "Plateforme centralisée de partage de modèles ou de jeux de données (ex. Hugging Face Hub).",
  "human-in-the-loop": "Humain dans la boucle : protocole où un opérateur humain valide ou corrige les sorties du système.",
  "Hypothetical Document Embeddings": "HyDE : technique consistant à faire générer par un LLM une réponse hypothétique à la requête, puis à utiliser son embedding pour la recherche.",
  "in-context learning": "Apprentissage en contexte : capacité d'un LLM à généraliser à partir d'exemples fournis dans le *prompt*, sans mise à jour des poids.",
  "inline": "En ligne : intégré directement dans le flux (ex. citation insérée dans le texte de la réponse).",
  "input": "Entrée d'un système.",
  "instruction tuning": "Affinage par instructions : étape d'entraînement où un modèle est appris à suivre des instructions formulées en langage naturel.",
  "inverse document frequency": "Fréquence inverse de document : composante d'IDF qui pondère la rareté d'un terme dans la collection.",
  "knowledge base": "Base de connaissances structurée.",
  "knowledge cutoff": "Date de coupure : date au-delà de laquelle un LLM n'a pas vu de données pendant son entraînement.",
  "knowledge distillation": "Distillation de connaissances : entraînement d'un modèle plus petit (élève) à imiter un modèle plus gros (maître).",
  "knowledge graph": "Graphe de connaissances : représentation structurée d'entités et de leurs relations.",
  "late interaction": "Interaction tardive : famille d'architectures (ex. ColBERT) qui combinent l'efficacité d'un *bi-encodeur* avec des interactions fines au niveau des tokens.",
  "leaderboard": "Classement public comparant les performances de différents modèles sur un *benchmark*.",
  "learning-to-rank": "Apprentissage d'ordonnancement : famille de méthodes apprenant à classer des documents par pertinence à partir de données annotées.",
  "listwise": "Approche d'apprentissage d'ordonnancement opérant sur des listes entières de candidats.",
  "LLM-as-judge": "LLM utilisé comme évaluateur automatique pour noter d'autres réponses selon une grille.",
  "LLM-as-a-judge": "Synonyme de *LLM-as-judge*.",
  "LLM-juge": "Forme francisée de *LLM-as-judge*.",
  "loader": "Chargeur : composant qui lit des données depuis une source et les rend exploitables.",
  "logger": "Composant logiciel qui enregistre des événements ou des métriques d'exécution.",
  "lost in the middle": "Phénomène par lequel un LLM exploite moins bien les passages situés au milieu d'un long contexte qu'en début ou en fin.",
  "machine-vérifiable": "Vérifiable automatiquement par une machine, sans intervention humaine.",
  "mapping": "Correspondance : table reliant des éléments d'un ensemble à ceux d'un autre.",
  "Massive Text Embedding Benchmark": "MTEB : *benchmark* de référence couvrant de nombreuses tâches d'évaluation des modèles d'embedding.",
  "Matryoshka Representation Learning": "Famille d'embeddings dont les premières dimensions portent déjà l'essentiel de l'information, permettant une troncature *a posteriori*.",
  "Mean Reciprocal Rank": "Rang réciproque moyen (MRR) : moyenne des inverses du rang du premier document pertinent.",
  "Memex": "Concept de bibliothèque mécanisée d'accès à l'information imaginé par Vannevar Bush en 1945, ancêtre conceptuel des hypertextes.",
  "mining": "Fouille (de données, de textes) : extraction automatique de motifs ou d'informations.",
  "multi-query": "Stratégie consistant à reformuler la requête en plusieurs variantes pour augmenter le rappel du retrieval.",
  "multi-stage": "Architecture en plusieurs étages (ex. retrieval large, puis *reranking* fin, puis génération).",
  "One-Factor-At-a-Time": "OFAT : protocole expérimental consistant à ne faire varier qu'un seul paramètre à la fois, toutes choses égales par ailleurs.",
  "open source": "À code source ouvert.",
  "open-source": "À code source ouvert.",
  "open weights": "Modèles dont les poids sont publiquement téléchargeables (mais pas nécessairement reproductibles).",
  "open-weights": "Idem *open weights*.",
  "output": "Sortie d'un système.",
  "overlap": "Recouvrement : portion de texte commune entre deux *chunks* consécutifs, qui amortit les coupures.",
  "pairwise": "Approche d'apprentissage d'ordonnancement opérant sur des paires de candidats.",
  "parent-document retrieval": "Récupération du document parent : on indexe des petits *chunks* mais on retourne au LLM le passage parent plus large.",
  "parser": "Analyseur syntaxique : composant qui transforme une entrée brute en structure exploitable.",
  "passage embeddings": "Embeddings de passages : représentations vectorielles de segments de texte plus longs qu'une phrase.",
  "pipeline": "Chaîne de traitement composée d'étapes successives.",
  "pointwise": "Approche d'apprentissage d'ordonnancement opérant indépendamment sur chaque candidat.",
  "pre-training": "Pré-entraînement : phase d'entraînement initiale d'un modèle sur de grandes quantités de données génériques.",
  "pretraining": "Idem *pre-training*.",
  "prompt": "Instruction ou message fourni en entrée à un LLM pour orienter sa génération.",
  "prompt engineering": "Ingénierie de *prompt* : conception et optimisation des instructions données à un LLM.",
  "prompting": "Action de formuler un *prompt*.",
  "Proof of Concept": "POC : démonstration de faisabilité d'un concept, sans engagement de mise en production.",
  "query expansion": "Expansion de requête : enrichissement automatique de la requête par des termes liés (synonymes, paraphrases).",
  "query likelihood": "Modèle probabiliste estimant la vraisemblance que la requête ait été générée par un document.",
  "query rewriting": "Réécriture de requête par un modèle (correction, normalisation, reformulation).",
  "ranker": "Composant qui classe une liste de candidats par pertinence.",
  "Reciprocal Rank": "Rang réciproque : inverse du rang du premier résultat pertinent.",
  "Reciprocal Rank Fusion": "RRF : méthode robuste de fusion de plusieurs classements via la somme des inverses des rangs.",
  "recursive character text splitter": "Découpeur de texte récursif qui essaie d'abord des séparateurs « forts » (paragraphes, phrases) avant de couper plus finement.",
  "rerank": "Reclasser une liste de candidats avec un modèle plus précis.",
  "reranker": "Composant qui effectue le *reranking* (souvent un *cross-encoder*).",
  "reranking": "Reclassement d'un petit ensemble de candidats par un modèle plus précis (et plus coûteux) que le retriever initial.",
  "relevance feedback": "Rétroaction de pertinence : reformulation de la requête à partir d'un sous-ensemble de documents jugés pertinents par l'utilisateur ou le système.",
  "retrieval": "Récupération : phase consistant à retrouver, dans un index, les passages pertinents pour une requête.",
  "retriever": "Composant chargé du *retrieval*.",
  "sampling": "Échantillonnage : sélection d'un sous-ensemble représentatif d'une population.",
  "screening": "Tri préliminaire : présélection rapide de candidats avant analyse plus poussée.",
  "sentence embeddings": "Embeddings de phrases : représentation vectorielle d'une phrase entière (ex. Sentence-BERT).",
  "siamese networks": "Réseaux siamois : architecture à deux branches partageant les mêmes poids, utilisée pour apprendre des similarités.",
  "sparse retrieval": "Recherche creuse : récupération fondée sur des représentations à très haute dimension et majoritairement nulles (BM25, TF-IDF).",
  "splitter": "Découpeur : composant qui segmente un texte en *chunks*.",
  "stack": "Pile technologique : ensemble des outils, bibliothèques et services utilisés dans un projet.",
  "standby": "En attente : état d'un composant prêt à prendre le relais.",
  "step-back prompting": "Stratégie consistant à reformuler la question en une question plus générale avant la recherche, pour mieux ancrer la réponse.",
  "tenant": "Locataire : isolement logique d'un client dans une infrastructure mutualisée (ex. *tenant* Azure).",
  "term frequency": "Fréquence d'un terme dans un document, composante de TF-IDF.",
  "term specificity": "Spécificité d'un terme : capacité d'un mot à discriminer les documents pertinents.",
  "text splitter": "Composant qui découpe un texte en *chunks*.",
  "time-consuming": "Chronophage.",
  "token": "Unité élémentaire de texte manipulée par un LLM (mot, sous-mot ou caractère selon le *tokenizer*).",
  "tokenization": "Découpage d'un texte en *tokens*.",
  "tokenizer": "Composant qui transforme une chaîne de caractères en suite de *tokens*.",
  "top-k": "Les $k$ premiers résultats d'un classement (ex. top-5 passages récupérés).",
  "top-n": "Les $n$ premiers résultats d'un classement.",
  "top-p": "Échantillonnage *top-p* (ou *nucleus sampling*) : limite la génération aux *tokens* dont la masse de probabilité cumulée atteint $p$.",
  "vector store": "Base de données vectorielle indexant des embeddings et supportant la recherche par similarité.",
  "Vision Language Model": "VLM : modèle multimodal qui traite conjointement images et texte.",
  "watermark": "Filigrane : signal discret inséré dans une sortie pour en tracer l'origine.",
  "watermarking": "Insertion de filigranes (*watermarks*) dans des sorties générées.",
  "workflow": "Flux de travail : séquence d'étapes coordonnées composant un processus.",
  "zero-shot": "Sans aucun exemple : capacité d'un modèle à réaliser une tâche qu'il n'a jamais explicitement vue à l'entraînement.",
};

// ---------- Lecture ----------
if (!existsSync(BACKUP)) {
  copyFileSync(SRC, BACKUP);
  console.log(`Backup créé : ${BACKUP}`);
}
let text = readFileSync(SRC, "utf8");

// ---------- Protection des zones sensibles ----------
// On remplace chaque zone protégée par un token unique \u0000PROT\u0000<id>\u0000
const protectedZones = [];
function protect(match) {
  const id = protectedZones.length;
  protectedZones.push(match);
  return `\u0000PROT${id}PROT\u0000`;
}

// Ordre important : blocs de code d'abord (peuvent contenir des $ et `).
text = text.replace(/```[\s\S]*?```/g, protect);   // fenced code
text = text.replace(/`[^`\n]+`/g, protect);         // inline code
text = text.replace(/\$\$[\s\S]*?\$\$/g, protect); // display math
// inline math : $...$ sans saut de ligne, attention aux $ isolés.
text = text.replace(/\$[^$\n]+?\$/g, protect);
// citations Pandoc : [@xxx], [@xxx; @yyy, p. 12]
text = text.replace(/\[@[^\]]+\]/g, protect);
// images ![alt](url)
text = text.replace(/!\[[^\]]*\]\([^)]+\)/g, protect);
// liens markdown [texte](url) — on protège tout (texte + url) pour éviter
// d'italiciser dans des libellés type [results/x.csv](results/x.csv).
text = text.replace(/\[[^\]]+\]\([^)]+\)/g, protect);
// blocs Pandoc :::
text = text.replace(/^:::[^\n]*$/gm, protect);
// raw LaTeX : \newpage etc.
text = text.replace(/\\newpage/g, protect);

// ---------- Construction des regex pour les termes ----------
// Frontière de mot personnalisée : on s'assure que le caractère adjacent
// n'est pas alphanumérique ni un tiret (pour les termes hyphénés gérés explicitement).
function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Pour gérer les variantes de casse, on construit la regex avec la casse exacte
// du terme. Les premières lettres deviennent insensibles à la casse (pour
// attraper "Chunk" en début de phrase et "chunk" ailleurs). On garde la casse
// trouvée dans le texte (groupe capturant).
function makeWordRegex(term) {
  // Caractère limite à gauche : début, espace, ponctuation, parenthèse… mais
  // pas une lettre, un chiffre, un astérisque (déjà italique/gras) ou un tiret
  // (pour ne pas casser "cross-encoder" en cherchant "encoder").
  // À droite : même chose, plus pas un astérisque ni un tiret.
  // On utilise des lookbehind/lookahead.
  const escaped = escapeRegex(term);
  // Si le terme contient déjà des caractères non-alphanumériques (espace, tiret),
  // on n'a pas besoin d'imposer une frontière "mot" pure.
  return new RegExp(
    `(?<![A-Za-zÀ-ÿ0-9*\\-_])(${escaped})(?![A-Za-zÀ-ÿ0-9*\\-_])`,
    "gi"
  );
}

// Regex pour la variante **term**
function makeBoldRegex(term) {
  const escaped = escapeRegex(term);
  return new RegExp(`\\*\\*(${escaped})\\*\\*`, "gi");
}

// ---------- Application des remplacements ----------
const counts = new Map(); // pour le glossaire : terme canonique -> nombre de remplacements
const seen = new Set(); // termes ayant au moins un match (forme canonique)

for (const term of TERMS) {
  const boldRe = makeBoldRegex(term);
  const wordRe = makeWordRegex(term);

  let nBold = 0;
  let nPlain = 0;

  // 1) **term** -> ***term***
  text = text.replace(boldRe, (_m, g1) => {
    nBold++;
    return `***${g1}***`;
  });

  // 2) bare term -> *term* (lookarounds empêchent déjà de toucher *term*)
  text = text.replace(wordRe, (_m, g1) => {
    nPlain++;
    return `*${g1}*`;
  });

  const total = nBold + nPlain;
  if (total > 0) {
    counts.set(term, total);
    seen.add(term);
  }
}

// ---------- Restauration des zones protégées ----------
text = text.replace(/\u0000PROT(\d+)PROT\u0000/g, (_m, id) => {
  return protectedZones[parseInt(id, 10)];
});

// ---------- Construction du glossaire ----------
// On retient une seule entrée canonique par concept (on évite les doublons
// pluriel/singulier en n'incluant que les formes qui ont une définition dans DEFS).
const glossaryKeys = new Set();
for (const term of seen) {
  if (DEFS[term]) {
    glossaryKeys.add(term);
  } else {
    // Essayer la forme singulier (retirer un s final)
    if (term.endsWith("s") && DEFS[term.slice(0, -1)]) {
      glossaryKeys.add(term.slice(0, -1));
    } else if (DEFS[term.toLowerCase()]) {
      glossaryKeys.add(term.toLowerCase());
    }
  }
}

// Tri alphabétique insensible à la casse / aux accents.
const sortedKeys = [...glossaryKeys].sort((a, b) =>
  a.localeCompare(b, "fr", { sensitivity: "base" })
);

const glossaryLines = ["", "## Glossaire des termes anglais", ""];
glossaryLines.push(
  "Ce glossaire reprend les termes anglais (mots et expressions) employés dans le mémoire et italicisés dans le texte. Les acronymes (RAG, LLM, BM25, GPT, API, MRR, nDCG, etc.) sont définis directement lors de leur première occurrence dans le corps du texte."
);
glossaryLines.push("");
for (const k of sortedKeys) {
  glossaryLines.push(`- ***${k}*** : ${DEFS[k]}`);
}
glossaryLines.push("");
const glossary = glossaryLines.join("\n");

// ---------- Insertion du glossaire AVANT "## Bibliographie" ----------
const bibMarker = "## Bibliographie";
if (text.includes(bibMarker)) {
  text = text.replace(bibMarker, glossary + "\n" + bibMarker);
} else {
  // fallback : ajouter à la fin
  text = text + "\n" + glossary;
}

// ---------- Écriture ----------
writeFileSync(SRC, text, "utf8");

// ---------- Rapport ----------
console.log(`\n=== Rapport ===`);
console.log(`Termes traités : ${TERMS.length}`);
console.log(`Termes avec au moins 1 occurrence : ${seen.size}`);
console.log(`Entrées du glossaire : ${sortedKeys.length}`);
console.log(`\nTop 30 termes par nombre de remplacements :`);
const sortedCounts = [...counts.entries()].sort((a, b) => b[1] - a[1]);
for (const [t, n] of sortedCounts.slice(0, 30)) {
  console.log(`  ${n.toString().padStart(4)} × ${t}`);
}
console.log(`\nFichier écrit : ${SRC}`);
console.log(`Backup disponible : ${BACKUP}`);
