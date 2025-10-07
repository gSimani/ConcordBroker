"""
Complete Miami-Dade parcel search including all alternative formats
Focus on Miami-Dade specific parcel formats and historical data
"""

from supabase import create_client
import json
import sys

def search_miami_dade_parcel_complete(parcel_id, county='MIAMI-DADE'):
    """Complete search for Miami-Dade parcel including all alternative formats"""

    # Use the exact credentials from .env.mcp
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

    print(f"COMPLETE MIAMI-DADE PARCEL SEARCH")
    print(f"=================================")
    print(f"Target Parcel: {parcel_id}")
    print(f"County: {county}")
    print("=" * 80)

    try:
        client = create_client(url, key)

        # Miami-Dade specific parcel formats
        # Format: 3040190012860 could be:
        # - 30-4019-001-2860 (Section-Township-Range-Parcel)
        # - 3040190012860 (Standard)
        # - 30-40-19-00-12-860 (6-digit breakdown)
        # - 3040-19-0012860 (Alternative)

        alternative_formats = [
            parcel_id,  # Original: 3040190012860
            f"30-4019-001-2860",  # Miami-Dade format 1
            f"30-4019-001-{parcel_id[7:]}",  # Dynamic
            f"30-40-19-001-{parcel_id[7:]}",  # 6-digit breakdown
            f"3040-19-00-{parcel_id[8:]}",  # Alternative breakdown
            f"{parcel_id[:4]}-{parcel_id[4:6]}-{parcel_id[6:9]}-{parcel_id[9:]}",  # 3040-19-001-2860
            f"{parcel_id[:2]}-{parcel_id[2:6]}-{parcel_id[6:9]}-{parcel_id[9:]}",  # 30-4019-001-2860
            f"{parcel_id[:6]}{parcel_id[6:]}",  # Remove any implicit formatting

            # Also try without leading zeros
            "304019001286",  # Remove trailing zero
            "30401900128600",  # Add trailing zero
        ]

        print(f"Alternative formats to try:")
        for i, fmt in enumerate(alternative_formats, 1):
            print(f"  {i:2d}. {fmt}")

        # Search all existing tables
        existing_tables = ['florida_parcels', 'properties', 'nav_assessments', 'florida_permits', 'property_assessments', 'tax_certificates']

        all_matches = {}

        for table_name in existing_tables:
            print(f"\n[SEARCHING] {table_name}")

            try:
                # Get table structure
                sample_result = client.table(table_name).select('*').limit(1).execute()
                if not sample_result.data:
                    print(f"  Table is empty")
                    continue

                columns = list(sample_result.data[0].keys())
                parcel_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['parcel', 'folio', 'strap', 'property_id'])]

                if not parcel_columns:
                    print(f"  No parcel-like columns")
                    continue

                print(f"  Parcel columns: {parcel_columns}")

                table_matches = []

                # Try all formats in all parcel columns
                for fmt in alternative_formats:
                    for col in parcel_columns:
                        try:
                            # Exact match
                            query_params = {col: f'eq.{fmt}'}
                            if 'county' in [c.lower() for c in columns] or 'COUNTY' in columns:
                                county_col = 'county' if 'county' in columns else 'COUNTY'
                                query_params[county_col] = f'eq.{county}'

                            result = client.table(table_name).select('*').match(query_params).execute()
                            if result.data:
                                print(f"    [EXACT MATCH] {col}={fmt} -> {len(result.data)} records")
                                table_matches.extend(result.data)
                                break  # Found exact match, no need to try more formats for this column

                        except Exception as e:
                            continue

                # If no exact matches, try partial matches with original ID
                if not table_matches:
                    for col in parcel_columns:
                        try:
                            # Partial match with original parcel ID
                            result = client.table(table_name).select('*').ilike(col, f'%{parcel_id}%').execute()
                            if result.data:
                                # Check if any actually match our county
                                miami_matches = []
                                for record in result.data:
                                    county_field = None
                                    for field_name in ['county', 'COUNTY', 'county_name']:
                                        if field_name in record and record[field_name]:
                                            county_field = record[field_name]
                                            break

                                    if county_field and county.upper() in str(county_field).upper():
                                        miami_matches.append(record)

                                if miami_matches:
                                    print(f"    [PARTIAL MATCH] {col} -> {len(miami_matches)} Miami-Dade records")
                                    table_matches.extend(miami_matches)
                                else:
                                    print(f"    [PARTIAL MATCH] {col} -> {len(result.data)} records (other counties)")
                                break
                        except:
                            continue

                if table_matches:
                    all_matches[table_name] = table_matches
                else:
                    print(f"  No matches found")

            except Exception as e:
                print(f"  Error: {str(e)[:100]}")

        # Display comprehensive results
        print(f"\n" + "=" * 80)
        print("COMPLETE SEARCH RESULTS")
        print("=" * 80)

        if all_matches:
            print(f"Found data in {len(all_matches)} tables:")

            # Process results for comprehensive display
            complete_parcel_data = {}

            for table_name, matches in all_matches.items():
                print(f"\n[TABLE] {table_name.upper()}")
                print(f"Records: {len(matches)}")

                complete_parcel_data[table_name] = matches

                # Show detailed information for each record
                for i, record in enumerate(matches):
                    print(f"\n  Record {i+1}:")

                    # Key fields to highlight
                    key_fields_mapping = {
                        'parcel_id': ['parcel_id', 'PARCEL_ID', 'folio', 'strap'],
                        'owner_name': ['owner_name', 'OWNER_NAME', 'owner'],
                        'owner_address': ['owner_addr1', 'owner_address', 'OWNER_ADDR1', 'owner_addr'],
                        'mailing_address': ['owner_addr1', 'owner_addr2', 'owner_city', 'owner_state', 'owner_zip'],
                        'property_address': ['phy_addr1', 'property_address', 'PHY_ADDR1', 'address'],
                        'subdivision': ['subdivision', 'SUBDIVISION', 'subdiv'],
                        'legal_description': ['legal_desc', 'LEGAL_DESC', 'legal_description'],
                        'just_value': ['just_value', 'JUST_VALUE', 'total_value'],
                        'assessed_value': ['assessed_value', 'ASSESSED_VALUE'],
                        'land_value': ['land_value', 'LAND_VALUE'],
                        'building_value': ['building_value', 'BUILDING_VALUE', 'improvement_value'],
                        'year_built': ['year_built', 'YEAR_BUILT', 'year_build'],
                        'living_area': ['total_living_area', 'living_area', 'LIVING_AREA', 'total_sqft'],
                        'bedrooms': ['bedrooms', 'BEDROOMS', 'beds'],
                        'bathrooms': ['bathrooms', 'BATHROOMS', 'baths'],
                        'property_use': ['property_use', 'PROPERTY_USE', 'use_code'],
                        'sale_date': ['sale_date', 'SALE_DATE', 'last_sale_date'],
                        'sale_price': ['sale_price', 'SALE_PRICE', 'last_sale_price'],
                        'land_sqft': ['land_sqft', 'LAND_SQFT', 'lot_size_sqft']
                    }

                    # Display organized field information
                    for category, possible_fields in key_fields_mapping.items():
                        found_field = None
                        found_value = None

                        for field in possible_fields:
                            if field in record and record[field] is not None:
                                found_field = field
                                found_value = record[field]
                                break

                        if found_field and found_value:
                            print(f"    {category.title().replace('_', ' ')}: {found_value} ({found_field})")
                        else:
                            print(f"    {category.title().replace('_', ' ')}: [NOT AVAILABLE]")

                    # Show additional fields that might contain important data
                    additional_interesting_fields = []
                    for field_name, value in record.items():
                        if (field_name.lower() not in [f.lower() for sublist in key_fields_mapping.values() for f in sublist] and
                            value is not None and
                            field_name.lower() not in ['id', 'created_at', 'updated_at', 'import_date', 'update_date', 'data_hash']):
                            additional_interesting_fields.append((field_name, value))

                    if additional_interesting_fields:
                        print(f"    Additional fields ({len(additional_interesting_fields)}):")
                        for field_name, value in additional_interesting_fields[:10]:  # Show first 10
                            value_str = str(value)[:50] if len(str(value)) > 50 else str(value)
                            print(f"      {field_name}: {value_str}")
                        if len(additional_interesting_fields) > 10:
                            print(f"      ... and {len(additional_interesting_fields) - 10} more")

            # Save complete results
            output_file = f'complete_miami_dade_parcel_{parcel_id}.json'
            with open(output_file, 'w') as f:
                json.dump(complete_parcel_data, f, indent=2, default=str)

            print(f"\n[SAVED] Complete results saved to: {output_file}")

            # Create summary report
            summary = {
                'parcel_id': parcel_id,
                'county': county,
                'search_date': str(sys.version),
                'tables_found': list(all_matches.keys()),
                'total_records': sum(len(matches) for matches in all_matches.values()),
                'data_gaps': []
            }

            # Identify missing critical data
            critical_fields = ['subdivision', 'legal_desc', 'bedrooms', 'bathrooms', 'lot', 'block']
            main_record = all_matches.get('florida_parcels', [{}])[0] if 'florida_parcels' in all_matches else {}

            for field in critical_fields:
                if not main_record.get(field):
                    summary['data_gaps'].append(field)

            summary_file = f'parcel_summary_{parcel_id}.json'
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            print(f"[SAVED] Summary report saved to: {summary_file}")

            return complete_parcel_data

        else:
            print(f"No data found for parcel {parcel_id} in {county}")
            print(f"Tried {len(alternative_formats)} different formats across {len(existing_tables)} tables")
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

    result = search_miami_dade_parcel_complete(parcel_id, county)

    if result:
        print(f"\n[SUCCESS] Found comprehensive data for parcel {parcel_id}")
        total_records = sum(len(matches) for matches in result.values())
        print(f"Total records across all tables: {total_records}")
    else:
        print(f"\n[FAILED] Could not locate parcel {parcel_id} in database")