"""
Florida SDF Sales Data Importer
Parses SDF files and imports sales data into Supabase property_sales_history table

SDF Record Layout (from Florida DOR documentation):
- Columns 1-19: Parcel ID
- Columns 20-21: County Code
- Columns 22-27: Qualified/Unqualified Sale Date (YYMMDD)
- Columns 28-38: Sale Price (cents, right-justified)
- Columns 39-73: Grantor Name
- Columns 74-108: Grantee Name
- Columns 109-113: OR Book Number
- Columns 114-117: OR Page Number
- Columns 118-134: Clerk Instrument Number
- Columns 135: VI Code (Validity Indicator)
- Columns 136: Sale Qualification (Q/U)
"""

import os
import csv
from pathlib import Path
from datetime import datetime
from supabase import create_client
from typing import List, Dict
import time

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Input directory
SDF_DIR = Path("TEMP/DATABASE PROPERTY APP/SDF/2025P")

# County code mapping
COUNTY_CODES = {
    "01": "ALACHUA", "02": "BAKER", "03": "BAY", "04": "BRADFORD", "05": "BREVARD",
    "06": "BROWARD", "07": "CALHOUN", "08": "CHARLOTTE", "09": "CITRUS", "10": "CLAY",
    "11": "COLLIER", "12": "COLUMBIA", "13": "DESOTO", "14": "DIXIE", "15": "DUVAL",
    "16": "ESCAMBIA", "17": "FLAGLER", "18": "FRANKLIN", "19": "GADSDEN", "20": "GILCHRIST",
    "21": "GLADES", "22": "GULF", "23": "HAMILTON", "24": "HARDEE", "25": "HENDRY",
    "26": "HERNANDO", "27": "HIGHLANDS", "28": "HILLSBOROUGH", "29": "HOLMES", "30": "INDIAN RIVER",
    "31": "JACKSON", "32": "JEFFERSON", "33": "LAFAYETTE", "34": "LAKE", "35": "LEE",
    "36": "LEON", "37": "LEVY", "38": "LIBERTY", "39": "MADISON", "40": "MANATEE",
    "41": "MARION", "42": "MARTIN", "43": "MIAMI-DADE", "44": "MONROE", "45": "NASSAU",
    "46": "OKALOOSA", "47": "OKEECHOBEE", "48": "ORANGE", "49": "OSCEOLA", "50": "PALM BEACH",
    "51": "PASCO", "52": "PINELLAS", "53": "POLK", "54": "PUTNAM", "55": "SANTA ROSA",
    "56": "SARASOTA", "57": "SEMINOLE", "58": "ST. JOHNS", "59": "ST. LUCIE", "60": "SUMTER",
    "61": "SUWANNEE", "62": "TAYLOR", "63": "UNION", "64": "VOLUSIA", "65": "WAKULLA",
    "66": "WALTON", "67": "WASHINGTON"
}

def parse_sdf_line(line: str) -> Dict | None:
    """Parse a single SDF line into a dictionary"""

    if len(line) < 136:
        return None

    try:
        # Extract fields based on fixed-width positions
        parcel_id = line[0:19].strip()
        county_code = line[19:21].strip()
        sale_date_raw = line[21:27].strip()  # YYMMDD
        sale_price_raw = line[27:38].strip()  # cents
        grantor = line[38:73].strip()
        grantee = line[73:108].strip()
        or_book = line[108:113].strip()
        or_page = line[113:117].strip()
        clerk_no = line[117:134].strip()
        vi_code = line[134:135].strip()
        quality_code = line[135:136].strip()

        # Validate parcel ID
        if not parcel_id or parcel_id == "0" * 19:
            return None

        # Parse sale date (YYMMDD to YYYY-MM-DD)
        if not sale_date_raw or len(sale_date_raw) != 6:
            return None

        yy = int(sale_date_raw[0:2])
        mm = int(sale_date_raw[2:4])
        dd = int(sale_date_raw[4:6])

        # Convert 2-digit year to 4-digit (assume 2000-2099)
        year = 2000 + yy

        # Validate date
        if mm < 1 or mm > 12 or dd < 1 or dd > 31:
            return None

        sale_date = f"{year:04d}-{mm:02d}-{dd:02d}"

        # Parse sale price (stored in cents)
        try:
            sale_price = int(sale_price_raw) if sale_price_raw else 0
        except ValueError:
            sale_price = 0

        # Skip sales with invalid prices
        if sale_price <= 0 or sale_price > 999999999999:  # Max $10B
            return None

        # Get county name from code
        county = COUNTY_CODES.get(county_code, f"UNKNOWN_{county_code}")

        return {
            'parcel_id': parcel_id,
            'county': county,
            'sale_date': sale_date,
            'sale_price': sale_price,  # In CENTS
            'sale_year': year,
            'sale_month': mm,
            'quality_code': quality_code if quality_code in ['Q', 'U'] else None,
            'clerk_no': clerk_no if clerk_no else None,
            'or_book': or_book if or_book else None,
            'or_page': or_page if or_page else None,
            'grantor_name': grantor if grantor else None,
            'grantee_name': grantee if grantee else None,
            'vi_code': vi_code if vi_code else None,
            'data_source': 'florida_sdf_2025p'
        }

    except Exception as e:
        print(f"    Parse error: {e}")
        return None

