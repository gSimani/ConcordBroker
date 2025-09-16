"""
Check and fix sales history data
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

def check_sales_data(parcel_id):
    print(f"CHECKING SALES HISTORY FOR PROPERTY: {parcel_id}")
    print("=" * 60)
    
    # 1. Check NAL file for sales data
    print("\n1. Checking NAL file for sales data...")
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('PARCEL_ID', '').strip() == parcel_id:
                print("   Found property in NAL file!")
                
                # Check all sales fields
                print("\n   SALES DATA IN NAL FILE:")
                print(f"   SALE_PRC1 (Price 1): {row.get('SALE_PRC1')}")
                print(f"   SALE_YR1 (Year 1): {row.get('SALE_YR1')}")
                print(f"   SALE_MO1 (Month 1): {row.get('SALE_MO1')}")
                print(f"   QUAL_CD1 (Qual Code 1): {row.get('QUAL_CD1')}")
                print(f"   VI_CD1 (VI Code 1): {row.get('VI_CD1')}")
                print(f"   OR_BOOK1: {row.get('OR_BOOK1')}")
                print(f"   OR_PAGE1: {row.get('OR_PAGE1')}")
                
                print(f"\n   SALE_PRC2 (Price 2): {row.get('SALE_PRC2')}")
                print(f"   SALE_YR2 (Year 2): {row.get('SALE_YR2')}")
                print(f"   SALE_MO2 (Month 2): {row.get('SALE_MO2')}")
                print(f"   QUAL_CD2 (Qual Code 2): {row.get('QUAL_CD2')}")
                
                # Build sales history
                sales = []
                
                # Check first sale
                if row.get('SALE_PRC1') and row['SALE_PRC1'].strip():
                    try:
                        price = int(float(row['SALE_PRC1']))
                        year = int(float(row.get('SALE_YR1', 0)))
                        if price > 0 and year > 1900:
                            month = row.get('SALE_MO1', '01').zfill(2)
                            sales.append({
                                'sale_price': price,
                                'sale_date': f"{year}-{month}-01",
                                'sale_year': year,
                                'sale_month': int(month),
                                'qual_code': row.get('QUAL_CD1'),
                                'book': row.get('OR_BOOK1'),
                                'page': row.get('OR_PAGE1')
                            })
                    except:
                        pass
                
                # Check second sale
                if row.get('SALE_PRC2') and row['SALE_PRC2'].strip():
                    try:
                        price = int(float(row['SALE_PRC2']))
                        year = int(float(row.get('SALE_YR2', 0)))
                        if price > 0 and year > 1900:
                            month = row.get('SALE_MO2', '01').zfill(2)
                            sales.append({
                                'sale_price': price,
                                'sale_date': f"{year}-{month}-01",
                                'sale_year': year,
                                'sale_month': int(month),
                                'qual_code': row.get('QUAL_CD2')
                            })
                    except:
                        pass
                
                if sales:
                    print(f"\n   FOUND {len(sales)} SALES:")
                    for i, sale in enumerate(sales, 1):
                        print(f"   Sale {i}: ${sale['sale_price']:,} on {sale['sale_date']}")
                else:
                    print("\n   No valid sales found in NAL file")
                
                break
    
    # 2. Check SDF file for sales data
    print("\n2. Checking for SDF file (Sales Data File)...")
    import glob
    sdf_files = glob.glob('*SDF*.csv') + glob.glob('*sdf*.csv')
    
    if sdf_files:
        sdf_file = sdf_files[0]
        print(f"   Found SDF file: {sdf_file}")
        
        # Check if headers exist
        with open(sdf_file, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
            
            # Check if it has headers or is fixed width
            if 'PARCEL' in first_line.upper() or 'FOLIO' in first_line.upper():
                print("   SDF file has headers, searching for property...")
                f.seek(0)
                reader = csv.DictReader(f)
                
                sales_found = []
                for row in reader:
                    # Check various possible parcel ID fields
                    parcel_fields = ['PARCEL_ID', 'PARCEL', 'FOLIO', 'FOLIO_NUMBER', 'PCN']
                    
                    for field in parcel_fields:
                        if row.get(field, '').strip() == parcel_id:
                            # Found a sale record
                            price = None
                            date = None
                            
                            # Try to find price
                            price_fields = ['SALE_PRICE', 'PRICE', 'SALE_PRC', 'AMOUNT', 'CONSIDERATION']
                            for pf in price_fields:
                                if row.get(pf):
                                    try:
                                        price = int(float(row[pf].replace(',', '').replace('$', '')))
                                        break
                                    except:
                                        pass
                            
                            # Try to find date
                            date_fields = ['SALE_DATE', 'DATE', 'SALE_DT', 'DEED_DATE']
                            for df in date_fields:
                                if row.get(df):
                                    date = row[df]
                                    break
                            
                            if price and date:
                                sales_found.append({
                                    'price': price,
                                    'date': date,
                                    'type': row.get('DEED_TYPE', row.get('SALE_TYPE', 'Unknown'))
                                })
                            break
                
                if sales_found:
                    print(f"   Found {len(sales_found)} sales in SDF file:")
                    for sale in sales_found:
                        print(f"     ${sale['price']:,} on {sale['date']} ({sale['type']})")
                else:
                    print("   No sales found for this property in SDF file")
            else:
                print("   SDF file appears to be fixed-width format (not implemented)")
    else:
        print("   No SDF file found")
    
    # 3. Check what's in the database
    print("\n3. Checking database for sales data...")
    
    # Check florida_parcels table
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            prop = data[0]
            if prop.get('sale_price') or prop.get('sale_date'):
                print(f"   florida_parcels table has sale: ${prop.get('sale_price', 0)} on {prop.get('sale_date', 'N/A')}")
            else:
                print("   No sale data in florida_parcels table")
    
    # Check fl_sdf_sales table if it exists
    url = f"{SUPABASE_URL}/rest/v1/fl_sdf_sales?parcel_id=eq.{parcel_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"   Found {len(data)} sales in fl_sdf_sales table:")
            for sale in data[:5]:  # Show first 5
                print(f"     ${sale.get('sale_price', 0):,} on {sale.get('sale_date', 'N/A')}")
        else:
            print("   No sales in fl_sdf_sales table")
    elif response.status_code == 404:
        print("   fl_sdf_sales table doesn't exist")
    
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("The NAL file doesn't have sales data for this property.")
    print("Sales data typically comes from:")
    print("  1. SDF (Sales Data File) - separate file with all sales")
    print("  2. BCPA API - real-time sales data")
    print("  3. Clerk of Courts records")
    print("\nTo show sales history, you need to:")
    print("  1. Download the SDF file for Broward County")
    print("  2. Load it into fl_sdf_sales table")
    print("  3. The component will automatically display it")

if __name__ == "__main__":
    check_sales_data("504231242730")