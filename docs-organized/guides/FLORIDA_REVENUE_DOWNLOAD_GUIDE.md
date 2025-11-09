# Florida Revenue Data Download Guide

## Complete Documentation for Downloading Florida Property Data

**Last Updated**: September 12, 2024  
**Purpose**: Comprehensive guide for downloading all Florida Revenue property data files

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Data Types Explained](#data-types-explained)
3. [Prerequisites](#prerequisites)
4. [Download Agents](#download-agents)
5. [Directory Structure](#directory-structure)
6. [Step-by-Step Instructions](#step-by-step-instructions)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)
9. [Data File Specifications](#data-file-specifications)

---

## 🎯 Overview

This guide documents the complete process for downloading Florida Department of Revenue property data files. The system uses Playwright-based agents to automatically download and organize data for all 67 Florida counties.

### What Gets Downloaded

- **308 Total Files** across 5 data types
- **67 Counties** of comprehensive property data
- **2024 & 2025** tax roll years
- **Automatic extraction** of ZIP files
- **Organized structure** by county and data type

---

## 📊 Data Types Explained

### 1. NAL (Non Ad Valorem) - 2025P
- **What**: Special assessments and non-property-value-based taxes
- **Files**: 62 files (one per county with data)
- **URL**: `/Tax%20Roll%20Data%20Files/NAL/2025P`
- **Content**: Assessment amounts, district codes, levy information

### 2. NAP (Name and Address of Property Owner) - 2025P
- **What**: Property owner names and mailing addresses
- **Files**: 62 files (one per county with data)
- **URL**: `/Tax%20Roll%20Data%20Files/NAP/2025P`
- **Content**: Owner names, addresses, ownership percentages

### 3. SDF (Sales Data File) - 2025P
- **What**: Property sales transaction records
- **Files**: 62 files (one per county with data)
- **URL**: `/Tax%20Roll%20Data%20Files/SDF/2025P`
- **Content**: Sale dates, prices, buyer/seller info, deed types

### 4. NAV N (Non Ad Valorem - Summary) - 2024
- **What**: Parcel-level summary of all non ad valorem assessments
- **Files**: 61 files (one per county with data)
- **URL**: `/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20N`
- **Content**: Total assessment amounts per parcel
- **File Pattern**: `NAVN[CountyCode]2401.txt`

### 5. NAV D (Non Ad Valorem - Detail) - 2024
- **What**: Detailed breakdown of each assessment/levy
- **Files**: 61 files (one per county with data)
- **URL**: `/Tax%20Roll%20Data%20Files/NAV/2024/NAV%20D`
- **Content**: Individual assessment line items
- **File Pattern**: `NAVD[CountyCode]2401.txt`

---

## 🛠 Prerequisites

### Required Software

```bash
# Python 3.8 or higher
python --version

# Required Python packages
pip install playwright aiohttp aiofiles

# Install Playwright browser
python -m playwright install chromium
```

### System Requirements

- **OS**: Windows 10/11 (adaptable for Mac/Linux)
- **RAM**: 4GB minimum
- **Disk Space**: 2-3GB free
- **Internet**: Stable broadband connection
- **Permissions**: Write access to target directory

---

## 🤖 Download Agents

### Main Agents Created

#### 1. **florida_comprehensive_downloader.py**
- Downloads NAL, NAP, SDF files from 2025P
- Uses Playwright for web scraping
- Handles ZIP extraction automatically

#### 2. **florida_nav_fixed_downloader.py**
- Downloads NAV N and NAV D files from 2024
- Navigates subdirectories for each type
- Processes TXT files directly

### Support Scripts

#### 3. **check_nav_downloads.py**
- Verifies download completeness
- Reports file counts by type and county

#### 4. **verify_downloader_ready.py**
- Checks all prerequisites
- Tests Playwright installation
- Verifies internet connectivity

---

## 📁 Directory Structure

```
C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\
│
├── ALACHUA\
│   ├── NAL\
│   │   └── [extracted NAL files]
│   ├── NAP\
│   │   └── [extracted NAP files]
│   ├── SDF\
│   │   └── [extracted SDF files]
│   └── NAV\
│       ├── NAV_N\
│       │   ├── NAVN112401.txt
│       │   └── NAVN112402.txt
│       └── NAV_D\
│           ├── NAVD112401.txt
│           └── NAVD112402.txt
│
├── BAKER\
│   └── [same structure]
│
... [continues for all 67 counties]
│
└── WASHINGTON\
    └── [same structure]
```

---

## 📝 Step-by-Step Instructions

### Step 1: Verify Prerequisites

```bash
# Run the verification script
python verify_downloader_ready.py
```

Expected output:
```
[OK] Python 3.x.x - OK
[OK] playwright - Installed
[OK] aiohttp - Installed
[OK] aiofiles - Installed
[OK] Playwright Chromium browser - Ready
[OK] Florida Revenue website - Reachable
ALL CHECKS PASSED
```

### Step 2: Download NAL, NAP, SDF Files (2025P)

```bash
# Run the comprehensive downloader
python florida_comprehensive_downloader.py
```

This will:
1. Navigate to each data type page (NAL, NAP, SDF)
2. Extract download links for all counties
3. Download ZIP files
4. Extract contents automatically
5. Delete ZIP files after extraction
6. Skip already downloaded files

**Expected Duration**: 30-60 minutes

### Step 3: Download NAV Files (2024)

```bash
# Run the NAV downloader
python florida_nav_fixed_downloader.py
```

This will:
1. Navigate to NAV N subdirectory
2. Download all 61 NAV N text files
3. Navigate to NAV D subdirectory
4. Download all 61 NAV D text files
5. Organize by county code

**Expected Duration**: 15-30 minutes

### Step 4: Verify Downloads

```bash
# Check download status
python check_nav_downloads.py
```

Expected output:
```
============================================================
NAV DOWNLOAD STATUS
============================================================
NAV_N files downloaded: 122
NAV_D files downloaded: 122
Counties with NAV data: 61
============================================================
```

---

## ✅ Verification

### Quick Verification Commands

```python
# Count all downloaded files
import os
from pathlib import Path

base = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")

counts = {
    'NAL': 0, 'NAP': 0, 'SDF': 0,
    'NAV_N': 0, 'NAV_D': 0
}

for county in base.iterdir():
    if county.is_dir():
        for data_type in counts.keys():
            if '_' in data_type:  # NAV files
                nav_type = data_type.split('_')[1]
                path = county / 'NAV' / f'NAV_{nav_type}'
            else:
                path = county / data_type
            
            if path.exists():
                files = list(path.glob('*'))
                counts[data_type] += len(files)

print("File counts by type:")
for dt, count in counts.items():
    print(f"  {dt}: {count} files")
```

### Expected Totals

- **NAL**: 62+ files
- **NAP**: 62+ files  
- **SDF**: 62+ files
- **NAV_N**: 122 files (61 counties × 2)
- **NAV_D**: 122 files (61 counties × 2)

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Playwright Browser Not Found

```bash
# Solution: Install Playwright browser
python -m playwright install chromium
```

#### 2. Connection Timeout Errors

```python
# Increase timeout in downloader scripts
timeout = aiohttp.ClientTimeout(total=600)  # 10 minutes
```

#### 3. ZIP Extraction Failures

```python
# Manual extraction if needed
import zipfile
from pathlib import Path

zip_path = Path("path/to/file.zip")
extract_to = zip_path.parent

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_to)
```

#### 4. Missing Counties

Some counties may not have data for certain types. This is normal. Counties without data won't have files.

#### 5. Partial Downloads

If downloads are interrupted:
1. The scripts automatically skip existing files
2. Simply re-run the script to continue
3. Check failed_downloads_*.json for retry list

---

## 📄 Data File Specifications

### NAL File Format
```
County|Parcel|AssessmentType|Amount|Year
```

### NAP File Format
```
County|Parcel|OwnerName|MailingAddress|City|State|Zip
```

### SDF File Format
```
County|Parcel|SaleDate|SalePrice|DeedType|Buyer|Seller
```

### NAV N File Format (Fixed Width)
```
RecordType|County|Parcel|AccountNum|TaxYear|TotalAssessments|NumAssessments
```

### NAV D File Format (Fixed Width)
```
RecordType|County|Parcel|LevyID|GovCode|FunctionCode|AssessmentAmount
```

---

## 🚀 Running Everything at Once

Create a master script `download_all_florida_data.py`:

```python
#!/usr/bin/env python3
"""
Master script to download all Florida Revenue data
"""

import asyncio
import subprocess
import sys
from pathlib import Path

async def run_script(script_name):
    """Run a Python script and return status"""
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print('='*60)
    
    result = subprocess.run(
        [sys.executable, script_name],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ {script_name} completed successfully")
        return True
    else:
        print(f"❌ {script_name} failed")
        print(result.stderr)
        return False

async def main():
    """Run all downloaders in sequence"""
    
    scripts = [
        "verify_downloader_ready.py",
        "florida_comprehensive_downloader.py",
        "florida_nav_fixed_downloader.py",
        "check_nav_downloads.py"
    ]
    
    print("FLORIDA REVENUE DATA DOWNLOAD - MASTER SCRIPT")
    print("="*60)
    
    for script in scripts:
        if not Path(script).exists():
            print(f"Warning: {script} not found, skipping...")
            continue
            
        success = await run_script(script)
        if not success and script == "verify_downloader_ready.py":
            print("Prerequisites not met. Please fix issues and retry.")
            return
    
    print("\n" + "="*60)
    print("ALL DOWNLOADS COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 Data Usage Examples

### Loading NAV Data

```python
import csv

def load_nav_n_file(county_code, county_name):
    """Load NAV N summary data for a county"""
    
    file_path = f"path/to/{county_name}/NAV/NAV_N/NAVN{county_code}2401.txt"
    
    with open(file_path, 'r') as f:
        # Parse fixed-width format
        for line in f:
            # Process each parcel's summary
            pass

def load_nav_d_file(county_code, county_name):
    """Load NAV D detail data for a county"""
    
    file_path = f"path/to/{county_name}/NAV/NAV_D/NAVD{county_code}2401.txt"
    
    with open(file_path, 'r') as f:
        # Parse fixed-width format
        for line in f:
            # Process each assessment detail
            pass
```

---

## 🔄 Updating Data

Florida Revenue typically updates data:
- **Preliminary Roll**: June-July
- **Final Roll**: November
- **Sales Data**: Monthly

To update, simply re-run the downloaders. They will:
1. Skip existing files (unless you delete them first)
2. Download any new files
3. Update the logs

---

## 📞 Support

For issues or questions:
1. Check the log files: `florida_download_*.log`
2. Review failed downloads: `failed_downloads_*.json`
3. Verify prerequisites: `python verify_downloader_ready.py`
4. Check Florida Revenue website for maintenance notices

---

## 🎯 Summary

This system provides automated, reliable downloading of all Florida property data with:
- **Automatic retry** on failures
- **Skip logic** for existing files
- **Organized structure** by county and type
- **Comprehensive logging** for troubleshooting
- **Verification tools** for completeness

Total time to download all data: **1-2 hours**
Total disk space required: **2-3 GB**

---

*Document maintained for ConcordBroker property data pipeline*