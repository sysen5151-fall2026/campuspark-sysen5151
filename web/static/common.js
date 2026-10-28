// Shared by every driver page: escaping, API calls, the trip kept between pages, and the top bar.
export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c =>
    ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}

export async function api(url, body) {
  const r = await fetch(url, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)
  });
  if (r.status === 422) return {error: "Check the trip: the arrival needs a time and the stay at least one hour."};
  if (!r.ok) return {error: "Something went wrong on our side, so nothing was booked. Try again in a moment."};
  return r.json();
}

// The driver ID stays in this tab's session and never goes into a URL.
export const session = {
  get driver() { try { return sessionStorage.getItem("cp.driver") || ""; } catch { return ""; } },
  set driver(v) { try { sessionStorage.setItem("cp.driver", v); } catch {} },
  get pending() { try { return JSON.parse(sessionStorage.getItem("cp.pending") || "null"); } catch { return null; } },
  set pending(v) { try { sessionStorage.setItem("cp.pending", JSON.stringify(v)); } catch {} },
  take(key) { try { const v = sessionStorage.getItem(key); sessionStorage.removeItem(key); return v; } catch { return null; } },
  put(key, v) { try { sessionStorage.setItem(key, v); } catch {} },
};

// Bookings made on this device, newest first, so "My bookings" can list them without an account.
export const recent = {
  all() { try { return JSON.parse(localStorage.getItem("cp.recent") || "[]"); } catch { return []; } },
  add(b) {
    try {
      const list = [b, ...this.all().filter(x => x.id !== b.id)].slice(0, 8);
      localStorage.setItem("cp.recent", JSON.stringify(list));
    } catch {}
  },
};

export function lotImage(poolId) {
  return `/static/media/lot-${poolId}.jpg`;
}

export async function destinations() {
  return (await (await fetch("/api/destinations")).json()).destinations;
}

export function stepper(root, min, max) {
  const out = root.querySelector("output"), input = root.querySelector("input");
  const show = () => { out.textContent = `${input.value} hr${input.value === "1" ? "" : "s"}`; };
  root.querySelector("[data-dec]").addEventListener("click", () => { input.value = Math.max(min, +input.value - 1); show(); });
  root.querySelector("[data-inc]").addEventListener("click", () => { input.value = Math.min(max, +input.value + 1); show(); });
  show();
}
