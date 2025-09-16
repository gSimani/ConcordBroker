#!/usr/bin/env python3
"""
Check NAV download status
"""

import os
from pathlib import Path

base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")

nav_n_count = 0
nav_d_count = 0
counties_with_nav = set()

# Check all county directories
for county_dir in base_path.iterdir():
    if county_dir.is_dir():
        nav_dir = county_dir / "NAV"
        if nav_dir.exists():
            # Check NAV_N
            nav_n_dir = nav_dir / "NAV_N"
            if nav_n_dir.exists():
                files = list(nav_n_dir.glob("*.txt")) + list(nav_n_dir.glob("*.TXT"))
                if files:
                    nav_n_count += len(files)
                    counties_with_nav.add(county_dir.name)
                    print(f"NAV_N: {county_dir.name} - {len(files)} file(s)")
            
            # Check NAV_D
            nav_d_dir = nav_dir / "NAV_D"
            if nav_d_dir.exists():
                files = list(nav_d_dir.glob("*.txt")) + list(nav_d_dir.glob("*.TXT"))
                if files:
                    nav_d_count += len(files)
                    print(f"NAV_D: {county_dir.name} - {len(files)} file(s)")

print("\n" + "="*60)
print("NAV DOWNLOAD STATUS")
print("="*60)
print(f"NAV_N files downloaded: {nav_n_count}")
print(f"NAV_D files downloaded: {nav_d_count}")
print(f"Counties with NAV data: {len(counties_with_nav)}")
print("="*60)