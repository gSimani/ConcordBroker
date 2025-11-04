"""
Upload Tax Deed Auctions - FIXED Environment Variable Version
Explicitly overrides system env var with correct key from .env.mcp
"""

import os
import sys
import json
import requests
from dotenv import dotenv_values

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# IMPORTANT: Explicitly load from .env.mcp and override system env vars
print("="*80)
print("LOADING ENVIRONMENT FROM .env.mcp")
print("="*80)

# Load values from .env.mcp
env_values = dotenv_values('.env.mcp')

# Explicitly override system environment variables
SUPABASE_URL = env_values.get('SUPABASE_URL')
SERVICE_ROLE_KEY = env_values.get('SUPABASE_SERVICE_ROLE_KEY')

print(f"\nSUPABASE_URL: {SUPABASE_URL}")
print(f"SERVICE_ROLE_KEY (first 30 chars): {SERVICE_ROLE_KEY[:30] if SERVICE_ROLE_KEY else 'NONE'}...")
print(f"SERVICE_ROLE_KEY (last 30 chars): ...{SERVICE_ROLE_KEY[-30:] if SERVICE_ROLE_KEY else 'NONE'}")
print(f"SERVICE_ROLE_KEY length: {len(SERVICE_ROLE_KEY)} characters")

# Verify project reference in JWT
parts = SERVICE_ROLE_KEY.split('.')
if len(parts) == 3:
    import base64
    payload_encoded = parts[1]
    padding = 4 - len(payload_encoded) % 4
    if padding != 4:
        payload_encoded += '=' * padding
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_encoded))
        ref = payload.get('ref', 'N/A')
        expected_ref = SUPABASE_URL.split('//')[1].split('.')[0]
        print(f"\nJWT Project Reference: {ref}")
        print(f"Expected from URL: {expected_ref}")
        if ref == expected_ref:
            print("✅ Project reference MATCHES!")
        else:
            print(f"❌ Project reference MISMATCH!")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️  Could not decode JWT: {e}")

# PostgREST endpoint
postgrest_url = f"{SUPABASE_URL}/rest/v1/tax_deed_bidding_items"

# Headers with service_role authentication
headers = {
    'apikey': SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'  # For upsert
}

def upload_auctions_from_json(json_file: str):
    """Upload auctions from JSON backup file using direct HTTP"""

    print(f"\n{'='*80}")
    print(f"UPLOADING TAX DEED AUCTIONS VIA DIRECT HTTP")
    print(f"{'='*80}")
    print(f"Reading from: {json_file}")

    # Read JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        auctions = json.load(f)

    print(f"✓ Loaded {len(auctions)} auctions from JSON")

    saved_count = 0
    error_count = 0

    for idx, auction in enumerate(auctions, 1):
        try:
            # Generate composite key
            composite_key = f"{auction.get('case_number', 'UNKNOWN')}_{auction.get('parcel_id', 'UNKNOWN')}_{auction.get('county', 'UNKNOWN')}"

            # Prepare data for database
            data = {
                'composite_key': composite_key,
                'county': auction.get('county'),
                'tax_deed_number': auction.get('case_number'),
                'parcel_id': auction.get('parcel_id'),
                'legal_situs_address': auction.get('full_address', auction.get('address')),
                'opening_bid': auction.get('opening_bid_clean'),
                'assessed_value': auction.get('assessed_value_clean'),
                'item_status': auction.get('status', 'Active'),
                'source_url': auction.get('source_url'),
                'scraped_at': auction.get('scraped_at'),
                'close_time': auction.get('auction_date'),
                'auction_description': f"Certificate: {auction.get('certificate', 'N/A')}"
            }

            # POST to PostgREST with upsert (on_conflict query parameter)
            response = requests.post(
                postgrest_url,
                headers=headers,
                params={'on_conflict': 'composite_key'},
                json=data
            )

            if response.status_code in [200, 201]:
                saved_count += 1
                if saved_count % 10 == 0:
                    print(f"  ✓ Saved {saved_count}/{len(auctions)} auctions...")
            else:
                error_count += 1
                print(f"  ✗ Error saving {auction.get('case_number', 'unknown')}: HTTP {response.status_code} - {response.text}")
                # Show first error details
                if error_count == 1:
                    print(f"\nFirst Error Details:")
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                    print(f"  Headers: {dict(response.headers)}")

        except Exception as e:
            error_count += 1
            print(f"  ✗ Exception saving {auction.get('case_number', 'unknown')}: {e}")

    print(f"\n{'='*80}")
    print(f"UPLOAD COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Successfully saved: {saved_count}")
    print(f"✗ Errors: {error_count}")

    # County breakdown
    print(f"\nCounty Breakdown:")
    counties = {}
    for auction in auctions:
        county = auction.get('county', 'Unknown')
        counties[county] = counties.get(county, 0) + 1

    for county, count in counties.items():
        print(f"  {county}: {count} auctions")

    return {'saved': saved_count, 'errors': error_count}


if __name__ == "__main__":
    # Find the most recent JSON backup file
    import glob

    # Look for both unified and county-specific files
    json_files = glob.glob('unified_tax_deed_auctions_*.json') + glob.glob('*_tax_deed_auctions_*.json')

    if not json_files:
        print("ERROR: No JSON backup files found!")
        print("Looking for: unified_tax_deed_auctions_*.json or *_tax_deed_auctions_*.json")
        sys.exit(1)

    # Get most recent file
    latest_file = max(json_files, key=os.path.getctime)

    print(f"\nFound JSON backup: {latest_file}")

    # Upload to database
    stats = upload_auctions_from_json(latest_file)

    if stats['saved'] > 0:
        print(f"\n✅ SUCCESS! Uploaded {stats['saved']} auctions to Supabase")
        print(f"\nYou can now view them at: http://localhost:5191/tax-deed-sales")
    else:
        print(f"\n❌ FAILED! No auctions were uploaded. Check errors above.")
