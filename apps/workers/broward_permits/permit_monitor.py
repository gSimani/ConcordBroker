"""
Broward County Permit Monitor
Orchestrates permit scraping, loading, and processing
"""

import os
import sys
import json
import time
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from permit_scraper import BrowardPermitScraper
from permit_db_loader import BrowardPermitDBLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('broward_permit_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BrowardPermitMonitor:
    """Monitors and orchestrates Broward County permit data collection"""
    
    def __init__(self):
        """Initialize monitor components"""
        self.scraper = BrowardPermitScraper()
        self.loader = BrowardPermitDBLoader()
        
        self.run_count = 0
        self.last_check = None
        self.last_full_scan = None
        
        # Status file
        self.status_file = Path("broward_permit_monitor_status.json")
        self.load_status()
        
        # Monitoring statistics
        self.monitoring_stats = {
            'total_permits_scraped': 0,
            'total_permits_loaded': 0,
            'scraping_runs': 0,
            'loading_runs': 0,
            'last_successful_scrape': None,
            'last_successful_load': None,
            'errors': []
        }
    
    def load_status(self):
        """Load monitor status from file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                    self.run_count = status.get('run_count', 0)
                    self.last_check = status.get('last_check')
                    self.last_full_scan = status.get('last_full_scan')
                    self.monitoring_stats = status.get('monitoring_stats', self.monitoring_stats)
            except Exception as e:
                logger.error(f"Error loading status: {e}")
    
    def save_status(self):
        """Save monitor status to file"""
        status = {
            'run_count': self.run_count,
            'last_check': self.last_check,
            'last_full_scan': self.last_full_scan,
            'monitoring_stats': self.monitoring_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving status: {e}")
    
    def scrape_and_load_permits(self, days_back: int = 7) -> Dict:
        """
        Scrape permits and load into database
        
        Args:
            days_back: Number of days to look back for permits
            
        Returns:
            Scraping and loading results
        """
        logger.info(f"Scraping permits from last {days_back} days")
        
        results = {
            'scrape_start': datetime.now().isoformat(),
            'days_back': days_back,
            'scraping': {},
            'loading': {},
            'total_permits_scraped': 0,
            'total_permits_loaded': 0,
            'errors': []
        }
        
        try:
            # 1. Scrape permits from all sources
            logger.info("Starting permit scraping...")
            scrape_result = self.scraper.scrape_all_permits(days_back=days_back)
            
            results['scraping'] = scrape_result
            results['total_permits_scraped'] = scrape_result.get('total_permits', 0)
            
            # Update monitoring stats
            self.monitoring_stats['scraping_runs'] += 1
            self.monitoring_stats['total_permits_scraped'] += results['total_permits_scraped']
            
            if scrape_result.get('success', False):
                self.monitoring_stats['last_successful_scrape'] = datetime.now().isoformat()
                logger.info(f"Scraped {results['total_permits_scraped']} permits successfully")
            else:
                logger.error("Permit scraping failed")
                results['errors'].append("Permit scraping failed")
            
            # 2. Load scraped permits into database
            logger.info("Loading permits into database...")
            load_result = self.loader.load_all_permit_files()
            
            results['loading'] = load_result
            results['total_permits_loaded'] = load_result.get('total_records_loaded', 0)
            
            # Update monitoring stats
            self.monitoring_stats['loading_runs'] += 1
            self.monitoring_stats['total_permits_loaded'] += results['total_permits_loaded']
            
            if load_result.get('files_processed', 0) > 0:
                self.monitoring_stats['last_successful_load'] = datetime.now().isoformat()
                logger.info(f"Loaded {results['total_permits_loaded']} new permits")
            
            results['scrape_end'] = datetime.now().isoformat()
            
            # Save status
            self.save_status()
            
        except Exception as e:
            logger.error(f"Error in scrape and load process: {e}")
            results['errors'].append(str(e))
            self.monitoring_stats['errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return results
    
    def daily_permit_check(self):
        """Perform daily permit check (last 2 days)"""
        logger.info(f"Running daily permit check #{self.run_count + 1}")
        
        self.run_count += 1
        self.last_check = datetime.now().isoformat()
        
        # Scrape and load permits from last 2 days (to catch any missed permits)
        result = self.scrape_and_load_permits(days_back=2)
        
        logger.info(f"Daily check complete: {result['total_permits_scraped']} scraped, {result['total_permits_loaded']} loaded")
        
        if result['errors']:
            logger.warning(f"Daily check had errors: {result['errors']}")
    
    def weekly_full_scan(self):
        """Perform weekly full scan (last 30 days)"""
        logger.info("Running weekly permit full scan")
        
        self.last_full_scan = datetime.now().isoformat()
        
        # Scrape and load permits from last 30 days
        result = self.scrape_and_load_permits(days_back=30)
        
        logger.info(f"Weekly scan complete: {result['total_permits_scraped']} scraped, {result['total_permits_loaded']} loaded")
        
        # Clean up old errors (keep last 50)
        if len(self.monitoring_stats['errors']) > 50:
            self.monitoring_stats['errors'] = self.monitoring_stats['errors'][-50:]
        
        self.save_status()
    
    def initialize_system(self) -> Dict:
        """Initialize permit system (create tables, initial scrape)"""
        logger.info("Initializing Broward permit monitoring system")
        
        results = {
            'initialization_start': datetime.now().isoformat(),
            'table_creation': False,
            'initial_scrape': {},
            'success': False
        }
        
        try:
            # 1. Create database tables
            logger.info("Creating permit database tables...")
            table_result = self.loader.create_permit_tables()
            results['table_creation'] = table_result
            
            if not table_result:
                logger.error("Failed to create permit tables")
                return results
            
            # 2. Perform initial scrape (last 60 days)
            logger.info("Performing initial permit scrape...")
            scrape_result = self.scrape_and_load_permits(days_back=60)
            results['initial_scrape'] = scrape_result
            
            results['success'] = table_result and scrape_result.get('total_permits_loaded', 0) > 0
            results['initialization_end'] = datetime.now().isoformat()
            
            if results['success']:
                logger.info("Permit monitoring system initialized successfully")
            else:
                logger.error("Failed to initialize permit monitoring system")
                
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            results['error'] = str(e)
        
        return results
    
    def scrape_specific_county_permits(self, county: str, days_back: int = 7) -> Dict:
        """
        Scrape permits for specific county/jurisdiction
        
        Args:
            county: County/jurisdiction to scrape
            days_back: Days to look back
            
        Returns:
            Scraping results
        """
        logger.info(f"Scraping permits for {county}")
        
        results = {
            'county': county,
            'days_back': days_back,
            'start_time': datetime.now().isoformat()
        }
        
        try:
            if county.lower() in ['bcs', 'unincorporated']:
                # Scrape BCS permits
                permits = self.scraper.scrape_bcs_permits(
                    start_date=(datetime.now() - timedelta(days=days_back)).date(),
                    end_date=datetime.now().date()
                )
                results['permits_found'] = len(permits)
                
            elif county.lower() == 'hollywood':
                # Scrape Hollywood permits
                permits = self.scraper.scrape_hollywood_permits(
                    start_date=(datetime.now() - timedelta(days=days_back)).date(),
                    end_date=datetime.now().date()
                )
                results['permits_found'] = len(permits)
                
            elif county.lower() in ['environmental', 'enviros']:
                # Scrape environmental permits
                permits = self.scraper.scrape_environmental_permits(
                    start_date=(datetime.now() - timedelta(days=days_back)).date(),
                    end_date=datetime.now().date()
                )
                results['permits_found'] = len(permits)
            
            else:
                logger.error(f"Unknown county: {county}")
                results['error'] = f"Unknown county: {county}"
                return results
            
            # Save permits
            if permits:
                filename = f"permit_{county.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.scraper.save_permits(permits, filename)
                results['saved_file'] = filename
            
            results['end_time'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error scraping {county} permits: {e}")
            results['error'] = str(e)
        
        return results
    
    def start_monitoring(self, daily_time: str = "06:00", weekly_day: str = "sunday"):
        """
        Start monitoring service
        
        Args:
            daily_time: Time for daily checks (24-hour format)
            weekly_day: Day for weekly full scans
        """
        logger.info("Starting Broward permit monitoring service")
        logger.info(f"Daily checks scheduled for {daily_time}")
        logger.info(f"Weekly full scans scheduled for {weekly_day}s at 05:00")
        
        # Schedule daily checks
        schedule.every().day.at(daily_time).do(self.daily_permit_check)
        
        # Schedule weekly full scans
        getattr(schedule.every(), weekly_day.lower()).at("05:00").do(self.weekly_full_scan)
        
        # Run initial check
        logger.info("Running initial permit check...")
        self.daily_permit_check()
        
        # Start monitoring loop
        logger.info("Permit monitoring service started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Permit monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Permit monitoring service error: {e}")
    
    def run_once(self, mode: str = 'daily', days_back: Optional[int] = None):
        """
        Run monitor once and exit
        
        Args:
            mode: 'daily' (2 days), 'weekly' (30 days), 'init' (initialize), 
                  'status' (show status), 'custom' (specify days_back)
            days_back: Custom number of days (for 'custom' mode)
        """
        logger.info(f"Running one-time permit check (mode: {mode})")
        
        if mode == 'status':
            # Show current status
            status = self.get_status()
            print("\nBroward Permit Monitor Status:")
            print(json.dumps(status, indent=2, default=str))
            
        elif mode == 'init':
            # Initialize system
            result = self.initialize_system()
            print("\nSystem Initialization Result:")
            print(f"  Tables created: {result['table_creation']}")
            print(f"  Initial permits loaded: {result['initial_scrape'].get('total_permits_loaded', 0)}")
            if not result['success']:
                print("  ❌ Initialization failed!")
            else:
                print("  ✅ Initialization successful!")
                
        elif mode == 'daily':
            # Daily check (2 days)
            result = self.scrape_and_load_permits(days_back=2)
            print("\nDaily Permit Check Result:")
            print(f"  Permits scraped: {result['total_permits_scraped']}")
            print(f"  Permits loaded: {result['total_permits_loaded']}")
            if result['errors']:
                print(f"  Errors: {result['errors']}")
            
        elif mode == 'weekly':
            # Weekly scan (30 days)
            result = self.scrape_and_load_permits(days_back=30)
            print("\nWeekly Permit Scan Result:")
            print(f"  Permits scraped: {result['total_permits_scraped']}")
            print(f"  Permits loaded: {result['total_permits_loaded']}")
            if result['errors']:
                print(f"  Errors: {result['errors']}")
                
        elif mode == 'custom':
            # Custom days back
            days = days_back or 7
            result = self.scrape_and_load_permits(days_back=days)
            print(f"\nCustom Permit Check Result ({days} days):")
            print(f"  Permits scraped: {result['total_permits_scraped']}")
            print(f"  Permits loaded: {result['total_permits_loaded']}")
            if result['errors']:
                print(f"  Errors: {result['errors']}")
        
        else:
            print(f"Invalid mode: {mode}")
    
    def get_status(self) -> Dict:
        """Get current monitor status"""
        # Get scraper status
        scraper_status = self.scraper.get_scraping_stats()
        
        # Get loader statistics
        loader_stats = self.loader.get_permit_statistics()
        
        return {
            'monitor': {
                'run_count': self.run_count,
                'last_check': self.last_check,
                'last_full_scan': self.last_full_scan,
                'monitoring_stats': self.monitoring_stats
            },
            'scraper': scraper_status,
            'database': loader_stats
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Broward Permit Monitor')
    parser.add_argument('--mode', 
                       choices=['monitor', 'daily', 'weekly', 'init', 'status', 'custom'],
                       default='daily',
                       help='Run mode: monitor (continuous), daily (2 days), weekly (30 days), init (initialize), status (show status), custom (specify days)')
    parser.add_argument('--daily-time', default='06:00',
                       help='Time for daily checks (24-hour format)')
    parser.add_argument('--weekly-day', default='sunday', 
                       choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                       help='Day for weekly scans')
    parser.add_argument('--days-back', type=int,
                       help='Number of days to look back (for custom mode)')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = BrowardPermitMonitor()
    
    if args.mode == 'monitor':
        # Start continuous monitoring
        monitor.start_monitoring(daily_time=args.daily_time, weekly_day=args.weekly_day)
    else:
        # Run once
        monitor.run_once(mode=args.mode, days_back=args.days_back)