"""
Run all verification queries requested by Supabase support
This script runs through the REST API since we don't have direct DB access yet
"""

from datetime import datetime
from supabase import create_client, Client
import json
import time

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def run_verification_queries():
    """Run all queries requested by Supabase support"""
    
    print("=" * 80)
    print("SUPABASE VERIFICATION QUERIES - REQUESTED BY SUPPORT")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    client = get_supabase_client()
    
    # Store results for summary
    results = {
        'timestamp': datetime.now().isoformat(),
        'queries': {}
    }
    
    # Query 1: Total parcels
    print("\n1. TOTAL PARCELS")
    print("-" * 40)
    print("SQL: SELECT count(*) as total_rows FROM public.florida_parcels;")
    print("-" * 40)
    
    try:
        result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        if hasattr(result, 'count'):
            total = result.count
            print(f"Result: {total:,} total rows")
            results['queries']['total_parcels'] = total
            
            # Calculate percentage
            expected = 9758470
            percentage = (total / expected * 100) if expected > 0 else 0
            print(f"Progress: {percentage:.2f}% of {expected:,} expected")
        else:
            print("Error: Could not get count")
            results['queries']['total_parcels'] = None
    except Exception as e:
        print(f"Error: {e}")
        results['queries']['total_parcels'] = None
    
    # Query 2: Parcels by county
    print("\n2. PARCELS BY COUNTY (Top 30)")
    print("-" * 40)
    print("SQL: SELECT county, count(*) as rows FROM public.florida_parcels")
    print("     GROUP BY county ORDER BY rows DESC LIMIT 100;")
    print("-" * 40)
    
    try:
        # Get counts for major counties
        counties_to_check = [
            'BROWARD', 'DADE', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE', 
            'PINELLAS', 'LEE', 'POLK', 'DUVAL', 'BREVARD',
            'VOLUSIA', 'SEMINOLE', 'PASCO', 'COLLIER', 'SARASOTA',
            'MANATEE', 'MARION', 'OSCEOLA', 'LAKE', 'ST. LUCIE',
            'ALACHUA', 'ESCAMBIA', 'LEON', 'ST. JOHNS', 'CLAY',
            'SANTA ROSA', 'HERNANDO', 'OKALOOSA', 'CHARLOTTE', 'INDIAN RIVER'
        ]
        
        county_counts = []
        print(f"{'County':<20} {'Count':>12} {'Expected':>12} {'Progress':>10}")
        print("-" * 55)
        
        expected_counts = {
            'BROWARD': 753242, 'DADE': 933276, 'PALM BEACH': 616436,
            'HILLSBOROUGH': 524735, 'ORANGE': 445018, 'PINELLAS': 444821,
            'LEE': 389491, 'POLK': 309595, 'DUVAL': 305928,
            'BREVARD': 283107, 'VOLUSIA': 258456, 'SEMINOLE': 192525,
            'PASCO': 181865, 'COLLIER': 167456, 'SARASOTA': 167214,
            'MANATEE': 156303, 'MARION': 155808, 'OSCEOLA': 136648,
            'LAKE': 135299, 'ST. LUCIE': 134308, 'ALACHUA': 106234,
            'ESCAMBIA': 123158, 'LEON': 91766, 'ST. JOHNS': 108775,
            'CLAY': 84090
        }
        
        for county in counties_to_check:
            try:
                result = client.table('florida_parcels').select('parcel_id', count='exact').eq('county', county).limit(1).execute()
                if hasattr(result, 'count'):
                    count = result.count
                    expected = expected_counts.get(county, 0)
                    progress = (count / expected * 100) if expected > 0 else 0
                    
                    county_counts.append({
                        'county': county,
                        'count': count,
                        'expected': expected,
                        'progress': progress
                    })
                    
                    print(f"{county:<20} {count:>12,} {expected:>12,} {progress:>9.1f}%")
            except Exception as e:
                print(f"{county:<20} {'Error':>12} {'-':>12} {'-':>9}")
        
        results['queries']['parcels_by_county'] = county_counts
        
        # Summary stats
        if county_counts:
            total_counted = sum(c['count'] for c in county_counts)
            total_expected = sum(c['expected'] for c in county_counts)
            print("-" * 55)
            print(f"{'SUBTOTAL':<20} {total_counted:>12,} {total_expected:>12,} {(total_counted/total_expected*100):>9.1f}%")
    
    except Exception as e:
        print(f"Error getting county counts: {e}")
        results['queries']['parcels_by_county'] = None
    
    # Query 3: Check for COPY progress (can't run via REST API)
    print("\n3. COPY PROGRESS CHECK")
    print("-" * 40)
    print("SQL: SELECT pid, datname, relid::regclass, bytes_processed, pct")
    print("     FROM pg_stat_progress_copy;")
    print("-" * 40)
    print("NOTE: Cannot check pg_stat_progress_copy via REST API")
    print("      Supabase support needs to run this directly")
    
    # Query 4: Check staging table
    print("\n4. STAGING TABLE CHECK")
    print("-" * 40)
    
    try:
        result = client.table('florida_parcels_staging').select('parcel_id', count='exact').limit(1).execute()
        if hasattr(result, 'count'):
            print(f"Staging table exists with {result.count:,} rows")
            results['queries']['staging_table'] = result.count
        else:
            print("Staging table not found or empty")
            results['queries']['staging_table'] = 0
    except Exception as e:
        if "not find" in str(e).lower() or "does not exist" in str(e).lower():
            print("Staging table does not exist")
            results['queries']['staging_table'] = None
        else:
            print(f"Error checking staging table: {e}")
            results['queries']['staging_table'] = None
    
    # Save results to file
    with open('verification_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print SQL queries for Supabase support to run directly
    print("\n" + "=" * 80)
    print("SQL QUERIES FOR SUPABASE SUPPORT TO RUN DIRECTLY")
    print("=" * 80)
    print("""
-- 1. Total parcels (should show ~9.7M when complete)
SELECT count(*) as total_rows FROM public.florida_parcels;

-- 2. Check if COPY is running
SELECT pid, datname, relid::regclass as relation, command, type, 
       bytes_processed, pg_size_pretty(bytes_processed) as bytes_processed_pretty,
       bytes_total, pg_size_pretty(bytes_total) as bytes_total_pretty,
       round(100.0 * bytes_processed / nullif(bytes_total,0), 2) as pct
FROM pg_stat_progress_copy
ORDER BY pid;

-- 3. Parcels by county with expected comparison
WITH expected_counts AS (
    SELECT * FROM (VALUES
        ('BROWARD', 753242),
        ('DADE', 933276),
        ('PALM BEACH', 616436),
        ('HILLSBOROUGH', 524735),
        ('ORANGE', 445018),
        ('PINELLAS', 444821),
        ('LEE', 389491),
        ('POLK', 309595),
        ('DUVAL', 305928),
        ('BREVARD', 283107)
    ) AS t(county, expected)
),
actual_counts AS (
    SELECT county, COUNT(*) as actual
    FROM public.florida_parcels
    GROUP BY county
)
SELECT 
    COALESCE(e.county, a.county) as county,
    COALESCE(a.actual, 0) as actual,
    e.expected,
    ROUND(100.0 * COALESCE(a.actual, 0) / NULLIF(e.expected, 0), 2) as pct_complete
FROM expected_counts e
FULL OUTER JOIN actual_counts a ON e.county = a.county
ORDER BY COALESCE(a.actual, 0) DESC;

-- 4. Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup as rows,
    n_tup_ins as inserts_since_vacuum,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE tablename IN ('florida_parcels', 'florida_parcels_staging')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 5. Check for statement timeouts
SHOW statement_timeout;
SELECT name, setting, unit, source
FROM pg_settings 
WHERE name LIKE '%timeout%';

-- 6. Check for active queries on florida_parcels
SELECT 
    pid,
    now() - query_start as duration,
    state,
    wait_event_type,
    wait_event,
    LEFT(query, 100) as query_snippet
FROM pg_stat_activity
WHERE query ILIKE '%florida_parcels%'
AND state != 'idle'
ORDER BY query_start;

-- 7. Check transaction rollback rate
SELECT 
    datname,
    xact_commit,
    xact_rollback,
    ROUND(100.0 * xact_rollback / NULLIF(xact_commit + xact_rollback, 0), 2) as rollback_pct,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database
WHERE datname = current_database();

-- 8. Session settings for bulk load (CRITICAL)
SET statement_timeout = 0;
SET lock_timeout = 0;
SET synchronous_commit = off;
SET client_min_messages = warning;
""")
    
    # Print recommendations
    print("\n" + "=" * 80)
    print("CRITICAL RECOMMENDATIONS")
    print("=" * 80)
    
    if results['queries'].get('total_parcels', 0) < 5000000:
        print("⚠️ LESS THAN 50% LOADED - Statement timeouts are killing uploads!")
        print("   ACTION: Disable timeouts immediately with:")
        print("   ALTER DATABASE postgres SET statement_timeout = 0;")
    
    # Check for missing major counties
    if results['queries'].get('parcels_by_county'):
        missing_major = []
        for county_data in results['queries']['parcels_by_county']:
            if county_data['county'] in ['PALM BEACH', 'ORANGE', 'PINELLAS'] and county_data['count'] == 0:
                missing_major.append(county_data['county'])
        
        if missing_major:
            print(f"\n⚠️ MAJOR COUNTIES MISSING: {', '.join(missing_major)}")
            print("   These are large counties that should have data!")
    
    print("\n✅ SOLUTION: Use PostgreSQL COPY with direct connection (not REST API)")
    print("   - Need actual database password (not JWT)")
    print("   - Use: postgresql://postgres.[ref]:[password]@db.[ref].supabase.co:5432/postgres")
    print("   - Set statement_timeout = 0 before loading")
    
    return results

def monitor_progress(duration=60, interval=10):
    """Monitor upload progress for specified duration"""
    print("\n" + "=" * 80)
    print(f"MONITORING PROGRESS FOR {duration} SECONDS")
    print("=" * 80)
    
    client = get_supabase_client()
    start_time = time.time()
    last_count = None
    
    while time.time() - start_time < duration:
        try:
            result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
            if hasattr(result, 'count'):
                current_count = result.count
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if last_count is not None:
                    change = current_count - last_count
                    rate = change / interval  # records per second
                    print(f"[{timestamp}] Total: {current_count:,} | Change: +{change:,} | Rate: {rate:.0f} rec/sec")
                else:
                    print(f"[{timestamp}] Total: {current_count:,}")
                
                last_count = current_count
                
        except Exception as e:
            print(f"Error monitoring: {e}")
        
        if time.time() - start_time < duration:
            time.sleep(interval)
    
    print("\nMonitoring complete")

if __name__ == "__main__":
    # Run verification queries
    results = run_verification_queries()
    
    # Ask if user wants to monitor
    print("\n" + "=" * 80)
    print("Would you like to monitor progress? (y/n)")
    choice = input("> ").strip().lower()
    
    if choice == 'y':
        monitor_progress(duration=60, interval=10)