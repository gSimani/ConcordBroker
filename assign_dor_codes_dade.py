"""
DOR Code Assignment - DADE County Batch Processor (Bulk Upsert Version)
Processes NULL/empty/99 properties in batches using bulk updates for speed.

USAGE:
  Set environment variables:
    SUPABASE_SERVICE_KEY=your_service_role_key

  Run:
    python assign_dor_codes_dade.py
"""

import os
import time
from datetime import datetime
from supabase import create_client, Client

# Configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5000"))
TARGET_COUNTY = os.getenv("TARGET_COUNTY", "DADE")

def get_supabase_client() -> Client:
    """Initialize Supabase client with service role"""
    if not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_KEY is not set")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_classification(building_value, land_value, just_value):
    """Apply intelligent DOR classification logic"""
    building_value = building_value or 0
    land_value = land_value or 0
    just_value = just_value or 0

    # Priority-ordered classification
    if building_value > 500000 and building_value > land_value * 2:
        return ("02", "MF 10+")
    elif building_value > 1000000 and land_value < 500000:
        return ("24", "Industria")
    elif just_value > 500000 and building_value > 200000:
        return ("17", "Commercia")
    elif land_value > building_value * 5 and land_value > 100000:
        return ("01", "Agricult.")
    elif 100000 <= just_value <= 500000 and 50000 <= building_value <= 300000:
        return ("03", "Condo")
    elif land_value > 0 and building_value < 1000:
        return ("10", "Vacant Re")
    elif building_value > 50000 and building_value > land_value:
        return ("00", "SFR")
    else:
        return ("00", "SFR")

def fetch_batch(supabase: Client):
    """Fetch one batch of NULL properties"""
    try:
        resp = (
            supabase.from_("florida_parcels")
            .select("id,parcel_id,building_value,land_value,just_value")
            .eq("year", 2025)
            .eq("county", TARGET_COUNTY)
            .is_("land_use_code", "null")
            .order("id")
            .limit(BATCH_SIZE)
            .execute()
        )
        properties = resp.data or []

        # Also fetch empty string and '99' codes
        if len(properties) < BATCH_SIZE:
            resp2 = (
                supabase.from_("florida_parcels")
                .select("id,parcel_id,building_value,land_value,just_value")
                .eq("year", 2025)
                .eq("county", TARGET_COUNTY)
                .eq("land_use_code", "")
                .order("id")
                .limit(BATCH_SIZE - len(properties))
                .execute()
            )
            properties.extend(resp2.data or [])

        if len(properties) < BATCH_SIZE:
            resp3 = (
                supabase.from_("florida_parcels")
                .select("id,parcel_id,building_value,land_value,just_value")
                .eq("year", 2025)
                .eq("county", TARGET_COUNTY)
                .eq("land_use_code", "99")
                .order("id")
                .limit(BATCH_SIZE - len(properties))
                .execute()
            )
            properties.extend(resp3.data or [])

        return properties
    except Exception as e:
        print(f"    [ERROR] Error fetching batch: {e}")
        return []

def bulk_update(supabase: Client, rows):
    """Bulk update properties with DOR codes"""
    if not rows:
        return 0

    # Prepare payload with classifications
    payload = []
    for r in rows:
        code, use = get_classification(
            r.get("building_value"),
            r.get("land_value"),
            r.get("just_value")
        )
        payload.append({
            "id": r["id"],
            "land_use_code": code,
            "property_use": use,
        })

    try:
        # Bulk upsert by primary key
        supabase.from_("florida_parcels").upsert(payload, on_conflict="id").execute()
        return len(payload)
    except Exception as e:
        print(f"    [ERROR] Error updating batch: {e}")
        return 0

def get_remaining_count(supabase: Client):
    """Count remaining NULL properties"""
    try:
        # Count NULL
        resp1 = (
            supabase.from_("florida_parcels")
            .select("id", count="exact")
            .eq("year", 2025)
            .eq("county", TARGET_COUNTY)
            .is_("land_use_code", "null")
            .execute()
        )
        count1 = resp1.count or 0

        # Count empty string
        resp2 = (
            supabase.from_("florida_parcels")
            .select("id", count="exact")
            .eq("year", 2025)
            .eq("county", TARGET_COUNTY)
            .eq("land_use_code", "")
            .execute()
        )
        count2 = resp2.count or 0

        # Count '99'
        resp3 = (
            supabase.from_("florida_parcels")
            .select("id", count="exact")
            .eq("year", 2025)
            .eq("county", TARGET_COUNTY)
            .eq("land_use_code", "99")
            .execute()
        )
        count3 = resp3.count or 0

        return count1 + count2 + count3
    except:
        return -1

def get_coverage_stats(supabase: Client):
    """Get current coverage statistics"""
    try:
        # Total properties
        total_resp = (
            supabase.from_("florida_parcels")
            .select("id", count="exact")
            .eq("year", 2025)
            .eq("county", TARGET_COUNTY)
            .execute()
        )

        # Properties with codes
        coded_resp = (
            supabase.from_("florida_parcels")
            .select("id", count="exact")
            .eq("year", 2025)
            .eq("county", TARGET_COUNTY)
            .not_.is_("land_use_code", "null")
            .neq("land_use_code", "")
            .neq("land_use_code", "99")
            .execute()
        )

        total = total_resp.count or 0
        coded = coded_resp.count or 0
        coverage = (coded / total * 100) if total > 0 else 0

        return total, coded, coverage
    except:
        return 0, 0, 0

def main():
    """Main execution loop"""
    print("=" * 80)
    print("DOR CODE ASSIGNMENT - DADE COUNTY BATCH PROCESSOR")
    print("=" * 80)
    print(f"Target: {TARGET_COUNTY} County")
    print(f"Batch Size: {BATCH_SIZE} properties")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    supabase = get_supabase_client()

    # Initial stats
    initial_remaining = get_remaining_count(supabase)
    print(f"\n[STATUS] Initial NULL properties: {initial_remaining:,}")

    total, coded, coverage = get_coverage_stats(supabase)
    print(f"[STATUS] Initial coverage: {coded:,}/{total:,} ({coverage:.2f}%)")

    # Process batches
    batch_num = 1
    total_processed = 0

    while True:
        print(f"\n[Batch {batch_num}] Fetching {BATCH_SIZE} NULL properties from {TARGET_COUNTY}...")

        rows = fetch_batch(supabase)

        if not rows:
            print(f"[Batch {batch_num}] No more NULL properties found!")
            break

        print(f"[Batch {batch_num}] Retrieved {len(rows)} properties")

        updated = bulk_update(supabase, rows)
        print(f"[Batch {batch_num}] ✓ Updated {updated} properties")

        total_processed += updated

        # Progress update
        remaining = get_remaining_count(supabase)
        total, coded, coverage = get_coverage_stats(supabase)

        print(f"\n[PROGRESS] Update:")
        print(f"   Processed this session: {total_processed:,}")
        print(f"   Remaining NULL: {remaining:,}")
        print(f"   Current coverage: {coded:,}/{total:,} ({coverage:.2f}%)")

        # Small delay to respect rate limits
        time.sleep(0.25)

        # Safety stop after 200 batches (1M properties)
        if batch_num >= 200:
            print("\n[WARNING] Reached safety limit of 200 batches. Run again to continue.")
            break

        batch_num += 1

    # Final stats
    print("\n" + "=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)

    final_total, final_coded, final_coverage = get_coverage_stats(supabase)
    print(f"Total processed: {total_processed:,} properties")
    print(f"Final coverage: {final_coded:,}/{final_total:,} ({final_coverage:.2f}%)")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()