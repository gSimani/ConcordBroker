/**
 * ConcordBroker Unified Cache Manager
 * Coordinates caching across all layers: Browser, Service Worker, API, and Database
 * Target: 80%+ cache hit rate across all website operations
 */

import { ServiceWorkerManager } from '../utils/serviceWorker';

interface CacheConfig {
  ttl: number;
  strategy: 'cache-first' | 'network-first' | 'stale-while-revalidate' | 'network-only';
  storageTypes: ('memory' | 'localStorage' | 'indexedDB' | 'serviceWorker' | 'api')[];
  compression?: boolean;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number;
  size: number;
  accessCount: number;
  lastAccess: number;
  strategy: string;
  compressed?: boolean;
}

interface CacheMetrics {
  hits: number;
  misses: number;
  totalRequests: number;
  hitRate: number;
  averageResponseTime: number;
  cacheSize: number;
  storageDistribution: Record<string, number>;
}

export class UnifiedCacheManager {
  private memoryCache = new Map<string, CacheEntry>();
  private serviceWorkerManager: ServiceWorkerManager | null = null;
  private metrics: CacheMetrics = {
    hits: 0,
    misses: 0,
    totalRequests: 0,
    hitRate: 0,
    averageResponseTime: 0,
    cacheSize: 0,
    storageDistribution: {}
  };

  // Cache configurations for different data types
  private cacheConfigs: Record<string, CacheConfig> = {
    'property-search': {
      ttl: 15 * 60 * 1000, // 15 minutes
      strategy: 'stale-while-revalidate',
      storageTypes: ['memory', 'serviceWorker', 'localStorage'],
      compression: true,
      priority: 'high'
    },
    'property-detail': {
      ttl: 30 * 60 * 1000, // 30 minutes
      strategy: 'cache-first',
      storageTypes: ['memory', 'serviceWorker', 'indexedDB'],
      compression: false,
      priority: 'high'
    },
    'sunbiz-entity': {
      ttl: 60 * 60 * 1000, // 1 hour
      strategy: 'cache-first',
      storageTypes: ['memory', 'indexedDB', 'api'],
      compression: true,
      priority: 'medium'
    },
    'user-preferences': {
      ttl: 24 * 60 * 60 * 1000, // 24 hours
      strategy: 'cache-first',
      storageTypes: ['localStorage'],
      compression: false,
      priority: 'medium'
    },
    'search-suggestions': {
      ttl: 5 * 60 * 1000, // 5 minutes
      strategy: 'stale-while-revalidate',
      storageTypes: ['memory', 'serviceWorker'],
      compression: false,
      priority: 'low'
    },
    'static-data': {
      ttl: 24 * 60 * 60 * 1000, // 24 hours
      strategy: 'cache-first',
      storageTypes: ['serviceWorker', 'localStorage'],
      compression: false,
      priority: 'critical'
    }
  };

  private readonly API_ENDPOINTS = [
    'http://localhost:8001',
    'http://localhost:8002',
    'http://localhost:3005'
  ];

  constructor() {
    this.initializeServiceWorker();
    this.startPerformanceMonitoring();
    this.scheduleMaintenanceTasks();
  }

  // === INITIALIZATION ===

