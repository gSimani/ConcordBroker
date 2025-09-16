#!/usr/bin/env python3
"""
Test a specific property to see if owner name is working
"""

import asyncio
from supabase import create_client, Client

async def test_property_owner():
    """Test specific property owner data"""

    print("TESTING SPECIFIC PROPERTY OWNER DATA")
    print("=" * 50)

    # Supabase configuration
    supabase_url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Connected to Supabase")

        # 1. Get any property with data
        print("\n1. Getting sample property...")
        sample_response = supabase.table('florida_parcels').select('parcel_id, phy_addr1, phy_city, owner_name').limit(5).execute()

        if sample_response.data:
            print("Found sample properties:")
            for i, prop in enumerate(sample_response.data, 1):
                parcel_id = prop['parcel_id']
                address = prop.get('phy_addr1', 'No address')
                city = prop.get('phy_city', 'No city')
                owner_name = prop.get('owner_name', 'No owner')

                print(f"  {i}. {parcel_id} - {address}, {city} - Owner: '{owner_name}'")

            # Test with the first property
            test_property = sample_response.data[0]
            test_parcel_id = test_property['parcel_id']

            print(f"\n2. Testing property: {test_parcel_id}")

            # Simulate the exact query from usePropertyData.ts (line 61)
            ui_query_response = supabase.table('florida_parcels').select('*').eq('parcel_id', test_parcel_id).limit(1).execute()

            if ui_query_response.data:
                florida_parcel = ui_query_response.data[0]
                print("Property data retrieved successfully")

                # Simulate the mapping from usePropertyData.ts (lines 168-169)
                mapped_owner_name = florida_parcel.get('owner_name')

                print(f"Raw owner_name from DB: '{mapped_owner_name}'")
                print(f"Type: {type(mapped_owner_name)}")
                print(f"Is None: {mapped_owner_name is None}")
                print(f"Is empty string: {mapped_owner_name == ''}")

                # This is what gets passed to bcpaData (lines 168-169)
                bcpa_data = {
                    'owner_name': mapped_owner_name,
                    'own_name': mapped_owner_name,  # What UI components expect
                }

                print(f"\nData sent to UI components:")
                print(f"  bcpaData.owner_name: '{bcpa_data['owner_name']}'")
                print(f"  bcpaData.own_name: '{bcpa_data['own_name']}'")

                # Test what UI components will display
                ui_display_value = bcpa_data['own_name'] or 'Unknown'
                print(f"\nWhat UI will show: '{ui_display_value}'")

                if ui_display_value == 'Unknown':
                    print("ISSUE FOUND: UI will show 'Unknown' because owner_name is null/empty")

                    # Check if there are other fields with owner data
                    print("\nChecking other owner-related fields:")
                    for field_name, field_value in florida_parcel.items():
                        if 'own' in field_name.lower() and field_value:
                            print(f"  {field_name}: '{field_value}'")
                else:
                    print("SUCCESS: UI will show actual owner name")

        else:
            print("No properties found in database")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_property_owner())