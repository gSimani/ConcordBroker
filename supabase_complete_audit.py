"""
COMPREHENSIVE SUPABASE DATABASE AUDIT
Using Supabase REST API and Python analysis
"""
import sys
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
print(" " * 30 + "COMPREHENSIVE SUPABASE AUDIT")
print(" " * 25 + "AI-Powered Database Analysis System")
print("=" * 100)
print()

audit_results = {
    "timestamp": datetime.now().isoformat(),
    "tables": {},
    "data_quality": {},
    "recommendations": []
}

# ============================================================================
# PHASE 1: DISCOVER ALL TABLES
# ============================================================================
print("PHASE 1: TABLE DISCOVERY VIA SUPABASE API")
print("-" * 100)

# List of known tables to check
known_tables = [
    'florida_parcels',
    'property_sales_history',
    'florida_entities',
    'sunbiz_corporate',
    'tax_certificates',
    'tax_deed_auctions',
    'dor_use_codes',
    'User',
    'property_notes',
    'property_contacts'
]

existing_tables = []

print("\nChecking known tables...\n")

for table_name in known_tables:
    try:
        response = supabase.table(table_name).select('*', count='exact').limit(1).execute()
        row_count = response.count if hasattr(response, 'count') else 0
        existing_tables.append(table_name)
        print(f"  ✅ {table_name:<30} - {row_count:,} rows")
        audit_results["tables"][table_name] = {
            "exists": True,
            "row_count": row_count
        }
    except Exception as e:
        print(f"  ❌ {table_name:<30} - NOT FOUND or ERROR")
        audit_results["tables"][table_name] = {
            "exists": False,
            "error": str(e)
        }

print()

# ============================================================================
# PHASE 2: DEEP ANALYSIS OF FLORIDA_PARCELS
# ============================================================================
print("=" * 100)
print("PHASE 2: FLORIDA_PARCELS DEEP ANALYSIS")
print("-" * 100)

try:
    # Get a larger sample for accurate analysis
    print("\nFetching 5,000 sample properties for analysis...")
    response = supabase.table('florida_parcels').select('*').limit(5000).execute()
    properties = response.data

    print(f"Analyzing {len(properties)} properties\n")

    # Get all column names from first property
    if properties:
        all_columns = list(properties[0].keys())
        print(f"Total columns found: {len(all_columns)}\n")

        # Analyze data completeness
        field_stats = defaultdict(lambda: {"null": 0, "not_null": 0, "zero": 0, "unique_samples": set()})

        critical_fields = [
            'parcel_id', 'county', 'year', 'owner_name', 'phy_addr1', 'phy_city', 'phy_zipcd',
            'just_value', 'assessed_value', 'taxable_value', 'land_value', 'building_value',
            'total_living_area', 'land_sqft', 'bedrooms', 'bathrooms', 'stories', 'units',
            'year_built', 'property_use', 'property_use_desc', 'land_use_code', 'zoning',
            'sale_date', 'sale_price', 'sale_qualification'
        ]

        for prop in properties:
            for field in critical_fields:
                if field in prop:
                    value = prop[field]
                    if value is None or value == '':
                        field_stats[field]["null"] += 1
                    elif value == 0:
                        field_stats[field]["zero"] += 1
                        field_stats[field]["not_null"] += 1
                    else:
                        field_stats[field]["not_null"] += 1
                        # Sample unique values
                        if len(field_stats[field]["unique_samples"]) < 10:
                            field_stats[field]["unique_samples"].add(str(value)[:30])

        print("FIELD COMPLETENESS ANALYSIS:")
        print()
        print(f"{'Field':<28} {'Has Data':<12} {'Null/Empty':<12} {'Zero':<10} {'% Complete':<12} {'Status'}")
        print("-" * 100)

        for field in critical_fields:
            not_null = field_stats[field]["not_null"]
            null = field_stats[field]["null"]
            zero = field_stats[field]["zero"]
            total = not_null + null
            pct = (not_null / total * 100) if total > 0 else 0

            status = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"

            print(f"{field:<28} {not_null:<12,} {null:<12,} {zero:<10,} {pct:<11.1f}% {status}")

            audit_results["data_quality"][field] = {
                "not_null": not_null,
                "null": null,
                "zero": zero,
                "pct_complete": pct,
                "unique_samples": list(field_stats[field]["unique_samples"])
            }

            if pct < 50:
                audit_results["recommendations"].append({
                    "type": "LOW_DATA_QUALITY",
                    "table": "florida_parcels",
                    "field": field,
                    "severity": "HIGH",
                    "message": f"Field '{field}' only {pct:.1f}% complete"
                })

        print()

except Exception as e:
    print(f"ERROR in Phase 2: {e}")

# ============================================================================
# PHASE 3: BUILDING SQUARE FOOTAGE COMPREHENSIVE ANALYSIS
# ============================================================================
print("=" * 100)
print("PHASE 3: BUILDING SQUARE FOOTAGE COMPREHENSIVE ANALYSIS")
print("-" * 100)

