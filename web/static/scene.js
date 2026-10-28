// The 3D world behind the driver page: a lot at dusk for the opening, the whole campus for booking.
// Everything is generated here; there are no image or model files.
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { CSS2DRenderer, CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";

const AMBER = new THREE.Color("#ffb547");
const NIGHT = new THREE.Color("#06080c");
const STALL_W = 2.7, STALL_D = 5.4, AISLE = 7;
const CAR_COLORS = ["#e9e9ec", "#a7adb5", "#2a2e35", "#203a5c", "#7c2323", "#cfc7b8", "#3c4a3f"];

let renderer, composer, labels, scene, camera, clock;
const cam = {px: 26, py: 11, pz: 30, tx: 0, ty: 1, tz: 2};   // animated by the page
const state = {idle: 1, stallGlow: 0, freeGlow: 0};
const world = {lots: {}, dests: {}, hero: null, route: null, routeMat: null, held: null};
let reduced = false;

function rng(seed) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}

/* ------------------------------------------------------------------ textures */
function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.35, "rgba(255,255,255,.35)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}

function pTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 512;
  const g = c.getContext("2d");
  g.fillStyle = "#ffb547";
  g.beginPath();
  g.roundRect(40, 40, 432, 432, 96);
  g.fill();
  g.fillStyle = "#1a1206";
  g.font = "700 330px -apple-system, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText("P", 262, 280);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

/* ------------------------------------------------------------------ a lot */
const geo = {
  line: new THREE.BoxGeometry(0.12, 0.02, STALL_D * 0.92),
  body: new RoundedBoxGeometry(1.86, 1.05, 4.3, 3, 0.42),
  cabin: new RoundedBoxGeometry(1.58, 0.62, 2.25, 3, 0.28),
  lamp: new THREE.BoxGeometry(0.34, 0.12, 0.06),
  pole: new THREE.CylinderGeometry(0.09, 0.12, 7.5, 10),
  head: new THREE.CylinderGeometry(0.42, 0.5, 0.16, 28),
  trunk: new THREE.CylinderGeometry(0.16, 0.22, 2.2, 6),
  crown: new THREE.IcosahedronGeometry(1.5, 1),
};
const mat = {
  line: new THREE.MeshStandardMaterial({color: "#d9d9d9", emissive: "#3a3a3a", roughness: 0.6}),
  body: new THREE.MeshStandardMaterial({roughness: 0.32, metalness: 0.55}),
  glass: new THREE.MeshStandardMaterial({color: "#0b0e13", roughness: 0.08, metalness: 0.9}),
  head: new THREE.MeshStandardMaterial({color: "#fff4e0", emissive: "#fff1d6", emissiveIntensity: 1.1}),
  tail: new THREE.MeshStandardMaterial({color: "#ff3b30", emissive: "#ff2a1f", emissiveIntensity: 1.2}),
  pole: new THREE.MeshStandardMaterial({color: "#3a3d42", roughness: 0.5, metalness: 0.6}),
  lampHead: new THREE.MeshStandardMaterial({color: "#ffe2b0", emissive: "#ffc477", emissiveIntensity: 2.2}),
  trunk: new THREE.MeshStandardMaterial({color: "#1a1410", roughness: 0.9}),
  crown: new THREE.MeshStandardMaterial({color: "#1b2c22", roughness: 0.8, flatShading: true}),
  patch: new THREE.MeshStandardMaterial({color: "#15181d", roughness: 0.48, metalness: 0.15}),
};

