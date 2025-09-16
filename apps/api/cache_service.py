"""
Redis Caching Service for ConcordBroker
Provides intelligent caching for API responses and database queries
"""

import os
import json
import hashlib
import asyncio
from typing import Any, Optional, Union, Callable
from functools import wraps
from datetime import timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Async Redis cache service with fallback to in-memory cache"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.is_connected = False
        self._connect_task = None
        
    async def connect(self):
        """Connect to Redis with fallback to memory cache"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        try:
            self.redis_client = await redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("[OK] Connected to Redis cache")
        except (RedisError, ConnectionError) as e:
            logger.warning(f"[WARNING] Redis not available, using memory cache: {e}")
            self.is_connected = False
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.is_connected and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except (RedisError, json.JSONDecodeError) as e:
                logger.error(f"Cache get error: {e}")
        
        # Fallback to memory cache
        return self.memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL in seconds"""
        serialized = json.dumps(value, default=str)
        
        if self.is_connected and self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, serialized)
                return True
            except RedisError as e:
                logger.error(f"Cache set error: {e}")
        
        # Fallback to memory cache
        self.memory_cache[key] = value
        # Limit memory cache size
        if len(self.memory_cache) > 1000:
            # Remove oldest entries
            for _ in range(100):
                self.memory_cache.pop(next(iter(self.memory_cache)))
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if self.is_connected and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except RedisError as e:
                logger.error(f"Cache delete error: {e}")
        
        # Also remove from memory cache
        self.memory_cache.pop(key, None)
        return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        count = 0
        
        if self.is_connected and self.redis_client:
            try:
                async for key in self.redis_client.scan_iter(pattern):
                    await self.redis_client.delete(key)
                    count += 1
            except RedisError as e:
                logger.error(f"Cache clear pattern error: {e}")
        
        # Clear from memory cache
        keys_to_delete = [k for k in self.memory_cache if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1
        
        return count
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

# Global cache instance
cache = CacheService()

def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = f"{args}:{sorted(kwargs.items())}"
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(ttl: int = 300, prefix: str = "api"):
    """
    Decorator for caching async function results
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        prefix: Cache key prefix for namespacing
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache miss: {key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator

class CacheManager:
    """Advanced cache management with strategies"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        
    @cached(ttl=600, prefix="property")
    async def get_property(self, property_id: str) -> Optional[dict]:
        """Cache property data for 10 minutes"""
        # This will be wrapped and cached automatically
        pass
    
    @cached(ttl=1800, prefix="search")
    async def search_properties(self, filters: dict, page: int = 1) -> dict:
        """Cache search results for 30 minutes"""
        pass
    
    @cached(ttl=3600, prefix="sunbiz")
    async def get_sunbiz_entity(self, entity_id: str) -> Optional[dict]:
        """Cache Sunbiz data for 1 hour"""
        pass
    
    async def invalidate_property(self, property_id: str):
        """Invalidate all caches related to a property"""
        patterns = [
            f"property:*{property_id}*",
            f"search:*",  # Clear search results as property may appear there
        ]
        
        for pattern in patterns:
            await self.cache.clear_pattern(pattern)
    
    async def invalidate_search(self):
        """Invalidate all search caches"""
        await self.cache.clear_pattern("search:*")
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            "connected": self.cache.is_connected,
            "type": "redis" if self.cache.is_connected else "memory",
        }
        
        if self.cache.is_connected and self.cache.redis_client:
            try:
                info = await self.cache.redis_client.info()
                stats.update({
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_connections": info.get("total_connections_received", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": round(
                        info.get("keyspace_hits", 0) / 
                        max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1) * 100, 
                        2
                    )
                })
            except RedisError:
                pass
        else:
            stats["memory_cache_size"] = len(self.cache.memory_cache)
        
        return stats

# Specific cache strategies for different data types
class PropertyCache:
    """Specialized caching for property data"""
    
    @staticmethod
    async def cache_property_summary(property_id: str, data: dict):
        """Cache property summary with appropriate TTL"""
        key = f"property:summary:{property_id}"
        await cache.set(key, data, ttl=600)  # 10 minutes
    
    @staticmethod
    async def cache_property_details(property_id: str, data: dict):
        """Cache full property details"""
        key = f"property:details:{property_id}"
        await cache.set(key, data, ttl=1800)  # 30 minutes
    
    @staticmethod
    async def cache_property_history(property_id: str, data: list):
        """Cache property sales history"""
        key = f"property:history:{property_id}"
        await cache.set(key, data, ttl=3600)  # 1 hour
    
    @staticmethod
    async def get_property_summary(property_id: str) -> Optional[dict]:
        """Get cached property summary"""
        key = f"property:summary:{property_id}"
        return await cache.get(key)

class SearchCache:
    """Specialized caching for search results"""
    
    @staticmethod
    def get_search_key(filters: dict, page: int = 1, page_size: int = 20) -> str:
        """Generate consistent search cache key"""
        # Sort filters for consistent keys
        sorted_filters = sorted(filters.items())
        key_data = f"{sorted_filters}:{page}:{page_size}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"search:results:{key_hash}"
    
    @staticmethod
    async def cache_search_results(filters: dict, page: int, results: dict):
        """Cache search results"""
        key = SearchCache.get_search_key(filters, page)
        await cache.set(key, results, ttl=900)  # 15 minutes
    
    @staticmethod
    async def get_search_results(filters: dict, page: int) -> Optional[dict]:
        """Get cached search results"""
        key = SearchCache.get_search_key(filters, page)
        return await cache.get(key)

# Initialize cache on module import
async def init_cache():
    """Initialize cache connection"""
    await cache.connect()

# Export for use in other modules
__all__ = [
    'cache',
    'cached',
    'CacheManager',
    'PropertyCache',
    'SearchCache',
    'init_cache'
]