"""Official season records from Wikipedia, for sports without a usable record book.

Only men's basketball needs this today: UVA doesn't post an MBB record book, and
Wikipedia's season list uses a structured template that's easy to read reliably.
"""

import re
import urllib.request

from sports import FIRST_SEASON

PAGES = {
    "mbball": "List_of_Virginia_Cavaliers_men%27s_basketball_seasons",
}

ENTRY = re.compile(r"\{\{CBB yearly record entry(.*?)\}\}", re.S)
FIELD = re.compile(r"\|\s*(\w+)\s*=\s*([^\n|]*(?:\[\[[^\]]*\]\][^\n|]*)*)")
RECORD = re.compile(r"(\d+)[–-](\d+)(?:[–-](\d+))?")


def fetch(title):
    url = f"https://en.wikipedia.org/w/index.php?title={title}&action=raw"
    req = urllib.request.Request(url, headers={"User-Agent": "uva-records/0.1 (fan project)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()


def wiki_records():
    """Yield (sport, academic start, overall, conference, source) tuples."""
    for slug, title in PAGES.items():
        for body in ENTRY.findall(fetch(title)):
            fields = dict(FIELD.findall(body))
            season = re.search(r"(\d{4})[–-]\d{2}", fields.get("season", ""))
            overall = RECORD.search(fields.get("overall", ""))
            if not season or not overall or int(season.group(1)) < FIRST_SEASON:
                continue
            conf = RECORD.search(fields.get("conference", ""))
            yield (
                slug,
                int(season.group(1)),
                tuple(x or "" for x in overall.groups()),
                tuple(x or "" for x in conf.groups()) if conf else ("", "", ""),
                "wikipedia",
            )
