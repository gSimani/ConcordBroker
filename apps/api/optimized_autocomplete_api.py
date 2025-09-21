"""
Ultra-optimized autocomplete API with local caching and smart querying
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import asyncio
from supabase import create_client
import os
from datetime import datetime
import time
from collections import defaultdict
import re

app = FastAPI(title="Optimized Autocomplete API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# In-memory cache for ultra-fast responses
class AutocompleteCache:
    def __init__(self):
        self.address_cache = {}  # prefix -> list of results
        self.city_cache = {}
        self.owner_cache = {}
        self.last_refresh = None
        self.preloaded_data = []

    async def preload_common_data(self):
        """Preload common searches into memory"""
        print("Preloading common data into memory...")

        # Load top cities
        cities = ["MIAMI", "FORT LAUDERDALE", "HOLLYWOOD", "DAVIE", "PEMBROKE PINES",
                  "CORAL SPRINGS", "MIRAMAR", "PLANTATION", "SUNRISE", "WESTON",
                  "BOCA RATON", "DELRAY BEACH", "TAMPA", "ORLANDO", "JACKSONVILLE"]

        for city in cities:
            try:
                result = supabase.table('florida_parcels') \
                    .select('phy_addr1,phy_city,phy_zipcd,owner_name') \
                    .ilike('phy_city', f'{city}%') \
                    .limit(50) \
                    .execute()

                self.city_cache[city.upper()] = [
                    {
                        'address': row['phy_addr1'],
                        'city': row['phy_city'],
                        'zip_code': row['phy_zipcd'],
                        'owner': row['owner_name']
                    }
                    for row in result.data[:20]
                ]
                print(f"  Cached {len(self.city_cache[city.upper()])} results for {city}")
            except:
                pass

        # Load common address prefixes
        prefixes = ["100", "200", "300", "400", "500", "1000", "2000", "3000", "4000", "5000"]

        for prefix in prefixes:
            try:
                # Use starts with for addresses (more efficient)
                result = supabase.table('florida_parcels') \
                    .select('phy_addr1,phy_city,phy_zipcd,owner_name') \
                    .filter('phy_addr1', 'gte', prefix) \
                    .filter('phy_addr1', 'lt', prefix + 'Z') \
                    .limit(30) \
                    .execute()

                self.address_cache[prefix] = [
                    {
                        'address': row['phy_addr1'],
                        'city': row['phy_city'],
                        'zip_code': row['phy_zipcd'],
                        'owner': row['owner_name']
                    }
                    for row in result.data[:20]
                ]
                print(f"  Cached {len(self.address_cache[prefix])} results for prefix {prefix}")
            except:
                pass

        self.last_refresh = datetime.now()
        print("Cache preloading complete!")

cache = AutocompleteCache()

@app.on_event("startup")
async def startup():
    """Initialize cache on startup"""
    await cache.preload_common_data()

@app.get("/")
async def root():
    return {
        "service": "Optimized Autocomplete API",
        "status": "running",
        "cache_size": len(cache.address_cache) + len(cache.city_cache),
        "endpoints": [
            "/api/autocomplete",
            "/api/autocomplete/fast"
        ]
    }

@app.get("/api/autocomplete")
async def autocomplete(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """Smart autocomplete that works with addresses, cities, and owners"""

    start_time = time.time()
    query = q.upper().strip()

    # Quick return for short queries
    if len(query) < 2:
        return {"success": True, "data": [], "cached": True, "time_ms": 0}

    results = []

    # Check if it's a number (address search)
    if query[0].isdigit():
        # Check cache first
        for prefix, cached_results in cache.address_cache.items():
            if query.startswith(prefix):
                results = [r for r in cached_results if r['address'].startswith(query)][:limit]
                if results:
                    return {
                        "success": True,
                        "data": format_results(results),
                        "cached": True,
                        "time_ms": int((time.time() - start_time) * 1000)
                    }

        # If not in cache, do a smart database query
        try:
            # Use a more efficient query pattern
            result = supabase.table('florida_parcels') \
                .select('phy_addr1,phy_city,phy_zipcd,owner_name') \
                .filter('phy_addr1', 'gte', query) \
                .filter('phy_addr1', 'lt', query + 'Z') \
                .limit(limit * 2) \
                .execute()

            results = [
                {
                    'address': row['phy_addr1'],
                    'city': row['phy_city'],
                    'zip_code': row['phy_zipcd'],
                    'owner': row['owner_name']
                }
                for row in result.data
                if row['phy_addr1'] and row['phy_addr1'].startswith(query)
            ][:limit]

        except Exception as e:
            print(f"Database error for query '{query}': {e}")
            # Fallback to a simpler query
            try:
                result = supabase.table('florida_parcels') \
                    .select('phy_addr1,phy_city,phy_zipcd,owner_name') \
                    .ilike('phy_addr1', f'{query[:3]}%') \
                    .limit(limit) \
                    .execute()

                results = [
                    {
                        'address': row['phy_addr1'],
                        'city': row['phy_city'],
                        'zip_code': row['phy_zipcd'],
                        'owner': row['owner_name']
                    }
                    for row in result.data
                ]
            except:
                pass

    else:
        # Text search (city or owner name)
        # Check city cache
        for city, cached_results in cache.city_cache.items():
            if city.startswith(query):
                results = cached_results[:limit]
                if results:
                    return {
                        "success": True,
                        "data": format_results(results),
                        "cached": True,
                        "time_ms": int((time.time() - start_time) * 1000)
                    }

        # Database query for cities
        try:
            result = supabase.table('florida_parcels') \
                .select('phy_addr1,phy_city,phy_zipcd,owner_name') \
                .ilike('phy_city', f'{query}%') \
                .limit(limit) \
                .execute()

            results = [
                {
                    'address': row['phy_addr1'],
                    'city': row['phy_city'],
                    'zip_code': row['phy_zipcd'],
                    'owner': row['owner_name']
                }
                for row in result.data
            ]
        except:
            pass

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "success": True,
        "data": format_results(results),
        "cached": False,
        "time_ms": elapsed_ms
    }

@app.get("/api/autocomplete/fast")
async def fast_autocomplete(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=20)
):
    """Ultra-fast autocomplete using only cached data"""

    query = q.upper().strip()
    results = []

    if query[0].isdigit():
        # Address search in cache
        for prefix, cached_results in cache.address_cache.items():
            if query.startswith(prefix):
                results.extend([r for r in cached_results if r['address'].startswith(query)])
    else:
        # City search in cache
        for city, cached_results in cache.city_cache.items():
            if city.startswith(query):
                results.extend(cached_results)

    return {
        "success": True,
        "data": format_results(results[:limit]),
        "cached": True,
        "time_ms": 0
    }

def format_results(results: List[Dict]) -> List[Dict]:
    """Format results for frontend"""
    formatted = []
    for r in results:
        if not r.get('address'):
            continue

        formatted.append({
            "address": r['address'].strip(),
            "city": (r.get('city') or '').strip(),
            "zip_code": str(r.get('zip_code', '')),
            "full_address": f"{r['address'].strip()}, {(r.get('city') or '').strip()} {r.get('zip_code', '')}",
            "type": "property",
            "owner_name": (r.get('owner') or r.get('owner_name', '')).strip()
        })

    return formatted

if __name__ == "__main__":
    import uvicorn
    print("Starting Optimized Autocomplete API on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002)