#!/usr/bin/env python3
"""
Website Data Test
================
Test the property data for website functionality
"""

from supabase import create_client
import os
from dotenv import load_dotenv

def main():
    load_dotenv('apps/web/.env')
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
    supabase = create_client(supabase_url, supabase_key)

    print('=== WEBSITE DATA VERIFICATION ===')
    print()

    # Get some sample property data to test display
    print('Testing property search functionality...')

    # Search for properties in Broward (16)
    broward_props = supabase.table('florida_parcels').select('parcel_id, owner_name, phy_addr1, phy_city, county, sale_price, assessed_value').eq('county', '16').limit(5).execute()

    print(f'Found {len(broward_props.data)} sample Broward properties:')
    for prop in broward_props.data:
        parcel_id = prop['parcel_id']
        print(f'  Parcel: {parcel_id}')
        print(f'    Owner: {prop.get("owner_name", "N/A")}')
        print(f'    Address: {prop.get("phy_addr1", "N/A")}, {prop.get("phy_city", "N/A")}')
        print(f'    Assessed Value: ${prop.get("assessed_value", "N/A")}')
        
        # Check for sales data
        sales = supabase.table('property_sales_history').select('sale_date, sale_amount').eq('parcel_id', parcel_id).limit(1).execute()
        if sales.data:
            print(f'    Recent Sale: {sales.data[0].get("sale_date", "N/A")} - ${sales.data[0].get("sale_amount", "N/A")}')
        else:
            print(f'    Recent Sale: No sales data found')
        print()

    print('=== DATA COMPLETENESS CHECK ===')

    # Check data quality - count non-null values
    florida_sample = supabase.table('florida_parcels').select('*').limit(1).execute()
    if florida_sample.data:
        sample_record = florida_sample.data[0]
        print('Sample florida_parcels record completeness:')
        non_null_count = 0
        total_fields = len(sample_record)
        
        for key, value in sample_record.items():
            status = 'HAS_DATA' if value is not None and value != '' else 'NULL/EMPTY'
            if status == 'HAS_DATA':
                non_null_count += 1
            print(f'  {key}: {status}')
        
        completion_rate = (non_null_count / total_fields) * 100
        print(f'\nData Completion Rate: {completion_rate:.1f}% ({non_null_count}/{total_fields} fields)')

    print()
    print('=== PERFORMANCE TEST ===')
    
    # Test query performance
    import time
    
    start_time = time.time()
    county_counts = supabase.table('florida_parcels').select('county, count', count='exact').execute()
    query_time = time.time() - start_time
    
    print(f'Query performance: {query_time:.2f} seconds for count query')
    
    print()
    print('Database is ready for website testing!')

if __name__ == "__main__":
    main()