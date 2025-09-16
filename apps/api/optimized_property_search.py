"""
Optimized Property Search API with Caching and Performance Improvements
Uses Pandas for data manipulation, Redis for caching, and optimized queries
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from typing import List, Dict, Optional, Any
import orjson
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import redis
import hashlib
import pickle
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../../.env.new' if os.path.exists('../../.env.new') else '../../.env')

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import Supabase client
from supabase_client import get_supabase_client

# Initialize Redis Cloud for caching
try:
    # Try Redis Cloud first
    redis_client = redis.Redis(
        host=os.getenv('REDIS_CLOUD_HOST', 'redis-19041.c276.us-east-1-2.ec2.cloud.redislabs.com'),
        port=int(os.getenv('REDIS_CLOUD_PORT', 19041)),
        password=os.getenv('REDIS_CLOUD_PASSWORD', 'S12inci89ipk76sc3x8ce5cgs3wfpivjr9wbkjf8srvuj1hjqqk'),
        db=0,
        decode_responses=False,
        socket_connect_timeout=5,
        socket_timeout=5,
        ssl=True,
        ssl_cert_reqs=None
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("[SUCCESS] Connected to Redis Cloud (LangCache)")
except Exception as e:
    # Fallback to local Redis
    try:
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=False,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        redis_client.ping()
        REDIS_AVAILABLE = True
        print("[SUCCESS] Connected to local Redis")
    except:
        redis_client = None
        REDIS_AVAILABLE = False
        print(f"[INFO] Redis not available ({e}), using in-memory cache")

# In-memory cache fallback
memory_cache = {}
cache_timestamps = {}

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=4)

app = FastAPI(
    title="Optimized Property Search API",
    description="High-performance property search with caching",
    version="2.0.0",
    default_response_class=ORJSONResponse  # Faster JSON serialization
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase
try:
    supabase = get_supabase_client()
    print("[SUCCESS] Connected to Supabase")
except Exception as e:
    print(f"[ERROR] Failed to connect to Supabase: {e}")
    supabase = None

# Cache configuration
CACHE_TTL = 300  # 5 minutes
BATCH_SIZE = 1000  # Process in batches

def generate_cache_key(prefix: str, params: dict) -> str:
    """Generate a cache key from parameters"""
    param_str = orjson.dumps(params, option=orjson.OPT_SORT_KEYS)
    hash_digest = hashlib.md5(param_str).hexdigest()
    return f"{prefix}:{hash_digest}"

def get_from_cache(key: str) -> Optional[Any]:
    """Get data from cache (Redis or memory)"""
    if REDIS_AVAILABLE and redis_client:
        try:
            data = redis_client.get(key)
            if data:
                return pickle.loads(data)
        except:
            pass

    # Fallback to memory cache
    if key in memory_cache:
        timestamp = cache_timestamps.get(key, 0)
        if datetime.now().timestamp() - timestamp < CACHE_TTL:
            return memory_cache[key]
        else:
            # Clean expired cache
            del memory_cache[key]
            del cache_timestamps[key]
    return None

def set_cache(key: str, value: Any, ttl: int = CACHE_TTL):
    """Set data in cache"""
    if REDIS_AVAILABLE and redis_client:
        try:
            redis_client.setex(key, ttl, pickle.dumps(value))
        except:
            pass

    # Also set in memory cache as backup
    memory_cache[key] = value
    cache_timestamps[key] = datetime.now().timestamp()

    # Clean old entries if memory cache gets too large
    if len(memory_cache) > 100:
        # Remove oldest entries
        sorted_keys = sorted(cache_timestamps.items(), key=lambda x: x[1])
        for old_key, _ in sorted_keys[:20]:
            if old_key in memory_cache:
                del memory_cache[old_key]
            if old_key in cache_timestamps:
                del cache_timestamps[old_key]

def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame memory usage"""
    for col in df.columns:
        col_type = df[col].dtype

        if col_type != 'object':
            if col_type == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')
            elif col_type == 'int64':
                df[col] = pd.to_numeric(df[col], downcast='integer')

    # Convert object columns to category if they have low cardinality
    for col in df.select_dtypes(['object']).columns:
        num_unique_values = len(df[col].unique())
        num_total_values = len(df[col])
        if num_unique_values / num_total_values < 0.5:
            df[col] = df[col].astype('category')

    return df

async def fetch_properties_batch(query_params: dict) -> pd.DataFrame:
    """Fetch properties in batches for better performance"""
    all_data = []
    offset = query_params.get('offset', 0)
    limit = query_params.get('limit', 100)

    # Build base query
    query = supabase.table('florida_parcels').select('*')

    # Apply filters
    if query_params.get('city'):
        query = query.ilike('phy_city', f"%{query_params['city']}%")
    if query_params.get('address'):
        query = query.ilike('phy_addr1', f"%{query_params['address']}%")
    if query_params.get('owner'):
        query = query.ilike('own_name', f"%{query_params['owner']}%")
    if query_params.get('min_value'):
        query = query.gte('just_value', query_params['min_value'])
    if query_params.get('max_value'):
        query = query.lte('just_value', query_params['max_value'])

    # Execute query with pagination
    query = query.range(offset, offset + limit - 1)
    result = await asyncio.get_event_loop().run_in_executor(
        executor, lambda: query.execute()
    )

    if result.data:
        df = pd.DataFrame(result.data)
        df = optimize_dataframe(df)
        return df

    return pd.DataFrame()

