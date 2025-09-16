"""
Ultra-Fast Property API with Multiple Optimization Strategies
"""

from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import redis
import json
import pickle
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import asyncpg
import orjson  # Faster JSON serialization
import logging
from functools import lru_cache
import msgpack  # Even faster serialization for cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ConcordBroker Ultra-Fast API",
    description="Optimized property search with caching and parallel processing",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connections
redis_pool = None
db_pool = None
thread_executor = ThreadPoolExecutor(max_workers=10)

# In-memory cache for hot data
memory_cache = {}
cache_timestamps = {}

@app.on_event("startup")
async def startup_event():
    """Initialize all connections and preload data"""
    global redis_pool, db_pool

    # Initialize Redis connection pool
    redis_pool = redis.ConnectionPool(
        host='localhost',
        port=6379,
        db=0,
        max_connections=50,
        socket_connect_timeout=5,
        socket_timeout=5
    )

    # Initialize PostgreSQL connection pool
    db_pool = await asyncpg.create_pool(
        host="aws-0-us-east-1.pooler.supabase.com",
        port=6543,
        user="postgres.pmispwtdngkcmsrsjwbp",
        password="vM4g2024$$Florida1",
        database="postgres",
        min_size=10,
        max_size=20,
        command_timeout=60
    )

    # Preload hot data
    await preload_hot_data()

    # Start background cache warming
    asyncio.create_task(warm_cache_periodically())

    logger.info("Fast API initialized with all optimizations")

async def preload_hot_data():
    """Preload frequently accessed data into memory"""
    async with db_pool.acquire() as conn:
        # Load top cities
        cities = await conn.fetch("""
            SELECT phy_city, COUNT(*) as count
            FROM florida_parcels
            WHERE phy_city IS NOT NULL
            GROUP BY phy_city
            ORDER BY count DESC
            LIMIT 100
        """)
        memory_cache['top_cities'] = [dict(city) for city in cities]

        # Load property type distribution
        property_types = await conn.fetch("""
            SELECT dor_uc, COUNT(*) as count
            FROM florida_parcels
            WHERE dor_uc IS NOT NULL
            GROUP BY dor_uc
            ORDER BY count DESC
            LIMIT 50
        """)
        memory_cache['property_types'] = [dict(pt) for pt in property_types]

        # Load price ranges for quick filtering
        price_stats = await conn.fetchrow("""
            SELECT
                MIN(jv) as min_price,
                MAX(jv) as max_price,
                AVG(jv) as avg_price,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY jv) as q1,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY jv) as median,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY jv) as q3
            FROM florida_parcels
            WHERE jv > 0
        """)
        memory_cache['price_stats'] = dict(price_stats)

        logger.info("Hot data preloaded into memory cache")

async def warm_cache_periodically():
    """Background task to warm cache with common queries"""
    while True:
        try:
            # Wait 5 minutes between cache warming
            await asyncio.sleep(300)

            # Warm cache with common queries
            common_filters = [
                {'city': 'MIAMI'},
                {'city': 'ORLANDO'},
                {'city': 'TAMPA'},
                {'minValue': 100000, 'maxValue': 500000},
                {'propertyType': 'single_family'},
            ]

            for filters in common_filters:
                cache_key = generate_cache_key(filters, 1, 100)
                if not check_memory_cache(cache_key):
                    # Execute query in background
                    asyncio.create_task(
                        search_properties_internal(filters, 1, 100, cache_only=True)
                    )

            logger.info("Cache warming completed")

        except Exception as e:
            logger.error(f"Cache warming error: {e}")

def generate_cache_key(filters: Dict, page: int, limit: int) -> str:
    """Generate deterministic cache key"""
    key_data = {**filters, 'page': page, 'limit': limit}
    key_str = json.dumps(key_data, sort_keys=True)
    return f"search:{hashlib.md5(key_str.encode()).hexdigest()}"

