"""
Query specific parcel data from Supabase using direct credentials
"""

from supabase import create_client
import json
import sys

def query_parcel_data(parcel_id, county='MIAMI-DADE'):
    """Query all data for a specific parcel"""

    # Use the exact credentials from .env.mcp
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

    print(f"Connecting to: {url}")
    print(f"Querying parcel: {parcel_id} in {county}")
    print("=" * 80)

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
            'florida_revenue',
            'florida_nal_data',
            'florida_nap_data',
            'florida_nav_data',
            'florida_sdf_data',
            'miami_dade_parcels',
            'property_data',
            'tax_data'
        ]

        all_results = {}
        table_structures = {}

        for table_name in tables_to_check:
            try:
                print(f"\nChecking table: {table_name}")

                # First, try to get the table structure
                try:
                    structure_result = client.table(table_name).select('*').limit(1).execute()
                    if structure_result.data:
                        columns = list(structure_result.data[0].keys())
                        table_structures[table_name] = columns
                        print(f"  Table exists with {len(columns)} columns")
                        print(f"  Columns: {', '.join(columns[:15])}")
                        if len(columns) > 15:
                            print(f"    ... and {len(columns) - 15} more")
                    else:
                        print(f"  Table exists but is empty")
                        table_structures[table_name] = []
                except Exception as e:
                    if "does not exist" in str(e).lower():
                        print(f"  Table does not exist")
                        continue
                    else:
                        print(f"  Error getting structure: {str(e)[:100]}")
                        continue

                # Now try different query patterns to find the parcel
                query_patterns = [
                    {'parcel_id': f'eq.{parcel_id}', 'county': f'eq.{county}'},
                    {'parcel_id': f'eq.{parcel_id}'},
                    {'PARCEL_ID': f'eq.{parcel_id}', 'COUNTY': f'eq.{county}'},
                    {'PARCEL_ID': f'eq.{parcel_id}'},
                    {'parcel': f'eq.{parcel_id}'},
                    {'folio': f'eq.{parcel_id}'},
                    {'property_id': f'eq.{parcel_id}'},
                    {'PARCEL': f'eq.{parcel_id}'},
                    {'FOLIO': f'eq.{parcel_id}'},
                    {'strap': f'eq.{parcel_id}'},
                    {'STRAP': f'eq.{parcel_id}'}
                ]

                found_data = False
                for query_params in query_patterns:
                    try:
                        result = client.table(table_name).select('*').match(query_params).execute()
                        if result.data:
                            print(f"  [FOUND] {len(result.data)} records with query: {query_params}")
                            all_results[table_name] = result.data
                            found_data = True
                            break
                    except Exception as e:
                        continue

                if not found_data and table_name in table_structures:
                    # Try wildcard search if we have columns
                    columns = table_structures[table_name]
                    parcel_like_columns = [col for col in columns if 'parcel' in col.lower() or 'folio' in col.lower() or 'strap' in col.lower()]

                    for col in parcel_like_columns:
                        try:
                            # Try ilike search for partial matches
                            result = client.table(table_name).select('*').ilike(col, f'%{parcel_id}%').limit(5).execute()
                            if result.data:
                                print(f"  ~ Found {len(result.data)} partial matches in column '{col}'")
                                if table_name not in all_results:
                                    all_results[table_name] = result.data
                                found_data = True
                                break
                        except:
                            continue

                if not found_data:
                    print(f"  - No matching records found")

            except Exception as e:
                print(f"  ⚠ Error with {table_name}: {str(e)[:100]}")

        # Display and save results
        print("\n" + "=" * 80)
        print("SEARCH RESULTS SUMMARY")
        print("=" * 80)

        if all_results:
            print(f"Found data in {len(all_results)} tables:")

            for table_name, data in all_results.items():
                print(f"\n[TABLE] {table_name.upper()}: {len(data)} records")
                if data:
                    sample_record = data[0]
                    print(f"   Columns ({len(sample_record)}):")

                    # Show all column names and sample values
                    for i, (key, value) in enumerate(sample_record.items()):
                        if i < 20:  # Show first 20 columns in detail
                            value_str = str(value)[:50] if value is not None else "NULL"
                            print(f"     {key}: {value_str}")
                        elif i == 20:
                            print(f"     ... and {len(sample_record) - 20} more columns")

            # Save detailed results
            output_file = f'parcel_data_{parcel_id.replace("/", "_")}.json'
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)

            print(f"\n[SAVED] Detailed results saved to: {output_file}")

            # Save table structures too
            structure_file = f'table_structures_{parcel_id.replace("/", "_")}.json'
            with open(structure_file, 'w') as f:
                json.dump(table_structures, f, indent=2)
            print(f"[SAVED] Table structures saved to: {structure_file}")

            return all_results
        else:
            print(f"[NO DATA] No data found for parcel {parcel_id} in {county}")
            print(f"[INFO] Checked {len(tables_to_check)} tables")

            if table_structures:
                print(f"[TABLES] Found {len(table_structures)} existing tables:")
                for table_name, columns in table_structures.items():
                    print(f"   {table_name}: {len(columns)} columns")

                # Save structure info even if no parcel data found
                structure_file = f'available_tables_{county.replace("-", "_")}.json'
                with open(structure_file, 'w') as f:
                    json.dump(table_structures, f, indent=2)
                print(f"[SAVED] Available table structures saved to: {structure_file}")

            return None

    except Exception as e:
        print(f"[ERROR] Database connection error: {e}")
        return None

if __name__ == "__main__":
    parcel_id = "3040190012860"
    county = "MIAMI-DADE"

    if len(sys.argv) > 1:
        parcel_id = sys.argv[1]
    if len(sys.argv) > 2:
        county = sys.argv[2]

    print("COMPREHENSIVE PARCEL DATA SEARCH")
    print("=" * 80)

    result = query_parcel_data(parcel_id, county)

    if not result:
        print(f"\n[RECOMMENDATIONS]:")
        print(f"1. Verify parcel ID format: {parcel_id}")
        print(f"2. Try alternative formats (with/without dashes, different lengths)")
        print(f"3. Check if data exists under different county name")
        print(f"4. Verify the parcel actually exists in this database")