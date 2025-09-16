"""
=====================================================
STEP 4: REDIS CLOUD CACHING LAYER
Expected Performance Gain: 1000x for repeated queries
=====================================================

Chain of Thought:
1. Connect to Redis Cloud using credentials
2. Implement intelligent cache key generation
3. Create cache decorators for common queries
4. Set up TTL strategies based on data volatility
5. Implement cache invalidation on data changes
6. Add cache warming for critical queries
7. Monitor cache hit rates
"""

import os
import json
import hashlib
import pickle
import redis
from redis import Redis
from redis.sentinel import Sentinel
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
from datetime import datetime, timedelta
import asyncio
import aioredis
from dataclasses import dataclass
from enum import Enum
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Load environment variables
load_dotenv('.env.mcp')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# CACHE CONFIGURATION
# =====================================================

class CacheTTL(Enum):
    """TTL strategies based on data volatility"""
    STATIC = 86400      # 24 hours - for reference data
    SEMI_STATIC = 3600  # 1 hour - for aggregations
    DYNAMIC = 300       # 5 minutes - for real-time data
    VOLATILE = 60       # 1 minute - for rapidly changing data
    SESSION = 1800      # 30 minutes - for user sessions

@dataclass
class CacheConfig:
    """Cache configuration"""
    host: str
    port: int
    password: str
    db: int = 0
    max_connections: int = 50
    socket_timeout: int = 5
    retry_on_timeout: bool = True
    decode_responses: bool = False

class RedisCache:
    """Advanced Redis caching layer with intelligent strategies"""

    def __init__(self):
        self.config = CacheConfig(
            host=os.getenv('REDIS_CLOUD_HOST'),
            port=int(os.getenv('REDIS_CLOUD_PORT', 6379)),
            password=os.getenv('REDIS_CLOUD_PASSWORD')
        )
        self.redis_client = None
        self.async_client = None
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'invalidations': 0
        }
        self._connect()

    def _connect(self):
        """Establish Redis connection with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.redis_client = Redis(
                    host=self.config.host,
                    port=self.config.port,
                    password=self.config.password,
                    db=self.config.db,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.socket_timeout,
                    retry_on_timeout=self.config.retry_on_timeout,
                    decode_responses=self.config.decode_responses,
                    connection_pool=redis.BlockingConnectionPool(
                        host=self.config.host,
                        port=self.config.port,
                        password=self.config.password,
                        max_connections=self.config.max_connections
                    )
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Connected to Redis Cloud at {self.config.host}:{self.config.port}")
                return
            except Exception as e:
                logger.error(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)

    async def _async_connect(self):
        """Establish async Redis connection"""
        self.async_client = await aioredis.create_redis_pool(
            f'redis://:{self.config.password}@{self.config.host}:{self.config.port}',
            minsize=5,
            maxsize=20
        )

    # =====================================================
    # CACHE KEY GENERATION
    # =====================================================

    def generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate intelligent cache key based on query parameters"""
        # Sort params for consistent key generation
        sorted_params = sorted(params.items())
        param_str = json.dumps(sorted_params, sort_keys=True, default=str)

        # Create hash for long keys
        if len(param_str) > 200:
            param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]
            return f"{prefix}:{param_hash}"

        # Use readable format for short keys
        param_parts = [f"{k}={v}" for k, v in sorted_params]
        return f"{prefix}:{':'.join(param_parts)}"

    # =====================================================
    # CACHE DECORATORS
    # =====================================================

    def cached(self, prefix: str, ttl: CacheTTL = CacheTTL.SEMI_STATIC):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_params = {
                    'args': args,
                    'kwargs': kwargs
                }
                cache_key = self.generate_cache_key(prefix, cache_params)

                # Try to get from cache
                try:
                    cached_value = self.redis_client.get(cache_key)
                    if cached_value:
                        self.stats['hits'] += 1
                        logger.debug(f"Cache hit for {cache_key}")
                        return pickle.loads(cached_value)
                except Exception as e:
                    logger.error(f"Cache get error: {e}")
                    self.stats['errors'] += 1

                # Cache miss - execute function
                self.stats['misses'] += 1
                logger.debug(f"Cache miss for {cache_key}")
                result = func(*args, **kwargs)

                # Store in cache
                try:
                    self.redis_client.setex(
                        cache_key,
                        ttl.value,
                        pickle.dumps(result)
                    )
                except Exception as e:
                    logger.error(f"Cache set error: {e}")
                    self.stats['errors'] += 1

                return result

            wrapper.cache_key_prefix = prefix
            wrapper.invalidate = lambda *args, **kwargs: self.invalidate_pattern(f"{prefix}*")
            return wrapper
        return decorator

    def batch_cached(self, prefix: str, ttl: CacheTTL = CacheTTL.SEMI_STATIC):
        """Decorator for caching batch query results"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(ids: List[Any], *args, **kwargs):
                # Check cache for each ID
                cached_results = {}
                uncached_ids = []

                for id_val in ids:
                    cache_key = f"{prefix}:{id_val}"
                    try:
                        cached_value = self.redis_client.get(cache_key)
                        if cached_value:
                            cached_results[id_val] = pickle.loads(cached_value)
                            self.stats['hits'] += 1
                        else:
                            uncached_ids.append(id_val)
                            self.stats['misses'] += 1
                    except Exception as e:
                        logger.error(f"Cache error for {id_val}: {e}")
                        uncached_ids.append(id_val)

                # Fetch uncached items
                if uncached_ids:
                    fresh_results = func(uncached_ids, *args, **kwargs)

                    # Cache fresh results
                    pipe = self.redis_client.pipeline()
                    for id_val, result in fresh_results.items():
                        cache_key = f"{prefix}:{id_val}"
                        pipe.setex(cache_key, ttl.value, pickle.dumps(result))

                    try:
                        pipe.execute()
                    except Exception as e:
                        logger.error(f"Batch cache set error: {e}")

                    cached_results.update(fresh_results)

                return cached_results

            return wrapper
        return decorator

    # =====================================================
    # CACHE INVALIDATION
    # =====================================================

    def invalidate_key(self, key: str):
        """Invalidate specific cache key"""
        try:
            self.redis_client.delete(key)
            self.stats['invalidations'] += 1
            logger.debug(f"Invalidated cache key: {key}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        try:
            # Use SCAN for efficient pattern matching
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = self.redis_client.scan(
                    cursor, match=pattern, count=100
                )
                if keys:
                    self.redis_client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break

            self.stats['invalidations'] += deleted
            logger.info(f"Invalidated {deleted} cache keys matching {pattern}")
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")

    def invalidate_tag(self, tag: str):
        """Invalidate all keys with specific tag"""
        self.invalidate_pattern(f"*:tag:{tag}:*")

    # =====================================================
    # CACHE WARMING
    # =====================================================

    def warm_cache(self, queries: List[Dict[str, Any]]):
        """Pre-populate cache with common queries"""
        logger.info(f"Warming cache with {len(queries)} queries")

        for query in queries:
            try:
                # Execute query function with caching
                func = query.get('func')
                args = query.get('args', [])
                kwargs = query.get('kwargs', {})

                if func:
                    func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Cache warming error: {e}")

    # =====================================================
    # CACHE STATISTICS
    # =====================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total if total > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'errors': self.stats['errors'],
            'invalidations': self.stats['invalidations'],
            'hit_rate': f"{hit_rate:.2%}",
            'total_requests': total
        }

    def reset_stats(self):
        """Reset cache statistics"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'invalidations': 0
        }

