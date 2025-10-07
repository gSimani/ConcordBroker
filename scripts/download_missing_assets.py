#!/usr/bin/env python3
"""
Download missing production assets from concordbroker.com
Specifically handles dynamic chunks that are imported by other modules
"""
import os
import re
import requests
from pathlib import Path
import time
import json

BASE_URL = "https://www.concordbroker.com"
TARGET_DIR = Path("apps/web/production-dist")

def extract_imports_from_js(js_content):
    """Extract import statements from JS content to find dependencies"""
    # Pattern for import statements like: from"./button-q6bqr-rG.js"
    import_pattern = r'from"\.\/([a-zA-Z0-9\-_.]+\.js)"'
    imports = re.findall(import_pattern, js_content)
    return imports

def download_file(url, dest_path):
    """Download a file from URL to destination path"""
    try:
        print(f"[DOWNLOAD] {url}")
        response = requests.get(url, timeout=30)

        # Check if we got HTML instead of JS (error page)
        if response.headers.get('content-type', '').startswith('text/html'):
            print(f"[SKIP] Got HTML error page for {url}")
            return False

        response.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(response.content)
        print(f"[OK] Downloaded: {dest_path} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        return False

def process_js_file(file_path):
    """Process a JS file to find and download its dependencies"""
    if not file_path.exists():
        return []

    try:
        content = file_path.read_text(encoding='utf-8')
        imports = extract_imports_from_js(content)
        return imports
    except:
        return []

def download_missing_assets():
    """Download all missing assets"""
    print("[START] Checking for missing production assets...")

    # Start with known files that need dependencies
    files_to_check = [
        "PropertySearch-DtIf0Kq0.js",
        "index-ClMffTrI.js",
        "_...all_-BWxLJFpT.js",
        "usePropertyData-BMCBE6cN.js",
        "EnhancedPropertyProfile-Bxu8mDH9.js"
    ]

    # Track what we've checked to avoid loops
    checked_files = set()
    files_to_download = set()

    # Process each file to find dependencies
    while files_to_check:
        current_file = files_to_check.pop(0)
        if current_file in checked_files:
            continue

        checked_files.add(current_file)
        file_path = TARGET_DIR / "assets" / current_file

        # Get dependencies from this file
        deps = process_js_file(file_path)
        for dep in deps:
            if dep not in checked_files:
                files_to_check.append(dep)

            # Check if dependency exists
            dep_path = TARGET_DIR / "assets" / dep
            if not dep_path.exists() or dep_path.stat().st_size < 1000:  # Less than 1KB likely means error page
                files_to_download.add(dep)

    # Additional known dependencies from PropertySearch
    known_deps = [
        "button-q6bqr-rG.js",
        "badge-z9qHCvrg.js",
        "target-YlVtG6sq.js",
        "useIcons-CfUqAIUU.js",
        "TaxDeedSalesTab-CxLiEgIn.js",
        "loader-2-oahdXbD5.js",
        "dollar-sign-CF7MFD4j.js",
        "calendar-Dvh8Yhs-.js",
        "alert-triangle-CNFK4a2r.js",
        "map-pin-DkfcV339.js",
        "info-CyvQchCa.js",
        "mail-BRFrE4XW.js",
        "sparkles-Bg5-Xqn3.js",
        "building-BYB_KvQi.js",
        "filter-DzNtRqfH.js",
        "tree-pine-1869e1FA.js",
        "refresh-cw-IVTQgTBH.js"
    ]

    files_to_download.update(known_deps)

    # Remove files that already exist with proper size
    existing_files = []
    for file_name in list(files_to_download):
        file_path = TARGET_DIR / "assets" / file_name
        if file_path.exists() and file_path.stat().st_size > 1000:
            existing_files.append(file_name)
            files_to_download.remove(file_name)

    print(f"\n[INFO] Found {len(existing_files)} files already downloaded correctly")
    print(f"[INFO] Need to download {len(files_to_download)} missing files")

    # Download missing files
    downloaded = 0
    failed = 0

    for file_name in files_to_download:
        url = f"{BASE_URL}/assets/{file_name}"
        dest_path = TARGET_DIR / "assets" / file_name

        if download_file(url, dest_path):
            downloaded += 1
            # Check the downloaded file for more dependencies
            new_deps = process_js_file(dest_path)
            for dep in new_deps:
                if dep not in checked_files and dep not in files_to_download:
                    dep_path = TARGET_DIR / "assets" / dep
                    if not dep_path.exists() or dep_path.stat().st_size < 1000:
                        print(f"[INFO] Found new dependency: {dep}")
                        files_to_download.add(dep)
        else:
            failed += 1

        time.sleep(0.1)  # Be polite

    print(f"\n[SUMMARY] Downloaded {downloaded} files, {failed} failed")

    # Clean up HTML error files
    print("\n[CLEANUP] Removing HTML error pages...")
    cleaned = 0
    for file_path in (TARGET_DIR / "assets").glob("*.js"):
        try:
            content = file_path.read_bytes()
            if content.startswith(b'<!doctype html>'):
                file_path.unlink()
                cleaned += 1
                print(f"[REMOVED] {file_path.name} (was HTML error page)")
        except:
            pass

    print(f"[CLEANUP] Removed {cleaned} error pages")

    return failed == 0

if __name__ == "__main__":
    success = download_missing_assets()
    exit(0 if success else 1)