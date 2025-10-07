"""
Import NAP (Property Characteristics) data for all Florida counties
This script downloads NAP files from Florida DOR and updates the florida_parcels table
with bedroom, bathroom, units, and accurate property use codes.
"""

import os
import requests
import zipfile
import csv
import time
from pathlib import Path
from supabase import create_client, Client
from datetime import datetime

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Florida counties (alphabetical order)
FLORIDA_COUNTIES = [
    "alachua", "baker", "bay", "bradford", "brevard", "broward", "calhoun", "charlotte",
    "citrus", "clay", "collier", "columbia", "desoto", "dixie", "duval", "escambia",
    "flagler", "franklin", "gadsden", "gilchrist", "glades", "gulf", "hamilton", "hardee",
    "hendry", "hernando", "highlands", "hillsborough", "holmes", "indian_river", "jackson",
    "jefferson", "lafayette", "lake", "lee", "leon", "levy", "liberty", "madison", "manatee",
    "marion", "martin", "miami-dade", "monroe", "nassau", "okaloosa", "okeechobee", "orange",
    "osceola", "palm_beach", "pasco", "pinellas", "polk", "putnam", "santa_rosa", "sarasota",
    "seminole", "st_johns", "st_lucie", "sumter", "suwannee", "taylor", "union", "volusia",
    "wakulla", "walton", "washington"
]

# Base URLs for NAP data
NAP_2025P_BASE = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P"
NAP_2025F_BASE = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025F"

