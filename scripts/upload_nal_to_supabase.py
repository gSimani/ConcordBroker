#!/usr/bin/env python3
"""
Upload NAL (Name and Address Listing) data to Supabase florida_parcels table
Handles CSV files from Florida Revenue Data Portal

Usage:
    python upload_nal_to_supabase.py                    # Upload all available NAL files
    python upload_nal_to_supabase.py --county LIBERTY   # Upload specific county
    python upload_nal_to_supabase.py --dry-run          # Show what would be uploaded
"""

import os
import sys
import glob
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import argparse

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nal_upload.log')
    ]
)
logger = logging.getLogger(__name__)

# Force correct Supabase configuration (override any environment variables)
# The shell may have different env vars set
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

from supabase import create_client

logger.info(f"Using Supabase URL: {SUPABASE_URL}")
DATA_PATH = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
BATCH_SIZE = 500  # Smaller batches for more reliable uploads

# County codes mapping (DOR standard)
COUNTY_CODES = {
    11: "ALACHUA", 12: "BAKER", 13: "BAY", 14: "BRADFORD", 15: "BREVARD",
    16: "BROWARD", 17: "CALHOUN", 18: "CHARLOTTE", 19: "CITRUS", 20: "CLAY",
    21: "COLLIER", 22: "COLUMBIA", 23: "MIAMI-DADE", 24: "DESOTO", 25: "DIXIE",
    26: "DUVAL", 27: "ESCAMBIA", 28: "FLAGLER", 29: "FRANKLIN", 30: "GADSDEN",
    31: "GILCHRIST", 32: "GLADES", 33: "GULF", 34: "HAMILTON", 35: "HARDEE",
    36: "HENDRY", 37: "HERNANDO", 38: "HIGHLANDS", 39: "HILLSBOROUGH", 40: "HOLMES",
    41: "INDIAN RIVER", 42: "JACKSON", 43: "JEFFERSON", 44: "LAFAYETTE", 45: "LAKE",
    46: "LEE", 47: "LEON", 48: "LEVY", 49: "LIBERTY", 50: "MADISON",
    51: "MANATEE", 52: "MARION", 53: "MARTIN", 54: "MONROE", 55: "NASSAU",
    56: "OKALOOSA", 57: "OKEECHOBEE", 58: "ORANGE", 59: "OSCEOLA", 60: "PALM BEACH",
    61: "PASCO", 62: "PINELLAS", 63: "POLK", 64: "PUTNAM", 65: "ST. JOHNS",
    66: "ST. LUCIE", 67: "SANTA ROSA", 68: "SARASOTA", 69: "SEMINOLE", 70: "SUMTER",
    71: "SUWANNEE", 72: "TAYLOR", 73: "UNION", 74: "VOLUSIA", 75: "WAKULLA",
    76: "WALTON", 77: "WASHINGTON"
}


def safe_int(v):
    """Safely convert to integer"""
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return int(float(str(v).replace(',', '')))
    except:
        return None


def safe_float(v):
    """Safely convert to float"""
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return float(str(v).replace(',', ''))
    except:
        return None