function buildLot(capacity, occupied, seed, detailed) {
  const group = new THREE.Group();
  const perRow = Math.min(10, capacity), rows = Math.ceil(capacity / perRow);
  const stalls = [];
  for (let i = 0; i < capacity; i++) {
    const r = Math.floor(i / perRow), c = i % perRow, pair = Math.floor(r / 2);
    const x = (c - (perRow - 1) / 2) * STALL_W;
    const z = pair * (2 * STALL_D + AISLE) + (r % 2) * STALL_D;
    stalls.push({x, z, facing: r % 2 ? 1 : -1, occupied: false});
  }
  const depth = (Math.ceil(rows / 2)) * (2 * STALL_D + AISLE) - AISLE;
  const zOff = -depth / 2 + STALL_D / 2;
  stalls.forEach(s => { s.z += zOff; });

  const patch = new THREE.Mesh(new THREE.PlaneGeometry(perRow * STALL_W + 10, depth + 12), mat.patch);
  patch.rotation.x = -Math.PI / 2;
  patch.position.y = 0.01;
  patch.receiveShadow = true;
  group.add(patch);

  const lines = new THREE.InstancedMesh(geo.line, mat.line, capacity + rows);
  let k = 0;
  const m = new THREE.Matrix4();
  stalls.forEach((s, i) => {
    m.makeTranslation(s.x - STALL_W / 2, 0.03, s.z);
    lines.setMatrixAt(k++, m);
    if (i % perRow === perRow - 1 || i === capacity - 1) {
      m.makeTranslation(s.x + STALL_W / 2, 0.03, s.z);
      lines.setMatrixAt(k++, m);
    }
  });
  lines.count = k;
  group.add(lines);

  const rand = rng(seed);
  const order = stalls.map((_, i) => i).sort(() => rand() - 0.5);
  order.slice(0, occupied).forEach(i => { stalls[i].occupied = true; });
  const cars = stalls.filter(s => s.occupied);
  if (cars.length) {
    const bodies = new THREE.InstancedMesh(geo.body, mat.body, cars.length);
    const cabins = new THREE.InstancedMesh(geo.cabin, mat.glass, cars.length);
    const heads = new THREE.InstancedMesh(geo.lamp, mat.head, cars.length * 2);
    const tails = new THREE.InstancedMesh(geo.lamp, mat.tail, cars.length * 2);
    const q = new THREE.Quaternion(), sc = new THREE.Vector3(1, 1, 1), color = new THREE.Color();
    cars.forEach((s, i) => {
      const yaw = (rand() - 0.5) * 0.08;
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
      const jitter = (rand() - 0.5) * 0.25;
      m.compose(new THREE.Vector3(s.x + jitter, 0.72, s.z), q, sc);
      bodies.setMatrixAt(i, m);
      bodies.setColorAt(i, color.set(CAR_COLORS[Math.floor(rand() * CAR_COLORS.length)]));
      m.compose(new THREE.Vector3(s.x + jitter, 1.48, s.z - 0.25 * s.facing), q, sc);
      cabins.setMatrixAt(i, m);
      [-0.62, 0.62].forEach((dx, j) => {
        m.compose(new THREE.Vector3(s.x + jitter + dx, 0.8, s.z + 2.16 * s.facing), q, sc);
        heads.setMatrixAt(i * 2 + j, m);
        m.compose(new THREE.Vector3(s.x + jitter + dx, 0.86, s.z - 2.16 * s.facing), q, sc);
        tails.setMatrixAt(i * 2 + j, m);
      });
    });
    [bodies, cabins].forEach(x => { x.castShadow = detailed; x.receiveShadow = detailed; group.add(x); });
    if (detailed) { group.add(heads); group.add(tails); }
  }

  // trees along the edges
  const treeCount = detailed ? 16 : 8;
  const trunks = new THREE.InstancedMesh(geo.trunk, mat.trunk, treeCount);
  const crowns = new THREE.InstancedMesh(geo.crown, mat.crown, treeCount);
  for (let i = 0; i < treeCount; i++) {
    const side = detailed ? [0, 1, 3][i % 3] : i % 4, f = rand() - 0.5;   // keep the camera side of the hero lot open
    const ex = perRow * STALL_W / 2 + 9 + rand() * 6, ez = depth / 2 + 9 + rand() * 6;
    const x = side < 2 ? (side ? ex : -ex) : f * 2 * ex;
    const z = side < 2 ? f * 2 * ez : (side === 2 ? ez : -ez);
    const sz = 0.65 + rand() * 0.45;
    m.compose(new THREE.Vector3(x, 1.1 * sz, z), new THREE.Quaternion(), new THREE.Vector3(sz, sz, sz));
    trunks.setMatrixAt(i, m);
    m.compose(new THREE.Vector3(x, 3.4 * sz, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rand(), rand(), 0)),
              new THREE.Vector3(sz, sz * 1.15, sz));
    crowns.setMatrixAt(i, m);
  }
  crowns.castShadow = detailed;
  group.add(trunks, crowns);

  // light poles on the corners
  const hw = perRow * STALL_W / 2 + 3.2, hd = depth / 2 + 3.5;
  [[-hw, -hd], [hw, -hd], [-hw, hd], [hw, hd]].forEach(([x, z], i) => {
    const pole = new THREE.Mesh(geo.pole, mat.pole);
    pole.position.set(x, 3.75, z);
    group.add(pole);
    const head = new THREE.Mesh(geo.head, mat.lampHead);
    head.position.set(x, 7.55, z);
    group.add(head);
    if (detailed && i < 4) {
      const light = new THREE.PointLight("#ffc98a", 70, 40, 1.5);
      light.position.set(x, 7.1, z);
      group.add(light);
    }
  });
  return {group, stalls, width: perRow * STALL_W, depth};
}

