"""Turn cached API responses into one clean games file per sport.

Every listed event is kept, but only "official" games count toward records.
The others are tagged so the site can show them on request:
  exhibition   flagged as an exhibition by the site
  intrasquad   UVA vs. UVA (Orange-Blue, alumni games), which the site doesn't flag
  event        no single-opponent W/L result (invitationals, tournaments, meets)
  scheduled    hasn't been played yet
Cancelled and postponed events are dropped.

data/overrides.json can exclude events or add games the site is missing; it's
applied last so official records always win.

Usage: .venv/bin/python scripts/normalize.py
"""

import json
import re
from pathlib import Path

from sports import SPORTS, season_label

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "games"
OVERRIDES = ROOT / "data" / "overrides.json"

INTRASQUAD = re.compile(r"orange[\s/-]*(and|&|vs\.?)?[\s/-]*blue|blue[\s/-]*(and|&|vs\.?)?[\s/-]*orange|intrasquad|alumni|blue[\s/-]*white|scrimmage", re.I)
# Older seasons mark exhibitions only in the opponent name, e.g. "Concordia (Exhibition)".
EXHIBITION_NAME = re.compile(r"\bexhibition\b|\(exh?\.?\)|\(ex\.\)", re.I)
# NCAA soccer records count games decided on penalty kicks as ties; the site often
# records the shootout winner instead. Field hockey shootouts do count as W/L.
PK_SPORTS = {"msoc", "wsoc"}
PK_NOTE = re.compile(r"\bpk|shoot-?out", re.I)
# Spring sports play fall-ball games that UVA files under the spring season; they never count.
FALL_MONTHS = {"08", "09", "10", "11", "12"}
DROPPED_STATUSES = {"cancelled", "canceled", "postponed"}
RESULTS = {"win": "W", "loss": "L", "tie": "T"}


def postseason(tournament):
    """Classify a tournament name. Regular-season tournaments return None."""
    if not tournament:
        return None
    name = tournament.lower()
    if "ncaa" in name:
        return "ncaa"
    if "acc" in name and ("championship" in name or "tournament" in name):
        return "acc"
    if "bowl" in name:
        return "bowl"
    if re.search(r"\b(nit|wnit|cbi|cit)\b", name):
        return "other"
    return None


def score(value):
    return None if value is None else int(round(float(value)))


def normalize_event(slug, start, e):
    if (e.get("status") or "").lower() in DROPPED_STATUSES:
        return None
    r = e.get("schedule_event_result") or {}
    result = RESULTS.get(r.get("result"))
    win, lose = score(r.get("winning_score")), score(r.get("losing_score"))
    uva, opp = (win, lose) if result in ("W", "T") else (lose, win)
    pk = None
    if slug in PK_SPORTS and result and PK_NOTE.search(r.get("text") or ""):
        pk, result = (result if result != "T" else None), "T"
    tournament = (e.get("tournament") or {}).get("name")
    opponent = (e.get("opponent_name") or "").strip()

    date = (e.get("datetime") or "")[:10]
    fall_ball = SPORTS[slug]["term"] == "spring" and date[5:7] in FALL_MONTHS

    if e.get("is_exhibition") or EXHIBITION_NAME.search(opponent) or fall_ball:
        kind = "exhibition"
    elif INTRASQUAD.search(opponent):
        kind = "intrasquad"
    elif result:
        kind = "official"
    elif (e.get("status") or "") == "completed" or e.get("second_opponent_name"):
        kind = "event"
    else:
        kind = "scheduled"

    return {
        "id": e["id"],
        "season": season_label(slug, start),
        "date": date,
        "opponent": opponent,
        "opponent_id": e.get("opponent_id"),
        "venue": "neutral" if e.get("neutral_event") else e.get("venue_type"),
        "location": e.get("location"),
        "result": result,
        "uva": uva,
        "opp": opp,
        "note": r.get("text"),
        "pk": pk,
        "conf": bool(e.get("is_conference")),
        "tournament": tournament,
        "post": postseason(tournament),
        "rank": e.get("ranking"),
        "opp_rank": e.get("opponent_ranking"),
        "kind": kind,
    }


def apply_overrides(slug, games, overrides):
    o = overrides.get(slug, {})
    for gid, kind in o.get("reclassify", {}).items():
        for g in games:
            if str(g["id"]) == gid:
                g["kind"] = kind
    for g in o.get("add", []):
        games.append({"kind": "official", "added": True, **g})
    return games


def main():
    overrides = json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}
    OUT.mkdir(parents=True, exist_ok=True)
    for slug in SPORTS:
        games = []
        for path in sorted((RAW / slug).glob("*.json")):
            start = int(path.stem)
            for e in json.loads(path.read_text())["events"]:
                g = normalize_event(slug, start, e)
                if g:
                    games.append(g)
        games = apply_overrides(slug, games, overrides)
        games.sort(key=lambda g: (g["date"], g["id"] if isinstance(g["id"], int) else 0))
        (OUT / f"{slug}.json").write_text(json.dumps(games, separators=(",", ":")))
        print(f"{slug}: {sum(g['kind'] == 'official' for g in games)} official of {len(games)}")


if __name__ == "__main__":
    main()
