"""
COMPREHENSIVE BUILDING SQUARE FOOTAGE ANALYSIS
Deep dive into Supabase and source files to find the truth about building sizes
"""
import sys
import os
import json
from datetime import datetime
from collections import defaultdict
from supabase import create_client, Client

# Fix Unicode on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 100)
print(" " * 30 + "COMPREHENSIVE BUILDING SQFT ANALYSIS")
print(" " * 25 + "Finding the Truth About Large Buildings in Florida")
print("=" * 100)
print()

analysis_results = {
    "timestamp": datetime.now().isoformat(),
    "supabase_analysis": {},
    "source_files_analysis": {},
    "findings": [],
    "recommendations": []
}

# ============================================================================
# PHASE 1: SUPABASE DATABASE ANALYSIS
# ============================================================================
print("PHASE 1: SUPABASE DATABASE DEEP ANALYSIS")
print("-" * 100)
print()

# Check what columns actually exist for building size
print("Step 1: Identifying all building size related columns...")
print("-" * 80)

try:
    # Get a sample property to see all columns
    response = supabase.table('florida_parcels').select('*').limit(1).execute()

    if response.data and len(response.data) > 0:
        all_columns = list(response.data[0].keys())
        print(f"Total columns in florida_parcels: {len(all_columns)}")
        print()

        # Find all building/area related columns
        building_columns = [col for col in all_columns if any(
            keyword in col.lower()
            for keyword in ['area', 'sqft', 'square', 'living', 'building', 'bldg', 'gross', 'net']
        )]

        print(f"Found {len(building_columns)} building/area related columns:")
        for col in building_columns:
            sample_value = response.data[0].get(col)
            print(f"  • {col:40s} = {sample_value}")

        analysis_results["supabase_analysis"]["total_columns"] = len(all_columns)
        analysis_results["supabase_analysis"]["building_columns"] = building_columns

        print()
    else:
        print("❌ ERROR: Could not fetch sample property")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Check total_living_area specifically
print("Step 2: Analyzing total_living_area column...")
print("-" * 80)

try:
    # Get total count of properties
    response_total = supabase.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
    total_properties = response_total.count if hasattr(response_total, 'count') else 0
    print(f"Total properties in database: {total_properties:,}")

    # Count properties WITH building data
    response_with_building = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .not_.is_('total_living_area', 'null')\
        .gt('total_living_area', 0)\
        .limit(1)\
        .execute()

    with_building = response_with_building.count if hasattr(response_with_building, 'count') else 0
    pct_with_building = (with_building / total_properties * 100) if total_properties > 0 else 0

    print(f"Properties WITH total_living_area > 0: {with_building:,} ({pct_with_building:.1f}%)")
    print(f"Properties WITHOUT building data: {total_properties - with_building:,} ({100 - pct_with_building:.1f}%)")
    print()

    analysis_results["supabase_analysis"]["total_properties"] = total_properties
    analysis_results["supabase_analysis"]["with_building_data"] = with_building
    analysis_results["supabase_analysis"]["pct_with_building_data"] = pct_with_building

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Now the crucial test - count by size ranges
print("Step 3: CRITICAL TEST - Count properties by building size ranges...")
print("-" * 80)

size_ranges = [
    (0, 1000, "0-1,000 sqft"),
    (1000, 2000, "1,000-2,000 sqft"),
    (2000, 3000, "2,000-3,000 sqft"),
    (3000, 5000, "3,000-5,000 sqft"),
    (5000, 7500, "5,000-7,500 sqft"),
    (7500, 10000, "7,500-10,000 sqft"),
    (10000, 15000, "10,000-15,000 sqft"),
    (15000, 20000, "15,000-20,000 sqft"),
    (20000, 30000, "20,000-30,000 sqft"),
    (30000, 50000, "30,000-50,000 sqft"),
    (50000, 100000, "50,000-100,000 sqft"),
    (100000, float('inf'), "100,000+ sqft")
]

print(f"{'Size Range':<25} {'Count':>15} {'% of Total':>12} {'% of Buildings':>15}")
print("-" * 80)

size_distribution = []

for low, high, label in size_ranges:
    try:
        if high == float('inf'):
            response = supabase.table('florida_parcels')\
                .select('parcel_id', count='exact')\
                .gte('total_living_area', low)\
                .limit(1)\
                .execute()
        else:
            response = supabase.table('florida_parcels')\
                .select('parcel_id', count='exact')\
                .gte('total_living_area', low)\
                .lt('total_living_area', high)\
                .limit(1)\
                .execute()

        count = response.count if hasattr(response, 'count') else 0
        pct_of_total = (count / total_properties * 100) if total_properties > 0 else 0
        pct_of_buildings = (count / with_building * 100) if with_building > 0 else 0

        status = "✅" if count > 0 else "❌"
        print(f"{status} {label:<23} {count:>15,} {pct_of_total:>11.2f}% {pct_of_buildings:>14.2f}%")

        size_distribution.append({
            "range": label,
            "low": low,
            "high": high if high != float('inf') else 999999999,
            "count": count,
            "pct_of_total": pct_of_total,
            "pct_of_buildings": pct_of_buildings
        })

    except Exception as e:
        print(f"❌ {label:<23} ERROR: {e}")

