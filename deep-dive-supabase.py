"""
Deep dive into Supabase florida_parcels table to understand building sqft data
"""
import os
import sys
from supabase import create_client, Client

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("🔍 DEEP DIVE: Supabase florida_parcels Building Square Footage Analysis")
print("=" * 80)
print()

# Step 1: Get table structure
print("📋 Step 1: Checking florida_parcels table columns...")
print("-" * 80)

try:
    # Query a single row to see all columns
    response = supabase.table('florida_parcels').select('*').limit(1).execute()

    if response.data and len(response.data) > 0:
        columns = list(response.data[0].keys())
        print(f"✅ Found {len(columns)} columns in florida_parcels table")
        print()

        # Look for building/living area related columns
        building_cols = [col for col in columns if 'area' in col.lower() or 'sqft' in col.lower() or 'living' in col.lower() or 'building' in col.lower()]

        print("🏠 Building/Area related columns:")
        for col in building_cols:
            sample_value = response.data[0].get(col)
            print(f"   - {col}: {sample_value} (type: {type(sample_value).__name__})")

        print()
        print("📊 All columns (first 50):")
        for i, col in enumerate(columns[:50], 1):
            print(f"   {i:2d}. {col}")

        if len(columns) > 50:
            print(f"   ... and {len(columns) - 50} more columns")

    print()
except Exception as e:
    print(f"❌ Error: {e}")
    print()

# Step 2: Check if total_living_area exists and has data
print("=" * 80)
print("📋 Step 2: Checking 'total_living_area' column...")
print("-" * 80)

try:
    # Try to query total_living_area
    response = supabase.table('florida_parcels').select('parcel_id, total_living_area').limit(100).execute()

    if response.data:
        # Count how many have non-null, non-zero values
        with_data = [p for p in response.data if p.get('total_living_area') and p.get('total_living_area') > 0]

        print(f"✅ total_living_area column EXISTS")
        print(f"   Sample size: {len(response.data)} properties")
        print(f"   With building data: {len(with_data)} ({len(with_data)/len(response.data)*100:.1f}%)")
        print(f"   Without building data: {len(response.data) - len(with_data)} ({(len(response.data) - len(with_data))/len(response.data)*100:.1f}%)")
        print()

        if with_data:
            print("   Sample properties WITH buildings:")
            for i, prop in enumerate(with_data[:5], 1):
                print(f"   {i}. Parcel: {prop['parcel_id']} - {prop['total_living_area']:,} sqft")

        print()

except Exception as e:
    print(f"❌ Error: {e}")
    print()

# Step 3: Find properties with buildings between 10,000 - 20,000 sqft
print("=" * 80)
print("📋 Step 3: Searching for properties with 10,000-20,000 sqft buildings...")
print("-" * 80)

try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id, phy_addr1, phy_city, total_living_area, just_value, county')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .limit(20)\
        .execute()

    if response.data:
        print(f"✅ Found {len(response.data)} properties with buildings 10k-20k sqft")
        print()

        for i, prop in enumerate(response.data, 1):
            address = prop.get('phy_addr1', 'No Address')
            city = prop.get('phy_city', 'Unknown')
            sqft = prop.get('total_living_area', 0)
            value = prop.get('just_value', 0)
            county = prop.get('county', 'Unknown')

            print(f"   {i:2d}. {sqft:,} sqft | ${value:,} | {address[:30]:30s} | {city} ({county})")

        print()
    else:
        print("❌ NO properties found with buildings 10k-20k sqft")
        print()

except Exception as e:
    print(f"❌ Error querying 10k-20k range: {e}")
    print()

# Step 4: Get statistics on building sizes
print("=" * 80)
print("📋 Step 4: Building size distribution statistics...")
print("-" * 80)

try:
    # Sample 10,000 properties to get distribution
    response = supabase.table('florida_parcels')\
        .select('total_living_area')\
        .not_.is_('total_living_area', 'null')\
        .gt('total_living_area', 0)\
        .limit(10000)\
        .execute()

    if response.data:
        sizes = [p['total_living_area'] for p in response.data if p.get('total_living_area')]

        if sizes:
            sizes.sort()

            print(f"✅ Analyzed {len(sizes)} properties with buildings")
            print()
            print("   Distribution:")
            print(f"   - Minimum:  {min(sizes):,} sqft")
            print(f"   - 25th %ile: {sizes[len(sizes)//4]:,} sqft")
            print(f"   - Median:    {sizes[len(sizes)//2]:,} sqft")
            print(f"   - 75th %ile: {sizes[3*len(sizes)//4]:,} sqft")
            print(f"   - Maximum:   {max(sizes):,} sqft")
            print()

            # Count by ranges
            ranges = [
                (0, 1000),
                (1000, 2000),
                (2000, 5000),
                (5000, 10000),
                (10000, 20000),
                (20000, 50000),
                (50000, float('inf'))
            ]

            print("   Buildings by size range:")
            for low, high in ranges:
                count = sum(1 for s in sizes if low <= s < high)
                pct = count / len(sizes) * 100
                range_label = f"{low:,}-{high:,}" if high != float('inf') else f"{low:,}+"
                print(f"   - {range_label:20s}: {count:5d} ({pct:5.1f}%)")

            print()
    else:
        print("❌ No building data found")
        print()

except Exception as e:
    print(f"❌ Error getting statistics: {e}")
    print()

# Step 5: Check total count of properties with buildings in 10k-20k range
print("=" * 80)
print("📋 Step 5: TOTAL COUNT of properties with 10k-20k sqft buildings...")
print("-" * 80)

try:
    # Count total
    response = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .limit(1)\
        .execute()

    total_count = response.count if hasattr(response, 'count') else 0

    print(f"📊 TOTAL properties with buildings 10k-20k sqft: {total_count:,}")
    print()

    if total_count == 0:
        print("⚠️  ZERO properties found in this range!")
        print("   This suggests either:")
        print("   1. The column name is wrong")
        print("   2. The data is stored differently")
        print("   3. The values are in a different unit")
        print()
    else:
        print(f"✅ There ARE {total_count:,} properties in this range in the database!")
        print("   The API filter should work if using correct column name.")
        print()

except Exception as e:
    print(f"❌ Error counting total: {e}")
    print()

print("=" * 80)
print("✅ Deep Dive Complete")
print("=" * 80)