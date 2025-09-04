"""
Official Records Worker
Runs scheduled scraping of Broward County Official Records
"""

import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import List
import schedule
import time
from .scraper import OfficialRecordsScraper, PropertyTransfer
from .database import OfficialRecordsDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OfficialRecordsWorker:
    """Worker for Official Records data collection"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.scraper = OfficialRecordsScraper()
        self.db = OfficialRecordsDB(self.database_url)
        self.is_running = False
        
    async def initialize(self):
        """Initialize worker components"""
        logger.info("Initializing Official Records worker...")
        await self.db.initialize()
        await self.scraper.initialize()
        logger.info("Worker initialized successfully")
        
    async def cleanup(self):
        """Cleanup resources"""
        await self.scraper.close()
        await self.db.close()
        
    async def daily_scrape(self):
        """Daily scrape of new records"""
        logger.info("Starting daily Official Records scrape...")
        
        try:
            # Get yesterday's transfers (most recent complete day)
            yesterday = datetime.now() - timedelta(days=1)
            transfers = await self.scraper.search_transfers(
                start_date=yesterday,
                end_date=yesterday
            )
            
            logger.info(f"Found {len(transfers)} transfers for {yesterday.date()}")
            
            # Save to database
            count = await self.db.bulk_insert_transfers(transfers)
            logger.info(f"Saved {count} transfers to database")
            
            # Check for high-value transfers
            high_value = [t for t in transfers 
                         if (t.consideration and t.consideration > 1000000) or
                            (t.mortgage_amount and t.mortgage_amount > 1000000)]
                            
            if high_value:
                logger.info(f"Found {len(high_value)} high-value transfers:")
                for transfer in high_value:
                    value = transfer.consideration or transfer.mortgage_amount
                    logger.info(f"  - {transfer.grantee} bought from {transfer.grantor}: ${value:,.0f}")
                    
            # Track known entities
            await self.track_entities(transfers)
            
            # Find potential flips
            await self.identify_flips()
            
        except Exception as e:
            logger.error(f"Error in daily scrape: {e}")
            
    async def weekly_deep_scrape(self):
        """Weekly deep scrape for last 7 days"""
        logger.info("Starting weekly deep scrape...")
        
        try:
            # Get last week's transfers
            start_date = datetime.now() - timedelta(days=7)
            transfers = await self.scraper.search_transfers(start_date)
            
            logger.info(f"Found {len(transfers)} transfers in last 7 days")
            
            # Save to database
            count = await self.db.bulk_insert_transfers(transfers)
            logger.info(f"Saved {count} transfers to database")
            
            # Analyze trends
            await self.analyze_weekly_trends(transfers)
            
        except Exception as e:
            logger.error(f"Error in weekly scrape: {e}")
            
    async def track_entities(self, transfers: List[PropertyTransfer]):
        """Track activity of known investment entities"""
        # List of known investment entities to track
        entities = [
            'BLACKSTONE',
            'INVITATION HOMES',
            'AMERICAN HOMES 4 RENT',
            'PROGRESS RESIDENTIAL',
            'TRICON RESIDENTIAL',
            'LLC',  # Generic LLC tracking
            'TRUST',  # Generic trust tracking
            'HOLDINGS',
            'PROPERTIES',
            'INVESTMENTS'
        ]
        
        for entity in entities:
            entity_transfers = []
            for transfer in transfers:
                if entity.lower() in transfer.grantor.lower() or \
                   entity.lower() in transfer.grantee.lower():
                    entity_transfers.append(transfer)
                    
            if entity_transfers:
                logger.info(f"Entity '{entity}' involved in {len(entity_transfers)} transfers")
                
    async def identify_flips(self):
        """Identify potential property flips"""
        try:
            flips = await self.db.find_flips()
            
            if flips:
                logger.info(f"Identified {len(flips)} potential flips:")
                for flip in flips[:5]:  # Show top 5
                    logger.info(
                        f"  - Parcel {flip['parcel_id']}: "
                        f"Bought ${flip['buy_price']:,.0f}, "
                        f"Sold ${flip['sell_price']:,.0f}, "
                        f"Profit ${flip['profit']:,.0f} "
                        f"in {flip['days_held']} days"
                    )
                    
        except Exception as e:
            logger.error(f"Error identifying flips: {e}")
            
    async def analyze_weekly_trends(self, transfers: List[PropertyTransfer]):
        """Analyze weekly transfer trends"""
        try:
            # Calculate statistics
            total_transfers = len(transfers)
            
            # Count by document type
            doc_types = {}
            for transfer in transfers:
                doc_type = transfer.doc_type
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
            # Calculate total consideration
            total_value = sum(t.consideration for t in transfers if t.consideration) or 0
            
            # Average transaction value
            valued_transfers = [t for t in transfers if t.consideration]
            avg_value = total_value / len(valued_transfers) if valued_transfers else 0
            
            logger.info("Weekly Transfer Analysis:")
            logger.info(f"  Total transfers: {total_transfers}")
            logger.info(f"  Total value: ${total_value:,.0f}")
            logger.info(f"  Average value: ${avg_value:,.0f}")
            logger.info("  By document type:")
            for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"    - {doc_type}: {count}")
                
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            
    async def run_once(self, task: str = 'daily'):
        """Run a single scraping task"""
        await self.initialize()
        
        try:
            if task == 'daily':
                await self.daily_scrape()
            elif task == 'weekly':
                await self.weekly_deep_scrape()
            else:
                logger.error(f"Unknown task: {task}")
                
        finally:
            await self.cleanup()
            
    def run_scheduled(self):
        """Run on schedule"""
        asyncio.run(self.initialize())
        
        # Schedule daily scrape at 2 AM
        schedule.every().day.at("02:00").do(
            lambda: asyncio.run(self.daily_scrape())
        )
        
        # Schedule weekly deep scrape on Sundays at 3 AM
        schedule.every().sunday.at("03:00").do(
            lambda: asyncio.run(self.weekly_deep_scrape())
        )
        
        logger.info("Official Records worker started. Running scheduled tasks...")
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Shutting down worker...")
            self.is_running = False
            asyncio.run(self.cleanup())
            
            
async def test_scraper():
    """Test the scraper with a small date range"""
    worker = OfficialRecordsWorker()
    
    try:
        await worker.initialize()
        
        # Test with just today's data
        today = datetime.now()
        transfers = await worker.scraper.search_transfers(
            start_date=today,
            end_date=today
        )
        
        print(f"Found {len(transfers)} transfers today")
        
        if transfers:
            # Show first transfer
            transfer = transfers[0]
            print(f"\nFirst transfer:")
            print(f"  Date: {transfer.recording_date}")
            print(f"  Type: {transfer.doc_type}")
            print(f"  From: {transfer.grantor}")
            print(f"  To: {transfer.grantee}")
            if transfer.consideration:
                print(f"  Amount: ${transfer.consideration:,.2f}")
                
    finally:
        await worker.cleanup()
        

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Run test
            asyncio.run(test_scraper())
        elif sys.argv[1] == "daily":
            # Run daily scrape once
            worker = OfficialRecordsWorker()
            asyncio.run(worker.run_once('daily'))
        elif sys.argv[1] == "weekly":
            # Run weekly scrape once  
            worker = OfficialRecordsWorker()
            asyncio.run(worker.run_once('weekly'))
        else:
            print("Usage: python worker.py [test|daily|weekly|schedule]")
    else:
        # Run scheduled worker
        worker = OfficialRecordsWorker()
        worker.run_scheduled()