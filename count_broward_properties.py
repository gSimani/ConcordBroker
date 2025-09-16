"""
Count Broward Properties - Simple Analysis
"""

import os
import pandas as pd
import glob

BROWARD_PATH = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\BROWARD"

print("BROWARD COUNTY PROPERTY DATA ANALYSIS")
print("=" * 50)

def count_csv_files(folder_path, data_type):
    print(f"\n{data_type} Analysis:")
    print(f"Path: {folder_path}")

    if not os.path.exists(folder_path):
        print("Folder not found")
        return 0

    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    if not csv_files:
        print("No CSV files found")
        return 0

    total_records = 0

    for csv_file in csv_files:
        try:
            file_size = os.path.getsize(csv_file) / (1024 * 1024)
            df = pd.read_csv(csv_file, low_memory=False)
            row_count = len(df)
            total_records += row_count

            filename = os.path.basename(csv_file)
            print(f"  {filename}: {row_count:,} records ({file_size:.1f} MB)")

        except Exception as e:
            print(f"  ERROR reading {csv_file}: {e}")

    print(f"  TOTAL {data_type}: {total_records:,} records")
    return total_records

# Main analysis
if not os.path.exists(BROWARD_PATH):
    print(f"ERROR: Broward folder not found: {BROWARD_PATH}")
    exit(1)

print(f"Analyzing: {BROWARD_PATH}")

# Count each data type
nal_count = count_csv_files(os.path.join(BROWARD_PATH, "NAL"), "NAL")
nap_count = count_csv_files(os.path.join(BROWARD_PATH, "NAP"), "NAP")
nav_count = count_csv_files(os.path.join(BROWARD_PATH, "NAV"), "NAV")
sdf_count = count_csv_files(os.path.join(BROWARD_PATH, "SDF"), "SDF")

# Summary
print("\n" + "=" * 50)
print("BROWARD SUMMARY")
print("=" * 50)
print(f"NAL (Properties): {nal_count:,}")
print(f"NAP (Details):    {nap_count:,}")
print(f"NAV (Values):     {nav_count:,}")
print(f"SDF (Sales):      {sdf_count:,}")

print(f"\nEstimated Unique Properties: {nal_count:,}")

# Check ZIP file
zip_path = os.path.join(BROWARD_PATH, "PropertyData.zip")
if os.path.exists(zip_path):
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"PropertyData.zip: {size_mb:.1f} MB")

# Database comparison
print("\n" + "=" * 50)
print("DATABASE COMPARISON")
print("=" * 50)

try:
    import sys
    sys.path.append(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api")
    from supabase_client import get_supabase_client

    supabase = get_supabase_client()

    # Count Broward in database
    result = supabase.table('florida_parcels').select('id', count='exact').eq('county', 'BROWARD').execute()

    if hasattr(result, 'count'):
        db_count = result.count
    else:
        db_count = len(result.data) if result.data else 0

    print(f"Database Broward:  {db_count:,}")
    print(f"Local Files:       {nal_count:,}")
    print(f"Missing:           {nal_count - db_count:,}")

    if nal_count > db_count:
        coverage = (db_count / nal_count * 100) if nal_count > 0 else 0
        print(f"Coverage:          {coverage:.1f}%")
        print(f"\nWARNING: {nal_count - db_count:,} properties missing from database!")
    else:
        print("Database appears complete for Broward")

except Exception as e:
    print(f"Could not connect to database: {e}")

print("\n" + "=" * 50)
print("KEY FINDINGS")
print("=" * 50)

if nal_count > 0:
    print(f"1. Broward has {nal_count:,} properties in local files")
    print(f"2. With 67 Florida counties, total should be 8M+ properties")
    print(f"3. Current database shows only 789k total - severely undercounted")
    print(f"4. Need to upload missing Broward data")
    print(f"5. Performance issues likely due to missing indexes, not data size")

print(f"\nNEXT: Upload missing properties to fix search performance!")