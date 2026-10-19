// Shared by every page: data loading, formatting, game rows and tables, the
// win % chart and sparklines, and the top bar and footer. Plain global
// functions, no modules or build step (same as h2h).

// ---- Small helpers ----

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function params() {
  return new URLSearchParams(location.search);
}

// Dates are stored as plain YYYY-MM-DD in Eastern time. Building them from parts
// avoids the browser shifting them a day when it parses them as UTC.
function parseDate(d) {
  const [y, m, day] = d.split("-").map(Number);
  return new Date(y, m - 1, day);
}

function fmtDate(d, withYear = true) {
  if (!d) return "";
  const opts = withYear ? { year: "numeric", month: "short", day: "numeric" } : { month: "short", day: "numeric" };
  return parseDate(d).toLocaleDateString("en-US", opts);
}

function fmtRec(r) {
  if (!r) return "";
  return r.t ? `${r.w}-${r.l}-${r.t}` : `${r.w}-${r.l}`;
}

function games(r) {
  return r ? r.w + r.l + r.t : 0;
}

function fmtPct(p) {
  if (p == null) return "";
  return p >= 1 ? "1.000" : p.toFixed(3).replace(/^0/, "");
}

function pctOf(r) {
  const n = games(r);
  return n ? (r.w + r.t / 2) / n : null;
}

function addRec(a, b) {
  return { w: a.w + b.w, l: a.l + b.l, t: a.t + b.t };
}

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function academicLabel(start) {
  return `${start}-${String(start + 1).slice(2)}`;
}

// ---- Data ----

const _cache = new Map();
function loadJSON(path) {
  if (!_cache.has(path)) {
    _cache.set(path, fetch(`site-data/${path}`).then(r => {
      if (!r.ok) throw new Error(`Couldn't load ${path} (${r.status})`);
      return r.json();
    }));
  }
  return _cache.get(path);
}

async function loadMeta() {
  const meta = await loadJSON("sports.json");
  meta.bySlug = Object.fromEntries(meta.sports.map(s => [s.slug, s]));
  return meta;
}

// Sports without any official record to check against.
const UNVERIFIED = {
  wlax: "Women's lacrosse records haven't been checked against an official source: UVA doesn't publish a year-by-year table for it.",
  msquash: "Squash records haven't been checked against an official source yet.",
  wsquash: "Squash records haven't been checked against an official source yet.",
};

// ---- Season and game formatting ----

function postText(post) {
  return Object.entries(post || {}).map(([k, r]) => `${k} ${fmtRec(r)}`).join(", ");
}

// † marks a season whose game list is incomplete; the record shown is official.
function seasonMark(row) {
  return row.status === "incomplete" ? '<span class="mark" aria-label="game list incomplete">&dagger;</span>' : "";
}

function venueWord(v) {
  return v === "a" ? "at" : v === "n" ? "vs." : "";
}

function resultCell(g) {
  if (g.k === "scheduled") return '<span class="muted">Upcoming</span>';
  if (!g.r) return '<span class="muted">&mdash;</span>';
  const score = g.u != null && g.p != null ? `${g.u}-${g.p}` : "";
  const fixed = g.f ? '<span class="mark" aria-label="corrected from the record book">&Dagger;</span>' : "";
  return `<span class="res ${g.r}">${g.r}</span> <span class="num">${score}</span>${g.n ? ` <span class="muted">(${esc(g.n)})</span>` : ""}${fixed}`;
}

function opponentCell(g) {
  const rank = g.ork && /^#?\d+$/.test(g.ork) ? `<span class="muted">#${esc(String(g.ork).replace("#", ""))}</span> ` : "";
  const name = g.os && g.o !== "Unknown opponent"
    ? `<a href="opponents.html?o=${encodeURIComponent(g.os)}">${esc(g.o)}</a>` : esc(g.o);
  const v = venueWord(g.v);
  return `${v ? `<span class="muted">${v}</span> ` : ""}${rank}${name}`;
}

function gameTags(g) {
  const tags = [];
  if (g.ps) tags.push(`<span class="tag post">${esc(g.t || g.ps.toUpperCase())}</span>`);
  else if (g.t) tags.push(`<span class="tag">${esc(g.t)}</span>`);
  if (g.c) tags.push('<span class="tag">ACC</span>');
  if (g.k === "exhibition" || g.k === "intrasquad") tags.push('<span class="tag">Exhibition</span>');
  if (g.k === "event") tags.push('<span class="tag">Event</span>');
  return tags.join("");
}

