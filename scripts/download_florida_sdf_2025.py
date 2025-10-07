"""
Florida SDF (Sales Disclosure Files) Downloader - 2025 Preliminary
Downloads all 67 Florida county SDF files from Florida DOR Data Portal
URL: https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P
"""

import os
import requests
import zipfile
import time
from pathlib import Path

# Base URL for 2025 Preliminary SDF files
BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P"

# All 67 Florida counties
FLORIDA_COUNTIES = [
    "ALACHUA", "BAKER", "BAY", "BRADFORD", "BREVARD", "BROWARD", "CALHOUN",
    "CHARLOTTE", "CITRUS", "CLAY", "COLLIER", "COLUMBIA", "DESOTO", "DIXIE",
    "DUVAL", "ESCAMBIA", "FLAGLER", "FRANKLIN", "GADSDEN", "GILCHRIST", "GLADES",
    "GULF", "HAMILTON", "HARDEE", "HENDRY", "HERNANDO", "HIGHLANDS", "HILLSBOROUGH",
    "HOLMES", "INDIAN RIVER", "JACKSON", "JEFFERSON", "LAFAYETTE", "LAKE", "LEE",
    "LEON", "LEVY", "LIBERTY", "MADISON", "MANATEE", "MARION", "MARTIN", "MIAMI-DADE",
    "MONROE", "NASSAU", "OKALOOSA", "OKEECHOBEE", "ORANGE", "OSCEOLA", "PALM BEACH",
    "PASCO", "PINELLAS", "POLK", "PUTNAM", "SANTA ROSA", "SARASOTA", "SEMINOLE",
    "ST. JOHNS", "ST. LUCIE", "SUMTER", "SUWANNEE", "TAYLOR", "UNION", "VOLUSIA",
    "WAKULLA", "WALTON", "WASHINGTON"
]

# Output directory
OUTPUT_DIR = Path("TEMP/DATABASE PROPERTY APP/SDF/2025P")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_county_sdf(county: str) -> bool:
    """Download and unzip SDF file for a single county"""

    # Format county name for filename (spaces to underscores, uppercase)
    county_filename = county.replace(" ", "_").upper()

    # Construct URL (e.g., ALACHUA_sdf_2025.zip)
    zip_filename = f"{county_filename}_sdf_2025.zip"
    url = f"{BASE_URL}/{zip_filename}"

    # Output paths
    zip_path = OUTPUT_DIR / zip_filename
    extract_dir = OUTPUT_DIR / county_filename

    print(f"\n[{county}]")
    print(f"  URL: {url}")

    try:
        # Download ZIP file
        print(f"  Downloading {zip_filename}...")
        response = requests.get(url, timeout=120)

        if response.status_code == 200:
            # Save ZIP file
            with open(zip_path, 'wb') as f:
                f.write(response.content)

            file_size_mb = len(response.content) / (1024 * 1024)
            print(f"  Downloaded: {file_size_mb:.2f} MB")

            # Unzip file
            print(f"  Unzipping...")
            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # List extracted files
            extracted_files = list(extract_dir.glob("*.txt"))
            print(f"  Extracted {len(extracted_files)} files:")
            for file in extracted_files:
                print(f"    - {file.name} ({file.stat().st_size / 1024:.1f} KB)")

            # Clean up ZIP file
            zip_path.unlink()

            return True

        elif response.status_code == 404:
            print(f"  NOT FOUND (404) - County may not have 2025P data yet")
            return False
        else:
            print(f"  ERROR: HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print(f"  TIMEOUT - Download took too long")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    print("=" * 80)
    print("FLORIDA SDF 2025 PRELIMINARY - DOWNLOAD ALL COUNTIES")
    print("=" * 80)
    print(f"Total counties: {len(FLORIDA_COUNTIES)}")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print()

    successful = 0
    failed = 0
    not_found = 0

    start_time = time.time()

    for i, county in enumerate(FLORIDA_COUNTIES, 1):
        print(f"\n[{i}/{len(FLORIDA_COUNTIES)}] Processing {county}...")

        result = download_county_sdf(county)

        if result:
            successful += 1
        else:
            # Check if it's a 404 or actual error
            county_filename = county.replace(" ", "_").upper()
            zip_filename = f"{county_filename}_sdf_2025.zip"
            url = f"{BASE_URL}/{zip_filename}"

            try:
                resp = requests.head(url, timeout=10)
                if resp.status_code == 404:
                    not_found += 1
                else:
                    failed += 1
            except:
                failed += 1

        # Rate limiting - be nice to the server
        if i < len(FLORIDA_COUNTIES):
            time.sleep(2)

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)
    print(f"Successful: {successful}")
    print(f"Not Found (404): {not_found}")
    print(f"Failed: {failed}")
    print(f"Total Time: {elapsed / 60:.1f} minutes")
    print(f"\nFiles saved to: {OUTPUT_DIR.absolute()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
