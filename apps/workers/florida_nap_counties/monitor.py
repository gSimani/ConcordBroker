"""
Florida Revenue NAP Counties Monitor
Monitors and orchestrates NAP data downloads, parsing, and loading for all Florida counties
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

from nap_counties_downloader import FloridaNAPCountiesDownloader
from nap_parser import NAPParser
from nap_database import NAPDatabaseLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_nap_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaNAPMonitor:
    """Monitors and manages Florida Revenue NAP data for all counties"""
    
    def __init__(self):
        """Initialize monitor components"""
        self.downloader = FloridaNAPCountiesDownloader()
        self.parser = NAPParser()
        self.loader = NAPDatabaseLoader()
        
        self.run_count = 0
        self.last_check = None
        self.last_update = None
        
        # Status file
        self.status_file = Path("florida_nap_monitor_status.json")
        self.load_status()
        
        # Processing statistics
        self.processing_stats = {
            'counties_processed': [],
            'total_records_loaded': 0,
            'total_assessments_amount': 0,
            'last_full_run': None,
            'errors': []
        }
    
    def load_status(self):
        """Load monitor status from file"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                status = json.load(f)
                self.run_count = status.get('run_count', 0)
                self.last_check = status.get('last_check')
                self.last_update = status.get('last_update')
                self.processing_stats = status.get('processing_stats', self.processing_stats)
    
    def save_status(self):
        """Save monitor status to file"""
        status = {
            'run_count': self.run_count,
            'last_check': self.last_check,
            'last_update': self.last_update,
            'processing_stats': self.processing_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
    
    def process_county(self, county_code: str, year: Optional[int] = None) -> Dict:
        """
        Process a single county: download, parse, and load to database
        
        Args:
            county_code: Two-digit county code
            year: Assessment year (defaults to current year)
            
        Returns:
            Processing result
        """
        if not year:
            year = datetime.now().year
        
        county_name = self.downloader.FLORIDA_COUNTIES.get(county_code, f"County_{county_code}")
        
        logger.info(f"Processing NAP data for {county_name} ({county_code}) for year {year}")
        
        try:
            # Step 1: Download NAP file
            download_result = self.downloader.download_county_nap(county_code, year)
            
            if not download_result:
                logger.warning(f"No NAP file available for {county_name}")
                return {
                    'county_code': county_code,
                    'county_name': county_name,
                    'status': 'no_data',
                    'year': year
                }
            
            if download_result['status'] == 'up_to_date':
                logger.info(f"NAP file for {county_name} is up to date, skipping")
                return {
                    'county_code': county_code,
                    'county_name': county_name,
                    'status': 'up_to_date',
                    'year': year
                }
            
            # Step 2: Parse NAP file
            file_path = Path(download_result['file_path'])
            
            logger.info(f"Parsing NAP file for {county_name}")
            parse_result = self.parser.parse_file(file_path)
            
            if not parse_result['success']:
                logger.error(f"Failed to parse NAP file for {county_name}: {parse_result.get('error')}")
                return {
                    'county_code': county_code,
                    'county_name': county_name,
                    'status': 'parse_error',
                    'error': parse_result.get('error'),
                    'year': year
                }
            
            logger.info(f"Parsed {parse_result['total_records']:,} NAP records for {county_name}")
            
            # Extract statistics
            stats = parse_result.get('statistics', {})
            
            # Step 3: Load to database
            logger.info(f"Loading {county_name} NAP data to database")
            load_result = self.loader.load_file(
                file_path,
                parse_result,
                county_code,
                county_name,
                year
            )
            
            if load_result['status'] != 'success':
                logger.error(f"Failed to load NAP data for {county_name}: {load_result.get('message')}")
                return {
                    'county_code': county_code,
                    'county_name': county_name,
                    'status': 'load_error',
                    'error': load_result.get('message'),
                    'year': year
                }
            
            # Update processing stats
            self.processing_stats['total_assessments_amount'] += stats.get('total_assessment_amount', 0)
            
            logger.info(f"Successfully processed NAP data for {county_name}:")
            logger.info(f"  Downloaded: {download_result.get('size', 0):,} bytes")
            logger.info(f"  Parsed: {parse_result['total_records']:,} records")
            logger.info(f"  Loaded: {load_result['loaded']:,} records")
            logger.info(f"  Total assessments: ${stats.get('total_assessment_amount', 0):,.2f}")
            logger.info(f"  Delinquent: {stats.get('delinquent_count', 0):,}")
            
            return {
                'county_code': county_code,
                'county_name': county_name,
                'status': 'success',
                'year': year,
                'records_parsed': parse_result['total_records'],
                'records_loaded': load_result['loaded'],
                'file_size': download_result.get('size', 0),
                'total_assessment_amount': stats.get('total_assessment_amount', 0),
                'delinquent_count': stats.get('delinquent_count', 0),
                'unique_districts': stats.get('unique_districts', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing NAP data for {county_name}: {e}")
            return {
                'county_code': county_code,
                'county_name': county_name,
                'status': 'error',
                'error': str(e),
                'year': year
            }
    
    def check_for_updates(self, year: Optional[int] = None) -> List[str]:
        """
        Check which counties have NAP updates available
        
        Returns:
            List of county codes with updates
        """
        logger.info("Checking for NAP updates across all counties")
        
        updates = self.downloader.check_for_updates(year)
        
        if updates:
            logger.info(f"Found NAP updates for {len(updates)} counties")
            for code in updates[:5]:  # Show first 5
                name = self.downloader.FLORIDA_COUNTIES.get(code, code)
                logger.info(f"  - {name} ({code})")
            if len(updates) > 5:
                logger.info(f"  ... and {len(updates) - 5} more")
        else:
            logger.info("No NAP updates found")
        
        return updates
    
    def process_updates(self, year: Optional[int] = None, max_counties: int = 10) -> Dict:
        """
        Process counties with available NAP updates
        
        Args:
            year: Assessment year
            max_counties: Maximum number of counties to process in one run
            
        Returns:
            Processing summary
        """
        # Check for updates
        updates = self.check_for_updates(year)
        
        if not updates:
            return {
                'status': 'no_updates',
                'message': 'No counties have NAP updates available'
            }
        
        # Limit processing to max_counties
        counties_to_process = updates[:max_counties]
        
        logger.info(f"Processing NAP data for {len(counties_to_process)} counties with updates")
        
        results = {
            'processed': [],
            'successful': [],
            'failed': [],
            'start_time': datetime.now().isoformat(),
            'total_assessment_amount': 0,
            'total_delinquent': 0
        }
        
        for county_code in counties_to_process:
            result = self.process_county(county_code, year)
            
            results['processed'].append(result)
            
            if result['status'] == 'success':
                results['successful'].append(county_code)
                self.processing_stats['total_records_loaded'] += result.get('records_loaded', 0)
                results['total_assessment_amount'] += result.get('total_assessment_amount', 0)
                results['total_delinquent'] += result.get('delinquent_count', 0)
            else:
                results['failed'].append(county_code)
                if result.get('error'):
                    self.processing_stats['errors'].append({
                        'county': county_code,
                        'error': result['error'],
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Rate limiting between counties
            time.sleep(2)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Update processing stats
        self.processing_stats['counties_processed'].extend(results['successful'])
        self.last_update = datetime.now().isoformat()
        
        # Save status
        self.save_status()
        
        # Log summary
        logger.info(f"\nNAP Processing Summary:")
        logger.info(f"  Processed: {len(results['processed'])} counties")
        logger.info(f"  Successful: {len(results['successful'])}")
        logger.info(f"  Failed: {len(results['failed'])}")
        logger.info(f"  Total assessments: ${results['total_assessment_amount']:,.2f}")
        logger.info(f"  Total delinquent: {results['total_delinquent']:,}")
        
        return results
    
    def process_priority_counties(self, year: Optional[int] = None) -> Dict:
        """Process priority counties (major population centers)"""
        logger.info("Processing NAP data for priority counties")
        
        results = {
            'processed': [],
            'successful': [],
            'failed': [],
            'start_time': datetime.now().isoformat(),
            'total_assessment_amount': 0
        }
        
        for county_code in self.downloader.PRIORITY_COUNTIES:
            result = self.process_county(county_code, year)
            
            results['processed'].append(result)
            
            if result['status'] == 'success':
                results['successful'].append(county_code)
                results['total_assessment_amount'] += result.get('total_assessment_amount', 0)
            else:
                results['failed'].append(county_code)
            
            time.sleep(2)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Save status
        self.save_status()
        
        return results
    
    def daily_check(self):
        """Perform daily check and processing"""
        logger.info(f"Running daily NAP check #{self.run_count + 1}")
        
        self.run_count += 1
        self.last_check = datetime.now().isoformat()
        
        # Process updates (max 10 counties per run)
        result = self.process_updates(max_counties=10)
        
        # Save status
        self.save_status()
        
        logger.info(f"Daily NAP check completed: {result.get('status')}")
    
    def weekly_full_run(self):
        """Perform weekly full processing of priority counties"""
        logger.info("Running weekly NAP full processing")
        
        result = self.process_priority_counties()
        
        self.processing_stats['last_full_run'] = datetime.now().isoformat()
        self.save_status()
        
        logger.info(f"Weekly NAP processing completed: {len(result['successful'])} successful")
    
    def start_monitoring(self, daily_time: str = "04:00", weekly_day: str = "sunday"):
        """
        Start monitoring service
        
        Args:
            daily_time: Time for daily checks (24-hour format)
            weekly_day: Day for weekly full runs
        """
        logger.info(f"Starting Florida NAP monitoring service")
        logger.info(f"Daily checks scheduled for {daily_time}")
        logger.info(f"Weekly full runs scheduled for {weekly_day}s")
        
        # Schedule daily checks
        schedule.every().day.at(daily_time).do(self.daily_check)
        
        # Schedule weekly full runs
        getattr(schedule.every(), weekly_day).at("03:00").do(self.weekly_full_run)
        
        # Run initial check
        logger.info("Running initial NAP check...")
        self.daily_check()
        
        # Start monitoring loop
        logger.info("NAP monitoring service started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("NAP monitoring service stopped by user")
        except Exception as e:
            logger.error(f"NAP monitoring service error: {e}")
    
    def run_once(self, mode: str = 'updates', counties: Optional[List[str]] = None):
        """
        Run monitor once and exit
        
        Args:
            mode: 'updates' (process updates), 'priority' (process priority counties), 
                  'specific' (process specific counties), 'status' (show status)
            counties: List of county codes for 'specific' mode
        """
        logger.info(f"Running one-time NAP check (mode: {mode})")
        
        if mode == 'status':
            # Show current status
            status = self.get_status()
            print("\nCurrent NAP Monitor Status:")
            print(json.dumps(status, indent=2))
            
        elif mode == 'updates':
            # Process available updates
            result = self.process_updates(max_counties=5)
            print("\nNAP Update Processing Result:")
            print(json.dumps(result, indent=2))
            
        elif mode == 'priority':
            # Process priority counties
            result = self.process_priority_counties()
            print("\nNAP Priority Counties Result:")
            print(json.dumps(result, indent=2))
            
        elif mode == 'specific' and counties:
            # Process specific counties
            results = []
            for county_code in counties:
                result = self.process_county(county_code)
                results.append(result)
                time.sleep(2)
            
            print("\nNAP Processing Results:")
            for result in results:
                print(f"  {result['county_name']}: {result['status']}")
                if result['status'] == 'success':
                    print(f"    Records: {result.get('records_loaded', 0):,}")
                    print(f"    Assessments: ${result.get('total_assessment_amount', 0):,.2f}")
        
        else:
            print("Invalid mode or missing counties for 'specific' mode")
    
    def get_status(self) -> Dict:
        """Get current monitor status"""
        # Get download status from downloader
        download_status = self.downloader.get_download_status()
        
        # Get database statistics
        db_stats = self.loader.get_statistics()
        
        return {
            'monitor': {
                'run_count': self.run_count,
                'last_check': self.last_check,
                'last_update': self.last_update
            },
            'downloads': {
                'coverage_percentage': download_status['coverage_percentage'],
                'counties_with_data': len(download_status['counties_with_data']),
                'total_counties': download_status['total_counties'],
                'last_check': download_status['last_check']
            },
            'database': db_stats,
            'processing': {
                'total_counties_processed': len(set(self.processing_stats['counties_processed'])),
                'total_records_loaded': self.processing_stats['total_records_loaded'],
                'total_assessments_amount': self.processing_stats['total_assessments_amount'],
                'last_full_run': self.processing_stats['last_full_run'],
                'recent_errors': self.processing_stats['errors'][-5:]  # Last 5 errors
            }
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida NAP Counties Monitor')
    parser.add_argument('--mode', choices=['monitor', 'once', 'priority', 'status'],
                       default='once',
                       help='Run mode: monitor (continuous), once (check updates), priority (process priority counties), status (show status)')
    parser.add_argument('--counties', nargs='+',
                       help='Specific county codes to process')
    parser.add_argument('--year', type=int,
                       help='Assessment year to process')
    parser.add_argument('--daily-time', default='04:00',
                       help='Time for daily checks (24-hour format)')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = FloridaNAPMonitor()
    
    if args.mode == 'monitor':
        # Start continuous monitoring
        monitor.start_monitoring(daily_time=args.daily_time)
    elif args.mode == 'priority':
        # Process priority counties
        result = monitor.process_priority_counties(args.year)
        print(f"\nProcessed {len(result['successful'])} NAP priority counties successfully")
    elif args.mode == 'status':
        # Show status
        monitor.run_once(mode='status')
    elif args.counties:
        # Process specific counties
        monitor.run_once(mode='specific', counties=args.counties)
    else:
        # Default: check for updates and process
        monitor.run_once(mode='updates')