# Directory for downloaded files
DOWNLOAD_DIR = Path("./nap_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# NAP column mapping (standard Florida DOR NAP format)
# Map NAP CSV columns to our florida_parcels table columns
NAP_COLUMN_MAPPING = {
    # Required identifier columns
    'PARCEL_ID': 'parcel_id',
    'COUNTY_NO': 'county_no',

    # Building characteristics
    'NO_BULDNG': 'units',  # Number of buildings/units
    'NO_RES_UNTS': 'units',  # Residential units (alternative)
    'ACT_YR_BLT': 'year_built',
    'EFF_YR_BLT': 'effective_year_built',

    # Room counts
    'BEDROOMS': 'bedrooms',
    'BATHROOMS': 'bathrooms',
    'TOT_LVG_AREA': 'total_living_area',
    'NO_OF_BUILDINGS': 'units',
    'STORIES': 'stories',

    # Property classification
    'DOR_UC': 'property_use',  # DOR Use Code (e.g., "01-05")
    'LND_SQFOOT': 'land_sqft',
    'LND_VAL': 'land_value',
    'BLDG_VAL': 'building_value',
    'JV': 'just_value',
}


def download_nap_file(county: str, year_version: str = "2025P") -> Path | None:
    """
    Download NAP ZIP file for a specific county

    Args:
        county: County name (lowercase, underscores for spaces)
        year_version: "2025P" or "2025F"

    Returns:
        Path to downloaded ZIP file or None if download failed
    """
    # Try different naming patterns
    base_url = NAP_2025P_BASE if year_version == "2025P" else NAP_2025F_BASE

    # Common file name patterns Florida uses
    patterns = [
        f"{county}_nap_2025.zip",
        f"{county.upper()}_NAP_2025.zip",
        f"{county.replace('_', '')}_nap_2025.zip",
        f"NAP_{county.upper()}_2025.zip",
    ]

    for pattern in patterns:
        url = f"{base_url}/{pattern}"
        zip_path = DOWNLOAD_DIR / f"{county}_nap_{year_version}.zip"

        print(f"Trying to download: {url}")

        try:
            response = requests.get(url, timeout=60)

            # Check if we got actual ZIP data (not HTML error page)
            if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('application'):
                with open(zip_path, 'wb') as f:
                    f.write(response.content)

                # Verify it's a valid ZIP file
                if zipfile.is_zipfile(zip_path):
                    print(f"[OK] Successfully downloaded {county} NAP file: {zip_path}")
                    return zip_path
                else:
                    print(f"[ERROR] Downloaded file is not a valid ZIP: {zip_path}")
                    zip_path.unlink()
            else:
                print(f"[ERROR] Got non-ZIP response (status {response.status_code})")

        except Exception as e:
            print(f"[ERROR] Error downloading {url}: {e}")

    print(f"[ERROR] Could not download NAP file for {county}")
    return None


def extract_nap_csv(zip_path: Path) -> Path | None:
    """
    Extract CSV file from NAP ZIP archive

    Args:
        zip_path: Path to ZIP file

    Returns:
        Path to extracted CSV file or None
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the CSV file (usually named like "broward_nap_2025.csv")
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv') or f.endswith('.txt')]

            if not csv_files:
                print(f"[ERROR] No CSV file found in {zip_path}")
                return None

            # Extract the first CSV file
            csv_file = csv_files[0]
            extract_dir = DOWNLOAD_DIR / zip_path.stem
            extract_dir.mkdir(exist_ok=True)

            zip_ref.extract(csv_file, extract_dir)
            csv_path = extract_dir / csv_file

            print(f"[OK] Extracted CSV: {csv_path}")
            return csv_path

    except Exception as e:
        print(f"[ERROR] Error extracting {zip_path}: {e}")
        return None


def parse_nap_csv(csv_path: Path, county: str) -> list[dict]:
    """
    Parse NAP CSV and extract property characteristics

    Args:
        csv_path: Path to CSV file
        county: County name

    Returns:
        List of property data dictionaries
    """
    properties = []

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Try to detect delimiter (could be comma or pipe)
            first_line = f.readline()
            f.seek(0)
            delimiter = '|' if '|' in first_line else ','

            reader = csv.DictReader(f, delimiter=delimiter)

            for row in reader:
                # Map NAP columns to our schema
                property_data = {
                    'county': county.upper(),
                }

                # Extract parcel ID (required)
                parcel_id = row.get('PARCEL_ID') or row.get('parcel_id') or row.get('Parcel_ID')
                if not parcel_id:
                    continue  # Skip rows without parcel ID

                property_data['parcel_id'] = parcel_id.strip()

                # Map other columns
                for nap_col, our_col in NAP_COLUMN_MAPPING.items():
                    if nap_col in row and row[nap_col]:
                        value = row[nap_col].strip()

                        # Convert numeric fields
                        if our_col in ['bedrooms', 'bathrooms', 'units', 'stories', 'year_built']:
                            try:
                                property_data[our_col] = int(float(value)) if value else None
                            except:
                                pass
                        elif our_col in ['total_living_area', 'land_sqft', 'land_value', 'building_value', 'just_value']:
                            try:
                                property_data[our_col] = float(value) if value else None
                            except:
                                pass
                        else:
                            property_data[our_col] = value

                if len(property_data) > 2:  # Has more than just county and parcel_id
                    properties.append(property_data)

        print(f"[OK] Parsed {len(properties)} properties from {csv_path}")
        return properties

    except Exception as e:
        print(f"[ERROR] Error parsing {csv_path}: {e}")
        return []


def update_supabase_batch(properties: list[dict], batch_size: int = 1000):
    """
    Update florida_parcels table with NAP data in batches

    Args:
        properties: List of property data dictionaries
        batch_size: Number of records per batch
    """
    total = len(properties)
    updated = 0
    errors = 0

    print(f"Updating {total} properties in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = properties[i:i+batch_size]

        for prop in batch:
            try:
                # Update existing record
                result = supabase.table('florida_parcels')\
                    .update(prop)\
                    .eq('parcel_id', prop['parcel_id'])\
                    .eq('county', prop['county'])\
                    .execute()

                updated += 1

            except Exception as e:
                print(f"[ERROR] Error updating {prop['parcel_id']}: {e}")
                errors += 1

        # Progress report
        print(f"  Progress: {min(i+batch_size, total)}/{total} ({updated} updated, {errors} errors)")
        time.sleep(0.1)  # Rate limiting

    print(f"[OK] Finished: {updated} updated, {errors} errors")


def process_county(county: str, year_version: str = "2025P"):
    """
    Download, parse, and import NAP data for a single county

    Args:
        county: County name
        year_version: "2025P" or "2025F"
    """
    print(f"\n{'='*60}")
    print(f"Processing {county.upper()} County - NAP {year_version}")
    print(f"{'='*60}")

    # Download
    zip_path = download_nap_file(county, year_version)
    if not zip_path:
        return False

    # Extract
    csv_path = extract_nap_csv(zip_path)
    if not csv_path:
        return False

    # Parse
    properties = parse_nap_csv(csv_path, county)
    if not properties:
        return False

    # Update database
    update_supabase_batch(properties)

    # Cleanup
    try:
        csv_path.unlink()
        zip_path.unlink()
    except:
        pass

    return True


def main():
    """
    Main function to process all counties
    """
    print("Florida NAP Data Import")
    print(f"Started at: {datetime.now()}")

    # Try 2025P first, fallback to 2025F if needed
    year_versions = ["2025P", "2025F"]

    success_count = 0
    failed_counties = []

    for county in FLORIDA_COUNTIES:
        success = False

        for year_version in year_versions:
            if process_county(county, year_version):
                success = True
                success_count += 1
                break

        if not success:
            failed_counties.append(county)

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total counties: {len(FLORIDA_COUNTIES)}")
    print(f"Successfully imported: {success_count}")
    print(f"Failed: {len(failed_counties)}")

    if failed_counties:
        print(f"\nFailed counties:")
        for county in failed_counties:
            print(f"  - {county}")

    print(f"\nCompleted at: {datetime.now()}")


if __name__ == "__main__":
    main()
