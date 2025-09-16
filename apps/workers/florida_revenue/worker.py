"""
Florida Revenue Worker
Scheduled processor for Florida Revenue TPP data
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime
from typing import Dict

from .main import FloridaRevenueAgent
from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaRevenueWorker:
    """Worker for Florida Revenue TPP data collection"""
    
    def __init__(self):
        self.is_running = False
        
    async def run_annual_collection(self, year: str = None) -> Dict:
        """Run annual TPP data collection"""
        if not year:
            year = str(datetime.now().year)
        
        logger.info(f"Starting Florida Revenue annual collection for {year}...")
        
        try:
            async with FloridaRevenueAgent() as agent:
                result = await agent.run_data_collection(year)
                
                if result.get('success'):
                    logger.info(f"Annual collection completed successfully:")
                    logger.info(f"  - Records processed: {result.get('records_processed', 0):,}")
                    logger.info(f"  - Records created: {result.get('records_created', 0):,}")
                    logger.info(f"  - Records updated: {result.get('records_updated', 0):,}")
                    logger.info(f"  - Duration: {result.get('duration_seconds', 0):.2f}s")
                    
                    if 'value_analysis' in result:
                        va = result['value_analysis']
                        logger.info(f"  - Total property value: ${va['total_value']:,.0f}")
                else:
                    logger.error(f"Annual collection failed: {result.get('error')}")
                    
                return result
                
        except Exception as e:
            logger.error(f"Error in annual collection: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_analytics_report(self) -> Dict:
        """Generate analytics report"""
        logger.info("Generating Florida Revenue analytics report...")
        
        try:
            async with FloridaRevenueAgent() as agent:
                analytics = await agent.get_database_analytics()
                
                if analytics.get('top_owners'):
                    logger.info("Top 5 Property Owners:")
                    for i, owner in enumerate(analytics['top_owners'][:5], 1):
                        logger.info(f"  {i}. {owner['owner_name']}: {owner['property_count']:,} properties")
                
                if analytics.get('naics_analysis'):
                    logger.info("Top 5 Business Categories:")
                    for i, naics in enumerate(analytics['naics_analysis'][:5], 1):
                        logger.info(f"  {i}. NAICS {naics['naics_code']}: {naics['record_count']:,} records")
                
                return analytics
                
        except Exception as e:
            logger.error(f"Error generating analytics: {e}")
            return {}
    
    async def run_once(self, task: str = 'annual', year: str = None):
        """Run a single task"""
        if task == 'annual':
            return await self.run_annual_collection(year)
        elif task == 'analytics':
            return await self.run_analytics_report()
        else:
            logger.error(f"Unknown task: {task}")
            return {}
    
    def run_scheduled(self):
        """Run on schedule"""
        logger.info("Starting Florida Revenue worker with scheduled tasks...")
        
        # Schedule annual collection in January
        schedule.every().year.do(
            lambda: asyncio.run(self.run_annual_collection())
        )
        
        # Schedule monthly analytics reports
        schedule.every().month.do(
            lambda: asyncio.run(self.run_analytics_report())
        )
        
        # Schedule quarterly analytics (more detailed)
        schedule.every(3).months.do(
            lambda: asyncio.run(self.run_analytics_report())
        )
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
                
        except KeyboardInterrupt:
            logger.info("Shutting down Florida Revenue worker...")
            self.is_running = False

async def test_worker():
    """Test the worker with current year data"""
    worker = FloridaRevenueWorker()
    
    try:
        # Test annual collection
        logger.info("Testing Florida Revenue worker...")
        result = await worker.run_once('annual', '2025')
        
        if result.get('success'):
            logger.info("✓ Annual collection test passed")
            
            # Test analytics
            analytics = await worker.run_once('analytics')
            if analytics:
                logger.info("✓ Analytics test passed")
            else:
                logger.warning("Analytics test returned empty results")
        else:
            logger.error(f"Annual collection test failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Worker test failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Run test
            asyncio.run(test_worker())
        elif sys.argv[1] == "annual":
            # Run annual collection once
            worker = FloridaRevenueWorker()
            year = sys.argv[2] if len(sys.argv) > 2 else None
            asyncio.run(worker.run_once('annual', year))
        elif sys.argv[1] == "analytics":
            # Run analytics once
            worker = FloridaRevenueWorker()
            asyncio.run(worker.run_once('analytics'))
        else:
            print("Usage: python worker.py [test|annual|analytics|schedule] [year]")
    else:
        # Run scheduled worker
        worker = FloridaRevenueWorker()
        worker.run_scheduled()