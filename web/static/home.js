// The home page's motion. A scene is a weather effect played over a photograph: autumn leaves, cherry
// blossom, snow, rain, sun or dusk fireflies. The scene is chosen in scenes.js before the page draws; here
// the photo cross-fades in, particles fall at two depths (behind and in front of the words), the pointer
// drives parallax and gusts, scrolling pushes the camera in, and a menu picks a scene or shuffles them.
// With reduced motion the photos still change but nothing moves.
import { esc } from "/static/common.js";

const $ = id => document.getElementById(id);
const hero = document.querySelector(".hero");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const {scenes, scene: firstScene, photo: firstPhoto, mode: savedMode, srcset, commons} = window.CP_SCENES;
const pick = list => list[Math.floor(Math.random() * list.length)];
const SHUFFLE_MS = 20000;

/* ------------------------------------------------------------------ the tag on the empty space */
function slotText() {
  const tag = $("slot-text");
  if (!tag) return;
  const [h, m] = ($("arrival").value || "09:00").split(":").map(Number);
  const end = (h + Number($("hours").value || 2)) % 24;
  const pad = n => String(n).padStart(2, "0");
  tag.textContent = `Held for you · ${pad(h)}:${pad(m)}–${pad(end)}:${pad(m)}`;
}
["arrival", "hours"].forEach(id => $(id).addEventListener("input", slotText));
slotText();

/* ------------------------------------------------------------------ photographs */
function photoLayer(p) {
  const layer = document.createElement("div");
  layer.className = "photo";
  layer.innerHTML = p.local
    ? `<picture><source srcset="/static/media/${p.local}.avif" type="image/avif"><source srcset="/static/media/${p.local}.webp" type="image/webp">
       <img src="/static/media/${p.local}.jpg" alt="" decoding="async"></picture>`
    : `<img alt="" decoding="async" sizes="100vw" srcset="${srcset(p)}" src="${commons(p, 1280)}">`;
  return layer;
}

async function showPhoto(p, first) {
  const box = $("photos"), layer = photoLayer(p), old = [...box.children];
  box.appendChild(layer);
  if (!first) { try { await layer.querySelector("img").decode(); } catch {} }   // fade in only once it can be drawn
  requestAnimationFrame(() => layer.classList.add("on"));
  setTimeout(() => old.forEach(o => o.remove()), 1800);
  hero.style.setProperty("--scrim2", p.scrim2 ?? 0.4);
  const fx = document.querySelector(".sunfx");
  if (p.sun) { fx.style.setProperty("--sx", `${p.sun[0]}%`); fx.style.setProperty("--sy", `${p.sun[1]}%`); }
  hero.toggleAttribute("data-slot", !!p.slot);
  if (p.slot && !first) {   // draw the outline again for the photo it belongs to
    const svg = document.querySelector(".slot");
    svg.replaceWith(svg.cloneNode(true));
    slotText();
  }
  $("photo-credit").innerHTML = p.page
    ? `Photo: <a href="${p.page}" target="_blank" rel="noopener">${esc(p.place)}</a> · ${esc(p.by)}, ${esc(p.license)}` : "";
}

/* ------------------------------------------------------------------ particles */
const PALETTE = {
  leaves: ["#c8642b", "#d98a2b", "#a8441f", "#e0a33a", "#b8541f", "#8f3a1a", "#d4b04a"],
  petals: ["#ffd6e0", "#ffc2d1", "#ffb3c6", "#fde2e4", "#f9c6d3", "#ffe9f0"],
};
// count behind the words, count in front, depth range of each
const FX = {
  leaves: {back: [26, .35, 1.05], front: [4, 1.5, 2.3], wind: [14, 16]},
  petals: {back: [36, .35, 1.1], front: [5, 1.5, 2.4], wind: [20, 14]},
  snow: {back: [120, .3, 1.1], front: [7, 1.6, 2.6], wind: [6, 12]},
  rain: {back: [180, .4, 1.1], front: [9, 1.5, 2.2], wind: [36, 22]},
  sun: {back: [38, .3, 1], front: [3, 1.6, 2.2], wind: [4, 4]},
  fireflies: {back: [30, .35, 1.05], front: [4, 1.5, 2.2], wind: [0, 3]},
};
const canBlur = "filter" in CanvasRenderingContext2D.prototype;

