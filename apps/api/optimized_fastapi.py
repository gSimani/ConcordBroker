"""
Optimized FastAPI Backend with Redis Caching and Pandas Processing
Significantly improves data loading speed from Supabase
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import redis
import json
import hashlib
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pickle
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# FastAPI app
app = FastAPI(title="ConcordBroker Optimized API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5176", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Redis configuration
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=False,  # We'll handle encoding/decoding
        socket_connect_timeout=5
    )
    redis_client.ping()
    REDIS_ENABLED = True
    print("Redis connected successfully")
except:
    REDIS_ENABLED = False
    print("Redis not available - using in-memory cache")

# In-memory cache fallback
memory_cache = {}

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=4)

class PropertyOptimizer:
    """Optimizes property data handling using Pandas"""

    def __init__(self):
        self.df_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def get_cache_key(self, query_params: dict) -> str:
        """Generate unique cache key from query parameters"""
        key_str = json.dumps(query_params, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def cache_set(self, key: str, data: Any, ttl: int = 300):
        """Set cache with Redis or memory fallback"""
        if REDIS_ENABLED:
            try:
                # Serialize with pickle for complex data structures
                redis_client.setex(
                    f"property:{key}",
                    ttl,
                    pickle.dumps(data)
                )
            except Exception as e:
                print(f"Redis cache error: {e}")
                memory_cache[key] = (data, datetime.now() + timedelta(seconds=ttl))
        else:
            memory_cache[key] = (data, datetime.now() + timedelta(seconds=ttl))

    def cache_get(self, key: str) -> Optional[Any]:
        """Get from cache with Redis or memory fallback"""
        if REDIS_ENABLED:
            try:
                data = redis_client.get(f"property:{key}")
                if data:
                    return pickle.loads(data)
            except Exception as e:
                print(f"Redis get error: {e}")

        # Check memory cache
        if key in memory_cache:
            data, expiry = memory_cache[key]
            if datetime.now() < expiry:
                return data
            else:
                del memory_cache[key]
        return None

    async def fetch_properties_optimized(
        self,
        county: str = "BROWARD",
        city: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Fetch properties with caching and optimization"""

        # Check cache first
        cache_key = self.get_cache_key({
            'county': county,
            'city': city,
            'limit': limit,
            'offset': offset
        })

        cached_result = self.cache_get(cache_key)
        if cached_result:
            print(f"Cache hit for key: {cache_key}")
            return cached_result

        print(f"Cache miss - fetching from database")

        # Build optimized query
        query = supabase.table('florida_parcels').select(
            'parcel_id,owner_name,phy_addr1,phy_city,phy_zipcd,'
            'taxable_value,just_value,land_value,year_built,sale_price,sale_date'
        )

        if county:
            query = query.eq('county', county.upper())
        if city:
            query = query.ilike('phy_city', f'%{city}%')

        # Get count efficiently
        count_query = query
        count_result = count_query.execute()
        total_count = len(count_result.data) if count_result.data else 0

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        # Execute query
        result = query.execute()

        # Process with Pandas for better performance
        if result.data:
            df = pd.DataFrame(result.data)

            # Optimize data types
            numeric_columns = ['taxable_value', 'just_value', 'land_value', 'sale_price']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Format for frontend
            properties = df.to_dict('records')
        else:
            properties = []

        response = {
            'properties': properties,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'cached': False
        }

        # Cache the result
        self.cache_set(cache_key, response, ttl=300)

        return response

    async def search_properties_parallel(
        self,
        search_term: str,
        counties: List[str] = ["BROWARD"],
        limit: int = 50
    ) -> Dict[str, Any]:
        """Parallel search across multiple counties"""

        async def search_county(county: str):
            query = supabase.table('florida_parcels').select(
                'parcel_id,owner_name,phy_addr1,phy_city,phy_zipcd,taxable_value'
            ).eq('county', county)

            # Search in multiple fields
            search_query = f"%{search_term}%"
            query = query.or_(
                f"phy_addr1.ilike.{search_query},"
                f"owner_name.ilike.{search_query},"
                f"phy_city.ilike.{search_query}"
            ).limit(limit)

            return query.execute()

        # Execute searches in parallel
        tasks = [search_county(county) for county in counties]
        results = await asyncio.gather(*tasks)

        # Combine results
        all_properties = []
        for result in results:
            if result.data:
                all_properties.extend(result.data)

        return {
            'properties': all_properties[:limit],
            'total': len(all_properties),
            'searched_counties': counties
        }

# Initialize optimizer
optimizer = PropertyOptimizer()

@app.on_event("startup")
async def startup_event():
    """Preload frequently accessed data"""
    print("Starting optimized API server...")

    # Preload Broward County data
    await optimizer.fetch_properties_optimized(
        county="BROWARD",
        limit=100,
        offset=0
    )
    print("Preloaded initial data")

@app.get("/")
async def root():
    return {
        "message": "ConcordBroker Optimized API",
        "redis": REDIS_ENABLED,
        "endpoints": {
            "properties": "/api/properties",
            "search": "/api/search",
            "stats": "/api/stats"
        }
    }

@app.get("/api/properties")
async def get_properties(
    county: str = Query("BROWARD"),
    city: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0)
):
    """Get properties with caching and optimization"""
    try:
        result = await optimizer.fetch_properties_optimized(
            county=county,
            city=city,
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search")
async def search_properties(
    q: str = Query(..., min_length=2),
    counties: Optional[str] = Query("BROWARD"),
    limit: int = Query(50, le=200)
):
    """Fast parallel search across counties"""
    try:
        county_list = counties.split(",") if counties else ["BROWARD"]
        result = await optimizer.search_properties_parallel(
            search_term=q,
            counties=county_list,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(county: str = Query("BROWARD")):
    """Get cached statistics for a county"""

    cache_key = f"stats_{county}"
    cached = optimizer.cache_get(cache_key)

    if cached:
        return cached

    # Calculate stats using Pandas
    query = supabase.table('florida_parcels').select(
        'taxable_value,just_value,sale_price,year_built'
    ).eq('county', county).limit(10000)

    result = query.execute()

    if result.data:
        df = pd.DataFrame(result.data)

        # Convert to numeric
        df['taxable_value'] = pd.to_numeric(df['taxable_value'], errors='coerce')
        df['just_value'] = pd.to_numeric(df['just_value'], errors='coerce')
        df['sale_price'] = pd.to_numeric(df['sale_price'], errors='coerce')

        stats = {
            'county': county,
            'total_properties': len(df),
            'avg_taxable_value': float(df['taxable_value'].mean()),
            'median_taxable_value': float(df['taxable_value'].median()),
            'total_market_value': float(df['just_value'].sum()),
            'properties_with_sales': int((df['sale_price'] > 0).sum()),
            'avg_sale_price': float(df[df['sale_price'] > 0]['sale_price'].mean()) if any(df['sale_price'] > 0) else 0
        }

        # Cache for 1 hour
        optimizer.cache_set(cache_key, stats, ttl=3600)

        return stats

    return {'error': 'No data available'}

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all caches"""
    if REDIS_ENABLED:
        redis_client.flushdb()
    memory_cache.clear()
    return {"message": "Cache cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)