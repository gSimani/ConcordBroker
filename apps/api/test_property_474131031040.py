import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('SUPABASE_DIRECT_URL')
conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
cur = conn.cursor()

print("\n=== Testing Property 474131031040 ===\n")

# Check property data
cur.execute("""
    SELECT 
        parcel_id, phy_addr1, phy_city, owner_name,
        just_value, taxable_value, sale_price, sale_date,
        tot_lvg_area, act_yr_blt, lnd_sqfoot
    FROM florida_parcels 
    WHERE parcel_id = %s
""", ('474131031040',))

parcel = cur.fetchone()
if parcel:
    print('PROPERTY FOUND:')
    print(f'  Address: {parcel["phy_addr1"]}, {parcel["phy_city"]}')
    print(f'  Owner: {parcel["owner_name"]}')
    
    # Check numeric values
    if parcel['just_value'] is not None:
        print(f'  Just Value: ${parcel["just_value"]:,.0f}')
    else:
        print('  Just Value: NULL')
        
    if parcel['sale_price'] is not None:
        print(f'  Sale Price: ${parcel["sale_price"]:,.0f}')
    else:
        print('  Sale Price: NULL')
        
    if parcel['tot_lvg_area'] is not None:
        print(f'  Living Area: {parcel["tot_lvg_area"]:,} sq ft')
    else:
        print('  Living Area: NULL')
else:
    print('Property not found in florida_parcels')

# Check sales history
print('\nSALES HISTORY:')
cur.execute("""
    SELECT sale_date, sale_price, sale_type
    FROM property_sales_history 
    WHERE parcel_id = %s 
    ORDER BY sale_date DESC 
    LIMIT 3
""", ('474131031040',))

sales = cur.fetchall()
if sales:
    for i, sale in enumerate(sales, 1):
        if sale['sale_price'] is not None:
            print(f'  Sale {i}: {sale["sale_date"]} - ${sale["sale_price"]:,.0f} ({sale["sale_type"]})')
        else:
            print(f'  Sale {i}: {sale["sale_date"]} - Price: NULL ({sale["sale_type"]})')
else:
    print('  No sales history found')

cur.close()
conn.close()

print('\n=== Data Status ===')
print('This property should display real data in the UI.')
print('If showing N/A, check the usePropertyData hook mapping.')