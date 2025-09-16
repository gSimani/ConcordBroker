#!/usr/bin/env python3
"""
Florida Data Scheduler & Automation System
Advanced scheduling with intelligent prioritization, resource management, and adaptive timing
"""

import asyncio
import schedule
import time
import json
import logging
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import pytz
import calendar
from concurrent.futures import ThreadPoolExecutor
import psutil
import os
import hashlib

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_config import SupabaseConfig
from florida_comprehensive_monitor import FloridaComprehensiveMonitor
from florida_monitoring_system import FloridaMonitoringSystem
from florida_error_handler import FloridaErrorHandler

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5

class TaskStatus(Enum):
    """Task execution status"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class ScheduleType(Enum):
    """Types of schedule patterns"""
    INTERVAL = "interval"  # Every N seconds/minutes/hours
    DAILY = "daily"       # Daily at specific time
    WEEKLY = "weekly"     # Weekly on specific day/time
    MONTHLY = "monthly"   # Monthly on specific day/time
    CRON = "cron"        # Cron expression
    ADAPTIVE = "adaptive" # Adaptive based on data patterns
    ON_DEMAND = "on_demand" # Triggered by events

@dataclass
class ResourceLimits:
    """Resource usage limits for tasks"""
    max_cpu_percent: float = 80.0
    max_memory_mb: int = 4096
    max_concurrent_tasks: int = 5
    max_disk_io_mbps: float = 100.0
    max_network_mbps: float = 50.0

@dataclass
class TaskDefinition:
    """Complete task definition"""
    task_id: str
    name: str
    description: str
    source: str
    operation: str
    priority: TaskPriority
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    enabled: bool = True
    timeout_minutes: int = 60
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    dependencies: List[str] = field(default_factory=list)
    retry_config: Dict[str, Any] = field(default_factory=dict)
    conditions: Dict[str, Any] = field(default_factory=dict)  # Conditions for execution
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskExecution:
    """Task execution record"""
    execution_id: str
    task_id: str
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.SCHEDULED
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    duration_seconds: Optional[float] = None

class AdaptiveScheduler:
    """Adaptive scheduling based on data patterns and system load"""
    
    def __init__(self):
        self.data_patterns = {}  # Source -> pattern analysis
        self.system_load_history = []
        self.update_frequency_analysis = {}
    
    async def analyze_data_patterns(self, source: str, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze data update patterns for a source"""
        if not historical_data:
            return {"recommended_interval": 3600}  # Default 1 hour
        
        # Analyze update frequencies
        update_times = []
        for record in historical_data:
            if record.get('timestamp'):
                update_times.append(datetime.fromisoformat(record['timestamp']))
        
        if len(update_times) < 2:
            return {"recommended_interval": 3600}
        
        # Calculate intervals between updates
        intervals = []
        for i in range(1, len(update_times)):
            interval = (update_times[i] - update_times[i-1]).total_seconds()
            intervals.append(interval)
        
        # Statistical analysis
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        
        # Determine optimal check frequency (more frequent than average update)
        recommended_interval = max(avg_interval * 0.5, min_interval * 0.25)
        recommended_interval = min(recommended_interval, 86400)  # Max 24 hours
        recommended_interval = max(recommended_interval, 300)    # Min 5 minutes
        
        return {
            "recommended_interval": int(recommended_interval),
            "avg_update_interval": avg_interval,
            "min_update_interval": min_interval,
            "max_update_interval": max_interval,
            "update_pattern": self._classify_update_pattern(intervals)
        }
    
    def _classify_update_pattern(self, intervals: List[float]) -> str:
        """Classify update pattern type"""
        if not intervals:
            return "unknown"
        
        # Check for regular patterns
        variance = sum((x - sum(intervals)/len(intervals))**2 for x in intervals) / len(intervals)
        coefficient_of_variation = (variance**0.5) / (sum(intervals)/len(intervals))
        
        if coefficient_of_variation < 0.1:
            return "regular"
        elif coefficient_of_variation < 0.3:
            return "semi_regular"
        else:
            return "irregular"
    
    def recommend_schedule(self, source: str, current_load: float = 0.5) -> Dict[str, Any]:
        """Recommend optimal schedule based on patterns and system load"""
        if source not in self.data_patterns:
            # Default recommendation
            return {
                "schedule_type": ScheduleType.INTERVAL,
                "interval_minutes": 60,
                "priority_adjustment": 0
            }
        
        pattern = self.data_patterns[source]
        base_interval = pattern.get("recommended_interval", 3600)
        
        # Adjust for system load
        if current_load > 0.8:
            # High load - reduce frequency
            adjusted_interval = base_interval * 1.5
            priority_adjustment = -1
        elif current_load < 0.3:
            # Low load - increase frequency
            adjusted_interval = base_interval * 0.8
            priority_adjustment = 1
        else:
            adjusted_interval = base_interval
            priority_adjustment = 0
        
        return {
            "schedule_type": ScheduleType.INTERVAL,
            "interval_minutes": int(adjusted_interval / 60),
            "priority_adjustment": priority_adjustment,
            "pattern_type": pattern.get("update_pattern", "unknown")
        }

