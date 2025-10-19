"""
Direct Database Property API - Serves 789k+ properties efficiently
Uses direct PostgreSQL connection instead of Supabase SDK
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ConcordBroker Direct Database API",
    description="High-performance API serving 789k+ Florida properties",
    version="3.0.0"
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

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in environment variables")

# Parse database URL
parsed_url = urlparse(DATABASE_URL)
db_config = {
    'host': parsed_url.hostname,
    'port': parsed_url.port or 5432,
    'database': parsed_url.path[1:] if parsed_url.path else 'postgres',
    'user': parsed_url.username,
    'password': unquote(parsed_url.password) if parsed_url.password else None
}

logger.info(f"Connecting to database at {db_config['host']}")

def get_db_connection():
    """Create a new database connection"""
    return psycopg2.connect(
        host=db_config['host'],
        port=db_config['port'],
        database=db_config['database'],
        user=db_config['user'],
        password=db_config['password'],
        sslmode='require',
        cursor_factory=RealDictCursor
    )

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ConcordBroker Direct Database API",
        "version": "3.0.0",
        "database": "Connected to 789k+ properties",
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
    
    # Pagination - FIXED: Increased limit from 1000 to 10000
    limit: int = Query(500, ge=1, le=10000),  # Default 500, max 10000
    offset: int = Query(0, ge=0),
    
    # Sorting
    sort_by: Optional[str] = Query("id"),
    sort_order: Optional[str] = Query("asc")
) -> Dict[str, Any]:
    """
    Search properties with direct database queries
    Efficiently handles 789k+ properties
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if q:
            search_term = f"%{q}%"
            where_clauses.append("""
                (phy_addr1 ILIKE %s OR 
                 phy_city ILIKE %s OR 
                 phy_zipcd ILIKE %s OR 
                 owner_name ILIKE %s OR 
                 parcel_id ILIKE %s)
            """)
            params.extend([search_term] * 5)
        
        if address:
            where_clauses.append("phy_addr1 ILIKE %s")
            params.append(f"%{address}%")
        
        if city and city != 'all-cities':
            where_clauses.append("phy_city ILIKE %s")
            params.append(f"%{city}%")
        
        if zip_code:
            where_clauses.append("phy_zipcd = %s")
            params.append(zip_code)
        
        if owner:
            where_clauses.append("owner_name ILIKE %s")
            params.append(f"%{owner}%")
        
        # Property type filter - optimized for actual data distribution
        if property_type and property_type != 'all-types':
            property_type_lower = property_type.lower()
            
            if property_type_lower == 'residential':
                # Residential: 001, 002, 003, 004, 005 (and their variations)
                where_clauses.append("(property_use LIKE '00%')")
            elif property_type_lower == 'commercial':
                # Commercial: All non-residential, non-vacant codes (10xx-39xx typically)
                # Since we have so few, use broader pattern matching
                where_clauses.append("(property_use LIKE '1%' AND property_use NOT LIKE '10%' OR property_use LIKE '2%' OR property_use LIKE '3%')")
            elif property_type_lower == 'industrial':
                # Industrial: 40xx-49xx
                where_clauses.append("property_use LIKE '4%'")
            elif property_type_lower == 'agricultural':
                # Agricultural: 50xx-59xx
                where_clauses.append("property_use LIKE '5%'")
            elif property_type_lower == 'vacant':
                # Vacant: 100 (vacant commercial), 400 (vacant industrial), etc.
                where_clauses.append("(property_use = '100' OR property_use = '400' OR property_use = '500')")
            elif property_type_lower == 'other':
                # Other: Everything else (06xx, 07xx, 09xx, 60xx+)
                where_clauses.append("(property_use LIKE '05%' OR property_use LIKE '06%' OR property_use LIKE '07%' OR property_use LIKE '09%' OR property_use >= '60')")
        
        # Value filters
        if min_value is not None:
            where_clauses.append("just_value >= %s")
            params.append(min_value)
        
        if max_value is not None:
            where_clauses.append("just_value <= %s")
            params.append(max_value)
        
        # Year built filters
        if min_year is not None:
            where_clauses.append("year_built >= %s")
            params.append(min_year)
        
        if max_year is not None:
            where_clauses.append("year_built <= %s")
            params.append(max_year)
        
        # Square footage filters
        if min_building_sqft is not None:
            where_clauses.append("total_living_area >= %s")
            params.append(min_building_sqft)
        
        if max_building_sqft is not None:
            where_clauses.append("total_living_area <= %s")
            params.append(max_building_sqft)
        
        if min_land_sqft is not None:
            where_clauses.append("land_sqft >= %s")
            params.append(min_land_sqft)
        
        if max_land_sqft is not None:
            where_clauses.append("land_sqft <= %s")
            params.append(max_land_sqft)
        
        # Build WHERE string
        where_str = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count first (optimized)
        count_query = f"SELECT COUNT(*) as count FROM florida_parcels WHERE {where_str}"
        logger.info(f"Executing count query: {count_query} with params: {params}")
        cur.execute(count_query, params)
        count_result = cur.fetchone()
        logger.info(f"Count result: {count_result}")
        total_count = count_result['count'] if count_result else 0
        
        # Get paginated results
        # Validate sort column to prevent SQL injection
        valid_columns = ['id', 'parcel_id', 'phy_addr1', 'phy_city', 'just_value', 'year_built', 'total_living_area']
        if sort_by not in valid_columns:
            sort_by = 'id'
        
        order_by = f"{sort_by} {sort_order.upper() if sort_order else 'ASC'}"
        
        data_query = f"""
            SELECT 
                id, parcel_id, phy_addr1, phy_city, phy_state, phy_zipcd,
                owner_name, owner_addr1, owner_city, owner_state, owner_zip,
                property_use, property_use_desc, land_use_code,
                year_built, total_living_area, land_sqft,
                bedrooms, bathrooms,
                just_value, assessed_value, taxable_value, land_value, building_value,
                sale_price, sale_date,
                county, zoning,
                centroid
            FROM florida_parcels 
            WHERE {where_str}
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """
        
        cur.execute(data_query, params + [limit, offset])
        properties = cur.fetchall() or []
        
        # Format properties
        formatted_properties = []
        for prop in properties:
            # Extract lat/lng from centroid if available
            lat, lng = None, None
            if prop.get('centroid'):
                try:
                    # Parse POINT geometry format: POINT(lng lat)
                    import re
                    match = re.match(r'POINT\(([-\d.]+) ([-\d.]+)\)', prop['centroid'])
                    if match:
                        lng = float(match.group(1))
                        lat = float(match.group(2))
                except:
                    pass
            
            formatted_prop = {
                'id': prop['id'],
                'parcel_id': prop['parcel_id'],
                'phy_addr1': prop['phy_addr1'] or '',
                'phy_city': prop['phy_city'] or '',
                'phy_state': prop['phy_state'] or 'FL',
                'phy_zipcd': prop['phy_zipcd'] or '',
                'own_name': prop['owner_name'] or '',
                'property_type': get_property_type_name(prop['property_use']),
                'dor_uc': prop['property_use'] or '',
                'jv': float(prop['just_value']) if prop['just_value'] else 0,
                'tv_sd': float(prop['taxable_value']) if prop['taxable_value'] else 0,
                'tot_lvg_area': prop['total_living_area'] or 0,
                'lnd_sqfoot': prop['land_sqft'] or 0,
                'act_yr_blt': prop['year_built'] or 0,
                'sale_prc1': float(prop['sale_price']) if prop['sale_price'] else 0,
                'sale_yr1': prop['sale_date'] or '',
                'bedroom_cnt': prop['bedrooms'] or 0,
                'bathroom_cnt': prop['bathrooms'] or 0,
                'latitude': lat,
                'longitude': lng
            }
            formatted_properties.append(formatted_prop)
        
        # Close connection
        cur.close()
        conn.close()
        
        logger.info(f"Search returned {len(formatted_properties)} of {total_count} total properties")
        
        return {
            'properties': formatted_properties,
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

@app.get("/api/properties/stats/overview")
async def get_property_stats() -> Dict[str, Any]:
    """Get overview statistics for all 789k+ properties"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get total count
        cur.execute("SELECT COUNT(*) as count FROM florida_parcels")
        total_properties = cur.fetchone()['count']
        
        # Get average value and other stats
        cur.execute("""
            SELECT 
                AVG(just_value) as avg_value,
                MIN(just_value) as min_value,
                MAX(just_value) as max_value,
                COUNT(DISTINCT phy_city) as unique_cities,
                COUNT(DISTINCT property_use) as property_types
            FROM florida_parcels
            WHERE just_value IS NOT NULL AND just_value > 0
        """)
        
        stats = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            'totalProperties': total_properties,
            'totalValue': float(stats['avg_value'] or 0) * total_properties if stats['avg_value'] else 0,
            'averageValue': float(stats['avg_value'] or 0),
            'minValue': float(stats['min_value'] or 0),
            'maxValue': float(stats['max_value'] or 0),
            'uniqueCities': stats['unique_cities'] or 0,
            'propertyTypes': stats['property_types'] or 0,
            'lastUpdated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting property stats: {str(e)}")
        return {
            'totalProperties': 0,
            'averageValue': 0,
            'totalValue': 0,
            'uniqueCities': 0,
            'propertyTypes': 0
        }

@app.get("/api/cities")
async def get_all_cities() -> List[str]:
    """Get list of all unique cities"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT phy_city 
            FROM florida_parcels 
            WHERE phy_city IS NOT NULL 
            ORDER BY phy_city
            LIMIT 200
        """)
        
        cities = [row['phy_city'] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return cities
        
    except Exception as e:
        logger.error(f"Error getting cities: {str(e)}")
        return []

@app.get("/api/properties/{property_id}")
async def get_property_details(property_id: str) -> Dict[str, Any]:
    """Get detailed information for a specific property"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Try by ID or parcel_id
        if property_id.isdigit():
            cur.execute("SELECT * FROM florida_parcels WHERE id = %s", [int(property_id)])
        else:
            cur.execute("SELECT * FROM florida_parcels WHERE parcel_id = %s", [property_id])
        
        property_data = cur.fetchone()
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        cur.close()
        conn.close()
        
        # Format the response
        return {
            'success': True,
            'data': dict(property_data),
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_property_type_name(property_use: str) -> str:
    """Convert property use code to readable property type"""
    if not property_use:
        return "Unknown"
    
    # Get first 2-4 digits of code
    code = str(property_use)[:4] if property_use else '0000'
    prefix = code[:2]
    
    # Map based on prefix for better coverage
    if prefix == '00':
        return 'Vacant Residential'
    elif prefix == '01':
        return 'Single Family'
    elif prefix == '02':
        return 'Mobile Home'
    elif prefix == '03':
        return 'Multi-Family'
    elif prefix == '04':
        return 'Condominium'
    elif prefix == '05':
        return 'Cooperative'
    elif prefix == '06':
        return 'Retirement Home'
    elif prefix == '07':
        return 'Miscellaneous'
    elif prefix == '08':
        return 'Multi-Residential'
    elif prefix == '09':
        return 'Acreage'
    elif prefix == '10':
        return 'Vacant Commercial'
    elif prefix in ['11', '12', '13', '14', '15', '16', '17', '18', '19']:
        return 'Commercial'
    elif prefix in ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29']:
        return 'Commercial Services'
    elif prefix in ['30', '31', '32', '33', '34', '35', '36', '37', '38', '39']:
        return 'Recreation/Entertainment'
    elif prefix in ['40', '41', '42', '43', '44', '45', '46', '47', '48', '49']:
        return 'Industrial'
    elif prefix in ['50', '51', '52', '53', '54', '55', '56', '57', '58', '59']:
        return 'Agricultural'
    elif prefix in ['60', '61', '62', '63', '64', '65', '66', '67', '68', '69']:
        return 'Retirement/Special'
    elif prefix in ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79']:
        return 'Institutional'
    elif prefix in ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89']:
        return 'Government'
    elif prefix in ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99']:
        return 'Utilities/Rights'
    else:
        return 'Other'

@app.get("/api/tax-deed-auctions")
async def get_tax_deed_auctions():
    """Get all tax deed auctions"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM tax_deed_auctions 
            ORDER BY auction_date DESC
        """)
        
        auctions = cur.fetchall() or []
        cur.close()
        conn.close()
        
        # Convert to list of dicts
        auction_list = [dict(auction) for auction in auctions]
        
        return {
            'success': True,
            'data': auction_list,
            'total': len(auction_list)
        }
        
    except Exception as e:
        logger.error(f"Error fetching tax deed auctions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tax-deed-items")
async def get_tax_deed_items(parcel_id: Optional[str] = Query(None)):
    """Get tax deed bidding items, optionally filtered by parcel ID"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if parcel_id:
            cur.execute("""
                SELECT * FROM tax_deed_items_view 
                WHERE parcel_id = %s
                ORDER BY auction_date DESC
            """, (parcel_id,))
        else:
            cur.execute("""
                SELECT * FROM tax_deed_items_view 
                ORDER BY auction_date DESC
                LIMIT 50
            """)
        
        items = cur.fetchall() or []
        cur.close()
        conn.close()
        
        # Convert to list of dicts
        item_list = [dict(item) for item in items]
        
        return {
            'success': True,
            'data': item_list,
            'total': len(item_list)
        }
        
    except Exception as e:
        logger.error(f"Error fetching tax deed items: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Autocomplete Endpoints
@app.get("/api/autocomplete/addresses")
async def autocomplete_addresses(
    q: str = Query(..., min_length=2),
    limit: int = Query(20)
) -> List[str]:
    """Autocomplete for property addresses from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Search addresses using ILIKE for case-insensitive partial matching
        cur.execute("""
            SELECT DISTINCT phy_addr1
            FROM florida_parcels 
            WHERE phy_addr1 ILIKE %s
            AND phy_addr1 IS NOT NULL
            AND phy_addr1 != ''
            ORDER BY phy_addr1
            LIMIT %s
        """, (f"%{q}%", limit))
        
        results = cur.fetchall() or []
        cur.close()
        conn.close()
        
        # Extract addresses
        addresses = [row['phy_addr1'] for row in results if row['phy_addr1']]
        return addresses
        
    except Exception as e:
        logger.error(f"Error in autocomplete_addresses: {str(e)}")
        return []

@app.get("/api/autocomplete/cities")
async def autocomplete_cities(
    q: str = Query(..., min_length=2),
    limit: int = Query(10)
) -> List[str]:
    """Autocomplete for cities from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT phy_city
            FROM florida_parcels 
            WHERE phy_city ILIKE %s
            AND phy_city IS NOT NULL
            AND phy_city != ''
            ORDER BY phy_city
            LIMIT %s
        """, (f"%{q}%", limit))
        
        results = cur.fetchall() or []
        cur.close()
        conn.close()
        
        # Extract cities
        cities = [row['phy_city'] for row in results if row['phy_city']]
        return cities
        
    except Exception as e:
        logger.error(f"Error in autocomplete_cities: {str(e)}")
        return []

