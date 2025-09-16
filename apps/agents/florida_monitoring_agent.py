#!/usr/bin/env python3
"""
Florida Monitoring Agent
Specialized agent for monitoring system health and generating alerts

Features:
- Real-time system monitoring and health checks
- Performance metrics collection and analysis
- Alert generation and notification system
- Historical trend analysis
- Resource usage monitoring
- Error tracking and escalation
- Custom dashboards and reporting
"""

import asyncio
import logging
import json
import smtplib
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import psutil
import statistics
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """System alert"""
    id: str
    severity: str  # info, warning, error, critical
    component: str
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

@dataclass
class MetricPoint:
    """Time-series metric point"""
    timestamp: datetime
    metric_name: str
    value: float
    tags: Dict[str, str]

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: str  # healthy, degraded, failed
    response_time_ms: float
    details: Dict[str, Any]
    timestamp: datetime

class FloridaMonitoringAgent:
    """Agent responsible for monitoring and alerting"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Monitoring configuration
        self.check_interval_seconds = self.config.get("monitoring", {}).get("check_interval_seconds", 60)
        self.metric_retention_days = self.config.get("monitoring", {}).get("metric_retention_days", 30)
        self.alert_cooldown_minutes = self.config.get("monitoring", {}).get("alert_cooldown_minutes", 15)
        
        # Alert thresholds
        self.thresholds = self.config.get("monitoring", {}).get("thresholds", {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "error_rate_percent": 10.0,
            "response_time_seconds": 30.0
        })
        
        # Notification settings
        self.notifications = self.config.get("monitoring", {}).get("notifications", {})
        
        # State tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.metrics_history: List[MetricPoint] = []
        self.health_check_history: List[HealthCheckResult] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            "total_alerts": 0,
            "critical_alerts": 0,
            "resolved_alerts": 0,
            "health_checks_performed": 0,
            "average_response_time": 0.0,
            "uptime_start": datetime.now()
        }

    async def initialize(self):
        """Initialize the monitoring agent"""
        logger.info("Initializing Florida Monitoring Agent...")
        
        # Load historical data if available
        await self._load_historical_data()
        
        # Validate notification configuration
        if self.notifications.get("email", {}).get("enabled"):
            await self._validate_email_config()
        
        if self.notifications.get("webhook", {}).get("enabled"):
            await self._validate_webhook_config()
        
        logger.info("✅ Florida Monitoring Agent initialized")

    async def cleanup(self):
        """Cleanup monitoring resources"""
        # Save historical data
        await self._save_historical_data()
        
        logger.info("✅ Florida Monitoring Agent cleanup complete")

    async def _load_historical_data(self):
        """Load historical monitoring data"""
        try:
            data_file = Path("monitoring_data.json")
            if data_file.exists():
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                # Load alerts
                for alert_data in data.get("alerts", []):
                    alert_data["timestamp"] = datetime.fromisoformat(alert_data["timestamp"])
                    if alert_data.get("resolved_at"):
                        alert_data["resolved_at"] = datetime.fromisoformat(alert_data["resolved_at"])
                    
                    alert = Alert(**alert_data)
                    if not alert.resolved:
                        self.active_alerts[alert.id] = alert
                
                # Load recent metrics
                for metric_data in data.get("metrics", []):
                    metric_data["timestamp"] = datetime.fromisoformat(metric_data["timestamp"])
                    self.metrics_history.append(MetricPoint(**metric_data))
                
                # Keep only recent data
                cutoff_date = datetime.now() - timedelta(days=self.metric_retention_days)
                self.metrics_history = [
                    m for m in self.metrics_history 
                    if m.timestamp > cutoff_date
                ]
                
                logger.info(f"Loaded {len(self.active_alerts)} active alerts and "
                           f"{len(self.metrics_history)} metric points")
                
        except Exception as e:
            logger.warning(f"Failed to load historical monitoring data: {e}")

    async def _save_historical_data(self):
        """Save historical monitoring data"""
        try:
            # Prepare data for serialization
            data = {
                "alerts": [
                    {
                        **asdict(alert),
                        "timestamp": alert.timestamp.isoformat(),
                        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                    }
                    for alert in list(self.active_alerts.values())[-1000:]  # Keep last 1000 alerts
                ],
                "metrics": [
                    {
                        **asdict(metric),
                        "timestamp": metric.timestamp.isoformat()
                    }
                    for metric in self.metrics_history[-10000:]  # Keep last 10000 metrics
                ]
            }
            
            with open("monitoring_data.json", 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save monitoring data: {e}")

    async def update_metrics_and_alerts(self, orchestration_result: Any) -> Dict[str, Any]:
        """Update monitoring metrics and check for alert conditions"""
        logger.info("📊 Updating monitoring metrics and checking alerts...")
        
        start_time = datetime.now()
        new_alerts = []
        resolved_alerts = []
        errors = []
        
        try:
            # Collect system metrics
            system_metrics = await self._collect_system_metrics()
            
            # Collect application metrics from orchestration result
            app_metrics = self._extract_app_metrics(orchestration_result)
            
            # Store all metrics
            all_metrics = {**system_metrics, **app_metrics}
            
            for metric_name, value in all_metrics.items():
                metric_point = MetricPoint(
                    timestamp=datetime.now(),
                    metric_name=metric_name,
                    value=float(value),
                    tags={"source": "florida_agent"}
                )
                self.metrics_history.append(metric_point)
            
            # Check for alert conditions
            alert_results = await self._check_alert_conditions(all_metrics)
            new_alerts.extend(alert_results.get("new_alerts", []))
            resolved_alerts.extend(alert_results.get("resolved_alerts", []))
            
            # Perform health checks
            health_results = await self._perform_health_checks()
            
            # Check health results for alerts
            for health_result in health_results:
                if health_result.status == "failed":
                    alert = await self._create_alert(
                        severity="critical",
                        component=health_result.component,
                        title=f"{health_result.component} Health Check Failed",
                        message=f"Component {health_result.component} failed health check: {health_result.details}"
                    )
                    if alert:
                        new_alerts.append(alert)
                elif health_result.status == "degraded":
                    alert = await self._create_alert(
                        severity="warning", 
                        component=health_result.component,
                        title=f"{health_result.component} Performance Degraded",
                        message=f"Component {health_result.component} showing degraded performance: {health_result.details}"
                    )
                    if alert:
                        new_alerts.append(alert)
            
            # Send notifications for new critical alerts
            for alert in new_alerts:
                if alert.severity in ["critical", "error"]:
                    await self._send_alert_notification(alert)
            
            # Clean up old metrics
            cutoff_date = datetime.now() - timedelta(days=self.metric_retention_days)
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_date
            ]
            
            # Update statistics
            self.stats["total_alerts"] += len(new_alerts)
            self.stats["critical_alerts"] += len([a for a in new_alerts if a.severity == "critical"])
            self.stats["resolved_alerts"] += len(resolved_alerts)
            self.stats["health_checks_performed"] += len(health_results)
            
            if health_results:
                avg_response = statistics.mean([h.response_time_ms for h in health_results])
                self.stats["average_response_time"] = avg_response
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Monitoring update complete: {len(new_alerts)} new alerts, "
                       f"{len(resolved_alerts)} resolved, {len(health_results)} health checks "
                       f"({duration:.2f}s)")
            
            return {
                "new_alerts": new_alerts,
                "resolved_alerts": resolved_alerts,
                "health_checks": health_results,
                "metrics_collected": len(all_metrics),
                "duration_seconds": duration,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Monitoring update failed: {e}")
            return {
                "new_alerts": [],
                "resolved_alerts": [],
                "health_checks": [],
                "metrics_collected": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "errors": [{"component": "monitoring_update", "error": str(e), "timestamp": datetime.now()}]
            }

    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system resource metrics"""
        try:
            metrics = {}
            
            # CPU usage
            metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics["memory_percent"] = memory.percent
            metrics["memory_used_mb"] = memory.used / 1024 / 1024
            metrics["memory_available_mb"] = memory.available / 1024 / 1024
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics["disk_percent"] = (disk.used / disk.total) * 100
            metrics["disk_used_gb"] = disk.used / 1024 / 1024 / 1024
            metrics["disk_free_gb"] = disk.free / 1024 / 1024 / 1024
            
            # Network I/O
            net_io = psutil.net_io_counters()
            metrics["network_bytes_sent"] = net_io.bytes_sent
            metrics["network_bytes_recv"] = net_io.bytes_recv
            
            # Process count
            metrics["process_count"] = len(psutil.pids())
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}

    def _extract_app_metrics(self, orchestration_result: Any) -> Dict[str, float]:
        """Extract application metrics from orchestration result"""
        metrics = {}
        
        try:
            if hasattr(orchestration_result, 'files_discovered'):
                metrics["files_discovered"] = orchestration_result.files_discovered
            if hasattr(orchestration_result, 'files_downloaded'):
                metrics["files_downloaded"] = orchestration_result.files_downloaded  
            if hasattr(orchestration_result, 'files_processed'):
                metrics["files_processed"] = orchestration_result.files_processed
            if hasattr(orchestration_result, 'records_updated'):
                metrics["records_updated"] = orchestration_result.records_updated
            if hasattr(orchestration_result, 'duration_seconds'):
                metrics["operation_duration_seconds"] = orchestration_result.duration_seconds
            if hasattr(orchestration_result, 'errors'):
                metrics["operation_errors"] = len(orchestration_result.errors)
            
            # Calculate error rate
            total_operations = sum([
                metrics.get("files_discovered", 0),
                metrics.get("files_downloaded", 0), 
                metrics.get("files_processed", 0)
            ])
            
            if total_operations > 0:
                error_count = metrics.get("operation_errors", 0)
                metrics["error_rate_percent"] = (error_count / total_operations) * 100
            else:
                metrics["error_rate_percent"] = 0
                
        except Exception as e:
            logger.warning(f"Failed to extract application metrics: {e}")
        
        return metrics

    async def _check_alert_conditions(self, metrics: Dict[str, float]) -> Dict[str, List[Alert]]:
        """Check current metrics against alert thresholds"""
        new_alerts = []
        resolved_alerts = []
        
        # Check each threshold
        for metric_name, threshold in self.thresholds.items():
            current_value = metrics.get(metric_name, 0)
            alert_id = f"threshold_{metric_name}"
            
            # Check if threshold is breached
            if current_value > threshold:
                # Create alert if not already active
                if alert_id not in self.active_alerts:
                    severity = "critical" if current_value > threshold * 1.2 else "warning"
                    
                    alert = await self._create_alert(
                        severity=severity,
                        component="system_metrics",
                        title=f"{metric_name.replace('_', ' ').title()} Threshold Breached",
                        message=f"{metric_name} is {current_value:.1f}, exceeding threshold of {threshold}"
                    )
                    
                    if alert:
                        new_alerts.append(alert)
                        self.active_alerts[alert_id] = alert
            else:
                # Resolve alert if it was active
                if alert_id in self.active_alerts:
                    alert = self.active_alerts[alert_id]
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    alert.resolution_notes = f"{metric_name} returned to normal: {current_value:.1f}"
                    
                    resolved_alerts.append(alert)
                    del self.active_alerts[alert_id]
        
        return {
            "new_alerts": new_alerts,
            "resolved_alerts": resolved_alerts
        }

    async def _perform_health_checks(self) -> List[HealthCheckResult]:
        """Perform health checks on system components"""
        health_checks = []
        
        # Database health check
        try:
            start_time = datetime.now()
            # This would typically check database connectivity
            # For now, simulate a basic health check
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health_checks.append(HealthCheckResult(
                component="database",
                status="healthy",
                response_time_ms=response_time,
                details={"connection": "ok", "response_time_ms": response_time},
                timestamp=datetime.now()
            ))
        except Exception as e:
            health_checks.append(HealthCheckResult(
                component="database",
                status="failed",
                response_time_ms=0,
                details={"error": str(e)},
                timestamp=datetime.now()
            ))
        
        # File system health check
        try:
            start_time = datetime.now()
            # Check if data directories are accessible
            data_dir = Path("florida_data")
            if data_dir.exists():
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                health_checks.append(HealthCheckResult(
                    component="file_system",
                    status="healthy",
                    response_time_ms=response_time,
                    details={"data_directory": "accessible"},
                    timestamp=datetime.now()
                ))
            else:
                health_checks.append(HealthCheckResult(
                    component="file_system",
                    status="degraded",
                    response_time_ms=0,
                    details={"data_directory": "not_found"},
                    timestamp=datetime.now()
                ))
        except Exception as e:
            health_checks.append(HealthCheckResult(
                component="file_system",
                status="failed",
                response_time_ms=0,
                details={"error": str(e)},
                timestamp=datetime.now()
            ))
        
        # Network connectivity health check
        try:
            start_time = datetime.now()
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get("https://floridarevenue.com/property/dataportal/") as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    if response.status == 200:
                        health_checks.append(HealthCheckResult(
                            component="network_connectivity",
                            status="healthy",
                            response_time_ms=response_time,
                            details={"florida_revenue_portal": "accessible", "status_code": response.status},
                            timestamp=datetime.now()
                        ))
                    else:
                        health_checks.append(HealthCheckResult(
                            component="network_connectivity",
                            status="degraded",
                            response_time_ms=response_time,
                            details={"florida_revenue_portal": "error", "status_code": response.status},
                            timestamp=datetime.now()
                        ))
        except Exception as e:
            health_checks.append(HealthCheckResult(
                component="network_connectivity",
                status="failed",
                response_time_ms=0,
                details={"error": str(e)},
                timestamp=datetime.now()
            ))
        
        # Store health check history
        self.health_check_history.extend(health_checks)
        
        # Keep only recent health checks
        cutoff_date = datetime.now() - timedelta(days=7)
        self.health_check_history = [
            h for h in self.health_check_history 
            if h.timestamp > cutoff_date
        ]
        
        return health_checks

    async def _create_alert(self, severity: str, component: str, 
                          title: str, message: str) -> Optional[Alert]:
        """Create a new alert with cooldown management"""
        alert_key = f"{component}_{severity}_{title}"
        
        # Check cooldown
        if alert_key in self.alert_cooldowns:
            last_alert = self.alert_cooldowns[alert_key]
            if datetime.now() - last_alert < timedelta(minutes=self.alert_cooldown_minutes):
                logger.debug(f"Alert {alert_key} is in cooldown period")
                return None
        
        # Create alert
        alert = Alert(
            id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(alert_key) % 10000}",
            severity=severity,
            component=component,
            title=title,
            message=message,
            timestamp=datetime.now()
        )
        
        # Update cooldown
        self.alert_cooldowns[alert_key] = datetime.now()
        
        logger.warning(f"🚨 New {severity} alert: {title} - {message}")
        
        return alert

    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification via configured channels"""
        try:
            # Email notification
            if self.notifications.get("email", {}).get("enabled"):
                await self._send_email_alert(alert)
            
            # Webhook notification  
            if self.notifications.get("webhook", {}).get("enabled"):
                await self._send_webhook_alert(alert)
                
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")

    async def _send_email_alert(self, alert: Alert):
        """Send email alert notification"""
        try:
            email_config = self.notifications["email"]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config["from_address"]
            msg['To'] = ", ".join(email_config["to_addresses"])
            msg['Subject'] = f"[{alert.severity.upper()}] Florida Data Agent Alert: {alert.title}"
            
            # Email body
            body = f"""