print()

analysis_results["supabase_analysis"]["size_distribution"] = size_distribution

# Find the BIGGEST buildings
print("Step 4: Finding the LARGEST buildings in database...")
print("-" * 80)

try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id, county, phy_addr1, phy_city, total_living_area, just_value, building_value, property_use')\
        .order('total_living_area', desc=True)\
        .limit(20)\
        .execute()

    if response.data:
        print(f"Top 20 LARGEST buildings by total_living_area:")
        print()
        print(f"{'Rank':<6} {'SqFt':>10} {'Value':>15} {'Address':<35} {'City':<20} {'County':<15}")
        print("-" * 120)

        largest_buildings = []
        for i, prop in enumerate(response.data, 1):
            sqft = prop.get('total_living_area', 0)
            value = prop.get('just_value', 0)
            addr = (prop.get('phy_addr1', 'No Address') or 'No Address')[:33]
            city = (prop.get('phy_city', 'Unknown') or 'Unknown')[:18]
            county = (prop.get('county', 'Unknown') or 'Unknown')[:13]

            print(f"{i:<6} {sqft:>10,} ${value:>14,} {addr:<35} {city:<20} {county:<15}")

            largest_buildings.append({
                "rank": i,
                "parcel_id": prop.get('parcel_id'),
                "sqft": sqft,
                "value": value,
                "address": addr,
                "city": city,
                "county": county
            })

        analysis_results["supabase_analysis"]["largest_buildings"] = largest_buildings
        print()
    else:
        print("❌ No buildings found!")
        print()

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# Check by county
print("Step 5: Building distribution by county...")
print("-" * 80)

