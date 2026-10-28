// Search results: the list on the left, a live campus map on the right, lot details opening in place.
// The map is a real map (OpenFreeMap tiles) with Cornell's real buildings raised from OpenStreetMap.
import { api, esc, session, destinations, lotImageStyle, lotPhotoStyle, lotPhotoCredit, lotPhotoUrl } from "/static/common.js";

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
let selected = null, hovered = null, orbit = false, orbitRate = 2, spinBtn = null;   // orbit in degrees a second
const beams = {};      // lot id -> {now, target} heights in metres
let walk = null;       // {coords, t0} for the arched trail being shown
// The animation sends new map data only when something changes. The glow's pulse and the travelling
// light run on feature state, which the map applies on the main thread without re-tiling any data.
let beamKey = "", glowPhases = [];

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
  ccw: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5v5h5"/><path d="M5.6 15.5A8 8 0 1 0 6 8.3L4 10"/></svg>',
  cw: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 5v5h-5"/><path d="M18.4 15.5A8 8 0 1 1 18 8.3l2 1.7"/></svg>',
  sun: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4L6 18M18 6l1.4-1.4"/></svg>',
  moon: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>',
  spin: '<svg viewBox="0 0 24 24" aria-hidden="true"><ellipse cx="12" cy="12" rx="9" ry="4"/><path d="M12 3v18"/><path d="M17.5 6.6l1.6-1.4-.4 2.1"/></svg>',
};

/* ------------------------------------------------------------------ the map */
function addWorld() {
  const night = theme === "night";
  // the buildings go above every ground layer and below the labels. The night style puts a water label
  // early, before its flat building footprints and roads, so "before the first label" would let those
  // paint over the 3D buildings like misplaced shadows.
  const layers = map.getStyle().layers;
  const lastGround = layers.findLastIndex(l => l.type !== "symbol");
  const firstLabel = layers.slice(lastGround + 1).find(l => l.type === "symbol")?.id;
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
  const pulse = ["number", ["feature-state", "pulse"], 0.5];
  map.addLayer({id: "glow", type: "circle", source: "glow", paint: {
    "circle-radius": ["+", 26, ["*", 14, pulse]], "circle-color": AMBER, "circle-blur": 1,
    "circle-opacity": ["+", 0.28, ["*", 0.2, pulse]]}});
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
  const lit = ["case", ["boolean", ["feature-state", "on"], false], 1, 0];
  map.addLayer({id: "comet", type: "circle", source: "comet", paint: {
    "circle-radius": 7, "circle-color": "#ffffff", "circle-blur": 0.4, "circle-stroke-width": 6,
    "circle-stroke-color": night ? "rgba(255,181,71,.45)" : "rgba(0,113,227,.35)",
    "circle-opacity": lit, "circle-stroke-opacity": lit}});
  beamKey = "";
  drawBeams(true);
  if (walk) setWalk(walk.lot, false);
}

function initMap() {
  map = new maplibregl.Map({
    container: "map", style: STYLES[theme],
    center: [-76.476, 42.452], zoom: 13.2, pitch: 0, bearing: 0, attributionControl: {compact: true},
  });
  map.addControl(new maplibregl.NavigationControl({showCompass: false}), "top-right");
  map.addControl(new MapSwitches(), "top-right");
  document.querySelector(".mapwrap").appendChild(rotateDial(map));
  ["dragstart", "zoomstart", "rotatestart", "pitchstart", "wheel"].forEach(ev => map.on(ev, e => { if (e.originalEvent) setOrbit(false); }));
  // the camera treats the map beside the floating panels as the view, so fly-ins and rotation centre there
  map.setPadding(viewPadding());
  map.on("resize", () => map.setPadding(viewPadding()));
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
  // one glow per lot the permit allows; its pulse is set each frame through feature state
  const glowing = Object.values(geo.lots).filter(l => allowed[l.pool_id]);
  glowPhases = glowing.map(l => l.lat * 900);
  map.getSource("glow").setData({type: "FeatureCollection", features: glowing.map((l, id) =>
    ({type: "Feature", id, properties: {}, geometry: {type: "Point", coordinates: [l.lon, l.lat]}}))});
}

