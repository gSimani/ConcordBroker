"""
Optimized Property API for handling 789k+ properties efficiently
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
    title="ConcordBroker Optimized Property API",
    description="High-performance API for 789k+ Florida properties",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize Supabase client with service role for better performance
# Use the correct Supabase instance that has the 789k properties
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for better performance

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase credentials not found")
    raise ValueError("Missing Supabase credentials")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info(f"Connected to Supabase: {SUPABASE_URL}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ConcordBroker Optimized Property API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/properties/search")
async def search_properties(
    # Search parameters
    q: Optional[str] = Query(None, description="General search query"),
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    
    # Filter parameters
    property_type: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    min_building_sqft: Optional[float] = Query(None),
    max_building_sqft: Optional[float] = Query(None),
    min_land_sqft: Optional[float] = Query(None),
    max_land_sqft: Optional[float] = Query(None),
    
    # Pagination - increased defaults for better performance
    limit: int = Query(100, ge=1, le=500),  # Allow up to 500 per page
    offset: int = Query(0, ge=0),
    
    # Sorting
    sort_by: Optional[str] = Query("id"),
    sort_order: Optional[str] = Query("asc")
) -> Dict[str, Any]:
    """
    Optimized search for properties with proper pagination
    Returns properties from the florida_parcels table
    """
    try:
        # Build base query with count
        query = supabase.table('florida_parcels').select('*', count='exact')
        
        # Apply search filters efficiently
        if q:
            # General search across key fields
            search_term = f"%{q}%"
            query = query.or_(
                f"phy_addr1.ilike.{search_term},"
                f"phy_city.ilike.{search_term},"
                f"phy_zipcd.ilike.{search_term},"
                f"own_name.ilike.{search_term},"
                f"parcel_id.ilike.{search_term}"
            )
        
        # Specific field filters
        if address:
            query = query.ilike('phy_addr1', f'%{address}%')
        
        if city and city != 'all-cities':
            query = query.ilike('phy_city', f'%{city}%')
        
        if zip_code:
            query = query.eq('phy_zipcd', zip_code)
        
        if owner:
            query = query.ilike('own_name', f'%{owner}%')
        
        # Property type filter
        if property_type and property_type != 'all-types':
            if property_type == 'residential':
                query = query.in_('dor_uc', ['0100', '0101', '0102', '0103', '0104'])
            elif property_type == 'commercial':
                query = query.in_('dor_uc', ['1100', '1200', '1300', '1400'])
            elif property_type == 'industrial':
                query = query.in_('dor_uc', ['4000', '4100', '4200'])
            elif property_type == 'agricultural':
                query = query.in_('dor_uc', ['5000', '5100', '5200'])
            elif property_type == 'vacant':
                query = query.in_('dor_uc', ['0000', '1000'])
        
        # Value filters (using jv - just value)
        if min_value is not None:
            query = query.gte('jv', min_value)
        
        if max_value is not None:
            query = query.lte('jv', max_value)
        
        # Year built filters
        if min_year is not None:
            query = query.gte('yr_blt', min_year)
        
        if max_year is not None:
            query = query.lte('yr_blt', max_year)
        
        # Square footage filters
        if min_building_sqft is not None:
            query = query.gte('tot_lvg_area', min_building_sqft)
        
        if max_building_sqft is not None:
            query = query.lte('tot_lvg_area', max_building_sqft)
        
        if min_land_sqft is not None:
            query = query.gte('lnd_sqfoot', min_land_sqft)
        
        if max_land_sqft is not None:
            query = query.lte('lnd_sqfoot', max_land_sqft)
        
        # Apply sorting
        if sort_by and sort_order:
            if sort_order.lower() == 'asc':
                query = query.order(sort_by)
            else:
                query = query.order(sort_by, desc=True)
        else:
            # Default sort by ID for consistent pagination
            query = query.order('id')
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Format response
        properties = []
        if response.data:
            for prop in response.data:
                # Format property data
                formatted_prop = {
                    'id': prop.get('id'),
                    'parcel_id': prop.get('parcel_id'),
                    'phy_addr1': prop.get('phy_addr1', ''),
                    'phy_city': prop.get('phy_city', ''),
                    'phy_state': prop.get('phy_state', 'FL'),
                    'phy_zipcd': prop.get('phy_zipcd', ''),
                    'own_name': prop.get('own_name', ''),
                    'property_type': get_property_type_name(prop.get('dor_uc', '')),
                    'dor_uc': prop.get('dor_uc', ''),
                    'jv': prop.get('jv', 0),
                    'tv_sd': prop.get('taxable_val', 0),
                    'lnd_val': prop.get('lnd_sqfoot', 0) * 10 if prop.get('lnd_sqfoot') else 0,
                    'tot_lvg_area': prop.get('tot_lvg_area', 0),
                    'lnd_sqfoot': prop.get('lnd_sqfoot', 0),
                    'act_yr_blt': prop.get('yr_blt', 0),
                    'sale_prc1': prop.get('sale_prc1', 0),
                    'sale_yr1': prop.get('sale_yr1', ''),
                    'bedroom_cnt': prop.get('bedroom_cnt', 0),
                    'bathroom_cnt': prop.get('bathroom_cnt', 0),
                    'millage_rate': prop.get('millage_rate', 0),
                    'latitude': prop.get('latitude'),
                    'longitude': prop.get('longitude')
                }
                properties.append(formatted_prop)
        
        # Get total count from response
        total_count = response.count if hasattr(response, 'count') else len(properties)
        
        logger.info(f"Search returned {len(properties)} properties out of {total_count} total")
        
        return {
            'properties': properties,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'page': (offset // limit) + 1,
            'total_pages': ((total_count - 1) // limit) + 1 if total_count > 0 else 0,
            'has_more': (offset + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error searching properties: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/properties/{property_id}")
async def get_property_details(property_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific property by ID or parcel_id"""
    try:
        # Try to get by ID first
        if property_id.isdigit():
            response = supabase.table('florida_parcels').select('*').eq('id', int(property_id)).single().execute()
        else:
            # Try by parcel_id
            response = supabase.table('florida_parcels').select('*').eq('parcel_id', property_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        prop = response.data
        
        # Format detailed property data
        property_details = {
            'id': prop.get('id'),
            'parcel_id': prop.get('parcel_id'),
            'phy_addr1': prop.get('phy_addr1', ''),
            'phy_city': prop.get('phy_city', ''),
            'phy_state': prop.get('phy_state', 'FL'),
            'phy_zipcd': prop.get('phy_zipcd', ''),
            'own_name': prop.get('own_name', ''),
            'own_addr1': prop.get('own_addr1', ''),
            'own_city': prop.get('own_city', ''),
            'own_state': prop.get('own_state', ''),
            'own_zipcd': prop.get('own_zipcd', ''),
            'property_type': get_property_type_name(prop.get('dor_uc', '')),
            'dor_uc': prop.get('dor_uc', ''),
            'state_par_use_cd': prop.get('state_par_use_cd', ''),
            'co_no': prop.get('co_no', ''),
            'yr_blt': prop.get('yr_blt'),
            'act_yr_blt': prop.get('act_yr_blt'),
            'tot_lvg_area': prop.get('tot_lvg_area'),
            'lnd_sqfoot': prop.get('lnd_sqfoot'),
            'bedroom_cnt': prop.get('bedroom_cnt'),
            'bathroom_cnt': prop.get('bathroom_cnt'),
            'jv': prop.get('jv'),
            'av_sd': prop.get('av_sd'),
            'taxable_val': prop.get('taxable_val'),
            'exempt_val': prop.get('exempt_val'),
            'sale_prc1': prop.get('sale_prc1'),
            'sale_yr1': prop.get('sale_yr1'),
            'vi_cd': prop.get('vi_cd'),
            'millage_rate': prop.get('millage_rate'),
            'nbhd_cd': prop.get('nbhd_cd'),
            'latitude': prop.get('latitude'),
            'longitude': prop.get('longitude'),
            'created_at': prop.get('created_at'),
            'updated_at': prop.get('updated_at')
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
    """Get overview statistics for all properties"""
    try:
        # Get total count efficiently
        count_response = supabase.table('florida_parcels').select('id', count='exact', head=True).execute()
        total_properties = count_response.count if hasattr(count_response, 'count') else 0
        
        # Get sample data for statistics (top 1000 by value)
        sample_response = supabase.table('florida_parcels').select('jv, phy_city, dor_uc').order('jv', desc=True).limit(1000).execute()
        
        if sample_response.data:
            # Calculate statistics from sample
            values = [p['jv'] for p in sample_response.data if p.get('jv')]
            avg_value = sum(values) / len(values) if values else 0
            
            # Count unique cities
            cities = set(p['phy_city'] for p in sample_response.data if p.get('phy_city'))
            
            # Count property types
            types = set(p['dor_uc'] for p in sample_response.data if p.get('dor_uc'))
        else:
            avg_value = 0
            cities = set()
            types = set()
        
        return {
            'success': True,
            'data': {
                'totalProperties': total_properties,
                'averageValue': avg_value,
                'estimatedTotalValue': avg_value * total_properties,
                'uniqueCities': len(cities),
                'propertyTypes': len(types),
                'lastUpdated': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting property stats: {str(e)}")
        return {
            'success': False,
            'data': {
                'totalProperties': 0,
                'averageValue': 0,
                'estimatedTotalValue': 0,
                'uniqueCities': 0,
                'propertyTypes': 0
            }
        }

@app.get("/api/cities")
async def get_all_cities() -> List[str]:
    """Get list of all unique cities"""
    try:
        # Get distinct cities
        response = supabase.table('florida_parcels').select('phy_city').execute()
        
        if response.data:
            # Extract unique cities
            cities = list(set(p['phy_city'] for p in response.data if p.get('phy_city')))
            cities.sort()
            return cities[:100]  # Return top 100 cities
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting cities: {str(e)}")
        return []

def get_property_type_name(dor_uc: str) -> str:
    """Convert DOR use code to readable property type"""
    property_types = {
        '0100': 'Single Family',
        '0101': 'Single Family',
        '0102': 'Single Family',
        '0103': 'Single Family',
        '0104': 'Single Family',
        '0200': 'Mobile Home',
        '0300': 'Multi-Family',
        '0400': 'Condominium',
        '0500': 'Cooperative',
        '0800': 'Duplex/Triplex',
        '1000': 'Vacant Land',
        '1100': 'Store/Office',
        '1200': 'Office Building',
        '1700': 'Professional',
        '4000': 'Vacant Commercial',
        '4100': 'Industrial',
        '5000': 'Agricultural'
    }
    
    # Get first 4 digits of code
    code = str(dor_uc)[:4] if dor_uc else '0000'
    return property_types.get(code, 'Other')

if __name__ == "__main__":
    # Run the optimized server
    uvicorn.run(
        "optimized_property_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )