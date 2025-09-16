"""
Florida Revenue NAP (Non-Ad Valorem Parcel) Counties Downloader
Downloads NAP files for all Florida counties from the state data portal
"""

import os
import hashlib
import json
import logging
import requests
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, quote
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaNAPCountiesDownloader:
    """Downloads NAP data files for all Florida counties"""
    
    # Base URL for Florida Revenue data portal
    BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/"
    
    # Florida county codes and names (same as NAL)
    FLORIDA_COUNTIES = {
        '01': 'Alachua', '02': 'Baker', '03': 'Bay', '04': 'Bradford', '05': 'Brevard',
        '06': 'Broward', '07': 'Calhoun', '08': 'Charlotte', '09': 'Citrus', '10': 'Clay',
        '11': 'Collier', '12': 'Columbia', '13': 'Miami-Dade', '14': 'DeSoto', '15': 'Dixie',
        '16': 'Duval', '17': 'Escambia', '18': 'Flagler', '19': 'Franklin', '20': 'Gadsden',
        '21': 'Gilchrist', '22': 'Glades', '23': 'Gulf', '24': 'Hamilton', '25': 'Hardee',
        '26': 'Hendry', '27': 'Hernando', '28': 'Highlands', '29': 'Hillsborough', '30': 'Holmes',
        '31': 'Indian River', '32': 'Jackson', '33': 'Jefferson', '34': 'Lafayette', '35': 'Lake',
        '36': 'Lee', '37': 'Leon', '38': 'Levy', '39': 'Liberty', '40': 'Madison',
        '41': 'Manatee', '42': 'Marion', '43': 'Martin', '44': 'Monroe', '45': 'Nassau',
        '46': 'Okaloosa', '47': 'Okeechobee', '48': 'Orange', '49': 'Osceola', '50': 'Palm Beach',
        '51': 'Pasco', '52': 'Pinellas', '53': 'Polk', '54': 'Putnam', '55': 'St. Johns',
        '56': 'St. Lucie', '57': 'Santa Rosa', '58': 'Sarasota', '59': 'Seminole', '60': 'Sumter',
        '61': 'Suwannee', '62': 'Taylor', '63': 'Union', '64': 'Volusia', '65': 'Wakulla',
        '66': 'Walton', '67': 'Washington'
    }
    
    # Priority counties (major population centers)
    PRIORITY_COUNTIES = ['06', '13', '29', '48', '50', '52']  # Broward, Miami-Dade, Hillsborough, Orange, Palm Beach, Pinellas
    
    def __init__(self, data_dir: str = "data/florida_nap_counties"):
        """
        Initialize the NAP counties downloader
        
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
            "counties_status": {}
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
    
    def get_nap_file_url(self, county_code: str, year: Optional[int] = None) -> str:
        """
        Construct NAP file URL for a specific county
        
        Args:
            county_code: Two-digit county code
            year: Year for the data (defaults to current year)
            
        Returns:
            URL for the NAP file
        """
        if not year:
            year = datetime.now().year
        
        # NAP file naming pattern: NAP[COUNTY_CODE]P[YEAR].txt
        # Example: NAP06P2025.txt for Broward County 2025
        filename = f"NAP{county_code}P{year}.txt"
        
        # Construct full URL
        url = f"{self.BASE_URL}NAP/{year}P/{filename}"
        
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
    
    def download_county_nap(self, county_code: str, year: Optional[int] = None, force: bool = False) -> Optional[Dict]:
        """
        Download NAP file for a specific county
        
        Args:
            county_code: Two-digit county code
            year: Year for the data
            force: Force download even if file exists
            
        Returns:
            Download information or None if failed
        """
        if not year:
            year = datetime.now().year
        
        county_name = self.FLORIDA_COUNTIES.get(county_code, f"County_{county_code}")
        
        # Get file URL
        url = self.get_nap_file_url(county_code, year)
        
        logger.info(f"Checking NAP file for {county_name} ({county_code}) - Year {year}")
        
        # Check if file exists
        exists, file_info = self.check_file_exists(url)
        
        if not exists:
            logger.warning(f"NAP file not found for {county_name} at {url}")
            return None
        
        # Check if we need to download
        download_key = f"{county_code}_{year}"
        
        if not force and download_key in self.download_history['downloads']:
            previous = self.download_history['downloads'][download_key]
            
            # Check if file has changed
            if (previous.get('size') == file_info['size'] and
                previous.get('etag') == file_info['etag']):
                logger.info(f"NAP file for {county_name} is up to date")
                return {
                    'status': 'up_to_date',
                    'county_code': county_code,
                    'county_name': county_name,
                    'year': year,
                    'file_path': previous.get('file_path')
                }
        
        # Download the file
        logger.info(f"Downloading NAP file for {county_name} ({file_info['size']:,} bytes)")
        
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save file
            filename = f"NAP{county_code}P{year}.txt"
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
                'county_code': county_code,
                'county_name': county_name,
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
            self.download_history['counties_status'][county_code] = {
                'last_download': datetime.now().isoformat(),
                'year': year,
                'status': 'success'
            }
            
            self._save_download_history()
            
            logger.info(f"Successfully downloaded NAP file for {county_name}")
            
            return {
                'status': 'downloaded',
                'county_code': county_code,
                'county_name': county_name,
                'year': year,
                'file_path': str(file_path),
                'size': file_info['size']
            }
            
        except Exception as e:
            logger.error(f"Failed to download NAP file for {county_name}: {e}")
            
            self.download_history['counties_status'][county_code] = {
                'last_attempt': datetime.now().isoformat(),
                'year': year,
                'status': 'failed',
                'error': str(e)
            }
            self._save_download_history()
            
            return None
    
    def download_all_counties(self, year: Optional[int] = None, counties: Optional[List[str]] = None) -> Dict:
        """
        Download NAP files for all or specified counties
        
        Args:
            year: Year for the data
            counties: List of county codes to download (None for all)
            
        Returns:
            Summary of downloads
        """
        if not year:
            year = datetime.now().year
        
        if not counties:
            counties = list(self.FLORIDA_COUNTIES.keys())
        
        logger.info(f"Starting download of NAP files for {len(counties)} counties - Year {year}")
        
        results = {
            'year': year,
            'total_counties': len(counties),
            'successful': [],
            'failed': [],
            'up_to_date': [],
            'start_time': datetime.now().isoformat()
        }
        
        # Sort counties with priority ones first
        sorted_counties = sorted(counties, key=lambda x: (x not in self.PRIORITY_COUNTIES, x))
        
        for i, county_code in enumerate(sorted_counties, 1):
            county_name = self.FLORIDA_COUNTIES.get(county_code, f"County_{county_code}")
            
            logger.info(f"Processing {i}/{len(counties)}: {county_name} ({county_code})")
            
            result = self.download_county_nap(county_code, year)
            
            if result:
                if result['status'] == 'downloaded':
                    results['successful'].append(county_code)
                elif result['status'] == 'up_to_date':
                    results['up_to_date'].append(county_code)
            else:
                results['failed'].append(county_code)
            
            # Rate limiting
            time.sleep(0.5)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Save summary
        self.download_history['last_check'] = datetime.now().isoformat()
        self._save_download_history()
        
        # Log summary
        logger.info(f"\nDownload Summary:")
        logger.info(f"  Total: {results['total_counties']}")
        logger.info(f"  Downloaded: {len(results['successful'])}")
        logger.info(f"  Up to date: {len(results['up_to_date'])}")
        logger.info(f"  Failed: {len(results['failed'])}")
        
        if results['failed']:
            logger.warning(f"  Failed counties: {', '.join(results['failed'])}")
        
        return results
    
    def download_priority_counties(self, year: Optional[int] = None) -> Dict:
        """Download NAP files for priority counties only"""
        return self.download_all_counties(year, self.PRIORITY_COUNTIES)
    
    def get_download_status(self) -> Dict:
        """Get current download status for all counties"""
        status = {
            'last_check': self.download_history.get('last_check'),
            'total_counties': len(self.FLORIDA_COUNTIES),
            'downloaded_counties': len(self.download_history.get('downloads', {})),
            'counties_status': self.download_history.get('counties_status', {}),
            'priority_counties': {
                code: self.FLORIDA_COUNTIES[code]
                for code in self.PRIORITY_COUNTIES
            }
        }
        
        # Calculate county coverage
        downloaded = set()
        for key in self.download_history.get('downloads', {}).keys():
            county_code = key.split('_')[0]
            downloaded.add(county_code)
        
        status['coverage_percentage'] = (len(downloaded) / len(self.FLORIDA_COUNTIES)) * 100
        status['counties_with_data'] = list(downloaded)
        status['counties_missing'] = list(set(self.FLORIDA_COUNTIES.keys()) - downloaded)
        
        return status
    
    def check_for_updates(self, year: Optional[int] = None) -> List[str]:
        """
        Check which counties have updated NAP files
        
        Returns:
            List of county codes with updates
        """
        if not year:
            year = datetime.now().year
        
        updates = []
        
        for county_code in self.FLORIDA_COUNTIES.keys():
            url = self.get_nap_file_url(county_code, year)
            exists, file_info = self.check_file_exists(url)
            
            if exists:
                download_key = f"{county_code}_{year}"
                
                if download_key in self.download_history['downloads']:
                    previous = self.download_history['downloads'][download_key]
                    
                    # Check if file has changed
                    if (previous.get('size') != file_info['size'] or
                        previous.get('etag') != file_info['etag']):
                        updates.append(county_code)
                else:
                    # New file available
                    updates.append(county_code)
        
        return updates


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida NAP Counties Downloader')
    parser.add_argument('--counties', nargs='+', help='County codes to download')
    parser.add_argument('--year', type=int, help='Year for the data')
    parser.add_argument('--priority', action='store_true', help='Download priority counties only')
    parser.add_argument('--all', action='store_true', help='Download all counties')
    parser.add_argument('--status', action='store_true', help='Show download status')
    parser.add_argument('--check-updates', action='store_true', help='Check for updates')
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = FloridaNAPCountiesDownloader()
    
    if args.status:
        # Show status
        status = downloader.get_download_status()
        print(f"\nDownload Status:")
        print(f"  Last check: {status['last_check']}")
        print(f"  Coverage: {status['coverage_percentage']:.1f}%")
        print(f"  Counties with data: {status['downloaded_counties']}/{status['total_counties']}")
        
        if status['counties_missing']:
            print(f"  Missing counties: {len(status['counties_missing'])}")
            
    elif args.check_updates:
        # Check for updates
        updates = downloader.check_for_updates(args.year)
        
        if updates:
            print(f"\nCounties with updates: {len(updates)}")
            for code in updates:
                name = downloader.FLORIDA_COUNTIES.get(code, code)
                print(f"  - {name} ({code})")
        else:
            print("No updates available")
            
    elif args.priority:
        # Download priority counties
        results = downloader.download_priority_counties(args.year)
        print(f"\nDownloaded {len(results['successful'])} priority counties")
        
    elif args.all:
        # Download all counties
        results = downloader.download_all_counties(args.year)
        
    elif args.counties:
        # Download specific counties
        results = downloader.download_all_counties(args.year, args.counties)
        
    else:
        # Default: download Broward County
        result = downloader.download_county_nap('06', args.year)
        if result:
            print(f"\nDownloaded: {result['county_name']}")
            print(f"  File: {result.get('file_path')}")
            print(f"  Size: {result.get('size', 0):,} bytes")