def check_memory_cache(key: str, ttl: int = 300) -> Optional[Any]:
    """Check in-memory cache with TTL"""
    if key in memory_cache:
        timestamp = cache_timestamps.get(key, 0)
        if datetime.now().timestamp() - timestamp < ttl:
            return memory_cache[key]
        else:
            # Expired
            del memory_cache[key]
            del cache_timestamps[key]
    return None

def set_memory_cache(key: str, value: Any):
    """Set in-memory cache"""
    memory_cache[key] = value
    cache_timestamps[key] = datetime.now().timestamp()

    # Limit memory cache size
    if len(memory_cache) > 1000:
        # Remove oldest entries
        oldest_keys = sorted(cache_timestamps.keys(),
                           key=lambda k: cache_timestamps[k])[:100]
        for k in oldest_keys:
            del memory_cache[k]
            del cache_timestamps[k]

async def get_redis_cache(key: str) -> Optional[Dict]:
    """Get from Redis cache"""
    try:
        r = redis.Redis(connection_pool=redis_pool)
        data = r.get(key)
        if data:
            return msgpack.unpackb(data, raw=False)
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
    return None

async def set_redis_cache(key: str, value: Dict, ttl: int = 3600):
    """Set Redis cache with TTL"""
    try:
        r = redis.Redis(connection_pool=redis_pool)
        packed = msgpack.packb(value)
        r.setex(key, ttl, packed)
    except Exception as e:
        logger.warning(f"Redis set error: {e}")

@app.get("/api/properties/search")
async def search_properties(
    background_tasks: BackgroundTasks,
    q: Optional[str] = Query(None),
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    minValue: Optional[float] = Query(None),
    maxValue: Optional[float] = Query(None),
    minYear: Optional[int] = Query(None),
    maxYear: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000)
):
    """Ultra-fast property search with multiple caching layers"""

    start_time = datetime.now()

    # Build filters dict
    filters = {}
    if q: filters['q'] = q
    if address: filters['address'] = address
    if city: filters['city'] = city
    if zipCode: filters['zipCode'] = zipCode
    if owner: filters['owner'] = owner
    if propertyType: filters['propertyType'] = propertyType
    if minValue: filters['minValue'] = minValue
    if maxValue: filters['maxValue'] = maxValue
    if minYear: filters['minYear'] = minYear
    if maxYear: filters['maxYear'] = maxYear

    # Check memory cache first (fastest)
    cache_key = generate_cache_key(filters, page, limit)
    cached = check_memory_cache(cache_key)
    if cached:
        cached['cache_hit'] = 'memory'
        cached['response_time_ms'] = 0
        return JSONResponse(content=cached, media_type="application/json")

    # Check Redis cache (fast)
    cached = await get_redis_cache(cache_key)
    if cached:
        # Also store in memory for next time
        set_memory_cache(cache_key, cached)
        cached['cache_hit'] = 'redis'
        cached['response_time_ms'] = int((datetime.now() - start_time).total_seconds() * 1000)
        return JSONResponse(content=cached, media_type="application/json")

    # Execute optimized search
    result = await search_properties_internal(filters, page, limit)

    # Calculate response time
    response_time = (datetime.now() - start_time).total_seconds() * 1000
    result['response_time_ms'] = int(response_time)
    result['cache_hit'] = 'none'

    # Cache results in background
    background_tasks.add_task(cache_results, cache_key, result)

    return JSONResponse(content=result, media_type="application/json")

