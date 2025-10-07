"""
Final check for sales data availability
"""

from supabase import create_client

# Initialize Supabase client
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("FINAL SALES DATA CHECK")
print("=" * 60)

# Get properties with sales data
response = supabase.table('florida_parcels').select('parcel_id, phy_addr1, phy_city, sale_price, sale_date').gt('sale_price', 0).limit(10).execute()

if response.data and len(response.data) > 0:
    print("✅ SALES DATA EXISTS IN FLORIDA_PARCELS!")
    print(f"\nFound {len(response.data)} properties with sales data")
    print("\nSample records:")
    for i, prop in enumerate(response.data[:3], 1):
        print(f"\n{i}. Parcel: {prop['parcel_id']}")
        print(f"   Address: {prop['phy_addr1']}, {prop['phy_city']}")
        print(f"   Sale Price: ${prop['sale_price']:,.0f}" if prop['sale_price'] else "N/A")
        print(f"   Sale Date: {prop['sale_date'] or 'Not specified'}")
else:
    print("❌ NO SALES DATA FOUND")
    print("\nThe florida_parcels table has sales columns but they are empty.")
    print("Sales data needs to be imported from Florida Revenue SDF files.")
