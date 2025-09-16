"""
Florida Revenue NAL/SDF/NAP Users Guide PDF Downloader
Downloads and monitors the official documentation for updates
"""

import os
import hashlib
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaRevenueGuideDownloader:
    """Downloads and monitors the Florida Revenue Users Guide PDF"""
    
    # 2024 Users Guide URL
    PDF_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2024%20Users%20guide%20and%20quick%20reference/2024_NAL_SDF_NAP_Users_Guide.pdf"
    
    # Base URL for checking other years
    BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/"
    
    def __init__(self, data_dir: str = "data/florida_revenue_guide"):
        """
        Initialize the PDF downloader
        
        Args:
            data_dir: Directory to store downloaded files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.pdf_dir = self.data_dir / "pdfs"
        self.extracted_dir = self.data_dir / "extracted"
        self.metadata_dir = self.data_dir / "metadata"
        
        for dir_path in [self.pdf_dir, self.extracted_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Version tracking file
        self.version_file = self.metadata_dir / "version_history.json"
        self.version_history = self._load_version_history()
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _load_version_history(self) -> Dict:
        """Load version history from file"""
        if self.version_file.exists():
            with open(self.version_file, 'r') as f:
                return json.load(f)
        return {
            "versions": [],
            "current_version": None,
            "last_check": None,
            "known_years": ["2024"]
        }
    
    def _save_version_history(self):
        """Save version history to file"""
        with open(self.version_file, 'w') as f:
            json.dump(self.version_history, f, indent=2, default=str)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def check_for_new_year(self) -> Optional[str]:
        """Check if a new year's guide is available"""
        current_year = datetime.now().year
        
        # Check if we've already found this year's guide
        if str(current_year) in self.version_history.get("known_years", []):
            return None
        
        # Try to find new year's guide
        test_urls = [
            f"{current_year}_NAL_SDF_NAP_Users_Guide.pdf",
            f"{current_year}_Users_Guide.pdf",
            f"{current_year}_NAL_SDF_NAP_User_Guide.pdf"
        ]
        
        for filename in test_urls:
            test_url = f"{self.BASE_URL}{current_year}%20Users%20guide%20and%20quick%20reference/{filename}"
            
            try:
                response = self.session.head(test_url, allow_redirects=True, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Found new year's guide: {test_url}")
                    return test_url
            except:
                continue
        
        return None
    
    def download_pdf(self, url: Optional[str] = None) -> Optional[Dict]:
        """
        Download the Users Guide PDF
        
        Args:
            url: Optional custom URL to download from
            
        Returns:
            Download information or None if failed
        """
        if not url:
            url = self.PDF_URL
            
            # Check for newer year's guide
            new_year_url = self.check_for_new_year()
            if new_year_url:
                logger.info(f"Found newer guide, using: {new_year_url}")
                url = new_year_url
                
                # Update known years
                year = datetime.now().year
                if str(year) not in self.version_history.get("known_years", []):
                    self.version_history["known_years"].append(str(year))
        
        logger.info(f"Checking Florida Revenue Users Guide for updates: {url}")
        
        try:
            # Get PDF headers to check if updated
            response = self.session.head(url, allow_redirects=True)
            response.raise_for_status()
            
            # Get file info from headers
            content_length = int(response.headers.get('content-length', 0))
            last_modified = response.headers.get('last-modified', '')
            etag = response.headers.get('etag', '')
            
            logger.info(f"PDF info - Size: {content_length:,} bytes, Modified: {last_modified}")
            
            # Check if we need to download
            need_download = True
            
            if self.version_history['current_version']:
                current = self.version_history['current_version']
                if (current.get('size') == content_length and 
                    current.get('last_modified') == last_modified and
                    current.get('etag') == etag and
                    current.get('url') == url):
                    logger.info("PDF has not been updated since last download")
                    need_download = False
            
            # Update last check time
            self.version_history['last_check'] = datetime.now().isoformat()
            
            if not need_download:
                self._save_version_history()
                return {
                    'status': 'no_update',
                    'message': 'PDF has not been updated',
                    'current_version': self.version_history['current_version']
                }
            
            # Download the PDF
            logger.info("Downloading updated PDF...")
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Extract year from URL or use current year
            year_match = url.split('/')[-1][:4] if url.split('/')[-1][:4].isdigit() else str(datetime.now().year)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"NAL_SDF_NAP_Users_Guide_{year_match}_{timestamp}.pdf"
            pdf_path = self.pdf_dir / pdf_filename
            
            # Save PDF
            with open(pdf_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress reporting
                        if content_length > 0:
                            progress = (downloaded / content_length) * 100
                            if progress % 20 < 0.1:  # Report every 20%
                                logger.debug(f"Download progress: {progress:.1f}%")
            
            # Calculate checksum
            checksum = self._calculate_checksum(pdf_path)
            
            # Create version record
            version_info = {
                'version': timestamp,
                'year': year_match,
                'filename': pdf_filename,
                'path': str(pdf_path),
                'url': url,
                'size': content_length,
                'last_modified': last_modified,
                'etag': etag,
                'checksum': checksum,
                'downloaded_at': datetime.now().isoformat()
            }
            
            # Update version history
            self.version_history['versions'].append(version_info)
            self.version_history['current_version'] = version_info
            self._save_version_history()
            
            # Also save as 'latest' for easy access
            latest_path = self.pdf_dir / "NAL_SDF_NAP_Users_Guide_latest.pdf"
            with open(pdf_path, 'rb') as src, open(latest_path, 'wb') as dst:
                dst.write(src.read())
            
            logger.info(f"Successfully downloaded PDF: {pdf_filename}")
            
            return {
                'status': 'downloaded',
                'message': 'PDF downloaded successfully',
                'version_info': version_info
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to download PDF: {e}")
            return None
    
    def check_for_updates(self) -> bool:
        """
        Check if the PDF has been updated
        
        Returns:
            True if updated, False otherwise
        """
        try:
            # First check current URL
            url = self.version_history.get('current_version', {}).get('url', self.PDF_URL)
            
            response = self.session.head(url, allow_redirects=True)
            response.raise_for_status()
            
            content_length = int(response.headers.get('content-length', 0))
            last_modified = response.headers.get('last-modified', '')
            etag = response.headers.get('etag', '')
            
            if self.version_history['current_version']:
                current = self.version_history['current_version']
                if (current.get('size') != content_length or 
                    current.get('last_modified') != last_modified or
                    current.get('etag') != etag):
                    return True
            else:
                # No current version, so update available
                return True
            
            # Also check for new year's guide
            new_year_url = self.check_for_new_year()
            if new_year_url:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
    
    def get_current_version(self) -> Optional[Dict]:
        """Get information about the current version"""
        return self.version_history.get('current_version')
    
    def get_version_history(self) -> List[Dict]:
        """Get complete version history"""
        return self.version_history.get('versions', [])
    
    def get_latest_pdf_path(self) -> Optional[Path]:
        """Get path to the latest downloaded PDF"""
        latest_path = self.pdf_dir / "NAL_SDF_NAP_Users_Guide_latest.pdf"
        if latest_path.exists():
            return latest_path
        
        # Fallback to current version path
        if self.version_history['current_version']:
            path = Path(self.version_history['current_version']['path'])
            if path.exists():
                return path
        
        return None


if __name__ == "__main__":
    # Initialize downloader
    downloader = FloridaRevenueGuideDownloader()
    
    # Download PDF
    result = downloader.download_pdf()
    
    if result:
        print(f"\nDownload Result: {json.dumps(result, indent=2)}")
        
        # Get current version info
        current = downloader.get_current_version()
        if current:
            print(f"\nCurrent Version:")
            print(f"  Year: {current.get('year', 'Unknown')}")
            print(f"  Version: {current['version']}")
            print(f"  Size: {current['size']:,} bytes")
            print(f"  Modified: {current['last_modified']}")
            print(f"  Checksum: {current['checksum']}")
    else:
        print("Failed to download PDF")