function canvasFor(r, blur) {
  const pad = Math.ceil(blur * 3) + 2, c = document.createElement("canvas");
  c.width = c.height = Math.ceil(r * 2 + pad * 2);
  const g = c.getContext("2d");
  if (blur && canBlur) g.filter = `blur(${blur}px)`;
  g.translate(c.width / 2, c.height / 2);
  return [c, g];
}

function leafSprite(color, r, blur, maple) {
  const [c, g] = canvasFor(r, blur);
  g.beginPath();
  if (maple) {
    for (let i = 0; i <= 120; i++) {
      const a = (i / 120) * Math.PI * 2 - Math.PI / 2;
      const k = r * (0.5 + 0.5 * Math.pow(Math.abs(Math.cos(a * 2.5)), 0.7)) * (a > Math.PI * 0.3 && a < Math.PI * 0.7 ? 0.55 : 1);
      g[i ? "lineTo" : "moveTo"](Math.cos(a) * k, Math.sin(a) * k);
    }
  } else {
    g.moveTo(0, -r);
    g.quadraticCurveTo(r * 0.85, -r * 0.15, 0, r);
    g.quadraticCurveTo(-r * 0.85, -r * 0.15, 0, -r);
  }
  const shade = g.createLinearGradient(-r, -r, r, r);
  shade.addColorStop(0, color);
  shade.addColorStop(1, "rgba(40,14,4,.9)");
  g.fillStyle = color; g.fill();
  g.globalAlpha = 0.35; g.fillStyle = shade; g.fill(); g.globalAlpha = 1;
  g.strokeStyle = "rgba(255,230,190,.28)"; g.lineWidth = Math.max(0.6, r / 12);
  g.beginPath(); g.moveTo(0, -r * 0.8); g.lineTo(0, r * 1.15); g.stroke();
  return c;
}

function petalSprite(color, r, blur) {   // a cherry petal: a rounded teardrop with a notch at its tip
  const [c, g] = canvasFor(r, blur);
  g.beginPath();
  g.moveTo(0, r);
  g.bezierCurveTo(r * 0.95, r * 0.35, r * 0.7, -r * 0.85, r * 0.18, -r * 0.92);
  g.lineTo(0, -r * 0.62);
  g.lineTo(-r * 0.18, -r * 0.92);
  g.bezierCurveTo(-r * 0.7, -r * 0.85, -r * 0.95, r * 0.35, 0, r);
  const fill = g.createLinearGradient(0, r, 0, -r);
  fill.addColorStop(0, "#fff6f8");
  fill.addColorStop(1, color);
  g.fillStyle = fill; g.fill();
  return c;
}

function glowSprite(r, blur, inner, outer) {   // a soft round light: snowflakes, motes, fireflies
  const [c, g] = canvasFor(r, blur);
  const grad = g.createRadialGradient(0, 0, 0, 0, 0, r);
  grad.addColorStop(0, inner);
  grad.addColorStop(0.45, inner.replace(/[\d.]+\)$/, m => `${parseFloat(m) * 0.55})`));
  grad.addColorStop(1, outer);
  g.fillStyle = grad;
  g.beginPath(); g.arc(0, 0, r, 0, Math.PI * 2); g.fill();
  return c;
}

function streakSprite(len, width, blur) {   // a large out-of-focus raindrop close to the lens
  const [c, g] = canvasFor(len / 2 + width, blur);
  const grad = g.createLinearGradient(0, -len / 2, 0, len / 2);
  grad.addColorStop(0, "rgba(210,225,245,0)");
  grad.addColorStop(1, "rgba(220,232,250,.55)");
  g.strokeStyle = grad; g.lineWidth = width; g.lineCap = "round";
  g.beginPath(); g.moveTo(0, -len / 2); g.lineTo(0, len / 2); g.stroke();
  return c;
}

