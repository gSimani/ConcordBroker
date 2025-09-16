#!/usr/bin/env python3
"""
Direct Supabase Property Appraiser Database Audit
"""

import os
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv('.env.mcp')

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def test_supabase_connection():
    """Test direct connection to Supabase and audit Property Appraiser data"""
    print("=" * 80)
    print("PROPERTY APPRAISER DATABASE AUDIT - DIRECT SUPABASE CONNECTION")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    try:
        # Create Supabase client with service role key
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        print(f"\n[OK] Connected to Supabase")
        print(f"URL: {SUPABASE_URL}")

        # Test table access
        print("\n1. TESTING TABLE ACCESS:")
        print("-" * 40)

        tables_to_test = [
            'florida_parcels',
            'nav_assessments',
            'sdf_sales',
            'nap_characteristics',
            'tax_deed_auctions',
            'tax_certificates',
            'building_permits'
        ]

        accessible_tables = []
        table_info = {}

        for table in tables_to_test:
            try:
                # Try to fetch one record
                response = supabase.table(table).select("*").limit(1).execute()

                if response.data is not None:
                    if len(response.data) > 0:
                        cols = list(response.data[0].keys())
                        print(f"  [OK] {table}: Table exists with {len(cols)} columns")
                        table_info[table] = cols
                    else:
                        print(f"  [OK] {table}: Table exists but is empty")
                        table_info[table] = []
                    accessible_tables.append(table)
                else:
                    print(f"  [X] {table}: No data returned")

            except Exception as e:
                error_msg = str(e)
                if 'relation' in error_msg and 'does not exist' in error_msg:
                    print(f"  [X] {table}: Table does not exist")
                elif 'permission denied' in error_msg:
                    print(f"  [X] {table}: Permission denied (check RLS)")
                else:
                    print(f"  [X] {table}: Error - {error_msg[:50]}...")

        # If florida_parcels exists, do deeper analysis
        if 'florida_parcels' in accessible_tables:
            print("\n2. FLORIDA_PARCELS TABLE ANALYSIS:")
            print("-" * 40)

            # Get sample data
            response = supabase.table('florida_parcels').select("*").limit(100).execute()

            if response.data and len(response.data) > 0:
                sample = response.data[0]

                # Check column mappings per CLAUDE.md
                print("\nColumn Mapping Verification (NAL -> florida_parcels):")
                critical_mappings = {
                    'parcel_id': 'Primary key (required)',
                    'county': 'County name (uppercase)',
                    'year': 'Tax year (2025)',
                    'land_sqft': 'LND_SQFOOT',
                    'phy_addr1': 'PHY_ADDR1',
                    'phy_addr2': 'PHY_ADDR2',
                    'owner_addr1': 'OWN_ADDR1',
                    'owner_addr2': 'OWN_ADDR2',
                    'owner_state': 'OWN_STATE (2 chars)',
                    'just_value': 'JV',
                    'land_value': 'Land assessed value',
                    'building_value': 'Building value',
                    'sale_date': 'SALE_YR1/SALE_MO1',
                    'sale_price': 'Sale price'
                }

                missing_columns = []
                validation_issues = []

                for col, desc in critical_mappings.items():
                    if col in sample:
                        value = sample[col]
                        print(f"  [OK] {col}: Present")

                        # Validate specific rules
                        if col == 'owner_state' and value and len(str(value)) > 2:
                            validation_issues.append(f"{col}: '{value}' should be 2 chars")
                        elif col == 'county' and value and value != value.upper():
                            validation_issues.append(f"{col}: '{value}' should be uppercase")
                        elif col == 'sale_date' and value == '':
                            validation_issues.append(f"{col}: empty string (should be NULL)")
                    else:
                        print(f"  [X] {col}: MISSING - {desc}")
                        missing_columns.append(col)

                if validation_issues:
                    print("\nValidation Issues Found:")
                    for issue in validation_issues:
                        print(f"  [WARNING] {issue}")

                # Analyze data distribution
                print("\n3. DATA DISTRIBUTION ANALYSIS:")
                print("-" * 40)

                counties = defaultdict(int)
                years = defaultdict(int)
                null_counts = defaultdict(int)
                empty_counts = defaultdict(int)

                for record in response.data:
                    # County distribution
                    if record.get('county'):
                        counties[record['county']] += 1

                    # Year distribution
                    if record.get('year'):
                        years[record['year']] += 1

                    # Check for null/empty values
                    for col in critical_mappings.keys():
                        if col in record:
                            if record[col] is None:
                                null_counts[col] += 1
                            elif record[col] == '':
                                empty_counts[col] += 1

                print(f"Sample size: {len(response.data)} records")
                print(f"Unique counties: {len(counties)}")
                print(f"Counties found: {', '.join(sorted(counties.keys())[:5])}")
                if len(counties) > 5:
                    print(f"  ... and {len(counties) - 5} more")

                print(f"\nYear distribution:")
                for year, count in sorted(years.items()):
                    print(f"  Year {year}: {count} records")

                if null_counts or empty_counts:
                    print(f"\nData completeness issues:")
                    for col in critical_mappings.keys():
                        total_issues = null_counts.get(col, 0) + empty_counts.get(col, 0)
                        if total_issues > 0:
                            pct = (total_issues / len(response.data)) * 100
                            print(f"  {col}: {pct:.1f}% null/empty")

        # Check data routing between tables
        if len(accessible_tables) > 1 and 'florida_parcels' in accessible_tables:
            print("\n4. DATA ROUTING & RELATIONSHIPS:")
            print("-" * 40)

            # Get a test parcel
            response = supabase.table('florida_parcels').select("parcel_id,county").limit(5).execute()

            if response.data and len(response.data) > 0:
                test_records = response.data

                routing_results = defaultdict(int)

                for test_record in test_records:
                    test_parcel = test_record.get('parcel_id')
                    test_county = test_record.get('county')

                    if test_parcel and test_county:
                        # Check each related table
                        for table in ['nav_assessments', 'sdf_sales', 'nap_characteristics']:
                            if table in accessible_tables:
                                try:
                                    result = supabase.table(table)\
                                        .select("parcel_id")\
                                        .eq('parcel_id', test_parcel)\
                                        .limit(1)\
                                        .execute()

                                    if result.data and len(result.data) > 0:
                                        routing_results[table] += 1
                                except:
                                    pass

                print(f"Tested {len(test_records)} parcels for relationships:")
                print("\nData flow mapping (SOURCE -> TABLE):")
                print("  NAL (Names/Addresses) -> florida_parcels")
                print("  NAP (Characteristics) -> nap_characteristics")
                print("  NAV (Values) -> nav_assessments")
                print("  SDF (Sales) -> sdf_sales")

                print(f"\nRelationship test results:")
                for table, matches in routing_results.items():
                    pct = (matches / len(test_records)) * 100
                    print(f"  florida_parcels -> {table}: {matches}/{len(test_records)} ({pct:.0f}%)")

        # Check county coverage
        print("\n5. COUNTY COVERAGE ANALYSIS:")
        print("-" * 40)

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

        if 'florida_parcels' in accessible_tables:
            try:
                # Get distinct counties
                response = supabase.table('florida_parcels')\
                    .select("county")\
                    .limit(10000)\
                    .execute()

                if response.data:
                    found_counties = set()
                    for record in response.data:
                        if record.get('county'):
                            found_counties.add(record['county'].upper())

                    missing_counties = set(all_counties) - found_counties

                    print(f"Total Florida counties: 67")
                    print(f"Counties with data: {len(found_counties)}")
                    print(f"Missing counties: {len(missing_counties)}")

                    if missing_counties:
                        print(f"\nMissing counties:")
                        for county in sorted(missing_counties)[:10]:
                            print(f"  - {county}")
                        if len(missing_counties) > 10:
                            print(f"  ... and {len(missing_counties) - 10} more")

            except Exception as e:
                print(f"Could not analyze county coverage: {e}")

        # Generate summary report
        print("\n" + "=" * 80)
        print("AUDIT SUMMARY REPORT")
        print("=" * 80)

        print(f"\nDatabase: Supabase PostgreSQL")
        print(f"Tables accessible: {len(accessible_tables)}/{len(tables_to_test)}")

        if accessible_tables:
            print(f"\nAccessible tables:")
            for table in accessible_tables:
                col_count = len(table_info.get(table, []))
                print(f"  - {table} ({col_count} columns)")

        missing = set(tables_to_test) - set(accessible_tables)
        if missing:
            print(f"\nMissing/Inaccessible tables:")
            for table in missing:
                print(f"  - {table}")

        print("\nRECOMMENDATIONS:")
        print("  1. Ensure all Property Appraiser tables are created")
        print("  2. Verify column mappings match CLAUDE.md specifications")
        print("  3. Create indexes on (parcel_id, county, year)")
        print("  4. Set up daily monitoring for Florida Revenue updates")
        print("  5. Implement data validation for state codes and dates")
        print("  6. Complete data upload for all 67 Florida counties")

        print("\nDATA ROUTING ARCHITECTURE:")
        print("  Source Files (Florida Revenue) -> Database Tables")
        print("  - NAL files -> florida_parcels (names/addresses)")
        print("  - NAP files -> nap_characteristics (property details)")
        print("  - NAV files -> nav_assessments (values)")
        print("  - SDF files -> sdf_sales (sales history)")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to connect to Supabase:")
        print(f"  {str(e)}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    exit(0 if success else 1)