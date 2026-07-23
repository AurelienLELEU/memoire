"""Convert soutenance_qa.md to a self-contained HTML with KaTeX for math, then print to PDF via headless Edge/Chrome.

Usage (from repo root):
    python scripts/md_to_pdf.py soutenance_qa.md soutenance_qa.pdf
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import markdown
import latex2mathml.converter as l2m

CSS = r"""
:root {
  --font-body: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  --font-mono: "Consolas", "Menlo", "Courier New", monospace;
  --color-text: #1b1b1b;
  --color-muted: #555;
  --color-border: #d0d7de;
  --color-code-bg: #f6f8fa;
  --color-callout-bg: #eef4fb;
  --color-callout-border: #3b6fa8;
  --color-accent: #b45309;
  --color-h1: #0b3d91;
  --color-h2: #0b3d91;
  --color-h3: #14274a;
}
@page {
  size: A4;
  margin: 18mm 16mm 22mm 16mm;
}
html { font-size: 10.5pt; }
body {
  font-family: var(--font-body);
  color: var(--color-text);
  line-height: 1.45;
  max-width: 100%;
  margin: 0;
  padding: 0;
  text-rendering: optimizeLegibility;
}
h1, h2, h3, h4 { font-weight: 600; line-height: 1.25; }
h1 { color: var(--color-h1); font-size: 1.9rem; margin-top: 1.4em; margin-bottom: 0.6em; border-bottom: 2px solid var(--color-h1); padding-bottom: 0.25em; page-break-before: auto; }
h1:first-of-type { margin-top: 0; }
h2 { color: var(--color-h2); font-size: 1.35rem; margin-top: 1.6em; margin-bottom: 0.5em; border-bottom: 1px solid var(--color-border); padding-bottom: 0.2em; }
h3 { color: var(--color-h3); font-size: 1.12rem; margin-top: 1.35em; margin-bottom: 0.4em; }
h4 { color: var(--color-h3); font-size: 1.02rem; margin-top: 1.1em; margin-bottom: 0.35em; }
p { margin: 0.5em 0; text-align: justify; hyphens: auto; }
ul, ol { margin: 0.4em 0 0.6em 1.2em; padding: 0; }
li { margin: 0.15em 0; }
strong { color: #111; }
em { color: #333; }
a { color: #0645ad; text-decoration: none; }
a:hover { text-decoration: underline; }
code { font-family: var(--font-mono); background: var(--color-code-bg); padding: 0.06em 0.35em; border-radius: 3px; font-size: 0.92em; }
pre { background: var(--color-code-bg); padding: 0.8em 1em; border-radius: 4px; overflow-x: auto; font-size: 0.88em; line-height: 1.35; page-break-inside: avoid; }
pre code { background: transparent; padding: 0; }

table {
  border-collapse: collapse;
  margin: 0.8em 0;
  width: 100%;
  font-size: 0.92em;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid var(--color-border);
  padding: 0.4em 0.6em;
  text-align: left;
  vertical-align: top;
}
th {
  background: #eef2f7;
  font-weight: 600;
  color: var(--color-h1);
}
tr:nth-child(even) td { background: #fbfcfd; }

blockquote {
  border-left: 4px solid var(--color-callout-border);
  background: var(--color-callout-bg);
  margin: 0.8em 0;
  padding: 0.6em 1em;
  color: #1b1b1b;
  border-radius: 0 4px 4px 0;
}
hr { border: none; border-top: 1px solid var(--color-border); margin: 1.6em 0; }

/* KaTeX display equations */
.katex-display { margin: 0.8em 0; overflow-x: auto; }
.katex { font-size: 1em; }

/* Print behavior */
h1, h2, h3 { page-break-after: avoid; }
li, tr { page-break-inside: avoid; }
img { max-width: 100%; }

/* MathML rendering */
math { font-family: "Cambria Math", "Latin Modern Math", "STIX Two Math", serif; }
math[display="block"] {
  display: block;
  text-align: center;
  margin: 0.8em 0;
  font-size: 1.05em;
}

/* Cover */
.cover-title {
  margin-top: 40mm;
  text-align: center;
  color: var(--color-h1);
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1.2;
}
.cover-sub {
  text-align: center;
  color: #333;
  font-size: 1.05rem;
  margin-top: 1.2em;
}
.cover-meta {
  position: fixed;
  bottom: 25mm;
  left: 0;
  right: 0;
  text-align: center;
  color: #666;
  font-size: 0.9rem;
}
"""

KATEX_CDN_HEAD = ""  # math is pre-rendered as MathML, no runtime dependency needed


def _render_math(latex: str, display: bool) -> str:
    """Render a LaTeX snippet to inline HTML using latex2mathml."""
    try:
        mathml = l2m.convert(latex, display="block" if display else "inline")
    except Exception:
        # Fallback: keep source visible if conversion fails
        span = (
            f'<span class="math-fallback" style="font-family:var(--font-mono);">'
            f'{"$$" if display else "$"}{latex}{"$$" if display else "$"}</span>'
        )
        return span
    if display:
        return f'<div class="math-display">{mathml}</div>'
    return mathml


def protect_math(md_text: str):
    """Extract $...$ / $$...$$ chunks, render them to MathML, and store as placeholders.

    Placeholders survive the markdown pass and are swapped back in the resulting HTML.
    """
    placeholders: dict[str, str] = {}
    counter = 0

    def replace_display(match: re.Match) -> str:
        nonlocal counter
        token = f"@@MATH{counter}@@"
        counter += 1
        placeholders[token] = _render_math(match.group(1).strip(), display=True)
        return token

    def replace_inline(match: re.Match) -> str:
        nonlocal counter
        token = f"@@MATH{counter}@@"
        counter += 1
        placeholders[token] = _render_math(match.group(1).strip(), display=False)
        return token

    md_protected = re.sub(r"\$\$([\s\S]+?)\$\$", replace_display, md_text)
    md_protected = re.sub(r"(?<!\\)\$([^$\n]+?)\$", replace_inline, md_protected)
    return md_protected, placeholders


def restore_math(html: str, placeholders: dict[str, str]) -> str:
    for token, expr in placeholders.items():
        # If the markdown pass wrapped the placeholder in <p>@@MATHn@@</p>,
        # unwrap it so display-block math is not nested inside a paragraph.
        html = re.sub(
            rf"<p>\s*{re.escape(token)}\s*</p>",
            expr,
            html,
        )
        html = html.replace(token, expr)
    return html


def convert_md_to_html(md_path: Path) -> str:
    raw = md_path.read_text(encoding="utf-8")
    protected, placeholders = protect_math(raw)

    md = markdown.Markdown(
        extensions=[
            "extra",         # tables, fenced_code, def_list, etc.
            "sane_lists",
            "toc",
            "admonition",
            "attr_list",
        ],
        output_format="html5",
    )
    body_html = md.convert(protected)
    body_html = restore_math(body_html, placeholders)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{md_path.stem}</title>
<style>{CSS}</style>
</head>
<body>
{body_html}
</body>
</html>
"""
    return html


def find_browser() -> str | None:
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    for exe in ("msedge", "chrome"):
        found = shutil.which(exe)
        if found:
            return found
    return None


def render_pdf(html_path: Path, pdf_path: Path) -> None:
    browser = find_browser()
    if browser is None:
        raise RuntimeError("Aucun navigateur Chromium (Edge/Chrome) trouvé pour rendre le PDF.")

    with tempfile.TemporaryDirectory(prefix="md2pdf-") as tmp_profile:
        url = html_path.absolute().as_uri()
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            f"--user-data-dir={tmp_profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--no-sandbox",
            f"--print-to-pdf={pdf_path.absolute()}",
            "--print-to-pdf-no-header",
            url,
        ]
        print(f"[md_to_pdf] Rendering via: {Path(browser).name}", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            sys.stderr.write(result.stdout + "\n" + result.stderr + "\n")
            raise RuntimeError(f"Le navigateur a renvoyé un code d'erreur {result.returncode}")

    if not pdf_path.exists():
        raise RuntimeError("PDF non généré (fichier attendu introuvable).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convertit un .md en .pdf via KaTeX + Edge/Chrome headless.")
    parser.add_argument("input", type=Path, help="Fichier Markdown source")
    parser.add_argument("output", type=Path, help="Fichier PDF cible")
    parser.add_argument("--keep-html", action="store_true", help="Conserver le HTML intermédiaire à côté du PDF")
    args = parser.parse_args()

    if not args.input.exists():
        parser.error(f"Fichier introuvable : {args.input}")

    html_content = convert_md_to_html(args.input)

    if args.keep_html:
        html_path = args.output.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
    else:
        html_fd = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".html", delete=False)
        html_path = Path(html_fd.name)
        html_fd.write(html_content)
        html_fd.close()

    try:
        render_pdf(html_path, args.output)
        print(f"[md_to_pdf] PDF écrit dans : {args.output}", flush=True)
    finally:
        if not args.keep_html:
            try:
                html_path.unlink()
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
