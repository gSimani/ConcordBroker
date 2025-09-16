#!/usr/bin/env python3
"""
Florida Data Error Handler & Retry Logic
Advanced error handling with exponential backoff, circuit breakers, and recovery strategies
"""

import asyncio
import aiohttp
import asyncpg
import logging
import json
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from functools import wraps
import smtplib
from email.mime.text import MIMEText

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_config import SupabaseConfig

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of errors in the system"""
    NETWORK_ERROR = "network_error"
    HTTP_ERROR = "http_error"
    SFTP_ERROR = "sftp_error"
    DATABASE_ERROR = "database_error"
    PARSING_ERROR = "parsing_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    FILE_NOT_FOUND = "file_not_found"
    DISK_SPACE_ERROR = "disk_space_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    """Recovery actions for different error types"""
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    FALLBACK = "fallback"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorRecord:
    """Error record structure"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    source: str
    operation: str
    message: str
    details: Dict[str, Any]
    stack_trace: str
    timestamp: datetime
    retry_count: int = 0
    resolved: bool = False
    recovery_action: Optional[RecoveryAction] = None

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 300.0  # Maximum delay in seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add random jitter to delays
    backoff_multiplier: float = 1.0

@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""
    failure_count: int = 0
    success_count: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3  # successes needed to close circuit

