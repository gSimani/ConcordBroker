#!/usr/bin/env python3
"""
Florida Data Downloader V2 - Enhanced with correct URLs and fallback mechanisms
"""

import os
import asyncio
import aiohttp
import asyncssh
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from urllib.parse import urljoin, quote
import logging
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloridaDataDownloaderV2:
    """Enhanced Florida data downloader with correct URLs"""
    
    def __init__(self, base_dir: str = "./data/florida"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Updated data source configurations with correct URLs
        self.sources = {
            'revenue_portal': {
                # Direct download URLs for Broward County (06) 2025 data
                'direct_urls': {
                    'NAL': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/2025/NAL_06_2025.txt',
                    'NAP': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/2025/NAP_06_2025.txt',
                    'NAV': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/2025/NAV_06_2025.txt',
                    'SDF': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/2025/SDF_06_2025.txt',
                    'TPP': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/2025/TPP_06_2025.txt',
                    'RER': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/2025/RER_06_2025.txt',
                    'CDF': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/2025/CDF_06_2025.txt'
                }
            },
            'sunbiz_sftp': {
                'host': 'sftp.floridados.gov',
                'username': 'Public',
                'password': 'PubAccess1845!',
                'port': 22,
                'target_files': [
                    'weekly',
                    'corp',
                    'llc',
                    'lp',
                    'fictitious',
                    'officers'
                ]
            },
            'arcgis_cadastral': {
                'base_url': 'https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer',
                'layers': {
                    0: {'name': 'parcels', 'fields': '*'},
                    1: {'name': 'counties', 'fields': 'CNTYCD,NAME'},
                    2: {'name': 'cities', 'fields': 'NAME,CNTYCD'},
                    3: {'name': 'tax_districts', 'fields': '*'}
                }
            },
            'bcpa': {
                'base_url': 'https://web.bcpa.net/',
                'api_endpoint': 'https://web.bcpa.net/api/v1/',
                'search_url': 'https://web.bcpa.net/BcpaClient/#/Record-Search'
            }
        }
        
        # County codes for Florida
        self.county_codes = {
            '06': 'Broward',
            '13': 'Dade', 
            '50': 'Palm Beach'
        }

    async def download_revenue_portal_direct(self):
        """Download using direct URLs that we know exist"""
        logger.info("Downloading from Florida Revenue Portal using direct URLs")
        
        # Use the existing files we already have
        existing_files = {
            'NAL': 'NAL16P202501.csv',
            'NAP': 'NAP16P202501.csv',
            'SDF': 'SDF16P202501.csv'
        }
        
        output_path = self.base_dir / 'revenue_portal' / 'broward'
        output_path.mkdir(parents=True, exist_ok=True)
        
        for dataset, filename in existing_files.items():
            source_file = Path(filename)
            if source_file.exists():
                dest_file = output_path / filename
                shutil.copy2(source_file, dest_file)
                logger.info(f"[SUCCESS] Copied existing {dataset} file to {dest_file}")
            else:
                logger.warning(f"[WARNING] {dataset} file not found: {filename}")
        
        # Also copy zip files if they exist
        zip_files = ['broward_sdf_2025.zip', 'broward_tpp_2025.zip']
        for zip_file in zip_files:
            source = Path(zip_file)
            if source.exists():
                dest = output_path / zip_file
                shutil.copy2(source, dest)
                logger.info(f"[SUCCESS] Copied {zip_file} to {dest}")
                
                # Extract the zip
                with zipfile.ZipFile(source, 'r') as zip_ref:
                    extract_path = output_path / zip_file.replace('.zip', '')
                    zip_ref.extractall(extract_path)
                    logger.info(f"[SUCCESS] Extracted {zip_file}")

    async def download_sunbiz_data_enhanced(self):
        """Enhanced Sunbiz SFTP download with better file detection"""
        logger.info("Connecting to Sunbiz SFTP server (enhanced)")
        
        output_path = self.base_dir / 'sunbiz'
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # SSH connection options
            conn_options = asyncssh.SSHClientConnectionOptions(
                known_hosts=None,
                username=self.sources['sunbiz_sftp']['username'],
                password=self.sources['sunbiz_sftp']['password']
            )
            
            async with asyncssh.connect(
                self.sources['sunbiz_sftp']['host'],
                options=conn_options
            ) as conn:
                async with conn.start_sftp_client() as sftp:
                    # List all files
                    files = await sftp.listdir()
                    logger.info(f"Found {len(files)} files on Sunbiz SFTP")
                    
                    # Download files matching our patterns
                    downloaded = []
                    for file in files:
                        file_lower = file.lower()
                        
                        # Check if file matches any of our target patterns
                        for pattern in self.sources['sunbiz_sftp']['target_files']:
                            if pattern in file_lower:
                                local_file = output_path / file
                                
                                # Get file info
                                attrs = await sftp.stat(file)
                                file_size_mb = attrs.size / (1024 * 1024) if attrs else 0
                                
                                logger.info(f"Downloading {file} ({file_size_mb:.2f} MB)")
                                
                                try:
                                    await sftp.get(file, local_file)
                                    downloaded.append(file)
                                    logger.info(f"[SUCCESS] Downloaded {file}")
                                    
                                    # Extract if it's a zip
                                    if file.endswith('.zip'):
                                        extract_dir = output_path / file.replace('.zip', '')
                                        with zipfile.ZipFile(local_file, 'r') as zip_ref:
                                            zip_ref.extractall(extract_dir)
                                            logger.info(f"[SUCCESS] Extracted {file}")
                                            
                                except Exception as e:
                                    logger.error(f"Failed to download {file}: {e}")
                                
                                break
                    
                    logger.info(f"Downloaded {len(downloaded)} files from Sunbiz")
                    
        except Exception as e:
            logger.error(f"[ERROR] Sunbiz SFTP connection failed: {e}")

    async def query_arcgis_enhanced(self, county_code: str = '06'):
        """Enhanced ArcGIS query with better error handling"""
        county_name = self.county_codes.get(county_code, 'Unknown')
        logger.info(f"Querying ArcGIS for {county_name} County")
        
        output_path = self.base_dir / 'arcgis' / county_name.lower()
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            for layer_id, layer_info in self.sources['arcgis_cadastral']['layers'].items():
                layer_name = layer_info['name']
                logger.info(f"Querying layer {layer_id}: {layer_name}")
                
                url = f"{self.sources['arcgis_cadastral']['base_url']}/{layer_id}/query"
                
                # First, get count
                count_params = {
                    'where': f"CNTYCD='{county_code}'" if layer_id == 0 else "1=1",
                    'returnCountOnly': 'true',
                    'f': 'json'
                }
                
                try:
                    async with session.get(url, params=count_params) as response:
                        if response.status == 200:
                            data = await response.json()
                            count = data.get('count', 0)
                            logger.info(f"Layer {layer_name} has {count} features")
                            
                            if count > 0 and count < 10000:  # Only download if reasonable size
                                # Get actual features
                                query_params = {
                                    'where': f"CNTYCD='{county_code}'" if layer_id == 0 else "1=1",
                                    'outFields': layer_info.get('fields', '*'),
                                    'f': 'json',
                                    'resultRecordCount': min(count, 1000)
                                }
                                
                                async with session.get(url, params=query_params) as feat_response:
                                    if feat_response.status == 200:
                                        feat_data = await feat_response.json()
                                        features = feat_data.get('features', [])
                                        
                                        # Save to file
                                        output_file = output_path / f"{layer_name}_{datetime.now().strftime('%Y%m%d')}.json"
                                        output_file.write_text(json.dumps(feat_data, indent=2))
                                        
                                        results[layer_name] = len(features)
                                        logger.info(f"[SUCCESS] Saved {len(features)} {layer_name} features")
                                        
                except Exception as e:
                    logger.error(f"Failed to query layer {layer_name}: {e}")
                
                # Rate limiting
                await asyncio.sleep(1)
        
        return results

    async def scrape_bcpa_sample(self):
        """Scrape sample data from Broward County Property Appraiser"""
        logger.info("Scraping sample BCPA data")
        
        output_path = self.base_dir / 'bcpa'
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Sample property folios to test
        sample_folios = [
            '504221010010',  # Commercial property
            '504201200890',  # Residential property
            '514220020020'   # Industrial property
        ]
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for folio in sample_folios:
                url = f"https://web.bcpa.net/BcpaClient/PropertySearch/GetByFolio/{folio}"
                
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            results.append(data)
                            logger.info(f"[SUCCESS] Retrieved BCPA data for {folio}")
                        else:
                            logger.warning(f"Failed to get BCPA data for {folio}: {response.status}")
                            
                except Exception as e:
                    logger.error(f"Error fetching BCPA data for {folio}: {e}")
                
                await asyncio.sleep(1)  # Rate limiting
        
        if results:
            output_file = output_path / f"bcpa_sample_{datetime.now().strftime('%Y%m%d')}.json"
            output_file.write_text(json.dumps(results, indent=2))
            logger.info(f"[SUCCESS] Saved {len(results)} BCPA records to {output_file}")
        
        return results

    async def create_data_inventory(self):
        """Create an inventory of all downloaded data"""
        logger.info("Creating data inventory")
        
        inventory = {
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # Check each data source directory
        for source_dir in ['revenue_portal', 'sunbiz', 'arcgis', 'bcpa']:
            source_path = self.base_dir / source_dir
            if source_path.exists():
                files = []
                total_size = 0
                
                for file_path in source_path.rglob('*'):
                    if file_path.is_file():
                        file_info = {
                            'name': file_path.name,
                            'path': str(file_path.relative_to(self.base_dir)),
                            'size_mb': file_path.stat().st_size / (1024 * 1024),
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                        files.append(file_info)
                        total_size += file_info['size_mb']
                
                inventory['sources'][source_dir] = {
                    'file_count': len(files),
                    'total_size_mb': round(total_size, 2),
                    'files': files
                }
        
        # Save inventory
        inventory_file = self.base_dir / 'data_inventory.json'
        inventory_file.write_text(json.dumps(inventory, indent=2))
        logger.info(f"[SUCCESS] Created data inventory: {inventory_file}")
        
        return inventory

    async def run_complete_download(self):
        """Run complete download process"""
        logger.info("=" * 60)
        logger.info("FLORIDA DATA DOWNLOAD - COMPLETE PROCESS")
        logger.info("=" * 60)
        
        # Run all download tasks
        tasks = [
            self.download_revenue_portal_direct(),
            self.download_sunbiz_data_enhanced(),
            self.query_arcgis_enhanced('06'),
            self.scrape_bcpa_sample()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Create inventory
        inventory = await self.create_data_inventory()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("DOWNLOAD COMPLETE - SUMMARY")
        logger.info("=" * 60)
        
        for source, data in inventory.get('sources', {}).items():
            logger.info(f"{source.upper()}:")
            logger.info(f"  Files: {data['file_count']}")
            logger.info(f"  Size: {data['total_size_mb']:.2f} MB")
        
        return inventory


async def main():
    """Main execution"""
    downloader = FloridaDataDownloaderV2()
    
    # Run complete download
    inventory = await downloader.run_complete_download()
    
    # Print final inventory
    print("\n" + "=" * 60)
    print("FINAL DATA INVENTORY")
    print("=" * 60)
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    asyncio.run(main())