#!/usr/bin/env python3
"""
Florida Property Data Downloader
Downloads all property data files (NAL, NAP, NAV, SDF) for all Florida counties
"""

import os
import requests
import time
from pathlib import Path
from datetime import datetime
import concurrent.futures
from tqdm import tqdm

# Base configuration
BASE_URL = "https://floridarevenue.com/property/dataportal/DataPortal_Files/"
OUTPUT_BASE = r"C:\TEMP\DATABASE PROPERTY APP"
YEAR = "2025"

# All Florida Counties with their codes
COUNTIES = {
    "01": "ALACHUA", "02": "BAKER", "03": "BAY", "04": "BRADFORD",
    "05": "BREVARD", "06": "BROWARD", "07": "CALHOUN", "08": "CHARLOTTE",
    "09": "CITRUS", "10": "CLAY", "11": "COLLIER", "12": "COLUMBIA",
    "13": "MIAMI-DADE", "14": "DESOTO", "15": "DIXIE", "16": "DUVAL",
    "17": "ESCAMBIA", "18": "FLAGLER", "19": "FRANKLIN", "20": "GADSDEN",
    "21": "GILCHRIST", "22": "GLADES", "23": "GULF", "24": "HAMILTON",
    "25": "HARDEE", "26": "HENDRY", "27": "HERNANDO", "28": "HIGHLANDS",
    "29": "HILLSBOROUGH", "30": "HOLMES", "31": "INDIAN_RIVER", "32": "JACKSON",
    "33": "JEFFERSON", "34": "LAFAYETTE", "35": "LAKE", "36": "LEE",
    "37": "LEON", "38": "LEVY", "39": "LIBERTY", "40": "MADISON",
    "41": "MANATEE", "42": "MARION", "43": "MARTIN", "44": "MONROE",
    "45": "NASSAU", "46": "OKALOOSA", "47": "OKEECHOBEE", "48": "ORANGE",
    "49": "OSCEOLA", "50": "PALM_BEACH", "51": "PASCO", "52": "PINELLAS",
    "53": "POLK", "54": "PUTNAM", "55": "ST_JOHNS", "56": "ST_LUCIE",
    "57": "SANTA_ROSA", "58": "SARASOTA", "59": "SEMINOLE", "60": "SUMTER",
    "61": "SUWANNEE", "62": "TAYLOR", "63": "UNION", "64": "VOLUSIA",
    "65": "WAKULLA", "66": "WALTON", "67": "WASHINGTON"
}

# File types to download
FILE_TYPES = ["NAL", "NAP", "NAV", "SDF"]

# Priority counties (major metros - download these first)
PRIORITY_COUNTIES = ["06", "13", "50", "48", "52", "29", "16", "36", "11", "58"]


def download_file(url, dest_path, max_retries=3):
    """Download a file with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Get total file size
            total_size = int(response.headers.get('content-length', 0))

            # Download with progress
            with open(dest_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

            return True, os.path.getsize(dest_path)

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                return False, str(e)


def download_county_file(county_code, county_name, file_type):
    """Download a single county file"""
    # Create directory structure
    county_path = Path(OUTPUT_BASE) / county_name
    type_path = county_path / file_type
    type_path.mkdir(parents=True, exist_ok=True)

    # File names
    source_filename = f"{county_code}_{file_type}_{YEAR}.txt"
    dest_filename = f"{county_name}_{file_type}_{YEAR}.csv"
    dest_path = type_path / dest_filename

    # Skip if already exists
    if dest_path.exists():
        size_mb = dest_path.stat().st_size / (1024 * 1024)
        return True, f"EXISTS ({size_mb:.2f} MB)"

    # Build URL
    url = f"{BASE_URL}{YEAR}/{source_filename}"

    # Download
    success, result = download_file(url, str(dest_path))

    if success:
        size_mb = result / (1024 * 1024)
        return True, f"OK ({size_mb:.2f} MB)"
    else:
        return False, f"FAILED: {result}"


def main():
    """Main download function"""
    print("=" * 60)
    print("FLORIDA PROPERTY DATA DOWNLOADER")
    print("=" * 60)
    print(f"Output Directory: {OUTPUT_BASE}")
    print(f"Year: {YEAR}")
    print(f"Total Counties: {len(COUNTIES)}")
    print(f"File Types: {', '.join(FILE_TYPES)}")
    print("=" * 60)

    # Create base directory
    Path(OUTPUT_BASE).mkdir(parents=True, exist_ok=True)

    # Statistics
    total_files = len(COUNTIES) * len(FILE_TYPES)
    success_count = 0
    fail_count = 0
    start_time = datetime.now()

    # Download priority counties first
    print("\n📍 DOWNLOADING PRIORITY COUNTIES (Major Metros):")
    print("-" * 50)

    for code in PRIORITY_COUNTIES:
        county_name = COUNTIES.get(code)
        if not county_name:
            continue

        print(f"\n[{code}] {county_name}")

        for file_type in FILE_TYPES:
            success, message = download_county_file(code, county_name, file_type)
            print(f"  {file_type}: {message}")

            if success:
                success_count += 1
            else:
                fail_count += 1

    # Download remaining counties
    print("\n\n📍 DOWNLOADING REMAINING COUNTIES:")
    print("-" * 50)

    remaining = [(k, v) for k, v in COUNTIES.items() if k not in PRIORITY_COUNTIES]

    for code, county_name in sorted(remaining):
        print(f"\n[{code}] {county_name}")

        for file_type in FILE_TYPES:
            success, message = download_county_file(code, county_name, file_type)
            print(f"  {file_type}: {message}")

            if success:
                success_count += 1
            else:
                fail_count += 1

    # Summary
    duration = datetime.now() - start_time

    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Total Files: {total_files}")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"⏱️  Duration: {duration}")

    # List complete counties
    print("\n✅ COUNTIES WITH COMPLETE DATA:")
    complete_counties = []

    for code, county_name in sorted(COUNTIES.items(), key=lambda x: x[1]):
        county_path = Path(OUTPUT_BASE) / county_name
        if county_path.exists():
            csv_files = list(county_path.rglob("*.csv"))
            if len(csv_files) == 4:
                complete_counties.append(county_name)
                print(f"  ✓ {county_name}")

    print(f"\nTotal complete: {len(complete_counties)}/{len(COUNTIES)} counties")

    # Special note for Broward (property 514124070600)
    if "06" in [k for k, v in COUNTIES.items() if v in complete_counties]:
        print("\n✅ BROWARD COUNTY DATA AVAILABLE!")
        print("Property 514124070600 sales data can now be imported.")

    print("\n✨ Download complete!")
    print("Next step: Run 'python import-to-supabase.py' to import into database")


if __name__ == "__main__":
    # Check for required packages
    try:
        import requests
        import tqdm
    except ImportError:
        print("Installing required packages...")
        os.system("pip install requests tqdm")
        import requests
        from tqdm import tqdm

    main()