const blurFor = z => (z < 0.55 ? 1.4 : z > 1.4 ? 2.5 + (z - 1.4) * 3 : 0);

// how each kind of particle starts, moves and is drawn
const KIND = {
  leaves: {
    spawn(l, w, h, top) {
      const z = l.z, r = 5 + 11 * z;
      Object.assign(l, {x: Math.random() * (w + 200) - 100, y: top ? -40 - Math.random() * 200 : Math.random() * h,
        fall: 16 + 34 * z, sway: 18 + 38 * z, freq: 0.35 + Math.random() * 0.55, phase: Math.random() * 6.3,
        rot: Math.random() * 6.3, spin: (Math.random() - 0.5) * 2.4, tumble: 0.6 + Math.random() * 1.6, alpha: Math.min(1, 0.45 + z * 0.5),
        img: leafSprite(pick(PALETTE.leaves), r, blurFor(z), Math.random() < 0.6)});
    },
    step: (l, dt, t, wind, w, h) => fallStep(l, dt, t, wind, w, h),
    draw: (ctx, l, t) => drawTumbling(ctx, l, t),
  },
  petals: {
    spawn(l, w, h, top) {
      const z = l.z, r = 4 + 7 * z;
      Object.assign(l, {x: Math.random() * (w + 240) - 160, y: top ? -30 - Math.random() * 160 : Math.random() * h,
        fall: 12 + 24 * z, sway: 26 + 42 * z, freq: 0.5 + Math.random() * 0.7, phase: Math.random() * 6.3,
        rot: Math.random() * 6.3, spin: (Math.random() - 0.5) * 3.4, tumble: 1.2 + Math.random() * 2.2, alpha: Math.min(1, 0.55 + z * 0.4),
        img: petalSprite(pick(PALETTE.petals), r, blurFor(z))});
    },
    step: (l, dt, t, wind, w, h) => fallStep(l, dt, t, wind, w, h),
    draw: (ctx, l, t) => drawTumbling(ctx, l, t),
  },
  snow: {
    spawn(l, w, h, top) {
      const z = l.z, r = z > 1.4 ? 7 + 4 * z : 1.2 + 3.4 * z;
      Object.assign(l, {x: Math.random() * (w + 100) - 50, y: top ? -20 - Math.random() * 120 : Math.random() * h,
        fall: 18 + 42 * z, sway: 8 + 18 * z, freq: 0.3 + Math.random() * 0.5, phase: Math.random() * 6.3, rot: 0, spin: 0,
        alpha: z > 1.4 ? 0.55 : Math.min(1, 0.5 + z * 0.45),
        img: glowSprite(r, z > 1.4 ? 3 + z : z < 0.5 ? 0.8 : 0, "rgba(255,255,255,1)", "rgba(255,255,255,0)")});
    },
    step: (l, dt, t, wind, w, h) => fallStep(l, dt, t, wind, w, h),
    draw: (ctx, l) => { ctx.globalAlpha = l.alpha; ctx.drawImage(l.img, l.x - l.img.width / 2, l.y - l.img.height / 2); },
  },
  rain: {
    spawn(l, w, h, top) {
      const z = l.z;
      Object.assign(l, {x: Math.random() * (w + 300) - 150, y: top ? -60 - Math.random() * h * 0.5 : Math.random() * h,
        speed: 650 + 650 * z, len: 10 + 24 * z, width: 0.7 + 0.9 * z, alpha: 0.16 + 0.3 * Math.min(1, z),
        ground: h * (0.7 + Math.random() * 0.32),
        img: z > 1.4 ? streakSprite(40 + 30 * (z - 1.4), 2 + z, 2.5) : null});
    },
    step(l, dt, t, wind, w, h, layer) {
      const vx = wind * 2.2;
      l.x += vx * dt; l.y += l.speed * dt; l.vx = vx;
      if (!l.img && l.y > l.ground) { if (Math.random() < 0.35) layer.splash(l.x, l.ground, l.z); return false; }
      return l.y < h + 80 && l.x > -160 && l.x < w + 160;
    },
    draw(ctx, l) {
      if (l.img) {   // near the lens: a soft streak
        ctx.globalAlpha = 0.5;
        ctx.save(); ctx.translate(l.x, l.y); ctx.rotate(-Math.atan2(l.vx || 0, l.speed));
        ctx.drawImage(l.img, -l.img.width / 2, -l.img.height / 2); ctx.restore();
        return;
      }
      const k = l.len / l.speed;
      ctx.globalAlpha = l.alpha;
      ctx.lineWidth = l.width;
      ctx.beginPath(); ctx.moveTo(l.x, l.y); ctx.lineTo(l.x - (l.vx || 0) * k, l.y - l.len); ctx.stroke();
    },
  },
  sun: {   // warm motes drifting up through the light, and a few large soft discs
    spawn(l, w, h, top) {
      const z = l.z, big = z > 1.4, r = big ? 26 + 30 * (z - 1.4) : 1 + 1.8 * z;
      Object.assign(l, {x: Math.random() * w, y: top ? h + 20 : Math.random() * h, rise: big ? 4 : 5 + 10 * z,
        sway: 10 + 20 * z, freq: 0.15 + Math.random() * 0.3, phase: Math.random() * 6.3, twinkle: 0.8 + Math.random() * 2,
        base: big ? 0.12 : 0.35 + 0.5 * z,
        img: glowSprite(r, big ? 4 : 0, big ? "rgba(255,236,190,.55)" : "rgba(255,244,214,1)", "rgba(255,220,160,0)")});
    },
    step(l, dt, t, wind) {
      l.y -= l.rise * dt; l.x += (wind * 0.4 + Math.sin(t * l.freq + l.phase) * l.sway * 0.4) * dt;
      return l.y > -60;
    },
    draw(ctx, l, t) {
      ctx.globalAlpha = l.base * (0.55 + 0.45 * Math.sin(t * l.twinkle + l.phase));
      ctx.drawImage(l.img, l.x - l.img.width / 2, l.y - l.img.height / 2);
    },
  },
  fireflies: {   // wandering lights low over the ground, each blinking on its own rhythm
    spawn(l, w, h) {
      const z = l.z, big = z > 1.4, r = big ? 16 + 10 * (z - 1.4) : 5 + 7 * z;
      Object.assign(l, {x: Math.random() * w, y: h * (0.35 + Math.random() * 0.62), ax: 0.2 + Math.random() * 0.4, ay: 0.15 + Math.random() * 0.35,
        speed: 14 + 26 * z, phase: Math.random() * 6.3, blink: 0.5 + Math.random() * 1.1,
        img: glowSprite(r, big ? 3.5 : 0, "rgba(232,255,140,1)", "rgba(170,255,80,0)")});
    },
    step(l, dt, t, wind, w, h) {
      l.x += Math.sin(t * l.ax + l.phase) * l.speed * dt + wind * 0.3 * dt;
      l.y += Math.cos(t * l.ay + l.phase * 1.7) * l.speed * 0.6 * dt;
      if (l.x < -30) l.x = w + 30; if (l.x > w + 30) l.x = -30;
      l.y = Math.min(h * 0.98, Math.max(h * 0.28, l.y));
      return true;
    },
    draw(ctx, l, t) {
      ctx.globalAlpha = 0.15 + 0.85 * Math.pow(Math.max(0, Math.sin(t * l.blink + l.phase)), 3);
      ctx.drawImage(l.img, l.x - l.img.width / 2, l.y - l.img.height / 2);
    },
  },
};

