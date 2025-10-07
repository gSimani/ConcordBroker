"""
Comprehensive parcel search including raw Florida data tables
Search for NAL, NAP, NAV, SDF raw data and multi-year records
"""

from supabase import create_client
import json
import sys

def comprehensive_parcel_search(parcel_id, county='MIAMI-DADE'):
    """Search for parcel data across ALL possible tables and formats"""

    # Use the exact credentials from .env.mcp
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

    print(f"COMPREHENSIVE PARCEL SEARCH")
    print(f"==================================================")
    print(f"Parcel ID: {parcel_id}")
    print(f"County: {county}")
    print(f"Database: {url}")
    print("=" * 80)

    try:
        client = create_client(url, key)

        # Try to discover ALL tables in the database first
        print("\nStep 1: Discovering all available tables...")

        # Extended list including raw Florida data tables
        all_possible_tables = [
            # Main tables we found
            'florida_parcels', 'properties', 'nav_assessments', 'florida_permits', 'property_assessments',

            # Raw Florida appraiser data tables (NAL, NAP, NAV, SDF)
            'florida_nal', 'florida_nap', 'florida_nav', 'florida_sdf',
            'miami_dade_nal', 'miami_dade_nap', 'miami_dade_nav', 'miami_dade_sdf',
            'broward_nal', 'broward_nap', 'broward_nav', 'broward_sdf',
            'palm_beach_nal', 'palm_beach_nap', 'palm_beach_nav', 'palm_beach_sdf',

            # Alternative table names
            'parcels', 'parcel_data', 'property_data', 'tax_data', 'assessment_data',
            'florida_properties', 'florida_tax_data', 'florida_assessments',
            'miami_dade_parcels', 'miami_dade_properties', 'miami_dade_tax_data',

            # Historical/multi-year tables
            'parcels_2025', 'parcels_2024', 'parcels_2023',
            'assessments_2025', 'assessments_2024', 'assessments_2023',
            'florida_parcels_2025', 'florida_parcels_2024', 'florida_parcels_2023',

            # Sales and building data
            'sales_history', 'property_sales', 'florida_sales', 'sdf_sales',
            'building_permits', 'permit_data', 'construction_permits',
            'building_details', 'property_features', 'extra_features',

            # Other potential tables
            'tax_certificates', 'tax_deeds', 'foreclosures',
            'property_owners', 'ownership_history', 'deed_transfers',
            'zoning_data', 'land_use', 'geographic_data',
            'subdivision_data', 'plat_data', 'legal_descriptions',

            # Raw import tables
            'raw_nal_data', 'raw_nap_data', 'raw_nav_data', 'raw_sdf_data',
            'imported_parcels', 'staging_parcels', 'temp_parcels'
        ]

        existing_tables = {}
        print(f"Checking {len(all_possible_tables)} potential tables...")

        # Check which tables actually exist
        for table_name in all_possible_tables:
            try:
                result = client.table(table_name).select('*').limit(1).execute()
                if result.data or hasattr(result, 'data'):
                    columns = list(result.data[0].keys()) if result.data else []
                    existing_tables[table_name] = columns
                    print(f"  [EXISTS] {table_name}: {len(columns)} columns")
            except Exception as e:
                if "does not exist" not in str(e).lower() and "PGRST205" not in str(e):
                    print(f"  [ERROR] {table_name}: {str(e)[:60]}")

        print(f"\nFound {len(existing_tables)} existing tables:")
        for table, cols in existing_tables.items():
            print(f"  - {table}: {len(cols)} columns")

        # Step 2: Search each existing table for the parcel
        print(f"\nStep 2: Searching for parcel {parcel_id} in all tables...")
        all_results = {}

        for table_name, columns in existing_tables.items():
            print(f"\n[SEARCHING] {table_name}")

            # Identify potential parcel ID columns
            parcel_columns = []
            for col in columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['parcel', 'folio', 'strap', 'property_id']):
                    parcel_columns.append(col)

            if not parcel_columns:
                print(f"  No parcel-like columns found")
                continue

            print(f"  Parcel columns: {parcel_columns}")

            # Try different formats of the parcel ID
            parcel_formats = [
                parcel_id,  # Original: 3040190012860
                f"{parcel_id[:2]}-{parcel_id[2:4]}-{parcel_id[4:6]}-{parcel_id[6:8]}-{parcel_id[8:11]}-{parcel_id[11:]}",  # 30-40-19-00-12-860
                f"{parcel_id[:2]}{parcel_id[2:4]}{parcel_id[4:6]}{parcel_id[6:8]}{parcel_id[8:11]}{parcel_id[11:]}",  # Same as original
                f"{parcel_id[:2]}-{parcel_id[2:4]}-{parcel_id[4:6]}-{parcel_id[6:]}",  # 30-40-19-0012860
                f"{parcel_id[:4]}-{parcel_id[4:8]}-{parcel_id[8:]}",  # 3040-1900-12860
            ]

            found_data = False
            for parcel_format in parcel_formats:
                for parcel_col in parcel_columns:
                    try:
                        # Try exact match
                        query_params = {parcel_col: f'eq.{parcel_format}'}
                        if 'county' in [c.lower() for c in columns]:
                            query_params['county'] = f'eq.{county}'
                        elif 'COUNTY' in columns:
                            query_params['COUNTY'] = f'eq.{county}'

                        result = client.table(table_name).select('*').match(query_params).execute()
                        if result.data:
                            print(f"  [FOUND] {len(result.data)} records with {parcel_col}={parcel_format}")
                            all_results[f"{table_name}_{parcel_col}"] = {
                                'table': table_name,
                                'column': parcel_col,
                                'format': parcel_format,
                                'data': result.data
                            }
                            found_data = True
                            break
                    except Exception as e:
                        continue

                if found_data:
                    break

            # If no exact matches, try wildcard searches
            if not found_data:
                for parcel_col in parcel_columns:
                    try:
                        result = client.table(table_name).select('*').ilike(parcel_col, f'%{parcel_id[-6:]}%').limit(5).execute()
                        if result.data:
                            print(f"  [PARTIAL] {len(result.data)} partial matches in {parcel_col}")
                            all_results[f"{table_name}_{parcel_col}_partial"] = {
                                'table': table_name,
                                'column': parcel_col,
                                'format': 'wildcard',
                                'data': result.data
                            }
                            found_data = True
                            break
                    except:
                        continue

            if not found_data:
                print(f"  No matches found")

        # Step 3: Display comprehensive results
        print(f"\n" + "=" * 80)
        print("COMPREHENSIVE RESULTS")
        print("=" * 80)

        if all_results:
            print(f"Found data in {len(all_results)} table/column combinations:")

            for key, result_info in all_results.items():
                table = result_info['table']
                column = result_info['column']
                format_used = result_info['format']
                data = result_info['data']

                print(f"\n[RESULT] {table}.{column} (format: {format_used})")
                print(f"         Records found: {len(data)}")

                if data:
                    sample = data[0]
                    print(f"         Sample record columns: {len(sample)}")

                    # Show key fields
                    key_fields = ['parcel_id', 'owner_name', 'property_address', 'phy_addr1',
                                'subdivision', 'legal_desc', 'year_built', 'just_value',
                                'land_value', 'building_value', 'total_living_area']

                    for field in key_fields:
                        for actual_field in sample.keys():
                            if field.lower() in actual_field.lower():
                                value = sample[actual_field]
                                print(f"         {actual_field}: {value}")

            # Save comprehensive results
            output_file = f'comprehensive_parcel_data_{parcel_id}.json'
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)

            print(f"\n[SAVED] All results saved to: {output_file}")

            # Save table inventory
            inventory_file = f'database_table_inventory.json'
            with open(inventory_file, 'w') as f:
                json.dump(existing_tables, f, indent=2)

            print(f"[SAVED] Database table inventory saved to: {inventory_file}")

            return all_results

        else:
            print(f"No data found for parcel {parcel_id}")
            print(f"Searched {len(existing_tables)} tables")

            # Still save the table inventory
            inventory_file = f'database_table_inventory.json'
            with open(inventory_file, 'w') as f:
                json.dump(existing_tables, f, indent=2)
            print(f"[SAVED] Database table inventory saved to: {inventory_file}")

            return None

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return None

if __name__ == "__main__":
    parcel_id = "3040190012860"
    county = "MIAMI-DADE"

    if len(sys.argv) > 1:
        parcel_id = sys.argv[1]
    if len(sys.argv) > 2:
        county = sys.argv[2]

    result = comprehensive_parcel_search(parcel_id, county)