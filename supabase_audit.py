import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('.env.mcp')

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not service_key:
    print("ERROR: Missing Supabase credentials in .env.mcp")
    exit(1)

supabase: Client = create_client(url, service_key)

def format_number(n):
    """Format number with commas"""
    return f"{n:,}"

def get_table_count(table_name, county_filter=None):
    """Get count of records in a table with optional county filter"""
    try:
        query = supabase.table(table_name).select("*", count='exact')
        if county_filter:
            query = query.eq('county', county_filter)

        # Execute with count only (no data)
        result = query.limit(0).execute()
        return result.count if hasattr(result, 'count') else 0
    except Exception as e:
        print(f"  Warning: Error counting {table_name}: {str(e)}")
        return 0

def get_table_sample(table_name, limit=1):
    """Get sample records from a table"""
    try:
        result = supabase.table(table_name).select("*").limit(limit).execute()
        return result.data if result.data else []
    except Exception as e:
        return []

def get_distinct_counties(table_name):
    """Get distinct counties from a table"""
    try:
        # Get a larger sample to find unique counties
        result = supabase.table(table_name).select("county").limit(1000).execute()
        if result.data:
            counties = set(row['county'] for row in result.data if row.get('county'))
            return sorted(list(counties))
        return []
    except Exception as e:
        return []

def analyze_florida_parcels():
    """Detailed analysis of florida_parcels table"""
    print("\n[FLORIDA_PARCELS TABLE ANALYSIS]")
    print("="*60)

    # Get total count
    total = get_table_count('florida_parcels')
    print(f"Total Records: {format_number(total)}")

    # Get counties
    counties = get_distinct_counties('florida_parcels')
    print(f"Counties Found: {len(counties)}")

    if counties[:10]:  # Show first 10 counties
        print(f"Sample Counties: {', '.join(counties[:10])}...")

    # Count by major counties
    major_counties = ['BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH']
    print("\nMajor County Breakdown:")
    county_totals = 0
    for county in major_counties:
        count = get_table_count('florida_parcels', county)
        county_totals += count
        if count > 0:
            print(f"  - {county}: {format_number(count)} properties")

    # Get sample record to show structure
    sample = get_table_sample('florida_parcels', 1)
    if sample:
        print(f"\nTable Structure (columns): {len(sample[0].keys())}")
        print(f"Key Fields: {', '.join(list(sample[0].keys())[:10])}...")

    return total, counties

def analyze_properties_table():
    """Analyze the properties table"""
    print("\n[PROPERTIES TABLE ANALYSIS]")
    print("="*60)

    total = get_table_count('properties')
    print(f"Total Records: {format_number(total)}")

    # Get sample to understand structure
    sample = get_table_sample('properties', 1)
    if sample:
        print(f"Table Structure (columns): {len(sample[0].keys())}")
        print(f"Key Fields: {', '.join(list(sample[0].keys())[:10])}...")

    return total

def analyze_other_tables():
    """Check for other property-related tables"""
    print("\n[OTHER PROPERTY-RELATED TABLES]")
    print("="*60)

    # Common property-related table names to check
    tables_to_check = [
        'property_sales',
        'sales_history',
        'tax_deeds',
        'property_tax',
        'property_characteristics',
        'property_values',
        'florida_sales',
        'florida_nav',
        'florida_nap',
        'florida_nal',
        'parcels',
        'User',
        'properties_contacts',
        'properties_notes'
    ]

    found_tables = {}

    for table in tables_to_check:
        count = get_table_count(table)
        if count > 0:
            found_tables[table] = count
            print(f"  - {table}: {format_number(count)} records")

    return found_tables

def generate_audit_report():
    """Generate comprehensive audit report"""
    print("\n" + "="*60)
    print("SUPABASE DATABASE AUDIT REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Analyze florida_parcels
    parcels_total, counties = analyze_florida_parcels()

    # Analyze properties table
    properties_total = analyze_properties_table()

    # Analyze other tables
    other_tables = analyze_other_tables()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print("\nTOTAL PROPERTY RECORDS:")
    print(f"  - florida_parcels: {format_number(parcels_total)}")
    print(f"  - properties: {format_number(properties_total)}")

    if 'property_sales' in other_tables:
        print(f"  - property_sales: {format_number(other_tables['property_sales'])}")
    if 'sales_history' in other_tables:
        print(f"  - sales_history: {format_number(other_tables['sales_history'])}")

    # Calculate unique properties estimate
    print(f"\nESTIMATED UNIQUE PROPERTIES:")
    print(f"  Primary Source (florida_parcels): {format_number(parcels_total)}")

    print(f"\nGEOGRAPHIC COVERAGE:")
    print(f"  Counties in Database: {len(counties)}")
    print(f"  Florida Total Counties: 67")
    print(f"  Coverage: {len(counties)/67*100:.1f}%")

    # Data completeness check
    print("\nDATA COMPLETENESS:")
    if parcels_total > 9000000:
        print("  - Excellent: >9M properties (approaching FL total of ~9.7M)")
    elif parcels_total > 5000000:
        print("  - Good: >5M properties")
    elif parcels_total > 1000000:
        print("  - Moderate: >1M properties")
    else:
        print("  - Limited: <1M properties")

    # Export summary to JSON
    summary = {
        "audit_timestamp": datetime.now().isoformat(),
        "florida_parcels": {
            "total": parcels_total,
            "counties_count": len(counties),
            "counties_list": counties[:20]  # First 20 counties
        },
        "properties_table": {
            "total": properties_total
        },
        "other_tables": other_tables,
        "summary": {
            "primary_property_count": parcels_total,
            "geographic_coverage_percent": round(len(counties)/67*100, 2)
        }
    }

    with open('supabase_audit_results.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print("\nDetailed results saved to: supabase_audit_results.json")

    return summary

if __name__ == "__main__":
    print("Starting Supabase Database Audit...")
    print("Connecting to Supabase...")

    try:
        summary = generate_audit_report()
        print("\nAudit Complete!")
    except Exception as e:
        print(f"\nAudit failed: {str(e)}")
        import traceback
        traceback.print_exc()