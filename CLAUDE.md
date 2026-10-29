# uva-records — project notes

Game-by-game results for UVA's head-to-head varsity sports since 2000-01, for a static site at
mattrudy13.github.io/uva-records/. SPEC.md has the decisions and source notes.

## Status (2026-10-19)

Data phase done: 300 seasons match the record books, 18 are flagged incomplete, 68 are unchecked
(women's lacrosse, squash, and seasons newer than the latest book). By 2026-10-21 unchecked was 74, as
the 2026-27 seasons started (`site-data/sports.json` → `status`).
Site built and tested locally: dashboard, sport pages, opponents, highlights. Daily refresh
workflow written. Live on GitHub Pages since 2026-10-19; daily refresh tested by hand the same day.

## Pipeline

All scripts use only the standard library, except build_official.py, which needs pypdf from
requirements-dev.txt. Always run them with `.venv/bin/python`.

1. `scripts/scrape.py`: pulls virginiasports.com's JSON API, trimmed to the fields we use, into
   `data/source/` (committed). `--current` re-pulls the two newest seasons of each sport.
2. `scripts/normalize.py`: `data/source/` → `data/games/<sport>.json`. Tags each event `official`,
   `exhibition`, `intrasquad`, `event` or `scheduled`; only `official` counts. Then applies
   `data/overrides.json`.
3. `scripts/build_official.py`: official season records from UVA record-book PDFs (and Wikipedia
   for MBB) → `data/official.csv`. Run yearly when new books come out, and review the diff.
4. `scripts/validate.py`: games vs official → `data/validation.json`. Exits 1 on any mismatch.
5. `scripts/build_coaches.py`: `data/coaches.csv` (coach ranges). Record books first (typed into
   the script), rosters only for seasons after the latest book.
6. `scripts/build_site.py`: `site-data/` for the pages (seasons, slim per-sport games, opponents,
   highlights). Opponent names are cleaned by `scripts/opponents.py` (rules plus
   `data/aliases.json`); run `scripts/opponents.py` to list names that may still need an alias.

`data/raw/books/` (gitignored) caches the record-book PDFs for build_official.py.
`.github/workflows/refresh.yml` runs steps 1, 2, 4 and 6 daily and commits on change; a
validation mismatch still publishes, then fails the run so it gets noticed.

## Site

Static pages at the repo root: `index.html` (dashboard), `sport.html`, `opponents.html`,
`highlights.html`, shared `common.js` and `style.css`. No build step. Test locally with
`.venv/bin/python -m http.server` and open http://localhost:8000.
- Look (v0.2, 2026-10-28): "Varsity", picked by Rudy from four mockups so the site stops sharing
  the h2h/te-tracker template. Graduate (slab numerals) + Archivo, square 2px navy frames, the
  navy-white-orange sweater stripe under the header and on each tile's cuff, no dark top bar
  (Rudy rejects those as too like his other sites). Don't copy another project's style.css here.
- Dashboard tiles are grouped Fall / Winter / Spring (`term` in sports.json), with column counts
  picked so no tile sits alone on a row.
- No hover tooltips (Rudy's preference): the win % chart prints each season's value on its
  column (sideways on phones), and clicking a column opens that season.
- † = incomplete season (official record, partial games); ‡ = game corrected or added from a book.

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
