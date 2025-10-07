#!/usr/bin/env python3
"""
Download complete production build from concordbroker.com
"""
import os
import re
import requests
from pathlib import Path
import time

BASE_URL = "https://www.concordbroker.com"
TARGET_DIR = Path("apps/web/production-dist")

def download_file(url, dest_path):
    """Download a file from URL to destination path"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(response.content)
        print(f"[OK] Downloaded: {dest_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        return False

def extract_asset_urls(content):
    """Extract all asset URLs from HTML or JS content"""
    # Pattern for JS/CSS assets
    patterns = [
        r'/assets/[a-zA-Z0-9\-_.]+\.js',
        r'/assets/[a-zA-Z0-9\-_.]+\.css',
        r'/assets/[a-zA-Z0-9\-_.]+\.js\.map',
        r'"([a-zA-Z0-9\-_.]+\.js)"',
    ]

    urls = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match.startswith('/'):
                urls.add(match)
            elif not match.startswith('http'):
                urls.add(f'/assets/{match}')

    return urls

def download_production_build():
    """Download complete production build"""
    print("[START] Starting production build download from concordbroker.com...")

    # Download index.html
    index_url = f"{BASE_URL}/"
    index_path = TARGET_DIR / "index.html"

    print(f"[DOWNLOAD] Downloading index.html...")
    response = requests.get(index_url)
    response.raise_for_status()
    index_content = response.text
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_content)
    print(f"[OK] Downloaded index.html")

    # Extract initial asset URLs from index
    asset_urls = extract_asset_urls(index_content)

    # Known dynamic chunks that are lazy-loaded
    known_chunks = [
        "/assets/PropertySearch-DtIf0Kq0.js",
        "/assets/_...all_-BWxLJFpT.js",
        "/assets/usePropertyData-BMCBE6cN.js",
        "/assets/EnhancedPropertyProfile-Bxu8mDH9.js",
        "/assets/supabase-BSQgP67N.js",
        "/assets/tabs-BAzMwSI9.js",
        "/assets/input-CLDtlUh2.js",
        "/assets/progress-C9pHb4TJ.js",
        "/assets/loader-2-BNrLWU1q.js",
        "/assets/chevron-up-BcDMwJO9.js",
        "/assets/filter-CQW7QY0W.js",
        "/assets/eye-CNxl8TAY.js",
        "/assets/dollar-sign-BdKy6g9j.js",
        "/assets/map-pin-DN_zQv0r.js",
        "/assets/mail-C7eGdXXS.js",
        "/assets/calendar-CuNBDi50.js",
        "/assets/target-C2s9ftC4.js",
        "/assets/building-CoJOaMkG.js",
        "/assets/bed-CdFGLRKU.js",
        "/assets/ruler-CwNVKF3u.js",
        "/assets/tree-pine-BgWzFmC3.js",
        "/assets/search-Bb3o7oJQ.js",
        "/assets/dashboard-e6PBBQy8.js",
        "/assets/TaxDeedSales-jKdXu9FC.js",
        "/assets/TaxDeedSalesTab-B1U-Ej5B.js",
        "/assets/Gate14-CQ8yYXt9.js",
        "/assets/FastPropertySearch-BouTrMsw.js",
        "/assets/AISearch-YPXOxOLF.js",
        "/assets/PerformanceTest-DSKLcUv-.js",
        "/assets/SimplePropertyPage-D94WrRj3.js",
        "/assets/6ELMOJL2-B3NF0S7f.js",
        "/assets/useOptimizedSearch-DQl_Bqef.js"
    ]

    # Add known chunks to asset URLs
    asset_urls.update(known_chunks)

    # Download all assets
    downloaded = []
    failed = []

    for asset_url in asset_urls:
        if not asset_url.startswith('/'):
            asset_url = '/' + asset_url

        # Determine local path
        local_path = TARGET_DIR / asset_url.lstrip('/')

        # Download the asset
        full_url = f"{BASE_URL}{asset_url}"
        if download_file(full_url, local_path):
            downloaded.append(asset_url)

            # If it's a JS file, check for more dependencies
            if asset_url.endswith('.js'):
                try:
                    js_content = local_path.read_text(encoding='utf-8')
                    more_urls = extract_asset_urls(js_content)
                    asset_urls.update(more_urls)
                except:
                    pass
        else:
            failed.append(asset_url)

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    # Summary
    print("\n" + "="*50)
    print("[SUMMARY] Download Summary:")
    print(f"[OK] Successfully downloaded: {len(downloaded)} files")
    if failed:
        print(f"[ERROR] Failed downloads: {len(failed)} files")
        for url in failed[:5]:
            print(f"  - {url}")

    print(f"\n[PATH] Production build saved to: {TARGET_DIR.absolute()}")
    print("[DONE] Done! Your local environment now matches production.")

    return len(failed) == 0

if __name__ == "__main__":
    success = download_production_build()
    exit(0 if success else 1)