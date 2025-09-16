#!/usr/bin/env python3
"""
Populate sample property data into Supabase database
"""

import os
from supabase import create_client, Client
from datetime import datetime, timedelta
import random

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'your-service-key')

def populate_sample_data():
    """Populate sample data into the database"""
    
    print("[INFO] Starting sample data population...")
    print(f"[INFO] Target: {SUPABASE_URL}")
    
    # Initialize Supabase client - use anon key for now
    SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    try:
        # Sample properties data
        sample_properties = [
            {
                'parcel_id': '064210010010',
                'phy_addr1': '1234 SAMPLE ST',
                'phy_city': 'FORT LAUDERDALE',
                'phy_state': 'FL',
                'phy_zipcd': '33301',
                'owner_name': 'SMITH JOHN & MARY',
                'owner_addr1': '1234 SAMPLE ST',
                'owner_city': 'FORT LAUDERDALE',
                'owner_state': 'FL',
                'owner_zip': '33301',
                'property_use': '001',
                'property_use_desc': 'Single Family Residential',
                'year_built': 1987,
                'total_living_area': 2450,
                'bedrooms': 4,
                'bathrooms': 3,
                'land_sqft': 7500,
                'land_acres': 0.17,
                'just_value': 485000,
                'assessed_value': 465000,
                'taxable_value': 440000,
                'land_value': 185000,
                'building_value': 300000,
                'sale_date': '2024-08-15',
                'sale_price': 485000,
                'is_redacted': False,
                'county': 'BROWARD',
                'subdivision': 'SAMPLE ESTATES',
                'lot': '15',
                'block': 'A',
                'homestead_exemption': True,
                'data_source': 'Sample Data'
            },
            {
                'parcel_id': '064210010011',
                'phy_addr1': '1236 SAMPLE ST',
                'phy_city': 'FORT LAUDERDALE',
                'phy_state': 'FL',
                'phy_zipcd': '33301',
                'owner_name': 'JOHNSON ROBERT',
                'owner_addr1': '1236 SAMPLE ST',
                'owner_city': 'FORT LAUDERDALE',
                'owner_state': 'FL',
                'owner_zip': '33301',
                'property_use': '001',
                'property_use_desc': 'Single Family Residential',
                'year_built': 1992,
                'total_living_area': 1875,
                'bedrooms': 3,
                'bathrooms': 2,
                'land_sqft': 6800,
                'land_acres': 0.16,
                'just_value': 375000,
                'assessed_value': 360000,
                'taxable_value': 340000,
                'land_value': 150000,
                'building_value': 225000,
                'sale_date': '2023-03-22',
                'sale_price': 380000,
                'is_redacted': False,
                'county': 'BROWARD',
                'subdivision': 'SAMPLE ESTATES',
                'lot': '16',
                'block': 'A',
                'homestead_exemption': True,
                'data_source': 'Sample Data'
            },
            {
                'parcel_id': '064210015020',
                'phy_addr1': '5678 EXAMPLE AVE',
                'phy_city': 'PEMBROKE PINES',
                'phy_state': 'FL',
                'phy_zipcd': '33028',
                'owner_name': 'SUNSHINE INVESTMENTS CORP',
                'owner_addr1': 'PO BOX 12345',
                'owner_city': 'MIAMI',
                'owner_state': 'FL',
                'owner_zip': '33101',
                'property_use': '101',
                'property_use_desc': 'Commercial Retail',
                'year_built': 2003,
                'total_living_area': 3200,
                'bedrooms': 0,
                'bathrooms': 2,
                'land_sqft': 12000,
                'land_acres': 0.28,
                'just_value': 625000,
                'assessed_value': 600000,
                'taxable_value': 580000,
                'land_value': 325000,
                'building_value': 300000,
                'sale_date': '2024-11-20',
                'sale_price': 675000,
                'is_redacted': False,
                'county': 'BROWARD',
                'subdivision': 'PEMBROKE COMMERCIAL CENTER',
                'lot': '5',
                'block': 'C',
                'homestead_exemption': False,
                'data_source': 'Sample Data'
            }
        ]
        
        # Check if florida_parcels table exists and insert data
        print("\n[1] Populating florida_parcels table...")
        for prop in sample_properties:
            try:
                # Check if record exists
                existing = supabase.table('florida_parcels').select('parcel_id').eq('parcel_id', prop['parcel_id']).execute()
                
                if existing.data:
                    # Update existing record
                    result = supabase.table('florida_parcels').update(prop).eq('parcel_id', prop['parcel_id']).execute()
                    print(f"  ✓ Updated: {prop['parcel_id']} - {prop['phy_addr1']}")
                else:
                    # Insert new record
                    result = supabase.table('florida_parcels').insert(prop).execute()
                    print(f"  ✓ Inserted: {prop['parcel_id']} - {prop['phy_addr1']}")
                    
            except Exception as e:
                print(f"  ✗ Error with {prop['parcel_id']}: {str(e)[:100]}")
        
        # Sample sales history data
        print("\n[2] Populating property_sales_history table...")
        sample_sales = [
            {
                'parcel_id': '064210010010',
                'sale_date': '2024-08-15',
                'sale_price': 485000,
                'sale_type': 'Warranty Deed',
                'sale_qualification': 'Qualified',
                'book': '12345',
                'page': '678',
                'book_page': '12345/678',
                'cin': '2024000123456',
                'grantor_name': 'BROWN ROBERT',
                'grantee_name': 'SMITH JOHN & MARY',
                'is_arms_length': True,
                'is_qualified_sale': True,
                'subdivision_name': 'SAMPLE ESTATES',
                'property_address': '1234 SAMPLE ST',
                'city': 'FORT LAUDERDALE',
                'zip_code': '33301'
            },
            {
                'parcel_id': '064210010010',
                'sale_date': '2021-03-22',
                'sale_price': 380000,
                'sale_type': 'Warranty Deed',
                'sale_qualification': 'Qualified',
                'book': '11890',
                'page': '456',
                'book_page': '11890/456',
                'cin': '2021000098765',
                'grantor_name': 'DAVIS MICHAEL',
                'grantee_name': 'BROWN ROBERT',
                'is_arms_length': True,
                'is_qualified_sale': True,
                'subdivision_name': 'SAMPLE ESTATES',
                'property_address': '1234 SAMPLE ST',
                'city': 'FORT LAUDERDALE',
                'zip_code': '33301'
            },
            {
                'parcel_id': '064210010010',
                'sale_date': '2018-11-10',
                'sale_price': 320000,
                'sale_type': 'Warranty Deed',
                'sale_qualification': 'Qualified',
                'book': '11234',
                'page': '789',
                'book_page': '11234/789',
                'cin': '2018000054321',
                'grantor_name': 'ORIGINAL OWNER',
                'grantee_name': 'DAVIS MICHAEL',
                'is_arms_length': True,
                'is_qualified_sale': True,
                'subdivision_name': 'SAMPLE ESTATES',
                'property_address': '1234 SAMPLE ST',
                'city': 'FORT LAUDERDALE',
                'zip_code': '33301'
            }
        ]
        
        for sale in sample_sales:
            try:
                # Try to insert into property_sales_history if table exists
                result = supabase.table('property_sales_history').insert(sale).execute()
                print(f"  ✓ Inserted sale: {sale['sale_date']} - ${sale['sale_price']:,.0f}")
            except Exception as e:
                if 'relation "public.property_sales_history" does not exist' in str(e):
                    print("  ⚠ property_sales_history table does not exist - skipping sales data")
                    break
                else:
                    print(f"  ✗ Error inserting sale: {str(e)[:100]}")
        
        # Verify the data
        print("\n[3] Verifying inserted data...")
        try:
            result = supabase.table('florida_parcels').select('parcel_id, phy_addr1, owner_name, taxable_value').limit(5).execute()
            if result.data:
                print(f"[SUCCESS] Found {len(result.data)} properties in database:")
                for prop in result.data:
                    print(f"  - {prop['parcel_id']}: {prop['phy_addr1']} (Owner: {prop['owner_name']}, Value: ${prop.get('taxable_value', 0):,.0f})")
            else:
                print("[WARNING] No data found after insertion")
        except Exception as e:
            print(f"[ERROR] Could not verify data: {str(e)[:100]}")
        
        print("\n[SUCCESS] Sample data population completed!")
        print("\nYou can now navigate to properties like:")
        print("  - http://localhost:5174/property/064210010010")
        print("  - http://localhost:5174/property/064210010011")
        print("  - http://localhost:5174/property/064210015020")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to populate sample data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    populate_sample_data()