function fallStep(l, dt, t, wind, w, h) {
  l.y += l.fall * dt;
  l.x += (wind * l.z + Math.sin(t * l.freq + l.phase) * l.sway * 0.9) * dt;
  l.rot += l.spin * dt;
  return !(l.y > h + 50 || l.x < -160 || l.x > w + 160);
}

function drawTumbling(ctx, l, t) {
  const flip = Math.cos(t * l.tumble + l.phase);   // the leaf or petal turning over in the air
  ctx.globalAlpha = l.alpha;
  ctx.save();
  ctx.translate(l.x, l.y); ctx.rotate(l.rot); ctx.scale(1, 0.25 + 0.75 * Math.abs(flip));
  ctx.drawImage(l.img, -l.img.width / 2, -l.img.height / 2);
  ctx.restore();
}

function particleLayer(canvas, which) {
  const ctx = canvas.getContext("2d");
  let w = 0, h = 0, dpr = 1, kind = null, parts = [], splashes = [];
  const size = () => {
    dpr = Math.min(1.75, devicePixelRatio || 1);
    w = canvas.clientWidth; h = canvas.clientHeight;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
  };
  size();
  new ResizeObserver(size).observe(canvas);
  const api = {
    set(name) {
      kind = KIND[name];
      const [count, zMin, zMax] = FX[name][which];
      const n = Math.max(1, Math.round(count * (innerWidth < 700 ? 0.5 : 1)));
      parts = Array.from({length: n}, () => { const l = {z: zMin + Math.random() * (zMax - zMin)}; kind.spawn(l, w, h, false); return l; });
      splashes = [];
    },
    splash(x, y, z) { splashes.push({x, y, z, age: 0}); },
    frame(t, dt, wind) {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      if (!kind) return;
      ctx.strokeStyle = "rgba(205,220,240,1)";
      for (const l of parts) {
        if (kind.step(l, dt, t, wind, w, h, api) === false) kind.spawn(l, w, h, true);
        kind.draw(ctx, l, t);
      }
      if (splashes.length) {   // rain hitting the ground: small rings that spread and fade
        ctx.lineWidth = 1;
        splashes = splashes.filter(s => (s.age += dt) < 0.35);
        for (const s of splashes) {
          ctx.globalAlpha = 0.45 * (1 - s.age / 0.35) * Math.min(1, s.z);
          ctx.beginPath(); ctx.ellipse(s.x, s.y, 2 + s.age * 26 * s.z, (2 + s.age * 26 * s.z) * 0.28, 0, 0, Math.PI * 2); ctx.stroke();
        }
      }
      ctx.globalAlpha = 1;
    },
  };
  return api;
}

