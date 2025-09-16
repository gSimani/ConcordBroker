"""
SUNBIZ SUPERVISOR AGENT - Permanent Orchestration System
========================================================
Master agent that oversees all Sunbiz database operations including:
- Daily update orchestration
- Health monitoring
- Error recovery
- Performance tracking
- Automated reporting

This agent runs permanently and ensures the Sunbiz database stays synchronized.
"""

import os
import sys
import json
import time
import logging
import threading
import psycopg2
import paramiko
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
from enum import Enum
import schedule
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SUPERVISOR] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_supervisor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent operational states"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    task_name: str
    status: str
    start_time: datetime
    end_time: datetime
    records_processed: int
    errors: List[str]
    metadata: Dict[str, Any]

class SunbizSupervisorAgent:
    """
    Master Supervisor Agent for Sunbiz Database Operations
    
    Responsibilities:
    - Orchestrate daily updates
    - Monitor system health
    - Handle errors and recovery
    - Generate reports
    - Ensure data integrity
    """
    
    def __init__(self):
        logger.info("Initializing Sunbiz Supervisor Agent...")
        
        # Configuration
        self.config = self._load_configuration()
        
        # State management
        self.status = AgentStatus.INITIALIZING
        self.current_tasks = {}
        self.task_history = []
        self.error_count = 0
        self.last_successful_update = None
        
        # Threading
        self.shutdown_event = threading.Event()
        self.worker_threads = []
        
        # Database connection pool
        self.db_url = self.config.get('database_url')
        
        # SFTP settings
        self.sftp_config = {
            'host': 'sftp.floridados.gov',
            'port': 22,
            'username': 'Public',
            'password': 'PubAccess1845!'
        }
        
        # Monitoring
        self.metrics = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'total_records': 0,
            'uptime_start': datetime.now(),
            'last_health_check': None
        }
        
        # Initialize subsystems
        self._initialize_database()
        self._setup_signal_handlers()
        
        logger.info("Supervisor Agent initialized successfully")
        self.status = AgentStatus.IDLE
    
    def _load_configuration(self) -> Dict:
        """Load configuration from environment and files"""
        config = {
            'database_url': os.getenv('DATABASE_URL', 
                "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"),
            'update_schedule': os.getenv('UPDATE_SCHEDULE', '02:00'),  # 2 AM daily
            'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '300')),  # 5 minutes
            'max_retries': int(os.getenv('MAX_RETRIES', '3')),
            'alert_email': os.getenv('ALERT_EMAIL'),
            'webhook_url': os.getenv('WEBHOOK_URL'),
            'enable_auto_recovery': os.getenv('ENABLE_AUTO_RECOVERY', 'true').lower() == 'true'
        }
        
        # Load from config file if exists
        config_file = 'sunbiz_supervisor_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        
        return config
    
    def _initialize_database(self):
        """Initialize database tables for supervisor operations"""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                # Supervisor status table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sunbiz_supervisor_status (
                        id SERIAL PRIMARY KEY,
                        status VARCHAR(50) NOT NULL,
                        last_update TIMESTAMP DEFAULT NOW(),
                        metrics JSONB,
                        error_log JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                
                # Task execution log
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sunbiz_task_log (
                        id SERIAL PRIMARY KEY,
                        task_id VARCHAR(100) UNIQUE NOT NULL,
                        task_name VARCHAR(255) NOT NULL,
                        task_type VARCHAR(50),
                        priority INTEGER DEFAULT 3,
                        status VARCHAR(50) NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        duration_seconds FLOAT,
                        records_processed INTEGER DEFAULT 0,
                        errors JSONB,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_task_log_status 
                    ON sunbiz_task_log(status, created_at DESC);
                """)
                
                # Health metrics table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sunbiz_health_metrics (
                        id SERIAL PRIMARY KEY,
                        metric_type VARCHAR(50) NOT NULL,
                        metric_value FLOAT,
                        threshold_value FLOAT,
                        is_healthy BOOLEAN DEFAULT true,
                        details JSONB,
                        measured_at TIMESTAMP DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_health_metrics_time 
                    ON sunbiz_health_metrics(measured_at DESC);
                """)
                
                conn.commit()
                logger.info("Database tables initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def _get_db_connection(self):
        """Get database connection"""
        parsed = urlparse(self.db_url)
        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password.replace('%40', '@') if parsed.password else None,
            sslmode='require',
            connect_timeout=30
        )
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    # ==================== CORE ORCHESTRATION ====================
    
    def run_forever(self):
        """Main execution loop - runs permanently"""
        logger.info("Starting Sunbiz Supervisor Agent in permanent mode")
        
        try:
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitor_thread.start()
            self.worker_threads.append(monitor_thread)
            
            # Start health check thread
            health_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            health_thread.start()
            self.worker_threads.append(health_thread)
            
            # Schedule daily updates
            self._schedule_daily_tasks()
            
            # Main loop
            while not self.shutdown_event.is_set():
                try:
                    # Run scheduled tasks
                    schedule.run_pending()
                    
                    # Process any immediate tasks
                    self._process_task_queue()
                    
                    # Update supervisor status
                    self._update_supervisor_status()
                    
                    # Sleep briefly
                    time.sleep(10)
                    
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    self._handle_critical_error(e)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()
    
    def _schedule_daily_tasks(self):
        """Schedule daily update tasks"""
        update_time = self.config['update_schedule']
        
        # Schedule main daily update
        schedule.every().day.at(update_time).do(
            lambda: self.execute_task('daily_update', self._run_daily_update, priority=TaskPriority.HIGH)
        )
        
        # Schedule verification 30 minutes after update
        verify_time = (datetime.strptime(update_time, "%H:%M") + timedelta(minutes=30)).strftime("%H:%M")
        schedule.every().day.at(verify_time).do(
            lambda: self.execute_task('daily_verification', self._verify_daily_update, priority=TaskPriority.NORMAL)
        )
        
        # Schedule weekly comprehensive check
        schedule.every().sunday.at("03:00").do(
            lambda: self.execute_task('weekly_audit', self._run_weekly_audit, priority=TaskPriority.LOW)
        )
        
        logger.info(f"Scheduled daily update at {update_time}, verification at {verify_time}")
    
    def execute_task(self, task_name: str, task_func: callable, 
                    priority: TaskPriority = TaskPriority.NORMAL, **kwargs) -> str:
        """Execute a task with monitoring and error handling"""
        task_id = f"{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Executing task: {task_id}")
        
        # Record task start
        self.current_tasks[task_id] = {
            'name': task_name,
            'priority': priority.value,
            'start_time': datetime.now(),
            'status': 'running'
        }
        
        result = TaskResult(
            task_id=task_id,
            task_name=task_name,
            status='started',
            start_time=datetime.now(),
            end_time=None,
            records_processed=0,
            errors=[],
            metadata=kwargs
        )
        
        try:
            # Execute the task
            task_result = task_func(**kwargs)
            
            # Update result
            result.status = 'completed'
            result.end_time = datetime.now()
            if isinstance(task_result, dict):
                result.records_processed = task_result.get('records_processed', 0)
                result.metadata.update(task_result)
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            result.status = 'failed'
            result.end_time = datetime.now()
            result.errors.append(str(e))
            
            # Attempt recovery if enabled
            if self.config['enable_auto_recovery']:
                self._attempt_recovery(task_id, task_name, e)
        
        finally:
            # Clean up and log
            if task_id in self.current_tasks:
                del self.current_tasks[task_id]
            
            self._log_task_result(result)
            self.task_history.append(result)
            
            # Keep history limited
            if len(self.task_history) > 1000:
                self.task_history = self.task_history[-500:]
        
        return task_id
    
    # ==================== DAILY UPDATE OPERATIONS ====================
    
    def _run_daily_update(self) -> Dict:
        """Execute daily Sunbiz database update"""
        logger.info("Starting daily Sunbiz update")
        self.status = AgentStatus.PROCESSING
        
        stats = {
            'files_processed': 0,
            'records_processed': 0,
            'entities_created': 0,
            'entities_updated': 0,
            'errors': []
        }
        
        try:
            # Connect to SFTP
            transport = paramiko.Transport((self.sftp_config['host'], self.sftp_config['port']))
            transport.connect(
                username=self.sftp_config['username'],
                password=self.sftp_config['password']
            )
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Find daily files
            daily_files = self._find_daily_files(sftp)
            logger.info(f"Found {len(daily_files)} daily files to process")
            
            # Process each file
            conn = self._get_db_connection()
            
            for file_info in daily_files:
                try:
                    file_stats = self._process_daily_file(sftp, conn, file_info)
                    stats['files_processed'] += 1
                    stats['records_processed'] += file_stats.get('records', 0)
                    stats['entities_created'] += file_stats.get('created', 0)
                    stats['entities_updated'] += file_stats.get('updated', 0)
                    
                except Exception as e:
                    logger.error(f"Failed to process {file_info['name']}: {e}")
                    stats['errors'].append({
                        'file': file_info['name'],
                        'error': str(e)
                    })
            
            # Cleanup
            conn.close()
            sftp.close()
            transport.close()
            
            # Update metrics
            self.metrics['total_updates'] += 1
            self.metrics['successful_updates'] += 1
            self.metrics['total_records'] += stats['records_processed']
            self.last_successful_update = datetime.now()
            
            # Send success notification
            self._send_notification(
                "Daily Update Complete",
                f"Processed {stats['files_processed']} files with {stats['records_processed']} records"
            )
            
        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            stats['errors'].append(str(e))
            self.metrics['failed_updates'] += 1
            
            # Send failure notification
            self._send_notification(
                "Daily Update Failed",
                f"Error: {e}",
                is_error=True
            )
            raise
        
        finally:
            self.status = AgentStatus.IDLE
        
        return stats
    
    def _find_daily_files(self, sftp) -> List[Dict]:
        """Find daily files to process"""
        files_to_process = []
        cutoff_date = datetime.now() - timedelta(days=1)  # Yesterday's files
        
        directories = {
            '/Corporate_Data/Daily': 'corporate',
            '/Fictitious_Name_Data/Daily': 'fictitious',
            '/General_Partnership_Data/Daily': 'partnership',
            '/Federal_Tax_Lien_Data/Daily': 'lien',
            '/Mark_Data/Daily': 'mark'
        }
        
        for dir_path, data_type in directories.items():
            try:
                sftp.chdir(dir_path)
                files = sftp.listdir()
                
                for file_name in files:
                    if not file_name.endswith('.txt'):
                        continue
                    
                    try:
                        file_date = datetime.strptime(file_name[:8], '%Y%m%d')
                        
                        if file_date >= cutoff_date:
                            # Check if already processed
                            if not self._is_file_processed(file_name):
                                files_to_process.append({
                                    'name': file_name,
                                    'path': f"{dir_path}/{file_name}",
                                    'type': data_type,
                                    'date': file_date
                                })
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not access {dir_path}: {e}")
        
        return files_to_process
    
    def _process_daily_file(self, sftp, conn, file_info: Dict) -> Dict:
        """Process a single daily file"""
        # Import the daily updater logic
        from florida_daily_updater import FloridaDailyUpdater
        
        updater = FloridaDailyUpdater()
        return updater.process_daily_file(sftp, file_info['name'], file_info['path'])
    
    def _is_file_processed(self, file_name: str) -> bool:
        """Check if file has been processed"""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM florida_daily_processed_files 
                        WHERE file_name = %s AND status = 'completed'
                    )
                """, (file_name,))
                result = cur.fetchone()[0]
            conn.close()
            return result
        except:
            return False
    
    # ==================== MONITORING & HEALTH ====================
    
    def _monitoring_loop(self):
        """Continuous monitoring thread"""
        logger.info("Starting monitoring loop")
        
        while not self.shutdown_event.is_set():
            try:
                # Check database connectivity
                self._check_database_health()
                
                # Check SFTP connectivity
                self._check_sftp_health()
                
                # Check for stale data
                self._check_data_freshness()
                
                # Sleep for monitoring interval
                time.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Back off on error
    
    def _health_check_loop(self):
        """Regular health check thread"""
        logger.info("Starting health check loop")
        
        while not self.shutdown_event.is_set():
            try:
                health_status = self._perform_health_check()
                self._record_health_metrics(health_status)
                
                # Alert if unhealthy
                if not health_status['is_healthy']:
                    self._handle_unhealthy_state(health_status)
                
                self.metrics['last_health_check'] = datetime.now()
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(60)
    
    def _perform_health_check(self) -> Dict:
        """Perform comprehensive health check"""
        health = {
            'is_healthy': True,
            'checks': {},
            'timestamp': datetime.now()
        }
        
        # Database check
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            conn.close()
            health['checks']['database'] = 'healthy'
        except Exception as e:
            health['checks']['database'] = f'unhealthy: {e}'
            health['is_healthy'] = False
        
        # SFTP check
        try:
            transport = paramiko.Transport((self.sftp_config['host'], self.sftp_config['port']))
            transport.connect(
                username=self.sftp_config['username'],
                password=self.sftp_config['password']
            )
            transport.close()
            health['checks']['sftp'] = 'healthy'
        except Exception as e:
            health['checks']['sftp'] = f'unhealthy: {e}'
            health['is_healthy'] = False
        
        # Data freshness check
        if self.last_successful_update:
            hours_since = (datetime.now() - self.last_successful_update).total_seconds() / 3600
            if hours_since > 48:
                health['checks']['data_freshness'] = f'stale: {hours_since:.1f} hours old'
                health['is_healthy'] = False
            else:
                health['checks']['data_freshness'] = 'fresh'
        else:
            health['checks']['data_freshness'] = 'no updates yet'
        
        # Error rate check
        if self.metrics['total_updates'] > 0:
            error_rate = self.metrics['failed_updates'] / self.metrics['total_updates']
            if error_rate > 0.1:  # More than 10% failure rate
                health['checks']['error_rate'] = f'high: {error_rate:.2%}'
                health['is_healthy'] = False
            else:
                health['checks']['error_rate'] = f'acceptable: {error_rate:.2%}'
        
        return health
    
    def _check_database_health(self):
        """Check database connectivity and performance"""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                # Check connection
                cur.execute("SELECT version()")
                
                # Check table sizes
                cur.execute("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('florida_entities')) as size,
                        COUNT(*) as row_count
                    FROM florida_entities
                """)
                size_info = cur.fetchone()
                logger.debug(f"Database size: {size_info}")
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            raise
    
    def _check_sftp_health(self):
        """Check SFTP server connectivity"""
        try:
            transport = paramiko.Transport((self.sftp_config['host'], self.sftp_config['port']))
            transport.connect(
                username=self.sftp_config['username'],
                password=self.sftp_config['password']
            )
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Try to list a directory
            sftp.listdir('/Corporate_Data/Daily')
            
            sftp.close()
            transport.close()
            
        except Exception as e:
            logger.error(f"SFTP health check failed: {e}")
            raise
    
    def _check_data_freshness(self):
        """Check if data is up to date"""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                # Check last update time
                cur.execute("""
                    SELECT MAX(processed_at) 
                    FROM florida_daily_processed_files 
                    WHERE status = 'completed'
                """)
                last_update = cur.fetchone()[0]
                
                if last_update:
                    hours_old = (datetime.now() - last_update).total_seconds() / 3600
                    if hours_old > 48:
                        logger.warning(f"Data is {hours_old:.1f} hours old")
                        self._send_notification(
                            "Stale Data Warning",
                            f"No successful updates in {hours_old:.1f} hours",
                            is_error=True
                        )
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Data freshness check failed: {e}")
    
    # ==================== ERROR HANDLING & RECOVERY ====================
    
    def _handle_critical_error(self, error: Exception):
        """Handle critical errors"""
        self.error_count += 1
        self.status = AgentStatus.ERROR
        
        logger.error(f"Critical error #{self.error_count}: {error}")
        
        # Send alert
        self._send_notification(
            "Critical Error in Supervisor",
            f"Error: {error}\nError count: {self.error_count}",
            is_error=True
        )
        
        # Attempt recovery if not too many errors
        if self.error_count < 5 and self.config['enable_auto_recovery']:
            logger.info("Attempting automatic recovery...")
            self.status = AgentStatus.RECOVERING
            time.sleep(30)  # Wait before retry
            self.error_count = 0
            self.status = AgentStatus.IDLE
        else:
            logger.error("Too many errors, entering maintenance mode")
            self.status = AgentStatus.MAINTENANCE
    
    def _attempt_recovery(self, task_id: str, task_name: str, error: Exception):
        """Attempt to recover from task failure"""
        logger.info(f"Attempting recovery for task {task_id}")
        
        retry_count = 0
        max_retries = self.config['max_retries']
        
        while retry_count < max_retries:
            retry_count += 1
            logger.info(f"Recovery attempt {retry_count}/{max_retries}")
            
            try:
                # Wait with exponential backoff
                wait_time = 2 ** retry_count * 10
                time.sleep(wait_time)
                
                # Retry the task
                if task_name == 'daily_update':
                    self._run_daily_update()
                    logger.info("Recovery successful")
                    return
                    
            except Exception as e:
                logger.error(f"Recovery attempt {retry_count} failed: {e}")
        
        logger.error(f"Recovery failed after {max_retries} attempts")
    
    def _handle_unhealthy_state(self, health_status: Dict):
        """Handle unhealthy system state"""
        logger.warning(f"System unhealthy: {health_status}")
        
        # Send alert
        self._send_notification(
            "System Health Alert",
            f"Health checks failed: {json.dumps(health_status['checks'], indent=2)}",
            is_error=True
        )
        
        # Attempt to fix specific issues
        if 'database' in health_status['checks'] and 'unhealthy' in health_status['checks']['database']:
            logger.info("Attempting to reconnect to database...")
            # Database reconnection logic
        
        if 'sftp' in health_status['checks'] and 'unhealthy' in health_status['checks']['sftp']:
            logger.info("SFTP connection issue detected")
            # SFTP reconnection logic
    
    # ==================== VERIFICATION & AUDITING ====================
    
    def _verify_daily_update(self) -> Dict:
        """Verify the daily update was successful"""
        logger.info("Verifying daily update")
        
        verification = {
            'is_valid': True,
            'checks': {},
            'issues': []
        }
        
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                # Check today's files were processed
                cur.execute("""
                    SELECT COUNT(*), SUM(records_processed)
                    FROM florida_daily_processed_files
                    WHERE DATE(processed_at) = CURRENT_DATE
                    AND status = 'completed'
                """)
                files_count, records_count = cur.fetchone()
                
                verification['checks']['files_processed'] = files_count or 0
                verification['checks']['records_processed'] = records_count or 0
                
                if files_count == 0:
                    verification['is_valid'] = False
                    verification['issues'].append("No files processed today")
                
                # Check for errors
                cur.execute("""
                    SELECT file_name, error_message
                    FROM florida_daily_processed_files
                    WHERE DATE(processed_at) = CURRENT_DATE
                    AND status = 'failed'
                """)
                
                errors = cur.fetchall()
                if errors:
                    verification['is_valid'] = False
                    verification['issues'].extend([f"{f}: {e}" for f, e in errors])
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            verification['is_valid'] = False
            verification['issues'].append(str(e))
        
        # Send verification report
        if not verification['is_valid']:
            self._send_notification(
                "Daily Update Verification Failed",
                f"Issues found: {json.dumps(verification['issues'], indent=2)}",
                is_error=True
            )
        
        return verification
    
    def _run_weekly_audit(self) -> Dict:
        """Run comprehensive weekly audit"""
        logger.info("Running weekly audit")
        
        audit_results = {
            'week_ending': datetime.now().date(),
            'statistics': {},
            'recommendations': []
        }
        
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                # Weekly statistics
                cur.execute("""
                    SELECT 
                        COUNT(*) as files_processed,
                        SUM(records_processed) as total_records,
                        SUM(entities_created) as entities_created,
                        SUM(entities_updated) as entities_updated,
                        AVG(processing_time_seconds) as avg_time
                    FROM florida_daily_processed_files
                    WHERE processed_at >= NOW() - INTERVAL '7 days'
                    AND status = 'completed'
                """)
                
                stats = cur.fetchone()
                audit_results['statistics'] = {
                    'files_processed': stats[0] or 0,
                    'total_records': stats[1] or 0,
                    'entities_created': stats[2] or 0,
                    'entities_updated': stats[3] or 0,
                    'avg_processing_time': stats[4] or 0
                }
                
                # Check for gaps
                cur.execute("""
                    SELECT DATE(processed_at), COUNT(*)
                    FROM florida_daily_processed_files
                    WHERE processed_at >= NOW() - INTERVAL '7 days'
                    GROUP BY DATE(processed_at)
                    ORDER BY DATE(processed_at)
                """)
                
                daily_counts = cur.fetchall()
                
                # Generate recommendations
                if len(daily_counts) < 5:  # Less than 5 business days
                    audit_results['recommendations'].append(
                        "Missing daily updates detected - check scheduler"
                    )
                
            conn.close()
            
            # Send weekly report
            self._send_notification(
                "Weekly Audit Report",
                json.dumps(audit_results, indent=2, default=str)
            )
            
        except Exception as e:
            logger.error(f"Weekly audit failed: {e}")
            audit_results['error'] = str(e)
        
        return audit_results
    
    # ==================== UTILITIES ====================
    
    def _process_task_queue(self):
        """Process any queued tasks"""
        # This can be extended to process tasks from a queue
        pass
    
    def _update_supervisor_status(self):
        """Update supervisor status in database"""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sunbiz_supervisor_status 
                    (status, metrics, error_log)
                    VALUES (%s, %s, %s)
                """, (
                    self.status.value,
                    json.dumps(self.metrics, default=str),
                    json.dumps({'error_count': self.error_count})
                ))
                conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    def _log_task_result(self, result: TaskResult):
        """Log task result to database"""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                duration = None
                if result.end_time and result.start_time:
                    duration = (result.end_time - result.start_time).total_seconds()
                
                cur.execute("""
                    INSERT INTO sunbiz_task_log 
                    (task_id, task_name, status, start_time, end_time, 
                     duration_seconds, records_processed, errors, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        end_time = EXCLUDED.end_time,
                        duration_seconds = EXCLUDED.duration_seconds,
                        records_processed = EXCLUDED.records_processed,
                        errors = EXCLUDED.errors
                """, (
                    result.task_id,
                    result.task_name,
                    result.status,
                    result.start_time,
                    result.end_time,
                    duration,
                    result.records_processed,
                    json.dumps(result.errors) if result.errors else None,
                    json.dumps(result.metadata, default=str)
                ))
                conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log task result: {e}")
    
    def _record_health_metrics(self, health_status: Dict):
        """Record health metrics to database"""
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cur:
                for check_name, check_result in health_status['checks'].items():
                    is_healthy = 'unhealthy' not in str(check_result)
                    
                    cur.execute("""
                        INSERT INTO sunbiz_health_metrics 
                        (metric_type, is_healthy, details)
                        VALUES (%s, %s, %s)
                    """, (
                        check_name,
                        is_healthy,
                        json.dumps({'result': str(check_result)})
                    ))
                
                conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record health metrics: {e}")
    
    def _send_notification(self, subject: str, message: str, is_error: bool = False):
        """Send notifications via configured channels"""
        logger.info(f"Sending notification: {subject}")
        
        # Webhook notification
        if self.config.get('webhook_url'):
            try:
                requests.post(self.config['webhook_url'], json={
                    'subject': subject,
                    'message': message,
                    'is_error': is_error,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to send webhook: {e}")
        
        # Email notification (if configured)
        if self.config.get('alert_email'):
            # Email sending logic here
            pass
        
        # Log notification
        logger.info(f"Notification: {subject} - {message[:100]}")
    
    def get_status(self) -> Dict:
        """Get current supervisor status"""
        uptime = datetime.now() - self.metrics['uptime_start']
        
        return {
            'status': self.status.value,
            'uptime': str(uptime),
            'metrics': self.metrics,
            'current_tasks': self.current_tasks,
            'last_successful_update': self.last_successful_update,
            'error_count': self.error_count,
            'recent_tasks': [asdict(t) for t in self.task_history[-10:]]
        }
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Initiating graceful shutdown...")
        self.status = AgentStatus.SHUTDOWN
        
        # Signal all threads to stop
        self.shutdown_event.set()
        
        # Wait for threads to complete
        for thread in self.worker_threads:
            thread.join(timeout=10)
        
        # Final status update
        self._update_supervisor_status()
        
        logger.info("Supervisor Agent shutdown complete")

# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point for the supervisor agent"""
    print("="*70)
    print("SUNBIZ SUPERVISOR AGENT")
    print("Permanent Orchestration System")
    print("="*70)
    
    # Create and run supervisor
    supervisor = SunbizSupervisorAgent()
    
    try:
        # Run forever
        supervisor.run_forever()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        supervisor.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()