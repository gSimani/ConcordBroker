/**
 * LRU (Least Recently Used) Cache for property data
 * Provides O(1) get/put operations with automatic eviction
 */

interface CacheNode<T> {
  key: string;
  value: T;
  timestamp: number;
  prev: CacheNode<T> | null;
  next: CacheNode<T> | null;
}

export class PropertyLRUCache<T = any> {
  private capacity: number;
  private cache: Map<string, CacheNode<T>>;
  private head: CacheNode<T> | null = null;
  private tail: CacheNode<T> | null = null;
  private hits = 0;
  private misses = 0;

  constructor(capacity = 1000) {
    this.capacity = capacity;
    this.cache = new Map();
  }

  /**
   * Get value from cache
   * @param key Cache key
   * @returns Cached value or null if not found
   */
  get(key: string): T | null {
    const node = this.cache.get(key);
    
    if (!node) {
      this.misses++;
      return null;
    }

    this.hits++;
    
    // Move to front (most recently used)
    this.moveToFront(node);
    
    return node.value;
  }

  /**
   * Put value in cache
   * @param key Cache key
   * @param value Value to cache
   */
  put(key: string, value: T): void {
    // Check if already exists
    if (this.cache.has(key)) {
      const node = this.cache.get(key)!;
      node.value = value;
      node.timestamp = Date.now();
      this.moveToFront(node);
      return;
    }

    // Create new node
    const newNode: CacheNode<T> = {
      key,
      value,
      timestamp: Date.now(),
      prev: null,
      next: this.head
    };

    // Add to front
    if (this.head) {
      this.head.prev = newNode;
    }
    this.head = newNode;

    if (!this.tail) {
      this.tail = newNode;
    }

    this.cache.set(key, newNode);

    // Evict if over capacity
    if (this.cache.size > this.capacity) {
      this.evictLRU();
    }
  }

  /**
   * Batch put multiple items
   */
  putBatch(items: Array<{ key: string; value: T }>): void {
    items.forEach(({ key, value }) => this.put(key, value));
  }

  /**
   * Check if key exists in cache
   */
  has(key: string): boolean {
    return this.cache.has(key);
  }

  /**
   * Delete specific key from cache
   */
  delete(key: string): boolean {
    const node = this.cache.get(key);
    if (!node) return false;

    this.removeNode(node);
    this.cache.delete(key);
    return true;
  }

  /**
   * Move node to front of list (most recently used)
   */
  private moveToFront(node: CacheNode<T>): void {
    if (node === this.head) return;

    // Remove from current position
    if (node.prev) {
      node.prev.next = node.next;
    }
    if (node.next) {
      node.next.prev = node.prev;
    }
    if (node === this.tail) {
      this.tail = node.prev;
    }

    // Move to front
    node.prev = null;
    node.next = this.head;
    if (this.head) {
      this.head.prev = node;
    }
    this.head = node;
  }

  /**
   * Remove node from linked list
   */
  private removeNode(node: CacheNode<T>): void {
    if (node.prev) {
      node.prev.next = node.next;
    } else {
      this.head = node.next;
    }

    if (node.next) {
      node.next.prev = node.prev;
    } else {
      this.tail = node.prev;
    }
  }

  /**
   * Evict least recently used item
   */
  private evictLRU(): void {
    if (!this.tail) return;

    const lru = this.tail;
    
    if (this.tail.prev) {
      this.tail = this.tail.prev;
      this.tail.next = null;
    } else {
      this.head = null;
      this.tail = null;
    }

    this.cache.delete(lru.key);
  }

  /**
   * Clear all cached items
   */
  clear(): void {
    this.cache.clear();
    this.head = null;
    this.tail = null;
    this.hits = 0;
    this.misses = 0;
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    size: number;
    capacity: number;
    hits: number;
    misses: number;
    hitRate: number;
  } {
    const totalRequests = this.hits + this.misses;
    return {
      size: this.cache.size,
      capacity: this.capacity,
      hits: this.hits,
      misses: this.misses,
      hitRate: totalRequests > 0 ? this.hits / totalRequests : 0
    };
  }

  /**
   * Get all cached keys
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.cache.size;
  }

  /**
   * Prune cache by age
   * @param maxAge Maximum age in milliseconds
   */
  pruneByAge(maxAge: number): number {
    const now = Date.now();
    const toDelete: string[] = [];

    this.cache.forEach((node, key) => {
      if (now - node.timestamp > maxAge) {
        toDelete.push(key);
      }
    });

    toDelete.forEach(key => this.delete(key));
    return toDelete.length;
  }
}

/**
 * Time-based expiring cache
 */
export class PropertyTTLCache<T = any> {
  private cache: Map<string, { value: T; expiry: number }>;
  private defaultTTL: number;
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(defaultTTL = 5 * 60 * 1000) { // 5 minutes default
    this.cache = new Map();
    this.defaultTTL = defaultTTL;
    this.startCleanup();
  }

  /**
   * Get value from cache
   */
  get(key: string): T | null {
    const item = this.cache.get(key);
    
    if (!item) return null;
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }
    
    return item.value;
  }

  /**
   * Put value in cache with optional TTL
   */
  put(key: string, value: T, ttl?: number): void {
    const expiry = Date.now() + (ttl ?? this.defaultTTL);
    this.cache.set(key, { value, expiry });
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    const item = this.cache.get(key);
    if (!item) return false;
    
    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }

  /**
   * Delete key from cache
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all cached items
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Start periodic cleanup of expired items
   */
  private startCleanup(): void {
    this.cleanupInterval = setInterval(() => {
      const now = Date.now();
      const toDelete: string[] = [];
      
      this.cache.forEach((item, key) => {
        if (now > item.expiry) {
          toDelete.push(key);
        }
      });
      
      toDelete.forEach(key => this.cache.delete(key));
    }, 60000); // Clean every minute
  }

  /**
   * Stop cleanup interval
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    this.cache.clear();
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.cache.size;
  }
}

/**
 * Composite cache with LRU and TTL
 */
export class PropertyHybridCache<T = any> {
  private lruCache: PropertyLRUCache<T>;
  private ttlCache: PropertyTTLCache<T>;

  constructor(capacity = 1000, defaultTTL = 5 * 60 * 1000) {
    this.lruCache = new PropertyLRUCache(capacity);
    this.ttlCache = new PropertyTTLCache(defaultTTL);
  }

  /**
   * Get from cache (checks TTL first, then LRU)
   */
  get(key: string): T | null {
    // Check TTL cache first (fresh data)
    let value = this.ttlCache.get(key);
    if (value !== null) return value;

    // Check LRU cache
    value = this.lruCache.get(key);
    if (value !== null) {
      // Refresh in TTL cache
      this.ttlCache.put(key, value);
    }

    return value;
  }

  /**
   * Put in both caches
   */
  put(key: string, value: T, ttl?: number): void {
    this.lruCache.put(key, value);
    this.ttlCache.put(key, value, ttl);
  }

  /**
   * Clear both caches
   */
  clear(): void {
    this.lruCache.clear();
    this.ttlCache.clear();
  }

  /**
   * Get combined stats
   */
  getStats() {
    return {
      lru: this.lruCache.getStats(),
      ttl: { size: this.ttlCache.size() }
    };
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.lruCache.clear();
    this.ttlCache.destroy();
  }
}

// Export singleton instances
export const propertyCache = new PropertyHybridCache(5000, 10 * 60 * 1000); // 5000 items, 10 min TTL
export const searchCache = new PropertyLRUCache<any>(100); // Cache 100 recent searches
export const apiResponseCache = new PropertyTTLCache<any>(2 * 60 * 1000); // 2 min API cache