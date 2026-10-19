"""Build the small JSON files the site reads, in site-data/.

  sports.json      sport list, the current academic year, the validation summary
  seasons.json     per sport, per season: record (official when there is one), coach,
                   postseason, status (match / incomplete / unchecked), progress
  games/<sport>    slim game rows with the cleaned opponent name and slug
  opponents.json   per school: record by sport, last meeting, current streak, and
                   (for Virginia Tech) the head-to-head for every academic year
  highlights.json  streaks, best/worst seasons, ranked wins, biggest margins

Usage: .venv/bin/python scripts/build_site.py
"""

import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from opponents import canonical, load_aliases
from sports import SPORTS, season_label
from build_coaches import label_start

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "site-data"
RIVAL = "Virginia Tech"
RANKED_SINCE = 2020  # academic start year of the first season with rankings in the data
POST_NAMES = {"acc": "ACC", "ncaa": "NCAA", "bowl": "Bowl", "other": "Postseason"}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def current_start(today=None):
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def record(games):
    r = {"w": 0, "l": 0, "t": 0}
    for g in games:
        r[g["result"].lower()] += 1
    return r


def pct(r):
    n = r["w"] + r["l"] + r["t"]
    return (r["w"] + r["t"] / 2) / n if n else None


def load_coaches():
    by = {}
    with open(DATA / "coaches.csv") as f:
        for row in csv.DictReader(f):
            slug = row["sport"]
            for start in range(label_start(slug, row["first_season"]), label_start(slug, row["last_season"]) + 1):
                by[(slug, start)] = row["coach"]
    return by


def slim(g, start):
    """Short keys keep the per-sport files small; the pages only need these."""
    out = {
        "id": g["id"], "s": g["season"], "y": start, "d": g["date"], "o": g["opp_name"], "os": g["opp_slug"],
        "v": (g["venue"] or "")[:1], "r": g["result"], "u": g["uva"], "p": g["opp"], "k": g["kind"],
    }
    for short, key in (("c", "conf"), ("t", "tournament"), ("ps", "post"), ("n", "note"),
                       ("rk", "rank"), ("ork", "opp_rank"), ("f", "fixed"), ("loc", "location")):
        if g.get(key):
            out[short] = g[key]
    return out


def rank_num(value):
    """A poll ranking as an int. Seeds ("5-Seed") and "RV" aren't rankings."""
    m = re.fullmatch(r"#?\s*(\d{1,2})", str(value or "").strip())
    return int(m.group(1)) if m else None


def streak_of(games):
    """Current streak, e.g. ("W", 4), from games in date order."""
    if not games:
        return None
    last = games[-1]["result"]
    n = 0
    for g in reversed(games):
        if g["result"] != last:
            break
        n += 1
    return [last, n]


