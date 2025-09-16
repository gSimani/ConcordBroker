#!/usr/bin/env python3
"""
Tax Deed Scheduler Integration
Integrates the Tax Deed Monitor with the existing Florida Scheduler
Provides automated scheduling and management of tax deed monitoring tasks
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from workers.florida_scheduler import FloridaScheduler, TaskPriority, TaskStatus, ScheduledTask
from workers.tax_deed_monitor import TaxDeedMonitor
from workers.alert_system import AlertSystem
from workers.supabase_config import SupabaseConfig

logger = logging.getLogger(__name__)

@dataclass
class TaxDeedMonitoringTask(ScheduledTask):
    """Specialized task for tax deed monitoring"""
    monitoring_type: str  # 'quick_check', 'deep_check', 'full_scan'
    county: str
    data_source: str
    check_interval: int  # seconds

class TaxDeedSchedulerIntegration:
    """Integrates tax deed monitoring with the main scheduler"""
    
    def __init__(self):
        self.scheduler = None
        self.monitor = None
        self.alert_system = None
        self.supabase = SupabaseConfig().client
        self.monitoring_tasks = {}
        self.performance_metrics = {
            'checks_performed': 0,
            'changes_detected': 0,
            'alerts_sent': 0,
            'errors_encountered': 0,
            'last_performance_report': datetime.now()
        }
        
    async def initialize(self):
        """Initialize the integration system"""
        try:
            # Initialize components
            self.scheduler = FloridaScheduler()
            self.monitor = TaxDeedMonitor()
            self.alert_system = AlertSystem()
            
            # Initialize all components
            await self.scheduler.initialize()
            await self.monitor.initialize()
            await self.alert_system.initialize()
            
            # Register tax deed monitoring tasks
            await self._register_monitoring_tasks()
            
            logger.info("Tax Deed Scheduler Integration initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Tax Deed Scheduler Integration: {e}")
            raise
    
    async def _register_monitoring_tasks(self):
        """Register all tax deed monitoring tasks with the scheduler"""
        try:
            # Get data sources from database
            data_sources = await self._get_data_sources()
            
            for source in data_sources:
                # Register quick check tasks (frequent)
                quick_check_task = TaxDeedMonitoringTask(
                    task_id=f"tax_deed_quick_{source['county']}_{source['source_name']}",
                    name=f"Tax Deed Quick Check - {source['county'].title()}",
                    description=f"Quick status check for {source['county']} tax deed auctions",
                    priority=TaskPriority.HIGH,
                    status=TaskStatus.SCHEDULED,
                    func=self._execute_quick_check,
                    schedule_type='interval',
                    interval_seconds=source['update_frequency'],
                    monitoring_type='quick_check',
                    county=source['county'],
                    data_source=source['source_name'],
                    check_interval=source['update_frequency'],
                    retry_count=3,
                    timeout_seconds=120
                )
                
                # Register deep check tasks (less frequent)
                deep_check_task = TaxDeedMonitoringTask(
                    task_id=f"tax_deed_deep_{source['county']}_{source['source_name']}",
                    name=f"Tax Deed Deep Check - {source['county'].title()}",
                    description=f"Deep content scan for {source['county']} tax deed auctions",
                    priority=TaskPriority.NORMAL,
                    status=TaskStatus.SCHEDULED,
                    func=self._execute_deep_check,
                    schedule_type='interval',
                    interval_seconds=source['update_frequency'] * 10,  # 10x less frequent
                    monitoring_type='deep_check',
                    county=source['county'],
                    data_source=source['source_name'],
                    check_interval=source['update_frequency'] * 10,
                    retry_count=2,
                    timeout_seconds=300
                )
                
                # Register full scan tasks (daily)
                full_scan_task = TaxDeedMonitoringTask(
                    task_id=f"tax_deed_full_{source['county']}_{source['source_name']}",
                    name=f"Tax Deed Full Scan - {source['county'].title()}",
                    description=f"Complete data scan for {source['county']} tax deed auctions",
                    priority=TaskPriority.LOW,
                    status=TaskStatus.SCHEDULED,
                    func=self._execute_full_scan,
                    schedule_type='cron',
                    cron_expression='0 2 * * *',  # Daily at 2 AM
                    monitoring_type='full_scan',
                    county=source['county'],
                    data_source=source['source_name'],
                    check_interval=86400,  # 24 hours
                    retry_count=3,
                    timeout_seconds=1800  # 30 minutes
                )
                
                # Add tasks to scheduler
                await self.scheduler.add_task(quick_check_task)
                await self.scheduler.add_task(deep_check_task)
                await self.scheduler.add_task(full_scan_task)
                
                # Store in local registry
                self.monitoring_tasks[source['county']] = {
                    'quick_check': quick_check_task,
                    'deep_check': deep_check_task,
                    'full_scan': full_scan_task,
                    'source_config': source
                }
                
            logger.info(f"Registered {len(data_sources) * 3} tax deed monitoring tasks")
            
        except Exception as e:
            logger.error(f"Failed to register monitoring tasks: {e}")
            raise
    
    async def _get_data_sources(self) -> List[Dict]:
        """Get active data sources from database"""
        try:
            result = await self.supabase.table('tax_deed_data_sources').select('*').eq('active', True).execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to get data sources: {e}")
            # Return default sources if database query fails
            return [
                {
                    'county': 'broward',
                    'source_name': 'broward_deed_auction',
                    'source_type': 'web_scraping',
                    'update_frequency': 30
                }
            ]
    
    async def _execute_quick_check(self, task: TaxDeedMonitoringTask) -> Dict[str, Any]:
        """Execute quick status check"""
        try:
            start_time = datetime.now()
            
            # Update monitoring status
            await self._update_monitoring_status(
                f"tax_deed_quick_{task.county}",
                'running',
                last_check=start_time
            )
            
            # Perform quick check
            changes_detected = 0
            if task.county == 'broward':
                await self.monitor._check_broward_status()
                changes_detected = len(self.monitor.auction_cache)  # Simplified for now
            
            # Update metrics
            self.performance_metrics['checks_performed'] += 1
            self.performance_metrics['changes_detected'] += changes_detected
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update monitoring status
            await self._update_monitoring_status(
                f"tax_deed_quick_{task.county}",
                'completed',
                checks_performed=self.performance_metrics['checks_performed'],
                changes_detected=changes_detected,
                performance_metrics={'execution_time': execution_time}
            )
            
            return {
                'status': 'success',
                'changes_detected': changes_detected,
                'execution_time': execution_time,
                'county': task.county
            }
            
        except Exception as e:
            logger.error(f"Quick check failed for {task.county}: {e}")
            
            # Update error status
            await self._update_monitoring_status(
                f"tax_deed_quick_{task.county}",
                'error',
                errors_encountered=self.performance_metrics['errors_encountered'] + 1
            )
            
            # Send error alert
            await self.alert_system.send_alert(
                'system_error',
                f'Tax Deed Quick Check Failed - {task.county.title()}',
                f'Quick check failed for {task.county}: {str(e)}',
                {'county': task.county, 'error': str(e)},
                'high'
            )
            
            raise
    
    async def _execute_deep_check(self, task: TaxDeedMonitoringTask) -> Dict[str, Any]:
        """Execute deep content check"""
        try:
            start_time = datetime.now()
            
            # Update monitoring status
            await self._update_monitoring_status(
                f"tax_deed_deep_{task.county}",
                'running',
                last_deep_check=start_time
            )
            
            # Perform deep check
            changes_detected = 0
            if task.county == 'broward':
                await self.monitor._deep_content_check()
                changes_detected = len(self.monitor.item_cache)  # Simplified for now
            
            # Update metrics
            self.performance_metrics['changes_detected'] += changes_detected
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update monitoring status
            await self._update_monitoring_status(
                f"tax_deed_deep_{task.county}",
                'completed',
                changes_detected=changes_detected,
                performance_metrics={'execution_time': execution_time}
            )
            
            return {
                'status': 'success',
                'changes_detected': changes_detected,
                'execution_time': execution_time,
                'county': task.county
            }
            
        except Exception as e:
            logger.error(f"Deep check failed for {task.county}: {e}")
            
            # Update error status
            await self._update_monitoring_status(
                f"tax_deed_deep_{task.county}",
                'error',
                errors_encountered=self.performance_metrics['errors_encountered'] + 1
            )
            
            raise
    
    async def _execute_full_scan(self, task: TaxDeedMonitoringTask) -> Dict[str, Any]:
        """Execute full data scan"""
        try:
            start_time = datetime.now()
            
            # Update monitoring status
            await self._update_monitoring_status(
                f"tax_deed_full_{task.county}",
                'running',
                last_deep_check=start_time
            )
            
            # Perform full scan
            changes_detected = 0
            if task.county == 'broward':
                await self.monitor._full_broward_scan()
                changes_detected = len(self.monitor.auction_cache) + len(self.monitor.item_cache)
            
            # Update metrics
            self.performance_metrics['changes_detected'] += changes_detected
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Generate daily report
            if execution_time > 0:  # Successful completion
                await self._generate_daily_report(task.county)
            
            # Update monitoring status
            await self._update_monitoring_status(
                f"tax_deed_full_{task.county}",
                'completed',
                changes_detected=changes_detected,
                performance_metrics={'execution_time': execution_time}
            )
            
            return {
                'status': 'success',
                'changes_detected': changes_detected,
                'execution_time': execution_time,
                'county': task.county
            }
            
        except Exception as e:
            logger.error(f"Full scan failed for {task.county}: {e}")
            
            # Update error status
            await self._update_monitoring_status(
                f"tax_deed_full_{task.county}",
                'error',
                errors_encountered=self.performance_metrics['errors_encountered'] + 1
            )
            
            raise
    
    async def _update_monitoring_status(self, monitor_name: str, status: str, **kwargs):
        """Update monitoring status in database"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            # Add optional fields
            for key, value in kwargs.items():
                if value is not None:
                    update_data[key] = value
            
            # Upsert status
            result = await self.supabase.table('tax_deed_monitoring_status').upsert(
                {**update_data, 'monitor_name': monitor_name},
                on_conflict='monitor_name'
            ).execute()
            
        except Exception as e:
            logger.error(f"Failed to update monitoring status: {e}")
    
    async def _generate_daily_report(self, county: str):
        """Generate daily monitoring report"""
        try:
            # Get recent changes
            changes_result = await self.supabase.table('tax_deed_changes').select('*').gte(
                'detected_at',
                (datetime.now() - timedelta(days=1)).isoformat()
            ).execute()
            
            changes = changes_result.data
            
            # Get monitoring status
            status_result = await self.supabase.table('tax_deed_monitoring_status').select('*').ilike(
                'monitor_name',
                f'%{county}%'
            ).execute()
            
            statuses = status_result.data
            
            # Generate report
            report = {
                'date': datetime.now().date().isoformat(),
                'county': county,
                'total_changes': len(changes),
                'critical_changes': len([c for c in changes if c.get('priority', 3) <= 2]),
                'monitoring_status': statuses,
                'change_types': {}
            }
            
            # Count change types
            for change in changes:
                change_type = change.get('change_type', 'unknown')
                report['change_types'][change_type] = report['change_types'].get(change_type, 0) + 1
            
            # Send daily report
            await self.alert_system.send_alert(
                'daily_report',
                f'Daily Tax Deed Report - {county.title()}',
                f'Daily monitoring report for {county}:\n'
                f'• Total changes: {report["total_changes"]}\n'
                f'• Critical changes: {report["critical_changes"]}\n'
                f'• Most common change: {max(report["change_types"].items(), key=lambda x: x[1])[0] if report["change_types"] else "None"}',
                report,
                'normal'
            )
            
        except Exception as e:
            logger.error(f"Failed to generate daily report for {county}: {e}")
    
    async def start_monitoring(self):
        """Start the integrated monitoring system"""
        try:
            logger.info("Starting Tax Deed integrated monitoring...")
            
            # Start the scheduler (which will run our monitoring tasks)
            await self.scheduler.start()
            
        except Exception as e:
            logger.error(f"Failed to start integrated monitoring: {e}")
            raise
    
    async def stop_monitoring(self):
        """Stop the integrated monitoring system"""
        try:
            logger.info("Stopping Tax Deed integrated monitoring...")
            
            # Stop scheduler
            if self.scheduler:
                await self.scheduler.stop()
            
            # Stop monitor
            if self.monitor:
                await self.monitor.stop_monitoring()
            
        except Exception as e:
            logger.error(f"Failed to stop integrated monitoring: {e}")
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        try:
            # Get database status
            result = await self.supabase.table('tax_deed_monitoring_status').select('*').execute()
            statuses = result.data
            
            # Get recent changes
            changes_result = await self.supabase.table('tax_deed_changes').select('*').gte(
                'detected_at',
                (datetime.now() - timedelta(hours=24)).isoformat()
            ).execute()
            
            recent_changes = changes_result.data
            
            return {
                'monitoring_active': len(statuses) > 0,
                'active_monitors': len([s for s in statuses if s['status'] == 'running']),
                'total_monitors': len(statuses),
                'recent_changes_24h': len(recent_changes),
                'critical_changes_24h': len([c for c in recent_changes if c.get('priority', 3) <= 2]),
                'last_update': max([s['updated_at'] for s in statuses]) if statuses else None,
                'performance_metrics': self.performance_metrics,
                'monitor_details': statuses
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring status: {e}")
            return {'error': str(e)}

# Main execution
async def main():
    """Main function for running the integrated monitoring system"""
    integration = TaxDeedSchedulerIntegration()
    
    try:
        await integration.initialize()
        await integration.start_monitoring()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(60)
            
            # Print status every hour
            status = await integration.get_monitoring_status()
            logger.info(f"Monitoring Status: {status['active_monitors']}/{status['total_monitors']} active, "
                       f"{status['recent_changes_24h']} changes in 24h")
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
    finally:
        await integration.stop_monitoring()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())