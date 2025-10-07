"""
Test NAP download for Broward County only
"""

import os
import requests
import zipfile
from pathlib import Path

# Test URLs for Broward County NAP files
NAP_2025P_BASE = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P"
NAP_2025F_BASE = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025F"

DOWNLOAD_DIR = Path("./nap_test")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Test patterns for Broward
patterns = [
    "broward_nap_2025.zip",
    "BROWARD_NAP_2025.zip",
    "broward_nap_2025P.zip",
    "BROWARD_NAP_2025P.zip",
    "browardnap2025.zip",
    "NAP_BROWARD_2025.zip",
    "nap_broward_2025.zip",
    "12_nap_2025.zip",  # County code 12 = Broward
    "NAP12_2025.zip",
]

print("Testing Broward County NAP Downloads")
print("=" * 60)

for base_name, base_url in [("2025P", NAP_2025P_BASE), ("2025F", NAP_2025F_BASE)]:
    print(f"\nTesting {base_name} directory:")

    for pattern in patterns:
        url = f"{base_url}/{pattern}"
        print(f"\nTrying: {url}")

        try:
            response = requests.get(url, timeout=30)
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"  Content-Length: {len(response.content)} bytes")

            if response.status_code == 200:
                # Save the response
                test_file = DOWNLOAD_DIR / f"test_{pattern}"
                with open(test_file, 'wb') as f:
                    f.write(response.content)

                # Check if it's a valid ZIP
                if zipfile.is_zipfile(test_file):
                    print(f"  [SUCCESS] Valid ZIP file!")
                    with zipfile.ZipFile(test_file, 'r') as z:
                        print(f"  Contents: {z.namelist()}")
                    break
                else:
                    print(f"  [FAIL] Not a valid ZIP file")
                    # Show first 200 chars to see if it's HTML
                    with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(200)
                        if '<html' in content.lower():
                            print(f"  [INFO] Response is HTML (probably 404 page)")

        except Exception as e:
            print(f"  [ERROR] {e}")

print("\n" + "=" * 60)
print("Test complete. Check nap_test/ directory for downloaded files.")
