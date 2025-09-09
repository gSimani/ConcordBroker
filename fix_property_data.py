"""
Fix property data display issue by checking and updating property 504231242730
with sales and exemption data from CSV files
"""

import os
import csv
import json
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

def check_property_current_data():
    """Check what data currently exists for property 504231242730"""
    print("\n1. CHECKING CURRENT PROPERTY DATA")
    print("=" * 60)
    
    parcel_id = '504231242730'
    
    # Check florida_parcels table
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            prop = data[0]
            print(f"   Property found in florida_parcels:")
            print(f"   Address: {prop.get('phy_addr1', 'N/A')}")
            print(f"   Owner: {prop.get('owner_name', 'N/A')}")
            print(f"   Just Value: ${prop.get('just_value', 0):,}")
            print(f"   Sale Price: ${prop.get('sale_price', 0) or 0:,}")
            print(f"   Sale Date: {prop.get('sale_date', 'N/A')}")
            print(f"   Homestead: {prop.get('homestead_exemption', 'N/A')}")
            print(f"   Year Built: {prop.get('year_built', 'N/A')}")
            print(f"   Living Area: {prop.get('total_living_area', 'N/A')}")
            print(f"   Bedrooms: {prop.get('bedrooms', 'N/A')}")
            print(f"   Bathrooms: {prop.get('bathrooms', 'N/A')}")
            return prop
        else:
            print(f"   Property {parcel_id} NOT found in database!")
            return None
    else:
        print(f"   Error checking property: {response.status_code}")
        return None

def check_sdf_sales_table():
    """Check if fl_sdf_sales table exists and has data"""
    print("\n2. CHECKING FL_SDF_SALES TABLE")
    print("=" * 60)
    
    parcel_id = '504231242730'
    
    url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales?parcel_id=eq.{parcel_id}&order=sale_date.desc"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"   Found {len(data)} sales in fl_sdf_sales table")
            for sale in data[:3]:  # Show first 3
                print(f"   - ${sale.get('sale_price', 0):,} on {sale.get('sale_date', 'N/A')}")
        else:
            print("   No sales found in fl_sdf_sales for this property")
        return data
    elif response.status_code == 404:
        print("   fl_sdf_sales table does not exist!")
        return None
    else:
        print(f"   Error checking sales table: {response.status_code}")
        return None

