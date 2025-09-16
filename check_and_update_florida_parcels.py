"""
Check florida_parcels table structure and update data accordingly
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

# Import after loading env
from supabase import create_client

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

print("Checking florida_parcels table structure...")
print("=" * 60)

# Create client
supabase = create_client(url, key)

try:
    # Get a sample record to see what columns exist
    result = supabase.table('florida_parcels').select('*').limit(1).execute()
    
    if result.data and len(result.data) > 0:
        existing_columns = list(result.data[0].keys())
        print(f"Found {len(existing_columns)} columns in florida_parcels table:")
        for col in sorted(existing_columns):
            print(f"  - {col}")
        
        print("\n" + "=" * 60)
        print("Loading data with available columns only...")
        
        # Sample properties with only the columns that exist
        sample_properties = [
            {
                "parcel_id": "504232100001",
                "phy_addr1": "123 OCEAN BLVD",
                "phy_city": "FORT LAUDERDALE",
                "phy_zipcd": "33301",
                "own_name": "OCEANVIEW PROPERTIES LLC",
                "dor_uc": "011",
                "jv": 3200000,
                "tv_sd": 2800000,
                "lnd_val": 1200000,
                "tot_lvg_area": 25000,
                "lnd_sqfoot": 35000,
                "sale_prc1": 3100000,
                "sale_yr1": "2022"
            },
            {
                "parcel_id": "504232100002",
                "phy_addr1": "456 SUNRISE BLVD",
                "phy_city": "FORT LAUDERDALE",
                "phy_zipcd": "33304",
                "own_name": "SMITH JOHN & MARY",
                "dor_uc": "001",
                "jv": 525000,
                "tv_sd": 475000,
                "lnd_val": 225000,
                "tot_lvg_area": 2800,
                "lnd_sqfoot": 8500,
                "sale_prc1": 485000,
                "sale_yr1": "2021"
            },
            {
                "parcel_id": "504232100003",
                "phy_addr1": "789 LAS OLAS BLVD",
                "phy_city": "FORT LAUDERDALE",
                "phy_zipcd": "33301",
                "own_name": "WILLIAMS ROBERT",
                "dor_uc": "004",
                "jv": 850000,
                "tv_sd": 800000,
                "lnd_val": 450000,
                "tot_lvg_area": 1500,
                "lnd_sqfoot": 0,
                "sale_prc1": 825000,
                "sale_yr1": "2023"
            },
            {
                "parcel_id": "504232100004",
                "phy_addr1": "321 ATLANTIC AVE",
                "phy_city": "HOLLYWOOD",
                "phy_zipcd": "33019",
                "own_name": "BEACH HOLDINGS INC",
                "dor_uc": "001",
                "jv": 725000,
                "tv_sd": 675000,
                "lnd_val": 325000,
                "tot_lvg_area": 3200,
                "lnd_sqfoot": 10000,
                "sale_prc1": 695000,
                "sale_yr1": "2020"
            },
            {
                "parcel_id": "504232100005",
                "phy_addr1": "555 CORAL WAY",
                "phy_city": "CORAL SPRINGS",
                "phy_zipcd": "33065",
                "own_name": "MARTINEZ ROBERTO",
                "dor_uc": "001",
                "jv": 425000,
                "tv_sd": 375000,
                "lnd_val": 175000,
                "tot_lvg_area": 2400,
                "lnd_sqfoot": 7500,
                "sale_prc1": 395000,
                "sale_yr1": "2019"
            },
            {
                "parcel_id": "504232100006",
                "phy_addr1": "100 BISCAYNE BLVD",
                "phy_city": "MIAMI",
                "phy_zipcd": "33131",
                "own_name": "BISCAYNE TOWER LLC",
                "dor_uc": "011",
                "jv": 45000000,
                "tv_sd": 42000000,
                "lnd_val": 15000000,
                "tot_lvg_area": 150000,
                "lnd_sqfoot": 45000,
                "sale_prc1": 43000000,
                "sale_yr1": "2021"
            },
            {
                "parcel_id": "504232100007",
                "phy_addr1": "2500 UNIVERSITY DR",
                "phy_city": "DAVIE",
                "phy_zipcd": "33324",
                "own_name": "UNIVERSITY PLAZA LLC",
                "dor_uc": "011",
                "jv": 12500000,
                "tv_sd": 11500000,
                "lnd_val": 4500000,
                "tot_lvg_area": 85000,
                "lnd_sqfoot": 125000,
                "sale_prc1": 12000000,
                "sale_yr1": "2022"
            },
            {
                "parcel_id": "504232100008",
                "phy_addr1": "8500 GRIFFIN RD",
                "phy_city": "COOPER CITY",
                "phy_zipcd": "33328",
                "own_name": "GRIFFIN ESTATES HOA",
                "dor_uc": "001",
                "jv": 625000,
                "tv_sd": 575000,
                "lnd_val": 275000,
                "tot_lvg_area": 2850,
                "lnd_sqfoot": 9500,
                "sale_prc1": 595000,
                "sale_yr1": "2020"
            }
        ]
        
        # Filter properties to only include existing columns
        for prop in sample_properties:
            # Keep only columns that exist in the table
            filtered_prop = {k: v for k, v in prop.items() if k in existing_columns}
            
            # Add missing required columns with defaults if they exist in table
            if 'id' in existing_columns and 'id' not in filtered_prop:
                filtered_prop.pop('id', None)  # Let database auto-generate
            
            # Handle numeric conversions
            for numeric_field in ['jv', 'tv_sd', 'lnd_val', 'tot_lvg_area', 'lnd_sqfoot', 'sale_prc1']:
                if numeric_field in filtered_prop and filtered_prop[numeric_field] is not None:
                    filtered_prop[numeric_field] = float(filtered_prop[numeric_field]) if '.' in str(filtered_prop[numeric_field]) else int(filtered_prop[numeric_field])
            
            try:
                # Check if property exists
                existing = supabase.table('florida_parcels').select('id').eq('parcel_id', filtered_prop['parcel_id']).execute()
                
                if existing.data:
                    # Update existing
                    result = supabase.table('florida_parcels').update(filtered_prop).eq('parcel_id', filtered_prop['parcel_id']).execute()
                    print(f"Updated: {filtered_prop.get('phy_addr1', 'N/A')}, {filtered_prop.get('phy_city', 'N/A')} - JV: ${filtered_prop.get('jv', 0):,.0f}")
                else:
                    # Insert new
                    result = supabase.table('florida_parcels').insert(filtered_prop).execute()
                    print(f"Inserted: {filtered_prop.get('phy_addr1', 'N/A')}, {filtered_prop.get('phy_city', 'N/A')} - JV: ${filtered_prop.get('jv', 0):,.0f}")
                    
            except Exception as e:
                error_msg = str(e)
                if 'row-level security' in error_msg.lower():
                    print(f"\nRLS is blocking access. The data cannot be inserted.")
                    print("To fix this:")
                    print("1. Go to your Supabase dashboard")
                    print("2. Navigate to Authentication > Policies")
                    print("3. Find the florida_parcels table")
                    print("4. Either disable RLS or add a policy for INSERT/UPDATE with:")
                    print("   - Policy name: 'Enable write for all'")
                    print("   - Allowed operation: INSERT, UPDATE")
                    print("   - Target roles: anon")
                    print("   - USING expression: true")
                    print("   - WITH CHECK expression: true")
                    break
                else:
                    print(f"Error: {error_msg[:100]}")
    else:
        print("No data found in florida_parcels table")
        
except Exception as e:
    print(f"Error accessing florida_parcels table: {str(e)}")

print("\n" + "=" * 60)
print("Done!")
print("\nTo view the properties:")
print("1. Go to http://localhost:5173/properties")
print("2. The properties should now show with addresses, cities, values, etc.")
print("3. Click on any property to see the detailed profile")