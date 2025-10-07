"""
Check Supabase for large buildings using direct SQL queries
"""
import sys
from supabase import create_client, Client

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 100)
print("SUPABASE DATABASE ANALYSIS - Large Buildings")
print("=" * 100)
print()

# Test 1: Count ALL properties with buildings
print("Test 1: Count of properties with total_living_area > 0")
print("-" * 80)
try:
    response = supabase.table('florida_parcels')\
        .select('*', count='exact', head=True)\
        .gt('total_living_area', 0)\
        .execute()

    total_with_buildings = response.count if hasattr(response, 'count') else 0
    print(f"  Properties with buildings: {total_with_buildings:,}")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 2: Count large buildings by range
print("Test 2: Count large buildings by size range")
print("-" * 80)

size_ranges = [
    (7500, 10000, "7.5k-10k"),
    (10000, 15000, "10k-15k"),
    (15000, 20000, "15k-20k"),
    (20000, 30000, "20k-30k"),
    (30000, 50000, "30k-50k"),
    (50000, 1000000, "50k+")
]

total_large = 0

for low, high, label in size_ranges:
    try:
        response = supabase.table('florida_parcels')\
            .select('*', count='exact', head=True)\
            .gte('total_living_area', low)\
            .lt('total_living_area', high)\
            .execute()

        count = response.count if hasattr(response, 'count') else 0
        total_large += count
        print(f"  {label:<15} {count:>12,}")

    except Exception as e:
        print(f"  {label:<15} ERROR: {e}")

print(f"  {'TOTAL LARGE':<15} {total_large:>12,}")
print()

# Test 3: Get actual sample properties
print("Test 3: Sample large properties from Supabase")
print("-" * 80)
try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id, county, total_living_area, owner_name')\
        .gte('total_living_area', 10000)\
        .lt('total_living_area', 20000)\
        .limit(20)\
        .execute()

    if response.data:
        print(f"Found {len(response.data)} properties in 10k-20k range:")
        print()
        print(f"{'Parcel ID':<20} {'County':<15} {'SqFt':>10} {'Owner':<50}")
        print("-" * 100)
        for prop in response.data:
            parcel_id = prop.get('parcel_id', '')
            county = prop.get('county', '')
            sqft = prop.get('total_living_area', 0)
            owner = (prop.get('owner_name') or '')[:48]
            print(f"{parcel_id:<20} {county:<15} {sqft:>10,} {owner:<50}")
    else:
        print("  No properties found in 10k-20k range!")

except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 4: Check specific parcels from NAL files
print("Test 4: Verify specific parcels from NAL files exist in Supabase")
print("-" * 80)

test_parcels = [
    ("00024-011-000", "ALACHUA", 26000),
    ("00082-000-000", "ALACHUA", 50757),
    ("00153-000-000", "ALACHUA", 78619),
]

for parcel_id, county, expected_sqft in test_parcels:
    try:
        response = supabase.table('florida_parcels')\
            .select('parcel_id, county, total_living_area')\
            .eq('parcel_id', parcel_id)\
            .eq('county', county.upper())\
            .execute()

        if response.data:
            prop = response.data[0]
            actual_sqft = prop.get('total_living_area', 0)
            match = "OK" if actual_sqft == expected_sqft else f"MISMATCH ({actual_sqft})"
            print(f"  {parcel_id:<20} {county:<15} Expected: {expected_sqft:>8,} - {match}")
        else:
            print(f"  {parcel_id:<20} {county:<15} Expected: {expected_sqft:>8,} - NOT FOUND")

    except Exception as e:
        print(f"  {parcel_id:<20} ERROR: {e}")

print()
print("=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)