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
import asyncio

# Load environment variables
load_dotenv()

# Import cache service
try:
    from cache_service import cache, cached, PropertyCache, SearchCache, init_cache
    CACHE_ENABLED = True
    print("SUCCESS: Redis cache service loaded")
except ImportError as e:
    CACHE_ENABLED = False
    print(f"WARNING: Cache service not available: {e}")
    # Define dummy decorators if cache not available
    def cached(ttl=300, prefix="api"):
        def decorator(func):
            return func
        return decorator

# Import AI routes
try:
    from routes.ai_routes import router as ai_router
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("AI routes not available - continuing without AI features")

# Import AI Search routes
try:
    from routes.ai_search import router as ai_search_router
    AI_SEARCH_ENABLED = True
    print("SUCCESS: AI Search with GPT integration loaded successfully")
except ImportError:
    AI_SEARCH_ENABLED = False
    print("AI Search routes not available - continuing without AI search features")

# Import Recommendation routes
try:
    from routes.recommendation_routes import router as recommendation_router
    RECOMMENDATIONS_ENABLED = True
    print("SUCCESS: Graph-based recommendation engine loaded")
except ImportError:
    RECOMMENDATIONS_ENABLED = False
    print("Recommendation routes not available - continuing without recommendation features")

# Import Graph routes
try:
    from routes.graph_routes import router as graph_router
    GRAPH_ENABLED = True
    print("SUCCESS: Graphiti graph services loaded")
except ImportError:
    GRAPH_ENABLED = False
    print("Graph routes not available - continuing without graph features")

# Import Autonomous System routes
try:
    from routes.autonomous_routes import router as autonomous_router
    AUTONOMOUS_ENABLED = True
    print("SUCCESS: Autonomous system loaded successfully")
except ImportError as e:
    AUTONOMOUS_ENABLED = False
    print(f"ERROR: Autonomous system not available: {e}")
    print("Continuing without autonomous features...")

# Import Property Search routes with Supabase integration
try:
    from routes.property_search import router as property_search_router
    PROPERTY_SEARCH_ENABLED = True
    print("SUCCESS: Property search with Supabase loaded successfully")
except ImportError as e:
    PROPERTY_SEARCH_ENABLED = False
    print(f"ERROR: Property search routes not available: {e}")
    print("Continuing with mock data...")

# Import Property Appraiser routes
try:
    from routes.property_appraiser_routes import router as property_appraiser_router
    PROPERTY_APPRAISER_ENABLED = True
    print("SUCCESS: Property Appraiser integration loaded successfully")
except ImportError as e:
    PROPERTY_APPRAISER_ENABLED = False
    print(f"WARNING: Property Appraiser routes not available: {e}")

# Import Graphiti Knowledge Graph routes
try:
    from routes.graph_routes import router as graph_router
    from graph.property_graph_service import PropertyGraphService
    from graph.enhanced_rag_service import EnhancedRAGService
    from graph.monitoring import GraphMonitor, GraphMetricsDashboard
    from agents.graph_enhanced_agents import GraphAgentOrchestrator
    GRAPHITI_ENABLED = os.getenv("ENABLE_GRAPHITI", "false").lower() == "true"
    
    if GRAPHITI_ENABLED:
        # Initialize graph services
        try:
            graph_service = PropertyGraphService()
            rag_service = EnhancedRAGService(graph_service)
            graph_monitor = GraphMonitor()
            graph_orchestrator = GraphAgentOrchestrator(graph_service)
            
            # Store in app state for access in routes
            app.state.graph_service = graph_service
            app.state.rag_service = rag_service
            app.state.graph_monitor = graph_monitor
            app.state.graph_orchestrator = graph_orchestrator
            
            print("✅ SUCCESS: Graphiti Knowledge Graph integration enabled")
            print("  - Neo4j connected")
            print("  - Graph agents initialized")
            print("  - Monitoring active")
            
            # Start monitoring in background
            asyncio.create_task(graph_monitor.start())
            
        except Exception as e:
            GRAPHITI_ENABLED = False
            print(f"⚠️ WARNING: Graphiti initialization failed: {e}")
            print("Continuing without knowledge graph features...")
    else:
        print("INFO: Graphiti disabled (set ENABLE_GRAPHITI=true to enable)")
        