def safe_str(v, max_len=None):
    """Safely convert to string with optional length limit"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    if not s or s.lower() == 'nan':
        return None
    if max_len:
        s = s[:max_len]
    return s


def build_sale_date(year, month):
    """Build sale date from year and month"""
    y = safe_int(year)
    m = safe_int(month)
    if not y or not m or m < 1 or m > 12:
        return None
    return f"{y}-{str(m).zfill(2)}-01"


def get_county_name(co_no: int) -> str:
    """Get county name from code"""
    return COUNTY_CODES.get(co_no, f"COUNTY_{co_no}")


def transform_nal_row(row: pd.Series, county_name: str) -> dict:
    """Transform a NAL CSV row to florida_parcels format"""

    # Get values
    jv = safe_float(row.get('JV'))
    land_val = safe_float(row.get('LND_VAL'))
    building_val = (jv - land_val) if (jv is not None and land_val is not None and land_val < jv) else None

    # Build record matching florida_parcels schema
    record = {
        # Core identifiers
        'co_no': safe_int(row.get('CO_NO')),
        'parcel_id': safe_str(row.get('PARCEL_ID')),
        'file_t': safe_str(row.get('FILE_T')),
        'asmnt_yr': safe_int(row.get('ASMNT_YR')),

        # Geographic
        'twn': safe_str(row.get('TWN')),
        'rng': safe_str(row.get('RNG')),
        'sec': safe_str(row.get('SEC')),
        'census_bk': safe_str(row.get('CENSUS_BK')),

        # Physical address
        'phy_addr1': safe_str(row.get('PHY_ADDR1'), 255),
        'phy_addr2': safe_str(row.get('PHY_ADDR2'), 255),
        'phy_city': safe_str(row.get('PHY_CITY'), 100),
        'phy_zipcd': safe_str(row.get('PHY_ZIPCD'), 10),

        # Owner info
        'owner_name': safe_str(row.get('OWN_NAME'), 255),
        'owner_addr1': safe_str(row.get('OWN_ADDR1'), 255),
        'owner_addr2': safe_str(row.get('OWN_ADDR2'), 255),
        'owner_city': safe_str(row.get('OWN_CITY'), 100),
        'owner_state': safe_str(row.get('OWN_STATE'), 2),  # Truncate to 2 chars
        'owner_zip': safe_str(row.get('OWN_ZIPCD'), 10),
        'owner_state_dom': safe_str(row.get('OWN_STATE_DOM'), 2),

        # Fiduciary
        'fidu_name': safe_str(row.get('FIDU_NAME'), 255),
        'fidu_addr1': safe_str(row.get('FIDU_ADDR1'), 255),
        'fidu_addr2': safe_str(row.get('FIDU_ADDR2'), 255),
        'fidu_city': safe_str(row.get('FIDU_CITY'), 100),
        'fidu_state': safe_str(row.get('FIDU_STATE'), 2),
        'fidu_zipcd': safe_str(row.get('FIDU_ZIPCD'), 10),
        'fidu_cd': safe_str(row.get('FIDU_CD')),

        # Values
        'just_value': safe_int(jv),
        'taxable_value': safe_int(row.get('TV_SD')),
        'assessed_value': safe_int(row.get('AV_SD')),
        'land_value': safe_int(land_val),
        'building_value': safe_int(building_val),
        'market_value': safe_int(jv),  # Alias for just_value

        # Homestead
        'jv_hmstd': safe_int(row.get('JV_HMSTD')),
        'av_hmstd': safe_int(row.get('AV_HMSTD')),

        # Property use
        'property_use': safe_str(row.get('DOR_UC')),
        'pa_uc': safe_str(row.get('PA_UC')),

        # Building details
        'year_built': safe_int(row.get('ACT_YR_BLT')),
        'eff_year_built': safe_int(row.get('EFF_YR_BLT')),
        'total_living_area': safe_int(row.get('TOT_LVG_AREA')),
        'no_buldng': safe_int(row.get('NO_BULDNG')),
        'no_res_unts': safe_int(row.get('NO_RES_UNTS')),

        # Land details
        'land_sqft': safe_int(row.get('LND_SQFOOT')),
        'lnd_unts_cd': safe_str(row.get('LND_UNTS_CD')),
        'no_lnd_unts': safe_int(row.get('NO_LND_UNTS')),

        # Quality
        'imp_qual': safe_str(row.get('IMP_QUAL')),
        'const_class': safe_str(row.get('CONST_CLASS')),
        'spec_feat_val': safe_int(row.get('SPEC_FEAT_VAL')),

        # Sale 1
        'sale_price': safe_int(row.get('SALE_PRC1')),
        'sale_date': build_sale_date(row.get('SALE_YR1'), row.get('SALE_MO1')),
        'sale_yr1': safe_int(row.get('SALE_YR1')),
        'sale_mo1': safe_int(row.get('SALE_MO1')),
        'qual_cd1': safe_str(row.get('QUAL_CD1')),
        'vi_cd1': safe_str(row.get('VI_CD1')),
        'or_book1': safe_str(row.get('OR_BOOK1')),
        'or_page1': safe_str(row.get('OR_PAGE1')),
        'clerk_no1': safe_str(row.get('CLERK_NO1')),
        'multi_par_sal1': safe_str(row.get('MULTI_PAR_SAL1')),

        # Sale 2
        'sale_prc2': safe_int(row.get('SALE_PRC2')),
        'sale_yr2': safe_int(row.get('SALE_YR2')),
        'sale_mo2': safe_int(row.get('SALE_MO2')),
        'qual_cd2': safe_str(row.get('QUAL_CD2')),
        'vi_cd2': safe_str(row.get('VI_CD2')),
        'or_book2': safe_str(row.get('OR_BOOK2')),
        'or_page2': safe_str(row.get('OR_PAGE2')),
        'clerk_no2': safe_str(row.get('CLERK_NO2')),

        # Legal description
        's_legal': safe_str(row.get('S_LEGAL'), 500),

        # Assessment info
        'app_stat': safe_str(row.get('APP_STAT')),
        'co_app_stat': safe_str(row.get('CO_APP_STAT')),
        'mkt_ar': safe_str(row.get('MKT_AR')),
        'nbrhd_cd': safe_str(row.get('NBRHD_CD')),

        # Other
        'alt_key': safe_str(row.get('ALT_KEY')),
        'public_lnd': safe_str(row.get('PUBLIC_LND')),
        'tax_auth_cd': safe_str(row.get('TAX_AUTH_CD')),
        'dt_last_inspt': safe_str(row.get('DT_LAST_INSPT')),

        # State parcel ID
        'state_par_id': safe_str(row.get('STATE_PAR_ID')),
        'seq_no': safe_int(row.get('SEQ_NO')),
        'rs_id': safe_str(row.get('RS_ID')),
        'mp_id': safe_str(row.get('MP_ID')),
    }

    # Build full address for search
    addr_parts = [record['phy_addr1'], record['phy_city'], 'FL', record['phy_zipcd']]
    record['property_address_full'] = ', '.join([p for p in addr_parts if p]) or None

    # Keep only essential columns that exist in the table to avoid schema mismatch
    # The table may not have all these columns - use minimal set for upload
    # Get county and year from the record (required columns)
    co_no = safe_int(row.get('CO_NO'))
    county_name = get_county_name(co_no) if co_no else county_name
    year = safe_int(row.get('ASMNT_YR')) or 2025

    # Build final record with required columns
    final_record = {
        'parcel_id': record['parcel_id'],
        'county': county_name,
        'year': year,
        'owner_name': record.get('owner_name'),
        'owner_addr1': record.get('owner_addr1'),
        'owner_addr2': record.get('owner_addr2'),
        'owner_city': record.get('owner_city'),
        'owner_state': record.get('owner_state'),
        'owner_zip': record.get('owner_zip'),
        'phy_addr1': record.get('phy_addr1'),
        'phy_addr2': record.get('phy_addr2'),
        'phy_city': record.get('phy_city'),
        'phy_zipcd': record.get('phy_zipcd'),
        'just_value': record.get('just_value'),
        'assessed_value': record.get('assessed_value'),
        'taxable_value': record.get('taxable_value'),
        'land_value': record.get('land_value'),
        'year_built': record.get('year_built'),
        'total_living_area': record.get('total_living_area'),
        'land_sqft': record.get('land_sqft'),
        'property_use': record.get('property_use'),
        'sale_price': record.get('sale_price'),
        'sale_date': record.get('sale_date'),
    }

    return final_record


def find_nal_files(base_path: Path, county: str = None) -> list:
    """Find all NAL CSV files"""
    files = []

    if county:
        # Specific county
        patterns = [
            base_path / county.upper() / "NAL" / "*.csv",
            base_path / county.upper().replace(" ", "_") / "NAL" / "*.csv",
        ]
    else:
        # All counties
        patterns = [
            base_path / "*" / "NAL" / "*.csv",
        ]

    for pattern in patterns:
        files.extend(glob.glob(str(pattern)))

    return sorted(set(files))


def upload_file(client, file_path: str, dry_run: bool = False) -> dict:
    """Upload a single NAL file to Supabase"""
    file_path = Path(file_path)
    logger.info(f"Processing: {file_path.name}")

    stats = {
        'file': str(file_path),
        'records_processed': 0,
        'records_uploaded': 0,
        'errors': 0,
        'start_time': datetime.now().isoformat()
    }

    try:
        # Read CSV
        df = pd.read_csv(file_path, low_memory=False, encoding='utf-8', on_bad_lines='skip')
        total_rows = len(df)
        stats['records_processed'] = total_rows
        logger.info(f"  Loaded {total_rows:,} records")

        if dry_run:
            logger.info(f"  [DRY RUN] Would upload {total_rows:,} records")
            stats['records_uploaded'] = total_rows
            return stats

        # Process in batches
        batch_count = 0
        for start in range(0, total_rows, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total_rows)
            batch = df.iloc[start:end]

            # Transform records
            records = []
            for _, row in batch.iterrows():
                try:
                    # Get county name from CO_NO
                    co_no = safe_int(row.get('CO_NO'))
                    county_name = get_county_name(co_no) if co_no else "UNKNOWN"

                    record = transform_nal_row(row, county_name)
                    if record.get('parcel_id'):  # Must have parcel_id
                        records.append(record)
                except Exception as e:
                    stats['errors'] += 1
                    if stats['errors'] <= 5:
                        logger.warning(f"  Row transform error: {e}")

            if not records:
                continue

            # Upsert to Supabase (unique constraint is on parcel_id, county, year)
            try:
                result = client.table('florida_parcels').upsert(
                    records,
                    on_conflict='parcel_id,county,year'
                ).execute()

                stats['records_uploaded'] += len(records)
                batch_count += 1

                if batch_count % 10 == 0:
                    logger.info(f"    Batch {batch_count}: {stats['records_uploaded']:,}/{total_rows:,} uploaded")

            except Exception as e:
                stats['errors'] += len(records)
                logger.error(f"    Batch upload error: {str(e)[:100]}")

        logger.info(f"  Completed: {stats['records_uploaded']:,} uploaded, {stats['errors']} errors")

    except Exception as e:
        logger.error(f"  File processing error: {e}")
        stats['error'] = str(e)

    stats['end_time'] = datetime.now().isoformat()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Upload NAL data to Supabase")
    parser.add_argument('--county', '-c', help='Specific county to upload')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be uploaded')
    parser.add_argument('--data-path', '-d', default=str(DATA_PATH), help='Base data directory')
    args = parser.parse_args()

    print("="*70)
    print("NAL DATA UPLOAD TO SUPABASE")
    print("="*70)
    print(f"Data path: {args.data_path}")
    print(f"County: {args.county or 'ALL'}")
    print(f"Dry run: {args.dry_run}")
    print("="*70)

    # Validate environment
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env.mcp")
        sys.exit(1)

    # Create client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Find files
    base_path = Path(args.data_path)
    files = find_nal_files(base_path, args.county)

    if not files:
        logger.error(f"No NAL files found in {base_path}")
        sys.exit(1)

    logger.info(f"Found {len(files)} NAL file(s)")

    # Process files
    all_stats = []
    total_uploaded = 0
    total_errors = 0

    for file_path in files:
        stats = upload_file(client, file_path, args.dry_run)
        all_stats.append(stats)
        total_uploaded += stats.get('records_uploaded', 0)
        total_errors += stats.get('errors', 0)

    # Summary
    print("\n" + "="*70)
    print("UPLOAD SUMMARY")
    print("="*70)
    print(f"Files processed: {len(files)}")
    print(f"Total records uploaded: {total_uploaded:,}")
    print(f"Total errors: {total_errors}")
    print("="*70)

    # Verify upload
    if not args.dry_run and total_uploaded > 0:
        try:
            result = client.table('florida_parcels').select('*', count='exact', head=True).execute()
            print(f"\nDatabase now has: {result.count:,} records in florida_parcels")
        except Exception as e:
            logger.error(f"Verification failed: {e}")


if __name__ == "__main__":
    main()
