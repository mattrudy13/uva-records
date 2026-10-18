# uva-records — project notes

Game-by-game results for UVA's head-to-head varsity sports since 2000-01, for a static site at
mattrudy13.github.io/uva-records/. SPEC.md has the decisions and source notes.

## Status (2026-10-18)

Phase 1 (data) in progress. Scraper, normalizer, official records and validation work end to end.
266/318 seasons with an official record match. Remaining mismatches are per-game fixes for
`data/overrides.json`. Women's lacrosse has no official source yet, so it's unchecked.
Not started: site pages, daily GitHub Action. No GitHub remote yet.

## Pipeline

All scripts use only the standard library, except build_official.py, which needs pypdf from
requirements-dev.txt. Always run them with `.venv/bin/python`.

1. `scripts/scrape.py`: pulls virginiasports.com's JSON API into `data/raw/` (gitignored cache).
   `--current` re-pulls only each sport's newest season.
2. `scripts/normalize.py`: raw → `data/games/<sport>.json`. Tags each event `official`,
   `exhibition`, `intrasquad`, `event` or `scheduled`; only `official` counts. Then applies
   `data/overrides.json`.
3. `scripts/build_official.py`: official season records from UVA record-book PDFs (and Wikipedia
   for MBB) → `data/official.csv`. Run yearly when new books come out, and review the diff.
4. `scripts/validate.py`: games vs official → `data/validation.json`. Exits 1 on any mismatch.

## Data rules learned the hard way

- Exhibitions are often unflagged: they show up only in the name ("Concordia (Exhibition)",
  "VCU (ex.)") or not at all (MBB vs. D-II/D-III opponents in early November).
- Spring sports file their fall-ball games (Aug–Dec) under the spring season, and none of them count.
- Intrasquad: "Orange-Blue World Series", "BLUE/ORANGE".
- Soccer games decided on PKs are ties in NCAA records, even when the site shows W/L
  (the shootout winner is kept in `pk`). Field hockey shootouts do count as W/L.
- Some 2000–2002 seasons are incomplete on the site (missing games, not just wrong ones).
- Record books split a season between coaches on a second line with no year (FH 2023).
- stats.ncaa.org blocks automated requests; don't try to get around it.
