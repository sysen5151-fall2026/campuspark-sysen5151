// Driver page: the scroll story over the 3D world, then booking on the campus map.
import * as World from "/static/scene.js";

const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = id => document.getElementById(id);
const out = $("out");
let lastSearch = null;
let campusReady = false;

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
  return {driver_id: $("driver").value.trim(), destination: $("destination").value,
          arrival: $("arrival").value, hours: Number($("hours").value)};
}

/* ------------------------------------------------------------------ world + story */
let worldOk = true;
try {
  World.init($("world"), {reduced});
} catch (e) {
  worldOk = false;
  document.body.classList.add("no-webgl");
}

const cam = World.cameraState, story = World.story;
const SHOTS = {
  hero:   {px: 30, py: 15, pz: 38, tx: 2, ty: 4.5, tz: -3},
  permit: {px: -38, py: 34, pz: 46, tx: 0, ty: 0, tz: 0},
  count:  {px: 16, py: 44, pz: 9, tx: 15, ty: 0, tz: 0},
  hold:   null,   // set from the empty stall once the lot is built
};

async function setup() {
  const [dests, map, pools] = await Promise.all([
    fetch("/api/destinations").then(r => r.json()),
    fetch("/api/map").then(r => r.json()),
    fetch("/api/admin/pools").then(r => r.json()),
  ]);
  $("destination").innerHTML = dests.destinations.map(x => `<option>${esc(x)}</option>`).join("");
  const caps = Object.fromEntries(pools.pools.map(p => [p.pool_id, p.capacity]));
  if (worldOk) {
    World.setCampus(map, "forest-home", caps);
    // the hero lot sits at the origin, so its empty stall is where the opening shot looks
    const lot = World.lotPoint("forest-home");
    ["hero", "permit", "count"].forEach(k => { const s = SHOTS[k]; s.tx += lot.x; s.tz += lot.z; s.px += lot.x; s.pz += lot.z; });
    // the closing shot sits low behind your empty stall, with the stall on the right of the frame
    const st = World.heroStallPoint();
    SHOTS.hold = {px: st.x + 3, py: 4.2, pz: st.z + 11, tx: st.x - 3.2, ty: 0.8, tz: st.z - 1};
    Object.assign(cam, SHOTS.hero);
    World.chooseDestination($("destination").value);
    campusReady = true;
    buildStory();
    if (window.ScrollTrigger) ScrollTrigger.refresh();
  }
  $("destination").addEventListener("change", () => worldOk && World.chooseDestination($("destination").value));
}

function overviewShot() {
  const d = World.destinationPoint($("destination").value) || {x: 0, z: 0};
  const h = World.lotPoint("forest-home");
  const cx = (d.x + h.x) / 2 - 30, cz = (d.z + h.z) / 2;
  const shift = window.innerWidth > 860 ? 70 : 0;
  return {px: cx - shift - 30, py: 175, pz: cz + 215, tx: cx - shift + 10, ty: 0, tz: cz - 15};
}

