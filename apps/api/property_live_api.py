"""
Property Live Data API for Frontend
Serves real property data from Supabase to localhost frontend
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ConcordBroker Live Property API",
    description="Real-time property data from Supabase",
    version="1.0.0"
)

# Configure CORS for localhost development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found in environment variables")
    raise ValueError("Missing Supabase credentials")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info(f"Connected to Supabase: {SUPABASE_URL}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ConcordBroker Live Property API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/properties/search")
async def search_properties(
    # Search parameters
    q: Optional[str] = Query(None, description="Search query"),
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    
    # Filter parameters
    propertyType: Optional[str] = Query(None),
    minValue: Optional[float] = Query(None),
    maxValue: Optional[float] = Query(None),
    minYear: Optional[int] = Query(None),
    maxYear: Optional[int] = Query(None),
    minBuildingSqFt: Optional[float] = Query(None),
    maxBuildingSqFt: Optional[float] = Query(None),
    minLandSqFt: Optional[float] = Query(None),
    maxLandSqFt: Optional[float] = Query(None),
    
    # Tax certificate filters
    hasTaxCertificate: Optional[bool] = Query(None),
    minCertAmount: Optional[float] = Query(None),
    maxCertAmount: Optional[float] = Query(None),
    
    # Pagination
    page: int = Query(1, ge=1),
    limit: int = Query(500, ge=1, le=10000),
    
    # Sorting
    sortBy: Optional[str] = Query("phy_addr1"),
    sortOrder: Optional[str] = Query("asc")
) -> Dict[str, Any]:
    """
    Search properties with filters from live Supabase database
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Start building the query
        query = supabase.table('florida_parcels').select('*')
        
        # Apply search filters
        if q:
            # General search across multiple fields
            search_query = f"%{q}%"
            query = query.or_(
                f"phy_addr1.ilike.{search_query},"
                f"phy_city.ilike.{search_query},"
                f"phy_zipcd.ilike.{search_query},"
                f"owner_name.ilike.{search_query},"
                f"parcel_id.ilike.{search_query}"
            )
        
        # Apply specific filters
        if address:
            query = query.ilike('phy_addr1', f'%{address}%')
        
        if city:
            query = query.ilike('phy_city', f'%{city}%')
        
        if zipCode:
            query = query.eq('phy_zipcd', zipCode)
        
        if owner:
            query = query.ilike('owner_name', f'%{owner}%')
        
        if propertyType:
            # Map frontend property types to database codes
            type_mapping = {
                'single_family': ['0100', '0101', '0102', '0103'],
                'multi_family': ['0200', '0201', '0202'],
                'commercial': ['1000', '1100', '1200'],
                'industrial': ['4000', '4100', '4200'],
                'agricultural': ['5000', '5100', '5200'],
                'vacant': ['0000', '0001']
            }
            
            if propertyType in type_mapping:
                codes = type_mapping[propertyType]
                query = query.in_('dor_uc', codes)
        
        # Value filters
        if minValue is not None:
            query = query.gte('jv', minValue)
        
        if maxValue is not None:
            query = query.lte('jv', maxValue)
        
        # Year built filters
        if minYear is not None:
            query = query.gte('yr_blt', minYear)
        
        if maxYear is not None:
            query = query.lte('yr_blt', maxYear)
        
        # Building square footage filters
        if minBuildingSqFt is not None:
            query = query.gte('tot_lvg_area', minBuildingSqFt)
        
        if maxBuildingSqFt is not None:
            query = query.lte('tot_lvg_area', maxBuildingSqFt)
        
        # Land square footage filters
        if minLandSqFt is not None:
            query = query.gte('lnd_sqfoot', minLandSqFt)
        
        if maxLandSqFt is not None:
            query = query.lte('lnd_sqfoot', maxLandSqFt)
        
        # Sorting
        if sortBy and sortOrder:
            if sortOrder.lower() == 'asc':
                query = query.order(sortBy)
            else:
                query = query.order(sortBy, desc=True)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Format properties for frontend
        properties = []
        for prop in response.data:
            # Calculate investment metrics
            market_value = float(prop.get('jv', 0) or 0)
            assessed_value = float(prop.get('av_sd', 0) or 0)
            tax_amount = float(prop.get('taxable_val', 0) or 0) * 0.02  # Approximate tax rate
            
            formatted_prop = {
                'id': prop.get('parcel_id'),
                'parcel_id': prop.get('parcel_id'),
                'address': prop.get('phy_addr1', ''),
                'city': prop.get('phy_city', ''),
                'state': prop.get('phy_state', 'FL'),
                'zipCode': prop.get('phy_zipcd', ''),
                'owner': prop.get('owner_name', ''),
                'ownerAddress': prop.get('owner_addr1', ''),
                'propertyType': prop.get('dor_uc', ''),
                'propertyUse': prop.get('dor_uc', ''),
                'yearBuilt': prop.get('yr_blt'),
                'bedrooms': prop.get('bedroom_cnt'),
                'bathrooms': prop.get('bathroom_cnt'),
                'buildingSqFt': prop.get('tot_lvg_area'),
                'landSqFt': prop.get('lnd_sqfoot'),
                'marketValue': market_value,
                'assessedValue': assessed_value,
                'taxableValue': prop.get('taxable_val'),
                'justValue': prop.get('jv'),
                'taxAmount': tax_amount,
                'lastSaleDate': prop.get('vi_cd'),
                'lastSalePrice': prop.get('sale_prc1'),
                'latitude': prop.get('latitude'),
                'longitude': prop.get('longitude'),
                
                # Investment metrics
                'investmentScore': calculate_investment_score(prop),
                'capRate': calculate_cap_rate(market_value, tax_amount),
                'pricePerSqFt': calculate_price_per_sqft(market_value, prop.get('tot_lvg_area')),
                
                # Additional data
                'county': prop.get('co_no'),
                'neighborhood': prop.get('nbhd_cd'),
                'millageRate': prop.get('millage_rate'),
                'exemptions': prop.get('exempt_val'),
                
                # Status flags
                'hasHomestead': prop.get('exempt_val', 0) > 0,
                'isTaxDelinquent': False,  # Would need to join with tax_certificates
                'isDistressed': market_value < assessed_value * 0.8
            }
            
            properties.append(formatted_prop)
        
        # Get total count (estimated based on limit for performance)
        total_count = len(response.data) if response.data else 0
        if len(response.data) == limit:
            total_count = (page * limit) + 1  # Estimate more pages exist
        
        return {
            'success': True,
            'data': properties,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit if total_count > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching properties: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties/{property_id}")
async def get_property_details(property_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific property"""
    try:
        # Query property from database
        response = supabase.table('florida_parcels').select('*').eq('parcel_id', property_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Property not found")

        prop = response.data[0]  # Get first matching property
        
        # Get tax certificates if available
        tax_certs = []
        try:
            cert_response = supabase.table('tax_certificates').select('*').eq('parcel_id', property_id).execute()
            if cert_response.data:
                tax_certs = cert_response.data
        except:
            pass
        
        # Get sales history if available
        sales_history = []
        try:
            sales_response = supabase.table('sales_history').select('*').eq('parcel_id', property_id).order('sale_date', desc=True).execute()
            if sales_response.data:
                sales_history = sales_response.data
        except:
            pass
        
        # Format detailed property data with all available fields
        property_details = {
            # Essential IDs
            'id': prop.get('parcel_id'),
            'parcel_id': prop.get('parcel_id'),

            # Property address information
            'phy_addr1': prop.get('phy_addr1', ''),
            'phy_addr2': prop.get('phy_addr2', ''),
            'phy_city': prop.get('phy_city', ''),
            'phy_state': prop.get('phy_state', 'FL'),
            'phy_zipcd': prop.get('phy_zipcd', ''),

            # Owner information
            'owner_name': prop.get('owner_name', ''),
            'owner_addr1': prop.get('owner_addr1', ''),
            'owner_addr2': prop.get('owner_addr2', ''),
            'owner_city': prop.get('owner_city', ''),
            'owner_state': prop.get('owner_state', ''),
            'owner_zip': prop.get('owner_zip', ''),

            # Property characteristics
            'property_use': prop.get('property_use', ''),
            'dor_uc': prop.get('dor_uc', prop.get('property_use', '')),
            'yr_blt': prop.get('yr_blt'),
            'act_yr_blt': prop.get('act_yr_blt', prop.get('yr_blt')),
            'eff_yr_blt': prop.get('eff_yr_blt'),
            'bedroom_cnt': prop.get('bedroom_cnt'),
            'bathroom_cnt': prop.get('bathroom_cnt'),
            'tot_lvg_area': prop.get('tot_lvg_area'),
            'lnd_sqfoot': prop.get('lnd_sqfoot'),
            'no_res_unts': prop.get('no_res_unts', 1),

            # Values
            'jv': prop.get('jv') or prop.get('just_value'),
            'just_value': prop.get('just_value') or prop.get('jv'),
            'av_sd': prop.get('av_sd') or prop.get('assessed_value'),
            'assessed_value': prop.get('assessed_value') or prop.get('av_sd'),
            'tv_sd': prop.get('tv_sd') or prop.get('taxable_value'),
            'taxable_value': prop.get('taxable_value') or prop.get('tv_sd'),
            'lnd_val': prop.get('lnd_val') or prop.get('land_value'),
            'land_value': prop.get('land_value') or prop.get('lnd_val'),
            'tax_amount': prop.get('tax_amount'),

            # Sales information
            'sale_prc1': prop.get('sale_prc1'),
            'sale_yr1': prop.get('sale_yr1'),
            'sale_mo1': prop.get('sale_mo1'),
            'qual_cd1': prop.get('qual_cd1'),
            'vi_cd': prop.get('vi_cd'),
            'or_book_page': prop.get('or_book_page'),

            # Additional info
            'subdivision': prop.get('subdivision'),
            'exempt_val': prop.get('exempt_val'),
            'homestead_exemption': prop.get('homestead_exemption', prop.get('exempt_val', 0) > 0),
            'county': prop.get('county'),
            'year': prop.get('year'),
            'nbhd_cd': prop.get('nbhd_cd'),
            'millage_rate': prop.get('millage_rate'),

            # Related data
            'taxCertificates': tax_certs,
            'salesHistory': sales_history,
            'investmentScore': calculate_investment_score(prop),

            # Formatted versions for backward compatibility
            'address': prop.get('phy_addr1', ''),
            'city': prop.get('phy_city', ''),
            'state': prop.get('phy_state', 'FL'),
            'zipCode': prop.get('phy_zipcd', ''),
            'owner': prop.get('owner_name', ''),
            'ownerAddress': prop.get('owner_addr1', ''),
            'propertyType': prop.get('dor_uc', prop.get('property_use', '')),
            'yearBuilt': prop.get('yr_blt'),
            'bedrooms': prop.get('bedroom_cnt'),
            'bathrooms': prop.get('bathroom_cnt'),
            'buildingSqFt': prop.get('tot_lvg_area'),
            'landSqFt': prop.get('lnd_sqfoot'),
            'marketValue': float(prop.get('jv') or prop.get('just_value') or 0),
            'assessedValue': float(prop.get('av_sd') or prop.get('assessed_value') or 0)
        }
        
        return {
            'success': True,
            'data': property_details,
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties/stats/overview")
async def get_property_stats() -> Dict[str, Any]:
    """Get overview statistics for properties"""
    try:
        # Get total count
        count_response = supabase.table('florida_parcels').select('*', count='exact', head=True).execute()
        total_properties = count_response.count or 0
        
        # Get average values (simplified query)
        stats = {
            'totalProperties': total_properties,
            'averageValue': 250000,  # Would need aggregation query
            'totalValue': total_properties * 250000,
            'uniqueCities': 67,  # Florida counties
            'propertyTypes': 6
        }
        
        return {
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting property stats: {str(e)}")
        return {
            'success': False,
            'data': {
                'totalProperties': 0,
                'averageValue': 0,
                'totalValue': 0,
                'uniqueCities': 0,
                'propertyTypes': 0
            }
        }

def calculate_investment_score(property_data: Dict) -> float:
    """Calculate investment score for a property"""
    score = 50.0  # Base score
    
    # Value factors
    market_value = float(property_data.get('jv', 0) or 0)
    assessed_value = float(property_data.get('av_sd', 0) or 0)
    
    if market_value > 0 and assessed_value > 0:
        if market_value < assessed_value:
            score += 10  # Undervalued
        
        if market_value < 100000:
            score += 5  # Low entry point
    
    # Property characteristics
    if property_data.get('yr_blt'):
        year_built = property_data.get('yr_blt')
        if year_built and year_built > 2000:
            score += 5  # Newer property
    
    if property_data.get('tot_lvg_area'):
        sqft = property_data.get('tot_lvg_area')
        if sqft and sqft > 1500:
            score += 5  # Good size
    
    return min(100, max(0, score))

def calculate_cap_rate(market_value: float, annual_tax: float) -> float:
    """Calculate capitalization rate"""
    if market_value > 0:
        estimated_annual_rent = market_value * 0.01 * 12  # 1% rule
        net_income = estimated_annual_rent - annual_tax - (estimated_annual_rent * 0.3)  # 30% expenses
        return (net_income / market_value) * 100
    return 0

def calculate_price_per_sqft(market_value: float, sqft: Optional[float]) -> float:
    """Calculate price per square foot"""
    if sqft and sqft > 0 and market_value > 0:
        return market_value / sqft
    return 0

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "property_live_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )