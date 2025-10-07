"""
COMPREHENSIVE SUPABASE DATABASE AUDIT
Using SQLAlchemy, PySpark concepts, and AI-driven analysis
"""
import sys
import json
from datetime import datetime
from collections import defaultdict
from supabase import create_client, Client
from sqlalchemy import create_engine, inspect, MetaData, text
from sqlalchemy.orm import sessionmaker

# Fix Unicode on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# PostgreSQL connection string for SQLAlchemy
DB_URL = "postgresql://postgres.pmispwtdngkcmsrsjwbp:Gideon%40123@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 100)
print(" " * 30 + "COMPREHENSIVE SUPABASE AUDIT")
print(" " * 25 + "AI-Powered Database Analysis System")
print("=" * 100)
print()

# Create results dictionary
audit_results = {
    "timestamp": datetime.now().isoformat(),
    "database_url": SUPABASE_URL,
    "tables": {},
    "relationships": {},
    "data_quality": {},
    "recommendations": []
}

# ============================================================================
# PHASE 1: DISCOVER ALL TABLES USING SQLALCHEMY
# ============================================================================
print("PHASE 1: TABLE DISCOVERY")
print("-" * 100)

try:
    engine = create_engine(DB_URL, echo=False)
    inspector = inspect(engine)

    # Get all tables
    all_tables = inspector.get_table_names(schema='public')

    print(f"Found {len(all_tables)} tables in the database:\n")

    for i, table_name in enumerate(sorted(all_tables), 1):
        print(f"  {i:3d}. {table_name}")
        audit_results["tables"][table_name] = {
            "exists": True,
            "columns": [],
            "row_count": 0,
            "indexes": [],
            "foreign_keys": []
        }

    print()

except Exception as e:
    print(f"ERROR in Phase 1: {e}")
    print()

# ============================================================================
# PHASE 2: DETAILED TABLE ANALYSIS
# ============================================================================
print("=" * 100)
print("PHASE 2: DETAILED TABLE ANALYSIS")
print("-" * 100)

priority_tables = [
    'florida_parcels',
    'property_sales_history',
    'florida_entities',
    'sunbiz_corporate',
    'tax_certificates',
    'tax_deed_auctions',
    'property_assessments',
    'building_characteristics',
    'land_characteristics'
]

for table_name in priority_tables:
    print(f"\nAnalyzing: {table_name}")
    print("-" * 80)

    try:
        # Check if table exists
        if table_name not in all_tables:
            print(f"  ⚠️  TABLE DOES NOT EXIST!")
            audit_results["tables"][table_name] = {"exists": False}
            audit_results["recommendations"].append({
                "type": "MISSING_TABLE",
                "table": table_name,
                "severity": "HIGH",
                "message": f"Critical table '{table_name}' is missing from database"
            })
            continue

        # Get column information
        columns = inspector.get_columns(table_name, schema='public')
        print(f"  Columns: {len(columns)}")

        column_info = []
        for col in columns:
            column_info.append({
                "name": col['name'],
                "type": str(col['type']),
                "nullable": col['nullable'],
                "default": str(col.get('default', 'None'))
            })

        audit_results["tables"][table_name]["columns"] = column_info

        # Get indexes
        indexes = inspector.get_indexes(table_name, schema='public')
        print(f"  Indexes: {len(indexes)}")
        audit_results["tables"][table_name]["indexes"] = [idx['name'] for idx in indexes]

        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name, schema='public')
        print(f"  Foreign Keys: {len(foreign_keys)}")
        audit_results["tables"][table_name]["foreign_keys"] = foreign_keys

        # Get row count using Supabase client
        try:
            response = supabase.table(table_name).select('*', count='exact').limit(1).execute()
            row_count = response.count if hasattr(response, 'count') else 0
            print(f"  Row Count: {row_count:,}")
            audit_results["tables"][table_name]["row_count"] = row_count

            if row_count == 0:
                audit_results["recommendations"].append({
                    "type": "EMPTY_TABLE",
                    "table": table_name,
                    "severity": "MEDIUM",
                    "message": f"Table '{table_name}' exists but has no data"
                })
        except Exception as e:
            print(f"  Error getting row count: {e}")

        print(f"  ✅ Analysis complete")

    except Exception as e:
        print(f"  ❌ Error: {e}")

