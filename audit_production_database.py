"""
Comprehensive Supabase Production Database Audit
Analyzes structure, performance, data quality, and optimization opportunities
"""

import os
from supabase import create_client
from datetime import datetime
import json

# Load environment variables
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

client = create_client(SUPABASE_URL, SUPABASE_KEY)

KNOWN_TABLES = [
    'florida_parcels',
    'property_sales_history',
    'florida_entities',
    'sunbiz_corporate',
    'tax_certificates',
    'dor_use_codes'
]

def print_section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80 + "\n")

def audit_table_structure(table_name):
    """Audit table structure and data quality"""
    print(f"[TABLE] Analyzing: {table_name}")

    try:
        # Get row count
        response = client.table(table_name).select("*", count="exact").limit(0).execute()
        count = response.count

        # Get sample data
        sample_response = client.table(table_name).select("*").limit(100).execute()
        sample_data = sample_response.data

        if count == 0:
            print(f"    Table is EMPTY (0 rows)")
            return {
                'exists': True,
                'count': 0,
                'columns': [],
                'issues': ['Table is empty']
            }

        print(f"   Row Count: {count:,}")

        if sample_data and len(sample_data) > 0:
            columns = list(sample_data[0].keys())
            print(f"   Columns: {len(columns)}")

            # Analyze null percentages
            null_counts = {col: 0 for col in columns}
            for row in sample_data:
                for col in columns:
                    if row.get(col) is None or row.get(col) == '':
                        null_counts[col] += 1

            # Report high null columns
            high_null_cols = []
            for col, null_count in null_counts.items():
                null_pct = (null_count / len(sample_data)) * 100
                if null_pct > 50:
                    high_null_cols.append(f"{col} ({null_pct:.1f}% null)")

            if high_null_cols:
                print(f"    High Null Columns: {', '.join(high_null_cols[:5])}")

            return {
                'exists': True,
                'count': count,
                'columns': columns,
                'sample': sample_data[0],
                'null_counts': null_counts,
                'issues': high_null_cols
            }

        return {'exists': True, 'count': count, 'columns': [], 'issues': []}

    except Exception as e:
        print(f"   Error: {str(e)}")
        return {'exists': False, 'error': str(e), 'issues': [str(e)]}

