"""
Download missing Sunbiz data, especially Officers/Directors with emails
"""

import os
import sys
import io
import ftplib
from pathlib import Path
import requests
from datetime import datetime

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_ftp_server():
    """Check what's available on Sunbiz FTP"""
    
    print("=" * 60)
    print("CHECKING SUNBIZ FTP SERVER")
    print("=" * 60)
    
    try:
        # Try HTTP first (sometimes FTP is blocked)
        base_url = "http://ftp.dos.state.fl.us/public/doc/"
        
        print(f"\nTrying HTTP access: {base_url}")
        response = requests.get(base_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ HTTP access successful!")
            
            # Parse directory listing
            content = response.text
            
            # Look for directories
            if "off" in content.lower():
                print("  ✅ /off/ directory found - Officers/Directors")
            if "annual" in content.lower():
                print("  ✅ /annual/ directory found - Annual Reports")
            if "llc" in content.lower():
                print("  ✅ /llc/ directory found - LLCs")
            if "ag" in content.lower():
                print("  ✅ /AG/ directory found - Registered Agents")
                
    except Exception as e:
        print(f"HTTP access failed: {e}")
        
    # Try FTP
    print("\nTrying FTP access...")
    try:
        ftp_host = "ftp.dos.state.fl.us"
        
        with ftplib.FTP(ftp_host) as ftp:
            ftp.login()  # Anonymous login
            print(f"✅ Connected to {ftp_host}")
            
            # Navigate to doc directory
            ftp.cwd("/public/doc")
            
            # List directories
            directories = []
            ftp.retrlines('LIST', lambda x: directories.append(x))
            
            print("\nAvailable directories on FTP:")
            print("-" * 40)
            
            for item in directories:
                parts = item.split()
                if len(parts) >= 9:
                    name = parts[-1]
                    size = parts[4] if len(parts) > 4 else "?"
                    
                    # Highlight important ones
                    if name in ['off', 'annual', 'llc', 'AG']:
                        print(f"  ⚠️  {name:15} - {size:>10} bytes - IMPORTANT!")
                    else:
                        print(f"     {name:15} - {size:>10} bytes")
            
            # Check officers directory specifically
            print("\nChecking /off/ directory for emails...")
            try:
                ftp.cwd("off")
                off_files = []
                ftp.retrlines('LIST', lambda x: off_files.append(x))
                
                if off_files:
                    print(f"  ✅ Found {len(off_files)} files in /off/ directory")
                    print("     These likely contain officer names and contact info!")
                    
                    # Show recent files
                    print("\n  Recent officer files:")
                    for file_info in off_files[:5]:
                        parts = file_info.split()
                        if len(parts) >= 9:
                            filename = parts[-1]
                            size_bytes = int(parts[4]) if parts[4].isdigit() else 0
                            size_mb = size_bytes / (1024*1024)
                            print(f"    - {filename} ({size_mb:.1f} MB)")
                            
            except Exception as e:
                print(f"  Could not access /off/ directory: {e}")
                
    except Exception as e:
        print(f"FTP access failed: {e}")
        print("\nFTP might be blocked. Try using a different network or VPN.")
    
    # Provide download commands
    print("\n" + "=" * 60)
    print("DOWNLOAD COMMANDS FOR MISSING DATA")
    print("=" * 60)
    
    print("\n1. Using wget (recommended):")
    print("-" * 40)
    print("# Download Officers/Directors (MAY HAVE EMAILS):")
    print("wget -r -np -nH --cut-dirs=2 ftp://ftp.dos.state.fl.us/public/doc/off/")
    print("\n# Download Annual Reports (MAY HAVE EMAILS):")
    print("wget -r -np -nH --cut-dirs=2 ftp://ftp.dos.state.fl.us/public/doc/annual/")
    print("\n# Download LLCs:")
    print("wget -r -np -nH --cut-dirs=2 ftp://ftp.dos.state.fl.us/public/doc/llc/")
    print("\n# Download Registered Agents:")
    print("wget -r -np -nH --cut-dirs=2 ftp://ftp.dos.state.fl.us/public/doc/AG/")
    
    print("\n2. Using Python (if wget not available):")
    print("-" * 40)
    print("# Run: python download_sunbiz_ftp.py --type off")
    print("# Run: python download_sunbiz_ftp.py --type annual")
    
    print("\n3. Using web browser:")
    print("-" * 40)
    print("Navigate to: ftp://ftp.dos.state.fl.us/public/doc/")
    print("Look for these directories:")
    print("  - /off/    - Officers with potential emails")
    print("  - /annual/ - Annual reports with contact info")
    print("  - /llc/    - LLC data (separate from corporations)")
    
    print("\n" + "=" * 60)
    print("IMPORTANT NOTE")
    print("=" * 60)
    print("The /off/ (Officers/Directors) directory is most likely")
    print("to contain email addresses and phone numbers as these")
    print("are sometimes included in officer filing documents.")
    
    return True

if __name__ == "__main__":
    check_ftp_server()