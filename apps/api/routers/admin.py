"""
Admin Router
Administrative endpoints for system management
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from ..database import db
from ..config import settings

router = APIRouter()


def verify_admin_token(x_admin_token: str = Header(None)):
    """Verify admin token"""
    if not x_admin_token or x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


class DataSourceTrigger(BaseModel):
    """Data source trigger request"""
    source: str
    mode: Optional[str] = "incremental"
    parameters: Optional[dict] = {}


@router.post("/trigger-sync", dependencies=[Depends(verify_admin_token)])
async def trigger_data_sync(request: DataSourceTrigger):
    """Manually trigger data source synchronization"""
    
    # Log the trigger request
    await db.execute(
        """
        INSERT INTO jobs (job_type, started_at, parameters)
        VALUES ($1, $2, $3)
        """,
        f"manual_{request.source}",
        datetime.now(),
        request.parameters
    )
    
    # In production, this would trigger the actual ETL job
    # For now, return acknowledgment
    return {
        "message": f"Sync triggered for {request.source}",
        "mode": request.mode,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/recalculate-scores", dependencies=[Depends(verify_admin_token)])
async def recalculate_all_scores(
    city: Optional[str] = None,
    use_code: Optional[str] = None
):
    """Recalculate investment scores for parcels"""
    
    conditions = []
    params = []
    
    if city:
        conditions.append("city = $1")
        params.append(city)
    
    if use_code:
        param_num = len(params) + 1
        conditions.append(f"main_use = ${param_num}")
        params.append(use_code)
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Get parcels to recalculate
    query = f"""
        SELECT folio FROM parcels
        {where_clause}
        LIMIT 1000
    """
    
    parcels = await db.fetch_many(query, *params)
    
    # In production, this would queue score calculations
    return {
        "message": "Score recalculation queued",
        "parcels_queued": len(parcels),
        "filters": {"city": city, "use_code": use_code}
    }


@router.get("/jobs", dependencies=[Depends(verify_admin_token)])
async def get_recent_jobs(limit: int = 50):
    """Get recent ETL job history"""
    
    jobs = await db.fetch_many(
        """
        SELECT * FROM jobs
        ORDER BY started_at DESC
        LIMIT $1
        """,
        limit
    )
    
    return jobs


@router.get("/data-quality", dependencies=[Depends(verify_admin_token)])
async def check_data_quality():
    """Run data quality checks"""
    
    checks = {}
    
    # Check for missing required fields
    missing_checks = await db.fetch_one(
        """
        SELECT 
            COUNT(CASE WHEN folio IS NULL THEN 1 END) as missing_folio,
            COUNT(CASE WHEN city IS NULL THEN 1 END) as missing_city,
            COUNT(CASE WHEN main_use IS NULL THEN 1 END) as missing_use,
            COUNT(CASE WHEN just_value IS NULL THEN 1 END) as missing_value
        FROM parcels
        """
    )
    checks['missing_fields'] = missing_checks
    
    # Check for duplicate folios
    duplicates = await db.fetch_one(
        """
        SELECT COUNT(*) as duplicate_count
        FROM (
            SELECT folio, COUNT(*) as cnt
            FROM parcels
            GROUP BY folio
            HAVING COUNT(*) > 1
        ) dups
        """
    )
    checks['duplicate_folios'] = duplicates['duplicate_count']
    
    # Check entity matching coverage
    entity_coverage = await db.fetch_one(
        """
        SELECT 
            COUNT(*) as total_parcels,
            COUNT(owner_entity_id) as matched_entities,
            ROUND(COUNT(owner_entity_id)::numeric / COUNT(*)::numeric * 100, 2) as match_percentage
        FROM parcels
        """
    )
    checks['entity_matching'] = entity_coverage
    
    # Check score coverage
    score_coverage = await db.fetch_one(
        """
        SELECT 
            COUNT(*) as total_parcels,
            COUNT(score) as scored_parcels,
            ROUND(COUNT(score)::numeric / COUNT(*)::numeric * 100, 2) as score_percentage
        FROM parcels
        """
    )
    checks['scoring'] = score_coverage
    
    return {
        "timestamp": datetime.now().isoformat(),
        "checks": checks
    }


@router.delete("/cache", dependencies=[Depends(verify_admin_token)])
async def clear_cache():
    """Clear application cache"""
    
    # In production, this would clear Redis cache
    return {"message": "Cache cleared", "timestamp": datetime.now().isoformat()}


@router.get("/debug/sql", dependencies=[Depends(verify_admin_token)])
async def execute_sql(query: str):
    """Execute arbitrary SQL query (debug only)"""
    
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=403, detail="Not available in production")
    
    try:
        # Only allow SELECT queries
        if not query.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Only SELECT queries allowed")
        
        results = await db.fetch_many(query)
        return {
            "query": query,
            "rows": len(results),
            "results": results[:100]  # Limit to 100 rows
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e)
        }