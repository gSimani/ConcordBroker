"""
Analyze Broward Property Data - Count Records and Compare with Database
"""

import os
import pandas as pd
import glob
from pathlib import Path

# Broward data path
BROWARD_PATH = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\BROWARD"

print("=" * 60)
print("BROWARD COUNTY PROPERTY DATA ANALYSIS")
print("=" * 60)

def analyze_folder(folder_path, data_type):
    """Analyze CSV files in a folder"""
    print(f"\n📁 {data_type.upper()} Data Analysis:")
    print(f"   Path: {folder_path}")

    if not os.path.exists(folder_path):
        print(f"   ❌ Folder not found")
        return 0

    # Find all CSV files
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    if not csv_files:
        print(f"   ❌ No CSV files found")
        return 0

    total_records = 0

    for csv_file in csv_files:
        try:
            # Get file size
            file_size = os.path.getsize(csv_file) / (1024 * 1024)  # MB

            # Read CSV and count rows
            df = pd.read_csv(csv_file, low_memory=False)
            row_count = len(df)
            total_records += row_count

            filename = os.path.basename(csv_file)
            print(f"   📄 {filename}")
            print(f"      Records: {row_count:,}")
            print(f"      Size: {file_size:.1f} MB")
            print(f"      Columns: {len(df.columns)}")

            # Show column names for reference
            if len(df.columns) <= 10:
                print(f"      Columns: {list(df.columns)}")
            else:
                print(f"      First 10 Columns: {list(df.columns[:10])}")

        except Exception as e:
            print(f"   ❌ Error reading {csv_file}: {e}")

    print(f"   📊 Total {data_type} Records: {total_records:,}")
    return total_records

def check_zip_file():
    """Check PropertyData.zip"""
    zip_path = os.path.join(BROWARD_PATH, "PropertyData.zip")
    if os.path.exists(zip_path):
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"\n📦 PropertyData.zip: {size_mb:.1f} MB")
        return True
    return False

# Check if Broward folder exists
if not os.path.exists(BROWARD_PATH):
    print(f"❌ Broward data folder not found: {BROWARD_PATH}")
    exit(1)

print(f"📂 Analyzing: {BROWARD_PATH}")
print(f"📅 Last modified: {pd.Timestamp.fromtimestamp(os.path.getmtime(BROWARD_PATH))}")

# Check ZIP file
has_zip = check_zip_file()

# Analyze each data type
nal_count = analyze_folder(os.path.join(BROWARD_PATH, "NAL"), "NAL (Names & Addresses)")
nap_count = analyze_folder(os.path.join(BROWARD_PATH, "NAP"), "NAP (Property Characteristics)")
nav_count = analyze_folder(os.path.join(BROWARD_PATH, "NAV"), "NAV (Property Values)")
sdf_count = analyze_folder(os.path.join(BROWARD_PATH, "SDF"), "SDF (Sales Data)")

# Summary
print("\n" + "=" * 60)
print("📊 BROWARD COUNTY DATA SUMMARY")
print("=" * 60)
print(f"NAL (Names/Addresses):    {nal_count:>10,} records")
print(f"NAP (Characteristics):    {nap_count:>10,} records")
print(f"NAV (Values):            {nav_count:>10,} records")
print(f"SDF (Sales):             {sdf_count:>10,} records")
print("-" * 60)

# The NAL file typically has one record per parcel (unique properties)
unique_properties = nal_count
print(f"🏠 Estimated Unique Properties: {unique_properties:,}")

if has_zip:
    print(f"📦 Additional data in PropertyData.zip")

print("\n" + "=" * 60)
print("🗄️  DATABASE COMPARISON")
print("=" * 60)

# Now compare with database
try:
    from supabase_client import get_supabase_client
    supabase = get_supabase_client()

    # Count Broward properties in database
    result = supabase.table('florida_parcels').select('*', count='exact').eq('county', 'BROWARD').execute()
    db_count = result.count if hasattr(result, 'count') else 0

    print(f"Database Broward Records:  {db_count:>10,}")
    print(f"Local File Records:       {unique_properties:>10,}")
    print(f"Difference:               {unique_properties - db_count:>10,}")

    if unique_properties > db_count:
        print(f"\n🚨 MISSING DATA DETECTED!")
        print(f"   Missing {unique_properties - db_count:,} properties from database")
        print(f"   Upload coverage: {(db_count/unique_properties*100):.1f}%")
    else:
        print(f"\n✅ Database appears complete for Broward")

except Exception as e:
    print(f"❌ Could not connect to database: {e}")

print("\n" + "=" * 60)
print("🎯 NEXT STEPS")
print("=" * 60)

if unique_properties > 0:
    print("1. ✅ Broward data files located and analyzed")
    print("2. 🔄 Compare with other counties")
    print("3. 📤 Upload missing records if found")
    print("4. 🚀 Test optimized search performance")
else:
    print("❌ No property data found - check file paths")

print(f"\n📍 Total Florida properties should be much higher than 789k!")
print(f"   Broward alone has {unique_properties:,} properties")
print(f"   With 67 counties, expect 8M+ total properties")