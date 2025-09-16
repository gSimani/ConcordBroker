"""
Optimized Property Service with SQLAlchemy, Caching, and Performance Features
"""

from fastapi import FastAPI, Query, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import and_, or_, func, text, select
from sqlalchemy.orm import Session, selectinload, joinedload
import redis
import json
import hashlib
import logging
from contextlib import asynccontextmanager
import time
from functools import lru_cache
import uvicorn

# Import our optimized database components
from database.optimized_connection import get_optimized_db, OptimizedDatabaseConnection
from database.models import (
    FloridaParcel, SalesHistory, TaxCertificate,
    TaxDeed, SunbizEntity, SunbizOfficer, SunbizPropertyMatch
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = get_optimized_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting optimized property service...")

    # Create performance indexes
    await create_performance_indexes()

    # Warm up cache with common queries
    await warm_up_cache()

    # Start background tasks
    asyncio.create_task(cache_maintenance_task())
    asyncio.create_task(performance_monitor_task())

    yield

    # Shutdown
    logger.info("Shutting down optimized property service...")
    db.close()

# Initialize FastAPI with lifespan
app = FastAPI(
    title="ConcordBroker Optimized Property Service",
    description="High-performance property data API with SQLAlchemy and caching",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db_session():
    """Get database session"""
    with db.get_session() as session:
        yield session

async def create_performance_indexes():
    """Create database indexes for optimal performance"""
    indexes = [
        {
            'name': 'idx_florida_parcels_search',
            'table': 'florida_parcels',
            'columns': ['phy_addr1', 'phy_city', 'owner_name'],
            'type': 'USING gin (to_tsvector(\'english\', phy_addr1 || \' \' || phy_city || \' \' || owner_name))'
        },
        {
            'name': 'idx_florida_parcels_value_filter',
            'table': 'florida_parcels',
            'columns': ['jv', 'av_sd'],
            'where': 'jv IS NOT NULL'
        },
        {
            'name': 'idx_florida_parcels_geo',
            'table': 'florida_parcels',
            'columns': ['latitude', 'longitude'],
            'type': 'USING gist (point(longitude, latitude))'
        },
        {
            'name': 'idx_tax_deeds_upcoming',
            'table': 'tax_deeds',
            'columns': ['auction_date', 'auction_status'],
            'where': "auction_status = 'Upcoming'"
        },
        {
            'name': 'idx_sunbiz_entity_active',
            'table': 'sunbiz_entities',
            'columns': ['entity_name', 'status'],
            'where': "status = 'Active'"
        }
    ]

    db.create_indexes(indexes)

    # Update table statistics
    db.analyze_tables(['florida_parcels', 'tax_deeds', 'sunbiz_entities'])

async def warm_up_cache():
    """Pre-load frequently accessed data into cache"""
    logger.info("Warming up cache...")

    common_queries = [
        # Top properties by value
        ("SELECT * FROM florida_parcels ORDER BY jv DESC LIMIT 100", None, 3600),

        # Upcoming tax deed auctions
        ("SELECT * FROM tax_deeds WHERE auction_status = 'Upcoming' ORDER BY auction_date LIMIT 50", None, 1800),

        # Property count by city
        ("SELECT phy_city, COUNT(*) as count FROM florida_parcels GROUP BY phy_city", None, 7200),

        # Active Sunbiz entities
        ("SELECT COUNT(*) FROM sunbiz_entities WHERE status = 'Active'", None, 3600),
    ]

    for query, params, ttl in common_queries:
        try:
            await db.cached_query(query, params, ttl)
        except Exception as e:
            logger.warning(f"Cache warmup error: {e}")

async def cache_maintenance_task():
    """Background task to maintain cache"""
    while True:
        try:
            # Clean expired cache entries
            with db.get_session() as session:
                session.execute(
                    text("DELETE FROM query_cache WHERE expires_at < NOW()")
                )
                session.commit()

            # Log cache metrics
            metrics = db.get_metrics()
            logger.info(f"Cache metrics: Hit rate={metrics['cache_hit_rate']:.2%}")

        except Exception as e:
            logger.error(f"Cache maintenance error: {e}")

        await asyncio.sleep(300)  # Run every 5 minutes

async def performance_monitor_task():
    """Monitor and log performance metrics"""
    while True:
        try:
            metrics = db.get_metrics()

            # Log performance warnings
            if metrics['avg_query_time'] > 1.0:
                logger.warning(f"High average query time: {metrics['avg_query_time']:.2f}s")

            if metrics['cache_hit_rate'] < 0.5:
                logger.warning(f"Low cache hit rate: {metrics['cache_hit_rate']:.2%}")

            if metrics['pool_overflow'] > 10:
                logger.warning(f"High connection pool overflow: {metrics['pool_overflow']}")

        except Exception as e:
            logger.error(f"Performance monitor error: {e}")

        await asyncio.sleep(60)  # Run every minute

@app.get("/")
async def root():
    """Health check with metrics"""
    metrics = db.get_metrics()
    return {
        "status": "healthy",
        "service": "ConcordBroker Optimized Property Service",
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "cache_hit_rate": f"{metrics['cache_hit_rate']:.2%}",
            "avg_query_time": f"{metrics['avg_query_time']:.3f}s",
            "total_queries": metrics['queries'],
            "connection_pool": {
                "active": metrics['pool_total'],
                "available": metrics['pool_checked_in'],
                "overflow": metrics['pool_overflow']
            }
        }
    }

@app.get("/api/properties/search/optimized")
async def search_properties_optimized(
    # Search parameters
    q: Optional[str] = Query(None, description="Full-text search query"),
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),

    # Filters
    property_type: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    min_sqft: Optional[float] = Query(None),
    max_sqft: Optional[float] = Query(None),

    # Special filters
    has_tax_deed: Optional[bool] = Query(None),
    has_business_entity: Optional[bool] = Query(None),
    investment_grade: Optional[bool] = Query(None),

    # Pagination
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),

    # Sorting
    sort_by: str = Query("jv", regex="^(jv|phy_addr1|yr_blt|sale_prc1)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),

    # Performance options
    use_cache: bool = Query(True),
    cache_ttl: int = Query(300),

    session: Session = Depends(get_db_session)
):
    """
    Optimized property search with SQLAlchemy and caching
    """
    start_time = time.time()

    # Generate cache key
    cache_params = {
        'q': q, 'address': address, 'city': city, 'zip_code': zip_code,
        'owner': owner, 'property_type': property_type,
        'min_value': min_value, 'max_value': max_value,
        'min_year': min_year, 'max_year': max_year,
        'min_sqft': min_sqft, 'max_sqft': max_sqft,
        'has_tax_deed': has_tax_deed, 'has_business_entity': has_business_entity,
        'investment_grade': investment_grade,
        'page': page, 'limit': limit, 'sort_by': sort_by, 'sort_order': sort_order
    }

    cache_key = hashlib.md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()

    # Try cache first if enabled
    if use_cache:
        cached_result = await get_cached_result(cache_key)
        if cached_result:
            return JSONResponse(
                content={
                    **cached_result,
                    'cached': True,
                    'query_time': time.time() - start_time
                }
            )

    # Build optimized query
    query = session.query(FloridaParcel)

    # Apply filters efficiently
    filters = []

    # Full-text search using PostgreSQL
    if q:
        # Use PostgreSQL full-text search
        search_vector = func.to_tsvector('english',
            func.concat(
                FloridaParcel.phy_addr1, ' ',
                FloridaParcel.phy_city, ' ',
                FloridaParcel.owner_name
            )
        )
        search_query = func.plainto_tsquery('english', q)
        filters.append(search_vector.match(search_query))

    # Specific field searches
    if address:
        filters.append(FloridaParcel.phy_addr1.ilike(f'%{address}%'))

    if city:
        filters.append(FloridaParcel.phy_city.ilike(f'%{city}%'))

    if zip_code:
        filters.append(FloridaParcel.phy_zipcd == zip_code)

    if owner:
        filters.append(FloridaParcel.owner_name.ilike(f'%{owner}%'))

    # Property type filter
    if property_type:
        type_codes = {
            'single_family': ['0100', '0101', '0102', '0103'],
            'multi_family': ['0200', '0201', '0202'],
            'commercial': ['1000', '1100', '1200'],
            'industrial': ['4000', '4100', '4200'],
            'agricultural': ['5000', '5100', '5200'],
            'vacant': ['0000', '0001']
        }
        if property_type in type_codes:
            filters.append(FloridaParcel.dor_uc.in_(type_codes[property_type]))

    # Value filters
    if min_value is not None:
        filters.append(FloridaParcel.jv >= min_value)

    if max_value is not None:
        filters.append(FloridaParcel.jv <= max_value)

    # Year built filters
    if min_year is not None:
        filters.append(FloridaParcel.yr_blt >= min_year)

    if max_year is not None:
        filters.append(FloridaParcel.yr_blt <= max_year)

    # Square footage filters
    if min_sqft is not None:
        filters.append(FloridaParcel.tot_lvg_area >= min_sqft)

    if max_sqft is not None:
        filters.append(FloridaParcel.tot_lvg_area <= max_sqft)

    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))

    # Special filters with joins
    if has_tax_deed:
        query = query.join(TaxDeed).filter(TaxDeed.auction_status == 'Upcoming')

    if has_business_entity:
        query = query.join(SunbizPropertyMatch).filter(SunbizPropertyMatch.confidence_score >= 0.8)

    # Investment grade filter (custom logic)
    if investment_grade:
        query = query.filter(
            and_(
                FloridaParcel.jv > 0,
                FloridaParcel.jv < FloridaParcel.av_sd * 0.9,  # Undervalued
                FloridaParcel.yr_blt > 1980,  # Not too old
                FloridaParcel.tot_lvg_area > 1000  # Decent size
            )
        )

    # Get total count before pagination
    total_count = query.count()

    # Apply sorting
    if sort_order == 'desc':
        query = query.order_by(getattr(FloridaParcel, sort_by).desc())
    else:
        query = query.order_by(getattr(FloridaParcel, sort_by))

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Execute with eager loading of relationships
    properties = query.options(
        selectinload(FloridaParcel.tax_deeds),
        selectinload(FloridaParcel.sunbiz_matches)
    ).all()

    # Format results
    results = []
    for prop in properties:
        result = prop.to_dict()

        # Add related data
        if prop.tax_deeds:
            result['tax_deed'] = {
                'auction_date': prop.tax_deeds[0].auction_date.isoformat() if prop.tax_deeds[0].auction_date else None,
                'opening_bid': float(prop.tax_deeds[0].opening_bid or 0)
            }

        if prop.sunbiz_matches:
            result['business_entity'] = True

        # Calculate investment score
        result['investment_score'] = calculate_investment_score_optimized(prop)

        results.append(result)

    # Prepare response
    response = {
        'success': True,
        'data': results,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total_count,
            'pages': (total_count + limit - 1) // limit
        },
        'query_time': time.time() - start_time,
        'cached': False,
        'timestamp': datetime.now().isoformat()
    }

    # Cache the result
    if use_cache:
        await cache_result(cache_key, response, cache_ttl)

    return response

