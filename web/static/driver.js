// Driver page: trip form, P-sign options, the held-place ticket and the campus map.
const out = document.getElementById("out");
const tag = document.getElementById("trip");
const motion = !matchMedia("(prefers-reduced-motion: reduce)").matches;
let lastSearch = null;
let geo = {lots: {}, destinations: {}};

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

/* ------------------------------------------------------------------ map */
const map = L.map("map", {zoomControl: true, scrollWheelZoom: false}).setView([42.4485, -76.4765], 15);
// OpenStreetMap tiles, turned to asphalt by the filter on .leaflet-tile-pane in style.css.
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

const lotMarkers = {};
let destMarker = null;
let walk = null;

function pIcon(state) {
  return L.divIcon({className: "", html: `<div class="pin-p ${state}">P</div>`, iconSize: [30, 30], iconAnchor: [15, 15]});
}

function setLot(id, state) {
  const m = lotMarkers[id];
  if (m) m.setIcon(pIcon(state));
}

function showDestination(name) {
  const d = geo.destinations[name];
  if (destMarker) destMarker.remove();
  if (!d) return;
  destMarker = L.marker([d.lat, d.lon], {
    icon: L.divIcon({className: "", html: '<div class="pin-dest"></div>', iconSize: [26, 26], iconAnchor: [13, 13]}),
    keyboard: false
  }).addTo(map).bindTooltip(esc(name), {permanent: true, direction: "right", offset: [12, 0], className: "pin-label"});
}

function drawWalk(lotId, animate) {
  if (walk) { walk.remove(); walk = null; }
  const lot = geo.lots[lotId], d = geo.destinations[lastSearch?.trip.destination];
  if (!lot || !d) return;
  walk = L.polyline([[lot.lat, lot.lon], [d.lat, d.lon]], {
    color: "#F4C21B", weight: 4, className: "walk-line" + (animate && motion ? " draw" : "")
  }).addTo(map);
}

async function loadMap() {
  const data = await (await fetch("/api/map")).json();
  data.lots.forEach(l => {
    geo.lots[l.pool_id] = l;
    lotMarkers[l.pool_id] = L.marker([l.lat, l.lon], {icon: pIcon("off"), title: l.name})
      .addTo(map).bindTooltip(esc(l.name), {direction: "top", offset: [0, -16], className: "pin-label"})
      .on("click", () => {
        const sign = document.querySelector(`[data-lot="${l.pool_id}"]`);
        if (sign) { sign.scrollIntoView({behavior: motion ? "smooth" : "auto", block: "center"}); highlight(l.pool_id); }
      });
  });
  data.destinations.forEach(d => { geo.destinations[d.name] = d; });
  showDestination(document.getElementById("destination").value);
}

function fitTo(ids) {
  const d = geo.destinations[lastSearch.trip.destination];
  const pts = ids.map(id => geo.lots[id]).filter(Boolean).map(l => [l.lat, l.lon]);
  if (d) pts.push([d.lat, d.lon]);
  if (pts.length) map.flyToBounds(pts, {padding: [70, 70], maxZoom: 16, duration: motion ? 0.9 : 0});
}

function highlight(id) {
  document.querySelectorAll(".sign").forEach(s => s.classList.toggle("active", s.dataset.lot === id));
  lastSearch?.ids.forEach(other => setLot(other, other === id ? "on" : ""));
  drawWalk(id, false);
}

/* ------------------------------------------------------------------ form */
fetch("/api/destinations").then(r => r.json()).then(d => {
  const sel = document.getElementById("destination");
  sel.innerHTML = d.destinations.map(x => `<option>${esc(x)}</option>`).join("");
  sel.addEventListener("change", () => showDestination(sel.value));
  loadMap();
});

function walkText(m) {
  return m === null ? {big: "No estimate", small: "walk time unavailable"} : {big: `${m} min`, small: "walk, estimated"};
}

function stalls(remaining, capacity) {
  const held = capacity - remaining;
  return `<div class="stalls" role="img" aria-label="${remaining} of ${capacity} places free for your whole stay">` +
    Array.from({length: capacity}, (_, i) => `<i class="${i < held ? "held" : ""}"></i>`).join("") + "</div>";
}

