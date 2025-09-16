#!/usr/bin/env python3
"""
Analyze Supabase database structure for ConcordBroker
Extract table names, record counts, and basic schema information
"""

import json
import requests
import time
from urllib.parse import quote

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def get_schema_info():
    """Get OpenAPI schema to extract table names"""
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
        if response.status_code == 200:
            schema = response.json()
            # Extract table names from paths
            table_names = []
            for path in schema.get('paths', {}):
                if path.startswith('/') and path != '/':
                    table_name = path[1:]  # Remove leading slash
                    if not table_name.startswith('rpc/'):  # Skip RPC functions
                        table_names.append(table_name)
            return sorted(list(set(table_names)))
        else:
            print(f"Error getting schema: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting schema: {e}")
        return []

def get_table_count(table_name):
    """Get record count for a table"""
    try:
        # Use HEAD request with Prefer: count=exact to get total count
        response = requests.head(
            f"{SUPABASE_URL}/rest/v1/{quote(table_name)}",
            headers={**headers, "Prefer": "count=exact"}
        )
        if response.status_code == 200:
            content_range = response.headers.get('Content-Range', '')
            if content_range:
                # Parse "0-9/1000" format
                parts = content_range.split('/')
                if len(parts) == 2:
                    return int(parts[1])
        return 0
    except Exception as e:
        print(f"Error getting count for {table_name}: {e}")
        return 0

def get_sample_record(table_name, limit=1):
    """Get a sample record to understand structure"""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{quote(table_name)}",
            headers=headers,
            params={"limit": limit}
        )
        if response.status_code == 200:
            data = response.json()
            return data[0] if data else {}
        return {}
    except Exception as e:
        print(f"Error getting sample for {table_name}: {e}")
        return {}

def categorize_table(table_name, sample_record):
    """Categorize table by name and structure"""
    name_lower = table_name.lower()
    columns = list(sample_record.keys()) if sample_record else []

    # Property appraiser related
    if any(keyword in name_lower for keyword in ['florida_parcels', 'nav_', 'nal_', 'nap_', 'sdf_']):
        return "Property Appraiser"

    # Tax deed related
    if any(keyword in name_lower for keyword in ['tax_deed', 'auction']):
        return "Tax Deed"

    # Business/entity related
    if any(keyword in name_lower for keyword in ['sunbiz', 'entity', 'business', 'corporation']):
        return "Business Entity"

    # Property related
    if any(keyword in name_lower for keyword in ['property', 'parcel']):
        return "Property"

    # Geographic/spatial
    if any(keyword in name_lower for keyword in ['spatial', 'geography']):
        return "Geographic"

    # Check for county column
    if any('county' in col.lower() for col in columns):
        return "County Data"

    return "Other"

def analyze_database():
    """Main analysis function"""
    print("Analyzing ConcordBroker Supabase Database Structure")
    print("=" * 60)

    # Get all table names
    print("Extracting table names...")
    table_names = get_schema_info()

    if not table_names:
        print("Could not extract table names")
        return

    print(f"Found {len(table_names)} tables")
    print()

    # Analyze each table
    table_analysis = []

    for i, table_name in enumerate(table_names, 1):
        print(f"Analyzing table {i}/{len(table_names)}: {table_name}")

        # Get record count
        count = get_table_count(table_name)

        # Get sample record for structure analysis
        sample = get_sample_record(table_name)

        # Categorize table
        category = categorize_table(table_name, sample)

        # Check for county data
        has_county = any('county' in col.lower() for col in sample.keys()) if sample else False

        table_info = {
            'name': table_name,
            'record_count': count,
            'category': category,
            'has_county_data': has_county,
            'columns': list(sample.keys()) if sample else [],
            'column_count': len(sample.keys()) if sample else 0
        }

        table_analysis.append(table_info)

        # Add small delay to avoid rate limiting
        time.sleep(0.1)

    # Generate report
    print("\n" + "="*60)
    print("DATABASE ANALYSIS REPORT")
    print("="*60)

    # Summary by category
    categories = {}
    total_records = 0
    county_tables = []

    for table in table_analysis:
        category = table['category']
        if category not in categories:
            categories[category] = {'count': 0, 'records': 0, 'tables': []}

        categories[category]['count'] += 1
        categories[category]['records'] += table['record_count']
        categories[category]['tables'].append(table)

        total_records += table['record_count']

        if table['has_county_data']:
            county_tables.append(table['name'])

    print(f"\nTOTAL TABLES: {len(table_analysis)}")
    print(f"TOTAL RECORDS: {total_records:,}")
    print(f"COUNTY TABLES: {len(county_tables)}")

    print("\nTABLES BY CATEGORY:")
    for category, info in sorted(categories.items()):
        print(f"\n  {category}:")
        print(f"    Tables: {info['count']}")
        print(f"    Records: {info['records']:,}")
        for table in sorted(info['tables'], key=lambda x: x['record_count'], reverse=True):
            print(f"      - {table['name']}: {table['record_count']:,} records ({table['column_count']} columns)")

    print(f"\nTABLES WITH COUNTY DATA:")
    for table_name in sorted(county_tables):
        table_info = next(t for t in table_analysis if t['name'] == table_name)
        print(f"    - {table_name}: {table_info['record_count']:,} records")

    # Detailed table list
    print(f"\nDETAILED TABLE ANALYSIS:")
    print("-" * 60)

    for table in sorted(table_analysis, key=lambda x: x['record_count'], reverse=True):
        print(f"\nTable: {table['name']}")
        print(f"  Category: {table['category']}")
        print(f"  Records: {table['record_count']:,}")
        print(f"  Columns: {table['column_count']}")
        print(f"  Has County Data: {table['has_county_data']}")

        if table['columns']:
            # Show first few columns as sample
            sample_cols = table['columns'][:8]
            if len(table['columns']) > 8:
                sample_cols.append('...')
            print(f"  Sample Columns: {', '.join(sample_cols)}")

    # Save detailed analysis to file
    with open('supabase_database_analysis.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tables': len(table_analysis),
                'total_records': total_records,
                'categories': categories,
                'county_tables': county_tables
            },
            'tables': table_analysis
        }, f, indent=2)

    print(f"\nDetailed analysis saved to: supabase_database_analysis.json")
    print("\nAnalysis complete!")

if __name__ == "__main__":
    analyze_database()