"""
Tax Deed API Endpoints
Provides REST API for tax deed auction data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/tax-deed", tags=["tax-deed"])

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
supabase_key = os.getenv('SUPABASE_ANON_KEY')

if supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    logger.warning("Supabase credentials not found")
    supabase = None


@router.get("/properties")
async def get_properties(
    auction_date: Optional[str] = Query(None, description="Filter by auction date (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filter by status (Active, Sold, Cancelled)"),
    is_homestead: Optional[bool] = Query(None, description="Filter by homestead status"),
    min_bid: Optional[float] = Query(None, description="Minimum opening bid"),
    max_bid: Optional[float] = Query(None, description="Maximum opening bid"),
    search: Optional[str] = Query(None, description="Search in address, parcel, or applicant"),
    limit: int = Query(100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip")
):
    """Get tax deed properties with filters"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Start with base query
        query = supabase.table('tax_deed_properties_with_contacts').select('*')
        
        # Apply filters
        if auction_date:
            query = query.eq('auction_date', auction_date)
        
        if status:
            query = query.eq('status', status)
        
        if is_homestead is not None:
            query = query.eq('is_homestead', is_homestead)
        
        if min_bid is not None:
            query = query.gte('opening_bid', min_bid)
        
        if max_bid is not None:
            query = query.lte('opening_bid', max_bid)
        
        if search:
            # Search in multiple fields
            search_term = f"%{search}%"
            query = query.or_(
                f"situs_address.ilike.{search_term},"
                f"parcel_number.ilike.{search_term},"
                f"applicant_name.ilike.{search_term}"
            )
        
        # Apply pagination and ordering
        query = query.order('auction_date', desc=True).order('opening_bid', desc=True)
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        return response.data
        
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auction-dates")
async def get_auction_dates():
    """Get all available auction dates"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        # Get unique auction dates with counts
        response = supabase.table('tax_deed_properties').select('auction_date').execute()
        
        if not response.data:
            return []
        
        # Process dates and count properties
        date_counts = {}
        for row in response.data:
            date_str = row.get('auction_date')
            if date_str:
                date_counts[date_str] = date_counts.get(date_str, 0) + 1
        
        # Format results
        results = []
        for date_str, count in sorted(date_counts.items(), reverse=True):
            try:
                auction_date = datetime.fromisoformat(date_str)
                results.append({
                    'date': date_str,
                    'description': auction_date.strftime('%B %Y Tax Deed Sale'),
                    'count': count,
                    'is_past': auction_date.date() < datetime.now().date()
                })
            except:
                pass
        
        return results
        
    except Exception as e:
        logger.error(f"Error fetching auction dates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape")
async def trigger_scrape():
    """Manually trigger a scrape of tax deed auctions"""
    
    try:
        return {
            "success": True,
            "message": "Scraping endpoint ready - implement scraper integration",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering scrape: {e}")
        raise HTTPException(status_code=500, detail=str(e))