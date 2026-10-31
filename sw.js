const CACHE_NAME = 'mushaf-cache-v91';
// Book files (books/<id>/NNN.json - تفسير البرهان etc.), one per surah: served
// cache-first from their own cache, which app updates never clear.
const BOOKS_CACHE_NAME = 'mushaf-books-v1';
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
  // Old app copies are deleted only once this version's own copy of the page
  // is fully saved. On a slow or broken connection the install step can fail
  // to save it; deleting the previous copy then would leave nothing to open
  // offline or on 3G. The old copy is kept (and still served) until a later
  // visit manages to save the new one.
  event.waitUntil(caches.open(CACHE_NAME).then((c) => c.match('./index.html')).then((have) => {
    if (!have) return;
    return caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME && k !== AUDIO_CACHE_NAME && k !== BOOKS_CACHE_NAME).map((k) => caches.delete(k))));
  }));
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
  if (/\/books\/[^/]+\/\d+\.json$/.test(new URL(event.request.url).pathname)) {
    event.respondWith(
      caches.open(BOOKS_CACHE_NAME).then((cache) =>
        cache.match(event.request.url).then((cached) => cached || fetch(event.request).then((resp) => {
          if (resp && resp.ok) cache.put(event.request.url, resp.clone());
          return resp;
        }))
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
  const isPage = event.request.mode === 'navigate' || /\/(index\.html)?$/.test(new URL(event.request.url).pathname);
  let servedSaved = false; // the saved copy was shown because the network was slow
  const network = fetch(event.request, sameOrigin ? { cache: 'no-cache' } : undefined).then((resp) => {
    if (resp && resp.ok) {
      const clone = resp.clone();
      return caches.open(CACHE_NAME).then((cache) => cache.match(event.request).then((old) => {
        // The page on screen came from the saved copy and the site now has a
        // different version: once it's saved, tell the page so it can offer
        // to switch to it right away (instead of only on the next opening).
        const changed = !old || (old.headers.get('etag') || old.headers.get('last-modified') || '') !== (resp.headers.get('etag') || resp.headers.get('last-modified') || '');
        return cache.put(event.request, clone).then(() => {
          if (isPage && servedSaved && changed) {
            self.clients.matchAll({ type: 'window' }).then((cs) => cs.forEach((c) => c.postMessage({ type: 'mushaf-update-ready' })));
          }
        });
      })).then(() => resp, () => resp);
    }
    return resp;
  });
  event.waitUntil(network.catch(() => {}));
  const cachedCopy = () => caches.match(event.request).then((cached) => cached || (event.request.mode === 'navigate' ? caches.match('./index.html') : undefined));
  event.respondWith(new Promise((resolve) => {
    let done = false;
    const finish = (r) => { if (!done && r) { done = true; resolve(r); } };
    network.then(finish, () => cachedCopy().then((c) => { if (!done) { done = true; resolve(c || Response.error()); } }));
    setTimeout(() => { if (!done) cachedCopy().then((c) => { if (!done && c) servedSaved = true; finish(c); }); }, NETWORK_WAIT_MS);
  }));
});