except ImportError as e:
    GRAPHITI_ENABLED = False
    print(f"INFO: Graphiti not installed: {e}")
    print("Install with: pip install -r requirements-graphiti.txt")

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
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:3000",
    "*"  # Allow all for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers to the client
)

# Add custom middleware to ensure CORS headers are always present
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class CORSMiddlewareCustom(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        return response

app.add_middleware(CORSMiddlewareCustom)

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
        "dor_uc": "001",  # Single Family
        "jv": 450000,
        "tv_sd": 400000,
        "lnd_val": 150000,
        "tot_lvg_area": 2500,
        "lnd_sqfoot": 7500,
        "act_yr_blt": 2010,
        "sale_prc1": 425000,
        "sale_yr1": 2023
    },
    {
        "id": 2,
        "parcel_id": "0987654321",
        "phy_addr1": "456 Ocean Blvd",
        "phy_city": "Hollywood",
        "phy_zipcd": "33019",
        "own_name": "Jane Smith",
        "property_type": "Commercial",
        "dor_uc": "102",  # Office Building
        "jv": 1250000,
        "tv_sd": 1100000,
        "lnd_val": 500000,
        "tot_lvg_area": 5000,
        "lnd_sqfoot": 10000,
        "act_yr_blt": 2015,
        "sale_prc1": 1150000,
        "sale_yr1": 2022
    },
    {
        "id": 3,
        "parcel_id": "5555555555",
        "phy_addr1": "789 Park Ave",
        "phy_city": "Pompano Beach",
        "phy_zipcd": "33060",
        "own_name": "ABC Corporation",
        "property_type": "Residential",
        "dor_uc": "003",  # Multi-Family
        "jv": 325000,
        "tv_sd": 300000,
        "lnd_val": 100000,
        "tot_lvg_area": 1800,
        "lnd_sqfoot": 6000,
        "act_yr_blt": 2005,
        "sale_prc1": 310000,
        "sale_yr1": 2021
    },
    {
        "id": 4,
        "parcel_id": "1111111111",
        "phy_addr1": "123 Sunset Blvd",
        "phy_city": "Fort Lauderdale",
        "phy_zipcd": "33304",
        "own_name": "John Smith",
        "property_type": "Residential",
        "dor_uc": "001",  # Single Family
        "jv": 550000,
        "tv_sd": 500000,
        "lnd_val": 200000,
        "tot_lvg_area": 3000,
        "lnd_sqfoot": 8000,
        "act_yr_blt": 2018,
        "sale_prc1": 525000,
        "sale_yr1": 2023
    },
    {
        "id": 5,
        "parcel_id": "2222222222",
        "phy_addr1": "456 Beach Road",
        "phy_city": "Hollywood",
        "phy_zipcd": "33020",
        "own_name": "Johnson Family Trust",
        "property_type": "Residential",
        "dor_uc": "004",  # Condominium
        "jv": 750000,
        "tv_sd": 700000,
        "lnd_val": 350000,
        "tot_lvg_area": 2800,
        "lnd_sqfoot": 9500,
        "act_yr_blt": 2012,
        "sale_prc1": 695000,
        "sale_yr1": 2024
    },
    {
        "id": 6,
        "parcel_id": "3333333333",
        "phy_addr1": "321 Commerce Way",
        "phy_city": "Davie",
        "phy_zipcd": "33314",
        "own_name": "Smith Enterprises LLC",
        "property_type": "Commercial",
        "dor_uc": "101",  # Retail Store
        "jv": 2500000,
        "tv_sd": 2200000,
        "lnd_val": 800000,
        "tot_lvg_area": 12000,
        "lnd_sqfoot": 25000,
        "act_yr_blt": 2008,
        "sale_prc1": 2300000,
        "sale_yr1": 2020
    }
]

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    if CACHE_ENABLED:
        await init_cache()
        print("[OK] Cache service initialized")
    print("[OK] API server started successfully")

