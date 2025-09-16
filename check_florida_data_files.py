#!/usr/bin/env python3
"""Check for Florida Property Data Files"""

from pathlib import Path

# Check data directory
data_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")

if not data_dir.exists():
    print(f"Data directory not found: {data_dir}")
    exit(1)

print("="*70)
print("FLORIDA PROPERTY DATA FILES CHECK")
print("="*70)

# Find all NAL CSV files
nal_files = list(data_dir.glob("*/NAL/NAL*.csv"))
print(f"\nNAL Files (Property Assessments): {len(nal_files)} found")
if nal_files:
    for f in nal_files[:5]:  # Show first 5
        print(f"  - {f.relative_to(data_dir)}")
    if len(nal_files) > 5:
        print(f"  ... and {len(nal_files) - 5} more")

# Find all NAP CSV files
nap_files = list(data_dir.glob("*/NAP/NAP*.csv"))
print(f"\nNAP Files (Property Owners): {len(nap_files)} found")
if nap_files:
    for f in nap_files[:5]:
        print(f"  - {f.relative_to(data_dir)}")

# Find all SDF CSV files
sdf_files = list(data_dir.glob("*/SDF/SDF*.csv"))
print(f"\nSDF Files (Sales): {len(sdf_files)} found")
if sdf_files:
    for f in sdf_files[:5]:
        print(f"  - {f.relative_to(data_dir)}")

# Find all NAV files
nav_files = list(data_dir.glob("*/NAV/*.txt"))
print(f"\nNAV Files (Non-Ad Valorem): {len(nav_files)} found")
if nav_files:
    for f in nav_files[:5]:
        print(f"  - {f.relative_to(data_dir)}")

print("\n" + "="*70)
if nal_files:
    print("Data files found! Ready to load into database.")
else:
    print("No data files found. Need to download them first.")