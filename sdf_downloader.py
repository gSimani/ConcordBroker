"""
Florida SDF File Downloader
Robust system for downloading Sales Data Files (SDF) from Florida Department of Revenue
with comprehensive error handling, progress tracking, and recovery mechanisms.
"""

import os
import json
import time
import zipfile
import requests
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import hashlib
from urllib.parse import urlparse
from tqdm import tqdm
import shutil

from florida_counties_manager import FloridaCountiesManager


@dataclass
class DownloadStatus:
    """Track download status for each county"""
    county: str
    status: str  # pending, downloading, completed, failed, skipped
    url: str
    file_path: Optional[str] = None
    file_size: int = 0
    download_time: float = 0.0
    error_message: Optional[str] = None
    attempts: int = 0
    last_attempt: Optional[str] = None
    checksum: Optional[str] = None
    extraction_status: str = 'pending'  # pending, extracted, failed
    csv_files: List[str] = None

    def __post_init__(self):
        if self.csv_files is None:
            self.csv_files = []


class SdfFileDownloader:
    """
    Comprehensive SDF file downloader with error handling and recovery
    """

    def __init__(self, download_dir: str = None, max_workers: int = 4):
        """
        Initialize the SDF downloader

        Args:
            download_dir: Directory to store downloaded files
            max_workers: Maximum concurrent downloads
        """
        self.download_dir = Path(download_dir or "C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/SDF_DATA")
        self.max_workers = max_workers
        self.counties_manager = FloridaCountiesManager()

        # Setup logging
        self.setup_logging()

        # Create directory structure
        self.setup_directories()

        # Download tracking
        self.download_status: Dict[str, DownloadStatus] = {}
        self.progress_file = self.download_dir / 'download_progress.json'

        # Load existing progress
        self.load_progress()

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.download_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler
        file_handler = logging.FileHandler(
            log_dir / f'sdf_downloader_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Setup logger
        self.logger = logging.getLogger('SdfDownloader')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def setup_directories(self):
        """Create necessary directory structure"""
        directories = [
            self.download_dir,
            self.download_dir / 'zips',
            self.download_dir / 'extracted',
            self.download_dir / 'logs',
            self.download_dir / 'progress'
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Directory structure created at: {self.download_dir}")

    def load_progress(self):
        """Load existing download progress"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress_data = json.load(f)

                for county, data in progress_data.items():
                    self.download_status[county] = DownloadStatus(**data)

                self.logger.info(f"Loaded progress for {len(self.download_status)} counties")
            except Exception as e:
                self.logger.error(f"Error loading progress: {e}")

    def save_progress(self):
        """Save current download progress"""
        try:
            progress_data = {
                county: asdict(status)
                for county, status in self.download_status.items()
            }

            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving progress: {e}")

    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum for file validation"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating checksum for {file_path}: {e}")
            return ""

    def validate_zip_file(self, file_path: Path) -> bool:
        """Validate that downloaded file is a valid ZIP"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Test the ZIP file
                zip_ref.testzip()
                return True
        except Exception as e:
            self.logger.error(f"Invalid ZIP file {file_path}: {e}")
            return False

    def download_county_sdf(self, county: str, max_retries: int = 3) -> DownloadStatus:
        """
        Download SDF file for a specific county with retry logic

        Args:
            county: County name
            max_retries: Maximum retry attempts

        Returns:
            DownloadStatus object with results
        """
        # Initialize or get existing status
        if county not in self.download_status:
            county_info = self.counties_manager.get_county_info(county)
            self.download_status[county] = DownloadStatus(
                county=county,
                status='pending',
                url=county_info['download_url']
            )

        status = self.download_status[county]

        # Skip if already completed successfully
        if status.status == 'completed' and status.file_path and Path(status.file_path).exists():
            self.logger.info(f"Skipping {county} - already completed")
            status.status = 'skipped'
            return status

        # Update status
        status.status = 'downloading'
        status.last_attempt = datetime.now().isoformat()

        for attempt in range(max_retries):
            status.attempts = attempt + 1

            try:
                self.logger.info(f"Downloading {county} (attempt {attempt + 1}/{max_retries})")

                # Configure session with retries and timeouts
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                # Make request with timeout
                response = session.get(
                    status.url,
                    stream=True,
                    timeout=(30, 300),  # 30s connect, 300s read
                    allow_redirects=True
                )

                if response.status_code == 200:
                    # Prepare file path
                    filename = f"{county}_SDF_{datetime.now().strftime('%Y%m%d')}.zip"
                    file_path = self.download_dir / 'zips' / filename

                    # Get file size for progress bar
                    total_size = int(response.headers.get('content-length', 0))
                    status.file_size = total_size

                    # Download with progress bar
                    start_time = time.time()

                    with open(file_path, 'wb') as f:
                        if total_size > 0:
                            with tqdm(
                                total=total_size,
                                unit='B',
                                unit_scale=True,
                                desc=f"{county[:12]:<12}",
                                leave=False
                            ) as pbar:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        pbar.update(len(chunk))
                        else:
                            # No content-length header
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                    status.download_time = time.time() - start_time
                    status.file_path = str(file_path)

                    # Validate downloaded file
                    if self.validate_zip_file(file_path):
                        status.checksum = self.calculate_file_checksum(file_path)
                        status.status = 'completed'
                        status.error_message = None

                        self.logger.info(
                            f"Successfully downloaded {county}: "
                            f"{file_path.stat().st_size:,} bytes in {status.download_time:.1f}s"
                        )

                        # Save progress after each successful download
                        self.save_progress()
                        return status
                    else:
                        # Invalid ZIP file
                        file_path.unlink(missing_ok=True)
                        raise Exception("Downloaded file is not a valid ZIP")

                else:
                    raise Exception(f"HTTP {response.status_code}: {response.reason}")

            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                self.logger.warning(f"{county} - {error_msg}")
                status.error_message = error_msg

                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt + 1
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

        # All attempts failed
        status.status = 'failed'
        self.logger.error(f"Failed to download {county} after {max_retries} attempts")
        return status

    def extract_sdf_files(self, county: str) -> bool:
        """
        Extract CSV files from downloaded ZIP

        Args:
            county: County name

        Returns:
            True if extraction successful
        """
        if county not in self.download_status:
            return False

        status = self.download_status[county]

        if status.status != 'completed' or not status.file_path:
            return False

        try:
            zip_path = Path(status.file_path)
            if not zip_path.exists():
                return False

            # Create extraction directory
            extract_dir = self.download_dir / 'extracted' / county
            extract_dir.mkdir(parents=True, exist_ok=True)

            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Find CSV/TXT files
            csv_files = []
            for ext in ['*.csv', '*.txt', '*.CSV', '*.TXT']:
                csv_files.extend(list(extract_dir.glob(f"**/{ext}")))

            if csv_files:
                status.csv_files = [str(f) for f in csv_files]
                status.extraction_status = 'extracted'

                self.logger.info(f"Extracted {len(csv_files)} files for {county}")
                return True
            else:
                status.extraction_status = 'failed'
                self.logger.error(f"No CSV/TXT files found in {county} ZIP")
                return False

        except Exception as e:
            status.extraction_status = 'failed'
            self.logger.error(f"Error extracting {county}: {e}")
            return False

    def download_all_counties(self, counties: List[str] = None, max_workers: int = None) -> Dict:
        """
        Download SDF files for multiple counties concurrently

        Args:
            counties: List of counties to download (default: all counties)
            max_workers: Override max workers for this operation

        Returns:
            Summary statistics
        """
        if counties is None:
            counties = self.counties_manager.get_all_counties()

        if max_workers is None:
            max_workers = self.max_workers

        self.logger.info(f"Starting download of {len(counties)} counties with {max_workers} workers")

        start_time = datetime.now()
        summary = {
            'start_time': start_time.isoformat(),
            'counties_requested': len(counties),
            'counties_completed': 0,
            'counties_failed': 0,
            'counties_skipped': 0,
            'total_size_bytes': 0,
            'total_download_time': 0.0,
            'failed_counties': []
        }

        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_county = {
                executor.submit(self.download_county_sdf, county): county
                for county in counties
            }

            # Process completed downloads
            with tqdm(total=len(counties), desc="Overall Progress") as overall_pbar:
                for future in as_completed(future_to_county):
                    county = future_to_county[future]

                    try:
                        status = future.result()

                        if status.status == 'completed':
                            summary['counties_completed'] += 1
                            summary['total_size_bytes'] += status.file_size
                            summary['total_download_time'] += status.download_time

                            # Extract files
                            self.extract_sdf_files(county)

                        elif status.status == 'skipped':
                            summary['counties_skipped'] += 1
                        else:
                            summary['counties_failed'] += 1
                            summary['failed_counties'].append({
                                'county': county,
                                'error': status.error_message
                            })

                    except Exception as e:
                        self.logger.error(f"Error processing {county}: {e}")
                        summary['counties_failed'] += 1
                        summary['failed_counties'].append({
                            'county': county,
                            'error': str(e)
                        })

                    overall_pbar.update(1)

                    # Save progress periodically
                    self.save_progress()

        # Calculate final statistics
        end_time = datetime.now()
        summary['end_time'] = end_time.isoformat()
        summary['total_duration_hours'] = (end_time - start_time).total_seconds() / 3600
        summary['average_download_speed_mbps'] = (
            (summary['total_size_bytes'] / (1024 * 1024)) /
            max(summary['total_download_time'], 1)
        )

        self.logger.info("Download Summary:")
        self.logger.info(f"  Completed: {summary['counties_completed']}")
        self.logger.info(f"  Failed: {summary['counties_failed']}")
        self.logger.info(f"  Skipped: {summary['counties_skipped']}")
        self.logger.info(f"  Total Size: {summary['total_size_bytes'] / (1024**3):.2f} GB")
        self.logger.info(f"  Duration: {summary['total_duration_hours']:.2f} hours")

        # Save final progress and summary
        self.save_progress()
        self.save_download_summary(summary)

        return summary

    def save_download_summary(self, summary: Dict):
        """Save download summary to file"""
        summary_file = self.download_dir / 'progress' / f'download_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        try:
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving summary: {e}")

    def retry_failed_downloads(self) -> Dict:
        """Retry all failed downloads"""
        failed_counties = [
            county for county, status in self.download_status.items()
            if status.status == 'failed'
        ]

        if not failed_counties:
            self.logger.info("No failed downloads to retry")
            return {'retried': 0}

        self.logger.info(f"Retrying {len(failed_counties)} failed downloads")
        return self.download_all_counties(failed_counties)

    def get_download_status(self) -> Dict:
        """Get comprehensive download status"""
        total_counties = len(self.counties_manager.get_all_counties())
        completed = sum(1 for s in self.download_status.values() if s.status == 'completed')
        failed = sum(1 for s in self.download_status.values() if s.status == 'failed')

        return {
            'total_counties': total_counties,
            'completed': completed,
            'failed': failed,
            'pending': total_counties - completed - failed,
            'completion_percentage': (completed / total_counties) * 100 if total_counties > 0 else 0,
            'status_details': {county: asdict(status) for county, status in self.download_status.items()}
        }

    def cleanup_old_files(self, days_old: int = 7):
        """Clean up files older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        for directory in [self.download_dir / 'zips', self.download_dir / 'extracted']:
            if directory.exists():
                for file_path in directory.rglob('*'):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            try:
                                file_path.unlink()
                                self.logger.info(f"Cleaned up old file: {file_path}")
                            except Exception as e:
                                self.logger.error(f"Error cleaning up {file_path}: {e}")


if __name__ == "__main__":
    # Example usage and testing
    downloader = SdfFileDownloader()

    # Test with a few small counties first
    test_counties = downloader.counties_manager.get_test_counties()[:2]

    print(f"Testing downloader with counties: {test_counties}")
    summary = downloader.download_all_counties(test_counties)

    print("\nDownload Summary:")
    print(json.dumps(summary, indent=2, default=str))