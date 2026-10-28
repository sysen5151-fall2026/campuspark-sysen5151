// Search results: the list on the left, a live campus map on the right, lot details opening in place.
// The map is a real map (OpenFreeMap tiles) with Cornell's real buildings raised from OpenStreetMap.
import { api, esc, session, destinations, lotImageStyle, lotPhotoStyle } from "/static/common.js";

const $ = id => document.getElementById(id);
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const params = new URLSearchParams(location.search);
const trip = {
  driver_id: session.driver,
  destination: params.get("to") || "",
  arrival: params.get("at") || "09:00",
  hours: Number(params.get("hours") || 2),
};
const AMBER = "#ffb547";
const STYLES = {night: "https://tiles.openfreemap.org/styles/dark", day: "https://tiles.openfreemap.org/styles/positron"};
let theme = "night";
let geo = {lots: {}, dests: {}};
let found = null, map = null, markers = {}, destMarker = null;
let selected = null, hovered = null, orbit = false;
const beams = {};      // lot id -> {now, target} heights in metres
let walk = null;       // {coords, t0} for the arched trail being shown

/* ------------------------------------------------------------------ geometry */
function circle(lon, lat, metres, steps = 40) {
  const pts = [], k = metres / 111320, kx = k / Math.cos(lat * Math.PI / 180);
  for (let i = 0; i <= steps; i++) {
    const a = (i / steps) * Math.PI * 2;
    pts.push([lon + kx * Math.cos(a), lat + k * Math.sin(a)]);
  }
  return [pts];
}

// An arch between two points, bowed sideways like a route drawn on a game map.
function arch(a, b, n = 64) {
  const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const c = [mx - dy * 0.28, my + dx * 0.28];
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, u = 1 - t;
    out.push([u * u * a[0] + 2 * u * t * c[0] + t * t * b[0], u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]]);
  }
  return out;
}

const empty = {type: "FeatureCollection", features: []};

const ICON = {
  walk: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="13" cy="4" r="2"/><path d="M10 21l2-6 3 3v3M7 12l3-4 4 1 3 3M12 9l-1 5"/></svg>',
  park: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><path d="M10 17V7h3a3 3 0 0 1 0 6h-3"/></svg>',
  clock: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
  back: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
};

/* ------------------------------------------------------------------ the map */
function addWorld() {
  const night = theme === "night";
  const firstLabel = map.getStyle().layers.find(l => l.type === "symbol")?.id;
  map.addLayer({
    id: "buildings-3d", type: "fill-extrusion", source: "openmaptiles", "source-layer": "building", minzoom: 13.5,
    paint: {
      "fill-extrusion-color": night
        ? ["interpolate", ["linear"], ["coalesce", ["get", "render_height"], 6], 0, "#2b313d", 40, "#414a5c"]
        : ["interpolate", ["linear"], ["coalesce", ["get", "render_height"], 6], 0, "#e6e6ea", 40, "#d4d5dc"],
      "fill-extrusion-height": ["coalesce", ["get", "render_height"], 6],
      "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
      "fill-extrusion-opacity": night ? 0.95 : 0.92,
      "fill-extrusion-vertical-gradient": true,
    },
  }, firstLabel);
  map.addSource("glow", {type: "geojson", data: empty});
  map.addLayer({id: "glow", type: "circle", source: "glow", paint: {
    "circle-radius": ["get", "r"], "circle-color": AMBER, "circle-blur": 1, "circle-opacity": ["get", "o"]}});
  map.addSource("beams", {type: "geojson", data: empty});
  map.addLayer({id: "beams", type: "fill-extrusion", source: "beams", paint: {
    "fill-extrusion-color": ["get", "color"], "fill-extrusion-height": ["get", "h"], "fill-extrusion-base": 0,
    "fill-extrusion-opacity": 0.9}});
  map.addSource("walk", {type: "geojson", data: empty});
  map.addLayer({id: "walk-glow", type: "line", source: "walk", layout: {"line-cap": "round", "line-join": "round"},
                paint: {"line-color": night ? AMBER : "#0071e3", "line-width": 14, "line-blur": 10, "line-opacity": 0.55}});
  map.addLayer({id: "walk", type: "line", source: "walk", layout: {"line-cap": "round", "line-join": "round"},
                paint: {"line-width": 4, "line-color": night ? "#ffe2b0" : "#0071e3", "line-dasharray": [0, 2, 2]}});
  map.addSource("comet", {type: "geojson", data: empty});
  map.addLayer({id: "comet", type: "circle", source: "comet", paint: {
    "circle-radius": 7, "circle-color": "#ffffff", "circle-blur": 0.4, "circle-stroke-width": 6,
    "circle-stroke-color": night ? "rgba(255,181,71,.45)" : "rgba(0,113,227,.35)"}});
  drawBeams(true);
  if (walk) setWalk(walk.lot, false);
}

