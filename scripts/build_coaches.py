"""Build data/coaches.csv: each sport's head coach, as ranges of seasons.

The record books' year-by-year tables come first (typed in below, in season labels).
The site's rosters (the head-coach staff entry, 2012-13 on) only fill seasons newer than
the latest book, because roster pages are sometimes updated after a coaching change.

Usage: .venv/bin/python scripts/build_coaches.py
"""

import csv
import io
import json
import re
from pathlib import Path

from scrape import get_all
from sports import FIRST_SEASON, SPORTS, season_label

ROOT = Path(__file__).resolve().parent.parent
FIRST_ROSTER_SEASON = 2012

# (sport, coach, first season, last season, source), with seasons as the site labels them.
BOOKS = [
    ("football", "George Welsh", "2000", "2000", "2026 football record book"),
    ("football", "Al Groh", "2001", "2009", "2026 football record book"),
    ("football", "Mike London", "2010", "2015", "2026 football record book"),
    ("football", "Bronco Mendenhall", "2016", "2021", "2026 football record book"),
    ("football", "Tony Elliott", "2022", "2025", "2026 football record book"),
    ("mbball", "Pete Gillen", "2000-01", "2004-05", "Wikipedia season list"),
    ("mbball", "Dave Leitao", "2005-06", "2008-09", "Wikipedia season list"),
    ("mbball", "Tony Bennett", "2009-10", "2023-24", "Wikipedia season list"),
    ("mbball", "Ron Sanchez (interim)", "2024-25", "2024-25", "Wikipedia season list"),
    ("mbball", "Ryan Odom", "2025-26", "2025-26", "Wikipedia season list"),
    ("wbball", "Debbie Ryan", "2000-01", "2010-11", "2025-26 WBB fact book"),
    ("wbball", "Joanne Boyle", "2011-12", "2017-18", "2025-26 WBB fact book"),
    ("wbball", "Tina Thompson", "2018-19", "2021-22", "2025-26 WBB fact book"),
    ("wbball", "Amaka Agugua-Hamilton", "2022-23", "2024-25", "2025-26 WBB fact book"),
    ("baseball", "Dennis Womack", "2001", "2003", "baseball record book"),
    ("baseball", "Brian O'Connor", "2004", "2024", "baseball record book"),
    ("fhockey", "Jessica Wilk", "2000", "2005", "2025 FH fact book"),
    ("fhockey", "Michele Madison", "2006", "2022", "2025 FH fact book"),
    # Madison coached most of 2023; Keusgen was acting head coach for the last six games.
    ("fhockey", "Michele Madison / Ole Keusgen (acting)", "2023", "2023", "2025 FH fact book"),
    ("fhockey", "Ole Keusgen", "2024", "2024", "2025 FH fact book"),
    ("mten", "Dick Stockton", "2001", "2001", "2026 MTEN fact book"),
    ("mten", "Brian Boland", "2002", "2017", "2026 MTEN fact book"),
    ("mten", "Andres Pedroso", "2018", "2025", "2026 MTEN fact book"),
    ("wten", "Phil Rogers", "2001", "2005", "2026 WTEN fact book"),
    ("wten", "Mark Guilbeau", "2006", "2017", "2026 WTEN fact book"),
    ("wten", "Sara O'Leary", "2018", "2025", "2026 WTEN fact book"),
    ("msoc", "George Gelnovatch", "2000", "2025", "2026 MSOC record book"),
    ("wsoc", "Steve Swanson", "2000", "2024", "2025-26 WSOC record book"),
    ("softball", "Cheryl Sprangel", "2001", "2005", "2026-27 softball record book"),
    ("softball", "Karen Johns", "2006", "2007", "2026-27 softball record book"),
    ("softball", "Eileen Schmidt", "2008", "2013", "2026-27 softball record book"),
    ("softball", "Blake Miller", "2014", "2016", "2026-27 softball record book"),
    ("softball", "Joanna Hardin", "2017", "2026", "2026-27 softball record book"),
    ("wrestling", "Lenny Bernstein", "2000-01", "2005-06", "2020-21 wrestling fact book"),
    ("wrestling", "Steve Garland", "2006-07", "2019-20", "2020-21 wrestling fact book"),
    ("mlax", "Dom Starsia", "2001", "2016", "2026 MLAX record book"),
    ("mlax", "Lars Tiffany", "2017", "2025", "2026 MLAX record book"),
    # Myers' 28th and last season was 2023 (her UVA bio); LaMonica took over for 2024.
    ("wlax", "Julie Myers", "2001", "2023", "Wikipedia program article; UVA staff bio"),
    ("wvball", "Melissa Aldrich Shelton", "2000", "2007", "2023 VB record book"),
    ("wvball", "Lee Maes", "2008", "2011", "2023 VB record book"),
    ("wvball", "Dennis Hohenshelt", "2012", "2016", "2023 VB record book"),
    ("wvball", "Aaron Smith", "2017", "2020", "2023 VB record book"),
    ("wvball", "Shannon Wells", "2021", "2022", "2023 VB record book"),
]