function beamFrame(t) {
  if (!map.getSource("beams")) return;
  // beams keep a similar size on screen: shorter as the camera comes closer
  const scale = Math.min(1.2, Math.max(0.18, Math.pow(2, 14.6 - map.getZoom())));
  let rising = false;
  Object.values(beams).forEach(b => {
    const gap = b.target - b.now;
    if (Math.abs(gap) > 0.3) { b.now += gap * 0.06; rising = true; } else b.now = b.target;
  });
  const key = `${scale.toFixed(3)}|${selected}|${hovered}`;
  if (rising || key !== beamKey) {
    beamKey = key;
    const feats = [];
    Object.values(geo.lots).forEach(l => {
      const b = beams[l.pool_id];
      if (!b || b.now < 0.5) return;
      const on = l.pool_id === selected || l.pool_id === hovered;
      feats.push({type: "Feature", properties: {h: b.now * scale, color: on ? "#ffc65a" : "#ff9a1f"},
                  geometry: {type: "Polygon", coordinates: circle(l.lon, l.lat, on ? 24 : 19)}});
    });
    map.getSource("beams").setData({type: "FeatureCollection", features: feats});
  }
  if (!reduced) glowPhases.forEach((phase, id) => map.setFeatureState({source: "glow", id}, {pulse: 0.5 + 0.5 * Math.sin(t / 520 + phase)}));
}

function setWalk(lotId, animate = true) {
  const l = geo.lots[lotId], d = geo.dests[trip.destination];
  if (!map?.getSource("walk")) { walk = l && d ? {lot: lotId} : null; return; }
  map.removeFeatureState({source: "comet"});
  if (!l || !d) { walk = null; map.getSource("walk").setData(empty); map.getSource("comet").setData(empty); return; }
  const coords = arch([l.lon, l.lat], [d.lon, d.lat]);
  walk = {lot: lotId, coords, t0: performance.now(), grow: animate && !reduced, drawn: 0, star: -1};
  // every point of the arch, unlit; the travelling light lights one at a time
  map.getSource("comet").setData({type: "FeatureCollection", features: coords.map((c, id) =>
    ({type: "Feature", id, properties: {}, geometry: {type: "Point", coordinates: c}}))});
}

let dashStep = 0;
const DASHES = [[0, 2, 2], [0.5, 2, 1.5], [1, 2, 1], [1.5, 2, 0.5], [2, 2, 0], [0, 0.5, 2, 1.5], [0, 1, 2, 1], [0, 1.5, 2, 0.5]];
function walkFrame(t) {
  if (!walk?.coords || !map?.getSource("walk")) return;
  const grow = walk.grow ? Math.min(1, (t - walk.t0) / 900) : 1;
  const n = Math.max(2, Math.round(walk.coords.length * grow));
  if (n !== walk.drawn) {   // the line changes only while it grows
    walk.drawn = n;
    map.getSource("walk").setData({type: "Feature", geometry: {type: "LineString", coordinates: walk.coords.slice(0, n)}});
  }
  if (reduced) return;
  const step = Math.floor(t / 90) % DASHES.length;
  if (step !== dashStep) { dashStep = step; map.setPaintProperty("walk", "line-dasharray", DASHES[step]); }
  const k = Math.floor((((t - walk.t0) / 2600) % 1) * (walk.coords.length - 1));
  if (k !== walk.star) {
    if (walk.star >= 0) map.setFeatureState({source: "comet", id: walk.star}, {on: false});
    map.setFeatureState({source: "comet", id: k}, {on: true});
    walk.star = k;
  }
}

let lastFrame = 0;
function loop(t) {
  if (map) {
    beamFrame(t);
    walkFrame(t);
    const dt = Math.min(64, t - (lastFrame || t));
    if (orbit && !reduced && !map.isMoving()) map.setBearing(map.getBearing() + orbitRate * dt / 1000);
  }
  lastFrame = t;
  requestAnimationFrame(loop);
}

function setOrbit(on, rate = orbitRate) {
  orbit = on && !reduced;
  orbitRate = rate;
  spinBtn?.setAttribute("aria-pressed", String(orbit));
}

