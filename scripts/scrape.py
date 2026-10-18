"""Pull UVA schedules and results from virginiasports.com's public JSON API.

Raw responses are cached in data/raw/ (gitignored) so the normalizer can be
re-run without hitting the site again. Use --refresh to re-download, and
--current to re-download only the newest season of each sport (the daily job).

Usage:
    .venv/bin/python scripts/scrape.py              # fill cache, then normalize
    .venv/bin/python scripts/scrape.py --current    # daily refresh
    .venv/bin/python scripts/scrape.py --sport baseball --refresh
"""

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from sports import FIRST_SEASON, SPORTS

API = "https://virginiasports.com/website-api"
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
USER_AGENT = "uva-records/0.1 (fan project; github.com/mattrudy13/uva-records)"
# Be polite: the site is fine with crawlers, but there's no reason to hurry.
DELAY_SECONDS = 0.5


def get(path, params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                time.sleep(DELAY_SECONDS)
                return json.load(resp)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))


def get_all(path, params):
    """Follow the API's page-based pagination and return every row."""
    rows, page = [], 1
    while True:
        body = get(path, {**params, "per_page": 100, "page": page})
        rows.extend(body["data"])
        if page >= body["meta"]["last_page"]:
            return rows
        page += 1


def schedule_index():
    """Map (sport slug, academic start year) -> schedule id, for the sports we track."""
    by_id = {s["sport_id"]: slug for slug, s in SPORTS.items()}
    index = {}
    for sched in get_all("schedules", {}):
        slug = by_id.get(sched["sport_id"])
        m = re.search(r"(\d{4})-\d{2}$", sched["name"])
        if not slug or not m:
            continue
        start = int(m.group(1))
        if start >= FIRST_SEASON:
            index[(slug, start)] = sched["id"]
    return index


def fetch_events(schedule_id):
    return get_all("schedule-events", {
        "filter[schedule_id]": schedule_id,
        "include": "scheduleEventResult,tournament",
    })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sport", action="append", help="limit to these sport slugs")
    ap.add_argument("--refresh", action="store_true", help="re-download even if cached")
    ap.add_argument("--current", action="store_true", help="re-download only each sport's newest season")
    args = ap.parse_args()

    index = schedule_index()
    newest = {}
    for slug, start in index:
        newest[slug] = max(newest.get(slug, 0), start)

    for (slug, start), sched_id in sorted(index.items()):
        if args.sport and slug not in args.sport:
            continue
        out = RAW / slug / f"{start}.json"
        stale = args.refresh or (args.current and start == newest[slug])
        if out.exists() and not stale:
            continue
        if args.current and start != newest[slug]:
            continue
        events = fetch_events(sched_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"schedule_id": sched_id, "events": events}))
        print(f"{slug} {start}: {len(events)} events")


if __name__ == "__main__":
    main()