@app.get("/api/properties/{parcel_id}/detailed")
async def get_property_detailed_optimized(
    parcel_id: str,
    include_history: bool = Query(True),
    include_tax_info: bool = Query(True),
    include_business: bool = Query(True),
    use_cache: bool = Query(True),
    session: Session = Depends(get_db_session)
):
    """
    Get detailed property information with all related data
    """
    cache_key = f"property_detail:{parcel_id}:{include_history}:{include_tax_info}:{include_business}"

    # Try cache first
    if use_cache:
        cached = await get_cached_result(cache_key)
        if cached:
            return cached

    # Query with eager loading
    query = session.query(FloridaParcel).filter(
        FloridaParcel.parcel_id == parcel_id
    )

    # Add eager loading based on requested data
    if include_history:
        query = query.options(selectinload(FloridaParcel.sales_history))

    if include_tax_info:
        query = query.options(
            selectinload(FloridaParcel.tax_certificates),
            selectinload(FloridaParcel.tax_deeds)
        )

    if include_business:
        query = query.options(
            selectinload(FloridaParcel.sunbiz_matches).selectinload(
                SunbizPropertyMatch.entity
            ).selectinload(SunbizEntity.officers)
        )

    property_data = query.first()

    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    # Build comprehensive response
    result = {
        **property_data.to_dict(),
        'details': {
            'parcel_id': property_data.parcel_id,
            'full_address': property_data.full_address,
            'county': property_data.county,
            'year': property_data.year,
            'subdivision': property_data.subdivision,
            'legal_description': property_data.subdivision,
            'neighborhood': property_data.nbhd_cd
        }
    }

    # Add sales history
    if include_history and property_data.sales_history:
        result['sales_history'] = [
            {
                'date': sale.sale_date.isoformat() if sale.sale_date else None,
                'price': float(sale.sale_price or 0),
                'seller': sale.seller_name,
                'buyer': sale.buyer_name
            }
            for sale in property_data.sales_history
        ]

    # Add tax information
    if include_tax_info:
        if property_data.tax_certificates:
            result['tax_certificates'] = [
                {
                    'certificate_number': cert.certificate_number,
                    'year': cert.tax_year,
                    'amount': float(cert.face_amount or 0),
                    'status': cert.status
                }
                for cert in property_data.tax_certificates
            ]

        if property_data.tax_deeds:
            result['tax_deeds'] = [
                {
                    'td_number': deed.td_number,
                    'auction_date': deed.auction_date.isoformat() if deed.auction_date else None,
                    'status': deed.auction_status,
                    'opening_bid': float(deed.opening_bid or 0)
                }
                for deed in property_data.tax_deeds
            ]

    # Add business entity information
    if include_business and property_data.sunbiz_matches:
        result['business_entities'] = []
        for match in property_data.sunbiz_matches:
            entity_data = {
                'doc_number': match.entity.doc_number,
                'name': match.entity.entity_name,
                'type': match.entity.entity_type,
                'status': match.entity.status,
                'match_type': match.match_type,
                'confidence': match.confidence_score
            }

            if match.entity.officers:
                entity_data['officers'] = [
                    {
                        'name': officer.name,
                        'title': officer.title
                    }
                    for officer in match.entity.officers[:5]  # Limit to 5 officers
                ]

            result['business_entities'].append(entity_data)

    # Calculate analytics
    result['analytics'] = {
        'investment_score': calculate_investment_score_optimized(property_data),
        'market_to_assessed_ratio': property_data.market_to_assessed_ratio,
        'price_per_sqft': calculate_price_per_sqft(property_data),
        'cap_rate': calculate_cap_rate(property_data),
        'days_on_market': calculate_days_on_market(property_data)
    }

    # Cache the result
    if use_cache:
        await cache_result(cache_key, result, 600)  # Cache for 10 minutes

    return result

