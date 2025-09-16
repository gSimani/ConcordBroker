"""
NAV Assessments Worker
Scheduled processor for NAV (Non Ad Valorem) assessments data
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime
from typing import Dict, List

try:
    from .main import NAVAssessmentsAgent
    from .config import settings
except ImportError:
    from main import NAVAssessmentsAgent
    from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NAVAssessmentsWorker:
    """Worker for NAV Assessments data collection"""
    
    def __init__(self):
        self.is_running = False
        
    async def run_annual_collection(self, year: str = None, counties: List[str] = None) -> Dict:
        """Run annual NAV data collection"""
        if not year:
            year = str(datetime.now().year)
        
        if not counties:
            counties = list(settings.PRIORITY_COUNTIES.keys())
        
        logger.info(f"Starting NAV annual collection for {year}, counties: {counties}")
        
        results = {
            'year': year,
            'counties': counties,
            'started_at': datetime.now().isoformat(),
            'table_results': {},
            'success': True,
            'errors': []
        }
        
        try:
            # Process NAV N table (parcel summaries) first
            async with NAVAssessmentsAgent() as agent:
                nav_n_result = await agent.run_nav_collection('N', year, counties)
                results['table_results']['N'] = nav_n_result
                
                if not nav_n_result.get('success'):
                    results['success'] = False
                    results['errors'].extend(nav_n_result.get('errors', []))
                    logger.error(f"NAV N collection failed for {year}")
                else:
                    logger.info(f"NAV N collection completed: {nav_n_result.get('records_created', 0):,} records created")
            
            # Process NAV D table (assessment details) second
            async with NAVAssessmentsAgent() as agent:
                nav_d_result = await agent.run_nav_collection('D', year, counties)
                results['table_results']['D'] = nav_d_result
                
                if not nav_d_result.get('success'):
                    results['success'] = False
                    results['errors'].extend(nav_d_result.get('errors', []))
                    logger.error(f"NAV D collection failed for {year}")
                else:
                    logger.info(f"NAV D collection completed: {nav_d_result.get('records_created', 0):,} records created")
            
            results['finished_at'] = datetime.now().isoformat()
            
            if results['success']:
                logger.info("NAV annual collection completed successfully")
                
                # Log summary statistics
                total_n_records = results['table_results']['N'].get('records_created', 0)
                total_d_records = results['table_results']['D'].get('records_created', 0)
                logger.info(f"Total NAV records processed:")
                logger.info(f"  - Parcel summaries (N): {total_n_records:,}")
                logger.info(f"  - Assessment details (D): {total_d_records:,}")
            else:
                logger.error("NAV annual collection completed with errors")
                
            return results
            
        except Exception as e:
            logger.error(f"Error in NAV annual collection: {e}")
            results['success'] = False
            results['errors'].append(str(e))
            return results
    
    async def run_analytics_report(self, counties: List[str] = None, year: str = None) -> Dict:
        """Generate NAV analytics report"""
        if not year:
            year = str(datetime.now().year)
        
        logger.info(f"Generating NAV analytics report for {year}...")
        
        analytics = {}
        
        try:
            # Get analytics for each county or overall
            if counties:
                for county_code in counties:
                    county_name = settings.get_county_name(county_code)
                    logger.info(f"Analyzing {county_name} County ({county_code})...")
                    
                    async with NAVAssessmentsAgent() as agent:
                        county_analytics = await agent.get_database_analytics(county_code, year)
                        analytics[county_code] = {
                            'county_name': county_name,
                            'analytics': county_analytics
                        }
                        
                        if county_analytics.get('summary'):
                            summary = county_analytics['summary']
                            logger.info(f"  Total parcels: {summary.get('total_parcels', 0):,}")
                            logger.info(f"  Total assessments: ${summary.get('total_assessment_amount', 0):,.0f}")
                            logger.info(f"  Average assessment: ${summary.get('avg_assessment_amount', 0):,.0f}")
            else:
                # Overall analytics
                async with NAVAssessmentsAgent() as agent:
                    overall_analytics = await agent.get_database_analytics(None, year)
                    analytics['overall'] = overall_analytics
                    
                    if overall_analytics.get('summary'):
                        summary = overall_analytics['summary']
                        logger.info(f"Overall NAV Statistics for {year}:")
                        logger.info(f"  Total parcels: {summary.get('total_parcels', 0):,}")
                        logger.info(f"  Total assessments: ${summary.get('total_assessment_amount', 0):,.0f}")
                        
                    if overall_analytics.get('function_analysis'):
                        logger.info("Top 5 Assessment Functions:")
                        for i, func in enumerate(overall_analytics['function_analysis'][:5], 1):
                            logger.info(f"  {i}. {func['function_description']}: ${func['total_amount']:,.0f}")
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating NAV analytics: {e}")
            return {}
    
    async def run_broward_focus(self, year: str = None) -> Dict:
        """Run focused collection for Broward County"""
        if not year:
            year = str(datetime.now().year)
        
        logger.info(f"Starting Broward County focused NAV collection for {year}")
        return await self.run_annual_collection(year, [settings.BROWARD_COUNTY_CODE])
    
    async def run_once(self, task: str = 'annual', year: str = None, counties: List[str] = None):
        """Run a single task"""
        if task == 'annual':
            return await self.run_annual_collection(year, counties)
        elif task == 'analytics':
            return await self.run_analytics_report(counties, year)
        elif task == 'broward':
            return await self.run_broward_focus(year)
        else:
            logger.error(f"Unknown task: {task}")
            return {}
    
    def run_scheduled(self):
        """Run on schedule"""
        logger.info("Starting NAV Assessments worker with scheduled tasks...")
        
        # Schedule annual collection in February (after tax rolls are finalized)
        schedule.every().year.do(
            lambda: asyncio.run(self.run_annual_collection())
        )
        
        # Schedule quarterly analytics reports
        schedule.every(3).months.do(
            lambda: asyncio.run(self.run_analytics_report())
        )
        
        # Schedule monthly Broward County updates (high priority)
        schedule.every().month.do(
            lambda: asyncio.run(self.run_broward_focus())
        )
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
                
        except KeyboardInterrupt:
            logger.info("Shutting down NAV Assessments worker...")
            self.is_running = False

async def test_worker():
    """Test the worker with sample data"""
    worker = NAVAssessmentsWorker()
    
    try:
        logger.info("Testing NAV Assessments worker...")
        
        # Test Broward County collection
        result = await worker.run_once('broward', '2024')
        
        if result.get('success'):
            logger.info("✓ Broward County collection test completed")
            
            # Test analytics
            analytics = await worker.run_once('analytics', '2024', [settings.BROWARD_COUNTY_CODE])
            if analytics:
                logger.info("✓ Analytics test completed")
            else:
                logger.warning("Analytics test returned empty results")
        else:
            logger.error(f"Broward County collection test failed: {result.get('errors')}")
            
    except Exception as e:
        logger.error(f"Worker test failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Run test
            asyncio.run(test_worker())
        elif sys.argv[1] == "annual":
            # Run annual collection
            worker = NAVAssessmentsWorker()
            year = sys.argv[2] if len(sys.argv) > 2 else None
            counties = sys.argv[3].split(',') if len(sys.argv) > 3 else None
            asyncio.run(worker.run_once('annual', year, counties))
        elif sys.argv[1] == "analytics":
            # Run analytics
            worker = NAVAssessmentsWorker()
            year = sys.argv[2] if len(sys.argv) > 2 else None
            counties = sys.argv[3].split(',') if len(sys.argv) > 3 else None
            asyncio.run(worker.run_once('analytics', year, counties))
        elif sys.argv[1] == "broward":
            # Run Broward focus
            worker = NAVAssessmentsWorker()
            year = sys.argv[2] if len(sys.argv) > 2 else None
            asyncio.run(worker.run_once('broward', year))
        else:
            print("Usage: python worker.py [test|annual|analytics|broward|schedule] [year] [counties]")
    else:
        # Run scheduled worker
        worker = NAVAssessmentsWorker()
        worker.run_scheduled()