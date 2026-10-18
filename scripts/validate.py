"""Compare season records built from games against data/official.csv.

Writes data/validation.json (read by the site and the daily job) and prints the
mismatches. Exit code is 1 if any season with an official record doesn't match.

Usage: .venv/bin/python scripts/validate.py [--sport SLUG] [--quiet]
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from sports import SPORTS

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "data" / "games"


def as_int(s):
    return int(s) if s not in ("", None) else 0


def computed_records(slug):
    recs = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "conf_w": 0, "conf_l": 0, "conf_t": 0})
    for g in json.loads((GAMES / f"{slug}.json").read_text()):
        if g["kind"] != "official":
            continue
        r = recs[g["season"]]
        key = g["result"].lower()
        r[key] += 1
        if g["conf"]:
            r["conf_" + key] += 1
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sport", action="append")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    official = defaultdict(dict)
    with open(ROOT / "data" / "official.csv") as f:
        for row in csv.DictReader(f):
            official[row["sport"]][row["season"]] = row

    overrides_path = ROOT / "data" / "overrides.json"
    overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}

    report, bad = {}, 0
    for slug in SPORTS:
        if args.sport and slug not in args.sport:
            continue
        mine = computed_records(slug)
        # Seasons where the site is missing games we can't recover. The official record is
        # shown instead, and these seasons are left out of streaks.
        incomplete = set(overrides.get(slug, {}).get("incomplete", []))
        rows = []
        for season in sorted(set(mine) | set(official[slug])):
            o, m = official[slug].get(season), mine.get(season)
            row = {"season": season, "games": m, "official": None, "status": "unchecked"}
            if o:
                want = {k: as_int(o[k]) for k in ("w", "l", "t")}
                got = {k: (m or {}).get(k, 0) for k in ("w", "l", "t")}
                row["official"] = want
                row["status"] = "match" if want == got else "mismatch"
                if row["status"] == "mismatch" and season in incomplete:
                    row["status"] = "incomplete"
                # Conference splits are informational: books and the site sometimes
                # disagree on which games counted (e.g. ACC Challenge, divisional play).
                if o["conf_w"] != "":
                    want_c = {k: as_int(o["conf_" + k]) for k in ("w", "l", "t")}
                    got_c = {k: (m or {}).get("conf_" + k, 0) for k in ("w", "l", "t")}
                    row["conf_match"] = want_c == got_c
            rows.append(row)
            if row["status"] == "mismatch":
                bad += 1
                if not args.quiet:
                    g = row["games"] or {}
                    print(f"{slug:9} {season:8} games {g.get('w',0)}-{g.get('l',0)}-{g.get('t',0)}"
                          f"  official {want['w']}-{want['l']}-{want['t']}")
        report[slug] = rows

    out = ROOT / "data" / "validation.json"
    if args.sport and out.exists():  # a partial run updates only the sports it checked
        report = {**json.loads(out.read_text()), **report}
    out.write_text(json.dumps(report, indent=1))
    counts = defaultdict(int)
    for rows in report.values():
        for r in rows:
            counts[r["status"]] += 1
    checked = counts["match"] + counts["mismatch"] + counts["incomplete"]
    print(f"{counts['match']}/{checked} checked seasons match; {counts['incomplete']} known incomplete; "
          f"{counts['mismatch']} mismatched; {counts['unchecked']} unchecked")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
