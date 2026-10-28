// Staff console: the controls in force (IO.17) and one change at a time through F.1 and F.7.
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}

async function loadPools() {
  const d = await (await fetch("/api/admin/pools")).json();
  document.getElementById("version").textContent = `Rules version ${d.version}.`;
  document.getElementById("pools").innerHTML = d.pools.map(p => `
    <tr>
      <td><div class="name">${esc(p.name)}</div><div class="id">${esc(p.pool_id)}</div></td>
      <td>${p.permits.map(x => `<span class="chip ${esc(x)}">${esc(x)}</span>`).join("")}</td>
      <td><strong>${p.capacity}</strong></td>
      <td>${p.closures.length
        ? p.closures.map(c => `<span class="closed">${esc(c.start)} to ${esc(c.end)}</span>`).join("<br>")
        : "Open all day"}</td>
    </tr>`).join("");
  const select = document.getElementById("pool");
  const keep = select.value;
  select.innerHTML = d.pools.map(p => `<option value="${esc(p.pool_id)}">${esc(p.name)}</option>`).join("");
  if (keep) select.value = keep;
}

async function submitChange(e) {
  e.preventDefault();
  const capacity = document.getElementById("capacity").value;
  const start = document.getElementById("close-start").value;
  const end = document.getElementById("close-end").value;
  const out = document.getElementById("result");
  if ((start && !end) || (!start && end)) {
    out.innerHTML = `<div class="notice">A closure needs both a start and an end time.</div>`;
    return;
  }
  const body = {
    account: document.getElementById("account").value,
    pool_id: document.getElementById("pool").value,
    capacity: capacity === "" ? null : Number(capacity),
    clear_closures: document.getElementById("clear").checked,
    add_closure: start && end ? {start, end} : null
  };
  const r = await fetch("/api/admin/controls", {method: "POST", headers: {"Content-Type": "application/json"},
                                                body: JSON.stringify(body)});
  if (!r.ok) {
    out.innerHTML = `<div class="notice">Check the form: times need hours and minutes, and places a whole number.</div>`;
    return;
  }
  const d = await r.json();
  if (!d.accepted) {
    out.innerHTML = `<div class="notice"><strong>Not changed.</strong> The ${esc(d.reason)}.</div>`;
    return;
  }
  const n = d.affected.length;
  out.innerHTML = `<div class="notice quiet" style="border-left-color: var(--curb); color: var(--ink)">
      <strong>Applied. Rules are now version ${d.version}.</strong>
      <p style="margin: 6px 0 0">${d.confirmed_count} confirmed booking${d.confirmed_count === 1 ? "" : "s"} in this pool;
        ${n ? `${n} overlap${n === 1 ? "s" : ""} the change and stay booked. Contact these drivers:` : "none overlaps the change."}</p>
      ${n ? `<table><thead><tr><th>Confirmation</th><th>Driver</th><th>Booked</th></tr></thead><tbody>
        ${d.affected.map(a => `<tr><td>${esc(a.reservation_id)}</td><td>${esc(a.driver_id)}</td><td>${esc(a.start)} to ${esc(a.end)}</td></tr>`).join("")}
      </tbody></table>` : ""}
    </div>`;
  loadPools();
}

loadPools();
