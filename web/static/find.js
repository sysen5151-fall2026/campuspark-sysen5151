// Search results: the list on the left, the map on the right, lot details opening in place.
import { api, esc, session, destinations, lotImage } from "/static/common.js";

const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const trip = {
  driver_id: session.driver,
  destination: params.get("to") || "",
  arrival: params.get("at") || "09:00",
  hours: Number(params.get("hours") || 2),
};
let geo = {lots: {}, dests: {}};
let found = null;
let markers = {};
let destMarker = null;
let map = null;
let selected = null;   // the lot whose details are open

/* ------------------------------------------------------------------ the map */
function initMap() {
  map = new maplibregl.Map({
    container: "map",
    style: "https://tiles.openfreemap.org/styles/positron",
    center: [-76.476, 42.449], zoom: 14.6, attributionControl: {compact: true},
  });
  map.addControl(new maplibregl.NavigationControl({showCompass: false}), "top-right");
  return new Promise(res => map.on("load", () => {
    map.addSource("walk", {type: "geojson", data: {type: "FeatureCollection", features: []}});
    map.addLayer({id: "walk-halo", type: "line", source: "walk", paint: {"line-color": "#ffffff", "line-width": 8, "line-opacity": 0.9}});
    map.addLayer({id: "walk", type: "line", source: "walk", layout: {"line-cap": "round"},
                  paint: {"line-color": "#0071e3", "line-width": 4, "line-dasharray": [0.1, 2]}});
    res();
  }));
}

function showWalk(lotId) {
  const l = geo.lots[lotId], d = geo.dests[trip.destination];
  const data = l && d ? {type: "Feature", geometry: {type: "LineString", coordinates: [[l.lon, l.lat], [d.lon, d.lat]]}}
                      : {type: "FeatureCollection", features: []};
  map?.getSource("walk")?.setData(data);
}

function fit(ids) {
  const pts = ids.map(id => geo.lots[id]).filter(Boolean);
  const d = geo.dests[trip.destination];
  if (d) pts.push(d);
  if (!pts.length || !map) return;
  const b = new maplibregl.LngLatBounds();
  pts.forEach(p => b.extend([p.lon, p.lat]));
  map.fitBounds(b, {padding: {top: 80, bottom: 80, left: 80, right: 80}, maxZoom: 16, duration: 900});
}

function placeMarkers() {
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
    markers[l.pool_id] = new maplibregl.Marker({element: el}).setLngLat([l.lon, l.lat]).addTo(map);
  });
  // the map can finish loading after the driver has already opened a lot
  if (selected) { select(selected); hot(selected); }
}

function hot(lotId) {
  document.querySelectorAll(".res").forEach(r => r.classList.toggle("hot", r.dataset.lot === lotId));
  Object.entries(markers).forEach(([id, m]) => m.getElement().classList.toggle("hot", id === lotId));
  showWalk(lotId);
}

function select(lotId) {
  selected = lotId;
  Object.entries(markers).forEach(([id, m]) => m.getElement().classList.toggle("on", id === lotId));
}

/* ------------------------------------------------------------------ the list */
function availClass(o) { return o.remaining / o.capacity < 0.2 ? "avail low" : "avail"; }

