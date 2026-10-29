# Enhancements

Ideas for the site, roughly in priority order. `[x]` done, `[~]` partly done.

## Better stats
- [ ] **Records by head coach**: each coach's overall record (W-L-T, win %, ACC record,
      postseason, seasons coached) per sport, e.g. on the sport page under the seasons table.
      Every season already has its coach in `site-data/seasons.json` (from `data/coaches.csv`), so
      this is mostly a rollup in `scripts/build_site.py`. Two things to settle first:
      - Split seasons: FH 2023 is "Michele Madison / Ole Keusgen (acting)". Needs a rule
        (credit the head coach, split by game date, or leave the season out of both).
      - Missing coaches: four played seasons have no coach in the data (as of 2026-10-28):
        football 2026, volleyball 2026, women's basketball 2025-26 and men's lacrosse 2026.
        Fill them in `scripts/build_coaches.py` first, or those seasons drop out of the rollup.
