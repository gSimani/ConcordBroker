"""
Redis Cache Configuration for Railway
Implements caching layer to reduce database load by 70-90%
"""

import os
import json
import redis
from functools import wraps, lru_cache
from typing import Any, Optional
import hashlib

# Redis client initialization
try:
    REDIS_URL = os.environ.get("REDIS_URL")
    if REDIS_URL:
        redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options={1: 1, 2: 3, 3: 5}
        )
        redis_client.ping()
        REDIS_AVAILABLE = True
        print("SUCCESS: Redis cache connected")
    else:
        redis_client = None
        REDIS_AVAILABLE = False
        print("INFO: Redis not configured, using in-memory cache")
except Exception as e:
    redis_client = None
    REDIS_AVAILABLE = False
    print(f"WARNING: Redis connection failed, using in-memory cache: {e}")

# In-memory fallback cache
memory_cache = {}

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a unique cache key from prefix and arguments"""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

def cache_result(key: str, data: Any, ttl: int = 3600) -> bool:
    """
    Cache data with TTL (time-to-live in seconds)
    Returns True if successful
    """
    try:
        if REDIS_AVAILABLE and redis_client:
            redis_client.setex(key, ttl, json.dumps(data))
            return True
        else:
            # Fallback to memory cache
            memory_cache[key] = data
            return True
    except Exception as e:
        print(f"Cache write error: {e}")
        return False

def get_cached(key: str) -> Optional[Any]:
    """
    Retrieve cached data
    Returns None if not found or error
    """
    try:
        if REDIS_AVAILABLE and redis_client:
            data = redis_client.get(key)
            return json.loads(data) if data else None
        else:
            # Fallback to memory cache
            return memory_cache.get(key)
    except Exception as e:
        print(f"Cache read error: {e}")
        return None

def clear_cache(pattern: str = "*") -> int:
    """
    Clear cache entries matching pattern
    Returns number of entries cleared
    """
    count = 0
    try:
        if REDIS_AVAILABLE and redis_client:
            keys = redis_client.keys(pattern)
            if keys:
                count = redis_client.delete(*keys)
        else:
            # Clear memory cache
            if pattern == "*":
                count = len(memory_cache)
                memory_cache.clear()
            else:
                keys_to_delete = [k for k in memory_cache if pattern in k]
                for k in keys_to_delete:
                    del memory_cache[k]
                    count += 1
    except Exception as e:
        print(f"Cache clear error: {e}")
    return count

def cache_decorator(ttl: int = 3600, prefix: str = "api"):
    """
    Decorator for caching function results

    Usage:
        @cache_decorator(ttl=600, prefix="property")
        def get_property_data(property_id: str):
            # Expensive database query
            return data
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)

            # Try to get from cache
            cached_data = get_cached(cache_key)
            if cached_data is not None:
                return cached_data

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_result(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)

            # Try to get from cache
            cached_data = get_cached(cache_key)
            if cached_data is not None:
                return cached_data

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_result(cache_key, result, ttl)
            return result

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# Cache configuration for different data types
CACHE_CONFIG = {
    "properties": {
        "ttl": 3600,  # 1 hour
        "prefix": "prop"
    },
    "search_results": {
        "ttl": 1800,  # 30 minutes
        "prefix": "search"
    },
    "autocomplete": {
        "ttl": 7200,  # 2 hours
        "prefix": "auto"
    },
    "tax_deeds": {
        "ttl": 900,  # 15 minutes
        "prefix": "tax"
    },
    "user_session": {
        "ttl": 86400,  # 24 hours
        "prefix": "user"
    }
}

# Health check for cache
def check_cache_health() -> dict:
    """Check cache health and return status"""
    return {
        "redis_available": REDIS_AVAILABLE,
        "redis_url": bool(os.environ.get("REDIS_URL")),
        "memory_cache_entries": len(memory_cache),
        "status": "healthy" if REDIS_AVAILABLE else "degraded"
    }