function buildStory() {
  if (!window.gsap) return;
  gsap.registerPlugin(ScrollTrigger);
  if (reduced) {
    story.stallGlow = 1;
    story.idle = 0;
    return;
  }
  const beats = gsap.utils.toArray(".beat");
  const over = overviewShot();
  // One camera move per section, each finishing as its words reach the middle of the screen.
  const legs = [
    {trigger: beats[0], from: SHOTS.hero, to: SHOTS.permit, glow: [0, 0.35], idle: [1, 0]},
    {trigger: beats[1], from: SHOTS.permit, to: SHOTS.count, glow: [0.35, 0.7]},
    {trigger: beats[2], from: SHOTS.count, to: SHOTS.hold, glow: [0.7, 1]},
  ];
  legs.forEach((leg, i) => {
    const tl = gsap.timeline({scrollTrigger: {trigger: leg.trigger, start: "top bottom", end: "center center", scrub: 1}});
    tl.fromTo(cam, {...leg.from}, {...leg.to, ease: "power2.inOut", immediateRender: false}, 0)
      .fromTo(story, {stallGlow: leg.glow[0]}, {stallGlow: leg.glow[1], ease: "none", immediateRender: false}, 0);
    if (leg.idle) tl.fromTo(story, {idle: 1}, {idle: 0, ease: "none", immediateRender: false}, 0);
    if (i === 1) tl.fromTo({n: 0}, {n: 0}, {n: 15, ease: "none", immediateRender: false,
      onUpdate() { $("count").textContent = Math.round(this.targets()[0].n); }}, 0);
  });
  // The last move rises from your stall to the whole campus, where booking happens.
  const lift = {t: 0};
  gsap.timeline({scrollTrigger: {trigger: "#book", start: "top bottom", end: "top 15%", scrub: 1}})
    .fromTo(cam, {...SHOTS.hold}, {...over, ease: "power3.inOut", immediateRender: false}, 0)
    .fromTo(lift, {t: 0}, {t: 1, ease: "none", immediateRender: false, onUpdate() { World.setCampusMode(lift.t); }}, 0);

  beats.forEach(section => {
    const el = section.querySelector(".beat-text");
    gsap.timeline({scrollTrigger: {trigger: section, start: "top 80%", end: "bottom 20%", scrub: true}})
      .fromTo(el, {opacity: 0, y: 50}, {opacity: 1, y: 0, ease: "power1.out", duration: 0.35})
      .to(el, {opacity: 1, duration: 0.3})
      .to(el, {opacity: 0, y: -30, ease: "power1.in", duration: 0.35});
  });
  // explicit start values: the CSS entrance may still be running when this is set up
  gsap.fromTo(".hero > *", {opacity: 1, y: 0}, {opacity: 0, y: -30, stagger: 0.04, ease: "none", immediateRender: false,
    scrollTrigger: {trigger: ".hero", start: "top top", end: "bottom 40%", scrub: true}});
}

function flyTo(shot) {
  if (!worldOk) return;
  if (reduced || !window.gsap) { Object.assign(cam, shot); return; }
  gsap.to(cam, {...shot, duration: 1.4, ease: "power3.inOut", overwrite: true});
}

function frameRoute(lotId) {
  const a = World.lotPoint(lotId), b = World.destinationPoint(lastSearch.trip.destination);
  if (!a || !b) return;
  const cx = (a.x + b.x) / 2, cz = (a.z + b.z) / 2;
  const span = Math.max(80, Math.hypot(a.x - b.x, a.z - b.z));
  // the booking panel covers the left of the screen, so aim left of the route to set it on the right
  const shift = window.innerWidth > 860 ? span * 0.42 : 0;
  flyTo({px: cx - shift - span * 0.35, py: span * 1.15 + 80, pz: cz + span * 1.25, tx: cx - shift, ty: 12, tz: cz - span * 0.05});
}

/* ------------------------------------------------------------------ booking */
function point(lotId) {
  if (!lastSearch || lastSearch.held) return;
  document.querySelectorAll(".opt").forEach(o => o.classList.toggle("active", o.dataset.lot === lotId));
  if (!worldOk) return;
  const progress = World.drawRoute(lotId, lastSearch.trip.destination, false);
  if (progress && !reduced && window.gsap) gsap.fromTo(progress, {value: 0}, {value: 1, duration: 1.1, ease: "power2.out"});
  frameRoute(lotId);
}

