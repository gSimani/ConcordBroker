#!/usr/bin/env python3
"""
Florida Data Download Agent - Automated Florida Revenue Portal downloads
Handles authentication, data validation, and scheduling for all Florida datasets
"""

import os
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import zipfile
import pandas as pd
from dataclasses import dataclass
import hashlib
import json
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class DownloadTask:
    dataset_name: str
    url: str
    expected_size: int  # bytes
    file_path: Path
    checksum: Optional[str] = None
    last_modified: Optional[datetime] = None
    status: str = 'pending'
    attempts: int = 0
    max_attempts: int = 3

class FloridaDownloadAgent:
    """
    Automated agent for downloading Florida Revenue Portal data
    Features: Session management, retry logic, data validation, scheduling
    """
    
    def __init__(self):
        self.base_url = "https://floridarevenue.com/property/Pages/DataPortal.aspx"
        self.session = None
        self.download_dir = Path("data/florida/revenue_portal/broward")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Dataset configurations
        self.datasets = {
            'NAL': {
                'description': 'Name and Address List',
                'url_pattern': 'https://floridarevenue.com/property/DataPortal/DownloadData.ashx?file=NAL16P{year}{month:02d}.csv',
                'expected_size': 350_000_000,  # ~350 MB
                'priority': 1
            },
            'NAP': {
                'description': 'Name and Parcel Assessment Roll', 
                'url_pattern': 'https://floridarevenue.com/property/DataPortal/DownloadData.ashx?file=NAP16P{year}{month:02d}.csv',
                'expected_size': 18_000_000,  # ~18 MB
                'priority': 2
            },
            'SDF': {
                'description': 'Sales Disclosure File',
                'url_pattern': 'https://floridarevenue.com/property/DataPortal/DownloadData.ashx?file=SDF16P{year}{month:02d}.csv', 
                'expected_size': 13_000_000,  # ~13 MB
                'priority': 3
            },
            'TPP': {
                'description': 'Tangible Personal Property',
                'url_pattern': 'https://floridarevenue.com/property/DataPortal/DownloadData.ashx?file=TPP16P{year}{month:02d}.csv',
                'expected_size': 5_000_000,  # ~5 MB
                'priority': 4
            }
        }
        
        # Authentication and session management
        self.session_timeout = 1800  # 30 minutes
        self.last_session_refresh = None
        
    async def run(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point called by orchestrator"""
        logger.info("FloridaDownloadAgent starting...")
        
        force_download = task_data.get('force_download', False)
        datasets_to_download = task_data.get('datasets', list(self.datasets.keys()))
        target_year = task_data.get('year', 2025)
        target_month = task_data.get('month', 1)
        
        try:
            # Initialize session
            await self._initialize_session()
            
            # Check for updates if not forcing
            if not force_download:
                updates_available = await self._check_for_updates(datasets_to_download, target_year, target_month)
                if not updates_available:
                    return {
                        'status': 'success',
                        'message': 'No updates available',
                        'downloads': {}
                    }
            
            # Download datasets
            download_results = {}
            for dataset_name in datasets_to_download:
                if dataset_name in self.datasets:
                    result = await self._download_dataset(dataset_name, target_year, target_month, force_download)
                    download_results[dataset_name] = result
                else:
                    logger.warning(f"Unknown dataset: {dataset_name}")
            
            # Validate all downloads
            validation_results = await self._validate_downloads(download_results)
            
            return {
                'status': 'success',
                'downloads': download_results,
                'validation': validation_results,
                'summary': self._create_download_summary(download_results)
            }
            
        except Exception as e:
            logger.error(f"FloridaDownloadAgent failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            await self._cleanup_session()

    async def _initialize_session(self):
        """Initialize authenticated session with Florida Revenue Portal"""
        logger.info("Initializing Florida Revenue Portal session...")
        
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=300, connect=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        # Visit main page to establish session
        async with self.session.get(self.base_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to initialize session: HTTP {response.status}")
        
        self.last_session_refresh = datetime.now()
        logger.info("Session initialized successfully")

    async def _check_for_updates(self, datasets: List[str], year: int, month: int) -> bool:
        """Check if new data is available for download"""
        logger.info(f"Checking for updates for {year}-{month:02d}")
        
        updates_needed = False
        
        for dataset_name in datasets:
            local_file = self._get_local_file_path(dataset_name, year, month)
            
            if not local_file.exists():
                logger.info(f"File {local_file} does not exist - download needed")
                updates_needed = True
                continue
            
            # Check file age (if older than 7 days, consider updating)
            file_age = datetime.now() - datetime.fromtimestamp(local_file.stat().st_mtime)
            if file_age > timedelta(days=7):
                logger.info(f"File {local_file} is {file_age.days} days old - update needed")
                updates_needed = True
                continue
            
            # Check file size against expected
            actual_size = local_file.stat().st_size
            expected_size = self.datasets[dataset_name]['expected_size']
            
            if actual_size < expected_size * 0.8:  # Less than 80% of expected size
                logger.info(f"File {local_file} appears incomplete ({actual_size} bytes) - update needed")
                updates_needed = True
                continue
        
        return updates_needed

    async def _download_dataset(self, dataset_name: str, year: int, month: int, force: bool = False) -> Dict[str, Any]:
        """Download a specific dataset with retry logic"""
        dataset_config = self.datasets[dataset_name]
        download_url = dataset_config['url_pattern'].format(year=year, month=month)
        local_file = self._get_local_file_path(dataset_name, year, month)
        
        logger.info(f"Downloading {dataset_name} from {download_url}")
        
        # Check if already exists and not forcing
        if local_file.exists() and not force:
            file_size = local_file.stat().st_size
            if file_size > dataset_config['expected_size'] * 0.8:
                logger.info(f"File {local_file} already exists and appears complete")
                return {
                    'status': 'skipped',
                    'file_path': str(local_file),
                    'size': file_size,
                    'message': 'File already exists'
                }
        
        # Attempt download with retries
        for attempt in range(3):
            try:
                # Refresh session if needed
                await self._refresh_session_if_needed()
                
                download_result = await self._perform_download(download_url, local_file, dataset_name)
                
                if download_result['status'] == 'success':
                    return download_result
                else:
                    logger.warning(f"Download attempt {attempt + 1} failed: {download_result.get('error')}")
                    if attempt < 2:  # Not last attempt
                        await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
            
            except Exception as e:
                logger.error(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < 2:  # Not last attempt
                    await asyncio.sleep(5 * (attempt + 1))
                else:
                    return {
                        'status': 'failed',
                        'error': str(e),
                        'attempts': attempt + 1
                    }
        
        return {
            'status': 'failed',
            'error': 'All download attempts failed',
            'attempts': 3
        }

    async def _perform_download(self, url: str, local_file: Path, dataset_name: str) -> Dict[str, Any]:
        """Perform the actual file download with progress tracking"""
        start_time = datetime.now()
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return {
                        'status': 'failed',
                        'error': f'HTTP {response.status}: {response.reason}'
                    }
                
                total_size = int(response.headers.get('content-length', 0))
                
                # Create temporary file
                temp_file = local_file.with_suffix('.tmp')
                downloaded = 0
                
                with open(temp_file, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress logging every 50MB
                        if downloaded % (50 * 1024 * 1024) == 0:
                            progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                            logger.info(f"Downloading {dataset_name}: {progress:.1f}% ({downloaded:,} bytes)")
                
                # Validate download
                if total_size > 0 and downloaded < total_size * 0.95:
                    return {
                        'status': 'failed',
                        'error': f'Incomplete download: {downloaded}/{total_size} bytes'
                    }
                
                # Move temp file to final location
                temp_file.rename(local_file)
                
                end_time = datetime.now()
                duration = end_time - start_time
                
                logger.info(f"Download completed: {dataset_name} ({downloaded:,} bytes in {duration})")
                
                return {
                    'status': 'success',
                    'file_path': str(local_file),
                    'size': downloaded,
                    'duration': str(duration),
                    'download_speed': f"{(downloaded / duration.total_seconds() / 1024 / 1024):.2f} MB/s"
                }
        
        except Exception as e:
            # Clean up temp file if it exists
            temp_file = local_file.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            raise e

    async def _refresh_session_if_needed(self):
        """Refresh session if it's getting old"""
        if (self.last_session_refresh and 
            datetime.now() - self.last_session_refresh > timedelta(minutes=20)):
            
            logger.info("Refreshing session...")
            await self._cleanup_session()
            await self._initialize_session()

    async def _validate_downloads(self, download_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all downloaded files"""
        logger.info("Validating downloaded files...")
        
        validation_results = {}
        
        for dataset_name, download_result in download_results.items():
            if download_result.get('status') == 'success':
                file_path = Path(download_result['file_path'])
                validation = await self._validate_file(file_path, dataset_name)
                validation_results[dataset_name] = validation
            else:
                validation_results[dataset_name] = {
                    'status': 'skipped',
                    'reason': 'Download failed'
                }
        
        return validation_results

    async def _validate_file(self, file_path: Path, dataset_name: str) -> Dict[str, Any]:
        """Validate a specific downloaded file"""
        try:
            # Check file exists and size
            if not file_path.exists():
                return {
                    'status': 'failed',
                    'error': 'File does not exist'
                }
            
            file_size = file_path.stat().st_size
            expected_size = self.datasets[dataset_name]['expected_size']
            
            # Size validation
            if file_size < expected_size * 0.8:
                return {
                    'status': 'failed',
                    'error': f'File too small: {file_size} bytes (expected ~{expected_size})'
                }
            
            # Try to read as CSV and get row count
            try:
                df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows
                column_count = len(df.columns)
                
                # Basic structure validation
                if column_count < 5:
                    return {
                        'status': 'warning',
                        'message': f'Few columns detected: {column_count}'
                    }
                
                # Get total row count estimate
                estimated_rows = int(file_size / (df.memory_usage(deep=True).sum() / len(df)))
                
                return {
                    'status': 'success',
                    'file_size': file_size,
                    'columns': column_count,
                    'estimated_rows': estimated_rows,
                    'sample_columns': list(df.columns)[:10]
                }
                
            except Exception as e:
                return {
                    'status': 'warning',
                    'error': f'CSV validation failed: {e}',
                    'file_size': file_size
                }
        
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _get_local_file_path(self, dataset_name: str, year: int, month: int) -> Path:
        """Get the local file path for a dataset"""
        return self.download_dir / f"{dataset_name}16P{year}{month:02d}.csv"

    def _create_download_summary(self, download_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of download session"""
        total_size = 0
        successful_downloads = 0
        failed_downloads = 0
        
        for result in download_results.values():
            if result.get('status') == 'success':
                successful_downloads += 1
                total_size += result.get('size', 0)
            elif result.get('status') == 'failed':
                failed_downloads += 1
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_datasets': len(download_results),
            'successful': successful_downloads,
            'failed': failed_downloads,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'download_location': str(self.download_dir)
        }

    async def _cleanup_session(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_status(self) -> Dict[str, Any]:
        """Get current download status"""
        local_files = {}
        total_size = 0
        
        for dataset_name in self.datasets:
            # Check most recent files (current year/month)
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            file_path = self._get_local_file_path(dataset_name, current_year, current_month)
            
            if file_path.exists():
                stat = file_path.stat()
                local_files[dataset_name] = {
                    'exists': True,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'path': str(file_path)
                }
                total_size += stat.st_size
            else:
                local_files[dataset_name] = {
                    'exists': False,
                    'expected_path': str(file_path)
                }
        
        return {
            'agent': 'FloridaDownloadAgent',
            'status': 'ready',
            'local_files': local_files,
            'total_local_size_mb': round(total_size / 1024 / 1024, 2),
            'download_directory': str(self.download_dir),
            'session_active': self.session is not None
        }