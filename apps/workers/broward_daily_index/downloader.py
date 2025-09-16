"""
Broward County Daily Index Extract Files Downloader
Fetches and monitors daily updates from:
https://www.broward.org/RecordsTaxesTreasury/Records/Pages/DailyIndexExtractFiles.aspx
"""

import os
import re
import time
import json
import zipfile
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BrowardDailyIndexDownloader:
    """Downloads and manages Broward County Daily Index Extract Files"""
    
    BASE_URL = "https://www.broward.org/RecordsTaxesTreasury/Records/Pages/DailyIndexExtractFiles.aspx"
    DOWNLOAD_BASE = "https://www.broward.org"
    
    def __init__(self, data_dir: str = "data/broward_daily_index"):
        """
        Initialize the downloader
        
        Args:
            data_dir: Directory to store downloaded files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.archive_dir = self.data_dir / "archive"
        self.metadata_dir = self.data_dir / "metadata"
        
        for dir_path in [self.raw_dir, self.processed_dir, self.archive_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Load download history
        self.history_file = self.metadata_dir / "download_history.json"
        self.download_history = self._load_history()
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _load_history(self) -> Dict:
        """Load download history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {
            "files": {},
            "last_check": None,
            "total_downloads": 0
        }
    
    def _save_history(self):
        """Save download history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.download_history, f, indent=2, default=str)
    
    def fetch_available_files(self) -> List[Dict]:
        """
        Fetch list of available daily index files from the website
        
        Returns:
            List of file information dictionaries
        """
        logger.info("Fetching available files from Broward County website")
        
        try:
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page: {e}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        files = []
        
        # Look for links to daily index files
        # Common patterns: DailyIndex_YYYYMMDD.zip, DailyExtract_YYYYMMDD.zip
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Check if this is a daily index file
            if any(pattern in href.lower() for pattern in ['dailyindex', 'dailyextract', '.zip']):
                # Extract date from filename
                date_match = re.search(r'(\d{8})', href)
                if date_match:
                    file_date = date_match.group(1)
                    
                    # Build full URL
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            file_url = self.DOWNLOAD_BASE + href
                        else:
                            file_url = self.DOWNLOAD_BASE + '/' + href
                    else:
                        file_url = href
                    
                    file_info = {
                        'url': file_url,
                        'filename': os.path.basename(href),
                        'date': file_date,
                        'date_formatted': datetime.strptime(file_date, '%Y%m%d').strftime('%Y-%m-%d'),
                        'text': text,
                        'size': None  # Will be determined during download
                    }
                    
                    files.append(file_info)
                    logger.debug(f"Found file: {file_info['filename']}")
        
        # Sort by date (newest first)
        files.sort(key=lambda x: x['date'], reverse=True)
        
        logger.info(f"Found {len(files)} daily index files")
        return files
    
    def download_file(self, file_info: Dict) -> Optional[str]:
        """
        Download a single file
        
        Args:
            file_info: Dictionary with file information
            
        Returns:
            Path to downloaded file or None if failed
        """
        filename = file_info['filename']
        url = file_info['url']
        
        # Check if already downloaded
        if filename in self.download_history['files']:
            existing = self.download_history['files'][filename]
            if existing.get('status') == 'completed':
                logger.info(f"File {filename} already downloaded")
                return existing.get('path')
        
        logger.info(f"Downloading {filename} from {url}")
        
        try:
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Get file size
            file_size = int(response.headers.get('content-length', 0))
            file_info['size'] = file_size
            
            # Download to raw directory
            file_path = self.raw_dir / filename
            
            with open(file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress reporting
                        if file_size > 0:
                            progress = (downloaded / file_size) * 100
                            if progress % 10 < 0.1:  # Report every 10%
                                logger.debug(f"Progress: {progress:.1f}%")
            
            # Calculate checksum
            checksum = self._calculate_checksum(file_path)
            
            # Update history
            self.download_history['files'][filename] = {
                'url': url,
                'path': str(file_path),
                'date': file_info['date'],
                'downloaded_at': datetime.now().isoformat(),
                'size': file_size,
                'checksum': checksum,
                'status': 'completed'
            }
            self.download_history['total_downloads'] += 1
            self._save_history()
            
            logger.info(f"Successfully downloaded {filename} ({file_size:,} bytes)")
            return str(file_path)
            
        except requests.RequestException as e:
            logger.error(f"Failed to download {filename}: {e}")
            
            # Update history with failure
            self.download_history['files'][filename] = {
                'url': url,
                'date': file_info['date'],
                'attempted_at': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            }
            self._save_history()
            
            return None
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def extract_zip_file(self, zip_path: str) -> List[str]:
        """
        Extract a downloaded ZIP file
        
        Args:
            zip_path: Path to ZIP file
            
        Returns:
            List of extracted file paths
        """
        zip_path = Path(zip_path)
        if not zip_path.exists():
            logger.error(f"ZIP file not found: {zip_path}")
            return []
        
        # Create extraction directory based on date
        filename = zip_path.stem
        extract_dir = self.processed_dir / filename
        extract_dir.mkdir(exist_ok=True)
        
        extracted_files = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # List contents
                file_list = zip_ref.namelist()
                logger.info(f"Extracting {len(file_list)} files from {zip_path.name}")
                
                # Extract all files
                zip_ref.extractall(extract_dir)
                
                for file_name in file_list:
                    extracted_path = extract_dir / file_name
                    extracted_files.append(str(extracted_path))
                    logger.debug(f"Extracted: {file_name}")
            
            logger.info(f"Successfully extracted {len(extracted_files)} files")
            
        except zipfile.BadZipFile as e:
            logger.error(f"Failed to extract {zip_path}: {e}")
        
        return extracted_files
    
    def download_latest(self, days_back: int = 7) -> Dict:
        """
        Download the latest daily index files
        
        Args:
            days_back: Number of days to look back for files
            
        Returns:
            Summary of downloads
        """
        logger.info(f"Starting download of latest files (last {days_back} days)")
        
        # Update last check time
        self.download_history['last_check'] = datetime.now().isoformat()
        
        # Fetch available files
        available_files = self.fetch_available_files()
        
        if not available_files:
            logger.warning("No files found on website")
            return {'status': 'no_files', 'downloaded': 0}
        
        # Filter to recent files
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
        recent_files = [f for f in available_files if f['date'] >= cutoff_date]
        
        logger.info(f"Found {len(recent_files)} files from last {days_back} days")
        
        # Download each file
        downloaded = []
        extracted = []
        
        for file_info in recent_files:
            file_path = self.download_file(file_info)
            if file_path:
                downloaded.append(file_path)
                
                # Extract if it's a ZIP file
                if file_path.endswith('.zip'):
                    extracted_files = self.extract_zip_file(file_path)
                    extracted.extend(extracted_files)
        
        # Save updated history
        self._save_history()
        
        summary = {
            'status': 'success',
            'downloaded': len(downloaded),
            'extracted': len(extracted),
            'total_available': len(available_files),
            'recent_available': len(recent_files),
            'files': downloaded
        }
        
        logger.info(f"Download complete: {summary['downloaded']} files downloaded, "
                   f"{summary['extracted']} files extracted")
        
        return summary
    
    def monitor_continuous(self, check_interval: int = 3600):
        """
        Continuously monitor for new files
        
        Args:
            check_interval: Seconds between checks (default 1 hour)
        """
        logger.info(f"Starting continuous monitoring (checking every {check_interval} seconds)")
        
        while True:
            try:
                # Download latest files
                summary = self.download_latest(days_back=1)
                
                if summary['downloaded'] > 0:
                    logger.info(f"Downloaded {summary['downloaded']} new files")
                else:
                    logger.info("No new files to download")
                
                # Wait before next check
                logger.info(f"Next check in {check_interval} seconds...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                logger.info(f"Retrying in {check_interval} seconds...")
                time.sleep(check_interval)
    
    def get_download_status(self) -> Dict:
        """Get current download status and statistics"""
        return {
            'last_check': self.download_history.get('last_check'),
            'total_downloads': self.download_history.get('total_downloads', 0),
            'files_tracked': len(self.download_history.get('files', {})),
            'completed': len([f for f in self.download_history.get('files', {}).values() 
                            if f.get('status') == 'completed']),
            'failed': len([f for f in self.download_history.get('files', {}).values() 
                         if f.get('status') == 'failed'])
        }


if __name__ == "__main__":
    # Initialize downloader
    downloader = BrowardDailyIndexDownloader()
    
    # Download latest files
    summary = downloader.download_latest(days_back=30)
    print(f"\nDownload Summary: {json.dumps(summary, indent=2)}")
    
    # Get status
    status = downloader.get_download_status()
    print(f"\nDownload Status: {json.dumps(status, indent=2, default=str)}")