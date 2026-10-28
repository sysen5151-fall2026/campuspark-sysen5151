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

// A real aerial photo of the lot: USGS National Map imagery (public domain), cropped around the lot.
export function lotAerial(lat, lon, w = 600, h = 400) {
  if (lat == null || lon == null) return "";
  const dLat = 0.0011, dLon = dLat * (w / h) / Math.cos(lat * Math.PI / 180);
  const bbox = [lon - dLon, lat - dLat, lon + dLon, lat + dLat].join(",");
  return "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/export?" +
    `bbox=${bbox}&bboxSR=4326&imageSR=3857&size=${w},${h}&format=jpg&f=image`;
}

// Real photographs of comparable campus lots and garages from Wikimedia Commons, free licences, credited
// where shown. No freely licensed photo of the fixture lots themselves exists, so each one stands in for
// its lot and is labelled that way; the aerial tab shows the actual spot.
const COMMONS = "https://upload.wikimedia.org/wikipedia/commons/thumb/";
export const LOT_PHOTOS = {
  "A-lot": {path: "b/bf/Summit_View_Parking_Lot_-_University_of_Wyoming_Campus_%2852511610724%29.jpg",
            place: "Summit View lot, University of Wyoming", by: "Tony Webster", license: "CC BY 2.0",
            page: "https://commons.wikimedia.org/wiki/File:Summit_View_Parking_Lot_-_University_of_Wyoming_Campus_(52511610724).jpg"},
  "hoy-garage": {path: "a/a9/Thompson_Parking_Structure_at_Night%2C_University_of_Michigan_Campus%2C_Ann_Arbor%2C_Michigan_-_panoramio.jpg",
                 place: "Thompson Street structure, University of Michigan", by: "Dwight Burdette", license: "CC BY 3.0",
                 page: "https://commons.wikimedia.org/wiki/File:Thompson_Parking_Structure_at_Night,_University_of_Michigan_Campus,_Ann_Arbor,_Michigan_-_panoramio.jpg"},
  "forest-home": {path: "b/b6/Parking_lot_at_Lake_Meridian_Park_%282025%29_-_0001.jpg",
                  place: "Lake Meridian Park lot, Kent, WA", by: "Roc0ast3r", license: "CC0",
                  page: "https://commons.wikimedia.org/wiki/File:Parking_lot_at_Lake_Meridian_Park_(2025)_-_0001.jpg"},
  "visitor-garage": {path: "0/05/VSU_Oak_St_Parking_Deck_5.jpg",
                     place: "Oak Street deck, Valdosta State University", by: "Michael Rivera", license: "CC BY-SA 3.0",
                     page: "https://commons.wikimedia.org/wiki/File:VSU_Oak_St_Parking_Deck_5.jpg"},
};

// w is the widest the photo is drawn, in device pixels; Commons serves these standard widths
export function lotPhotoUrl(poolId, w) {
  const p = LOT_PHOTOS[poolId];
  if (!p) return "";
  const size = [330, 500, 960, 1280].find(s => s >= w) || 1920;
  return `${COMMONS}${p.path}/${size}px-${p.path.split("/").pop()}`;
}

export function lotPhotoCredit(poolId) {
  const p = LOT_PHOTOS[poolId];
  return p ? `Similar lot: <a href="${p.page}" target="_blank" rel="noopener">${esc(p.place)}</a> · ${esc(p.by)}, ${esc(p.license)}` : "";
}

// The lot's photo over a plain gradient. (A layer underneath would be downloaded even when hidden.)
export function lotPhotoStyle(poolId, w) {
  const photo = lotPhotoUrl(poolId, w);
  return `background-image:${photo ? `url('${photo}'), ` : ""}linear-gradient(135deg,#2a2f3a,#161a22)`;
}

export function lotImageStyle(lat, lon, w, h) {
  const aerial = lotAerial(lat, lon, w, h);
  return `background-image:${aerial ? `url('${aerial}'), ` : ""}linear-gradient(135deg,#2a2f3a,#161a22)`;
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
