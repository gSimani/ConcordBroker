#!/usr/bin/env python3
"""
Verify owner name data in Supabase using correct connection
"""

import asyncio
import json
from supabase import create_client, Client
import sys

async def verify_owner_data():
    """Verify owner name data using Supabase client"""

    print("VERIFYING OWNER NAME DATA IN SUPABASE")
    print("=" * 60)

    # Supabase configuration from .env
    supabase_url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✓ Connected to Supabase")

        # 1. Check table schema for florida_parcels
        print("\n1. CHECKING FLORIDA_PARCELS TABLE STRUCTURE")
        print("-" * 50)

        # Get a sample record to see what columns exist
        response = supabase.table('florida_parcels').select('*').limit(1).execute()

        if response.data and len(response.data) > 0:
            sample_record = response.data[0]
            print("✓ florida_parcels table exists")
            print("Columns found:")
            owner_related_columns = []
            for col in sample_record.keys():
                print(f"  {col}")
                if 'own' in col.lower() or 'owner' in col.lower():
                    owner_related_columns.append(col)

            print(f"\nOwner-related columns: {owner_related_columns}")
        else:
            print("❌ No data found in florida_parcels table")
            return

        # 2. Check owner name field data
        print("\n2. CHECKING OWNER NAME DATA")
        print("-" * 50)

        # Test different owner field names
        owner_fields_to_check = ['owner_name', 'own_name', 'ownr_name']

        working_owner_field = None
        for field in owner_fields_to_check:
            if field in sample_record:
                print(f"✓ Found field: {field}")

                # Check how many records have non-null values
                count_response = supabase.table('florida_parcels').select(field, count='exact').neq(field, None).execute()

                print(f"  Non-null records: {count_response.count:,}")

                # Get sample values
                sample_response = supabase.table('florida_parcels').select(f'parcel_id, county, {field}').neq(field, None).limit(5).execute()

                if sample_response.data:
                    print(f"  Sample values:")
                    for record in sample_response.data:
                        print(f"    {record['parcel_id']} ({record['county']}): {record[field]}")
                    working_owner_field = field
                break
            else:
                print(f"❌ Field not found: {field}")

        # 3. Test a specific property that should have owner data
        print("\n3. TESTING SPECIFIC PROPERTY")
        print("-" * 50)

        # Look for a property with owner data
        if working_owner_field:
            test_response = supabase.table('florida_parcels').select('*').neq(working_owner_field, None).limit(3).execute()

            if test_response.data:
                for i, property_data in enumerate(test_response.data, 1):
                    parcel_id = property_data['parcel_id']
                    owner_name = property_data.get(working_owner_field, 'Not found')
                    address = property_data.get('phy_addr1', 'No address')
                    city = property_data.get('phy_city', 'No city')

                    print(f"Test Property {i}:")
                    print(f"  Parcel ID: {parcel_id}")
                    print(f"  Address: {address}, {city}")
                    print(f"  Owner ({working_owner_field}): {owner_name}")
                    print()

        # 4. Check what the UI hook is actually receiving
        print("\n4. SIMULATING UI DATA FETCH")
        print("-" * 50)

        if test_response.data:
            test_property = test_response.data[0]
            parcel_id = test_property['parcel_id']

            print(f"Fetching data for parcel: {parcel_id}")

            # Simulate the same query as usePropertyData.ts
            ui_response = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).limit(1).execute()

            if ui_response.data:
                florida_parcel = ui_response.data[0]
                print("✓ Found florida_parcel data")

                # Show how the hook would map this data
                mapped_owner_name = florida_parcel.get('owner_name')  # Line 168 in hook
                print(f"  florida_parcel.owner_name: {mapped_owner_name}")

                # This is what gets passed to UI components
                ui_data = {
                    'owner_name': mapped_owner_name,
                    'own_name': mapped_owner_name,  # Line 169 in hook - what UI expects
                }

                print("  Data passed to UI components:")
                print(f"    owner_name: {ui_data['owner_name']}")
                print(f"    own_name: {ui_data['own_name']}")

                # Check if this is null/empty
                if not mapped_owner_name or mapped_owner_name.strip() == '':
                    print("  ❌ ISSUE: owner_name is null/empty!")
                    print("  This is why owner names are not showing in UI")

                    # Check what other owner fields might exist
                    print("  Checking alternative owner fields:")
                    for field in florida_parcel.keys():
                        if 'own' in field.lower() and florida_parcel[field]:
                            print(f"    {field}: {florida_parcel[field]}")
                else:
                    print("  ✓ Owner name data looks good")

        # 5. Check total statistics
        print("\n5. OVERALL STATISTICS")
        print("-" * 50)

        total_response = supabase.table('florida_parcels').select('parcel_id', count='exact').execute()
        print(f"Total properties in database: {total_response.count:,}")

        if working_owner_field:
            owner_response = supabase.table('florida_parcels').select('parcel_id', count='exact').neq(working_owner_field, None).execute()
            percentage = (owner_response.count / total_response.count) * 100 if total_response.count > 0 else 0
            print(f"Properties with owner names: {owner_response.count:,} ({percentage:.1f}%)")

        print("\n✓ Verification completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_owner_data())