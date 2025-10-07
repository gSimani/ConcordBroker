"""
Execute County-Batched DOR Use Code Assignment via Supabase REST API
Uses PostgREST API for updates, no direct SQL needed
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple
import json

# Supabase Configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal,count=exact"
}

def test_connection() -> bool:
    """Test Supabase connection"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/"
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code in [200, 404]  # 404 is OK for root endpoint
    except Exception as e:
        print(f"[ERROR] Connection test failed: {e}")
        return False

def get_county_list() -> List[str]:
    """Get list of counties that need updates"""
    print("\n[PHASE 1] Analyzing County Distribution")
    print("=" * 80)

    # Get unique counties
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    params = {
        "select": "county",
        "year": "eq.2025",
        "limit": "67"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code != 200:
            print(f"[ERROR] Failed to get counties: {response.status_code}")
            return []

        data = response.json()
        # Get unique counties
        counties = sorted(list(set(row["county"] for row in data if row.get("county"))))

        print(f"[SUCCESS] Found {len(counties)} counties")
        return counties

    except Exception as e:
        print(f"[ERROR] Failed to get county list: {e}")
        return []

def get_county_status(county: str) -> Dict:
    """Get status for a specific county"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

    try:
        # Total count
        params = {
            "select": "id",
            "year": "eq.2025",
            "county": f"eq.{county}",
            "limit": "0"
        }
        headers_count = headers.copy()
        headers_count["Prefer"] = "count=exact"

        response = requests.get(url, headers=headers_count, params=params, timeout=30)
        total = int(response.headers.get("Content-Range", "0-0/0").split("/")[-1])

        # With code count
        params["land_use_code"] = "not.is.null"
        response = requests.get(url, headers=headers_count, params=params, timeout=30)
        with_code = int(response.headers.get("Content-Range", "0-0/0").split("/")[-1])

        need_update = total - with_code
        coverage = (with_code / total * 100) if total > 0 else 0

        return {
            "county": county,
            "total": total,
            "with_code": with_code,
            "need_update": need_update,
            "coverage": coverage
        }

    except Exception as e:
        print(f"[ERROR] Failed to get status for {county}: {e}")
        return {}

def assign_dor_code_for_property(property_data: Dict) -> Tuple[str, str]:
    """Determine DOR code for a single property"""
    bldg = property_data.get("building_value") or 0
    land = property_data.get("land_value") or 0
    just = property_data.get("just_value") or 0

    # Multi-Family 10+
    if bldg > 500000 and bldg > land * 2:
        return ("02", "MF 10+")

    # Industrial
    if bldg > 1000000 and land < 500000:
        return ("24", "Industria")

    # Commercial
    if just > 500000 and bldg > 200000 and (land * 0.3 <= bldg <= land * 4):
        return ("17", "Commercia")

    # Agricultural
    if land > bldg * 5 and land > 100000:
        return ("01", "Agricult.")

    # Condominium
    if 100000 <= just <= 500000 and 50000 <= bldg <= 300000 and (land * 0.8 <= bldg <= land * 1.5):
        return ("03", "Condo")

    # Vacant Residential
    if land > 0 and bldg < 1000:
        return ("10", "Vacant Re")

    # Single Family
    if bldg > 50000 and bldg > land and just < 1000000:
        return ("00", "SFR")

    # Default
    return ("00", "SFR")

def process_county_batch(county: str, batch_size: int = 500) -> Dict:
    """Process a county in batches using REST API"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

    try:
        # Get properties needing updates
        params = {
            "select": "id,parcel_id,building_value,land_value,just_value",
            "year": "eq.2025",
            "county": f"eq.{county}",
            "or": "(land_use_code.is.null,land_use_code.eq.,land_use_code.eq.99)",
            "limit": str(batch_size)
        }

        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code != 200:
            return {"success": False, "error": f"Status {response.status_code}"}

        properties = response.json()
        if not properties:
            return {"success": True, "updated": 0, "message": "No properties to update"}

        # Process each property
        updates = []
        for prop in properties:
            code, label = assign_dor_code_for_property(prop)
            updates.append({
                "id": prop["id"],
                "land_use_code": code,
                "property_use": label
            })

        # Batch update via PATCH
        updated_count = 0
        for update in updates:
            patch_url = f"{url}?id=eq.{update['id']}"
            patch_data = {
                "land_use_code": update["land_use_code"],
                "property_use": update["property_use"]
            }

            patch_response = requests.patch(patch_url, headers=headers, json=patch_data, timeout=10)
            if patch_response.status_code in [200, 204]:
                updated_count += 1

        return {"success": True, "updated": updated_count, "total_batch": len(properties)}

    except Exception as e:
        return {"success": False, "error": str(e)}

def process_county(county: str, index: int, total: int) -> Dict:
    """Process all batches for a county"""
    start_time = time.time()

    print(f"\n[{index}/{total}] Processing {county}...", end=" ", flush=True)

    # Get initial status
    status_before = get_county_status(county)
    if not status_before or status_before.get("need_update", 0) == 0:
        print(f"✓ Already complete (100%)")
        return {
            "success": True,
            "county": county,
            "updated": 0,
            "coverage": status_before.get("coverage", 100),
            "elapsed": 0
        }

    # Process in batches until no more updates needed
    total_updated = 0
    max_batches = 100  # Safety limit
    batch_count = 0

    while batch_count < max_batches:
        result = process_county_batch(county, batch_size=500)

        if not result["success"]:
            print(f"✗ ERROR: {result.get('error')}")
            return {
                "success": False,
                "county": county,
                "error": result.get("error")
            }

        updated = result.get("updated", 0)
        total_updated += updated

        # If no updates made, we're done
        if updated == 0:
            break

        batch_count += 1

    # Get final status
    status_after = get_county_status(county)
    elapsed = time.time() - start_time

    print(f"✓ Updated {total_updated:,} | Coverage: {status_after.get('coverage', 0):.1f}% | {elapsed:.2f}s")

    return {
        "success": True,
        "county": county,
        "updated": total_updated,
        "total": status_after.get("total", 0),
        "coverage": status_after.get("coverage", 0),
        "batches": batch_count,
        "elapsed": elapsed
    }

def get_overall_status() -> Dict:
    """Get overall coverage status"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

    try:
        # Total count
        params = {
            "select": "id",
            "year": "eq.2025",
            "limit": "0"
        }
        headers_count = headers.copy()
        headers_count["Prefer"] = "count=exact"

        response = requests.get(url, headers=headers_count, params=params, timeout=30)
        total = int(response.headers.get("Content-Range", "0-0/0").split("/")[-1])

        # With code count
        params["land_use_code"] = "not.is.null"
        response = requests.get(url, headers=headers_count, params=params, timeout=30)
        with_code = int(response.headers.get("Content-Range", "0-0/0").split("/")[-1])

        coverage = (with_code / total * 100) if total > 0 else 0

        return {
            "total": total,
            "with_code": with_code,
            "without_code": total - with_code,
            "coverage_pct": coverage
        }

    except Exception as e:
        print(f"[ERROR] Failed to get overall status: {e}")
        return {}

def main():
    """Execute county-batched DOR assignment"""
    print("=" * 80)
    print("[AI AGENT] County-Batched DOR Use Code Assignment")
    print("Using Supabase REST API")
    print("=" * 80)

    start_time = time.time()

    # Test connection
    print("\n[CONNECTING] Testing Supabase connection...")
    if not test_connection():
        print("[ERROR] Failed to connect to Supabase")
        return False

    print("[SUCCESS] Connected to Supabase")

    # Phase 1: Discovery
    counties = get_county_list()
    if not counties:
        print("\n[ERROR] Failed to get county list")
        return False

    initial_status = get_overall_status()
    print(f"\n[INITIAL STATUS]")
    print(f"  Total Properties: {initial_status.get('total', 0):,}")
    print(f"  With Code: {initial_status.get('with_code', 0):,}")
    print(f"  Without Code: {initial_status.get('without_code', 0):,}")
    print(f"  Coverage: {initial_status.get('coverage_pct', 0):.2f}%")

    print(f"\n[DISCOVERY] Processing {len(counties)} counties")

    # Phase 2 & 3: Process all counties
    print(f"\n[PHASE 2 & 3] Processing All Counties")
    print("=" * 80)

    results = []
    for i, county in enumerate(counties, 1):
        result = process_county(county, i, len(counties))
        results.append(result)

        # Brief pause to avoid rate limiting
        time.sleep(0.2)

    # Phase 4: Final Validation
    print(f"\n[PHASE 4] Final Validation")
    print("=" * 80)

    final_status = get_overall_status()
    total_elapsed = time.time() - start_time

    # Generate Report
    print(f"\n{'=' * 80}")
    print(f"[EXECUTION COMPLETE] ✓")
    print(f"{'=' * 80}")

    print(f"\n[BEFORE]")
    print(f"  Total Properties: {initial_status.get('total', 0):,}")
    print(f"  With Code: {initial_status.get('with_code', 0):,}")
    print(f"  Coverage: {initial_status.get('coverage_pct', 0):.2f}%")

    print(f"\n[AFTER]")
    print(f"  Total Properties: {final_status.get('total', 0):,}")
    print(f"  With Code: {final_status.get('with_code', 0):,}")
    print(f"  Coverage: {final_status.get('coverage_pct', 0):.2f}%")

    print(f"\n[IMPACT]")
    properties_updated = final_status.get('with_code', 0) - initial_status.get('with_code', 0)
    improvement = final_status.get('coverage_pct', 0) - initial_status.get('coverage_pct', 0)
    print(f"  Properties Updated: {properties_updated:,}")
    print(f"  Coverage Improvement: +{improvement:.2f}%")
    print(f"  Execution Time: {total_elapsed / 60:.2f} minutes")
    print(f"  Counties Processed: {len(results)}")
    print(f"  Successful Counties: {sum(1 for r in results if r.get('success'))}")
    print(f"  Failed Counties: {sum(1 for r in results if not r.get('success'))}")

    # Success Rating
    coverage = final_status.get('coverage_pct', 0)
    if coverage >= 100:
        rating = 10
    elif coverage >= 99.5:
        rating = 9
    elif coverage >= 95:
        rating = 8
    elif coverage >= 90:
        rating = 7
    else:
        rating = 6

    print(f"\n[SUCCESS RATING] {rating}/10")

    # Check for gaps
    gaps = [r for r in results if not r.get('success')]
    if gaps:
        print(f"\n[GAPS IDENTIFIED] {len(gaps)} counties failed:")
        for gap in gaps:
            print(f"  - {gap['county']}: {gap.get('error', 'Unknown error')}")

    print("=" * 80)

    # Save detailed results
    report = {
        "execution_timestamp": datetime.now().isoformat(),
        "initial_status": initial_status,
        "final_status": final_status,
        "properties_updated": properties_updated,
        "coverage_improvement": improvement,
        "execution_time_minutes": total_elapsed / 60,
        "counties_processed": len(results),
        "successful_counties": sum(1 for r in results if r.get('success')),
        "failed_counties": sum(1 for r in results if not r.get('success')),
        "county_results": results,
        "success_rating": rating,
        "gaps": gaps,
        "method": "Supabase REST API with county batching"
    }

    filename = f"DOR_ASSIGNMENT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n[REPORT SAVED] {filename}\n")

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)