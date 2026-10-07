const CACHE_NAME = 'mushaf-cache-v23';
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
  // Network-first: an update published to the site shows up on the very next
  // open (the old "answer from cache, refresh in the background" scheme only
  // showed it one open later, and could keep serving the browser's own
  // 10-minute HTTP cache copy). Offline, the saved copy is used instead.
  const sameOrigin = new URL(event.request.url).origin === self.location.origin;
  event.respondWith(
    fetch(event.request, sameOrigin ? { cache: 'no-cache' } : undefined).then((resp) => {
      if (resp && resp.ok) { const clone = resp.clone(); caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone)); }
      return resp;
    }).catch(() => caches.match(event.request).then((cached) => cached || (event.request.mode === 'navigate' ? caches.match('./index.html') : undefined)))
  );
});
