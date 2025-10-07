"""
Check Supabase florida_parcels table for large properties
"""
import os
from supabase import create_client, Client

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.mcp')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: Missing Supabase credentials in .env.mcp")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 80)
print("SUPABASE LARGE PROPERTIES ANALYSIS")
print("=" * 80)

# Query for large properties breakdown
query = """
SELECT
    CASE
        WHEN total_living_area >= 7500 AND total_living_area < 10000 THEN '7,500-10,000 sqft'
        WHEN total_living_area >= 10000 AND total_living_area < 15000 THEN '10,000-15,000 sqft'
        WHEN total_living_area >= 15000 AND total_living_area < 20000 THEN '15,000-20,000 sqft'
        WHEN total_living_area >= 20000 AND total_living_area < 30000 THEN '20,000-30,000 sqft'
        WHEN total_living_area >= 30000 AND total_living_area < 50000 THEN '30,000-50,000 sqft'
        WHEN total_living_area >= 50000 THEN '50,000+ sqft'
    END as size_range,
    COUNT(*) as count
FROM florida_parcels
WHERE total_living_area >= 7500
GROUP BY size_range
ORDER BY MIN(total_living_area);
"""

print("\nQuerying Supabase for large properties (7,500+ sqft)...")

try:
    # Use RPC or direct query
    result = supabase.rpc('execute_sql', {'query': query}).execute()

    print("\nResults:")
    print("-" * 80)

    total = 0
    for row in result.data:
        count = row['count']
        total += count
        print(f"{row['size_range']:20s}: {count:8,}")

    print("-" * 80)
    print(f"{'TOTAL':20s}: {total:8,}")

except Exception as e:
    print(f"\nDirect SQL query failed: {e}")
    print("\nTrying alternative method with filters...")

    # Try alternative method using filters
    ranges = [
        (7500, 10000, "7,500-10,000 sqft"),
        (10000, 15000, "10,000-15,000 sqft"),
        (15000, 20000, "15,000-20,000 sqft"),
        (20000, 30000, "20,000-30,000 sqft"),
        (30000, 50000, "30,000-50,000 sqft"),
        (50000, 999999, "50,000+ sqft")
    ]

    print("\nResults:")
    print("-" * 80)

    total = 0
    for min_size, max_size, label in ranges:
        try:
            result = supabase.table('florida_parcels') \
                .select('parcel_id', count='exact') \
                .gte('total_living_area', min_size) \
                .lt('total_living_area', max_size) \
                .execute()

            count = result.count if hasattr(result, 'count') else len(result.data)
            total += count
            print(f"{label:20s}: {count:8,}")
        except Exception as e2:
            print(f"{label:20s}: ERROR - {e2}")

    print("-" * 80)
    print(f"{'TOTAL':20s}: {total:8,}")

# Get some sample properties
print("\n" + "=" * 80)
print("SAMPLE LARGE PROPERTIES FROM SUPABASE")
print("=" * 80)

try:
    result = supabase.table('florida_parcels') \
        .select('parcel_id, county, total_living_area, dor_uc, owner_name') \
        .gte('total_living_area', 7500) \
        .order('total_living_area', desc=True) \
        .limit(10) \
        .execute()

    print("\nTop 10 Largest Properties:")
    print("-" * 80)
    for i, prop in enumerate(result.data, 1):
        print(f"\n{i}. Parcel ID: {prop.get('parcel_id', 'N/A')}")
        print(f"   County: {prop.get('county', 'N/A')}")
        print(f"   Living Area: {prop.get('total_living_area', 0):,.0f} sqft")
        print(f"   DOR Use Code: {prop.get('dor_uc', 'N/A')}")
        print(f"   Owner: {prop.get('owner_name', 'N/A')[:50]}")

except Exception as e:
    print(f"\nFailed to get sample properties: {e}")

# Check total records with living area data
print("\n" + "=" * 80)
print("DATABASE STATISTICS")
print("=" * 80)

try:
    # Total records
    result = supabase.table('florida_parcels') \
        .select('parcel_id', count='exact') \
        .limit(1) \
        .execute()
    total_records = result.count if hasattr(result, 'count') else 0
    print(f"\nTotal records in florida_parcels: {total_records:,}")

    # Records with living area
    result = supabase.table('florida_parcels') \
        .select('parcel_id', count='exact') \
        .gt('total_living_area', 0) \
        .limit(1) \
        .execute()
    with_living = result.count if hasattr(result, 'count') else 0
    print(f"Records with living area > 0: {with_living:,}")

    # Records with large living area
    result = supabase.table('florida_parcels') \
        .select('parcel_id', count='exact') \
        .gte('total_living_area', 7500) \
        .limit(1) \
        .execute()
    large_props = result.count if hasattr(result, 'count') else 0
    print(f"Records with living area >= 7,500 sqft: {large_props:,}")

    percentage = (large_props / with_living * 100) if with_living > 0 else 0
    print(f"Percentage of large properties: {percentage:.2f}%")

except Exception as e:
    print(f"\nFailed to get statistics: {e}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)