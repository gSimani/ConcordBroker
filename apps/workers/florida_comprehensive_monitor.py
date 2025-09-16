#!/usr/bin/env python3
"""
Comprehensive Florida Data Ecosystem Monitor
Advanced monitoring and download system for all Florida property data sources
"""

import asyncio
import aiohttp
import asyncssh
import os
import sys
import logging
import json
import hashlib
import re
import zipfile
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
from urllib.parse import urljoin, quote, urlparse
from bs4 import BeautifulSoup
import schedule
import time
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_config import SupabaseConfig, SupabaseUpdateMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_comprehensive_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()

class DataSourceType(Enum):
    """Types of data sources"""
    HTTP_DIRECTORY = "http_directory"
    SFTP = "sftp"
    REST_API = "rest_api"
    WEB_SCRAPE = "web_scrape"
    DIRECT_DOWNLOAD = "direct_download"

class UpdateFrequency(Enum):
    """Update frequency types"""
    DAILY = "daily"
    WEEKLY = "weekly" 
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"

@dataclass
class FilePattern:
    """File naming pattern configuration"""
    pattern: str  # Regex pattern
    description: str
    county_position: int  # Position of county code in pattern
    year_position: int    # Position of year in pattern
    period_position: Optional[int] = None
    extension: str = "txt"
    compressed: bool = False

@dataclass
class DataSourceConfig:
    """Enhanced data source configuration"""
    name: str
    source_type: DataSourceType
    base_url: str
    update_frequency: UpdateFrequency
    file_patterns: List[FilePattern]
    county_codes: List[str]
    years: List[str]
    priority: int
    enabled: bool
    retry_attempts: int = 3
    timeout_seconds: int = 300
    rate_limit_delay: float = 1.0
    batch_size: int = 1000
    auth_config: Optional[Dict[str, Any]] = None
    custom_headers: Optional[Dict[str, str]] = None
    processing_rules: Optional[Dict[str, Any]] = None

