"""
DEFINITIVE ANALYSIS: Large Buildings in Florida
Compare NAL source files vs Supabase to find the truth
"""
import os
import csv
import json
from datetime import datetime
from collections import defaultdict
from supabase import create_client, Client

print("=" * 100)
print("DEFINITIVE ANALYSIS: Large Buildings in Florida")
print("Comparing NAL source files vs Supabase database")
print("=" * 100)
print()

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

results = {
    "timestamp": datetime.now().isoformat(),
    "nal_files": {},
    "supabase": {},
    "comparison": {}
}

# Define size ranges
size_ranges = [
    (7500, 10000, "7.5k-10k"),
    (10000, 15000, "10k-15k"),
    (15000, 20000, "15k-20k"),
    (20000, 30000, "20k-30k"),
    (30000, 50000, "30k-50k"),
    (50000, 1000000, "50k+")
]

# ============================================================================
# PART 1: Analyze NAL Source Files
# ============================================================================
print("PART 1: Analyzing NAL Source Files")
print("-" * 100)

source_dir = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

nal_stats = {
    "total_files": 0,
    "total_properties": 0,
    "with_building": 0,
    "by_size": {r[2]: 0 for r in size_ranges},
    "by_county": defaultdict(lambda: {"total": 0, "large": 0}),
    "samples": []
}

print("Scanning for NAL files...")

for root, dirs, files in os.walk(source_dir):
    for file in files:
        if file.upper().startswith('NAL') and file.endswith('.csv'):
            nal_stats["total_files"] += 1
            file_path = os.path.join(root, file)
            county = os.path.basename(os.path.dirname(root))

            try:
                with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    reader = csv.DictReader(f)

                    for row in reader:
                        nal_stats["total_properties"] += 1

                        # Get TOT_LVG_AREA value
                        living_area = row.get('TOT_LVG_AREA', '')

                        if living_area and living_area.strip():
                            try:
                                sqft = int(living_area)
                                if sqft > 0:
                                    nal_stats["with_building"] += 1
                                    nal_stats["by_county"][county]["total"] += 1

                                    # Check if it's a large building
                                    for low, high, label in size_ranges:
                                        if low <= sqft < high:
                                            nal_stats["by_size"][label] += 1
                                            nal_stats["by_county"][county]["large"] += 1

                                            # Save sample
                                            if len(nal_stats["samples"]) < 50:
                                                nal_stats["samples"].append({
                                                    "parcel_id": row.get('PARCEL_ID'),
                                                    "county": county,
                                                    "sqft": sqft,
                                                    "owner": row.get('OWN_NAME', '')[:50]
                                                })
                                            break
                            except (ValueError, TypeError):
                                pass

                print(f"  ✓ {county:20s} - {file:30s}")

            except Exception as e:
                print(f"  ✗ {county:20s} - ERROR: {str(e)[:50]}")

print()
print(f"NAL Files Summary:")
print(f"  Files processed: {nal_stats['total_files']}")
print(f"  Total properties: {nal_stats['total_properties']:,}")
print(f"  With buildings: {nal_stats['with_building']:,}")
print()

print("Large buildings by size range (NAL files):")
print(f"{'Size Range':<20} {'Count':>15} {'% of Buildings':>15}")
print("-" * 55)
total_large = 0
for label in [r[2] for r in size_ranges]:
    count = nal_stats["by_size"][label]
    total_large += count
    pct = (count / nal_stats["with_building"] * 100) if nal_stats["with_building"] > 0 else 0
    print(f"{label:<20} {count:>15,} {pct:>14.2f}%")

print(f"{'TOTAL LARGE':<20} {total_large:>15,}")
print()

results["nal_files"] = nal_stats

# ============================================================================
# PART 2: Analyze Supabase Database
# ============================================================================
print()
print("=" * 100)
print("PART 2: Analyzing Supabase Database")
print("-" * 100)

supabase_stats = {
    "by_size": {r[2]: 0 for r in size_ranges},
    "samples": []
}

print("Querying Supabase for large buildings...")
print()

