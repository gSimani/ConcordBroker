import os
import requests
import csv
from dotenv import load_dotenv

load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}

# Update the properties table with correct data from florida_parcels
parcel_id = '504231242720'

print(f'Updating property data for parcel: {parcel_id}')
print('=' * 60)

# First get the correct data from florida_parcels
url = f'{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}'
response = requests.get(url, headers=headers)

if response.status_code == 200:
    florida_data = response.json()
    if florida_data:
        florida_parcel = florida_data[0]
        
        print('\nCurrent florida_parcels data:')
        print(f'  Owner: {florida_parcel["owner_name"]}')
        print(f'  Address: {florida_parcel["phy_addr1"]}, {florida_parcel["phy_city"]}, {florida_parcel["phy_state"]} {florida_parcel["phy_zipcd"]}')
        
        # Update properties table with correct owner
        update_data = {
            'owner_name': florida_parcel['owner_name'],
            'zip_code': florida_parcel['phy_zipcd']  # Also fix zip code (33312 not 33021)
        }
        
        url = f'{SUPABASE_URL}/rest/v1/properties?parcel_id=eq.{parcel_id}'
        response = requests.patch(url, json=update_data, headers=headers)
        
        if response.status_code in [200, 204]:
            print('\n[OK] Updated properties table with correct data:')
            print(f'  Owner: {update_data["owner_name"]}')
            print(f'  Zip: {update_data["zip_code"]}')
        else:
            print(f'[X] Error updating: {response.status_code} - {response.text}')
    else:
        print('No florida_parcels data found')
else:
    print(f'Error fetching florida_parcels: {response.status_code}')

# Also check if we need to load real sales data from SDF file
print('\n' + '=' * 60)
print('Checking for real sales data in SDF file...')

if os.path.exists('SDF16P202501.csv'):
    with open('SDF16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        found_sales = []
        for row in reader:
            if row.get('PARCEL_ID', '').strip() == parcel_id:
                sale_price_str = row.get('SALE_PRC', '0').strip()
                sale_year_str = row.get('SALE_YR', '0').strip()
                sale_month_str = row.get('SALE_MO', '0').strip()
                
                try:
                    sale_price = int(float(sale_price_str))
                    sale_year = int(float(sale_year_str))
                    sale_month = int(float(sale_month_str))
                    
                    if sale_price > 0 and sale_year > 1900:
                        found_sales.append({
                            'price': sale_price,
                            'year': sale_year,
                            'month': sale_month,
                            'qual_code': row.get('QUAL_CD', '').strip(),
                            'or_book': row.get('OR_BOOK', '').strip(),
                            'or_page': row.get('OR_PAGE', '').strip()
                        })
                except:
                    pass
        
        if found_sales:
            print(f'\nFound {len(found_sales)} real sales for this property:')
            for i, sale in enumerate(found_sales[:5]):  # Show first 5
                print(f'  Sale {i+1}: ${sale["price"]:,} in {sale["year"]}/{sale["month"]:02d} (Qual: {sale["qual_code"]}, Book: {sale["or_book"]}, Page: {sale["or_page"]})')
            
            # Update the most recent sale in properties table
            if found_sales:
                most_recent = max(found_sales, key=lambda x: x['year'] * 100 + x['month'])
                sale_date = f"{most_recent['year']}-{most_recent['month']:02d}-01"
                
                update_data = {
                    'last_sale_date': sale_date,
                    'last_sale_price': float(most_recent['price'])
                }
                
                url = f'{SUPABASE_URL}/rest/v1/properties?parcel_id=eq.{parcel_id}'
                response = requests.patch(url, json=update_data, headers=headers)
                
                if response.status_code in [200, 204]:
                    print(f'\n[OK] Updated last sale to: ${most_recent["price"]:,} on {sale_date}')
                else:
                    print(f'[X] Error updating sale: {response.status_code}')
                    
            # Also insert these sales into property_sales_history if not already there
            print('\nInserting sales into property_sales_history...')
            for sale in found_sales:
                sale_date = f"{sale['year']}-{sale['month']:02d}-01"
                
                # Check if this sale already exists
                url = f'{SUPABASE_URL}/rest/v1/property_sales_history?parcel_id=eq.{parcel_id}&sale_date=eq.{sale_date}'
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200 and not response.json():
                    # Insert the sale
                    sale_data = {
                        'parcel_id': parcel_id,
                        'sale_date': sale_date,
                        'sale_price': float(sale['price']),
                        'sale_year': sale['year'],
                        'sale_month': sale['month'],
                        'qual_code': sale['qual_code'] or None,
                        'or_book': sale['or_book'] or None,
                        'or_page': sale['or_page'] or None,
                        'data_source': 'SDF'
                    }
                    
                    url = f'{SUPABASE_URL}/rest/v1/property_sales_history'
                    response = requests.post(url, json=sale_data, headers=headers)
                    
                    if response.status_code in [200, 201, 204]:
                        print(f'  [OK] Inserted sale from {sale_date}')
                    else:
                        print(f'  [X] Error inserting sale: {response.status_code}')
                        
        else:
            print('No sales found in SDF file for this parcel')
else:
    print('SDF file not found')

print('\nData update complete!')