"""
Test Supabase data directly to see what fields have values
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps/api'))
from supabase_client import get_supabase_client

# Load environment variables
load_dotenv('apps/web/.env')

supabase = get_supabase_client()

print("Testing Supabase florida_parcels table...")
print("=" * 60)

try:
    # Get a sample of properties with non-null values
    result = supabase.table('florida_parcels').select('*').not_.is_('jv', 'null').limit(5).execute()
    
    if result.data:
        print(f"Found {len(result.data)} properties with jv (just value) data:")
        for prop in result.data:
            print(f"\nParcel ID: {prop.get('parcel_id')}")
            print(f"  Address: {prop.get('phy_addr1')}, {prop.get('phy_city')}")
            print(f"  Owner: {prop.get('own_name')}")
            print(f"  Just Value: ${prop.get('jv', 0):,.0f}")
            print(f"  Taxable Value: ${prop.get('tv_sd', 0):,.0f}")
            print(f"  DOR Code: {prop.get('dor_uc')}")
            print(f"  Land SqFt: {prop.get('lnd_sqfoot')}")
            print(f"  Year Built: {prop.get('act_yr_blt')}")
    else:
        print("No properties found with jv values")
        
    # Check what columns actually have data
    print("\n" + "=" * 60)
    print("Checking first 10 properties to see what fields have data:")
    
    result = supabase.table('florida_parcels').select('*').limit(10).execute()
    
    if result.data:
        # Count non-null fields
        field_counts = {}
        for prop in result.data:
            for key, value in prop.items():
                if value is not None and value != '' and value != 0:
                    field_counts[key] = field_counts.get(key, 0) + 1
        
        print("\nFields with data (out of 10 properties):")
        for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {field}: {count}/10 properties have data")
            
        # Show sample property with most complete data
        print("\n" + "=" * 60)
        print("Sample property data:")
        if result.data[0]:
            for key, value in result.data[0].items():
                if value is not None and value != '' and value != 0:
                    print(f"  {key}: {value}")
                    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()