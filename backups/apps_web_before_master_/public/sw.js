// ConcordBroker Service Worker - Advanced Performance & Caching v1.2.0
const CACHE_NAME = 'concordbroker-v1.2.0';
const STATIC_CACHE = 'concordbroker-static-v1.2.0';
const API_CACHE = 'concordbroker-api-v1.2.0';
const IMAGE_CACHE = 'concordbroker-images-v1.2.0';
const RUNTIME_CACHE = 'concordbroker-runtime-v1.2.0';

// Critical static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/js/main.js',
  '/static/css/main.css',
  // Critical fonts for performance
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
];

// API endpoints with aggressive caching
const CACHEABLE_API_PATTERNS = [
  /\/api\/properties\/search/,
  /\/api\/properties\/suggestions/,
  /\/api\/properties\/autocomplete/,
  /\/api\/counties/,
  /\/api\/cities/,
  /\/api\/property-types/,
  /\/api\/dor-codes/,
];

// Network-first API patterns (user-specific data)
const NETWORK_FIRST_PATTERNS = [
  /\/api\/auth/,
  /\/api\/user/,
  /\/api\/favorites/,
  /\/api\/alerts/,
  /\/api\/tracking/,
];

// Enhanced Performance monitoring for 80%+ cache hit rate target
const performanceMetrics = {
  cacheHits: 0,
  cacheMisses: 0,
  networkRequests: 0,
  errors: 0,
  avgResponseTime: 0,
  totalResponses: 0,
  cacheHitRate: 0,
  warmCacheHits: 0,
  indexedDBHits: 0,
  lastPerformanceReport: Date.now()
};

// IndexedDB cache for large datasets
let dbCache;
const DB_NAME = 'ConcordBrokerCache';
const DB_VERSION = 1;
const STORE_NAME = 'propertyData';

// Initialize IndexedDB
async function initIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      dbCache = request.result;
      resolve(dbCache);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'url' });
        store.createIndex('timestamp', 'timestamp');
        store.createIndex('type', 'type');
      }
    };
  });
}

// Cache warming scheduler
const cacheWarmingSchedule = {
  lastWarming: 0,
  interval: 30 * 60 * 1000, // 30 minutes
  popularSearches: [
    'county=BROWARD&limit=20',
    'county=MIAMI-DADE&limit=20',
    'county=PALM%20BEACH&limit=20',
    'min_value=100000&max_value=500000&limit=20',
    'property_type=RESIDENTIAL&limit=20',
    'city=Miami&limit=20',
    'city=Fort%20Lauderdale&limit=20'
  ]
};

// Install event - cache critical resources and initialize IndexedDB
self.addEventListener('install', (event) => {
  console.log('[SW v2.0.0] Installing enhanced service worker with comprehensive caching');

  event.waitUntil(
    Promise.all([
      // Initialize IndexedDB for large dataset caching
      initIndexedDB().catch(error => {
        console.log('[SW] IndexedDB initialization failed:', error);
      }),

      // Cache static assets
      caches.open(STATIC_CACHE).then((cache) => {
        console.log('[SW] Caching critical static assets');
        return cache.addAll(STATIC_ASSETS);
      }),

      // Enhanced pre-caching with multiple API endpoints
      caches.open(API_CACHE).then(async (cache) => {
        console.log('[SW] Pre-caching popular property searches across all APIs');

        const apiEndpoints = [
          'http://localhost:8000',
          'http://localhost:8002',
          'http://localhost:3005'
        ];

        const searchQueries = cacheWarmingSchedule.popularSearches;

        try {
          for (const endpoint of apiEndpoints) {
            for (const query of searchQueries) {
              try {
                const url = `${endpoint}/api/properties/search?${query}`;
                const response = await fetch(url, {
                  timeout: 5000,
                  headers: { 'Cache-Control': 'max-age=300' }
                });

                if (response.ok) {
                  await cache.put(url, response.clone());

                  // Also store in IndexedDB for large datasets
                  if (dbCache) {
                    const data = await response.json();
                    await storeInIndexedDB(url, data, 'search');
                  }
                }
              } catch (error) {
                console.log('[SW] Pre-cache failed for:', endpoint, query);
              }
            }
          }
        } catch (error) {
          console.log('[SW] Enhanced pre-caching failed:', error);
        }
      }),

      // Initialize performance monitoring
      initPerformanceMonitoring(),

      // Skip waiting to activate immediately
      self.skipWaiting()
    ])
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activate');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            // Delete old caches
            if (cacheName !== STATIC_CACHE && cacheName !== API_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        // Take control of all clients immediately
        return self.clients.claim();
      })
  );
});

