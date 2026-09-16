#!/usr/bin/env python3
"""Собирает PDF для чтения из разбора главы.

Использование:
    python3 tools/md2pdf.py analysis/chapter-01.md
    python3 tools/md2pdf.py analysis/*.md

PDF складывается в analysis/pdf/. Markdown остаётся источником истины.
"""
import sys, os, subprocess, tempfile, html
import markdown

def _find_chrome() -> str:
    candidates = [
        os.environ.get("CHROME_BIN", ""),
        "/opt/pw-browsers/chromium",
        "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
        "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
        "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
    ]
    for c in candidates:
        if c and os.path.isfile(os.path.realpath(c)):
            return c
    raise RuntimeError("Не найден chromium — задай путь в CHROME_BIN")


CHROME = _find_chrome()

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
* { box-sizing: border-box; }
body {
  font-family: "DejaVu Serif", "Liberation Serif", Georgia, serif;
  font-size: 10.5pt; line-height: 1.62; color: #1a1a1a;
  margin: 0; hyphens: auto;
}
h1 {
  font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
  font-size: 19pt; line-height: 1.25; margin: 0 0 4mm 0;
  color: #111; border-bottom: 2.5px solid #b8860b; padding-bottom: 3mm;
}
h2 {
  font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
  font-size: 13pt; margin: 9mm 0 3mm 0; color: #111;
  page-break-after: avoid; break-after: avoid;
}
h3 {
  font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
  font-size: 11pt; margin: 6mm 0 2mm 0; color: #333;
  page-break-after: avoid; break-after: avoid;
}
p { margin: 0 0 3.2mm 0; text-align: justify; }
strong { color: #000; }
em { color: #444; }
blockquote {
  margin: 4mm 0; padding: 3mm 5mm; border-left: 3px solid #b8860b;
  background: #faf7f0; font-style: italic; color: #333;
  page-break-inside: avoid; break-inside: avoid;
}
blockquote p { margin: 0 0 2mm 0; text-align: left; }
blockquote p:last-child { margin-bottom: 0; }
ul, ol { margin: 0 0 3.5mm 0; padding-left: 7mm; }
li { margin-bottom: 1.6mm; }
table {
  border-collapse: collapse; width: 100%; margin: 4mm 0;
  font-size: 9.3pt; page-break-inside: avoid; break-inside: avoid;
}
th {
  background: #f0ece2; text-align: left; padding: 2mm 2.5mm;
  border: 1px solid #d5cdb8; font-family: "DejaVu Sans", sans-serif;
  font-size: 8.8pt; font-weight: bold;
}
td { padding: 2mm 2.5mm; border: 1px solid #ddd6c4; vertical-align: top; }
tr:nth-child(even) td { background: #fbfaf6; }
hr { border: none; border-top: 1px solid #ddd; margin: 7mm 0; }
code {
  font-family: "DejaVu Sans Mono", monospace; font-size: 9pt;
  background: #f4f1e8; padding: 0.4mm 1.2mm; border-radius: 2px;
}
pre {
  background: #f7f5ee; border: 1px solid #e3ddcc; border-radius: 3px;
  padding: 3mm; overflow-x: auto; page-break-inside: avoid; break-inside: avoid;
}
pre code { background: none; font-size: 8.2pt; line-height: 1.35; }
.footer {
  margin-top: 10mm; padding-top: 3mm; border-top: 1px solid #ddd;
  font-family: "DejaVu Sans", sans-serif; font-size: 8pt; color: #999;
  text-align: center;
}
"""

TPL = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>{title}</title>
<style>{css}</style></head><body>{body}
<div class="footer">E-Myth · разбор, система, применение · {name}</div>
</body></html>"""


def convert(md_path: str) -> str:
    with open(md_path, encoding="utf-8") as f:
        text = f.read()

    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"]
    )
    title = next(
        (l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("# ")),
        os.path.basename(md_path),
    )
    page = TPL.format(
        title=html.escape(title), css=CSS, body=body,
        name=html.escape(os.path.basename(md_path)),
    )

    out_dir = os.path.join(os.path.dirname(md_path) or ".", "pdf")
    os.makedirs(out_dir, exist_ok=True)
    out_pdf = os.path.join(
        out_dir, os.path.splitext(os.path.basename(md_path))[0] + ".pdf"
    )

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as tmp:
        tmp.write(page)
        tmp_html = tmp.name

    try:
        subprocess.run(
            [CHROME, "--headless", "--no-sandbox", "--disable-gpu",
             "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}",
             "file://" + tmp_html],
            check=True, capture_output=True, timeout=120,
        )
    finally:
        os.unlink(tmp_html)

    return out_pdf


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        print(f"{path} -> {convert(path)}")
