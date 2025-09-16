#!/usr/bin/env python3
"""
Download missing Florida data files - RER, CDF, Map Data
Direct download from Florida Revenue Portal
"""

import os
import requests
import zipfile
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_missing_data():
    """Download missing Florida Revenue data files"""
    
    base_path = Path('data/florida/revenue_portal/broward')
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Files we need to download (2025 Broward County)
    missing_files = {
        'RER': {
            'desc': 'Real Estate Transfer',
            'urls': [
                'https://floridarevenue.com/property/Documents/dr219rer.pdf',  # RER form
                'https://floridarevenue.com/property/Documents/rer_file_layout.pdf'  # Layout
            ]
        },
        'CDF': {
            'desc': 'Code Definition File',
            'urls': [
                'https://floridarevenue.com/property/Documents/cdf_codes_2025.pdf',
                'https://floridarevenue.com/property/Documents/use_codes.pdf'
            ]
        },
        'Map_Data': {
            'desc': 'GIS Map Data',
            'urls': [
                'https://www.broward.org/RecordsTaxesTreasury/Records/Documents/PlatBookPages.zip',
                'https://gis.broward.org/data/parcels.zip'
            ]
        }
    }
    
    downloaded = []
    failed = []
    
    for file_type, info in missing_files.items():
        logger.info(f"Attempting to download {info['desc']} ({file_type})")
        
        for url in info['urls']:
            filename = url.split('/')[-1]
            output_file = base_path / filename
            
            try:
                logger.info(f"  Downloading: {filename}")
                response = requests.get(url, timeout=30, stream=True)
                
                if response.status_code == 200:
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    downloaded.append(filename)
                    logger.info(f"  [SUCCESS] Downloaded {filename}")
                    
                    # Extract if ZIP
                    if filename.endswith('.zip'):
                        extract_dir = base_path / filename.replace('.zip', '')
                        with zipfile.ZipFile(output_file, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                            logger.info(f"  [SUCCESS] Extracted {filename}")
                else:
                    logger.warning(f"  [FAILED] {filename} - Status: {response.status_code}")
                    failed.append(filename)
                    
            except Exception as e:
                logger.error(f"  [ERROR] Failed to download {filename}: {e}")
                failed.append(filename)
    
    # Try alternative sources for Broward GIS data
    broward_gis_urls = [
        'https://bcgis.broward.org/arcgis/rest/services/Parcels/MapServer',
        'https://gis.broward.org/GISData/Download',
        'https://www.broward.org/GIS/Pages/default.aspx'
    ]
    
    logger.info("\nChecking Broward County GIS sources:")
    for url in broward_gis_urls:
        try:
            response = requests.head(url, timeout=5)
            if response.status_code < 400:
                logger.info(f"  [AVAILABLE] {url}")
            else:
                logger.info(f"  [UNAVAILABLE] {url} - Status: {response.status_code}")
        except:
            logger.info(f"  [UNREACHABLE] {url}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("="*60)
    logger.info(f"Downloaded: {len(downloaded)} files")
    for f in downloaded:
        logger.info(f"  ✓ {f}")
    
    if failed:
        logger.info(f"\nFailed: {len(failed)} files")
        for f in failed:
            logger.info(f"  ✗ {f}")
    
    # Check what we have
    logger.info("\nExisting Florida data files:")
    data_dir = Path('data/florida/revenue_portal/broward')
    if data_dir.exists():
        files = list(data_dir.glob('*'))
        for f in files:
            size_mb = f.stat().st_size / (1024*1024) if f.is_file() else 0
            logger.info(f"  {f.name} ({size_mb:.2f} MB)")
    
    return downloaded, failed


def create_florida_data_summary():
    """Create a summary of all Florida data we have"""
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'data_sources': {
            'Revenue_Portal': {
                'NAL': 'NAL16P202501.csv',  # Name/Address/Legal
                'NAP': 'NAP16P202501.csv',  # Non-Ad Valorem
                'NAV': 'Not found locally',  # Need to download
                'SDF': 'SDF16P202501.csv',  # Sales Data File
                'TPP': 'broward_tpp_2025.zip',  # Tangible Personal Property
                'RER': 'Not downloaded',  # Real Estate Transfer
                'CDF': 'Not downloaded'   # Code Definition
            },
            'Map_Data': 'Not downloaded',
            'Sunbiz': 'Pipeline configured',
            'ArcGIS': 'API available',
            'BCPA': 'Web scraping ready'
        },
        'next_steps': [
            '1. Download NAV (Value Assessment) data',
            '2. Download RER (Real Estate Transfer) data', 
            '3. Download CDF (Code Definition) files',
            '4. Access Broward GIS map data',
            '5. Setup automated Sunbiz SFTP sync',
            '6. Connect to ArcGIS REST API for parcels'
        ]
    }
    
    # Save summary
    summary_file = Path('FLORIDA_DATA_SUMMARY.json')
    import json
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nCreated data summary: {summary_file}")
    return summary


if __name__ == "__main__":
    # Download missing files
    downloaded, failed = download_missing_data()
    
    # Create summary
    summary = create_florida_data_summary()
    
    print("\n" + "="*60)
    print("FLORIDA DATA STATUS")
    print("="*60)
    print("Available:")
    print("  ✓ NAL - Name/Address/Legal")
    print("  ✓ NAP - Non-Ad Valorem Assessment") 
    print("  ✓ SDF - Sales Data File")
    print("  ✓ TPP - Tangible Personal Property")
    print("\nMissing:")
    print("  ✗ NAV - Value Assessment")
    print("  ✗ RER - Real Estate Transfer")
    print("  ✗ CDF - Code Definition")
    print("  ✗ Map Data - GIS/Parcels")
    print("\nConfigured:")
    print("  ✓ Sunbiz Pipeline")
    print("  ✓ Database Tables")
    print("  ✓ Data Agents")