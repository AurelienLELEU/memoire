#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_crossrefs.py — ajoute :
  1. des ancres sur les Parties, Chapitres, Sections, Annexes et entrées de glossaire ;
  2. des liens (Pandoc Markdown) sur tous les renvois "Ch. N", "Chapitre N",
     "Partie I/II/III", "§ N.M(.K)", "Annexe A-D" dans le corps du texte ;
  3. des liens vers le glossaire sur chaque terme anglais italicisé reconnu.

Le script préserve les blocs de code, le code inline, les blocs raw LaTeX
``{=latex}``, les blocs HTML / Pandoc divs et le bloc bibliographie. Il ne
modifie ni les titres, ni le glossaire lui-même (en dehors de l'ajout d'ancres).

Usage :
    python scripts/add_crossrefs.py
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "memoire_complet.md"
BACKUP = ROOT / "memoire_complet.precrossrefs.backup.md"

# ---------------------------------------------------------------------------
# 1. Glossaire : map "forme rencontrée" -> "id ancre glossaire".
#    L'id est dérivé de la forme canonique en minuscule, dé-accentuée,
#    espaces/slashs/tirets normalisés en tirets simples.
# ---------------------------------------------------------------------------

def slug(text: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


# Les entrées canoniques sont celles qui figurent dans Annexe D (en lecture du fichier).
# Pour chacune, on génère un id "gloss-<slug>". On enregistre aussi les variantes
# (singulier/pluriel, formes dérivées) qui pointent vers le même id.
#
# Chaque tuple est (forme_de_reference_canonique, [variantes_qui_pointent_vers_le_meme_id])
GLOSSARY_VARIANTS: list[tuple[str, list[str]]] = [
    ("Advanced RAG", ["Advanced RAG"]),
    ("agentic", ["agentic"]),
    ("answer relevance", ["answer relevance", "answer relevancy"]),
    ("Approximate Nearest Neighbor", ["Approximate Nearest Neighbor"]),
    ("audit trail", ["audit trail", "Audit trail"]),
    ("backend", ["backend"]),
    ("baseline", ["baseline", "baselines"]),
    ("batching", ["batching"]),
    ("benchmark", ["benchmark", "benchmarks", "benchmarker", "benchmarking", "benchmarkées", "benchmarké", "benchmarkés", "benchmarkée"]),
    ("chatbot", ["chatbot", "chatbots"]),
    ("chunk", ["chunk", "chunks"]),
    ("chunker", ["chunker", "chunkers"]),
    ("chunking", ["chunking", "chunkings"]),
    ("citation completeness", ["citation completeness"]),
    ("citation correctness", ["citation correctness"]),
    ("citation faithfulness", ["citation faithfulness"]),
    ("cluster", ["cluster", "clusters"]),
    ("clustering", ["clustering"]),
    ("code-switching", ["code-switching"]),
    ("context precision", ["context precision", "Context Precision"]),
    ("context recall", ["context recall", "Context Recall"]),
    ("context relevance", ["context relevance"]),
    ("cross-encoder", ["cross-encoder", "cross-encoders"]),
    ("custom", ["custom"]),
    ("dense retrieval", ["dense retrieval"]),
    ("dual-encoder", ["dual-encoder"]),
    ("embedding", ["embedding", "embeddings"]),
    ("end-to-end", ["end-to-end"]),
    ("endpoint", ["endpoint", "endpoints"]),
    ("exact match", ["exact match"]),
    ("faithfulness", ["faithfulness", "Faithfulness"]),
    ("few-shot", ["few-shot"]),
    ("fine-tuning", ["fine-tuning", "fine-tune", "fine-tuned", "fine-tunes", "fine-tunable", "fine-tunabilité"]),
    ("flip rate", ["flip rate"]),
    ("framework", ["framework", "frameworks"]),
    ("frontend", ["frontend"]),
    ("gap analysis", ["gap analysis", "GAP analysis"]),
    ("gold standard", ["gold standard"]),
    ("GraphRAG", ["GraphRAG"]),
    ("grounding", ["grounding", "grounding explicite"]),
    ("groundedness", ["groundedness"]),
    ("hard negatives", ["hard negatives"]),
    ("human-in-the-loop", ["human-in-the-loop"]),
    ("inline", ["inline"]),
    ("late interaction", ["late interaction", "late-interaction"]),
    ("leaderboards", ["leaderboards", "leaderboard"]),
    ("learning-to-rank", ["learning-to-rank"]),
    ("listwise", ["listwise"]),
    ("LLM-as-judge", ["LLM-as-judge", "LLM-as-a-judge", "LLM-juge"]),
    ("loader", ["loader", "loaders"]),
    ("logger", ["logger", "loggers"]),
    ("lost in the middle", ["lost in the middle"]),
    ("machine-vérifiable", ["machine-vérifiable"]),
    ("mapping", ["mapping"]),
    ("Massive Text Embedding Benchmark", ["Massive Text Embedding Benchmark"]),
    ("Matryoshka Representation Learning", ["Matryoshka Representation Learning"]),
    ("max tokens", ["max tokens"]),
    ("Mean Reciprocal Rank", ["Mean Reciprocal Rank"]),
    ("Memex", ["Memex"]),
    ("multi-query", ["multi-query"]),
    ("multi-stage", ["multi-stage"]),
    ("One-Factor-At-a-Time", ["One-Factor-At-a-Time"]),
    ("open-source", ["open-source", "open source", "open-weights", "open weights"]),
    ("output", ["output", "outputs"]),
    ("overlap", ["overlap"]),
    ("pairwise", ["pairwise"]),
    ("parent-document retrieval", ["parent-document retrieval"]),
    ("parser", ["parser", "parsers"]),
    ("pipeline", ["pipeline", "pipelines"]),
    ("pointwise", ["pointwise"]),
    ("prompt", ["prompt", "prompts", "prompting"]),
    ("query expansion", ["query expansion"]),
    ("query likelihood", ["query likelihood"]),
    ("query rewriting", ["query rewriting"]),
    ("Reciprocal Rank Fusion", ["Reciprocal Rank Fusion"]),
    ("recursive splitter", ["recursive splitter", "recursive character text splitter"]),
    ("relevance feedback", ["relevance feedback"]),
    ("reranker", ["reranker", "rerankers", "ranker"]),
    ("reranking", ["reranking", "rerank", "reranked"]),
    ("retrieval", ["retrieval", "retrievals"]),
    ("retriever", ["retriever", "retrievers"]),
    ("retriever-reader", ["retriever-reader"]),
    ("screening", ["screening"]),
    ("seed", ["seed"]),
    ("siamese networks", ["siamese networks"]),
    ("sparse retrieval", ["sparse retrieval"]),
    ("splitter", ["splitter", "splitters"]),
    ("stack", ["stack", "Stack"]),
    ("step-back prompting", ["step-back prompting"]),
    ("tenant", ["tenant"]),
    ("term specificity", ["term specificity"]),
    ("time-consuming", ["time-consuming"]),
    ("token", ["token", "tokens"]),
    ("tokenizer", ["tokenizer", "tokenizers"]),
    ("top-k", ["top-k"]),
    ("top-p", ["top-p"]),
    ("Vision Language Model", ["Vision Language Model"]),
    ("watermark", ["watermark", "watermarks", "watermarking"]),
    ("workflow", ["workflow", "workflows"]),
    # Termes mentionnés en italique dans la prose mais non listés dans le glossaire :
    # on ne crée PAS de lien vers le glossaire pour ces termes (cf. Answer Relevancy
    # est traité au-dessus, etc.). Si un terme italicisé n'a pas de glossaire, il
    # restera en italique simple.
]


def build_glossary_map() -> tuple[dict[str, str], dict[str, str]]:
    """Retourne (variants_to_id, canon_to_id)."""
    canon_to_id: dict[str, str] = {}
    variants_to_id: dict[str, str] = {}
    for canon, variants in GLOSSARY_VARIANTS:
        anchor_id = "gloss-" + slug(canon)
        canon_to_id[canon] = anchor_id
        for v in variants:
            # On indexe sur la forme minuscule pour matcher de façon
            # case-insensitive ; la forme d'origine sera préservée à l'écriture.
            variants_to_id[v.lower()] = anchor_id
    return variants_to_id, canon_to_id


# ---------------------------------------------------------------------------
# 2. Découpage du document en segments protégés / éditables
#    On reconnaît :
#      - fences ``` ... ``` (avec attributs {=latex} ou autre)
#      - blocs Pandoc ::: ... :::
#      - code inline `...`
#      - math display $$...$$ et inline $...$
#      - liens Markdown [texte](url) et images ![alt](url){#fig:...}
#      - citations Pandoc [@xxx; @yyy]
#      - balises raw LaTeX et HTML inline (cf. ~\ etc.)
# ---------------------------------------------------------------------------

FENCE_RE = re.compile(r"^```")


def split_into_blocks(text: str) -> list[tuple[str, str]]:
    """
    Découpe en (kind, content) où kind est :
      - 'fence' : bloc ``` ... ``` (intact, jamais modifié)
      - 'glossary' : la section Annexe D (modifiée pour ajouter ancres mais pas pour ajouter liens)
      - 'biblio' : la section Bibliographie + le bloc ::: refs (jamais modifié)
      - 'heading' : ligne de titre (ajout d'id explicite uniquement, pas de liens dedans)
      - 'text' : texte normal (modifié pour ajouter liens)
    """
    lines = text.split("\n")
    blocks: list[tuple[str, str]] = []
    i = 0
    n = len(lines)

    in_glossary = False
    in_biblio = False

    cur_kind = "text"
    cur: list[str] = []

    def flush(kind_override: str | None = None) -> None:
        nonlocal cur
        if cur:
            blocks.append((kind_override or cur_kind, "\n".join(cur)))
            cur = []

    while i < n:
        line = lines[i]

        # Détection début/fin du glossaire (Annexe D)
        if re.match(r"^## Annexe D : ", line):
            flush()
            in_glossary = True
            in_biblio = False
            cur_kind = "glossary"
            cur.append(line)
            i += 1
            continue

        # Détection bibliographie : `# Bibliographie {-}` jusqu'à `# Annexes {-}`
        if re.match(r"^# Bibliographie", line):
            flush()
            in_biblio = True
            in_glossary = False
            cur_kind = "biblio"
            cur.append(line)
            i += 1
            continue
        if in_biblio and re.match(r"^# Annexes", line):
            # Fin de la bibliographie : flush et repartir en text
            flush()
            in_biblio = False
            cur_kind = "text"
            cur.append(line)
            i += 1
            continue

        # Détection d'un fence ```
        m = FENCE_RE.match(line)
        if m:
            flush()
            fence_lines = [line]
            i += 1
            while i < n and not FENCE_RE.match(lines[i]):
                fence_lines.append(lines[i])
                i += 1
            if i < n:
                fence_lines.append(lines[i])
                i += 1
            blocks.append(("fence", "\n".join(fence_lines)))
            continue

        # Headings (## et plus) : on les sort en blocs séparés pour pouvoir
        # leur ajouter un id explicite sans modifier le contenu.
        if re.match(r"^#{1,6} ", line):
            flush()
            blocks.append(("heading", line))
            i += 1
            continue

        cur.append(line)
        i += 1

    flush()
    return blocks


# ---------------------------------------------------------------------------
# 3. Phase A : numérotation des chapitres / sections / sous-sections
#    et construction de la table heading_pos -> id.
#    Règles :
#      - On ignore les titres avec `{-}` (= non numérotés)
#      - `## ` = chapitre N
#      - `### ` = section N.M
#      - `#### ` = sous-section N.M.K
#    On ajoute en plus :
#      - les Annexes A-D : id "annexe-A" etc.
#      - les Parties : ids "partie-1/2/3" appliqués en post-traitement
#        au texte (au-dessus des Annexes, dans le corps).
# ---------------------------------------------------------------------------

class HeadingIndex:
    """Suit la numérotation et associe chaque titre à un id stable."""

    def __init__(self) -> None:
        self.ch = 0
        self.sec = 0
        self.sub = 0
        # Le numéro Pandoc d'une référence "Ch. N.M.K" -> son id
        self.refs: dict[str, str] = {}

    def visit(self, line: str) -> tuple[str, str | None]:
        """
        line : une ligne `## Title` / `### Title` / `#### Title` (ou avec {-}).
        Retourne (new_line, anchor_id_if_any).
        """
        # Skip s'il y a déjà un attribut {#...} explicite : pas de double-id.
        already_has_id = bool(re.search(r"\{#[^}]+\}", line))

        # Annexes : "## Annexe X : Titre {-}"
        m_annexe = re.match(r"^## Annexe ([A-D]) : (.+?)( \{-\})?$", line)
        if m_annexe:
            letter = m_annexe.group(1)
            anchor = f"annexe-{letter}"
            if already_has_id:
                return line, anchor
            tail = m_annexe.group(3) or ""
            new = f"## Annexe {letter} : {m_annexe.group(2)}{tail} {{#{anchor}}}"
            self.refs[f"annexe-{letter}"] = anchor
            return new, anchor

        # Titres avec {-} non-annexes (intro, conclusion, etc.) : on les laisse
        # tels quels — pas de référence chiffrée pointant dessus.
        if "{-}" in line:
            return line, None

        m2 = re.match(r"^## (.+)$", line)
        m3 = re.match(r"^### (.+)$", line)
        m4 = re.match(r"^#### (.+)$", line)

        if m2:
            self.ch += 1
            self.sec = 0
            self.sub = 0
            anchor = f"ch{self.ch}"
            self.refs[str(self.ch)] = anchor
            if already_has_id:
                return line, anchor
            return f"## {m2.group(1)} {{#{anchor}}}", anchor

        if m3:
            if self.ch == 0:
                # Section avant tout chapitre : on saute la numérotation.
                return line, None
            self.sec += 1
            self.sub = 0
            anchor = f"sec{self.ch}-{self.sec}"
            self.refs[f"{self.ch}.{self.sec}"] = anchor
            if already_has_id:
                return line, anchor
            return f"### {m3.group(1)} {{#{anchor}}}", anchor

        if m4:
            if self.ch == 0 or self.sec == 0:
                return line, None
            self.sub += 1
            anchor = f"sec{self.ch}-{self.sec}-{self.sub}"
            self.refs[f"{self.ch}.{self.sec}.{self.sub}"] = anchor
            if already_has_id:
                return line, anchor
            return f"#### {m4.group(1)} {{#{anchor}}}", anchor

        return line, None


# ---------------------------------------------------------------------------
# 4. Phase B : pose des ancres "[]{#partie-N}" dans le corps,
#    juste après chaque bloc raw LaTeX qui contient "{\Huge\bfseries PARTIE X}".
#    On suppose que ces ancres ne sont pas encore présentes.
# ---------------------------------------------------------------------------

PARTIE_LATEX_RE = re.compile(
    r"^```\{=latex\}\s*$(?P<body>.*?)^```\s*$",
    re.DOTALL | re.MULTILINE,
)

ROMAN_TO_INT = {"I": 1, "II": 2, "III": 3}


def annotate_partie_blocks(text: str) -> str:
    """Pour chaque bloc ```{=latex}``` contenant "PARTIE I/II/III", ajoute juste
    après une ligne `[]{#partie-N}`. Si l'ancre est déjà présente, on ne touche pas."""

    def repl(match: re.Match[str]) -> str:
        full = match.group(0)
        body = match.group("body")
        m = re.search(r"\\Huge\\bfseries PARTIE (I{1,3})\b", body)
        if not m:
            return full
        roman = m.group(1)
        n = ROMAN_TO_INT.get(roman)
        if n is None:
            return full
        # Si l'ancre existe déjà juste après le bloc, ne rien faire.
        return full  # ajout fait dans une passe ligne par ligne ci-dessous

    # On ne modifie pas via le regex (qui ne sait pas regarder après) : on procède
    # ligne par ligne.
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        out.append(line)
        # Détecte un bloc qui commence par ```{=latex}
        if line.strip() == "```{=latex}":
            # Avance jusqu'à la fermeture, en mémorisant le corps
            j = i + 1
            body_lines: list[str] = []
            while j < n and lines[j].strip() != "```":
                body_lines.append(lines[j])
                j += 1
            # Inclut la ligne de fermeture
            if j < n:
                out.extend(lines[i + 1 : j + 1])
                i = j + 1
            else:
                i = j
                continue
            body = "\n".join(body_lines)
            m = re.search(r"\\Huge\\bfseries PARTIE (I{1,3})\b", body)
            if m:
                roman = m.group(1)
                num = ROMAN_TO_INT.get(roman)
                if num:
                    anchor = f"partie-{num}"
                    # Si la ligne suivante (après la fermeture du bloc) n'est pas
                    # déjà l'ancre, on l'insère (précédée et suivie de lignes vides).
                    next_line = lines[i] if i < n else ""
                    if anchor not in next_line:
                        out.append("")
                        out.append(f"[]{{#{anchor}}}")
            continue
        i += 1
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 5. Phase C : application des ids sur les titres (chapitres / sections /
#    sous-sections / annexes) en parcourant tout le document, mais en
#    ignorant les fences et le glossaire pour la détection (elles sont
#    déjà séparées en blocs).
# ---------------------------------------------------------------------------

def apply_heading_ids(text: str) -> tuple[str, HeadingIndex]:
    blocks = split_into_blocks(text)
    idx = HeadingIndex()
    new_blocks: list[tuple[str, str]] = []
    for kind, content in blocks:
        if kind == "heading":
            new_line, _ = idx.visit(content)
            new_blocks.append((kind, new_line))
        else:
            new_blocks.append((kind, content))
    return "\n".join(c for _, c in new_blocks), idx


# ---------------------------------------------------------------------------
# 6. Phase D : ajout d'ancres dans le glossaire.
#    Chaque ligne "- *terme* : Definition" reçoit "- []{#gloss-<slug>}*terme* : ..."
#    Variantes ("- *a* (variantes : *b*) : ...") : on tagge sur la première forme.
# ---------------------------------------------------------------------------

GLOSSARY_ITEM_RE = re.compile(r"^(- )(\*+)([^*]+?)(\*+)(.*)$")


def annotate_glossary(text: str) -> str:
    blocks = split_into_blocks(text)
    out: list[tuple[str, str]] = []
    for kind, content in blocks:
        if kind != "glossary":
            out.append((kind, content))
            continue
        new_lines = []
        for line in content.split("\n"):
            m = GLOSSARY_ITEM_RE.match(line)
            if not m:
                new_lines.append(line)
                continue
            prefix, stars1, term, stars2, rest = m.groups()
            # Si l'ancre est déjà présente, on ne touche pas.
            if "{#gloss-" in line:
                new_lines.append(line)
                continue
            anchor = "gloss-" + slug(term)
            new_line = f"{prefix}[]{{#{anchor}}}{stars1}{term}{stars2}{rest}"
            new_lines.append(new_line)
        out.append((kind, "\n".join(new_lines)))
    return "\n".join(c for _, c in out)


# ---------------------------------------------------------------------------
# 7. Phase E : remplacement des références dans le corps du texte
#    (Ch. N(.M(.K)?)?, Chapitre N, § N.M(.K), Annexe A-D, Partie I/II/III).
#    On opère uniquement sur les blocs de type 'text' ; on protège en plus
#    le code inline `...` et les liens [..](..) existants.
# ---------------------------------------------------------------------------

# Protège tout ce qui ne doit pas être touché à l'intérieur d'un bloc 'text' :
PROTECT_PATTERNS = [
    (re.compile(r"`[^`\n]+`"), "inline_code"),
    (re.compile(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?"), "image"),
    (re.compile(r"\[[^\]]*\]\([^)]*\)"), "link"),
    (re.compile(r"\$\$[^$]+\$\$"), "math_block"),
    (re.compile(r"\$[^$\n]+\$"), "math_inline"),
    (re.compile(r"\[@[^\]]+\]"), "cite"),
]


def protect(text: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}
    counter = 0

    def store(s: str) -> str:
        nonlocal counter
        key = f"\x00PH{counter}\x00"
        counter += 1
        placeholders[key] = s
        return key

    out = text
    for pat, _ in PROTECT_PATTERNS:
        out = pat.sub(lambda m: store(m.group(0)), out)
    return out, placeholders


def restore(text: str, placeholders: dict[str, str]) -> str:
    out = text
    for key, val in placeholders.items():
        out = out.replace(key, val)
    return out


def replace_refs(text: str, idx: HeadingIndex) -> str:
    """Ajoute des liens Markdown sur les renvois.
    Ne touche pas le contenu déjà sous forme de lien (protégé en amont)."""

    # Helper qui renvoie l'id pour un numéro "N", "N.M", "N.M.K" si connu.
    def id_for_number(num: str) -> str | None:
        return idx.refs.get(num)

    # "Ch. N(.M(.K)?)?" — le point final n'est pas captif.
    def repl_ch_abbr(m: re.Match[str]) -> str:
        prefix = m.group("prefix")
        num = m.group("num")
        anchor = id_for_number(num)
        if not anchor:
            return m.group(0)
        # Le label visible inclut la forme exacte écrite par l'auteur.
        label = f"{prefix}{num}"
        return f"[{label}](#{anchor})"

    # "Ch. 7-8", "Ch. 5-6", "Ch. 8-9" (intervalle de chapitres) — DOIT
    # passer AVANT repl_ch_abbr, sinon le premier numéro est consommé seul.
    def repl_ch_range(m: re.Match[str]) -> str:
        a = int(m.group("a"))
        b = int(m.group("b"))
        ida = idx.refs.get(str(a))
        idb = idx.refs.get(str(b))
        if not (ida and idb):
            return m.group(0)
        return f"[Ch. {a}](#{ida})-[{b}](#{idb})"

    text = re.sub(
        r"\bCh\.\s(?P<a>\d+)-(?P<b>\d+)\b",
        repl_ch_range,
        text,
    )

    # On ne consomme PAS le caractère qui suit le numéro :
    # lookahead pour exclure ".X" supplémentaire (sinon on attraperait
    # "Ch. 4" dans "Ch. 4.3").
    text = re.sub(
        r"(?P<prefix>\bCh\.\s)(?P<num>\d+(?:\.\d+){0,2})(?!\.\d)(?!\w)",
        repl_ch_abbr,
        text,
    )

    # "Chapitre N(.M(.K)?)?"
    text = re.sub(
        r"(?P<prefix>\bChapitre\s)(?P<num>\d+(?:\.\d+){0,2})(?!\.\d)(?!\w)",
        repl_ch_abbr,
        text,
    )

    # "§ N.M-N.K" (intervalle de sections) — DOIT passer AVANT repl_para,
    # sinon le premier numéro est consommé seul.
    def repl_para_range(m: re.Match[str]) -> str:
        prefix = m.group("prefix")
        a = m.group("a")
        b = m.group("b")
        ida = id_for_number(a)
        idb = id_for_number(b)
        if not (ida and idb):
            return m.group(0)
        return f"[{prefix}{a}](#{ida})-[{b}](#{idb})"

    text = re.sub(
        r"(?P<prefix>§\s*)(?P<a>\d+\.\d+(?:\.\d+)?)-(?P<b>\d+\.\d+(?:\.\d+)?)\b",
        repl_para_range,
        text,
    )

    # "§ N.M(.K)?" — ici il faut au moins un point pour viser une section.
    def repl_para(m: re.Match[str]) -> str:
        prefix = m.group("prefix")
        num = m.group("num")
        anchor = id_for_number(num)
        if not anchor:
            return m.group(0)
        return f"[{prefix}{num}](#{anchor})"

    text = re.sub(
        r"(?P<prefix>§\s*)(?P<num>\d+\.\d+(?:\.\d+)?)(?!\.\d)(?!\w)",
        repl_para,
        text,
    )

    # "Annexe X" — X ∈ {A, B, C, D} (on évite "Annexe III" du règlement)
    def repl_annexe(m: re.Match[str]) -> str:
        letter = m.group("letter")
        anchor = idx.refs.get(f"annexe-{letter}")
        if not anchor:
            return m.group(0)
        return f"[Annexe {letter}](#{anchor})"

    text = re.sub(
        r"\bAnnexe\s(?P<letter>[ABCD])\b",
        repl_annexe,
        text,
    )

    # "Partie I/II/III" et "PARTIE I/II/III" (cas spéciaux : "Parties I et II")
    PART_MAP = {"I": 1, "II": 2, "III": 3}

    def repl_partie_single(m: re.Match[str]) -> str:
        prefix = m.group("prefix")
        roman = m.group("roman")
        n = PART_MAP.get(roman)
        if not n:
            return m.group(0)
        return f"[{prefix}{roman}](#partie-{n})"

    text = re.sub(
        r"(?P<prefix>\b(?:Partie|PARTIE)\s)(?P<roman>I{1,3})\b",
        repl_partie_single,
        text,
    )

    # "Parties I et II", "Parties I et III", "Parties II et III"
    def repl_parties_pair(m: re.Match[str]) -> str:
        r1 = m.group("r1")
        sep = m.group("sep")
        r2 = m.group("r2")
        n1 = PART_MAP.get(r1)
        n2 = PART_MAP.get(r2)
        if not (n1 and n2):
            return m.group(0)
        return f"[Parties {r1}](#partie-{n1}){sep}[{r2}](#partie-{n2})"

    text = re.sub(
        r"\bParties\s(?P<r1>I{1,3})(?P<sep>\set\s)(?P<r2>I{1,3})\b",
        repl_parties_pair,
        text,
    )

    return text


# ---------------------------------------------------------------------------
# 8. Phase F : remplacement des termes anglais italicisés par des liens vers
#    le glossaire.
#    On ne traite que les occurrences déjà *italiques* (*term* ou ***term***)
#    pour rester conservateur.
#    On ne touche pas aux entrées du glossaire lui-même.
# ---------------------------------------------------------------------------

def add_glossary_links(text: str, variants_to_id: dict[str, str]) -> str:
    """Cherche les occurrences ***term***, **term** (italique gras pandoc) et *term*
    dont le contenu (insensible à la casse) figure dans variants_to_id, et les
    transforme en [*term*](#gloss-...). Conserve l'emphase originale."""

    # Trie les variantes par longueur décroissante pour matcher d'abord les
    # expressions multi-mots.
    sorted_variants = sorted(variants_to_id.keys(), key=len, reverse=True)
    # Construit un regex case-insensitive qui matche n'importe quelle variante,
    # avec frontières mot pour les variantes purement alphabétiques.
    # On compose un regex "ITALICS" qui matche *...* ou ***...*** et capture
    # le contenu (sans les *).
    italics_re = re.compile(r"(?P<stars>\*{1,3})(?P<inner>[^*\n]+?)(?P=stars)")

    def is_already_linked(text: str, start: int) -> bool:
        # Si la chaîne immédiatement précédente se termine par "](" rien
        # qu'à inspecter le caractère qui suit après le bloc protégé.
        return False  # Les liens existants sont protégés en amont (PROTECT_PATTERNS).

    def repl(match: re.Match[str]) -> str:
        stars = match.group("stars")
        inner = match.group("inner")
        # On ne traite que les italiques *...* (1 étoile) et bold-italic ***...***
        # (3 étoiles). On laisse les **...** (gras pur) tranquilles.
        if len(stars) == 2:
            return match.group(0)
        # Si la portion entre les étoiles contient déjà un crochet ou un (,
        # c'est probablement un lien existant ou une construction complexe :
        # on s'abstient.
        if "[" in inner or "]" in inner or "(" in inner or ")" in inner:
            return match.group(0)
        key = inner.strip().lower()
        anchor = variants_to_id.get(key)
        if not anchor:
            return match.group(0)
        return f"[{stars}{inner}{stars}](#{anchor})"

    return italics_re.sub(repl, text)


# ---------------------------------------------------------------------------
# 9. Orchestration
# ---------------------------------------------------------------------------

def process(text: str) -> str:
    # 1. Pose des ancres sur les Parties (raw LaTeX)
    text = annotate_partie_blocks(text)
    # 2. Pose des ids sur les titres + construction de l'index
    text, idx = apply_heading_ids(text)
    # 3. Annotation du glossaire
    text = annotate_glossary(text)

    # 4. Application des liens dans les blocs 'text' uniquement.
    blocks = split_into_blocks(text)
    out_blocks: list[str] = []
    variants_to_id, _ = build_glossary_map()
    for kind, content in blocks:
        if kind != "text":
            out_blocks.append(content)
            continue
        protected, ph = protect(content)
        protected = replace_refs(protected, idx)
        protected = add_glossary_links(protected, variants_to_id)
        out_blocks.append(restore(protected, ph))
    return "\n".join(out_blocks)


def main() -> int:
    if not SRC.exists():
        print(f"Fichier introuvable : {SRC}", file=sys.stderr)
        return 1
    original = SRC.read_text(encoding="utf-8")
    if not BACKUP.exists():
        shutil.copy2(SRC, BACKUP)
        print(f"Backup écrit : {BACKUP.relative_to(ROOT)}")
    else:
        print(f"Backup existant conservé : {BACKUP.relative_to(ROOT)}")
    new_text = process(original)
    if new_text == original:
        print("Aucun changement appliqué.")
        return 0
    SRC.write_text(new_text, encoding="utf-8")
    # Compte rapide des changements
    added_links = new_text.count("](#") - original.count("](#")
    added_ids = new_text.count("{#") - original.count("{#")
    print(f"Ajouts : +{added_links} liens, +{added_ids} ancres.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
