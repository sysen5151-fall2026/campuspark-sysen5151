// The confirmation: a success moment when you have just booked, then the pass you show and keep.
import { api, esc, session, recent } from "/static/common.js";

const $ = id => document.getElementById(id);
const id = decodeURIComponent(location.pathname.split("/").pop());
const fresh = session.take("cp.justBooked") === id;
const driver = session.driver || (recent.all().find(b => b.id === id) || {}).driver || "";

function today() {
  const d = new Date();
  return d.toLocaleDateString("en-US", {weekday: "long", month: "long", day: "numeric"});
}

function ics(b) {
  const d = new Date(), pad = n => String(n).padStart(2, "0");
  const day = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}`;
  const t = s => s.replace(":", "") + "00";
  const body = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CampusPark//EN", "BEGIN:VEVENT",
    `UID:${b.confirmation}@campuspark`, `DTSTART:${day}T${t(b.start)}`, `DTEND:${day}T${t(b.end === "24:00" ? "23:59" : b.end)}`,
    `SUMMARY:Parking at ${b.lot}`, `LOCATION:${b.address}`, `DESCRIPTION:Confirmation ${b.confirmation}`,
    "END:VEVENT", "END:VCALENDAR"].join("\r\n");
  return URL.createObjectURL(new Blob([body], {type: "text/calendar"}));
}

function render(b) {
  $("main").innerHTML = `
    ${fresh ? `<div class="done-head">
        <svg class="check" viewBox="0 0 80 80" aria-hidden="true"><circle cx="40" cy="40" r="36"/><path d="M24 41l11 11 21-23"/></svg>
        <h1>You're all set.</h1>
        <p>Your place at ${esc(b.lot)} is held from ${esc(b.start)} to ${esc(b.end)}.</p>
      </div>` : `<p class="steps">My bookings</p><h1 style="margin-bottom:22px">Your booking.</h1>`}
    <article class="pass" aria-label="Parking pass">
      <i class="holo" aria-hidden="true"></i>
      <div class="pass-top"><b>CampusPark</b><span>Held</span></div>
      <div class="pass-main">
        <div class="live" id="live" aria-live="polite"><span class="dot"></span><b id="live-text"></b><span class="meter"><i id="live-bar"></i></span></div>
        <small>Lot</small>
        <p class="lot">${esc(b.lot)}</p>
        <div class="pass-grid">
          <div><small>Date</small><b>${esc(today())}</b></div>
          <div><small>Time</small><b>${esc(b.start)} to ${esc(b.end)}</b></div>
          <div style="grid-column:1/-1"><small>Address</small><b style="font-size:16px">${esc(b.address)}</b></div>
        </div>
      </div>
      <div class="pass-cut" aria-hidden="true"></div>
      <div class="pass-bottom">
        <div><small style="color:#a1a1a6;font-size:12px">Confirmation</small><div class="code">${esc(b.confirmation)}</div></div>
        <div class="qr" id="qr" aria-label="QR code for ${esc(b.confirmation)}"></div>
      </div>
    </article>
    <p class="guide">${b.guidance ? esc(b.guidance) : ""}</p>
    ${b.warning ? `<p class="warnbox">${esc(b.warning)}</p>` : ""}
    <div class="actions">
      <a class="btn dark" target="_blank" rel="noopener" href="https://maps.apple.com/?daddr=${encodeURIComponent(b.address)}">Get directions</a>
      <a class="btn ghost" id="cal" download="campuspark-${esc(b.confirmation)}.ics">Add to calendar</a>
    </div>
    <p style="text-align:center;margin-top:18px"><a href="/">Done</a></p>
    <p class="fine">${esc(b.note)}</p>`;
  $("cal").href = ics(b);
  if (window.QRCode) new QRCode($("qr"), {text: b.confirmation, width: 92, height: 92, colorDark: "#111", colorLight: "#fff"});
  live(b);
  setInterval(() => live(b), 20000);
  tilt(document.querySelector(".pass"));
  if (fresh) burst();
}

// where today's booking stands right now: before it, during it (with the share of the stay gone), or after
function live(b) {
  const at = hhmm => { const [h, m] = hhmm.split(":").map(Number); const d = new Date(); d.setHours(h, m, 0, 0); return d; };
  const start = at(b.start), end = at(b.end), now = new Date();
  const span = mins => mins >= 60 ? `${Math.floor(mins / 60)} h ${mins % 60} min` : `${mins} min`;
  const box = $("live");
  let text, state, share = 0;
  if (now < start) { state = "soon"; text = `Starts in ${span(Math.ceil((start - now) / 60000))}`; }
  else if (now < end) { state = "now"; text = `Held now · ${span(Math.ceil((end - now) / 60000))} left`; share = (now - start) / (end - start); }
  else { state = "over"; text = `Ended at ${b.end}`; share = 1; }
  box.dataset.state = state;
  $("live-text").textContent = text;
  $("live-bar").style.width = `${Math.round(share * 100)}%`;
}

// the pass leans toward the pointer and its foil catches the light, like a card held in the hand
function tilt(card) {
  if (!card || matchMedia("(prefers-reduced-motion: reduce)").matches || !matchMedia("(hover: hover)").matches) return;
  card.addEventListener("pointermove", e => {
    const r = card.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    card.classList.add("tilting");
    card.style.setProperty("--ry", `${(x - 0.5) * 16}deg`);
    card.style.setProperty("--rx", `${(0.5 - y) * 12}deg`);
    card.style.setProperty("--hx", `${x * 100}%`);
    card.style.setProperty("--hy", `${y * 100}%`);
  });
  card.addEventListener("pointerleave", () => {
    card.classList.remove("tilting");
    card.style.setProperty("--rx", "0deg");
    card.style.setProperty("--ry", "0deg");
  });
}

// when the booking has just been made: a burst of light from the check mark
function burst() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const check = document.querySelector(".check");
  if (!check) return;
  const c = document.createElement("canvas");
  c.className = "burst";
  document.body.appendChild(c);
  const dpr = Math.min(2, devicePixelRatio || 1);
  c.width = innerWidth * dpr; c.height = innerHeight * dpr;
  const g = c.getContext("2d");
  g.scale(dpr, dpr);
  const r = check.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const colors = ["#ffd690", "#ffb547", "#ffffff", "#7ee2a0", "#34c759"];
  const sparks = Array.from({length: 90}, () => {
    const a = Math.random() * Math.PI * 2, v = 160 + Math.random() * 420;
    return {x: cx, y: cy, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 120, r: 1.2 + Math.random() * 2.6, life: 0.9 + Math.random() * 0.8,
            color: colors[Math.floor(Math.random() * colors.length)]};
  });
  let t0 = null;
  const frame = t => {
    t0 ??= t;
    const s = (t - t0) / 1000;
    g.clearRect(0, 0, innerWidth, innerHeight);
    let alive = 0;
    for (const p of sparks) {
      const k = s / p.life;
      if (k >= 1) continue;
      alive++;
      const x = p.x + p.vx * s * (1 - k * 0.35), y = p.y + p.vy * s + 260 * s * s;
      g.globalAlpha = 1 - k;
      g.fillStyle = p.color;
      g.shadowColor = p.color; g.shadowBlur = 8;
      g.beginPath(); g.arc(x, y, p.r * (1 - k * 0.5), 0, Math.PI * 2); g.fill();
    }
    if (alive) requestAnimationFrame(frame); else c.remove();
  };
  setTimeout(() => { navigator.vibrate?.(14); requestAnimationFrame(frame); }, 650);
}

async function load(driverId) {
  const res = await api(`/api/reservations/${encodeURIComponent(id)}?driver_id=${encodeURIComponent(driverId)}`);
  if (res.error) {
    $("main").innerHTML = `<h1>We couldn't open this booking.</h1>
      <p class="lede">Enter the driver ID it was made with.</p>
      <form class="card" id="who"><label class="field"><span>Driver ID</span><input id="d" required></label>
      <button class="btn full">Show booking</button></form>`;
    $("who").addEventListener("submit", e => { e.preventDefault(); session.driver = $("d").value.trim(); load(session.driver); });
    return;
  }
  render(res);
}

load(driver);