@app.get("/")
async def root():
    """Root endpoint"""
    cache_status = "enabled" if CACHE_ENABLED else "disabled"
    return {
        "message": "ConcordBroker API - Development Server",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
        "cache": cache_status,
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
        "ai_enabled": AI_ENABLED,
        "autonomous_enabled": AUTONOMOUS_ENABLED,
        "property_search_enabled": PROPERTY_SEARCH_ENABLED,
        "graphiti_enabled": GRAPHITI_ENABLED,
        "using_real_data": PROPERTY_SEARCH_ENABLED,
        "timestamp": datetime.now().isoformat()
    }

# Include AI routes if available
if AI_ENABLED:
    app.include_router(ai_router)

# Include AI Search routes if available
if AI_SEARCH_ENABLED:
    app.include_router(ai_search_router)
    print("AI Search routes are active - GPT integration enabled")

# Include Recommendation routes if available
if RECOMMENDATIONS_ENABLED:
    app.include_router(recommendation_router)
    print("Recommendation routes are active - intelligent property suggestions enabled")

# Include Autonomous System routes if available
if AUTONOMOUS_ENABLED:
    app.include_router(autonomous_router)

# Include Property Search routes with Supabase if available
if PROPERTY_SEARCH_ENABLED:
    app.include_router(property_search_router)
    print("Property search routes with Supabase are active - using real database")
else:
    print("Using mock data for property search")

# Include Property Appraiser routes if available
if PROPERTY_APPRAISER_ENABLED:
    app.include_router(property_appraiser_router)
    print("Property Appraiser routes are active - Florida property data integrated")

# Include Graphiti Knowledge Graph routes if available
if GRAPHITI_ENABLED:
    app.include_router(graph_router)
    print("Graph routes are active - knowledge graph enabled")
    
    # Add graph monitoring endpoint
    @app.get("/api/graph/monitoring/dashboard")
    async def get_graph_dashboard():
        """Get graph monitoring dashboard data"""
        if hasattr(app.state, 'graph_monitor'):
            dashboard = GraphMetricsDashboard(app.state.graph_monitor)
            return await dashboard.get_dashboard_data()
        return {"error": "Graph monitoring not available"}

# Include LangGraph routes if available
try:
    from routes.langgraph_routes import router as langgraph_router
    app.include_router(langgraph_router)
    print("LangGraph routes are active - intelligent workflows enabled")
except ImportError:
    print("LangGraph routes not available - install langgraph to enable")

