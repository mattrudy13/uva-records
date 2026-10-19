# UVA Records

Game-by-game results for every University of Virginia head-to-head varsity sport since 2000-01:
season records, coaches, postseason, opponents, streaks and highlights.
Unofficial fan project, not affiliated with UVA.

**Site:** https://mattrudy13.github.io/uva-records/

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
