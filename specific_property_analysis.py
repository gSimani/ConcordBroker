#!/usr/bin/env python3
"""
Specific Property Analysis
==========================
Quick analysis of the two target properties across all relevant tables
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

def get_db_url():
    """Get cleaned database URL"""
    url = os.getenv('DATABASE_URL')
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+psycopg2://', 1)
        if '&supa=' in url:
            url = url.split('&supa=')[0]
        if '&pgbouncer=' in url:
            url = url.split('&pgbouncer=')[0]
        return url
    raise ValueError("No DATABASE_URL found")

def analyze_specific_properties():
    """Analyze the two target properties"""
    target_properties = ['1078130000370', '504231242730']

    # Tables to search for parcel data
    property_tables = [
        'florida_parcels',
        'property_sales_history',
        'property_assessments',
        'tax_certificates',
        'nav_parcel_assessments',
        'property_sales',
        'fact_property_score'
    ]

    results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'properties_analyzed': target_properties,
        'tables_searched': property_tables,
        'results': {}
    }

    db_url = get_db_url()
    engine = create_engine(db_url, pool_size=5, max_overflow=10)

    with engine.connect() as conn:
        for parcel_id in target_properties:
            print(f"\nAnalyzing Property: {parcel_id}")
            print("=" * 50)

            property_data = {
                'parcel_id': parcel_id,
                'found_in_tables': [],
                'data_summary': {},
                'total_records_found': 0
            }

            # Search each table
            for table_name in property_tables:
                try:
                    # Check if table exists and has parcel_id column
                    table_check = conn.execute(text(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        AND column_name = 'parcel_id'
                    """)).fetchall()

                    if not table_check:
                        print(f"  SKIP {table_name}: No parcel_id column")
                        continue

                    # Search for the property
                    result = conn.execute(text(f"""
                        SELECT COUNT(*)
                        FROM {table_name}
                        WHERE parcel_id = :parcel_id
                    """), {'parcel_id': parcel_id}).scalar()

                    if result > 0:
                        print(f"  FOUND {table_name}: {result} records found")
                        property_data['found_in_tables'].append(table_name)
                        property_data['total_records_found'] += result

                        # Get sample data
                        sample_query = f"""
                            SELECT * FROM {table_name}
                            WHERE parcel_id = :parcel_id
                            LIMIT 1
                        """
                        sample_result = conn.execute(text(sample_query), {'parcel_id': parcel_id}).fetchone()

                        if sample_result:
                            # Get column names
                            columns = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 1")).keys()

                            # Convert to dict, handling special types
                            sample_dict = {}
                            for i, col in enumerate(columns):
                                value = sample_result[i]
                                if hasattr(value, 'isoformat'):
                                    value = value.isoformat()
                                elif isinstance(value, (bytes, memoryview)):
                                    value = str(value)
                                sample_dict[col] = value

                            property_data['data_summary'][table_name] = {
                                'record_count': result,
                                'sample_record': sample_dict
                            }
                    else:
                        print(f"  NOT FOUND {table_name}: No records found")

                except Exception as e:
                    print(f"  ERROR {table_name}: Error - {e}")

            # Summary for this property
            if property_data['total_records_found'] > 0:
                print(f"\nSummary for {parcel_id}:")
                print(f"  Found in {len(property_data['found_in_tables'])} tables")
                print(f"  Total records: {property_data['total_records_found']}")
                print(f"  Tables: {', '.join(property_data['found_in_tables'])}")

                # Extract key info if found in florida_parcels
                if 'florida_parcels' in property_data['data_summary']:
                    parcels_data = property_data['data_summary']['florida_parcels']['sample_record']
                    print(f"\nProperty Details:")
                    print(f"  County: {parcels_data.get('county', 'N/A')}")
                    print(f"  Address: {parcels_data.get('phy_addr1', 'N/A')}")
                    print(f"  Owner: {parcels_data.get('owner_name1', 'N/A')}")
                    print(f"  Just Value: ${parcels_data.get('just_value', 0):,}")
                    print(f"  Year: {parcels_data.get('year', 'N/A')}")
            else:
                print(f"\nProperty {parcel_id} not found in any table")

            results['results'][parcel_id] = property_data

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"specific_property_analysis_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nAnalysis saved to {output_file}")

    # Print final summary
    print(f"\n" + "="*60)
    print("SPECIFIC PROPERTY ANALYSIS SUMMARY")
    print("="*60)

    for parcel_id in target_properties:
        data = results['results'][parcel_id]
        print(f"\nProperty {parcel_id}:")
        if data['total_records_found'] > 0:
            print(f"  Found in {len(data['found_in_tables'])} tables")
            print(f"  Total records: {data['total_records_found']}")
            print(f"  Tables: {', '.join(data['found_in_tables'])}")
        else:
            print(f"  Not found in database")

    return results

if __name__ == "__main__":
    analyze_specific_properties()