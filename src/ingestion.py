"""
Ingestion PDF -> Markdown/texte avec préservation de la structure.
Sauvegarde dans data/extracted/{nom}.md + métadonnées JSON.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterator

import fitz  # pymupdf
from tqdm import tqdm

from src.config import INPUT_DIR, EXTRACTED_DIR


def detect_language(text: str) -> str:
    """Heuristique simple FR/EN basée sur stopwords fréquents."""
    sample = text[:5000].lower()
    fr_markers = sum(sample.count(w) for w in [" le ", " la ", " les ", " des ", " et ", " est ", " une ", " dans "])
    en_markers = sum(sample.count(w) for w in [" the ", " of ", " and ", " is ", " in ", " to ", " a ", " for "])
    return "fr" if fr_markers >= en_markers else "en"


def clean_text(text: str) -> str:
    """Nettoyage léger : espaces multiples, sauts de ligne excessifs."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_to_markdown(pdf_path: Path) -> tuple[str, dict]:
    """
    Extrait un PDF en markdown approximatif.
    PyMuPDF préserve mieux le layout que pypdf.
    """
    doc = fitz.open(pdf_path)
    parts: list[str] = []
    n_pages = len(doc)

    for page_idx, page in enumerate(doc):
        # blocs = (x0, y0, x1, y1, text, block_no, block_type)
        blocks = page.get_text("blocks")
        # tri haut->bas, gauche->droite
        blocks = sorted(blocks, key=lambda b: (round(b[1], 1), round(b[0], 1)))
        page_text = "\n\n".join(b[4].strip() for b in blocks if b[4].strip())

        # Détection grossière des titres : ligne courte en majuscules ou commençant par numéro
        lines = []
        for line in page_text.split("\n"):
            stripped = line.strip()
            if not stripped:
                lines.append("")
                continue
            is_short = len(stripped) < 80
            is_upper = stripped.isupper() and len(stripped) > 3
            is_numbered = bool(re.match(r"^(\d+(\.\d+)*\.?\s+|[A-Z]\.\s+|Chapitre|Section|Article|Article\s+\d)", stripped))
            if is_short and (is_upper or is_numbered):
                # niveau heuristique
                if re.match(r"^\d+\.\s", stripped):
                    lines.append(f"## {stripped}")
                elif re.match(r"^\d+\.\d+", stripped):
                    lines.append(f"### {stripped}")
                else:
                    lines.append(f"## {stripped}")
            else:
                lines.append(line)
        parts.append("\n".join(lines))

    full_text = clean_text("\n\n".join(parts))
    doc.close()

    metadata = {
        "filename": pdf_path.name,
        "n_pages": n_pages,
        "n_chars": len(full_text),
        "language": detect_language(full_text),
    }
    return full_text, metadata


def ingest_all(input_dir: Path = INPUT_DIR, output_dir: Path = EXTRACTED_DIR) -> list[dict]:
    """Parcourt input/, extrait chaque PDF, sauvegarde .md + meta.json."""
    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"⚠ Aucun PDF trouvé dans {input_dir}")
        return []

    manifest = []
    for pdf in tqdm(pdfs, desc="Ingestion PDFs"):
        try:
            text, meta = extract_pdf_to_markdown(pdf)
        except Exception as e:
            print(f"✗ Erreur sur {pdf.name}: {e}")
            continue

        out_md = output_dir / f"{pdf.stem}.md"
        out_meta = output_dir / f"{pdf.stem}.meta.json"
        out_md.write_text(text, encoding="utf-8")
        out_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append({"stem": pdf.stem, **meta})

    manifest_path = output_dir / "_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {len(manifest)} documents extraits dans {output_dir}")
    return manifest


def iter_documents(extracted_dir: Path = EXTRACTED_DIR) -> Iterator[tuple[str, str, dict]]:
    """Yield (doc_id, text, metadata) pour chaque .md extrait."""
    for md_file in sorted(extracted_dir.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        meta_file = md_file.with_suffix(".meta.json")
        meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
        yield md_file.stem, md_file.read_text(encoding="utf-8"), meta


if __name__ == "__main__":
    ingest_all()
