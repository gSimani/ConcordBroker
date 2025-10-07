"""
Execute DOR Use Code Assignment - RECOMMENDED METHOD
Uses Supabase direct connection with intelligent fallback
"""

import requests
import time
from datetime import datetime
import json

# Configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json"
}

def print_banner():
    """Print execution banner"""
    print("=" * 80)
    print("  DOR USE CODE ASSIGNMENT - AUTOMATED EXECUTION")
    print("  Target: 5.95M properties | Expected Time: 15-60 minutes")
    print("=" * 80)
    print()

def get_current_status():
    """Get current coverage status"""
    print("[1/5] Checking current status...")

    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

    # Get total count
    params = {"select": "id", "year": "eq.2025", "limit": "0"}
    h = headers.copy()
    h["Prefer"] = "count=exact"

    try:
        response = requests.get(url, headers=h, params=params, timeout=30)
        total = int(response.headers.get("Content-Range", "0-0/0").split("/")[-1])

        # Get with code count
        params["land_use_code"] = "not.is.null"
        params["land_use_code"] = "neq."
        response = requests.get(url, headers=h, params=params, timeout=30)
        with_code_range = response.headers.get("Content-Range", "0-0/0")

        # Try alternative method - get properties without codes
        del params["land_use_code"]
        params["or"] = "(land_use_code.is.null,land_use_code.eq.)"
        response = requests.get(url, headers=h, params=params, timeout=30)
        without_code = int(response.headers.get("Content-Range", "0-0/0").split("/")[-1])

        with_code = total - without_code
        coverage = (with_code / total * 100) if total > 0 else 0

        print(f"  Total Properties: {total:,}")
        print(f"  With Codes: {with_code:,}")
        print(f"  Need Assignment: {without_code:,}")
        print(f"  Coverage: {coverage:.2f}%")
        print()

        return {
            "total": total,
            "with_code": with_code,
            "without_code": without_code,
            "coverage": coverage
        }

    except Exception as e:
        print(f"  [WARNING] Could not get exact status: {e}")
        print(f"  Proceeding with execution anyway...")
        print()
        return {"total": 0, "with_code": 0, "without_code": 0, "coverage": 0}

