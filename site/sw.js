/* OpenDict service worker — offline-first for dictionary data */
const CACHE = "opendict-v2";
const SHELL = ["./", "./index.html", "./css/style.css", "./js/app.js",
               "./js/data.js", "./js/i18n.js", "./manifest.json", "./favicon.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(e.request);
    // dictionary data: cache-first (immutable per build)
    if (url.pathname.includes("/data/")) {
      if (cached) return cached;
      try {
        const res = await fetch(e.request);
        if (res.ok) cache.put(e.request, res.clone());
        return res;
      } catch { return cached || Response.error(); }
    }
    // app shell: network-first, fall back to cache
    try {
      const res = await fetch(e.request);
      if (res.ok) cache.put(e.request, res.clone());
      return res;
    } catch {
      return cached || cache.match("./index.html");
    }
  })());
});