// Rotation, bottom right: turn left, a compass that shows the heading and turns back to north, turn right,
// and a slow spin. A tap turns 45 degrees; holding keeps the map turning until you let go.
function rotateDial(m) {
  const el = document.createElement("div");
  el.className = "dial";
  el.setAttribute("role", "group");
  el.setAttribute("aria-label", "Rotate the map");
  el.innerHTML = `
    <button type="button" data-turn="1" title="Rotate left · hold to keep turning (Q)" aria-label="Rotate left">${ICON.ccw}</button>
    <button type="button" class="compass" title="Face north (N)" aria-label="Face north"><span class="needle"><i></i><b>N</b></span></button>
    <button type="button" data-turn="-1" title="Rotate right · hold to keep turning (E)" aria-label="Rotate right">${ICON.cw}</button>
    <button type="button" class="spin" aria-pressed="false" title="Spin slowly around the view" aria-label="Spin the map">${ICON.spin}</button>`;
  const needle = el.querySelector(".needle");
  const heading = () => {
    const b = m.getBearing();
    needle.style.transform = `rotate(${-b}deg)`;
    el.querySelector(".compass").classList.toggle("north", Math.abs(((b % 360) + 360) % 360) < 1);
  };
  m.on("rotate", heading);
  heading();
  el.querySelectorAll("[data-turn]").forEach(btn => {
    const dir = +btn.dataset.turn;
    let hold = null, raf = 0, t0 = 0, last = 0;
    const keepTurning = now => { m.setBearing(m.getBearing() + dir * 60 * (now - last) / 1000); last = now; raf = requestAnimationFrame(keepTurning); };
    btn.addEventListener("pointerdown", e => {
      setOrbit(false);
      t0 = performance.now();
      btn.setPointerCapture(e.pointerId);
      hold = setTimeout(() => { last = performance.now(); raf = requestAnimationFrame(keepTurning); }, 250);
    });
    const stop = tapped => {
      clearTimeout(hold); cancelAnimationFrame(raf);
      if (tapped && performance.now() - t0 < 250) turn(m, dir * 45);
    };
    btn.addEventListener("pointerup", () => stop(true));
    btn.addEventListener("pointercancel", () => stop(false));
    btn.addEventListener("click", e => { if (e.detail === 0) turn(m, dir * 45); });   // keyboard
  });
  el.querySelector(".compass").addEventListener("click", () => { setOrbit(false); m.easeTo({bearing: 0, duration: reduced ? 0 : 700}); });
  spinBtn = el.querySelector(".spin");
  spinBtn.addEventListener("click", () => {
    if (orbit) return setOrbit(false);
    if (m.getPitch() < 20) m.easeTo({pitch: 55, duration: reduced ? 0 : 800});
    setOrbit(true, 9);
  });
  if (reduced) spinBtn.hidden = true;
  return el;
}

function turn(m, deg) {
  setOrbit(false);
  m.easeTo({bearing: m.getBearing() + deg, duration: reduced ? 0 : 650, easing: k => 1 - Math.pow(1 - k, 3)});
}

addEventListener("keydown", e => {
  if (!map || e.metaKey || e.ctrlKey || e.altKey || e.target.closest?.("input, select, textarea")) return;
  const k = e.key.toLowerCase();
  if (k === "q" || k === "e") turn(map, k === "q" ? 45 : -45);
  if (k === "n") { setOrbit(false); map.easeTo({bearing: 0, duration: reduced ? 0 : 700}); }
});

function viewPadding() {
  return window.innerWidth > 900 ? {left: 472, top: 140, right: 56, bottom: 16} : {left: 0, top: 0, right: 0, bottom: 0};
}