# =====================================================
# SPECIALIZED CACHE IMPLEMENTATIONS
# =====================================================

class PropertyCache(RedisCache):
    """Specialized cache for property data"""

    @property
    def db_connection(self):
        """Get database connection"""
        if not hasattr(self, '_db_conn'):
            self._db_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
                database=os.getenv('POSTGRES_DATABASE'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                cursor_factory=RealDictCursor
            )
        return self._db_conn

    def get_property(self, parcel_id: str, county: str) -> Optional[Dict]:
        """Get property with caching"""
        cache_key = f"property:{county}:{parcel_id}"

        # Try cache first
        cached = self.redis_client.get(cache_key)
        if cached:
            self.stats['hits'] += 1
            return pickle.loads(cached)

        # Cache miss - fetch from database
        self.stats['misses'] += 1
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM florida_parcels
                WHERE parcel_id = %s AND county = %s
                LIMIT 1
            """, (parcel_id, county))
            result = cursor.fetchone()

        if result:
            # Cache for 1 hour
            self.redis_client.setex(
                cache_key,
                CacheTTL.SEMI_STATIC.value,
                pickle.dumps(dict(result))
            )

        return dict(result) if result else None

    def get_county_stats(self, county: str) -> Dict:
        """Get county statistics with caching"""
        cache_key = f"county_stats:{county}"

        # Try cache first
        cached = self.redis_client.get(cache_key)
        if cached:
            self.stats['hits'] += 1
            return pickle.loads(cached)

        # Cache miss - use materialized view
        self.stats['misses'] += 1
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM mv_county_statistics
                WHERE county = %s
            """, (county,))
            result = cursor.fetchone()

        if result:
            stats = dict(result)
            # Cache for 24 hours (static data)
            self.redis_client.setex(
                cache_key,
                CacheTTL.STATIC.value,
                pickle.dumps(stats)
            )
            return stats

        return {}

    def search_properties(self, filters: Dict) -> List[Dict]:
        """Search properties with result caching"""
        cache_key = self.generate_cache_key("search", filters)

        # Try cache first
        cached = self.redis_client.get(cache_key)
        if cached:
            self.stats['hits'] += 1
            return pickle.loads(cached)

        # Build query dynamically
        where_clauses = []
        params = []

        if 'county' in filters:
            where_clauses.append("county = %s")
            params.append(filters['county'])

        if 'min_value' in filters:
            where_clauses.append("just_value >= %s")
            params.append(filters['min_value'])

        if 'max_value' in filters:
            where_clauses.append("just_value <= %s")
            params.append(filters['max_value'])

        if 'property_use' in filters:
            where_clauses.append("property_use ILIKE %s")
            params.append(f"%{filters['property_use']}%")

        # Execute search
        self.stats['misses'] += 1
        with self.db_connection.cursor() as cursor:
            query = f"""
                SELECT parcel_id, county, owner_name, phy_addr1,
                       just_value, sale_price, sale_date
                FROM florida_parcels
                WHERE {' AND '.join(where_clauses)}
                LIMIT 100
            """
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]

        # Cache results for 5 minutes
        self.redis_client.setex(
            cache_key,
            CacheTTL.DYNAMIC.value,
            pickle.dumps(results)
        )

        return results