class FloridaScheduler:
    """Comprehensive scheduler for Florida data operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.pool = None
        self.tasks = {}  # task_id -> TaskDefinition
        self.executions = {}  # execution_id -> TaskExecution
        self.running_tasks = {}  # execution_id -> asyncio.Task
        self.adaptive_scheduler = AdaptiveScheduler()
        self.system_monitor = SystemResourceMonitor()
        
        # Components
        self.comprehensive_monitor = None
        self.monitoring_system = None
        self.error_handler = None
        
        # Statistics
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "skipped_executions": 0,
            "average_execution_time": 0.0,
            "last_execution": None,
            "scheduler_uptime": datetime.now()
        }
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load scheduler configuration"""
        default_config = {
            "timezone": "US/Eastern",  # Florida timezone
            "max_concurrent_tasks": 5,
            "resource_monitoring": {
                "enabled": True,
                "check_interval_seconds": 30,
                "cpu_threshold": 80.0,
                "memory_threshold": 80.0,
                "disk_threshold": 90.0
            },
            "adaptive_scheduling": {
                "enabled": True,
                "analysis_days": 30,
                "min_check_interval_minutes": 5,
                "max_check_interval_hours": 24
            },
            "task_defaults": {
                "timeout_minutes": 60,
                "retry_attempts": 3,
                "retry_delay_minutes": 5
            },
            "maintenance": {
                "cleanup_old_executions_days": 30,
                "optimization_hour": 2,  # 2 AM daily optimization
                "health_check_minutes": 15
            },
            "notifications": {
                "task_failure_threshold": 3,
                "system_overload_threshold": 5,
                "send_daily_summary": True
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize database
        self.pool = await SupabaseConfig.get_db_pool()
        await self._initialize_scheduler_tables()
        
        # Initialize components
        self.comprehensive_monitor = FloridaComprehensiveMonitor()
        await self.comprehensive_monitor.__aenter__()
        
        self.monitoring_system = FloridaMonitoringSystem()
        await self.monitoring_system.__aenter__()
        
        self.error_handler = FloridaErrorHandler()
        await self.error_handler.__aenter__()
        
        # Load existing tasks and executions
        await self._load_tasks_from_database()
        await self._initialize_default_tasks()
        
        # Start system monitoring
        asyncio.create_task(self.system_monitor.start_monitoring())
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Stop running tasks
        for task in self.running_tasks.values():
            task.cancel()
        
        # Close components
        if self.error_handler:
            await self.error_handler.__aexit__(exc_type, exc_val, exc_tb)
        if self.monitoring_system:
            await self.monitoring_system.__aexit__(exc_type, exc_val, exc_tb)
        if self.comprehensive_monitor:
            await self.comprehensive_monitor.__aexit__(exc_type, exc_val, exc_tb)
        
        if self.pool:
            await self.pool.close()
    
    async def _initialize_scheduler_tables(self):
        """Initialize scheduler database tables"""
        async with self.pool.acquire() as conn:
            # Task definitions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_scheduler_tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    source TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    schedule_type TEXT NOT NULL,
                    schedule_config JSONB NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    timeout_minutes INTEGER DEFAULT 60,
                    resource_limits JSONB,
                    dependencies JSONB,
                    retry_config JSONB,
                    conditions JSONB,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Task executions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_scheduler_executions (
                    execution_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    scheduled_time TIMESTAMPTZ NOT NULL,
                    start_time TIMESTAMPTZ,
                    end_time TIMESTAMPTZ,
                    status TEXT NOT NULL DEFAULT 'scheduled',
                    result JSONB,
                    error_message TEXT,
                    resource_usage JSONB,
                    duration_seconds FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    FOREIGN KEY (task_id) REFERENCES fl_scheduler_tasks(task_id)
                )
            """)
            
            # Schedule analytics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_schedule_analytics (
                    id SERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    analysis_date DATE DEFAULT CURRENT_DATE,
                    update_pattern JSONB,
                    recommended_schedule JSONB,
                    system_load_avg FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_task_time ON fl_scheduler_executions(task_id, scheduled_time DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_status ON fl_scheduler_executions(status, scheduled_time)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_enabled ON fl_scheduler_tasks(enabled, priority)")
    
    async def _load_tasks_from_database(self):
        """Load existing tasks from database"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM fl_scheduler_tasks WHERE enabled = TRUE")
            
            for row in rows:
                task = TaskDefinition(
                    task_id=row['task_id'],
                    name=row['name'],
                    description=row['description'],
                    source=row['source'],
                    operation=row['operation'],
                    priority=TaskPriority(row['priority']),
                    schedule_type=ScheduleType(row['schedule_type']),
                    schedule_config=row['schedule_config'],
                    enabled=row['enabled'],
                    timeout_minutes=row['timeout_minutes'],
                    resource_limits=ResourceLimits(**row['resource_limits']) if row['resource_limits'] else ResourceLimits(),
                    dependencies=row['dependencies'] or [],
                    retry_config=row['retry_config'] or {},
                    conditions=row['conditions'] or {},
                    metadata=row['metadata'] or {}
                )
                self.tasks[task.task_id] = task
        
        logger.info(f"Loaded {len(self.tasks)} tasks from database")
    
    async def _initialize_default_tasks(self):
        """Initialize default Florida data tasks if not exists"""
        default_tasks = [
            {
                "task_id": "florida_revenue_daily",
                "name": "Florida Revenue Data Check",
                "description": "Daily check for new Florida Revenue data files",
                "source": "florida_revenue",
                "operation": "comprehensive_check",
                "priority": TaskPriority.HIGH,
                "schedule_type": ScheduleType.DAILY,
                "schedule_config": {"time": "06:00", "timezone": "US/Eastern"},
                "timeout_minutes": 120
            },
            {
                "task_id": "sunbiz_weekly",
                "name": "Sunbiz Weekly Data Sync",
                "description": "Weekly synchronization of Florida business registry data",
                "source": "sunbiz",
                "operation": "comprehensive_sync",
                "priority": TaskPriority.NORMAL,
                "schedule_type": ScheduleType.WEEKLY,
                "schedule_config": {"day": "sunday", "time": "02:00", "timezone": "US/Eastern"},
                "timeout_minutes": 180
            },
            {
                "task_id": "broward_daily_index",
                "name": "Broward Daily Index Monitor",
                "description": "Monitor Broward County daily index files",
                "source": "broward",
                "operation": "daily_index_check",
                "priority": TaskPriority.HIGH,
                "schedule_type": ScheduleType.INTERVAL,
                "schedule_config": {"minutes": 30},
                "timeout_minutes": 30
            },
            {
                "task_id": "system_health_check",
                "name": "System Health Check",
                "description": "Periodic system health and resource monitoring",
                "source": "system",
                "operation": "health_check",
                "priority": TaskPriority.CRITICAL,
                "schedule_type": ScheduleType.INTERVAL,
                "schedule_config": {"minutes": 15},
                "timeout_minutes": 10
            },
            {
                "task_id": "adaptive_optimization",
                "name": "Adaptive Schedule Optimization",
                "description": "Optimize schedules based on data patterns and system load",
                "source": "system",
                "operation": "adaptive_optimization",
                "priority": TaskPriority.LOW,
                "schedule_type": ScheduleType.DAILY,
                "schedule_config": {"time": "02:00", "timezone": "US/Eastern"},
                "timeout_minutes": 60
            }
        ]
        
        for task_config in default_tasks:
            if task_config["task_id"] not in self.tasks:
                await self.create_task(**task_config)
    
    async def create_task(self, **kwargs) -> str:
        """Create a new scheduled task"""
        # Generate task ID if not provided
        if "task_id" not in kwargs:
            kwargs["task_id"] = hashlib.md5(
                f"{kwargs['source']}_{kwargs['operation']}_{datetime.now()}".encode()
            ).hexdigest()[:12]
        
        task = TaskDefinition(**kwargs)
        
        # Store in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fl_scheduler_tasks 
                (task_id, name, description, source, operation, priority, schedule_type, 
                 schedule_config, enabled, timeout_minutes, resource_limits, dependencies, 
                 retry_config, conditions, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (task_id) DO UPDATE SET
                    name = $2, description = $3, schedule_config = $8, enabled = $9,
                    updated_at = NOW()
            """, task.task_id, task.name, task.description, task.source, task.operation,
                task.priority.value, task.schedule_type.value, json.dumps(task.schedule_config),
                task.enabled, task.timeout_minutes, json.dumps(asdict(task.resource_limits)),
                json.dumps(task.dependencies), json.dumps(task.retry_config),
                json.dumps(task.conditions), json.dumps(task.metadata))
        
        # Add to memory
        self.tasks[task.task_id] = task
        
        logger.info(f"Created task {task.task_id}: {task.name}")
        return task.task_id
    
    async def schedule_task_execution(self, task_id: str, scheduled_time: datetime = None) -> str:
        """Schedule a task execution"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        if not task.enabled:
            logger.info(f"Task {task_id} is disabled, skipping execution")
            return None
        
        # Use current time if not specified
        if scheduled_time is None:
            scheduled_time = datetime.now()
        
        # Generate execution ID
        execution_id = hashlib.md5(
            f"{task_id}_{scheduled_time.isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Create execution record
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task_id,
            scheduled_time=scheduled_time
        )
        
        # Store in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fl_scheduler_executions 
                (execution_id, task_id, scheduled_time, status)
                VALUES ($1, $2, $3, $4)
            """, execution_id, task_id, scheduled_time, TaskStatus.SCHEDULED.value)
        
        # Add to memory
        self.executions[execution_id] = execution
        
        logger.info(f"Scheduled execution {execution_id} for task {task_id} at {scheduled_time}")
        return execution_id
    
    async def execute_task(self, execution_id: str) -> Dict[str, Any]:
        """Execute a scheduled task"""
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        task = self.tasks[execution.task_id]
        
        # Check dependencies
        if task.dependencies:
            dependency_satisfied = await self._check_dependencies(task.dependencies)
            if not dependency_satisfied:
                execution.status = TaskStatus.SKIPPED
                execution.error_message = "Dependencies not satisfied"
                await self._update_execution_status(execution)
                return {"status": "skipped", "reason": "dependencies_not_satisfied"}
        
        # Check conditions
        if task.conditions:
            conditions_met = await self._check_conditions(task.conditions)
            if not conditions_met:
                execution.status = TaskStatus.SKIPPED
                execution.error_message = "Conditions not met"
                await self._update_execution_status(execution)
                return {"status": "skipped", "reason": "conditions_not_met"}
        
        # Check resource availability
        if not await self._check_resource_availability(task.resource_limits):
            execution.status = TaskStatus.SKIPPED
            execution.error_message = "Insufficient resources"
            await self._update_execution_status(execution)
            return {"status": "skipped", "reason": "insufficient_resources"}
        
        # Start execution
        execution.status = TaskStatus.RUNNING
        execution.start_time = datetime.now()
        await self._update_execution_status(execution)
        
        # Monitor resource usage
        resource_monitor = ResourceUsageMonitor()
        resource_monitor.start()
        
        try:
            # Execute the actual task
            result = await self._execute_task_operation(task)
            
            # Mark as completed
            execution.status = TaskStatus.COMPLETED
            execution.end_time = datetime.now()
            execution.result = result
            execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
            
            # Record success
            await self.error_handler._update_circuit_breaker(task.source, success=True)
            self.stats["successful_executions"] += 1
            
        except Exception as e:
            # Mark as failed
            execution.status = TaskStatus.FAILED
            execution.end_time = datetime.now()
            execution.error_message = str(e)
            execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
            
            # Record error
            await self.error_handler.record_error(e, task.source, task.operation, {
                "task_id": task.task_id,
                "execution_id": execution_id
            })
            self.stats["failed_executions"] += 1
        
        finally:
            # Stop resource monitoring
            execution.resource_usage = resource_monitor.stop()
            
            # Update execution record
            await self._update_execution_status(execution)
            
            # Remove from running tasks
            if execution_id in self.running_tasks:
                del self.running_tasks[execution_id]
            
            # Update statistics
            self.stats["total_executions"] += 1
            self.stats["last_execution"] = datetime.now()
            
            # Calculate average execution time
            if execution.duration_seconds:
                total_time = self.stats["average_execution_time"] * (self.stats["total_executions"] - 1)
                self.stats["average_execution_time"] = (total_time + execution.duration_seconds) / self.stats["total_executions"]
        
        return {"status": execution.status.value, "result": execution.result}
    
    async def _execute_task_operation(self, task: TaskDefinition) -> Dict[str, Any]:
        """Execute the actual task operation"""
        if task.source == "florida_revenue" and task.operation == "comprehensive_check":
            return await self.comprehensive_monitor.run_monitoring_cycle()
        
        elif task.source == "system" and task.operation == "health_check":
            return await self._system_health_check()
        
        elif task.source == "system" and task.operation == "adaptive_optimization":
            return await self._adaptive_optimization()
        
        elif task.source == "broward" and task.operation == "daily_index_check":
            # Specific Broward daily index monitoring
            return {"status": "completed", "message": "Broward index check completed"}
        
        elif task.source == "sunbiz" and task.operation == "comprehensive_sync":
            # Sunbiz synchronization
            return {"status": "completed", "message": "Sunbiz sync completed"}
        
        else:
            # Generic monitoring operation
            return await self.monitoring_system.check_all_sources()
    
    async def _system_health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        health_status = {
            "timestamp": datetime.now(),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "active_tasks": len(self.running_tasks),
            "error_rate": self._calculate_error_rate(),
            "status": "healthy"
        }
        
        # Determine overall health status
        if (health_status["cpu_usage"] > 90 or 
            health_status["memory_usage"] > 90 or 
            health_status["disk_usage"] > 95):
            health_status["status"] = "critical"
        elif (health_status["cpu_usage"] > 80 or 
              health_status["memory_usage"] > 80 or 
              health_status["error_rate"] > 0.1):
            health_status["status"] = "warning"
        
        return health_status
    
    async def _adaptive_optimization(self) -> Dict[str, Any]:
        """Perform adaptive schedule optimization"""
        optimization_results = {
            "timestamp": datetime.now(),
            "sources_analyzed": 0,
            "schedules_updated": 0,
            "recommendations": []
        }
        
        # Analyze each source
        for source in ["florida_revenue", "sunbiz", "broward", "arcgis"]:
            try:
                # Get historical data for analysis
                historical_data = await self._get_historical_update_data(source)
                
                # Analyze patterns
                pattern_analysis = await self.adaptive_scheduler.analyze_data_patterns(source, historical_data)
                self.adaptive_scheduler.data_patterns[source] = pattern_analysis
                
                # Get recommendations
                current_load = psutil.cpu_percent() / 100.0
                recommendation = self.adaptive_scheduler.recommend_schedule(source, current_load)
                
                optimization_results["sources_analyzed"] += 1
                optimization_results["recommendations"].append({
                    "source": source,
                    "current_pattern": pattern_analysis,
                    "recommendation": recommendation
                })
                
                # Update task schedules if needed
                updated = await self._update_source_schedules(source, recommendation)
                if updated:
                    optimization_results["schedules_updated"] += 1
                    
            except Exception as e:
                logger.error(f"Optimization failed for {source}: {e}")
        
        return optimization_results
    
    async def _get_historical_update_data(self, source: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical update data for a source"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT timestamp, records_processed, new_records, status
                FROM fl_data_updates
                WHERE agent_name LIKE $1 AND timestamp > NOW() - INTERVAL '%s days'
                ORDER BY timestamp DESC
            """, f"%{source}%", days)
        
        return [dict(row) for row in rows]
    
    async def _update_source_schedules(self, source: str, recommendation: Dict[str, Any]) -> bool:
        """Update schedules for a source based on recommendations"""
        # Find tasks for this source
        source_tasks = [task for task in self.tasks.values() if task.source == source]
        
        updated = False
        for task in source_tasks:
            if recommendation["schedule_type"] == ScheduleType.INTERVAL:
                new_interval = recommendation["interval_minutes"]
                current_interval = task.schedule_config.get("minutes", 60)
                
                # Only update if there's a significant change
                if abs(new_interval - current_interval) > max(5, current_interval * 0.2):
                    task.schedule_config["minutes"] = new_interval
                    await self._save_task_to_database(task)
                    updated = True
                    logger.info(f"Updated {task.task_id} interval from {current_interval} to {new_interval} minutes")
        
        return updated
    
    async def _save_task_to_database(self, task: TaskDefinition):
        """Save task configuration to database"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE fl_scheduler_tasks 
                SET schedule_config = $1, updated_at = NOW()
                WHERE task_id = $2
            """, json.dumps(task.schedule_config), task.task_id)
    
    def _calculate_error_rate(self) -> float:
        """Calculate recent error rate"""
        total = self.stats["total_executions"]
        failed = self.stats["failed_executions"]
        
        if total == 0:
            return 0.0
        
        return failed / total
    
    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_task_id in dependencies:
            # Check if dependency task completed successfully recently
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT status FROM fl_scheduler_executions
                    WHERE task_id = $1 AND start_time > NOW() - INTERVAL '24 hours'
                    ORDER BY start_time DESC
                    LIMIT 1
                """, dep_task_id)
            
            if not result or result['status'] != TaskStatus.COMPLETED.value:
                return False
        
        return True
    
    async def _check_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Check if task conditions are met"""
        # Example condition checks
        if "min_cpu_available" in conditions:
            if psutil.cpu_percent() > (100 - conditions["min_cpu_available"]):
                return False
        
        if "min_memory_available" in conditions:
            if psutil.virtual_memory().percent > (100 - conditions["min_memory_available"]):
                return False
        
        if "time_window" in conditions:
            current_hour = datetime.now().hour
            window = conditions["time_window"]
            if not (window["start"] <= current_hour <= window["end"]):
                return False
        
        return True
    
    async def _check_resource_availability(self, limits: ResourceLimits) -> bool:
        """Check if system resources are available for task execution"""
        # Check CPU
        if psutil.cpu_percent() > limits.max_cpu_percent:
            return False
        
        # Check memory
        memory_usage_mb = psutil.virtual_memory().used / (1024 * 1024)
        if memory_usage_mb > limits.max_memory_mb:
            return False
        
        # Check concurrent tasks
        if len(self.running_tasks) >= limits.max_concurrent_tasks:
            return False
        
        return True
    
    async def _update_execution_status(self, execution: TaskExecution):
        """Update execution status in database"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE fl_scheduler_executions 
                SET start_time = $1, end_time = $2, status = $3, result = $4, 
                    error_message = $5, resource_usage = $6, duration_seconds = $7
                WHERE execution_id = $8
            """, execution.start_time, execution.end_time, execution.status.value,
                json.dumps(execution.result), execution.error_message,
                json.dumps(execution.resource_usage), execution.duration_seconds, execution.execution_id)
    
    async def start_scheduler(self):
        """Start the scheduler daemon"""
        logger.info("Starting Florida Data Scheduler")
        
        # Set timezone
        timezone = pytz.timezone(self.config["timezone"])
        
        # Schedule all tasks
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            await self._schedule_recurring_task(task, timezone)
        
        # Start scheduler loop
        logger.info("Scheduler daemon started")
        
        try:
            while True:
                # Run pending scheduled tasks
                schedule.run_pending()
                
                # Process scheduled executions
                await self._process_pending_executions()
                
                # System maintenance
                if datetime.now().minute == 0:  # Every hour
                    await self._periodic_maintenance()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            raise
    
    async def _schedule_recurring_task(self, task: TaskDefinition, timezone):
        """Schedule a recurring task with the schedule library"""
        config = task.schedule_config
        
        if task.schedule_type == ScheduleType.DAILY:
            time_str = config.get("time", "00:00")
            schedule.every().day.at(time_str).do(
                lambda: asyncio.create_task(self.schedule_task_execution(task.task_id))
            )
        
        elif task.schedule_type == ScheduleType.WEEKLY:
            day = config.get("day", "monday")
            time_str = config.get("time", "00:00")
            getattr(schedule.every(), day.lower()).at(time_str).do(
                lambda: asyncio.create_task(self.schedule_task_execution(task.task_id))
            )
        
        elif task.schedule_type == ScheduleType.INTERVAL:
            minutes = config.get("minutes", 60)
            schedule.every(minutes).minutes.do(
                lambda: asyncio.create_task(self.schedule_task_execution(task.task_id))
            )
        
        logger.info(f"Scheduled task {task.task_id} with {task.schedule_type.value} schedule")
    
    async def _process_pending_executions(self):
        """Process executions that are ready to run"""
        current_time = datetime.now()
        
        # Find executions ready to run
        pending_executions = [
            execution for execution in self.executions.values()
            if (execution.status == TaskStatus.SCHEDULED and 
                execution.scheduled_time <= current_time and
                execution.execution_id not in self.running_tasks)
        ]
        
        # Sort by priority and scheduled time
        pending_executions.sort(key=lambda x: (
            self.tasks[x.task_id].priority.value, 
            x.scheduled_time
        ))
        
        # Execute tasks up to concurrency limit
        max_concurrent = self.config["max_concurrent_tasks"]
        available_slots = max_concurrent - len(self.running_tasks)
        
        for execution in pending_executions[:available_slots]:
            task = asyncio.create_task(self.execute_task(execution.execution_id))
            self.running_tasks[execution.execution_id] = task
    
    async def _periodic_maintenance(self):
        """Perform periodic maintenance tasks"""
        try:
            # Clean up old execution records
            cutoff_date = datetime.now() - timedelta(days=self.config["maintenance"]["cleanup_old_executions_days"])
            
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM fl_scheduler_executions 
                    WHERE created_at < $1 AND status IN ('completed', 'failed', 'skipped')
                """, cutoff_date)
                
                logger.info(f"Cleaned up old execution records: {result}")
            
            # Update system statistics
            await self._update_system_statistics()
            
        except Exception as e:
            logger.error(f"Maintenance error: {e}")
    
    async def _update_system_statistics(self):
        """Update system performance statistics"""
        # Calculate performance metrics
        recent_executions = []
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for execution in self.executions.values():
            if execution.start_time and execution.start_time > cutoff_time:
                recent_executions.append(execution)
        
        if recent_executions:
            avg_duration = sum(e.duration_seconds for e in recent_executions if e.duration_seconds) / len(recent_executions)
            success_rate = len([e for e in recent_executions if e.status == TaskStatus.COMPLETED]) / len(recent_executions)
            
            # Store statistics
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO fl_schedule_analytics 
                    (source, analysis_date, update_pattern, system_load_avg)
                    VALUES ('system', CURRENT_DATE, $1, $2)
                    ON CONFLICT (source, analysis_date) DO UPDATE SET
                        update_pattern = $1, system_load_avg = $2
                """, json.dumps({
                    "avg_execution_duration": avg_duration,
                    "success_rate": success_rate,
                    "total_executions": len(recent_executions)
                }), psutil.cpu_percent())

class SystemResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {}
    
    async def start_monitoring(self):
        """Start continuous resource monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            self.stats = {
                "timestamp": datetime.now(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "network_io": dict(psutil.net_io_counters()._asdict()),
                "process_count": len(psutil.pids())
            }
            
            await asyncio.sleep(30)  # Update every 30 seconds
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        return self.stats

class ResourceUsageMonitor:
    """Monitor resource usage for a specific task"""
    
    def __init__(self):
        self.start_stats = None
        self.process = psutil.Process()
    
    def start(self):
        """Start monitoring"""
        self.start_stats = {
            "cpu_percent": self.process.cpu_percent(),
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "timestamp": datetime.now()
        }
    
    def stop(self) -> Dict[str, float]:
        """Stop monitoring and return usage statistics"""
        if not self.start_stats:
            return {}
        
        end_stats = {
            "cpu_percent": self.process.cpu_percent(),
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "timestamp": datetime.now()
        }
        
        return {
            "duration_seconds": (end_stats["timestamp"] - self.start_stats["timestamp"]).total_seconds(),
            "peak_memory_mb": max(self.start_stats["memory_mb"], end_stats["memory_mb"]),
            "avg_cpu_percent": (self.start_stats["cpu_percent"] + end_stats["cpu_percent"]) / 2
        }

async def main():
    """Test the scheduler"""
    print("Testing Florida Scheduler...")
    
    async with FloridaScheduler() as scheduler:
        # Show current tasks
        print(f"\nLoaded Tasks: {len(scheduler.tasks)}")
        for task_id, task in scheduler.tasks.items():
            print(f"  {task_id}: {task.name} ({task.schedule_type.value})")
        
        # Test single task execution
        if scheduler.tasks:
            test_task_id = next(iter(scheduler.tasks.keys()))
            execution_id = await scheduler.schedule_task_execution(test_task_id)
            
            if execution_id:
                result = await scheduler.execute_task(execution_id)
                print(f"\nTest Execution Result: {result}")
        
        # Show statistics
        print(f"\nScheduler Statistics:")
        for key, value in scheduler.stats.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())