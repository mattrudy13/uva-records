# UVA Records: spec

Game-by-game results for every UVA head-to-head varsity sport since 2000-01, published as a
static site at mattrudy13.github.io/uva-records/. Unofficial fan project; no UVA logos.

## Decisions (2026-10-17)

| Topic | Decision |
|---|---|
| Unit of data | Every game: date, opponent, venue, score, W/L/T, conference flag, tournament, rankings |
| Sports | Football, M/W basketball, baseball, softball, M/W soccer, M/W lacrosse, field hockey, volleyball, M/W tennis, wrestling, M/W squash (2017-18 on) |
| Window | Academic 2000-01 to now (all the source has) |
| Source | virginiasports.com public JSON API (`/website-api`), used for all sports, football and basketball included |
| Edge games | Only official W-L-T games count. Exhibitions, intrasquad games and non-dual events are kept but tagged, and hidden by default |
| Mismatches | The official record wins. `data/overrides.json` fixes extra or wrong games and adds single missing ones. Seasons missing many games are flagged incomplete: the site shows the official record with a note and leaves them out of streaks |
| Unverified | Women's lacrosse has no official year-by-year source, so it's shown with a "not checked" note |
| Season labels | Fall sports "2005", spring sports "2006", winter sports "2005-06" |
| Extras | Postseason tags (ACC / NCAA / bowl), head coach (hand-kept `data/coaches.csv`), rankings at game time |
| Site | Sport page, all-sports dashboard, opponent records, streaks and highlights |
| Style | UVA navy and orange on a light layout, dark mode, an accent color per sport |
| Refresh | Daily GitHub Action that re-pulls only in-season sports and commits only on change |

## Source notes

- `GET /website-api/schedules` lists every schedule (`"Baseball 2005-06"`, `sport_id`).
- `GET /website-api/schedule-events?filter[schedule_id]=ID&include=scheduleEventResult,tournament`
  returns events with `venue_type`, `neutral_event`, `is_conference`, `is_exhibition`, `ranking`,
  `opponent_ranking`, `status`, and the result (`result`, `winning_score`, `losing_score`, `text`).
- Known quirks: fall intrasquad games are filed under the previous spring's season and aren't
  flagged as exhibitions, and some ties are missing.
- stats.ncaa.org blocks automated requests, so it isn't used. Official season records come from
  Wikipedia where it has them, otherwise from UVA media guides and record books.

## Build order

1. Scraper + normalizer + validation against official records (this phase).
2. Site pages on top of `data/games/*.json`.
3. GitHub Action for the daily refresh.
