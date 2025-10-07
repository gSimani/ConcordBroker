#!/usr/bin/env python3
"""
Download the exact production build including all assets
"""
import os
import re
import requests
from pathlib import Path
import time
from bs4 import BeautifulSoup

BASE_URL = "https://www.concordbroker.com"
TARGET_DIR = Path("apps/web/production-exact")

def download_file(url, dest_path, headers=None):
    """Download a file from URL to destination path"""
    try:
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(response.content)
        print(f"[OK] Downloaded: {dest_path.name} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        return False

def extract_all_assets(html_content):
    """Extract all asset URLs from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    assets = set()

    # Get all script tags
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            if not src.startswith('http'):
                src = '/' + src.lstrip('/')
            assets.add(src)

    # Get all link tags
    for link in soup.find_all('link'):
        href = link.get('href')
        if href and ('.css' in href or '.js' in href):
            if not href.startswith('http'):
                href = '/' + href.lstrip('/')
            assets.add(href)

    # Get modulepreload
    for link in soup.find_all('link', rel='modulepreload'):
        href = link.get('href')
        if href:
            if not href.startswith('http'):
                href = '/' + href.lstrip('/')
            assets.add(href)

    return assets

def download_production():
    """Download complete production build"""
    print("[START] Downloading exact production build...")

    # Download main page
    print("\n[1/4] Downloading /properties page...")
    properties_url = f"{BASE_URL}/properties"
    response = requests.get(properties_url)
    html_content = response.text

    # Save the HTML
    properties_path = TARGET_DIR / "properties.html"
    properties_path.parent.mkdir(parents=True, exist_ok=True)
    properties_path.write_text(html_content)
    print(f"[OK] Saved properties.html")

    # Extract all assets
    assets = extract_all_assets(html_content)
    print(f"\n[2/4] Found {len(assets)} assets to download")

    # Download all assets
    downloaded = 0
    for asset_url in assets:
        # Construct full URL
        if not asset_url.startswith('http'):
            full_url = BASE_URL + asset_url
        else:
            full_url = asset_url

        # Determine local path
        local_path = TARGET_DIR / asset_url.lstrip('/')

        # Download the asset
        if download_file(full_url, local_path):
            downloaded += 1
            time.sleep(0.1)  # Be polite

    print(f"\n[3/4] Downloaded {downloaded}/{len(assets)} assets")

    # Download the root index.html
    print("\n[4/4] Downloading index.html...")
    index_response = requests.get(BASE_URL)
    index_content = index_response.text

    # Update paths in index.html to be relative
    index_content = index_content.replace('href="/', 'href="')
    index_content = index_content.replace('src="/', 'src="')

    # Save index.html
    index_path = TARGET_DIR / "index.html"
    index_path.write_text(index_content)
    print("[OK] Saved index.html")

    # Also update properties.html paths
    properties_content = properties_path.read_text()
    properties_content = properties_content.replace('href="/', 'href="')
    properties_content = properties_content.replace('src="/', 'src="')
    properties_path.write_text(properties_content)

    print(f"\n[COMPLETE] Production build saved to: {TARGET_DIR.absolute()}")
    print("\nTo serve this build, run:")
    print(f"  cd scripts && DIST_DIR=../apps/web/production-exact node serve-dist.cjs")

    return True

if __name__ == "__main__":
    download_production()