function initMap() {
  map = new maplibregl.Map({
    container: "map", style: STYLES[theme],
    center: [-76.476, 42.452], zoom: 13.2, pitch: 0, bearing: 0, attributionControl: {compact: true},
  });
  map.addControl(new maplibregl.NavigationControl({visualizePitch: true}), "top-right");
  map.addControl(new MapSwitches(), "top-right");
  ["dragstart", "zoomstart", "rotatestart", "pitchstart", "wheel"].forEach(ev => map.on(ev, e => { if (e.originalEvent) orbit = false; }));
  map.on("style.load", addWorld);
  map.once("style.load", () => $("map-loading")?.remove());   // tiles then fade in; "idle" never fires while beams animate
  return new Promise(res => map.once("load", res));
}

function drawBeams(instant) {
  if (!map?.getSource("beams")) return;
  const allowed = Object.fromEntries((found?.options || []).map(o => [o.lot_id, o]));
  Object.values(geo.lots).forEach(l => {
    const o = allowed[l.pool_id];
    const b = beams[l.pool_id] || (beams[l.pool_id] = {now: 0, target: 0});
    b.target = o ? 40 + 160 * (o.remaining / o.capacity) : 0;
    if (instant || reduced) b.now = b.target;
  });
}

function beamFrame(t) {
  const allowed = Object.fromEntries((found?.options || []).map(o => [o.lot_id, o]));
  const feats = [], glows = [];
  // beams keep a similar size on screen: shorter as the camera comes closer
  const scale = Math.min(1.2, Math.max(0.18, Math.pow(2, 14.6 - map.getZoom())));
  Object.values(geo.lots).forEach(l => {
    const b = beams[l.pool_id];
    if (!b) return;
    b.now += (b.target - b.now) * 0.06;
    if (b.now < 0.5) return;
    const on = l.pool_id === selected || l.pool_id === hovered;
    feats.push({type: "Feature", properties: {h: b.now * scale, color: on ? "#ffc65a" : "#ff9a1f"},
                geometry: {type: "Polygon", coordinates: circle(l.lon, l.lat, on ? 24 : 19)}});
    const pulse = reduced ? 0.5 : 0.5 + 0.5 * Math.sin(t / 520 + l.lat * 900);
    if (allowed[l.pool_id]) glows.push({type: "Feature", properties: {r: 26 + 14 * pulse, o: 0.28 + 0.2 * pulse},
                                        geometry: {type: "Point", coordinates: [l.lon, l.lat]}});
  });
  map.getSource("beams")?.setData({type: "FeatureCollection", features: feats});
  map.getSource("glow")?.setData({type: "FeatureCollection", features: glows});
}

function setWalk(lotId, animate = true) {
  const l = geo.lots[lotId], d = geo.dests[trip.destination];
  if (!map?.getSource("walk")) { walk = l && d ? {lot: lotId} : null; return; }
  if (!l || !d) { walk = null; map.getSource("walk").setData(empty); map.getSource("comet").setData(empty); return; }
  const coords = arch([l.lon, l.lat], [d.lon, d.lat]);
  walk = {lot: lotId, coords, t0: performance.now(), grow: animate && !reduced};
}