/* ------------------------------------------------------------------ scenes */
let current = null, currentPhoto = null, mode = savedMode, shuffleTimer = 0, lightningTimer = 0, layers = null;

function lightning() {   // now and then the rain scene's sky flashes
  clearTimeout(lightningTimer);
  if (current?.effect !== "rain" || reduced) return;
  lightningTimer = setTimeout(() => {
    const f = document.querySelector(".flash");
    f.classList.remove("on"); void f.offsetWidth; f.classList.add("on");
    lightning();
  }, 9000 + Math.random() * 14000);
}

function setEffect(name, first) {
  if (!layers) return;
  const canvases = [$("leaves-back"), $("leaves-front")];
  if (first) { layers.forEach(l => l.set(name)); return; }
  canvases.forEach(c => { c.style.opacity = 0; });
  setTimeout(() => { layers.forEach(l => l.set(name)); canvases.forEach(c => { c.style.opacity = ""; }); }, 700);
}

function applyScene(s, p, first = false) {
  current = s;
  currentPhoto = p;
  hero.dataset.fx = s.effect;
  document.documentElement.dataset.scene = s.id;
  showPhoto(p, first);
  setEffect(s.effect, first);
  lightning();
  renderButton();
  if (!first) renderMenu();
}

function scheduleShuffle() {
  clearTimeout(shuffleTimer);
  document.documentElement.dataset.mode = mode;
  const clock = document.querySelector(".scene-btn .clock");
  clock.classList.remove("run");
  if (mode !== "shuffle") return;
  void clock.getBoundingClientRect();
  clock.classList.add("run");
  shuffleTimer = setTimeout(() => {
    if (!document.hidden && heroVisible) {
      const s = pick(scenes.filter(x => x !== current));
      applyScene(s, pick(s.photos));
    }
    scheduleShuffle();
  }, SHUFFLE_MS);
}

