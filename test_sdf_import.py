"""
Test SDF import with one county first
"""

import os
import zipfile
import pandas as pd
import glob

# Test with Broward county first
SDF_ZIP_PATH = r"C:\TEMP\FLORIDA_SDF_DATA"
SDF_EXTRACT_PATH = r"C:\TEMP\FLORIDA_SDF_EXTRACTED"

def extract_and_analyze():
    print("=" * 70)
    print("TESTING SDF IMPORT - BROWARD COUNTY")
    print("=" * 70)

    # Extract Broward if not already done
    broward_zip = os.path.join(SDF_ZIP_PATH, "Broward_06_Final_SDF_2025.zip")
    broward_extract = os.path.join(SDF_EXTRACT_PATH, "Broward")

    if os.path.exists(broward_zip):
        print(f"\nFound ZIP: {broward_zip}")

        if not os.path.exists(broward_extract):
            os.makedirs(broward_extract)
            print("Extracting ZIP file...")
            with zipfile.ZipFile(broward_zip, 'r') as zip_ref:
                zip_ref.extractall(broward_extract)
            print("Extraction complete!")
    else:
        print(f"ZIP file not found: {broward_zip}")
        return

    # Find extracted files
    print("\nSearching for CSV/TXT files in extracted directory...")

    # Check different possible locations
    search_patterns = [
        os.path.join(broward_extract, "*.csv"),
        os.path.join(broward_extract, "*.txt"),
        os.path.join(broward_extract, "*", "*.csv"),
        os.path.join(broward_extract, "*", "*.txt"),
        os.path.join(broward_extract, "*", "*", "*.csv"),
        os.path.join(broward_extract, "*", "*", "*.txt"),
    ]

    all_files = []
    for pattern in search_patterns:
        files = glob.glob(pattern)
        all_files.extend(files)

    if all_files:
        print(f"\nFound {len(all_files)} files:")
        for f in all_files[:10]:  # Show first 10
            size_mb = os.path.getsize(f) / 1024 / 1024
            print(f"  - {os.path.basename(f)} ({size_mb:.1f} MB)")

        # Analyze first CSV/TXT file
        data_file = all_files[0]
        print(f"\nAnalyzing structure of: {os.path.basename(data_file)}")

        try:
            # Try reading as CSV
            if data_file.endswith('.txt'):
                # Try tab-delimited
                df = pd.read_csv(data_file, sep='\t', nrows=5, encoding='latin1')
            else:
                df = pd.read_csv(data_file, nrows=5, encoding='latin1')

            print(f"\nColumns found ({len(df.columns)}):")
            for col in df.columns:
                print(f"  - {col}")

            print(f"\nFirst 2 rows of data:")
            print(df.head(2).to_string())

            # Check for sales-related columns
            sales_cols = [col for col in df.columns if any(
                keyword in col.upper() for keyword in
                ['SALE', 'PRICE', 'DATE', 'QUAL', 'DEED', 'GRANT']
            )]

            if sales_cols:
                print(f"\nSales-related columns found:")
                for col in sales_cols:
                    print(f"  - {col}")
            else:
                print("\nNo obvious sales columns found. Showing all columns again:")
                for i, col in enumerate(df.columns, 1):
                    print(f"  {i}. {col}")

        except Exception as e:
            print(f"\nError reading file: {e}")
            print("\nTrying to read first few lines as text:")
            with open(data_file, 'r', encoding='latin1') as f:
                for i in range(5):
                    line = f.readline()
                    print(f"Line {i+1}: {line[:200]}...")

    else:
        print("\nNo CSV/TXT files found after extraction!")
        print("\nDirectory structure:")
        for root, dirs, files in os.walk(broward_extract):
            level = root.replace(broward_extract, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            sub_indent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # Show first 5 files
                print(f'{sub_indent}{file}')

if __name__ == "__main__":
    extract_and_analyze()