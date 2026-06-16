// Service worker — shell offline + notifications push.
const CACHE = 'pocket-v3';
const SHELL = ['./', './index.html', './app.js', './style.css', './icon.svg', './manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.hostname === 'api.github.com') return; // jamais en cache
  e.respondWith(caches.match(e.request).then((c) => c || fetch(e.request).catch(() => caches.match('./index.html'))));
});

// Push : affiche la notification envoyée par le workflow à la fin d'une tâche.
self.addEventListener('push', (e) => {
  let data = {};
  try { data = e.data.json(); } catch { data = { title: 'Claude Pocket', body: e.data ? e.data.text() : 'Tâche terminée' }; }
  e.waitUntil(self.registration.showNotification(data.title || 'Claude Pocket', {
    body: data.body || 'Une tâche est terminée.',
    icon: './icon.svg', badge: './icon.svg', tag: data.tag || 'pocket',
    data: { url: data.url || './' },
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