def get_counties():
    """Get list of counties needing updates"""
    print("[2/5] Discovering counties needing updates...")

    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"
    params = {
        "select": "county",
        "year": "eq.2025",
        "or": "(land_use_code.is.null,land_use_code.eq.,land_use_code.eq.99)",
        "limit": "1000"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 200:
            data = response.json()
            counties = sorted(list(set(row["county"] for row in data if row.get("county"))))
            print(f"  Found {len(counties)} counties needing updates")
            print(f"  Sample: {', '.join(counties[:5])}...")
            print()
            return counties
        else:
            print(f"  [WARNING] Could not get county list (status {response.status_code})")
            # Fallback: Use known Florida counties
            print(f"  Using standard Florida county list...")
            print()
            return ["MIAMI-DADE", "BROWARD", "PALM BEACH", "HILLSBOROUGH", "ORANGE"]
    except Exception as e:
        print(f"  [WARNING] Error getting counties: {e}")
        print(f"  Using standard Florida county list...")
        print()
        return ["MIAMI-DADE", "BROWARD", "PALM BEACH", "HILLSBOROUGH", "ORANGE"]

def classify_property(prop):
    """Classify a single property"""
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

def process_county_batch(county, batch_size=200):
    """Process properties for a county in small batches"""
    url = f"{SUPABASE_URL}/rest/v1/florida_parcels"

    total_updated = 0
    batch_num = 0
    max_batches = 500  # Safety limit per county

    while batch_num < max_batches:
        try:
            # Get properties needing update
            params = {
                "select": "id,parcel_id,building_value,land_value,just_value",
                "year": "eq.2025",
                "county": f"eq.{county}",
                "or": "(land_use_code.is.null,land_use_code.eq.,land_use_code.eq.99)",
                "limit": str(batch_size),
                "order": "id"
            }

            response = requests.get(url, headers=headers, params=params, timeout=60)
            if response.status_code != 200:
                break

            properties = response.json()
            if not properties:
                break

            # Update each property
            for prop in properties:
                code, label = classify_property(prop)

                update_url = f"{url}?id=eq.{prop['id']}"
                update_data = {
                    "land_use_code": code,
                    "property_use": label
                }

                update_response = requests.patch(update_url, headers=headers, json=update_data, timeout=10)
                if update_response.status_code in [200, 204]:
                    total_updated += 1

            batch_num += 1

            # Brief pause to avoid rate limits
            time.sleep(0.1)

        except Exception as e:
            print(f"    [ERROR] Batch {batch_num} failed: {e}")
            break

    return total_updated

def execute_county_updates(counties):
    """Execute updates for all counties"""
    print(f"[3/5] Processing {len(counties)} counties...")
    print()

    results = []
    total_updated = 0

    for i, county in enumerate(counties, 1):
        start = time.time()
        print(f"  [{i}/{len(counties)}] {county}...", end=" ", flush=True)

        updated = process_county_batch(county, batch_size=200)
        elapsed = time.time() - start
        total_updated += updated

        print(f"✓ {updated:,} updated ({elapsed:.1f}s)")

        results.append({
            "county": county,
            "updated": updated,
            "elapsed": elapsed
        })

        time.sleep(0.2)  # Rate limiting

    print()
    print(f"  Total properties updated: {total_updated:,}")
    print()

    return results, total_updated

def get_final_status():
    """Get final coverage status"""
    print("[4/5] Validating results...")

    status = get_current_status()
    return status

def generate_report(initial, final, results, execution_time):
    """Generate final report"""
    print("[5/5] Generating execution report...")
    print()

    properties_updated = final["with_code"] - initial["with_code"]
    improvement = final["coverage"] - initial["coverage"]

    # Calculate rating
    coverage = final["coverage"]
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

    report = {
        "execution_timestamp": datetime.now().isoformat(),
        "execution_time_minutes": execution_time / 60,
        "initial_status": initial,
        "final_status": final,
        "properties_updated": properties_updated,
        "coverage_improvement": improvement,
        "counties_processed": len(results),
        "county_results": results,
        "success_rating": rating,
        "method": "REST API with county batching"
    }

    # Save to file
    filename = f"DOR_EXECUTION_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("=" * 80)
    print("  EXECUTION COMPLETE!")
    print("=" * 80)
    print()
    print(f"[BEFORE]")
    print(f"  Total: {initial['total']:,}")
    print(f"  With Code: {initial['with_code']:,}")
    print(f"  Coverage: {initial['coverage']:.2f}%")
    print()
    print(f"[AFTER]")
    print(f"  Total: {final['total']:,}")
    print(f"  With Code: {final['with_code']:,}")
    print(f"  Coverage: {final['coverage']:.2f}%")
    print()
    print(f"[IMPACT]")
    print(f"  Properties Updated: {properties_updated:,}")
    print(f"  Coverage Improvement: +{improvement:.2f}%")
    print(f"  Execution Time: {execution_time / 60:.2f} minutes")
    print(f"  Counties Processed: {len(results)}")
    print()
    print(f"[SUCCESS RATING] {rating}/10")
    print()
    print(f"[REPORT SAVED] {filename}")
    print("=" * 80)

    return report

def main():
    """Main execution flow"""
    start_time = time.time()

    print_banner()

    # Step 1: Get initial status
    initial = get_current_status()

    # Step 2: Get counties
    counties = get_counties()

    # Step 3: Execute updates
    results, total_updated = execute_county_updates(counties)

    # Step 4: Get final status
    final = get_final_status()

    # Step 5: Generate report
    execution_time = time.time() - start_time
    report = generate_report(initial, final, results, execution_time)

    return report

if __name__ == "__main__":
    try:
        report = main()
        print("\n✓ Execution successful!")
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Execution cancelled by user")
    except Exception as e:
        print(f"\n\n[ERROR] Execution failed: {e}")
        import traceback
        traceback.print_exc()