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
      <div class="pass-top"><b>CampusPark</b><span>Held</span></div>
      <div class="pass-main">
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
