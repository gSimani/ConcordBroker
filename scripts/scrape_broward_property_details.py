"""
Scrape Broward County Property Appraiser website for missing bedroom/bathroom data
Updates florida_parcels table with accurate property characteristics
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
import time
from datetime import datetime

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def scrape_broward_property(parcel_id: str) -> dict:
    """
    Scrape property details from Broward County Property Appraiser website

    Args:
        parcel_id: Broward County parcel ID (e.g., "474130030430")

    Returns:
        Dictionary with property characteristics
    """
    url = f"https://bcpa.net/RecInfo.asp?URL_Folio={parcel_id}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch {parcel_id}: HTTP {response.status_code}")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract data from the page
        data = {}

        # Find all table cells and extract key-value pairs
        cells = soup.find_all('td')

        for i in range(len(cells) - 1):
            label = cells[i].get_text(strip=True)
            value = cells[i + 1].get_text(strip=True)

            # Bedrooms
            if 'Bedrooms' in label or 'BED' in label.upper():
                try:
                    data['bedrooms'] = int(re.search(r'\d+', value).group())
                except:
                    pass

            # Bathrooms
            if 'Bathrooms' in label or 'BATH' in label.upper():
                try:
                    data['bathrooms'] = int(float(re.search(r'[\d.]+', value).group()))
                except:
                    pass

            # Units
            if 'Units' in label or 'UNIT' in label.upper():
                try:
                    data['units'] = int(re.search(r'\d+', value).group())
                except:
                    pass

            # DOR Use Code
            if 'DOR' in label.upper() and 'Code' in label:
                match = re.search(r'\d+-\d+', value)
                if match:
                    data['property_use'] = match.group()

            # Year Built
            if 'Year Built' in label or 'YR BUILT' in label.upper():
                try:
                    year = int(re.search(r'\d{4}', value).group())
                    if 1800 < year <= datetime.now().year:
                        data['year_built'] = year
                except:
                    pass

            # Living Area
            if 'Living' in label and 'Area' in label:
                try:
                    sqft = int(re.search(r'[\d,]+', value).group().replace(',', ''))
                    data['total_living_area'] = sqft
                except:
                    pass

        return data

    except Exception as e:
        print(f"[ERROR] Exception scraping {parcel_id}: {e}")
        return {}


def get_broward_properties_missing_bedrooms() -> list:
    """
    Get Broward County properties from database that are missing bedroom/bathroom data

    Returns:
        List of property dictionaries with parcel_id
    """
    try:
        # Query for Broward properties with null bedrooms
        response = supabase.table('florida_parcels')\
            .select('parcel_id, bedrooms, bathrooms, property_use')\
            .eq('county', 'BROWARD')\
            .is_('bedrooms', 'null')\
            .limit(100)\
            .execute()

        return response.data if response.data else []

    except Exception as e:
        print(f"[ERROR] Failed to query database: {e}")
        return []


def update_property(parcel_id: str, data: dict) -> bool:
    """
    Update property in database with scraped data

    Args:
        parcel_id: Property parcel ID
        data: Dictionary of property data to update

    Returns:
        True if successful, False otherwise
    """
    if not data:
        return False

    try:
        result = supabase.table('florida_parcels')\
            .update(data)\
            .eq('parcel_id', parcel_id)\
            .eq('county', 'BROWARD')\
            .execute()

        return True

    except Exception as e:
        print(f"[ERROR] Failed to update {parcel_id}: {e}")
        return False


def main():
    """
    Main function to scrape and update Broward properties
    """
    print("Broward County Property Data Scraper")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)

    # Get properties missing bedroom data
    print("\nQuerying database for properties missing bedroom data...")
    properties = get_broward_properties_missing_bedrooms()
    print(f"Found {len(properties)} properties missing bedroom data")

    if not properties:
        print("No properties to update!")
        return

    # Process each property
    updated_count = 0
    failed_count = 0

    for i, prop in enumerate(properties, 1):
        parcel_id = prop['parcel_id']

        print(f"\n[{i}/{len(properties)}] Processing {parcel_id}...")

        # Scrape data
        scraped_data = scrape_broward_property(parcel_id)

        if scraped_data:
            print(f"  Found: {scraped_data}")

            # Update database
            if update_property(parcel_id, scraped_data):
                print(f"  [OK] Updated successfully")
                updated_count += 1
            else:
                print(f"  [FAIL] Update failed")
                failed_count += 1
        else:
            print(f"  [SKIP] No data found")
            failed_count += 1

        # Rate limiting - be nice to their server
        time.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total processed: {len(properties)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed/Skipped: {failed_count}")
    print(f"\nCompleted at: {datetime.now()}")


if __name__ == "__main__":
    main()
