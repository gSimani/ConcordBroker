#!/usr/bin/env python3
"""
Master Orchestrator Agent - Central command for all ConcordBroker agents
Manages data loading, updates, monitoring, and recovery automatically
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import schedule
import time
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"

class Priority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class AgentTask:
    id: str
    agent_name: str
    task_type: str
    priority: Priority
    data: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    scheduled_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: AgentStatus = AgentStatus.IDLE
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class AgentConfig:
    name: str
    module_path: str
    description: str
    schedule_pattern: str  # cron-like pattern
    dependencies: List[str]  # other agents this depends on
    timeout_minutes: int = 30
    enabled: bool = True
    auto_retry: bool = True
    health_check_interval: int = 300  # seconds

class MasterOrchestrator:
    """
    Master agent that coordinates all other agents for seamless database updates
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self.task_queue: List[AgentTask] = []
        self.running_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[AgentTask] = []
        self.agent_statuses: Dict[str, AgentStatus] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Load agent configurations
        self._load_agent_configs()
        
        # Initialize monitoring
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'uptime_start': datetime.now(),
            'last_health_check': None,
            'database_status': 'unknown'
        }

    def _load_agent_configs(self):
        """Load agent configurations"""
        self.agents = {
            'data_loader': AgentConfig(
                name='data_loader',
                module_path='apps.agents.data_loader_agent',
                description='Loads Florida data into Supabase',
                schedule_pattern='0 2 * * 1',  # Monday 2 AM
                dependencies=[],
                timeout_minutes=120,
                auto_retry=True
            ),
            'florida_downloader': AgentConfig(
                name='florida_downloader', 
                module_path='apps.agents.florida_download_agent',
                description='Downloads latest Florida Revenue data',
                schedule_pattern='0 1 1 * *',  # 1st of month, 1 AM
                dependencies=[],
                timeout_minutes=60
            ),
            'sunbiz_sync': AgentConfig(
                name='sunbiz_sync',
                module_path='apps.agents.sunbiz_sync_agent', 
                description='Syncs Sunbiz business entity data',
                schedule_pattern='0 3 * * 0',  # Sunday 3 AM
                dependencies=['data_loader'],
                timeout_minutes=30
            ),
            'entity_matcher': AgentConfig(
                name='entity_matcher',
                module_path='apps.agents.entity_matching_agent',
                description='Matches properties to business entities',
                schedule_pattern='0 4 * * 1',  # Monday 4 AM
                dependencies=['data_loader', 'sunbiz_sync'],
                timeout_minutes=45
            ),
            'schema_migrator': AgentConfig(
                name='schema_migrator',
                module_path='apps.agents.schema_migration_agent',
                description='Handles database schema updates',
                schedule_pattern='0 0 * * *',  # Daily midnight
                dependencies=[],
                timeout_minutes=15
            ),
            'health_monitor': AgentConfig(
                name='health_monitor',
                module_path='apps.agents.health_monitoring_agent',
                description='Monitors system health and recovery',
                schedule_pattern='*/15 * * * *',  # Every 15 minutes
                dependencies=[],
                timeout_minutes=5,
                health_check_interval=900  # 15 minutes
            ),
            'backup_agent': AgentConfig(
                name='backup_agent',
                module_path='apps.agents.backup_recovery_agent',
                description='Performs database backups',
                schedule_pattern='0 6 * * *',  # Daily 6 AM
                dependencies=[],
                timeout_minutes=30
            )
        }

    async def add_task(self, task: AgentTask):
        """Add a task to the queue with priority ordering"""
        # Insert task based on priority
        inserted = False
        for i, existing_task in enumerate(self.task_queue):
            if task.priority.value < existing_task.priority.value:
                self.task_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.task_queue.append(task)
        
        logger.info(f"Added task {task.id} for agent {task.agent_name} with priority {task.priority.name}")

    async def process_task_queue(self):
        """Process tasks from queue"""
        while self.task_queue:
            task = self.task_queue.pop(0)
            
            # Check dependencies
            if not await self._check_dependencies(task):
                # Re-queue task for later
                task.scheduled_at = datetime.now() + timedelta(minutes=5)
                await self.add_task(task)
                continue
            
            # Execute task
            await self._execute_task(task)
            
            # Small delay to prevent overwhelming
            await asyncio.sleep(1)

    async def _check_dependencies(self, task: AgentTask) -> bool:
        """Check if task dependencies are satisfied"""
        agent_config = self.agents.get(task.agent_name)
        if not agent_config or not agent_config.dependencies:
            return True
        
        for dep in agent_config.dependencies:
            if self.agent_statuses.get(dep) != AgentStatus.SUCCESS:
                logger.info(f"Task {task.id} waiting for dependency {dep}")
                return False
        
        return True

    async def _execute_task(self, task: AgentTask):
        """Execute a specific task"""
        task.status = AgentStatus.RUNNING
        task.started_at = datetime.now()
        self.running_tasks[task.id] = task
        
        logger.info(f"Executing task {task.id} for agent {task.agent_name}")
        
        try:
            # Dynamic import and execution
            agent_config = self.agents[task.agent_name]
            
            # Import agent module dynamically
            module_parts = agent_config.module_path.split('.')
            module = __import__(agent_config.module_path, fromlist=[module_parts[-1]])
            
            # Get agent class (assume it follows naming convention)
            agent_class_name = ''.join(word.capitalize() for word in task.agent_name.split('_'))
            agent_class = getattr(module, agent_class_name)
            
            # Create and run agent
            agent_instance = agent_class()
            
            # Run with timeout
            result = await asyncio.wait_for(
                agent_instance.run(task.data),
                timeout=agent_config.timeout_minutes * 60
            )
            
            # Task completed successfully
            task.status = AgentStatus.SUCCESS
            task.completed_at = datetime.now()
            self.agent_statuses[task.agent_name] = AgentStatus.SUCCESS
            self.metrics['tasks_completed'] += 1
            
            logger.info(f"Task {task.id} completed successfully")
            
        except asyncio.TimeoutError:
            task.status = AgentStatus.FAILED
            task.error_message = f"Task timed out after {agent_config.timeout_minutes} minutes"
            await self._handle_task_failure(task)
            
        except Exception as e:
            task.status = AgentStatus.FAILED  
            task.error_message = str(e)
            await self._handle_task_failure(task)
        
        finally:
            task.completed_at = datetime.now()
            self.completed_tasks.append(task)
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

    async def _handle_task_failure(self, task: AgentTask):
        """Handle task failure with retry logic"""
        self.agent_statuses[task.agent_name] = AgentStatus.FAILED
        self.metrics['tasks_failed'] += 1
        
        logger.error(f"Task {task.id} failed: {task.error_message}")
        
        # Retry logic
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = AgentStatus.IDLE
            task.scheduled_at = datetime.now() + timedelta(minutes=5 * task.retry_count)
            
            await self.add_task(task)
            logger.info(f"Retrying task {task.id} (attempt {task.retry_count}/{task.max_retries})")
        else:
            logger.error(f"Task {task.id} failed permanently after {task.max_retries} retries")
            
            # Send alert for critical failures
            if task.priority == Priority.CRITICAL:
                await self._send_alert(f"CRITICAL: Task {task.id} failed permanently", task.error_message)

    async def _send_alert(self, subject: str, message: str):
        """Send alert notification"""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'message': message,
            'system': 'ConcordBroker Master Orchestrator'
        }
        
        # Log alert
        logger.critical(f"ALERT: {subject} - {message}")
        
        # Could integrate with email, Slack, etc.
        # For now, write to alerts log
        Path('logs').mkdir(exist_ok=True)
        with open('logs/alerts.log', 'a') as f:
            f.write(f"{json.dumps(alert_data)}\n")

    def schedule_routine_tasks(self):
        """Schedule routine agent tasks"""
        logger.info("Scheduling routine tasks")
        
        # Schedule immediate data loading if tables are empty
        self._schedule_immediate_data_load()
        
        # Schedule regular maintenance tasks
        for agent_name, config in self.agents.items():
            if config.enabled:
                self._schedule_agent_task(agent_name, config)

    def _schedule_immediate_data_load(self):
        """Schedule immediate data loading if needed"""
        # Check if database is empty and schedule immediate load
        task = AgentTask(
            id=f"immediate_load_{int(time.time())}",
            agent_name='data_loader',
            task_type='immediate_load',
            priority=Priority.CRITICAL,
            data={'force_reload': True, 'batch_size': 100}
        )
        
        asyncio.create_task(self.add_task(task))

    def _schedule_agent_task(self, agent_name: str, config: AgentConfig):
        """Schedule a specific agent task"""
        task = AgentTask(
            id=f"{agent_name}_{int(time.time())}",
            agent_name=agent_name,
            task_type='scheduled',
            priority=Priority.MEDIUM,
            data={'scheduled': True}
        )
        
        asyncio.create_task(self.add_task(task))

    async def health_check(self):
        """Perform system health check"""
        logger.info("Performing health check")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'orchestrator_status': 'healthy',
            'agent_statuses': dict(self.agent_statuses),
            'queue_size': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'metrics': self.metrics
        }
        
        # Check database connectivity
        try:
            # Quick database health check
            health_status['database_status'] = await self._check_database_health()
        except Exception as e:
            health_status['database_status'] = f'unhealthy: {str(e)}'
            await self._send_alert('Database Health Check Failed', str(e))
        
        self.metrics['last_health_check'] = datetime.now()
        
        # Save health status
        Path('logs').mkdir(exist_ok=True)
        with open('logs/health_status.json', 'w') as f:
            json.dump(health_status, f, indent=2)
        
        return health_status

    async def _check_database_health(self) -> str:
        """Check database connectivity and basic functionality"""
        # This would implement actual database health check
        # For now, return healthy
        return 'healthy'

    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.metrics['uptime_start']),
            'agents': {name: status.value for name, status in self.agent_statuses.items()},
            'queue_size': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks),
            'metrics': self.metrics,
            'recent_tasks': [
                {
                    'id': task.id,
                    'agent': task.agent_name,
                    'status': task.status.value,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                }
                for task in self.completed_tasks[-10:]
            ]
        }

    async def run_forever(self):
        """Main orchestrator loop"""
        logger.info("Master Orchestrator starting...")
        
        # Schedule initial tasks
        self.schedule_routine_tasks()
        
        # Main processing loop
        while True:
            try:
                # Process task queue
                await self.process_task_queue()
                
                # Health check every 15 minutes
                if (not self.metrics['last_health_check'] or 
                    datetime.now() - self.metrics['last_health_check'] > timedelta(minutes=15)):
                    await self.health_check()
                
                # Brief pause
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                await self._send_alert('Orchestrator Error', str(e))
                await asyncio.sleep(60)  # Wait longer on error


async def main():
    """Main entry point"""
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Initialize orchestrator
    orchestrator = MasterOrchestrator()
    
    # Run forever
    await orchestrator.run_forever()


if __name__ == "__main__":
    asyncio.run(main())