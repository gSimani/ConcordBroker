"""
Fix missing fields like Homestead Exemption, Bedrooms, Bathrooms
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

def update_property_details(parcel_id):
    print(f"Finding complete details for property {parcel_id}...")
    
    # Find the property in NAL file
    with open('NAL16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row.get('PARCEL_ID', '').strip() == parcel_id:
                print("Found property in NAL file!")
                
                # Show exemption fields
                print("\nEXEMPTION DATA FROM NAL FILE:")
                print(f"  EXMPT_01 (Homestead): {row.get('EXMPT_01')}")
                print(f"  EXMPT_02: {row.get('EXMPT_02')}")
                print(f"  EXMPT_03: {row.get('EXMPT_03')}")
                print(f"  EXMPT_04: {row.get('EXMPT_04')}")
                print(f"  EXMPT_05: {row.get('EXMPT_05')}")
                
                # Show building details
                print("\nBUILDING DETAILS FROM NAL FILE:")
                print(f"  NO_BULDNG (Buildings): {row.get('NO_BULDNG')}")
                print(f"  NO_RES_UNTS (Units): {row.get('NO_RES_UNTS')}")
                print(f"  TOT_LVG_AREA: {row.get('TOT_LVG_AREA')}")
                print(f"  EFF_YR_BLT: {row.get('EFF_YR_BLT')}")
                print(f"  ACT_YR_BLT: {row.get('ACT_YR_BLT')}")
                print(f"  IMP_QUAL (Quality): {row.get('IMP_QUAL')}")
                print(f"  CONST_CLASS: {row.get('CONST_CLASS')}")
                
                # Build update data
                update_data = {
                    'parcel_id': parcel_id
                }
                
                # Check for homestead exemption
                homestead_value = 0
                if row.get('EXMPT_01') and row['EXMPT_01'].strip():
                    try:
                        homestead_value = int(float(row['EXMPT_01']))
                    except:
                        pass
                
                # Add homestead exemption flag
                update_data['homestead_exemption'] = homestead_value > 0
                update_data['homestead_exemption_value'] = homestead_value if homestead_value > 0 else None
                
                # Add other exemptions
                exemptions = []
                for i in range(1, 47):  # Check EXMPT_01 through EXMPT_46
                    field = f'EXMPT_{str(i).zfill(2)}'
                    if row.get(field) and row[field].strip():
                        try:
                            value = int(float(row[field]))
                            if value > 0:
                                exemptions.append({
                                    'code': field,
                                    'value': value
                                })
                        except:
                            pass
                
                if exemptions:
                    update_data['exemptions'] = str(exemptions)  # Store as JSON string
                
                # Add building details
                if row.get('NO_BULDNG') and row['NO_BULDNG'].strip():
                    update_data['buildings'] = int(float(row['NO_BULDNG']))
                    
                if row.get('EFF_YR_BLT') and row['EFF_YR_BLT'].strip():
                    year = int(float(row['EFF_YR_BLT']))
                    if year > 1800:
                        update_data['eff_year_built'] = year
                
                # Unfortunately, NAL file doesn't have bedroom/bathroom data
                # We need to check NAP or other files for that
                print("\nNOTE: Bedroom/Bathroom data not available in NAL file")
                print("      These fields are typically in the NAP (Name Address Property) file")
                
                print("\nUPDATE DATA:")
                for key, value in update_data.items():
                    if key != 'parcel_id':
                        print(f"  {key}: {value}")
                
                # Update in Supabase
                url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
                response = requests.patch(url, json=update_data, headers=headers)
                
                if response.status_code in [200, 204]:
                    print("\nSuccessfully updated property!")
                else:
                    print(f"\nUpdate failed: {response.status_code}")
                    print(response.text[:500])
                
                return
        
        print(f"Property {parcel_id} not found in NAL file")

def check_nap_file(parcel_id):
    """Check if we have bedroom/bathroom data in NAP file"""
    print(f"\nChecking NAP file for bedroom/bathroom data...")
    
    # Check if NAP file exists
    import glob
    nap_files = glob.glob('NAP*.csv')
    
    if not nap_files:
        print("No NAP file found")
        return
    
    nap_file = nap_files[0]
    print(f"Found NAP file: {nap_file}")
    
    # Check first line for column headers
    with open(nap_file, 'r', encoding='utf-8', errors='ignore') as f:
        headers = f.readline().strip().split(',')
        
        # Look for bedroom/bathroom columns
        bed_cols = [h for h in headers if 'BED' in h.upper() or 'BDRM' in h.upper()]
        bath_cols = [h for h in headers if 'BATH' in h.upper() or 'BTH' in h.upper()]
        
        if bed_cols or bath_cols:
            print(f"  Found bedroom columns: {bed_cols}")
            print(f"  Found bathroom columns: {bath_cols}")
            
            # Now search for the property
            f.seek(0)
            reader = csv.DictReader(f)
            
            for row in reader:
                if row.get('PARCEL_ID', '').strip() == parcel_id:
                    print(f"\nFound property in NAP file!")
                    
                    update_data = {'parcel_id': parcel_id}
                    
                    # Extract bedroom data
                    for col in bed_cols:
                        if row.get(col) and row[col].strip():
                            try:
                                update_data['bedrooms'] = int(float(row[col]))
                                print(f"  Bedrooms: {update_data['bedrooms']}")
                                break
                            except:
                                pass
                    
                    # Extract bathroom data
                    for col in bath_cols:
                        if row.get(col) and row[col].strip():
                            try:
                                # Bathrooms might be decimal (e.g., 2.5)
                                update_data['bathrooms'] = float(row[col])
                                print(f"  Bathrooms: {update_data['bathrooms']}")
                                break
                            except:
                                pass
                    
                    if len(update_data) > 1:
                        # Update in Supabase
                        url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
                        response = requests.patch(url, json=update_data, headers=headers)
                        
                        if response.status_code in [200, 204]:
                            print("  Updated bedroom/bathroom data!")
                        else:
                            print(f"  Update failed: {response.status_code}")
                    
                    return
            
            print(f"  Property {parcel_id} not found in NAP file")
        else:
            print("  No bedroom/bathroom columns found in NAP file")

if __name__ == "__main__":
    # Update the specific property
    parcel_id = "504231242730"
    
    # First update from NAL file
    update_property_details(parcel_id)
    
    # Then check NAP file for bedroom/bathroom data
    check_nap_file(parcel_id)
    
    # Finally, show what we have in the database
    print("\n" + "="*60)
    print("FINAL DATABASE VALUES:")
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            prop = data[0]
            print(f"  Homestead Exemption: {prop.get('homestead_exemption', False)}")
            print(f"  Homestead Value: ${prop.get('homestead_exemption_value', 0)}")
            print(f"  Units: {prop.get('units', 'N/A')}")
            print(f"  Bedrooms: {prop.get('bedrooms', 'N/A')}")
            print(f"  Bathrooms: {prop.get('bathrooms', 'N/A')}")
            print(f"  Buildings: {prop.get('buildings', 'N/A')}")
            print(f"  Eff Year Built: {prop.get('eff_year_built', 'N/A')}")
            print(f"  Living Area: {prop.get('total_living_area', 'N/A')} sq ft")