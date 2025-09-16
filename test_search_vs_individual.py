#!/usr/bin/env python3
"""
Test difference between search results and individual property lookup
"""

import asyncio
from supabase import create_client, Client

async def test_search_vs_individual():
    """Test search results vs individual property lookup"""

    print("TESTING SEARCH VS INDIVIDUAL PROPERTY LOOKUP")
    print("=" * 60)

    # Supabase configuration
    supabase_url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Connected to Supabase")

        # Test parcel ID from the frontend console log
        test_parcel_id = '474128021200'

        print(f"\n1. TESTING INDIVIDUAL PROPERTY LOOKUP")
        print(f"Parcel ID: {test_parcel_id}")
        print("-" * 50)

        # Individual property lookup (same as usePropertyData.ts)
        individual_response = supabase.table('florida_parcels').select('*').eq('parcel_id', test_parcel_id).limit(1).execute()

        if individual_response.data:
            property_data = individual_response.data[0]
            print("Individual lookup SUCCESS")
            print(f"  parcel_id: {property_data.get('parcel_id')}")
            print(f"  owner_name: {property_data.get('owner_name')}")
            print(f"  phy_addr1: {property_data.get('phy_addr1')}")
            print(f"  phy_city: {property_data.get('phy_city')}")
            print(f"  just_value: {property_data.get('just_value')}")
            print(f"  Records has {len(property_data.keys())} total fields")
        else:
            print("Individual lookup FAILED - No data found")

        print(f"\n2. TESTING SEARCH RESULTS (simulating frontend search)")
        print("-" * 50)

        # Simulate the search that's happening in the frontend
        # Based on the service, it's searching with county=BROWARD, propertyType=Residential
        search_response = supabase.table('florida_parcels').select('*', count='exact').eq('county', 'BROWARD').limit(50).execute()

        if search_response.data:
            print(f"Search returned {len(search_response.data)} results")
            print(f"Total count: {search_response.count}")

            # Check if our test parcel is in the search results
            matching_property = None
            for prop in search_response.data:
                if prop.get('parcel_id') == test_parcel_id:
                    matching_property = prop
                    break

            if matching_property:
                print(f"\nFound matching property in search results:")
                print(f"  parcel_id: {matching_property.get('parcel_id')}")
                print(f"  owner_name: {matching_property.get('owner_name')}")
                print(f"  phy_addr1: {matching_property.get('phy_addr1')}")
                print(f"  phy_city: {matching_property.get('phy_city')}")
                print(f"  just_value: {matching_property.get('just_value')}")
                print(f"  Records has {len(matching_property.keys())} total fields")

                # Compare the two results
                print(f"\n3. COMPARISON:")
                print("-" * 50)
                if matching_property == property_data:
                    print("SUCCESS: Individual and search results are IDENTICAL")
                else:
                    print("ISSUE: Individual and search results are DIFFERENT")

                    # Show differences
                    individual_keys = set(property_data.keys())
                    search_keys = set(matching_property.keys())

                    if individual_keys != search_keys:
                        print(f"Different fields:")
                        print(f"  Individual has {len(individual_keys)} fields")
                        print(f"  Search has {len(search_keys)} fields")

                        only_in_individual = individual_keys - search_keys
                        only_in_search = search_keys - individual_keys

                        if only_in_individual:
                            print(f"  Only in individual: {only_in_individual}")
                        if only_in_search:
                            print(f"  Only in search: {only_in_search}")

                    # Check specific fields
                    important_fields = ['owner_name', 'phy_addr1', 'phy_city', 'just_value']
                    for field in important_fields:
                        individual_val = property_data.get(field)
                        search_val = matching_property.get(field)
                        if individual_val != search_val:
                            print(f"  {field}: Individual='{individual_val}' vs Search='{search_val}'")
            else:
                print(f"ISSUE: Parcel {test_parcel_id} NOT found in search results")

                # Show what the search results actually look like
                print("\nFirst 3 search results:")
                for i, prop in enumerate(search_response.data[:3], 1):
                    print(f"  {i}. {prop}")

        else:
            print("Search FAILED - No results returned")

        print(f"\n4. CHECKING TABLE STRUCTURE")
        print("-" * 50)

        # Let's see if there are multiple tables or views
        schema_query = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND (table_name ILIKE '%florida%' OR table_name ILIKE '%property%' OR table_name ILIKE '%parcel%')
        ORDER BY table_name;
        """

        # Can't run raw SQL with the Python client easily, so let's check our known table
        # Let's also see the exact structure by getting all field names
        structure_response = supabase.table('florida_parcels').select('*').limit(1).execute()
        if structure_response.data:
            sample_record = structure_response.data[0]
            print(f"florida_parcels table has {len(sample_record.keys())} columns:")
            for i, field_name in enumerate(sorted(sample_record.keys()), 1):
                field_value = sample_record.get(field_name)
                field_type = type(field_value).__name__
                print(f"  {i:2d}. {field_name} ({field_type})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_vs_individual())