#!/usr/bin/env python3
"""
NAL Monitoring Agent
===================
Real-time monitoring and metrics agent for NAL import pipeline.
Tracks performance, resource usage, and provides operational insights.
"""

import asyncio
import logging
import time
import json
import os
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
from collections import deque
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    records_processed: int
    records_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    active_connections: int
    queue_depth: int
    error_rate: float

@dataclass
class ResourceAlert:
    """Resource usage alert"""
    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    current_value: float
    threshold_value: float
    recommendations: List[str]

class NALMonitoringAgent:
    """
    Agent specialized in monitoring NAL import pipeline performance and resources
    
    Features:
    - Real-time performance metrics collection
    - Resource usage monitoring (CPU, memory, disk, network)
    - Progress tracking and ETA calculations
    - Alert generation for resource thresholds
    - Performance visualization and reporting
    - Bottleneck identification and recommendations
    """
    
    def __init__(self):
        # Monitoring configuration
        self.monitoring_interval = 5.0  # seconds
        self.metrics_retention_hours = 24
        self.max_metrics_points = int((self.metrics_retention_hours * 3600) / self.monitoring_interval)
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=self.max_metrics_points)
        self.alerts: List[ResourceAlert] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.start_time = None
        
        # Resource thresholds
        self.resource_thresholds = {
            'memory_usage_percent': 85.0,
            'cpu_usage_percent': 90.0,
            'disk_usage_percent': 90.0,
            'error_rate_percent': 5.0,
            'queue_depth_max': 100
        }
        
        # Performance baselines
        self.performance_baselines = {
            'min_records_per_second': 100,
            'max_batch_time_seconds': 30,
            'max_error_rate_percent': 2.0
        }
        
        # System information
        self.system_info = self._collect_system_info()
        
        logger.info("NAL Monitoring Agent initialized")
        logger.info(f"System info: {self.system_info}")
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect static system information"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'total_memory_gb': round(memory.total / (1024**3), 2),
                'total_disk_gb': round(disk.total / (1024**3), 2),
                'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                'platform': os.name,
                'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
            }
        except Exception as e:
            logger.warning(f"Failed to collect system info: {e}")
            return {'error': str(e)}
    
    async def start_monitoring(self, import_status_ref: Any = None):
        """Start monitoring the import pipeline"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.start_time = datetime.now()
        self.import_status_ref = import_status_ref
        
        # Start monitoring in background thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info("Monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        logger.info("Monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop (runs in background thread)"""
        logger.debug("Monitoring loop started")
        
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = self._collect_current_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                self._check_resource_alerts(metrics)
                
                # Log periodic status
                if len(self.metrics_history) % 12 == 0:  # Every minute if 5s interval
                    self._log_periodic_status(metrics)
                
                # Wait for next interval
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitoring_interval)
        
        logger.debug("Monitoring loop stopped")
    
    def _collect_current_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        timestamp = datetime.now()
        
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0
            
            # Import-specific metrics
            if hasattr(self, 'import_status_ref') and self.import_status_ref:
                records_processed = getattr(self.import_status_ref, 'processed_records', 0)
                error_rate = self._calculate_error_rate()
            else:
                records_processed = 0
                error_rate = 0.0
            
            # Calculate records per second
            records_per_second = self._calculate_records_per_second(records_processed)
            
            # Network connections (approximate)
            try:
                connections = len(psutil.net_connections(kind='tcp'))
            except:
                connections = 0
            
            metrics = PerformanceMetrics(
                timestamp=timestamp,
                records_processed=records_processed,
                records_per_second=records_per_second,
                memory_usage_mb=memory.used / (1024**2),
                cpu_usage_percent=cpu_percent,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                active_connections=connections,
                queue_depth=0,  # Would be set by queue monitoring
                error_rate=error_rate
            )
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Failed to collect metrics: {e}")
            return PerformanceMetrics(
                timestamp=timestamp,
                records_processed=0,
                records_per_second=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                active_connections=0,
                queue_depth=0,
                error_rate=0.0
            )
    
    def _calculate_records_per_second(self, current_records: int) -> float:
        """Calculate current records processing rate"""
        if not self.start_time or current_records == 0:
            return 0.0
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        if elapsed_time <= 0:
            return 0.0
        
        return current_records / elapsed_time
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate percentage"""
        if hasattr(self, 'import_status_ref') and self.import_status_ref:
            processed = getattr(self.import_status_ref, 'processed_records', 0)
            failed = getattr(self.import_status_ref, 'failed_records', 0)
            
            if processed > 0:
                return (failed / processed) * 100
        
        return 0.0
    
    def _check_resource_alerts(self, metrics: PerformanceMetrics):
        """Check for resource threshold violations and generate alerts"""
        
        # Memory usage alert
        memory_percent = (metrics.memory_usage_mb / (self.system_info.get('total_memory_gb', 1) * 1024)) * 100
        
        if memory_percent > self.resource_thresholds['memory_usage_percent']:
            self._create_alert(
                'memory_usage',
                'high',
                f"Memory usage at {memory_percent:.1f}%",
                memory_percent,
                self.resource_thresholds['memory_usage_percent'],
                [
                    "Reduce batch size to lower memory usage",
                    "Monitor for memory leaks in processing",
                    "Consider increasing system memory"
                ]
            )
        
        # CPU usage alert
        if metrics.cpu_usage_percent > self.resource_thresholds['cpu_usage_percent']:
            self._create_alert(
                'cpu_usage',
                'high',
                f"CPU usage at {metrics.cpu_usage_percent:.1f}%",
                metrics.cpu_usage_percent,
                self.resource_thresholds['cpu_usage_percent'],
                [
                    "Reduce worker thread count",
                    "Check for inefficient processing logic",
                    "Consider distributed processing"
                ]
            )
        
        # Error rate alert
        if metrics.error_rate > self.resource_thresholds['error_rate_percent']:
            self._create_alert(
                'error_rate',
                'medium',
                f"Error rate at {metrics.error_rate:.1f}%",
                metrics.error_rate,
                self.resource_thresholds['error_rate_percent'],
                [
                    "Review error logs for patterns",
                    "Check data quality issues",
                    "Verify database connectivity"
                ]
            )
        
        # Performance alert
        if (metrics.records_per_second > 0 and 
            metrics.records_per_second < self.performance_baselines['min_records_per_second']):
            self._create_alert(
                'performance',
                'medium',
                f"Processing speed at {metrics.records_per_second:.1f} records/second",
                metrics.records_per_second,
                self.performance_baselines['min_records_per_second'],
                [
                    "Check for database bottlenecks",
                    "Optimize batch size",
                    "Review parallel processing configuration"
                ]
            )
    
    def _create_alert(self, alert_type: str, severity: str, message: str, 
                     current_value: float, threshold_value: float, 
                     recommendations: List[str]):
        """Create a new alert if not already active"""
        
        # Check if similar alert already exists (avoid spam)
        recent_alerts = [
            alert for alert in self.alerts[-10:]  # Check last 10 alerts
            if alert.alert_type == alert_type and 
            (datetime.now() - alert.timestamp).total_seconds() < 300  # Within 5 minutes
        ]
        
        if recent_alerts:
            return  # Don't create duplicate alerts
        
        alert = ResourceAlert(
            alert_id=f"{alert_type}_{int(time.time())}",
            timestamp=datetime.now(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=current_value,
            threshold_value=threshold_value,
            recommendations=recommendations
        )
        
        self.alerts.append(alert)
        
        # Log alert
        log_level = getattr(logger, severity.lower(), logger.info)
        log_level(f"ALERT: {message} | Recommendations: {'; '.join(recommendations)}")
    
    def _log_periodic_status(self, metrics: PerformanceMetrics):
        """Log periodic status summary"""
        
        memory_percent = (metrics.memory_usage_mb / (self.system_info.get('total_memory_gb', 1) * 1024)) * 100
        
        status_message = (
            f"Status: {metrics.records_processed:,} records processed "
            f"| Rate: {metrics.records_per_second:.1f} rec/s "
            f"| Memory: {memory_percent:.1f}% "
            f"| CPU: {metrics.cpu_usage_percent:.1f}% "
            f"| Errors: {metrics.error_rate:.1f}%"
        )
        
        logger.info(status_message)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_summary(self, last_minutes: int = 10) -> Dict[str, Any]:
        """Get summary of metrics for specified time period"""
        
        if not self.metrics_history:
            return {}
        
        # Filter metrics by time period
        cutoff_time = datetime.now() - timedelta(minutes=last_minutes)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            recent_metrics = list(self.metrics_history)[-min(120, len(self.metrics_history)):]  # Last 120 points
        
        if not recent_metrics:
            return {}
        
        # Calculate summary statistics
        records_per_second_values = [m.records_per_second for m in recent_metrics]
        memory_values = [m.memory_usage_mb for m in recent_metrics]
        cpu_values = [m.cpu_usage_percent for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        
        summary = {
            'time_period_minutes': last_minutes,
            'data_points': len(recent_metrics),
            'performance': {
                'avg_records_per_second': sum(records_per_second_values) / len(records_per_second_values) if records_per_second_values else 0,
                'max_records_per_second': max(records_per_second_values) if records_per_second_values else 0,
                'min_records_per_second': min(records_per_second_values) if records_per_second_values else 0,
                'current_records_per_second': recent_metrics[-1].records_per_second if recent_metrics else 0
            },
            'resources': {
                'avg_memory_mb': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max_memory_mb': max(memory_values) if memory_values else 0,
                'avg_cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max_cpu_percent': max(cpu_values) if cpu_values else 0
            },
            'quality': {
                'avg_error_rate': sum(error_rates) / len(error_rates) if error_rates else 0,
                'max_error_rate': max(error_rates) if error_rates else 0,
                'current_error_rate': recent_metrics[-1].error_rate if recent_metrics else 0
            },
            'active_alerts': len([a for a in self.alerts[-10:] if (datetime.now() - a.timestamp).total_seconds() < 300])
        }
        
        return summary
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends"""
        
        if len(self.metrics_history) < 10:
            return {'insufficient_data': True}
        
        # Split history into two halves for trend analysis
        mid_point = len(self.metrics_history) // 2
        first_half = list(self.metrics_history)[:mid_point]
        second_half = list(self.metrics_history)[mid_point:]
        
        def avg_metric(metrics_list, attr):
            values = [getattr(m, attr) for m in metrics_list]
            return sum(values) / len(values) if values else 0
        
        first_avg_rps = avg_metric(first_half, 'records_per_second')
        second_avg_rps = avg_metric(second_half, 'records_per_second')
        
        first_avg_memory = avg_metric(first_half, 'memory_usage_mb')
        second_avg_memory = avg_metric(second_half, 'memory_usage_mb')
        
        first_avg_cpu = avg_metric(first_half, 'cpu_usage_percent')
        second_avg_cpu = avg_metric(second_half, 'cpu_usage_percent')
        
        trends = {
            'performance_trend': {
                'direction': 'improving' if second_avg_rps > first_avg_rps else 'degrading',
                'change_percent': ((second_avg_rps - first_avg_rps) / first_avg_rps * 100) if first_avg_rps > 0 else 0
            },
            'memory_trend': {
                'direction': 'increasing' if second_avg_memory > first_avg_memory else 'stable',
                'change_percent': ((second_avg_memory - first_avg_memory) / first_avg_memory * 100) if first_avg_memory > 0 else 0
            },
            'cpu_trend': {
                'direction': 'increasing' if second_avg_cpu > first_avg_cpu else 'stable',
                'change_percent': ((second_avg_cpu - first_avg_cpu) / first_avg_cpu * 100) if first_avg_cpu > 0 else 0
            }
        }
        
        return trends
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        current_metrics = self.get_current_metrics()
        metrics_summary = self.get_metrics_summary(30)  # Last 30 minutes
        trends = self.get_performance_trends()
        
        # Calculate uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'uptime_seconds': uptime_seconds,
            'uptime_formatted': str(timedelta(seconds=int(uptime_seconds))),
            'current_metrics': asdict(current_metrics) if current_metrics else None,
            'metrics_summary': metrics_summary,
            'performance_trends': trends,
            'recent_alerts': [asdict(alert) for alert in self.alerts[-10:]],
            'resource_thresholds': self.resource_thresholds,
            'performance_baselines': self.performance_baselines,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return recommendations
        
        metrics_summary = self.get_metrics_summary(10)
        if not metrics_summary:
            return recommendations
        
        # Performance recommendations
        avg_rps = metrics_summary.get('performance', {}).get('avg_records_per_second', 0)
        if avg_rps < self.performance_baselines['min_records_per_second']:
            recommendations.append(
                f"Performance below baseline ({avg_rps:.1f} < {self.performance_baselines['min_records_per_second']}). "
                "Consider increasing batch size or parallel workers."
            )
        
        # Memory recommendations
        total_memory_gb = self.system_info.get('total_memory_gb', 8)
        memory_usage_percent = (current_metrics.memory_usage_mb / (total_memory_gb * 1024)) * 100
        
        if memory_usage_percent > 70:
            recommendations.append(
                f"Memory usage high ({memory_usage_percent:.1f}%). "
                "Consider reducing batch size or optimizing memory usage."
            )
        
        # CPU recommendations
        if current_metrics.cpu_usage_percent > 80:
            recommendations.append(
                f"CPU usage high ({current_metrics.cpu_usage_percent:.1f}%). "
                "Consider reducing parallel workers or optimizing processing logic."
            )
        
        # Error rate recommendations
        if current_metrics.error_rate > 2.0:
            recommendations.append(
                f"Error rate elevated ({current_metrics.error_rate:.1f}%). "
                "Review error logs and data quality issues."
            )
        
        # General recommendations
        if not recommendations:
            if avg_rps > self.performance_baselines['min_records_per_second'] * 2:
                recommendations.append("Performance is excellent. Consider increasing batch size for even better throughput.")
            else:
                recommendations.append("System is performing within normal parameters.")
        
        return recommendations
    
    async def save_metrics_to_file(self, filename: str = None):
        """Save metrics history to JSON file"""
        
        if not filename:
            filename = f"nal_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            metrics_data = {
                'export_timestamp': datetime.now().isoformat(),
                'system_info': self.system_info,
                'metrics_count': len(self.metrics_history),
                'metrics': [asdict(m) for m in self.metrics_history],
                'alerts': [asdict(a) for a in self.alerts],
                'thresholds': self.resource_thresholds,
                'baselines': self.performance_baselines
            }
            
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"Metrics saved to: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    async def create_performance_charts(self, output_dir: str = "monitoring_charts"):
        """Create performance visualization charts"""
        
        if len(self.metrics_history) < 10:
            logger.warning("Insufficient data for chart creation")
            return
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Prepare data
            timestamps = [m.timestamp for m in self.metrics_history]
            records_per_second = [m.records_per_second for m in self.metrics_history]
            memory_usage = [m.memory_usage_mb for m in self.metrics_history]
            cpu_usage = [m.cpu_usage_percent for m in self.metrics_history]
            error_rates = [m.error_rate for m in self.metrics_history]
            
            # Set style
            plt.style.use('seaborn')
            sns.set_palette("husl")
            
            # Create performance chart
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('NAL Import Pipeline Performance Metrics', fontsize=16)
            
            # Records per second
            ax1.plot(timestamps, records_per_second, linewidth=2, color='blue')
            ax1.set_title('Processing Rate (Records/Second)')
            ax1.set_ylabel('Records/Second')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Memory usage
            ax2.plot(timestamps, memory_usage, linewidth=2, color='green')
            ax2.set_title('Memory Usage (MB)')
            ax2.set_ylabel('Memory (MB)')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # CPU usage
            ax3.plot(timestamps, cpu_usage, linewidth=2, color='orange')
            ax3.set_title('CPU Usage (%)')
            ax3.set_ylabel('CPU (%)')
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
            
            # Error rate
            ax4.plot(timestamps, error_rates, linewidth=2, color='red')
            ax4.set_title('Error Rate (%)')
            ax4.set_ylabel('Error Rate (%)')
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            chart_file = os.path.join(output_dir, f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Performance chart saved: {chart_file}")
            
        except Exception as e:
            logger.error(f"Failed to create performance charts: {e}")
    
    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get summary of recent alerts"""
        
        if not self.alerts:
            return {'total_alerts': 0, 'recent_alerts': 0, 'alert_types': {}}
        
        # Recent alerts (last hour)
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_alerts = [a for a in self.alerts if a.timestamp >= recent_cutoff]
        
        # Alert type distribution
        alert_types = {}
        for alert in self.alerts:
            alert_types[alert.alert_type] = alert_types.get(alert.alert_type, 0) + 1
        
        return {
            'total_alerts': len(self.alerts),
            'recent_alerts': len(recent_alerts),
            'alert_types': alert_types,
            'latest_alert': asdict(self.alerts[-1]) if self.alerts else None
        }