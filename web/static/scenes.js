// The home page's scenes: a weather effect and the photographs it can play over. Loaded in <head> so the
// scene is chosen, and its photo starts loading, before the page draws. Commons photos are real, freely
// licensed and credited on the page; the autumn photo is the project's own.
(function () {
  const C = "https://commons.wikimedia.org/wiki/File:";
  const scenes = [
    {id: "autumn", name: "Autumn leaves", effect: "leaves", photos: [
      {local: "hero-autumn", w: 1672, slot: true, scrim2: 0}]},
    {id: "sakura", name: "Cherry blossom", effect: "petals", photos: [
      {path: "d/db/The_Cornell_Botanic_Gardens.jpg", w: 4208, place: "Cornell Botanic Gardens", by: "Bimala Rai Colavito",
       license: "CC BY-SA 4.0", page: C + "The_Cornell_Botanic_Gardens.jpg", scrim2: .45},
      {path: "a/a9/Cornell_University_-_Beebe_Lake_and_Triphammer_Falls.jpg", w: 5880, place: "Beebe Lake and Triphammer Falls",
       by: "P. Hughes", license: "CC BY 4.0", page: C + "Cornell_University_-_Beebe_Lake_and_Triphammer_Falls.jpg", scrim2: .35}]},
    {id: "snow", name: "Snow", effect: "snow", photos: [
      {path: "d/d8/Ithaca_Falls_in_winter_3_%2844330311385%29.jpg", w: 5184, place: "Ithaca Falls in winter",
       by: "VillageHero", license: "CC BY-SA 2.0", page: C + "Ithaca_Falls_in_winter_3_(44330311385).jpg", scrim2: .7},
      {path: "6/64/Buttermilk_falls_in_winter_%28Ithaca%29_%2844518698994%29.jpg", w: 5184, place: "Buttermilk Falls in winter",
       by: "VillageHero", license: "CC BY-SA 2.0", page: C + "Buttermilk_falls_in_winter_(Ithaca)_(44518698994).jpg", scrim2: .7}]},
    {id: "rain", name: "Rain", effect: "rain", photos: [
      {path: "c/c8/Ithaca_Falls_01.jpg", w: 4288, place: "Ithaca Falls", by: "LBM1948", license: "CC BY-SA 4.0",
       page: C + "Ithaca_Falls_01.jpg", scrim2: .35},
      {path: "c/c1/Ithaca_-_Cascadilla_Gorge_Trail.jpg", w: 6048, place: "Cascadilla Gorge Trail", by: "P. Hughes",
       license: "CC BY 4.0", page: C + "Ithaca_-_Cascadilla_Gorge_Trail.jpg", scrim2: .25}]},
    {id: "sunny", name: "Sunny", effect: "sun", photos: [
      {path: "4/45/Ithaca%2C_NY_01.jpg", w: 4288, place: "Cayuga Lake from the Johnson Museum", by: "LBM1948",
       license: "CC BY-SA 4.0", page: C + "Ithaca,_NY_01.jpg", scrim2: .5, sun: [82, 6]},
      {path: "0/05/Lower_Taughannock_Falls_April_2024.jpg", w: 4032, place: "Lower Taughannock Falls", by: "Awinch1001",
       license: "CC0", page: C + "Lower_Taughannock_Falls_April_2024.jpg", scrim2: .55, sun: [18, 4]}]},
    {id: "dusk", name: "Dusk", effect: "fireflies", photos: [
      {path: "2/21/Sunset_on_the_lake_-_panoramio.jpg", w: 3200, place: "Sunset on Cayuga Lake, Stewart Park", by: "Arseny Khakhalin",
       license: "CC BY 3.0", page: C + "Sunset_on_the_lake_-_panoramio.jpg", scrim2: .25},
      {path: "e/e2/Sunrise_at_Beebe_Lake_%284026352842%29.jpg", w: 4272, place: "Sunrise at Beebe Lake", by: "Yisong Yue",
       license: "CC BY-SA 2.0", page: C + "Sunrise_at_Beebe_Lake_(4026352842).jpg", scrim2: .3}]},
  ];

  // Commons serves these standard widths; 1920 covers a laptop screen without sending a 4K file
  const commons = (p, w) => `https://upload.wikimedia.org/wikipedia/commons/thumb/${p.path}/${w}px-${p.path.split("/").pop()}`;
  const srcset = p => [1280, 1920].filter(w => w <= p.w).map(w => `${commons(p, w)} ${w}w`).join(", ");

  let mode = "random";
  try { mode = localStorage.getItem("cp.scene") || "random"; } catch (e) {}
  const pick = list => list[Math.floor(Math.random() * list.length)];
  const scene = scenes.find(s => s.id === mode) || pick(scenes);
  const photo = pick(scene.photos);
  document.documentElement.dataset.scene = scene.id;

  const link = document.createElement("link");
  link.rel = "preload";
  link.as = "image";
  link.fetchPriority = "high";
  if (photo.local) { link.href = `/static/media/${photo.local}.avif`; link.type = "image/avif"; }
  else { link.href = commons(photo, 1280); link.imageSrcset = srcset(photo); link.imageSizes = "100vw"; }
  document.head.appendChild(link);

  window.CP_SCENES = {scenes, scene, photo, mode, srcset, commons};
})();
