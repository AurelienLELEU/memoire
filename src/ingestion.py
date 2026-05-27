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


# Ground-truth language manifest (stem.lower() -> "fr"|"en").
# Généré depuis les métadonnées corpus – couvre tous les PDFs de input/.
_LANG_LOOKUP: dict[str, str] = {
    # ALIGN / PAS91 ----------------------------------------------------------------
    "2023 11 bytp cdm 2015 competence statement (002)": "en",
    "2025 07 29 spip action plan update": "en",
    "2025 09 01 september c1 sector shwelt": "en",
    "2025 10 first alert stay risk aware in the line of fire - align": "en",
    "2025 10 safety alert unexploded ordnance (uxo) - align": "en",
    "align jv a5 powb train booklet update mar 25": "en",
    "align jv_report_september_ 2025 draft1": "en",
    "align safely stand together 2024": "en",
    "align_safety climate survey 2024": "en",
    "bytp-qua-pro-1020_management of major product  quality deviations_en": "en",
    "c4-q10 example of questionnaire for subcontractor": "en",
    "c4-q10 subcontractor management (hse process)": "en",
    "c4-q11 example of rams": "en",
    "c4-q11 example of welfare, working hours, fatigue analysis and consideration": "en",
    "c4-q2 bytp h&s policy 2025": "en",
    "c4-q2 bytp uk h&s policy 2025": "en",
    "c4-q2 list of bytp hse policies and standards": "en",
    "c4-q3 bytp certificate iso45001v2018": "en",
    "c4-q3 list of bytp hse policies and standards": "en",
    "c4-q4 bytp health & safety organisation chart": "en",
    "c4-q5 construction phase plan - project example": "en",
    "c4-q5 project hse training matrix": "en",
    "c4-q5 \u2013 flash event example": "en",
    "c4-q5 \u2013 flash info example": "en",
    "c4-q6 hse memo competence assurance": "en",
    "c4-q7 example of h&s action plan": "en",
    "c4-q7 example of improvement plan": "en",
    "c4-q9 example of procedure for management of health and safety events": "en",
    "cdm readiness process": "en",
    "construction phase plan": "en",
    "consultation with workers": "en",
    "example health management plan": "en",
    "example induction": "en",
    "example tunnel induction": "en",
    "general policy bytp (en)": "en",
    "health matters - edition 14 11 august": "en",
    "improvement process": "en",
    "independant safety review ": "en",
    "induction process": "en",
    "km-10121-b csfr processus": "en",
    "local cpp": "en",
    "performance measures september 2025": "en",
    "ppe requirements": "en",
    "risk assessment and methods process": "en",
    "safety matters - edition 17 25 september": "en",
    "slam & improve": "en",
    "stakeholder engagement": "en",
    "supervisor induction": "en",
    "supply chain summit june 2025 (1)": "en",
    # ENBRIDGE ---------------------------------------------------------------------
    "contractor safety specifications v2.2": "en",
    "ground disturbance standard - v3.0": "en",
    "operational risk matrix": "en",
    "operational risk matrix with risk authorities": "en",
    "project safety management standard ver 1.2": "en",
    "projects contractor safety performance program guide": "en",
    "projects event analysis standard v1": "en",
    "projects hand protection specification": "en",
    "us dot contractor danda policy rev 2": "en",
    "us non-dot contractor drug  alcohol policy": "en",
    # BYTP -------------------------------------------------------------------------
    "bycn - ppe guide bycn specifications v6": "en",
    "bycn - ppe guide equipments v8": "en",
    "bytp health & safety policy 2025": "en",
    "bytp-certificat iso 45001-v2018": "fr",
    "bytp-h&s-for-2072-va addiction control attendance sheet": "en",
    "bytp-h&s-for-2075-a addiction assessment form": "en",
    "bytp-h&s-for-2086-va attestation de prise en charge": "fr",
    "bytp-h&s-for-2086-va certificate of care": "en",
    "bytp-h&s-for-2110 top site general regulation": "en",
    "bytp-h&s-for-2110 top site reglement general": "fr",
    "bytp-h&s-for-2138-vb procedure de gestion de levage projet": "fr",
    "bytp-h&s-for-2138-vb project lifting management plan": "en",
    "bytp-h&s-inf-2031-va dispositifs et materiels de consignation": "fr",
    "bytp-h&s-inf-2031-va lockout devices and materials": "en",
    "bytp-h&s-inf-2084 definitions - populations-events": "en",
    "bytp-h&s-inf-2084 definitions populations-evenements": "fr",
    "bytp-h&s-inf-2108-vb bytp health & safety system": "en",
    "bytp-h&s-inf-2108-vb systeme sante securite bytp": "fr",
    "bytp-h&s-inf-2113-va exhaustive list of exclusions by major risk": "en",
    "bytp-h&s-inf-2113-va liste exhaustive des exclusions par risque majeur": "fr",
    "bytp-h&s-inf-2122-va h&s questionnaire for subcontractors": "en",
    "bytp-h&s-inf-2122-va questionnaire sante securite pour sous-traitants": "fr",
    "bytp-h&s-inf-2123-va criteres d'evaluation sante securite pour les sous-traitants": "fr",
    "bytp-h&s-inf-2123-va h&s assessment criteria for subcontractors": "en",
    "bytp-h&s-inf-2135-va missions detaillees des acteurs du levage": "fr",
    "bytp-h&s-inf-2135-vb roles of lifting personnel": "en",
    "bytp-h&s-inf-2137-vc safe lifting techniques": "en",
    "bytp-h&s-inf-2137-vc techniques de levage en securite": "fr",
    "bytp-h&s-inf-2137-vd safe lifting techniques": "en",
    "bytp-h&s-inf-2137-vd techniques de levage en securite": "fr",
    "bytp-h&s-inf-2141-vb elingages standards": "fr",
    "bytp-h&s-inf-2141-vb standard slinging": "en",
    "bytp-h&s-inf-2151-va consignation-bonnes pratiques": "fr",
    "bytp-h&s-inf-2151-va lock out-good practices": "en",
    "bytp-h&s-inf-2166-vb standard de securisation d'acces et de travaux en hauteur": "fr",
    "bytp-h&s-inf-2166-vc standard de securisation d'acces et de travaux en hauteur": "fr",
    "bytp-h&s-inf-2166-vc standard practices for securing access to height and work at height": "en",
    "bytp-h&s-inf-2168-vb signaling standards and vehicle-pedestrian protection systems": "en",
    "bytp-h&s-inf-2168-vb standards de signalisation et systemes de protection engins-pietons": "fr",
    "bytp-h&s-inf-2169-va etapes de consignations": "fr",
    "bytp-h&s-inf-2169-va lockout steps": "en",
    "bytp-h&s-inf-2170-va cellule de gestion des urgences": "fr",
    "bytp-h&s-inf-2170-va central emergency team": "en",
    "bytp-h&s-inf-2172-va emergency measures in underground environments": "en",
    "bytp-h&s-inf-2172-va mesures d'urgence en milieu souterrain": "fr",
    "bytp-h&s-pol-2007 - bytp health & safety policy 2025": "en",
    "bytp-h&s-pol-2007 - politique sante securite bytp 2025": "fr",
    "bytp-h&s-pro-2062-va repondre a un ao sante securite": "fr",
    "bytp-h&s-pro-2068-vc gestion drogue et alcool au travail": "fr",
    "bytp-h&s-pro-2068-vc management of drug and alcohol at work": "en",
    "bytp-h&s-pro-2078-va gestion des sous-traitants": "fr",
    "bytp-h&s-pro-2078-va management of subcontractors": "en",
    "bytp-h&s-pro-2082-vd gestion des evenements sante securite": "fr",
    "bytp-h&s-pro-2082-vd management of health & safety events": "en",
    "bytp-h&s-pro-2093-va projects h&s reporting": "en",
    "bytp-h&s-pro-2093-va reporting p2s projet": "fr",
    "bytp-h&s-pro-2094-vd indicateurs et reporting p2s bytp": "fr",
    "bytp-h&s-pro-2114-va management of unforeseen situations": "en",
    "bytp-h&s-pro-2114-va proc\u00e9dure de gestion de l'impr\u00e9vu": "fr",
    "bytp-h&s-ref-2200-vc referentiel barrieres de defense et regles vitales": "fr",
    "bytp-h&s-ref-2200-vc standard lines of defence and life saving rules": "en",
    "bytp-h&s-ref-2201-vc referentiel systeme \u2013 manuel sante securite": "fr",
    "bytp-h&s-ref-2201-vc standard system \u2013 health and safety manual": "en",
    "bytp-h&s-ref-2210-vd referentiel levage": "fr",
    "bytp-h&s-ref-2210-vd standard lifting": "en",
    "bytp-h&s-ref-2211-vc referentiel prevention des chutes de hauteur": "fr",
    "bytp-h&s-ref-2211-vc standard fall from height prevention": "en",
    "bytp-h&s-ref-2212-vc referentiel interactions engins pietons": "fr",
    "bytp-h&s-ref-2212-vc standard vehicles pedestrian interaction": "en",
    "bytp-h&s-ref-2213-vd referentiel stabilite": "fr",
    "bytp-h&s-ref-2213-vd standard stability": "en",
    "bytp-h&s-ref-2214-vc referentiel energies dangereuses": "fr",
    "bytp-h&s-ref-2214-vc standard dangerous energies sources": "en",
    "bytp-h&s-ref-2215-vc referentiel engins de chantier et maintenances associees": "fr",
    "bytp-h&s-ref-2215-vc standard construction machinery and associated maintenance": "en",
    "bytp-h&s-ref-2216-vb referentiel installations de chantier": "fr",
    "bytp-h&s-ref-2216-vb standard site installations": "en",
    "bytp-h&s-ref-2217-va referentiel logistique et stockage": "fr",
    "bytp-h&s-ref-2217-va standard logistics and storage": "en",
    "bytp-h&s-ref-2218-va referentiel ergonomie": "fr",
    "bytp-h&s-ref-2218-va standard ergonomics": "en",
    "bytp-h&s-ref-2219-vc referentiel epi": "fr",
    "bytp-h&s-ref-2219-vc standard ppe": "en",
    "bytp-h&s-ref-2220-vb referentiel outillages": "fr",
    "bytp-h&s-ref-2220-vb standard portable tools": "en",
    "bytp-h&s-ref-2221-vb referentiel gestion des situations d'urgence": "fr",
    "bytp-h&s-ref-2221-vb standard emergency management": "en",
    "bytp-h&s-ref-2222-vc referentiel agents chimiques dangereux": "fr",
    "bytp-h&s-ref-2222-vc standard hazardous chemicals": "en",
    "bytp-h&s-ref-2223-va referentiel espaces confines": "fr",
    "bytp-h&s-ref-2223-va standard confined spaces": "en",
    "bytp-h&s-ref-2224-va referentiel equipements sous pression": "fr",
    "bytp-h&s-ref-2224-va standard work with high pressure tools": "en",
    "bytp-h&s-ref-2225-vb referentiel travail par point chaud": "fr",
    "bytp-h&s-ref-2225-vb standard hot works": "en",
    "bytp-h&s-ref-2226-vc referentiel terrassement": "fr",
    "bytp-h&s-ref-2226-vc standard earthworks": "en",
    "bytp-h&s-ref-2227-vb referentiel activites de travaux souterrains": "fr",
    "bytp-h&s-ref-2227-vb standard underground construction work": "en",
    "bytp-h&s-ref-2228-va referentiel activites de travaux speciaux et fondations profondes": "fr",
    "bytp-h&s-ref-2228-va standard special works and deep foundations": "en",
    "bytp-h&s-ref-2229-va referentiel activites de travaux fluviaux et maritime": "fr",
    "bytp-h&s-ref-2229-va standard river and maritime works": "en",
    "bytp-h&s-ref-2230-va referentiel activites de beton": "fr",
    "bytp-h&s-ref-2230-va standard work with concrete": "en",
    "bytp-h&s-ref-2231-va referentiel consignation": "fr",
    "bytp-h&s-ref-2231-va standard lock out - tag out": "en",
    "bytp-h&s-ref-2232-va referentiel radioprotection pour les activites tp": "fr",
    "bytp-h&s-ref-2232-va standard radiation protection for civil works activities": "en",
    "bytp-h&s-ref-2233-vb referentiel equipements de production motorises": "fr",
    "bytp-h&s-ref-2233-vb standard powered production equipment": "en",
    "bytp_projectmanagement_sheet_sd": "fr",
    "guide epi bycn 2018 produits en v8": "en",
    "guide epi bycn 2018 produits fr v8": "fr",
    "guide epi bycn 2018 specifications en v6": "en",
    "guide epi bycn 2018 specifications fr v6": "fr",
    "guide reporting bycn sante securite 2022 fr 18112022": "fr",
    "lettre engagament project directors - safety": "fr",
    "mng-not-0007-c3-programme des audits041120": "fr",
    "mng-pro-0001 -o-procedure d'audit qse-fr signee": "fr",
    "mng-pro-0001-o-qhse audit procedure-en": "en",
    "presentation commercial h&s - en - 1225 - revue communication": "fr",
    "protocole_reporting_groupebouygues_2024_vfinale_va": "en",
    "protocole_reporting_groupebouygues_2024_vfinale_vf": "fr",
    "slides rm et responsabilites delegataire de pouvoir": "fr",
    # Flavien ----------------------------------------------------------------------
    "c4 prequalification uk questionnary": "en",
}


def detect_language(text: str, filename_stem: str = "") -> str:
    """Détection FR/EN : lookup ground-truth par nom de fichier, fallback stopwords."""
    if filename_stem:
        lang = _LANG_LOOKUP.get(filename_stem.lower())
        if lang is not None:
            return lang
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
        "language": detect_language(full_text, pdf_path.stem),
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