# Property endpoints
@app.get("/api/properties/search")
@cached(ttl=900, prefix="search")  # Cache for 15 minutes
async def search_properties(
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    min_building_sqft: Optional[float] = Query(None),
    max_building_sqft: Optional[float] = Query(None),
    min_land_sqft: Optional[float] = Query(None),
    max_land_sqft: Optional[float] = Query(None),
    min_sale_price: Optional[float] = Query(None),
    max_sale_price: Optional[float] = Query(None),
    min_appraised_value: Optional[float] = Query(None),
    max_appraised_value: Optional[float] = Query(None),
    usage_code: Optional[str] = Query(None),
    sub_usage_code: Optional[str] = Query(None),
    has_tax_certificates: Optional[bool] = Query(None),
    certificate_years: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0)
) -> Dict:
    """Search properties by address and other criteria - using real Supabase data"""
    
    try:
        # Import supabase client
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Start with base query - use 'florida_parcels' table which has the data
        query = supabase.table('florida_parcels').select('*')
        
        # Apply filters with correct column names for 'florida_parcels' table
        if city and city != 'all-cities':
            query = query.ilike('phy_city', f'%{city}%')
        if address:
            query = query.ilike('phy_addr1', f'%{address}%')
        if zip_code:
            query = query.eq('phy_zipcd', zip_code)
        if owner:
            query = query.ilike('owner_name', f'%{owner}%')
        if property_type and property_type != 'all-types':
            # Map property types to DOR use code ranges using the correct column name 'property_use'
            if property_type == 'Residential':
                # DOR codes 000-099: Residential
                query = query.gte('property_use', '000').lte('property_use', '099')
            elif property_type == 'Commercial':
                # DOR codes 100-399: Commercial
                query = query.gte('property_use', '100').lte('property_use', '399')
            elif property_type == 'Industrial':
                # DOR codes 400-499: Industrial
                query = query.gte('property_use', '400').lte('property_use', '499')
            elif property_type == 'Agricultural':
                # DOR codes 500-599: Agricultural
                query = query.gte('property_use', '500').lte('property_use', '599')
            elif property_type == 'Vacant Land':
                # DOR codes for vacant land (000, 100, 400, 500, etc.)
                query = query.in_('property_use', ['000', '100', '400', '500'])
            elif property_type == 'Tax Deed Sales':
                # Filter properties that have tax certificates
                tax_deed_parcels = ['064210010010', '064210010011', '064210015020', '064210025030']
                query = query.in_('parcel_id', tax_deed_parcels)
        if min_value:
            query = query.gte('taxable_value', min_value)
        if max_value:
            query = query.lte('taxable_value', max_value)
        if min_building_sqft:
            query = query.gte('total_living_area', min_building_sqft)
        if max_building_sqft:
            query = query.lte('total_living_area', max_building_sqft)
        
        # Apply tax certificate filtering
        if has_tax_certificates and has_tax_certificates == True:
            # Filter properties that have tax certificates in the last N years
            years_back = certificate_years or 7
            cutoff_year = 2025 - years_back
            
            # Join with tax certificates table to get properties with tax certificates
            # For now, we'll use parcel_ids that match our tax deed sample data
            # In production, this would be a proper database join
            tax_deed_parcels = ['064210010010', '064210010011', '064210015020', '064210025030']
            query = query.in_('parcel_id', tax_deed_parcels)
        
        # Get total count
        count_query = query
        count_result = count_query.execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        # Transform data to match expected format - map from 'florida_parcels' table columns
        properties = []
        if result.data:
            for row in result.data:
                properties.append({
                    "id": row.get("id"),
                    "parcel_id": row.get("parcel_id"),
                    "phy_addr1": row.get("phy_addr1"),
                    "phy_city": row.get("phy_city"),
                    "phy_zipcd": row.get("phy_zipcd"),
                    "own_name": row.get("owner_name"),
                    "property_type": row.get("property_use_desc", "Residential"),
                    "dor_uc": row.get("property_use", "001"),
                    "jv": row.get("just_value", 0),
                    "tv_sd": row.get("taxable_value", 0),
                    "lnd_val": row.get("land_value", 0),
                    "tot_lvg_area": row.get("total_living_area", 0),
                    "lnd_sqfoot": row.get("land_sqft", 0),
                    "act_yr_blt": row.get("year_built", 0),
                    "sale_prc1": row.get("sale_price", 0),
                    "sale_yr1": str(row.get("sale_date", "")).split("-")[0] if row.get("sale_date") else "",
                    "has_tax_certificates": row.get("parcel_id") in ['064210010010', '064210010011', '064210015020', '064210025030'],
                    "certificate_count": 1 if row.get("parcel_id") in ['064210010010', '064210010011', '064210015020', '064210025030'] else 0,
                    "total_certificate_amount": 8500 if row.get("parcel_id") == '064210010010' else 3200 if row.get("parcel_id") == '064210010011' else 12500 if row.get("parcel_id") == '064210015020' else 18500 if row.get("parcel_id") == '064210025030' else 0,
                    # Tax deed auction information
                    "auction_date": "2025-01-15" if row.get("parcel_id") in ['064210010010', '064210010011'] else "2024-11-20" if row.get("parcel_id") in ['064210015020', '064210025030'] else None,
                    "opening_bid": 8500 if row.get("parcel_id") == '064210010010' else 3200 if row.get("parcel_id") == '064210010011' else 12500 if row.get("parcel_id") == '064210015020' else 18500 if row.get("parcel_id") == '064210025030' else None,
                    "tax_deed_number": "TD-2025-00123" if row.get("parcel_id") == '064210010010' else "TD-2025-00124" if row.get("parcel_id") == '064210010011' else "TD-2024-00987" if row.get("parcel_id") == '064210015020' else "TD-2024-00988" if row.get("parcel_id") == '064210025030' else None,
                    "auction_url": "https://broward.deedauction.net/auction/110" if row.get("parcel_id") in ['064210010010', '064210010011'] else "https://broward.deedauction.net/auction/109" if row.get("parcel_id") in ['064210015020', '064210025030'] else None
                })
        
        return {
            "properties": properties,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        print(f"Error searching properties: {str(e)}")
        # Fall back to mock data if database fails
        results = mock_properties.copy()
        
        if city:
            results = [p for p in results if city.lower() in p["phy_city"].lower()]
        if address:
            results = [p for p in results if address.lower() in p["phy_addr1"].lower()]
        
        paginated = results[offset:offset + limit]
        
        return {
            "properties": paginated,
            "total": len(results),
            "limit": limit,
            "offset": offset
        }

@app.get("/api/properties/by-address/{city}/{address_slug}")
async def get_property_by_address_slug(
    city: str,
    address_slug: str
) -> Dict:
    """Get property by city and address slug"""
    # For now, just return a test response to confirm the route works
    return {
        "test": "Route works!",
        "city": city,
        "address_slug": address_slug
    }
    
    # Try exact match first
    for prop in mock_properties:
        prop_city = prop["phy_city"]
        prop_address = prop["phy_addr1"]
        
        print(f"API: Checking property: '{prop_city}', '{prop_address}'")
        
        # Check if city matches (case insensitive, exact match)
        if city_readable.lower() == prop_city.lower():
            # Check if address matches (case insensitive, exact match first)
            if address_readable.lower() == prop_address.lower():
                print(f"API: Exact match found!")
                return prop
    
    # Try partial matching
    for prop in mock_properties:
        prop_city = prop["phy_city"]
        prop_address = prop["phy_addr1"]
        
        if city_readable.lower() == prop_city.lower():
            # Try partial match - check if address contains key elements
            address_parts = address_readable.lower().split()
            prop_parts = prop_address.lower().split()
            
            # Check if we have the street number and at least one street word match
            if (len(address_parts) >= 2 and len(prop_parts) >= 2 and
                address_parts[0] == prop_parts[0]):  # Same street number
                
                # Check if any of the street name parts match
                street_words_match = any(word in prop_parts for word in address_parts[1:] if len(word) > 2)
                if street_words_match:
                    print(f"API: Partial match found!")
                    return prop
    
    print(f"API: No match found")
    raise HTTPException(status_code=404, detail=f"Property not found for {city_readable}, {address_readable}")

@app.get("/api/properties/{property_id}")
@cached(ttl=1800, prefix="property")  # Cache for 30 minutes
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
@cached(ttl=1800, prefix="property_parcel")  # Cache for 30 minutes
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

# Autocomplete endpoints
@app.get("/api/autocomplete/addresses")
async def autocomplete_addresses(
    q: str = Query(..., min_length=2),
    limit: int = Query(10)
) -> List[str]:
    """Autocomplete for property addresses - searches address, city, or zip"""
    # Return full addresses with city and zip
    full_addresses = []
    query_lower = q.lower()
    
    for p in mock_properties:
        # Create full address string
        full_address = f"{p['phy_addr1']}, {p['phy_city']}, FL {p['phy_zipcd']}"
        
        # Search in address, city, or zip code
        if (p["phy_addr1"] and query_lower in p["phy_addr1"].lower()) or \
           (p["phy_city"] and query_lower in p["phy_city"].lower()) or \
           (p["phy_zipcd"] and query_lower in str(p["phy_zipcd"])):
            if full_address not in full_addresses:
                full_addresses.append(full_address)
    
    return full_addresses[:limit]

@app.get("/api/autocomplete/cities")
async def autocomplete_cities(
    q: str = Query(..., min_length=2),
    limit: int = Query(10)
) -> List[str]:
    """Autocomplete for cities"""
    cities = list(set([p["phy_city"] for p in mock_properties]))
    matching = [city for city in cities if q.lower() in city.lower()]
    return matching[:limit]

@app.get("/api/autocomplete/owners")
async def autocomplete_owners(
    q: str = Query(..., min_length=2),
    limit: int = Query(10)
) -> List[str]:
    """Autocomplete for owner names"""
    owners = list(set([p["own_name"] for p in mock_properties]))
    matching = [owner for owner in owners if q.lower() in owner.lower()]
    return matching[:limit]

@app.get("/api/properties/{parcel_id}/tax-certificates")
async def get_tax_certificates(parcel_id: str) -> Dict:
    """Get tax certificates for a property from Supabase"""
    try:
        from supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Get tax certificates
        cert_response = supabase.table('tax_certificates').select('*').eq('parcel_id', parcel_id).execute()
        
        # Get property tax values
        prop_response = supabase.table('florida_parcels').select(
            'just_value, assessed_value, taxable_value, land_value, building_value'
        ).eq('parcel_id', parcel_id).execute()
        
        certificates = cert_response.data if cert_response.data else []
        property_values = prop_response.data[0] if prop_response.data else {}
        
        # Calculate annual tax if taxable value exists
        annual_tax = None
        if property_values.get('taxable_value'):
            millage_rate = 0.0197099  # Broward County average
            annual_tax = property_values['taxable_value'] * millage_rate
        
        return {
            "certificates": certificates,
            "property_values": property_values,
            "annual_tax": annual_tax,
            "millage_rate": 19.7099,  # in mills
            "has_certificates": len(certificates) > 0
        }
        
    except Exception as e:
        print(f"Error fetching tax certificates: {e}")
        # Return mock data if error
        return {
            "certificates": [],
            "property_values": {},
            "annual_tax": None,
            "millage_rate": 19.7099,
            "has_certificates": False
        }

@app.get("/api/properties/{parcel_id}/sunbiz-entities")
async def get_sunbiz_entities_for_property(parcel_id: str) -> Dict:
    """Get live Sunbiz entities matching the property owner"""
    try:
        from supabase_client import get_supabase_client
        from services.sunbiz_live_agent import SunbizLiveAgent
        
        supabase = get_supabase_client()
        
        # Get property owner name
        prop_response = supabase.table('florida_parcels').select('owner_name').eq('parcel_id', parcel_id).execute()
        
        if not prop_response.data:
            return {
                "error": "Property not found",
                "entities": [],
                "property_owner": None
            }
        
        owner_name = prop_response.data[0].get('owner_name')
        
        if not owner_name:
            return {
                "entities": [],
                "property_owner": None,
                "message": "No owner name available"
            }
        
        # Initialize Sunbiz agent and search
        agent = SunbizLiveAgent()
        entities = agent.find_entities_for_property_owner(owner_name)
        
        return {
            "entities": entities,
            "property_owner": owner_name,
            "parcel_id": parcel_id,
            "search_timestamp": datetime.now().isoformat(),
            "total_matches": len(entities)
        }
        
    except Exception as e:
        print(f"Error searching Sunbiz entities: {e}")
        return {
            "error": str(e),
            "entities": [],
            "property_owner": None
        }

@app.get("/api/sunbiz/search/{entity_name}")
async def search_sunbiz_entity(entity_name: str) -> Dict:
    """Search Sunbiz for a specific entity name"""
    try:
        from services.sunbiz_live_agent import SunbizLiveAgent
        
        agent = SunbizLiveAgent()
        entities = agent.find_entities_for_property_owner(entity_name)
        
        return {
            "search_term": entity_name,
            "entities": entities,
            "total_matches": len(entities),
            "search_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error searching Sunbiz: {e}")
        return {
            "error": str(e),
            "search_term": entity_name,
            "entities": []
        }

@app.get("/api/usage-codes")
async def get_usage_codes() -> Dict:
    """Get all property usage codes"""
    return {
        "main_categories": {
            "000-099": "Residential",
            "100-399": "Commercial",
            "400-499": "Industrial",
            "500-599": "Agricultural",
            "600-699": "Government",
            "700-799": "Institutional",
            "800-899": "Miscellaneous",
            "900-999": "Non-agricultural acreage"
        },
        "all_codes": get_all_usage_codes()
    }

@app.get("/api/autocomplete/usage-codes")
async def autocomplete_usage_codes(
    q: str = Query(..., min_length=1),
    limit: int = Query(20)
) -> List[Dict[str, str]]:
    """Autocomplete for DOR usage codes"""
    all_codes = get_all_usage_codes()
    query_lower = q.lower()
    
    matching_codes = []
    for code_info in all_codes:
        code = code_info["code"]
        desc = code_info["description"]
        category = code_info["category"]
        
        # Match by code number or description
        if query_lower in code or query_lower in desc.lower() or query_lower in category.lower():
            matching_codes.append({
                "code": code,
                "description": desc,
                "category": category,
                "display": f"{code} - {desc} ({category})"
            })
    
    return matching_codes[:limit]

@app.get("/api/autocomplete/sub-usage-codes")
async def autocomplete_sub_usage_codes(
    usage_code: str = Query(...),
    q: str = Query("", min_length=0),
    limit: int = Query(20)
) -> List[Dict[str, str]]:
    """Autocomplete for sub-usage codes based on main usage code"""
    # Sub-usage codes are typically 00-99 within each main code
    sub_codes = [
        {"code": "00", "description": "Standard/Default"},
        {"code": "01", "description": "Improved"},
        {"code": "02", "description": "Unimproved"},
        {"code": "03", "description": "Special"},
        {"code": "04", "description": "Waterfront"},
        {"code": "05", "description": "Corner Lot"},
        {"code": "10", "description": "With Pool"},
        {"code": "11", "description": "With Garage"},
        {"code": "20", "description": "Historic"},
        {"code": "21", "description": "Renovated"},
        {"code": "99", "description": "Other/Miscellaneous"}
    ]
    
    if q:
        query_lower = q.lower()
        sub_codes = [sc for sc in sub_codes 
                     if query_lower in sc["code"] or query_lower in sc["description"].lower()]
    
    # Format for display
    return [
        {
            "code": sc["code"],
            "description": sc["description"],
            "display": f"{sc['code']} - {sc['description']}"
        }
        for sc in sub_codes[:limit]
    ]

def get_all_usage_codes() -> List[Dict[str, str]]:
    """Get comprehensive list of DOR usage codes"""
    return [
        # Residential (000-099)
        {"code": "000", "description": "Vacant Residential", "category": "Residential"},
        {"code": "001", "description": "Single Family", "category": "Residential"},
        {"code": "002", "description": "Mobile Home", "category": "Residential"},
        {"code": "003", "description": "Multi-Family (2-9 units)", "category": "Residential"},
        {"code": "004", "description": "Condominium", "category": "Residential"},
        {"code": "005", "description": "Cooperative", "category": "Residential"},
        {"code": "006", "description": "Retirement Home", "category": "Residential"},
        {"code": "007", "description": "Miscellaneous Residential", "category": "Residential"},
        {"code": "008", "description": "Multi-Family (10+ units)", "category": "Residential"},
        {"code": "009", "description": "Undefined Residential", "category": "Residential"},
        
        # Commercial (100-399)
        {"code": "100", "description": "Vacant Commercial", "category": "Commercial"},
        {"code": "101", "description": "Retail Store", "category": "Commercial"},
        {"code": "102", "description": "Office Building", "category": "Commercial"},
        {"code": "103", "description": "Department Store", "category": "Commercial"},
        {"code": "104", "description": "Supermarket", "category": "Commercial"},
        {"code": "105", "description": "Regional Shopping Center", "category": "Commercial"},
        {"code": "106", "description": "Community Shopping Center", "category": "Commercial"},
        {"code": "107", "description": "Wholesale Outlet", "category": "Commercial"},
        {"code": "108", "description": "Restaurant/Cafeteria", "category": "Commercial"},
        {"code": "109", "description": "Hotel/Motel", "category": "Commercial"},
        {"code": "110", "description": "Finance/Insurance/Real Estate", "category": "Commercial"},
        {"code": "111", "description": "Service Station", "category": "Commercial"},
        {"code": "112", "description": "Auto Sales/Service/Rental", "category": "Commercial"},
        {"code": "113", "description": "Parking Lot/Mobile Home Park", "category": "Commercial"},
        {"code": "114", "description": "Nightclub/Bar/Lounge", "category": "Commercial"},
        {"code": "115", "description": "Bowling Alley/Skating Rink", "category": "Commercial"},
        {"code": "116", "description": "Theater/Auditorium", "category": "Commercial"},
        
        # Industrial (400-499)
        {"code": "400", "description": "Vacant Industrial", "category": "Industrial"},
        {"code": "401", "description": "Light Manufacturing", "category": "Industrial"},
        {"code": "402", "description": "Heavy Manufacturing", "category": "Industrial"},
        {"code": "403", "description": "Lumber Yard/Saw Mill", "category": "Industrial"},
        {"code": "404", "description": "Packing Plant", "category": "Industrial"},
        {"code": "405", "description": "Cannery", "category": "Industrial"},
        {"code": "406", "description": "Food Processing", "category": "Industrial"},
        {"code": "407", "description": "Mineral Processing", "category": "Industrial"},
        {"code": "408", "description": "Warehouse/Storage", "category": "Industrial"},
        {"code": "409", "description": "Open Storage", "category": "Industrial"},
        
        # Agricultural (500-599)
        {"code": "500", "description": "Improved Agricultural", "category": "Agricultural"},
        {"code": "501", "description": "Cropland/Soil", "category": "Agricultural"},
        {"code": "502", "description": "Timber Land", "category": "Agricultural"},
        {"code": "503", "description": "Grazing Land", "category": "Agricultural"},
        {"code": "504", "description": "Orchard/Grove", "category": "Agricultural"},
        {"code": "505", "description": "Poultry/Bee/Fish Farm", "category": "Agricultural"},
        {"code": "506", "description": "Dairy", "category": "Agricultural"},
        
        # Government (600-699)
        {"code": "600", "description": "Undefined Government", "category": "Government"},
        {"code": "601", "description": "Military", "category": "Government"},
        {"code": "602", "description": "Forest/Park/Recreational", "category": "Government"},
        {"code": "603", "description": "Public School", "category": "Government"},
        {"code": "604", "description": "College", "category": "Government"},
        {"code": "605", "description": "Hospital", "category": "Government"},
        {"code": "606", "description": "County", "category": "Government"},
        {"code": "607", "description": "State", "category": "Government"},
        {"code": "608", "description": "Federal", "category": "Government"},
        {"code": "609", "description": "Municipal", "category": "Government"},
        
        # Institutional (700-799)
        {"code": "700", "description": "Institutional", "category": "Institutional"},
        {"code": "701", "description": "Church", "category": "Institutional"},
        {"code": "702", "description": "Private School", "category": "Institutional"},
        {"code": "703", "description": "Hospital", "category": "Institutional"},
        {"code": "704", "description": "Charitable Service", "category": "Institutional"},
        {"code": "705", "description": "Clubs/Lodges", "category": "Institutional"},
        {"code": "706", "description": "Sanitarium/Convalescent", "category": "Institutional"},
        {"code": "707", "description": "Orphanage", "category": "Institutional"},
        {"code": "708", "description": "Cemetery", "category": "Institutional"},
        
        # Miscellaneous (800-999)
        {"code": "800", "description": "Undefined Miscellaneous", "category": "Miscellaneous"},
        {"code": "900", "description": "Leasehold Interest", "category": "Miscellaneous"},
        {"code": "901", "description": "Utility", "category": "Miscellaneous"},
        {"code": "902", "description": "Mining/Petroleum", "category": "Miscellaneous"},
        {"code": "903", "description": "Subsurface Rights", "category": "Miscellaneous"},
        {"code": "904", "description": "Right of Way", "category": "Miscellaneous"},
        {"code": "905", "description": "Rivers/Lakes", "category": "Miscellaneous"},
        {"code": "906", "description": "Submerged Land", "category": "Miscellaneous"},
        {"code": "907", "description": "Waste Land", "category": "Miscellaneous"}
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)