# =====================================================
# CACHE-ASIDE PATTERN WITH WRITE-THROUGH
# =====================================================

class CacheAsideManager:
    """Implements cache-aside pattern with write-through"""

    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.write_through_enabled = True

    def read(self, key: str, fetch_func: Callable, ttl: CacheTTL = CacheTTL.SEMI_STATIC):
        """Read with cache-aside pattern"""
        # Try cache
        cached = self.cache.redis_client.get(key)
        if cached:
            self.cache.stats['hits'] += 1
            return pickle.loads(cached)

        # Cache miss - fetch and cache
        self.cache.stats['misses'] += 1
        data = fetch_func()

        if data is not None:
            self.cache.redis_client.setex(
                key, ttl.value, pickle.dumps(data)
            )

        return data

    def write(self, key: str, data: Any, write_func: Callable, ttl: CacheTTL = CacheTTL.SEMI_STATIC):
        """Write with write-through caching"""
        # Write to database
        write_func(data)

        # Update cache if write-through enabled
        if self.write_through_enabled:
            self.cache.redis_client.setex(
                key, ttl.value, pickle.dumps(data)
            )

            # Invalidate related caches
            self._invalidate_related(key)

    def _invalidate_related(self, key: str):
        """Invalidate related cache entries"""
        # Extract entity type from key
        if key.startswith("property:"):
            # Invalidate county stats and searches
            county = key.split(":")[1]
            self.cache.invalidate_pattern(f"county_stats:{county}")
            self.cache.invalidate_pattern(f"search:*county={county}*")

# =====================================================
# USAGE EXAMPLES AND TESTING
# =====================================================

def test_cache_implementation():
    """Test cache implementation"""
    print("\n" + "="*60)
    print("TESTING REDIS CACHE IMPLEMENTATION")
    print("="*60)

    # Initialize cache
    cache = PropertyCache()

    # Test 1: Single property lookup
    print("\n1. Testing single property lookup...")
    start = time.time()
    prop1 = cache.get_property("123456789", "BROWARD")
    time1 = time.time() - start

    start = time.time()
    prop2 = cache.get_property("123456789", "BROWARD")  # Should hit cache
    time2 = time.time() - start

    print(f"   First call (DB): {time1:.4f}s")
    print(f"   Second call (Cache): {time2:.4f}s")
    print(f"   Speedup: {time1/time2:.1f}x")

    # Test 2: County statistics
    print("\n2. Testing county statistics...")
    start = time.time()
    stats1 = cache.get_county_stats("MIAMI-DADE")
    time1 = time.time() - start

    start = time.time()
    stats2 = cache.get_county_stats("MIAMI-DADE")  # Should hit cache
    time2 = time.time() - start

    print(f"   First call (DB): {time1:.4f}s")
    print(f"   Second call (Cache): {time2:.4f}s")
    print(f"   Speedup: {time1/time2:.1f}x")

    # Test 3: Property search
    print("\n3. Testing property search...")
    filters = {
        'county': 'PALM BEACH',
        'min_value': 500000,
        'max_value': 1000000,
        'property_use': 'RESIDENTIAL'
    }

    start = time.time()
    results1 = cache.search_properties(filters)
    time1 = time.time() - start

    start = time.time()
    results2 = cache.search_properties(filters)  # Should hit cache
    time2 = time.time() - start

    print(f"   First call (DB): {time1:.4f}s")
    print(f"   Second call (Cache): {time2:.4f}s")
    print(f"   Speedup: {time1/time2:.1f}x")

    # Display statistics
    print("\n4. Cache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n" + "="*60)
    print("CACHE IMPLEMENTATION TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_cache_implementation()