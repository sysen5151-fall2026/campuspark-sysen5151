// The home page's motion: falling leaves at two depths, pointer parallax, a camera that pushes in as you
// scroll, the empty space's tag following the trip being typed, sections that rise into view, and tiles that
// tilt toward the pointer. Nothing here is needed to search; with reduced motion only the tag text runs.
const $ = id => document.getElementById(id);
const hero = document.querySelector(".hero");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ------------------------------------------------------------------ the tag on the empty space */
function slotText() {
  const [h, m] = ($("arrival").value || "09:00").split(":").map(Number);
  const end = (h + Number($("hours").value || 2)) % 24;
  const pad = n => String(n).padStart(2, "0");
  $("slot-text").textContent = `Held for you · ${pad(h)}:${pad(m)}–${pad(end)}:${pad(m)}`;
}
["arrival", "hours"].forEach(id => $(id).addEventListener("input", slotText));
slotText();

if (!reduced) {
  /* ---------------------------------------------------------------- leaves */
  const COLORS = ["#c8642b", "#d98a2b", "#a8441f", "#e0a33a", "#b8541f", "#8f3a1a", "#d4b04a"];
  const canBlur = "filter" in CanvasRenderingContext2D.prototype;

  // one leaf drawn once into a small canvas; maple-like lobes or a simple oval, lit from one side
  function sprite(color, r, blur, maple) {
    const pad = Math.ceil(blur * 3) + 2, c = document.createElement("canvas");
    c.width = c.height = Math.ceil(r * 2 + pad * 2);
    const g = c.getContext("2d");
    if (blur && canBlur) g.filter = `blur(${blur}px)`;
    g.translate(c.width / 2, c.height / 2);
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
    g.fillStyle = color;
    g.fill();
    g.globalAlpha = 0.35;
    g.fillStyle = shade;
    g.fill();
    g.globalAlpha = 1;
    g.strokeStyle = "rgba(255,230,190,.28)";
    g.lineWidth = Math.max(0.6, r / 12);
    g.beginPath(); g.moveTo(0, -r * 0.8); g.lineTo(0, r * 1.15); g.stroke();
    return c;
  }

  function layer(canvas, count, zMin, zMax) {
    const ctx = canvas.getContext("2d");
    let w = 0, h = 0, dpr = 1;
    const leaves = [];
    const size = () => {
      dpr = Math.min(1.75, devicePixelRatio || 1);
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    };
    const spawn = (leaf, top) => {
      const z = zMin + Math.random() * (zMax - zMin);
      const r = 5 + 11 * z;
      Object.assign(leaf, {
        z, x: Math.random() * (w + 200) - 100, y: top ? -40 - Math.random() * 200 : Math.random() * h,
        fall: 16 + 34 * z, sway: 18 + 38 * z, freq: 0.35 + Math.random() * 0.55, phase: Math.random() * 6.3,
        rot: Math.random() * 6.3, spin: (Math.random() - 0.5) * 2.4, tumble: 0.6 + Math.random() * 1.6,
        alpha: Math.min(1, 0.45 + z * 0.5),
        img: sprite(COLORS[Math.floor(Math.random() * COLORS.length)], r, z < 0.55 ? 1.6 : z > 1.4 ? 2.5 + (z - 1.4) * 3 : 0, Math.random() < 0.6),
      });
      return leaf;
    };
    size();
    for (let i = 0; i < count; i++) leaves.push(spawn({}, false));
    new ResizeObserver(size).observe(canvas);
    return (t, dt, wind) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      for (const l of leaves) {
        l.y += l.fall * dt;
        l.x += (wind * l.z + Math.sin(t * l.freq + l.phase) * l.sway * 0.9) * dt;
        l.rot += l.spin * dt;
        if (l.y > h + 50 || l.x < -140 || l.x > w + 140) spawn(l, true);
        const flip = Math.cos(t * l.tumble + l.phase);   // the leaf turning over in the air
        ctx.save();
        ctx.globalAlpha = l.alpha;
        ctx.translate(l.x, l.y);
        ctx.rotate(l.rot);
        ctx.scale(1, 0.25 + 0.75 * Math.abs(flip));
        ctx.drawImage(l.img, -l.img.width / 2, -l.img.height / 2);
        ctx.restore();
      }
    };
  }

  const narrow = innerWidth < 700;
  const back = layer($("leaves-back"), narrow ? 12 : 26, 0.35, 1.05);
  const front = layer($("leaves-front"), narrow ? 1 : 4, 1.5, 2.3);

  /* ---------------------------------------------------------------- pointer, scroll and the frame loop */
  const target = {x: 0, y: 0}, now = {x: 0, y: 0};
  let gust = 0, lastX = null;
  hero.addEventListener("pointermove", e => {
    target.x = e.clientX / innerWidth * 2 - 1;
    target.y = e.clientY / innerHeight * 2 - 1;
    if (lastX !== null) gust = Math.max(-80, Math.min(80, gust + (e.clientX - lastX) * 0.6));   // a sweep of the mouse is a gust
    lastX = e.clientX;
  });
  hero.addEventListener("pointerleave", () => { target.x = 0; target.y = 0; lastX = null; });

  let visible = true, last = 0, running = false;
  const frame = t => {
    if (!visible) { running = false; return; }
    const s = t / 1000, dt = Math.min(0.05, last ? s - last : 0.016);
    last = s;
    now.x += (target.x - now.x) * 0.06;
    now.y += (target.y - now.y) * 0.06;
    gust *= 0.96;
    const wind = 14 + 16 * Math.sin(s * 0.13) + gust;
    hero.style.setProperty("--mx", now.x.toFixed(4));
    hero.style.setProperty("--my", now.y.toFixed(4));
    back(s, dt, wind);
    front(s, dt, wind);
    requestAnimationFrame(frame);
  };
  const start = () => { if (!running) { running = true; last = 0; requestAnimationFrame(frame); } };
  // the leaves stop when the hero is off screen
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) start(); }).observe(hero);
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
}
