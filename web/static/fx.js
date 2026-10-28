// Shared by every page: a light that follows the pointer across glass, primary buttons that lean toward the
// pointer, and a command menu (⌘K or Ctrl K, or the Search button in the top bar) that reaches any page,
// destination or recent booking in a few keystrokes. A page can add its own commands to window.CP_COMMANDS.
import { esc, recent, destinations } from "/static/common.js";

const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;
const mac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

/* ------------------------------------------------------------------ light on glass */
const GLASS = ".card, .sheet, .side, .search, .summary .chips, .recent, .dial, .scene-btn, .tile .cap, .palette-box";
if (finePointer) {
  let lit = null;
  addEventListener("pointermove", e => {
    const el = e.target.closest?.(GLASS) || null;
    if (lit && lit !== el) lit.classList.remove("lit");
    lit = el;
    if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty("--hx", `${Math.round(e.clientX - r.left)}px`);
    el.style.setProperty("--hy", `${Math.round(e.clientY - r.top)}px`);
    el.classList.add("lit");
  }, {passive: true});
}

/* ------------------------------------------------------------------ buttons that lean toward the pointer */
if (finePointer && !reduced) {
  let pulled = null;
  const release = () => { pulled?.style.removeProperty("--mgx"); pulled?.style.removeProperty("--mgy"); pulled = null; };
  addEventListener("pointermove", e => {
    const b = e.target.closest?.(".btn:not(:disabled)");
    if (b !== pulled) release();
    if (!b) return;
    pulled = b;
    const r = b.getBoundingClientRect(), k = r.width > 300 ? 0.04 : 0.16;
    b.style.setProperty("--mgx", `${((e.clientX - r.left) / r.width - 0.5) * r.width * k}px`);
    b.style.setProperty("--mgy", `${((e.clientY - r.top) / r.height - 0.5) * r.height * 0.3}px`);
  }, {passive: true});
  addEventListener("pointerleave", release);
}

/* ------------------------------------------------------------------ the command menu */
const ICON = {
  go: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  home: '<path d="M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z"/>',
  ticket: '<path d="M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2a3 3 0 0 0 0 6v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-2a3 3 0 0 0 0-6z"/><path d="M14 5v14" stroke-dasharray="2 2.5"/>',
  shield: '<path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
  pin: '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/>',
};
const svg = d => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;

