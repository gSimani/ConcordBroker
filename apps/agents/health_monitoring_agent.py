#!/usr/bin/env python3
"""
Health Monitoring Agent - Continuous system health monitoring and recovery
Monitors database, API, agents, and triggers recovery actions
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
import psutil
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthMetric:
    name: str
    status: HealthStatus
    value: Any
    threshold: Optional[float] = None
    message: Optional[str] = None
    last_checked: datetime = None
    
    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.now()

class HealthMonitoringAgent:
    """
    Comprehensive health monitoring with automated recovery
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
        
        self.api_url = f"{self.supabase_url}/rest/v1" if self.supabase_url else None
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        } if self.supabase_key else {}
        
        # Health metrics storage
        self.metrics: Dict[str, HealthMetric] = {}
        self.alerts_sent: List[Dict] = []
        
        # Monitoring configuration
        self.checks = {
            'database_connectivity': {
                'interval': 300,  # 5 minutes
                'timeout': 10,
                'critical': True
            },
            'api_responsiveness': {
                'interval': 600,  # 10 minutes
                'timeout': 5,
                'critical': True
            },
            'data_freshness': {
                'interval': 3600,  # 1 hour
                'timeout': 30,
                'critical': False
            },
            'system_resources': {
                'interval': 300,  # 5 minutes
                'timeout': 5,
                'critical': False
            },
            'disk_space': {
                'interval': 1800,  # 30 minutes  
                'timeout': 5,
                'critical': True
            },
            'agent_health': {
                'interval': 900,  # 15 minutes
                'timeout': 10,
                'critical': False
            }
        }

    async def run(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main health monitoring cycle"""
        logger.info("HealthMonitoringAgent starting health checks...")
        
        try:
            # Run all health checks
            results = await self._run_all_checks()
            
            # Analyze results and trigger alerts
            await self._analyze_health_results(results)
            
            # Save health report
            await self._save_health_report(results)
            
            # Determine overall status
            overall_status = self._get_overall_status(results)
            
            return {
                'status': 'success',
                'overall_health': overall_status.value,
                'checks_performed': len(results),
                'critical_issues': sum(1 for r in results.values() if r.status == HealthStatus.CRITICAL),
                'warnings': sum(1 for r in results.values() if r.status == HealthStatus.WARNING)
            }
            
        except Exception as e:
            logger.error(f"Health monitoring failed: {e}")
            return {'status': 'error', 'error': str(e)}

    async def _run_all_checks(self) -> Dict[str, HealthMetric]:
        """Run all configured health checks"""
        results = {}
        
        # Run checks concurrently
        tasks = []
        for check_name, config in self.checks.items():
            task = asyncio.create_task(self._run_check(check_name, config))
            tasks.append((check_name, task))
        
        # Collect results
        for check_name, task in tasks:
            try:
                result = await task
                results[check_name] = result
                self.metrics[check_name] = result
            except Exception as e:
                logger.error(f"Check {check_name} failed: {e}")
                results[check_name] = HealthMetric(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    value=None,
                    message=f"Check failed: {str(e)}"
                )
        
        return results

    async def _run_check(self, check_name: str, config: Dict) -> HealthMetric:
        """Run a specific health check"""
        try:
            timeout = config.get('timeout', 10)
            
            if check_name == 'database_connectivity':
                return await asyncio.wait_for(self._check_database_connectivity(), timeout)
            elif check_name == 'api_responsiveness':
                return await asyncio.wait_for(self._check_api_responsiveness(), timeout)
            elif check_name == 'data_freshness':
                return await asyncio.wait_for(self._check_data_freshness(), timeout)
            elif check_name == 'system_resources':
                return await asyncio.wait_for(self._check_system_resources(), timeout)
            elif check_name == 'disk_space':
                return await asyncio.wait_for(self._check_disk_space(), timeout)
            elif check_name == 'agent_health':
                return await asyncio.wait_for(self._check_agent_health(), timeout)
            else:
                return HealthMetric(
                    name=check_name,
                    status=HealthStatus.UNKNOWN,
                    value=None,
                    message="Unknown check type"
                )
                
        except asyncio.TimeoutError:
            return HealthMetric(
                name=check_name,
                status=HealthStatus.CRITICAL,
                value=None,
                message=f"Check timed out after {timeout}s"
            )

    async def _check_database_connectivity(self) -> HealthMetric:
        """Check database connectivity and basic operations"""
        if not self.api_url:
            return HealthMetric(
                name='database_connectivity',
                status=HealthStatus.CRITICAL,
                value=False,
                message="No database configuration found"
            )
        
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test basic connectivity
                async with session.get(
                    f"{self.api_url}/fl_nal_name_address?select=count&limit=1",
                    headers=self.headers
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status == 200:
                        return HealthMetric(
                            name='database_connectivity',
                            status=HealthStatus.HEALTHY,
                            value=response_time,
                            threshold=5.0,
                            message=f"Database responsive in {response_time:.2f}s"
                        )
                    else:
                        return HealthMetric(
                            name='database_connectivity',
                            status=HealthStatus.CRITICAL,
                            value=response.status,
                            message=f"Database returned status {response.status}"
                        )
                        
        except Exception as e:
            return HealthMetric(
                name='database_connectivity',
                status=HealthStatus.CRITICAL,
                value=None,
                message=f"Database connection failed: {str(e)}"
            )

    async def _check_api_responsiveness(self) -> HealthMetric:
        """Check API endpoint responsiveness"""
        try:
            # Test local API if available
            start_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get('http://localhost:8000/api/health') as response:
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        if response.status == 200:
                            status = HealthStatus.HEALTHY if response_time < 2.0 else HealthStatus.WARNING
                            return HealthMetric(
                                name='api_responsiveness',
                                status=status,
                                value=response_time,
                                threshold=2.0,
                                message=f"API responded in {response_time:.2f}s"
                            )
                        else:
                            return HealthMetric(
                                name='api_responsiveness',
                                status=HealthStatus.WARNING,
                                value=response.status,
                                message=f"API returned status {response.status}"
                            )
                            
                except aiohttp.ClientConnectorError:
                    return HealthMetric(
                        name='api_responsiveness',
                        status=HealthStatus.WARNING,
                        value=None,
                        message="Local API not running"
                    )
                    
        except Exception as e:
            return HealthMetric(
                name='api_responsiveness',
                status=HealthStatus.WARNING,
                value=None,
                message=f"API check failed: {str(e)}"
            )

    async def _check_data_freshness(self) -> HealthMetric:
        """Check if data is fresh and up to date"""
        try:
            # Check when data was last updated
            log_files = list(Path('logs').glob('*.log')) if Path('logs').exists() else []
            
            if not log_files:
                return HealthMetric(
                    name='data_freshness',
                    status=HealthStatus.WARNING,
                    value=None,
                    message="No log files found to check freshness"
                )
            
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            last_update = datetime.fromtimestamp(latest_log.stat().st_mtime)
            age_hours = (datetime.now() - last_update).total_seconds() / 3600
            
            if age_hours < 24:
                status = HealthStatus.HEALTHY
            elif age_hours < 72:
                status = HealthStatus.WARNING  
            else:
                status = HealthStatus.CRITICAL
            
            return HealthMetric(
                name='data_freshness',
                status=status,
                value=age_hours,
                threshold=24.0,
                message=f"Data last updated {age_hours:.1f} hours ago"
            )
            
        except Exception as e:
            return HealthMetric(
                name='data_freshness',
                status=HealthStatus.WARNING,
                value=None,
                message=f"Unable to check data freshness: {str(e)}"
            )

    async def _check_system_resources(self) -> HealthMetric:
        """Check system resource utilization"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Determine status based on resource usage
            if cpu_percent > 90 or memory_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"High resource usage: CPU {cpu_percent}%, Memory {memory_percent}%"
            elif cpu_percent > 70 or memory_percent > 70:
                status = HealthStatus.WARNING
                message = f"Moderate resource usage: CPU {cpu_percent}%, Memory {memory_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Normal resource usage: CPU {cpu_percent}%, Memory {memory_percent}%"
            
            return HealthMetric(
                name='system_resources',
                status=status,
                value={'cpu': cpu_percent, 'memory': memory_percent},
                threshold=70.0,
                message=message
            )
            
        except Exception as e:
            return HealthMetric(
                name='system_resources',
                status=HealthStatus.WARNING,
                value=None,
                message=f"Unable to check system resources: {str(e)}"
            )

    async def _check_disk_space(self) -> HealthMetric:
        """Check available disk space"""
        try:
            disk_usage = psutil.disk_usage('.')
            used_percent = (disk_usage.used / disk_usage.total) * 100
            free_gb = disk_usage.free / (1024**3)
            
            if used_percent > 95 or free_gb < 1:
                status = HealthStatus.CRITICAL
            elif used_percent > 85 or free_gb < 5:
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.HEALTHY
            
            return HealthMetric(
                name='disk_space',
                status=status,
                value={'used_percent': used_percent, 'free_gb': free_gb},
                threshold=85.0,
                message=f"Disk usage: {used_percent:.1f}%, {free_gb:.1f}GB free"
            )
            
        except Exception as e:
            return HealthMetric(
                name='disk_space',
                status=HealthStatus.WARNING,
                value=None,
                message=f"Unable to check disk space: {str(e)}"
            )

    async def _check_agent_health(self) -> HealthMetric:
        """Check health of other agents"""
        try:
            # Check if orchestrator log exists and is recent
            orchestrator_log = Path('logs/orchestrator.log')
            
            if not orchestrator_log.exists():
                return HealthMetric(
                    name='agent_health',
                    status=HealthStatus.WARNING,
                    value=None,
                    message="Orchestrator log not found"
                )
            
            # Check log age
            log_age = datetime.now() - datetime.fromtimestamp(orchestrator_log.stat().st_mtime)
            age_minutes = log_age.total_seconds() / 60
            
            if age_minutes < 30:
                status = HealthStatus.HEALTHY
                message = f"Agents active (log {age_minutes:.0f}min old)"
            elif age_minutes < 120:
                status = HealthStatus.WARNING
                message = f"Agents may be inactive (log {age_minutes:.0f}min old)"
            else:
                status = HealthStatus.CRITICAL
                message = f"Agents likely inactive (log {age_minutes:.0f}min old)"
            
            return HealthMetric(
                name='agent_health',
                status=status,
                value=age_minutes,
                threshold=30.0,
                message=message
            )
            
        except Exception as e:
            return HealthMetric(
                name='agent_health',
                status=HealthStatus.WARNING,
                value=None,
                message=f"Unable to check agent health: {str(e)}"
            )

    async def _analyze_health_results(self, results: Dict[str, HealthMetric]):
        """Analyze health results and trigger appropriate actions"""
        critical_issues = [r for r in results.values() if r.status == HealthStatus.CRITICAL]
        
        if critical_issues:
            await self._handle_critical_issues(critical_issues)
        
        # Check for patterns that might indicate problems
        warning_count = sum(1 for r in results.values() if r.status == HealthStatus.WARNING)
        if warning_count >= 3:
            await self._send_alert('Multiple Warning Conditions', 
                                 f"{warning_count} systems showing warnings")

    async def _handle_critical_issues(self, issues: List[HealthMetric]):
        """Handle critical health issues with automated recovery"""
        for issue in issues:
            logger.critical(f"CRITICAL: {issue.name} - {issue.message}")
            
            # Attempt automated recovery based on issue type
            if issue.name == 'database_connectivity':
                await self._attempt_database_recovery()
            elif issue.name == 'disk_space':
                await self._attempt_disk_cleanup()
            
            # Send alert
            await self._send_alert(f'CRITICAL: {issue.name}', issue.message or 'No details')

    async def _attempt_database_recovery(self):
        """Attempt automated database recovery"""
        logger.info("Attempting database recovery...")
        
        # Could implement:
        # - Connection pool reset
        # - Service restart
        # - Fallback database connection
        
        # For now, just log the attempt
        logger.info("Database recovery attempt logged")

    async def _attempt_disk_cleanup(self):
        """Attempt automated disk cleanup"""
        logger.info("Attempting disk cleanup...")
        
        try:
            # Clean old logs
            log_dir = Path('logs')
            if log_dir.exists():
                old_logs = [f for f in log_dir.glob('*.log') 
                           if (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days > 7]
                
                for log_file in old_logs:
                    log_file.unlink()
                    logger.info(f"Deleted old log: {log_file}")
        
        except Exception as e:
            logger.error(f"Disk cleanup failed: {e}")

    async def _send_alert(self, subject: str, message: str):
        """Send health alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'message': message,
            'agent': 'HealthMonitoringAgent'
        }
        
        self.alerts_sent.append(alert)
        logger.warning(f"ALERT: {subject} - {message}")
        
        # Save alert to file
        Path('logs').mkdir(exist_ok=True)
        with open('logs/health_alerts.log', 'a') as f:
            f.write(f"{json.dumps(alert)}\n")

    def _get_overall_status(self, results: Dict[str, HealthMetric]) -> HealthStatus:
        """Determine overall system health status"""
        if any(r.status == HealthStatus.CRITICAL for r in results.values()):
            return HealthStatus.CRITICAL
        elif any(r.status == HealthStatus.WARNING for r in results.values()):
            return HealthStatus.WARNING
        elif all(r.status == HealthStatus.HEALTHY for r in results.values()):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    async def _save_health_report(self, results: Dict[str, HealthMetric]):
        """Save comprehensive health report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._get_overall_status(results).value,
            'checks': {
                name: {
                    'status': metric.status.value,
                    'value': metric.value,
                    'message': metric.message,
                    'threshold': metric.threshold
                }
                for name, metric in results.items()
            },
            'alerts_sent_today': len([a for a in self.alerts_sent 
                                    if datetime.fromisoformat(a['timestamp']).date() == datetime.now().date()])
        }
        
        Path('logs').mkdir(exist_ok=True)
        with open('logs/health_report.json', 'w') as f:
            json.dump(report, f, indent=2)

    async def get_status(self) -> Dict[str, Any]:
        """Get current health monitoring status"""
        return {
            'agent': 'HealthMonitoringAgent',
            'last_check': max((m.last_checked for m in self.metrics.values()), default=None),
            'active_metrics': len(self.metrics),
            'recent_alerts': len(self.alerts_sent),
            'overall_health': self._get_overall_status(self.metrics).value if self.metrics else 'unknown'
        }