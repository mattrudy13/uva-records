# Enhancements

Ideas for the site, roughly in priority order. `[x]` done, `[~]` partly done. Each note says
where the data already is, so it's clear what's a page change and what needs new data.

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
- [ ] **Home / away / neutral split**: every game has a venue (`v`: `h` home, `a` away, `n` neutral),
      so a sport's season row or an opponent page can show "X-Y home, X-Y away, X-Y neutral".
- [ ] **Postseason history**: one table per sport of ACC tournament, NCAA and bowl results by
      season. The per-season counts are already in `seasons.json` (`post`), and the games carry
      their tournament name, so this is a new section or page with no new data.
- [ ] **Losing streaks and droughts**: Highlights has win streaks only. Add longest losing streaks
      and the longest gap between wins over a given opponent, using the same streak code (and
      the same rule that an incomplete season breaks a streak).

## Dashboard
- [ ] **This week's games**: upcoming games are already in the per-sport game files
      (`k: "scheduled"`, with date, opponent and venue). A strip under the scorebox listing the
      next 7 days across all sports would make the dashboard worth opening mid-season.
- [ ] **Same point last year**: next to an in-progress record, last season's record after the
      same number of games (football today: 4-4 now, 7-1 after eight games in 2025). Needs only the game files.

## Trust and data
- [ ] **Show each season's check status**: `seasons.json` already has `status` (`match`,
      `unchecked`, `incomplete`), but only incomplete seasons get a mark (†). A small "checked
      against the record book" note per season would show the reconciliation work that the
      README describes.
- [ ] **CI smoke test**: after the daily refresh, load each page's JSON and fail the run if a
      required field is missing, so a format change doesn't silently blank the site (or the hub
      tile that reads these files).

## Look and feel
- [ ] **Light/dark toggle**: the site follows the system setting only. The portfolio's toggle
      (saved in the browser) could be reused; the Varsity colors are already tokens in `style.css`.
- [ ] **Opponents list sorting**: click a column (games, record, win %, last met) to sort, and a
      filter for ACC opponents (games carry an ACC flag, `c`).