function nextQuarter() {
  const d = new Date(Date.now() + 15 * 60000);
  d.setMinutes(Math.floor(d.getMinutes() / 15) * 15);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

async function commands() {
  const at = nextQuarter();
  const go = href => () => { location.href = href; };
  const list = [
    {group: "Go to", title: "Home", hint: "Search for parking", icon: ICON.home, run: go("/")},
    {group: "Go to", title: "My bookings", hint: "Open a booking with its confirmation number", icon: ICON.ticket, run: go("/bookings")},
    {group: "Go to", title: "Staff controls", hint: "Places and closures in force", icon: ICON.shield, run: go("/admin")},
  ];
  try {
    for (const d of await destinations()) {
      list.push({group: "Find parking", title: `Parking near ${d}`, hint: `Arriving ${at}, staying 2 hours`, icon: ICON.pin,
                 run: go(`/find?${new URLSearchParams({to: d, at, hours: 2})}`)});
    }
  } catch {}
  for (const b of recent.all()) {
    list.push({group: "Recent bookings", title: `${b.lot}, ${b.start} to ${b.end}`, hint: b.id, icon: ICON.ticket,
               run: go(`/booking/${encodeURIComponent(b.id)}`)});
  }
  for (const c of window.CP_COMMANDS || []) list.push({group: "On this page", icon: ICON.spark, ...c});
  return list;
}

let palette = null, items = [], shown = [], active = 0, lastFocus = null;

function build() {
  palette = document.createElement("div");
  palette.className = "palette";
  palette.hidden = true;
  palette.innerHTML = `
    <div class="palette-box" role="dialog" aria-modal="true" aria-label="Command menu">
      <label class="palette-input">${svg(ICON.search)}
        <input id="palette-q" placeholder="Go anywhere: pages, destinations, bookings…" autocomplete="off" spellcheck="false"
               role="combobox" aria-expanded="true" aria-controls="palette-list" aria-autocomplete="list">
        <kbd>esc</kbd></label>
      <ul class="palette-list" id="palette-list" role="listbox"></ul>
      <div class="palette-foot"><span><kbd>↑</kbd><kbd>↓</kbd> move</span><span><kbd>↵</kbd> open</span><span><kbd>${mac ? "⌘" : "Ctrl"}</kbd><kbd>K</kbd> toggle</span></div>
    </div>`;
  document.body.appendChild(palette);
  const q = palette.querySelector("input");
  q.addEventListener("input", () => { active = 0; render(q.value); });
  q.addEventListener("keydown", e => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      active = (active + (e.key === "ArrowDown" ? 1 : -1) + shown.length) % Math.max(1, shown.length);
      highlight();
    } else if (e.key === "Enter" && shown[active]) { e.preventDefault(); runItem(shown[active]); }
  });
  palette.addEventListener("pointerdown", e => { if (e.target === palette) close(); });
  palette.querySelector(".palette-list").addEventListener("click", e => {
    const li = e.target.closest("li[data-i]");
    if (li) runItem(shown[+li.dataset.i]);
  });
  palette.querySelector(".palette-list").addEventListener("pointermove", e => {
    const li = e.target.closest("li[data-i]");
    if (li && +li.dataset.i !== active) { active = +li.dataset.i; highlight(); }
  });
}

function render(query) {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  shown = items.filter(c => words.every(w => `${c.title} ${c.hint} ${c.group}`.toLowerCase().includes(w)));
  let group = "", html = "";
  shown.forEach((c, i) => {
    if (c.group !== group) { group = c.group; html += `<li class="palette-group" role="presentation">${esc(group)}</li>`; }
    html += `<li role="option" id="pal-${i}" data-i="${i}"><i>${svg(c.icon)}</i><span>${esc(c.title)}<small>${esc(c.hint)}</small></span>${svg(ICON.go)}</li>`;
  });
  palette.querySelector(".palette-list").innerHTML = html || `<li class="palette-empty">Nothing matches “${esc(query)}”.</li>`;
  highlight();
}

function highlight() {
  palette.querySelectorAll("li[data-i]").forEach(li => li.setAttribute("aria-selected", String(+li.dataset.i === active)));
  const cur = palette.querySelector(`#pal-${active}`);
  palette.querySelector("input").setAttribute("aria-activedescendant", cur ? cur.id : "");
  cur?.scrollIntoView({block: "nearest"});
}

function runItem(c) { close(); c.run(); }

async function open() {
  if (!palette) build();
  if (!palette.hidden) return;
  lastFocus = document.activeElement;
  items = await commands();
  palette.hidden = false;
  document.documentElement.classList.add("palette-open");
  const q = palette.querySelector("input");
  q.value = "";
  active = 0;
  render("");
  q.focus();
}

function close() {
  if (!palette || palette.hidden) return;
  palette.hidden = true;
  document.documentElement.classList.remove("palette-open");
  lastFocus?.focus?.();
}

addEventListener("keydown", e => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); palette && !palette.hidden ? close() : open(); }
  else if (e.key === "Escape" && palette && !palette.hidden) { e.preventDefault(); close(); }
});

// the Search button in the top bar
const nav = document.querySelector(".bar nav");
if (nav) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "kbar";
  b.setAttribute("aria-label", "Open the command menu");
  b.innerHTML = `${svg(ICON.search)}<span>Search</span><kbd>${mac ? "⌘" : "Ctrl"} K</kbd>`;
  b.addEventListener("click", open);
  nav.prepend(b);
}
