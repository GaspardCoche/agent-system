// Service worker minimal — cache du shell de l'app (offline shell).
// Les appels API GitHub ne sont JAMAIS mis en cache (toujours réseau).
const CACHE = 'pocket-v2';
const SHELL = ['./', './index.html', './app.js', './style.css', './icon.svg', './manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Ne jamais intercepter l'API GitHub
  if (url.hostname === 'api.github.com') return;
  // Shell : cache-first ; reste : réseau avec repli cache
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request).catch(() => caches.match('./index.html')))
  );
});