let dashStep = 0;
const DASHES = [[0, 2, 2], [0.5, 2, 1.5], [1, 2, 1], [1.5, 2, 0.5], [2, 2, 0], [0, 0.5, 2, 1.5], [0, 1, 2, 1], [0, 1.5, 2, 0.5]];
function walkFrame(t) {
  if (!walk?.coords || !map?.getSource("walk")) return;
  const grow = walk.grow ? Math.min(1, (t - walk.t0) / 900) : 1;
  const n = Math.max(2, Math.round(walk.coords.length * grow));
  map.getSource("walk").setData({type: "Feature", geometry: {type: "LineString", coordinates: walk.coords.slice(0, n)}});
  if (!reduced) {
    const step = Math.floor(t / 90) % DASHES.length;
    if (step !== dashStep) { dashStep = step; map.setPaintProperty("walk", "line-dasharray", DASHES[step]); }
    const k = ((t - walk.t0) / 2600) % 1;
    const p = walk.coords[Math.floor(k * (walk.coords.length - 1))];
    map.getSource("comet").setData({type: "Feature", geometry: {type: "Point", coordinates: p}});
  } else {
    map.getSource("comet").setData(empty);
  }
}

function loop(t) {
  if (map) {
    beamFrame(t);
    walkFrame(t);
    if (orbit && !reduced && !map.isMoving()) map.setBearing(map.getBearing() + 0.035);
  }
  requestAnimationFrame(loop);
}

function fit(ids, intro) {
  const pts = ids.map(id => geo.lots[id]).filter(Boolean);
  const d = geo.dests[trip.destination];
  if (d) pts.push(d);
  if (!pts.length || !map) return;
  const b = new maplibregl.LngLatBounds();
  pts.forEach(p => b.extend([p.lon, p.lat]));
  const wide = window.innerWidth > 900;
  const cam = map.cameraForBounds(b, {padding: {top: wide ? 170 : 90, bottom: 90, left: wide ? 520 : 60, right: 90}, maxZoom: 16.2});
  if (!cam) return;
  const shot = {...cam, pitch: 58, bearing: -22};
  if (reduced) map.jumpTo(shot);
  else map.flyTo({...shot, duration: intro ? 2600 : 1400, curve: 1.4, essential: true});
}

function placeMarkers() {
  if (!map) return;
  Object.values(markers).forEach(m => m.remove());
  markers = {};
  destMarker?.remove();
  const d = geo.dests[trip.destination];
  if (d) {
    const el = document.createElement("div");
    el.className = "mk-dest";
    el.innerHTML = `<i></i><span>${esc(trip.destination)}</span>`;
    destMarker = new maplibregl.Marker({element: el, anchor: "left", offset: [-8, 0]}).setLngLat([d.lon, d.lat]).addTo(map);
  }
  const allowed = Object.fromEntries((found?.options || []).map(o => [o.lot_id, o]));
  Object.values(geo.lots).forEach(l => {
    const o = allowed[l.pool_id];
    const el = document.createElement("button");
    el.type = "button";
    el.className = "mk" + (o ? "" : " off");
    el.textContent = o ? (o.walk_minutes === null ? "Walk ?" : `${o.walk_minutes} min`) : "";
    el.title = o ? l.name : `${l.name}: not for your permit`;
    el.setAttribute("aria-label", el.title);
    if (o) {
      el.addEventListener("click", () => openDetail(l.pool_id));
      el.addEventListener("mouseenter", () => hot(l.pool_id));
    }
    markers[l.pool_id] = new maplibregl.Marker({element: el, anchor: "bottom", offset: [0, -6]}).setLngLat([l.lon, l.lat]).addTo(map);
  });
  if (selected) { select(selected); hot(selected); }
}

