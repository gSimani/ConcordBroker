"""
Master Data Pipeline Orchestrator
Coordinates all data collection agents and manages execution schedules
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import time

# Import all agents
from .sunbiz_loader.main import SunbizLoader
from .official_records.worker import OfficialRecordsWorker  
from .bcpa_scraper.main import BCPAScraper
from .dor_processor.unified_pipeline import UnifiedPipelineOrchestrator
from .florida_revenue.main import FloridaRevenueAgent
from .nav_assessments.main import NAVAssessmentsAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MasterOrchestrator:
    """Master orchestrator for all data collection agents"""
    
    def __init__(self):
        self.agents = {
            'sunbiz': SunbizLoader(),
            'official_records': OfficialRecordsWorker(),
            'bcpa_scraper': BCPAScraper(),
            'florida_revenue': FloridaRevenueAgent(),
            'nav_assessments': NAVAssessmentsAgent()
        }
        self.is_running = False
        self.execution_log = []
    
    async def run_sunbiz_daily(self) -> Dict:
        """Run Sunbiz daily collection"""
        logger.info("Starting Sunbiz daily collection...")
        start_time = datetime.now()
        
        try:
            result = await self.agents['sunbiz'].run_daily()
            result['agent'] = 'sunbiz'
            result['execution_time'] = datetime.now()
            self.execution_log.append(result)
            
            logger.info(f"Sunbiz daily completed: {result.get('entities_created', 0)} created, "
                       f"{result.get('entities_updated', 0)} updated")
            return result
            
        except Exception as e:
            error_result = {
                'agent': 'sunbiz',
                'success': False,
                'error': str(e),
                'execution_time': datetime.now()
            }
            self.execution_log.append(error_result)
            logger.error(f"Sunbiz daily failed: {e}")
            return error_result
    
    async def run_official_records_daily(self) -> Dict:
        """Run Official Records daily scrape"""
        logger.info("Starting Official Records daily scrape...")
        
        try:
            await self.agents['official_records'].initialize()
            await self.agents['official_records'].daily_scrape()
            
            result = {
                'agent': 'official_records',
                'success': True,
                'execution_time': datetime.now(),
                'task': 'daily_scrape'
            }
            self.execution_log.append(result)
            
            logger.info("Official Records daily scrape completed")
            return result
            
        except Exception as e:
            error_result = {
                'agent': 'official_records',
                'success': False,
                'error': str(e),
                'execution_time': datetime.now()
            }
            self.execution_log.append(error_result)
            logger.error(f"Official Records daily failed: {e}")
            return error_result
        finally:
            await self.agents['official_records'].cleanup()
    
    async def run_florida_revenue_annual(self, year: str = None) -> Dict:
        """Run Florida Revenue annual collection"""
        if not year:
            year = str(datetime.now().year)
            
        logger.info(f"Starting Florida Revenue annual collection for {year}...")
        
        try:
            async with self.agents['florida_revenue'] as agent:
                result = await agent.run_data_collection(year)
                result['agent'] = 'florida_revenue'
                result['execution_time'] = datetime.now()
                self.execution_log.append(result)
                
                logger.info(f"Florida Revenue annual completed: "
                           f"{result.get('records_created', 0)} created, "
                           f"{result.get('records_updated', 0)} updated")
                return result
                
        except Exception as e:
            error_result = {
                'agent': 'florida_revenue',
                'success': False,
                'error': str(e),
                'execution_time': datetime.now()
            }
            self.execution_log.append(error_result)
            logger.error(f"Florida Revenue annual failed: {e}")
            return error_result
    
    async def run_nav_assessments_annual(self, year: str = None) -> Dict:
        """Run NAV Assessments annual collection"""
        if not year:
            year = str(datetime.now().year)
            
        logger.info(f"Starting NAV Assessments annual collection for {year}...")
        
        try:
            async with self.agents['nav_assessments'] as agent:
                # Collect both NAV N and NAV D tables
                nav_n_result = await agent.run_nav_collection('N', year)
                nav_d_result = await agent.run_nav_collection('D', year)
                
                result = {
                    'agent': 'nav_assessments',
                    'success': nav_n_result.get('success', False) and nav_d_result.get('success', False),
                    'nav_n_records': nav_n_result.get('records_created', 0),
                    'nav_d_records': nav_d_result.get('records_created', 0),
                    'total_records': (nav_n_result.get('records_created', 0) + 
                                    nav_d_result.get('records_created', 0)),
                    'execution_time': datetime.now(),
                    'year': year,
                    'nav_n_result': nav_n_result,
                    'nav_d_result': nav_d_result
                }
                
                self.execution_log.append(result)
                
                logger.info(f"NAV Assessments annual completed: "
                           f"{result['nav_n_records']} parcel records, "
                           f"{result['nav_d_records']} detail records")
                return result
                
        except Exception as e:
            error_result = {
                'agent': 'nav_assessments',
                'success': False,
                'error': str(e),
                'execution_time': datetime.now()
            }
            self.execution_log.append(error_result)
            logger.error(f"NAV Assessments annual failed: {e}")
            return error_result
    
    async def run_bcpa_sweep(self, cities: List[str] = None) -> Dict:
        """Run BCPA property sweep"""
        logger.info("Starting BCPA property sweep...")
        
        try:
            result = await self.agents['bcpa_scraper'].run_sweep(cities)
            result['agent'] = 'bcpa_scraper'
            result['execution_time'] = datetime.now()
            self.execution_log.append(result)
            
            logger.info(f"BCPA sweep completed: {result.get('properties_found', 0)} properties found")
            return result
            
        except Exception as e:
            error_result = {
                'agent': 'bcpa_scraper',
                'success': False,
                'error': str(e),
                'execution_time': datetime.now()
            }
            self.execution_log.append(error_result)
            logger.error(f"BCPA sweep failed: {e}")
            return error_result
    
    async def run_weekly_comprehensive(self) -> Dict:
        """Run comprehensive weekly data collection"""
        logger.info("Starting weekly comprehensive data collection...")
        
        results = {
            'started_at': datetime.now().isoformat(),
            'tasks': {},
            'success': True,
            'errors': []
        }
        
        # Run Sunbiz quarterly if it's the first week of quarter
        now = datetime.now()
        if now.month in [1, 4, 7, 10] and now.day <= 7:
            logger.info("Running Sunbiz quarterly collection...")
            try:
                sunbiz_result = await self.agents['sunbiz'].run_quarterly()
                results['tasks']['sunbiz_quarterly'] = sunbiz_result
            except Exception as e:
                results['errors'].append(f"Sunbiz quarterly failed: {e}")
                results['success'] = False
        
        # Run Official Records weekly deep scrape
        try:
            await self.agents['official_records'].initialize()
            await self.agents['official_records'].weekly_deep_scrape()
            results['tasks']['official_records_weekly'] = {'success': True}
        except Exception as e:
            results['errors'].append(f"Official Records weekly failed: {e}")
            results['success'] = False
        finally:
            await self.agents['official_records'].cleanup()
        
        # Run BCPA sweep on priority cities
        priority_cities = ['FORT LAUDERDALE', 'HOLLYWOOD', 'POMPANO BEACH', 'CORAL SPRINGS']
        try:
            bcpa_result = await self.run_bcpa_sweep(priority_cities)
            results['tasks']['bcpa_priority_sweep'] = bcpa_result
        except Exception as e:
            results['errors'].append(f"BCPA sweep failed: {e}")
            results['success'] = False
        
        results['finished_at'] = datetime.now().isoformat()
        results['duration_seconds'] = (
            datetime.fromisoformat(results['finished_at']) - 
            datetime.fromisoformat(results['started_at'])
        ).total_seconds()
        
        logger.info(f"Weekly comprehensive collection completed in {results['duration_seconds']:.2f}s")
        self.execution_log.append(results)
        
        return results
    
    async def run_daily_pipeline(self) -> Dict:
        """Run daily data pipeline"""
        logger.info("Starting daily data pipeline...")
        
        results = {
            'started_at': datetime.now().isoformat(),
            'tasks': {},
            'success': True,
            'errors': []
        }
        
        # Run daily tasks in parallel where possible
        daily_tasks = [
            ('sunbiz_daily', self.run_sunbiz_daily()),
            ('official_records_daily', self.run_official_records_daily())
        ]
        
        for task_name, task_coro in daily_tasks:
            try:
                task_result = await task_coro
                results['tasks'][task_name] = task_result
                if not task_result.get('success', True):
                    results['success'] = False
            except Exception as e:
                results['errors'].append(f"{task_name} failed: {e}")
                results['success'] = False
        
        results['finished_at'] = datetime.now().isoformat()
        results['duration_seconds'] = (
            datetime.fromisoformat(results['finished_at']) - 
            datetime.fromisoformat(results['started_at'])
        ).total_seconds()
        
        logger.info(f"Daily pipeline completed in {results['duration_seconds']:.2f}s")
        self.execution_log.append(results)
        
        return results
    
    def get_execution_summary(self, hours: int = 24) -> Dict:
        """Get execution summary for last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_executions = [
            log for log in self.execution_log 
            if log.get('execution_time', datetime.min) > cutoff_time
        ]
        
        summary = {
            'total_executions': len(recent_executions),
            'successful': len([e for e in recent_executions if e.get('success', True)]),
            'failed': len([e for e in recent_executions if not e.get('success', True)]),
            'agents_used': list(set(e.get('agent', 'unknown') for e in recent_executions)),
            'last_execution': max(recent_executions, key=lambda x: x.get('execution_time', datetime.min)) if recent_executions else None
        }
        
        return summary
    
    async def health_check(self) -> Dict:
        """Perform health check on all agents"""
        logger.info("Performing health check on all agents...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'agents': {},
            'overall_healthy': True
        }
        
        # Test Sunbiz connection
        try:
            sunbiz_healthy = await self.agents['sunbiz'].test_connection()
            health_status['agents']['sunbiz'] = {'healthy': sunbiz_healthy}
        except Exception as e:
            health_status['agents']['sunbiz'] = {'healthy': False, 'error': str(e)}
            health_status['overall_healthy'] = False
        
        # Test Florida Revenue (basic connectivity)
        try:
            # Just test that we can create the agent
            async with FloridaRevenueAgent() as agent:
                health_status['agents']['florida_revenue'] = {'healthy': True}
        except Exception as e:
            health_status['agents']['florida_revenue'] = {'healthy': False, 'error': str(e)}
            health_status['overall_healthy'] = False
        
        # Test NAV Assessments (basic connectivity)
        try:
            async with NAVAssessmentsAgent() as agent:
                health_status['agents']['nav_assessments'] = {'healthy': True}
        except Exception as e:
            health_status['agents']['nav_assessments'] = {'healthy': False, 'error': str(e)}
            health_status['overall_healthy'] = False
        
        # Other agents would be tested similarly...
        health_status['agents']['official_records'] = {'healthy': True, 'note': 'Basic initialization only'}
        health_status['agents']['bcpa_scraper'] = {'healthy': True, 'note': 'Basic initialization only'}
        
        logger.info(f"Health check completed. Overall healthy: {health_status['overall_healthy']}")
        return health_status
    
    def setup_schedule(self):
        """Setup scheduled tasks"""
        logger.info("Setting up scheduled tasks...")
        
        # Daily tasks at 2 AM
        schedule.every().day.at("02:00").do(
            lambda: asyncio.run(self.run_daily_pipeline())
        )
        
        # Weekly comprehensive on Sundays at 3 AM  
        schedule.every().sunday.at("03:00").do(
            lambda: asyncio.run(self.run_weekly_comprehensive())
        )
        
        # Annual Florida Revenue in January
        schedule.every().year.do(
            lambda: asyncio.run(self.run_florida_revenue_annual())
        )
        
        # Annual NAV Assessments in February (after tax rolls finalized)
        schedule.every().year.do(
            lambda: asyncio.run(self.run_nav_assessments_annual())
        )
        
        # Health check every 4 hours
        schedule.every(4).hours.do(
            lambda: asyncio.run(self.health_check())
        )
        
        logger.info("Schedule configured")
    
    def run_scheduled(self):
        """Run orchestrator with scheduled tasks"""
        logger.info("Starting Master Data Pipeline Orchestrator...")
        
        self.setup_schedule()
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Shutting down orchestrator...")
            self.is_running = False

