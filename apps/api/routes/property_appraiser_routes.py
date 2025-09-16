"""
Property Appraiser Routes - FastAPI endpoints for Property Appraiser data
Integrates with Supabase property_assessments table
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
from supabase import create_client, Client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/property-appraiser", tags=["property-appraiser"])

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    if not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration missing")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@router.get("/search")
async def search_properties(
    q: Optional[str] = Query(None, description="Search query (address, owner, parcel ID)"),
    county: Optional[str] = Query(None, description="County code or name"),
    min_value: Optional[float] = Query(None, description="Minimum taxable value"),
    max_value: Optional[float] = Query(None, description="Maximum taxable value"),
    property_type: Optional[str] = Query(None, description="Property use code"),
    limit: int = Query(100, le=1000, description="Max results to return"),
    offset: int = Query(0, description="Offset for pagination")
) -> Dict[str, Any]:
    """
    Search Property Appraiser data with filters
    """
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("property_assessments").select("*")
        
        # Apply search filter
        if q:
            # Search across multiple fields
            search_filter = f"owner_name.ilike.%{q}%,property_address.ilike.%{q}%,parcel_id.eq.{q}"
            query = query.or_(search_filter)
        
        # Apply county filter
        if county:
            if len(county) == 2:  # County code
                query = query.eq("county_code", county)
            else:  # County name
                query = query.ilike("county_name", f"%{county}%")
        
        # Apply value range filters
        if min_value:
            query = query.gte("taxable_value", min_value)
        if max_value:
            query = query.lte("taxable_value", max_value)
        
        # Apply property type filter
        if property_type:
            query = query.eq("property_use_code", property_type)
        
        # Apply pagination
        query = query.order("taxable_value", desc=True).range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        return {
            "success": True,
            "count": len(response.data),
            "properties": response.data,
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Property search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/property/{parcel_id}")
async def get_property_details(
    parcel_id: str,
    county_code: Optional[str] = Query(None, description="County code for faster lookup")
) -> Dict[str, Any]:
    """
    Get detailed property information by parcel ID
    """
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table("property_assessments").select("*").eq("parcel_id", parcel_id)
        
        # Add county filter if provided (faster query)
        if county_code:
            query = query.eq("county_code", county_code)
        
        # Execute query
        response = query.execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        property_data = response.data[0]
        
        # Get additional data (sales, owners if available)
        sales_data = []
        owner_data = []
        
        try:
            # Get sales history
            sales_response = supabase.table("property_sales").select("*")\
                .eq("parcel_id", parcel_id)\
                .order("sale_date", desc=True)\
                .limit(10)\
                .execute()
            sales_data = sales_response.data
        except:
            pass
        
        try:
            # Get owner history
            owner_response = supabase.table("property_owners").select("*")\
                .eq("parcel_id", parcel_id)\
                .execute()
            owner_data = owner_response.data
        except:
            pass
        
        return {
            "success": True,
            "property": property_data,
            "sales_history": sales_data,
            "owners": owner_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Property details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_property_statistics(
    county_code: Optional[str] = Query(None, description="Filter by county")
) -> Dict[str, Any]:
    """
    Get property statistics and analytics
    """
    try:
        supabase = get_supabase_client()
        
        # Base query
        query = supabase.table("property_assessments").select("county_name, taxable_value")
        
        if county_code:
            query = query.eq("county_code", county_code)
        
        response = query.execute()
        data = response.data
        
        if not data:
            return {
                "success": True,
                "statistics": {
                    "total_properties": 0,
                    "total_value": 0,
                    "average_value": 0
                }
            }
        
        # Calculate statistics
        total_properties = len(data)
        values = [p["taxable_value"] for p in data if p["taxable_value"]]
        total_value = sum(values)
        avg_value = total_value / len(values) if values else 0
        
        # Group by county
        county_stats = {}
        for prop in data:
            county = prop["county_name"] or "Unknown"
            if county not in county_stats:
                county_stats[county] = {
                    "count": 0,
                    "total_value": 0,
                    "values": []
                }
            county_stats[county]["count"] += 1
            if prop["taxable_value"]:
                county_stats[county]["total_value"] += prop["taxable_value"]
                county_stats[county]["values"].append(prop["taxable_value"])
        
        # Calculate county averages
        for county in county_stats:
            values = county_stats[county]["values"]
            county_stats[county]["average_value"] = sum(values) / len(values) if values else 0
            del county_stats[county]["values"]  # Remove raw values from response
        
        return {
            "success": True,
            "statistics": {
                "total_properties": total_properties,
                "total_value": total_value,
                "average_value": avg_value,
                "by_county": county_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-properties")
async def get_top_properties(
    county_code: Optional[str] = Query(None, description="Filter by county"),
    limit: int = Query(10, le=100, description="Number of properties to return")
) -> Dict[str, Any]:
    """
    Get top properties by value
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table("property_assessments").select(
            "parcel_id, owner_name, property_address, property_city, "
            "county_name, taxable_value, total_sq_ft, year_built"
        )
        
        if county_code:
            query = query.eq("county_code", county_code)
        
        # Get top properties by value
        response = query.order("taxable_value", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "count": len(response.data),
            "properties": response.data
        }
        
    except Exception as e:
        logger.error(f"Top properties error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent-sales")
