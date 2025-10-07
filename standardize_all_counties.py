#!/usr/bin/env python3
"""
DOR Code Standardization - ALL Properties, All Counties
Overwrites existing county codes with standardized classifications
"""
import requests
import time
from datetime import datetime

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# All 67 Florida counties in priority order (largest first)
ALL_COUNTIES = [
    'DADE', 'BROWARD', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE', 'PINELLAS',
    'DUVAL', 'LEE', 'POLK', 'BREVARD', 'VOLUSIA', 'PASCO', 'SEMINOLE',
    'COLLIER', 'SARASOTA', 'MANATEE', 'LAKE', 'MARION', 'OSCEOLA', 'ESCAMBIA',
    'ST LUCIE', 'HERNANDO', 'MARTIN', 'CLAY', 'ALACHUA', 'CHARLOTTE',
    'SANTA ROSA', 'OKALOOSA', 'CITRUS', 'BAY', 'ST JOHNS', 'INDIAN RIVER',
    'FLAGLER', 'SUMTER', 'COLUMBIA', 'HIGHLANDS', 'NASSAU', 'PUTNAM',
    'LEON', 'MONROE', 'JACKSON', 'HARDEE', 'OKEECHOBEE', 'DESOTO',
    'SUWANNEE', 'HENDRY', 'WALTON', 'LEVY', 'GADSDEN', 'BAKER',
    'BRADFORD', 'TAYLOR', 'WAKULLA', 'MADISON', 'UNION', 'GILCHRIST',
    'HAMILTON', 'HOLMES', 'DIXIE', 'WASHINGTON', 'JEFFERSON', 'CALHOUN',
    'GULF', 'FRANKLIN', 'GLADES', 'LAFAYETTE', 'LIBERTY'
]

BATCH_SIZE = 5000  # Properties per batch
SLEEP_BETWEEN_BATCHES = 3  # Seconds

def get_county_properties(county):
    """Get all properties for a county that need standardization"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
    }

    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/florida_parcels",
        headers=headers,
        params={
            "select": "id,parcel_id,building_value,land_value,just_value",
            "year": "eq.2025",
            "county": f"eq.{county}",
            "limit": BATCH_SIZE
        },
        timeout=30
    )

    if response.status_code == 200:
        return response.json()
    return []

def calculate_dor_code(building_value, land_value, just_value):
    """Calculate standardized DOR code based on property values"""
    building_value = building_value or 0
    land_value = land_value or 0
    just_value = just_value or 0

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

def update_property_batch(updates):
    """Update properties with new standardized codes"""
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    success_count = 0
    for update in updates:
        try:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/florida_parcels",
                headers=headers,
                params={
                    "id": f"eq.{update['id']}"
                },
                json={
                    "land_use_code": update['code'],
                    "property_use": update['use']
                },
                timeout=10
            )

            if response.status_code in [200, 204]:
                success_count += 1

        except Exception as e:
            continue

    return success_count

def process_county(county):
    """Process all properties in a county"""
    print(f"\n{'='*80}")
    print(f"Processing: {county}")
    print(f"{'='*80}")

    total_processed = 0
    batch_num = 0

    while True:
        batch_num += 1

        # Fetch batch
        properties = get_county_properties(county)

        if not properties:
            break

        print(f"  Batch {batch_num}: Retrieved {len(properties)} properties")

        # Calculate codes
        updates = []
        for prop in properties:
            code, use_label = calculate_dor_code(
                prop.get('building_value'),
                prop.get('land_value'),
                prop.get('just_value')
            )
            updates.append({
                'id': prop['id'],
                'code': code,
                'use': use_label
            })

        # Update database
        updated = update_property_batch(updates)
        total_processed += updated

        print(f"  Batch {batch_num}: Updated {updated}/{len(properties)} properties")
        print(f"  Running total: {total_processed:,} properties")

        if len(properties) < BATCH_SIZE:
            break

        time.sleep(1)

    return total_processed

def main():
    print("=" * 80)
    print("DOR CODE STANDARDIZATION - ALL PROPERTIES, ALL COUNTIES")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Counties to process: {len(ALL_COUNTIES)}")
    print()

    grand_total = 0
    completed_counties = []
    failed_counties = []

    for i, county in enumerate(ALL_COUNTIES, 1):
        print(f"\n[{i}/{len(ALL_COUNTIES)}] {county}")

        try:
            updated = process_county(county)
            grand_total += updated
            completed_counties.append((county, updated))

            print(f"✓ {county}: {updated:,} properties standardized")

            # Sleep between counties
            if i < len(ALL_COUNTIES):
                print(f"  Sleeping {SLEEP_BETWEEN_BATCHES}s...")
                time.sleep(SLEEP_BETWEEN_BATCHES)

        except Exception as e:
            print(f"✗ {county}: ERROR - {e}")
            failed_counties.append(county)
            continue

    print("\n" + "=" * 80)
    print("STANDARDIZATION COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Properties Standardized: {grand_total:,}")
    print(f"Counties Completed: {len(completed_counties)}/{len(ALL_COUNTIES)}")

    if failed_counties:
        print(f"\nFailed Counties ({len(failed_counties)}):")
        for county in failed_counties:
            print(f"  - {county}")

    print("\n" + "=" * 80)
    print("TOP 10 COUNTIES BY PROPERTIES STANDARDIZED")
    print("=" * 80)
    for county, count in sorted(completed_counties, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {county:20s} {count:>12,}")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Check dashboard: http://localhost:8080")
    print("2. Verify with SQL:")
    print("   SELECT COUNT(*), land_use_code")
    print("   FROM florida_parcels WHERE year = 2025")
    print("   GROUP BY land_use_code ORDER BY COUNT(*) DESC;")
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
