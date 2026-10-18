# uva-records — project notes

Game-by-game results for UVA's head-to-head varsity sports since 2000-01, for a static site at
mattrudy13.github.io/uva-records/. SPEC.md has the decisions and source notes.

## Status (2026-10-18)

Phase 1 (data) done. 16 sports, 2000-01 to now. Every season with an official record either
matches exactly (300) or is listed as known incomplete in `data/overrides.json` (18: the site is
missing games). 68 seasons are unchecked: women's lacrosse (no official source), squash (no book),
and seasons newer than the latest record book.
Not started: site pages, daily GitHub Action. Repo: github.com/mattrudy13/uva-records.

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
5. `scripts/build_coaches.py`: `data/coaches.csv` (coach ranges). Record books first (typed into
   the script), rosters only for seasons after the latest book.

## Overrides

`data/overrides.json`, per sport: `games` (fix by API event id: `kind`, `result`, `uva`, `opp`),
`add` (games the site lacks, typed from the book) and `incomplete` (seasons we can't fix).
Every entry has a `why` naming its source. When a new mismatch shows up, diff that season's
games against the book's game list by date before adding an override.

## Data rules learned the hard way

- Exhibitions are often unflagged: they show up only in the name ("Concordia (Exhibition)",
  "VCU (ex.)") or not at all (MBB vs. D-II/D-III opponents in early November).
- Spring sports file their fall-ball games (Aug–Dec) under the spring season, and none of them count.
- Intrasquad: "Orange-Blue World Series", "BLUE/ORANGE".
- Soccer games decided on PKs: UVA's own books are inconsistent (some count as ties, some as
  W/L), so a blanket rule breaks seasons. Fix them one game at a time in overrides.
  Field hockey shootouts count as W/L.
- The API stores UTC; convert to Eastern or evening games land on the next day.
- Some API results are flipped (W stored as L, with scores swapped), and some games are duplicated.
- Some 2000–2002 seasons are incomplete on the site (missing games, not just wrong ones).
  Wrestling duals inside multi-team events have no results at all.
- Record books can disagree with themselves (FH 2014: header 12-8, game list 11-9). The header
  record, which matches the conference record, wins.
- Record books split a season between coaches on a second line with no year (FH 2023).
- stats.ncaa.org blocks automated requests; don't try to get around it.
