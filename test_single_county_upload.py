"""
Test upload of a single county with correct field mapping
"""

import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import json

def get_supabase_client() -> Client:
    """Create Supabase client"""
    url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
    return create_client(url, key)

def prepare_record(row: pd.Series, county: str) -> dict:
    """Map NAL columns to florida_parcels schema"""
    # Calculate building value if we have both JV and LND_VAL
    building_val = None
    if row.get('JV') and row.get('LND_VAL'):
        try:
            building_val = float(row.get('JV', 0)) - float(row.get('LND_VAL', 0))
        except:
            building_val = None
    
    # Build sale_date timestamp if we have year and month
    sale_date = None
    if row.get('SALE_YR1') and row.get('SALE_MO1'):
        try:
            sale_date = f"{int(row.get('SALE_YR1'))}-{str(row.get('SALE_MO1')).zfill(2)}-01T00:00:00"
        except:
            sale_date = None
    
    record = {
        'parcel_id': str(row.get('PARCEL_ID', '')),
        'county': county.upper(),
        'year': 2025,
        'owner_name': str(row.get('OWN_NAME', '')),
        'owner_addr1': str(row.get('OWN_ADDR1', '')),
        'owner_addr2': str(row.get('OWN_ADDR2', '')),
        'owner_city': str(row.get('OWN_CITY', '')),
        'owner_state': str(row.get('OWN_STATE', ''))[:2],  # Truncate to 2 chars for state code
        'owner_zip': str(row.get('OWN_ZIPCD', '')),
        'phy_addr1': str(row.get('PHY_ADDR1', '')),
        'phy_addr2': str(row.get('PHY_ADDR2', '')),
        'phy_city': str(row.get('PHY_CITY', '')),
        'phy_zipcd': str(row.get('PHY_ZIPCD', '')),
        'legal_desc': str(row.get('S_LEGAL', '')),
        'property_use': str(row.get('PA_UC', '')),
        'just_value': row.get('JV'),
        'land_value': row.get('LND_VAL'),
        'building_value': building_val,
        'assessed_value': row.get('AV_SD'),
        'taxable_value': row.get('TV_SD'),
        'year_built': row.get('ACT_YR_BLT'),
        'total_living_area': row.get('TOT_LVG_AREA'),
        'land_sqft': row.get('LND_SQFOOT'),
        'land_acres': float(row.get('LND_SQFOOT', 0)) / 43560 if row.get('LND_SQFOOT') else None,
        'sale_price': row.get('SALE_PRC1'),
        'sale_date': sale_date,
        'sale_qualification': str(row.get('QUAL_CD1', '')) if row.get('QUAL_CD1') else None,
    }
    
    # Clean numeric fields
    numeric_fields = ['just_value', 'land_value', 'building_value', 'assessed_value', 'taxable_value',
                     'year_built', 'total_living_area', 'land_sqft', 'land_acres', 'sale_price']
    
    for field in numeric_fields:
        if field in record:
            value = record[field]
            if pd.isna(value) or value == '' or value == 'None':
                record[field] = None
            else:
                try:
                    if field in ['year_built', 'sale_year', 'sale_month']:
                        record[field] = int(float(value)) if value else None
                    else:
                        record[field] = float(value) if value else None
                except:
                    record[field] = None
    
    # Clean string fields  
    for key, value in record.items():
        if key not in numeric_fields:
            if pd.isna(value) or value == 'nan' or value == '':
                # Use None for sale_date since it's a timestamp field
                record[key] = None if key == 'sale_date' else ''
    
    return record

def test_upload():
    """Test upload with BROWARD county (we know this exists)"""
    csv_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\BROWARD\NAL\NAL16P202501.csv"
    county = "BROWARD"
    
    print("Reading CSV file...")
    # Read first 10 rows to test
    df = pd.read_csv(csv_path, nrows=10, low_memory=False, encoding='utf-8', on_bad_lines='skip')
    
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {', '.join(df.columns[:10])}...")
    
    # Prepare records for upload
    records = []
    for _, row in df.iterrows():
        record = prepare_record(row, county)
        records.append(record)
    
    # Show sample record
    print("\nSample mapped record:")
    print(json.dumps(records[0], indent=2, default=str)[:800])
    
    client = get_supabase_client()
    
    # Test upload
    print(f"\nUploading {len(records)} records to florida_parcels...")
    try:
        result = client.table('florida_parcels').upsert(
            records,
            on_conflict='parcel_id,county,year'
        ).execute()
        print("Upload successful!")
        
        # Check count
        count_result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        if hasattr(count_result, 'count'):
            print(f"Total records in database: {count_result.count:,}")
    except Exception as e:
        print(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_upload()