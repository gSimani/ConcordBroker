#!/usr/bin/env python3
"""
Florida Data Monitoring System
Advanced monitoring with intelligent alerting and anomaly detection
Real-time file detection, change tracking, and automated notifications
"""

import asyncio
import aiohttp
import asyncpg
import logging
import json
import hashlib
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import schedule
import time
import pandas as pd
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_config import SupabaseConfig, SupabaseUpdateMonitor
from florida_url_resolver import FloridaURLResolver
from florida_comprehensive_monitor import FloridaComprehensiveMonitor

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringEvent(Enum):
    """Types of monitoring events"""
    NEW_FILE_DETECTED = "new_file_detected"
    FILE_UPDATED = "file_updated"
    FILE_SIZE_CHANGED = "file_size_changed"
    DOWNLOAD_FAILED = "download_failed"
    PROCESSING_FAILED = "processing_failed"
    SOURCE_UNAVAILABLE = "source_unavailable"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    SCHEDULE_MISSED = "schedule_missed"
    ANOMALY_DETECTED = "anomaly_detected"

@dataclass
class MonitoringAlert:
    """Alert data structure"""
    alert_id: str
    event_type: MonitoringEvent
    level: AlertLevel
    source: str
    title: str
    description: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    acknowledged: bool = False

@dataclass
class FileChangeEvent:
    """File change tracking"""
    file_path: str
    source: str
    change_type: str  # new, modified, deleted, size_changed
    old_size: Optional[int] = None
    new_size: Optional[int] = None
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