def import_county_sdf(county: str) -> tuple[int, int]:
    """Import SDF file for a single county"""

    county_filename = county.replace(" ", "_").upper()
    county_dir = SDF_DIR / county_filename

    if not county_dir.exists():
        print(f"  Directory not found: {county_dir}")
        return 0, 0

    # Find SDF .txt file
    sdf_files = list(county_dir.glob("*.txt"))

    if not sdf_files:
        print(f"  No .txt files found in {county_dir}")
        return 0, 0

    sdf_file = sdf_files[0]
    print(f"  Processing: {sdf_file.name}")

    sales_records = []
    parsed_count = 0
    skipped_count = 0

    # Parse SDF file
    with open(sdf_file, 'r', encoding='latin-1') as f:
        for line_num, line in enumerate(f, 1):
            record = parse_sdf_line(line)

            if record:
                sales_records.append(record)
                parsed_count += 1
            else:
                skipped_count += 1

            # Progress indicator
            if line_num % 10000 == 0:
                print(f"    Processed {line_num:,} lines, {parsed_count:,} valid sales...")

    print(f"  Parsed: {parsed_count:,} sales, Skipped: {skipped_count:,} invalid lines")

    if not sales_records:
        print(f"  No valid sales records to import")
        return 0, 0

    # Import to Supabase in batches
    BATCH_SIZE = 1000
    imported = 0
    errors = 0

    print(f"  Importing {len(sales_records):,} sales to Supabase...")

    for i in range(0, len(sales_records), BATCH_SIZE):
        batch = sales_records[i:i + BATCH_SIZE]

        try:
            result = supabase.table('property_sales_history').insert(batch).execute()
            imported += len(batch)

            if (i + BATCH_SIZE) % 10000 == 0:
                print(f"    Imported {imported:,} / {len(sales_records):,} sales...")

        except Exception as e:
            print(f"    Batch import error: {e}")
            errors += len(batch)

        # Rate limiting
        time.sleep(0.1)

    print(f"  Import complete: {imported:,} imported, {errors:,} errors")

    return imported, errors

def main():
    print("=" * 80)
    print("FLORIDA SDF SALES DATA IMPORTER")
    print("=" * 80)
    print(f"Input directory: {SDF_DIR.absolute()}")
    print()

    # Check if SDF directory exists
    if not SDF_DIR.exists():
        print(f"ERROR: SDF directory not found: {SDF_DIR}")
        print("Please run download_florida_sdf_2025.py first")
        return

    # Get list of county directories
    county_dirs = [d for d in SDF_DIR.iterdir() if d.is_dir()]

    if not county_dirs:
        print("ERROR: No county directories found")
        return

    print(f"Found {len(county_dirs)} counties to import")
    print()

    total_imported = 0
    total_errors = 0
    start_time = time.time()

    for i, county_dir in enumerate(sorted(county_dirs), 1):
        county = county_dir.name.replace("_", " ")

        print(f"\n[{i}/{len(county_dirs)}] {county}")

        imported, errors = import_county_sdf(county)

        total_imported += imported
        total_errors += errors

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Total counties processed: {len(county_dirs)}")
    print(f"Total sales imported: {total_imported:,}")
    print(f"Total errors: {total_errors:,}")
    print(f"Total time: {elapsed / 60:.1f} minutes")
    print("=" * 80)

    # Verify count in database
    print("\nVerifying database count...")
    try:
        result = supabase.table('property_sales_history').select('*', count='exact').limit(0).execute()
        print(f"Total records in property_sales_history: {result.count:,}")
    except Exception as e:
        print(f"ERROR verifying count: {e}")

if __name__ == "__main__":
    main()
