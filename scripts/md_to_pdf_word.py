"""Convert soutenance_qa.md → PDF using pandoc (via pypandoc-binary) + MS Word COM.

Pipeline:
    1. `pandoc` transforms Markdown → DOCX with math rendered as OMML (Word-native).
    2. Word COM opens the DOCX and exports it to PDF.

Word is the fallback because this workstation blocks Chromium headless mode
and lacks GTK for WeasyPrint. Word 2016+ handles OMML equations natively,
which gives clean formulas without needing LaTeX or KaTeX runtime.

Usage:
    python scripts/md_to_pdf_word.py soutenance_qa.md soutenance_qa.pdf
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

import pypandoc


def md_to_docx(md_path: Path, docx_path: Path, reference_docx: Path | None = None) -> None:
    """Convert Markdown to DOCX via pandoc, with math rendered as OMML."""
    extra_args = [
        "--from=markdown+tex_math_dollars+pipe_tables+fenced_code_blocks+table_captions+backtick_code_blocks+auto_identifiers+implicit_header_references",
        "--to=docx",
        # Table of contents at the top
        "--toc",
        "--toc-depth=3",
        # Number sections (Partie A, B, C, D … keeps its own numbering because
        # the headings already spell it out; the TOC still helps to navigate)
        # Use standalone document
        "--standalone",
        "--wrap=preserve",
    ]
    if reference_docx and reference_docx.exists():
        extra_args.append(f"--reference-doc={reference_docx}")
    pypandoc.convert_file(
        source_file=str(md_path),
        to="docx",
        format="markdown",
        outputfile=str(docx_path),
        extra_args=extra_args,
    )


def docx_to_pdf_via_word(docx_path: Path, pdf_path: Path) -> None:
    """Use Word COM automation to save DOCX as PDF (Word 2016+ export)."""
    try:
        import pythoncom  # type: ignore
        from win32com import client as win32client  # type: ignore
    except ImportError:
        print("[md_to_pdf_word] pywin32 required, installing...", flush=True)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
        import pythoncom  # type: ignore
        from win32com import client as win32client  # type: ignore

    pythoncom.CoInitialize()
    word = win32client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0  # wdAlertsNone

    try:
        # Open with absolute path, no template, read-only False
        doc = word.Documents.Open(
            FileName=str(docx_path.absolute()),
            ConfirmConversions=False,
            ReadOnly=False,
            AddToRecentFiles=False,
        )
        try:
            # wdExportFormatPDF = 17
            doc.ExportAsFixedFormat(
                OutputFileName=str(pdf_path.absolute()),
                ExportFormat=17,        # wdExportFormatPDF
                OpenAfterExport=False,
                OptimizeFor=0,          # wdExportOptimizeForPrint
                Range=0,                # wdExportAllDocument
                Item=0,                 # wdExportDocumentContent
                IncludeDocProps=True,
                KeepIRM=True,
                CreateBookmarks=1,      # wdExportCreateHeadingBookmarks
                DocStructureTags=True,
                BitmapMissingFonts=True,
                UseISO19005_1=False,
            )
        finally:
            doc.Close(SaveChanges=0)
    finally:
        word.Quit()
        pythoncom.CoUninitialize()


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert MD → PDF via pandoc + Word COM.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--keep-docx", action="store_true", help="Conserver le .docx intermédiaire")
    parser.add_argument("--reference-docx", type=Path, default=None,
                        help="Modèle Word (styles) à utiliser pour le rendu")
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"Fichier introuvable : {args.input}")

    if args.keep_docx:
        docx_path = args.output.with_suffix(".docx")
    else:
        fd, name = tempfile.mkstemp(suffix=".docx")
        os.close(fd)
        docx_path = Path(name)

    try:
        print(f"[md_to_pdf_word] Pandoc: {args.input.name} -> {docx_path.name}", flush=True)
        md_to_docx(args.input, docx_path, args.reference_docx)

        print(f"[md_to_pdf_word] Word: {docx_path.name} -> {args.output.name}", flush=True)
        docx_to_pdf_via_word(docx_path, args.output)

        print(f"[md_to_pdf_word] PDF ecrit : {args.output}", flush=True)
    finally:
        if not args.keep_docx and docx_path.exists():
            try:
                docx_path.unlink()
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
