// Driver page: numbered steps and a schematic campus map drawn in SVG (no map tiles).
const out = document.getElementById("out");
const held = document.getElementById("held");
const motion = !matchMedia("(prefers-reduced-motion: reduce)").matches;
const SVG = "http://www.w3.org/2000/svg";
let lastSearch = null;
let geo = {lots: [], destinations: []};
let pos = {};          // id or destination name -> {x, y}
let rank = {};         // lot id -> walking order in the current search
let heldLot = null;

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}

async function call(url, body) {
  const r = await fetch(url, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)
  });
  if (r.status === 422) return {error: "Check the form: the arrival needs a time and the stay at least one hour."};
  if (!r.ok) return {error: "Something went wrong on our side, so nothing was booked. Try again in a moment."};
  return r.json();
}

function trip() {
  return {
    driver_id: document.getElementById("driver").value.trim(),
    destination: document.getElementById("destination").value,
    arrival: document.getElementById("arrival").value,
    hours: Number(document.getElementById("hours").value)
  };
}

/* ------------------------------------------------------------ schematic map */
const W = 720, H = 520, PAD = 70, STEP = 40;   // STEP: the construction grid every node snaps to

function el(tag, attrs, text) {
  const n = document.createElementNS(SVG, tag);
  Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
  if (text !== undefined) n.textContent = text;
  return n;
}

function layout() {
  // Start from the real geography (equal metres on both axes), then push apart nodes that sit too
  // close to read, the way a transit diagram does. The result keeps who is north, east or near of
  // whom, but it is not to scale.
  const pts = [...geo.lots.map(l => ({id: l.pool_id, lat: l.lat, lon: l.lon})),
               ...geo.destinations.map(d => ({id: d.name, lat: d.lat, lon: d.lon}))];
  const lat0 = pts.reduce((a, p) => a + p.lat, 0) / pts.length;
  pts.forEach(p => { p.x = p.lon * 111320 * Math.cos(lat0 * Math.PI / 180); p.y = -p.lat * 110540; });
  const fit = () => {
    const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
    const minX = Math.min(...xs), minY = Math.min(...ys);
    const k = Math.min((W - 2 * PAD) / (Math.max(...xs) - minX || 1), (H - 2 * PAD) / (Math.max(...ys) - minY || 1));
    pts.forEach(p => { p.x = PAD + (p.x - minX) * k; p.y = PAD + (p.y - minY) * k; });
  };
  fit();
  const MIN = 120;
  for (let round = 0; round < 200; round++) {
    let moved = false;
    for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
      const a = pts[i], b = pts[j];
      let dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 0.01;
      if (d < MIN) {
        const push = (MIN - d) / 2;
        dx /= d; dy /= d;
        a.x -= dx * push; a.y -= dy * push; b.x += dx * push; b.y += dy * push;
        moved = true;
      }
    }
    if (!moved) break;
  }
  fit();
  const snap = v => Math.round(v / STEP) * STEP;
  pts.forEach(p => { pos[p.id] = {x: snap(p.x), y: snap(p.y)}; });
}