function fit(ids, intro) {
  const pts = ids.map(id => geo.lots[id]).filter(Boolean);
  const d = geo.dests[trip.destination];
  if (d) pts.push(d);
  if (!pts.length || !map) return;
  const b = new maplibregl.LngLatBounds();
  pts.forEach(p => b.extend([p.lon, p.lat]));
  const bearing = intro ? -22 : map.getBearing();
  const cam = map.cameraForBounds(b, {padding: {top: 50, bottom: 80, left: 60, right: 70}, maxZoom: 16.2, bearing});
  if (!cam) return;
  const shot = {...cam, pitch: intro || map.getPitch() > 5 ? 58 : 0};
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
      mode.innerHTML = theme === "night" ? ICON.sun : ICON.moon;
      mode.title = theme === "night" ? "Day map" : "Night map";
    };
    dim.addEventListener("click", () => {
      const flat = m.getPitch() > 5;
      setOrbit(false);
      m.easeTo({pitch: flat ? 0 : 58, duration: 900});
    });
    mode.addEventListener("click", () => {
      theme = theme === "night" ? "day" : "night";
      document.body.classList.toggle("map-day", theme === "day");
      m.setStyle(STYLES[theme], {diff: false});   // a full reload fires style.load, which puts the 3D layers back
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
      <div class="thumb" style="${lotPhotoStyle(o.lot_id, 256)}"></div>
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
  }).join("") + `<p class="credit">Photos are real photos of similar campus lots (Wikimedia Commons, credited on each lot). Open a lot for the aerial of the actual spot.</p>`;
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
    setOrbit(false);
    const shot = {center: [l.lon, l.lat], zoom: 16.3, pitch: 60, bearing: map.getBearing() + 35};
    if (reduced) map.jumpTo(shot);
    else { map.flyTo({...shot, duration: 1600, curve: 1.3, essential: true}); map.once("moveend", () => { if (selected === lotId) setOrbit(true, 2); }); }
  }
  const free = Math.round(100 * o.remaining / o.capacity);
  const walkTxt = o.walk_minutes === null ? "No estimate" : `${o.walk_minutes} min`;
  $("detail").innerHTML = `
    <div class="media" id="media">
      <div class="slides" id="slides">
        <div class="slide" style="${lotPhotoStyle(lotId, 900)}"></div>
        <div class="slide" id="aerial-slide"></div>
      </div>
      <button class="fab" id="back" type="button" aria-label="Back to all lots">${ICON.back}</button>
      <div class="media-tabs" role="tablist" aria-label="Lot picture">
        <button type="button" role="tab" aria-selected="true" data-slide="0">Photo</button>
        <button type="button" role="tab" aria-selected="false" data-slide="1">Aerial</button>
      </div>
      <p class="media-credit" id="media-credit">${lotPhotoCredit(lotId)}</p>
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
      <p class="credit">Lot names are pilot fixtures. The photo shows a similar lot elsewhere; the aerial (USGS The National Map, public domain) shows this one.</p>
    </div>
    <div class="dock">
      <div class="dock-sum"><b>${esc(found.start)}–${esc(found.end)} today</b><span>${esc(o.name)} · ${walkTxt} walk</span></div>
      <button class="btn" id="reserve" type="button">Reserve</button>
    </div>`;
  $("detail").classList.add("open");
  document.querySelector(".side").classList.add("has-detail");
  $("back").addEventListener("click", closeDetail);
  // the aerial is drawn on demand by a slow map server, so it is fetched only once the card has settled
  const loadAerial = () => { const s = $("aerial-slide"); if (s && !s.style.backgroundImage) s.setAttribute("style", lotImageStyle(l?.lat, l?.lon, 960, 560)); };
  setTimeout(loadAerial, 1200);
  const showSlide = n => {
    if (n) loadAerial();
    $("slides").style.transform = `translateX(${-50 * n}%)`;
    document.querySelectorAll(".media-tabs button").forEach(b => b.setAttribute("aria-selected", String(+b.dataset.slide === n)));
    $("media-credit").innerHTML = n ? "This exact spot from above · USGS, public domain" : lotPhotoCredit(lotId);
  };
  document.querySelectorAll(".media-tabs button").forEach(b => b.addEventListener("click", () => showSlide(+b.dataset.slide)));
  let x0 = null;
  $("media").addEventListener("pointerdown", e => { x0 = e.clientX; });
  $("media").addEventListener("pointerup", e => { if (x0 !== null && Math.abs(e.clientX - x0) > 40) showSlide(e.clientX < x0 ? 1 : 0); x0 = null; });
  // the review page shows the same photo larger: start fetching it as the pointer reaches Reserve
  $("reserve").addEventListener("pointerenter", () => { new Image().src = lotPhotoUrl(lotId, 1240); }, {once: true});
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
  setOrbit(false);
  select(null);
  fit(found.options.map(o => o.lot_id));
}

/* ------------------------------------------------------------------ search */
async function search(intro) {
  $("results").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div>`;
  $("detail").classList.remove("open");
  document.querySelector(".side").classList.remove("has-detail");
  selected = null;
  setOrbit(false);
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

// a hairline under the list heading once the list scrolls beneath it
$("results").addEventListener("scroll", e => document.querySelector(".side-head").classList.toggle("scrolled", e.target.scrollTop > 4));

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
