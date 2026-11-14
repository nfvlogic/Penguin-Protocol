// Offline support: cache the page, the game and the pinned Pyodide files the first time they are loaded.
const CACHE = "penguin-__VERSION__";
const CORE = ["./", "index.html", "style.css", "app.js", "penguin.zip", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k.startsWith("penguin-") && k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const ours = url.origin === location.origin;
  const pyodide = url.hostname === "cdn.jsdelivr.net" && url.pathname.startsWith("/pyodide/");
  if (!ours && !pyodide) return;
  e.respondWith(caches.open(CACHE).then(async (cache) => {
    const hit = await cache.match(e.request, { ignoreSearch: true });
    if (hit) return hit;
    const res = await fetch(e.request);
    if (res.ok || res.type === "opaque") cache.put(e.request, res.clone());
    return res;
  }));
});
