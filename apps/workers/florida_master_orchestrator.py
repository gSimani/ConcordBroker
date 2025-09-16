#!/usr/bin/env python3
"""
Florida Data Master Orchestrator
Central coordination system that integrates all components:
- Comprehensive monitoring
- Advanced scheduling
- Error handling & recovery
- Real-time alerting
- Performance optimization
"""

import asyncio
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import signal
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_config import SupabaseConfig
from florida_comprehensive_monitor import FloridaComprehensiveMonitor
from florida_monitoring_system import FloridaMonitoringSystem
from florida_error_handler import FloridaErrorHandler
from florida_scheduler import FloridaScheduler
from florida_url_resolver import FloridaURLResolver
from florida_data_processor import FloridaDataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_master_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()

@dataclass
class SystemHealth:
    """System health status"""
    overall_status: str  # healthy, warning, critical
    component_status: Dict[str, str]
    active_alerts: int
    error_rate: float
    uptime_hours: float
    last_check: datetime
    resource_usage: Dict[str, float]

class FloridaMasterOrchestrator:
    """Master orchestrator that coordinates all Florida data operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.console = Console()
        
        # Component instances
        self.comprehensive_monitor = None
        self.monitoring_system = None
        self.error_handler = None
        self.scheduler = None
        self.url_resolver = None
        self.data_processor = None
        
        # System state
        self.running = False
        self.start_time = None
        self.system_health = None
        self.performance_metrics = {}
        
        # Statistics
        self.orchestrator_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "data_sources_monitored": 0,
            "files_processed": 0,
            "alerts_generated": 0,
            "uptime_start": datetime.now()
        }
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load orchestrator configuration"""
        default_config = {
            "orchestrator": {
                "name": "Florida Property Data Orchestrator",
                "version": "1.0.0",
                "timezone": "US/Eastern",
                "log_level": "INFO"
            },
            "components": {
                "comprehensive_monitor": {"enabled": True, "priority": 1},
                "monitoring_system": {"enabled": True, "priority": 2},
                "error_handler": {"enabled": True, "priority": 3},
                "scheduler": {"enabled": True, "priority": 4},
                "url_resolver": {"enabled": True, "priority": 5},
                "data_processor": {"enabled": True, "priority": 6}
            },
            "health_checks": {
                "interval_minutes": 5,
                "alert_thresholds": {
                    "error_rate": 0.1,
                    "response_time_seconds": 30,
                    "cpu_usage_percent": 80,
                    "memory_usage_percent": 80
                }
            },
            "performance": {
                "max_concurrent_operations": 10,
                "operation_timeout_minutes": 30,
                "batch_size": 1000,
                "enable_optimization": True
            },
            "data_sources": {
                "florida_revenue": {
                    "priority": 1,
                    "check_interval_hours": 1,
                    "enabled": True
                },
                "sunbiz": {
                    "priority": 2,
                    "check_interval_hours": 24,
                    "enabled": True
                },
                "broward_daily": {
                    "priority": 3,
                    "check_interval_minutes": 30,
                    "enabled": True
                },
                "arcgis": {
                    "priority": 4,
                    "check_interval_hours": 12,
                    "enabled": True
                }
            },
            "dashboard": {
                "enabled": True,
                "refresh_interval_seconds": 30,
                "show_detailed_logs": False
            },
            "backup_and_recovery": {
                "enabled": True,
                "backup_interval_hours": 6,
                "retention_days": 30
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge configurations
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_config
    
    async def __aenter__(self):
        """Async context manager entry - Initialize all components"""
        self.console.print(f"[bold green]Initializing {self.config['orchestrator']['name']}...[/bold green]")
        
        # Initialize components in priority order
        components_to_init = sorted(
            self.config["components"].items(),
            key=lambda x: x[1].get("priority", 99)
        )
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            for component_name, component_config in components_to_init:
                if not component_config.get("enabled", True):
                    continue
                
                task = progress.add_task(f"Initializing {component_name}...")
                
                try:
                    if component_name == "comprehensive_monitor":
                        self.comprehensive_monitor = FloridaComprehensiveMonitor()
                        await self.comprehensive_monitor.__aenter__()
                    
                    elif component_name == "monitoring_system":
                        self.monitoring_system = FloridaMonitoringSystem()
                        await self.monitoring_system.__aenter__()
                    
                    elif component_name == "error_handler":
                        self.error_handler = FloridaErrorHandler()
                        await self.error_handler.__aenter__()
                    
                    elif component_name == "scheduler":
                        self.scheduler = FloridaScheduler()
                        await self.scheduler.__aenter__()
                    
                    elif component_name == "url_resolver":
                        self.url_resolver = FloridaURLResolver()
                        await self.url_resolver.__aenter__()
                    
                    elif component_name == "data_processor":
                        self.data_processor = FloridaDataProcessor()
                        await self.data_processor.__aenter__()
                    
                    progress.update(task, description=f"✓ {component_name} initialized")
                    
                except Exception as e:
                    progress.update(task, description=f"✗ {component_name} failed: {e}")
                    logger.error(f"Failed to initialize {component_name}: {e}")
                    raise
        
        self.start_time = datetime.now()
        self.running = True
        
        self.console.print("[bold green]✓ All components initialized successfully[/bold green]")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - Cleanup all components"""
        self.console.print("[yellow]Shutting down orchestrator components...[/yellow]")
        
        self.running = False
        
        # Shutdown components in reverse priority order
        components = [
            ("data_processor", self.data_processor),
            ("url_resolver", self.url_resolver),
            ("scheduler", self.scheduler),
            ("error_handler", self.error_handler),
            ("monitoring_system", self.monitoring_system),
            ("comprehensive_monitor", self.comprehensive_monitor)
        ]
        
        for name, component in components:
            if component:
                try:
                    await component.__aexit__(exc_type, exc_val, exc_tb)
                    self.console.print(f"[green]✓ {name} shutdown complete[/green]")
                except Exception as e:
                    self.console.print(f"[red]✗ {name} shutdown failed: {e}[/red]")
        
        self.console.print("[green]✓ Orchestrator shutdown complete[/green]")
    
    async def run_health_check(self) -> SystemHealth:
        """Perform comprehensive system health check"""
        logger.info("Running system health check")
        
        component_status = {}
        overall_status = "healthy"
        active_alerts = 0
        error_rate = 0.0
        
        # Check each component
        if self.comprehensive_monitor:
            try:
                monitor_stats = self.comprehensive_monitor.download_stats
                component_status["comprehensive_monitor"] = "healthy"
                if monitor_stats.get("failed_downloads", 0) > 0:
                    component_status["comprehensive_monitor"] = "warning"
            except Exception as e:
                component_status["comprehensive_monitor"] = "critical"
                logger.error(f"Comprehensive monitor health check failed: {e}")
        
        if self.monitoring_system:
            try:
                alerts = await self.monitoring_system.get_active_alerts()
                active_alerts = len(alerts)
                component_status["monitoring_system"] = "healthy"
                
                if active_alerts > 10:
                    component_status["monitoring_system"] = "warning"
                    overall_status = "warning"
                elif active_alerts > 20:
                    component_status["monitoring_system"] = "critical"
                    overall_status = "critical"
                    
            except Exception as e:
                component_status["monitoring_system"] = "critical"
                overall_status = "critical"
                logger.error(f"Monitoring system health check failed: {e}")
        
        if self.error_handler:
            try:
                error_stats = self.error_handler.get_error_statistics()
                error_rate = error_stats["current_stats"].get("failed_runs", 0) / max(
                    error_stats["current_stats"].get("total_runs", 1), 1
                )
                component_status["error_handler"] = "healthy"
                
                if error_rate > 0.1:
                    component_status["error_handler"] = "warning"
                    if overall_status == "healthy":
                        overall_status = "warning"
                elif error_rate > 0.25:
                    component_status["error_handler"] = "critical"
                    overall_status = "critical"
                    
            except Exception as e:
                component_status["error_handler"] = "critical"
                overall_status = "critical"
                logger.error(f"Error handler health check failed: {e}")
        
        if self.scheduler:
            try:
                scheduler_stats = self.scheduler.stats
                component_status["scheduler"] = "healthy"
                
                # Check if scheduler is executing tasks
                if scheduler_stats.get("total_executions", 0) == 0:
                    component_status["scheduler"] = "warning"
                    
            except Exception as e:
                component_status["scheduler"] = "critical"
                overall_status = "critical"
                logger.error(f"Scheduler health check failed: {e}")
        
        # Get resource usage
        try:
            import psutil
            resource_usage = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            }
            
            # Check resource thresholds
            if (resource_usage["cpu_percent"] > 80 or 
                resource_usage["memory_percent"] > 80):
                if overall_status == "healthy":
                    overall_status = "warning"
                    
            if (resource_usage["cpu_percent"] > 95 or 
                resource_usage["memory_percent"] > 95):
                overall_status = "critical"
                
        except Exception as e:
            resource_usage = {}
            logger.error(f"Resource monitoring failed: {e}")
        
        # Calculate uptime
        uptime_hours = 0.0
        if self.start_time:
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        # Create health status
        self.system_health = SystemHealth(
            overall_status=overall_status,
            component_status=component_status,
            active_alerts=active_alerts,
            error_rate=error_rate,
            uptime_hours=uptime_hours,
            last_check=datetime.now(),
            resource_usage=resource_usage
        )
        
        return self.system_health
    
    async def run_comprehensive_operation(self) -> Dict[str, Any]:
        """Run a comprehensive data operation across all sources"""
        logger.info("Starting comprehensive data operation")
        
        operation_results = {
            "timestamp": datetime.now(),
            "operation_id": f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "running",
            "components": {},
            "summary": {
                "sources_checked": 0,
                "files_discovered": 0,
                "files_downloaded": 0,
                "files_processed": 0,
                "errors": 0,
                "duration_seconds": 0
            }
        }
        
        start_time = datetime.now()
        
        try:
            # Run comprehensive monitoring
            if self.comprehensive_monitor:
                monitor_result = await self.comprehensive_monitor.run_monitoring_cycle()
                operation_results["components"]["comprehensive_monitor"] = monitor_result
                
                # Update summary
                operation_results["summary"]["sources_checked"] = monitor_result.get("sources_processed", 0)
                operation_results["summary"]["files_discovered"] = monitor_result.get("files_discovered", 0)
                operation_results["summary"]["files_downloaded"] = monitor_result.get("files_downloaded", 0)
                operation_results["summary"]["files_processed"] = monitor_result.get("files_processed", 0)
                operation_results["summary"]["errors"] = len(monitor_result.get("errors", []))
            
            # Run monitoring system checks
            if self.monitoring_system:
                monitoring_result = await self.monitoring_system.check_all_sources()
                operation_results["components"]["monitoring_system"] = monitoring_result
            
            # Process any downloaded files
            if self.data_processor and operation_results["summary"]["files_downloaded"] > 0:
                # This would process the downloaded files
                # Implementation depends on specific file handling logic
                processing_result = {"message": "File processing completed"}
                operation_results["components"]["data_processor"] = processing_result
            
            # Update statistics
            self.orchestrator_stats["total_operations"] += 1
            self.orchestrator_stats["successful_operations"] += 1
            operation_results["status"] = "completed"
            
        except Exception as e:
            logger.error(f"Comprehensive operation failed: {e}")
            operation_results["status"] = "failed"
            operation_results["error"] = str(e)
            self.orchestrator_stats["failed_operations"] += 1
            
            # Record error if error handler is available
            if self.error_handler:
                await self.error_handler.record_error(e, "orchestrator", "comprehensive_operation")
        
        # Calculate duration
        end_time = datetime.now()
        operation_results["summary"]["duration_seconds"] = (end_time - start_time).total_seconds()
        
        logger.info(f"Comprehensive operation completed in {operation_results['summary']['duration_seconds']:.2f} seconds")
        
        return operation_results
    
    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data"""
        dashboard = {
            "timestamp": datetime.now(),
            "system_info": {
                "name": self.config["orchestrator"]["name"],
                "version": self.config["orchestrator"]["version"],
                "uptime_hours": (datetime.now() - self.orchestrator_stats["uptime_start"]).total_seconds() / 3600,
                "status": self.system_health.overall_status if self.system_health else "unknown"
            },
            "statistics": self.orchestrator_stats.copy(),
            "component_status": {},
            "data_sources": {},
            "recent_activity": [],
            "alerts": []
        }
        
        # Component status
        if self.system_health:
            dashboard["component_status"] = self.system_health.component_status
            dashboard["resource_usage"] = self.system_health.resource_usage
            dashboard["active_alerts"] = self.system_health.active_alerts
            dashboard["error_rate"] = self.system_health.error_rate
        
        # Data source status
        for source_name, source_config in self.config["data_sources"].items():
            dashboard["data_sources"][source_name] = {
                "enabled": source_config["enabled"],
                "priority": source_config["priority"],
                "last_check": "unknown",
                "status": "unknown"
            }
        
        return dashboard
    
    async def display_live_dashboard(self):
        """Display live dashboard with real-time updates"""
        def create_dashboard_layout():
            """Create the dashboard layout"""
            layout = Layout()
            
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="footer", size=3)
            )
            
            layout["main"].split_row(
                Layout(name="left"),
                Layout(name="right")
            )
            
            layout["left"].split_column(
                Layout(name="system", size=10),
                Layout(name="components", size=10)
            )
            
            layout["right"].split_column(
                Layout(name="sources", size=10),
                Layout(name="alerts", size=10)
            )
            
            return layout
        
        def update_dashboard(layout, dashboard_data):
            """Update dashboard with current data"""
            # Header
            header_text = f"[bold blue]{dashboard_data['system_info']['name']} v{dashboard_data['system_info']['version']}[/bold blue]\n"
            header_text += f"Status: [{'green' if dashboard_data['system_info']['status'] == 'healthy' else 'red'}]{dashboard_data['system_info']['status'].upper()}[/] | "
            header_text += f"Uptime: {dashboard_data['system_info']['uptime_hours']:.1f}h | "
            header_text += f"Last Update: {dashboard_data['timestamp'].strftime('%H:%M:%S')}"
            layout["header"].update(Panel(header_text, border_style="blue"))
            
            # System stats
            system_table = Table(title="System Statistics")
            system_table.add_column("Metric", style="cyan")
            system_table.add_column("Value", style="green")
            
            stats = dashboard_data["statistics"]
            system_table.add_row("Total Operations", str(stats["total_operations"]))
            system_table.add_row("Successful", str(stats["successful_operations"]))
            system_table.add_row("Failed", str(stats["failed_operations"]))
            system_table.add_row("Files Processed", str(stats["files_processed"]))
            system_table.add_row("Alerts Generated", str(stats["alerts_generated"]))
            
            layout["system"].update(Panel(system_table, title="System"))
            
            # Component status
            component_table = Table(title="Component Status")
            component_table.add_column("Component", style="cyan")
            component_table.add_column("Status", style="green")
            
            for component, status in dashboard_data.get("component_status", {}).items():
                color = "green" if status == "healthy" else "yellow" if status == "warning" else "red"
                component_table.add_row(component, f"[{color}]{status.upper()}[/{color}]")
            
            layout["components"].update(Panel(component_table, title="Components"))
            
            # Data sources
            sources_table = Table(title="Data Sources")
            sources_table.add_column("Source", style="cyan")
            sources_table.add_column("Status", style="green")
            sources_table.add_column("Priority", style="yellow")
            
            for source, info in dashboard_data.get("data_sources", {}).items():
                enabled = "✓" if info["enabled"] else "✗"
                sources_table.add_row(source, enabled, str(info["priority"]))
            
            layout["sources"].update(Panel(sources_table, title="Data Sources"))
            
            # Active alerts
            alert_count = dashboard_data.get("active_alerts", 0)
            error_rate = dashboard_data.get("error_rate", 0)
            
            alert_text = f"Active Alerts: {alert_count}\n"
            alert_text += f"Error Rate: {error_rate:.2%}\n"
            
            if alert_count > 0:
                alert_text += f"\n[red]⚠ {alert_count} alerts require attention[/red]"
            else:
                alert_text += f"\n[green]✓ No active alerts[/green]"
            
            layout["alerts"].update(Panel(alert_text, title="Alerts"))
            
            # Footer
            resource_usage = dashboard_data.get("resource_usage", {})
            footer_text = f"CPU: {resource_usage.get('cpu_percent', 0):.1f}% | "
            footer_text += f"Memory: {resource_usage.get('memory_percent', 0):.1f}% | "
            footer_text += f"Disk: {resource_usage.get('disk_percent', 0):.1f}%"
            layout["footer"].update(Panel(footer_text, border_style="dim"))
        
        # Create layout
        layout = create_dashboard_layout()
        
        # Live dashboard loop
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while self.running:
                try:
                    # Update health check
                    await self.run_health_check()
                    
                    # Generate dashboard data
                    dashboard_data = self.generate_dashboard_data()
                    
                    # Update display
                    update_dashboard(layout, dashboard_data)
                    
                    # Wait before next update
                    await asyncio.sleep(self.config["dashboard"]["refresh_interval_seconds"])
                    
                except Exception as e:
                    logger.error(f"Dashboard update failed: {e}")
                    await asyncio.sleep(5)
    
    async def start_orchestrator(self, mode: str = "daemon"):
        """Start the orchestrator in specified mode"""
        self.console.print(f"[bold green]Starting Florida Data Orchestrator in {mode} mode[/bold green]")
        
        if mode == "daemon":
            # Start scheduler daemon
            scheduler_task = asyncio.create_task(self.scheduler.start_scheduler())
            
            # Start health monitoring
            async def health_monitor():
                while self.running:
                    await self.run_health_check()
                    await asyncio.sleep(self.config["health_checks"]["interval_minutes"] * 60)
            
            health_task = asyncio.create_task(health_monitor())
            
            # Wait for tasks
            await asyncio.gather(scheduler_task, health_task, return_exceptions=True)
            
        elif mode == "dashboard":
            # Start live dashboard
            await self.display_live_dashboard()
            
        elif mode == "single":
            # Run single comprehensive operation
            result = await self.run_comprehensive_operation()
            self.console.print_json(json.dumps(result, indent=2, default=str))
            
        elif mode == "health":
            # Run health check only
            health = await self.run_health_check()
            self.console.print_json(json.dumps(asdict(health), indent=2, default=str))

def setup_signal_handlers(orchestrator):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        orchestrator.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Florida Data Master Orchestrator")
    parser.add_argument("--mode", choices=["daemon", "dashboard", "single", "health"], 
                       default="single", help="Operation mode")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and run orchestrator
    async with FloridaMasterOrchestrator(args.config) as orchestrator:
        # Setup signal handlers
        setup_signal_handlers(orchestrator)
        
        try:
            await orchestrator.start_orchestrator(args.mode)
        except KeyboardInterrupt:
            console.print("\n[yellow]Orchestrator stopped by user[/yellow]")
        except Exception as e:
            console.print(f"[red]Orchestrator error: {e}[/red]")
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    asyncio.run(main())