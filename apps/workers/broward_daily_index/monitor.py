"""
Monitoring service for Broward County Daily Index updates
Runs as a background service to check for new files daily
"""

import os
import sys
import logging
import json
import schedule
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pipeline import BrowardDailyIndexPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('broward_daily_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BrowardDailyMonitor:
    """Monitor service for daily index updates"""
    
    def __init__(self):
        """Initialize monitor"""
        self.pipeline = BrowardDailyIndexPipeline()
        self.run_count = 0
        self.last_run = None
        self.last_result = None
    
    def daily_check(self):
        """Run daily check for new files"""
        logger.info("Starting daily check for Broward County index files")
        self.run_count += 1
        
        try:
            # Run pipeline for last day
            result = self.pipeline.run_full_pipeline(days_back=1)
            
            self.last_run = datetime.now()
            self.last_result = result
            
            # Log results
            logger.info(f"Daily check #{self.run_count} completed")
            logger.info(f"Files downloaded: {result.get('files_downloaded', 0)}")
            logger.info(f"Records inserted: {result.get('records_inserted', 0)}")
            
            if result.get('errors'):
                logger.warning(f"Errors encountered: {result['errors']}")
            
            # Save status to file
            self._save_status()
            
        except Exception as e:
            logger.error(f"Daily check failed: {e}")
            self.last_result = {'status': 'failed', 'error': str(e)}
    
    def initial_load(self, days_back: int = 30):
        """Run initial load of historical data"""
        logger.info(f"Running initial load for last {days_back} days")
        
        try:
            result = self.pipeline.run_full_pipeline(days_back=days_back)
            
            logger.info(f"Initial load completed")
            logger.info(f"Files downloaded: {result.get('files_downloaded', 0)}")
            logger.info(f"Records inserted: {result.get('records_inserted', 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Initial load failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _save_status(self):
        """Save monitor status to file"""
        status = {
            'run_count': self.run_count,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_result': self.last_result,
            'pipeline_status': self.pipeline.get_status()
        }
        
        with open('broward_monitor_status.json', 'w') as f:
            json.dump(status, f, indent=2, default=str)
    
    def start_monitoring(self, check_time: str = "02:00"):
        """
        Start daily monitoring
        
        Args:
            check_time: Time to run daily check (24-hour format, e.g., "02:00")
        """
        logger.info(f"Starting Broward Daily Index monitoring service")
        logger.info(f"Daily checks scheduled for {check_time}")
        
        # Schedule daily check
        schedule.every().day.at(check_time).do(self.daily_check)
        
        # Run initial check
        logger.info("Running initial check...")
        self.daily_check()
        
        # Start monitoring loop
        logger.info("Monitoring service started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Monitoring service error: {e}")
    
    def run_once(self, days_back: int = 1):
        """Run pipeline once and exit"""
        logger.info(f"Running one-time check for last {days_back} days")
        
        result = self.pipeline.run_full_pipeline(days_back=days_back)
        
        print("\nPipeline Results:")
        print(json.dumps(result, indent=2))
        
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Broward Daily Index Monitor')
    parser.add_argument('--mode', choices=['monitor', 'once', 'initial'], 
                       default='once',
                       help='Run mode: monitor (continuous), once (single run), initial (historical load)')
    parser.add_argument('--days', type=int, default=1,
                       help='Number of days to look back')
    parser.add_argument('--time', default="02:00",
                       help='Time for daily checks (24-hour format)')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = BrowardDailyMonitor()
    
    if args.mode == 'monitor':
        # Start continuous monitoring
        monitor.start_monitoring(check_time=args.time)
    elif args.mode == 'initial':
        # Run initial historical load
        monitor.initial_load(days_back=args.days)
    else:
        # Run once
        monitor.run_once(days_back=args.days)