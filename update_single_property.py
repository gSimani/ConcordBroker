"""
Update a single property with complete data from NAL file
"""

import os
import csv
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}

def update_property(parcel_id):
    print(f"Updating property {parcel_id} with complete data...")
    
    # Find the property in NAL file
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('PARCEL_ID', '').strip() == parcel_id:
                print("Found property in NAL file!")
                
                # Show raw values
                print("\nRAW VALUES FROM NAL FILE:")
                print(f"  JV (Just Value): {row.get('JV')}")
                print(f"  AV_SD (Assessed): {row.get('AV_SD')}")
                print(f"  TV_SD (Taxable): {row.get('TV_SD')}")
                print(f"  LND_VAL (Land): {row.get('LND_VAL')}")
                print(f"  TOT_LVG_AREA: {row.get('TOT_LVG_AREA')}")
                print(f"  ACT_YR_BLT: {row.get('ACT_YR_BLT')}")
                print(f"  NO_RES_UNTS: {row.get('NO_RES_UNTS')}")
                print(f"  SALE_PRC1: {row.get('SALE_PRC1')}")
                print(f"  SALE_YR1: {row.get('SALE_YR1')}")
                
                # Build update data
                update_data = {
                    'parcel_id': parcel_id
                }
                
                # Add values if they exist and are not empty
                if row.get('JV') and row['JV'].strip():
                    update_data['just_value'] = int(float(row['JV']))
                    
                if row.get('AV_SD') and row['AV_SD'].strip():
                    update_data['assessed_value'] = int(float(row['AV_SD']))
                    
                if row.get('TV_SD') and row['TV_SD'].strip():
                    update_data['taxable_value'] = int(float(row['TV_SD']))
                    
                if row.get('LND_VAL') and row['LND_VAL'].strip():
                    update_data['land_value'] = int(float(row['LND_VAL']))
                    
                    # Calculate building value
                    if 'just_value' in update_data:
                        update_data['building_value'] = update_data['just_value'] - update_data['land_value']
                
                if row.get('TOT_LVG_AREA') and row['TOT_LVG_AREA'].strip():
                    update_data['total_living_area'] = int(float(row['TOT_LVG_AREA']))
                    
                if row.get('ACT_YR_BLT') and row['ACT_YR_BLT'].strip():
                    year = int(float(row['ACT_YR_BLT']))
                    if year > 1800:  # Valid year
                        update_data['year_built'] = year
                        
                if row.get('NO_RES_UNTS') and row['NO_RES_UNTS'].strip():
                    update_data['units'] = int(float(row['NO_RES_UNTS']))
                    
                if row.get('LND_SQFOOT') and row['LND_SQFOOT'].strip():
                    update_data['land_sqft'] = int(float(row['LND_SQFOOT']))
                    
                if row.get('SALE_PRC1') and row['SALE_PRC1'].strip():
                    price = int(float(row['SALE_PRC1']))
                    if price > 0:
                        update_data['sale_price'] = price
                        
                if row.get('SALE_YR1') and row['SALE_YR1'].strip():
                    year = int(float(row['SALE_YR1']))
                    if year > 1900:
                        month = row.get('SALE_MO1', '01').zfill(2)
                        update_data['sale_date'] = f"{year}-{month}-01"
                
                print("\nUPDATE DATA:")
                for key, value in update_data.items():
                    if key != 'parcel_id':
                        print(f"  {key}: {value}")
                
                # Update in Supabase
                url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
                response = requests.patch(url, json=update_data, headers=headers)
                
                if response.status_code in [200, 204]:
                    print("\n✓ Successfully updated property!")
                    
                    # Verify the update
                    print("\nVerifying update...")
                    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
                    response = requests.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            prop = data[0]
                            print("\nCURRENT DATABASE VALUES:")
                            print(f"  Just Value: ${prop.get('just_value', 'N/A')}")
                            print(f"  Assessed Value: ${prop.get('assessed_value', 'N/A')}")
                            print(f"  Taxable Value: ${prop.get('taxable_value', 'N/A')}")
                            print(f"  Land Value: ${prop.get('land_value', 'N/A')}")
                            print(f"  Building Value: ${prop.get('building_value', 'N/A')}")
                            print(f"  Year Built: {prop.get('year_built', 'N/A')}")
                            print(f"  Living Area: {prop.get('total_living_area', 'N/A')} sq ft")
                else:
                    print(f"\n✗ Update failed: {response.status_code}")
                    print(response.text[:500])
                
                return
        
        print(f"Property {parcel_id} not found in NAL file")

if __name__ == "__main__":
    # Update the specific property
    update_property("504231242730")