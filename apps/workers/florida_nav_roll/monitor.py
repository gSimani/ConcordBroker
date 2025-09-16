"""
Florida Revenue NAV Assessment Roll Monitor
Monitors and processes NAV roll data files for all Florida counties
"""

import os
import sys
import json
import time
import schedule
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from nav_roll_parser import NAVRollParser
from nav_roll_database import NAVRollDatabaseLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_nav_roll_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaNAVRollMonitor:
    """Monitors and manages Florida Revenue NAV Assessment Roll data"""
    
    # Florida counties with codes
    FLORIDA_COUNTIES = {
        '01': 'Alachua', '02': 'Baker', '03': 'Bay', '04': 'Bradford',
        '05': 'Brevard', '06': 'Broward', '07': 'Calhoun', '08': 'Charlotte',
        '09': 'Citrus', '10': 'Clay', '11': 'Collier', '12': 'Columbia',
        '13': 'Miami-Dade', '14': 'Desoto', '15': 'Dixie', '16': 'Duval',
        '17': 'Escambia', '18': 'Flagler', '19': 'Franklin', '20': 'Gadsden',
        '21': 'Gilchrist', '22': 'Glades', '23': 'Gulf', '24': 'Hamilton',
        '25': 'Hardee', '26': 'Hendry', '27': 'Hernando', '28': 'Highlands',
        '29': 'Hillsborough', '30': 'Holmes', '31': 'Indian River', '32': 'Jackson',
        '33': 'Jefferson', '34': 'Lafayette', '35': 'Lake', '36': 'Lee',
        '37': 'Leon', '38': 'Levy', '39': 'Liberty', '40': 'Madison',
        '41': 'Manatee', '42': 'Marion', '43': 'Martin', '44': 'Monroe',
        '45': 'Nassau', '46': 'Okaloosa', '47': 'Okeechobee', '48': 'Orange',
        '49': 'Osceola', '50': 'Palm Beach', '51': 'Pasco', '52': 'Pinellas',
        '53': 'Polk', '54': 'Putnam', '55': 'St. Johns', '56': 'St. Lucie',
        '57': 'Santa Rosa', '58': 'Sarasota', '59': 'Seminole', '60': 'Sumter',
        '61': 'Suwannee', '62': 'Taylor', '63': 'Union', '64': 'Volusia',
        '65': 'Wakulla', '66': 'Walton', '67': 'Washington'
    }
    
    # Priority counties (major population centers)
    PRIORITY_COUNTIES = ['06', '13', '29', '48', '50', '52']  # Broward, Miami-Dade, Hillsborough, Orange, Palm Beach, Pinellas
    
    def __init__(self, data_dir: str = "data/florida_nav_roll"):
        """
        Initialize monitor
        
        Args:
            data_dir: Directory for NAV roll files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.raw_dir = self.data_dir / "raw"
        self.metadata_dir = self.data_dir / "metadata"
        
        for dir_path in [self.raw_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Initialize components
        self.parser = NAVRollParser()
        self.loader = NAVRollDatabaseLoader()
        
        # Status tracking
        self.status_file = self.metadata_dir / "monitor_status.json"
        self.load_status()
        
        # Processing statistics
        self.processing_stats = {
            'counties_processed': [],
            'total_parcels_loaded': 0,
            'total_assessments_loaded': 0,
            'total_tax_amount': 0,
            'last_full_run': None,
            'errors': []
        }
    
    def load_status(self):
        """Load monitor status from file"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                status = json.load(f)
                self.processing_stats = status.get('processing_stats', self.processing_stats)
    
    def save_status(self):
        """Save monitor status to file"""
        status = {
            'processing_stats': self.processing_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
    
    def find_nav_roll_files(self, county_number: str, year: Optional[int] = None) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Find NAV roll files for a county
        
        Args:
            county_number: Two-digit county code
            year: Assessment year (defaults to current year)
            
        Returns:
            Tuple of (Table N file path, Table D file path)
        """
        if not year:
            year = datetime.now().year
        
        # File naming convention: NAVN[CC][YY]01.TXT and NAVD[CC][YY]01.TXT
        # Where CC is county code and YY is last two digits of year
        year_suffix = str(year)[-2:]
        
        # Look for files in raw directory
        table_n_pattern = f"NAVN{county_number}{year_suffix}*.TXT"
        table_d_pattern = f"NAVD{county_number}{year_suffix}*.TXT"
        
        table_n_files = list(self.raw_dir.glob(table_n_pattern))
        table_d_files = list(self.raw_dir.glob(table_d_pattern))
        
        table_n_file = table_n_files[0] if table_n_files else None
        table_d_file = table_d_files[0] if table_d_files else None
        
        # Also check for CSV files
        if not table_n_file:
            csv_pattern = f"NAVN{county_number}*.csv"
            csv_files = list(self.raw_dir.glob(csv_pattern))
            table_n_file = csv_files[0] if csv_files else None
        
        if not table_d_file:
            csv_pattern = f"NAVD{county_number}*.csv"
            csv_files = list(self.raw_dir.glob(csv_pattern))
            table_d_file = csv_files[0] if csv_files else None
        
        return table_n_file, table_d_file
    
    def process_county(self, county_number: str, year: Optional[int] = None) -> Dict:
        """
        Process NAV roll data for a county
        
        Args:
            county_number: Two-digit county code
            year: Assessment year
            
        Returns:
            Processing result
        """
        if not year:
            year = datetime.now().year
        
        county_name = self.FLORIDA_COUNTIES.get(county_number, f"County_{county_number}")
        
        logger.info(f"Processing NAV Roll for {county_name} ({county_number}) - Year {year}")
        
        try:
            # Find NAV roll files
            table_n_file, table_d_file = self.find_nav_roll_files(county_number, year)
            
            if not table_n_file:
                logger.warning(f"No NAV roll files found for {county_name}")
                return {
                    'county_code': county_number,
                    'county_name': county_name,
                    'status': 'no_files',
                    'year': year
                }
            
            logger.info(f"Found files for {county_name}:")
            logger.info(f"  Table N: {table_n_file.name if table_n_file else 'Not found'}")
            logger.info(f"  Table D: {table_d_file.name if table_d_file else 'Not found'}")
            
            # Parse files
            logger.info(f"Parsing NAV roll files for {county_name}")
            parse_result = self.parser.parse_file(table_n_file, table_d_file)
            
            if not parse_result['success']:
                logger.error(f"Failed to parse NAV roll for {county_name}: {parse_result.get('error')}")
                return {
                    'county_code': county_number,
                    'county_name': county_name,
                    'status': 'parse_error',
                    'error': parse_result.get('error'),
                    'year': year
                }
            
            # Log parsing results
            logger.info(f"Parsed NAV roll for {county_name}:")
            logger.info(f"  Table N records: {parse_result.get('table_n_count', 0):,}")
            logger.info(f"  Table D records: {parse_result.get('table_d_count', 0):,}")
            
            # Extract statistics
            stats = parse_result.get('statistics', {})
            
            # Load to database
            logger.info(f"Loading {county_name} NAV roll to database")
            load_result = self.loader.load_file(
                table_n_file,
                table_d_file,
                parse_result,
                county_number,
                county_name,
                year
            )
            
            if load_result['status'] not in ['success', 'parcels_only', 'assessments_only', 'partial']:
                logger.error(f"Failed to load NAV roll for {county_name}: {load_result.get('status')}")
                return {
                    'county_code': county_number,
                    'county_name': county_name,
                    'status': 'load_error',
                    'error': load_result.get('status'),
                    'year': year
                }
            
            # Update processing stats
            if load_result['parcels']:
                self.processing_stats['total_parcels_loaded'] += load_result['parcels'].get('loaded', 0)
            if load_result['assessments']:
                self.processing_stats['total_assessments_loaded'] += load_result['assessments'].get('loaded', 0)
            
            # Calculate total tax from assessments
            if 'table_d_records' in parse_result and parse_result['table_d_records']:
                total_tax = sum(r.get('tax_amount', 0) or 0 for r in parse_result['table_d_records'])
                self.processing_stats['total_tax_amount'] += total_tax
                
                logger.info(f"  Total tax amount: ${total_tax:,.2f}")
            
            logger.info(f"Successfully processed NAV roll for {county_name}")
            
            return {
                'county_code': county_number,
                'county_name': county_name,
                'status': 'success',
                'year': year,
                'parcels_parsed': parse_result.get('table_n_count', 0),
                'assessments_parsed': parse_result.get('table_d_count', 0),
                'parcels_loaded': load_result['parcels'].get('loaded', 0) if load_result['parcels'] else 0,
                'assessments_loaded': load_result['assessments'].get('loaded', 0) if load_result['assessments'] else 0,
                'unique_authorities': stats.get('unique_authorities', 0),
                'unique_functions': stats.get('unique_functions', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing NAV roll for {county_name}: {e}")
            return {
                'county_code': county_number,
                'county_name': county_name,
                'status': 'error',
                'error': str(e),
                'year': year
            }
    
    def process_priority_counties(self, year: Optional[int] = None) -> Dict:
        """Process priority counties (major population centers)"""
        logger.info("Processing NAV roll for priority counties")
        
        results = {
            'processed': [],
            'successful': [],
            'failed': [],
            'start_time': datetime.now().isoformat(),
            'total_parcels': 0,
            'total_assessments': 0
        }
        
        for county_code in self.PRIORITY_COUNTIES:
            result = self.process_county(county_code, year)
            
            results['processed'].append(result)
            
            if result['status'] == 'success':
                results['successful'].append(county_code)
                results['total_parcels'] += result.get('parcels_loaded', 0)
                results['total_assessments'] += result.get('assessments_loaded', 0)
            else:
                results['failed'].append(county_code)
                if result.get('error'):
                    self.processing_stats['errors'].append({
                        'county': county_code,
                        'error': result['error'],
                        'timestamp': datetime.now().isoformat()
                    })
            
            time.sleep(2)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Update processing stats
        self.processing_stats['counties_processed'].extend(results['successful'])
        
        # Save status
        self.save_status()
        
        # Log summary
        logger.info(f"\nNAV Roll Processing Summary:")
        logger.info(f"  Processed: {len(results['processed'])} counties")
        logger.info(f"  Successful: {len(results['successful'])}")
        logger.info(f"  Failed: {len(results['failed'])}")
        logger.info(f"  Total parcels: {results['total_parcels']:,}")
        logger.info(f"  Total assessments: {results['total_assessments']:,}")
        
        return results
    
    def scan_for_files(self) -> Dict:
        """Scan raw directory for available NAV roll files"""
        logger.info("Scanning for available NAV roll files")
        
        available = {
            'table_n_files': [],
            'table_d_files': [],
            'counties_with_data': set(),
            'years_available': set()
        }
        
        # Scan for Table N files
        for file_path in self.raw_dir.glob("NAVN*.TXT"):
            filename = file_path.name
            # Extract county and year from filename
            if len(filename) >= 8:
                county = filename[4:6]
                year_suffix = filename[6:8]
                
                available['table_n_files'].append({
                    'file': filename,
                    'county': county,
                    'county_name': self.FLORIDA_COUNTIES.get(county, county),
                    'year': f"20{year_suffix}"
                })
                
                available['counties_with_data'].add(county)
                available['years_available'].add(f"20{year_suffix}")
        
        # Scan for Table D files
        for file_path in self.raw_dir.glob("NAVD*.TXT"):
            filename = file_path.name
            # Extract county and year from filename
            if len(filename) >= 8:
                county = filename[4:6]
                year_suffix = filename[6:8]
                
                available['table_d_files'].append({
                    'file': filename,
                    'county': county,
                    'county_name': self.FLORIDA_COUNTIES.get(county, county),
                    'year': f"20{year_suffix}"
                })
                
                available['counties_with_data'].add(county)
                available['years_available'].add(f"20{year_suffix}")
        
        # Also check for CSV files
        for file_path in self.raw_dir.glob("NAV*.csv"):
            filename = file_path.name
            available['counties_with_data'].add('CSV')
        
        available['counties_with_data'] = list(available['counties_with_data'])
        available['years_available'] = list(available['years_available'])
        
        logger.info(f"Found {len(available['table_n_files'])} Table N files")
        logger.info(f"Found {len(available['table_d_files'])} Table D files")
        logger.info(f"Counties with data: {len(available['counties_with_data'])}")
        logger.info(f"Years available: {', '.join(sorted(available['years_available']))}")
        
        return available
    
    def daily_check(self):
        """Perform daily check and processing"""
        logger.info(f"Running daily NAV roll check")
        
        # Scan for available files
        available = self.scan_for_files()
        
        # Process counties with available files
        counties_to_process = available['counties_with_data'][:5]  # Limit to 5 per run
        
        results = {
            'processed': [],
            'successful': [],
            'failed': []
        }
        
        for county_code in counties_to_process:
            if county_code == 'CSV':
                continue
            
            result = self.process_county(county_code)
            results['processed'].append(result)
            
            if result['status'] == 'success':
                results['successful'].append(county_code)
            else:
                results['failed'].append(county_code)
            
            time.sleep(2)
        
        # Save status
        self.save_status()
        
        logger.info(f"Daily NAV roll check completed: {len(results['successful'])} successful")
    
    def weekly_full_run(self):
        """Perform weekly full processing of priority counties"""
        logger.info("Running weekly NAV roll full processing")
        
        result = self.process_priority_counties()
        
        self.processing_stats['last_full_run'] = datetime.now().isoformat()
        self.save_status()
        
        logger.info(f"Weekly NAV roll processing completed: {len(result['successful'])} successful")
    
    def start_monitoring(self, daily_time: str = "05:00", weekly_day: str = "sunday"):
        """
        Start monitoring service
        
        Args:
            daily_time: Time for daily checks (24-hour format)
            weekly_day: Day for weekly full runs
        """
        logger.info(f"Starting Florida NAV Roll monitoring service")
        logger.info(f"Daily checks scheduled for {daily_time}")
        logger.info(f"Weekly full runs scheduled for {weekly_day}s")
        
        # Schedule daily checks
        schedule.every().day.at(daily_time).do(self.daily_check)
        
        # Schedule weekly full runs
        getattr(schedule.every(), weekly_day).at("04:00").do(self.weekly_full_run)
        
        # Run initial check
        logger.info("Running initial NAV roll check...")
        self.daily_check()
        
        # Start monitoring loop
        logger.info("NAV Roll monitoring service started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("NAV Roll monitoring service stopped by user")
        except Exception as e:
            logger.error(f"NAV Roll monitoring service error: {e}")
    
    def run_once(self, mode: str = 'scan', counties: Optional[List[str]] = None):
        """
        Run monitor once and exit
        
        Args:
            mode: 'scan' (scan for files), 'priority' (process priority counties),
                  'specific' (process specific counties), 'status' (show status)
            counties: List of county codes for 'specific' mode
        """
        logger.info(f"Running one-time NAV roll check (mode: {mode})")
        
        if mode == 'status':
            # Show current status
            stats = self.get_status()
            print("\nCurrent NAV Roll Monitor Status:")
            print(json.dumps(stats, indent=2))
            
        elif mode == 'scan':
            # Scan for available files
            available = self.scan_for_files()
            print("\nAvailable NAV Roll Files:")
            print(f"  Table N files: {len(available['table_n_files'])}")
            print(f"  Table D files: {len(available['table_d_files'])}")
            print(f"  Counties with data: {len(available['counties_with_data'])}")
            if available['counties_with_data']:
                for county in available['counties_with_data'][:10]:
                    if county != 'CSV':
                        print(f"    - {self.FLORIDA_COUNTIES.get(county, county)} ({county})")
            
        elif mode == 'priority':
            # Process priority counties
            result = self.process_priority_counties()
            print("\nNAV Roll Priority Counties Result:")
            print(json.dumps(result, indent=2))
            
        elif mode == 'specific' and counties:
            # Process specific counties
            results = []
            for county_code in counties:
                result = self.process_county(county_code)
                results.append(result)
                time.sleep(2)
            
            print("\nNAV Roll Processing Results:")
            for result in results:
                print(f"  {result['county_name']}: {result['status']}")
                if result['status'] == 'success':
                    print(f"    Parcels: {result.get('parcels_loaded', 0):,}")
                    print(f"    Assessments: {result.get('assessments_loaded', 0):,}")
        
        else:
            print("Invalid mode or missing counties for 'specific' mode")
    
    def get_status(self) -> Dict:
        """Get current monitor status"""
        # Get database statistics
        db_stats = self.loader.get_statistics()
        
        # Scan for available files
        available = self.scan_for_files()
        
        return {
            'files': {
                'table_n_files': len(available['table_n_files']),
                'table_d_files': len(available['table_d_files']),
                'counties_with_data': len(available['counties_with_data']),
                'years_available': available['years_available']
            },
            'database': db_stats,
            'processing': {
                'total_counties_processed': len(set(self.processing_stats['counties_processed'])),
                'total_parcels_loaded': self.processing_stats['total_parcels_loaded'],
                'total_assessments_loaded': self.processing_stats['total_assessments_loaded'],
                'total_tax_amount': self.processing_stats['total_tax_amount'],
                'last_full_run': self.processing_stats['last_full_run'],
                'recent_errors': self.processing_stats['errors'][-5:]  # Last 5 errors
            }
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida NAV Roll Monitor')
    parser.add_argument('--mode', choices=['monitor', 'scan', 'priority', 'status', 'once'],
                       default='scan',
                       help='Run mode: monitor (continuous), scan (check files), priority (process priority counties), status (show status)')
    parser.add_argument('--counties', nargs='+',
                       help='Specific county codes to process')
    parser.add_argument('--year', type=int,
                       help='Assessment year to process')
    parser.add_argument('--daily-time', default='05:00',
                       help='Time for daily checks (24-hour format)')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = FloridaNAVRollMonitor()
    
    if args.mode == 'monitor':
        # Start continuous monitoring
        monitor.start_monitoring(daily_time=args.daily_time)
    elif args.mode == 'priority':
        # Process priority counties
        result = monitor.process_priority_counties(args.year)
        print(f"\nProcessed {len(result['successful'])} NAV roll priority counties successfully")
    elif args.mode == 'status':
        # Show status
        monitor.run_once(mode='status')
    elif args.mode == 'scan':
        # Scan for available files
        monitor.run_once(mode='scan')
    elif args.counties:
        # Process specific counties
        monitor.run_once(mode='specific', counties=args.counties)
    else:
        # Default: scan for files
        monitor.run_once(mode='scan')