Alert Details:
- Severity: {alert.severity.upper()}
- Component: {alert.component}
- Title: {alert.title}
- Message: {alert.message}
- Timestamp: {alert.timestamp}
- Alert ID: {alert.id}

This is an automated alert from the Florida Property Data Agent system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            if email_config.get("use_tls"):
                server.starttls()
            if email_config.get("username") and email_config.get("password"):
                server.login(email_config["username"], email_config["password"])
            
            server.sendmail(msg['From'], email_config["to_addresses"], msg.as_string())
            server.quit()
            
            logger.info(f"Email alert sent for: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert notification"""
        try:
            webhook_config = self.notifications["webhook"]
            
            # Prepare webhook payload
            payload = {
                "alert_id": alert.id,
                "severity": alert.severity,
                "component": alert.component,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "source": "florida_data_agent"
            }
            
            # Send webhook
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    webhook_config["url"], 
                    json=payload,
                    headers=webhook_config.get("headers", {})
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent for: {alert.title}")
                    else:
                        logger.error(f"Webhook alert failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    async def _validate_email_config(self):
        """Validate email notification configuration"""
        try:
            email_config = self.notifications["email"]
            required_fields = ["smtp_server", "smtp_port", "from_address", "to_addresses"]
            
            for field in required_fields:
                if not email_config.get(field):
                    raise ValueError(f"Missing required email config field: {field}")
            
            logger.info("Email notification configuration validated")
            
        except Exception as e:
            logger.warning(f"Email notification configuration invalid: {e}")
            self.notifications["email"]["enabled"] = False

    async def _validate_webhook_config(self):
        """Validate webhook notification configuration"""
        try:
            webhook_config = self.notifications["webhook"]
            
            if not webhook_config.get("url"):
                raise ValueError("Missing webhook URL")
            
            logger.info("Webhook notification configuration validated")
            
        except Exception as e:
            logger.warning(f"Webhook notification configuration invalid: {e}")
            self.notifications["webhook"]["enabled"] = False

    async def get_active_alerts(self) -> List[Alert]:
        """Get all currently active alerts"""
        return list(self.active_alerts.values())

    async def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Manually resolve an alert"""
        try:
            # Find alert in active alerts
            alert_to_resolve = None
            alert_key = None
            
            for key, alert in self.active_alerts.items():
                if alert.id == alert_id:
                    alert_to_resolve = alert
                    alert_key = key
                    break
            
            if not alert_to_resolve:
                logger.warning(f"Alert {alert_id} not found in active alerts")
                return False
            
            # Resolve the alert
            alert_to_resolve.resolved = True
            alert_to_resolve.resolved_at = datetime.now()
            alert_to_resolve.resolution_notes = resolution_notes
            
            # Remove from active alerts
            del self.active_alerts[alert_key]
            
            # Update statistics
            self.stats["resolved_alerts"] += 1
            
            logger.info(f"Alert {alert_id} resolved: {resolution_notes}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False

    async def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of metrics over the specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter metrics to the time period
            recent_metrics = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            # Group metrics by name
            metric_groups = {}
            for metric in recent_metrics:
                if metric.metric_name not in metric_groups:
                    metric_groups[metric.metric_name] = []
                metric_groups[metric.metric_name].append(metric.value)
            
            # Calculate summaries
            summary = {}
            for metric_name, values in metric_groups.items():
                if values:
                    summary[metric_name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": statistics.mean(values),
                        "current": values[-1] if values else 0
                    }
                    
                    if len(values) > 1:
                        summary[metric_name]["std_dev"] = statistics.stdev(values)
            
            return {
                "time_period_hours": hours,
                "metrics_count": len(recent_metrics),
                "unique_metrics": len(metric_groups),
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Failed to generate metrics summary: {e}")
            return {"error": str(e)}

    async def get_health_status(self):
        """Get health status of the monitoring agent"""
        from dataclasses import dataclass
        from typing import List
        
        @dataclass
        class AgentHealth:
            name: str
            status: str
            last_run: Optional[datetime]
            success_rate: float
            error_count: int
            performance_metrics: Dict[str, float]
            alerts: List[str]
        
        # Calculate uptime
        uptime_hours = (datetime.now() - self.stats["uptime_start"]).total_seconds() / 3600
        
        # Determine status based on active critical alerts
        critical_alert_count = len([a for a in self.active_alerts.values() if a.severity == "critical"])
        
        if critical_alert_count == 0:
            status = "healthy"
        elif critical_alert_count <= 2:
            status = "degraded"
        else:
            status = "failed"
        
        alerts = []
        if critical_alert_count > 0:
            alerts.append(f"{critical_alert_count} critical alerts active")
        
        recent_metrics = len([m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(hours=1)])
        if recent_metrics == 0:
            alerts.append("No recent metrics collected")
        
        return AgentHealth(
            name="monitoring_agent",
            status=status,
            last_run=datetime.now(),  # Monitoring is always running
            success_rate=1.0,  # Monitoring itself rarely fails
            error_count=critical_alert_count,
            performance_metrics={
                "total_alerts": self.stats["total_alerts"],
                "active_alerts": len(self.active_alerts),
                "uptime_hours": uptime_hours,
                "metrics_collected": len(self.metrics_history),
                "health_checks_performed": self.stats["health_checks_performed"]
            },
            alerts=alerts
        )