/* ------------------------------------------------------------------ the hero's empty stall */
function buildHeroStall(stall, glowTex) {
  const g = new THREE.Group();
  g.position.set(stall.x, 0, stall.z);
  const amberLine = new THREE.MeshStandardMaterial({color: AMBER, emissive: AMBER, emissiveIntensity: 0});
  const sides = [[0.12, STALL_D * 0.92, -STALL_W / 2, 0], [0.12, STALL_D * 0.92, STALL_W / 2, 0],
                 [STALL_W, 0.12, 0, -STALL_D * 0.46]];
  sides.forEach(([w, d, x, z]) => {
    const b = new THREE.Mesh(new THREE.BoxGeometry(w, 0.03, d), amberLine);
    b.position.set(x, 0.05, z);
    g.add(b);
  });
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(STALL_W * 2.6, STALL_D * 1.9),
    new THREE.MeshBasicMaterial({map: glowTex, color: AMBER, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false}));
  glow.rotation.x = -Math.PI / 2;
  glow.position.y = 0.06;
  g.add(glow);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: pTexture(), transparent: true, opacity: 0}));
  sprite.scale.set(1.9, 1.9, 1);
  sprite.position.y = 3.1;
  g.add(sprite);
  return {group: g, amberLine, glow, sprite};
}

/* ------------------------------------------------------------------ sky and buildings */
function skyDome() {
  const m = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: {top: {value: new THREE.Color("#04060a")}, horizon: {value: new THREE.Color("#1a2540")}, glow: {value: new THREE.Color("#3a2a24")}},
    vertexShader: `varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform vec3 top; uniform vec3 horizon; uniform vec3 glow; varying vec3 vP;
      void main(){ float h = clamp(vP.y, 0.0, 1.0);
        vec3 c = mix(horizon, top, pow(h, 0.45));
        c += glow * pow(1.0 - h, 10.0) * 0.6;
        gl_FragColor = vec4(c, 1.0); }`,
  });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(5000, 32, 16), m);
  dome.renderOrder = -1;
  return dome;
}

function windowTexture(seed, warm) {
  const c = document.createElement("canvas");
  c.width = 256; c.height = 512;
  const g = c.getContext("2d");
  g.fillStyle = "#000";
  g.fillRect(0, 0, 256, 512);
  const rand = rng(seed);
  for (let y = 12; y < 512; y += 22) for (let x = 10; x < 256; x += 18) {
    if (rand() < 0.52) {
      g.fillStyle = rand() < (warm ? 0.8 : 0.35) ? `rgba(255,${190 + rand() * 40 | 0},${120 + rand() * 60 | 0},${0.55 + rand() * 0.45})`
                                                 : `rgba(${170 + rand() * 40 | 0},${200 + rand() * 30 | 0},255,${0.4 + rand() * 0.4})`;
      g.fillRect(x, y, 10, 12);
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

const buildingMats = [1, 2, 3, 4].map(i => new THREE.MeshStandardMaterial({
  color: "#0e1117", roughness: 0.7, metalness: 0.2, emissive: "#ffffff", emissiveIntensity: 1.35,
  emissiveMap: windowTexture(i * 97, i % 2 === 0)}));

function building(x, z, w, d, h, variant) {
  const geo = new THREE.BoxGeometry(w, h, d);
  // scale UVs so windows keep their size whatever the building's size
  const uv = geo.attributes.uv, n = geo.attributes.normal;
  for (let i = 0; i < uv.count; i++) {
    const side = Math.abs(n.getX(i)) > 0.5 ? d : w;
    if (Math.abs(n.getY(i)) > 0.5) { uv.setXY(i, 0, 0); continue; }
    uv.setXY(i, uv.getX(i) * side / 14, uv.getY(i) * h / 28);
  }
  const b = new THREE.Mesh(geo, buildingMats[variant % buildingMats.length]);
  b.position.set(x, h / 2, z);
  b.castShadow = true;
  b.receiveShadow = true;
  return b;
}

/* ------------------------------------------------------------------ campus map pieces */
function beam(color, height, radius, opacity) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, 1, 32, 1, true),
    new THREE.MeshBasicMaterial({color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide}));
  m.scale.y = height;
  m.position.y = height / 2;
  return m;
}

