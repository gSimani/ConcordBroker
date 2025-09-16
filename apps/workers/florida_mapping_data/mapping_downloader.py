"""
Florida Revenue Mapping Data Downloader
Downloads GIS mapping data files for all Florida counties
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
import zipfile
from io import BytesIO
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaMappingDownloader:
    """Downloads GIS mapping data files for Florida counties"""
    
    # Base URLs for Florida Revenue mapping data
    BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/"
    INFO_URL = "https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/Mapping%20Data%20Information"
    
    # Mapping data types available
    MAPPING_TYPES = {
        'parcels': 'Property parcel boundaries',
        'sections': 'Section, township, and range boundaries',
        'subdivisions': 'Subdivision boundaries',
        'condos': 'Condominium boundaries',
        'roads': 'Road centerlines and names',
        'water': 'Water features and boundaries',
        'municipal': 'Municipal boundaries',
        'districts': 'Special district boundaries',
        'land_use': 'Land use classifications',
        'zoning': 'Zoning classifications'
    }
    
    # Florida counties with codes
    FLORIDA_COUNTIES = {
        '01': 'Alachua', '02': 'Baker', '03': 'Bay', '04': 'Bradford',
        '05': 'Brevard', '06': 'Broward', '07': 'Calhoun', '08': 'Charlotte',
        '09': 'Citrus', '10': 'Clay', '11': 'Collier', '12': 'Columbia',
        '13': 'Miami-Dade', '14': 'Desoto', '15': 'Dixie', '16': 'Duval',
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
    
    # Priority counties for mapping data
    PRIORITY_COUNTIES = ['06', '13', '29', '48', '50', '52']  # Major population centers
    
    def __init__(self, data_dir: str = "data/florida_mapping"):
        """
        Initialize the mapping downloader
        
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
            "counties_status": {},
            "available_files": {}
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
    
    def scan_available_files(self) -> Dict:
        """
        Scan the mapping data page for available files
        
        Returns:
            Dictionary of available mapping files
        """
        logger.info("Scanning for available mapping data files")
        
        available = {
            'shapefiles': [],
            'geodatabases': [],
            'metadata': [],
            'documentation': [],
            'scan_time': datetime.now().isoformat()
        }
        
        try:
            # Get the mapping data information page
            response = self.session.get(self.INFO_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for links to mapping data files
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                # Check for shapefile links
                if '.zip' in href.lower() and 'shape' in text.lower():
                    file_info = {
                        'name': text,
                        'url': href if href.startswith('http') else f"https://floridarevenue.com{href}",
                        'type': 'shapefile',
                        'found_date': datetime.now().isoformat()
                    }
                    available['shapefiles'].append(file_info)
                
                # Check for geodatabase links
                elif '.gdb' in href.lower() or 'geodatabase' in text.lower():
                    file_info = {
                        'name': text,
                        'url': href if href.startswith('http') else f"https://floridarevenue.com{href}",
                        'type': 'geodatabase',
                        'found_date': datetime.now().isoformat()
                    }
                    available['geodatabases'].append(file_info)
                
                # Check for metadata
                elif '.xml' in href.lower() or 'metadata' in text.lower():
                    file_info = {
                        'name': text,
                        'url': href if href.startswith('http') else f"https://floridarevenue.com{href}",
                        'type': 'metadata',
                        'found_date': datetime.now().isoformat()
                    }
                    available['metadata'].append(file_info)
                
                # Check for documentation
                elif '.pdf' in href.lower() and 'map' in text.lower():
                    file_info = {
                        'name': text,
                        'url': href if href.startswith('http') else f"https://floridarevenue.com{href}",
                        'type': 'documentation',
                        'found_date': datetime.now().isoformat()
                    }
                    available['documentation'].append(file_info)
            
            # Store in history
            self.download_history['available_files'] = available
            self._save_download_history()
            
            logger.info(f"Found {len(available['shapefiles'])} shapefiles")
            logger.info(f"Found {len(available['geodatabases'])} geodatabases")
            logger.info(f"Found {len(available['metadata'])} metadata files")
            logger.info(f"Found {len(available['documentation'])} documentation files")
            
        except Exception as e:
            logger.error(f"Error scanning for mapping files: {e}")
        
        return available
    
    def get_mapping_file_url(self, county_code: str, map_type: str = 'parcels', 
                            year: Optional[int] = None) -> str:
        """
        Construct mapping file URL for a specific county and type
        
        Args:
            county_code: Two-digit county code
            map_type: Type of mapping data
            year: Year for the data (defaults to current year)
            
        Returns:
            URL for the mapping file
        """
        if not year:
            year = datetime.now().year
        
        county_name = self.FLORIDA_COUNTIES.get(county_code, f"County_{county_code}")
        
        # Common URL patterns for mapping data
        # Pattern 1: County-specific shapefiles
        if map_type == 'parcels':
            filename = f"{county_name.replace(' ', '_')}_Parcels_{year}.zip"
        elif map_type == 'roads':
            filename = f"{county_name.replace(' ', '_')}_Roads_{year}.zip"
        elif map_type == 'water':
            filename = f"{county_name.replace(' ', '_')}_Water_{year}.zip"
        else:
            filename = f"{county_name.replace(' ', '_')}_{map_type}_{year}.zip"
        
        url = f"{self.BASE_URL}{year}/{filename}"
        
        return url
    
    def download_mapping_file(self, url: str, filename: str, force: bool = False) -> Optional[Dict]:
        """
        Download a mapping file
        
        Args:
            url: URL of the file to download
            filename: Name to save the file as
            force: Force download even if file exists
            
        Returns:
            Download information or None if failed
        """
        logger.info(f"Downloading mapping file: {filename}")
        
        # Check if already downloaded
        file_path = self.raw_dir / filename
        
        if not force and file_path.exists():
            logger.info(f"File {filename} already exists")
            return {
                'status': 'exists',
                'file_path': str(file_path),
                'filename': filename
            }
        
        try:
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Get file size
            file_size = int(response.headers.get('content-length', 0))
            
            # Download file
            with open(file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress for large files
                        if file_size > 0 and downloaded % (1024 * 1024 * 10) == 0:
                            progress = (downloaded / file_size) * 100
                            logger.debug(f"  Downloaded {progress:.1f}%")
            
            # Calculate checksum
            checksum = self._calculate_checksum(file_path)
            
            # Extract if it's a zip file
            if filename.endswith('.zip'):
                self._extract_zip(file_path)
            
            download_info = {
                'status': 'downloaded',
                'file_path': str(file_path),
                'filename': filename,
                'size': file_size,
                'checksum': checksum,
                'downloaded_at': datetime.now().isoformat()
            }
            
            # Update history
            self.download_history['downloads'][filename] = download_info
            self._save_download_history()
            
            logger.info(f"Successfully downloaded {filename} ({file_size:,} bytes)")
            
            return download_info
            
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return None
    
    def _extract_zip(self, zip_path: Path):
        """Extract a zip file to the extracted directory"""
        try:
            extract_dir = self.extracted_dir / zip_path.stem
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info(f"Extracted {zip_path.name} to {extract_dir}")
            
        except Exception as e:
            logger.error(f"Failed to extract {zip_path.name}: {e}")
    
    def download_county_mapping(self, county_code: str, map_types: Optional[List[str]] = None,
                               year: Optional[int] = None) -> Dict:
        """
        Download mapping data for a specific county
        
        Args:
            county_code: Two-digit county code
            map_types: List of map types to download (None for all)
            year: Year for the data
            
        Returns:
            Download results
        """
        if not year:
            year = datetime.now().year
        
        if not map_types:
            map_types = ['parcels', 'roads', 'water']
        
        county_name = self.FLORIDA_COUNTIES.get(county_code, f"County_{county_code}")
        
        logger.info(f"Downloading mapping data for {county_name} ({county_code})")
        
        results = {
            'county_code': county_code,
            'county_name': county_name,
            'year': year,
            'downloads': [],
            'failed': []
        }
        
        for map_type in map_types:
            url = self.get_mapping_file_url(county_code, map_type, year)
            filename = f"{county_code}_{map_type}_{year}.zip"
            
            result = self.download_mapping_file(url, filename)
            
            if result:
                results['downloads'].append({
                    'map_type': map_type,
                    'filename': filename,
                    'status': result['status']
                })
            else:
                results['failed'].append(map_type)
            
            time.sleep(1)  # Rate limiting
        
        # Update county status
        self.download_history['counties_status'][county_code] = {
            'last_download': datetime.now().isoformat(),
            'year': year,
            'map_types': map_types,
            'status': 'success' if not results['failed'] else 'partial'
        }
        
        self._save_download_history()
        
        return results
    
    def download_all_available(self) -> Dict:
        """Download all available mapping files found in scan"""
        available = self.download_history.get('available_files', {})
        
        if not available:
            available = self.scan_available_files()
        
        results = {
            'downloaded': [],
            'failed': [],
            'start_time': datetime.now().isoformat()
        }
        
        # Download shapefiles
        for file_info in available.get('shapefiles', []):
            filename = file_info['name'].replace(' ', '_').replace('/', '_')
            result = self.download_mapping_file(file_info['url'], filename)
            
            if result:
                results['downloaded'].append(filename)
            else:
                results['failed'].append(filename)
            
            time.sleep(1)
        
        # Download metadata
        for file_info in available.get('metadata', []):
            filename = file_info['name'].replace(' ', '_').replace('/', '_')
            result = self.download_mapping_file(file_info['url'], filename)
            
            if result:
                results['downloaded'].append(filename)
            else:
                results['failed'].append(filename)
            
            time.sleep(0.5)
        
        results['end_time'] = datetime.now().isoformat()
        
        logger.info(f"Downloaded {len(results['downloaded'])} files")
        if results['failed']:
            logger.warning(f"Failed to download: {results['failed']}")
        
        return results
    
    def get_download_status(self) -> Dict:
        """Get current download status"""
        status = {
            'last_check': self.download_history.get('last_check'),
            'total_downloads': len(self.download_history.get('downloads', {})),
            'counties_status': self.download_history.get('counties_status', {}),
            'available_files': self.download_history.get('available_files', {})
        }
        
        # List downloaded files
        status['downloaded_files'] = list(self.download_history.get('downloads', {}).keys())
        
        # Check extracted files
        extracted_dirs = [d.name for d in self.extracted_dir.iterdir() if d.is_dir()]
        status['extracted_datasets'] = extracted_dirs
        
        return status


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida Mapping Data Downloader')
    parser.add_argument('--scan', action='store_true', help='Scan for available files')
    parser.add_argument('--download-all', action='store_true', help='Download all available files')
    parser.add_argument('--county', help='Download mapping for specific county code')
    parser.add_argument('--types', nargs='+', help='Map types to download')
    parser.add_argument('--year', type=int, help='Year for the data')
    parser.add_argument('--status', action='store_true', help='Show download status')
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = FloridaMappingDownloader()
    
    if args.scan:
        # Scan for available files
        available = downloader.scan_available_files()
        print("\nAvailable Mapping Files:")
        print(f"  Shapefiles: {len(available['shapefiles'])}")
        print(f"  Geodatabases: {len(available['geodatabases'])}")
        print(f"  Metadata: {len(available['metadata'])}")
        print(f"  Documentation: {len(available['documentation'])}")
        
    elif args.download_all:
        # Download all available files
        results = downloader.download_all_available()
        print(f"\nDownloaded: {len(results['downloaded'])} files")
        if results['failed']:
            print(f"Failed: {len(results['failed'])} files")
            
    elif args.county:
        # Download county mapping
        results = downloader.download_county_mapping(args.county, args.types, args.year)
        print(f"\nDownloaded mapping for {results['county_name']}:")
        for download in results['downloads']:
            print(f"  - {download['map_type']}: {download['status']}")
        if results['failed']:
            print(f"  Failed: {results['failed']}")
            
    elif args.status:
        # Show status
        status = downloader.get_download_status()
        print("\nDownload Status:")
        print(f"  Total downloads: {status['total_downloads']}")
        print(f"  Extracted datasets: {len(status['extracted_datasets'])}")
        if status['extracted_datasets']:
            print(f"  Datasets: {', '.join(status['extracted_datasets'][:5])}")
            
    else:
        # Default: scan for files
        downloader.scan_available_files()