@app.post("/api/properties/bulk-search")
async def bulk_property_search(
    parcel_ids: List[str],
    session: Session = Depends(get_db_session)
):
    """
    Bulk search for multiple properties efficiently
    """
    if len(parcel_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 parcel IDs allowed")

    # Use SQLAlchemy's IN clause for efficient bulk query
    properties = session.query(FloridaParcel).filter(
        FloridaParcel.parcel_id.in_(parcel_ids)
    ).all()

    # Create a map for quick lookup
    property_map = {prop.parcel_id: prop.to_dict() for prop in properties}

    # Return results in the same order as requested
    results = []
    for parcel_id in parcel_ids:
        if parcel_id in property_map:
            results.append(property_map[parcel_id])
        else:
            results.append({'parcel_id': parcel_id, 'error': 'Not found'})

    return {
        'success': True,
        'data': results,
        'found': len(property_map),
        'total_requested': len(parcel_ids)
    }

@app.get("/api/analytics/market-trends")
async def get_market_trends(
    city: Optional[str] = None,
    county: Optional[str] = None,
    property_type: Optional[str] = None,
    days: int = Query(30, ge=7, le=365),
    session: Session = Depends(get_db_session)
):
    """
    Get market trends and analytics
    """
    cache_key = f"trends:{city}:{county}:{property_type}:{days}"

    # Try cache
    cached = await get_cached_result(cache_key)
    if cached:
        return cached

    # Build trend query
    base_query = session.query(
        func.date_trunc('day', FloridaParcel.updated_at).label('date'),
        func.avg(FloridaParcel.jv).label('avg_value'),
        func.count(FloridaParcel.id).label('count'),
        func.min(FloridaParcel.jv).label('min_value'),
        func.max(FloridaParcel.jv).label('max_value')
    )

    # Apply filters
    if city:
        base_query = base_query.filter(FloridaParcel.phy_city == city)

    if county:
        base_query = base_query.filter(FloridaParcel.county == county)

    if property_type:
        # Use property type mapping
        type_codes = {
            'single_family': ['0100', '0101', '0102', '0103'],
            'multi_family': ['0200', '0201', '0202'],
            'commercial': ['1000', '1100', '1200']
        }
        if property_type in type_codes:
            base_query = base_query.filter(FloridaParcel.dor_uc.in_(type_codes[property_type]))

    # Group by date and order
    trends = base_query.group_by('date').order_by('date').all()

    result = {
        'trends': [
            {
                'date': trend.date.isoformat(),
                'avg_value': float(trend.avg_value or 0),
                'count': trend.count,
                'min_value': float(trend.min_value or 0),
                'max_value': float(trend.max_value or 0)
            }
            for trend in trends
        ],
        'filters': {
            'city': city,
            'county': county,
            'property_type': property_type,
            'days': days
        }
    }

    # Cache for 1 hour
    await cache_result(cache_key, result, 3600)

    return result

# Helper functions

async def get_cached_result(cache_key: str) -> Optional[Dict]:
    """Get cached result from Redis or memory"""
    try:
        # Try memory cache first
        cached = await db.memory_cache.get(cache_key)
        if cached:
            return cached

        # Try Redis
        if db.redis_client:
            cached_str = db.redis_client.get(f"api:{cache_key}")
            if cached_str:
                return json.loads(cached_str)
    except Exception as e:
        logger.warning(f"Cache retrieval error: {e}")

    return None

async def cache_result(cache_key: str, data: Dict, ttl: int = 300):
    """Cache result in Redis and memory"""
    try:
        # Cache in memory
        await db.memory_cache.set(cache_key, data, ttl=ttl)

        # Cache in Redis
        if db.redis_client:
            db.redis_client.setex(
                f"api:{cache_key}",
                ttl,
                json.dumps(data)
            )
    except Exception as e:
        logger.warning(f"Cache write error: {e}")

def calculate_investment_score_optimized(property_data: FloridaParcel) -> float:
    """Calculate investment score with optimized logic"""
    score = 50.0

    # Value factors
    if property_data.jv and property_data.av_sd:
        ratio = property_data.market_to_assessed_ratio
        if ratio < 0.9:
            score += 15  # Undervalued
        elif ratio < 1.0:
            score += 10

        if property_data.jv < 200000:
            score += 10  # Affordable entry

    # Property quality
    if property_data.yr_blt and property_data.yr_blt > 2000:
        score += 10  # Newer property

    if property_data.tot_lvg_area and property_data.tot_lvg_area > 1500:
        score += 5  # Good size

    # Tax deed bonus
    if property_data.tax_deeds:
        score += 15  # Has tax deed opportunity

    return min(100, max(0, score))

def calculate_price_per_sqft(property_data: FloridaParcel) -> float:
    """Calculate price per square foot"""
    if property_data.tot_lvg_area and property_data.tot_lvg_area > 0:
        return float(property_data.jv or 0) / property_data.tot_lvg_area
    return 0

def calculate_cap_rate(property_data: FloridaParcel) -> float:
    """Calculate capitalization rate"""
    if property_data.jv and property_data.jv > 0:
        # Estimate rental income (1% rule)
        monthly_rent = float(property_data.jv) * 0.01
        annual_income = monthly_rent * 12

        # Estimate expenses (30% of income)
        annual_expenses = annual_income * 0.3

        # Calculate NOI and cap rate
        noi = annual_income - annual_expenses
        return (noi / float(property_data.jv)) * 100

    return 0

def calculate_days_on_market(property_data: FloridaParcel) -> int:
    """Calculate days on market"""
    if property_data.updated_at:
        return (datetime.now() - property_data.updated_at).days
    return 0

if __name__ == "__main__":
    uvicorn.run(
        "optimized_property_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )