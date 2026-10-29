# UVA Records

Game-by-game results for every University of Virginia head-to-head varsity sport since 2000-01:
season records, coaches, postseason, opponents, streaks and highlights.
Unofficial fan project, not affiliated with UVA.

**Site:** https://mattrudy13.github.io/uva-records/

## At a glance

- **What it does:** 10,561 official games across 16 sports and 392 seasons since 2000-01, with season
  records, coaches, postseason results, every opponent's all-time record, streaks and highlights.
- **Data quality:** the school's public API has flipped results, duplicate games and exhibitions that
  aren't flagged. Every season is reconciled against UVA's official record books: 300 match exactly,
  18 are flagged incomplete, and 74 can't be checked yet (no book covers them). Each correction is
  logged with its source in `data/overrides.json`.
- **Built with:** Python (standard library only), a daily GitHub Actions refresh, plain JavaScript with
  hand-built charts (no chart library), and GitHub Pages.

(Counts as of Oct 21, 2026.)

## Pages

- **Dashboard** (`index.html`): every sport for the current academic year (or any year back to
  2000-01), the combined record, and this year's head-to-head with Virginia Tech.
- **Sport** (`sport.html?s=<slug>`): win % by season, then a season table (W-L-T, ACC record, coach,
  postseason); each season opens into its game list.
- **Opponents** (`opponents.html?o=<school>`): one page per school, with the all-sports record, per-sport breakdown,
  last meeting, streak and games.
- **Highlights** (`highlights.html`): win streaks, best and worst seasons, ranked wins (since 2020-21)
  and biggest wins and losses per sport.

## Data

- Games come from [virginiasports.com](https://virginiasports.com)'s public JSON API.
- Season records are checked against UVA's record books. Where they disagree, the official record
  wins: `data/overrides.json` lists every corrected, added or reclassified game with its source.
- A daily GitHub Action refreshes the current seasons.

## Run it locally

```sh
python3 -m venv .venv
.venv/bin/python scripts/scrape.py --current   # refresh current seasons
.venv/bin/python scripts/normalize.py
.venv/bin/python scripts/validate.py
.venv/bin/python scripts/build_site.py
.venv/bin/python -m http.server                # then open http://localhost:8000
```

Only `scripts/build_official.py` needs a package (`pip install -r requirements-dev.txt`).