for low, high, label in size_ranges:
    try:
        # Use aggressive pagination to get count
        offset = 0
        batch_size = 1000
        range_count = 0

        while True:
            response = supabase.table('florida_parcels')\
                .select('parcel_id, county, total_living_area, owner_name')\
                .gte('total_living_area', low)\
                .lt('total_living_area', high)\
                .range(offset, offset + batch_size - 1)\
                .execute()

            if not response.data:
                break

            batch_count = len(response.data)
            range_count += batch_count

            # Save samples from first batch
            if offset == 0:
                for prop in response.data[:5]:
                    supabase_stats["samples"].append({
                        "parcel_id": prop.get('parcel_id'),
                        "county": prop.get('county'),
                        "sqft": prop.get('total_living_area'),
                        "owner": (prop.get('owner_name') or '')[:50]
                    })

            # If we got less than batch_size, we're done
            if batch_count < batch_size:
                break

            offset += batch_size

            # Safety limit
            if offset > 50000:
                print(f"  ⚠️  {label}: Reached 50k limit, actual count may be higher")
                break

        supabase_stats["by_size"][label] = range_count
        print(f"  ✓ {label:<20} {range_count:>15,} properties")

    except Exception as e:
        print(f"  ✗ {label:<20} ERROR: {str(e)[:60]}")
        supabase_stats["by_size"][label] = 0

print()

total_supabase = sum(supabase_stats["by_size"].values())
print(f"Total large buildings in Supabase: {total_supabase:,}")
print()

results["supabase"] = supabase_stats

# ============================================================================
# PART 3: Comparison and Analysis
# ============================================================================
print()
print("=" * 100)
print("PART 3: COMPARISON AND ANALYSIS")
print("-" * 100)
print()

print(f"{'Size Range':<20} {'NAL Files':>15} {'Supabase':>15} {'Difference':>15} {'% Missing':>12}")
print("-" * 85)

comparison = []
total_nal = 0
total_db = 0

for label in [r[2] for r in size_ranges]:
    nal_count = nal_stats["by_size"][label]
    db_count = supabase_stats["by_size"][label]
    diff = nal_count - db_count
    pct_missing = (diff / nal_count * 100) if nal_count > 0 else 0

    total_nal += nal_count
    total_db += db_count

    status = "✓" if abs(pct_missing) < 10 else "⚠️"
    print(f"{status} {label:<18} {nal_count:>15,} {db_count:>15,} {diff:>15,} {pct_missing:>11.1f}%")

    comparison.append({
        "range": label,
        "nal": nal_count,
        "supabase": db_count,
        "difference": diff,
        "pct_missing": pct_missing
    })

print("-" * 85)
total_diff = total_nal - total_db
total_pct_missing = (total_diff / total_nal * 100) if total_nal > 0 else 0
print(f"{'TOTAL':<20} {total_nal:>15,} {total_db:>15,} {total_diff:>15,} {total_pct_missing:>11.1f}%")

results["comparison"]["by_size"] = comparison
results["comparison"]["total_nal"] = total_nal
results["comparison"]["total_supabase"] = total_db
results["comparison"]["missing"] = total_diff
results["comparison"]["pct_missing"] = total_pct_missing

# ============================================================================
# FINDINGS
# ============================================================================
print()
print("=" * 100)
print("KEY FINDINGS")
print("=" * 100)
print()

findings = []

if total_nal > 50000:
    findings.append(f"✓ NAL source files contain {total_nal:,} large buildings (7,500+ sqft)")
    findings.append(f"  This is {int(total_nal / 794)} times more than Zillow's estimate of 794")
else:
    findings.append(f"⚠️  Only {total_nal:,} large buildings found in NAL files (seems low)")

if total_db < 1000:
    findings.append(f"❌ CRITICAL: Only {total_db:,} large buildings in Supabase")
    findings.append(f"  This is {total_pct_missing:.1f}% missing from source files!")
    findings.append(f"  {total_diff:,} properties need to be imported")
elif total_pct_missing > 20:
    findings.append(f"⚠️  WARNING: {total_pct_missing:.1f}% of large buildings missing from Supabase")
    findings.append(f"  {total_diff:,} properties need to be imported")
else:
    findings.append(f"✓ Good import success rate: {100 - total_pct_missing:.1f}% complete")

# Top counties
print("Top 10 Counties by Large Building Count (NAL files):")
print("-" * 60)
sorted_counties = sorted(nal_stats["by_county"].items(), key=lambda x: x[1]["large"], reverse=True)[:10]
for i, (county, stats) in enumerate(sorted_counties, 1):
    print(f"  {i:2d}. {county:20s} {stats['large']:>10,} large buildings")

print()
print()

for finding in findings:
    print(finding)

results["findings"] = findings

print()

# Sample properties
print()
print("Sample Large Properties from NAL Files:")
print("-" * 100)
print(f"{'County':<15} {'Parcel ID':<20} {'SqFt':>10} {'Owner':<50}")
print("-" * 100)
for sample in nal_stats["samples"][:15]:
    print(f"{sample['county']:<15} {sample['parcel_id']:<20} {sample['sqft']:>10,} {sample['owner']:<50}")

print()

# Save results
output_file = f"large_buildings_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2, default=str)

print()
print("=" * 100)
print(f"Analysis complete. Results saved to: {output_file}")
print("=" * 100)