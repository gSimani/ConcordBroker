"""
Optimized Query API for 1.2M+ Property Records
High-performance endpoints with caching and optimization
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import redis
import json
import hashlib
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/v2", tags=["optimized"])

# Redis connection for caching
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Database pool for async queries
db_pool = None

async def get_db_pool():
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(
            os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL'),
            min_size=10,
            max_size=20,
            command_timeout=60
        )
    return db_pool

class PropertySearchParams(BaseModel):
    query: Optional[str] = None
    city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    property_type: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    page: int = 1
    limit: int = 20
    sort_by: str = "relevance"

class PropertyResponse(BaseModel):
    properties: List[Dict[Any, Any]]
    total: int
    page: int
    pages: int
    cached: bool = False
    query_time: float

@router.get("/properties/search")
async def search_properties(params: PropertySearchParams = Depends()):
    """
    Ultra-fast property search with caching and optimization
    """
    start_time = datetime.now()
    
    # Generate cache key
    cache_key = f"search:{hashlib.md5(json.dumps(params.dict(), sort_keys=True).encode()).hexdigest()}"
    
    # Check cache first
    cached_result = redis_client.get(cache_key)
    if cached_result:
        result = json.loads(cached_result)
        result['cached'] = True
        result['query_time'] = (datetime.now() - start_time).total_seconds()
        return result
    
    # Get database connection
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        # Build optimized query
        query_parts = []
        query_params = []
        param_count = 0
        
        # Base query with CTEs for performance
        base_query = """
        WITH filtered_properties AS (
            SELECT 
                parcel_id,
                phy_addr1,
                phy_city,
                phy_zipcd,
                owner_name,
                taxable_value,
                year_built,
                total_living_area,
                sale_date,
                sale_price,
                property_data,
                -- Calculate relevance score
                CASE 
                    WHEN $1::text IS NOT NULL THEN
                        ts_rank(to_tsvector('english', 
                            coalesce(phy_addr1,'') || ' ' || 
                            coalesce(phy_city,'') || ' ' || 
                            coalesce(owner_name,'')), 
                            plainto_tsquery('english', $1::text))
                    ELSE 1.0
                END as relevance
            FROM florida_parcels_optimized
            WHERE 1=1
        """
        
        param_count += 1
        query_params.append(params.query)
        
        # Add filters
        if params.city:
            param_count += 1
            query_parts.append(f"AND UPPER(phy_city) = UPPER(${param_count})")
            query_params.append(params.city)
        
        if params.min_price:
            param_count += 1
            query_parts.append(f"AND taxable_value >= ${param_count}")
            query_params.append(params.min_price)
        
        if params.max_price:
            param_count += 1
            query_parts.append(f"AND taxable_value <= ${param_count}")
            query_params.append(params.max_price)
        
        if params.min_year:
            param_count += 1
            query_parts.append(f"AND year_built >= ${param_count}")
            query_params.append(params.min_year)
        
        if params.max_year:
            param_count += 1
            query_parts.append(f"AND year_built <= ${param_count}")
            query_params.append(params.max_year)
        
        # Add text search if query provided
        if params.query:
            query_parts.append("""
                AND to_tsvector('english', 
                    coalesce(phy_addr1,'') || ' ' || 
                    coalesce(phy_city,'') || ' ' || 
                    coalesce(owner_name,'')) 
                @@ plainto_tsquery('english', $1)
            """)
        
        # Combine query parts
        where_clause = " ".join(query_parts)
        
        # Add sorting
        order_clause = {
            "relevance": "ORDER BY relevance DESC, taxable_value DESC",
            "price_asc": "ORDER BY taxable_value ASC",
            "price_desc": "ORDER BY taxable_value DESC",
            "newest": "ORDER BY year_built DESC",
            "oldest": "ORDER BY year_built ASC",
            "recent_sales": "ORDER BY sale_date DESC"
        }.get(params.sort_by, "ORDER BY relevance DESC")
        
        # Calculate offset
        offset = (params.page - 1) * params.limit
        
        # Final query with pagination
        final_query = f"""
        {base_query}
        {where_clause}
        ),
        counted AS (
            SELECT COUNT(*) as total FROM filtered_properties
        )
        SELECT 
            p.*,
            c.total
        FROM filtered_properties p
        CROSS JOIN counted c
        {order_clause}
        LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        query_params.extend([params.limit, offset])
        
        # Execute query
        rows = await conn.fetch(final_query, *query_params)
        
        if not rows:
            result = {
                "properties": [],
                "total": 0,
                "page": params.page,
                "pages": 0,
                "cached": False,
                "query_time": (datetime.now() - start_time).total_seconds()
            }
        else:
            total = rows[0]['total'] if rows else 0
            properties = [
                {
                    "parcel_id": row['parcel_id'],
                    "address": row['phy_addr1'],
                    "city": row['phy_city'],
                    "zip": row['phy_zipcd'],
                    "owner": row['owner_name'],
                    "value": row['taxable_value'],
                    "year_built": row['year_built'],
                    "sqft": row['total_living_area'],
                    "sale_date": row['sale_date'].isoformat() if row['sale_date'] else None,
                    "sale_price": row['sale_price'],
                    "relevance": row['relevance']
                }
                for row in rows
            ]
            
            result = {
                "properties": properties,
                "total": total,
                "page": params.page,
                "pages": (total + params.limit - 1) // params.limit,
                "cached": False,
                "query_time": (datetime.now() - start_time).total_seconds()
            }
        
        # Cache the result for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(result, default=str))
        
        return result

