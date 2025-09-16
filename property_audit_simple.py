#!/usr/bin/env python3
"""
Property Appraiser Database Audit Script
Connects through MCP Server to audit Supabase database
"""

import json
import requests
from datetime import datetime
from collections import defaultdict

# MCP Server configuration
MCP_BASE_URL = "http://localhost:3001"
API_KEY = "concordbroker-mcp-key"

def make_request(endpoint, method="GET", data=None):
    """Make a request to MCP Server"""
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    url = f"{MCP_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            return None

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

def check_table(table_name):
    """Check if a table exists and get sample data"""
    print(f"\nChecking table: {table_name}")
    print("-" * 40)

    # Try to get data from the table
    result = make_request(f"/api/supabase/{table_name}?limit=5")

    if result and 'data' in result:
        data = result['data']
        if data and len(data) > 0:
            print(f"✓ Table exists with {len(data)} sample records")

            # Show columns from first record
            print("Columns found:")
            for key in data[0].keys():
                value_type = type(data[0][key]).__name__ if data[0][key] is not None else "null"
                print(f"  • {key}: {value_type}")

            return True
    elif result and isinstance(result, list):
        if len(result) > 0:
            print(f"✓ Table exists with {len(result)} sample records")

            # Show columns from first record
            print("Columns found:")
            for key in result[0].keys():
                value_type = type(result[0][key]).__name__ if result[0][key] is not None else "null"
                print(f"  • {key}: {value_type}")

            return True
        else:
            print(f"✓ Table exists but is empty")
            return True
    else:
        print(f"✗ Table not accessible or doesn't exist")
        return False

def analyze_florida_parcels():
    """Deep analysis of florida_parcels table"""
    print("\n" + "=" * 60)
    print("FLORIDA_PARCELS TABLE DEEP ANALYSIS")
    print("=" * 60)

    # Get sample data
    result = make_request("/api/supabase/florida_parcels?limit=100")

    if not result:
        print("Could not access florida_parcels table")
        return

    data = result if isinstance(result, list) else result.get('data', [])

    if not data:
        print("No data found in florida_parcels table")
        return

    print(f"Analyzing {len(data)} sample records...")

    # Column mapping verification (based on CLAUDE.md requirements)
    critical_columns = {
        'parcel_id': 'Primary identifier',
        'county': 'County name (should be uppercase)',
        'year': 'Tax year (should be 2025)',
        'land_sqft': 'From LND_SQFOOT',
        'phy_addr1': 'From PHY_ADDR1',
        'phy_addr2': 'From PHY_ADDR2',
        'owner_addr1': 'From OWN_ADDR1',
        'owner_addr2': 'From OWN_ADDR2',
        'owner_state': 'From OWN_STATE (2 chars)',
        'just_value': 'From JV',
        'land_value': 'Land assessed value',
        'building_value': 'Building assessed value',
        'sale_date': 'From SALE_YR1/SALE_MO1',
        'sale_price': 'Last sale price'
    }

    print("\n1. CRITICAL COLUMN MAPPING CHECK:")
    print("-" * 40)

    sample = data[0] if data else {}
    for col, description in critical_columns.items():
        if col in sample:
            value = sample[col]
            print(f"  ✓ {col}: Present ({description})")

            # Validate specific column rules
            if col == 'owner_state' and value and len(str(value)) > 2:
                print(f"    ⚠ WARNING: owner_state = '{value}' (should be 2 chars)")
            elif col == 'sale_date' and value == '':
                print(f"    ⚠ WARNING: sale_date is empty string (should be NULL)")
            elif col == 'county' and value and value != value.upper():
                print(f"    ⚠ WARNING: county = '{value}' (should be uppercase)")
        else:
            print(f"  ✗ {col}: MISSING! ({description})")

    # Analyze data distribution
    print("\n2. DATA DISTRIBUTION ANALYSIS:")
    print("-" * 40)

    counties = defaultdict(int)
    years = defaultdict(int)
    null_counts = defaultdict(int)

    for record in data:
        # County distribution
        if record.get('county'):
            counties[record['county']] += 1

        # Year distribution
        if record.get('year'):
            years[record['year']] += 1

        # Check for null values in critical fields
        for col in critical_columns.keys():
            if col in record and (record[col] is None or record[col] == ''):
                null_counts[col] += 1

    print(f"Counties found: {len(counties)}")
    for county, count in sorted(counties.items())[:5]:
        print(f"  • {county}: {count} records")
    if len(counties) > 5:
        print(f"  ... and {len(counties) - 5} more counties")

    print(f"\nYear distribution:")
    for year, count in sorted(years.items()):
        print(f"  • {year}: {count} records")

    if null_counts:
        print(f"\nNull/Empty values in critical columns:")
        for col, count in sorted(null_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(data)) * 100
            print(f"  • {col}: {count} ({percentage:.1f}%)")

