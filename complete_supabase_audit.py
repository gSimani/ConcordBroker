"""
Complete Supabase Database Audit - Using the CORRECT Database
"""
import os
import json
from datetime import datetime
from supabase import create_client, Client
import time

# CORRECT Supabase credentials (from property_live_api.py)
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

print("="*70)
print("COMPLETE SUPABASE DATABASE AUDIT")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
print()

print("Connecting to CORRECT Supabase database...")
print(f"URL: {SUPABASE_URL}")
print(f"Project ID: pmispwtdngkcmsrsjwbp")
print()

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def format_number(n):
    """Format number with commas"""
    return f"{n:,}" if n else "0"

def get_table_count(table_name, filters=None):
    """Get count of records in a table"""
    try:
        query = supabase.table(table_name).select("*", count='exact')

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        result = query.limit(0).execute()
        return result.count if hasattr(result, 'count') else 0
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg:
            return None
        print(f"  Error counting {table_name}: {error_msg}")
        return 0

def get_sample_record(table_name):
    """Get a sample record from a table"""
    try:
        result = supabase.table(table_name).select("*").limit(1).execute()
        return result.data[0] if result.data else None
    except:
        return None

def get_distinct_values(table_name, column, limit=10):
    """Get distinct values from a column"""
    try:
        result = supabase.table(table_name).select(column).limit(1000).execute()
        if result.data:
            values = set(row.get(column) for row in result.data if row.get(column))
            return sorted(list(values))[:limit]
        return []
    except:
        return []

# Main audit
print("[1] CHECKING FOR PROPERTY TABLES")
print("-"*50)

# List of common property table names to check
table_names = [
    'Properties',
    'properties',
    'Property',
    'property',
    'florida_parcels',
    'florida_properties',
    'parcels',
    'property_data',
    'real_estate',
    'listings',
    'property_sales',
    'sales_history',
    'tax_deeds',
    'property_tax',
    'User',
    'users',
    'contacts',
    'notes',
    'watchlist'
]

found_tables = []
total_properties = 0

for table in table_names:
    count = get_table_count(table)
    if count is not None and count >= 0:
        found_tables.append((table, count))
        print(f"  FOUND: {table} - {format_number(count)} records")

        # Get sample for property tables
        if count > 0 and 'propert' in table.lower():
            sample = get_sample_record(table)
            if sample:
                columns = list(sample.keys())[:10]
                print(f"    Sample columns: {', '.join(columns)}")
                total_properties = max(total_properties, count)

print()
print("[2] DETAILED ANALYSIS OF LARGEST TABLE")
print("-"*50)

if found_tables:
    # Sort by count and get largest
    found_tables.sort(key=lambda x: x[1], reverse=True)
    largest_table, largest_count = found_tables[0]

    print(f"Analyzing '{largest_table}' table ({format_number(largest_count)} records)")

    # Get sample record
    sample = get_sample_record(largest_table)
    if sample:
        print()
        print("Table Structure:")
        print(f"  Total Columns: {len(sample.keys())}")
        print()
        print("Column Names:")
        for i, col in enumerate(sample.keys(), 1):
            print(f"  {i:2}. {col}")

        # Check for location-based columns
        location_cols = [col for col in sample.keys() if any(x in col.lower() for x in ['county', 'city', 'state', 'address', 'location', 'zip'])]
        if location_cols:
            print()
            print("Geographic Columns Found:")
            for col in location_cols:
                values = get_distinct_values(largest_table, col, 5)
                if values:
                    print(f"  - {col}: {', '.join(str(v) for v in values[:5])}")

        # Check for value columns
        value_cols = [col for col in sample.keys() if any(x in col.lower() for x in ['value', 'price', 'amount', 'assessment', 'sale'])]
        if value_cols:
            print()
            print("Value/Price Columns Found:")
            for col in value_cols:
                print(f"  - {col}")
else:
    print("No property tables found in this database.")

print()
print("[3] GEOGRAPHIC COVERAGE ANALYSIS")
print("-"*50)

# Try to find county data
county_data_found = False
for table_name, count in found_tables:
    if count > 0:
        sample = get_sample_record(table_name)
        if sample and 'county' in [col.lower() for col in sample.keys()]:
            county_col = next(col for col in sample.keys() if col.lower() == 'county')
            counties = get_distinct_values(table_name, county_col, 100)
            if counties:
                county_data_found = True
                print(f"Counties found in '{table_name}' table:")
                print(f"  Total unique counties: {len(counties)}")
                print(f"  Sample counties: {', '.join(counties[:10])}")

                # Check specific Florida counties
                florida_counties = ['BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH']
                print()
                print("Major Florida Counties:")
                for county in florida_counties:
                    county_count = get_table_count(table_name, {county_col: county})
                    if county_count and county_count > 0:
                        print(f"  - {county}: {format_number(county_count)} properties")
                break

if not county_data_found:
    print("No geographic (county) data found in available tables.")

print()
print("="*70)
print("AUDIT SUMMARY")
print("="*70)
print()
print(f"Database Project: pmispwtdngkcmsrsjwbp")
print(f"Total Tables Found: {len(found_tables)}")
print()

if found_tables:
    print("Tables Summary:")
    for table_name, count in found_tables[:10]:  # Show top 10 tables
        print(f"  - {table_name}: {format_number(count)} records")

    total_records = sum(count for _, count in found_tables)
    print()
    print(f"TOTAL RECORDS ACROSS ALL TABLES: {format_number(total_records)}")

    if total_properties > 0:
        print(f"ESTIMATED PROPERTY RECORDS: {format_number(total_properties)}")

        # Assessment based on count
        print()
        print("Data Assessment:")
        if total_properties > 5000000:
            print("  Status: EXCELLENT - Database contains millions of property records")
            print("  Coverage: Likely covers most of Florida's ~9.7M properties")
        elif total_properties > 1000000:
            print("  Status: GOOD - Database contains over 1M property records")
            print("  Coverage: Substantial Florida property coverage")
        elif total_properties > 100000:
            print("  Status: MODERATE - Database contains over 100K property records")
            print("  Coverage: Partial Florida property coverage")
        else:
            print("  Status: LIMITED - Database contains under 100K property records")
            print("  Coverage: Limited property data available")
else:
    print("Status: NO DATA FOUND")
    print("This database appears to be empty or uses different table naming.")

# Save detailed results
results = {
    "audit_timestamp": datetime.now().isoformat(),
    "database_url": SUPABASE_URL,
    "project_id": "pmispwtdngkcmsrsjwbp",
    "tables_found": [
        {"name": name, "record_count": count}
        for name, count in found_tables
    ],
    "total_tables": len(found_tables),
    "total_records": sum(count for _, count in found_tables) if found_tables else 0,
    "estimated_properties": total_properties
}

with open('complete_audit_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print("Detailed results saved to: complete_audit_results.json")
print("="*70)