class FloridaErrorHandler:
    """Comprehensive error handling system for Florida data operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.pool = None
        self.error_stats = {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_source": {},
            "resolved_errors": 0,
            "unresolved_errors": 0,
            "retry_attempts": 0,
            "recovery_successes": 0
        }
        self.circuit_breakers = {}  # Source -> CircuitBreakerState
        self.active_errors = {}  # error_id -> ErrorRecord
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load error handling configuration"""
        default_config = {
            "retry_configs": {
                "network_error": RetryConfig(max_attempts=5, base_delay=2.0, max_delay=120.0),
                "http_error": RetryConfig(max_attempts=3, base_delay=1.0, max_delay=60.0),
                "sftp_error": RetryConfig(max_attempts=4, base_delay=5.0, max_delay=300.0),
                "database_error": RetryConfig(max_attempts=3, base_delay=1.0, max_delay=30.0),
                "parsing_error": RetryConfig(max_attempts=1, base_delay=0.0),  # Don't retry parsing
                "timeout_error": RetryConfig(max_attempts=3, base_delay=10.0, max_delay=180.0),
                "authentication_error": RetryConfig(max_attempts=2, base_delay=5.0),
                "rate_limit_error": RetryConfig(max_attempts=5, base_delay=60.0, max_delay=3600.0),
                "default": RetryConfig(max_attempts=3, base_delay=1.0, max_delay=60.0)
            },
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout": 300,  # 5 minutes
                "success_threshold": 3
            },
            "recovery_strategies": {
                "network_error": [RecoveryAction.RETRY, RecoveryAction.FALLBACK],
                "http_error": [RecoveryAction.RETRY, RecoveryAction.SKIP],
                "database_error": [RecoveryAction.RETRY, RecoveryAction.ABORT],
                "parsing_error": [RecoveryAction.SKIP, RecoveryAction.MANUAL_INTERVENTION],
                "authentication_error": [RecoveryAction.MANUAL_INTERVENTION],
                "default": [RecoveryAction.RETRY, RecoveryAction.SKIP]
            },
            "notifications": {
                "critical_errors": True,
                "error_threshold": 10,  # Alert after 10 errors in 1 hour
                "email_recipients": []
            },
            "logging": {
                "log_all_errors": True,
                "log_retry_attempts": True,
                "log_recovery_actions": True
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.pool = await SupabaseConfig.get_db_pool()
        await self._initialize_error_tables()
        await self._load_existing_errors()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.pool:
            await self.pool.close()
    
    async def _initialize_error_tables(self):
        """Initialize error tracking tables"""
        async with self.pool.acquire() as conn:
            # Error records table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_error_records (
                    error_id TEXT PRIMARY KEY,
                    error_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details JSONB,
                    stack_trace TEXT,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    retry_count INTEGER DEFAULT 0,
                    resolved BOOLEAN DEFAULT FALSE,
                    recovery_action TEXT,
                    resolved_at TIMESTAMPTZ
                )
            """)
            
            # Circuit breaker states
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_circuit_breaker_states (
                    source TEXT PRIMARY KEY,
                    failure_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    last_failure TIMESTAMPTZ,
                    last_success TIMESTAMPTZ,
                    state TEXT DEFAULT 'CLOSED',
                    failure_threshold INTEGER DEFAULT 5,
                    recovery_timeout INTEGER DEFAULT 60,
                    success_threshold INTEGER DEFAULT 3,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Error statistics
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_error_statistics (
                    id SERIAL PRIMARY KEY,
                    date DATE DEFAULT CURRENT_DATE,
                    error_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    severity_counts JSONB,
                    UNIQUE(date, error_type, source)
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON fl_error_records(timestamp DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_errors_type_source ON fl_error_records(error_type, source)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_errors_resolved ON fl_error_records(resolved, timestamp DESC)")
    
    async def _load_existing_errors(self):
        """Load existing unresolved errors and circuit breaker states"""
        async with self.pool.acquire() as conn:
            # Load unresolved errors
            error_rows = await conn.fetch("""
                SELECT * FROM fl_error_records 
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
            """)
            
            for row in error_rows:
                error = ErrorRecord(
                    error_id=row['error_id'],
                    error_type=ErrorType(row['error_type']),
                    severity=ErrorSeverity(row['severity']),
                    source=row['source'],
                    operation=row['operation'],
                    message=row['message'],
                    details=row['details'] or {},
                    stack_trace=row['stack_trace'] or "",
                    timestamp=row['timestamp'],
                    retry_count=row['retry_count'],
                    resolved=row['resolved'],
                    recovery_action=RecoveryAction(row['recovery_action']) if row['recovery_action'] else None
                )
                self.active_errors[error.error_id] = error
            
            # Load circuit breaker states
            breaker_rows = await conn.fetch("SELECT * FROM fl_circuit_breaker_states")
            
            for row in breaker_rows:
                state = CircuitBreakerState(
                    failure_count=row['failure_count'],
                    success_count=row['success_count'],
                    last_failure=row['last_failure'],
                    last_success=row['last_success'],
                    state=row['state'],
                    failure_threshold=row['failure_threshold'],
                    recovery_timeout=row['recovery_timeout'],
                    success_threshold=row['success_threshold']
                )
                self.circuit_breakers[row['source']] = state
        
        logger.info(f"Loaded {len(self.active_errors)} active errors and {len(self.circuit_breakers)} circuit breakers")
    
    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> Tuple[ErrorType, ErrorSeverity]:
        """Classify error type and severity"""
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Network and connection errors
        if any(keyword in error_str for keyword in ['connection', 'network', 'unreachable', 'dns']):
            return ErrorType.NETWORK_ERROR, ErrorSeverity.MEDIUM
        
        # HTTP errors
        if isinstance(error, aiohttp.ClientError) or 'http' in error_str:
            if any(code in error_str for code in ['404', '403', '401']):
                return ErrorType.HTTP_ERROR, ErrorSeverity.HIGH
            elif any(code in error_str for code in ['500', '502', '503']):
                return ErrorType.HTTP_ERROR, ErrorSeverity.CRITICAL
            else:
                return ErrorType.HTTP_ERROR, ErrorSeverity.MEDIUM
        
        # Database errors
        if isinstance(error, (asyncpg.PostgresError, asyncpg.InterfaceError)):
            return ErrorType.DATABASE_ERROR, ErrorSeverity.HIGH
        
        # Timeout errors
        if 'timeout' in error_str or isinstance(error, asyncio.TimeoutError):
            return ErrorType.TIMEOUT_ERROR, ErrorSeverity.MEDIUM
        
        # Authentication errors
        if any(keyword in error_str for keyword in ['auth', 'credential', 'permission', 'unauthorized']):
            return ErrorType.AUTHENTICATION_ERROR, ErrorSeverity.HIGH
        
        # File errors
        if 'file not found' in error_str or isinstance(error, FileNotFoundError):
            return ErrorType.FILE_NOT_FOUND, ErrorSeverity.MEDIUM
        
        # Rate limiting
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429']):
            return ErrorType.RATE_LIMIT_ERROR, ErrorSeverity.MEDIUM
        
        # Parsing errors
        if any(keyword in error_str for keyword in ['parse', 'decode', 'json', 'xml']):
            return ErrorType.PARSING_ERROR, ErrorSeverity.MEDIUM
        
        # Validation errors
        if 'validation' in error_str or 'invalid' in error_str:
            return ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW
        
        # Disk space
        if 'disk' in error_str or 'space' in error_str:
            return ErrorType.DISK_SPACE_ERROR, ErrorSeverity.CRITICAL
        
        # SFTP errors
        if 'sftp' in error_str or 'ssh' in error_str:
            return ErrorType.SFTP_ERROR, ErrorSeverity.MEDIUM
        
        return ErrorType.UNKNOWN_ERROR, ErrorSeverity.MEDIUM
    
    async def record_error(self, error: Exception, source: str, operation: str, 
                          context: Dict[str, Any] = None) -> str:
        """Record an error and return error ID"""
        error_type, severity = self.classify_error(error, context)
        
        # Generate error ID
        error_id = hashlib.md5(
            f"{source}_{operation}_{error_type.value}_{str(error)}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Create error record
        error_record = ErrorRecord(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            source=source,
            operation=operation,
            message=str(error),
            details=context or {},
            stack_trace=traceback.format_exc(),
            timestamp=datetime.now()
        )
        
        # Store in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fl_error_records 
                (error_id, error_type, severity, source, operation, message, details, stack_trace, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, error_record.error_id, error_record.error_type.value, error_record.severity.value,
                error_record.source, error_record.operation, error_record.message,
                json.dumps(error_record.details), error_record.stack_trace, error_record.timestamp)
            
            # Update statistics
            await conn.execute("""
                INSERT INTO fl_error_statistics (date, error_type, source, count, severity_counts)
                VALUES (CURRENT_DATE, $1, $2, 1, $3)
                ON CONFLICT (date, error_type, source)
                DO UPDATE SET 
                    count = fl_error_statistics.count + 1,
                    severity_counts = $3
            """, error_record.error_type.value, error_record.source, 
                json.dumps({severity.value: 1}))
        
        # Add to active errors
        self.active_errors[error_id] = error_record
        
        # Update stats
        self.error_stats["total_errors"] += 1
        self.error_stats["errors_by_type"][error_type.value] = \
            self.error_stats["errors_by_type"].get(error_type.value, 0) + 1
        self.error_stats["errors_by_source"][source] = \
            self.error_stats["errors_by_source"].get(source, 0) + 1
        
        # Update circuit breaker
        await self._update_circuit_breaker(source, success=False)
        
        # Check if critical error notification is needed
        if severity == ErrorSeverity.CRITICAL:
            await self._send_critical_error_notification(error_record)
        
        logger.error(f"Recorded {severity.value} {error_type.value} for {source}: {str(error)}")
        return error_id
    
    async def _update_circuit_breaker(self, source: str, success: bool):
        """Update circuit breaker state"""
        if source not in self.circuit_breakers:
            self.circuit_breakers[source] = CircuitBreakerState(
                **self.config["circuit_breaker"]
            )
        
        breaker = self.circuit_breakers[source]
        
        if success:
            breaker.success_count += 1
            breaker.last_success = datetime.now()
            
            # Check if we can close the circuit
            if breaker.state == "HALF_OPEN" and breaker.success_count >= breaker.success_threshold:
                breaker.state = "CLOSED"
                breaker.failure_count = 0
                logger.info(f"Circuit breaker for {source} closed after {breaker.success_count} successes")
        else:
            breaker.failure_count += 1
            breaker.success_count = 0
            breaker.last_failure = datetime.now()
            
            # Check if we need to open the circuit
            if breaker.state == "CLOSED" and breaker.failure_count >= breaker.failure_threshold:
                breaker.state = "OPEN"
                logger.warning(f"Circuit breaker for {source} opened after {breaker.failure_count} failures")
            elif breaker.state == "HALF_OPEN":
                breaker.state = "OPEN"
                logger.warning(f"Circuit breaker for {source} reopened after failure in HALF_OPEN state")
        
        # Check if we can transition to HALF_OPEN
        if (breaker.state == "OPEN" and 
            breaker.last_failure and 
            (datetime.now() - breaker.last_failure).seconds >= breaker.recovery_timeout):
            breaker.state = "HALF_OPEN"
            logger.info(f"Circuit breaker for {source} transitioned to HALF_OPEN")
        
        # Update in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fl_circuit_breaker_states 
                (source, failure_count, success_count, last_failure, last_success, state, 
                 failure_threshold, recovery_timeout, success_threshold, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                ON CONFLICT (source)
                DO UPDATE SET
                    failure_count = $2,
                    success_count = $3,
                    last_failure = $4,
                    last_success = $5,
                    state = $6,
                    updated_at = NOW()
            """, source, breaker.failure_count, breaker.success_count,
                breaker.last_failure, breaker.last_success, breaker.state,
                breaker.failure_threshold, breaker.recovery_timeout, breaker.success_threshold)
    
    def should_allow_operation(self, source: str) -> bool:
        """Check if operation should be allowed based on circuit breaker state"""
        if source not in self.circuit_breakers:
            return True
        
        breaker = self.circuit_breakers[source]
        
        if breaker.state == "CLOSED":
            return True
        elif breaker.state == "OPEN":
            # Check if recovery timeout has passed
            if (breaker.last_failure and 
                (datetime.now() - breaker.last_failure).seconds >= breaker.recovery_timeout):
                breaker.state = "HALF_OPEN"
                return True
            return False
        elif breaker.state == "HALF_OPEN":
            return True
        
        return True
    
    def get_retry_config(self, error_type: ErrorType) -> RetryConfig:
        """Get retry configuration for error type"""
        return self.config["retry_configs"].get(
            error_type.value, 
            self.config["retry_configs"]["default"]
        )
    
    async def should_retry(self, error_id: str) -> bool:
        """Determine if an error should be retried"""
        if error_id not in self.active_errors:
            return False
        
        error = self.active_errors[error_id]
        retry_config = self.get_retry_config(error.error_type)
        
        # Check retry limit
        if error.retry_count >= retry_config.max_attempts:
            return False
        
        # Check circuit breaker
        if not self.should_allow_operation(error.source):
            logger.info(f"Circuit breaker open for {error.source}, skipping retry")
            return False
        
        return True
    
    def calculate_retry_delay(self, error_type: ErrorType, retry_count: int) -> float:
        """Calculate delay before next retry"""
        retry_config = self.get_retry_config(error_type)
        
        # Exponential backoff
        delay = retry_config.base_delay * (retry_config.exponential_base ** retry_count)
        delay *= retry_config.backoff_multiplier
        
        # Cap at maximum delay
        delay = min(delay, retry_config.max_delay)
        
        # Add jitter if configured
        if retry_config.jitter:
            import random
            jitter = random.uniform(0.5, 1.5)
            delay *= jitter
        
        return delay
    
    async def execute_with_retry(self, func: Callable, source: str, operation: str,
                               *args, **kwargs) -> Any:
        """Execute function with automatic retry logic"""
        retry_count = 0
        last_error = None
        
        while True:
            try:
                # Check circuit breaker
                if not self.should_allow_operation(source):
                    raise Exception(f"Circuit breaker open for {source}")
                
                # Execute function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Record success
                await self._update_circuit_breaker(source, success=True)
                self.error_stats["recovery_successes"] += 1
                
                # Mark any previous errors as resolved
                if last_error:
                    await self.resolve_error(last_error)
                
                return result
                
            except Exception as error:
                # Record error
                error_id = await self.record_error(error, source, operation, {
                    "retry_count": retry_count,
                    "function": func.__name__ if hasattr(func, '__name__') else str(func)
                })
                
                last_error = error_id
                
                # Check if we should retry
                if not await self.should_retry(error_id):
                    # Determine recovery action
                    recovery_action = self._determine_recovery_action(error_id)
                    await self._execute_recovery_action(error_id, recovery_action)
                    raise error
                
                # Calculate delay and wait
                error_type, _ = self.classify_error(error)
                delay = self.calculate_retry_delay(error_type, retry_count)
                
                logger.info(f"Retrying {operation} for {source} in {delay:.2f}s (attempt {retry_count + 1})")
                await asyncio.sleep(delay)
                
                retry_count += 1
                self.error_stats["retry_attempts"] += 1
                
                # Update retry count in database
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE fl_error_records 
                        SET retry_count = $1 
                        WHERE error_id = $2
                    """, retry_count, error_id)
    
    def _determine_recovery_action(self, error_id: str) -> RecoveryAction:
        """Determine appropriate recovery action for error"""
        if error_id not in self.active_errors:
            return RecoveryAction.SKIP
        
        error = self.active_errors[error_id]
        strategies = self.config["recovery_strategies"].get(
            error.error_type.value,
            self.config["recovery_strategies"]["default"]
        )
        
        # Return first strategy (most preferred)
        return strategies[0] if strategies else RecoveryAction.SKIP
    
    async def _execute_recovery_action(self, error_id: str, action: RecoveryAction):
        """Execute recovery action for error"""
        if error_id not in self.active_errors:
            return
        
        error = self.active_errors[error_id]
        error.recovery_action = action
        
        logger.info(f"Executing recovery action {action.value} for error {error_id}")
        
        if action == RecoveryAction.SKIP:
            # Mark as resolved but record that it was skipped
            await self.resolve_error(error_id, note="Skipped due to recovery action")
        
        elif action == RecoveryAction.ABORT:
            # Mark as resolved and stop related operations
            await self.resolve_error(error_id, note="Aborted due to recovery action")
            # Could trigger broader system halt if needed
        
        elif action == RecoveryAction.FALLBACK:
            # Could implement fallback data source logic here
            logger.info(f"Fallback action needed for {error.source} - {error.operation}")
        
        elif action == RecoveryAction.MANUAL_INTERVENTION:
            # Send notification for manual review
            await self._send_manual_intervention_notification(error)
        
        # Update in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE fl_error_records 
                SET recovery_action = $1 
                WHERE error_id = $2
            """, action.value, error_id)
    
    async def resolve_error(self, error_id: str, note: str = None):
        """Mark error as resolved"""
        if error_id not in self.active_errors:
            return
        
        error = self.active_errors[error_id]
        error.resolved = True
        
        # Update in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE fl_error_records 
                SET resolved = TRUE, resolved_at = NOW()
                WHERE error_id = $1
            """, error_id)
        
        # Remove from active errors
        del self.active_errors[error_id]
        
        # Update stats
        self.error_stats["resolved_errors"] += 1
        self.error_stats["unresolved_errors"] = len(self.active_errors)
        
        logger.info(f"Resolved error {error_id}" + (f": {note}" if note else ""))
    
    async def _send_critical_error_notification(self, error: ErrorRecord):
        """Send notification for critical errors"""
        if not self.config["notifications"]["critical_errors"]:
            return
        
        try:
            subject = f"CRITICAL ERROR - Florida Data System - {error.source}"
            body = f"""
            Critical Error Detected:
            
            Source: {error.source}
            Operation: {error.operation}
            Error Type: {error.error_type.value}
            Message: {error.message}
            Time: {error.timestamp}
            
            Details:
            {json.dumps(error.details, indent=2)}
            
            Stack Trace:
            {error.stack_trace}
            """
            
            # Send email if configured
            if self.config["notifications"]["email_recipients"]:
                await self._send_email_notification(subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send critical error notification: {e}")
    
    async def _send_manual_intervention_notification(self, error: ErrorRecord):
        """Send notification requesting manual intervention"""
        try:
            subject = f"Manual Intervention Required - Florida Data System - {error.source}"
            body = f"""
            Manual Intervention Required:
            
            Error ID: {error.error_id}
            Source: {error.source}
            Operation: {error.operation}
            Error Type: {error.error_type.value}
            Message: {error.message}
            Retry Count: {error.retry_count}
            Time: {error.timestamp}
            
            This error requires manual review and resolution.
            """
            
            # Send email if configured
            if self.config["notifications"]["email_recipients"]:
                await self._send_email_notification(subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send manual intervention notification: {e}")
    
    async def _send_email_notification(self, subject: str, body: str):
        """Send email notification"""
        # This would implement email sending logic
        # Placeholder for now
        logger.info(f"Email notification: {subject}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        return {
            "current_stats": self.error_stats.copy(),
            "active_errors": len(self.active_errors),
            "circuit_breaker_states": {
                source: {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count,
                    "success_count": breaker.success_count
                }
                for source, breaker in self.circuit_breakers.items()
            }
        }
    
    async def get_recent_errors(self, hours: int = 24, severity: ErrorSeverity = None) -> List[ErrorRecord]:
        """Get recent errors from database"""
        async with self.pool.acquire() as conn:
            if severity:
                rows = await conn.fetch("""
                    SELECT * FROM fl_error_records 
                    WHERE timestamp > NOW() - INTERVAL '%s hours' AND severity = $1
                    ORDER BY timestamp DESC
                """, hours, severity.value)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM fl_error_records 
                    WHERE timestamp > NOW() - INTERVAL '%s hours'
                    ORDER BY timestamp DESC
                """, hours)
        
        errors = []
        for row in rows:
            error = ErrorRecord(
                error_id=row['error_id'],
                error_type=ErrorType(row['error_type']),
                severity=ErrorSeverity(row['severity']),
                source=row['source'],
                operation=row['operation'],
                message=row['message'],
                details=row['details'] or {},
                stack_trace=row['stack_trace'] or "",
                timestamp=row['timestamp'],
                retry_count=row['retry_count'],
                resolved=row['resolved'],
                recovery_action=RecoveryAction(row['recovery_action']) if row['recovery_action'] else None
            )
            errors.append(error)
        
        return errors

def with_error_handling(source: str, operation: str):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need access to error handler instance
            # Implementation depends on how this is integrated
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {operation} for {source}: {e}")
                raise
        return wrapper
    return decorator

async def main():
    """Test the error handler"""
    print("Testing Florida Error Handler...")
    
    async with FloridaErrorHandler() as handler:
        # Test error classification
        test_errors = [
            ConnectionError("Network unreachable"),
            aiohttp.ClientError("HTTP 404 Not Found"),
            asyncio.TimeoutError("Request timeout"),
            ValueError("Invalid data format"),
            FileNotFoundError("File not found")
        ]
        
        for error in test_errors:
            error_type, severity = handler.classify_error(error)
            print(f"  {type(error).__name__}: {error_type.value} ({severity.value})")
        
        # Test retry logic
        async def test_function():
            raise ConnectionError("Test connection error")
        
        try:
            await handler.execute_with_retry(test_function, "test_source", "test_operation")
        except Exception as e:
            print(f"Final error: {e}")
        
        # Show statistics
        stats = handler.get_error_statistics()
        print(f"\nError Statistics:")
        print(json.dumps(stats, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())