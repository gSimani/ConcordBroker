"""
Backfill property_use_desc in florida_parcels table
Processes in batches by county to avoid timeouts
Uses Supabase REST API with SERVICE_ROLE_KEY for optimal performance
"""
import os
import time
from supabase import create_client, Client
from typing import Dict, List

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable not set")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Florida counties (67 total)
FLORIDA_COUNTIES = [
    'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN', 'CHARLOTTE',
    'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DESOTO', 'DIXIE', 'DUVAL', 'ESCAMBIA',
    'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON', 'HARDEE',
    'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES', 'INDIAN RIVER', 'JACKSON',
    'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE',
    'MARION', 'MARTIN', 'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE',
    'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA',
    'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
    'WAKULLA', 'WALTON', 'WASHINGTON'
]

def get_property_use_description(property_use: str, county: str) -> str:
    """
    Get property use description from DOR lookup tables

    Args:
        property_use: Property use code (numeric or text)
        county: County name

    Returns:
        Property use description
    """
    if not property_use:
        return 'Unknown Property Type'

    try:
        # Try exact mapping via dor_code_mappings_std
        mapping_response = supabase.table('dor_code_mappings_std') \
            .select('standard_full_code') \
            .eq('legacy_code', str(property_use)) \
            .execute()

        if mapping_response.data:
            # Try county-specific mapping first
            county_mapping = next((m for m in mapping_response.data if m.get('county') == county), None)
            if not county_mapping:
                # Fall back to generic mapping (county = NULL)
                county_mapping = next((m for m in mapping_response.data if not m.get('county')), None)

            if county_mapping:
                full_code = county_mapping['standard_full_code']

                # Get description from dor_use_codes_std
                code_response = supabase.table('dor_use_codes_std') \
                    .select('description') \
                    .eq('full_code', full_code) \
                    .single() \
                    .execute()

                if code_response.data:
                    return code_response.data['description']

        # Fallback to category-based description
        try:
            code_num = int(property_use)
            if 0 <= code_num <= 9:
                return 'Residential Property'
            elif 10 <= code_num <= 39:
                return 'Commercial Property'
            elif 40 <= code_num <= 49:
                return 'Industrial Property'
            elif 50 <= code_num <= 69:
                return 'Agricultural Property'
            elif 70 <= code_num <= 79:
                return 'Institutional Property'
            elif 80 <= code_num <= 89:
                return 'Government Property'
            elif 90 <= code_num <= 99:
                return 'Vacant Land'
        except ValueError:
            pass

        return 'Unknown Property Type'

    except Exception as e:
        print(f"Error looking up property use {property_use}: {e}")
        return 'Unknown Property Type'

def backfill_county(county: str, batch_size: int = 1000) -> Dict:
    """
    Backfill property_use_desc for a single county

    Args:
        county: County name
        batch_size: Number of records to process at once

    Returns:
        Statistics dict with counts
    """
    print(f"\n{'='*80}")
    print(f"Processing county: {county}")
    print(f"{'='*80}")

    start_time = time.time()

    # Get total count for this county
    count_response = supabase.table('florida_parcels') \
        .select('*', count='exact') \
        .eq('county', county) \
        .is_('property_use_desc', 'null') \
        .not_.is_('property_use', 'null') \
        .execute()

    total_records = count_response.count or 0

    if total_records == 0:
        print(f"✓ {county}: No records to update")
        return {'county': county, 'updated': 0, 'total': 0, 'duration': 0}

    print(f"Found {total_records:,} records to update in {county}")

    updated_count = 0
    offset = 0

    while offset < total_records:
        batch_start = time.time()

        # Fetch batch of records
        response = supabase.table('florida_parcels') \
            .select('id, parcel_id, property_use, county') \
            .eq('county', county) \
            .is_('property_use_desc', 'null') \
            .not_.is_('property_use', 'null') \
            .range(offset, offset + batch_size - 1) \
            .execute()

        records = response.data

        if not records:
            break

        # Process each record
        updates = []
        for record in records:
            desc = get_property_use_description(record['property_use'], county)
            updates.append({
                'id': record['id'],
                'property_use_desc': desc
            })

        # Batch update
        if updates:
            try:
                for update in updates:
                    supabase.table('florida_parcels') \
                        .update({'property_use_desc': update['property_use_desc']}) \
                        .eq('id', update['id']) \
                        .execute()

                updated_count += len(updates)

                batch_duration = time.time() - batch_start
                progress_pct = (offset + len(records)) / total_records * 100

                print(f"  Batch {offset:,}-{offset+len(records):,}: "
                      f"Updated {len(updates):,} records in {batch_duration:.2f}s "
                      f"({progress_pct:.1f}% complete)")

            except Exception as e:
                print(f"  ERROR updating batch: {e}")

        offset += len(records)

        # Rate limiting
        time.sleep(0.1)

    duration = time.time() - start_time

    print(f"\n✓ {county} COMPLETE:")
    print(f"  - Updated: {updated_count:,} records")
    print(f"  - Duration: {duration:.2f}s")
    print(f"  - Rate: {updated_count/duration:.1f} records/sec")

    return {
        'county': county,
        'updated': updated_count,
        'total': total_records,
        'duration': duration
    }

def main():
    """Main execution function"""
    print("="*80)
    print("FLORIDA PARCELS - PROPERTY USE DESCRIPTION BACKFILL")
    print("="*80)
    print(f"\nProcessing {len(FLORIDA_COUNTIES)} counties")
    print(f"Using Supabase: {SUPABASE_URL}")
    print(f"\nStarting at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    overall_start = time.time()
    results = []

    # Process each county
    for county in FLORIDA_COUNTIES:
        try:
            result = backfill_county(county, batch_size=500)
            results.append(result)
        except Exception as e:
            print(f"\n❌ ERROR processing {county}: {e}")
            results.append({
                'county': county,
                'updated': 0,
                'total': 0,
                'duration': 0,
                'error': str(e)
            })

    # Summary
    overall_duration = time.time() - overall_start
    total_updated = sum(r['updated'] for r in results)
    total_records = sum(r['total'] for r in results)

    print("\n" + "="*80)
    print("BACKFILL COMPLETE - SUMMARY")
    print("="*80)
    print(f"\nTotal records updated: {total_updated:,} / {total_records:,}")
    print(f"Total duration: {overall_duration/60:.2f} minutes")
    print(f"Average rate: {total_updated/overall_duration:.1f} records/sec")

    # Top 10 counties by size
    print("\nTop 10 counties by records updated:")
    sorted_results = sorted(results, key=lambda x: x['updated'], reverse=True)[:10]
    for i, result in enumerate(sorted_results, 1):
        print(f"  {i}. {result['county']}: {result['updated']:,} records "
              f"({result['duration']:.1f}s)")

    print(f"\nCompleted at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

if __name__ == '__main__':
    main()