@app.get("/api/autocomplete/owners")
async def autocomplete_owners(
    q: str = Query(..., min_length=2),
    limit: int = Query(10)
) -> List[str]:
    """Autocomplete for property owners from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT own_name
            FROM florida_parcels 
            WHERE own_name ILIKE %s
            AND own_name IS NOT NULL
            AND own_name != ''
            ORDER BY own_name
            LIMIT %s
        """, (f"%{q}%", limit))
        
        results = cur.fetchall() or []
        cur.close()
        conn.close()
        
        # Extract owner names
        owners = [row['own_name'] for row in results if row['own_name']]
        return owners
        
    except Exception as e:
        logger.error(f"Error in autocomplete_owners: {str(e)}")
        return []

@app.get("/api/autocomplete/usage-codes")
async def autocomplete_usage_codes(
    q: str = Query(..., min_length=1),
    limit: int = Query(20)
) -> List[Dict[str, str]]:
    """Autocomplete for DOR usage codes"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT dor_uc, COUNT(*) as count
            FROM florida_parcels 
            WHERE dor_uc ILIKE %s
            AND dor_uc IS NOT NULL
            AND dor_uc != ''
            GROUP BY dor_uc
            ORDER BY count DESC, dor_uc
            LIMIT %s
        """, (f"%{q}%", limit))
        
        results = cur.fetchall() or []
        cur.close()
        conn.close()
        
        # Format usage codes with descriptions
        usage_codes = []
        for row in results:
            code = row['dor_uc']
            count = row['count']
            
            # Basic category mapping
            if code.startswith('0'):
                category = "Residential"
            elif code.startswith('1') or code.startswith('2') or code.startswith('3'):
                category = "Commercial"
            elif code.startswith('4'):
                category = "Industrial"
            else:
                category = "Other"
                
            usage_codes.append({
                "code": code,
                "description": f"Usage Code {code}",
                "category": category,
                "count": count,
                "display": f"{code} - {category} ({count:,} properties)"
            })
        
        return usage_codes
        
    except Exception as e:
        logger.error(f"Error in autocomplete_usage_codes: {str(e)}")
        return []

if __name__ == "__main__":
    # Test database connection on startup
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM florida_parcels")
        count = cur.fetchone()['count']
        logger.info(f"Database connected successfully! Found {count:,} properties")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    # Run the server
    uvicorn.run(
        "direct_database_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )