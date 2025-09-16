#!/usr/bin/env python3
"""
Florida Revenue Downloader Readiness Verification
Checks that all dependencies and setup are correct before running the full download.
"""

import sys
import os
import subprocess
from pathlib import Path
import asyncio

def check_python_version():
    """Check if Python version is adequate"""
    print("Python: Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"[FAIL] Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\nDependencies: Checking required packages...")
    required_packages = ['playwright', 'aiohttp', 'aiofiles']
    all_ok = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package} - Installed")
        except ImportError:
            print(f"[FAIL] {package} - Not found")
            all_ok = False
    
    return all_ok

def check_playwright_browser():
    """Check if Playwright browser is installed"""
    print("\nBrowser: Checking Playwright browser...")
    try:
        result = subprocess.run([
            sys.executable, '-c', 
            'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); print("OK")'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("[OK] Playwright Chromium browser - Ready")
            return True
        else:
            print("[FAIL] Playwright browser not ready")
            print("   Run: python -m playwright install chromium")
            return False
    except Exception as e:
        print(f"[FAIL] Playwright browser check failed: {e}")
        return False

def check_directory_structure():
    """Check if output directories can be created"""
    print("\nDirectories: Checking directory structure...")
    base_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP")
    
    try:
        # Test creating a directory
        test_dir = base_dir / "TEST_COUNTY" / "TEST_TYPE"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Test writing a file
        test_file = test_dir / "test.txt"
        test_file.write_text("test")
        
        # Cleanup
        test_file.unlink()
        test_dir.rmdir()
        (base_dir / "TEST_COUNTY").rmdir()
        
        print(f"[OK] Directory structure - OK")
        print(f"   Base path: {base_dir}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Directory structure - Failed: {e}")
        return False

def check_internet_connectivity():
    """Check if we can reach Florida Revenue website"""
    print("\nNetwork: Checking internet connectivity...")
    try:
        import urllib.request
        url = "https://floridarevenue.com"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                print("[OK] Florida Revenue website - Reachable")
                return True
            else:
                print(f"[FAIL] Florida Revenue website - HTTP {response.status}")
                return False
                
    except Exception as e:
        print(f"[FAIL] Internet connectivity - Failed: {e}")
        return False

def check_main_script():
    """Check if the main downloader script exists and imports correctly"""
    print("\nScript: Checking main script...")
    script_path = Path("florida_comprehensive_downloader.py")
    
    if not script_path.exists():
        print("[FAIL] florida_comprehensive_downloader.py - Not found")
        return False
    
    try:
        # Test import
        result = subprocess.run([
            sys.executable, '-c', 
            'from florida_comprehensive_downloader import FloridaRevenueDownloader; print("Import OK")'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("[OK] florida_comprehensive_downloader.py - Ready")
            return True
        else:
            print(f"[FAIL] Main script import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Main script check failed: {e}")
        return False

def estimate_disk_space():
    """Estimate required disk space"""
    print("\nDisk: Estimating disk space...")
    base_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP")
    
    try:
        import shutil
        free_space = shutil.disk_usage(base_dir).free
        free_gb = free_space / (1024**3)
        
        required_gb = 2.0  # Estimate 2GB needed
        
        if free_gb >= required_gb:
            print(f"[OK] Disk space - OK ({free_gb:.1f}GB available, ~{required_gb}GB needed)")
            return True
        else:
            print(f"[WARN] Disk space - Low ({free_gb:.1f}GB available, ~{required_gb}GB needed)")
            return True  # Don't fail, just warn
            
    except Exception as e:
        print(f"[WARN] Could not check disk space: {e}")
        return True

def main():
    """Run all checks"""
    print("Florida Revenue Downloader - Readiness Check")
    print("=" * 60)
    
    checks = [
        check_python_version,
        check_dependencies,
        check_playwright_browser,
        check_directory_structure,
        check_internet_connectivity,
        check_main_script,
        estimate_disk_space
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"ALL CHECKS PASSED ({passed}/{total})")
        print("\nSystem is ready to run the Florida Revenue Downloader!")
        print("\nTo start the download run:")
        print("   python florida_comprehensive_downloader.py")
        print("or")
        print("   .\\run_florida_downloader.ps1")
    else:
        print(f"SOME CHECKS FAILED ({passed}/{total})")
        print("\nPlease fix the issues above before running the downloader.")
        
        if not check_dependencies():
            print("\nTo install dependencies:")
            print("   pip install playwright aiohttp aiofiles")
        
        if not check_playwright_browser():
            print("\nTo install Playwright browser:")
            print("   python -m playwright install chromium")

if __name__ == "__main__":
    main()