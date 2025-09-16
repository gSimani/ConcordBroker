/**
 * Redis Cache Service for MCP
 * Provides high-performance caching with automatic fallback
 */

const redis = require('redis');

class RedisCacheService {
  constructor() {
    this.client = null;
    this.memoryCache = new Map();
    this.isConnected = false;
    this.stats = {
      hits: 0,
      misses: 0,
      errors: 0,
      memorySize: 0
    };
  }

  async connect() {
    try {
      // Connect to Redis Cloud
      const redisConfig = {
        host: process.env.REDIS_CLOUD_HOST || process.env.REDIS_HOST || 'redis-19041.c276.us-east-1-2.ec2.cloud.redislabs.com',
        port: process.env.REDIS_CLOUD_PORT || process.env.REDIS_PORT || 19041,
        password: process.env.REDIS_CLOUD_PASSWORD || process.env.REDIS_PASSWORD || process.env.REDIS_CLOUD_API_KEY,
        retry_strategy: (options) => {
          if (options.error && options.error.code === 'ECONNREFUSED') {
            console.log('Redis connection refused, using memory cache');
            return new Error('Redis not available');
          }
          if (options.total_retry_time > 1000 * 60 * 60) {
            return new Error('Retry time exhausted');
          }
          if (options.attempt > 10) {
            return undefined;
          }
          return Math.min(options.attempt * 100, 3000);
        }
      };

      // Create the Redis client
      this.client = redis.createClient(redisConfig);

      await new Promise((resolve, reject) => {
        this.client.on('connect', () => {
          console.log('[Redis] Connected successfully');
          this.isConnected = true;
          resolve();
        });

        this.client.on('error', (err) => {
          console.log('[Redis] Connection error:', err.message);
          this.isConnected = false;
        });

        // Timeout after 2 seconds
        setTimeout(() => {
          if (!this.isConnected) {
            console.log('[Redis] Connection timeout, using memory cache');
            reject(new Error('Redis connection timeout'));
          }
        }, 2000);
      });

    } catch (error) {
      console.log('[Cache] Redis not available, using in-memory cache');
      this.isConnected = false;
    }

    return this;
  }

  /**
   * Get value from cache
   */
  async get(key) {
    try {
      // Try Redis first
      if (this.isConnected && this.client) {
        return new Promise((resolve) => {
          this.client.get(key, (err, value) => {
            if (err) {
              this.stats.errors++;
              resolve(this.getFromMemory(key));
            } else if (value) {
              this.stats.hits++;
              resolve(JSON.parse(value));
            } else {
              this.stats.misses++;
              resolve(null);
            }
          });
        });
      }
    } catch (error) {
      this.stats.errors++;
    }

    // Fallback to memory cache
    return this.getFromMemory(key);
  }

  /**
   * Set value in cache
   */
  async set(key, value, ttl = 300) {
    const serialized = JSON.stringify(value);

    try {
      // Try Redis first
      if (this.isConnected && this.client) {
        this.client.setex(key, ttl, serialized);
      }
    } catch (error) {
      this.stats.errors++;
    }

    // Always set in memory cache as backup
    this.setInMemory(key, value, ttl);
  }

  /**
   * Get from memory cache
   */
  getFromMemory(key) {
    const item = this.memoryCache.get(key);
    if (item && item.expiry > Date.now()) {
      this.stats.hits++;
      return item.value;
    }
    if (item) {
      this.memoryCache.delete(key);
    }
    this.stats.misses++;
    return null;
  }

  /**
   * Set in memory cache
   */
  setInMemory(key, value, ttl) {
    // Limit memory cache size
    if (this.memoryCache.size > 1000) {
      // Remove oldest entries
      const keysToDelete = Array.from(this.memoryCache.keys()).slice(0, 100);
      keysToDelete.forEach(k => this.memoryCache.delete(k));
    }

    this.memoryCache.set(key, {
      value,
      expiry: Date.now() + (ttl * 1000)
    });

    this.stats.memorySize = this.memoryCache.size;
  }

  /**
   * Clear cache
   */
  async clear(pattern = '*') {
    try {
      if (this.isConnected && this.client) {
        if (pattern === '*') {
          this.client.flushdb();
        } else {
          // Clear specific pattern
          this.client.keys(pattern, (err, keys) => {
            if (!err && keys.length > 0) {
              this.client.del(keys);
            }
          });
        }
      }
    } catch (error) {
      console.error('[Cache] Clear error:', error);
    }

    // Clear memory cache
    if (pattern === '*') {
      this.memoryCache.clear();
    } else {
      // Clear matching keys from memory
      const regex = new RegExp(pattern.replace('*', '.*'));
      Array.from(this.memoryCache.keys())
        .filter(key => regex.test(key))
        .forEach(key => this.memoryCache.delete(key));
    }

    this.stats.memorySize = this.memoryCache.size;
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const hitRate = this.stats.hits + this.stats.misses > 0
      ? (this.stats.hits / (this.stats.hits + this.stats.misses) * 100).toFixed(2)
      : 0;

    return {
      ...this.stats,
      hitRate: `${hitRate}%`,
      redisConnected: this.isConnected,
      cacheType: this.isConnected ? 'Redis' : 'Memory'
    };
  }

  /**
   * Generate cache key from parameters
   */
  generateKey(prefix, params) {
    const sorted = Object.keys(params)
      .sort()
      .map(key => `${key}:${params[key]}`)
      .join('|');
    return `${prefix}:${sorted}`;
  }
}

// Singleton instance
let cacheInstance = null;

async function getCacheService() {
  if (!cacheInstance) {
    cacheInstance = new RedisCacheService();
    await cacheInstance.connect();
  }
  return cacheInstance;
}

module.exports = {
  RedisCacheService,
  getCacheService
};