async def get_recent_sales(
    county_code: Optional[str] = Query(None, description="Filter by county"),
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(50, le=200, description="Number of sales to return")
) -> Dict[str, Any]:
    """
    Get recent property sales
    """
    try:
        supabase = get_supabase_client()
        
        # Calculate date threshold
        from datetime import datetime, timedelta
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        
        query = supabase.table("property_sales").select(
            "*, property_assessments!inner(owner_name, property_address, property_city)"
        )
        
        if county_code:
            query = query.eq("county_code", county_code)
        
        # Get recent sales
        response = query.gte("sale_date", date_threshold)\
            .order("sale_date", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "success": True,
            "count": len(response.data),
            "sales": response.data
        }
        
    except Exception as e:
        logger.error(f"Recent sales error: {e}")
        # Return empty result if sales table doesn't exist yet
        return {
            "success": True,
            "count": 0,
            "sales": []
        }

@router.get("/counties")
async def get_counties() -> Dict[str, Any]:
    """
    Get list of available counties with property counts
    """
    try:
        supabase = get_supabase_client()
        
        # Get unique counties with counts
        response = supabase.table("property_assessments")\
            .select("county_code, county_name")\
            .execute()
        
        # Count by county
        county_counts = {}
        for prop in response.data:
            key = f"{prop['county_code']}_{prop['county_name']}"
            if key not in county_counts:
                county_counts[key] = {
                    "county_code": prop["county_code"],
                    "county_name": prop["county_name"],
                    "property_count": 0
                }
            county_counts[key]["property_count"] += 1
        
        counties = list(county_counts.values())
        counties.sort(key=lambda x: x["property_count"], reverse=True)
        
        return {
            "success": True,
            "count": len(counties),
            "counties": counties
        }
        
    except Exception as e:
        logger.error(f"Counties error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync-status")
async def get_sync_status() -> Dict[str, Any]:
    """
    Get Property Appraiser data sync status
    """
    try:
        supabase = get_supabase_client()
        
        # Get last sync info
        response = supabase.table("property_sync_log")\
            .select("*")\
            .eq("status", "completed")\
            .order("processed_at", desc=True)\
            .limit(1)\
            .execute()
        
        last_sync = response.data[0] if response.data else None
        
        # Get total property count
        count_response = supabase.table("property_assessments")\
            .select("count", count="exact")\
            .execute()
        
        return {
            "success": True,
            "last_sync": last_sync["processed_at"] if last_sync else None,
            "total_properties": count_response.count,
            "sync_status": "active" if last_sync else "pending"
        }
        
    except Exception as e:
        logger.error(f"Sync status error: {e}")
        # Return basic status if sync tables don't exist yet
        return {
            "success": True,
            "last_sync": None,
            "total_properties": 0,
            "sync_status": "not_configured"
        }