async def search_properties_internal(filters: Dict,
                                    page: int,
                                    limit: int,
                                    cache_only: bool = False) -> Dict:
    """Internal search implementation with query optimization"""

    offset = (page - 1) * limit

    # Build optimized query
    query = """
        SELECT
            parcel_id,
            phy_addr1,
            phy_city,
            phy_state,
            phy_zipcd,
            owner_name,
            owner_addr1,
            dor_uc,
            yr_blt,
            bedroom_cnt,
            bathroom_cnt,
            tot_lvg_area,
            lnd_sqfoot,
            jv,
            av_sd,
            tv_sd,
            sale_prc1,
            sale_yr1
        FROM florida_parcels
        WHERE 1=1
    """

    params = []
    param_count = 0

    # Add filters
    if filters.get('q'):
        param_count += 1
        search_term = f"%{filters['q']}%"
        query += f"""
            AND (
                phy_addr1 ILIKE ${param_count} OR
                phy_city ILIKE ${param_count} OR
                owner_name ILIKE ${param_count}
            )
        """
        params.append(search_term)

    if filters.get('city'):
        param_count += 1
        query += f" AND phy_city ILIKE ${param_count}"
        params.append(f"%{filters['city']}%")

    if filters.get('zipCode'):
        param_count += 1
        query += f" AND phy_zipcd = ${param_count}"
        params.append(filters['zipCode'])

    if filters.get('owner'):
        param_count += 1
        query += f" AND owner_name ILIKE ${param_count}"
        params.append(f"%{filters['owner']}%")

    if filters.get('minValue'):
        param_count += 1
        query += f" AND jv >= ${param_count}"
        params.append(filters['minValue'])

    if filters.get('maxValue'):
        param_count += 1
        query += f" AND jv <= ${param_count}"
        params.append(filters['maxValue'])

    if filters.get('propertyType'):
        codes = get_property_codes(filters['propertyType'])
        if codes:
            param_count += 1
            query += f" AND dor_uc = ANY(${param_count})"
            params.append(codes)

    # Add ordering and pagination
    query += f"""
        ORDER BY jv DESC NULLS LAST
        LIMIT {limit}
        OFFSET {offset}
    """

    # Execute query
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

        # Get approximate count for pagination
        count_query = "SELECT COUNT(*) FILTER (WHERE jv > 0) as count FROM florida_parcels"
        count_result = await conn.fetchrow(count_query)
        total_count = count_result['count'] if count_result else 0

    # Convert to list of dicts and enhance
    properties = []
    for row in rows:
        prop = dict(row)

        # Calculate investment metrics using NumPy for batch operations
        jv = float(prop.get('jv', 0) or 0)
        av_sd = float(prop.get('av_sd', 0) or 0)
        tot_lvg_area = float(prop.get('tot_lvg_area', 0) or 0)

        # Investment score
        score = 50.0
        if jv > 0:
            if jv < av_sd:
                score += 10
            if jv < 100000:
                score += 5
            if tot_lvg_area > 1500:
                score += 5

        prop['investment_score'] = min(100, max(0, score))

        # Price per sqft
        prop['price_per_sqft'] = jv / tot_lvg_area if tot_lvg_area > 0 else 0

        # Cap rate
        if jv > 0:
            estimated_rent = jv * 0.01 * 12
            net_income = estimated_rent * 0.7
            prop['cap_rate'] = (net_income / jv) * 100
        else:
            prop['cap_rate'] = 0

        properties.append(prop)

    result = {
        'success': True,
        'data': properties,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': min(total_count, 10000),  # Cap for performance
            'pages': min((total_count + limit - 1) // limit, 100)
        },
        'timestamp': datetime.now().isoformat()
    }

    if cache_only:
        # Store in cache but don't return
        await cache_results(generate_cache_key(filters, page, limit), result)

    return result

async def cache_results(cache_key: str, result: Dict):
    """Cache results in both memory and Redis"""
    # Memory cache
    set_memory_cache(cache_key, result)

    # Redis cache
    await set_redis_cache(cache_key, result, ttl=3600)

def get_property_codes(property_type: str) -> List[str]:
    """Map property type to codes"""
    mapping = {
        'single_family': ['0100', '0101', '0102', '0103'],
        'multi_family': ['0200', '0201', '0202'],
        'commercial': ['1000', '1100', '1200'],
        'industrial': ['4000', '4100', '4200'],
        'agricultural': ['5000', '5100', '5200'],
        'vacant': ['0000', '0001']
    }
    return mapping.get(property_type, [])

