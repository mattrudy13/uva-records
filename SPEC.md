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
| Style | UVA navy and orange on a light layout, dark mode, an accent color per sport (replaced 2026-10-28, see Redesign) |
| Refresh | Daily GitHub Action that re-pulls only in-season sports and commits only on change |

## Site decisions (2026-10-19)

| Topic | Decision |
|---|---|
| Home | All-sports dashboard. Opens on the current academic year (live): in-progress sports are marked, and sports that haven't started show their first game date plus last season's record, greyed out. Season picker back to 2000-01. Combined all-sports record |
| VT rivalry | Dashboard panel: this year's UVA vs. VT head-to-head in every sport plus all-time totals, linking to VT's opponent page |
| Sport page | Win % by season chart, then a season table (W-L-T, ACC, coach, postseason). A season row expands in place into its game list; `?season=` links straight to it |
| Opponents | One page per school: all-sports record, per-sport breakdown, last meeting, streak, games. Names are cleaned by rules plus a reviewed alias file, with a report of leftovers |
| Highlights | Win streaks (longest and current; incomplete seasons break streaks), best and worst seasons, ranked wins (labeled "since 2020-21", the only years with rankings), biggest wins and losses per sport |
| Caveats | † next to the record, plus an always-visible footnote under the table. No tooltips |
| Build | Same as h2h: plain HTML/CSS/JS, no build step, hand-built charts (SVG sparklines, HTML win % chart since v0.2), per-sport JSON loaded on demand |

## Redesign (2026-10-28, v0.2)

Same features and data; new look and layout, so the site stops sharing the h2h/te-tracker template.

| Topic | Decision |
|---|---|
| Direction | "Varsity", picked from four mockups (Colonnade, Almanac, Varsity, Record Book): the letter sweater |
| Type | Graduate (collegiate slab) for headings and records, Archivo for everything else |
| Look | White ground (dark theme from the system setting), square 2px navy frames, no shadows, no dark top bar. The navy-white-orange sweater stripe runs under the header and along each tile's cuff |
| Dashboard | Totals in a framed scorebox; sport tiles grouped Fall / Winter / Spring, sized so no tile sits alone on a row; teams that haven't started show last season's record in outline; VT panel as a scoreline |
| Win % chart | Every column carries its value (sideways on phones), with a y-axis and a dashed .500 line. Picked over a click-to-read box and bars inside the table. Built in HTML/CSS so labels keep their size on phones |
| Dropdowns | Custom chevron with room from the border (the browser's arrow hugged the edge) |

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
