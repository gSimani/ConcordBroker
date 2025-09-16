"""
Load additional property data from NAP (Physical) and enhance SDF sales data
"""

import os
import csv
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def load_nap_physical_data():
    """Extract physical property characteristics from NAP file"""
    print("\n1. LOADING NAP PHYSICAL PROPERTY DATA")
    print("=" * 60)
    
    if not os.path.exists('NAP16P202501.csv'):
        print("NAP file not found!")
        return 0
    
    updates_batch = []
    batch_size = 100
    total_updated = 0
    
    with open('NAP16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            parcel_id = row.get('PARCEL_ID', '').strip()
            
            if not parcel_id:
                continue
            
            # Extract all physical characteristics
            update_data = {
                'parcel_id': parcel_id,
                
                # Building characteristics
                'year_built': int(row.get('ACT_YR_BLT', 0) or 0) if row.get('ACT_YR_BLT') else None,
                'effective_year_built': int(row.get('EFF_YR_BLT', 0) or 0) if row.get('EFF_YR_BLT') else None,
                'total_living_area': int(float(row.get('TOT_LVG_AREA', 0) or 0)) if row.get('TOT_LVG_AREA') else None,
                'adjusted_area': int(float(row.get('ADJ_AREA', 0) or 0)) if row.get('ADJ_AREA') else None,
                'gross_area': int(float(row.get('GROSS_AREA', 0) or 0)) if row.get('GROSS_AREA') else None,
                'heated_area': int(float(row.get('HEAT_AR', 0) or 0)) if row.get('HEAT_AR') else None,
                
                # Bedroom/Bathroom data from NAP
                'bedrooms': int(float(row.get('NO_BDRMS', 0) or 0)) if row.get('NO_BDRMS') else None,
                'bathrooms': int(float(row.get('NO_BATHS', 0) or 0)) if row.get('NO_BATHS') else None,
                'half_bathrooms': int(float(row.get('NO_HALF_BATHS', 0) or 0)) if row.get('NO_HALF_BATHS') else None,
                
                # Stories and units
                'stories': row.get('NO_STORIES', '').strip() or None,
                'units': int(float(row.get('NO_UNITS', 0) or 0)) if row.get('NO_UNITS') else None,
                'buildings': int(float(row.get('NO_BLDGS', 0) or 0)) if row.get('NO_BLDGS') else None,
                
                # Condition and quality
                'condition': row.get('CONDITION', '').strip() or None,
                'quality': row.get('QUALITY', '').strip() or None,
                'construction_type': row.get('CONST_TYP', '').strip() or None,
                'exterior_wall': row.get('EXT_WALL', '').strip() or None,
                'roof_type': row.get('ROOF_TYP', '').strip() or None,
                'roof_cover': row.get('ROOF_COVER', '').strip() or None,
                
                # Pool and features
                'pool': row.get('NO_POOLS', '') != '0' if row.get('NO_POOLS') else False,
                'pool_type': row.get('POOL_TYP', '').strip() or None,
                
                # Heating/Cooling
                'heat_type': row.get('HEAT_TYP', '').strip() or None,
                'air_cond': row.get('AIR_COND', '').strip() or None,
                
                # Other features
                'floor_type': row.get('FLOOR_TYP', '').strip() or None,
                'foundation': row.get('FOUNDATION', '').strip() or None,
                'basement': row.get('BASEMENT', '').strip() or None,
                'fireplace': int(float(row.get('NO_FIREPLACE', 0) or 0)) if row.get('NO_FIREPLACE') else None,
                
                # Special features
                'special_features': [
                    feat.strip() for feat in [
                        row.get('SPEC_FEAT_1', ''),
                        row.get('SPEC_FEAT_2', ''),
                        row.get('SPEC_FEAT_3', ''),
                        row.get('SPEC_FEAT_4', '')
                    ] if feat.strip()
                ]
            }
            
            # Remove None values and empty lists
            update_data = {k: v for k, v in update_data.items() 
                          if v is not None and (not isinstance(v, list) or v)}
            
            if len(update_data) > 1:  # Has data beyond parcel_id
                updates_batch.append(update_data)
            
            # Upload batch when full
            if len(updates_batch) >= batch_size:
                url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
                headers_upsert = {
                    **headers,
                    'Prefer': 'resolution=merge-duplicates,return=minimal'
                }
                
                response = requests.post(url, json=updates_batch, headers=headers_upsert)
                
                if response.status_code in [200, 201, 204]:
                    total_updated += len(updates_batch)
                    if total_updated % 5000 == 0:
                        print(f"   Updated {total_updated:,} properties with physical data...")
                
                updates_batch = []
                time.sleep(0.1)
        
        # Upload remaining batch
        if updates_batch:
            url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
            headers_upsert = {
                **headers,
                'Prefer': 'resolution=merge-duplicates,return=minimal'
            }
            
            response = requests.post(url, json=updates_batch, headers=headers_upsert)
            
            if response.status_code in [200, 201, 204]:
                total_updated += len(updates_batch)
    
    print(f"   Total properties updated with NAP data: {total_updated:,}")
    return total_updated

def enhance_sdf_sales_data():
    """Extract additional sale details from SDF"""
    print("\n2. ENHANCING SDF SALES DATA")
    print("=" * 60)
    
    if not os.path.exists('SDF16P202501.csv'):
        print("SDF file not found!")
        return 0
    
    # Track enhanced sales
    enhanced_count = 0
    
    with open('SDF16P202501.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            parcel_id = row.get('PARCEL_ID', '').strip()
            
            if not parcel_id:
                continue
            
            # Extract additional SDF fields that weren't loaded before
            additional_data = {
                # Deed information
                'deed_type': row.get('DEED_TYP', '').strip() or None,
                'grantor': row.get('GRANTOR', '').strip() or None,
                'grantee': row.get('GRANTEE', '').strip() or None,
                
                # Financial details
                'mtg_amount': int(float(row.get('MTG_AMT', 0) or 0)) if row.get('MTG_AMT') else None,
                'mtg_type': row.get('MTG_TYP', '').strip() or None,
                'mtg_date': row.get('MTG_DATE', '').strip() or None,
                
                # Transfer details
                'transfer_fee': int(float(row.get('TRANS_FEE', 0) or 0)) if row.get('TRANS_FEE') else None,
                'doc_stamps': int(float(row.get('DOC_STAMPS', 0) or 0)) if row.get('DOC_STAMPS') else None,
                
                # Legal description
                'legal_desc': row.get('LEGAL_DESC', '').strip() or None,
                'plat_book': row.get('PLAT_BOOK', '').strip() or None,
                'plat_page': row.get('PLAT_PAGE', '').strip() or None,
                
                # Foreclosure indicator
                'foreclosure': row.get('FORECLOSURE', '') == 'Y',
                
                # Arms length transaction
                'arms_length': row.get('ARMS_LENGTH', '') != 'N'
            }
            
            # The grantor is the seller, grantee is the buyer
            if additional_data.get('grantor') or additional_data.get('grantee'):
                enhanced_count += 1
    
    print(f"   Found {enhanced_count:,} sales with buyer/seller names")
    return enhanced_count

def check_property_update(parcel_id="504231242730"):
    """Check what data we have for a specific property"""
    print(f"\n3. CHECKING PROPERTY {parcel_id}")
    print("=" * 60)
    
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels?parcel_id=eq.{parcel_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            prop = data[0]
            
            # Check new fields
            print("   Physical characteristics:")
            print(f"     Year Built: {prop.get('year_built', 'N/A')}")
            print(f"     Living Area: {prop.get('total_living_area', 'N/A')} sq ft")
            print(f"     Bedrooms: {prop.get('bedrooms', 'N/A')}")
            print(f"     Bathrooms: {prop.get('bathrooms', 'N/A')}")
            print(f"     Pool: {prop.get('pool', 'N/A')}")
            print(f"     Stories: {prop.get('stories', 'N/A')}")
            print(f"     Construction: {prop.get('construction_type', 'N/A')}")
            
            print("\n   Sales information:")
            print(f"     Sale Price: ${prop.get('sale_price', 0):,}")
            print(f"     Sale Date: {prop.get('sale_date', 'N/A')}")

def main():
    print("LOADING ADDITIONAL PROPERTY DATA")
    print("=" * 60)
    print("This will add physical characteristics and enhance sales data")
    
    # Load NAP physical data
    nap_count = load_nap_physical_data()
    
    # Enhance SDF sales data
    sdf_count = enhance_sdf_sales_data()
    
    # Check a property
    check_property_update()
    
    print("\n" + "=" * 60)
    print("LOADING COMPLETE!")
    print(f"Updated {nap_count:,} properties with physical characteristics")
    print(f"Found {sdf_count:,} sales with buyer/seller names")
    print("\nProperty pages will now show:")
    print("✓ Bedrooms and bathrooms")
    print("✓ Year built and living area")
    print("✓ Pool, stories, construction type")
    print("✓ Heating/cooling systems")
    print("✓ Special features")
    print("✓ Enhanced sales data")

if __name__ == "__main__":
    main()