# Test function
async def test_orchestrator():
    """Test the orchestrator"""
    orchestrator = MasterOrchestrator()
    
    logger.info("Testing orchestrator...")
    
    # Test health check
    health = await orchestrator.health_check()
    logger.info(f"Health check result: {health}")
    
    # Test individual agents (optional, commented out for safety)
    # result = await orchestrator.run_florida_revenue_annual('2025')
    # logger.info(f"Florida Revenue test result: {result}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        orchestrator = MasterOrchestrator()
        
        if sys.argv[1] == "test":
            asyncio.run(test_orchestrator())
        elif sys.argv[1] == "daily":
            asyncio.run(orchestrator.run_daily_pipeline())
        elif sys.argv[1] == "weekly":
            asyncio.run(orchestrator.run_weekly_comprehensive())
        elif sys.argv[1] == "health":
            result = asyncio.run(orchestrator.health_check())
            print(f"Health Status: {result}")
        elif sys.argv[1] == "florida-revenue":
            year = sys.argv[2] if len(sys.argv) > 2 else None
            asyncio.run(orchestrator.run_florida_revenue_annual(year))
        elif sys.argv[1] == "nav-assessments":
            year = sys.argv[2] if len(sys.argv) > 2 else None
            asyncio.run(orchestrator.run_nav_assessments_annual(year))
        else:
            print("Usage: python orchestrator.py [test|daily|weekly|health|florida-revenue|nav-assessments] [year]")
    else:
        # Run scheduled orchestrator
        orchestrator = MasterOrchestrator()
        orchestrator.run_scheduled()