$("trip").addEventListener("submit", async e => {
  e.preventDefault();
  out.innerHTML = `<p class="status">Checking your permit…</p>`;
  const res = await call("/api/options", trip());
  if (worldOk) World.reset();
  if (res.error) { out.innerHTML = `<p class="notice">${esc(res.error)}</p>`; lastSearch = null; return; }
  const t = trip();
  lastSearch = {trip: t, search_id: res.search_id, held: false};
  if (worldOk) {
    World.setCampusMode(1);
    World.chooseDestination(t.destination);
    World.showOptions(res.options);
    flyTo(overviewShot());
  }
  if (!res.options.length) {
    out.innerHTML = `<p class="notice">Nothing your ${esc(res.permit)} permit allows is free for the whole of
      ${esc(res.start)} to ${esc(res.end)}. ${esc(res.reason || "")} Try another time or a shorter stay.</p>`;
    return;
  }
  out.innerHTML = `<p class="status"><span class="permit">${esc(res.permit)} permit</span> ${esc(res.start)} to ${esc(res.end)}</p>
    <ol class="opts">` + res.options.map(o => `
      <li class="opt" data-lot="${esc(o.lot_id)}" tabindex="0">
        <div class="min">${o.walk_minutes === null ? "–" : o.walk_minutes}<small>min walk</small></div>
        <div class="what">
          <h3>${esc(o.name)}</h3>
          <p>${o.remaining} of ${o.capacity} places free all stay</p>
          <div class="bar"><i style="width:${Math.round(100 * o.remaining / o.capacity)}%"></i></div>
          <details><summary>Why this lot</summary><ul>${o.facts.map(f => `<li>${esc(f)}</li>`).join("")}</ul></details>
        </div>
        <button class="pill small" data-hold="${esc(o.lot_id)}">Hold</button>
      </li>`).join("") + `</ol><p class="fine">${esc(res.capacity_basis)}</p>`;
  out.querySelectorAll(".opt").forEach(li => {
    li.addEventListener("mouseenter", () => point(li.dataset.lot));
    li.addEventListener("focus", () => point(li.dataset.lot));
  });
  out.querySelectorAll("[data-hold]").forEach(b => b.addEventListener("click", () => hold(b, b.dataset.hold)));
  if (res.options[0]) point(res.options[0].lot_id);
});

function ticket(res, title) {
  return `<div class="ticket">
      <p class="t-title">${esc(title)}</p>
      <p class="code">${esc(res.confirmation)}</p>
      <dl>
        <dt>Lot</dt><dd>${esc(res.lot)}</dd>
        <dt>When</dt><dd>${esc(res.start)} to ${esc(res.end)}</dd>
        <dt>Address</dt><dd>${esc(res.address)}</dd>
        <dt>Getting there</dt><dd>${res.guidance ? esc(res.guidance) : "Route guidance unavailable"}</dd>
      </dl>
      ${res.warning ? `<p class="notice">${esc(res.warning)}</p>` : ""}
      <p class="fine">${esc(res.note)}</p>
    </div>`;
}

async function hold(button, lotId) {
  button.disabled = true;
  button.textContent = "Holding…";
  const res = await call("/api/reserve", {...lastSearch.trip, lot_id: lotId, search_id: lastSearch.search_id,
                                          request_id: crypto.randomUUID()});
  if (res.error) {
    button.disabled = false;
    button.textContent = "Try again";
    button.closest(".opt").insertAdjacentHTML("beforeend", `<p class="refusal">${esc(res.error)}</p>`);
    return;
  }
  lastSearch.held = true;
  if (worldOk) {
    const progress = World.drawRoute(lotId, lastSearch.trip.destination, true);
    if (progress && !reduced && window.gsap) gsap.fromTo(progress, {value: 0}, {value: 1, duration: 1.4, ease: "power2.inOut"});
    World.holdLot(lotId);
    frameRoute(lotId);
  }
  out.innerHTML = ticket(res, `Held at ${res.lot}`) + `<button class="link" id="again">Search again</button>`;
  $("again").addEventListener("click", () => $("trip").requestSubmit());
}

$("lookup-form").addEventListener("submit", async e => {
  e.preventDefault();
  const res = await call(`/api/reservations/${encodeURIComponent($("lookup-id").value.trim())}?driver_id=${encodeURIComponent($("lookup-driver").value.trim())}`);
  $("lookup-out").innerHTML = res.error
    ? `<p class="notice">${esc(res.error)} Check the number on your confirmation and the ID you booked with.</p>`
    : ticket(res, `Your booking at ${res.lot}`);
});
document.querySelector("[data-lookup]").addEventListener("click", () => { $("lookup").open = true; });

setup();
