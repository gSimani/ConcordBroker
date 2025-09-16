"""
Florida Revenue Mapping Data Monitor
Monitors and orchestrates GIS mapping data downloads and processing
"""

import os
import sys
import json
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from mapping_downloader import FloridaMappingDownloader
from gis_parser import GISParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_mapping_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaMappingMonitor:
    """Monitors and manages Florida Revenue GIS mapping data"""
    
    def __init__(self):
        """Initialize monitor components"""
        self.downloader = FloridaMappingDownloader()
        self.parser = GISParser()
        
        self.run_count = 0
        self.last_check = None
        self.last_scan = None
        
        # Status file
        self.status_file = Path("florida_mapping_monitor_status.json")
        self.load_status()
        
        # Processing statistics
        self.processing_stats = {
            'files_downloaded': [],
            'files_processed': [],
            'total_parcels_extracted': 0,
            'last_full_scan': None,
            'errors': []
        }
    
    def load_status(self):
        """Load monitor status from file"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                status = json.load(f)
                self.run_count = status.get('run_count', 0)
                self.last_check = status.get('last_check')
                self.last_scan = status.get('last_scan')
                self.processing_stats = status.get('processing_stats', self.processing_stats)
    
    def save_status(self):
        """Save monitor status to file"""
        status = {
            'run_count': self.run_count,
            'last_check': self.last_check,
            'last_scan': self.last_scan,
            'processing_stats': self.processing_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
    
    def scan_and_download(self) -> Dict:
        """
        Scan for available mapping files and download new ones
        
        Returns:
            Scan and download results
        """
        logger.info("Scanning for available mapping data files")
        
        # Scan for available files
        available = self.downloader.scan_available_files()
        
        self.last_scan = datetime.now().isoformat()
        
        results = {
            'scan_time': self.last_scan,
            'available_files': {
                'shapefiles': len(available.get('shapefiles', [])),
                'geodatabases': len(available.get('geodatabases', [])),
                'metadata': len(available.get('metadata', [])),
                'documentation': len(available.get('documentation', []))
            },
            'downloaded': [],
            'failed': []
        }
        
        # Check for new shapefiles
        existing_downloads = set(self.downloader.download_history.get('downloads', {}).keys())
        
        for file_info in available.get('shapefiles', []):
            filename = file_info['name'].replace(' ', '_').replace('/', '_')
            
            if filename not in existing_downloads:
                logger.info(f"New shapefile found: {filename}")
                
                # Download the file
                download_result = self.downloader.download_mapping_file(
                    file_info['url'],
                    filename
                )
                
                if download_result:
                    results['downloaded'].append(filename)
                    self.processing_stats['files_downloaded'].append({
                        'filename': filename,
                        'downloaded_at': datetime.now().isoformat()
                    })
                else:
                    results['failed'].append(filename)
                
                time.sleep(1)  # Rate limiting
        
        # Save status
        self.save_status()
        
        logger.info(f"Scan complete: {len(results['downloaded'])} new files downloaded")
        
        return results
    
    def process_shapefile(self, file_path: Path) -> Dict:
        """
        Process a downloaded shapefile
        
        Args:
            file_path: Path to shapefile
            
        Returns:
            Processing result
        """
        logger.info(f"Processing shapefile: {file_path.name}")
        
        try:
            # Parse shapefile
            parse_result = self.parser.parse_shapefile(file_path)
            
            if not parse_result['success']:
                logger.error(f"Failed to parse {file_path.name}: {parse_result.get('error')}")
                return {
                    'status': 'parse_error',
                    'file': str(file_path),
                    'error': parse_result.get('error')
                }
            
            # Extract statistics
            stats = parse_result.get('statistics', {})
            
            logger.info(f"Parsed {file_path.name}:")
            logger.info(f"  Total features: {stats.get('total_features', 0):,}")
            logger.info(f"  Unique parcels: {stats.get('unique_parcels', 0):,}")
            logger.info(f"  Has geometry: {stats.get('has_geometry', 0):,}")
            
            # Extract parcels
            parcels = self.parser.extract_parcels(parse_result)
            
            if parcels:
                # Save parcels as CSV
                csv_path = file_path.parent / f"{file_path.stem}_parcels.csv"
                self.parser.save_as_csv(parse_result, csv_path)
                logger.info(f"Saved {len(parcels)} parcels to {csv_path.name}")
                
                # Update statistics
                self.processing_stats['total_parcels_extracted'] += len(parcels)
            
            # Mark as processed
            self.processing_stats['files_processed'].append({
                'filename': file_path.name,
                'processed_at': datetime.now().isoformat(),
                'features': stats.get('total_features', 0),
                'parcels': len(parcels)
            })
            
            return {
                'status': 'success',
                'file': str(file_path),
                'features': stats.get('total_features', 0),
                'parcels': len(parcels),
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            
            self.processing_stats['errors'].append({
                'file': str(file_path),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'status': 'error',
                'file': str(file_path),
                'error': str(e)
            }
    
    def process_extracted_files(self) -> Dict:
        """
        Process all extracted shapefile directories
        
        Returns:
            Processing results
        """
        logger.info("Processing extracted shapefiles")
        
        extracted_dir = self.downloader.extracted_dir
        
        results = {
            'processed': [],
            'failed': [],
            'start_time': datetime.now().isoformat()
        }
        
        # Find all .shp files in extracted directories
        shapefiles = list(extracted_dir.glob("**/*.shp"))
        
        logger.info(f"Found {len(shapefiles)} shapefiles to process")
        
        # Get list of already processed files
        processed_files = {p['filename'] for p in self.processing_stats['files_processed']}
        
        for shapefile in shapefiles:
            if shapefile.name in processed_files:
                logger.debug(f"Skipping already processed: {shapefile.name}")
                continue
            
            result = self.process_shapefile(shapefile)
            
            if result['status'] == 'success':
                results['processed'].append(shapefile.name)
            else:
                results['failed'].append(shapefile.name)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Save status
        self.save_status()
        
        logger.info(f"Processing complete: {len(results['processed'])} successful, {len(results['failed'])} failed")
        
        return results
    
    def download_county_mapping(self, county_code: str, year: Optional[int] = None) -> Dict:
        """
        Download and process mapping for a specific county
        
        Args:
            county_code: Two-digit county code
            year: Year for the data
            
        Returns:
            Download and processing results
        """
        logger.info(f"Downloading mapping for county {county_code}")
        
        # Download county mapping
        download_result = self.downloader.download_county_mapping(
            county_code,
            map_types=['parcels', 'roads', 'water'],
            year=year
        )
        
        results = {
            'county_code': county_code,
            'county_name': download_result['county_name'],
            'downloads': download_result['downloads'],
            'processing': []
        }
        
        # Process downloaded files
        for download in download_result['downloads']:
            if download['status'] in ['downloaded', 'exists']:
                # Find extracted shapefile
                filename_stem = download['filename'].replace('.zip', '')
                extracted_dir = self.downloader.extracted_dir / filename_stem
                
                if extracted_dir.exists():
                    # Find .shp file
                    shapefiles = list(extracted_dir.glob("*.shp"))
                    
                    for shapefile in shapefiles:
                        process_result = self.process_shapefile(shapefile)
                        results['processing'].append({
                            'file': shapefile.name,
                            'status': process_result['status'],
                            'parcels': process_result.get('parcels', 0)
                        })
        
        return results
    
    def daily_check(self):
        """Perform daily check for new mapping data"""
        logger.info(f"Running daily mapping check #{self.run_count + 1}")
        
        self.run_count += 1
        self.last_check = datetime.now().isoformat()
        
        # Scan and download new files
        scan_result = self.scan_and_download()
        
        # Process any new files
        if scan_result['downloaded']:
            process_result = self.process_extracted_files()
            logger.info(f"Processed {len(process_result['processed'])} new files")
        
        # Save status
        self.save_status()
        
        logger.info(f"Daily mapping check completed")
    
    def weekly_full_scan(self):
        """Perform weekly full scan and processing"""
        logger.info("Running weekly mapping full scan")
        
        # Scan for all available files
        scan_result = self.scan_and_download()
        
        # Process all extracted files
        process_result = self.process_extracted_files()
        
        self.processing_stats['last_full_scan'] = datetime.now().isoformat()
        self.save_status()
        
        logger.info(f"Weekly scan completed: {len(process_result['processed'])} files processed")
    
    def process_priority_counties(self, year: Optional[int] = None) -> Dict:
        """Process mapping for priority counties"""
        logger.info("Processing mapping for priority counties")
        
        results = {
            'counties': [],
            'total_parcels': 0,
            'start_time': datetime.now().isoformat()
        }
        
        for county_code in self.downloader.PRIORITY_COUNTIES:
            county_result = self.download_county_mapping(county_code, year)
            
            results['counties'].append(county_result)
            
            # Count parcels
            for process in county_result.get('processing', []):
                results['total_parcels'] += process.get('parcels', 0)
            
            time.sleep(2)
        
        results['end_time'] = datetime.now().isoformat()
        
        logger.info(f"Priority counties complete: {results['total_parcels']:,} parcels extracted")
        
        return results
    
    def start_monitoring(self, daily_time: str = "06:00", weekly_day: str = "sunday"):
        """
        Start monitoring service
        
        Args:
            daily_time: Time for daily checks (24-hour format)
            weekly_day: Day for weekly full scans
        """
        logger.info(f"Starting Florida Mapping monitoring service")
        logger.info(f"Daily checks scheduled for {daily_time}")
        logger.info(f"Weekly full scans scheduled for {weekly_day}s")
        
        # Schedule daily checks
        schedule.every().day.at(daily_time).do(self.daily_check)
        
        # Schedule weekly full scans
        getattr(schedule.every(), weekly_day).at("05:00").do(self.weekly_full_scan)
        
        # Run initial check
        logger.info("Running initial mapping check...")
        self.daily_check()
        
        # Start monitoring loop
        logger.info("Mapping monitoring service started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Mapping monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Mapping monitoring service error: {e}")
    
    def run_once(self, mode: str = 'scan'):
        """
        Run monitor once and exit
        
        Args:
            mode: 'scan' (scan and download), 'process' (process files), 
                  'priority' (process priority counties), 'status' (show status)
        """
        logger.info(f"Running one-time mapping check (mode: {mode})")
        
        if mode == 'status':
            # Show current status
            status = self.get_status()
            print("\nCurrent Mapping Monitor Status:")
            print(json.dumps(status, indent=2))
            
        elif mode == 'scan':
            # Scan and download
            result = self.scan_and_download()
            print("\nScan and Download Result:")
            print(f"  Available files: {result['available_files']}")
            print(f"  Downloaded: {len(result['downloaded'])} files")
            if result['failed']:
                print(f"  Failed: {result['failed']}")
            
        elif mode == 'process':
            # Process extracted files
            result = self.process_extracted_files()
            print("\nProcessing Result:")
            print(f"  Processed: {len(result['processed'])} files")
            if result['failed']:
                print(f"  Failed: {result['failed']}")
            
        elif mode == 'priority':
            # Process priority counties
            result = self.process_priority_counties()
            print("\nPriority Counties Result:")
            print(f"  Counties processed: {len(result['counties'])}")
            print(f"  Total parcels: {result['total_parcels']:,}")
        
        else:
            print("Invalid mode")
    
    def get_status(self) -> Dict:
        """Get current monitor status"""
        # Get download status
        download_status = self.downloader.get_download_status()
        
        return {
            'monitor': {
                'run_count': self.run_count,
                'last_check': self.last_check,
                'last_scan': self.last_scan
            },
            'downloads': {
                'total_downloads': download_status['total_downloads'],
                'extracted_datasets': len(download_status['extracted_datasets'])
            },
            'processing': {
                'files_downloaded': len(self.processing_stats['files_downloaded']),
                'files_processed': len(self.processing_stats['files_processed']),
                'total_parcels_extracted': self.processing_stats['total_parcels_extracted'],
                'last_full_scan': self.processing_stats['last_full_scan'],
                'recent_errors': self.processing_stats['errors'][-5:]  # Last 5 errors
            }
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida Mapping Data Monitor')
    parser.add_argument('--mode', choices=['monitor', 'scan', 'process', 'priority', 'status'],
                       default='scan',
                       help='Run mode: monitor (continuous), scan (scan and download), process (process files), priority (priority counties), status (show status)')
    parser.add_argument('--daily-time', default='06:00',
                       help='Time for daily checks (24-hour format)')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = FloridaMappingMonitor()
    
    if args.mode == 'monitor':
        # Start continuous monitoring
        monitor.start_monitoring(daily_time=args.daily_time)
    else:
        # Run once
        monitor.run_once(mode=args.mode)