# ============================================================================
# PHASE 3: DATA QUALITY ANALYSIS - FLORIDA PARCELS
# ============================================================================
print("\n" + "=" * 100)
print("PHASE 3: DATA QUALITY ANALYSIS - florida_parcels")
print("-" * 100)

try:
    # Sample properties for analysis
    response = supabase.table('florida_parcels').select('*').limit(1000).execute()
    properties = response.data

    print(f"\nAnalyzing {len(properties)} sample properties...\n")

    # Analyze data completeness
    field_stats = defaultdict(lambda: {"null": 0, "not_null": 0, "unique_values": set()})

    critical_fields = [
        'parcel_id', 'county', 'owner_name', 'phy_addr1', 'phy_city',
        'just_value', 'assessed_value', 'taxable_value', 'land_value', 'building_value',
        'total_living_area', 'land_sqft', 'bedrooms', 'bathrooms',
        'year_built', 'property_use', 'sale_date', 'sale_price'
    ]

    for prop in properties:
        for field in critical_fields:
            if field in prop:
                value = prop[field]
                if value is None or value == '' or value == 0:
                    field_stats[field]["null"] += 1
                else:
                    field_stats[field]["not_null"] += 1
                    if len(field_stats[field]["unique_values"]) < 100:
                        field_stats[field]["unique_values"].add(str(value)[:50])

    print("Field Completeness Analysis:")
    print()
    print(f"{'Field':<25} {'Not Null':<12} {'Null/Empty':<12} {'% Complete':<12} {'Status'}")
    print("-" * 80)

    for field in critical_fields:
        not_null = field_stats[field]["not_null"]
        null = field_stats[field]["null"]
        total = not_null + null
        pct = (not_null / total * 100) if total > 0 else 0

        status = "✅" if pct >= 80 else "⚠️" if pct >= 50 else "❌"

        print(f"{field:<25} {not_null:<12,} {null:<12,} {pct:<11.1f}% {status}")

        audit_results["data_quality"][field] = {
            "not_null": not_null,
            "null": null,
            "pct_complete": pct
        }

        if pct < 50:
            audit_results["recommendations"].append({
                "type": "LOW_DATA_QUALITY",
                "table": "florida_parcels",
                "field": field,
                "severity": "HIGH",
                "message": f"Field '{field}' only {pct:.1f}% complete - may need additional data source"
            })

    print()

except Exception as e:
    print(f"ERROR in Phase 3: {e}")
    print()

# ============================================================================
# PHASE 4: IDENTIFY MISSING CRITICAL TABLES
# ============================================================================
print("=" * 100)
print("PHASE 4: MISSING CRITICAL TABLES ANALYSIS")
print("-" * 100)

expected_tables = {
    "property_characteristics": "Detailed building characteristics (rooms, features, construction)",
    "property_improvements": "Building improvements and renovations history",
    "property_exemptions": "Tax exemptions and special assessments",
    "property_liens": "Liens and encumbrances on properties",
    "property_permits": "Building permits and inspections",
    "property_violations": "Code violations and compliance issues",
    "property_zoning": "Zoning classifications and restrictions",
    "property_flood_zone": "Flood zone designations and insurance data",
    "property_utilities": "Utility availability and connections",
    "property_environmental": "Environmental hazards and assessments",
    "neighborhood_data": "Neighborhood statistics and demographics",
    "market_trends": "Market value trends and appreciation rates",
    "rental_data": "Rental rates and vacancy information",
    "foreclosure_data": "Foreclosure and distressed property data",
    "hoa_data": "HOA information and fees"
}

print("\nChecking for specialized property tables...\n")

missing_tables = []
for table_name, description in expected_tables.items():
    exists = table_name in all_tables
    status = "✅ EXISTS" if exists else "❌ MISSING"
    print(f"  {table_name:<30} {status:12} - {description}")

    if not exists:
        missing_tables.append(table_name)
        audit_results["recommendations"].append({
            "type": "RECOMMENDED_TABLE",
            "table": table_name,
            "severity": "MEDIUM",
            "message": f"Consider creating '{table_name}' table: {description}"
        })

print(f"\n  Missing {len(missing_tables)} specialized tables")
print()

# ============================================================================
# PHASE 5: BUILDING SQFT DEEP ANALYSIS
# ============================================================================
print("=" * 100)
print("PHASE 5: BUILDING SQUARE FOOTAGE DEEP ANALYSIS")
print("-" * 100)

