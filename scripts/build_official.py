"""Build data/official.csv (official season records) from UVA's record books.

The record books are PDFs that UVA updates each year. Each one has a
year-by-year table, but the layouts differ, so each sport says which pages to
read and which line format to expect. Sports without a usable record book come
from Wikipedia (see wiki_records.py) and are merged in here.

Run once a year after the new books come out, then review the diff by hand:
    .venv/bin/pip install -r requirements-dev.txt
    .venv/bin/python scripts/build_official.py
"""

import csv
import io
import re
import urllib.request
from pathlib import Path

import pypdf

from sports import FIRST_SEASON, SPORTS, season_label
from wiki_records import wiki_records

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "official.csv"
CACHE = ROOT / "data" / "raw" / "books"

# (url, pages, format). Pages are 1-based. "line" = the year starts the line and the first
# two W-L(-T) records on it are overall and conference. "mlax" = space-separated columns.
BOOKS = {
    "football": ("https://static.virginiasports.com/custompages/sports/m-footbl/factbook/2026/2026_Virginia_Football_Record_Book_web.pdf", range(86, 89), "line"),
    "wbball": ("https://static.virginiasports.com/pdfs/w-bball/2025-26/2026-WBBFactBook.pdf", range(44, 48), "line"),
    "baseball": ("https://static.virginiasports.com/custompages/sports/m-basebl/history/BaseballRecordBook.pdf", [19], "line"),
    "fhockey": ("https://static.virginiasports.com/custompages/sports/w-fieldh/stats/2025/fhfactbook.pdf", [24], "line"),
    "mten": ("https://static.virginiasports.com/pdfs/tennis/2026/men/2026MTENFactbook.pdf", [42], "line"),
    "wten": ("https://static.virginiasports.com/pdfs/tennis/History/WTEN/2026WTENFactBook.pdf", [18], "line"),
    "msoc": ("https://static.virginiasports.com/pdfs/msoc/history/2026_MSOC_RecordBook.pdf", [19], "line"),
    "wvball": ("https://static.virginiasports.com/pdfs/w-vball/2023/VB_Record_Book_2023.pdf", range(23, 27), "line"),
    "mlax": ("https://static.virginiasports.com/pdfs/m-lax/2026/2026_MLAX_Record_Book.pdf", [8], "mlax"),
    "softball": ("https://storage.googleapis.com/virginiasports-com-prod/2026/07/01/EFeYivoRL4qME27mdXjkr7HdI4r3c5RXnrg8vgwb.pdf", [15], "line"),
    "wsoc": ("https://storage.googleapis.com/virginiasports-com-prod/2025/08/2025-26WSoccerRecordBook.pdf", range(16, 19), "line"),
    # The newest wrestling book on the site is the 2020-21 edition; later seasons go unchecked.
    "wrestling": ("https://storage.googleapis.com/virginiasports-com-prod/2020/12/bbc6e6c0-2021wrestlingfactbook.pdf", [30], "line"),
}

RECORD = re.compile(r"\b(\d{1,2})-(\d{1,2})(?:-(\d{1,2}))?\b")
# A year, or an academic year like 2005-06, at the start of a line, then an optional
# footnote marker (* or ^) that some books use for postseason appearances.
YEAR_LINE = re.compile(r"^\s*((?:19|20)\d{2})(?:-(\d{2}))?[*^]*\s")


def pdf_pages(slug, url, pages):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{slug}.pdf"
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "uva-records/0.1"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            path.write_bytes(resp.read())
    reader = pypdf.PdfReader(str(path))
    return "\n".join(reader.pages[p - 1].extract_text() or "" for p in pages)


def academic_start(slug, year, has_span):
    """Convert the year a book prints to the academic start year the API uses."""
    if has_span or SPORTS[slug]["term"] == "fall":
        return year
    return year - 1  # spring books print the spring year


# A record with no year in front continues the previous year's row; books use this
# when a season was split between two coaches.
SPLIT_LINE = re.compile(r"^\s+\d{1,2}-\d{1,2}")


def add(a, b):
    return tuple(str(int(x or 0) + int(y or 0)) if (x or y) else "" for x, y in zip(a, b))


def parse_line_format(slug, text):
    rows, last = {}, None
    for line in text.splitlines():
        m = YEAR_LINE.match(line)
        if not m:
            if last is not None and SPLIT_LINE.match(line):
                recs = RECORD.findall(line)
                overall, conf = rows[last]
                rows[last] = (add(overall, recs[0]), add(conf, recs[1]) if len(recs) > 1 else conf)
            last = None if not SPLIT_LINE.match(line) else last
            continue
        start = academic_start(slug, int(m.group(1)), m.group(2) is not None)
        recs = RECORD.findall(line[m.end():])
        if start < FIRST_SEASON or not recs or start in rows:
            last = None
            continue
        overall = recs[0]
        conf = recs[1] if len(recs) > 1 else ("", "", "")
        rows[start] = (overall, conf)
        last = start
    return rows


def parse_mlax(text):
    # year W L T GF GA confW confL finish coach ... (2020 has N/A for the ACC columns)
    rows = {}
    for line in text.splitlines():
        m = re.match(r"^\s*(20\d{2})\**\s+(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+\d+\s+(?:(\d+)\s+(\d+)\s)?", line)
        if m and int(m.group(1)) - 1 >= FIRST_SEASON:
            y, w, l, t, cw, cl = m.groups()
            rows[int(y) - 1] = ((w, l, t), (cw or "", cl or "", ""))
    return rows


def main():
    out = []
    for slug, (url, pages, fmt) in BOOKS.items():
        text = pdf_pages(slug, url, pages)
        rows = parse_mlax(text) if fmt == "mlax" else parse_line_format(slug, text)
        for start, (overall, conf) in sorted(rows.items()):
            out.append([slug, season_label(slug, start), start, *overall, *conf, "record book"])
        print(f"{slug}: {len(rows)} seasons from record book")
    for slug, start, overall, conf, source in wiki_records():
        out.append([slug, season_label(slug, start), start, *overall, *conf, source])

    out.sort(key=lambda r: (r[0], r[2]))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["sport", "season", "academic_start", "w", "l", "t", "conf_w", "conf_l", "conf_t", "source"])
    w.writerows([[c if c != "" else "" for c in r] for r in out])
    OUT.write_text(buf.getvalue())
    print(f"wrote {len(out)} rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