// Advanced fetch handler with intelligent caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  const startTime = performance.now();

  // Skip non-GET requests and non-http protocols
  if (request.method !== 'GET' || !url.protocol.startsWith('http')) {
    return;
  }

  // Track network request
  performanceMetrics.networkRequests++;

  // Route to appropriate caching strategy
  if (isImage(url)) {
    event.respondWith(handleImageRequest(request, startTime));
  } else if (isApiRequest(url)) {
    if (isNetworkFirstApi(url)) {
      event.respondWith(handleNetworkFirstApi(request, startTime));
    } else if (isCacheableApi(url)) {
      event.respondWith(handleStaleWhileRevalidateApi(request, startTime));
    } else {
      event.respondWith(handleNetworkOnlyApi(request, startTime));
    }
  } else if (isStaticAsset(url)) {
    event.respondWith(handleCacheFirstStatic(request, startTime));
  } else if (request.mode === 'navigate') {
    event.respondWith(handleNavigation(request, startTime));
  } else {
    // Default: stale-while-revalidate for unknown requests
    event.respondWith(handleStaleWhileRevalidate(request, RUNTIME_CACHE, startTime));
  }
});

// Enhanced helper functions for request classification
function isApiRequest(url) {
  return url.pathname.startsWith('/api/') ||
         (url.hostname.includes('localhost') && (url.port === '8000' || url.port === '8002')) ||
         url.hostname.includes('api.');
}

