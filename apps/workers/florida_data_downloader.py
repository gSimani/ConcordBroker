#!/usr/bin/env python3
"""
Florida Data Downloader - Master script for all Florida data sources
Handles Revenue Portal, Sunbiz SFTP, Geospatial API, and ArcGIS REST
"""

import os
import asyncio
import aiohttp
import asyncssh
import json
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloridaDataDownloader:
    """Master downloader for all Florida data sources"""
    
    def __init__(self, base_dir: str = "./data/florida"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Data source configurations
        self.sources = {
            'revenue_portal': {
                'base_url': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/',
                'tax_roll_path': 'Tax%20Roll%20Data%20Files/',
                'map_data_path': 'Map%20Data/',
                'file_layouts_path': 'File%20Layouts/'
            },
            'sunbiz_sftp': {
                'host': 'sftp.floridados.gov',
                'username': 'Public',
                'password': 'PubAccess1845!',
                'port': 22
            },
            'geodata_api': {
                'base_url': 'https://geodata.floridagio.gov/api/v1/',
                'datasets': {
                    'parcels': 'datasets/florida-parcels',
                    'floods': 'datasets/flood-zones',
                    'counties': 'datasets/county-boundaries',
                    'zoning': 'datasets/zoning-districts',
                    'schools': 'datasets/school-districts'
                }
            },
            'arcgis_cadastral': {
                'base_url': 'https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/',
                'service': 'Florida_Statewide_Cadastral/FeatureServer',
                'layers': {
                    0: 'parcels',
                    1: 'counties',
                    2: 'cities',
                    3: 'tax_districts'
                }
            }
        }
        
        # County codes
        self.county_codes = {
            '01': 'Alachua', '02': 'Baker', '03': 'Bay', '04': 'Bradford',
            '05': 'Brevard', '06': 'Broward', '07': 'Calhoun', '08': 'Charlotte',
            '09': 'Citrus', '10': 'Clay', '11': 'Collier', '12': 'Columbia',
            '13': 'Dade', '14': 'DeSoto', '15': 'Dixie', '16': 'Duval',
            '17': 'Escambia', '18': 'Flagler', '19': 'Franklin', '20': 'Gadsden',
            '21': 'Gilchrist', '22': 'Glades', '23': 'Gulf', '24': 'Hamilton',
            '25': 'Hardee', '26': 'Hendry', '27': 'Hernando', '28': 'Highlands',
            '29': 'Hillsborough', '30': 'Holmes', '31': 'Indian River', '32': 'Jackson',
            '33': 'Jefferson', '34': 'Lafayette', '35': 'Lake', '36': 'Lee',
            '37': 'Leon', '38': 'Levy', '39': 'Liberty', '40': 'Madison',
            '41': 'Manatee', '42': 'Marion', '43': 'Martin', '44': 'Monroe',
            '45': 'Nassau', '46': 'Okaloosa', '47': 'Okeechobee', '48': 'Orange',
            '49': 'Osceola', '50': 'Palm Beach', '51': 'Pasco', '52': 'Pinellas',
            '53': 'Polk', '54': 'Putnam', '55': 'St. Johns', '56': 'St. Lucie',
            '57': 'Santa Rosa', '58': 'Sarasota', '59': 'Seminole', '60': 'Sumter',
            '61': 'Suwannee', '62': 'Taylor', '63': 'Union', '64': 'Volusia',
            '65': 'Wakulla', '66': 'Walton', '67': 'Washington'
        }

    async def download_revenue_portal_data(self, 
                                          county_code: str = '06',
                                          year: str = '2025',
                                          datasets: List[str] = None):
        """Download data from Florida Revenue Portal"""
        if datasets is None:
            datasets = ['NAL', 'NAP', 'NAV', 'SDF', 'TPP', 'RER', 'CDF']
        
        county_name = self.county_codes.get(county_code, 'Unknown')
        logger.info(f"Downloading Revenue Portal data for {county_name} County ({county_code})")
        
        async with aiohttp.ClientSession() as session:
            for dataset in datasets:
                try:
                    # Construct filename (format: DDDYYPMMMMMDD.csv)
                    # DDD = dataset, YY = year, P = period, MMMMMM = county, DD = day
                    filename = f"{dataset}{year[-2:]}P{county_code.zfill(6)}01.csv"
                    url = urljoin(
                        self.sources['revenue_portal']['base_url'],
                        self.sources['revenue_portal']['tax_roll_path'] + filename
                    )
                    
                    output_path = self.base_dir / 'revenue_portal' / county_name.lower()
                    output_path.mkdir(parents=True, exist_ok=True)
                    output_file = output_path / filename
                    
                    # Download file
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            output_file.write_bytes(content)
                            logger.info(f"[SUCCESS] Downloaded {dataset} to {output_file}")
                        else:
                            logger.warning(f"[FAILED] {dataset} - Status: {response.status}")
                            
                except Exception as e:
                    logger.error(f"[ERROR] Failed to download {dataset}: {e}")

    async def download_map_data(self, county_code: str = '06'):
        """Download Map Data from Florida Revenue Portal"""
        county_name = self.county_codes.get(county_code, 'Unknown')
        logger.info(f"Downloading Map Data for {county_name} County")
        
        map_types = ['parcels.zip', 'plats.zip', 'aerials.zip', 'tax_maps.zip']
        
        async with aiohttp.ClientSession() as session:
            for map_type in map_types:
                try:
                    url = urljoin(
                        self.sources['revenue_portal']['base_url'],
                        f"{self.sources['revenue_portal']['map_data_path']}{county_name}/{map_type}"
                    )
                    
                    output_path = self.base_dir / 'map_data' / county_name.lower()
                    output_path.mkdir(parents=True, exist_ok=True)
                    output_file = output_path / map_type
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()
                            output_file.write_bytes(content)
                            
                            # Extract zip files
                            if map_type.endswith('.zip'):
                                with zipfile.ZipFile(output_file, 'r') as zip_ref:
                                    zip_ref.extractall(output_path / map_type.replace('.zip', ''))
                            
                            logger.info(f"[SUCCESS] Downloaded {map_type}")
                        else:
                            logger.warning(f"[FAILED] {map_type} - Status: {response.status}")
                            
                except Exception as e:
                    logger.error(f"[ERROR] Failed to download {map_type}: {e}")

    async def download_sunbiz_data(self):
        """Download Sunbiz data via SFTP"""
        logger.info("Connecting to Sunbiz SFTP server")
        
        try:
            async with asyncssh.connect(
                self.sources['sunbiz_sftp']['host'],
                username=self.sources['sunbiz_sftp']['username'],
                password=self.sources['sunbiz_sftp']['password'],
                known_hosts=None
            ) as conn:
                async with conn.start_sftp_client() as sftp:
                    # List available files
                    files = await sftp.listdir()
                    logger.info(f"Found {len(files)} files on Sunbiz SFTP")
                    
                    output_path = self.base_dir / 'sunbiz'
                    output_path.mkdir(parents=True, exist_ok=True)
                    
                    # Download relevant files
                    target_files = [
                        'weekly_corp.zip',
                        'weekly_llc.zip', 
                        'weekly_lp.zip',
                        'weekly_officers.zip',
                        'annual_reports.zip'
                    ]
                    
                    for file in files:
                        if any(target in file.lower() for target in target_files):
                            local_file = output_path / file
                            await sftp.get(file, local_file)
                            logger.info(f"[SUCCESS] Downloaded {file}")
                            
                            # Extract zip files
                            if file.endswith('.zip'):
                                with zipfile.ZipFile(local_file, 'r') as zip_ref:
                                    zip_ref.extractall(output_path / file.replace('.zip', ''))
                                    
        except Exception as e:
            logger.error(f"[ERROR] Sunbiz SFTP download failed: {e}")

    async def query_arcgis_cadastral(self, 
                                    county_code: str = '06',
                                    layer: int = 0,
                                    limit: int = 1000):
        """Query ArcGIS REST API for cadastral data"""
        county_name = self.county_codes.get(county_code, 'Unknown')
        logger.info(f"Querying ArcGIS cadastral data for {county_name} County")
        
        url = urljoin(
            self.sources['arcgis_cadastral']['base_url'],
            f"{self.sources['arcgis_cadastral']['service']}/{layer}/query"
        )
        
        all_features = []
        offset = 0
        
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    'where': f"CNTYCD='{county_code}'",
                    'outFields': '*',
                    'f': 'json',
                    'returnGeometry': 'true',
                    'resultOffset': offset,
                    'resultRecordCount': limit
                }
                
                try:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            features = data.get('features', [])
                            
                            if not features:
                                break
                                
                            all_features.extend(features)
                            offset += limit
                            
                            logger.info(f"Fetched {len(features)} features (total: {len(all_features)})")
                            
                            # ArcGIS rate limiting
                            await asyncio.sleep(1)
                        else:
                            logger.error(f"ArcGIS query failed: {response.status}")
                            break
                            
                except Exception as e:
                    logger.error(f"[ERROR] ArcGIS query failed: {e}")
                    break
        
        # Save results
        if all_features:
            output_path = self.base_dir / 'arcgis' / county_name.lower()
            output_path.mkdir(parents=True, exist_ok=True)
            
            output_file = output_path / f"parcels_{datetime.now().strftime('%Y%m%d')}.json"
            output_file.write_text(json.dumps({
                'type': 'FeatureCollection',
                'features': all_features
            }, indent=2))
            
            logger.info(f"[SUCCESS] Saved {len(all_features)} parcels to {output_file}")
        
        return all_features

    async def query_geodata_portal(self, dataset: str = 'parcels'):
        """Query Florida Geospatial Open Data Portal"""
        logger.info(f"Querying Florida Geospatial Portal: {dataset}")
        
        endpoint = self.sources['geodata_api']['datasets'].get(dataset)
        if not endpoint:
            logger.error(f"Unknown dataset: {dataset}")
            return
        
        url = urljoin(self.sources['geodata_api']['base_url'], endpoint)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        output_path = self.base_dir / 'geodata'
                        output_path.mkdir(parents=True, exist_ok=True)
                        
                        output_file = output_path / f"{dataset}_{datetime.now().strftime('%Y%m%d')}.json"
                        output_file.write_text(json.dumps(data, indent=2))
                        
                        logger.info(f"[SUCCESS] Downloaded {dataset} to {output_file}")
                        return data
                    else:
                        logger.error(f"Geodata query failed: {response.status}")
                        
            except Exception as e:
                logger.error(f"[ERROR] Geodata query failed: {e}")

    async def download_all_broward(self):
        """Download all data for Broward County"""
        logger.info("Starting complete Broward County data download")
        
        tasks = [
            # Revenue Portal data
            self.download_revenue_portal_data('06', '2025'),
            # Map data
            self.download_map_data('06'),
            # Sunbiz data
            self.download_sunbiz_data(),
            # ArcGIS cadastral
            self.query_arcgis_cadastral('06'),
            # Geodata portal
            self.query_geodata_portal('parcels'),
            self.query_geodata_portal('floods'),
            self.query_geodata_portal('zoning')
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Summary
        logger.info("=" * 50)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 50)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i+1} failed: {result}")
            else:
                logger.info(f"Task {i+1} completed successfully")

    def get_download_status(self) -> Dict[str, Any]:
        """Check status of downloaded files"""
        status = {
            'revenue_portal': {},
            'map_data': {},
            'sunbiz': {},
            'arcgis': {},
            'geodata': {}
        }
        
        # Check Revenue Portal files
        revenue_path = self.base_dir / 'revenue_portal'
        if revenue_path.exists():
            for county_dir in revenue_path.iterdir():
                if county_dir.is_dir():
                    files = list(county_dir.glob('*.csv'))
                    status['revenue_portal'][county_dir.name] = {
                        'files': len(files),
                        'size_mb': sum(f.stat().st_size for f in files) / (1024*1024)
                    }
        
        # Check Map Data
        map_path = self.base_dir / 'map_data'
        if map_path.exists():
            for county_dir in map_path.iterdir():
                if county_dir.is_dir():
                    status['map_data'][county_dir.name] = {
                        'parcels': (county_dir / 'parcels').exists(),
                        'plats': (county_dir / 'plats').exists(),
                        'aerials': (county_dir / 'aerials').exists()
                    }
        
        # Check Sunbiz
        sunbiz_path = self.base_dir / 'sunbiz'
        if sunbiz_path.exists():
            status['sunbiz'] = {
                'files': len(list(sunbiz_path.glob('*'))),
                'last_update': max((f.stat().st_mtime for f in sunbiz_path.glob('*')), default=0)
            }
        
        return status


async def main():
    """Main execution"""
    downloader = FloridaDataDownloader()
    
    # Download all Broward County data
    await downloader.download_all_broward()
    
    # Check status
    status = downloader.get_download_status()
    print("\nDownload Status:")
    print(json.dumps(status, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())