"""
Final comparison between NAL source files and Supabase database
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment from the main .env (frontend variables)
load_dotenv()

SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in .env")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("FINAL COMPARISON REPORT: NAL FILES vs SUPABASE DATABASE")
print("=" * 80)

# First, load the NAL analysis results
try:
    with open(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\nal_large_properties_analysis.json", 'r') as f:
        nal_data = json.load(f)
except FileNotFoundError:
    print("\nERROR: NAL analysis file not found. Run analyze_large_properties.py first.")
    exit(1)

print("\n" + "=" * 80)
print("NAL SOURCE FILES ANALYSIS (Ground Truth)")
print("=" * 80)

nal_summary = nal_data['summary']
print(f"\nTotal Files Analyzed: {nal_summary['total_files_analyzed']}")
print(f"Total Large Properties (7,500+ sqft): {nal_summary['total_large_properties']:,}")

print("\nBreakdown by Size Range:")
print("-" * 80)
print(f"{'Size Range':<25} {'Count':>15} {'Percentage':>12}")
print("-" * 80)

for range_label, count in nal_summary['size_range_counts'].items():
    pct = (count / nal_summary['total_large_properties'] * 100) if nal_summary['total_large_properties'] > 0 else 0
    print(f"{range_label:<25} {count:>15,} {pct:>11.1f}%")

# Now query Supabase
print("\n" + "=" * 80)
print("SUPABASE DATABASE ANALYSIS")
print("=" * 80)

# Define size ranges
ranges = [
    (7500, 10000, "7,500-10,000 sqft"),
    (10000, 15000, "10,000-15,000 sqft"),
    (15000, 20000, "15,000-20,000 sqft"),
    (20000, 30000, "20,000-30,000 sqft"),
    (30000, 50000, "30,000-50,000 sqft"),
    (50000, 999999, "50,000+ sqft")
]

print("\nQuerying Supabase for large properties...")

supabase_counts = {}
supabase_total = 0

for min_size, max_size, label in ranges:
    try:
        # Query with count
        result = supabase.table('florida_parcels') \
            .select('parcel_id', count='exact') \
            .gte('total_living_area', min_size) \
            .lt('total_living_area', max_size) \
            .limit(1) \
            .execute()

        count = result.count if hasattr(result, 'count') else 0
        supabase_counts[label] = count
        supabase_total += count
    except Exception as e:
        print(f"Error querying {label}: {e}")
        supabase_counts[label] = 0

print("\nBreakdown by Size Range:")
print("-" * 80)
print(f"{'Size Range':<25} {'Count':>15} {'Percentage':>12}")
print("-" * 80)

for label, count in supabase_counts.items():
    pct = (count / supabase_total * 100) if supabase_total > 0 else 0
    print(f"{label:<25} {count:>15,} {pct:>11.1f}%")

print("-" * 80)
print(f"{'TOTAL':<25} {supabase_total:>15,}")

# Get database statistics
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

    # Records with living area
    result = supabase.table('florida_parcels') \
        .select('parcel_id', count='exact') \
        .gt('total_living_area', 0) \
        .limit(1) \
        .execute()
    with_living = result.count if hasattr(result, 'count') else 0

    print(f"\nTotal records in Supabase: {total_records:,}")
    print(f"Records with living area > 0: {with_living:,}")
    print(f"Records with living area >= 7,500 sqft: {supabase_total:,}")

except Exception as e:
    print(f"\nFailed to get statistics: {e}")

# COMPARISON
print("\n" + "=" * 80)
print("COMPARISON: NAL vs SUPABASE")
print("=" * 80)

print("\nSummary:")
print("-" * 80)
print(f"NAL Source Files (Ground Truth): {nal_summary['total_large_properties']:>15,} large properties")
print(f"Supabase Database (Current):     {supabase_total:>15,} large properties")
print("-" * 80)

if nal_summary['total_large_properties'] > 0:
    missing = nal_summary['total_large_properties'] - supabase_total
    missing_pct = (missing / nal_summary['total_large_properties'] * 100)
    imported_pct = (supabase_total / nal_summary['total_large_properties'] * 100)

    print(f"Properties Imported:             {imported_pct:>14.1f}%")
    print(f"Properties MISSING:              {missing_pct:>14.1f}%")
    print(f"Missing Count:                   {missing:>15,} properties")

print("\nDetailed Comparison by Size Range:")
print("-" * 80)
print(f"{'Size Range':<25} {'NAL':>12} {'Supabase':>12} {'Missing':>12} {'% Missing':>12}")
print("-" * 80)

for label in ranges:
    range_label = label[2]
    nal_count = nal_summary['size_range_counts'].get(range_label, 0)
    sb_count = supabase_counts.get(range_label, 0)
    missing = nal_count - sb_count
    missing_pct = (missing / nal_count * 100) if nal_count > 0 else 0

    print(f"{range_label:<25} {nal_count:>12,} {sb_count:>12,} {missing:>12,} {missing_pct:>11.1f}%")

# Sample properties that SHOULD be in Supabase
print("\n" + "=" * 80)
print("VERIFICATION: Sample Properties from NAL Files")
print("=" * 80)

# Get samples from NAL data and check if they exist in Supabase
samples_to_check = []
for range_label, samples in nal_data['samples'].items():
    for sample in samples[:2]:  # Check 2 from each range
        samples_to_check.append({
            'parcel_id': sample['parcel_id'],
            'living_area': sample['living_area'],
            'range': range_label
        })

print(f"\nChecking {len(samples_to_check)} sample properties in Supabase...")
print("-" * 80)

found_count = 0
not_found_count = 0

for sample in samples_to_check[:10]:  # Check first 10
    try:
        result = supabase.table('florida_parcels') \
            .select('parcel_id, total_living_area, county, owner_name') \
            .eq('parcel_id', sample['parcel_id']) \
            .execute()

        if result.data and len(result.data) > 0:
            found_count += 1
            prop = result.data[0]
            status = "FOUND"
            living_area = prop.get('total_living_area', 0)
            print(f"{status:10s} Parcel: {sample['parcel_id']:20s} NAL: {sample['living_area']:>8,.0f} sqft  Supabase: {living_area:>8,.0f} sqft")
        else:
            not_found_count += 1
            print(f"NOT FOUND  Parcel: {sample['parcel_id']:20s} NAL: {sample['living_area']:>8,.0f} sqft  Supabase: N/A")
    except Exception as e:
        not_found_count += 1
        print(f"ERROR      Parcel: {sample['parcel_id']:20s} {e}")

print("-" * 80)
print(f"Sample Check Results: {found_count} found, {not_found_count} not found")

# FINAL VERDICT
print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

if supabase_total == 0:
    print("\nCRITICAL ISSUE: NO large properties found in Supabase!")
    print("The florida_parcels table appears to be EMPTY or the upload was NOT COMPLETED.")
    print("\nAction Required:")
    print("1. The NAL files contain comprehensive data")
    print("2. The Supabase database needs to be populated")
    print("3. Run the NAL import/upload process to populate florida_parcels table")
elif supabase_total < nal_summary['total_large_properties'] * 0.5:
    print(f"\nMAJOR DATA LOSS: Only {imported_pct:.1f}% of large properties imported!")
    print("\nPossible Causes:")
    print("1. Upload was interrupted or incomplete")
    print("2. Data filtering during import removed large properties")
    print("3. Column mapping error (e.g., total_living_area not mapped correctly)")
    print("4. Only a subset of counties were imported")
elif supabase_total < nal_summary['total_large_properties'] * 0.9:
    print(f"\nPARTIAL IMPORT: Only {imported_pct:.1f}% of large properties imported")
    print("\nRecommendation: Review import logs and re-import missing counties")
else:
    print(f"\nGOOD: {imported_pct:.1f}% of large properties successfully imported")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80)