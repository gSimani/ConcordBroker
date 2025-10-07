"""
Identify which counties have missing data by comparing NAL vs Supabase
"""
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment
load_dotenv()

SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load NAL analysis
with open(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\nal_large_properties_analysis.json", 'r') as f:
    nal_data = json.load(f)

print("=" * 80)
print("MISSING DATA ANALYSIS BY COUNTY")
print("=" * 80)

# Get NAL county breakdown
nal_counties = {item['county']: item['count'] for item in nal_data['county_breakdown']}

print("\nQuerying Supabase for county-level data...")
print("This may take a few minutes...\n")

# Query Supabase for each county
supabase_counts = {}
errors = []

for county_name in sorted(nal_counties.keys()):
    try:
        result = supabase.table('florida_parcels') \
            .select('parcel_id', count='exact') \
            .eq('county', county_name) \
            .gte('total_living_area', 7500) \
            .limit(1) \
            .execute()

        count = result.count if hasattr(result, 'count') else 0
        supabase_counts[county_name] = count
        print(f"  {county_name:<20s} - {count:>6,} large properties")
    except Exception as e:
        errors.append(f"{county_name}: {e}")
        supabase_counts[county_name] = 0

if errors:
    print("\nErrors encountered:")
    for error in errors:
        print(f"  {error}")

# Analysis
print("\n" + "=" * 80)
print("COMPARISON BY COUNTY")
print("=" * 80)

print(f"\n{'County':<20s} {'NAL':>10s} {'Supabase':>10s} {'Missing':>10s} {'% Loss':>8s}")
print("-" * 80)

total_nal = 0
total_supabase = 0
total_missing = 0

counties_with_loss = []

for county in sorted(nal_counties.keys(), key=lambda x: nal_counties[x], reverse=True):
    nal_count = nal_counties[county]
    sb_count = supabase_counts.get(county, 0)
    missing = nal_count - sb_count
    missing_pct = (missing / nal_count * 100) if nal_count > 0 else 0

    total_nal += nal_count
    total_supabase += sb_count
    total_missing += missing

    symbol = ""
    if missing_pct > 30:
        symbol = " ⚠️ HIGH LOSS"
        counties_with_loss.append((county, missing, missing_pct))
    elif missing_pct > 20:
        symbol = " ⚠️"
        counties_with_loss.append((county, missing, missing_pct))

    print(f"{county:<20s} {nal_count:>10,} {sb_count:>10,} {missing:>10,} {missing_pct:>7.1f}%{symbol}")

print("-" * 80)
print(f"{'TOTAL':<20s} {total_nal:>10,} {total_supabase:>10,} {total_missing:>10,} {(total_missing/total_nal*100):>7.1f}%")

# Counties with significant loss
if counties_with_loss:
    print("\n" + "=" * 80)
    print("COUNTIES WITH SIGNIFICANT DATA LOSS (>20%)")
    print("=" * 80)

    for county, missing, pct in sorted(counties_with_loss, key=lambda x: x[2], reverse=True):
        print(f"{county:<20s} Missing: {missing:>6,} properties ({pct:.1f}%)")

# Check if any counties are completely missing
print("\n" + "=" * 80)
print("COUNTIES WITH NO LARGE PROPERTIES IN SUPABASE")
print("=" * 80)

missing_counties = [county for county, count in supabase_counts.items() if count == 0 and nal_counties.get(county, 0) > 0]

if missing_counties:
    print("\nThese counties have large properties in NAL but NONE in Supabase:")
    for county in sorted(missing_counties):
        print(f"  {county:<20s} Expected: {nal_counties[county]:>6,} properties")
else:
    print("\nAll counties have at least some data in Supabase.")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

if counties_with_loss:
    print("\n1. Re-import data for counties with >20% loss:")
    for county, _, _ in counties_with_loss[:5]:
        print(f"   - {county}")

if missing_counties:
    print("\n2. Import missing counties:")
    for county in missing_counties[:5]:
        print(f"   - {county}")

print("\n3. Investigate import logs for:")
print("   - Timeout errors during upload")
print("   - Validation failures")
print("   - Duplicate key conflicts")

print("\n" + "=" * 80)
print("END OF ANALYSIS")
print("=" * 80)