function renderList() {
  const opts = found.options;
  $("title").textContent = opts.length ? `${opts.length === 1 ? "One lot" : `${opts.length} lots`} for your trip` : "No lot fits this trip";
  $("subtitle").textContent = `${trip.destination}, ${found.start} to ${found.end}, nearest walk first`;
  if (!opts.length) {
    $("results").innerHTML = `<div class="empty-state"><b>Nothing your ${esc(found.permit)} permit allows is free for the whole stay.</b>
      ${esc(found.reason || "")} Try an earlier or later arrival, or a shorter stay.</div>`;
    return;
  }
  $("results").innerHTML = opts.map(o => `
    <li class="res" data-lot="${esc(o.lot_id)}" tabindex="0">
      <div class="thumb" style="background-image:url('${lotImage(o.lot_id)}'), linear-gradient(135deg,#dfe3ea,#c8ced8)"></div>
      <div>
        <h3>${esc(o.name)}</h3>
        <div class="meta">${esc(o.address || "Address unavailable")}</div>
        <div class="facts"><span><b>${o.walk_minutes === null ? "–" : o.walk_minutes}</b> min walk</span>
          <span><b>${o.remaining}</b> of ${o.capacity} free</span></div>
        <div class="${availClass(o)}"><i style="width:${Math.round(100 * o.remaining / o.capacity)}%"></i></div>
      </div>
    </li>`).join("");
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
  if (l && map) map.easeTo({center: [l.lon, l.lat], zoom: Math.max(map.getZoom(), 15.4), duration: 700});
  $("detail").innerHTML = `
    <button class="back" id="back" type="button">‹ All lots</button>
    <div class="cover" style="background-image:url('${lotImage(lotId)}'), linear-gradient(135deg,#dfe3ea,#c8ced8)"></div>
    <div class="body">
      <h2>${esc(o.name)}</h2>
      <p class="addr">${esc(o.address || "Address unavailable")}</p>
      <div class="stats">
        <div><b>${o.walk_minutes === null ? "–" : o.walk_minutes} min</b><span>walk to ${esc(trip.destination)}</span></div>
        <div><b>${o.remaining}</b><span>of ${o.capacity} places free all stay</span></div>
        <div><b>${esc(found.start)}</b><span>to ${esc(found.end)} today</span></div>
      </div>
      <div class="${availClass(o)}"><i style="width:${Math.round(100 * o.remaining / o.capacity)}%"></i></div>
      <div class="why"><h4>Why this lot was offered</h4><ul>${o.facts.map(f => `<li>${esc(f)}</li>`).join("")}</ul></div>
    </div>
    <div class="cta-dock">
      <button class="btn big" id="reserve" type="button">Reserve a place here</button>
      <small>You'll review it before anything is booked.</small>
    </div>`;
  $("detail").classList.add("open");
  $("back").addEventListener("click", closeDetail);
  $("reserve").addEventListener("click", () => {
    session.pending = {trip, lot: o, start: found.start, end: found.end, permit: found.permit,
                       search_id: found.search_id, request_id: crypto.randomUUID()};
    location.href = "/review";
  });
  $("back").focus();
}

function closeDetail() {
  $("detail").classList.remove("open");
  select(null);
  fit(found.options.map(o => o.lot_id));
}

/* ------------------------------------------------------------------ search */
async function search() {
  $("results").innerHTML = `<div class="skeleton"></div><div class="skeleton"></div>`;
  $("detail").classList.remove("open");
  const res = await api("/api/options", trip);
  if (res.error) {
    found = null;
    $("title").textContent = "We couldn't search";
    $("subtitle").textContent = "";
    $("permit").innerHTML = "";
    $("results").innerHTML = `<div class="empty-state"><b>${esc(res.error)}</b>Check the driver ID and the trip above, then update.</div>`;
    if (map) placeMarkers();
    return;
  }
  found = res;
  $("permit").innerHTML = `<span class="tagp">${esc(res.permit)} permit</span>checked just now`;
  renderList();
  if (map) { placeMarkers(); fit(res.options.map(o => o.lot_id)); if (res.options[0]) hot(res.options[0].lot_id); }
}

$("search").addEventListener("submit", e => {
  e.preventDefault();
  Object.assign(trip, {driver_id: $("driver").value.trim(), destination: $("destination").value,
                       arrival: $("arrival").value, hours: Number($("hours").value)});
  session.driver = trip.driver_id;
  history.replaceState(null, "", `/find?${new URLSearchParams({to: trip.destination, at: trip.arrival, hours: trip.hours})}`);
  search();
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
  const searching = trip.driver_id ? search() : Promise.resolve();
  if (!trip.driver_id) {
    $("title").textContent = "Who's driving?";
    $("results").innerHTML = `<div class="empty-state"><b>Enter your driver ID above.</b>We use it once to check your permit.</div>`;
    $("driver").focus();
  }
  try {
    await initMap(); await searching; placeMarkers();
    if (found && !selected) { fit(found.options.map(o => o.lot_id)); if (found.options[0]) hot(found.options[0].lot_id); }
  }
  catch { $("map").innerHTML = '<p class="empty-state">The map could not load. The list still works.</p>'; }
})();
