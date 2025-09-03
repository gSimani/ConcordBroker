"""
Health Check Router
System health and status endpoints
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    version: str
    environment: str


class DataSourceStatus(BaseModel):
    """Data source status"""
    name: str
    status: str
    last_sync: datetime = None
    records: int = 0
    error: str = None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    
    # Check database connection
    try:
        await db.fetch_one("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        timestamp=datetime.now(),
        database=db_status,
        version="0.1.0",
        environment=settings.ENVIRONMENT
    )


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with component status"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        result = await db.fetch_one("SELECT COUNT(*) as count FROM parcels")
        health_status["components"]["database"] = {
            "status": "healthy",
            "parcels_count": result['count']
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check data sources
    data_sources = await check_data_sources()
    health_status["components"]["data_sources"] = data_sources
    
    # Check last job status
    try:
        last_jobs = await db.fetch_many(
            """
            SELECT job_type, finished_at, ok
            FROM jobs
            ORDER BY finished_at DESC
            LIMIT 5
            """
        )
        health_status["components"]["etl_jobs"] = {
            "status": "healthy",
            "recent_jobs": last_jobs
        }
    except Exception as e:
        health_status["components"]["etl_jobs"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    return health_status


async def check_data_sources() -> Dict[str, Any]:
    """Check status of all data sources"""
    
    sources = {}
    
    # Check DOR data
    try:
        dor_status = await db.fetch_one(
            """
            SELECT 
                MAX(last_seen_at) as last_sync,
                COUNT(*) as records
            FROM parcels
            WHERE data_source = 'DOR'
            """
        )
        sources["dor"] = {
            "status": "active" if dor_status['last_sync'] else "waiting",
            "last_sync": dor_status['last_sync'],
            "records": dor_status['records']
        }
    except:
        sources["dor"] = {"status": "error"}
    
    # Check Sunbiz data
    try:
        sunbiz_status = await db.fetch_one(
            """
            SELECT 
                MAX(updated_at) as last_sync,
                COUNT(*) as records
            FROM entities
            """
        )
        sources["sunbiz"] = {
            "status": "active" if sunbiz_status['last_sync'] else "waiting",
            "last_sync": sunbiz_status['last_sync'],
            "records": sunbiz_status['records']
        }
    except:
        sources["sunbiz"] = {"status": "error"}
    
    # Check Official Records
    try:
        or_status = await db.fetch_one(
            """
            SELECT 
                MAX(rec_datetime) as last_sync,
                COUNT(*) as records
            FROM recorded_docs
            """
        )
        sources["official_records"] = {
            "status": "active" if or_status['last_sync'] else "waiting",
            "last_sync": or_status['last_sync'],
            "records": or_status['records']
        }
    except:
        sources["official_records"] = {"status": "error"}
    
    return sources


@router.get("/status")
async def system_status():
    """Get system status and statistics"""
    
    stats = {}
    
    # Get table counts
    tables = ['parcels', 'sales', 'entities', 'recorded_docs', 'jobs']
    
    for table in tables:
        try:
            result = await db.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = result['count']
        except:
            stats[table] = 0
    
    # Get recent activity
    try:
        recent_activity = await db.fetch_many(
            """
            SELECT 
                'parcel' as type,
                folio as id,
                updated_at as timestamp
            FROM parcels
            WHERE updated_at > NOW() - INTERVAL '24 hours'
            UNION ALL
            SELECT 
                'entity' as type,
                id::text,
                updated_at
            FROM entities
            WHERE updated_at > NOW() - INTERVAL '24 hours'
            ORDER BY timestamp DESC
            LIMIT 10
            """
        )
        stats['recent_activity'] = recent_activity
    except:
        stats['recent_activity'] = []
    
    # Get scoring statistics
    try:
        score_stats = await db.fetch_one(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(score) as scored,
                AVG(score) as avg_score,
                MIN(score) as min_score,
                MAX(score) as max_score
            FROM parcels
            """
        )
        stats['scoring'] = score_stats
    except:
        stats['scoring'] = {}
    
    return {
        "timestamp": datetime.now().isoformat(),
        "statistics": stats
    }


@router.post("/health/ping")
async def ping():
    """Simple ping endpoint for uptime monitoring"""
    return {"pong": datetime.now().isoformat()}