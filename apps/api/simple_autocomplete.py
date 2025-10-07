"""
Simple Autocomplete API for ConcordBroker
Provides fast autocomplete for property search
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from supabase import create_client
import uvicorn

app = FastAPI(title="Simple Autocomplete API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
async def root():
    return {
        "service": "Simple Autocomplete API",
        "status": "running",
        "endpoints": ["/api/autocomplete"]
    }

@app.get("/api/autocomplete")
async def autocomplete(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50)
):
    """Address autocomplete with unit numbers for condos"""

    query = q.strip()

    if len(query) < 2:
        return {"suggestions": [], "success": True, "data": []}

    suggestions = []

    try:
        # Get properties including phy_addr2 which might have unit info
        result = supabase.table('florida_parcels') \
            .select('phy_addr1,phy_addr2,phy_city,phy_zipcd,owner_name,parcel_id,just_value') \
            .ilike('phy_addr1', f'{query}%') \
            .order('phy_addr1') \
            .limit(limit) \
            .execute()

        for row in result.data:
            address = (row.get('phy_addr1') or '').strip()
            address2 = (row.get('phy_addr2') or '').strip()  # This might contain unit info
            city = (row.get('phy_city') or '').strip()
            parcel_id = row.get('parcel_id', '')

            # Skip if address is empty
            if not address:
                continue

            # Try to extract unit number from various sources
            unit_number = ""

            # Check if phy_addr2 contains unit info
            if address2:
                # Look for patterns like "UNIT 1234", "APT 5B", "#401", etc.
                import re
                unit_match = re.search(r'(UNIT|APT|#|SUITE|STE)\s*([A-Z0-9]+)', address2, re.IGNORECASE)
                if unit_match:
                    unit_number = unit_match.group(2)
                else:
                    # Sometimes it's just the unit number
                    if address2 and len(address2) <= 10:  # Reasonable length for a unit number
                        unit_number = address2

            # If no unit found in address2, try extracting from parcel_id patterns
            if not unit_number and parcel_id:
                # For condos, parcel IDs often have patterns indicating unit
                # Example: 8580920000 might have the unit encoded
                # This is property-specific and may need adjustment
                pass

            # Format display address with unit if available
            display_address = address
            if unit_number:
                display_address = f"{address} Unit {unit_number}"

            # Format full address for display
            full_address = f"{display_address}, {city} {row.get('phy_zipcd', '')}".strip(', ')

            # Check if this is a condo based on unit number presence
            is_condo = bool(unit_number)  # If has unit number, likely a condo

            suggestions.append({
                # Autocomplete display fields
                "address": display_address,
                "city": city,
                "zip_code": row.get('phy_zipcd', ''),
                "full_address": full_address,
                "type": "property",

                # Unit information
                "unit_number": unit_number,
                "is_condo": is_condo,

                # Complete property data for mini cards (using both field formats)
                "parcel_id": parcel_id,

                # Owner fields (both formats for compatibility)
                "owner_name": row.get('owner_name', ''),
                "own_name": row.get('owner_name', ''),

                # Value fields (all formats)
                "just_value": row.get('just_value', 0),
                "jv": row.get('just_value', 0),
                "market_value": row.get('just_value', 0),

                # Property type
                "property_type": "Condo" if is_condo else "Property",

                # Address fields (formatted for cards)
                "phy_addr1": address,
                "phy_addr2": address2,
                "phy_city": city,
                "phy_zipcd": row.get('phy_zipcd', '')
            })

    except Exception as e:
        print(f"Database error: {e}")
        # Return empty results on error
        suggestions = []

    return {
        "suggestions": suggestions,
        "success": True,
        "data": suggestions
    }

if __name__ == "__main__":
    print("Starting Simple Autocomplete API on port 8003...")
    uvicorn.run(app, host="0.0.0.0", port=8003)