try:
    # Get sample of properties with buildings
    response = supabase.table('florida_parcels')\
        .select('county, total_living_area')\
        .not_.is_('total_living_area', 'null')\
        .gt('total_living_area', 0)\
        .limit(10000)\
        .execute()

    if response.data:
        county_stats = defaultdict(lambda: {"total": 0, "over_10k": 0, "over_20k": 0})

        for prop in response.data:
            county = prop.get('county', 'UNKNOWN')
            sqft = prop.get('total_living_area', 0)

            county_stats[county]["total"] += 1
            if sqft >= 10000:
                county_stats[county]["over_10k"] += 1
            if sqft >= 20000:
                county_stats[county]["over_20k"] += 1

        # Sort by total
        sorted_counties = sorted(county_stats.items(), key=lambda x: x[1]["total"], reverse=True)[:15]

        print(f"{'County':<20} {'Total':>12} {'10k+ sqft':>12} {'20k+ sqft':>12} {'% Large':>10}")
        print("-" * 80)

        for county, stats in sorted_counties:
            pct_large = (stats["over_10k"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"{county:<20} {stats['total']:>12,} {stats['over_10k']:>12,} {stats['over_20k']:>12,} {pct_large:>9.2f}%")

        print()

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# ============================================================================
# PHASE 2: SOURCE FILES ANALYSIS
# ============================================================================
print()
print("=" * 100)
print("PHASE 2: SOURCE FILES ANALYSIS")
print("-" * 100)
print()

source_directory = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

print(f"Scanning directory: {source_directory}")
print()

try:
    # Check if directory exists
    if not os.path.exists(source_directory):
        print(f"❌ ERROR: Directory does not exist: {source_directory}")
        analysis_results["findings"].append("Source directory not found")
    else:
        # Count files by type
        file_counts = defaultdict(int)
        total_size = 0

        for root, dirs, files in os.walk(source_directory):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                file_counts[ext] += 1
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)

        print(f"Found {sum(file_counts.values())} files, {total_size / (1024**3):.2f} GB total")
        print()
        print("File types:")
        for ext, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {ext or '(no extension)':15s}: {count:,} files")

        analysis_results["source_files_analysis"]["total_files"] = sum(file_counts.values())
        analysis_results["source_files_analysis"]["total_size_gb"] = total_size / (1024**3)
        analysis_results["source_files_analysis"]["file_types"] = dict(file_counts)

        print()

        # Look for NAP files (property characteristics including building sqft)
        print("Looking for NAP files (building characteristics)...")
        print("-" * 80)

        nap_files = []
        for root, dirs, files in os.walk(source_directory):
            for file in files:
                if 'NAP' in file.upper() and file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    county = os.path.basename(os.path.dirname(root))
                    nap_files.append({
                        "file": file,
                        "path": file_path,
                        "size_mb": file_size / (1024**2),
                        "county": county
                    })

        print(f"Found {len(nap_files)} NAP files")

        if nap_files:
            print()
            print("Sample NAP files:")
            for nap in nap_files[:10]:
                print(f"  {nap['county']:20s} - {nap['file']:40s} ({nap['size_mb']:.1f} MB)")

            analysis_results["source_files_analysis"]["nap_files_count"] = len(nap_files)
            analysis_results["source_files_analysis"]["nap_files_sample"] = nap_files[:10]

            # Try to read one NAP file to see what columns it has
            print()
            print("Analyzing sample NAP file structure...")
            print("-" * 80)

            sample_nap = nap_files[0]
            try:
                import csv
                with open(sample_nap['path'], 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames

                    print(f"NAP file: {sample_nap['file']}")
                    print(f"Columns: {len(headers)}")
                    print()

                    # Find building size related columns
                    building_cols = [col for col in headers if any(
                        keyword in col.upper()
                        for keyword in ['AREA', 'SQFT', 'SQUARE', 'LIVING', 'BUILDING', 'BLDG', 'GROSS', 'NET', 'TOT_LVG']
                    )]

                    print(f"Building-related columns in NAP file ({len(building_cols)}):")
                    for col in building_cols:
                        print(f"  • {col}")

                    print()

                    # Read a few samples
                    print("Sample data from NAP file:")
                    print("-" * 80)

                    f.seek(0)
                    next(reader)  # Skip header

                    samples = []
                    for i, row in enumerate(reader):
                        if i >= 5:
                            break

                        sample_data = {}
                        for col in building_cols[:5]:  # Show first 5 building columns
                            sample_data[col] = row.get(col, 'N/A')
                        samples.append(sample_data)

                        print(f"Row {i+1}:")
                        for col, val in sample_data.items():
                            print(f"  {col}: {val}")
                        print()

                    analysis_results["source_files_analysis"]["nap_sample_file"] = sample_nap['file']
                    analysis_results["source_files_analysis"]["nap_building_columns"] = building_cols
                    analysis_results["source_files_analysis"]["nap_samples"] = samples

            except Exception as e:
                print(f"❌ ERROR reading NAP file: {e}")
                print()

        print()

except Exception as e:
    print(f"❌ ERROR: {e}")
    print()

# ============================================================================
# PHASE 3: KEY FINDINGS AND RECOMMENDATIONS
# ============================================================================
print()
print("=" * 100)
print("PHASE 3: KEY FINDINGS AND RECOMMENDATIONS")
print("-" * 100)
print()

findings = []

# Analyze the distribution
over_10k = next((item for item in size_distribution if item["low"] == 10000 and item["high"] == 15000), None)
over_15k = next((item for item in size_distribution if item["low"] == 15000 and item["high"] == 20000), None)

if over_10k and over_15k:
    total_10k_20k = over_10k["count"] + over_15k["count"]
    findings.append(f"Found {total_10k_20k:,} properties with 10k-20k sqft buildings in Supabase")

    if total_10k_20k < 100:
        findings.append("⚠️  CRITICAL: This is SIGNIFICANTLY lower than expected")
        findings.append("   Zillow shows 794 results for 7.5k+ sqft in Florida")
        findings.append("   We should have thousands, not dozens")

        # Check if data is missing
        if pct_with_building < 50:
            findings.append(f"⚠️  PROBLEM IDENTIFIED: Only {pct_with_building:.1f}% of properties have building data")
            findings.append("   This explains the low counts!")

            recommendations = [
                "URGENT: Import NAP (building characteristics) files from source directory",
                f"We have {len(nap_files) if 'nap_files' in locals() else 0} NAP files ready to import",
                "NAP files contain TOT_LVG_AREA and other critical building data",
                "After import, building data completeness should increase from {:.1f}% to 90%+".format(pct_with_building),
                "This will add tens of thousands of large buildings to the database"
            ]
        else:
            findings.append("✅ Building data completeness is good")
            recommendations = [
                "Investigate why large buildings are missing despite good data completeness",
                "Check if total_living_area values are stored in different units",
                "Verify data import process for large properties"
            ]
    else:
        findings.append("✅ Building count looks reasonable")
        recommendations = ["Data appears complete"]

# Print findings
print("🔍 KEY FINDINGS:")
print()
for i, finding in enumerate(findings, 1):
    print(f"{i}. {finding}")

print()
print()

# Print recommendations
print("💡 RECOMMENDATIONS:")
print()
for i, rec in enumerate(recommendations if 'recommendations' in locals() else [], 1):
    print(f"{i}. {rec}")

print()

analysis_results["findings"] = findings
analysis_results["recommendations"] = recommendations if 'recommendations' in locals() else []

# Save results
output_file = f"building_sqft_comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(analysis_results, f, indent=2, default=str)

print()
print("=" * 100)
print("ANALYSIS COMPLETE")
print("=" * 100)
print(f"Results saved to: {output_file}")
print()
print("=" * 100)