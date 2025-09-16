"""
Comprehensive Property Count Verification
Compares local filesystem data with Supabase database
"""

import os
import csv
import glob
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
from pathlib import Path

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def count_local_properties():
    """Count all properties in local filesystem"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("=" * 80)
    print("LOCAL FILESYSTEM PROPERTY COUNT")
    print("=" * 80)
    
    county_stats = {}
    total_properties = 0
    
    # Get all county folders
    for county_folder in os.listdir(base_path):
        county_path = os.path.join(base_path, county_folder)
        
        # Skip non-county folders
        if not os.path.isdir(county_path) or county_folder in ['NAL_2025', 'NAL_2025P']:
            continue
            
        # Look for NAL folder
        nal_path = os.path.join(county_path, 'NAL')
        if not os.path.exists(nal_path):
            continue
            
        # Count CSV rows
        csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
        county_total = 0
        
        for csv_file in csv_files:
            try:
                # Count rows efficiently
                with open(csv_file, 'r', encoding='utf-8') as f:
                    row_count = sum(1 for line in f) - 1  # Subtract header
                    county_total += row_count
            except Exception as e:
                print(f"  Error reading {csv_file}: {e}")
                continue
        
        if county_total > 0:
            county_stats[county_folder] = county_total
            total_properties += county_total
            print(f"{county_folder:<20} {county_total:>12,} properties")
    
    print("-" * 80)
    print(f"{'TOTAL LOCAL':<20} {total_properties:>12,} properties")
    print(f"Counties with data: {len(county_stats)}")
    
    return county_stats, total_properties

def count_supabase_properties():
    """Count all properties in Supabase database"""
    client = get_supabase_client()
    
    print("\n" + "=" * 80)
    print("SUPABASE DATABASE PROPERTY COUNT")
    print("=" * 80)
    
    try:
        # Get counts by county using raw SQL through RPC
        # First, let's get distinct counties and their counts
        county_stats = {}
        
        # We'll need to query each county individually due to API limitations
        # First get list of counties
        counties_result = client.table('florida_parcels').select('county').execute()
        
        if counties_result.data:
            # Get unique counties
            unique_counties = set()
            for row in counties_result.data:
                if row.get('county'):
                    unique_counties.add(row['county'])
            
            print(f"Found {len(unique_counties)} unique counties in database")
            print("-" * 80)
            
            # Get count for each county
            total_db_properties = 0
            for county in sorted(unique_counties):
                try:
                    # Use count parameter to get exact count
                    result = client.table('florida_parcels').select('parcel_id', count='exact').eq('county', county).limit(1).execute()
                    
                    if hasattr(result, 'count') and result.count is not None:
                        county_stats[county] = result.count
                        total_db_properties += result.count
                        print(f"{county:<20} {result.count:>12,} properties")
                except Exception as e:
                    print(f"  Error counting {county}: {e}")
                    # Try alternative method - get a sample
                    try:
                        sample = client.table('florida_parcels').select('parcel_id').eq('county', county).limit(1000).execute()
                        if sample.data:
                            county_stats[county] = f">{len(sample.data)}"
                            print(f"{county:<20} {f'>{len(sample.data)}':>12} properties (sample)")
                    except:
                        pass
            
            print("-" * 80)
            print(f"{'TOTAL SUPABASE':<20} {total_db_properties:>12,} properties")
            print(f"Counties in database: {len(county_stats)}")
            
            return county_stats, total_db_properties
        else:
            print("No data found in florida_parcels table")
            return {}, 0
            
    except Exception as e:
        print(f"Error querying Supabase: {e}")
        return {}, 0

def compare_counts(local_stats, local_total, db_stats, db_total):
    """Compare local filesystem counts with database counts"""
    print("\n" + "=" * 80)
    print("COMPARISON: LOCAL vs SUPABASE")
    print("=" * 80)
    
    # Compare totals
    print(f"{'Total Properties (Local):':<30} {local_total:>15,}")
    print(f"{'Total Properties (Supabase):':<30} {db_total:>15,}")
    print(f"{'Difference:':<30} {local_total - db_total:>15,}")
    print(f"{'Upload Percentage:':<30} {(db_total/local_total*100 if local_total > 0 else 0):>14.1f}%")
    
    print("\n" + "-" * 80)
    print("COUNTY-BY-COUNTY COMPARISON")
    print("-" * 80)
    print(f"{'County':<20} {'Local':<15} {'Supabase':<15} {'Difference':<15} {'Status'}")
    print("-" * 80)
    
    all_counties = set(local_stats.keys()) | set(db_stats.keys())
    
    missing_counties = []
    incomplete_counties = []
    complete_counties = []
    
    for county in sorted(all_counties):
        local_count = local_stats.get(county.upper(), 0)
        db_count = db_stats.get(county.upper(), 0)
        
        # Handle string counts (samples)
        if isinstance(db_count, str):
            db_display = db_count
            diff_display = "Unknown"
            status = "PARTIAL"
        else:
            db_display = f"{db_count:,}"
            diff = local_count - db_count
            diff_display = f"{diff:,}"
            
            if db_count == 0:
                status = "MISSING"
                missing_counties.append(county)
            elif db_count < local_count * 0.9:  # Less than 90% uploaded
                status = "INCOMPLETE"
                incomplete_counties.append(county)
            else:
                status = "OK"
                complete_counties.append(county)
        
        print(f"{county:<20} {local_count:<15,} {db_display:<15} {diff_display:<15} {status}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Complete counties (>90% uploaded): {len(complete_counties)}")
    print(f"Incomplete counties (<90% uploaded): {len(incomplete_counties)}")
    print(f"Missing counties (0% uploaded): {len(missing_counties)}")
    
    if missing_counties:
        print(f"\nMissing counties: {', '.join(missing_counties)}")
    
    if incomplete_counties:
        print(f"\nIncomplete counties: {', '.join(incomplete_counties)}")
    
    # Special check for large counties
    print("\n" + "-" * 80)
    print("LARGE COUNTIES CHECK")
    print("-" * 80)
    large_counties = ['BROWARD', 'DADE', 'PALM BEACH', 'HILLSBOROUGH', 'ORANGE', 'PINELLAS']
    for county in large_counties:
        local = local_stats.get(county, 0)
        db = db_stats.get(county, 0)
        if isinstance(db, int):
            print(f"{county:<20} Local: {local:>10,}  Supabase: {db:>10,}  ({db/local*100 if local > 0 else 0:.1f}%)")

def main():
    """Main execution"""
    print("=" * 80)
    print("FLORIDA PROPERTY APPRAISER DATA VERIFICATION")
    print(f"Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Count local properties
    print("\nCounting local filesystem properties...")
    local_stats, local_total = count_local_properties()
    
    # Count Supabase properties
    print("\nCounting Supabase database properties...")
    db_stats, db_total = count_supabase_properties()
    
    # Compare
    compare_counts(local_stats, local_total, db_stats, db_total)
    
    # Generate report for Supabase support
    print("\n" + "=" * 80)
    print("PROMPT FOR SUPABASE SUPPORT")
    print("=" * 80)
    print("""
Please help verify our Florida Property Appraiser data upload:

1. We have uploaded property data for all 67 Florida counties
2. Our local filesystem shows significantly more properties than what we're seeing in the database
3. Broward County alone should have ~750,000+ properties

Can you please:
1. Run this query to get exact counts by county:
   SELECT county, COUNT(*) as property_count 
   FROM florida_parcels 
   GROUP BY county 
   ORDER BY property_count DESC;

2. Check the total row count:
   SELECT COUNT(*) as total_properties FROM florida_parcels;

3. Verify if there are any constraints or limits affecting our uploads
4. Check if the monitoring view is working:
   SELECT * FROM florida_parcels_ingest_status;

5. Look for any failed upload logs or timeout issues

Our upload script encountered many "statement timeout" errors (code 57014).
Could this have caused data loss during uploads?
""")

if __name__ == "__main__":
    main()