const CACHE_NAME = 'mushaf-cache-v29';
const APP_SHELL = ['./', './index.html', './manifest.json'];
// Recitation audio downloaded via the "⬇" download manager in the app is
// stored in this separate cache (page JS writes to it directly through the
// Cache API - see downloadAudioUrl() in work.html). This worker's only job
// for it is to serve a matching request from that cache first, so a
// downloaded ayah/surah plays back offline exactly like it would online.
const AUDIO_CACHE_NAME = 'mushaf-audio-v1';
const AUDIO_HOSTS = ['everyayah.com', 'mp3quran.net', 'cdn.islamic.network'];
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME && k !== AUDIO_CACHE_NAME).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  let hostname = '';
  try { hostname = new URL(event.request.url).hostname; } catch (e) { /* ignore */ }
  const isAudio = AUDIO_HOSTS.some((h) => hostname === h || hostname.endsWith('.' + h));
  if (isAudio) {
    event.respondWith(
      caches.open(AUDIO_CACHE_NAME).then((cache) =>
        cache.match(event.request).then((cached) => cached || fetch(event.request, { mode: 'no-cors' }).catch(() => undefined))
      )
    );
    return;
  }
  // Network-first with a time limit: an update published to the site still
  // shows up on the very next open whenever the connection is reasonably
  // quick, but on a slow connection (3G) the app no longer sits waiting for
  // the ~5 MB page - after NETWORK_WAIT_MS the saved copy is shown at once,
  // while the download carries on in the background and refreshes the saved
  // copy for the next open. Offline, the saved copy is used straight away.
  const NETWORK_WAIT_MS = 1800;
  const sameOrigin = new URL(event.request.url).origin === self.location.origin;
  const network = fetch(event.request, sameOrigin ? { cache: 'no-cache' } : undefined).then((resp) => {
    if (resp && resp.ok) {
      const clone = resp.clone();
      return caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone)).then(() => resp, () => resp);
    }
    return resp;
  });
  event.waitUntil(network.catch(() => {}));
  const cachedCopy = () => caches.match(event.request).then((cached) => cached || (event.request.mode === 'navigate' ? caches.match('./index.html') : undefined));
  event.respondWith(new Promise((resolve) => {
    let done = false;
    const finish = (r) => { if (!done && r) { done = true; resolve(r); } };
    network.then(finish, () => cachedCopy().then((c) => { if (!done) { done = true; resolve(c || Response.error()); } }));
    setTimeout(() => { if (!done) cachedCopy().then(finish); }, NETWORK_WAIT_MS);
  }));
});
