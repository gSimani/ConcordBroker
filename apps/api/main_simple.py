"""
ConcordBroker FastAPI Backend - Simplified Localhost Version
Direct implementation without complex imports
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ConcordBroker API",
    description="Real Estate Intelligence Platform - Address-Based Property Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for localhost
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"  # Allow all for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for testing
mock_properties = [
    {
        "id": 1,
        "parcel_id": "1234567890",
        "phy_addr1": "123 Main Street",
        "phy_city": "Fort Lauderdale",
        "phy_zipcd": "33301",
        "own_name": "John Doe",
        "property_type": "Residential",
        "jv": 450000,
        "tv_sd": 400000,
        "lnd_val": 150000,
        "tot_lvg_area": 2500,
        "lnd_sqfoot": 7500,
        "act_yr_blt": 2010
    },
    {
        "id": 2,
        "parcel_id": "0987654321",
        "phy_addr1": "456 Ocean Blvd",
        "phy_city": "Hollywood",
        "phy_zipcd": "33019",
        "own_name": "Jane Smith",
        "property_type": "Commercial",
        "jv": 1250000,
        "tv_sd": 1100000,
        "lnd_val": 500000,
        "tot_lvg_area": 5000,
        "lnd_sqfoot": 10000,
        "act_yr_blt": 2015
    },
    {
        "id": 3,
        "parcel_id": "5555555555",
        "phy_addr1": "789 Park Ave",
        "phy_city": "Pompano Beach",
        "phy_zipcd": "33060",
        "own_name": "ABC Corporation",
        "property_type": "Residential",
        "jv": 325000,
        "tv_sd": 300000,
        "lnd_val": 100000,
        "tot_lvg_area": 1800,
        "lnd_sqfoot": 6000,
        "act_yr_blt": 2005
    }
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ConcordBroker API - Development Server",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "endpoints": {
            "properties": "/api/properties",
            "search": "/api/properties/search",
            "dashboard": "/api/properties/stats/overview"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api": "running",
        "environment": "development",
        "timestamp": datetime.now().isoformat()
    }

# Property endpoints
@app.get("/api/properties/search")
async def search_properties(
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0)
) -> Dict:
    """Search properties by address and other criteria"""
    
    # Filter mock data based on criteria
    results = mock_properties.copy()
    
    if city:
        results = [p for p in results if city.lower() in p["phy_city"].lower()]
    if address:
        results = [p for p in results if address.lower() in p["phy_addr1"].lower()]
    if property_type:
        results = [p for p in results if property_type.lower() in p["property_type"].lower()]
    if min_value:
        results = [p for p in results if p["jv"] >= min_value]
    if max_value:
        results = [p for p in results if p["jv"] <= max_value]
    
    # Apply pagination
    paginated = results[offset:offset + limit]
    
    return {
        "properties": paginated,
        "total": len(results),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/properties/{property_id}")
async def get_property(property_id: int) -> Dict:
    """Get property by ID"""
    for prop in mock_properties:
        if prop["id"] == property_id:
            return prop
    raise HTTPException(status_code=404, detail="Property not found")

@app.get("/api/properties/address/{address}")
async def get_property_by_address(
    address: str,
    city: Optional[str] = None
) -> Dict:
    """Get property by street address"""
    for prop in mock_properties:
        if address.lower() in prop["phy_addr1"].lower():
            if not city or city.lower() in prop["phy_city"].lower():
                return prop
    raise HTTPException(status_code=404, detail="Property not found")

@app.get("/api/properties/parcel/{parcel_id}")
async def get_property_by_parcel(parcel_id: str) -> Dict:
    """Get property by parcel ID"""
    for prop in mock_properties:
        if prop["parcel_id"] == parcel_id:
            return prop
    raise HTTPException(status_code=404, detail="Property not found")

# Dashboard Statistics
@app.get("/api/properties/stats/overview")
async def get_overview_statistics() -> Dict:
    """Get dashboard overview statistics"""
    total_value = sum(p["jv"] for p in mock_properties)
    avg_value = total_value / len(mock_properties) if mock_properties else 0
    
    return {
        "totalProperties": len(mock_properties),
        "totalValue": total_value,
        "averageValue": avg_value,
        "recentSales": 5,
        "highValueCount": len([p for p in mock_properties if p["jv"] > 1000000]),
        "watchedCount": 2
    }

@app.get("/api/properties/stats/by-city")
async def get_city_statistics() -> List[Dict]:
    """Get property statistics grouped by city"""
    cities = {}
    for prop in mock_properties:
        city = prop["phy_city"]
        if city not in cities:
            cities[city] = {
                "city": city,
                "propertyCount": 0,
                "totalValue": 0,
                "averageValue": 0,
                "percentChange": 5.5  # Mock data
            }
        cities[city]["propertyCount"] += 1
        cities[city]["totalValue"] += prop["jv"]
    
    # Calculate averages
    for city_data in cities.values():
        if city_data["propertyCount"] > 0:
            city_data["averageValue"] = city_data["totalValue"] / city_data["propertyCount"]
    
    return list(cities.values())

@app.get("/api/properties/stats/by-type")
async def get_type_statistics() -> List[Dict]:
    """Get property statistics grouped by type"""
    types = {}
    total = len(mock_properties)
    
    for prop in mock_properties:
        prop_type = prop["property_type"]
        if prop_type not in types:
            types[prop_type] = {
                "type": prop_type,
                "count": 0,
                "totalValue": 0,
                "averageValue": 0,
                "percentage": 0
            }
        types[prop_type]["count"] += 1
        types[prop_type]["totalValue"] += prop["jv"]
    
    # Calculate percentages and averages
    for type_data in types.values():
        if total > 0:
            type_data["percentage"] = (type_data["count"] / total) * 100
        if type_data["count"] > 0:
            type_data["averageValue"] = type_data["totalValue"] / type_data["count"]
    
    return list(types.values())

@app.get("/api/properties/recent-sales")
async def get_recent_sales(
    days: int = Query(30),
    limit: int = Query(10)
) -> List[Dict]:
    """Get recent property sales"""
    # Return mock sales data
    sales = [
        {
            "id": 1,
            "address": "123 Main Street",
            "city": "Fort Lauderdale",
            "saleDate": "2024-01-15",
            "salePrice": 475000,
            "propertyType": "Residential"
        },
        {
            "id": 2,
            "address": "456 Ocean Blvd",
            "city": "Hollywood",
            "saleDate": "2024-01-10",
            "salePrice": 1300000,
            "propertyType": "Commercial"
        },
        {
            "id": 3,
            "address": "789 Park Ave",
            "city": "Pompano Beach",
            "saleDate": "2024-01-05",
            "salePrice": 350000,
            "propertyType": "Residential"
        }
    ]
    return sales[:limit]

@app.get("/api/properties/high-value")
async def get_high_value_properties(
    min_value: float = Query(1000000),
    limit: int = Query(20)
) -> List[Dict]:
    """Get high-value properties"""
    high_value = [p for p in mock_properties if p["jv"] >= min_value]
    return high_value[:limit]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)