class FloridaComprehensiveMonitor:
    """Comprehensive monitoring system for Florida data sources"""
    
    def __init__(self, base_data_dir: str = "./data/florida"):
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = None
        self.monitor = None
        self.sources = self._initialize_data_sources()
        self.discovered_files = {}
        self.download_stats = {
            "total_files": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "total_size_mb": 0,
            "last_update": None
        }
    
    def _initialize_data_sources(self) -> Dict[str, DataSourceConfig]:
        """Initialize all Florida data sources with enhanced configurations"""
        
        # Define common file patterns
        florida_revenue_patterns = [
            FilePattern(
                pattern=r"(NAL|NAP|NAV|SDF|TPP|RER|CDF|JVS)(\d{2})(P|F)(\d{6})\.txt",
                description="Florida Revenue standard format: TYPE + County + Period + YYYYMM",
                county_position=2,
                year_position=4,
                period_position=3
            ),
            FilePattern(
                pattern=r"broward_(nal|nap|nav|sdf|tpp)_(\d{4})\.zip",
                description="Broward county specific ZIP format",
                county_position=0,
                year_position=2,
                extension="zip",
                compressed=True
            )
        ]
        
        sunbiz_patterns = [
            FilePattern(
                pattern=r"(corp|llc|lp|fictitious|officers)_(\d{8})\.txt",
                description="Sunbiz daily format: type_YYYYMMDD",
                county_position=-1,
                year_position=2
            ),
            FilePattern(
                pattern=r"(quarterly|weekly)_(\d{4})_(\d{2})\.zip",
                description="Sunbiz periodic format: period_YYYY_MM",
                county_position=-1,
                year_position=2,
                extension="zip",
                compressed=True
            )
        ]
        
        return {
            "florida_revenue_portal": DataSourceConfig(
                name="Florida Revenue Data Portal",
                source_type=DataSourceType.HTTP_DIRECTORY,
                base_url="https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/",
                update_frequency=UpdateFrequency.MONTHLY,
                file_patterns=florida_revenue_patterns,
                county_codes=["06", "13", "50"],  # Broward, Miami-Dade, Palm Beach
                years=["2024", "2025", "2026"],
                priority=10,
                enabled=True,
                timeout_seconds=600,
                custom_headers={"User-Agent": "FloridaDataBot/1.0"}
            ),
            
            "sunbiz_sftp": DataSourceConfig(
                name="Florida Sunbiz SFTP",
                source_type=DataSourceType.SFTP,
                base_url="sftp://sftp.floridados.gov",
                update_frequency=UpdateFrequency.WEEKLY,
                file_patterns=sunbiz_patterns,
                county_codes=[],  # Statewide
                years=["2024", "2025"],
                priority=9,
                enabled=True,
                auth_config={
                    "username": "Public",
                    "password": "PubAccess1845!",
                    "port": 22
                },
                rate_limit_delay=2.0
            ),
            
            "arcgis_cadastral": DataSourceConfig(
                name="Florida Statewide Cadastral",
                source_type=DataSourceType.REST_API,
                base_url="https://services9.arcgis.com/Gh9awoU677aKree0/arcgis/rest/services/Florida_Statewide_Cadastral/FeatureServer",
                update_frequency=UpdateFrequency.QUARTERLY,
                file_patterns=[],
                county_codes=["06", "13", "50"],
                years=["2024", "2025"],
                priority=7,
                enabled=True,
                batch_size=1000,
                rate_limit_delay=0.5
            ),
            
            "broward_daily_index": DataSourceConfig(
                name="Broward County Daily Index",
                source_type=DataSourceType.WEB_SCRAPE,
                base_url="https://www.broward.org/RecordsTaxesTreasury/Records/Pages/DailyIndexExtractFiles.aspx",
                update_frequency=UpdateFrequency.DAILY,
                file_patterns=[
                    FilePattern(
                        pattern=r"(\d{8})\.zip",
                        description="Daily index format: YYYYMMDD.zip",
                        county_position=-1,
                        year_position=1,
                        extension="zip",
                        compressed=True
                    )
                ],
                county_codes=["06"],
                years=["2024", "2025"],
                priority=8,
                enabled=True,
                rate_limit_delay=3.0
            ),
            
            "florida_geospatial": DataSourceConfig(
                name="Florida Geospatial Open Data",
                source_type=DataSourceType.REST_API,
                base_url="https://geodata.floridagio.gov/api/v1/",
                update_frequency=UpdateFrequency.QUARTERLY,
                file_patterns=[],
                county_codes=["06", "13", "50"],
                years=["2024", "2025"],
                priority=6,
                enabled=True,
                rate_limit_delay=1.0
            )
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=600),
            connector=aiohttp.TCPConnector(limit=10, limit_per_host=3)
        )
        
        # Initialize Supabase monitoring
        pool = await SupabaseConfig.get_db_pool()
        self.monitor = SupabaseUpdateMonitor(pool)
        await self.monitor.initialize_tracking_tables()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def discover_directory_structure(self, source_config: DataSourceConfig) -> Dict[str, List[str]]:
        """Dynamically discover directory structure and available files"""
        logger.info(f"Discovering directory structure for {source_config.name}")
        
        discovered = {"directories": [], "files": [], "years": [], "periods": []}
        
        try:
            if source_config.source_type == DataSourceType.HTTP_DIRECTORY:
                discovered = await self._discover_http_structure(source_config)
            elif source_config.source_type == DataSourceType.SFTP:
                discovered = await self._discover_sftp_structure(source_config)
            elif source_config.source_type == DataSourceType.REST_API:
                discovered = await self._discover_api_structure(source_config)
            
        except Exception as e:
            logger.error(f"Directory discovery failed for {source_config.name}: {e}")
        
        return discovered
    
    async def _discover_http_structure(self, config: DataSourceConfig) -> Dict[str, List[str]]:
        """Discover HTTP directory structure"""
        discovered = {"directories": [], "files": [], "years": [], "periods": []}
        
        # Try different year folder patterns
        year_patterns = ["2024", "2025", "2024F", "2025P", "TAX_ROLL_2024", "TAX_ROLL_2025"]
        
        for year_pattern in year_patterns:
            try:
                url = urljoin(config.base_url, f"{year_pattern}/")
                
                async with self.session.get(url, headers=config.custom_headers or {}) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract links
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link['href']
                            
                            # Check if it's a file matching our patterns
                            for pattern in config.file_patterns:
                                if re.match(pattern.pattern, href):
                                    discovered["files"].append(href)
                                    
                                    # Extract year/period info
                                    match = re.match(pattern.pattern, href)
                                    if match:
                                        if pattern.year_position > 0:
                                            year = match.group(pattern.year_position)
                                            if year not in discovered["years"]:
                                                discovered["years"].append(year)
                        
                        discovered["directories"].append(year_pattern)
                        
            except Exception as e:
                logger.debug(f"Could not access {url}: {e}")
                continue
        
        return discovered
    
    async def _discover_sftp_structure(self, config: DataSourceConfig) -> Dict[str, List[str]]:
        """Discover SFTP directory structure"""
        discovered = {"directories": [], "files": [], "years": [], "periods": []}
        
        try:
            conn_options = asyncssh.SSHClientConnectionOptions(
                known_hosts=None,
                username=config.auth_config["username"],
                password=config.auth_config["password"]
            )
            
            parsed_url = urlparse(config.base_url)
            
            async with asyncssh.connect(
                parsed_url.hostname,
                port=config.auth_config.get("port", 22),
                options=conn_options
            ) as conn:
                async with conn.start_sftp_client() as sftp:
                    # List root directory
                    files = await sftp.listdir('.')
                    
                    for file in files:
                        discovered["files"].append(file)
                        
                        # Check against patterns
                        for pattern in config.file_patterns:
                            match = re.match(pattern.pattern, file)
                            if match and pattern.year_position > 0:
                                year = match.group(pattern.year_position)
                                if year not in discovered["years"]:
                                    discovered["years"].append(year)
                    
        except Exception as e:
            logger.error(f"SFTP discovery failed: {e}")
        
        return discovered
    
    async def _discover_api_structure(self, config: DataSourceConfig) -> Dict[str, List[str]]:
        """Discover REST API structure"""
        discovered = {"directories": [], "files": [], "years": [], "periods": []}
        
        try:
            # For ArcGIS, list available layers
            if "arcgis" in config.base_url.lower():
                url = f"{config.base_url}?f=json"
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract layer information
                        for layer in data.get("layers", []):
                            discovered["directories"].append(f"layer_{layer['id']}")
                            discovered["files"].append(f"{layer['name']}.json")
                            
        except Exception as e:
            logger.error(f"API discovery failed: {e}")
        
        return discovered
    
    async def detect_file_updates(self, source_config: DataSourceConfig, discovered_files: List[str]) -> List[Dict[str, Any]]:
        """Detect which files need to be updated based on changes"""
        updates_needed = []
        
        for file_path in discovered_files:
            try:
                # Check if we've seen this file before
                needs_update = await self.monitor.check_for_update(
                    agent_name=source_config.name,
                    source_url=f"{source_config.base_url}/{file_path}"
                )
                
                if needs_update:
                    # Get file metadata
                    metadata = await self._get_file_metadata(source_config, file_path)
                    
                    updates_needed.append({
                        "file_path": file_path,
                        "source": source_config.name,
                        "url": f"{source_config.base_url}/{file_path}",
                        "metadata": metadata,
                        "priority": source_config.priority
                    })
                    
            except Exception as e:
                logger.error(f"Update detection failed for {file_path}: {e}")
        
        # Sort by priority
        updates_needed.sort(key=lambda x: x["priority"], reverse=True)
        
        return updates_needed
    
    async def _get_file_metadata(self, config: DataSourceConfig, file_path: str) -> Dict[str, Any]:
        """Get file metadata (size, modified time, etc.)"""
        metadata = {"size": 0, "last_modified": None, "hash": None}
        
        try:
            if config.source_type == DataSourceType.HTTP_DIRECTORY:
                url = urljoin(config.base_url, file_path)
                
                async with self.session.head(url, headers=config.custom_headers or {}) as response:
                    if response.status == 200:
                        metadata["size"] = int(response.headers.get("content-length", 0))
                        metadata["last_modified"] = response.headers.get("last-modified")
                        
        except Exception as e:
            logger.debug(f"Could not get metadata for {file_path}: {e}")
        
        return metadata
    
    async def download_file(self, source_config: DataSourceConfig, file_info: Dict[str, Any]) -> Optional[str]:
        """Download a single file with progress tracking"""
        file_path = file_info["file_path"]
        url = file_info["url"]
        
        logger.info(f"Downloading {file_path} from {source_config.name}")
        
        try:
            # Create local path
            local_dir = self.base_data_dir / source_config.name.lower().replace(" ", "_")
            local_dir.mkdir(parents=True, exist_ok=True)
            local_file = local_dir / file_path
            
            if source_config.source_type == DataSourceType.HTTP_DIRECTORY:
                downloaded_path = await self._download_http_file(url, local_file, source_config)
            elif source_config.source_type == DataSourceType.SFTP:
                downloaded_path = await self._download_sftp_file(file_path, local_file, source_config)
            else:
                return None
            
            if downloaded_path:
                # Calculate file hash
                file_hash = self._calculate_file_hash(downloaded_path)
                
                # Record successful download
                await self.monitor.record_update(
                    agent_name=source_config.name,
                    source_url=url,
                    update_data={
                        "status": "completed",
                        "file_hash": file_hash,
                        "file_size": downloaded_path.stat().st_size,
                        "last_modified": datetime.now(),
                        "metadata": file_info.get("metadata", {})
                    }
                )
                
                self.download_stats["successful_downloads"] += 1
                self.download_stats["total_size_mb"] += downloaded_path.stat().st_size / (1024 * 1024)
                
                return str(downloaded_path)
            
        except Exception as e:
            logger.error(f"Download failed for {file_path}: {e}")
            
            # Record failed download
            await self.monitor.record_update(
                agent_name=source_config.name,
                source_url=url,
                update_data={
                    "status": "failed",
                    "error_message": str(e)
                }
            )
            
            self.download_stats["failed_downloads"] += 1
        
        return None
    
    async def _download_http_file(self, url: str, local_path: Path, config: DataSourceConfig) -> Optional[Path]:
        """Download file via HTTP"""
        try:
            async with self.session.get(
                url, 
                headers=config.custom_headers or {},
                timeout=aiohttp.ClientTimeout(total=config.timeout_seconds)
            ) as response:
                if response.status == 200:
                    with open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    # Handle compressed files
                    if local_path.suffix.lower() == '.zip':
                        extracted_path = await self._extract_compressed_file(local_path)
                        return extracted_path or local_path
                    
                    return local_path
                else:
                    raise Exception(f"HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"HTTP download failed: {e}")
            return None
    
    async def _download_sftp_file(self, file_path: str, local_path: Path, config: DataSourceConfig) -> Optional[Path]:
        """Download file via SFTP"""
        try:
            conn_options = asyncssh.SSHClientConnectionOptions(
                known_hosts=None,
                username=config.auth_config["username"],
                password=config.auth_config["password"]
            )
            
            parsed_url = urlparse(config.base_url)
            
            async with asyncssh.connect(
                parsed_url.hostname,
                port=config.auth_config.get("port", 22),
                options=conn_options
            ) as conn:
                async with conn.start_sftp_client() as sftp:
                    await sftp.get(file_path, local_path)
                    
                    # Handle compressed files
                    if local_path.suffix.lower() == '.zip':
                        extracted_path = await self._extract_compressed_file(local_path)
                        return extracted_path or local_path
                    
                    return local_path
                    
        except Exception as e:
            logger.error(f"SFTP download failed: {e}")
            return None
    
    async def _extract_compressed_file(self, compressed_path: Path) -> Optional[Path]:
        """Extract compressed files"""
        try:
            extract_dir = compressed_path.parent / compressed_path.stem
            extract_dir.mkdir(exist_ok=True)
            
            if compressed_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(compressed_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                    
                # Return path to first extracted file
                extracted_files = list(extract_dir.glob('*'))
                if extracted_files:
                    return extracted_files[0]
                    
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
        
        return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def process_downloaded_file(self, source_config: DataSourceConfig, file_path: str) -> int:
        """Process downloaded file and load into Supabase"""
        logger.info(f"Processing {file_path}")
        
        records_processed = 0
        
        try:
            # Determine file type and processing method
            if any(pattern.pattern for pattern in source_config.file_patterns if re.match(pattern.pattern, Path(file_path).name)):
                # Process based on source type
                if "tpp" in file_path.lower():
                    records_processed = await self._process_tpp_file(file_path)
                elif "nav" in file_path.lower():
                    records_processed = await self._process_nav_file(file_path)
                elif "sdf" in file_path.lower():
                    records_processed = await self._process_sdf_file(file_path)
                elif "sunbiz" in source_config.name.lower():
                    records_processed = await self._process_sunbiz_file(file_path)
                    
        except Exception as e:
            logger.error(f"Processing failed for {file_path}: {e}")
        
        return records_processed
    
    async def _process_tpp_file(self, file_path: str) -> int:
        """Process TPP (Tangible Personal Property) file"""
        # Implementation would parse TPP format and insert to fl_tpp_accounts
        logger.info(f"Processing TPP file: {file_path}")
        return 0
    
    async def _process_nav_file(self, file_path: str) -> int:
        """Process NAV (Non Ad Valorem) file"""
        # Implementation would parse NAV format and insert to appropriate tables
        logger.info(f"Processing NAV file: {file_path}")
        return 0
    
    async def _process_sdf_file(self, file_path: str) -> int:
        """Process SDF (Sales Data File) file"""
        # Implementation would parse SDF format and insert to fl_sdf_sales
        logger.info(f"Processing SDF file: {file_path}")
        return 0
    
    async def _process_sunbiz_file(self, file_path: str) -> int:
        """Process Sunbiz business registry file"""
        # Implementation would parse Sunbiz format and insert to sunbiz tables
        logger.info(f"Processing Sunbiz file: {file_path}")
        return 0
    
    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run one complete monitoring cycle for all sources"""
        logger.info("Starting comprehensive monitoring cycle")
        
        results = {
            "timestamp": datetime.now(),
            "sources_processed": 0,
            "files_discovered": 0,
            "files_downloaded": 0,
            "files_processed": 0,
            "total_records": 0,
            "errors": []
        }
        
        for source_name, source_config in self.sources.items():
            if not source_config.enabled:
                continue
                
            try:
                logger.info(f"Processing source: {source_name}")
                
                # Discover available files
                discovered = await self.discover_directory_structure(source_config)
                results["files_discovered"] += len(discovered.get("files", []))
                
                # Detect files that need updates
                updates_needed = await self.detect_file_updates(source_config, discovered.get("files", []))
                
                # Download updated files
                for update_info in updates_needed:
                    downloaded_path = await self.download_file(source_config, update_info)
                    
                    if downloaded_path:
                        results["files_downloaded"] += 1
                        
                        # Process the downloaded file
                        records = await self.process_downloaded_file(source_config, downloaded_path)
                        if records > 0:
                            results["files_processed"] += 1
                            results["total_records"] += records
                    
                    # Rate limiting
                    await asyncio.sleep(source_config.rate_limit_delay)
                
                results["sources_processed"] += 1
                
            except Exception as e:
                error_msg = f"Source {source_name} failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        self.download_stats["last_update"] = datetime.now()
        
        return results
    
    def generate_status_report(self) -> str:
        """Generate comprehensive status report"""
        report = []
        report.append("=" * 80)
        report.append("FLORIDA DATA COMPREHENSIVE MONITORING REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now()}")
        report.append("")
        
        # Overall statistics
        report.append("OVERALL STATISTICS:")
        report.append("-" * 40)
        report.append(f"Total Files Downloaded: {self.download_stats['successful_downloads']}")
        report.append(f"Failed Downloads: {self.download_stats['failed_downloads']}")
        report.append(f"Total Data Size: {self.download_stats['total_size_mb']:.2f} MB")
        report.append(f"Last Update: {self.download_stats['last_update']}")
        report.append("")
        
        # Source status
        report.append("DATA SOURCE STATUS:")
        report.append("-" * 40)
        for name, config in self.sources.items():
            status = "ENABLED" if config.enabled else "DISABLED"
            priority = config.priority
            frequency = config.update_frequency.value
            report.append(f"{name:<30} | {status:<8} | Priority: {priority} | {frequency}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

async def main():
    """Main execution function"""
    console.print("[bold green]Florida Comprehensive Data Monitor Starting...[/bold green]")
    
    async with FloridaComprehensiveMonitor() as monitor:
        # Run monitoring cycle
        results = await monitor.run_monitoring_cycle()
        
        # Display results
        console.print(f"\n[bold cyan]Monitoring Cycle Complete![/bold cyan]")
        console.print(f"Sources Processed: {results['sources_processed']}")
        console.print(f"Files Discovered: {results['files_discovered']}")
        console.print(f"Files Downloaded: {results['files_downloaded']}")
        console.print(f"Files Processed: {results['files_processed']}")
        console.print(f"Total Records: {results['total_records']}")
        
        if results['errors']:
            console.print(f"\n[bold red]Errors Encountered:[/bold red]")
            for error in results['errors']:
                console.print(f"  - {error}")
        
        # Generate and save status report
        report = monitor.generate_status_report()
        report_path = Path("florida_monitoring_report.txt")
        report_path.write_text(report)
        console.print(f"\n[green]Status report saved to: {report_path}[/green]")

if __name__ == "__main__":
    asyncio.run(main())