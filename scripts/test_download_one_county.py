"""
Test download for a single county (BROWARD) to verify the process works
"""

import os
import requests
import zipfile
from pathlib import Path

# Base URL
BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/2025P"

# Test with BROWARD county
COUNTY = "BROWARD"

# Output directory
OUTPUT_DIR = Path("TEMP/DATABASE PROPERTY APP/SDF/2025P")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print(f"TEST DOWNLOAD - {COUNTY} COUNTY SDF FILE")
print("=" * 80)

# Construct URL
zip_filename = f"{COUNTY}_sdf_2025.zip"
url = f"{BASE_URL}/{zip_filename}"

print(f"\nURL: {url}")
print(f"Output: {OUTPUT_DIR.absolute()}")

# Try to download
print(f"\nDownloading {zip_filename}...")

try:
    response = requests.get(url, timeout=120)

    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content):,} bytes ({len(response.content) / (1024 * 1024):.2f} MB)")

    if response.status_code == 200:
        # Save ZIP file
        zip_path = OUTPUT_DIR / zip_filename
        with open(zip_path, 'wb') as f:
            f.write(response.content)

        print(f"Saved to: {zip_path}")

        # Unzip
        extract_dir = OUTPUT_DIR / COUNTY
        extract_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nExtracting to: {extract_dir}...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # List files
        extracted_files = list(extract_dir.glob("*"))
        print(f"\nExtracted {len(extracted_files)} files:")
        for file in extracted_files:
            size_kb = file.stat().st_size / 1024
            print(f"  - {file.name} ({size_kb:,.1f} KB)")

        # Read first few lines of .txt file
        txt_files = list(extract_dir.glob("*.txt"))
        if txt_files:
            print(f"\nFirst 5 lines of {txt_files[0].name}:")
            with open(txt_files[0], 'r', encoding='latin-1') as f:
                for i, line in enumerate(f, 1):
                    if i <= 5:
                        print(f"  {i}: {line[:100]}...")
                    else:
                        break

        # Clean up ZIP
        zip_path.unlink()

        print("\n" + "=" * 80)
        print("SUCCESS! Download and extraction working correctly")
        print("=" * 80)

    elif response.status_code == 404:
        print("\nERROR: File not found (404)")
        print("The 2025P SDF files may not be available yet")
    else:
        print(f"\nERROR: Unexpected status code {response.status_code}")

except requests.exceptions.Timeout:
    print("\nERROR: Download timed out")
except Exception as e:
    print(f"\nERROR: {e}")
