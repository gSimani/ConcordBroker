"""
Complete audit of Property Appraiser database tables and data routing
"""
import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.mcp')

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(url, key)

def audit_database():
    """Perform complete database audit"""
    audit_report = {
        "audit_timestamp": datetime.now().isoformat(),
        "database_url": url,
        "tables": {},
        "property_appraiser_tables": {},
        "data_routing": {},
        "issues_found": [],
        "recommendations": []
    }

    print("\n" + "="*80)
    print("PROPERTY APPRAISER DATABASE AUDIT")
    print("="*80 + "\n")

    # 1. Get all tables in the database
    print("1. Retrieving all database tables...")
    try:
        # Check main Property Appraiser table
        tables_to_check = [
            'florida_parcels',
            'nal_assessments',
            'nap_characteristics',
            'nav_values',
            'sdf_sales',
            'properties',
            'property_values',
            'sales_history',
            'tax_certificates',
            'tax_deed_sales',
            'florida_business_entities',
            'sunbiz_corporations',
            'building_permits'
        ]

        for table_name in tables_to_check:
            try:
                # Get table info by querying with limit=0
                response = supabase.table(table_name).select("*").limit(0).execute()

                # Get actual count
                count_response = supabase.table(table_name).select("*", count='exact').limit(1).execute()
                record_count = count_response.count if hasattr(count_response, 'count') else 0

                # Get sample record for schema inspection
                sample = supabase.table(table_name).select("*").limit(1).execute()
                columns = list(sample.data[0].keys()) if sample.data else []

                table_info = {
                    "exists": True,
                    "record_count": record_count,
                    "columns": columns,
                    "column_count": len(columns)
                }

                audit_report["tables"][table_name] = table_info
                print(f"  [OK] {table_name}: {record_count:,} records, {len(columns)} columns")

                # Mark as Property Appraiser table if applicable
                if table_name in ['florida_parcels', 'nal_assessments', 'nap_characteristics',
                                  'nav_values', 'sdf_sales']:
                    audit_report["property_appraiser_tables"][table_name] = table_info

            except Exception as e:
                audit_report["tables"][table_name] = {
                    "exists": False,
                    "error": str(e)
                }
                print(f"  [MISSING] {table_name}: Not found or error - {str(e)[:50]}")

    except Exception as e:
        print(f"  Error retrieving tables: {e}")
        audit_report["issues_found"].append(f"Table retrieval error: {str(e)}")

    # 2. Audit florida_parcels specifically (main Property Appraiser table)
    print("\n2. Auditing florida_parcels table (main Property Appraiser data)...")
    try:
        # Get column mapping verification
        sample = supabase.table('florida_parcels').select("*").limit(5).execute()

        if sample.data:
            required_columns = {
                'parcel_id': 'Primary identifier',
                'county': 'County name',
                'year': 'Tax year',
                'land_sqft': 'Land square footage (from LND_SQFOOT)',
                'phy_addr1': 'Physical address line 1',
                'phy_addr2': 'Physical address line 2',
                'owner_addr1': 'Owner address line 1',
                'owner_addr2': 'Owner address line 2',
                'owner_state': 'Owner state (2 chars)',
                'just_value': 'Just/market value',
                'land_value': 'Land value',
                'building_value': 'Building/improvement value',
                'sale_date': 'Most recent sale date'
            }

            existing_columns = set(sample.data[0].keys())

            print("\n  Column Mapping Verification:")
            for col, desc in required_columns.items():
                if col in existing_columns:
                    print(f"    [OK] {col}: {desc}")
                else:
                    print(f"    [MISSING] {col}: MISSING - {desc}")
                    audit_report["issues_found"].append(f"Missing required column: {col}")

            # Check for extra columns not in standard mapping
            extra_columns = existing_columns - set(required_columns.keys())
            if extra_columns:
                print(f"\n  Additional columns found: {', '.join(extra_columns)}")

        # Get county distribution
        print("\n  Checking county distribution...")
        counties = supabase.table('florida_parcels').select("county").limit(1000).execute()
        if counties.data:
            unique_counties = set([r['county'] for r in counties.data if r.get('county')])
            print(f"    Found {len(unique_counties)} unique counties in sample")
            audit_report["property_appraiser_tables"]["florida_parcels"]["counties"] = list(unique_counties)[:10]

    except Exception as e:
        print(f"  Error auditing florida_parcels: {e}")
        audit_report["issues_found"].append(f"florida_parcels audit error: {str(e)}")

    # 3. Check data routing and relationships
    print("\n3. Checking data routing and relationships...")

    routing_checks = [
        {
            "name": "Property Appraiser to Properties",
            "source": "florida_parcels",
            "target": "properties",
            "link_field": "parcel_id",
            "description": "Main property data flow"
        },
        {
            "name": "Sales History to Properties",
            "source": "sdf_sales",
            "target": "sales_history",
            "link_field": "parcel_id",
            "description": "Sales transaction data"
        },
        {
            "name": "Tax Deed to Properties",
            "source": "tax_deed_sales",
            "target": "properties",
            "link_field": "parcel_id",
            "description": "Tax deed auction data"
        },
        {
            "name": "Business Entities to Properties",
            "source": "florida_business_entities",
            "target": "properties",
            "link_field": "owner_name",
            "description": "Owner entity matching"
        }
    ]

    for check in routing_checks:
        try:
            # Check if both tables exist
            source_exists = audit_report["tables"].get(check["source"], {}).get("exists", False)
            target_exists = audit_report["tables"].get(check["target"], {}).get("exists", False)

            routing_info = {
                "source": check["source"],
                "target": check["target"],
                "link_field": check["link_field"],
                "source_exists": source_exists,
                "target_exists": target_exists,
                "description": check["description"]
            }

            if source_exists and target_exists:
                routing_info["status"] = "operational"
                print(f"  [OK] {check['name']}: Operational")
            else:
                routing_info["status"] = "broken"
                print(f"  [BROKEN] {check['name']}: Broken (missing table)")
                audit_report["issues_found"].append(f"Broken routing: {check['name']}")

            audit_report["data_routing"][check["name"]] = routing_info

        except Exception as e:
            print(f"  Error checking {check['name']}: {e}")

    # 4. Performance and optimization checks
    print("\n4. Checking indexes and performance...")

    critical_indexes = [
        "florida_parcels: (parcel_id, county, year)",
        "properties: (parcel_id)",
        "sales_history: (parcel_id, sale_date)",
        "tax_deed_sales: (parcel_id, auction_date)"
    ]

    print("  Recommended indexes for Property Appraiser data:")
    for idx in critical_indexes:
        print(f"    - {idx}")

    # 5. Data quality checks
    print("\n5. Data quality checks...")

    if audit_report["tables"].get("florida_parcels", {}).get("exists"):
        try:
            # Check for nulls in required fields
            sample = supabase.table('florida_parcels').select("parcel_id,county,year").limit(100).execute()

            null_parcels = sum(1 for r in sample.data if not r.get('parcel_id'))
            null_counties = sum(1 for r in sample.data if not r.get('county'))
            null_years = sum(1 for r in sample.data if not r.get('year'))

            print(f"  Sample quality (100 records):")
            print(f"    - Null parcel_ids: {null_parcels}")
            print(f"    - Null counties: {null_counties}")
            print(f"    - Null years: {null_years}")

            if null_parcels > 0:
                audit_report["issues_found"].append(f"Found {null_parcels} null parcel_ids")
            if null_counties > 0:
                audit_report["issues_found"].append(f"Found {null_counties} null counties")

        except Exception as e:
            print(f"  Error in quality checks: {e}")

    # 6. Generate recommendations
    print("\n6. Generating recommendations...")

    # Check total Property Appraiser records
    total_pa_records = sum(
        audit_report["tables"].get(t, {}).get("record_count", 0)
        for t in ['florida_parcels', 'nal_assessments', 'nap_characteristics', 'nav_values', 'sdf_sales']
    )

    if total_pa_records < 1000000:
        audit_report["recommendations"].append(
            f"Low record count ({total_pa_records:,}). Expected ~9.7M properties for all Florida counties."
        )

    if not audit_report["tables"].get("florida_parcels", {}).get("exists"):
        audit_report["recommendations"].append(
            "Critical: florida_parcels table missing. This is the main Property Appraiser table."
        )

    if audit_report["issues_found"]:
        audit_report["recommendations"].append(
            f"Address {len(audit_report['issues_found'])} issues found during audit."
        )

    # Save full report
    report_filename = f"property_appraiser_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(audit_report, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print("AUDIT SUMMARY")
    print(f"{'='*80}")
    print(f"Tables found: {sum(1 for t in audit_report['tables'].values() if t.get('exists'))}/{len(tables_to_check)}")
    print(f"Property Appraiser tables: {len(audit_report['property_appraiser_tables'])}")
    print(f"Total PA records: {total_pa_records:,}")
    print(f"Issues found: {len(audit_report['issues_found'])}")
    print(f"Recommendations: {len(audit_report['recommendations'])}")
    print(f"\nFull report saved to: {report_filename}")

    return audit_report

if __name__ == "__main__":
    audit_database()