def check_data_relationships():
    """Check relationships between Property Appraiser tables"""
    print("\n" + "=" * 60)
    print("DATA RELATIONSHIPS & ROUTING")
    print("=" * 60)

    # Get a sample parcel from florida_parcels
    result = make_request("/api/supabase/florida_parcels?limit=1")

    if not result:
        print("Could not get sample parcel for relationship testing")
        return

    data = result if isinstance(result, list) else result.get('data', [])

    if not data:
        print("No sample data available")
        return

    test_parcel = data[0].get('parcel_id')
    test_county = data[0].get('county')

    if not test_parcel or not test_county:
        print("Sample parcel missing required fields")
        return

    print(f"Testing relationships for parcel: {test_parcel}")
    print(f"County: {test_county}")
    print("-" * 40)

    # Check related tables
    related_tables = [
        ('nav_assessments', 'NAV - Property Values'),
        ('sdf_sales', 'SDF - Sales History'),
        ('nap_characteristics', 'NAP - Property Characteristics'),
        ('tax_deed_auctions', 'Tax Deed Auction Data'),
        ('tax_certificates', 'Tax Certificate Data'),
        ('building_permits', 'Building Permits')
    ]

    for table_name, description in related_tables:
        # Try to find matching record
        endpoint = f"/api/supabase/{table_name}?parcel_id=eq.{test_parcel}&limit=1"
        result = make_request(endpoint)

        if result:
            data = result if isinstance(result, list) else result.get('data', [])
            if data and len(data) > 0:
                print(f"  ✓ {table_name}: Found matching record ({description})")
            else:
                print(f"  ✗ {table_name}: No matching record ({description})")
        else:
            print(f"  ? {table_name}: Table not accessible ({description})")

def get_county_coverage():
    """Check county coverage in the database"""
    print("\n" + "=" * 60)
    print("COUNTY COVERAGE ANALYSIS")
    print("=" * 60)

    # All 67 Florida counties
    all_counties = [
        'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
        'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DESOTO', 'DIXIE',
        'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES',
        'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH',
        'HOLMES', 'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE',
        'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN',
        'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA',
        'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA',
        'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION',
        'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
    ]

    # Get larger sample to find more counties
    result = make_request("/api/supabase/florida_parcels?limit=1000&select=county,parcel_id")

    if not result:
        print("Could not access county data")
        return

    data = result if isinstance(result, list) else result.get('data', [])

    if not data:
        print("No data available for county analysis")
        return

    # Count parcels per county
    county_counts = defaultdict(int)
    for record in data:
        if record.get('county'):
            county_counts[record['county'].upper()] += 1

    found_counties = set(county_counts.keys())
    missing_counties = set(all_counties) - found_counties

    print(f"Counties with data: {len(found_counties)}/67")
    print(f"Missing counties: {len(missing_counties)}/67")

    if found_counties:
        print("\nCounties with data (sample):")
        for county in sorted(found_counties)[:10]:
            print(f"  • {county}: {county_counts[county]} parcels in sample")
        if len(found_counties) > 10:
            print(f"  ... and {len(found_counties) - 10} more counties")

    if missing_counties:
        print("\nMissing counties:")
        for county in sorted(missing_counties)[:10]:
            print(f"  • {county}")
        if len(missing_counties) > 10:
            print(f"  ... and {len(missing_counties) - 10} more counties")

def main():
    """Main audit function"""
    print("=" * 80)
    print("PROPERTY APPRAISER DATABASE AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"MCP Server: {MCP_BASE_URL}")
    print("=" * 80)

    # Check MCP Server health
    print("\nMCP SERVER STATUS:")
    print("-" * 40)
    health = make_request("/health")
    if health:
        print(f"✓ MCP Server is healthy")
        if 'services' in health:
            for service, status in health['services'].items():
                if isinstance(status, dict) and 'status' in status:
                    print(f"  • {service}: {status['status']}")
    else:
        print("✗ MCP Server not responding")
        return

    # Check available tables
    print("\n" + "=" * 60)
    print("TABLE AVAILABILITY CHECK")
    print("=" * 60)

    tables_to_check = [
        'florida_parcels',      # Main property data (NAL)
        'nav_assessments',       # Property values (NAV)
        'sdf_sales',            # Sales history (SDF)
        'nap_characteristics',   # Property characteristics (NAP)
        'tax_deed_auctions',
        'tax_certificates',
        'building_permits',
        'property_appraiser_data'
    ]

    available_tables = []
    for table in tables_to_check:
        if check_table(table):
            available_tables.append(table)

    if not available_tables:
        print("\n⚠ WARNING: No Property Appraiser tables are accessible!")
        print("Please check:")
        print("  1. Database connection in .env.mcp")
        print("  2. Table names and schemas in Supabase")
        print("  3. RLS policies and permissions")
        return

    # Deep analysis of main tables
    if 'florida_parcels' in available_tables:
        analyze_florida_parcels()
        check_data_relationships()
        get_county_coverage()

    # Summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)

    print(f"Tables accessible: {len(available_tables)}/{len(tables_to_check)}")
    print(f"Tables found: {', '.join(available_tables)}")

    print("\nRECOMMENDATIONS:")
    if len(available_tables) < len(tables_to_check):
        missing = set(tables_to_check) - set(available_tables)
        print(f"  • Create missing tables: {', '.join(missing)}")

    print("  • Verify column mappings match CLAUDE.md specifications")
    print("  • Ensure indexes exist on (parcel_id, county, year)")
    print("  • Check RLS policies for proper access control")
    print("  • Monitor daily updates from Florida Revenue portal")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()