function drawMap() {
  const fig = document.getElementById("map");
  layout();
  // On a narrow screen the diagram shrinks; scale marks and type back up so they stay readable.
  const k = Math.min(2, Math.max(1, 0.62 * W / (fig.clientWidth || W)));
  const R = 15 * k;
  const svg = el("svg", {viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true", style: `--k: ${k}`});
  for (let x = STEP; x < W; x += STEP) svg.appendChild(el("line", {x1: x, y1: 0, x2: x, y2: H, class: "grid-line"}));
  for (let y = STEP; y < H; y += STEP) svg.appendChild(el("line", {x1: 0, y1: y, x2: W, y2: y, class: "grid-line"}));
  svg.appendChild(el("text", {x: W - 24, y: 40, class: "north", "text-anchor": "middle"}, "N"));
  svg.appendChild(el("path", {d: `M${W - 24} 48 L${W - 24} 76`, class: "north-line"}));
  svg.appendChild(el("g", {id: "walk-layer"}));

  const chosen = document.getElementById("destination").value;
  geo.destinations.forEach(d => {
    const p = pos[d.name], on = d.name === chosen;
    const h = 9 * k;
    svg.appendChild(el("rect", {x: p.x - h, y: p.y - h, width: 2 * h, height: 2 * h, class: "dest-sq" + (on ? " chosen" : "")}));
    svg.appendChild(el("text", {x: p.x + h + 8, y: p.y + 6 * k, class: "dest-label" + (on ? " chosen" : "")}, d.name));
  });
  geo.lots.forEach(l => {
    const p = pos[l.pool_id], n = rank[l.pool_id];
    const g = el("g", {class: "lot-hit", "data-lot": l.pool_id});
    const state = l.pool_id === heldLot ? " held" : n ? " allowed" : "";
    g.appendChild(el("circle", {cx: p.x, cy: p.y, r: R, class: "lot-ring" + state, id: "ring-" + l.pool_id}));
    if (n) g.appendChild(el("text", {x: p.x, y: p.y + 1, class: "lot-num"}, n));
    g.appendChild(el("text", {x: p.x + R + 7, y: p.y - R + 3, class: "lot-label" + (n ? "" : " off")}, l.name));
    g.addEventListener("mouseenter", () => n && point(l.pool_id));
    g.addEventListener("click", () => {
      const row = document.querySelector(`.lot[data-lot="${l.pool_id}"]`);
      if (row) { row.scrollIntoView({behavior: motion ? "smooth" : "auto", block: "center"}); point(l.pool_id); }
    });
    svg.appendChild(g);
  });
  fig.innerHTML = "";
  fig.appendChild(svg);
  fig.insertAdjacentHTML("beforeend", `<p class="scale">Schematic, not to scale. Walking times are estimates.</p>`);
  if (heldLot) walkLine(heldLot, true, false);
}

function walkLine(lotId, isHeld, animate) {
  const layer = document.getElementById("walk-layer");
  if (!layer) return;
  layer.innerHTML = "";
  const a = pos[lotId], b = pos[lastSearch?.trip.destination];
  if (!a || !b) return;
  // Transit-diagram walk: 45 degrees first, then straight.
  const dx = b.x - a.x, dy = b.y - a.y, d = Math.min(Math.abs(dx), Math.abs(dy));
  const mid = {x: a.x + Math.sign(dx) * d, y: a.y + Math.sign(dy) * d};
  layer.appendChild(el("path", {d: `M${a.x} ${a.y} L${mid.x} ${mid.y} L${b.x} ${b.y}`,
                                class: "walk" + (isHeld ? " held" : "") + (animate && motion ? " draw" : "")}));
  const minutes = lastSearch.minutes[lotId];
  if (minutes !== null && minutes !== undefined) {
    // Label the longer of the two segments at its middle, set off to one side of the line.
    const first = Math.hypot(mid.x - a.x, mid.y - a.y), second = Math.hypot(b.x - mid.x, b.y - mid.y);
    const [p, q] = first >= second ? [a, mid] : [mid, b];
    const len = Math.hypot(q.x - p.x, q.y - p.y) || 1;
    const nx = -(q.y - p.y) / len, ny = (q.x - p.x) / len;
    const side = nx >= 0 ? 1 : -1;
    layer.appendChild(el("text", {x: (p.x + q.x) / 2 + side * nx * 22, y: (p.y + q.y) / 2 + side * ny * 22 + 7,
                                  class: "walk-min" + (isHeld ? " held" : ""), "text-anchor": side > 0 ? "start" : "end"},
                         `${minutes} min`));
  }
}

function point(lotId) {
  if (heldLot) return;
  document.querySelectorAll(".lot").forEach(r => r.classList.toggle("active", r.dataset.lot === lotId));
  document.querySelectorAll(".lot-ring.allowed, .lot-ring.active").forEach(c =>
    c.setAttribute("class", "lot-ring " + (c.id === "ring-" + lotId ? "active" : "allowed")));
  walkLine(lotId, false, true);
}

/* ------------------------------------------------------------ steps */
fetch("/api/destinations").then(r => r.json()).then(async d => {
  const sel = document.getElementById("destination");
  sel.innerHTML = d.destinations.map(x => `<option>${esc(x)}</option>`).join("");
  geo = await (await fetch("/api/map")).json();
  drawMap();
  sel.addEventListener("change", drawMap);
});

function ticks(remaining, capacity) {
  const taken = capacity - remaining;
  return `<div class="ticks" role="img" aria-label="${remaining} of ${capacity} places free for your whole stay">` +
    Array.from({length: capacity}, (_, i) => `<i class="${i >= capacity - taken ? "held" : ""}"></i>`).join("") + "</div>";
}

async function findParking(e) {
  e.preventDefault();
  heldLot = null;
  out.innerHTML = `<h2>Lots</h2><p class="empty">Checking your permit and the lots near ${esc(trip().destination)}…</p>`;
  const res = await call("/api/options", trip());
  const permit = document.getElementById("permit");
  if (res.error) {
    permit.classList.remove("on");
    rank = {};
    lastSearch = null;
    drawMap();
    out.innerHTML = `<h2>Lots</h2><p class="notice">${esc(res.error)}</p>`;
    return;
  }
  const t = trip();
  lastSearch = {trip: t, search_id: res.search_id, minutes: {}};
  rank = {};
  res.options.forEach((o, i) => { rank[o.lot_id] = i + 1; lastSearch.minutes[o.lot_id] = o.walk_minutes; });
  permit.innerHTML = `Permit checked: <b>${esc(res.permit)}</b>, ${esc(res.start)} to ${esc(res.end)}`;
  permit.classList.add("on");
  drawMap();

  if (!res.options.length) {
    out.innerHTML = `<h2>Lots</h2><p class="notice">Nothing your ${esc(res.permit)} permit allows is free for the
      whole of ${esc(res.start)} to ${esc(res.end)}. ${esc(res.reason || "")} Try another time or a shorter stay.</p>`;
    return;
  }
  out.innerHTML = `<h2>${res.options.length === 1 ? "One lot" : `${res.options.length} lots`} for ${esc(t.destination)}</h2>
    <ol class="lots">` + res.options.map(o => `
      <li class="lot" data-lot="${esc(o.lot_id)}" onmouseenter="point('${esc(o.lot_id)}')" onfocusin="point('${esc(o.lot_id)}')">
        <div class="min">${o.walk_minutes === null ? "–" : o.walk_minutes}<span class="min-unit">${o.walk_minutes === null ? "walk unknown" : "min walk"}</span></div>
        <div>
          <h3>${esc(o.name)}</h3>
          <p class="addr">${esc(o.address || "Address unavailable")}</p>
        </div>
        <div class="free">${o.remaining}<small>/${o.capacity}</small><span class="free-unit">free all stay</span></div>
        ${ticks(o.remaining, o.capacity)}
        <details><summary>Why this lot was offered</summary>
          <ul>${o.facts.map(f => `<li>${esc(f)}</li>`).join("")}</ul></details>
        <button class="hold" onclick="reserve(this, '${esc(o.lot_id)}')">Hold a place here</button>
      </li>`).join("") + `</ol><p class="note">${esc(res.capacity_basis)}</p>`;
}

function heldBlock(res, heading) {
  return `<div class="held-block">
      <h3>${esc(heading)}</h3>
      <p class="code">${esc(res.confirmation)}</p>
      <dl>
        <dt>Lot</dt><dd>${esc(res.lot)}</dd>
        <dt>When</dt><dd>${esc(res.start)} to ${esc(res.end)}</dd>
        <dt>Address</dt><dd>${esc(res.address)}</dd>
        <dt>Getting there</dt><dd>${res.guidance ? esc(res.guidance) : "Route guidance unavailable"}</dd>
      </dl>
      ${res.warning ? `<p class="warn">${esc(res.warning)}</p>` : ""}
      <p class="note">${esc(res.note)}</p>
    </div>`;
}

async function reserve(button, lotId) {
  button.disabled = true;
  button.textContent = "Holding your place…";
  const res = await call("/api/reserve", {...lastSearch.trip, lot_id: lotId, search_id: lastSearch.search_id,
                                          request_id: crypto.randomUUID()});
  if (res.error) {
    button.disabled = false;
    button.textContent = "Try again";
    button.insertAdjacentHTML("beforebegin", `<p class="refusal">${esc(res.error)}</p>`);
    return;
  }
  heldLot = lotId;
  drawMap();
  walkLine(lotId, true, true);
  held.innerHTML = heldBlock(res, `Held at ${res.lot}.`) +
    `<button class="plain" onclick="document.getElementById('trip').requestSubmit()">Search again</button>`;
  document.getElementById("lookup").scrollIntoView({behavior: motion ? "smooth" : "auto", block: "start"});
}

async function findBooking(e) {
  e.preventDefault();
  const id = encodeURIComponent(document.getElementById("lookup-id").value.trim());
  const driver = encodeURIComponent(document.getElementById("lookup-driver").value.trim());
  const res = await call(`/api/reservations/${id}?driver_id=${driver}`);
  held.innerHTML = res.error
    ? `<p class="notice">${esc(res.error)} Check the number on your confirmation and the ID you booked with.</p>`
    : heldBlock(res, `Your booking at ${res.lot}.`);
}
