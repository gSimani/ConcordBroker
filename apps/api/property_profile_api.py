"""
Property Profile API
FastAPI endpoints for property profile data
"""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import logging

from property_profile_service import PropertyProfileService, PropertyProfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ConcordBroker Property Profile API",
    description="Comprehensive property data aggregation API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
profile_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global profile_service
    profile_service = PropertyProfileService()
    await profile_service.initialize()
    logger.info("Property Profile Service initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Close database connections
    pass

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "active",
        "service": "ConcordBroker Property Profile API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/property/profile/{city}/{address}")
async def get_property_profile(
    city: str = Path(..., description="City name"),
    address: str = Path(..., description="Street address"),
    state: str = Query("FL", description="State code")
) -> Dict:
    """
    Get comprehensive property profile by address
    
    Example: /api/property/profile/fort-lauderdale/123-main-street
    """
    try:
        # Format address (replace hyphens with spaces)
        formatted_address = address.replace("-", " ")
        formatted_city = city.replace("-", " ")
        
        logger.info(f"Fetching profile for: {formatted_address}, {formatted_city}, {state}")
        
        # Get property profile
        profile = await profile_service.get_property_profile(
            address=formatted_address,
            city=formatted_city,
            state=state
        )
        
        # Convert to dict for JSON response
        profile_dict = profile_service.to_dict(profile)
        
        return {
            "success": True,
            "data": profile_dict,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting property profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property/search")
async def search_properties(
    q: str = Query(..., description="Search query"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    property_type: Optional[str] = Query(None, description="Property type"),
    limit: int = Query(20, description="Result limit")
) -> Dict:
    """
    Search for properties
    """
    try:
        # This would search across multiple data sources
        results = []
        
        # Add search logic here
        
        return {
            "success": True,
            "query": q,
            "results": results,
            "count": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property/investment-opportunities")
async def get_investment_opportunities(
    min_score: int = Query(70, description="Minimum investment score"),
    include_distressed: bool = Query(True, description="Include distressed properties"),
    include_reo: bool = Query(True, description="Include REO properties"),
    max_nav: float = Query(5000, description="Maximum NAV assessment"),
    limit: int = Query(50, description="Result limit")
) -> Dict:
    """
    Get top investment opportunities based on scoring
    """
    try:
        # Query properties matching criteria
        opportunities = []
        
        # This would query the database for high-scoring properties
        # Add implementation based on your database structure
        
        return {
            "success": True,
            "opportunities": opportunities,
            "count": len(opportunities),
            "criteria": {
                "min_score": min_score,
                "include_distressed": include_distressed,
                "include_reo": include_reo,
                "max_nav": max_nav
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property/market-analysis/{city}")
async def get_market_analysis(
    city: str = Path(..., description="City name"),
    period_days: int = Query(30, description="Analysis period in days")
) -> Dict:
    """
    Get market analysis for a city
    """
    try:
        formatted_city = city.replace("-", " ")
        
        # Aggregate market data
        analysis = {
            "city": formatted_city,
            "period_days": period_days,
            "total_sales": 0,
            "avg_sale_price": 0,
            "median_sale_price": 0,
            "distressed_rate": 0,
            "bank_sale_rate": 0,
            "avg_days_on_market": 0,
            "price_trend": "stable",
            "top_neighborhoods": [],
            "investor_activity": {
                "llc_purchases": 0,
                "corp_purchases": 0,
                "trust_purchases": 0,
                "individual_purchases": 0
            }
        }
        
        # Add market analysis logic here
        
        return {
            "success": True,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/property/owner/{owner_name}")
async def get_owner_portfolio(
    owner_name: str = Path(..., description="Owner name")
) -> Dict:
    """
    Get all properties owned by a person or entity
    """
    try:
        # Search for properties by owner
        properties = []
        
        # Add owner search logic here
        
        return {
            "success": True,
            "owner": owner_name,
            "properties": properties,
            "count": len(properties),
            "total_value": sum(p.get('market_value', 0) for p in properties),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting owner portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/property/alert")
async def create_property_alert(
    address: str,
    city: str,
    alert_types: List[str]
) -> Dict:
    """
    Create alerts for property changes
    """
    try:
        # Create alert subscription
        alert_id = f"alert_{datetime.now().timestamp()}"
        
        return {
            "success": True,
            "alert_id": alert_id,
            "address": address,
            "city": city,
            "alert_types": alert_types,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/status")
async def get_data_status() -> Dict:
    """
    Get status of all data sources
    """
    try:
        status = {
            "bcpa": "unknown",
            "sdf": "unknown",
            "nav": "unknown",
            "tpp": "unknown",
            "sunbiz": "unknown",
            "official_records": "unknown",
            "dor": "unknown"
        }
        
        # Check each data source
        if profile_service:
            for source, db in profile_service.data_sources.items():
                if db:
                    status[source] = "connected"
                else:
                    status[source] = "disconnected"
        
        return {
            "success": True,
            "data_sources": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting data status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn property_profile_api:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)