try:
    print("\nQuerying ALL properties with buildings (may take a moment)...")

    # Get count of properties with buildings
    response_count = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .not_.is_('total_living_area', 'null')\
        .gt('total_living_area', 0)\
        .limit(1)\
        .execute()

    total_with_buildings = response_count.count if hasattr(response_count, 'count') else 0
    print(f"Total properties with buildings: {total_with_buildings:,}\n")

    # Query specific ranges
    ranges_to_check = [
        (0, 1000),
        (1000, 2000),
        (2000, 5000),
        (5000, 10000),
        (10000, 20000),
        (20000, 50000),
        (50000, 100000)
    ]

    print("BUILDING SIZE DISTRIBUTION:")
    print()
    print(f"{'Size Range':<25} {'Count':<15} {'% of Total':<12} {'Sample Properties'}")
    print("-" * 100)

    for low, high in ranges_to_check:
        try:
            response = supabase.table('florida_parcels')\
                .select('parcel_id, phy_addr1, phy_city, total_living_area, just_value, county', count='exact')\
                .gte('total_living_area', low)\
                .lt('total_living_area', high)\
                .limit(3)\
                .execute()

            count = response.count if hasattr(response, 'count') else 0
            pct = (count / total_with_buildings * 100) if total_with_buildings > 0 else 0

            # Get sample properties
            samples = []
            if response.data:
                for prop in response.data[:2]:
                    addr = prop.get('phy_addr1', 'No Address')[:20]
                    city = prop.get('phy_city', 'Unknown')[:15]
                    sqft = prop.get('total_living_area', 0)
                    samples.append(f"{sqft:,} sqft - {addr}, {city}")

            sample_text = " | ".join(samples) if samples else "No samples"

            range_label = f"{low:,}-{high:,} sqft"
            print(f"{range_label:<25} {count:<15,} {pct:<11.1f}% {sample_text[:60]}")

        except Exception as e:
            print(f"{low:,}-{high:,} sqft: Error - {e}")

    print()

    # Focus on 10k-20k range
    print("\nDETAILED ANALYSIS: 10,000-20,000 SQFT BUILDINGS")
    print("-" * 80)

    response_detailed = supabase.table('florida_parcels')\
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, county, total_living_area, just_value, building_value, property_use')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .limit(50)\
        .execute()

    if response_detailed.data:
        print(f"\nFound {len(response_detailed.data)} properties in 10k-20k sqft range:\n")

        for i, prop in enumerate(response_detailed.data[:20], 1):
            parcel = prop.get('parcel_id', 'Unknown')
            addr = prop.get('phy_addr1', 'No Address')[:30]
            city = prop.get('phy_city', 'Unknown')[:15]
            county = prop.get('county', 'Unknown')[:10]
            sqft = prop.get('total_living_area', 0)
            value = prop.get('just_value', 0)
            use_code = prop.get('property_use', 'N/A')

            print(f"  {i:2d}. {sqft:,} sqft | ${value:,} | {addr:30s} | {city:15s} | {county:10s} | Use: {use_code}")

        # Analyze by county
        county_counts = defaultdict(int)
        for prop in response_detailed.data:
            county = prop.get('county', 'UNKNOWN')
            county_counts[county] += 1

        print("\n\nBy County:")
        for county, count in sorted(county_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {county:15s}: {count:3d} properties")

    else:
        print("\n❌ NO PROPERTIES FOUND in 10k-20k sqft range!")
        audit_results["recommendations"].append({
            "type": "DATA_ANOMALY",
            "severity": "HIGH",
            "message": "No properties found with buildings 10k-20k sqft - possible data issue"
        })

    print()

except Exception as e:
    print(f"ERROR in Phase 3: {e}")

# ============================================================================
# PHASE 4: FILTER TESTING
# ============================================================================
print("=" * 100)
print("PHASE 4: FILTER ACCURACY TESTING")
print("-" * 100)

print("\nTesting various filter combinations...\n")

filter_tests = [
    {"name": "All properties", "filters": {}},
    {"name": "With buildings > 0", "filters": {"total_living_area": ">0"}},
    {"name": "Buildings 1k-2k sqft", "filters": {"total_living_area": "1000-2000"}},
    {"name": "Buildings 10k-20k sqft", "filters": {"total_living_area": "10000-20000"}},
    {"name": "Value $500k-$1M", "filters": {"just_value": "500000-1000000"}},
    {"name": "Value $500k-$1M + Buildings 10k-20k", "filters": {"just_value": "500000-1000000", "total_living_area": "10000-20000"}}
]

for test in filter_tests:
    try:
        query = supabase.table('florida_parcels').select('parcel_id', count='exact')

        filters = test["filters"]

        if "total_living_area" in filters:
            val = filters["total_living_area"]
            if val == ">0":
                query = query.gt('total_living_area', 0)
            elif "-" in val:
                low, high = val.split("-")
                query = query.gte('total_living_area', int(low)).lte('total_living_area', int(high))

        if "just_value" in filters:
            val = filters["just_value"]
            if "-" in val:
                low, high = val.split("-")
                query = query.gte('just_value', int(low)).lte('just_value', int(high))

        response = query.limit(1).execute()
        count = response.count if hasattr(response, 'count') else 0

        status = "✅" if count > 0 else "❌"
        print(f"  {status} {test['name']:<50} Results: {count:,}")

    except Exception as e:
        print(f"  ❌ {test['name']:<50} Error: {e}")

print()

# ============================================================================
# SAVE RESULTS
# ============================================================================
output_file = f"supabase_complete_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(audit_results, f, indent=2, default=str)

print("=" * 100)
print("AUDIT COMPLETE")
print("=" * 100)
print(f"\nResults saved to: {output_file}")
print()
print("SUMMARY:")
print(f"  - Tables checked: {len(audit_results['tables'])}")
print(f"  - Tables existing: {len([t for t in audit_results['tables'].values() if t.get('exists', False)])}")
print(f"  - Data quality issues: {len([r for r in audit_results['recommendations'] if r['type'] == 'LOW_DATA_QUALITY'])}")
print(f"  - Total recommendations: {len(audit_results['recommendations'])}")
print()
print("=" * 100)