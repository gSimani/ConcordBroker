"""
Tax Deed Scraper Scheduler
Runs the scraper automatically at scheduled intervals
"""

import asyncio
import schedule
import time
from datetime import datetime
import logging
import os
import sys
from tax_deed_scraper import BrowardTaxDeedScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tax_deed_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaxDeedScheduler:
    def __init__(self):
        self.is_running = False
        self.last_run = None
        self.run_count = 0
        
    async def run_scraper(self):
        """Run the tax deed scraper"""
        try:
            logger.info("=" * 60)
            logger.info(f"Starting scheduled scrape #{self.run_count + 1}")
            logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            async with BrowardTaxDeedScraper() as scraper:
                results = await scraper.scrape_all()
                
                self.run_count += 1
                self.last_run = datetime.now()
                
                # Log results
                logger.info(f"✅ Scrape #{self.run_count} complete")
                logger.info(f"  - Auctions: {results.get('auctions_scraped', 0)}")
                logger.info(f"  - Properties: {results.get('properties_scraped', 0)}")
                logger.info(f"  - Saved: {results.get('properties_saved', 0)}")
                
                if results.get('errors'):
                    logger.warning(f"  - Errors: {len(results['errors'])}")
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Scraper error: {e}")
            return None
    
    def run_sync(self):
        """Synchronous wrapper for the async scraper"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_scraper())
        finally:
            loop.close()
    
    def schedule_jobs(self):
        """Set up the schedule"""
        # Run every day at 6 AM and 6 PM
        schedule.every().day.at("06:00").do(self.run_sync)
        schedule.every().day.at("18:00").do(self.run_sync)
        
        # Also run every 4 hours during business hours (9 AM - 5 PM)
        schedule.every().day.at("09:00").do(self.run_sync)
        schedule.every().day.at("13:00").do(self.run_sync)
        schedule.every().day.at("17:00").do(self.run_sync)
        
        logger.info("📅 Schedule configured:")
        logger.info("  - Daily at 6:00 AM and 6:00 PM")
        logger.info("  - Business hours at 9:00 AM, 1:00 PM, 5:00 PM")
    
    def run_immediately(self):
        """Run scraper immediately on startup"""
        logger.info("🚀 Running initial scrape on startup...")
        self.run_sync()
    
    def start(self, run_immediately=True):
        """Start the scheduler"""
        logger.info("=" * 60)
        logger.info("TAX DEED SCRAPER SCHEDULER STARTED")
        logger.info("=" * 60)
        
        self.schedule_jobs()
        
        if run_immediately:
            self.run_immediately()
        
        logger.info("\n⏰ Scheduler is running. Press Ctrl+C to stop.")
        logger.info(f"Next scheduled run: {self.get_next_run_time()}")
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Log status every hour
                if datetime.now().minute == 0:
                    self.log_status()
                    
        except KeyboardInterrupt:
            logger.info("\n⏹️ Scheduler stopped by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            self.is_running = False
    
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        jobs = schedule.get_jobs()
        if jobs:
            next_run = min(job.next_run for job in jobs)
            return next_run.strftime('%Y-%m-%d %H:%M:%S')
        return "No scheduled jobs"
    
    def log_status(self):
        """Log current scheduler status"""
        logger.info(f"📊 Status Update:")
        logger.info(f"  - Total runs: {self.run_count}")
        if self.last_run:
            logger.info(f"  - Last run: {self.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  - Next run: {self.get_next_run_time()}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tax Deed Scraper Scheduler')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--no-immediate', action='store_true', help='Don\'t run immediately on startup')
    args = parser.parse_args()
    
    scheduler = TaxDeedScheduler()
    
    if args.once:
        # Run once and exit
        logger.info("Running scraper once...")
        scheduler.run_sync()
        logger.info("✅ Single run complete")
    else:
        # Start scheduler
        scheduler.start(run_immediately=not args.no_immediate)


if __name__ == "__main__":
    main()