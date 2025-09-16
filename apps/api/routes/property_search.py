"""
Property Search API Routes with Supabase Integration
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Optional
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import supabase_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import get_supabase_client

# Load environment variables
load_dotenv()

# Initialize Supabase client using the fixed client
supabase = get_supabase_client()

router = APIRouter(prefix="/api", tags=["property-search"])

@router.get("/autocomplete/addresses")
async def autocomplete_addresses(
    q: str = Query(..., min_length=2),
    limit: int = Query(20)
) -> List[str]:
    """
    Autocomplete for property addresses from Supabase database
    Returns full addresses with city and zip
    """
    try:
        query_lower = q.lower()
        
        # Query florida_parcels table for addresses
        response = supabase.table('florida_parcels').select(
            'phy_addr1, phy_city, phy_state, phy_zipcd'
        ).or_(
            f"phy_addr1.ilike.%{query_lower}%,"
            f"phy_city.ilike.%{query_lower}%,"
            f"phy_zipcd.ilike.%{query_lower}%"
        ).limit(limit * 2).execute()  # Get extra to account for duplicates
        
        # Format unique addresses
        unique_addresses = []
        seen = set()
        
        if response.data:
            for prop in response.data:
                if prop.get('phy_addr1'):
                    # Create full address string
                    city = prop.get('phy_city', '')
                    state = prop.get('phy_state', 'FL')
                    zip_code = prop.get('phy_zipcd', '')
                    
                    full_address = f"{prop['phy_addr1']}"
                    if city:
                        full_address += f", {city}"
                    if state:
                        full_address += f", {state}"
                    if zip_code:
                        full_address += f" {zip_code}"
                    
                    # Add to results if unique
                    if full_address not in seen:
                        seen.add(full_address)
                        unique_addresses.append(full_address)
                        
                        if len(unique_addresses) >= limit:
                            break
        
        return unique_addresses
        
    except Exception as e:
        print(f"Error in autocomplete_addresses: {str(e)}")
        return []

@router.get("/autocomplete/cities")
async def autocomplete_cities(
    q: str = Query(..., min_length=2),
    limit: int = Query(10)
) -> List[str]:
    """
    Autocomplete for cities from Supabase database
    """
    try:
        query_lower = q.lower()
        
        # Query florida_parcels table for unique cities
        response = supabase.table('florida_parcels').select(
            'phy_city'
        ).ilike('phy_city', f'%{query_lower}%').limit(100).execute()
        
        # Get unique cities
        unique_cities = []
        seen = set()
        
        if response.data:
            for prop in response.data:
                city = prop.get('phy_city')
                if city and city not in seen:
                    seen.add(city)
                    unique_cities.append(city)
                    
                    if len(unique_cities) >= limit:
                        break
        
        # Sort alphabetically
        unique_cities.sort()
        
        return unique_cities[:limit]
        
    except Exception as e:
        print(f"Error in autocomplete_cities: {str(e)}")
        return []

@router.get("/autocomplete/owners")
async def autocomplete_owners(
    q: str = Query(..., min_length=2),
    limit: int = Query(10)
) -> List[str]:
    """
    Autocomplete for property owners from Supabase database
    """
    try:
        query_lower = q.lower()
        
        # Query florida_parcels table for owners
        response = supabase.table('florida_parcels').select(
            'owner_name'
        ).ilike('owner_name', f'%{query_lower}%').limit(100).execute()
        
        # Get unique owners
        unique_owners = []
        seen = set()
        
        if response.data:
            for prop in response.data:
                owner = prop.get('owner_name')
                if owner and owner not in seen:
                    seen.add(owner)
                    unique_owners.append(owner)
                    
                    if len(unique_owners) >= limit:
                        break
        
        # Sort alphabetically
        unique_owners.sort()
        
        return unique_owners[:limit]
        
    except Exception as e:
        print(f"Error in autocomplete_owners: {str(e)}")
        return []

@router.get("/autocomplete/parcels")
async def autocomplete_parcels(
    q: str = Query(..., min_length=3),
    limit: int = Query(10)
) -> List[Dict[str, str]]:
    """
    Autocomplete for parcel IDs with address info
    """
    try:
        query_lower = q.lower()
        
        # Query florida_parcels table for parcel IDs
        response = supabase.table('florida_parcels').select(
            'parcel_id, phy_addr1, phy_city, phy_zipcd'
        ).ilike('parcel_id', f'{query_lower}%').limit(limit).execute()
        
        results = []
        if response.data:
            for prop in response.data:
                results.append({
                    'parcel_id': prop.get('parcel_id', ''),
                    'address': f"{prop.get('phy_addr1', '')}, {prop.get('phy_city', '')}, FL {prop.get('phy_zipcd', '')}"
                })
        
        return results
        
    except Exception as e:
        print(f"Error in autocomplete_parcels: {str(e)}")
        return []

@router.get("/search/properties")
async def search_properties(
    address: Optional[str] = None,
    city: Optional[str] = None,
    owner: Optional[str] = None,
    parcel_id: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
) -> Dict:
    """
    Search properties from Supabase database with multiple filters
    """
    try:
        # Start building the query
        query = supabase.table('florida_parcels').select(
            'parcel_id, phy_addr1, phy_city, phy_state, phy_zipcd, '
            'owner_name, owner_addr1, owner_city, owner_state, owner_zip, '
            'property_use, property_use_desc, year_built, total_living_area, '
            'bedrooms, bathrooms, land_sqft, land_acres, '
            'just_value, assessed_value, taxable_value, land_value, building_value, '
            'sale_date, sale_price, county, subdivision'
        )
        
        # Apply filters
        filters = []
        
        if address:
            filters.append(f"phy_addr1.ilike.%{address}%")
        
        if city:
            filters.append(f"phy_city.ilike.%{city}%")
        
        if owner:
            filters.append(f"owner_name.ilike.%{owner}%")
        
        if parcel_id:
            filters.append(f"parcel_id.eq.{parcel_id}")
        
        # Apply OR filter if we have any filters
        if filters:
            query = query.or_(','.join(filters))
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        # Get total count for pagination
        count_query = supabase.table('florida_parcels').select('*', count='exact')
        if filters:
            count_query = count_query.or_(','.join(filters))
        count_response = count_query.execute()
        
        total_count = len(count_response.data) if count_response.data else 0
        
        return {
            'properties': response.data or [],
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        }
        
    except Exception as e:
        print(f"Error in search_properties: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/property/{parcel_id}")
async def get_property_details(parcel_id: str) -> Dict:
    """
    Get detailed property information by parcel ID
    """
    try:
        # Query florida_parcels table
        response = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        property_data = response.data[0]
        
        # Get sales history
        sales_response = supabase.table('property_sales_history').select('*').eq(
            'parcel_id', parcel_id
        ).order('sale_date', desc=True).execute()
        
        # Get NAV assessments
        nav_response = supabase.table('nav_assessments').select('*').eq(
            'parcel_id', parcel_id
        ).execute()
        
        # Get Sunbiz data (if owner is a company or individual is an officer)
        sunbiz_data = []
        owner_name = property_data.get('owner_name', '')
        
        if owner_name:
            # Check if it's a company
            if any(term in owner_name.upper() for term in ['LLC', 'INC', 'CORP', 'LP', 'TRUST']):
                sunbiz_response = supabase.table('sunbiz_corporate').select('*').ilike(
                    'corporate_name', f'%{owner_name}%'
                ).limit(5).execute()
                sunbiz_data = sunbiz_response.data or []
            else:
                # Search for individual as officer
                sunbiz_response = supabase.table('sunbiz_corporate').select('*').ilike(
                    'officers', f'%{owner_name.split()[0]}%'
                ).limit(5).execute()
                sunbiz_data = sunbiz_response.data or []
        
        return {
            'property': property_data,
            'sales_history': sales_response.data or [],
            'nav_assessments': nav_response.data or [],
            'sunbiz_data': sunbiz_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_property_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_database_stats() -> Dict:
    """
    Get database statistics and summary
    """
    try:
        # Get total properties count
        total_response = supabase.table('florida_parcels').select('*', count='exact').execute()
        total_properties = len(total_response.data) if total_response.data else 0
        
        # Get unique cities
        cities_response = supabase.table('florida_parcels').select('phy_city').execute()
        unique_cities = len(set(p['phy_city'] for p in cities_response.data if p.get('phy_city'))) if cities_response.data else 0
        
        # Get property use distribution (sample)
        use_response = supabase.table('florida_parcels').select('property_use_desc').limit(1000).execute()
        use_counts = {}
        if use_response.data:
            for prop in use_response.data:
                use_type = prop.get('property_use_desc', 'Unknown')
                use_counts[use_type] = use_counts.get(use_type, 0) + 1
        
        return {
            'total_properties': total_properties,
            'unique_cities': unique_cities,
            'property_use_distribution': use_counts,
            'database_status': 'connected'
        }
        
    except Exception as e:
        print(f"Error in get_database_stats: {str(e)}")
        return {
            'total_properties': 0,
            'unique_cities': 0,
            'property_use_distribution': {},
            'database_status': 'error',
            'error': str(e)
        }