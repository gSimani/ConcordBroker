"""
Comprehensive Logging System for ConcordBroker
Based on Self-Improving Agent principles for debugging and monitoring
"""

import logging
import json
import traceback
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import asyncio
from functools import wraps
import os
import sys

# Create logs directory if it doesn't exist
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


class LogLevel(Enum):
    """Extended log levels for comprehensive tracking"""
    TRACE = 5      # Detailed execution trace
    DEBUG = 10     # Debug information
    INFO = 20      # General information
    DECISION = 25  # Agent decisions
    WARNING = 30   # Warning messages
    ERROR = 40     # Error messages
    CRITICAL = 50  # Critical errors requiring immediate attention
    ESCALATION = 60  # Human escalation required


# Add custom log levels
logging.addLevelName(LogLevel.TRACE.value, "TRACE")
logging.addLevelName(LogLevel.DECISION.value, "DECISION")
logging.addLevelName(LogLevel.ESCALATION.value, "ESCALATION")


class StructuredLogger:
    """
    Structured logger with comprehensive tracking capabilities
    """
    
    def __init__(self, name: str, log_to_file: bool = True):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(LogLevel.TRACE.value)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler with color coding
        console_handler = ColoredConsoleHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-10s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handlers
        if log_to_file:
            # Detailed log file (all levels)
            detailed_handler = logging.FileHandler(
                f"{LOGS_DIR}/{name}_detailed_{datetime.now().strftime('%Y%m%d')}.log"
            )
            detailed_handler.setLevel(LogLevel.TRACE.value)
            detailed_formatter = JsonFormatter()
            detailed_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(detailed_handler)
            
            # Error log file (errors and above)
            error_handler = logging.FileHandler(
                f"{LOGS_DIR}/{name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = JsonFormatter(include_traceback=True)
            error_handler.setFormatter(error_formatter)
            self.logger.addHandler(error_handler)
            
            # Decision log file (decisions and escalations)
            decision_handler = logging.FileHandler(
                f"{LOGS_DIR}/{name}_decisions_{datetime.now().strftime('%Y%m%d')}.log"
            )
            decision_handler.setLevel(LogLevel.DECISION.value)
            decision_handler.addFilter(DecisionFilter())
            decision_formatter = JsonFormatter()
            decision_handler.setFormatter(decision_formatter)
            self.logger.addHandler(decision_handler)
        
        # Operation context stack
        self.context_stack = []
        
    def trace(self, message: str, **kwargs):
        """Log trace-level debugging information"""
        self._log(LogLevel.TRACE.value, message, **kwargs)
        
    def debug(self, message: str, **kwargs):
        """Log debug information"""
        self._log(logging.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log general information"""
        self._log(logging.INFO, message, **kwargs)
        
    def decision(self, message: str, confidence: float = None, **kwargs):
        """Log agent decision"""
        if confidence is not None:
            kwargs['confidence'] = confidence
        self._log(LogLevel.DECISION.value, message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning"""
        self._log(logging.WARNING, message, **kwargs)
        
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Log error with optional exception"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['traceback'] = traceback.format_exc()
        self._log(logging.ERROR, message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log critical error"""
        self._log(logging.CRITICAL, message, **kwargs)
        
    def escalation(self, message: str, reason: str, **kwargs):
        """Log human escalation requirement"""
        kwargs['escalation_reason'] = reason
        self._log(LogLevel.ESCALATION.value, message, **kwargs)
        
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with context"""
        # Add context to kwargs
        if self.context_stack:
            kwargs['context'] = self.context_stack.copy()
        
        # Create extra dict for structured logging
        extra = {'structured_data': kwargs}
        
        self.logger.log(level, message, extra=extra)
        
    @contextmanager
    def operation_context(self, operation: str, **kwargs):
        """
        Context manager for tracking operations
        Usage:
            with logger.operation_context("fetch_property", parcel_id="123"):
                # operation code
        """
        operation_id = f"{operation}_{datetime.now().timestamp()}"
        context = {
            'operation': operation,
            'operation_id': operation_id,
            'start_time': datetime.now().isoformat(),
            **kwargs
        }
        
        self.context_stack.append(context)
        self.trace(f"Starting operation: {operation}", operation_id=operation_id)
        
        try:
            yield operation_id
            
            # Log successful completion
            end_time = datetime.now()
            context['end_time'] = end_time.isoformat()
            context['duration'] = (end_time - datetime.fromisoformat(context['start_time'])).total_seconds()
            context['status'] = 'success'
            
            self.trace(f"Completed operation: {operation}", 
                      operation_id=operation_id,
                      duration=context['duration'])
            
        except Exception as e:
            # Log failure
            end_time = datetime.now()
            context['end_time'] = end_time.isoformat()
            context['duration'] = (end_time - datetime.fromisoformat(context['start_time'])).total_seconds()
            context['status'] = 'failed'
            context['error'] = str(e)
            
            self.error(f"Failed operation: {operation}",
                      exception=e,
                      operation_id=operation_id,
                      duration=context['duration'])
            raise
            
        finally:
            self.context_stack.pop()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def __init__(self, include_traceback: bool = False):
        super().__init__()
        self.include_traceback = include_traceback
        
    def format(self, record):
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add structured data if present
        if hasattr(record, 'structured_data'):
            log_data['data'] = record.structured_data
            
        # Add exception info if present
        if record.exc_info and self.include_traceback:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'TRACE': '\033[90m',     # Gray
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'DECISION': '\033[35m',  # Magenta
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[91m',  # Bright Red
        'ESCALATION': '\033[95m' # Bright Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        
        # Add structured data summary if present
        if hasattr(record, 'structured_data') and record.structured_data:
            # Create a summary of key data
            summary_items = []
            for key, value in record.structured_data.items():
                if key not in ['context', 'traceback']:  # Skip large fields
                    if isinstance(value, (str, int, float, bool)):
                        summary_items.append(f"{key}={value}")
            
            if summary_items:
                record.msg += f" | {' '.join(summary_items[:3])}"  # Show first 3 items
                
        return super().format(record)


class ColoredConsoleHandler(logging.StreamHandler):
    """Console handler with color support"""
    
    def __init__(self):
        super().__init__(sys.stdout)


class DecisionFilter(logging.Filter):
    """Filter for decision and escalation logs"""
    
    def filter(self, record):
        return record.levelno in [LogLevel.DECISION.value, LogLevel.ESCALATION.value]


# Decorator for logging function execution
def log_execution(logger: StructuredLogger):
    """
    Decorator to automatically log function execution
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            
            with logger.operation_context(f"function_{func_name}", 
                                         args=str(args)[:100],
                                         kwargs=str(kwargs)[:100]):
                try:
                    result = await func(*args, **kwargs)
                    logger.trace(f"Function {func_name} returned successfully")
                    return result
                except Exception as e:
                    logger.error(f"Function {func_name} failed", exception=e)
                    raise
                    
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            
            with logger.operation_context(f"function_{func_name}",
                                         args=str(args)[:100],
                                         kwargs=str(kwargs)[:100]):
                try:
                    result = func(*args, **kwargs)
                    logger.trace(f"Function {func_name} returned successfully")
                    return result
                except Exception as e:
                    logger.error(f"Function {func_name} failed", exception=e)
                    raise
                    
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


class MetricsLogger:
    """Logger for tracking performance metrics"""
    
    def __init__(self, name: str):
        self.logger = StructuredLogger(f"metrics.{name}")
        self.metrics = {}
        
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        self.logger.info(f"Metric: {metric_name}",
                        metric=metric_name,
                        value=value,
                        tags=tags or {})
        
        # Store for aggregation
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            'value': value,
            'timestamp': datetime.now(),
            'tags': tags or {}
        })
        
    def record_timing(self, operation: str, duration: float):
        """Record operation timing"""
        self.record_metric(f"{operation}_duration", duration, {'unit': 'seconds'})
        
    def record_count(self, event: str, count: int = 1):
        """Record event count"""
        self.record_metric(f"{event}_count", count, {'type': 'counter'})
        
    def record_gauge(self, name: str, value: float):
        """Record gauge value (current state)"""
        self.record_metric(f"{name}_gauge", value, {'type': 'gauge'})
        
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                metric_values = [v['value'] for v in values]
                summary[metric_name] = {
                    'count': len(metric_values),
                    'sum': sum(metric_values),
                    'avg': sum(metric_values) / len(metric_values),
                    'min': min(metric_values),
                    'max': max(metric_values),
                    'latest': metric_values[-1]
                }
                
        return summary


# Global logger instances
def get_logger(name: str) -> StructuredLogger:
    """Get or create a logger instance"""
    return StructuredLogger(name)


def get_metrics_logger(name: str) -> MetricsLogger:
    """Get or create a metrics logger instance"""
    return MetricsLogger(name)


# Example usage for ConcordBroker
class PropertyOperationLogger:
    """Example of comprehensive logging for property operations"""
    
    def __init__(self):
        self.logger = get_logger("property_operations")
        self.metrics = get_metrics_logger("property_operations")
        
    @log_execution(get_logger("property_operations"))
    async def fetch_property(self, parcel_id: str) -> Dict[str, Any]:
        """Example operation with comprehensive logging"""
        
        with self.logger.operation_context("fetch_property", parcel_id=parcel_id):
            # Log decision
            self.logger.decision("Fetching property data", 
                               confidence=0.95,
                               parcel_id=parcel_id)
            
            # Simulate database operation
            self.logger.trace("Querying database")
            
            # Track metrics
            start = datetime.now()
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            # Record timing
            duration = (datetime.now() - start).total_seconds()
            self.metrics.record_timing("property_fetch", duration)
            
            # Log successful fetch
            self.logger.info("Property fetched successfully",
                           parcel_id=parcel_id,
                           duration=duration)
            
            return {"parcel_id": parcel_id, "data": "example"}
            
    async def update_property(self, parcel_id: str, updates: Dict[str, Any]):
        """Example of operation requiring escalation"""
        
        with self.logger.operation_context("update_property",
                                          parcel_id=parcel_id,
                                          update_count=len(updates)):
            
            # Check confidence
            confidence = 0.65  # Below threshold
            
            self.logger.decision("Property update requested",
                               confidence=confidence,
                               parcel_id=parcel_id)
            
            if confidence < 0.7:
                self.logger.escalation(
                    "Property update requires human approval",
                    reason=f"Low confidence: {confidence}",
                    parcel_id=parcel_id,
                    updates=updates
                )
                raise Exception("Human escalation required")
                
            # Continue with update...
            self.logger.info("Property updated", parcel_id=parcel_id)


if __name__ == "__main__":
    # Demonstrate comprehensive logging
    async def test_logging():
        ops = PropertyOperationLogger()
        
        # Test successful operation
        await ops.fetch_property("1234567890")
        
        # Test operation requiring escalation
        try:
            await ops.update_property("1234567890", {"value": 1000000})
        except Exception:
            pass
        
        # Show metrics summary
        print("\nMetrics Summary:")
        print(json.dumps(ops.metrics.get_summary(), indent=2))
    
    asyncio.run(test_logging())