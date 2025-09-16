#!/usr/bin/env python3
"""
Florida Data Downloader Agent
Downloads Florida property data files with resume capability.
Handles large files reliably with checksums and verification.
"""

import asyncio
import logging
import hashlib
import aiohttp
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import sqlite3
import zipfile
import shutil
from urllib.parse import urlparse
import time
import math

logger = logging.getLogger(__name__)

@dataclass
class DownloadResult:
    """Result of a download operation"""
    url: str
    filename: str
    local_path: str
    size: int
    duration: float
    success: bool
    error: Optional[str] = None
    checksum: Optional[str] = None
    resume_count: int = 0

@dataclass
class DownloadProgress:
    """Download progress information"""
    url: str
    filename: str
    total_size: int
    downloaded: int
    speed: float  # bytes per second
    eta: float  # estimated time remaining in seconds
    percentage: float

class FloridaDataDownloader:
    """Downloads Florida Department of Revenue data files"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.download_dir = Path(config.get('download_directory', 'florida_daily_updates/data'))
        self.temp_dir = Path(config.get('temp_directory', 'florida_daily_updates/temp'))
        self.max_concurrent = config.get('max_concurrent_downloads', 3)
        self.chunk_size = config.get('chunk_size', 1024 * 1024)  # 1MB chunks
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 30)  # seconds
        self.timeout = config.get('timeout', 3600)  # 1 hour
        self.verify_checksums = config.get('verify_checksums', True)
        self.extract_archives = config.get('extract_archives', True)
        
        # Progress tracking
        self.progress_callbacks = []
        self.downloads_in_progress = {}
        
        # State database
        self.db_path = Path(config.get('state_db_path', 'florida_downloader_state.db'))
        
        # Ensure directories exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Statistics
        self.download_stats = {
            'total_downloads': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'bytes_downloaded': 0,
            'total_time': 0.0,
            'average_speed': 0.0
        }
    
    def _init_database(self):
        """Initialize SQLite database for state tracking"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    size INTEGER,
                    checksum TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration REAL,
                    success BOOLEAN,
                    error TEXT,
                    resume_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS download_state (
                    url TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    total_size INTEGER,
                    downloaded INTEGER DEFAULT 0,
                    checksum TEXT,
                    temp_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            
            conn.commit()
    
    async def download_file(self, url: str, filename: Optional[str] = None) -> DownloadResult:
        """Download a single file with resume capability"""
        if not filename:
            filename = Path(urlparse(url).path).name
        
        start_time = time.time()
        
        try:
            # Check if download is already in progress
            if url in self.downloads_in_progress:
                logger.warning(f"Download already in progress: {filename}")
                return self.downloads_in_progress[url]
            
            # Create download result placeholder
            result = DownloadResult(
                url=url,
                filename=filename,
                local_path="",
                size=0,
                duration=0.0,
                success=False
            )
            
            self.downloads_in_progress[url] = result
            
            try:
                # Check for partial download
                partial_info = self._get_partial_download_info(url)
                resume_from = partial_info['downloaded'] if partial_info else 0
                
                # Get file info
                total_size = await self._get_file_size(url)
                if total_size is None:
                    raise Exception("Could not determine file size")
                
                # Set up paths
                final_path = self._get_download_path(filename)
                temp_path = self.temp_dir / f"{filename}.tmp"
                
                # Download with resume
                actual_size = await self._download_with_resume(
                    url, temp_path, resume_from, total_size
                )
                
                # Verify download
                if actual_size != total_size:
                    raise Exception(f"Size mismatch: expected {total_size}, got {actual_size}")
                
                # Calculate checksum if enabled
                checksum = None
                if self.verify_checksums:
                    checksum = await self._calculate_checksum(temp_path)
                
                # Move to final location
                if final_path.exists():
                    shutil.copy2(str(final_path), str(final_path.with_suffix('.bak')))
                
                shutil.move(str(temp_path), str(final_path))
                
                # Extract if it's an archive
                extracted_path = final_path
                if self.extract_archives and self._is_archive(final_path):
                    extracted_path = await self._extract_archive(final_path)
                
                # Update result
                duration = time.time() - start_time
                result.local_path = str(extracted_path)
                result.size = actual_size
                result.duration = duration
                result.success = True
                result.checksum = checksum
                result.resume_count = partial_info['retry_count'] if partial_info else 0
                
                # Update statistics
                self._update_download_stats(result)
                
                # Save to database
                await self._save_download_result(result)
                
                # Clean up state
                self._clean_download_state(url)
                
                logger.info(f"Successfully downloaded {filename} ({actual_size:,} bytes in {duration:.1f}s)")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                result.duration = duration
                result.error = str(e)
                
                # Update retry count
                self._increment_retry_count(url)
                
                logger.error(f"Failed to download {filename}: {e}")
                return result
            
            finally:
                # Remove from in-progress tracking
                self.downloads_in_progress.pop(url, None)
                
        except Exception as e:
            logger.error(f"Critical error downloading {filename}: {e}")
            return DownloadResult(
                url=url,
                filename=filename or "unknown",
                local_path="",
                size=0,
                duration=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def download_multiple(self, urls: List[str], max_concurrent: Optional[int] = None) -> List[DownloadResult]:
        """Download multiple files concurrently"""
        if max_concurrent is None:
            max_concurrent = self.max_concurrent
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(url: str) -> DownloadResult:
            async with semaphore:
                return await self.download_file(url)
        
        tasks = [download_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(DownloadResult(
                    url=urls[i],
                    filename=Path(urlparse(urls[i]).path).name,
                    local_path="",
                    size=0,
                    duration=0.0,
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _get_file_size(self, url: str) -> Optional[int]:
        """Get file size from HTTP headers"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    if 'content-length' in response.headers:
                        return int(response.headers['content-length'])
                    return None
        except Exception as e:
            logger.error(f"Error getting file size for {url}: {e}")
            return None
    
    async def _download_with_resume(self, url: str, temp_path: Path, resume_from: int, total_size: int) -> int:
        """Download file with resume capability"""
        headers = {}
        if resume_from > 0:
            headers['Range'] = f'bytes={resume_from}-'
            logger.info(f"Resuming download from byte {resume_from:,}")
        
        downloaded = resume_from
        start_time = time.time()
        last_update = start_time
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                # Check if resume is supported
                if resume_from > 0 and response.status not in [206, 200]:
                    raise Exception(f"Server doesn't support resume: HTTP {response.status}")
                
                # Open file for writing
                mode = 'ab' if resume_from > 0 else 'wb'
                async with aiofiles.open(temp_path, mode) as f:
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        current_time = time.time()
                        if current_time - last_update >= 1.0:  # Update every second
                            elapsed = current_time - start_time
                            speed = (downloaded - resume_from) / elapsed if elapsed > 0 else 0
                            eta = (total_size - downloaded) / speed if speed > 0 else 0
                            percentage = (downloaded / total_size) * 100
                            
                            progress = DownloadProgress(
                                url=url,
                                filename=temp_path.name,
                                total_size=total_size,
                                downloaded=downloaded,
                                speed=speed,
                                eta=eta,
                                percentage=percentage
                            )
                            
                            await self._notify_progress(progress)
                            last_update = current_time
                            
                            # Update state database
                            self._update_download_state(url, downloaded)
        
        return downloaded
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(self.chunk_size):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _get_download_path(self, filename: str) -> Path:
        """Get the final download path for a file"""
        # Create year/type directory structure
        date_str = datetime.now().strftime('%Y-%m')
        file_type = self._detect_file_type(filename)
        
        download_path = self.download_dir / date_str / file_type
        download_path.mkdir(parents=True, exist_ok=True)
        
        return download_path / filename
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        filename_lower = filename.lower()
        
        if 'nal' in filename_lower:
            return 'NAL'
        elif 'nap' in filename_lower:
            return 'NAP'
        elif 'sdf' in filename_lower:
            return 'SDF'
        elif 'permit' in filename_lower:
            return 'permits'
        else:
            return 'other'
    
    def _is_archive(self, file_path: Path) -> bool:
        """Check if file is an archive"""
        return file_path.suffix.lower() in ['.zip', '.tar', '.gz', '.bz2']
    
    async def _extract_archive(self, archive_path: Path) -> Path:
        """Extract archive file"""
        extract_dir = archive_path.with_suffix('')
        extract_dir.mkdir(exist_ok=True)
        
        if archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find the main data file in extracted contents
            data_files = list(extract_dir.glob('*.csv')) + list(extract_dir.glob('*.txt'))
            if data_files:
                return data_files[0]
        
        return extract_dir
    
    def _get_partial_download_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get information about partial download"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT total_size, downloaded, retry_count, temp_path FROM download_state WHERE url = ?',
                (url,)
            )
            result = cursor.fetchone()
            
            if result:
                total_size, downloaded, retry_count, temp_path = result
                
                # Check if temp file exists
                if temp_path and Path(temp_path).exists():
                    actual_size = Path(temp_path).stat().st_size
                    return {
                        'total_size': total_size,
                        'downloaded': min(downloaded, actual_size),  # Use smaller of recorded vs actual
                        'retry_count': retry_count,
                        'temp_path': temp_path
                    }
            
            return None
    
    def _update_download_state(self, url: str, downloaded: int):
        """Update download state in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE download_state 
                SET downloaded = ?, last_updated = CURRENT_TIMESTAMP
                WHERE url = ?
            ''', (downloaded, url))
            conn.commit()
    
    def _increment_retry_count(self, url: str):
        """Increment retry count for a download"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE download_state 
                SET retry_count = retry_count + 1, last_updated = CURRENT_TIMESTAMP
                WHERE url = ?
            ''', (url,))
            conn.commit()
    
    def _clean_download_state(self, url: str):
        """Clean up download state after successful download"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM download_state WHERE url = ?', (url,))
            conn.commit()
    
    async def _save_download_result(self, result: DownloadResult):
        """Save download result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO download_history 
                (url, filename, local_path, size, checksum, start_time, end_time, 
                 duration, success, error, resume_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.url,
                result.filename,
                result.local_path,
                result.size,
                result.checksum,
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                result.duration,
                result.success,
                result.error,
                result.resume_count,
                json.dumps(asdict(result), default=str)
            ))
            conn.commit()
    
    def _update_download_stats(self, result: DownloadResult):
        """Update download statistics"""
        self.download_stats['total_downloads'] += 1
        
        if result.success:
            self.download_stats['successful_downloads'] += 1
            self.download_stats['bytes_downloaded'] += result.size
            self.download_stats['total_time'] += result.duration
            
            if self.download_stats['total_time'] > 0:
                self.download_stats['average_speed'] = (
                    self.download_stats['bytes_downloaded'] / self.download_stats['total_time']
                )
        else:
            self.download_stats['failed_downloads'] += 1
    
    async def _notify_progress(self, progress: DownloadProgress):
        """Notify progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress)
                else:
                    callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def add_progress_callback(self, callback):
        """Add a progress callback function"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback):
        """Remove a progress callback function"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get download statistics"""
        return self.download_stats.copy()
    
    def get_download_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get download history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM download_history 
                ORDER BY start_time DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def cleanup_old_files(self, days_old: int = 30):
        """Clean up old downloaded files"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        cleaned_size = 0
        
        # Find old files in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT local_path, size FROM download_history 
                WHERE start_time < ? AND success = 1
            ''', (cutoff_date.isoformat(),))
            
            for local_path, size in cursor.fetchall():
                file_path = Path(local_path)
                if file_path.exists():
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += size or 0
                        logger.debug(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error cleaning up {file_path}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old files ({cleaned_size:,} bytes)")
        return cleaned_count, cleaned_size

# Progress display callback for testing
def display_progress(progress: DownloadProgress):
    """Display download progress"""
    speed_mb = progress.speed / (1024 * 1024)
    eta_min = progress.eta / 60
    
    print(f"\r{progress.filename}: {progress.percentage:.1f}% "
          f"({progress.downloaded:,}/{progress.total_size:,} bytes) "
          f"Speed: {speed_mb:.1f} MB/s ETA: {eta_min:.1f}m", end='')

# Standalone execution for testing
async def main():
    """Test the downloader"""
    config = {
        'download_directory': 'test_downloads',
        'temp_directory': 'test_temp',
        'max_concurrent_downloads': 2,
        'chunk_size': 1024 * 1024,  # 1MB
        'verify_checksums': True
    }
    
    downloader = FloridaDataDownloader(config)
    downloader.add_progress_callback(display_progress)
    
    # Test URLs (replace with actual Florida data URLs)
    test_urls = [
        "https://example.com/test_file1.csv",
        "https://example.com/test_file2.zip"
    ]
    
    print("Starting downloads...")
    results = await downloader.download_multiple(test_urls)
    
    print(f"\nDownload results:")
    for result in results:
        status = "SUCCESS" if result.success else "FAILED"
        print(f"{result.filename}: {status}")
        if result.error:
            print(f"  Error: {result.error}")
        else:
            print(f"  Size: {result.size:,} bytes")
            print(f"  Duration: {result.duration:.1f}s")
            print(f"  Location: {result.local_path}")
    
    # Display statistics
    stats = downloader.get_download_stats()
    print(f"\nStatistics:")
    print(f"  Total downloads: {stats['total_downloads']}")
    print(f"  Successful: {stats['successful_downloads']}")
    print(f"  Failed: {stats['failed_downloads']}")
    print(f"  Bytes downloaded: {stats['bytes_downloaded']:,}")
    print(f"  Average speed: {stats['average_speed'] / (1024*1024):.1f} MB/s")

if __name__ == "__main__":
    asyncio.run(main())