function hot(lotId) {
  hovered = lotId;
  document.querySelectorAll(".res").forEach(r => r.classList.toggle("hot", r.dataset.lot === lotId));
  Object.entries(markers).forEach(([id, m]) => m.getElement().classList.toggle("hot", id === lotId));
  if (!walk || walk.lot !== lotId) setWalk(lotId, true);
}

function select(lotId) {
  selected = lotId;
  Object.entries(markers).forEach(([id, m]) => m.getElement().classList.toggle("on", id === lotId));
}

// Two switches beside the zoom buttons: 2D/3D and night/day.
class MapSwitches {
  onAdd(m) {
    this.el = document.createElement("div");
    this.el.className = "maplibregl-ctrl maplibregl-ctrl-group";
    const dim = document.createElement("button"), mode = document.createElement("button");
    [dim, mode].forEach(b => { b.type = "button"; b.className = "dim-toggle"; this.el.appendChild(b); });
    const label = () => {
      dim.textContent = m.getPitch() > 5 ? "2D" : "3D";
      dim.title = `Switch to ${dim.textContent} view`;
      mode.textContent = theme === "night" ? "☀︎" : "☾";
      mode.title = theme === "night" ? "Day map" : "Night map";
    };
    dim.addEventListener("click", () => {
      const flat = m.getPitch() > 5;
      orbit = false;
      m.easeTo({pitch: flat ? 0 : 58, bearing: flat ? 0 : -22, duration: 900});
    });
    mode.addEventListener("click", () => {
      theme = theme === "night" ? "day" : "night";
      document.body.classList.toggle("map-day", theme === "day");
      m.setStyle(STYLES[theme]);
      label();
    });
    m.on("pitchend", label);
    label();
    return this.el;
  }
  onRemove() { this.el.remove(); }
}

/* ------------------------------------------------------------------ the list */
function availClass(o) { return o.remaining / o.capacity < 0.2 ? "avail low" : "avail"; }
function at(id) { return geo.lots[id] || {}; }

function renderList() {
  const opts = found.options;
  $("title").textContent = opts.length ? `${opts.length === 1 ? "One lot" : `${opts.length} lots`} for your trip` : "No lot fits this trip";
  $("subtitle").textContent = `${trip.destination}, ${found.start} to ${found.end}, nearest walk first`;
  if (!opts.length) {
    $("results").innerHTML = `<div class="empty-state"><b>Nothing your ${esc(found.permit)} permit allows is free for the whole stay.</b>
      ${esc(found.reason || "")} Try an earlier or later arrival, or a shorter stay.</div>`;
    return;
  }
  const most = opts.reduce((a, o) => (o.remaining > a.remaining ? o : a), opts[0]);
  $("results").innerHTML = opts.map((o, i) => {
    const tags = [i === 0 && o.walk_minutes !== null ? "Closest walk" : "", o === most && opts.length > 1 ? "Most room" : ""].filter(Boolean);
    return `
    <li class="res" data-lot="${esc(o.lot_id)}" tabindex="0">
      <div class="thumb" style="${lotPhotoStyle(o.lot_id, at(o.lot_id).lat, at(o.lot_id).lon, 336, 252)}"></div>
      <div class="res-body">
        ${tags.length ? `<div class="tags">${tags.map(t => `<span>${t}</span>`).join("")}</div>` : ""}
        <h3>${esc(o.name)}</h3>
        <div class="meta">${esc(o.address || "Address unavailable")}</div>
        <div class="facts">
          <span>${ICON.walk}<b>${o.walk_minutes === null ? "–" : o.walk_minutes}</b> min</span>
          <span>${ICON.park}<b>${o.remaining}</b>/${o.capacity} free</span>
        </div>
      </div>
    </li>`;
  }).join("") + `<p class="credit">Lot photos are illustrative. Open a lot for its real aerial view.</p>`;
  document.querySelectorAll(".res").forEach(li => {
    li.addEventListener("mouseenter", () => hot(li.dataset.lot));
    li.addEventListener("focus", () => hot(li.dataset.lot));
    li.addEventListener("click", () => openDetail(li.dataset.lot));
    li.addEventListener("keydown", e => { if (e.key === "Enter") openDetail(li.dataset.lot); });
  });
}