@app.get("/api/optimized/search")
async def optimized_search(
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0)
):
    """Optimized property search with caching and parallel processing"""

    # Build query parameters
    query_params = {
        'address': address,
        'city': city,
        'zip_code': zip_code,
        'owner': owner,
        'min_value': min_value,
        'max_value': max_value,
        'limit': limit,
        'offset': offset
    }

    # Remove None values
    query_params = {k: v for k, v in query_params.items() if v is not None}

    # Check cache
    cache_key = generate_cache_key("search", query_params)
    cached_result = get_from_cache(cache_key)

    if cached_result:
        return ORJSONResponse(content=cached_result)

    try:
        # Fetch data using optimized batch processing
        df = await fetch_properties_batch(query_params)

        if df.empty:
            result = {"properties": [], "total": 0, "cached": False}
        else:
            # Process with Pandas for speed
            # Convert to dict format optimized for JSON
            properties = df.to_dict('records')

            # Clean NaN values
            for prop in properties:
                for key, value in prop.items():
                    if pd.isna(value):
                        prop[key] = None

            result = {
                "properties": properties,
                "total": len(properties),
                "cached": False
            }

        # Cache the result
        set_cache(cache_key, result)

        return ORJSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/optimized/autocomplete")
async def optimized_autocomplete(
    field: str = Query(..., description="Field to autocomplete (address, city, owner)"),
    q: str = Query(..., description="Query string"),
    limit: int = Query(10)
):
    """Fast autocomplete with caching"""

    cache_key = generate_cache_key(f"autocomplete_{field}", {"q": q, "limit": limit})
    cached_result = get_from_cache(cache_key)

    if cached_result:
        return ORJSONResponse(content=cached_result)

    try:
        # Map field names to database columns
        field_map = {
            'address': 'phy_addr1',
            'city': 'phy_city',
            'owner': 'own_name'
        }

        db_field = field_map.get(field)
        if not db_field:
            raise HTTPException(status_code=400, detail="Invalid field")

        # Use database function for faster distinct values
        query = supabase.table('florida_parcels').select(db_field)
        query = query.ilike(db_field, f"{q}%")
        query = query.limit(limit * 3)  # Get more to ensure enough unique values

        result = await asyncio.get_event_loop().run_in_executor(
            executor, lambda: query.execute()
        )

        if result.data:
            df = pd.DataFrame(result.data)
            unique_values = df[db_field].dropna().unique()[:limit].tolist()
            suggestions = [{"value": v, "label": v} for v in unique_values]
        else:
            suggestions = []

        result = {"suggestions": suggestions}
        set_cache(cache_key, result, ttl=60)  # Shorter TTL for autocomplete

        return ORJSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/optimized/stats")
async def get_stats():
    """Get cache statistics and performance metrics"""
    stats = {
        "cache_type": "Redis" if REDIS_AVAILABLE else "Memory",
        "memory_cache_size": len(memory_cache),
        "redis_available": REDIS_AVAILABLE,
        "database_connected": supabase is not None
    }

    if REDIS_AVAILABLE and redis_client:
        try:
            info = redis_client.info()
            stats["redis_used_memory"] = info.get("used_memory_human", "N/A")
            stats["redis_connected_clients"] = info.get("connected_clients", 0)
        except:
            pass

    return stats

@app.post("/api/optimized/clear-cache")
async def clear_cache():
    """Clear all caches"""
    # Clear Redis cache
    if REDIS_AVAILABLE and redis_client:
        try:
            redis_client.flushdb()
        except:
            pass

    # Clear memory cache
    memory_cache.clear()
    cache_timestamps.clear()

    return {"status": "Cache cleared"}

@app.get("/api/optimized/prefetch")
async def prefetch_common_queries():
    """Prefetch common queries to warm up cache"""
    common_cities = ["Fort Lauderdale", "Hollywood", "Pompano Beach", "Coral Springs"]

    tasks = []
    for city in common_cities:
        query_params = {'city': city, 'limit': 100, 'offset': 0}
        tasks.append(fetch_properties_batch(query_params))

    results = await asyncio.gather(*tasks)

    # Cache results
    for city, df in zip(common_cities, results):
        if not df.empty:
            properties = df.to_dict('records')
            result = {"properties": properties, "total": len(properties), "cached": False}
            cache_key = generate_cache_key("search", {'city': city, 'limit': 100, 'offset': 0})
            set_cache(cache_key, result)

    return {"status": "Prefetch complete", "cities": common_cities}

@app.on_event("startup")
async def startup_event():
    """Warm up cache on startup"""
    print("Warming up cache...")
    try:
        await prefetch_common_queries()
        print("Cache warmed up successfully")
    except Exception as e:
        print(f"Failed to warm up cache: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)