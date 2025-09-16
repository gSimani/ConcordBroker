"""
Broward County Export Files Layout PDF Downloader and Monitor
Downloads and monitors the schema documentation PDF for updates
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

class LayoutPDFDownloader:
    """Downloads and monitors the Export Files Layout PDF"""
    
    PDF_URL = "https://www.broward.org/RecordsTaxesTreasury/Records/Documents/ExportFilesLayout.pdf"
    
    def __init__(self, data_dir: str = "data/broward_layout_schema"):
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
            "last_check": None
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
    
    def download_pdf(self) -> Optional[Dict]:
        """
        Download the Export Files Layout PDF
        
        Returns:
            Download information or None if failed
        """
        logger.info("Checking Export Files Layout PDF for updates")
        
        try:
            # Get PDF headers to check if updated
            response = self.session.head(self.PDF_URL, allow_redirects=True)
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
                    current.get('etag') == etag):
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
            response = self.session.get(self.PDF_URL, stream=True)
            response.raise_for_status()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"ExportFilesLayout_{timestamp}.pdf"
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
                'filename': pdf_filename,
                'path': str(pdf_path),
                'url': self.PDF_URL,
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
            latest_path = self.pdf_dir / "ExportFilesLayout_latest.pdf"
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
            response = self.session.head(self.PDF_URL, allow_redirects=True)
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
        latest_path = self.pdf_dir / "ExportFilesLayout_latest.pdf"
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
    downloader = LayoutPDFDownloader()
    
    # Download PDF
    result = downloader.download_pdf()
    
    if result:
        print(f"\nDownload Result: {json.dumps(result, indent=2)}")
        
        # Get current version info
        current = downloader.get_current_version()
        if current:
            print(f"\nCurrent Version:")
            print(f"  Version: {current['version']}")
            print(f"  Size: {current['size']:,} bytes")
            print(f"  Modified: {current['last_modified']}")
            print(f"  Checksum: {current['checksum']}")
    else:
        print("Failed to download PDF")