function openDetail(lotId) {
  const o = found.options.find(x => x.lot_id === lotId);
  if (!o) return;
  hot(lotId);
  select(lotId);
  const l = geo.lots[lotId];
  if (l && map) {
    orbit = false;
    const shot = {center: [l.lon, l.lat], zoom: 16.3, pitch: 60, bearing: map.getBearing() + 35,
                  padding: {left: window.innerWidth > 900 ? 480 : 0, top: 60, right: 0, bottom: 0}};
    if (reduced) map.jumpTo(shot);
    else { map.flyTo({...shot, duration: 1600, curve: 1.3, essential: true}); map.once("moveend", () => { if (selected === lotId) orbit = true; }); }
  }
  const free = Math.round(100 * o.remaining / o.capacity);
  const walkTxt = o.walk_minutes === null ? "No estimate" : `${o.walk_minutes} min`;
  $("detail").innerHTML = `
    <div class="media" id="media">
      <div class="slides" id="slides">
        <div class="slide" style="${lotPhotoStyle(lotId, l?.lat, l?.lon, 960, 560)}"></div>
        <div class="slide" style="${lotImageStyle(l?.lat, l?.lon, 960, 560)}"></div>
      </div>
      <button class="fab" id="back" type="button" aria-label="Back to all lots">${ICON.back}</button>
      <div class="media-tabs" role="tablist" aria-label="Lot picture">
        <button type="button" role="tab" aria-selected="true" data-slide="0">Photo</button>
        <button type="button" role="tab" aria-selected="false" data-slide="1">Aerial</button>
      </div>
      <p class="media-credit" id="media-credit">Illustrative photo, not the actual lot</p>
    </div>
    <div class="body">
      <h2>${esc(o.name)}</h2>
      <p class="addr">${esc(o.address || "Address unavailable")}</p>
      <div class="quick">
        <div>${ICON.walk}<b>${walkTxt}</b><span>to ${esc(trip.destination)}</span></div>
        <div>${ICON.park}<b>${o.remaining} free</b><span>of ${o.capacity}, whole stay</span></div>
        <div>${ICON.clock}<b>${esc(found.start)}–${esc(found.end)}</b><span>today</span></div>
      </div>

      <section class="block">
        <h4>Places for your stay <small>${free}% free</small></h4>
        <div class="cells" role="img" aria-label="${o.remaining} of ${o.capacity} places free for your whole stay">
          ${Array.from({length: o.capacity}, (_, i) => `<i class="${i >= o.remaining ? "taken" : ""}"></i>`).join("")}
        </div>
        <p class="hint">Each square is one place. Filled ones are already held at some point in your stay.</p>
      </section>

      <section class="block">
        <h4>Why this lot was offered</h4>
        <ul class="checks">${o.facts.map(f => `<li>${ICON.check}<span>${esc(f)}</span></li>`).join("")}</ul>
      </section>
      <p class="credit">Lot names are pilot fixtures. Aerial view: USGS The National Map (public domain).</p>
    </div>
    <div class="dock">
      <div class="dock-sum"><b>${esc(found.start)}–${esc(found.end)} today</b><span>${esc(o.name)} · ${walkTxt} walk</span></div>
      <button class="btn" id="reserve" type="button">Reserve</button>
    </div>`;
  $("detail").classList.add("open");
  document.querySelector(".side").classList.add("has-detail");
  $("back").addEventListener("click", closeDetail);
  const showSlide = n => {
    $("slides").style.transform = `translateX(${-50 * n}%)`;
    document.querySelectorAll(".media-tabs button").forEach(b => b.setAttribute("aria-selected", String(+b.dataset.slide === n)));
    $("media-credit").textContent = n ? "Real aerial view of this spot" : "Illustrative photo, not the actual lot";
  };
  document.querySelectorAll(".media-tabs button").forEach(b => b.addEventListener("click", () => showSlide(+b.dataset.slide)));
  let x0 = null;
  $("media").addEventListener("pointerdown", e => { x0 = e.clientX; });
  $("media").addEventListener("pointerup", e => { if (x0 !== null && Math.abs(e.clientX - x0) > 40) showSlide(e.clientX < x0 ? 1 : 0); x0 = null; });
  $("reserve").addEventListener("click", () => {
    session.pending = {trip, lot: {...o, lat: l?.lat, lon: l?.lon}, start: found.start, end: found.end, permit: found.permit,
                       search_id: found.search_id, request_id: crypto.randomUUID()};
    location.href = "/review";
  });
  $("back").focus();
}

