"""
ConcordBroker Property Filter API
Comprehensive filtering system for MiniPropertyCard integration
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import requests
import pandas as pd
from datetime import datetime
import json
import uvicorn

# Configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

app = FastAPI(title="ConcordBroker Property Filter API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "https://www.concordbroker.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Property categories mapping
PROPERTY_CATEGORIES = {
    'Single Family': ['0100', '0101', '0102', '0103', '0104', '0105', '0106', '0107', '0108', '0109'],
    'Condo': ['0400', '0401', '0402', '0403', '0404', '0405'],
    'Multi-family': ['0800', '0801', '0802', '0803', '0804', '0805', '0806', '0807', '0808', '0809'],
    'Commercial': ['1000', '1100', '1200', '1300', '1400', '1500', '1600', '1700', '1800', '1900'],
    'Vacant Land': ['0000', '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009'],
    'Agricultural': ['5000', '5100', '5200', '5300', '5400', '5500', '5600', '5700', '5800', '5900'],
    'Industrial': ['4000', '4100', '4200', '4300', '4400', '4500', '4600', '4700', '4800', '4900']
}

class PropertySearchRequest(BaseModel):
    """Request model for property search"""
    # Location filters
    address: Optional[str] = Field(None, description="Property address")
    city: Optional[str] = Field(None, description="City name")
    zipcode: Optional[str] = Field(None, description="ZIP code")
    county: Optional[str] = Field(None, description="County name")

    # Owner filter
    owner_name: Optional[str] = Field(None, description="Owner name")

    # Property type filter
    property_category: Optional[str] = Field(None, description="Property category")
    property_use: Optional[str] = Field(None, description="DOR use code")

    # Value filters
    min_value: Optional[float] = Field(None, description="Minimum just value")
    max_value: Optional[float] = Field(None, description="Maximum just value")
    min_taxable_value: Optional[float] = Field(None, description="Minimum taxable value")
    max_taxable_value: Optional[float] = Field(None, description="Maximum taxable value")

    # Size filters
    min_land_sqft: Optional[float] = Field(None, description="Minimum land square feet")
    max_land_sqft: Optional[float] = Field(None, description="Maximum land square feet")
    min_building_sqft: Optional[float] = Field(None, description="Minimum building square feet")
    max_building_sqft: Optional[float] = Field(None, description="Maximum building square feet")

    # Year built filter
    min_year_built: Optional[int] = Field(None, description="Minimum year built")
    max_year_built: Optional[int] = Field(None, description="Maximum year built")

    # Sale filters
    min_sale_price: Optional[float] = Field(None, description="Minimum sale price")
    max_sale_price: Optional[float] = Field(None, description="Maximum sale price")
    min_sale_date: Optional[str] = Field(None, description="Minimum sale date")
    max_sale_date: Optional[str] = Field(None, description="Maximum sale date")

    # Other filters
    tax_delinquent: Optional[bool] = Field(None, description="Tax delinquent properties only")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=200, description="Results per page")

    # Sorting
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc/desc)")


def categorize_property(property_use: str) -> str:
    """Categorize property based on DOR use code"""
    if not property_use:
        return 'Other'

    use_code = str(property_use).zfill(4)[:4]

    # Check exact matches
    for category, codes in PROPERTY_CATEGORIES.items():
        if use_code in codes:
            return category

    # Check by prefix
    prefix = use_code[:2]
    if prefix == '01':
        return 'Single Family'
    elif prefix == '04':
        return 'Condo'
    elif prefix == '08':
        return 'Multi-family'
    elif prefix in ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19']:
        return 'Commercial'
    elif prefix == '00':
        return 'Vacant Land'
    elif prefix in ['50', '51', '52', '53', '54', '55', '56', '57', '58', '59']:
        return 'Agricultural'
    elif prefix in ['40', '41', '42', '43', '44', '45', '46', '47', '48', '49']:
        return 'Industrial'

    return 'Other'


def prepare_card_data(property_data: Dict) -> Dict:
    """Transform property data for MiniPropertyCard display"""

    # Calculate derived fields
    jv = property_data.get('jv', 0) or 0
    tv_sd = property_data.get('tv_sd', 0) or 0
    building_sqft = property_data.get('building_sqft', 0) or 0

    price_per_sqft = round(jv / building_sqft, 2) if jv and building_sqft else None
    tax_rate = round((tv_sd / jv) * 100, 2) if jv else None

    # Format display values
    if jv >= 1000000:
        value_display = f"${jv/1000000:.2f}M"
    elif jv >= 1000:
        value_display = f"${jv/1000:.0f}K"
    else:
        value_display = f"${jv:.0f}"

    # Get category
    property_category = categorize_property(property_data.get('property_use'))

    # Category icons and colors
    category_icons = {
        'Single Family': 'Home',
        'Condo': 'Building',
        'Multi-family': 'Building2',
        'Commercial': 'Briefcase',
        'Vacant Land': 'TreePine',
        'Agricultural': 'TreePine',
        'Industrial': 'Building2',
        'Other': 'Home'
    }

    category_colors = {
        'Single Family': 'blue',
        'Condo': 'purple',
        'Multi-family': 'orange',
        'Commercial': 'green',
        'Vacant Land': 'yellow',
        'Agricultural': 'emerald',
        'Industrial': 'gray',
        'Other': 'slate'
    }

    # Format address
    address_parts = [
        property_data.get('phy_addr1', ''),
        property_data.get('phy_city', ''),
        'FL',
        property_data.get('phy_zipcode', '')
    ]
    display_address = ', '.join(filter(None, address_parts))

    return {
        'id': property_data.get('id'),
        'parcel_id': property_data.get('parcel_id'),

        # Address fields
        'phy_addr1': property_data.get('phy_addr1', ''),
        'phy_city': property_data.get('phy_city', ''),
        'phy_zipcode': property_data.get('phy_zipcode', ''),

        # Owner info
        'owner_name': property_data.get('owner_name', 'Unknown Owner'),

        # Values
        'jv': jv,
        'tv_sd': tv_sd,

        # Property characteristics
        'property_use': property_data.get('property_use', ''),
        'property_category': property_category,
        'land_sqft': property_data.get('land_sqft', 0),
        'building_sqft': building_sqft,
        'year_built': property_data.get('year_built'),
        'bedrooms': property_data.get('bedrooms'),
        'bathrooms': property_data.get('bathrooms'),

        # Sales info
        'sale_price': property_data.get('sale_price'),
        'sale_date': property_data.get('sale_date'),

        # Calculated fields
        'price_per_sqft': price_per_sqft,
        'tax_rate': tax_rate,
        'display_address': display_address,
        'value_display': value_display,
        'category_icon': category_icons.get(property_category, 'Home'),
        'category_color': category_colors.get(property_category, 'slate')
    }


@app.post("/api/properties/search")
async def search_properties(request: PropertySearchRequest):
    """Search properties with advanced filters"""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        # Build query parameters
        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        params = {
            'select': '*',
            'limit': request.page_size,
            'offset': (request.page - 1) * request.page_size
        }

        # Build filters
        filters = []

        # Location filters
        if request.address:
            filters.append(f"phy_addr1.ilike.*{request.address}*")
        if request.city:
            filters.append(f"phy_city.ilike.*{request.city}*")
        if request.zipcode:
            filters.append(f"phy_zipcode.eq.{request.zipcode}")
        if request.county:
            filters.append(f"county.ilike.*{request.county}*")

        # Owner filter
        if request.owner_name:
            filters.append(f"owner_name.ilike.*{request.owner_name}*")

        # Property use filter
        if request.property_use:
            filters.append(f"property_use.eq.{request.property_use}")

        # Value filters
        if request.min_value:
            filters.append(f"jv.gte.{request.min_value}")
        if request.max_value:
            filters.append(f"jv.lte.{request.max_value}")
        if request.min_taxable_value:
            filters.append(f"tv_sd.gte.{request.min_taxable_value}")
        if request.max_taxable_value:
            filters.append(f"tv_sd.lte.{request.max_taxable_value}")

        # Size filters
        if request.min_land_sqft:
            filters.append(f"land_sqft.gte.{request.min_land_sqft}")
        if request.max_land_sqft:
            filters.append(f"land_sqft.lte.{request.max_land_sqft}")
        if request.min_building_sqft:
            filters.append(f"building_sqft.gte.{request.min_building_sqft}")
        if request.max_building_sqft:
            filters.append(f"building_sqft.lte.{request.max_building_sqft}")

        # Year built filters
        if request.min_year_built:
            filters.append(f"year_built.gte.{request.min_year_built}")
        if request.max_year_built:
            filters.append(f"year_built.lte.{request.max_year_built}")

        # Apply filters to URL
        if filters:
            url += "?" + "&".join(filters)

        # Make request
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch properties")

        properties = response.json()

        # Filter by category if specified
        if request.property_category:
            category_codes = PROPERTY_CATEGORIES.get(request.property_category, [])
            properties = [p for p in properties if str(p.get('property_use', '')).zfill(4)[:4] in category_codes or categorize_property(p.get('property_use')) == request.property_category]

        # Prepare card data
        card_data = [prepare_card_data(prop) for prop in properties]

        # Get total count (approximation)
        total = len(properties)
        if total == request.page_size:
            # If we got a full page, there might be more
            total = request.page * request.page_size + 1
        else:
            # This is the last page
            total = (request.page - 1) * request.page_size + total

        total_pages = (total + request.page_size - 1) // request.page_size

        # Calculate statistics
        if properties:
            df = pd.DataFrame(properties)
            statistics = {
                'total_results': total,
                'avg_value': float(df['jv'].mean()) if 'jv' in df.columns and not df['jv'].isna().all() else 0,
                'median_value': float(df['jv'].median()) if 'jv' in df.columns and not df['jv'].isna().all() else 0,
                'min_value': float(df['jv'].min()) if 'jv' in df.columns and not df['jv'].isna().all() else 0,
                'max_value': float(df['jv'].max()) if 'jv' in df.columns and not df['jv'].isna().all() else 0
            }
        else:
            statistics = {
                'total_results': 0,
                'avg_value': 0,
                'median_value': 0,
                'min_value': 0,
                'max_value': 0
            }

        return {
            "success": True,
            "properties": card_data,
            "pagination": {
                "total": total,
                "page": request.page,
                "page_size": request.page_size,
                "total_pages": total_pages
            },
            "statistics": statistics,
            "filters_applied": {
                "location": bool(request.address or request.city or request.zipcode or request.county),
                "owner": bool(request.owner_name),
                "property_type": bool(request.property_category or request.property_use),
                "value": bool(request.min_value or request.max_value),
                "size": bool(request.min_land_sqft or request.max_land_sqft or request.min_building_sqft or request.max_building_sqft),
                "year": bool(request.min_year_built or request.max_year_built)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/properties/categories")
async def get_property_categories():
    """Get available property categories with counts"""
    return {
        "success": True,
        "categories": [
            {"value": "Single Family", "label": "Single Family", "icon": "Home", "color": "blue"},
            {"value": "Condo", "label": "Condo", "icon": "Building", "color": "purple"},
            {"value": "Multi-family", "label": "Multi-family", "icon": "Building2", "color": "orange"},
            {"value": "Commercial", "label": "Commercial", "icon": "Briefcase", "color": "green"},
            {"value": "Vacant Land", "label": "Vacant Land", "icon": "TreePine", "color": "yellow"},
            {"value": "Agricultural", "label": "Agricultural", "icon": "TreePine", "color": "emerald"},
            {"value": "Industrial", "label": "Industrial", "icon": "Building2", "color": "gray"}
        ]
    }


@app.get("/api/properties/filters/cities")
async def get_cities(county: Optional[str] = None):
    """Get list of cities, optionally filtered by county"""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
        params = {
            'select': 'phy_city',
            'limit': 1000
        }

        if county:
            url += f"?county.ilike.*{county}*"

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            cities = list(set([d['phy_city'] for d in data if d.get('phy_city')]))
            cities.sort()
            return {"success": True, "cities": cities}
        else:
            return {"success": False, "cities": []}

    except Exception as e:
        return {"success": False, "error": str(e), "cities": []}


@app.get("/api/properties/filters/value-ranges")
async def get_value_ranges():
    """Get predefined value ranges for filtering"""
    return {
        "success": True,
        "ranges": [
            {"min": 0, "max": 100000, "label": "Under $100K", "count": 0},
            {"min": 100000, "max": 250000, "label": "$100K - $250K", "count": 0},
            {"min": 250000, "max": 500000, "label": "$250K - $500K", "count": 0},
            {"min": 500000, "max": 1000000, "label": "$500K - $1M", "count": 0},
            {"min": 1000000, "max": 2000000, "label": "$1M - $2M", "count": 0},
            {"min": 2000000, "max": None, "label": "Over $2M", "count": 0}
        ]
    }


@app.get("/api/properties/{parcel_id}")
async def get_property_details(parcel_id: str):
    """Get detailed information for a specific property"""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data:
                property_data = data[0]
                card_data = prepare_card_data(property_data)
                return {
                    "success": True,
                    "property": card_data
                }
            else:
                raise HTTPException(status_code=404, detail="Property not found")
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch property")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ConcordBroker Property Filter API",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("Starting ConcordBroker Property Filter API...")
    print("API will be available at: http://localhost:8001")
    print("Documentation: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)