function label(html, cls) {
  const div = document.createElement("div");
  div.className = "label3d " + (cls || "");
  div.innerHTML = html;
  return new CSS2DObject(div);
}

const routeVert = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`;
const routeFrag = `uniform float uTime; uniform float uProgress; uniform vec3 uColor; uniform float uSolid; varying vec2 vUv;
  void main(){
    if (vUv.x > uProgress) discard;
    float dash = smoothstep(0.0, 0.45, fract(vUv.x * 16.0 - uTime * 0.9));
    float a = mix(0.25 + 0.75 * dash, 1.0, uSolid);
    float head = smoothstep(uProgress - 0.04, uProgress, vUv.x) * 1.5;
    gl_FragColor = vec4(uColor * (1.0 + head), a);
  }`;

/* ------------------------------------------------------------------ public */
export function init(container, opts = {}) {
  reduced = !!opts.reduced;
  renderer = new THREE.WebGLRenderer({antialias: true, powerPreference: "high-performance"});
  const small = window.innerWidth < 860;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, small ? 1.5 : 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.3;
  renderer.shadowMap.enabled = !small;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  labels = new CSS2DRenderer();
  labels.setSize(window.innerWidth, window.innerHeight);
  labels.domElement.className = "labels3d";
  container.appendChild(labels.domElement);

  scene = new THREE.Scene();
  scene.background = NIGHT;
  scene.fog = new THREE.Fog("#0b1019", 40, 140);
  camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.5, 6000);

  scene.add(new THREE.HemisphereLight("#4a5f8f", "#0a0b0e", 0.8));
  const moon = new THREE.DirectionalLight("#a9bcff", 1.25);
  moon.position.set(-40, 70, 30);
  moon.castShadow = true;
  moon.shadow.mapSize.set(2048, 2048);
  Object.assign(moon.shadow.camera, {left: -45, right: 45, top: 45, bottom: -45, near: 10, far: 200});
  moon.shadow.bias = -0.0004;
  scene.add(moon);

  scene.add(skyDome());
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(8000, 8000),
    new THREE.MeshStandardMaterial({color: "#0b0d11", roughness: 0.62, metalness: 0.1}));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);
  const grid = new THREE.GridHelper(4000, 200, "#1b2130", "#121722");
  grid.material.transparent = true;
  grid.material.opacity = 0.0;
  grid.position.y = 0.02;
  scene.add(grid);
  world.grid = grid;
  world.glowTex = glowTexture();

  composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.7, 0.5, 0.86));
  composer.addPass(new OutputPass());

  clock = new THREE.Clock();
  window.addEventListener("resize", onResize);
  renderer.setAnimationLoop(frame);
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
  labels.setSize(window.innerWidth, window.innerHeight);
}

// Place every lot and destination from /api/map. The hero lot sits at the origin.
export function setCampus(mapData, heroId, capacities) {
  const pts = [...mapData.lots, ...mapData.destinations];
  const lat0 = pts.reduce((a, p) => a + p.lat, 0) / pts.length;
  const hero = mapData.lots.find(l => l.pool_id === heroId) || mapData.lots[0];
  const toXZ = p => ({x: (p.lon - hero.lon) * 111320 * Math.cos(lat0 * Math.PI / 180) * 0.24,
                      z: -(p.lat - hero.lat) * 110540 * 0.24});
  mapData.lots.forEach((l, i) => {
    const cap = capacities[l.pool_id] || 20;
    const isHero = l.pool_id === hero.pool_id;
    const built = buildLot(cap, isHero ? cap - 1 : Math.round(cap * (0.45 + 0.35 * ((i * 37) % 10) / 10)), 11 + i * 7, isHero);
    const p = toXZ(l);
    built.group.position.set(p.x, 0, p.z);
    scene.add(built.group);
    const halo = new THREE.Mesh(new THREE.PlaneGeometry(built.width * 2.4, built.depth * 2.6),
      new THREE.MeshBasicMaterial({map: world.glowTex, color: AMBER, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false}));
    halo.rotation.x = -Math.PI / 2;
    halo.position.set(p.x, 0.04, p.z);
    scene.add(halo);
    const pillar = beam(AMBER, 1, 2.4, 0);
    pillar.position.x = p.x; pillar.position.z = p.z;
    scene.add(pillar);
    const tag = label(`<b>${l.name}</b>`, "lot");
    tag.position.set(p.x, 0, p.z);
    tag.element.style.opacity = 0;
    scene.add(tag);
    world.lots[l.pool_id] = {...built, x: p.x, z: p.z, pillar, halo, tag, name: l.name, height: 0};
    if (isHero) {
      const empty = built.stalls.find(s => !s.occupied);
      world.hero = buildHeroStall(empty, world.glowTex);
      world.hero.group.position.x += p.x;
      world.hero.group.position.z += p.z;
      scene.add(world.hero.group);
    }
  });
  mapData.destinations.forEach(d => {
    const p = toXZ(d);
    const g = new THREE.Group();
    g.position.set(p.x, 0, p.z);
    const b = beam("#dfe8ff", 70, 0.55, 0.0);
    g.add(b);
    const ring = new THREE.Mesh(new THREE.RingGeometry(3.2, 4.2, 48),
      new THREE.MeshBasicMaterial({color: "#ffffff", transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false}));
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.05;
    g.add(ring);
    const tag = label(d.name, "dest");
    tag.position.set(0, 4, 0);
    tag.element.style.opacity = 0;
    g.add(tag);
    scene.add(g);
    scene.add(building(p.x, p.z - 14, 30, 18, 22, 0));
    world.dests[d.name] = {x: p.x, z: p.z, beam: b, ring, tag};
  });
  // the rest of campus: blocks of lit buildings that keep clear of lots and destinations
  const rand = rng(2026);
  const keep = [...Object.values(world.lots).map(l => ({x: l.x, z: l.z, r: l.group.children.some(c => c.isPointLight) ? 85 : 46})),
                ...Object.values(world.dests).map(d => ({x: d.x, z: d.z, r: 34}))];
  let placed = 0;
  for (let tries = 0; tries < 900 && placed < 30; tries++) {
    const x = (rand() - 0.5) * 700 - 90, z = (rand() - 0.5) * 600 + 40;
    const w = 14 + rand() * 26, d = 12 + rand() * 22, h = 7 + rand() * 18;
    if (keep.some(k => Math.hypot(k.x - x, k.z - z) < k.r + Math.max(w, d) / 2)) continue;
    scene.add(building(x, z, w, d, h, placed));
    keep.push({x, z, r: Math.max(w, d) / 2 + 6});
    placed++;
  }
}

export const cameraState = cam;
export const story = state;

// Campus mode: the lots, beams and labels fade in; the opening details stay.
const NIGHT_BLOCK = new THREE.Color("#0e1117"), MODEL_BLOCK = new THREE.Color("#323a4a");
export function setCampusMode(t) {
  world.campusT = t;
  // at street level the buildings are lit windows; from above they settle into a quiet model
  buildingMats.forEach(m => { m.emissiveIntensity = 1.35 - 1.25 * t; m.color.copy(NIGHT_BLOCK).lerp(MODEL_BLOCK, t); });
  Object.values(world.lots).forEach(l => { l.halo.material.opacity = (l.allowed ? 0.55 : 0.22) * t; });
  world.grid.material.opacity = 0.55 * t;
  Object.values(world.dests).forEach(d => {
    d.beam.material.opacity = d.chosen ? 0.32 * t : 0.12 * t;
    d.ring.material.opacity = (d.chosen ? 0.9 : 0.35) * t;
    d.tag.element.style.opacity = t;
  });
  Object.values(world.lots).forEach(l => { l.tag.element.style.opacity = t; });
}

export function chooseDestination(name) {
  Object.entries(world.dests).forEach(([n, d]) => {
    d.chosen = n === name;
    d.beam.scale.y = d.chosen ? 90 : 50;
    d.beam.position.y = d.beam.scale.y / 2;
    d.tag.element.classList.toggle("chosen", d.chosen);
  });
  setCampusMode(world.campusT || 0);
}

export function destinationPoint(name) {
  const d = world.dests[name];
  return d ? {x: d.x, z: d.z} : null;
}

export function heroStallPoint() {
  return world.hero ? {x: world.hero.group.position.x, z: world.hero.group.position.z} : null;
}

export function lotPoint(id) {
  const l = world.lots[id];
  return l ? {x: l.x, z: l.z} : null;
}

// After a search: allowed lots get a beam whose height is the share of places free.
export function showOptions(options) {
  const allowed = {};
  options.forEach((o, i) => { allowed[o.lot_id] = {...o, rank: i + 1}; });
  Object.entries(world.lots).forEach(([id, l]) => {
    const o = allowed[id];
    l.allowed = !!o;
    l.halo.material.opacity = (o ? 0.55 : 0.12) * (world.campusT || 1);
    l.targetHeight = o ? 12 + 50 * (o.remaining / o.capacity) : 0;
    l.tag.element.className = "label3d lot " + (o ? "allowed" : "off");
    l.tag.element.innerHTML = o
      ? `<span class="n">${o.rank}</span><b>${l.name}</b><small>${o.walk_minutes === null ? "walk unknown" : o.walk_minutes + " min walk"} · ${o.remaining} free</small>`
      : `<b>${l.name}</b><small>not for this permit</small>`;
  });
  clearRoute();
}

function clearRoute() {
  if (world.route) { scene.remove(world.route); world.route.geometry.dispose(); world.route = null; }
}

// A light trail from the lot to the destination, arched like a flight path.
export function drawRoute(lotId, destName, solid) {
  clearRoute();
  const l = world.lots[lotId], d = world.dests[destName];
  if (!l || !d) return null;
  const a = new THREE.Vector3(l.x, 1.2, l.z), b = new THREE.Vector3(d.x, 1.2, d.z);
  const dist = a.distanceTo(b);
  const c = a.clone().lerp(b, 0.5); c.y = Math.max(14, dist * 0.32);
  const curve = new THREE.QuadraticBezierCurve3(a, c, b);
  const matR = new THREE.ShaderMaterial({
    uniforms: {uTime: {value: 0}, uProgress: {value: reduced ? 1 : 0}, uColor: {value: AMBER.clone()}, uSolid: {value: solid ? 1 : 0}},
    vertexShader: routeVert, fragmentShader: routeFrag,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
  });
  world.route = new THREE.Mesh(new THREE.TubeGeometry(curve, 160, solid ? 1.1 : 0.75, 10, false), matR);
  world.routeMat = matR;
  scene.add(world.route);
  Object.entries(world.lots).forEach(([id, x]) => x.tag.element.classList.toggle("active", id === lotId));
  return matR.uniforms.uProgress;
}

export function holdLot(lotId) {
  const l = world.lots[lotId];
  if (!l) return;
  if (world.held) scene.remove(world.held);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({map: pTexture(), transparent: true}));
  s.scale.set(9, 9, 1);
  s.position.set(l.x, l.targetHeight + 10, l.z);
  s.userData.lot = lotId;
  scene.add(s);
  world.held = s;
}

export function reset() {
  clearRoute();
  if (world.held) { scene.remove(world.held); world.held = null; }
  Object.values(world.lots).forEach(l => { l.targetHeight = 0; l.tag.element.className = "label3d lot"; l.tag.element.innerHTML = `<b>${l.name}</b>`; });
}

/* ------------------------------------------------------------------ loop */
const target = new THREE.Vector3();
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05), t = clock.elapsedTime;
  const sway = reduced ? 0 : state.idle;
  camera.position.set(cam.px + Math.sin(t * 0.18) * 3.5 * sway, cam.py + Math.sin(t * 0.25) * 0.6 * sway, cam.pz + Math.cos(t * 0.18) * 2.5 * sway);
  target.set(cam.tx, cam.ty, cam.tz);
  camera.lookAt(target);
  const dist = camera.position.distanceTo(target);
  scene.fog.near = dist * 1.2;
  scene.fog.far = dist * 7;

  if (world.hero) {
    world.hero.amberLine.emissiveIntensity = 3.2 * state.stallGlow;
    world.hero.glow.material.opacity = 0.55 * state.stallGlow * (0.85 + 0.15 * Math.sin(t * 2.2));
    world.hero.sprite.material.opacity = state.stallGlow;
    world.hero.sprite.position.y = 3.1 + Math.sin(t * 1.6) * 0.18;
  }
  Object.values(world.lots).forEach(l => {
    l.height += ((l.targetHeight || 0) - l.height) * Math.min(1, dt * 3.2);
    const h = Math.max(0.001, l.height);
    l.pillar.scale.y = h;
    l.pillar.position.y = h / 2;
    l.pillar.material.opacity = l.allowed ? 0.42 : 0;
    l.tag.position.y = h + 6;
  });
  if (world.routeMat) world.routeMat.uniforms.uTime.value = t;
  if (world.held) {
    const l = world.lots[world.held.userData.lot];
    world.held.position.y = (l ? l.height : 0) + 10 + (reduced ? 0 : Math.sin(t * 1.5) * 0.8);
  }
  composer.render();
  labels.render(scene, camera);
}
