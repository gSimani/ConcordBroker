"""
Supabase Bulk Loading Verification Script
Implements all checks recommended by Supabase support
"""

from datetime import datetime
from supabase import create_client, Client
import time
import json

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def run_verification_checks():
    """Run all verification checks recommended by Supabase support"""
    client = get_supabase_client()
    
    print("=" * 80)
    print("SUPABASE BULK LOADING VERIFICATION")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = {}
    
    # 1. Check total parcels
    print("\n1. TOTAL PARCELS CHECK")
    print("-" * 40)
    try:
        # Using count parameter for exact count
        result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
        if hasattr(result, 'count'):
            total_count = result.count
            print(f"Total rows in florida_parcels: {total_count:,}")
            results['total_parcels'] = total_count
        else:
            print("Unable to get exact count")
            results['total_parcels'] = None
    except Exception as e:
        print(f"Error getting total count: {e}")
        results['total_parcels'] = None
    
    # 2. Check parcels by county
    print("\n2. PARCELS BY COUNTY")
    print("-" * 40)
    print(f"{'County':<20} {'Row Count':>15} {'Percentage':>12}")
    print("-" * 47)
    
    county_counts = {}
    counties_to_check = [
        'BROWARD', 'DADE', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE', 
        'PINELLAS', 'LEE', 'POLK', 'DUVAL', 'BREVARD',
        'VOLUSIA', 'SEMINOLE', 'PASCO', 'COLLIER', 'SARASOTA',
        'MANATEE', 'MARION', 'OSCEOLA', 'LAKE', 'ST. LUCIE',
        'ALACHUA', 'ESCAMBIA', 'LEON', 'ST. JOHNS', 'CLAY'
    ]
    
    total_checked = 0
    for county in counties_to_check:
        try:
            result = client.table('florida_parcels').select('parcel_id', count='exact').eq('county', county).limit(1).execute()
            if hasattr(result, 'count') and result.count:
                count = result.count
                county_counts[county] = count
                total_checked += count
                percentage = (count / results['total_parcels'] * 100) if results['total_parcels'] else 0
                print(f"{county:<20} {count:>15,} {percentage:>11.2f}%")
        except Exception as e:
            print(f"{county:<20} {'Error':>15} {'-':>11}")
    
    results['county_counts'] = county_counts
    results['total_checked'] = total_checked
    
    # 3. Check for staging table
    print("\n3. STAGING TABLE CHECK")
    print("-" * 40)
    try:
        # Try to query staging table
        result = client.table('florida_parcels_staging').select('parcel_id', count='exact').limit(1).execute()
        if hasattr(result, 'count'):
            staging_count = result.count
            print(f"Staging table exists with {staging_count:,} rows")
            results['staging_table'] = True
            results['staging_count'] = staging_count
        else:
            print("Staging table not accessible via API")
            results['staging_table'] = False
    except Exception as e:
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("Staging table does not exist")
            results['staging_table'] = False
        else:
            print(f"Cannot verify staging table: {e}")
            results['staging_table'] = None
    
    # 4. Check monitoring view
    print("\n4. MONITORING VIEW CHECK")
    print("-" * 40)
    try:
        result = client.table('florida_parcels_ingest_status').select('*').execute()
        if result.data:
            print(f"{'County':<20} {'Total Rows':>15} {'Last Insert':>25}")
            print("-" * 60)
            for row in result.data:
                print(f"{row['county']:<20} {row['total_rows']:>15,} {row['last_insert_at']:>25}")
            results['monitoring_view'] = True
            results['monitoring_data'] = result.data
        else:
            print("Monitoring view exists but has no data")
            results['monitoring_view'] = True
            results['monitoring_data'] = []
    except Exception as e:
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("Monitoring view does not exist")
            results['monitoring_view'] = False
        else:
            print(f"Cannot access monitoring view: {e}")
            results['monitoring_view'] = None
    
    # 5. Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    if results.get('total_parcels'):
        expected = 9758470
        actual = results['total_parcels']
        percentage = (actual / expected) * 100
        
        print(f"\nData Upload Status:")
        print(f"  Expected: {expected:,} properties")
        print(f"  Actual:   {actual:,} properties")
        print(f"  Progress: {percentage:.2f}%")
        
        if percentage < 1:
            print("\n⚠️ CRITICAL: Less than 1% of data uploaded!")
            print("   Statement timeouts are causing silent failures.")
        elif percentage < 50:
            print("\n⚠️ WARNING: Less than 50% uploaded.")
            print("   Bulk loading is incomplete.")
        elif percentage < 90:
            print("\n⚠️ INFO: Upload in progress.")
        else:
            print("\n✅ SUCCESS: Most data appears to be uploaded.")
    
    # Check county distribution
    if county_counts:
        missing_counties = []
        incomplete_counties = []
        
        expected_counts = {
            'BROWARD': 753242,
            'DADE': 933276,
            'PALM BEACH': 616436,
            'HILLSBOROUGH': 524735,
            'ORANGE': 445018,
            'PINELLAS': 444821
        }
        
        for county, expected_count in expected_counts.items():
            actual = county_counts.get(county, 0)
            if actual == 0:
                missing_counties.append(county)
            elif actual < expected_count * 0.9:
                incomplete_counties.append(f"{county} ({actual}/{expected_count})")
        
        if missing_counties:
            print(f"\n⚠️ Missing counties: {', '.join(missing_counties)}")
        if incomplete_counties:
            print(f"⚠️ Incomplete counties: {', '.join(incomplete_counties)}")
    
    # SQL queries for Supabase support
    print("\n" + "=" * 80)
    print("SQL QUERIES FOR SUPABASE SUPPORT TO RUN")
    print("=" * 80)
    
    print("""
-- 1. Total rows currently in florida_parcels
SELECT COUNT(*) as total_rows FROM public.florida_parcels;

-- 2. Check if COPY is running right now
SELECT pid, datname, relid::regclass as relation, command, type, 
       bytes_processed, pg_size_pretty(bytes_processed) as bytes_processed_pretty,
       bytes_total, pg_size_pretty(bytes_total) as bytes_total_pretty,
       round(100.0 * bytes_processed / nullif(bytes_total,0), 2) as pct
FROM pg_stat_progress_copy
ORDER BY pid;

-- 3. Rows by county to verify loading distribution
SELECT county, COUNT(*) as rows
FROM public.florida_parcels
GROUP BY county
ORDER BY rows DESC
LIMIT 100;

-- 4. Check table size growth
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup as estimated_rows
FROM pg_stat_user_tables
WHERE tablename IN ('florida_parcels', 'florida_parcels_staging')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 5. Check for blocking locks
SELECT 
    blocking.pid AS blocking_pid,
    blocking.usename AS blocking_user,
    blocked.pid AS blocked_pid,
    blocked.usename AS blocked_user,
    blocked.query AS blocked_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked ON blocked.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_stat_activity blocking ON blocking.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- 6. Session settings for bulk load (run after connecting)
SET statement_timeout = 0;
SET lock_timeout = 0; 
SET synchronous_commit = off;
SET client_min_messages = warning;
""")
    
    # Save results to file
    with open('verification_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to verification_results.json")
    
    return results

def continuous_monitoring(interval=30, duration=300):
    """Monitor upload progress continuously"""
    print("\n" + "=" * 80)
    print("CONTINUOUS MONITORING MODE")
    print(f"Checking every {interval} seconds for {duration} seconds")
    print("=" * 80)
    
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < duration:
        check_count += 1
        print(f"\n--- Check #{check_count} at {datetime.now().strftime('%H:%M:%S')} ---")
        
        client = get_supabase_client()
        
        try:
            # Get total count
            result = client.table('florida_parcels').select('parcel_id', count='exact').limit(1).execute()
            if hasattr(result, 'count'):
                print(f"Total rows: {result.count:,}")
            
            # Get top counties
            top_counties = ['BROWARD', 'DADE', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE']
            for county in top_counties:
                result = client.table('florida_parcels').select('parcel_id', count='exact').eq('county', county).limit(1).execute()
                if hasattr(result, 'count') and result.count > 0:
                    print(f"  {county}: {result.count:,}")
        
        except Exception as e:
            print(f"Error in monitoring: {e}")
        
        if time.time() - start_time < duration:
            time.sleep(interval)
    
    print("\nMonitoring complete")

if __name__ == "__main__":
    # Run verification checks
    results = run_verification_checks()
    
    # Ask if user wants continuous monitoring
    print("\n" + "=" * 80)
    print("Would you like to start continuous monitoring? (y/n)")
    choice = input("> ").strip().lower()
    
    if choice == 'y':
        continuous_monitoring(interval=30, duration=600)  # Monitor for 10 minutes