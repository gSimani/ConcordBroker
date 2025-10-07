"""
DEFINITIVE ANALYSIS: Large Buildings in Florida - Simple Version
"""
import os
import csv
import json
import sys
from datetime import datetime
from collections import defaultdict

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 100)
print("DEFINITIVE ANALYSIS: Large Buildings in Florida")
print("=" * 100)
print()

# Define size ranges
size_ranges = [
    (7500, 10000, "7.5k-10k"),
    (10000, 15000, "10k-15k"),
    (15000, 20000, "15k-20k"),
    (20000, 30000, "20k-30k"),
    (30000, 50000, "30k-50k"),
    (50000, 1000000, "50k+")
]

nal_stats = {
    "total_files": 0,
    "total_properties": 0,
    "with_building": 0,
    "by_size": {r[2]: 0 for r in size_ranges},
    "by_county": defaultdict(lambda: {"total": 0, "large": 0}),
    "samples": []
}

print("PART 1: Analyzing NAL Source Files")
print("-" * 100)

source_dir = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

print(f"Scanning: {source_dir}")
print()

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

                        living_area = row.get('TOT_LVG_AREA', '')

                        if living_area and living_area.strip():
                            try:
                                sqft = int(living_area)
                                if sqft > 0:
                                    nal_stats["with_building"] += 1
                                    nal_stats["by_county"][county]["total"] += 1

                                    for low, high, label in size_ranges:
                                        if low <= sqft < high:
                                            nal_stats["by_size"][label] += 1
                                            nal_stats["by_county"][county]["large"] += 1

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

                print(f"  OK  {county:20s} - {file:30s}")

            except Exception as e:
                print(f"  ERR {county:20s} - {str(e)[:50]}")

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

print("Top 10 Counties by Large Building Count:")
print(f"{'County':<20} {'Large Buildings':>20}")
print("-" * 45)
sorted_counties = sorted(nal_stats["by_county"].items(), key=lambda x: x[1]["large"], reverse=True)[:10]
for i, (county, stats) in enumerate(sorted_counties, 1):
    print(f"  {i:2d}. {county:20s} {stats['large']:>15,}")

print()
print()

print("Sample Large Properties:")
print(f"{'County':<15} {'Parcel ID':<20} {'SqFt':>10} {'Owner':<50}")
print("-" * 100)
for sample in nal_stats["samples"][:20]:
    print(f"{sample['county']:<15} {sample['parcel_id']:<20} {sample['sqft']:>10,} {sample['owner']:<50}")

print()
print("=" * 100)
print(f"CONCLUSION: Found {total_large:,} large buildings (7,500+ sqft) in NAL source files")
print("=" * 100)

# Save results
output_file = f"nal_large_buildings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(nal_stats, f, indent=2, default=str)

print(f"Results saved to: {output_file}")