function closeDetail() {
  $("detail").classList.remove("open");
  document.querySelector(".side").classList.remove("has-detail");
  orbit = false;
  select(null);
  fit(found.options.map(o => o.lot_id));
}

/* ------------------------------------------------------------------ search */
async function search(intro) {
  $("results").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div>`;
  $("detail").classList.remove("open");
  selected = null;
  orbit = false;
  const res = await api("/api/options", trip);
  if (res.error) {
    found = null;
    $("title").textContent = "We couldn't search";
    $("subtitle").textContent = "";
    $("permit").innerHTML = "";
    $("results").innerHTML = `<div class="empty-state"><b>${esc(res.error)}</b>Check the driver ID and the trip above, then update.</div>`;
    drawBeams();
    setWalk(null);
    placeMarkers();
    return;
  }
  found = res;
  $("permit").innerHTML = `<span class="tagp">${esc(res.permit)} permit</span>checked just now`;
  renderList();
  drawBeams();
  placeMarkers();
  if (map) { fit(res.options.map(o => o.lot_id), intro); if (res.options[0]) hot(res.options[0].lot_id); }
}

$("search").addEventListener("submit", e => {
  e.preventDefault();
  Object.assign(trip, {driver_id: $("driver").value.trim(), destination: $("destination").value,
                       arrival: $("arrival").value, hours: Number($("hours").value)});
  session.driver = trip.driver_id;
  history.replaceState(null, "", `/find?${new URLSearchParams({to: trip.destination, at: trip.arrival, hours: trip.hours})}`);
  search(false);
});

(async () => {
  const [dests, mapData] = await Promise.all([destinations(), fetch("/api/map").then(r => r.json())]);
  $("destination").innerHTML = dests.map(d => `<option>${esc(d)}</option>`).join("");
  if (!trip.destination) trip.destination = dests[0];
  $("destination").value = trip.destination;
  $("driver").value = trip.driver_id;
  $("arrival").value = trip.arrival;
  $("hours").value = trip.hours;
  mapData.lots.forEach(l => { geo.lots[l.pool_id] = l; });
  mapData.destinations.forEach(d => { geo.dests[d.name] = d; });
  // the list does not wait for the map: search and map load run side by side
  const mapReady = initMap().then(() => { requestAnimationFrame(loop); })
    .catch(() => { $("map").innerHTML = '<p class="empty-state">The map could not load. The list still works.</p>'; });
  if (trip.driver_id) {
    await search(true);
    await mapReady;
    placeMarkers(); drawBeams(); if (found && !selected) { fit(found.options.map(o => o.lot_id), true); if (found.options[0]) hot(found.options[0].lot_id); }
  } else {
    $("title").textContent = "Who's driving?";
    $("results").innerHTML = `<div class="empty-state"><b>Enter your driver ID above.</b>We use it once to check your permit.</div>`;
    $("driver").focus();
    placeMarkers();
  }
})();
