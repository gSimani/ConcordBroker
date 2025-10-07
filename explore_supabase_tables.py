import os
import json
from supabase import create_client, Client
from datetime import datetime

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def explore_database():
    print("=" * 80)
    print("SUPABASE DATABASE EXPLORATION - CONCORDBROKER")
    print("=" * 80)
    print(f"Database URL: {SUPABASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 80)

    # List of known tables to check
    tables_to_check = [
        'florida_parcels',
        'florida_sales',
        'florida_nav',
        'florida_tpp',
        'florida_nap',
        'florida_nal',
        'florida_sdf',
        'properties',
        'property_characteristics',
        'property_assessments',
        'property_values',
        'sales_history',
        'tax_certificates',
        'tax_deeds',
        'foreclosures',
        'permits',
        'User',
        'property_notes',
        'property_watchlist',
        'property_contacts',
        'property_analysis',
        'investment_opportunities',
        'dor_use_codes',
        'dor_use_code_descriptions',
        'dor_use_code_mappings',
        'county_data',
        'zip_codes',
        'cdd_districts',
        'hoa_associations',
        'rental_analysis',
        'comp_sales',
        'market_trends',
        'mortgage_data',
        'lien_data',
        'code_violations',
        'environmental_data',
        'flood_zones',
        'schools',
        'demographics'
    ]

    existing_tables = []
    table_details = {}

    print("\n[CHECKING TABLES]:")
    print("-" * 80)

    for table_name in tables_to_check:
        try:
            # Try to query the table (limit 1 to just check if it exists)
            response = supabase.table(table_name).select("*").limit(1).execute()

            # If we get here, the table exists
            existing_tables.append(table_name)

            # Get count (approximation)
            count_response = supabase.table(table_name).select("*", count='exact').limit(0).execute()
            record_count = count_response.count if hasattr(count_response, 'count') else 'Unknown'

            # Get sample record to understand structure
            sample_data = response.data[0] if response.data else {}
            columns = list(sample_data.keys()) if sample_data else []

            table_details[table_name] = {
                'exists': True,
                'record_count': record_count,
                'columns': columns,
                'sample_columns': columns[:10] if len(columns) > 10 else columns
            }

            print(f"[OK] {table_name:<30} | Records: {record_count:<10} | Columns: {len(columns)}")

        except Exception as e:
            # Table doesn't exist or we don't have access
            if "relation" not in str(e).lower() or "does not exist" not in str(e).lower():
                # Only note if it's not just a missing table
                print(f"[X] {table_name:<30} | Error: {str(e)[:50]}")

    print("\n" + "=" * 80)
    print(f"[SUMMARY]: Found {len(existing_tables)} tables")
    print("=" * 80)

    # Detailed view of main tables
    print("\n[DETAILED TABLE INFORMATION]:")
    print("-" * 80)

    for table in existing_tables:
        details = table_details.get(table, {})
        print(f"\n[TABLE]: {table}")
        print(f"   Records: {details.get('record_count', 'Unknown')}")
        print(f"   Column Count: {len(details.get('columns', []))}")
        if details.get('sample_columns'):
            print(f"   Sample Columns: {', '.join(details['sample_columns'][:8])}")

    # Focus on the main property table
    print("\n" + "=" * 80)
    print("[MAIN PROPERTY TABLE ANALYSIS]: florida_parcels")
    print("=" * 80)

    if 'florida_parcels' in existing_tables:
        try:
            # Get more detailed info about florida_parcels
            sample_properties = supabase.table('florida_parcels').select("*").limit(5).execute()

            if sample_properties.data:
                first_property = sample_properties.data[0]

                print("\n[Column Structure]:")
                print("-" * 40)
                for i, (key, value) in enumerate(first_property.items(), 1):
                    value_type = type(value).__name__
                    value_preview = str(value)[:50] if value else 'NULL'
                    print(f"{i:3}. {key:<30} | Type: {value_type:<10} | Sample: {value_preview}")

                # Check for specific important columns
                important_columns = [
                    'parcel_id', 'county', 'phy_addr1', 'phy_city', 'phy_zipcd',
                    'owner_name', 'just_value', 'assessed_value', 'taxable_value',
                    'property_use', 'year_built', 'living_area', 'land_sqft'
                ]

                print("\n[Key Property Fields Present]:")
                print("-" * 40)
                for col in important_columns:
                    if col in first_property:
                        print(f"  [YES] {col}")
                    else:
                        # Check for variations
                        variations = [c for c in first_property.keys() if col.replace('_', '') in c.replace('_', '').lower()]
                        if variations:
                            print(f"  [WARN] {col} -> Found as: {variations[0]}")
                        else:
                            print(f"  [NO] {col} (not found)")

        except Exception as e:
            print(f"Error analyzing florida_parcels: {e}")

    # Check for sales data
    print("\n" + "=" * 80)
    print("[SALES DATA TABLES]")
    print("=" * 80)

    sales_tables = [t for t in existing_tables if 'sale' in t.lower() or 'sdf' in t.lower()]
    if sales_tables:
        for table in sales_tables:
            details = table_details.get(table, {})
            print(f"  - {table}: {details.get('record_count', 'Unknown')} records")
    else:
        print("  No sales tables found")

    # Check for tax-related tables
    print("\n" + "=" * 80)
    print("[TAX & ASSESSMENT TABLES]")
    print("=" * 80)

    tax_tables = [t for t in existing_tables if any(x in t.lower() for x in ['tax', 'assess', 'nav', 'tpp'])]
    if tax_tables:
        for table in tax_tables:
            details = table_details.get(table, {})
            print(f"  - {table}: {details.get('record_count', 'Unknown')} records")
    else:
        print("  No tax/assessment tables found")

    # Export findings to JSON
    output = {
        'database_url': SUPABASE_URL,
        'scan_timestamp': datetime.now().isoformat(),
        'total_tables_found': len(existing_tables),
        'existing_tables': existing_tables,
        'table_details': table_details
    }

    with open('supabase_tables_report.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print("\n" + "=" * 80)
    print("[COMPLETE] Report saved to: supabase_tables_report.json")
    print("=" * 80)

if __name__ == "__main__":
    explore_database()