// A game table. `opts.sport` adds a sport column (opponent pages).
function gamesTable(list, opts = {}) {
  if (!list.length) return '<p class="muted">No games listed.</p>';
  const rows = list.map(g => `
    <tr class="${g.k === "official" || g.k === "scheduled" ? "" : "exh"}">
      <td class="num">${fmtDate(g.d, opts.withYear)}</td>
      ${opts.sport ? `<td>${esc(opts.sport(g))}</td>` : ""}
      <td class="wrap-ok">${opponentCell(g)}${gameTags(g)}</td>
      <td>${resultCell(g)}</td>
    </tr>`).join("");
  return `<div class="table-wrap"><table>
    <thead><tr><th>Date</th>${opts.sport ? "<th>Sport</th>" : ""}<th>Opponent</th><th>Result</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

// ---- Charts ----

// Win % by season as columns, one series, so no legend: the heading names it.
// No hover tooltips: every value is in the season table right below the chart,
// and clicking a column opens that season there.
function winPctChart(rows, onPick) {
  const W = 960, H = 220, padL = 36, padR = 8, padT = 10, padB = 26;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const band = plotW / Math.max(rows.length, 1);
  const barW = Math.min(24, band * 0.7);
  const y = p => padT + plotH * (1 - p);
  const grid = [0, .25, .5, .75, 1].map(p =>
    `<line x1="${padL}" x2="${W - padR}" y1="${y(p)}" y2="${y(p)}"></line>`).join("");
  const yLabels = [0, .5, 1].map(p =>
    `<text x="${padL - 6}" y="${y(p) + 4}" text-anchor="end">${p === 1 ? "100%" : p * 100 + "%"}</text>`).join("");
  const every = Math.ceil(rows.length / 9);
  const bars = rows.map((r, i) => {
    if (r.pct == null) return "";
    const x = padL + band * i + (band - barW) / 2;
    const top = y(r.pct), h = Math.max(plotH * r.pct, 1);
    // 4px rounded top, square at the baseline.
    const rad = Math.min(4, h, barW / 2);
    const path = `M${x},${top + h} V${top + rad} Q${x},${top} ${x + rad},${top} H${x + barW - rad} Q${x + barW},${top} ${x + barW},${top + rad} V${top + h} Z`;
    const label = `${r.season}: ${fmtRec(r.record)}, ${fmtPct(r.pct)}${r.upcoming ? " so far" : ""}`;
    return `<a href="#s-${esc(r.season)}" data-season="${esc(r.season)}" aria-label="${esc(label)}">
      <path class="bar${r.upcoming ? " part" : ""}" d="${path}"></path>
      <rect x="${padL + band * i}" y="${padT}" width="${band}" height="${plotH}" fill="transparent"></rect></a>`;
  }).join("");
  // Label every `every`th season, plus the newest one unless it would crowd the previous label.
  const last = rows.length - 1;
  const xLabels = rows.map((r, i) => (i % every === 0 && !(i !== last && last - i < every / 2 + 1 && last % every !== 0) || i === last)
    ? `<text x="${padL + band * i + band / 2}" y="${H - 8}" text-anchor="middle">${esc(r.season)}</text>` : "").join("");
  const html = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Win percentage by season">
    <g class="grid">${grid}</g><line class="half" x1="${padL}" x2="${W - padR}" y1="${y(.5)}" y2="${y(.5)}"></line>
    ${bars}<g class="axis">${yLabels}${xLabels}</g></svg>`;
  return { html, wire(root) {
    root.querySelectorAll("a[data-season]").forEach(a => a.addEventListener("click", e => {
      e.preventDefault();
      onPick(a.dataset.season);
    }));
  } };
}

// Tiny win % columns for a dashboard card: the last `n` seasons up to `uptoStart`.
function sparkline(rows, uptoStart, n = 12) {
  const list = rows.filter(r => r.start <= uptoStart && r.pct != null).slice(-n);
  if (!list.length) return "";
  const W = 200, H = 34, gap = 2, bw = (W - gap * (n - 1)) / n;
  const off = (n - list.length) * (bw + gap);
  const bars = list.map((r, i) => {
    const h = Math.max(2, r.pct * H);
    return `<rect x="${off + i * (bw + gap)}" y="${H - h}" width="${bw}" height="${h}" rx="1.5"></rect>`;
  }).join("");
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" width="100%" height="${H}" aria-hidden="true">${bars}</svg>`;
}

// ---- Page chrome ----

function renderChrome(current) {
  const tabs = [["index.html", "Dashboard"], ["sport.html", "Sports"], ["opponents.html", "Opponents"], ["highlights.html", "Highlights"]];
  document.getElementById("topbar").innerHTML = `<div class="wrap">
    <a class="wordmark" href="index.html"><span>UVA</span> Records</a>
    <nav class="tabs" aria-label="Main">${tabs.map(([href, label]) =>
      `<a href="${href}"${href === current ? ' aria-current="page"' : ""}>${label}</a>`).join("")}</nav></div>`;
}

async function renderFooter() {
  const el = document.getElementById("footer");
  let built = "";
  try { built = (await loadMeta()).built; } catch (e) { /* the page shows its own error */ }
  el.innerHTML = `<div class="wrap">
    Unofficial fan project, not affiliated with the University of Virginia. Game data from
    <a href="https://virginiasports.com">virginiasports.com</a>; season records checked against UVA's record books.
    Seasons from 2000-01 on.${built ? ` Updated ${fmtDate(built)}.` : ""}
    <a href="https://github.com/mattrudy13/uva-records">Source</a></div>`;
}

function showError(el, err) {
  el.innerHTML = `<p class="error">Something went wrong loading the data: ${esc(err.message)}</p>`;
}
