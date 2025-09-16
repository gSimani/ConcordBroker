"""
Check actual structure of Property Appraiser data
"""

import os
import glob

def check_data_structure():
    """Check what files actually exist"""
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    print("Checking data structure...")
    print("=" * 60)
    
    # Get first few counties to analyze
    counties = []
    for item in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, item)):
            if item not in ['NAL_2025', 'NAL_2025P']:
                counties.append(item)
    
    # Check first 5 counties
    for county in sorted(counties)[:5]:
        county_path = os.path.join(base_path, county)
        print(f"\n{county}:")
        
        # Check each data type folder
        for data_type in ['NAL', 'NAP', 'NAV', 'SDF']:
            type_path = os.path.join(county_path, data_type)
            if os.path.exists(type_path):
                # List all files
                files = os.listdir(type_path)
                print(f"  {data_type}: {len(files)} files")
                for f in files[:3]:  # Show first 3 files
                    size = os.path.getsize(os.path.join(type_path, f))
                    print(f"    - {f} ({size:,} bytes)")
            else:
                print(f"  {data_type}: [folder not found]")
    
    # Check if NAL_2025 has the actual CSV files
    print("\n" + "=" * 60)
    print("Checking NAL_2025 folder:")
    nal_2025_path = os.path.join(base_path, "NAL_2025")
    if os.path.exists(nal_2025_path):
        csv_files = glob.glob(os.path.join(nal_2025_path, "*.csv"))
        txt_files = glob.glob(os.path.join(nal_2025_path, "*.txt"))
        print(f"  CSV files: {len(csv_files)}")
        print(f"  TXT files: {len(txt_files)}")
        
        # Show first few files
        for f in csv_files[:5]:
            size = os.path.getsize(f)
            name = os.path.basename(f)
            print(f"    - {name} ({size:,} bytes)")

if __name__ == "__main__":
    check_data_structure()