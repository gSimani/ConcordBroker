#!/usr/bin/env python3
"""
Verify Core Property Tab field mappings and database connections
Tests all fields shown in the reference implementation
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("VITE_SUPABASE_URL", "")
key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

def test_property_fields(parcel_id="1078130000370"):
    """Test all required fields for Core Property Info tab"""

    print(f"Testing property fields for parcel_id: {parcel_id}")
    print("=" * 60)

    # Fetch property data
    try:
        response = supabase.table('florida_parcels')\
            .select("*")\
            .eq('parcel_id', parcel_id)\
            .single()\
            .execute()

        if response.data:
            property_data = response.data
            print("[OK] Successfully fetched property data")

            # Define required fields based on UI requirements
            required_fields = {
                # Property Information
                'parcel_id': 'Folio',
                'subdivision': 'Sub-Division',
                'phy_addr1': 'Property Address',
                'phy_city': 'Property City',
                'phy_zipcd': 'Property Zip',
                'owner_name': 'Owner Name',
                'owner_addr1': 'Mailing Address',
                'owner_city': 'Owner City',
                'owner_state': 'Owner State',
                'owner_zip': 'Owner Zip',

                # Property Characteristics
                'zoning': 'Zoning/PA Zone',
                'property_use': 'Primary Land Use Code',
                'dor_uc': 'Land Use Code',
                'bedrooms': 'Bedrooms',
                'bathrooms': 'Bathrooms',
                'half_bathrooms': 'Half Bathrooms',
                'stories': 'Floors/Stories',
                'units': 'Living Units',
                'year_built': 'Year Built',

                # Area Information
                'total_living_area': 'Living Area',
                'adjusted_area': 'Adjusted Area',
                'land_sqft': 'Lot Size',

                # Values
                'land_value': 'Land Value',
                'building_value': 'Building Value',
                'just_value': 'Market Value',
                'assessed_value': 'Assessed Value',
                'taxable_value': 'Taxable Value',

                # Additional fields
                'latitude': 'Latitude',
                'longitude': 'Longitude',
                'county': 'County',
                'year': 'Assessment Year'
            }

            print("\nField Mapping Verification:")
            print("-" * 60)

            missing_fields = []
            present_fields = []

            for db_field, ui_label in required_fields.items():
                if db_field in property_data:
                    value = property_data[db_field]
                    status = "[OK]" if value is not None else "[WARN]"
                    present_fields.append(db_field)
                    print(f"{status} {ui_label:30} ({db_field:25}): {str(value)[:50]}")
                else:
                    missing_fields.append(db_field)
                    print(f"[ERROR] {ui_label:30} ({db_field:25}): MISSING IN DATABASE")

            # Check for additional NAL fields that might be missing
            additional_nal_fields = [
                'pa_zone',           # PA Primary Zone
                'land_use_desc',     # Land Use Description
                'imp_qual',          # Improvement Quality
                'const_class',       # Construction Class
                'extra_feature_value', # Extra Feature Value
                'act_yr_blt',        # Legacy year built field
                'tot_lvg_area',      # Legacy total living area
                'lnd_sqfoot'         # Legacy land sqft
            ]

            print("\nAdditional NAL Fields Check:")
            print("-" * 60)
            for field in additional_nal_fields:
                if field in property_data:
                    print(f"[OK] {field}: {property_data[field]}")
                else:
                    print(f"[WARN] {field}: Not in current schema")

            # Summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Total Required Fields: {len(required_fields)}")
            print(f"Present Fields: {len(present_fields)} ({len(present_fields)/len(required_fields)*100:.1f}%)")
            print(f"Missing Fields: {len(missing_fields)} ({len(missing_fields)/len(required_fields)*100:.1f}%)")

            if missing_fields:
                print(f"\n[WARN] Missing fields that need to be added to database:")
                for field in missing_fields:
                    print(f"  - {field}")
            else:
                print("\n[OK] All required fields are present in the database!")

            # Test sales history connection
            print("\n" + "=" * 60)
            print("SALES HISTORY CONNECTION TEST")
            print("=" * 60)

            try:
                sales_response = supabase.table('florida_sales')\
                    .select("*")\
                    .eq('parcel_id', parcel_id)\
                    .order('sale_date', desc=True)\
                    .limit(5)\
                    .execute()

                if sales_response.data and len(sales_response.data) > 0:
                    print(f"[OK] Found {len(sales_response.data)} sales records")
                    for sale in sales_response.data:
                        print(f"  - {sale.get('sale_date')}: ${sale.get('sale_price', 0):,.0f}")
                else:
                    print("[INFO] No sales history found (this is normal for many properties)")
            except Exception as e:
                print(f"[ERROR] Error fetching sales history: {e}")

            # Return results for programmatic use
            return {
                'success': True,
                'total_fields': len(required_fields),
                'present_fields': len(present_fields),
                'missing_fields': missing_fields,
                'data': property_data
            }

        else:
            print(f"[ERROR] No property found with parcel_id: {parcel_id}")
            return {'success': False, 'error': 'Property not found'}

    except Exception as e:
        print(f"[ERROR] Error fetching property data: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    # Test with the specific property
    result = test_property_fields("1078130000370")

    # Save results to file for reference
    with open('core_property_field_test_results.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)

    print("\n[OK] Test results saved to core_property_field_test_results.json")