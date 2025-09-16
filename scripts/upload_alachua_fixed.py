import os, glob
import pandas as pd
from supabase import create_client

SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

ROOT = r"C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker"
BASE_PATH = os.path.join(ROOT, 'TEMP', 'DATABASE PROPERTY APP')
COUNTY = 'ALACHUA'
BATCH_SIZE = 500
YEAR = 2025

client = create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_int(v):
    try:
        return int(float(str(v).replace(',', ''))) if (v is not None and str(v) != '' and str(v).lower() != 'nan') else None
    except:
        return None

def safe_float(v):
    try:
        return float(str(v).replace(',', '')) if (v is not None and str(v) != '' and str(v).lower() != 'nan') else None
    except:
        return None

def build_sale_date(yr, mo):
    y = safe_int(yr); m = safe_int(mo)
    if not y or not m:
        return None
    return f"{y}-{str(m).zfill(2)}-01T00:00:00"

nal_path = os.path.join(BASE_PATH, COUNTY, 'NAL')
files = glob.glob(os.path.join(nal_path, '*.csv'))
if not files:
    raise SystemExit(f'No CSV files found in {nal_path}')

csv_file = files[0]
print(f'Uploading from {csv_file} -> florida_parcels')

total_uploaded = 0
chunk_iter = pd.read_csv(csv_file, chunksize=BATCH_SIZE, low_memory=False, encoding='utf-8', on_bad_lines='skip')

for i, chunk in enumerate(chunk_iter, start=1):
    records = []
    for _, row in chunk.iterrows():
        parcel_id = str(row.get('PARCEL_ID', '')).strip()
        if not parcel_id:
            continue
        jv = safe_float(row.get('JV'))
        land_val = safe_float(row.get('LND_VAL'))
        building_val = (jv - land_val) if (jv is not None and land_val is not None) else None
        rec = {
            'parcel_id': parcel_id,
            'county': COUNTY,
            'year': YEAR,
            'owner_name': (str(row.get('OWN_NAME'))[:255] if pd.notna(row.get('OWN_NAME')) else None),
            'owner_addr1': (str(row.get('OWN_ADDR1'))[:255] if pd.notna(row.get('OWN_ADDR1')) else None),
            'owner_city': (str(row.get('OWN_CITY'))[:100] if pd.notna(row.get('OWN_CITY')) else None),
            'owner_state': (str(row.get('OWN_STATE'))[:2] if pd.notna(row.get('OWN_STATE')) else None),
            'owner_zip': (str(row.get('OWN_ZIPCD'))[:10] if pd.notna(row.get('OWN_ZIPCD')) else None),
            'phy_addr1': (str(row.get('PHY_ADDR1'))[:255] if pd.notna(row.get('PHY_ADDR1')) else None),
            'phy_addr2': (str(row.get('PHY_ADDR2'))[:255] if pd.notna(row.get('PHY_ADDR2')) else None),
            'phy_city': (str(row.get('PHY_CITY'))[:100] if pd.notna(row.get('PHY_CITY')) else None),
            'phy_state': 'FL',
            'phy_zipcd': (str(row.get('PHY_ZIPCD'))[:10] if pd.notna(row.get('PHY_ZIPCD')) else None),
            'property_use': (str(row.get('DOR_UC'))[:10] if pd.notna(row.get('DOR_UC')) else None),
            'year_built': safe_int(row.get('ACT_YR_BLT')),
            'total_living_area': safe_int(row.get('TOT_LVG_AREA')),
            'just_value': jv,
            'assessed_value': safe_float(row.get('AV_SD')),
            'taxable_value': safe_float(row.get('TV_SD')),
            'land_value': land_val,
            'building_value': building_val,
            'sale_price': safe_float(row.get('SALE_PRC1')),
            'sale_date': build_sale_date(row.get('SALE_YR1'), row.get('SALE_MO1')),
        }
        records.append(rec)
    if not records:
        continue
    try:
        client.table('florida_parcels').upsert(records, on_conflict='parcel_id,county,year').execute()
        total_uploaded += len(records)
        if i % 5 == 0:
            print(f'Chunk {i}: total_uploaded={total_uploaded}')
    except Exception as e:
        print('Batch error:', str(e)[:300])
        break

print(f'Done. Total uploaded: {total_uploaded}')