/* ------------------------------------------------------------------ the menu */
const ICON = {
  leaves: '<path d="M5 19c8 0 14-6 14-14-8 0-14 6-14 14z"/><path d="M5 19l8-8"/>',
  petals: '<circle cx="12" cy="12" r="2"/><path d="M12 10c-2-3-1-6 0-7 1 1 2 4 0 7zM14 12c3-2 6-1 7 0-1 1-4 2-7 0zM12 14c2 3 1 6 0 7-1-1-2-4 0-7zM10 12c-3 2-6 1-7 0 1-1 4-2 7 0z"/>',
  snow: '<path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7"/><path d="M9 4l3 2 3-2M9 20l3-2 3 2"/>',
  rain: '<path d="M6 14a4 4 0 0 1 .5-8 6 6 0 0 1 11.3 2A3.5 3.5 0 0 1 17.5 14H6z"/><path d="M8 17l-1 3M12 17l-1 3M16 17l-1 3"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4L6 18M18 6l1.4-1.4"/>',
  fireflies: '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/><path d="M17 3v3M15.5 4.5h3"/>',
  shuffle: '<path d="M3 7h3c4 0 6 10 10 10h5M3 17h3c1.6 0 2.8-1.6 3.8-3.5M14.2 10.5C15.2 8.6 16.4 7 18 7h3"/><path d="M18 4l3 3-3 3M18 14l3 3-3 3"/>',
  random: '<rect x="4" y="4" width="16" height="16" rx="4"/><circle cx="9" cy="9" r="1.2"/><circle cx="15" cy="15" r="1.2"/><circle cx="15" cy="9" r="1.2"/><circle cx="9" cy="15" r="1.2"/>',
};
const svg = d => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;

function renderButton() {
  $("scene-ico").innerHTML = svg(ICON[current.effect]);
  $("scene-name").textContent = mode === "shuffle" ? `Shuffle · ${current.name}` : current.name;
  $("scene-btn").setAttribute("aria-label", `Scene: ${current.name}. Change scene`);
}

function renderMenu() {
  const item = (value, icon, name, sub) => `<button type="button" role="menuitemradio" data-value="${value}" aria-checked="${mode === value}">
      <i>${svg(icon)}</i><span>${esc(name)}<small>${esc(sub)}</small></span></button>`;
  $("scene-menu").innerHTML = `<p>Scene</p>
    ${item("shuffle", ICON.shuffle, "Shuffle", "A new scene every 20 seconds")}
    ${item("random", ICON.random, "Surprise me", "A different scene on each visit")}
    <hr>
    ${scenes.map(s => item(s.id, ICON[s.effect], s.name, s.photos.map(p => p.place || "Cornell, autumn").join(" · "))).join("")}`;
}

function choose(value) {
  mode = value;
  try { localStorage.setItem("cp.scene", value); } catch {}
  const chosen = scenes.find(s => s.id === value);
  // picking a scene again shows another of its photos
  if (chosen) applyScene(chosen, pick(chosen.photos.length > 1 ? chosen.photos.filter(p => p !== currentPhoto) : chosen.photos));
  else if (value === "random") { const s = pick(scenes.filter(x => x !== current)); applyScene(s, pick(s.photos)); }
  scheduleShuffle();
  renderButton();
  renderMenu();
}

function toggleMenu(open = $("scene-menu").hidden) {
  $("scene-menu").hidden = !open;
  $("scene-btn").setAttribute("aria-expanded", String(open));
  if (open) { renderMenu(); $("scene-menu").querySelector('[aria-checked="true"]')?.focus(); }
}
$("scene-btn").addEventListener("click", () => toggleMenu());
$("scene-menu").addEventListener("click", e => {
  const b = e.target.closest("button[data-value]");
  if (b) { choose(b.dataset.value); toggleMenu(false); $("scene-btn").focus(); }
});
document.addEventListener("click", e => { if (!e.target.closest(".scene-ui")) toggleMenu(false); });
document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("scene-menu").hidden) { toggleMenu(false); $("scene-btn").focus(); } });

