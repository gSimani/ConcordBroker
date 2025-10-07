#!/usr/bin/env python3
"""
DOR Code Standardization with Real-Time Progress Tracking
Updates progress_tracker.json for live dashboard monitoring
"""
import requests
import time
import json
from datetime import datetime
from pathlib import Path

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

PROGRESS_FILE = Path(__file__).parent / "progress_tracker.json"
BATCH_SIZE = 1000

ALL_COUNTIES = [
    'DADE', 'BROWARD', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE', 'PINELLAS',
    'DUVAL', 'LEE', 'POLK', 'BREVARD', 'VOLUSIA', 'PASCO', 'SEMINOLE',
    'COLLIER', 'SARASOTA', 'MANATEE', 'LAKE', 'MARION', 'OSCEOLA', 'ESCAMBIA'
]

def update_progress(data):
    """Write progress to JSON file for dashboard"""
    data['last_update'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_dor_code(building_value, land_value, just_value):
    """Calculate standardized DOR code"""
    building_value = building_value or 0
    land_value = land_value or 0
    just_value = just_value or 0

    if building_value > 500000 and building_value > land_value * 2:
        return '02', 'MF 10+'
    if building_value > 1000000 and land_value < 500000:
        return '24', 'Industria'
    if (just_value > 500000 and building_value > 200000 and
        land_value * 0.3 <= building_value <= (land_value if land_value > 0 else 1) * 4):
        return '17', 'Commercia'
    if land_value > building_value * 5 and land_value > 100000:
        return '01', 'Agricult.'
    if (100000 <= just_value <= 500000 and
        50000 <= building_value <= 300000 and
        land_value * 0.8 <= building_value <= (land_value if land_value > 0 else 1) * 1.5):
        return '03', 'Condo'
    if land_value > 0 and building_value < 1000:
        return '10', 'Vacant Re'
    if building_value > 50000 and building_value > land_value and just_value < 1000000:
        return '00', 'SFR'
    return '00', 'SFR'

def get_county_total(county):
    """Get total properties in county"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Range": "0-0",
        "Prefer": "count=exact"
    }
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/florida_parcels",
            headers=headers,
            params={
                "select": "id",
                "year": "eq.2025",
                "county": f"eq.{county}"
            },
            timeout=10
        )
        if "content-range" in response.headers:
            return int(response.headers["content-range"].split("/")[1])
    except:
        pass
    return 0

def process_county(county, progress_data):
    """Process all properties in a county with real-time tracking"""
    print(f"\n{'='*80}")
    print(f"Processing: {county}")
    print(f"{'='*80}")

    # Get total for this county
    county_total = get_county_total(county)
    print(f"  Total properties in {county}: {county_total:,}")

    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    total_updated = 0
    offset = 0

    while True:
        # Fetch batch
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/florida_parcels",
                headers=headers,
                params={
                    "select": "id,parcel_id,building_value,land_value,just_value",
                    "year": "eq.2025",
                    "county": f"eq.{county}",
                    "limit": BATCH_SIZE,
                    "offset": offset
                },
                timeout=30
            )

            if response.status_code != 200 or not response.json():
                break

            properties = response.json()
            print(f"  Batch: {len(properties)} properties (offset: {offset})")

            # Process each property
            for prop in properties:
                code, use_label = calculate_dor_code(
                    prop.get('building_value'),
                    prop.get('land_value'),
                    prop.get('just_value')
                )

                # Update property
                try:
                    update_resp = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/florida_parcels",
                        headers=headers,
                        params={"id": f"eq.{prop['id']}"},
                        json={
                            "land_use_code": code,
                            "property_use": use_label
                        },
                        timeout=10
                    )

                    if update_resp.status_code in [200, 204]:
                        total_updated += 1
                        progress_data['properties_processed'] += 1

                        # Update county progress
                        progress_data['current_county_progress'] = {
                            'processed': total_updated,
                            'total': county_total
                        }

                        # Update progress file every 50 properties
                        if total_updated % 50 == 0:
                            update_progress(progress_data)
                            pct = (total_updated / county_total * 100) if county_total > 0 else 0
                            print(f"  OK {county}: {total_updated:,}/{county_total:,} ({pct:.1f}%) | Total: {progress_data['properties_processed']:,}")

                except Exception as e:
                    continue

            offset += BATCH_SIZE

            if len(properties) < BATCH_SIZE:
                break

        except Exception as e:
            print(f"  WARNING: Error in batch: {e}")
            break

    print(f"COMPLETE {county}: {total_updated:,} properties standardized")
    return total_updated

def main():
    print("=" * 80)
    print("DOR CODE STANDARDIZATION - WITH LIVE TRACKING")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Counties to process: {len(ALL_COUNTIES)}")
    print(f"Progress file: {PROGRESS_FILE}")
    print()

    # Initialize progress
    progress_data = {
        "start_time": datetime.now().isoformat(),
        "last_update": datetime.now().isoformat(),
        "total_properties": 9113150,
        "properties_processed": 0,
        "counties_completed": [],
        "current_county": "",
        "current_county_progress": {"processed": 0, "total": 0},
        "counties_remaining": ALL_COUNTIES.copy(),
        "status": "running"
    }
    update_progress(progress_data)

    # Process each county
    for i, county in enumerate(ALL_COUNTIES, 1):
        progress_data['current_county'] = county
        progress_data['status'] = f"processing {county}"
        update_progress(progress_data)

        print(f"\n[{i}/{len(ALL_COUNTIES)}] {county}")

        try:
            updated = process_county(county, progress_data)

            # Mark county as complete
            progress_data['counties_completed'].append({
                "county": county,
                "properties": updated,
                "completed_at": datetime.now().isoformat()
            })
            progress_data['counties_remaining'].remove(county)
            update_progress(progress_data)

            # Sleep between counties
            if i < len(ALL_COUNTIES):
                print(f"  Sleeping 3s...")
                time.sleep(3)

        except Exception as e:
            print(f"  ERROR processing {county}: {e}")
            continue

    # Final update
    progress_data['status'] = "complete"
    progress_data['current_county'] = ""
    update_progress(progress_data)

    print("\n" + "=" * 80)
    print("STANDARDIZATION COMPLETE")
    print("=" * 80)
    print(f"Total Properties Processed: {progress_data['properties_processed']:,}")
    print(f"Counties Completed: {len(progress_data['counties_completed'])}/{len(ALL_COUNTIES)}")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nWARNING: Process interrupted by user")
        progress_data = json.load(open(PROGRESS_FILE))
        progress_data['status'] = "interrupted"
        update_progress(progress_data)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