def label_start(slug, label):
    """Inverse of season_label: the academic start year for a season label."""
    if SPORTS[slug]["term"] == "spring":
        return int(label) - 1
    return int(label[:4])


# Titles vary: "Head Coach", "The Fralin Family Head Football Coach", "... Interim Head ...".
HEAD = re.compile(r"\bhead\b.*\bcoach\b", re.I)
NOT_HEAD = re.compile(r"assoc|assist|student|strength|volunteer|director of (operations|player)", re.I)


def roster_coaches():
    by_id = {s["sport_id"]: slug for slug, s in SPORTS.items()}
    out = []
    for roster in get_all("rosters", {}):
        slug = by_id.get(roster["sport_id"])
        m = re.search(r"(\d{4})-\d{2}$", roster["name"])
        if not slug or not m or int(m.group(1)) < FIRST_ROSTER_SEASON:
            continue
        staff = get_all("roster-staff-members", {"filter[roster_id]": roster["id"], "include": "staffMember"})
        heads = [s for s in staff if HEAD.search(s.get("position") or "") and not NOT_HEAD.search(s.get("position") or "")]
        for s in heads:
            sm = s.get("staff_member") or {}
            name = f"{sm.get('first_name', '').strip()} {sm.get('last_name', '').strip()}".strip()
            title = "interim" if "interim" in s["position"].lower() else ""
            out.append((slug, int(m.group(1)), name, title))
    return out


def collapse(rows):
    """Turn one row per season into (sport, coach, first, last, note, sources) ranges."""
    ranges = []
    for slug, start, coach, note, source in sorted(rows):
        last = ranges[-1] if ranges else None
        if last and last[0] == slug and last[1] == coach and last[3] == start - 1 and last[4] == note:
            last[3] = start
            if source not in last[5]:
                last[5].append(source)
        else:
            ranges.append([slug, coach, start, start, note, [source]])
    return ranges


def main():
    by_season = {}
    for slug, coach, first, last, source in BOOKS:
        for start in range(max(label_start(slug, first), FIRST_SEASON), label_start(slug, last) + 1):
            by_season[(slug, start)] = (coach, "", source)
    for slug, start, coach, note in roster_coaches():
        by_season.setdefault((slug, start), (coach, note, "virginiasports.com roster"))

    rows = [(slug, start, coach, note, source) for (slug, start), (coach, note, source) in by_season.items()]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["sport", "coach", "first_season", "last_season", "note", "source"])
    for slug, coach, first, last, note, sources in collapse(rows):
        w.writerow([slug, coach, season_label(slug, first), season_label(slug, last), note, "; ".join(sources)])
    (ROOT / "data" / "coaches.csv").write_text(buf.getvalue())
    print(buf.getvalue())

    # Seasons with games but no known coach, so gaps are visible.
    games_dir = ROOT / "data" / "games"
    for slug in SPORTS:
        seasons = {g["season"] for g in json.loads((games_dir / f"{slug}.json").read_text())}
        missing = sorted(s for s in seasons if (slug, label_start(slug, s)) not in by_season)
        if missing:
            print(f"no coach: {slug} {' '.join(missing)}")


if __name__ == "__main__":
    main()