def audit_florida_parcels():
    """Deep audit of florida_parcels table"""
    print_section("  FLORIDA PARCELS DEEP ANALYSIS")

    try:
        # Check critical fields
        response = client.table('florida_parcels').select(
            'parcel_id,county,year,owner_name,just_value,phy_addr1,property_use,dor_uc'
        ).limit(1000).execute()

        if not response.data:
            print("    No data available for analysis")
            return

        data = response.data
        total = len(data)

        # Count missing fields
        missing_stats = {
            'parcel_id': sum(1 for r in data if not r.get('parcel_id')),
            'county': sum(1 for r in data if not r.get('county')),
            'year': sum(1 for r in data if not r.get('year')),
            'owner_name': sum(1 for r in data if not r.get('owner_name')),
            'just_value': sum(1 for r in data if not r.get('just_value') or r.get('just_value') == 0),
            'phy_addr1': sum(1 for r in data if not r.get('phy_addr1')),
            'property_use': sum(1 for r in data if not r.get('property_use')),
            'dor_uc': sum(1 for r in data if not r.get('dor_uc'))
        }

        print("Critical Field Completeness (sample of 1000):")
        for field, missing in missing_stats.items():
            completeness = ((total - missing) / total) * 100
            status = "" if completeness > 90 else "" if completeness > 50 else ""
            print(f"  {status} {field}: {completeness:.1f}% complete ({missing} missing)")

        # Check value ranges
        values = [r.get('just_value', 0) for r in data if r.get('just_value')]
        if values:
            print(f"\nValue Statistics:")
            print(f"  Min: ${min(values):,.0f}")
            print(f"  Max: ${max(values):,.0f}")
            print(f"  Avg: ${sum(values)/len(values):,.0f}")

        # Check counties
        counties = {}
        for r in data:
            county = r.get('county', 'Unknown')
            counties[county] = counties.get(county, 0) + 1

        print(f"\nCounties in sample:")
        for county, count in sorted(counties.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {county}: {count}")

    except Exception as e:
        print(f"   Error: {str(e)}")

def audit_sales_history():
    """Deep audit of property_sales_history table"""
    print_section("° PROPERTY SALES HISTORY ANALYSIS")

    try:
        response = client.table('property_sales_history').select(
            'parcel_id,sale_price,sale_date,quality_code,or_book,or_page'
        ).limit(1000).execute()

        if not response.data:
            print("    No data available for analysis")
            return

        data = response.data
        total = len(data)

        # Price analysis
        prices = [r.get('sale_price', 0) for r in data if r.get('sale_price')]
        if prices:
            # Prices are stored in cents
            prices_dollars = [p / 100 for p in prices]
            print(f"Sale Price Statistics ({len(prices)} sales):")
            print(f"  Min: ${min(prices_dollars):,.2f}")
            print(f"  Max: ${max(prices_dollars):,.2f}")
            print(f"  Avg: ${sum(prices_dollars)/len(prices_dollars):,.2f}")
            print(f"  Median: ${sorted(prices_dollars)[len(prices_dollars)//2]:,.2f}")

        # Quality code distribution
        quality_codes = {}
        for r in data:
            code = r.get('quality_code', 'Unknown')
            quality_codes[code] = quality_codes.get(code, 0) + 1

        print(f"\nQuality Code Distribution:")
        for code, count in sorted(quality_codes.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total) * 100
            print(f"  {code}: {count} ({pct:.1f}%)")

        # Date range
        dates = [r.get('sale_date') for r in data if r.get('sale_date')]
        if dates:
            dates.sort()
            print(f"\nDate Range:")
            print(f"  Earliest: {dates[0]}")
            print(f"  Latest: {dates[-1]}")

    except Exception as e:
        print(f"   Error: {str(e)}")

def audit_relationships():
    """Check foreign key relationships and data integrity"""
    print_section("— RELATIONSHIP & INTEGRITY ANALYSIS")

    try:
        # Check for orphaned sales records
        print("Checking sales-to-parcels relationship...")
        sales_response = client.table('property_sales_history').select('parcel_id').limit(50).execute()

        if sales_response.data:
            orphaned = 0
            checked = 0
            for sale in sales_response.data[:20]:
                parcel_id = sale.get('parcel_id')
                if parcel_id:
                    parcel_response = client.table('florida_parcels').select('parcel_id').eq('parcel_id', parcel_id).limit(1).execute()
                    if not parcel_response.data:
                        orphaned += 1
                    checked += 1

            if orphaned > 0:
                print(f"    Found {orphaned}/{checked} orphaned sales records")
            else:
                print(f"   All {checked} sampled sales have matching parcels")

        # Check for duplicate parcels
        print("\nChecking for duplicate parcel_ids...")
        # This would require a more complex query
        print("    Requires direct SQL query for efficiency")

    except Exception as e:
        print(f"   Error: {str(e)}")

def main():
    print_section(" COMPREHENSIVE SUPABASE DATABASE AUDIT")
    print(f"Database: {SUPABASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    # Phase 1: Table structure analysis
    print_section("Š PHASE 1: TABLE STRUCTURE ANALYSIS")

    results = {}
    for table in KNOWN_TABLES:
        results[table] = audit_table_structure(table)
        print()

    # Phase 2: Deep analysis of main tables
    audit_florida_parcels()
    audit_sales_history()

    # Phase 3: Relationship analysis
    audit_relationships()

    # Phase 4: Summary and recommendations
    print_section("‹ AUDIT SUMMARY & RECOMMENDATIONS")

    total_rows = sum(r.get('count', 0) for r in results.values())
    existing_tables = sum(1 for r in results.values() if r.get('exists'))

    print(f"Š Tables Found: {existing_tables}/{len(KNOWN_TABLES)}")
    print(f"Š Total Records: {total_rows:,}")

    # Critical issues
    print("\n¨ CRITICAL ISSUES:\n")

    empty_tables = [name for name, r in results.items() if r.get('count', 0) == 0]
    if empty_tables:
        print(f"   Empty tables: {', '.join(empty_tables)}")

    # Recommendations
    print("\n¡ PERFORMANCE RECOMMENDATIONS:\n")
    print("  1.  Add composite index: CREATE INDEX idx_parcels_county_year ON florida_parcels(county, year);")
    print("  2.  Add index: CREATE INDEX idx_parcels_value ON florida_parcels(just_value) WHERE just_value > 0;")
    print("  3.  Add index: CREATE INDEX idx_sales_date ON property_sales_history(sale_date);")
    print("  4.  Add index: CREATE INDEX idx_sales_parcel ON property_sales_history(parcel_id);")
    print("  5.  Add full-text search: CREATE INDEX idx_parcels_owner_fts ON florida_parcels USING gin(to_tsvector('english', owner_name));")
    print("  6.  Enable RLS: ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;")
    print("  7.  Partition by county: Consider table partitioning for tables > 10M rows")
    print("  8.  Add CHECK constraint: ALTER TABLE property_sales_history ADD CHECK (sale_price >= 0);")

    print("\n§ DATA QUALITY RECOMMENDATIONS:\n")
    print("  1.   Standardize county names (uppercase)")
    print("  2.   Validate parcel_id format (non-empty, reasonable length)")
    print("  3.   Set default year to current year where NULL")
    print("  4.   Normalize property_use codes with dor_use_codes table")
    print("  5.   Add foreign key: ALTER TABLE property_sales_history ADD FOREIGN KEY (parcel_id) REFERENCES florida_parcels(parcel_id);")

    print("\n" + "="*80)
    print("Audit Complete!")
    print("="*80)

if __name__ == "__main__":
    main()
