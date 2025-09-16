"""
Check what Sunbiz data we have downloaded vs what's available
"""

import os
import sys
import io
from pathlib import Path
import json

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_downloaded_data():
    """Check what Sunbiz data we have"""
    
    base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
    doc_path = base_path / "doc"
    
    print("=" * 60)
    print("SUNBIZ DATA DOWNLOAD STATUS")
    print("=" * 60)
    
    # Known Sunbiz data types (from their FTP site)
    sunbiz_data_types = {
        'cor': 'Corporations (Active/Inactive)',
        'fic': 'Fictitious Names (DBAs)',
        'lp': 'Limited Partnerships',
        'llc': 'Limited Liability Companies',
        'AG': 'Registered Agents',
        'off': 'Officers/Directors',
        'lien': 'Liens',
        'gp': 'General Partnerships',
        'foreign': 'Foreign Corporations',
        'annual': 'Annual Reports',
        'addr': 'Address Changes',
        'amend': 'Amendments',
        'merge': 'Mergers',
        'name': 'Name Changes',
        'reinstate': 'Reinstatements',
        'withdraw': 'Withdrawals'
    }
    
    print("\n1. WHAT WE SHOULD HAVE (Sunbiz Data Types):")
    print("-" * 40)
    for code, description in sunbiz_data_types.items():
        print(f"  {code:10} - {description}")
    
    print("\n2. WHAT WE ACTUALLY HAVE:")
    print("-" * 40)
    
    downloaded = {}
    missing = []
    
    if doc_path.exists():
        for subdir in sorted(doc_path.iterdir()):
            if subdir.is_dir():
                files = list(subdir.glob("*.txt")) + list(subdir.glob("*.TXT"))
                if files:
                    total_size = sum(f.stat().st_size for f in files)
                    size_mb = total_size / (1024**2)
                    size_gb = total_size / (1024**3)
                    
                    if size_gb > 1:
                        size_str = f"{size_gb:.2f} GB"
                    else:
                        size_str = f"{size_mb:.1f} MB"
                    
                    downloaded[subdir.name] = {
                        'files': len(files),
                        'size': size_str,
                        'path': str(subdir)
                    }
                    
                    print(f"  ✅ {subdir.name:10} - {len(files):5} files - {size_str:>10}")
                    
                    # Check for email content
                    sample_file = files[0]
                    with open(sample_file, 'r', encoding='utf-8', errors='ignore') as f:
                        sample = f.read(5000)
                        if '@' in sample and '.' in sample:
                            email_count = sample.count('@')
                            print(f"     ⚠️  CONTAINS EMAILS (found {email_count} @ symbols in sample)")
    
    # Check what's missing
    for code in sunbiz_data_types:
        if code not in downloaded and code.lower() not in downloaded and code.upper() not in downloaded:
            missing.append(code)
    
    print("\n3. MISSING DATA TYPES:")
    print("-" * 40)
    if missing:
        for code in missing:
            print(f"  ❌ {code:10} - {sunbiz_data_types.get(code, 'Unknown')}")
    else:
        print("  None - all types downloaded")
    
    # Check for officer/email data specifically
    print("\n4. EMAIL/CONTACT DATA CHECK:")
    print("-" * 40)
    
    # Check for officers directory
    off_variations = ['off', 'OFF', 'officers', 'Officers', 'officer']
    officers_found = False
    
    for variant in off_variations:
        check_path = doc_path / variant
        if check_path.exists():
            officers_found = True
            print(f"  ✅ Officers data found at: {check_path}")
            break
    
    if not officers_found:
        print("  ❌ Officers/Directors data NOT found")
        print("     This typically contains officer names and addresses")
        print("     Some versions include email addresses")
    
    # Check registered agents
    ag_path = doc_path / "AG"
    if not ag_path.exists():
        ag_path = doc_path / "ag"
    
    if ag_path.exists():
        ag_files = list(ag_path.glob("*.txt")) + list(ag_path.glob("*.TXT"))
        if ag_files:
            print(f"  ✅ Registered Agents: {len(ag_files)} files found")
            # Check for emails in agents
            with open(ag_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(10000)
                if '@' in sample:
                    print("     ⚠️  AGENTS FILE CONTAINS EMAILS!")
    
    # Check for additional email sources
    print("\n5. SUNBIZ FTP STRUCTURE (What's Available):")
    print("-" * 40)
    print("  ftp://ftp.dos.state.fl.us/public/doc/")
    print("  Directories typically include:")
    print("    - /cor/  - Corporations (weekly updates)")
    print("    - /llc/  - Limited Liability Companies")
    print("    - /lp/   - Limited Partnerships") 
    print("    - /off/  - Officers/Directors (MAY HAVE EMAILS)")
    print("    - /AG/   - Registered Agents")
    print("    - /annual/ - Annual Reports (MAY HAVE EMAILS)")
    print("    - /amend/  - Amendments")
    
    print("\n6. RECOMMENDATION:")
    print("-" * 40)
    print("  TO GET EMAIL DATA, DOWNLOAD:")
    if 'off' not in [d.lower() for d in downloaded.keys()]:
        print("  1. /off/ directory - Officers/Directors with contact info")
    if 'annual' not in [d.lower() for d in downloaded.keys()]:
        print("  2. /annual/ directory - Annual reports may have emails")
    if 'llc' not in [d.lower() for d in downloaded.keys()]:
        print("  3. /llc/ directory - LLC data (separate from cor)")
    
    print("\n  Use FTP client or wget to download:")
    print("  wget -r ftp://ftp.dos.state.fl.us/public/doc/off/")
    print("  wget -r ftp://ftp.dos.state.fl.us/public/doc/annual/")
    
    return downloaded, missing

if __name__ == "__main__":
    downloaded, missing = check_downloaded_data()