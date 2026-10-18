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
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sports import SPORTS, season_label

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "games"
OVERRIDES = ROOT / "data" / "overrides.json"

INTRASQUAD = re.compile(r"orange[\s/-]*(and|&|vs\.?)?[\s/-]*blue|blue[\s/-]*(and|&|vs\.?)?[\s/-]*orange|intrasquad|alumni|blue[\s/-]*white|scrimmage", re.I)
# Older seasons mark exhibitions only in the opponent name, e.g. "Concordia (Exhibition)".
EXHIBITION_NAME = re.compile(r"\bexhibition\b|\(exh?\.?\)|\(ex\.\)|\(scrim", re.I)

# Some tournament entries are another game's final, e.g. "Richmond 54, Lafayette 46".
OTHER_GAME = re.compile(r"\D \d+, .+ \d+$")
# Spring sports play fall-ball games that UVA files under the spring season; they never count.
FALL_MONTHS = {"08", "09", "10", "11", "12"}
DROPPED_STATUSES = {"cancelled", "canceled", "postponed"}
RESULTS = {"win": "W", "loss": "L", "tie": "T"}
EASTERN = ZoneInfo("America/New_York")


def local_date(stamp):
    """The API stores UTC, so a 7 PM Eastern game would otherwise land on the next day.
    All-day events are stored as Eastern midnight, which this also handles."""
    if not stamp:
        return ""
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(EASTERN).date().isoformat()


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
    tournament = (e.get("tournament") or {}).get("name")
    opponent = (e.get("opponent_name") or "").strip()

    date = local_date(e.get("datetime"))
    fall_ball = SPORTS[slug]["term"] == "spring" and date[5:7] in FALL_MONTHS

    if e.get("is_exhibition") or EXHIBITION_NAME.search(opponent) or fall_ball:
        kind = "exhibition"
    elif INTRASQUAD.search(opponent):
        kind = "intrasquad"
    elif OTHER_GAME.search(opponent):
        kind = "event"
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
        "conf": bool(e.get("is_conference")),
        "tournament": tournament,
        "post": postseason(tournament),
        "rank": e.get("ranking"),
        "opp_rank": e.get("opponent_ranking"),
        "kind": kind,
    }


def apply_overrides(slug, games, overrides):
    """Per-game fixes keyed by API event id: {"kind": ..., "result": ..., "why": ...}.
    Every override carries a "why" so the fix can be re-checked against its source."""
    fixes = overrides.get(slug, {}).get("games", {})
    for g in games:
        fix = fixes.get(str(g["id"]))
        if not fix:
            continue
        for key in ("kind", "result", "uva", "opp"):
            if key in fix:
                g[key] = fix[key]
        g["fixed"] = fix["why"]
    # Games the site is missing entirely, typed in from the record book.
    for g in overrides.get(slug, {}).get("add", []):
        games.append({
            "id": f"add-{g['date']}-{g['opponent']}", "opponent_id": None, "location": None,
            "note": None, "tournament": None, "post": None, "rank": None, "opp_rank": None,
            "conf": False, "kind": "official", "fixed": g["why"], **g,
        })
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
