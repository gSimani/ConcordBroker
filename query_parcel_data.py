"""
Query specific parcel data from Supabase
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import json

# Load environment variables from .env.mcp
load_dotenv('.env.mcp')

def query_parcel_data(parcel_id, county='MIAMI-DADE'):
    """Query all data for a specific parcel"""

    # Get credentials from .env.mcp
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.mcp")
        return None

    print(f"Connecting to: {url}")
    print(f"Querying parcel: {parcel_id} in {county}")

    try:
        client = create_client(url, key)

        # List of potential tables to check for parcel data
        tables_to_check = [
            'florida_parcels',
            'parcels',
            'broward_parcels',
            'properties',
            'nal_parcels',
            'nap_parcels',
            'nav_assessments',
            'sdf_sales',
            'sales_history',
            'florida_sales',
            'building_permits',
            'florida_permits',
            'property_assessments',
            'property_tax_info',
            'florida_nav',
            'florida_revenue'
        ]

        all_results = {}

        for table_name in tables_to_check:
            try:
                print(f"\nChecking table: {table_name}")

                # Try different query patterns
                queries_to_try = [
                    {'parcel_id': f'eq.{parcel_id}', 'county': f'eq.{county}'},
                    {'parcel_id': f'eq.{parcel_id}'},
                    {'PARCEL_ID': f'eq.{parcel_id}', 'COUNTY': f'eq.{county}'},
                    {'PARCEL_ID': f'eq.{parcel_id}'},
                    {'parcel': f'eq.{parcel_id}'},
                    {'folio': f'eq.{parcel_id}'},
                    {'property_id': f'eq.{parcel_id}'}
                ]

                found_data = False
                for query_params in queries_to_try:
                    try:
                        result = client.table(table_name).select('*').match(query_params).execute()
                        if result.data:
                            print(f"  ✓ Found {len(result.data)} records with query: {query_params}")
                            all_results[table_name] = result.data
                            found_data = True
                            break
                    except Exception as e:
                        continue

                if not found_data:
                    # Try to get table structure by fetching first few records
                    try:
                        result = client.table(table_name).select('*').limit(1).execute()
                        if result.data:
                            print(f"  - Table exists but no matching records found")
                            print(f"  - Sample columns: {list(result.data[0].keys()) if result.data else 'None'}")
                    except Exception as e:
                        if "does not exist" not in str(e).lower():
                            print(f"  - Error accessing table: {str(e)[:100]}")

            except Exception as e:
                if "does not exist" not in str(e).lower():
                    print(f"  ⚠ Error with {table_name}: {str(e)[:100]}")

        # Save results
        if all_results:
            output_file = f'parcel_data_{parcel_id.replace("/", "_")}.json'
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)

            print(f"\n" + "=" * 80)
            print(f"RESULTS SUMMARY:")
            print(f"Found data in {len(all_results)} tables:")

            for table_name, data in all_results.items():
                print(f"\n{table_name.upper()}: {len(data)} records")
                if data:
                    sample_record = data[0]
                    print(f"  Columns ({len(sample_record)}): {', '.join(list(sample_record.keys())[:10])}")
                    if len(sample_record) > 10:
                        print(f"    ... and {len(sample_record) - 10} more")

            print(f"\nDetailed results saved to: {output_file}")
            return all_results
        else:
            print(f"\nNo data found for parcel {parcel_id} in {county}")
            return None

    except Exception as e:
        print(f"Database connection error: {e}")
        return None

if __name__ == "__main__":
    parcel_id = "3040190012860"
    county = "MIAMI-DADE"

    if len(sys.argv) > 1:
        parcel_id = sys.argv[1]
    if len(sys.argv) > 2:
        county = sys.argv[2]

    query_parcel_data(parcel_id, county)