function isNetworkFirstApi(url) {
  return NETWORK_FIRST_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isCacheableApi(url) {
  return CACHEABLE_API_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isStaticAsset(url) {
  return /\.(js|css|woff|woff2|ttf|eot)$/i.test(url.pathname) ||
         url.pathname.startsWith('/static/');
}

function isImage(url) {
  return /\.(png|jpg|jpeg|gif|svg|webp|ico|avif)$/i.test(url.pathname);
}

function trackResponseTime(startTime) {
  const responseTime = performance.now() - startTime;
  performanceMetrics.totalResponses++;
  performanceMetrics.avgResponseTime =
    ((performanceMetrics.avgResponseTime * (performanceMetrics.totalResponses - 1)) + responseTime) /
    performanceMetrics.totalResponses;
}

// Advanced caching handlers

// Cache-first strategy for static assets
async function handleCacheFirstStatic(request, startTime) {
  try {
    const cache = await caches.open(STATIC_CACHE);
    const cachedResponse = await cache.match(request);

    if (cachedResponse) {
      performanceMetrics.cacheHits++;
      trackResponseTime(startTime);

      // Update cache in background if resource is old
      if (isStale(cachedResponse, 24 * 60 * 60 * 1000)) { // 24 hours
        updateCacheInBackground(request, cache);
      }

      return cachedResponse;
    }

    // Not in cache, fetch from network
    performanceMetrics.cacheMisses++;
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }

    trackResponseTime(startTime);
    return networkResponse;
  } catch (error) {
    performanceMetrics.errors++;
    console.error('[SW] Cache-first static failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Image cache-first with compression hints
async function handleImageRequest(request, startTime) {
  try {
    const cache = await caches.open(IMAGE_CACHE);
    const cachedResponse = await cache.match(request);

    if (cachedResponse) {
      performanceMetrics.cacheHits++;
      trackResponseTime(startTime);
      return cachedResponse;
    }

    performanceMetrics.cacheMisses++;

    // Add image optimization headers
    const optimizedRequest = new Request(request, {
      headers: {
        ...request.headers,
        'Accept': 'image/webp,image/avif,image/*,*/*;q=0.8'
      }
    });

    const networkResponse = await fetch(optimizedRequest);

    if (networkResponse.ok) {
      // Only cache images under 5MB
      const contentLength = networkResponse.headers.get('content-length');
      if (!contentLength || parseInt(contentLength) < 5 * 1024 * 1024) {
        cache.put(request, networkResponse.clone());
      }
    }

    trackResponseTime(startTime);
    return networkResponse;
  } catch (error) {
    performanceMetrics.errors++;
    console.error('[SW] Image cache failed:', error);
    return new Response('Image unavailable', { status: 503 });
  }
}

// Network-first for user-specific APIs
async function handleNetworkFirstApi(request, startTime) {
  const cache = await caches.open(API_CACHE);

  try {
    const networkResponse = await fetch(request, { timeout: 5000 });

    if (networkResponse.ok) {
      // Cache successful responses briefly for offline fallback
      const headers = new Headers(networkResponse.headers);
      headers.set('sw-cached-at', new Date().toISOString());

      const responseWithMetadata = new Response(networkResponse.body, {
        status: networkResponse.status,
        statusText: networkResponse.statusText,
        headers
      });

      cache.put(request, responseWithMetadata.clone());
    }

    trackResponseTime(startTime);
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network-first failed, trying cache:', error.message);

    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      performanceMetrics.cacheHits++;

      // Add offline indicator
      const headers = new Headers(cachedResponse.headers);
      headers.set('X-Served-By', 'service-worker-cache');
      headers.set('X-Cache-Status', 'OFFLINE-FALLBACK');

      trackResponseTime(startTime);
      return new Response(cachedResponse.body, {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers
      });
    }

    performanceMetrics.errors++;
    trackResponseTime(startTime);
    return new Response(JSON.stringify({
      error: 'Offline - No cached data available',
      offline: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Stale-while-revalidate for property searches
async function handleStaleWhileRevalidateApi(request, startTime) {
  const cache = await caches.open(API_CACHE);
  const cachedResponse = await cache.match(request);

  // Always fetch fresh data in background
  const fetchPromise = fetch(request).then(async (networkResponse) => {
    if (networkResponse.ok) {
      // Add metadata to response
      const headers = new Headers(networkResponse.headers);
      headers.set('sw-cached-at', new Date().toISOString());
      headers.set('sw-strategy', 'stale-while-revalidate');

      const responseWithMetadata = new Response(networkResponse.body, {
        status: networkResponse.status,
        statusText: networkResponse.statusText,
        headers
      });

      await cache.put(request, responseWithMetadata.clone());
    }
    return networkResponse;
  }).catch(error => {
    console.log('[SW] Background fetch failed:', error.message);
    return null;
  });

  // Return cached response immediately if available
  if (cachedResponse) {
    performanceMetrics.cacheHits++;

    // Enhance cached response with metadata
    const responseBody = await cachedResponse.text();
    let parsedBody;

    try {
      parsedBody = JSON.parse(responseBody);
      parsedBody.cached = true;
      parsedBody.offline = !navigator.onLine;
      parsedBody.cacheTimestamp = cachedResponse.headers.get('sw-cached-at');
    } catch (error) {
      // If not JSON, return as-is
      trackResponseTime(startTime);
      return cachedResponse;
    }

    trackResponseTime(startTime);
    return new Response(JSON.stringify(parsedBody), {
      status: cachedResponse.status,
      statusText: cachedResponse.statusText,
      headers: {
        ...Object.fromEntries(cachedResponse.headers),
        'X-Cache-Status': 'HIT',
        'Content-Type': 'application/json'
      }
    });
  }

  // No cached response, wait for network
  performanceMetrics.cacheMisses++;
  const networkResponse = await fetchPromise;

  trackResponseTime(startTime);
  return networkResponse || new Response(JSON.stringify({
    error: 'Network unavailable',
    offline: true
  }), {
    status: 503,
    headers: { 'Content-Type': 'application/json' }
  });
}

// Network-only for real-time APIs
async function handleNetworkOnlyApi(request, startTime) {
  try {
    const response = await fetch(request);
    trackResponseTime(startTime);
    return response;
  } catch (error) {
    performanceMetrics.errors++;
    trackResponseTime(startTime);
    return new Response(JSON.stringify({
      error: 'Network Error',
      message: error.message
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Generic stale-while-revalidate
async function handleStaleWhileRevalidate(request, cacheName, startTime) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

  const fetchPromise = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(error => {
    console.log('[SW] Background fetch failed:', error.message);
    return null;
  });

  if (cachedResponse) {
    performanceMetrics.cacheHits++;
    trackResponseTime(startTime);
    return cachedResponse;
  }

  performanceMetrics.cacheMisses++;
  const networkResponse = await fetchPromise;
  trackResponseTime(startTime);
  return networkResponse || new Response('Offline', { status: 503 });
}

// Navigation handler with app shell
async function handleNavigation(request, startTime) {
  try {
    const response = await fetch(request);
    trackResponseTime(startTime);
    return response;
  } catch (error) {
    // Serve app shell when offline
    const cache = await caches.open(STATIC_CACHE);
    const appShell = await cache.match('/index.html');

    if (appShell) {
      performanceMetrics.cacheHits++;
      trackResponseTime(startTime);
      return appShell;
    }

    performanceMetrics.errors++;
    trackResponseTime(startTime);
    return new Response('Offline', { status: 503 });
  }
}

// Utility functions
function isStale(response, maxAge = 5 * 60 * 1000) {
  const cacheDate = response.headers.get('sw-cached-at') || response.headers.get('date');
  if (!cacheDate) return true;

  const age = Date.now() - new Date(cacheDate).getTime();
  return age > maxAge;
}

async function updateCacheInBackground(request, cache) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      await cache.put(request, response);
    }
  } catch (error) {
    console.log('[SW] Background update failed:', error.message);
  }
}

// Legacy API request handler for compatibility
async function handleApiRequest(request) {
  const cache = await caches.open(API_CACHE);

  // For property search, implement stale-while-revalidate
  if (request.url.includes('/properties/search')) {
    return staleWhileRevalidate(request, cache);
  }

  // For other API requests, try network first
  try {
    const networkResponse = await fetch(request);

    // Cache successful GET requests
    if (request.method === 'GET' && networkResponse.ok) {
      const responseClone = networkResponse.clone();

      // Only cache responses under 10MB
      const contentLength = responseClone.headers.get('content-length');
      if (!contentLength || parseInt(contentLength) < 10 * 1024 * 1024) {
        cache.put(request, responseClone);
      }
    }

    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed, trying cache', error);

    // If network fails, try cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // If no cache, return error response
    return new Response(
      JSON.stringify({
        error: 'Network unavailable',
        cached: false,
        offline: true
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle static assets - Cache First
async function handleStaticAsset(request) {
  const cache = await caches.open(STATIC_CACHE);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Failed to fetch static asset', error);
    throw error;
  }
}

// Handle navigation requests
async function handleNavigation(request) {
  try {
    return await fetch(request);
  } catch (error) {
    // If offline, serve cached index.html
    const cache = await caches.open(STATIC_CACHE);
    return cache.match('/index.html');
  }
}

// Stale While Revalidate strategy for property searches
async function staleWhileRevalidate(request, cache) {
  // Get cached version first
  const cachedResponse = await cache.match(request);

  // Fetch fresh version in background
  const networkPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        // Update cache with fresh response
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch((error) => {
      console.log('Service Worker: Network error in background', error);
      return null;
    });

  // Return cached version immediately if available
  if (cachedResponse) {
    // Add cache indicator
    const modifiedResponse = cachedResponse.clone();

    // Try to add cached flag to response if possible
    try {
      const responseData = await modifiedResponse.json();
      responseData.cached = true;
      responseData.offline = !navigator.onLine;

      return new Response(JSON.stringify(responseData), {
        status: modifiedResponse.status,
        statusText: modifiedResponse.statusText,
        headers: modifiedResponse.headers
      });
    } catch (error) {
      // If response is not JSON, return as-is
      return cachedResponse;
    }
  }

  // If no cached version, wait for network
  return networkPromise || new Response(
    JSON.stringify({
      error: 'No cached data available',
      cached: false,
      offline: true
    }),
    {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}

// Enhanced message handling for comprehensive cache management
self.addEventListener('message', async (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case 'CLEAR_CACHE':
      await clearCache(payload?.cacheNames);
      event.ports[0]?.postMessage({ type: 'CACHE_CLEARED' });
      break;

    case 'PREFETCH_PROPERTIES':
      await prefetchCommonSearches();
      event.ports[0]?.postMessage({ type: 'PREFETCH_COMPLETE' });
      break;

    case 'WARM_CACHE':
      await warmCache();
      event.ports[0]?.postMessage({ type: 'CACHE_WARMED' });
      break;

    case 'GET_CACHE_SIZE':
      const size = await getCacheSize();
      event.ports[0]?.postMessage({ type: 'CACHE_SIZE', size });
      break;

    case 'GET_PERFORMANCE_REPORT':
      await generatePerformanceReport();
      const totalRequests = performanceMetrics.cacheHits + performanceMetrics.cacheMisses;
      const hitRate = totalRequests > 0 ? (performanceMetrics.cacheHits / totalRequests) * 100 : 0;

      event.ports[0]?.postMessage({
        type: 'PERFORMANCE_REPORT',
        data: {
          ...performanceMetrics,
          hitRate,
          target: { hitRate: 80, achieved: hitRate >= 80 },
          cacheSize: await getCacheSize()
        }
      });
      break;

    case 'INVALIDATE_CACHE':
      const invalidated = await invalidateCache(payload?.pattern || '', payload?.reason || 'manual');
      event.ports[0]?.postMessage({
        type: 'CACHE_INVALIDATED',
        count: invalidated
      });
      break;

    case 'GET_POPULAR_URLS':
      const popularUrls = smartCache.getTopUrls(payload?.limit || 10);
      event.ports[0]?.postMessage({
        type: 'POPULAR_URLS',
        urls: popularUrls
      });
      break;

    case 'GET_CACHE_STATS':
      const allCaches = await caches.keys();
      const stats = {};

      for (const cacheName of allCaches) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        stats[cacheName] = keys.length;
      }

      event.ports[0]?.postMessage({
        type: 'CACHE_STATS',
        stats,
        indexedDBAvailable: !!dbCache
      });
      break;

    default:
      console.log('[SW] Unknown message type:', type);
  }
});

// Clear specific caches
async function clearCache(cacheNames = [API_CACHE]) {
  for (const cacheName of cacheNames) {
    await caches.delete(cacheName);
    console.log('Service Worker: Cleared cache', cacheName);
  }
}

// Prefetch common property searches
async function prefetchCommonSearches() {
  const commonSearches = [
    'county=BROWARD&limit=20',
    'county=MIAMI-DADE&limit=20',
    'county=PALM BEACH&limit=20',
    'min_value=100000&max_value=500000&limit=20',
  ];

  const cache = await caches.open(API_CACHE);

  for (const searchParams of commonSearches) {
    try {
      const url = `http://localhost:8000/api/properties/search?${searchParams}`;
      const response = await fetch(url);

      if (response.ok) {
        await cache.put(url, response);
        console.log('Service Worker: Prefetched search', searchParams);
      }
    } catch (error) {
      console.log('Service Worker: Failed to prefetch', searchParams, error);
    }
  }
}

// Get total cache size
async function getCacheSize() {
  const cacheNames = await caches.keys();
  let totalSize = 0;

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();

    for (const request of requests) {
      const response = await cache.match(request);
      if (response) {
        const blob = await response.blob();
        totalSize += blob.size;
      }
    }
  }

  return totalSize;
}

// Enhanced IndexedDB operations for large dataset caching
async function storeInIndexedDB(url, data, type = 'general') {
  if (!dbCache) return false;

  try {
    const transaction = dbCache.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    const item = {
      url: url,
      data: data,
      type: type,
      timestamp: Date.now(),
      size: JSON.stringify(data).length
    };

    await store.put(item);
    return true;
  } catch (error) {
    console.error('[SW] IndexedDB store error:', error);
    return false;
  }
}

async function getFromIndexedDB(url) {
  if (!dbCache) return null;

  try {
    const transaction = dbCache.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(url);

    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        const result = request.result;
        if (result && !isIndexedDBExpired(result)) {
          performanceMetrics.indexedDBHits++;
          resolve(result.data);
        } else {
          resolve(null);
        }
      };
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('[SW] IndexedDB get error:', error);
    return null;
  }
}

function isIndexedDBExpired(item, maxAge = 30 * 60 * 1000) { // 30 minutes default
  return (Date.now() - item.timestamp) > maxAge;
}

async function cleanupIndexedDB() {
  if (!dbCache) return;

  try {
    const transaction = dbCache.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index('timestamp');

    // Delete entries older than 24 hours
    const cutoffTime = Date.now() - (24 * 60 * 60 * 1000);
    const range = IDBKeyRange.upperBound(cutoffTime);

    const request = index.openCursor(range);
    request.onsuccess = (event) => {
      const cursor = event.target.result;
      if (cursor) {
        cursor.delete();
        cursor.continue();
      }
    };
  } catch (error) {
    console.error('[SW] IndexedDB cleanup error:', error);
  }
}

// Performance monitoring and reporting
async function initPerformanceMonitoring() {
  // Start cache warming scheduler
  setInterval(async () => {
    if (Date.now() - cacheWarmingSchedule.lastWarming > cacheWarmingSchedule.interval) {
      await warmCache();
      cacheWarmingSchedule.lastWarming = Date.now();
    }
  }, 10 * 60 * 1000); // Check every 10 minutes

  // Performance reporting every 30 minutes
  setInterval(async () => {
    await generatePerformanceReport();
  }, 30 * 60 * 1000);

  // IndexedDB cleanup every hour
  setInterval(async () => {
    await cleanupIndexedDB();
  }, 60 * 60 * 1000);
}

async function warmCache() {
  console.log('[SW] Starting cache warming cycle');

  const cache = await caches.open(API_CACHE);
  const apiEndpoints = [
    'http://localhost:8000',
    'http://localhost:8002',
    'http://localhost:3005'
  ];

  for (const endpoint of apiEndpoints) {
    for (const query of cacheWarmingSchedule.popularSearches) {
      try {
        const url = `${endpoint}/api/properties/search?${query}`;
        const response = await fetch(url, {
          headers: { 'Cache-Control': 'max-age=900' }
        });

        if (response.ok) {
          await cache.put(url, response.clone());
          performanceMetrics.warmCacheHits++;

          // Store large datasets in IndexedDB
          if (dbCache) {
            const data = await response.json();
            await storeInIndexedDB(url, data, 'warm-cache');
          }
        }
      } catch (error) {
        console.log('[SW] Cache warming failed for:', endpoint, query);
      }
    }
  }

  console.log('[SW] Cache warming completed');
}

async function generatePerformanceReport() {
  const totalRequests = performanceMetrics.cacheHits + performanceMetrics.cacheMisses;
  if (totalRequests > 0) {
    performanceMetrics.cacheHitRate = (performanceMetrics.cacheHits / totalRequests) * 100;
  }

  const report = {
    timestamp: new Date().toISOString(),
    metrics: { ...performanceMetrics },
    cacheSize: await getCacheSize(),
    target: { hitRate: 80, achieved: performanceMetrics.cacheHitRate >= 80 }
  };

  console.log('[SW] Performance Report:', report);

  // Send report to main thread if available
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage({
      type: 'PERFORMANCE_REPORT',
      data: report
    });
  });
}

// Enhanced cache invalidation strategies
async function invalidateCache(pattern, reason = 'manual') {
  console.log(`[SW] Invalidating cache pattern: ${pattern}, reason: ${reason}`);

  const cacheNames = await caches.keys();
  let invalidatedCount = 0;

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();

    for (const request of requests) {
      if (request.url.includes(pattern)) {
        await cache.delete(request);
        invalidatedCount++;
      }
    }
  }

  // Also invalidate from IndexedDB
  if (dbCache) {
    try {
      const transaction = dbCache.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.openCursor();

      request.onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          if (cursor.value.url.includes(pattern)) {
            cursor.delete();
            invalidatedCount++;
          }
          cursor.continue();
        }
      };
    } catch (error) {
      console.error('[SW] IndexedDB invalidation error:', error);
    }
  }

  console.log(`[SW] Invalidated ${invalidatedCount} cache entries`);
  return invalidatedCount;
}

// Smart cache management with ML-like prioritization
class SmartCacheManager {
  constructor() {
    this.accessPatterns = new Map();
    this.popularityScore = new Map();
  }

  recordAccess(url) {
    const count = this.accessPatterns.get(url) || 0;
    this.accessPatterns.set(url, count + 1);

    // Calculate popularity score based on recency and frequency
    const now = Date.now();
    const score = this.popularityScore.get(url) || { score: 0, lastAccess: now };

    // Decay previous score and add new access
    const timeDiff = now - score.lastAccess;
    const decayFactor = Math.exp(-timeDiff / (24 * 60 * 60 * 1000)); // 24 hour decay

    score.score = (score.score * decayFactor) + 1;
    score.lastAccess = now;

    this.popularityScore.set(url, score);
  }

  shouldCache(url, responseSize) {
    const score = this.popularityScore.get(url);

    // Cache if popular or if it's a small response
    if (!score) return responseSize < 1024 * 1024; // Cache small responses by default

    // Higher threshold for larger responses
    const sizeThreshold = responseSize > 5 * 1024 * 1024 ? 10 : 2;

    return score.score >= sizeThreshold;
  }

  getTopUrls(limit = 10) {
    return Array.from(this.popularityScore.entries())
      .sort(([,a], [,b]) => b.score - a.score)
      .slice(0, limit)
      .map(([url]) => url);
  }
}

const smartCache = new SmartCacheManager();