"""
Analytics Router
Market analytics and insights endpoints
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..database import db

router = APIRouter()


class MarketTrend(BaseModel):
    """Market trend data"""
    period: str
    city: Optional[str]
    use_code: Optional[str]
    avg_price: float
    median_price: float
    transaction_count: int
    total_volume: float


@router.get("/market-trends")
async def get_market_trends(
    city: Optional[str] = Query(None),
    use_code: Optional[str] = Query(None),
    days: int = Query(90, description="Number of days to analyze")
):
    """Get market trends and statistics"""
    
    conditions = ["s.sale_date >= NOW() - INTERVAL '%s days'" % days]
    params = []
    param_count = 0
    
    if city:
        param_count += 1
        conditions.append(f"p.city = ${param_count}")
        params.append(city)
    
    if use_code:
        param_count += 1
        conditions.append(f"p.main_use = ${param_count}")
        params.append(use_code)
    
    where_clause = "WHERE " + " AND ".join(conditions)
    
    query = f"""
        SELECT 
            DATE_TRUNC('month', s.sale_date) as period,
            AVG(s.price) as avg_price,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.price) as median_price,
            COUNT(*) as transaction_count,
            SUM(s.price) as total_volume
        FROM sales s
        JOIN parcels p ON s.folio = p.folio
        {where_clause}
        GROUP BY period
        ORDER BY period DESC
    """
    
    results = await db.fetch_many(query, *params)
    return results


@router.get("/top-opportunities")
async def get_top_opportunities(
    city: Optional[str] = Query(None),
    use_code: Optional[str] = Query(None),
    limit: int = Query(20)
):
    """Get top investment opportunities by score"""
    
    conditions = ["p.score IS NOT NULL"]
    params = []
    param_count = 0
    
    if city:
        param_count += 1
        conditions.append(f"p.city = ${param_count}")
        params.append(city)
    
    if use_code:
        param_count += 1
        conditions.append(f"p.main_use = ${param_count}")
        params.append(use_code)
    
    where_clause = "WHERE " + " AND ".join(conditions)
    
    param_count += 1
    params.append(limit)
    
    query = f"""
        SELECT 
            p.folio,
            p.city,
            p.main_use,
            p.situs_addr,
            p.owner_raw,
            p.just_value,
            p.score,
            p.score_updated_at,
            (p.just_value - p.assessed_soh) as value_gap,
            CASE 
                WHEN p.land_sf > 0 THEN p.just_value / p.land_sf 
                ELSE NULL 
            END as price_per_sf
        FROM parcels p
        {where_clause}
        ORDER BY p.score DESC
        LIMIT ${param_count}
    """
    
    results = await db.fetch_many(query, *params)
    return results


@router.get("/city-statistics")
async def get_city_statistics():
    """Get statistics by city"""
    
    query = """
        SELECT 
            city,
            COUNT(*) as property_count,
            AVG(just_value) as avg_value,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY just_value) as median_value,
            SUM(just_value) as total_value,
            AVG(score) as avg_score,
            COUNT(CASE WHEN score >= 70 THEN 1 END) as high_score_count
        FROM parcels
        WHERE city IS NOT NULL
        GROUP BY city
        ORDER BY total_value DESC
    """
    
    results = await db.fetch_many(query)
    return results


@router.get("/use-code-analysis")
async def analyze_use_codes():
    """Analyze properties by use code"""
    
    query = """
        SELECT 
            main_use,
            COUNT(*) as property_count,
            AVG(just_value) as avg_value,
            AVG(score) as avg_score,
            AVG(CASE WHEN land_sf > 0 THEN just_value / land_sf END) as avg_price_per_sf,
            COUNT(DISTINCT city) as city_count
        FROM parcels
        GROUP BY main_use
        ORDER BY avg_score DESC NULLS LAST
    """
    
    results = await db.fetch_many(query)
    return results


@router.get("/entity-concentration")
async def get_entity_concentration(
    min_properties: int = Query(5, description="Minimum properties owned")
):
    """Get entities with highest property concentration"""
    
    query = """
        SELECT 
            e.id,
            e.name,
            e.status,
            COUNT(DISTINCT pel.folio) as property_count,
            COUNT(DISTINCT p.city) as city_count,
            SUM(p.just_value) as total_value,
            AVG(p.score) as avg_score,
            array_agg(DISTINCT p.main_use) as use_codes
        FROM entities e
        JOIN parcel_entity_links pel ON e.id = pel.entity_id
        JOIN parcels p ON pel.folio = p.folio
        GROUP BY e.id, e.name, e.status
        HAVING COUNT(DISTINCT pel.folio) >= $1
        ORDER BY total_value DESC
        LIMIT 50
    """
    
    results = await db.fetch_many(query, min_properties)
    return results


@router.get("/recent-activity")
async def get_recent_activity(days: int = Query(7)):
    """Get recent market activity"""
    
    query = """
        WITH recent_sales AS (
            SELECT 
                'sale' as activity_type,
                s.folio,
                p.city,
                p.main_use,
                s.sale_date as activity_date,
                s.price as value,
                p.situs_addr
            FROM sales s
            JOIN parcels p ON s.folio = p.folio
            WHERE s.sale_date >= NOW() - INTERVAL '%s days'
        ),
        recent_docs AS (
            SELECT 
                'document' as activity_type,
                dp.folio,
                p.city,
                p.main_use,
                rd.rec_datetime as activity_date,
                rd.consideration as value,
                p.situs_addr
            FROM recorded_docs rd
            JOIN doc_parcels dp ON rd.instrument_no = dp.instrument_no
            JOIN parcels p ON dp.folio = p.folio
            WHERE rd.rec_datetime >= NOW() - INTERVAL '%s days'
        )
        SELECT * FROM (
            SELECT * FROM recent_sales
            UNION ALL
            SELECT * FROM recent_docs
        ) combined
        ORDER BY activity_date DESC
        LIMIT 100
    """ % (days, days)
    
    results = await db.fetch_many(query)
    return results