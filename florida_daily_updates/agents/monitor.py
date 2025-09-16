#!/usr/bin/env python3
"""
Florida Data Monitor Agent
Monitors the Florida Department of Revenue portal for new data files daily.
Checks NAL, NAP, and SDF files for all configured counties.
"""

import asyncio
import logging
import hashlib
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import re
import sqlite3
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Information about a data file"""
    url: str
    filename: str
    county: str
    file_type: str  # NAL, NAP, SDF
    year: str
    size: Optional[int] = None
    last_modified: Optional[datetime] = None
    hash: Optional[str] = None
    status: str = "discovered"

@dataclass
class MonitorResult:
    """Result of monitoring operation"""
    timestamp: datetime
    new_files: List[FileInfo]
    updated_files: List[FileInfo]
    errors: List[str]
    total_files_checked: int
    success: bool

class FloridaDataMonitor:
    """Monitors Florida Department of Revenue portal for data updates"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = "https://floridarevenue.com/property/dataportal"
        self.session = None
        self.db_path = Path(config.get('state_db_path', 'florida_monitor_state.db'))
        self.counties = config.get('counties', ['broward'])
        self.file_types = config.get('file_types', ['NAL', 'NAP', 'SDF'])
        self.current_year = config.get('current_year', '2025P')
        self.user_agent = config.get('user_agent', 'Florida Property Data Monitor 1.0')
        
        # Initialize database
        self._init_database()
        
        # Statistics
        self.monitor_stats = {
            'total_checks': 0,
            'files_discovered': 0,
            'files_updated': 0,
            'errors': 0,
            'last_successful_check': None
        }
    
    def _init_database(self):
        """Initialize SQLite database for state tracking"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    county TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    year TEXT NOT NULL,
                    size INTEGER,
                    last_modified TEXT,
                    file_hash TEXT,
                    first_discovered TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_checked TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'discovered',
                    download_attempts INTEGER DEFAULT 0,
                    last_download_success TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS monitor_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    files_checked INTEGER DEFAULT 0,
                    new_files INTEGER DEFAULT 0,
                    updated_files INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    success BOOLEAN DEFAULT 1,
                    details TEXT
                )
            ''')
            
            conn.commit()
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.user_agent},
            timeout=aiohttp.ClientTimeout(total=300)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_for_updates(self) -> MonitorResult:
        """Check Florida portal for data updates"""
        start_time = datetime.now()
        new_files = []
        updated_files = []
        errors = []
        total_files_checked = 0
        
        try:
            logger.info("Starting Florida data portal check...")
            
            # Get the main data portal page
            portal_urls = await self._discover_data_urls()
            
            for county in self.counties:
                try:
                    county_files = await self._check_county_files(county, portal_urls)
                    total_files_checked += len(county_files)
                    
                    for file_info in county_files:
                        if await self._is_new_file(file_info):
                            new_files.append(file_info)
                            await self._save_file_info(file_info)
                        elif await self._is_updated_file(file_info):
                            updated_files.append(file_info)
                            await self._update_file_info(file_info)
                    
                except Exception as e:
                    error_msg = f"Error checking {county} county: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Update statistics
            self.monitor_stats['total_checks'] += 1
            self.monitor_stats['files_discovered'] += len(new_files)
            self.monitor_stats['files_updated'] += len(updated_files)
            self.monitor_stats['errors'] += len(errors)
            
            success = len(errors) == 0
            if success:
                self.monitor_stats['last_successful_check'] = start_time
            
            result = MonitorResult(
                timestamp=start_time,
                new_files=new_files,
                updated_files=updated_files,
                errors=errors,
                total_files_checked=total_files_checked,
                success=success
            )
            
            # Save to database
            await self._save_monitor_result(result)
            
            logger.info(f"Monitor check completed: {len(new_files)} new, {len(updated_files)} updated, {len(errors)} errors")
            return result
            
        except Exception as e:
            error_msg = f"Critical error in monitor check: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            return MonitorResult(
                timestamp=start_time,
                new_files=[],
                updated_files=[],
                errors=errors,
                total_files_checked=0,
                success=False
            )
    
    async def _discover_data_urls(self) -> Dict[str, str]:
        """Discover URLs for different data types"""
        urls = {}
        
        try:
            async with self.session.get(self.base_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to access portal: HTTP {response.status}")
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for Tax Roll Data Files links
                for link in soup.find_all('a', href=True):
                    text = link.get_text().strip().lower()
                    href = link['href']
                    
                    if 'tax roll data files' in text:
                        urls['tax_roll'] = urljoin(self.base_url, href)
                    elif 'nal' in text and 'file' in text:
                        urls['nal'] = urljoin(self.base_url, href)
                    elif 'nap' in text and 'file' in text:
                        urls['nap'] = urljoin(self.base_url, href)
                    elif 'sdf' in text and 'file' in text:
                        urls['sdf'] = urljoin(self.base_url, href)
                
                # If we found the main tax roll page, get specific URLs from there
                if 'tax_roll' in urls:
                    sub_urls = await self._discover_tax_roll_urls(urls['tax_roll'])
                    urls.update(sub_urls)
                
                logger.info(f"Discovered URLs: {list(urls.keys())}")
                return urls
                
        except Exception as e:
            logger.error(f"Error discovering portal URLs: {e}")
            # Fallback to known URL patterns
            return {
                'nal': f"{self.base_url}/nal-files",
                'nap': f"{self.base_url}/nap-files", 
                'sdf': f"{self.base_url}/sdf-files"
            }
    
    async def _discover_tax_roll_urls(self, tax_roll_url: str) -> Dict[str, str]:
        """Get specific file type URLs from tax roll page"""
        urls = {}
        
        try:
            async with self.session.get(tax_roll_url) as response:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    text = link.get_text().strip().lower()
                    href = link['href']
                    
                    if 'nal' in text:
                        urls['nal'] = urljoin(tax_roll_url, href)
                    elif 'nap' in text:
                        urls['nap'] = urljoin(tax_roll_url, href)
                    elif 'sdf' in text:
                        urls['sdf'] = urljoin(tax_roll_url, href)
                
                return urls
                
        except Exception as e:
            logger.error(f"Error discovering tax roll URLs: {e}")
            return {}
    
    async def _check_county_files(self, county: str, portal_urls: Dict[str, str]) -> List[FileInfo]:
        """Check files for a specific county"""
        files = []
        
        for file_type in self.file_types:
            try:
                type_files = await self._get_files_for_type(county, file_type, portal_urls)
                files.extend(type_files)
            except Exception as e:
                logger.error(f"Error checking {file_type} files for {county}: {e}")
        
        return files
    
    async def _get_files_for_type(self, county: str, file_type: str, portal_urls: Dict[str, str]) -> List[FileInfo]:
        """Get files for a specific type (NAL, NAP, SDF)"""
        files = []
        type_key = file_type.lower()
        
        if type_key not in portal_urls:
            logger.warning(f"No URL found for file type {file_type}")
            return files
        
        try:
            url = portal_urls[type_key]
            async with self.session.get(url) as response:
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for year sections (e.g., 2025P)
                year_section = self._find_year_section(soup, self.current_year)
                if not year_section:
                    logger.warning(f"No section found for year {self.current_year}")
                    return files
                
                # Find county files in this section
                county_files = await self._extract_county_files(
                    year_section, county, file_type, url
                )
                files.extend(county_files)
                
        except Exception as e:
            logger.error(f"Error getting {file_type} files for {county}: {e}")
        
        return files
    
    def _find_year_section(self, soup: BeautifulSoup, year: str) -> Optional[Any]:
        """Find the section for the current year"""
        # Look for headings containing the year
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if year in heading.get_text():
                return heading.parent or heading
        
        # Look for divs with year in class or id
        for div in soup.find_all('div'):
            if year.lower() in str(div.get('class', '')).lower() or year.lower() in str(div.get('id', '')).lower():
                return div
        
        # If no specific section found, return the whole soup
        return soup
    
    async def _extract_county_files(self, section: Any, county: str, file_type: str, base_url: str) -> List[FileInfo]:
        """Extract county files from a page section"""
        files = []
        county_patterns = [
            county.lower(),
            county.capitalize(),
            county.upper(),
            f"{county}_{file_type}",
            f"{county.lower()}_{file_type.lower()}"
        ]
        
        # Look for download links
        for link in section.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            
            # Check if this link is for our county
            is_county_file = any(pattern in text.lower() or pattern in href.lower() 
                               for pattern in county_patterns)
            
            if is_county_file and any(ext in href.lower() for ext in ['.csv', '.txt', '.zip']):
                file_url = urljoin(base_url, href)
                filename = Path(urlparse(href).path).name
                
                # Get file metadata
                size, last_modified = await self._get_file_metadata(file_url)
                
                file_info = FileInfo(
                    url=file_url,
                    filename=filename,
                    county=county,
                    file_type=file_type,
                    year=self.current_year,
                    size=size,
                    last_modified=last_modified
                )
                
                files.append(file_info)
                logger.debug(f"Found file: {filename} for {county} {file_type}")
        
        return files
    
    async def _get_file_metadata(self, url: str) -> Tuple[Optional[int], Optional[datetime]]:
        """Get file size and last modified date without downloading"""
        try:
            async with self.session.head(url) as response:
                size = None
                last_modified = None
                
                if 'content-length' in response.headers:
                    size = int(response.headers['content-length'])
                
                if 'last-modified' in response.headers:
                    from email.utils import parsedate_to_datetime
                    last_modified = parsedate_to_datetime(response.headers['last-modified'])
                
                return size, last_modified
                
        except Exception as e:
            logger.debug(f"Could not get metadata for {url}: {e}")
            return None, None
    
    async def _is_new_file(self, file_info: FileInfo) -> bool:
        """Check if this is a new file"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM file_tracking WHERE url = ?',
                (file_info.url,)
            )
            return cursor.fetchone() is None
    
    async def _is_updated_file(self, file_info: FileInfo) -> bool:
        """Check if this file has been updated"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT size, last_modified, file_hash FROM file_tracking WHERE url = ?',
                (file_info.url,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False
            
            stored_size, stored_modified, stored_hash = result
            
            # Check size change
            if file_info.size and stored_size and file_info.size != stored_size:
                return True
            
            # Check modification date
            if file_info.last_modified and stored_modified:
                stored_date = datetime.fromisoformat(stored_modified)
                if file_info.last_modified > stored_date:
                    return True
            
            return False
    
    async def _save_file_info(self, file_info: FileInfo):
        """Save new file info to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO file_tracking 
                (url, filename, county, file_type, year, size, last_modified, file_hash, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_info.url,
                file_info.filename,
                file_info.county,
                file_info.file_type,
                file_info.year,
                file_info.size,
                file_info.last_modified.isoformat() if file_info.last_modified else None,
                file_info.hash,
                'new'
            ))
            conn.commit()
    
    async def _update_file_info(self, file_info: FileInfo):
        """Update existing file info in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE file_tracking 
                SET size = ?, last_modified = ?, file_hash = ?, status = 'updated', 
                    last_checked = CURRENT_TIMESTAMP
                WHERE url = ?
            ''', (
                file_info.size,
                file_info.last_modified.isoformat() if file_info.last_modified else None,
                file_info.hash,
                file_info.url
            ))
            conn.commit()
    
    async def _save_monitor_result(self, result: MonitorResult):
        """Save monitoring result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO monitor_history 
                (timestamp, files_checked, new_files, updated_files, errors, success, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.timestamp.isoformat(),
                result.total_files_checked,
                len(result.new_files),
                len(result.updated_files),
                len(result.errors),
                result.success,
                json.dumps(asdict(result), default=str)
            ))
            conn.commit()
    
    def get_pending_downloads(self) -> List[FileInfo]:
        """Get files that need to be downloaded"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT url, filename, county, file_type, year, size, last_modified, file_hash
                FROM file_tracking 
                WHERE status IN ('new', 'updated', 'download_failed')
                ORDER BY first_discovered ASC
            ''')
            
            files = []
            for row in cursor.fetchall():
                url, filename, county, file_type, year, size, last_modified, file_hash = row
                
                file_info = FileInfo(
                    url=url,
                    filename=filename,
                    county=county,
                    file_type=file_type,
                    year=year,
                    size=size,
                    last_modified=datetime.fromisoformat(last_modified) if last_modified else None,
                    hash=file_hash
                )
                files.append(file_info)
            
            return files
    
    def get_monitor_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total files tracked
            cursor.execute('SELECT COUNT(*) FROM file_tracking')
            total_files = cursor.fetchone()[0]
            
            # Get files by status
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM file_tracking 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Get recent monitor history
            cursor.execute('''
                SELECT * FROM monitor_history 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            recent_history = cursor.fetchall()
            
            return {
                'total_files_tracked': total_files,
                'status_counts': status_counts,
                'recent_checks': len(recent_history),
                'monitor_stats': self.monitor_stats,
                'recent_history': recent_history
            }

# Standalone execution for testing
async def main():
    """Test the monitor"""
    config = {
        'counties': ['broward'],
        'file_types': ['NAL', 'NAP', 'SDF'],
        'current_year': '2025P',
        'state_db_path': 'test_monitor_state.db'
    }
    
    async with FloridaDataMonitor(config) as monitor:
        result = await monitor.check_for_updates()
        print(f"Monitor result: {result.success}")
        print(f"New files: {len(result.new_files)}")
        print(f"Updated files: {len(result.updated_files)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.errors:
            for error in result.errors:
                print(f"Error: {error}")

if __name__ == "__main__":
    asyncio.run(main())