#!/usr/bin/env python3
"""
DOR Code Assignment - Batched by ID Range
Processes properties in ID-based batches to avoid timeouts
"""
import requests
import time
from datetime import datetime

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

BATCH_SIZE = 50000  # Process 50k IDs at a time
SLEEP_BETWEEN_BATCHES = 2  # 2 seconds between batches

def execute_sql(sql):
    """Execute SQL via Supabase SQL API"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    # Note: Direct SQL execution may be disabled
    # This is a fallback approach using the existing stored procedure

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/assign_dor_codes_batch",
        headers=headers,
        json={
            "target_county": "ALL",
            "batch_size": 5000
        },
        timeout=120
    )

    return response

def get_next_start_id():
    """Find the next ID range that needs processing"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
    }

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers=headers,
        params={
            "select": "id",
            "year": "eq.2025",
            "or": "(land_use_code.is.null,land_use_code.eq.,land_use_code.eq.99)",
            "order": "id.asc",
            "limit": 1
        },
        timeout=30
    )

    if response.status_code == 200 and response.json():
        return response.json()[0]['id']
    return None

def process_batch_by_county(county):
    """Process a single county"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/assign_dor_codes_batch",
            headers=headers,
            json={
                "target_county": county,
                "batch_size": 5000
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('processed_count', 0)
        return 0
    except Exception as e:
        print(f"Error processing {county}: {e}")
        return 0

def get_all_counties():
    """Get list of all counties with properties needing codes"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
    }

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers=headers,
        params={
            "select": "county",
            "year": "eq.2025",
            "or": "(land_use_code.is.null,land_use_code.eq.,land_use_code.eq.99)",
        },
        timeout=30
    )

    if response.status_code == 200:
        counties = set(p['county'] for p in response.json() if p.get('county'))
        return sorted(counties)
    return []

def check_coverage():
    """Check current coverage percentage"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Range": "0-0",
        "Prefer": "count=exact"
    }

    # Total count
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers=headers,
        params={"select": "id", "year": "eq.2025"}
    )

    total = 0
    if "content-range" in response.headers:
        total = int(response.headers["content-range"].split("/")[1])

    # With codes count
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers=headers,
        params={
            "select": "id",
            "year": "eq.2025",
            "land_use_code": "not.is.null"
        }
    )

    with_code = 0
    if "content-range" in response.headers:
        with_code = int(response.headers["content-range"].split("/")[1])

    coverage = (with_code / total * 100) if total > 0 else 0
    return total, with_code, coverage

def main():
    print("=" * 80)
    print("DOR CODE ASSIGNMENT - COUNTY-BY-COUNTY BATCH PROCESSOR")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check initial coverage
    print("Checking initial coverage...")
    total, with_code, coverage = check_coverage()
    print(f"Total Properties: {total:,}")
    print(f"With DOR Code: {with_code:,}")
    print(f"Coverage: {coverage:.2f}%")
    print(f"Need Assignment: {total - with_code:,}")
    print()

    # Get counties needing processing
    print("Getting counties needing processing...")
    counties = get_all_counties()
    print(f"Found {len(counties)} counties with properties needing codes")
    print()

    if not counties:
        print("✅ No counties need processing!")
        return

    # Process each county
    total_processed = 0
    for i, county in enumerate(counties, 1):
        print(f"[{i}/{len(counties)}] Processing {county}...")

        try:
            processed = process_batch_by_county(county)
            total_processed += processed
            print(f"[{i}/{len(counties)}] {county}: {processed:,} properties updated")

            # Sleep between counties
            if i < len(counties):
                print(f"[{i}/{len(counties)}] Sleeping {SLEEP_BETWEEN_BATCHES}s...")
                time.sleep(SLEEP_BETWEEN_BATCHES)
        except Exception as e:
            print(f"[{i}/{len(counties)}] ERROR processing {county}: {e}")
            continue

    print()
    print("=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)

    # Check final coverage
    print("Checking final coverage...")
    total, with_code, coverage = check_coverage()
    print(f"Total Properties: {total:,}")
    print(f"With DOR Code: {with_code:,}")
    print(f"Coverage: {coverage:.2f}%")
    print()

    # Grade the results
    if coverage >= 99.5:
        print("🎉 GRADE: 10/10 - PERFECT! ✅")
    elif coverage >= 95:
        print("🎉 GRADE: 9/10 - EXCELLENT! ✅")
    elif coverage >= 90:
        print("✓ GRADE: 8/10 - GOOD! ✅")
    elif coverage >= 80:
        print("✓ GRADE: 7/10 - ACCEPTABLE")
    else:
        print(f"⚠️  GRADE: 6/10 - Needs more work (only {coverage:.2f}%)")

    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