/* ------------------------------------------------------------------ pointer, scroll and the frame loop */
let heroVisible = true;
if (!reduced) layers = [particleLayer($("leaves-back"), "back"), particleLayer($("leaves-front"), "front")];
applyScene(firstScene, firstPhoto, true);
scheduleShuffle();

if (!reduced) {
  const target = {x: 0, y: 0}, now = {x: 0, y: 0};
  let gust = 0, lastX = null;
  hero.addEventListener("pointermove", e => {
    target.x = e.clientX / innerWidth * 2 - 1;
    target.y = e.clientY / innerHeight * 2 - 1;
    if (lastX !== null) gust = Math.max(-90, Math.min(90, gust + (e.clientX - lastX) * 0.6));   // a sweep of the mouse is a gust
    lastX = e.clientX;
  });
  hero.addEventListener("pointerleave", () => { target.x = 0; target.y = 0; lastX = null; });

  const fx = document.querySelector(".sunfx"), flares = [...fx.querySelectorAll(".flare")];
  let last = 0, running = false;
  const frame = t => {
    if (!heroVisible) { running = false; return; }
    const s = t / 1000, dt = Math.min(0.05, last ? s - last : 0.016);
    last = s;
    now.x += (target.x - now.x) * 0.06;
    now.y += (target.y - now.y) * 0.06;
    gust *= 0.96;
    const [base, swing] = FX[current.effect].wind;
    const wind = base + swing * Math.sin(s * 0.13) + gust;
    hero.style.setProperty("--mx", now.x.toFixed(4));
    hero.style.setProperty("--my", now.y.toFixed(4));
    layers.forEach(l => l.frame(s, dt, wind));
    if (current.effect === "sun") {   // flares sit on the line from the sun through the point opposite the pointer
      const W = hero.clientWidth, H = hero.clientHeight;
      const sx = parseFloat(fx.style.getPropertyValue("--sx") || 80) / 100 * W, sy = parseFloat(fx.style.getPropertyValue("--sy") || 6) / 100 * H;
      const cx = W / 2 - now.x * W * 0.25, cy = H / 2 - now.y * H * 0.25;
      flares.forEach(f => {
        const k = parseFloat(f.style.getPropertyValue("--k"));
        f.style.setProperty("--fx", `${sx + (cx - sx) * k}px`);
        f.style.setProperty("--fy", `${sy + (cy - sy) * k}px`);
      });
    }
    requestAnimationFrame(frame);
  };
  const start = () => { if (!running) { running = true; last = 0; requestAnimationFrame(frame); } };
  // everything stops when the hero is off screen
  new IntersectionObserver(([e]) => { heroVisible = e.isIntersecting; if (heroVisible) start(); }).observe(hero);
  start();

  const onScroll = () => hero.style.setProperty("--p", Math.min(1, Math.max(0, scrollY / innerHeight)).toFixed(4));
  addEventListener("scroll", onScroll, {passive: true});
  onScroll();

  /* ---------------------------------------------------------------- the section below */
  document.documentElement.classList.add("js-reveal");
  const io = new IntersectionObserver(entries => entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), {threshold: 0.18});
  document.querySelectorAll(".reveal").forEach(el => io.observe(el));

  if (matchMedia("(hover: hover)").matches) {
    document.querySelectorAll(".tile").forEach(tile => {
      tile.addEventListener("pointermove", e => {
        const r = tile.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        tile.classList.add("tilting");
        tile.style.setProperty("--ry", `${(x - 0.5) * 14}deg`);
        tile.style.setProperty("--rx", `${(0.5 - y) * 12}deg`);
        tile.style.setProperty("--gx", `${x * 100}%`);
        tile.style.setProperty("--gy", `${y * 100}%`);
      });
      tile.addEventListener("pointerleave", () => {
        tile.classList.remove("tilting");
        ["--rx", "--ry"].forEach(v => tile.style.setProperty(v, "0deg"));
      });
    });
  }
} else {
  new IntersectionObserver(([e]) => { heroVisible = e.isIntersecting; }).observe(hero);
}
