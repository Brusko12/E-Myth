#!/usr/bin/env python3
"""Достаёт текст главы из EPUB для работы над разбором.

    python3 tools/extract.py 1          # глава 1
    python3 tools/extract.py foreword   # служебный раздел
    python3 tools/extract.py --list     # что вообще есть в книге

Текст кладётся во временную папку (по умолчанию $EMYTH_WORK или .work/),
которая НЕ коммитится: полный текст книги в репозитории не хранится.
"""
import sys, os, re, zipfile, html

EPUB = os.environ.get("EMYTH_EPUB", "original/e-myth.epub")
WORK = os.environ.get("EMYTH_WORK", ".work")

BLOCK_END = re.compile(
    r"</(p|div|h[1-6]|li|blockquote|tr|section)>", re.I)


def to_text(xhtml: str) -> str:
    s = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", "", xhtml)
    s = BLOCK_END.sub("\n\n", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</?(em|i)>", "*", s)
    s = re.sub(r"(?i)</?(strong|b)>", "**", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def resolve(z: zipfile.ZipFile, what: str) -> str:
    names = z.namelist()
    if what.isdigit():
        target = "chapter%02d.xhtml" % int(what)
    else:
        target = what if what.endswith(".xhtml") else what + ".xhtml"
    for n in names:
        if n.endswith("/" + target) or n == target:
            return n
    raise SystemExit("Не нашёл раздел %r. Посмотри: --list" % what)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    z = zipfile.ZipFile(EPUB)

    if sys.argv[1] in ("--list", "-l"):
        for n in z.namelist():
            if n.endswith(".xhtml"):
                n_txt = to_text(z.read(n).decode("utf-8", "replace"))
                head = next((l for l in n_txt.splitlines() if l.strip()), "")
                print("%-45s %6d зн.  %s" % (
                    os.path.basename(n), len(n_txt), head[:60]))
        return

    for what in sys.argv[1:]:
        name = resolve(z, what)
        text = to_text(z.read(name).decode("utf-8", "replace"))
        os.makedirs(WORK, exist_ok=True)
        out = os.path.join(WORK, os.path.basename(name).replace(".xhtml", ".txt"))
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print("%s -> %s  (%d знаков, ~%d слов)" % (
            name, out, len(text), len(text.split())))


if __name__ == "__main__":
    main()