async function findParking(e) {
  e.preventDefault();
  out.innerHTML = `<p class="results-head">Checking your permit and the lots near ${esc(trip().destination)}…</p>`;
  const res = await call("/api/options", trip());
  if (walk) { walk.remove(); walk = null; }
  if (res.error) {
    tag.removeAttribute("data-permit");
    Object.keys(lotMarkers).forEach(id => setLot(id, "off"));
    out.innerHTML = `<div class="notice">${esc(res.error)}</div>`;
    return;
  }
  const t = trip();
  lastSearch = {trip: t, search_id: res.search_id, ids: res.options.map(o => o.lot_id)};
  tag.dataset.permit = res.permit;
  document.getElementById("permit-line").innerHTML =
    `Permit checked: <b>${esc(res.permit)}</b>, ${esc(res.start)} to ${esc(res.end)}`;
  showDestination(t.destination);

  Object.keys(lotMarkers).forEach(id => setLot(id, "off"));
  lastSearch.ids.forEach((id, i) => setTimeout(() => setLot(id, motion ? "settle" : ""), motion ? 250 + i * 160 : 0));
  fitTo(lastSearch.ids);

  if (!res.options.length) {
    out.innerHTML = `<div class="notice">Nothing your ${esc(res.permit)} permit allows is free for the whole of
      ${esc(res.start)} to ${esc(res.end)}. ${esc(res.reason || "")} Try a different time or a shorter stay.</div>`;
    return;
  }
  out.innerHTML =
    `<p class="results-head">${res.options.length === 1 ? "One lot" : `${res.options.length} lots`} near ${esc(t.destination)}, nearest walk first</p>` +
    res.options.map(o => {
      const w = walkText(o.walk_minutes);
      return `
      <article class="sign" data-lot="${esc(o.lot_id)}" tabindex="-1"
               onmouseenter="highlight('${esc(o.lot_id)}')" onfocusin="highlight('${esc(o.lot_id)}')">
        <div class="p-col" aria-hidden="true">P</div>
        <div class="body">
          <h2>${esc(o.name)}</h2>
          <p class="addr">${esc(o.address || "Address unavailable")}</p>
          <div class="numbers">
            <div><b>${esc(w.big)}</b><span>${esc(w.small)}</span></div>
            <div><b>${o.remaining} free</b><span>of ${o.capacity} places, all stay</span></div>
          </div>
          ${stalls(o.remaining, o.capacity)}
          <details><summary>Why this lot was offered</summary>
            <ul>${o.facts.map(f => `<li>${esc(f)}</li>`).join("")}</ul></details>
          <button class="hold" onclick="reserve(this, '${esc(o.lot_id)}')">Hold a place here</button>
        </div>
      </article>`;
    }).join("") + `<p class="basis">${esc(res.capacity_basis)}</p>`;
}

function ticket(res, heading) {
  return `<article class="ticket">
      <div class="stripe" aria-hidden="true"></div>
      <div class="inner">
        <h2>${esc(heading)}</h2>
        <p class="code">${esc(res.confirmation)}</p>
        <dl>
          <dt>Lot</dt><dd>${esc(res.lot)}</dd>
          <dt>When</dt><dd>${esc(res.start)} to ${esc(res.end)}</dd>
          <dt>Address</dt><dd>${esc(res.address)}</dd>
          <dt>Getting there</dt><dd>${res.guidance ? esc(res.guidance) : "Route guidance unavailable"}</dd>
        </dl>
        ${res.warning ? `<p class="warn">${esc(res.warning)}</p>` : ""}
        <p class="basis">${esc(res.note)}</p>
      </div>
    </article>`;
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
  lastSearch.ids.forEach(id => setLot(id, id === lotId ? "lit" : "off"));
  drawWalk(lotId, true);
  out.innerHTML = ticket(res, `Your place at ${res.lot} is held`) +
    `<button class="plain" onclick="document.getElementById('trip').requestSubmit()">See the other lots again</button>`;
  out.scrollIntoView({behavior: motion ? "smooth" : "auto", block: "start"});
}

async function findBooking(e) {
  e.preventDefault();
  const id = encodeURIComponent(document.getElementById("lookup-id").value.trim());
  const driver = encodeURIComponent(document.getElementById("lookup-driver").value.trim());
  const res = await call(`/api/reservations/${id}?driver_id=${driver}`);
  document.getElementById("lookup-out").innerHTML = res.error
    ? `<div class="notice">${esc(res.error)} Check the number on your confirmation and the ID you booked with.</div>`
    : ticket(res, `Your booking at ${res.lot}`);
}
