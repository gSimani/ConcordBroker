#!/usr/bin/env python3
"""
Quick check of DOR code assignment status in Supabase
"""
import requests
import json

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def check_status():
    print("=" * 80)
    print("DOR CODE ASSIGNMENT STATUS CHECK")
    print("=" * 80)
    print()

    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    # Get total count
    print("Checking total properties...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers={**headers, "Range": "0-0", "Prefer": "count=exact"},
        params={"select": "parcel_id", "year": "eq.2025"}
    )

    total_count = 0
    if "content-range" in response.headers:
        total_count = int(response.headers["content-range"].split("/")[1])

    print(f"✓ Total properties (year 2025): {total_count:,}")
    print()

    # Get count with codes
    print("Checking properties with DOR codes...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers={**headers, "Range": "0-0", "Prefer": "count=exact"},
        params={
            "select": "parcel_id",
            "year": "eq.2025",
            "land_use_code": "not.is.null"
        }
    )

    with_code_count = 0
    if "content-range" in response.headers:
        with_code_count = int(response.headers["content-range"].split("/")[1])

    print(f"✓ Properties with DOR code: {with_code_count:,}")
    print()

    # Calculate coverage
    need_update = total_count - with_code_count
    coverage_pct = (with_code_count / total_count * 100) if total_count > 0 else 0

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Properties:        {total_count:>12,}")
    print(f"With DOR Code:           {with_code_count:>12,}")
    print(f"Need Assignment:         {need_update:>12,}")
    print(f"Coverage:                {coverage_pct:>11.2f}%")
    print()

    if coverage_pct < 99.5:
        print(f"⚠️  {need_update:,} properties need DOR code assignment")
        print("   Recommendation: Execute EXECUTE_DOR_ASSIGNMENT.sql")
    else:
        print("✅ Coverage is excellent! (≥99.5%)")

    print("=" * 80)

    # Sample some properties
    print()
    print("Sample properties:")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers=headers,
        params={
            "select": "parcel_id,county,land_use_code,property_use,just_value",
            "year": "eq.2025",
            "limit": "5"
        }
    )

    if response.status_code == 200:
        properties = response.json()
        for i, prop in enumerate(properties[:5], 1):
            code = prop.get('land_use_code') or 'NULL'
            use = prop.get('property_use') or 'NULL'
            value = prop.get('just_value') or 0
            print(f"{i}. {prop['parcel_id']:20s} | County: {prop['county']:12s} | Code: {code:3s} | Use: {use:10s} | Value: ${value:,}")

    print()

if __name__ == "__main__":
    try:
        check_status()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
