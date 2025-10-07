#!/usr/bin/env python3
"""
DOR Code Assignment - Batch Execution via Supabase REST API
Processes properties in batches to avoid timeouts
"""
import requests
import time
from datetime import datetime

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

BATCH_SIZE = 1000  # Process 1000 properties at a time
SLEEP_BETWEEN_BATCHES = 1  # 1 second delay between batches

def assign_dor_code(property_data):
    """Determine DOR code based on property values"""
    building_value = property_data.get('building_value') or 0
    land_value = property_data.get('land_value') or 0
    just_value = property_data.get('just_value') or 0

    # Priority 1: Multi-Family 10+
    if building_value > 500000 and building_value > land_value * 2:
        return '02', 'MF 10+'

    # Priority 2: Industrial
    if building_value > 1000000 and land_value < 500000:
        return '24', 'Industria'

    # Priority 3: Commercial
    if (just_value > 500000 and building_value > 200000 and
        land_value * 0.3 <= building_value <= (land_value if land_value > 0 else 1) * 4):
        return '17', 'Commercia'

    # Priority 4: Agricultural
    if land_value > building_value * 5 and land_value > 100000:
        return '01', 'Agricult.'

    # Priority 5: Condominium
    if (100000 <= just_value <= 500000 and
        50000 <= building_value <= 300000 and
        land_value * 0.8 <= building_value <= (land_value if land_value > 0 else 1) * 1.5):
        return '03', 'Condo'

    # Priority 6: Vacant Residential
    if land_value > 0 and building_value < 1000:
        return '10', 'Vacant Re'

    # Priority 7: Single Family
    if building_value > 50000 and building_value > land_value and just_value < 1000000:
        return '00', 'SFR'

    # Default
    return '00', 'SFR'

def get_properties_needing_assignment(offset=0, limit=BATCH_SIZE):
    """Fetch properties that need DOR code assignment"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers=headers,
        params={
            "select": "parcel_id,county,building_value,land_value,just_value",
            "year": "eq.2025",
            "or": "(land_use_code.is.null,land_use_code.eq.,land_use_code.eq.99)",
            "limit": limit,
            "offset": offset
        },
        timeout=30
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching properties: {response.status_code} - {response.text}")
        return []

def update_property_batch(updates):
    """Update multiple properties with their DOR codes"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    success_count = 0
    for update in updates:
        try:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/florida_parcels",
                headers=headers,
                params={
                    "parcel_id": f"eq.{update['parcel_id']}",
                    "year": "eq.2025"
                },
                json={
                    "land_use_code": update['land_use_code'],
                    "property_use": update['property_use']
                },
                timeout=10
            )

            if response.status_code in [200, 204]:
                success_count += 1
            else:
                print(f"Failed to update {update['parcel_id']}: {response.status_code}")
        except Exception as e:
            print(f"Error updating {update['parcel_id']}: {e}")

    return success_count

def main():
    print("=" * 80)
    print("DOR CODE ASSIGNMENT - BATCH PROCESSOR")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    total_processed = 0
    total_updated = 0
    batch_num = 0

    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Delay Between Batches: {SLEEP_BETWEEN_BATCHES}s")
    print()
    print("Processing...")
    print("-" * 80)

    while True:
        batch_num += 1
        offset = (batch_num - 1) * BATCH_SIZE

        # Fetch batch
        print(f"\n[Batch {batch_num}] Fetching properties (offset: {offset:,})...")
        properties = get_properties_needing_assignment(offset)

        if not properties:
            print(f"[Batch {batch_num}] No more properties to process")
            break

        print(f"[Batch {batch_num}] Retrieved {len(properties)} properties")

        # Calculate DOR codes
        updates = []
        for prop in properties:
            code, use_label = assign_dor_code(prop)
            updates.append({
                'parcel_id': prop['parcel_id'],
                'land_use_code': code,
                'property_use': use_label
            })

        # Update database
        print(f"[Batch {batch_num}] Updating {len(updates)} properties...")
        updated = update_property_batch(updates)

        total_processed += len(properties)
        total_updated += updated

        print(f"[Batch {batch_num}] Updated: {updated}/{len(properties)}")
        print(f"[Batch {batch_num}] Running Total: {total_updated:,} properties updated")

        # Calculate progress
        if total_processed >= 5952048:  # Estimated total needing update
            print(f"[Batch {batch_num}] Reached estimated total")
            break

        # Sleep to avoid rate limiting
        if len(properties) == BATCH_SIZE:  # More batches to process
            print(f"[Batch {batch_num}] Sleeping {SLEEP_BETWEEN_BATCHES}s...")
            time.sleep(SLEEP_BETWEEN_BATCHES)
        else:
            print(f"[Batch {batch_num}] Last batch (received {len(properties)} < {BATCH_SIZE})")
            break

    print()
    print("=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Properties Processed: {total_processed:,}")
    print(f"Total Properties Updated: {total_updated:,}")
    print(f"Success Rate: {(total_updated/total_processed*100):.2f}%")
    print()
    print("Next Steps:")
    print("1. Check dashboard: http://localhost:8080")
    print("2. Verify coverage with: python check_dor_status.py")
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