try:
    # Query properties with buildings
    response = supabase.table('florida_parcels')\
        .select('parcel_id, county, phy_city, total_living_area, building_value, just_value, property_use')\
        .not_.is_('total_living_area', 'null')\
        .gt('total_living_area', 0)\
        .limit(10000)\
        .execute()

    building_data = response.data

    print(f"\nAnalyzed {len(building_data)} properties with buildings\n")

    # Analyze by size range
    size_ranges = [
        (0, 1000, "0-1,000 sqft"),
        (1000, 2000, "1,000-2,000 sqft"),
        (2000, 3000, "2,000-3,000 sqft"),
        (3000, 5000, "3,000-5,000 sqft"),
        (5000, 10000, "5,000-10,000 sqft"),
        (10000, 20000, "10,000-20,000 sqft"),
        (20000, 50000, "20,000-50,000 sqft"),
        (50000, float('inf'), "50,000+ sqft")
    ]

    print("Building Size Distribution:")
    print()
    print(f"{'Size Range':<25} {'Count':<12} {'Percentage':<12} {'Avg Value'}")
    print("-" * 80)

    for low, high, label in size_ranges:
        in_range = [p for p in building_data if low <= p['total_living_area'] < high]
        count = len(in_range)
        pct = count / len(building_data) * 100 if building_data else 0
        avg_value = sum(p.get('just_value', 0) or 0 for p in in_range) / count if count > 0 else 0

        print(f"{label:<25} {count:<12,} {pct:<11.1f}% ${avg_value:<,.0f}")

    # Analyze by county
    print("\n\nBuildings by County (Top 10):")
    print()

    county_stats = defaultdict(lambda: {"count": 0, "avg_size": 0, "total_size": 0})
    for prop in building_data:
        county = prop.get('county', 'UNKNOWN')
        size = prop.get('total_living_area', 0)
        county_stats[county]["count"] += 1
        county_stats[county]["total_size"] += size

    for county, stats in county_stats.items():
        stats["avg_size"] = stats["total_size"] / stats["count"] if stats["count"] > 0 else 0

    sorted_counties = sorted(county_stats.items(), key=lambda x: x[1]["count"], reverse=True)[:10]

    print(f"{'County':<20} {'Count':<12} {'Avg Size'}")
    print("-" * 60)
    for county, stats in sorted_counties:
        print(f"{county:<20} {stats['count']:<12,} {stats['avg_size']:<,.0f} sqft")

    print()

except Exception as e:
    print(f"ERROR in Phase 5: {e}")
    print()

# ============================================================================
# PHASE 6: GENERATE RECOMMENDATIONS
# ============================================================================
print("=" * 100)
print("PHASE 6: AI-GENERATED RECOMMENDATIONS")
print("-" * 100)

print("\n🤖 CRITICAL RECOMMENDATIONS:\n")

# Prioritize recommendations
critical = [r for r in audit_results["recommendations"] if r["severity"] == "HIGH"]
medium = [r for r in audit_results["recommendations"] if r["severity"] == "MEDIUM"]

if critical:
    print("HIGH PRIORITY:")
    for i, rec in enumerate(critical, 1):
        print(f"\n  {i}. [{rec['type']}] {rec['table'] if 'table' in rec else 'N/A'}")
        print(f"     {rec['message']}")

if medium:
    print("\n\nMEDIUM PRIORITY:")
    for i, rec in enumerate(medium, 1):
        print(f"\n  {i}. [{rec['type']}] {rec.get('table', 'N/A')}")
        print(f"     {rec['message']}")

# ============================================================================
# PHASE 7: SAVE AUDIT RESULTS
# ============================================================================
print("\n" + "=" * 100)
print("PHASE 7: SAVING AUDIT RESULTS")
print("-" * 100)

output_file = f"supabase_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(audit_results, f, indent=2, default=str)

print(f"\n✅ Audit results saved to: {output_file}")
print()

print("=" * 100)
print(" " * 35 + "AUDIT COMPLETE")
print("=" * 100)
print()

print("SUMMARY:")
print(f"  - Tables Found: {len([t for t in audit_results['tables'].values() if t.get('exists', False)])}")
print(f"  - Missing Tables: {len([t for t in audit_results['tables'].values() if not t.get('exists', True)])}")
print(f"  - Critical Issues: {len(critical)}")
print(f"  - Recommendations: {len(audit_results['recommendations'])}")
print()
print("=" * 100)