class FloridaMonitoringSystem:
    """Comprehensive monitoring system for Florida data sources"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.pool = None
        self.monitor = None
        self.url_resolver = None
        self.comprehensive_monitor = None
        self.active_alerts = {}
        self.file_registry = {}  # Track all known files
        self.baseline_metrics = {}  # Baseline for anomaly detection
        self.monitoring_stats = {
            "total_checks": 0,
            "files_monitored": 0,
            "alerts_generated": 0,
            "anomalies_detected": 0,
            "last_check": None,
            "uptime_start": datetime.now()
        }
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "check_intervals": {
                "florida_revenue": 3600,  # 1 hour
                "sunbiz": 86400,  # 24 hours
                "broward_daily": 1800,  # 30 minutes
                "arcgis": 43200,  # 12 hours
            },
            "alert_thresholds": {
                "file_size_change_percent": 20,  # Alert if file size changes by >20%
                "download_failure_count": 3,  # Alert after 3 consecutive failures
                "processing_error_rate": 0.1,  # Alert if >10% of records fail processing
                "response_time_seconds": 30,  # Alert if response time > 30 seconds
            },
            "notification": {
                "enabled": True,
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": []
                },
                "slack": {
                    "webhook_url": "",
                    "channel": "#florida-data-alerts"
                },
                "discord": {
                    "webhook_url": ""
                }
            },
            "data_quality": {
                "min_records_per_file": 100,
                "max_null_percentage": 30,
                "expected_columns": {},  # Per dataset type
                "outlier_detection": True
            },
            "retention": {
                "alert_history_days": 90,
                "file_change_history_days": 30,
                "metrics_history_days": 365
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults
                default_config.update(user_config)
        
        return default_config
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize database connection
        self.pool = await SupabaseConfig.get_db_pool()
        self.monitor = SupabaseUpdateMonitor(self.pool)
        await self.monitor.initialize_tracking_tables()
        
        # Initialize monitoring tables
        await self._initialize_monitoring_tables()
        
        # Initialize other components
        self.url_resolver = FloridaURLResolver()
        await self.url_resolver.__aenter__()
        
        self.comprehensive_monitor = FloridaComprehensiveMonitor()
        await self.comprehensive_monitor.__aenter__()
        
        # Load existing file registry
        await self._load_file_registry()
        await self._load_baseline_metrics()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.comprehensive_monitor:
            await self.comprehensive_monitor.__aexit__(exc_type, exc_val, exc_tb)
        if self.url_resolver:
            await self.url_resolver.__aexit__(exc_type, exc_val, exc_tb)
        if self.pool:
            await self.pool.close()
    
    async def _initialize_monitoring_tables(self):
        """Initialize monitoring-specific database tables"""
        async with self.pool.acquire() as conn:
            # Alerts table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_monitoring_alerts (
                    alert_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    details JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    resolved BOOLEAN DEFAULT FALSE,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMPTZ,
                    acknowledged_at TIMESTAMPTZ
                )
            """)
            
            # File change events
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_file_changes (
                    id SERIAL PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    source TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    old_size BIGINT,
                    new_size BIGINT,
                    old_hash TEXT,
                    new_hash TEXT,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB
                )
            """)
            
            # Monitoring metrics
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_monitoring_metrics (
                    id SERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value NUMERIC,
                    metric_data JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # File registry
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_file_registry (
                    file_path TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    first_seen TIMESTAMPTZ DEFAULT NOW(),
                    last_seen TIMESTAMPTZ DEFAULT NOW(),
                    last_size BIGINT,
                    last_hash TEXT,
                    last_modified TIMESTAMPTZ,
                    status TEXT DEFAULT 'active',
                    metadata JSONB
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON fl_monitoring_alerts(timestamp DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_level ON fl_monitoring_alerts(level, resolved)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_file_changes_timestamp ON fl_file_changes(timestamp DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_source_time ON fl_monitoring_metrics(source, timestamp DESC)")
    
    async def _load_file_registry(self):
        """Load existing file registry from database"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM fl_file_registry WHERE status = 'active'")
            
            for row in rows:
                self.file_registry[row['file_path']] = {
                    "source": row['source'],
                    "first_seen": row['first_seen'],
                    "last_seen": row['last_seen'],
                    "last_size": row['last_size'],
                    "last_hash": row['last_hash'],
                    "last_modified": row['last_modified'],
                    "metadata": row['metadata'] or {}
                }
        
        logger.info(f"Loaded {len(self.file_registry)} files from registry")
    
    async def _load_baseline_metrics(self):
        """Load baseline metrics for anomaly detection"""
        async with self.pool.acquire() as conn:
            # Load recent metrics for each source
            sources = ["florida_revenue", "sunbiz", "broward_daily", "arcgis"]
            
            for source in sources:
                rows = await conn.fetch("""
                    SELECT metric_name, AVG(metric_value) as avg_value, 
                           STDDEV(metric_value) as stddev_value, COUNT(*) as count
                    FROM fl_monitoring_metrics 
                    WHERE source = $1 AND timestamp > NOW() - INTERVAL '30 days'
                    GROUP BY metric_name
                    HAVING COUNT(*) > 5
                """, source)
                
                self.baseline_metrics[source] = {}
                for row in rows:
                    self.baseline_metrics[source][row['metric_name']] = {
                        "mean": float(row['avg_value']) if row['avg_value'] else 0,
                        "stddev": float(row['stddev_value']) if row['stddev_value'] else 0,
                        "count": row['count']
                    }
        
        logger.info(f"Loaded baseline metrics for {len(self.baseline_metrics)} sources")
    
    async def check_all_sources(self) -> Dict[str, Any]:
        """Perform comprehensive check of all data sources"""
        logger.info("Starting comprehensive source check")
        
        check_results = {
            "timestamp": datetime.now(),
            "sources_checked": 0,
            "new_files_detected": 0,
            "files_updated": 0,
            "alerts_generated": 0,
            "anomalies_detected": 0,
            "errors": []
        }
        
        # Run comprehensive monitoring
        try:
            monitor_results = await self.comprehensive_monitor.run_monitoring_cycle()
            
            # Process results and generate alerts
            await self._process_monitoring_results(monitor_results, check_results)
            
            # Check for anomalies
            anomalies = await self._detect_anomalies(monitor_results)
            check_results["anomalies_detected"] = len(anomalies)
            
            # Update monitoring stats
            self.monitoring_stats["total_checks"] += 1
            self.monitoring_stats["last_check"] = datetime.now()
            self.monitoring_stats["alerts_generated"] += check_results["alerts_generated"]
            self.monitoring_stats["anomalies_detected"] += len(anomalies)
            
        except Exception as e:
            error_msg = f"Comprehensive check failed: {e}"
            logger.error(error_msg)
            check_results["errors"].append(error_msg)
            
            # Generate critical alert
            await self._generate_alert(
                MonitoringEvent.SOURCE_UNAVAILABLE,
                AlertLevel.CRITICAL,
                "system",
                "Monitoring System Failure",
                f"Comprehensive monitoring check failed: {e}"
            )
        
        return check_results
    
    async def _process_monitoring_results(self, monitor_results: Dict[str, Any], 
                                        check_results: Dict[str, Any]):
        """Process monitoring results and generate alerts"""
        
        # Check for new files
        if monitor_results.get("files_downloaded", 0) > 0:
            check_results["new_files_detected"] = monitor_results["files_downloaded"]
            
            await self._generate_alert(
                MonitoringEvent.NEW_FILE_DETECTED,
                AlertLevel.INFO,
                "system",
                f"New Files Downloaded",
                f"Downloaded {monitor_results['files_downloaded']} new files"
            )
        
        # Check for processing errors
        if monitor_results.get("errors"):
            for error in monitor_results["errors"]:
                await self._generate_alert(
                    MonitoringEvent.PROCESSING_FAILED,
                    AlertLevel.ERROR,
                    "system",
                    "Processing Error",
                    f"Processing failed: {error}"
                )
                check_results["alerts_generated"] += 1
        
        # Check processing efficiency
        total_files = monitor_results.get("files_discovered", 0)
        processed_files = monitor_results.get("files_processed", 0)
        
        if total_files > 0:
            processing_rate = processed_files / total_files
            if processing_rate < 0.8:  # Less than 80% success rate
                await self._generate_alert(
                    MonitoringEvent.DATA_QUALITY_ISSUE,
                    AlertLevel.WARNING,
                    "system",
                    "Low Processing Success Rate",
                    f"Only {processing_rate:.1%} of files processed successfully"
                )
                check_results["alerts_generated"] += 1
    
    async def _detect_anomalies(self, monitor_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in monitoring data using statistical methods"""
        anomalies = []
        
        # File count anomaly detection
        for source_name in self.baseline_metrics:
            if source_name in self.baseline_metrics:
                baseline = self.baseline_metrics[source_name]
                
                # Check file count anomalies
                if "file_count" in baseline:
                    expected_count = baseline["file_count"]["mean"]
                    stddev = baseline["file_count"]["stddev"]
                    
                    current_count = monitor_results.get("files_discovered", 0)
                    
                    # Use 2-sigma rule for anomaly detection
                    if abs(current_count - expected_count) > 2 * stddev:
                        anomaly = {
                            "type": "file_count_anomaly",
                            "source": source_name,
                            "expected": expected_count,
                            "actual": current_count,
                            "deviation": abs(current_count - expected_count) / stddev if stddev > 0 else 0,
                            "timestamp": datetime.now()
                        }
                        anomalies.append(anomaly)
                        
                        await self._generate_alert(
                            MonitoringEvent.ANOMALY_DETECTED,
                            AlertLevel.WARNING,
                            source_name,
                            f"File Count Anomaly Detected",
                            f"Expected ~{expected_count:.0f} files, found {current_count}"
                        )
        
        return anomalies
    
    async def _generate_alert(self, event_type: MonitoringEvent, level: AlertLevel, 
                            source: str, title: str, description: str, 
                            details: Dict[str, Any] = None) -> str:
        """Generate and store an alert"""
        alert_id = hashlib.md5(
            f"{event_type.value}_{source}_{title}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        alert = MonitoringAlert(
            alert_id=alert_id,
            event_type=event_type,
            level=level,
            source=source,
            title=title,
            description=description,
            details=details or {},
            timestamp=datetime.now()
        )
        
        # Store in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fl_monitoring_alerts 
                (alert_id, event_type, level, source, title, description, details, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, alert.alert_id, alert.event_type.value, alert.level.value,
                alert.source, alert.title, alert.description, 
                json.dumps(alert.details), alert.timestamp)
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        # Send notifications if enabled
        if self.config["notification"]["enabled"]:
            await self._send_notifications(alert)
        
        logger.info(f"Generated {level.value} alert: {title}")
        return alert_id
    
    async def _send_notifications(self, alert: MonitoringAlert):
        """Send alert notifications via configured channels"""
        
        # Email notifications
        if (self.config["notification"]["email"]["recipients"] and 
            alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]):
            await self._send_email_alert(alert)
        
        # Slack notifications
        if (self.config["notification"]["slack"]["webhook_url"] and
            alert.level in [AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]):
            await self._send_slack_alert(alert)
        
        # Discord notifications
        if (self.config["notification"]["discord"]["webhook_url"] and
            alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]):
            await self._send_discord_alert(alert)
    
    async def _send_email_alert(self, alert: MonitoringAlert):
        """Send email alert notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["notification"]["email"]["username"]
            msg['To'] = ', '.join(self.config["notification"]["email"]["recipients"])
            msg['Subject'] = f"[{alert.level.value.upper()}] Florida Data Alert: {alert.title}"
            
            body = f"""
            Alert Details:
            - Level: {alert.level.value.upper()}
            - Source: {alert.source}
            - Event: {alert.event_type.value}
            - Time: {alert.timestamp}
            
            Description:
            {alert.description}
            
            Additional Details:
            {json.dumps(alert.details, indent=2)}
            
            ---
            Florida Data Monitoring System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(
                self.config["notification"]["email"]["smtp_server"],
                self.config["notification"]["email"]["smtp_port"]
            )
            server.starttls()
            server.login(
                self.config["notification"]["email"]["username"],
                self.config["notification"]["email"]["password"]
            )
            
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'].split(', '), text)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_slack_alert(self, alert: MonitoringAlert):
        """Send Slack alert notification"""
        try:
            color_map = {
                AlertLevel.INFO: "good",
                AlertLevel.WARNING: "warning", 
                AlertLevel.ERROR: "danger",
                AlertLevel.CRITICAL: "danger"
            }
            
            payload = {
                "channel": self.config["notification"]["slack"]["channel"],
                "username": "Florida Data Monitor",
                "attachments": [{
                    "color": color_map.get(alert.level, "warning"),
                    "title": alert.title,
                    "text": alert.description,
                    "fields": [
                        {"title": "Level", "value": alert.level.value.upper(), "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Event", "value": alert.event_type.value, "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["notification"]["slack"]["webhook_url"],
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert.alert_id}")
                    else:
                        logger.error(f"Slack alert failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    async def _send_discord_alert(self, alert: MonitoringAlert):
        """Send Discord alert notification"""
        try:
            color_map = {
                AlertLevel.INFO: 0x00ff00,
                AlertLevel.WARNING: 0xffff00,
                AlertLevel.ERROR: 0xff8000,
                AlertLevel.CRITICAL: 0xff0000
            }
            
            payload = {
                "embeds": [{
                    "title": alert.title,
                    "description": alert.description,
                    "color": color_map.get(alert.level, 0xffff00),
                    "fields": [
                        {"name": "Level", "value": alert.level.value.upper(), "inline": True},
                        {"name": "Source", "value": alert.source, "inline": True},
                        {"name": "Event", "value": alert.event_type.value, "inline": True}
                    ],
                    "timestamp": alert.timestamp.isoformat()
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["notification"]["discord"]["webhook_url"],
                    json=payload
                ) as response:
                    if response.status in [200, 204]:
                        logger.info(f"Discord alert sent for {alert.alert_id}")
                    else:
                        logger.error(f"Discord alert failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
    
    async def get_active_alerts(self, level: AlertLevel = None) -> List[MonitoringAlert]:
        """Get active alerts, optionally filtered by level"""
        async with self.pool.acquire() as conn:
            if level:
                rows = await conn.fetch("""
                    SELECT * FROM fl_monitoring_alerts 
                    WHERE resolved = FALSE AND level = $1
                    ORDER BY timestamp DESC
                """, level.value)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM fl_monitoring_alerts 
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                """)
        
        alerts = []
        for row in rows:
            alert = MonitoringAlert(
                alert_id=row['alert_id'],
                event_type=MonitoringEvent(row['event_type']),
                level=AlertLevel(row['level']),
                source=row['source'],
                title=row['title'],
                description=row['description'],
                details=row['details'] or {},
                timestamp=row['timestamp'],
                resolved=row['resolved'],
                acknowledged=row['acknowledged']
            )
            alerts.append(alert)
        
        return alerts
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE fl_monitoring_alerts 
                SET resolved = TRUE, resolved_at = NOW()
                WHERE alert_id = $1
            """, alert_id)
            
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].resolved = True
                del self.active_alerts[alert_id]
        
        return result != "UPDATE 0"
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for monitoring dashboard"""
        dashboard = {
            "timestamp": datetime.now(),
            "system_health": {
                "uptime_hours": (datetime.now() - self.monitoring_stats["uptime_start"]).total_seconds() / 3600,
                "total_checks": self.monitoring_stats["total_checks"],
                "files_monitored": len(self.file_registry),
                "active_alerts": len(self.active_alerts),
                "last_check": self.monitoring_stats["last_check"]
            },
            "alert_summary": {
                "critical": len([a for a in self.active_alerts.values() if a.level == AlertLevel.CRITICAL]),
                "error": len([a for a in self.active_alerts.values() if a.level == AlertLevel.ERROR]),
                "warning": len([a for a in self.active_alerts.values() if a.level == AlertLevel.WARNING]),
                "info": len([a for a in self.active_alerts.values() if a.level == AlertLevel.INFO])
            },
            "recent_activity": {
                "alerts_today": self.monitoring_stats["alerts_generated"],
                "anomalies_detected": self.monitoring_stats["anomalies_detected"]
            }
        }
        
        return dashboard
    
    async def start_monitoring_service(self):
        """Start the continuous monitoring service"""
        logger.info("Starting Florida Data Monitoring Service")
        
        # Schedule periodic checks
        for source, interval in self.config["check_intervals"].items():
            schedule.every(interval).seconds.do(
                lambda: asyncio.create_task(self.check_all_sources())
            )
        
        logger.info("Monitoring service started. Press Ctrl+C to stop.")
        
        try:
            # Run initial check
            await self.check_all_sources()
            
            # Start monitoring loop
            while True:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Monitoring service error: {e}")
            raise

async def main():
    """Test the monitoring system"""
    print("Testing Florida Monitoring System...")
    
    async with FloridaMonitoringSystem() as monitor:
        # Run a single check
        results = await monitor.check_all_sources()
        
        print("\nMonitoring Results:")
        print(json.dumps(results, indent=2, default=str))
        
        # Get active alerts
        alerts = await monitor.get_active_alerts()
        print(f"\nActive Alerts: {len(alerts)}")
        
        for alert in alerts:
            print(f"  [{alert.level.value.upper()}] {alert.title}")
        
        # Generate dashboard data
        dashboard = monitor.generate_dashboard_data()
        print(f"\nDashboard Summary:")
        print(json.dumps(dashboard, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())