  private async initializeServiceWorker() {
    try {
      if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        this.serviceWorkerManager = new ServiceWorkerManager();
        console.log('[Cache] Service Worker integration ready');
      }
    } catch (error) {
      console.warn('[Cache] Service Worker initialization failed:', error);
    }
  }

  // === CORE CACHE OPERATIONS ===

  async get<T>(key: string, type: string = 'default'): Promise<T | null> {
    const startTime = performance.now();
    this.metrics.totalRequests++;

    try {
      const config = this.cacheConfigs[type] || this.getDefaultConfig();
      let result: T | null = null;

      // Try each storage type in order of preference
      for (const storageType of config.storageTypes) {
        result = await this.getFromStorage<T>(key, storageType);

        if (result !== null) {
          this.metrics.hits++;
          this.updateMetrics(performance.now() - startTime);
          this.updateAccessPattern(key);

          console.log(`[Cache] Hit from ${storageType} for ${key}`);
          return result;
        }
      }

      this.metrics.misses++;
      this.updateMetrics(performance.now() - startTime);
      console.log(`[Cache] Miss for ${key}`);
      return null;

    } catch (error) {
      console.error(`[Cache] Get error for ${key}:`, error);
      this.metrics.misses++;
      return null;
    }
  }

  async set<T>(key: string, data: T, type: string = 'default'): Promise<boolean> {
    try {
      const config = this.cacheConfigs[type] || this.getDefaultConfig();
      const serializedData = JSON.stringify(data);
      const size = new Blob([serializedData]).size;

      const entry: CacheEntry = {
        data,
        timestamp: Date.now(),
        ttl: config.ttl,
        size,
        accessCount: 1,
        lastAccess: Date.now(),
        strategy: config.strategy,
        compressed: config.compression && size > 1024 // Compress if enabled and > 1KB
      };

      // Store in all configured storage types
      const promises = config.storageTypes.map(storageType =>
        this.setInStorage(key, entry, storageType)
      );

      const results = await Promise.allSettled(promises);
      const successCount = results.filter(r => r.status === 'fulfilled').length;

      console.log(`[Cache] Stored ${key} in ${successCount}/${config.storageTypes.length} storage types`);
      return successCount > 0;

    } catch (error) {
      console.error(`[Cache] Set error for ${key}:`, error);
      return false;
    }
  }

  // === STORAGE-SPECIFIC OPERATIONS ===

  private async getFromStorage<T>(key: string, storageType: string): Promise<T | null> {
    switch (storageType) {
      case 'memory':
        return this.getFromMemory<T>(key);

      case 'localStorage':
        return this.getFromLocalStorage<T>(key);

      case 'indexedDB':
        return this.getFromIndexedDB<T>(key);

      case 'serviceWorker':
        return this.getFromServiceWorker<T>(key);

      case 'api':
        return this.getFromAPI<T>(key);

      default:
        return null;
    }
  }

  private async setInStorage<T>(key: string, entry: CacheEntry, storageType: string): Promise<boolean> {
    switch (storageType) {
      case 'memory':
        return this.setInMemory(key, entry);

      case 'localStorage':
        return this.setInLocalStorage(key, entry);

      case 'indexedDB':
        return this.setInIndexedDB(key, entry);

      case 'serviceWorker':
        return this.setInServiceWorker(key, entry);

      case 'api':
        return this.setInAPI(key, entry);

      default:
        return false;
    }
  }

  // === MEMORY CACHE ===

  private getFromMemory<T>(key: string): T | null {
    const entry = this.memoryCache.get(key);

    if (!entry) return null;

    if (this.isExpired(entry)) {
      this.memoryCache.delete(key);
      return null;
    }

    entry.accessCount++;
    entry.lastAccess = Date.now();
    return entry.data as T;
  }

  private setInMemory(key: string, entry: CacheEntry): boolean {
    // Limit memory cache size
    if (this.memoryCache.size >= 1000) {
      this.evictLeastUsed();
    }

    this.memoryCache.set(key, entry);
    return true;
  }

  // === LOCAL STORAGE ===

  private getFromLocalStorage<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(`cache:${key}`);
      if (!item) return null;

      const entry: CacheEntry = JSON.parse(item);

      if (this.isExpired(entry)) {
        localStorage.removeItem(`cache:${key}`);
        return null;
      }

      return entry.data as T;
    } catch (error) {
      console.error('[Cache] LocalStorage get error:', error);
      return null;
    }
  }

  private setInLocalStorage(key: string, entry: CacheEntry): boolean {
    try {
      // Check storage quota
      if (this.getLocalStorageSize() > 4 * 1024 * 1024) { // 4MB limit
        this.cleanupLocalStorage();
      }

      localStorage.setItem(`cache:${key}`, JSON.stringify(entry));
      return true;
    } catch (error) {
      console.error('[Cache] LocalStorage set error:', error);
      return false;
    }
  }

  // === INDEXEDDB ===

  private async getFromIndexedDB<T>(key: string): Promise<T | null> {
    try {
      const db = await this.openIndexedDB();
      const transaction = db.transaction(['cache'], 'readonly');
      const store = transaction.objectStore('cache');

      return new Promise((resolve) => {
        const request = store.get(key);

        request.onsuccess = () => {
          const entry = request.result;

          if (!entry || this.isExpired(entry)) {
            resolve(null);
            return;
          }

          resolve(entry.data as T);
        };

        request.onerror = () => resolve(null);
      });
    } catch (error) {
      console.error('[Cache] IndexedDB get error:', error);
      return null;
    }
  }

  private async setInIndexedDB(key: string, entry: CacheEntry): Promise<boolean> {
    try {
      const db = await this.openIndexedDB();
      const transaction = db.transaction(['cache'], 'readwrite');
      const store = transaction.objectStore('cache');

      return new Promise((resolve) => {
        const request = store.put({ ...entry, id: key });

        request.onsuccess = () => resolve(true);
        request.onerror = () => resolve(false);
      });
    } catch (error) {
      console.error('[Cache] IndexedDB set error:', error);
      return false;
    }
  }

  // === SERVICE WORKER ===

  private async getFromServiceWorker<T>(key: string): Promise<T | null> {
    // Service worker caching is handled automatically through fetch interception
    // This is a placeholder for explicit SW communication if needed
    return null;
  }

  private async setInServiceWorker(key: string, entry: CacheEntry): Promise<boolean> {
    // Service worker caching is handled automatically
    return true;
  }

  // === API CACHE ===

  private async getFromAPI<T>(key: string): Promise<T | null> {
    // Try to get cached data from API endpoints with Redis backend
    for (const endpoint of this.API_ENDPOINTS) {
      try {
        const response = await fetch(`${endpoint}/api/cache/${encodeURIComponent(key)}`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
          const data = await response.json();
          return data as T;
        }
      } catch (error) {
        console.log(`[Cache] API cache miss for ${endpoint}`);
      }
    }

    return null;
  }

  private async setInAPI(key: string, entry: CacheEntry): Promise<boolean> {
    // Store in API cache (Redis backend)
    const promises = this.API_ENDPOINTS.map(async endpoint => {
      try {
        const response = await fetch(`${endpoint}/api/cache/${encodeURIComponent(key)}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            data: entry.data,
            ttl: Math.floor(entry.ttl / 1000) // Convert to seconds
          })
        });

        return response.ok;
      } catch (error) {
        console.error(`[Cache] API cache set error for ${endpoint}:`, error);
        return false;
      }
    });

    const results = await Promise.allSettled(promises);
    return results.some(r => r.status === 'fulfilled' && r.value);
  }

  // === INTELLIGENT CACHE STRATEGIES ===

  async getWithStrategy<T>(
    key: string,
    fetcher: () => Promise<T>,
    type: string = 'default'
  ): Promise<T> {
    const config = this.cacheConfigs[type] || this.getDefaultConfig();

    switch (config.strategy) {
      case 'cache-first':
        return this.cacheFirst(key, fetcher, type);

      case 'network-first':
        return this.networkFirst(key, fetcher, type);

      case 'stale-while-revalidate':
        return this.staleWhileRevalidate(key, fetcher, type);

      case 'network-only':
        return fetcher();

      default:
        return this.staleWhileRevalidate(key, fetcher, type);
    }
  }

  private async cacheFirst<T>(key: string, fetcher: () => Promise<T>, type: string): Promise<T> {
    const cached = await this.get<T>(key, type);

    if (cached !== null) {
      return cached;
    }

    const data = await fetcher();
    await this.set(key, data, type);
    return data;
  }

  private async networkFirst<T>(key: string, fetcher: () => Promise<T>, type: string): Promise<T> {
    try {
      const data = await fetcher();
      await this.set(key, data, type);
      return data;
    } catch (error) {
      const cached = await this.get<T>(key, type);

      if (cached !== null) {
        return cached;
      }

      throw error;
    }
  }

  private async staleWhileRevalidate<T>(key: string, fetcher: () => Promise<T>, type: string): Promise<T> {
    const cached = await this.get<T>(key, type);

    // Start background fetch
    const backgroundFetch = fetcher().then(data => {
      this.set(key, data, type);
      return data;
    }).catch(error => {
      console.error('[Cache] Background fetch failed:', error);
    });

    if (cached !== null) {
      // Return cached data immediately, update in background
      return cached;
    }

    // No cached data, wait for fetch
    return await backgroundFetch as T;
  }

  // === CACHE MANAGEMENT ===

  async invalidate(pattern: string, reason: string = 'manual'): Promise<number> {
    let invalidatedCount = 0;

    // Clear memory cache
    for (const [key] of this.memoryCache) {
      if (key.includes(pattern)) {
        this.memoryCache.delete(key);
        invalidatedCount++;
      }
    }

    // Clear localStorage
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && key.startsWith('cache:') && key.includes(pattern)) {
        localStorage.removeItem(key);
        invalidatedCount++;
      }
    }

    // Clear IndexedDB
    try {
      const db = await this.openIndexedDB();
      const transaction = db.transaction(['cache'], 'readwrite');
      const store = transaction.objectStore('cache');
      const request = store.openCursor();

      await new Promise<void>((resolve) => {
        request.onsuccess = (event) => {
          const cursor = (event.target as IDBRequest).result;
          if (cursor) {
            if (cursor.key.toString().includes(pattern)) {
              cursor.delete();
              invalidatedCount++;
            }
            cursor.continue();
          } else {
            resolve();
          }
        };
      });
    } catch (error) {
      console.error('[Cache] IndexedDB invalidation error:', error);
    }

    // Invalidate service worker cache
    if (this.serviceWorkerManager) {
      try {
        await this.serviceWorkerManager.clearCache([pattern]);
      } catch (error) {
        console.error('[Cache] Service Worker invalidation error:', error);
      }
    }

    console.log(`[Cache] Invalidated ${invalidatedCount} entries for pattern: ${pattern}`);
    return invalidatedCount;
  }

  async warmCache(urls: string[] = []): Promise<void> {
    console.log('[Cache] Starting cache warming...');

    const popularSearches = [
      '/api/properties/search?county=BROWARD&limit=20',
      '/api/properties/search?county=MIAMI-DADE&limit=20',
      '/api/properties/search?min_value=100000&max_value=500000&limit=20',
      '/api/properties/search?city=Miami&limit=20',
      '/api/properties/search?property_type=RESIDENTIAL&limit=20'
    ];

    const urlsToWarm = urls.length > 0 ? urls : popularSearches;

    for (const endpoint of this.API_ENDPOINTS) {
      for (const url of urlsToWarm) {
        try {
          const fullUrl = `${endpoint}${url}`;
          const response = await fetch(fullUrl);

          if (response.ok) {
            const data = await response.json();
            const cacheKey = this.generateCacheKey(fullUrl);
            await this.set(cacheKey, data, 'property-search');
          }
        } catch (error) {
          console.error(`[Cache] Warming failed for ${endpoint}${url}:`, error);
        }
      }
    }

    console.log('[Cache] Cache warming completed');
  }

  // === PERFORMANCE MONITORING ===

  private startPerformanceMonitoring() {
    setInterval(() => {
      this.calculateMetrics();
      this.reportPerformance();
    }, 60000); // Every minute
  }

  private calculateMetrics() {
    const total = this.metrics.hits + this.metrics.misses;
    this.metrics.hitRate = total > 0 ? (this.metrics.hits / total) * 100 : 0;
    this.metrics.cacheSize = this.calculateTotalCacheSize();
  }

  private calculateTotalCacheSize(): number {
    let size = 0;

    // Memory cache
    for (const [, entry] of this.memoryCache) {
      size += entry.size;
    }

    // LocalStorage (approximate)
    try {
      let localStorageSize = 0;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cache:')) {
          localStorageSize += localStorage.getItem(key)?.length || 0;
        }
      }
      size += localStorageSize;
    } catch (error) {
      console.error('[Cache] LocalStorage size calculation error:', error);
    }

    return size;
  }

  private reportPerformance() {
    const report = {
      ...this.metrics,
      timestamp: new Date().toISOString(),
      target: { hitRate: 80, achieved: this.metrics.hitRate >= 80 }
    };

    console.log('[Cache] Performance Report:', report);

    // Send to analytics if available
    if (window.gtag) {
      window.gtag('event', 'cache_performance', {
        hit_rate: this.metrics.hitRate,
        cache_size: this.metrics.cacheSize,
        total_requests: this.metrics.totalRequests
      });
    }
  }

  // === UTILITY METHODS ===

  private getDefaultConfig(): CacheConfig {
    return {
      ttl: 5 * 60 * 1000, // 5 minutes
      strategy: 'stale-while-revalidate',
      storageTypes: ['memory'],
      priority: 'medium'
    };
  }

  private generateCacheKey(url: string): string {
    // Create a consistent cache key from URL
    try {
      const urlObj = new URL(url);
      const params = new URLSearchParams(urlObj.search);

      // Sort parameters for consistent keys
      const sortedParams = Array.from(params.entries()).sort();
      const normalizedUrl = `${urlObj.pathname}?${new URLSearchParams(sortedParams).toString()}`;

      return btoa(normalizedUrl).replace(/[+/=]/g, ''); // Base64 encode and remove special chars
    } catch (error) {
      // Fallback to simple hash
      return btoa(url).replace(/[+/=]/g, '');
    }
  }

  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }

  private updateAccessPattern(key: string) {
    const entry = this.memoryCache.get(key);
    if (entry) {
      entry.accessCount++;
      entry.lastAccess = Date.now();
    }
  }

  private updateMetrics(responseTime: number) {
    this.metrics.totalRequests++;
    this.metrics.averageResponseTime =
      (this.metrics.averageResponseTime * (this.metrics.totalRequests - 1) + responseTime) /
      this.metrics.totalRequests;
  }

  private evictLeastUsed() {
    // Remove 20% of least recently used items
    const entries = Array.from(this.memoryCache.entries())
      .sort(([,a], [,b]) => a.lastAccess - b.lastAccess);

    const toRemove = Math.floor(entries.length * 0.2);

    for (let i = 0; i < toRemove; i++) {
      this.memoryCache.delete(entries[i][0]);
    }
  }

  private cleanupLocalStorage() {
    const cacheKeys = [];

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('cache:')) {
        cacheKeys.push(key);
      }
    }

    // Remove oldest 25% of cache entries
    const toRemove = Math.floor(cacheKeys.length * 0.25);

    for (let i = 0; i < toRemove; i++) {
      localStorage.removeItem(cacheKeys[i]);
    }
  }

  private getLocalStorageSize(): number {
    let size = 0;
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('cache:')) {
        size += localStorage.getItem(key)?.length || 0;
      }
    }
    return size;
  }

  private async openIndexedDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('ConcordBrokerUnifiedCache', 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        if (!db.objectStoreNames.contains('cache')) {
          const store = db.createObjectStore('cache', { keyPath: 'id' });
          store.createIndex('timestamp', 'timestamp');
          store.createIndex('type', 'type');
        }
      };
    });
  }

  private scheduleMaintenanceTasks() {
    // Cleanup expired entries every 30 minutes
    setInterval(() => {
      this.cleanupExpiredEntries();
    }, 30 * 60 * 1000);

    // Full cache optimization every 2 hours
    setInterval(() => {
      this.optimizeCache();
    }, 2 * 60 * 60 * 1000);
  }

  private async cleanupExpiredEntries() {
    // Memory cache cleanup
    for (const [key, entry] of this.memoryCache) {
      if (this.isExpired(entry)) {
        this.memoryCache.delete(key);
      }
    }

    // LocalStorage cleanup
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);
      if (key && key.startsWith('cache:')) {
        try {
          const item = localStorage.getItem(key);
          if (item) {
            const entry = JSON.parse(item);
            if (this.isExpired(entry)) {
              localStorage.removeItem(key);
            }
          }
        } catch (error) {
          localStorage.removeItem(key); // Remove corrupted entries
        }
      }
    }

    console.log('[Cache] Cleanup completed');
  }

  private async optimizeCache() {
    console.log('[Cache] Starting cache optimization...');

    // Analyze access patterns and adjust cache configurations
    const accessData = new Map<string, { count: number; avgResponseTime: number }>();

    // Implementation would analyze actual usage patterns
    // and dynamically adjust cache strategies

    console.log('[Cache] Cache optimization completed');
  }

  // === PUBLIC API ===

  getMetrics(): CacheMetrics {
    return { ...this.metrics };
  }

  async getCacheStatus(): Promise<{
    totalSize: number;
    hitRate: number;
    storageBreakdown: Record<string, number>;
    isHealthy: boolean;
  }> {
    return {
      totalSize: this.calculateTotalCacheSize(),
      hitRate: this.metrics.hitRate,
      storageBreakdown: {
        memory: this.memoryCache.size,
        localStorage: this.getLocalStorageSize(),
        // IndexedDB size would require additional calculation
      },
      isHealthy: this.metrics.hitRate >= 80
    };
  }
}

// Global instance
export const unifiedCache = new UnifiedCacheManager();

// React Hook for easy integration
export function useUnifiedCache() {
  return {
    get: unifiedCache.get.bind(unifiedCache),
    set: unifiedCache.set.bind(unifiedCache),
    getWithStrategy: unifiedCache.getWithStrategy.bind(unifiedCache),
    invalidate: unifiedCache.invalidate.bind(unifiedCache),
    warmCache: unifiedCache.warmCache.bind(unifiedCache),
    getMetrics: unifiedCache.getMetrics.bind(unifiedCache),
    getCacheStatus: unifiedCache.getCacheStatus.bind(unifiedCache)
  };
}

// Export types
export type { CacheConfig, CacheEntry, CacheMetrics };