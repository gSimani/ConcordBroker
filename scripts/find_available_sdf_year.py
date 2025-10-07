"""
Find which year's SDF files are actually available
"""

import requests

BASE_URL_TEMPLATE = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/{year}"

YEARS_TO_TEST = ["2025P", "2025", "2024", "2023"]
TEST_COUNTY = "BROWARD"

print("=" * 80)
print("FINDING AVAILABLE SDF FILES")
print("=" * 80)
print(f"\nTesting county: {TEST_COUNTY}")
print()

for year in YEARS_TO_TEST:
    base_url = BASE_URL_TEMPLATE.format(year=year)
    zip_filename = f"{TEST_COUNTY}_sdf_{year.lower()}.zip"
    url = f"{base_url}/{zip_filename}"

    print(f"[{year}] {url}")

    try:
        response = requests.head(url, timeout=10)

        if response.status_code == 200:
            print(f"    SUCCESS - Files available for {year}")
            print(f"    Full URL pattern: {base_url}/{{COUNTY}}_sdf_{year.lower()}.zip")
            break
        elif response.status_code == 404:
            print(f"    404 - Not available")
        else:
            print(f"    {response.status_code} - Unexpected")

    except Exception as e:
        print(f"    ERROR: {e}")

print("\n" + "=" * 80)