def find_sales_in_sdf_file():
    """Find sales for property 504231242730 in SDF file"""
    print("\n3. SEARCHING SDF FILE FOR SALES")
    print("=" * 60)
    
    parcel_id = '504231242730'
    sales = []
    
    sdf_file = 'SDF16P202501.csv'
    if not os.path.exists(sdf_file):
        print(f"   SDF file not found: {sdf_file}")
        return []
    
    with open(sdf_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('PARCEL_ID', '').strip() == parcel_id:
                try:
                    sale_price = int(float(row.get('SALE_PRC', 0) or 0))
                    sale_year = int(float(row.get('SALE_YR', 0) or 0))
                    sale_month = int(float(row.get('SALE_MO', 0) or 0))
                    
                    if sale_price > 0 and sale_year > 1900:
                        sale_date = f"{sale_year}-{str(sale_month).zfill(2)}-01"
                        
                        sales.append({
                            'parcel_id': parcel_id,
                            'sale_price': sale_price,
                            'sale_date': sale_date,
                            'sale_year': sale_year,
                            'sale_month': sale_month,
                            'deed_type': row.get('DEED_TYPE', ''),
                            'or_book': row.get('OR_BOOK', ''),
                            'or_page': row.get('OR_PAGE', ''),
                            'qual_code': row.get('QUAL_CODE', ''),
                            'vi_code': row.get('VI_CODE', '')
                        })
                        
                        print(f"   Found sale: ${sale_price:,} on {sale_date}")
                        print(f"     Deed: {row.get('DEED_TYPE', 'N/A')}")
                        print(f"     Book/Page: {row.get('OR_BOOK', '')}/{row.get('OR_PAGE', '')}")
                except Exception as e:
                    continue
    
    if not sales:
        print(f"   No sales found for parcel {parcel_id} in SDF file")
    else:
        print(f"\n   Total sales found: {len(sales)}")
        # Sort by date, most recent first
        sales.sort(key=lambda x: x['sale_year'], reverse=True)
    
    return sales

def find_exemptions_in_nal_file():
    """Find exemption data in NAL file"""
    print("\n4. SEARCHING NAL FILE FOR EXEMPTIONS")
    print("=" * 60)
    
    parcel_id = '504231242730'
    
    nal_file = 'NAL16P202501.csv'
    if not os.path.exists(nal_file):
        print(f"   NAL file not found: {nal_file}")
        return None
    
    with open(nal_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('PARCEL_ID', '').strip() == parcel_id:
                exemptions = []
                homestead = False
                
                # Check all exemption fields
                for i in range(1, 10):
                    exmpt_field = f'EXMPT_{str(i).zfill(2)}'
                    if exmpt_field in row and row[exmpt_field]:
                        exemptions.append(row[exmpt_field])
                        if row[exmpt_field] in ['HS', 'HX', 'HW']:  # Homestead codes
                            homestead = True
                
                print(f"   Found property in NAL file")
                print(f"   Exemptions: {', '.join(exemptions) if exemptions else 'None'}")
                print(f"   Homestead: {'Yes' if homestead else 'No'}")
                
                return {
                    'exemptions': exemptions,
                    'homestead_exemption': homestead,
                    'assessed_value': int(float(row.get('ASS_VAL', 0) or 0)),
                    'taxable_value': int(float(row.get('TAXABLE_VAL', 0) or 0)),
                    'just_value': int(float(row.get('JV', 0) or 0))
                }
    
    print(f"   Property {parcel_id} not found in NAL file")
    return None

def find_physical_data_in_nap_file():
    """Find physical characteristics in NAP file"""
    print("\n5. SEARCHING NAP FILE FOR PHYSICAL DATA")
    print("=" * 60)
    
    parcel_id = '504231242730'
    
    nap_file = 'NAP16P202501.csv'
    if not os.path.exists(nap_file):
        print(f"   NAP file not found: {nap_file}")
        return None
    
    with open(nap_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('PARCEL_ID', '').strip() == parcel_id:
                print(f"   Found property in NAP file")
                
                year_built = row.get('ACT_YR_BLT', '')
                bedrooms = row.get('NO_BEDRMS', '')
                bathrooms = row.get('NO_BATHRMS', '')
                half_baths = row.get('NO_HALF_BATHRMS', '')
                living_area = row.get('TOT_LVG_AREA', '')
                
                print(f"   Year Built: {year_built or 'N/A'}")
                print(f"   Bedrooms: {bedrooms or 'N/A'}")
                print(f"   Bathrooms: {bathrooms or 'N/A'}")
                print(f"   Half Baths: {half_baths or 'N/A'}")
                print(f"   Living Area: {living_area or 'N/A'} sq ft")
                
                return {
                    'year_built': int(year_built) if year_built else None,
                    'bedrooms': int(float(bedrooms)) if bedrooms else None,
                    'bathrooms': int(float(bathrooms)) if bathrooms else None,
                    'half_bathrooms': int(float(half_baths)) if half_baths else None,
                    'total_living_area': int(float(living_area)) if living_area else None
                }
    
    print(f"   Property {parcel_id} not found in NAP file")
    return None

def update_property_with_all_data():
    """Update property with sales, exemptions, and physical data"""
    print("\n6. UPDATING PROPERTY WITH ALL DATA")
    print("=" * 60)
    
    parcel_id = '504231242730'
    
    # Gather all data
    sales = find_sales_in_sdf_file()
    exemption_data = find_exemptions_in_nal_file()
    physical_data = find_physical_data_in_nap_file()
    
    if not any([sales, exemption_data, physical_data]):
        print("   No data found to update")
        return
    
    # Build update payload
    update_data = {'parcel_id': parcel_id}
    
    # Add most recent sale
    if sales:
        most_recent = sales[0]
        update_data['sale_price'] = most_recent['sale_price']
        update_data['sale_date'] = most_recent['sale_date']
        print(f"\n   Adding sale: ${most_recent['sale_price']:,} on {most_recent['sale_date']}")
    
    # Add exemption data
    if exemption_data:
        update_data['homestead_exemption'] = exemption_data['homestead_exemption']
        if exemption_data['just_value']:
            update_data['just_value'] = exemption_data['just_value']
        if exemption_data['assessed_value']:
            update_data['assessed_value'] = exemption_data['assessed_value']
        if exemption_data['taxable_value']:
            update_data['taxable_value'] = exemption_data['taxable_value']
        print(f"   Adding homestead: {exemption_data['homestead_exemption']}")
    
    # Add physical data
    if physical_data:
        for key, value in physical_data.items():
            if value is not None:
                update_data[key] = value
        print(f"   Adding physical: {physical_data.get('bedrooms')} bed, {physical_data.get('bathrooms')} bath")
    
    # Update the property
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    headers_upsert = {
        **headers,
        'Prefer': 'resolution=merge-duplicates,return=representation'
    }
    
    print(f"\n   Sending update to Supabase...")
    response = requests.post(url, json=[update_data], headers=headers_upsert)
    
    if response.status_code in [200, 201, 204]:
        print("   [SUCCESS] Property updated successfully!")
        
        # If we also need to create fl_sdf_sales records
        if sales and check_sdf_sales_table() is not None:
            print("\n   Creating sales history records...")
            for sale in sales[:5]:  # Create up to 5 sales records
                sale_record = {
                    'parcel_id': parcel_id,
                    'sale_date': sale['sale_date'],
                    'sale_price': str(sale['sale_price']),
                    'document_type': sale.get('deed_type', 'Warranty Deed'),
                    'book': sale.get('or_book'),
                    'page': sale.get('or_page'),
                    'qualified_sale': sale.get('qual_code') == 'Q',
                    'vi_code': sale.get('vi_code')
                }
                
                url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales"
                resp = requests.post(url, json=sale_record, headers=headers_upsert)
                if resp.status_code in [200, 201, 204]:
                    print(f"   [SUCCESS] Added sale record for {sale['sale_date']}")
    else:
        print(f"   [FAILED] Update failed: {response.status_code}")
        print(f"   Response: {response.text}")

def verify_update():
    """Verify the property now has the data"""
    print("\n7. VERIFYING UPDATE")
    print("=" * 60)
    
    prop = check_property_current_data()
    
    if prop:
        has_sales = prop.get('sale_price') and prop.get('sale_price') > 0
        has_homestead = prop.get('homestead_exemption') is not None
        has_physical = prop.get('bedrooms') is not None or prop.get('year_built') is not None
        
        print(f"\n   Data Status:")
        print(f"   [CHECK] Sales data: {'Yes' if has_sales else 'No'}")
        print(f"   [CHECK] Homestead exemption: {'Yes' if has_homestead else 'No'}")
        print(f"   [CHECK] Physical characteristics: {'Yes' if has_physical else 'No'}")
        
        if has_sales and has_homestead:
            print("\n   [SUCCESS] Property should now display correctly in the UI!")
        else:
            print("\n   [WARNING] Some data may still be missing")

def main():
    print("FIXING PROPERTY DATA DISPLAY ISSUE")
    print("Property: 504231242730 at 3930 SW 53 CT")
    print("=" * 60)
    
    # Check current state
    current_data = check_property_current_data()
    sdf_table_data = check_sdf_sales_table()
    
    # Find data in CSV files
    sales = find_sales_in_sdf_file()
    exemptions = find_exemptions_in_nal_file()
    physical = find_physical_data_in_nap_file()
    
    # Update the property
    update_property_with_all_data()
    
    # Verify the update
    verify_update()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    
    if not current_data:
        print("\n[WARNING] Property not in database - may need to run initial data load")
    elif not any([sales, exemptions, physical]):
        print("\n[WARNING] No data found in CSV files - check file paths")
    else:
        print("\n[SUCCESS] Property data has been updated")
        print("   The Sales History and Exemptions sections should now display correctly")

if __name__ == "__main__":
    main()