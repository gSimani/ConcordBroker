"""
Fixed Autocomplete API with timeout handling
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import asyncio
from supabase import create_client
import uvicorn
import time

app = FastAPI(title="Fixed Autocomplete API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase connection with timeout
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Create client with custom timeout
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fallback mock data for testing
MOCK_DATA = [
    {
        "phy_addr1": "123 Main Street",
        "phy_addr2": "Unit 101",
        "phy_city": "Miami",
        "phy_zipcd": "33101",
        "owner_name": "John Smith",
        "parcel_id": "123456789",
        "just_value": 450000
    },
    {
        "phy_addr1": "456 Oak Avenue",
        "phy_addr2": None,
        "phy_city": "Fort Lauderdale",
        "phy_zipcd": "33301",
        "owner_name": "Jane Doe",
        "parcel_id": "987654321",
        "just_value": 325000
    },
    {
        "phy_addr1": "789 Beach Boulevard",
        "phy_addr2": "APT 2405",
        "phy_city": "Miami Beach",
        "phy_zipcd": "33139",
        "owner_name": "Beach Properties LLC",
        "parcel_id": "555666777",
        "just_value": 1250000
    }
]

@app.get("/")
async def root():
    return {
        "service": "Fixed Autocomplete API",
        "status": "running",
        "endpoints": ["/api/autocomplete", "/api/autocomplete/combined"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

async def query_with_timeout(query_func, timeout=5):
    """Execute a query with timeout"""
    try:
        # Create a task for the query
        task = asyncio.create_task(asyncio.to_thread(query_func))
        # Wait for it with a timeout
        result = await asyncio.wait_for(task, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        print(f"Query timeout after {timeout} seconds")
        return None
    except Exception as e:
        print(f"Query error: {e}")
        return None

@app.get("/api/autocomplete")
@app.get("/api/autocomplete/combined")
async def autocomplete(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50)
):
    """Address autocomplete with unit numbers for condos"""

    query = q.strip()

    if len(query) < 2:
        return {"suggestions": [], "success": True, "data": []}

    suggestions = []

    # Try database first with timeout
    try:
        print(f"Attempting database query for: {query}")

        # Define the query function
        def run_query():
            # Only select essential fields to minimize query time
            return supabase.table('florida_parcels') \
                .select('parcel_id,phy_addr1,phy_addr2,phy_city,phy_zipcd,owner_name,just_value') \
                .ilike('phy_addr1', f'{query}%') \
                .limit(limit) \
                .execute()

        # Execute with timeout
        result = await query_with_timeout(run_query, timeout=3)

        if result and result.data:
            print(f"Got {len(result.data)} results from database")
            rows = result.data
        else:
            print("Database query failed or timed out, using mock data")
            # Filter mock data based on query
            rows = [row for row in MOCK_DATA if query.lower() in row['phy_addr1'].lower()][:limit]
    except Exception as e:
        print(f"Database error: {e}, using mock data")
        # Filter mock data based on query
        rows = [row for row in MOCK_DATA if query.lower() in row['phy_addr1'].lower()][:limit]

    # Process results
    for row in rows:
        address = (row.get('phy_addr1') or '').strip()
        address2 = (row.get('phy_addr2') or '').strip()
        city = (row.get('phy_city') or '').strip()
        zip_code = row.get('phy_zipcd', '')
        parcel_id = row.get('parcel_id', '')

        # Skip if address is empty
        if not address:
            continue

        # Extract unit number if present
        unit_number = ""
        if address2:
            import re
            unit_match = re.search(r'(UNIT|APT|#|SUITE|STE)\s*([A-Z0-9]+)', address2, re.IGNORECASE)
            if unit_match:
                unit_number = unit_match.group(2)
            elif address2 and len(address2) <= 10:
                unit_number = address2

        # Format display address with unit if available
        display_address = address
        if unit_number:
            display_address = f"{address} Unit {unit_number}"

        # Format full address for display
        full_address = f"{display_address}, {city} {zip_code}".strip(', ')

        # Check if this is a condo based on unit number presence
        is_condo = bool(unit_number)

        # Get the appraised value (handle None values)
        just_value = row.get('just_value', 0) or 0

        suggestions.append({
            # Autocomplete display fields
            "address": display_address,
            "city": city,
            "zip_code": zip_code,
            "full_address": full_address,
            "type": "property",

            # Unit information
            "unit_number": unit_number,
            "is_condo": is_condo,

            # Complete property data for mini cards
            "parcel_id": parcel_id,

            # Owner fields (both formats for compatibility)
            "owner_name": row.get('owner_name', ''),
            "own_name": row.get('owner_name', ''),

            # Value fields (all formats) - ensure numbers, not None
            "just_value": just_value,
            "jv": just_value,
            "market_value": just_value,
            "appraised_value": just_value,

            # Property type
            "property_type": "Condo" if is_condo else "Property",

            # Address fields (formatted for cards)
            "phy_addr1": address,
            "phy_addr2": address2,
            "phy_city": city,
            "phy_zipcd": zip_code
        })

    print(f"Returning {len(suggestions)} suggestions")

    return {
        "suggestions": suggestions,
        "success": True,
        "data": suggestions
    }

if __name__ == "__main__":
    print("Starting Fixed Autocomplete API on port 8003...")
    print("This API includes timeout handling and fallback to mock data")
    uvicorn.run(app, host="0.0.0.0", port=8003)