@router.get("/properties/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=2),
    field: str = Query("address", regex="^(address|city|owner)$")
):
    """
    Fast autocomplete using database indexes
    """
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if field == "address":
            query = """
            SELECT DISTINCT phy_addr1 as value
            FROM florida_parcels_optimized
            WHERE phy_addr1 ILIKE $1
            LIMIT 10
            """
        elif field == "city":
            query = """
            SELECT DISTINCT phy_city as value, COUNT(*) as count
            FROM florida_parcels_optimized
            WHERE phy_city ILIKE $1
            GROUP BY phy_city
            ORDER BY count DESC
            LIMIT 10
            """
        else:  # owner
            query = """
            SELECT DISTINCT owner_name as value
            FROM florida_parcels_optimized
            WHERE owner_name ILIKE $1
            LIMIT 10
            """
        
        rows = await conn.fetch(query, f"{q}%")
        return [{"value": row['value'], "count": row.get('count')} for row in rows]

@router.get("/properties/stats")
async def get_stats(city: Optional[str] = None):
    """
    Get property statistics from materialized views
    """
    cache_key = f"stats:{city or 'all'}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        if city:
            stats = await conn.fetchrow("""
                SELECT * FROM mv_city_summary
                WHERE phy_city = $1
            """, city)
        else:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as property_count,
                    AVG(taxable_value) as avg_value,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY taxable_value) as median_value,
                    SUM(taxable_value) as total_value
                FROM florida_parcels_optimized
                WHERE taxable_value > 0
            """)
        
        result = dict(stats) if stats else {}
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(result, default=str))
        
        return result

@router.get("/properties/{parcel_id}")
async def get_property(parcel_id: str):
    """
    Get single property details with caching
    """
    cache_key = f"property:{parcel_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        property_data = await conn.fetchrow("""
            SELECT 
                *,
                -- Get nearby properties count
                (SELECT COUNT(*) FROM florida_parcels_optimized p2 
                 WHERE p2.phy_city = p1.phy_city 
                 AND p2.parcel_id != p1.parcel_id) as nearby_count,
                -- Get average neighborhood value
                (SELECT AVG(taxable_value) FROM florida_parcels_optimized p2 
                 WHERE p2.phy_city = p1.phy_city) as neighborhood_avg_value
            FROM florida_parcels_optimized p1
            WHERE parcel_id = $1
        """, parcel_id)
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        result = dict(property_data)
        
        # Cache for 30 minutes
        redis_client.setex(cache_key, 1800, json.dumps(result, default=str))
        
        return result

@router.post("/properties/bulk")
async def get_bulk_properties(parcel_ids: List[str]):
    """
    Get multiple properties in one request
    """
    if len(parcel_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 properties per request")
    
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        properties = await conn.fetch("""
            SELECT * FROM florida_parcels_optimized
            WHERE parcel_id = ANY($1::text[])
        """, parcel_ids)
        
        return [dict(p) for p in properties]