def main():
    aliases = load_aliases()
    coaches = load_coaches()
    validation = json.loads((DATA / "validation.json").read_text())
    overrides = json.loads((DATA / "overrides.json").read_text())
    with open(DATA / "official.csv") as f:
        official = {(r["sport"], r["season"]): r for r in csv.DictReader(f)}
    now = current_start()
    today = date.today().isoformat()

    (OUT / "games").mkdir(parents=True, exist_ok=True)
    seasons_out, all_games = {}, {}
    for slug in SPORTS:
        games = json.loads((DATA / "games" / f"{slug}.json").read_text())
        status = {r["season"]: r["status"] for r in validation.get(slug, [])}
        incomplete = set(overrides.get(slug, {}).get("incomplete", []))
        for g in games:
            g["opp_name"] = canonical(g.get("school") or g["opponent"], aliases) or "Unknown opponent"
            g["opp_slug"] = slugify(g["opp_name"])
            g["start"] = label_start(slug, g["season"])
        rows_out = []
        by_season = defaultdict(list)
        for g in games:
            by_season[g["season"]].append(g)
        for season, sg in sorted(by_season.items(), key=lambda kv: label_start(slug, kv[0])):
            start = label_start(slug, season)
            played = [g for g in sg if g["kind"] == "official"]
            upcoming = sorted((g for g in sg if g["kind"] == "scheduled" and g["date"] >= today), key=lambda g: g["date"])
            rec = record(played)
            conf = record([g for g in played if g["conf"]])
            o = official.get((slug, season))
            if o:  # the official record wins; the game list may be partial
                rec = {k: int(o[k] or 0) for k in ("w", "l", "t")}
                if o["conf_w"] != "":
                    conf = {k: int(o["conf_" + k] or 0) for k in ("w", "l", "t")}
            post = defaultdict(lambda: {"w": 0, "l": 0, "t": 0})
            for g in played:
                if g["post"]:
                    post[POST_NAMES[g["post"]]][g["result"].lower()] += 1
            if not played and not upcoming:
                continue
            rows_out.append({
                "season": season, "start": start, "record": rec, "pct": pct(rec), "conf": conf,
                "coach": coaches.get((slug, start), ""), "post": dict(post),
                "status": "incomplete" if season in incomplete else status.get(season, "unchecked"),
                "listed": len(played), "upcoming": len(upcoming),
                "next": upcoming[0]["date"] if upcoming else None,
                "first": min((g["date"] for g in played + upcoming), default=None),
                "last_played": max((g["date"] for g in played), default=None),
            })
        seasons_out[slug] = rows_out
        all_games[slug] = games
        (OUT / "games" / f"{slug}.json").write_text(
            json.dumps([slim(g, g["start"]) for g in games if g["kind"] != "duplicate"], separators=(",", ":")))

    # ---- Opponents ----
    opp = defaultdict(lambda: {"by_sport": defaultdict(list)})
    for slug, games in all_games.items():
        for g in games:
            if g["kind"] == "official" and g["opp_name"] != "Unknown opponent":
                o = opp[g["opp_slug"]]
                o["name"] = g["opp_name"]
                o["by_sport"][slug].append(g)
    opponents_out = []
    for oslug, o in opp.items():
        everything = sorted((g for gs in o["by_sport"].values() for g in gs), key=lambda g: g["date"])
        entry = {
            "slug": oslug, "name": o["name"], "record": record(everything),
            "first": everything[0]["date"], "last": everything[-1]["date"],
            "sports": {
                s: {"record": record(gs), "last": {"d": gs[-1]["date"], "r": gs[-1]["result"], "u": gs[-1]["uva"], "p": gs[-1]["opp"]},
                    "streak": streak_of(sorted(gs, key=lambda g: g["date"]))}
                for s, gs in o["by_sport"].items()
            },
        }
        if o["name"] == RIVAL:
            by_year = defaultdict(lambda: defaultdict(lambda: {"w": 0, "l": 0, "t": 0}))
            for s, gs in o["by_sport"].items():
                for g in gs:
                    by_year[g["start"]][s][g["result"].lower()] += 1
            entry["by_year"] = {str(y): dict(v) for y, v in sorted(by_year.items())}
        opponents_out.append(entry)
    opponents_out.sort(key=lambda e: -sum(e["record"].values()))
    (OUT / "opponents.json").write_text(json.dumps(opponents_out, separators=(",", ":")))

    # ---- Highlights ----
    highlights = {}
    for slug, games in all_games.items():
        incomplete = set(overrides.get(slug, {}).get("incomplete", []))
        played = sorted((g for g in games if g["kind"] == "official"), key=lambda g: (g["date"], str(g["id"])))
        # Longest win streaks. A season with missing games breaks the streak, since we
        # can't know what happened in the games that aren't listed.
        streaks, run, prev_season = [], [], None
        for g in played:
            broken = g["season"] in incomplete or (prev_season in incomplete and g["season"] != prev_season)
            if g["result"] == "W" and not broken:
                run.append(g)
            else:
                if len(run) >= 2:
                    streaks.append(run)
                run = [g] if g["result"] == "W" and g["season"] not in incomplete else []
            prev_season = g["season"]
        if len(run) >= 2:
            streaks.append(run)
        streaks.sort(key=lambda r: -len(r))
        seasons = [s for s in seasons_out[slug] if s["pct"] is not None and s["start"] < now
                   and sum(s["record"].values()) >= 5]
        margin = lambda g: (g["uva"] or 0) - (g["opp"] or 0)
        scored = [g for g in played if g["uva"] is not None and g["opp"] is not None]
        ranked = [g for g in played if g["start"] >= RANKED_SINCE and g["result"] == "W" and rank_num(g.get("opp_rank"))]
        upsets = [g for g in ranked if not rank_num(g.get("rank")) and rank_num(g["opp_rank"]) <= 10]
        pick = lambda gs: [slim(g, g["start"]) for g in gs]
        highlights[slug] = {
            "streaks": [{"n": len(r), "from": r[0]["date"], "to": r[-1]["date"], "seasons": sorted({g["season"] for g in r})}
                        for r in streaks[:5]],
            "current": streak_of(played),
            "best": [{"season": s["season"], "record": s["record"], "pct": s["pct"]} for s in sorted(seasons, key=lambda s: -s["pct"])[:5]],
            "worst": [{"season": s["season"], "record": s["record"], "pct": s["pct"]} for s in sorted(seasons, key=lambda s: s["pct"])[:5]],
            "ranked_wins": len(ranked),
            "ranked": pick(sorted(ranked, key=lambda g: rank_num(g["opp_rank"]))[:10]),
            "upsets": pick(sorted(upsets, key=lambda g: rank_num(g["opp_rank"]))),
            "biggest_wins": pick(sorted((g for g in scored if g["result"] == "W"), key=lambda g: -margin(g))[:5]),
            "biggest_losses": pick(sorted((g for g in scored if g["result"] == "L"), key=lambda g: margin(g))[:5]),
        }
    (OUT / "highlights.json").write_text(json.dumps(highlights, separators=(",", ":")))

    counts = defaultdict(int)
    for rows in seasons_out.values():
        for r in rows:
            counts[r["status"]] += 1
    (OUT / "seasons.json").write_text(json.dumps(seasons_out, separators=(",", ":")))
    (OUT / "sports.json").write_text(json.dumps({
        "built": today, "current": now, "ranked_since": RANKED_SINCE, "rival": RIVAL, "rival_slug": slugify(RIVAL),
        "status": counts,
        "sports": [{"slug": s, "name": m["name"], "term": m["term"],
                    "current_label": season_label(s, now)} for s, m in SPORTS.items()],
    }, separators=(",", ":")))
    sizes = {p.name: p.stat().st_size for p in OUT.rglob("*.json")}
    print(f"{len(opponents_out)} opponents; {sum(sizes.values()) // 1024} KB total; "
          f"largest {max(sizes, key=sizes.get)} {max(sizes.values()) // 1024} KB")


if __name__ == "__main__":
    main()
