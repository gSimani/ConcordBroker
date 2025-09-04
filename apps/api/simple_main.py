"""
Simplified ConcordBroker API for local development
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
from datetime import datetime

app = FastAPI(
    title="ConcordBroker API",
    description="Real Estate Investment Intelligence Platform",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    company: Optional[str] = None

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class PropertySearchRequest(BaseModel):
    city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    property_type: Optional[str] = None
    limit: int = 20
    offset: int = 0

class Property(BaseModel):
    folio: str
    owner_name: str
    site_addr: str
    city: str
    assessed_value: float
    lot_size: float
    year_built: Optional[int]
    use_code: str
    use_desc: str
    zoning: Optional[str]

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "concordbroker-api"
    }

# Auth endpoints
@app.post("/api/v1/auth/signup")
async def sign_up(request: SignUpRequest):
    """Sign up a new user"""
    # For demo, just return success
    return {
        "success": True,
        "message": "Account created successfully. Please check your email for verification.",
        "user_id": "demo-user-123",
        "email": request.email
    }

@app.post("/api/v1/auth/signin")
async def sign_in(request: SignInRequest):
    """Sign in a user"""
    # For demo, return mock tokens
    return {
        "success": True,
        "access_token": "demo-access-token",
        "refresh_token": "demo-refresh-token",
        "user_id": "demo-user-123",
        "email": request.email
    }

@app.post("/api/v1/auth/signout")
async def sign_out():
    """Sign out current user"""
    return {"success": True, "message": "Signed out successfully"}

@app.get("/api/v1/auth/me")
async def get_current_user():
    """Get current user info"""
    return {
        "id": "demo-user-123",
        "email": "demo@concordbroker.com",
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {"full_name": "Demo User"}
    }

# Property search
@app.get("/api/v1/parcels/search", response_model=List[Property])
async def search_properties(
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    property_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Search for properties"""
    # Return mock data for demo
    mock_properties = [
        Property(
            folio="494210010010",
            owner_name="INVESTMENT GROUP LLC",
            site_addr="123 MAIN ST",
            city="FORT LAUDERDALE",
            assessed_value=450000.00,
            lot_size=7500.0,
            year_built=1975,
            use_code="0100",
            use_desc="SINGLE FAMILY",
            zoning="RS-8"
        ),
        Property(
            folio="494210020020",
            owner_name="DEVELOPMENT PARTNERS",
            site_addr="456 OAK AVE",
            city="HOLLYWOOD",
            assessed_value=325000.00,
            lot_size=6200.0,
            year_built=1982,
            use_code="0200",
            use_desc="MOBILE HOME",
            zoning="RM-15"
        ),
        Property(
            folio="494210030030",
            owner_name="SUNSHINE ESTATES LLC",
            site_addr="789 PALM DR",
            city="POMPANO BEACH",
            assessed_value=580000.00,
            lot_size=9800.0,
            year_built=1990,
            use_code="0300",
            use_desc="MULTI-FAMILY",
            zoning="RM-25"
        ),
        Property(
            folio="494210040040",
            owner_name="COASTAL PROPERTIES INC",
            site_addr="321 BEACH BLVD",
            city="DEERFIELD BEACH",
            assessed_value=750000.00,
            lot_size=12000.0,
            year_built=1995,
            use_code="0400",
            use_desc="CONDOMINIUM",
            zoning="B-3"
        ),
        Property(
            folio="494210050050",
            owner_name="PRIME REAL ESTATE",
            site_addr="555 COMMERCE WAY",
            city="DAVIE",
            assessed_value=920000.00,
            lot_size=15000.0,
            year_built=2000,
            use_code="1700",
            use_desc="OFFICE BUILDING",
            zoning="B-3"
        )
    ]
    
    # Filter by city if provided
    if city:
        mock_properties = [p for p in mock_properties if city.upper() in p.city.upper()]
    
    # Filter by price range
    if min_price:
        mock_properties = [p for p in mock_properties if p.assessed_value >= min_price]
    if max_price:
        mock_properties = [p for p in mock_properties if p.assessed_value <= max_price]
    
    # Apply pagination
    return mock_properties[offset:offset + limit]

# Analytics endpoints
@app.get("/api/v1/analytics/market-trends")
async def get_market_trends():
    """Get market trends data"""
    return {
        "trends": [
            {"month": "Jan", "value": 450000, "volume": 120},
            {"month": "Feb", "value": 465000, "volume": 135},
            {"month": "Mar", "value": 478000, "volume": 142},
            {"month": "Apr", "value": 492000, "volume": 155},
            {"month": "May", "value": 505000, "volume": 168},
            {"month": "Jun", "value": 518000, "volume": 175}
        ],
        "average_price": 485000,
        "total_volume": 895
    }

@app.get("/api/v1/analytics/top-opportunities")
async def get_top_opportunities():
    """Get top investment opportunities"""
    return [
        {
            "folio": "494210010010",
            "address": "123 MAIN ST, FORT LAUDERDALE",
            "score": 92,
            "potential_roi": 18.5,
            "price": 450000
        },
        {
            "folio": "494210050050",
            "address": "555 COMMERCE WAY, DAVIE",
            "score": 88,
            "potential_roi": 15.2,
            "price": 920000
        },
        {
            "folio": "494210040040",
            "address": "321 BEACH BLVD, DEERFIELD BEACH",
            "score": 85,
            "potential_roi": 14.8,
            "price": 750000
        }
    ]

@app.get("/api/v1/analytics/city-statistics")
async def get_city_statistics():
    """Get statistics by city"""
    return [
        {"city": "FORT LAUDERDALE", "count": 2845, "avg_value": 485000},
        {"city": "HOLLYWOOD", "count": 2134, "avg_value": 425000},
        {"city": "POMPANO BEACH", "count": 1876, "avg_value": 395000},
        {"city": "DEERFIELD BEACH", "count": 1234, "avg_value": 520000},
        {"city": "DAVIE", "count": 987, "avg_value": 445000}
    ]

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ConcordBroker API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)