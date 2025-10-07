"""
Micro-Batched DOR Assignment - Optimized for Timeout Avoidance
Processes 50k rows at a time using ID ranges within each county
"""

import requests
import time
from datetime import datetime
import json

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json"
}

# Top counties by volume
TOP_COUNTIES = [
    ("DADE", 1084021),
    ("LEE", 596266),
    ("ORANGE", 553213),
    ("BROWARD", 433746),
    ("HILLSBOROUGH", 391715),
    ("MIAMI-DADE", 340188),
    ("COLLIER", 327686),
    ("PASCO", 254648),
    ("CHARLOTTE", 206119),
    ("BREVARD", 189205)
]

def classify_property(prop):
    """Classify a single property - OPTIMIZED"""
    bldg = prop.get("building_value") or 0
    land = prop.get("land_value") or 0
    just = prop.get("just_value") or 0

    # Multi-Family 10+
    if bldg > 500000 and land > 0 and bldg > land * 2:
        return ("02", "MF 10+")
    # Industrial
    if bldg > 1000000 and land < 500000:
        return ("24", "Industria")
    # Commercial
    if just > 500000 and bldg > 200000 and land > 0 and (land * 0.3 <= bldg <= land * 4):
        return ("17", "Commercia")
    # Agricultural
    if bldg > 0 and land > bldg * 5 and land > 100000:
        return ("01", "Agricult.")
    # Condominium
    if 100000 <= just <= 500000 and 50000 <= bldg <= 300000 and land > 0 and (land * 0.8 <= bldg <= land * 1.5):
        return ("03", "Condo")
    # Vacant Residential
    if land > 0 and bldg < 1000:
        return ("10", "Vacant Re")
    # Single Family
    if bldg > 50000 and bldg > land and just < 1000000:
        return ("00", "SFR")
    # Default
    return ("00", "SFR")

def get_id_range_for_county(county):
    """Get min and max ID for a county"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

    # Get min ID
    params = {
        "select": "id",
        "year": "eq.2025",
        "county": f"eq.{county}",
        "order": "id.asc",
        "limit": "1"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200 and response.json():
            min_id = response.json()[0]["id"]
        else:
            return None, None

        # Get max ID
        params["order"] = "id.desc"
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200 and response.json():
            max_id = response.json()[0]["id"]
        else:
            return None, None

        return min_id, max_id
    except:
        return None, None

def process_micro_batch(county, id_start, id_end, batch_size=100):
    """Process a micro-batch of properties"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

    updated = 0

    try:
        # Get properties in ID range
        params = {
            "select": "id,parcel_id,building_value,land_value,just_value",
            "year": "eq.2025",
            "county": f"eq.{county}",
            "id": f"gte.{id_start}",
            "and": f"(id.lte.{id_end})",
            "or": "(land_use_code.is.null,land_use_code.eq.,land_use_code.eq.99)",
            "limit": str(batch_size)
        }

        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code != 200:
            return 0

        properties = response.json()
        if not properties:
            return 0

        # Update each property individually (safest)
        for prop in properties:
            code, label = classify_property(prop)

            update_url = f"{url}?id=eq.{prop['id']}"
            update_data = {
                "land_use_code": code,
                "property_use": label
            }

            try:
                update_response = requests.patch(update_url, headers=headers, json=update_data, timeout=5)
                if update_response.status_code in [200, 204]:
                    updated += 1
            except:
                continue

        return updated

    except Exception as e:
        print(f"      [ERROR] {e}")
        return 0

def process_county_in_ranges(county, estimated_count):
    """Process a county in ID range batches"""
    print(f"\n  Processing {county} (~{estimated_count:,} properties)...")

    # Get ID range
    min_id, max_id = get_id_range_for_county(county)
    if min_id is None:
        print(f"    [SKIP] Could not determine ID range")
        return 0

    print(f"    ID range: {min_id:,} to {max_id:,}")

    total_updated = 0
    range_size = 50000  # Process 50k IDs at a time
    batch_size = 100    # Fetch 100 records per micro-batch

    current_start = min_id
    range_num = 0

    while current_start <= max_id:
        current_end = min(current_start + range_size - 1, max_id)
        range_num += 1

        print(f"    Range {range_num}: {current_start:,}-{current_end:,}...", end=" ", flush=True)

        range_start_time = time.time()
        range_updated = 0

        # Process this range in micro-batches
        batch_start = current_start
        max_batches = 1000  # Safety limit
        batch_count = 0

        while batch_start <= current_end and batch_count < max_batches:
            batch_updated = process_micro_batch(county, batch_start, current_end, batch_size)

            if batch_updated == 0:
                break  # No more records to update in this range

            range_updated += batch_updated
            batch_start += batch_size * 10  # Skip ahead
            batch_count += 1

            time.sleep(0.05)  # Tiny pause

        elapsed = time.time() - range_start_time
        total_updated += range_updated

        print(f"{range_updated:,} updated ({elapsed:.1f}s)")

        current_start = current_end + 1
        time.sleep(0.2)  # Pause between ranges

    print(f"    ✓ {county} complete: {total_updated:,} total updated")
    return total_updated

def main():
    """Execute micro-batched updates"""
    print("=" * 80)
    print("  MICRO-BATCHED DOR ASSIGNMENT (50k ID ranges)")
    print("=" * 80)

    start_time = time.time()

    results = []
    grand_total = 0

    print("\n[PHASE 1] Processing Top 10 Counties")
    print("=" * 80)

    for i, (county, estimate) in enumerate(TOP_COUNTIES, 1):
        print(f"\n[{i}/10] {county}")
        county_start = time.time()

        updated = process_county_in_ranges(county, estimate)

        county_elapsed = time.time() - county_start
        grand_total += updated

        results.append({
            "county": county,
            "estimated": estimate,
            "updated": updated,
            "elapsed": county_elapsed
        })

        print(f"  Elapsed: {county_elapsed / 60:.2f} minutes | Total so far: {grand_total:,}")

        time.sleep(1)  # Pause between counties

    total_elapsed = time.time() - start_time

    # Report
    print("\n" + "=" * 80)
    print("  EXECUTION COMPLETE")
    print("=" * 80)
    print(f"\n  Total Updated: {grand_total:,}")
    print(f"  Execution Time: {total_elapsed / 60:.2f} minutes")
    print(f"  Counties Processed: {len(results)}")
    print(f"  Average per County: {total_elapsed / len(results) / 60:.2f} minutes")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_updated": grand_total,
        "execution_time_minutes": total_elapsed / 60,
        "counties": results,
        "method": "Micro-batched ID ranges (50k chunks)"
    }

    filename = f"MICRO_BATCH_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n  Report saved: {filename}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Execution cancelled")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()