const CACHE_NAME = 'htgen-v1';
const STATIC_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/localstorage.js',
    '/static/js/sw-register.js',
    '/static/icons/icon-96x96.png',
    '/static/icons/icon-144x144.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

// Install Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Pre-caching offline assets');
                return cache.addAll(STATIC_CACHE);
            })
    );
    self.skipWaiting();
});

// Activate Service Worker
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => cacheName !== CACHE_NAME)
                    .map(cacheName => {
                        console.log('[Service Worker] Removing old cache:', cacheName);
                        return caches.delete(cacheName);
                    })
            );
        })
    );
    return self.clients.claim();
});

// Fetch Event Handler
self.addEventListener('fetch', event => {
    console.log('[Service Worker] Fetching:', event.request.url);
    // Skip cross-origin requests
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }

    // Handle XHR requests for hashtags
    if (event.request.url.includes('/hashtags')) {
        return event.respondWith(
             fetch(event.request)
            .then(response => response)
            .catch(async error => {
                // We should never reach this point
                // since when offline we disable the generate button
                console.error('/hashtags request failed:', error);
                throw error;
            })

        );
    }


    // Handle static assets with stale-while-revalidate strategy
    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                const fetchPromise = fetch(event.request)
                    .then(async networkResponse => {
                        // Don't process non-successful responses
                        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                            return networkResponse;
                        }

                        // If we have a cached response, compare it with the network response
                        if (cachedResponse) {
                            const cachedText = await cachedResponse.clone().text();
                            const networkText = await networkResponse.clone().text();

                            // Only update cache if the content has changed
                            if (cachedText !== networkText) {
                                const cache = await caches.open(CACHE_NAME);
                                await cache.put(event.request, networkResponse.clone());
                                console.log('[Service Worker] Updated cached response for:', event.request.url);
                            }
                        } else {
                            // No cached response exists, cache the network response
                            const cache = await caches.open(CACHE_NAME);
                            await cache.put(event.request, networkResponse.clone());
                            console.log('[Service Worker] Cached new response for:', event.request.url);
                        }

                        return networkResponse;
                    })
                    .catch(() => {
                        // Return offline page if available
                        if (event.request.mode === 'navigate') {
                            return caches.match('/');
                        }
                        return null;
                    });

                // Return cached response immediately if available, otherwise wait for network
                return cachedResponse || fetchPromise;
            })
    );
});