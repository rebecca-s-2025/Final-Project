const CACHE_NAME = 'assets-cache-v1';

// Optionally, pre-cache specific URLs (you can add more if needed)
const urlsToPrecache = [
  // Example: Pre-cache your home page, essential CSS/JS, etc.
  // '/',
];

self.addEventListener('install', event => {
  console.log('[ServiceWorker] Install');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[ServiceWorker] Pre-caching assets');
        return cache.addAll(urlsToPrecache);
      })
  );
  self.skipWaiting();
});

self.addEventListener('fetch', event => {
  const requestUrl = new URL(event.request.url);

  // Cache only requests that start with /static/ or /media/
  if (requestUrl.pathname.startsWith('/static/') || requestUrl.pathname.startsWith('/media/')) {
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        if (cachedResponse) {
          console.log('[ServiceWorker] Serving from cache:', event.request.url);
          return cachedResponse;
        }
        return fetch(event.request).then(networkResponse => {
          // Only cache valid responses
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            return networkResponse;
          }
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });
          return networkResponse;
        });
      })
    );
  } else {
    // For all other requests, use network-first strategy
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  }
});

self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activate');
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log('[ServiceWorker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});