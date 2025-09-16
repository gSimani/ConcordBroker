"""
Florida Revenue NAV (Non-Ad Valorem Assessment) Downloader
Downloads NAV district files from the state data portal
"""

import os
import hashlib
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaNAVDownloader:
    """Downloads NAV data files by district"""
    
    # Base URL for Florida Revenue data portal
    BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/"
    
    # NAV files are organized by district codes (A-Z)
    DISTRICT_CODES = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    def __init__(self, data_dir: str = "data/florida_nav"):
        """
        Initialize the NAV downloader
        
        Args:
            data_dir: Directory to store downloaded files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.raw_dir = self.data_dir / "raw"
        self.extracted_dir = self.data_dir / "extracted"
        self.metadata_dir = self.data_dir / "metadata"
        
        for dir_path in [self.raw_dir, self.extracted_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Download history file
        self.history_file = self.metadata_dir / "download_history.json"
        self.download_history = self._load_download_history()
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _load_download_history(self) -> Dict:
        """Load download history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {
            "downloads": {},
            "last_check": None,
            "districts_status": {}
        }
    
    def _save_download_history(self):
        """Save download history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.download_history, f, indent=2, default=str)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_nav_file_url(self, district_code: str, year: Optional[int] = None) -> str:
        """
        Construct NAV file URL for a specific district
        
        Args:
            district_code: Single letter district code (A-Z)
            year: Year for the data (defaults to current year)
            
        Returns:
            URL for the NAV file
        """
        if not year:
            year = datetime.now().year
        
        # NAV file naming pattern: NAV_[DISTRICT].txt
        # Located in: NAV/[YEAR]/NAV_[DISTRICT]/NAV_[DISTRICT].txt
        filename = f"NAV_{district_code}.txt"
        url = f"{self.BASE_URL}NAV/{year}/NAV%20{district_code}/{filename}"
        
        return url
    
    def check_file_exists(self, url: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a file exists at the given URL
        
        Returns:
            Tuple of (exists, file_info)
        """
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                file_info = {
                    'url': url,
                    'size': int(response.headers.get('content-length', 0)),
                    'last_modified': response.headers.get('last-modified', ''),
                    'etag': response.headers.get('etag', '')
                }
                return True, file_info
            
            return False, None
            
        except Exception as e:
            logger.debug(f"Error checking file {url}: {e}")
            return False, None
    
    def download_district_nav(self, district_code: str, year: Optional[int] = None, force: bool = False) -> Optional[Dict]:
        """
        Download NAV file for a specific district
        
        Args:
            district_code: Single letter district code (A-Z)
            year: Year for the data
            force: Force download even if file exists
            
        Returns:
            Download information or None if failed
        """
        if not year:
            year = datetime.now().year
        
        # Get file URL
        url = self.get_nav_file_url(district_code, year)
        
        logger.info(f"Checking NAV file for District {district_code} - Year {year}")
        
        # Check if file exists
        exists, file_info = self.check_file_exists(url)
        
        if not exists:
            logger.warning(f"NAV file not found for District {district_code} at {url}")
            return None
        
        # Check if we need to download
        download_key = f"{district_code}_{year}"
        
        if not force and download_key in self.download_history['downloads']:
            previous = self.download_history['downloads'][download_key]
            
            # Check if file has changed
            if (previous.get('size') == file_info['size'] and
                previous.get('etag') == file_info['etag']):
                logger.info(f"NAV file for District {district_code} is up to date")
                return {
                    'status': 'up_to_date',
                    'district_code': district_code,
                    'year': year,
                    'file_path': previous.get('file_path')
                }
        
        # Download the file
        logger.info(f"Downloading NAV file for District {district_code} ({file_info['size']:,} bytes)")
        
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save file
            filename = f"NAV_{district_code}_{year}.txt"
            file_path = self.raw_dir / filename
            
            with open(file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            # Calculate checksum
            checksum = self._calculate_checksum(file_path)
            
            # Update download history
            download_info = {
                'district_code': district_code,
                'year': year,
                'url': url,
                'file_path': str(file_path),
                'size': file_info['size'],
                'etag': file_info['etag'],
                'last_modified': file_info['last_modified'],
                'checksum': checksum,
                'downloaded_at': datetime.now().isoformat()
            }
            
            self.download_history['downloads'][download_key] = download_info
            self.download_history['districts_status'][district_code] = {
                'last_download': datetime.now().isoformat(),
                'year': year,
                'status': 'success'
            }
            
            self._save_download_history()
            
            logger.info(f"Successfully downloaded NAV file for District {district_code}")
            
            return {
                'status': 'downloaded',
                'district_code': district_code,
                'year': year,
                'file_path': str(file_path),
                'size': file_info['size']
            }
            
        except Exception as e:
            logger.error(f"Failed to download NAV file for District {district_code}: {e}")
            
            self.download_history['districts_status'][district_code] = {
                'last_attempt': datetime.now().isoformat(),
                'year': year,
                'status': 'failed',
                'error': str(e)
            }
            self._save_download_history()
            
            return None
    
    def download_all_districts(self, year: Optional[int] = None, districts: Optional[List[str]] = None) -> Dict:
        """
        Download NAV files for all or specified districts
        
        Args:
            year: Year for the data
            districts: List of district codes to download (None for all)
            
        Returns:
            Summary of downloads
        """
        if not year:
            year = datetime.now().year
        
        if not districts:
            districts = self.DISTRICT_CODES
        
        logger.info(f"Starting download of NAV files for {len(districts)} districts - Year {year}")
        
        results = {
            'year': year,
            'total_districts': len(districts),
            'successful': [],
            'failed': [],
            'up_to_date': [],
            'start_time': datetime.now().isoformat()
        }
        
        for i, district_code in enumerate(districts, 1):
            logger.info(f"Processing {i}/{len(districts)}: District {district_code}")
            
            result = self.download_district_nav(district_code, year)
            
            if result:
                if result['status'] == 'downloaded':
                    results['successful'].append(district_code)
                elif result['status'] == 'up_to_date':
                    results['up_to_date'].append(district_code)
            else:
                results['failed'].append(district_code)
            
            # Rate limiting
            time.sleep(0.5)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Save summary
        self.download_history['last_check'] = datetime.now().isoformat()
        self._save_download_history()
        
        # Log summary
        logger.info(f"\nDownload Summary:")
        logger.info(f"  Total: {results['total_districts']}")
        logger.info(f"  Downloaded: {len(results['successful'])}")
        logger.info(f"  Up to date: {len(results['up_to_date'])}")
        logger.info(f"  Failed: {len(results['failed'])}")
        
        if results['failed']:
            logger.warning(f"  Failed districts: {', '.join(results['failed'])}")
        
        return results
    
    def get_download_status(self) -> Dict:
        """Get current download status for all districts"""
        status = {
            'last_check': self.download_history.get('last_check'),
            'total_districts': len(self.DISTRICT_CODES),
            'downloaded_districts': len(self.download_history.get('downloads', {})),
            'districts_status': self.download_history.get('districts_status', {})
        }
        
        # Calculate district coverage
        downloaded = set()
        for key in self.download_history.get('downloads', {}).keys():
            district_code = key.split('_')[0]
            downloaded.add(district_code)
        
        status['coverage_percentage'] = (len(downloaded) / len(self.DISTRICT_CODES)) * 100
        status['districts_with_data'] = list(downloaded)
        status['districts_missing'] = list(set(self.DISTRICT_CODES) - downloaded)
        
        return status
    
    def check_for_updates(self, year: Optional[int] = None) -> List[str]:
        """
        Check which districts have updated NAV files
        
        Returns:
            List of district codes with updates
        """
        if not year:
            year = datetime.now().year
        
        updates = []
        
        for district_code in self.DISTRICT_CODES:
            url = self.get_nav_file_url(district_code, year)
            exists, file_info = self.check_file_exists(url)
            
            if exists:
                download_key = f"{district_code}_{year}"
                
                if download_key in self.download_history['downloads']:
                    previous = self.download_history['downloads'][download_key]
                    
                    # Check if file has changed
                    if (previous.get('size') != file_info['size'] or
                        previous.get('etag') != file_info['etag']):
                        updates.append(district_code)
                else:
                    # New file available
                    updates.append(district_code)
        
        return updates


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida NAV Downloader')
    parser.add_argument('--districts', nargs='+', help='District codes to download (A-Z)')
    parser.add_argument('--year', type=int, help='Year for the data')
    parser.add_argument('--all', action='store_true', help='Download all districts')
    parser.add_argument('--status', action='store_true', help='Show download status')
    parser.add_argument('--check-updates', action='store_true', help='Check for updates')
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = FloridaNAVDownloader()
    
    if args.status:
        # Show status
        status = downloader.get_download_status()
        print(f"\nDownload Status:")
        print(f"  Last check: {status['last_check']}")
        print(f"  Coverage: {status['coverage_percentage']:.1f}%")
        print(f"  Districts with data: {status['downloaded_districts']}/{status['total_districts']}")
        
        if status['districts_missing']:
            print(f"  Missing districts: {', '.join(status['districts_missing'])}")
            
    elif args.check_updates:
        # Check for updates
        updates = downloader.check_for_updates(args.year)
        
        if updates:
            print(f"\nDistricts with updates: {len(updates)}")
            print(f"  Districts: {', '.join(updates)}")
        else:
            print("No updates available")
            
    elif args.all:
        # Download all districts
        results = downloader.download_all_districts(args.year)
        
    elif args.districts:
        # Download specific districts
        results = downloader.download_all_districts(args.year, args.districts)
        
    else:
        # Default: download District A
        result = downloader.download_district_nav('A', args.year)
        if result:
            print(f"\nDownloaded: District {result['district_code']}")
            print(f"  File: {result.get('file_path')}")
            print(f"  Size: {result.get('size', 0):,} bytes")