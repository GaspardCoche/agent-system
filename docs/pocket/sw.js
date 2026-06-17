// Service worker — réseau d'abord (évite le cache figé), repli hors-ligne + push.
const CACHE = 'pocket-v10';
const SHELL = ['./', './index.html', './app.js', './style.css', './icon.svg', './manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

// Réseau d'abord : on sert toujours la dernière version si en ligne, cache en secours hors-ligne.
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.hostname === 'api.github.com') return; // jamais intercepté
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match(e.request).then((c) => c || caches.match('./index.html')))
  );
});

// Push : notification de fin de tâche.
self.addEventListener('push', (e) => {
  let data = {};
  try { data = e.data.json(); } catch { data = { title: 'Claude Pocket', body: e.data ? e.data.text() : 'Tâche terminée' }; }
  e.waitUntil(self.registration.showNotification(data.title || 'Claude Pocket', {
    body: data.body || 'Une tâche est terminée.', icon: './icon.svg', badge: './icon.svg', tag: data.tag || 'pocket', data: { url: data.url || './' },
  }));
});
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || './';
  e.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    for (const c of list) { if ('focus' in c) return c.focus(); }
    if (clients.openWindow) return clients.openWindow(url);
  }));
});
