"""
SFTP Client for Sunbiz Data Downloads
Connects to sftp.floridados.gov with confirmed credentials
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import paramiko
from paramiko import SSHClient, AutoAddPolicy
import aiofiles

from .config import settings

logger = logging.getLogger(__name__)


class SunbizSFTPClient:
    """SFTP client for downloading Sunbiz corporate data"""
    
    # Confirmed working credentials
    SFTP_HOST = "sftp.floridados.gov"
    SFTP_USERNAME = "Public"
    SFTP_PASSWORD = "PubAccess1845!"
    SFTP_PORT = 22
    
    # Directory structure
    DAILY_DIR = "/public/daily"
    QUARTERLY_DIR = "/public/quarterly"
    
    def __init__(self):
        self.client = None
        self.sftp = None
        
    async def connect(self):
        """Establish SFTP connection"""
        try:
            self.client = SSHClient()
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            
            logger.info(f"Connecting to {self.SFTP_HOST}...")
            
            # Connect with confirmed credentials
            await asyncio.to_thread(
                self.client.connect,
                hostname=self.SFTP_HOST,
                port=self.SFTP_PORT,
                username=self.SFTP_USERNAME,
                password=self.SFTP_PASSWORD,
                timeout=30
            )
            
            self.sftp = self.client.open_sftp()
            logger.info("SFTP connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to SFTP: {e}")
            raise
    
    async def disconnect(self):
        """Close SFTP connection"""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        logger.info("SFTP connection closed")
    
    async def list_files(self, directory: str) -> List[str]:
        """List files in a directory"""
        if not self.sftp:
            await self.connect()
        
        try:
            files = await asyncio.to_thread(self.sftp.listdir, directory)
            logger.info(f"Found {len(files)} files in {directory}")
            return files
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            raise
    
    async def download_file(self, remote_path: str, local_path: Path) -> Path:
        """Download a single file"""
        if not self.sftp:
            await self.connect()
        
        # Create local directory if needed
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Downloading {remote_path} to {local_path}")
            
            # Get file stats for progress tracking
            file_stat = await asyncio.to_thread(self.sftp.stat, remote_path)
            file_size = file_stat.st_size
            
            # Download with progress callback
            downloaded = 0
            
            def progress_callback(transferred, total):
                nonlocal downloaded
                downloaded = transferred
                percent = (transferred / total) * 100
                if percent % 10 == 0:  # Log every 10%
                    logger.info(f"Progress: {percent:.0f}% ({transferred:,}/{total:,} bytes)")
            
            await asyncio.to_thread(
                self.sftp.get,
                remote_path,
                str(local_path),
                callback=progress_callback
            )
            
            logger.info(f"Successfully downloaded {local_path.name} ({file_size:,} bytes)")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download {remote_path}: {e}")
            raise
    
    async def download_daily_files(self, local_base_path: Path, 
                                  date: Optional[datetime] = None) -> List[Path]:
        """Download daily update files"""
        if not date:
            date = datetime.now() - timedelta(days=1)  # Yesterday's files
        
        date_str = date.strftime("%Y%m%d")
        local_dir = local_base_path / "daily" / date_str
        local_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        
        try:
            await self.connect()
            
            # List daily directory files
            files = await self.list_files(self.DAILY_DIR)
            
            # Filter files for the specified date
            target_files = [f for f in files if date_str in f]
            
            logger.info(f"Found {len(target_files)} files for date {date_str}")
            
            # Download each file
            for filename in target_files:
                remote_path = f"{self.DAILY_DIR}/{filename}"
                local_path = local_dir / filename
                
                # Skip if already downloaded
                if local_path.exists():
                    logger.info(f"Skipping {filename} (already exists)")
                    downloaded_files.append(local_path)
                    continue
                
                downloaded_path = await self.download_file(remote_path, local_path)
                downloaded_files.append(downloaded_path)
            
            return downloaded_files
            
        finally:
            await self.disconnect()
    
    async def download_quarterly_files(self, local_base_path: Path,
                                      quarter: Optional[str] = None) -> List[Path]:
        """Download quarterly full dataset"""
        if not quarter:
            # Determine current quarter
            month = datetime.now().month
            year = datetime.now().year
            if month <= 3:
                quarter = f"{year}Q1"
            elif month <= 6:
                quarter = f"{year}Q2"
            elif month <= 9:
                quarter = f"{year}Q3"
            else:
                quarter = f"{year}Q4"
        
        local_dir = local_base_path / "quarterly" / quarter
        local_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        
        try:
            await self.connect()
            
            # List quarterly directory
            files = await self.list_files(self.QUARTERLY_DIR)
            
            # Common quarterly file patterns
            patterns = ["cordata", "corpoff", "corphis", "fedtax", "ficname"]
            target_files = [f for f in files 
                          if any(p in f.lower() for p in patterns)]
            
            logger.info(f"Found {len(target_files)} quarterly files")
            
            for filename in target_files:
                remote_path = f"{self.QUARTERLY_DIR}/{filename}"
                local_path = local_dir / filename
                
                if local_path.exists():
                    logger.info(f"Skipping {filename} (already exists)")
                    downloaded_files.append(local_path)
                    continue
                
                downloaded_path = await self.download_file(remote_path, local_path)
                downloaded_files.append(downloaded_path)
            
            return downloaded_files
            
        finally:
            await self.disconnect()
    
    async def test_connection(self) -> bool:
        """Test SFTP connection and list available directories"""
        try:
            await self.connect()
            
            # Try to list root directory
            root_files = await self.list_files("/public")
            logger.info(f"Root directory contains: {root_files}")
            
            # Check if expected directories exist
            daily_exists = "daily" in root_files
            quarterly_exists = "quarterly" in root_files
            
            logger.info(f"Daily directory exists: {daily_exists}")
            logger.info(f"Quarterly directory exists: {quarterly_exists}")
            
            # List sample files from daily
            if daily_exists:
                daily_files = await self.list_files(self.DAILY_DIR)
                logger.info(f"Sample daily files: {daily_files[:5]}")
            
            await self.disconnect()
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False