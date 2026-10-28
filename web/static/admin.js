// Staff console: the controls in force (IO.17) and one change at a time through F.1 and F.7.
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}
const $ = id => document.getElementById(id);

async function loadPools() {
  const d = await (await fetch("/api/admin/pools")).json();
  $("version").textContent = `Rules version ${d.version}.`;
  $("pools").innerHTML = d.pools.map(p => `
    <tr>
      <td><div class="name">${esc(p.name)}</div><div class="id">${esc(p.pool_id)}</div></td>
      <td>${p.permits.map(x => `<span class="pchip">${esc(x)}</span>`).join("")}</td>
      <td><div class="cap" data-count="${p.capacity}">${p.capacity}</div></td>
      <td>${p.closures.length ? p.closures.map(c => `<span class="closed">${esc(c.start)} to ${esc(c.end)}</span>`).join("<br>") : "Open all day"}</td>
    </tr>`).join("");
  countUp();
  const keep = $("pool").value;
  $("pool").innerHTML = d.pools.map(p => `<option value="${esc(p.pool_id)}">${esc(p.name)}</option>`).join("");
  if (keep) $("pool").value = keep;
}

// place counts roll up to their value when the table is drawn or changes
const shown = {};
function countUp() {
  document.querySelectorAll(".pools [data-count]").forEach((el, i) => {
    const to = Number(el.dataset.count), from = shown[i] ?? 0;
    shown[i] = to;
    if (from === to || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t0 = performance.now();
    const step = t => {
      const k = Math.min(1, (t - t0) / 900);
      el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
}

$("change").addEventListener("submit", async e => {
  e.preventDefault();
  const capacity = $("capacity").value, start = $("close-start").value, end = $("close-end").value;
  const out = $("result");
  if ((start && !end) || (!start && end)) { out.innerHTML = `<p class="err">A closure needs both a start and an end time.</p>`; return; }
  const r = await fetch("/api/admin/controls", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({
    account: $("account").value, pool_id: $("pool").value, capacity: capacity === "" ? null : Number(capacity),
    clear_closures: $("clear").checked, add_closure: start && end ? {start, end} : null})});
  if (!r.ok) { out.innerHTML = `<p class="err">Check the form: times need hours and minutes, and places a whole number.</p>`; return; }
  const d = await r.json();
  if (!d.accepted) { out.innerHTML = `<p class="err">Not changed. The ${esc(d.reason)}.</p>`; return; }
  const n = d.affected.length;
  out.innerHTML = `<div class="ok">
      <b>${n}</b> of ${d.confirmed_count} confirmed booking${d.confirmed_count === 1 ? "" : "s"} in this pool
      ${n === 1 ? "overlaps" : "overlap"} the change and ${n === 1 ? "stays" : "stay"} booked. Rules are now version ${d.version}.
      ${n ? `<table><thead><tr><th>Confirmation</th><th>Driver</th><th>Booked</th></tr></thead><tbody>
        ${d.affected.map(a => `<tr><td>${esc(a.reservation_id)}</td><td>${esc(a.driver_id)}</td><td>${esc(a.start)} to ${esc(a.end)}</td></tr>`).join("")}
      </tbody></table>` : ""}
    </div>`;
  loadPools();
});

loadPools();