@app.get("/api/properties/{property_id}")
async def get_property_details(property_id: str):
    """Get property details with caching"""

    # Check memory cache
    cache_key = f"property:{property_id}"
    cached = check_memory_cache(cache_key, ttl=1800)
    if cached:
        return JSONResponse(content=cached)

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM florida_parcels
            WHERE parcel_id = $1
            LIMIT 1
        """, property_id)

        if not row:
            raise HTTPException(status_code=404, detail="Property not found")

        property_details = dict(row)

        # Get related data in parallel
        tax_certs_task = conn.fetch("""
            SELECT * FROM tax_certificates
            WHERE parcel_id = $1
            ORDER BY certificate_year DESC
            LIMIT 10
        """, property_id)

        sales_history_task = conn.fetch("""
            SELECT * FROM sales_history
            WHERE parcel_id = $1
            ORDER BY sale_date DESC
            LIMIT 20
        """, property_id)

        tax_certs, sales_history = await asyncio.gather(
            tax_certs_task,
            sales_history_task,
            return_exceptions=True
        )

        # Add to property details
        property_details['tax_certificates'] = [dict(tc) for tc in tax_certs] if not isinstance(tax_certs, Exception) else []
        property_details['sales_history'] = [dict(sh) for sh in sales_history] if not isinstance(sales_history, Exception) else []

    result = {
        'success': True,
        'data': property_details,
        'timestamp': datetime.now().isoformat()
    }

    # Cache result
    set_memory_cache(cache_key, result)

    return JSONResponse(content=result)

@app.get("/api/properties/autocomplete")
async def autocomplete(
    field: str = Query(..., description="Field to autocomplete (city, address, owner)"),
    q: str = Query(..., min_length=2, description="Search query")
):
    """Fast autocomplete using cached data"""

    # Check memory cache for common queries
    cache_key = f"autocomplete:{field}:{q[:3]}"  # Cache by first 3 chars
    cached = check_memory_cache(cache_key, ttl=600)
    if cached:
        return JSONResponse(content=cached)

    async with db_pool.acquire() as conn:
        if field == 'city':
            query = """
                SELECT DISTINCT phy_city as value, COUNT(*) as count
                FROM florida_parcels
                WHERE phy_city ILIKE $1
                GROUP BY phy_city
                ORDER BY count DESC
                LIMIT 10
            """
        elif field == 'address':
            query = """
                SELECT DISTINCT phy_addr1 as value
                FROM florida_parcels
                WHERE phy_addr1 ILIKE $1
                LIMIT 10
            """
        elif field == 'owner':
            query = """
                SELECT DISTINCT owner_name as value, COUNT(*) as count
                FROM florida_parcels
                WHERE owner_name ILIKE $1
                GROUP BY owner_name
                ORDER BY count DESC
                LIMIT 10
            """
        else:
            raise HTTPException(status_code=400, detail="Invalid field")

        rows = await conn.fetch(query, f"{q}%")
        suggestions = [dict(row) for row in rows]

    result = {
        'success': True,
        'suggestions': suggestions
    }

    # Cache result
    set_memory_cache(cache_key, result)

    return JSONResponse(content=result)

@app.get("/")
async def health_check():
    """Health check with performance stats"""
    return {
        'status': 'healthy',
        'service': 'ConcordBroker Fast API',
        'cache_stats': {
            'memory_entries': len(memory_cache),
            'memory_size_kb': sum(len(str(v)) for v in memory_cache.values()) / 1024
        },
        'pool_stats': {
            'db_connections': db_pool.get_size() if db_pool else 0,
            'db_idle': db_pool.get_idle_size() if db_pool else 0
        },
        'timestamp': datetime.now().isoformat()
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if db_pool:
        await db_pool.close()
    thread_executor.shutdown(wait=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, workers=4)