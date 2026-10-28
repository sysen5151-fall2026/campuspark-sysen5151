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
      <td>${p.permits.map(x => `<span class="chip">${esc(x)}</span>`).join("")}</td>
      <td><div class="cap">${p.capacity}</div></td>
      <td>${p.closures.length ? p.closures.map(c => `<span class="closed">${esc(c.start)} to ${esc(c.end)}</span>`).join("<br>") : "Open all day"}</td>
    </tr>`).join("");
  const keep = $("pool").value;
  $("pool").innerHTML = d.pools.map(p => `<option value="${esc(p.pool_id)}">${esc(p.name)}</option>`).join("");
  if (keep) $("pool").value = keep;
}

$("change").addEventListener("submit", async e => {
  e.preventDefault();
  const capacity = $("capacity").value, start = $("close-start").value, end = $("close-end").value;
  const out = $("result");
  if ((start && !end) || (!start && end)) { out.innerHTML = `<p class="notice">A closure needs both a start and an end time.</p>`; return; }
  const r = await fetch("/api/admin/controls", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({
    account: $("account").value, pool_id: $("pool").value, capacity: capacity === "" ? null : Number(capacity),
    clear_closures: $("clear").checked, add_closure: start && end ? {start, end} : null})});
  if (!r.ok) { out.innerHTML = `<p class="notice">Check the form: times need hours and minutes, and places a whole number.</p>`; return; }
  const d = await r.json();
  if (!d.accepted) { out.innerHTML = `<p class="notice">Not changed. The ${esc(d.reason)}.</p>`; return; }
  const n = d.affected.length;
  out.innerHTML = `<div class="done">
      <b>${n}</b> of ${d.confirmed_count} confirmed booking${d.confirmed_count === 1 ? "" : "s"} in this pool
      ${n === 1 ? "overlaps" : "overlap"} the change and ${n === 1 ? "stays" : "stay"} booked. Rules are now version ${d.version}.
      ${n ? `<table><thead><tr><th>Confirmation</th><th>Driver</th><th>Booked</th></tr></thead><tbody>
        ${d.affected.map(a => `<tr><td>${esc(a.reservation_id)}</td><td>${esc(a.driver_id)}</td><td>${esc(a.start)} to ${esc(a.end)}</td></tr>`).join("")}
      </tbody></table>` : ""}
    </div>`;
  loadPools();
});

loadPools();
