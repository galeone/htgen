const CACHE_NAME = 'htgen-v1';
const STATIC_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/css/style.css',
    '/static/js/localstorage.js',
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

    // Handle API requests
    if (event.request.url.includes('/hashtags')) {
        return event.respondWith(handleApiRequest(event));
    }

    // Handle static assets
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }

                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    })
                    .catch(() => {
                        // Return offline page if available
                        if (event.request.mode === 'navigate') {
                            return caches.match('/');
                        }
                        return null;
                    });
            })
    );
});

// Handle API Requests
function handleApiRequest(event) {
    // we need to clone the request because fetch consumes it
    // and in the catch we can't call clone
    let request = event.request.clone();
    return fetch(event.request)
        .then(response => response)
        .catch(error => {
            // If offline, store the request for later
            // navigator.onLine is not reliable, so we check if the fetch failed
            if (!navigator.onLine || error.message.toLowerCase().includes('failed to fetch')) {
                return saveRequestForLater(request)
                    .then(() => {
                        let response = new Response(JSON.stringify({
                            error: 'You are offline. Your request will be processed when you are back online.'
                        }), {
                            headers: { 'Content-Type': 'application/json' }
                        });
                        return response;
                    });
            }
            throw error;
        });
}

navigator.connection.onchange = async (event) => {
  if (navigator.onLine) {
    await processPendingRequest();
  }
};


// Store pending requests in IndexedDB
const dbName = 'HTGenOfflineDB';
const storeName = 'pendingRequests';

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(dbName, 1);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(storeName)) {
                db.createObjectStore(storeName, { autoIncrement: true });
            }
        };
    });
}

async function saveRequestForLater(request) {
    const db = await openDB();
    const serializedRequest = await serializeRequest(request);
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    return store.put(serializedRequest);
}

// Process pending request - only the last one
async function processPendingRequest() {
    const db = await openDB();
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    const requests = await store.getAll(); // should be 1
    requests.onsuccess = function() {
        const processPromises = requests.result.map(async (serializedRequest) => {
            try {
                const request = deserializeRequest(serializedRequest);
                await fetch(request);
                // Remove processed request
                const db = await openDB();
                const tx = db.transaction(storeName, 'readwrite');
                const store = tx.objectStore(storeName);
                await store.delete(serializedRequest.id);
            } catch (error) {
                console.error('Failed to process pending request:', error);
            }
        });

        return Promise.all(processPromises);
    };
}

// Helper functions to serialize/deserialize requests
async function serializeRequest(request) {
    const serialized = {
        url: request.url,
        method: request.method,
        headers: Array.from(request.headers.entries()),
        mode: request.mode,
        credentials: request.credentials,
        cache: request.cache,
        redirect: request.redirect,
        referrer: request.referrer
    };

    if (request.method !== 'GET') {
        serialized.body = await request.clone().text();
    }

    return serialized;
}

function deserializeRequest(serialized) {
    return new Request(serialized.url, {
        method: serialized.method,
        headers: serialized.headers,
        mode: serialized.mode,
        credentials: serialized.credentials,
        cache: serialized.cache,
        redirect: serialized.redirect,
        referrer: serialized.referrer,
        body: serialized.body
    });
}
