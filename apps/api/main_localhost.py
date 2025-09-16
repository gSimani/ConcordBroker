"""
ConcordBroker API - Localhost Version with Real Database
Connects to Supabase and serves real property data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../../.env.new' if os.path.exists('../../.env.new') else '../../.env')

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import the fixed Supabase client
from supabase_client import get_supabase_client

app = FastAPI(
    title="ConcordBroker API - Localhost",
    description="Real Estate Property Data API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for localhost development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers to the client
)

# Initialize Supabase client
try:
    supabase = get_supabase_client()
    print("[SUCCESS] Connected to Supabase")
except Exception as e:
    print(f"[ERROR] Failed to connect to Supabase: {e}")
    supabase = None

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "ConcordBroker API - Localhost",
        "status": "running",
        "database": "connected" if supabase else "disconnected",
        "docs": "http://localhost:8000/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if supabase else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/properties")
async def get_properties(
    limit: int = Query(100, description="Number of properties to return"),
    offset: int = Query(0, description="Number of properties to skip"),
    city: Optional[str] = Query(None, description="Filter by city"),
    min_price: Optional[float] = Query(None, description="Minimum property value"),
    max_price: Optional[float] = Query(None, description="Maximum property value")
):
    """Get list of properties from database"""
    
    if not supabase:
        # Return mock data if database is not connected
        return {
            "data": [
                {
                    "id": 1,
                    "parcel_id": "MOCK-001",
                    "address": "123 Mock Street",
                    "city": "Fort Lauderdale",
                    "owner_name": "Sample Owner",
                    "just_value": 450000,
                    "assessed_value": 400000,
                    "year_built": 2010
                }
            ],
            "count": 1,
            "message": "Database not connected - showing mock data"
        }
    
    try:
        # Build query
        query = supabase.table('florida_parcels').select('*')
        
        # Apply filters
        if city:
            query = query.ilike('phy_city', f'%{city}%')
        if min_price:
            query = query.gte('just_value', min_price)
        if max_price:
            query = query.lte('just_value', max_price)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        # Format response
        properties = []
        for row in result.data:
            properties.append({
                "id": row.get('id'),
                "parcel_id": row.get('parcel_id'),
                "address": row.get('phy_addr1'),
                "city": row.get('phy_city'),
                "zip_code": row.get('phy_zipcd'),
                "owner_name": row.get('owner_name'),
                "owner_address": row.get('owner_addr1'),
                "owner_city": row.get('owner_city'),
                "owner_state": row.get('owner_state'),
                "owner_zip": row.get('owner_zip'),
                "just_value": row.get('just_value'),
                "assessed_value": row.get('assessed_value'),
                "taxable_value": row.get('taxable_value'),
                "land_value": row.get('land_value'),
                "building_value": row.get('building_value'),
                "year_built": row.get('year_built'),
                "square_feet": row.get('total_living_area'),
                "land_sqft": row.get('land_sqft'),
                "sale_date": row.get('sale_date'),
                "sale_price": row.get('sale_price'),
                "property_use": row.get('property_use')
            })
        
        return {
            "data": properties,
            "count": len(properties),
            "total": result.count if hasattr(result, 'count') else len(properties),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/properties/{parcel_id}")
async def get_property(parcel_id: str):
    """Get a single property by parcel ID"""
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        result = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        row = result.data[0]
        return {
            "id": row.get('id'),
            "parcel_id": row.get('parcel_id'),
            "address": row.get('phy_addr1'),
            "city": row.get('phy_city'),
            "zip_code": row.get('phy_zipcd'),
            "owner_name": row.get('owner_name'),
            "owner_address": row.get('owner_addr1'),
            "owner_city": row.get('owner_city'),
            "owner_state": row.get('owner_state'),
            "owner_zip": row.get('owner_zip'),
            "just_value": row.get('just_value'),
            "assessed_value": row.get('assessed_value'),
            "taxable_value": row.get('taxable_value'),
            "land_value": row.get('land_value'),
            "building_value": row.get('building_value'),
            "year_built": row.get('year_built'),
            "square_feet": row.get('total_living_area'),
            "land_sqft": row.get('land_sqft'),
            "sale_date": row.get('sale_date'),
            "sale_price": row.get('sale_price'),
            "property_use": row.get('property_use')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/properties/search")
async def search_properties(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, description="Number of results")
):
    """Search properties by address or owner name"""
    
    if not supabase:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Search in multiple fields
        result = supabase.table('florida_parcels').select('*').or_(
            f"phy_addr1.ilike.%{q}%,"
            f"owner_name.ilike.%{q}%,"
            f"parcel_id.ilike.%{q}%"
        ).limit(limit).execute()
        
        properties = []
        for row in result.data:
            properties.append({
                "id": row.get('id'),
                "parcel_id": row.get('parcel_id'),
                "address": row.get('phy_addr1'),
                "city": row.get('phy_city'),
                "owner_name": row.get('owner_name'),
                "just_value": row.get('just_value'),
                "year_built": row.get('year_built')
            })
        
        return {
            "data": properties,
            "count": len(properties),
            "query": q
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    
    if not supabase:
        return {"message": "Database not connected"}
    
    try:
        # Get total count
        result = supabase.table('florida_parcels').select('count', count='exact').execute()
        total_count = result.count if hasattr(result, 'count') else 0
        
        # Get sample of cities
        cities_result = supabase.table('florida_parcels').select('phy_city').limit(100).execute()
        cities = list(set([r['phy_city'] for r in cities_result.data if r.get('phy_city')]))
        
        return {
            "total_properties": total_count,
            "cities_available": cities[:10],  # First 10 cities
            "database_status": "connected",
            "message": f"Database contains {total_count} properties"
        }
        
    except Exception as e:
        return {"error": str(e), "database_status": "error"}

# Import datetime for health check
from datetime import datetime

if __name__ == "__main__":
    import uvicorn
    print("Starting ConcordBroker API on http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)