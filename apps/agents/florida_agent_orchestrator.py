#!/usr/bin/env python3
"""
Florida Property Data Agent Orchestrator
Production-ready orchestrator for automated daily updates of Florida property data

This is the main coordination system that manages:
- Daily automated monitoring for new/updated files
- Download agents for fetching from Florida Revenue portal
- Data processing agents for validation and transformation
- Database agents for Supabase operations
- Monitoring and alerting agents

Features:
- Comprehensive error handling and recovery
- Performance optimization for large datasets
- Scalable to all 67 Florida counties
- Real-time monitoring and alerts
- Historical data versioning
"""

import asyncio
import logging
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import argparse
import signal
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress
import schedule

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "workers"))

# Import agent components
from florida_download_agent import FloridaDownloadAgent
from florida_processing_agent import FloridaProcessingAgent  
from florida_database_agent import FloridaDatabaseAgent
from florida_monitoring_agent import FloridaMonitoringAgent
from florida_config_manager import FloridaConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_agent_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()

@dataclass
class OrchestrationResult:
    """Result of a complete orchestration cycle"""
    timestamp: datetime
    operation_id: str
    status: str  # success, partial, failed
    components_run: List[str]
    files_discovered: int
    files_downloaded: int
    files_processed: int
    records_updated: int
    errors: List[Dict[str, Any]]
    duration_seconds: float
    next_scheduled_run: Optional[datetime] = None

@dataclass
class AgentHealth:
    """Health status of an individual agent"""
    name: str
    status: str  # healthy, degraded, failed, unknown
    last_run: Optional[datetime]
    success_rate: float
    error_count: int
    performance_metrics: Dict[str, float]
    alerts: List[str]

class FloridaAgentOrchestrator:
    """Production-ready orchestrator for Florida property data agents"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = FloridaConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Initialize agents
        self.download_agent = None
        self.processing_agent = None
        self.database_agent = None
        self.monitoring_agent = None
        
        # Orchestrator state
        self.running = False
        self.start_time = None
        self.operation_history: List[OrchestrationResult] = []
        self.agent_health: Dict[str, AgentHealth] = {}
        
        # Statistics
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "partial_operations": 0,
            "failed_operations": 0,
            "total_files_processed": 0,
            "total_records_updated": 0,
            "uptime_start": datetime.now()
        }
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def __aenter__(self):
        """Initialize all agent components"""
        logger.info("Initializing Florida Agent Orchestrator...")
        
        try:
            # Initialize agents in dependency order
            self.download_agent = FloridaDownloadAgent(self.config_manager)
            await self.download_agent.initialize()
            
            self.processing_agent = FloridaProcessingAgent(self.config_manager)
            await self.processing_agent.initialize()
            
            self.database_agent = FloridaDatabaseAgent(self.config_manager)
            await self.database_agent.initialize()
            
            self.monitoring_agent = FloridaMonitoringAgent(self.config_manager)
            await self.monitoring_agent.initialize()
            
            self.start_time = datetime.now()
            self.running = True
            
            logger.info("✅ All agents initialized successfully")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all agents"""
        logger.info("Shutting down Florida Agent Orchestrator...")
        self.running = False
        
        # Shutdown agents in reverse order
        agents = [
            ("monitoring_agent", self.monitoring_agent),
            ("database_agent", self.database_agent), 
            ("processing_agent", self.processing_agent),
            ("download_agent", self.download_agent)
        ]
        
        for name, agent in agents:
            if agent:
                try:
                    await agent.cleanup()
                    logger.info(f"✅ {name} shutdown complete")
                except Exception as e:
                    logger.error(f"❌ {name} shutdown failed: {e}")

    async def run_health_check(self) -> Dict[str, AgentHealth]:
        """Perform comprehensive health check on all agents"""
        logger.info("Running comprehensive health check...")
        
        health_results = {}
        
        # Check each agent
        agents = [
            ("download_agent", self.download_agent),
            ("processing_agent", self.processing_agent),
            ("database_agent", self.database_agent),
            ("monitoring_agent", self.monitoring_agent)
        ]
        
        for agent_name, agent in agents:
            if agent:
                try:
                    health = await agent.get_health_status()
                    health_results[agent_name] = health
                    
                except Exception as e:
                    logger.error(f"Health check failed for {agent_name}: {e}")
                    health_results[agent_name] = AgentHealth(
                        name=agent_name,
                        status="failed",
                        last_run=None,
                        success_rate=0.0,
                        error_count=1,
                        performance_metrics={},
                        alerts=[f"Health check failed: {str(e)}"]
                    )
        
        self.agent_health = health_results
        return health_results

    async def run_daily_update_cycle(self) -> OrchestrationResult:
        """Run a complete daily update cycle"""
        operation_id = f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Starting daily update cycle: {operation_id}")
        
        result = OrchestrationResult(
            timestamp=start_time,
            operation_id=operation_id,
            status="running",
            components_run=[],
            files_discovered=0,
            files_downloaded=0,
            files_processed=0,
            records_updated=0,
            errors=[],
            duration_seconds=0.0
        )
        
        try:
            # 1. Discovery Phase - Check for new/updated files
            logger.info("🔍 Phase 1: Discovery - Checking for new/updated files")
            discovery_result = await self.download_agent.discover_available_files()
            result.components_run.append("download_agent_discovery")
            result.files_discovered = len(discovery_result.get("available_files", []))
            
            if discovery_result.get("errors"):
                result.errors.extend(discovery_result["errors"])
            
            # 2. Download Phase - Download new/changed files
            if result.files_discovered > 0:
                logger.info(f"📥 Phase 2: Download - Downloading {result.files_discovered} files")
                download_result = await self.download_agent.download_files(discovery_result["available_files"])
                result.components_run.append("download_agent_download")
                result.files_downloaded = len(download_result.get("downloaded_files", []))
                
                if download_result.get("errors"):
                    result.errors.extend(download_result["errors"])
            else:
                logger.info("📥 Phase 2: Download - No new files to download")
                result.files_downloaded = 0
            
            # 3. Processing Phase - Process downloaded files
            if result.files_downloaded > 0:
                logger.info(f"⚙️ Phase 3: Processing - Processing {result.files_downloaded} files")
                processing_result = await self.processing_agent.process_files(
                    download_result.get("downloaded_files", [])
                )
                result.components_run.append("processing_agent")
                result.files_processed = processing_result.get("files_processed", 0)
                
                if processing_result.get("errors"):
                    result.errors.extend(processing_result["errors"])
                
                # 4. Database Phase - Update database with processed data
                if result.files_processed > 0:
                    logger.info("💾 Phase 4: Database - Updating database with processed data")
                    db_result = await self.database_agent.update_database(
                        processing_result.get("processed_data", [])
                    )
                    result.components_run.append("database_agent")
                    result.records_updated = db_result.get("records_updated", 0)
                    
                    if db_result.get("errors"):
                        result.errors.extend(db_result["errors"])
                else:
                    logger.info("💾 Phase 4: Database - No processed data to update")
                    result.records_updated = 0
            else:
                logger.info("⚙️ Phase 3: Processing - No downloaded files to process")
                logger.info("💾 Phase 4: Database - No new data to update")
                result.files_processed = 0
                result.records_updated = 0
            
            # 5. Monitoring Phase - Update monitoring and send alerts
            logger.info("📊 Phase 5: Monitoring - Updating metrics and sending alerts")
            monitoring_result = await self.monitoring_agent.update_metrics_and_alerts(result)
            result.components_run.append("monitoring_agent")
            
            if monitoring_result.get("errors"):
                result.errors.extend(monitoring_result["errors"])
            
            # Determine final status
            if len(result.errors) == 0:
                result.status = "success"
                self.stats["successful_operations"] += 1
            elif result.files_processed > 0 or result.records_updated > 0:
                result.status = "partial"
                self.stats["partial_operations"] += 1
            else:
                result.status = "failed"
                self.stats["failed_operations"] += 1
            
        except Exception as e:
            logger.error(f"Daily update cycle failed: {e}")
            result.status = "failed"
            result.errors.append({
                "component": "orchestrator",
                "error": str(e),
                "timestamp": datetime.now()
            })
            self.stats["failed_operations"] += 1
        
        # Calculate duration and schedule next run
        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        result.next_scheduled_run = self._calculate_next_run()
        
        # Update statistics
        self.stats["total_operations"] += 1
        self.stats["total_files_processed"] += result.files_processed
        self.stats["total_records_updated"] += result.records_updated
        
        # Store in history
        self.operation_history.append(result)
        
        # Keep only last 30 days of history
        cutoff_date = datetime.now() - timedelta(days=30)
        self.operation_history = [
            op for op in self.operation_history 
            if op.timestamp > cutoff_date
        ]
        
        logger.info(f"✅ Daily update cycle completed: {result.status} in {result.duration_seconds:.2f}s")
        
        return result

    def _calculate_next_run(self) -> datetime:
        """Calculate next scheduled run time based on configuration"""
        schedule_config = self.config.get("scheduling", {})
        next_run_hour = schedule_config.get("daily_hour", 2)  # Default 2 AM
        
        # Schedule for tomorrow at the configured hour
        tomorrow = datetime.now().replace(hour=next_run_hour, minute=0, second=0, microsecond=0)
        if tomorrow <= datetime.now():
            tomorrow += timedelta(days=1)
            
        return tomorrow

    async def run_scheduler(self):
        """Run the daily scheduler"""
        logger.info("Starting Florida property data scheduler...")
        
        # Schedule daily updates
        schedule_config = self.config.get("scheduling", {})
        daily_hour = schedule_config.get("daily_hour", 2)  # 2 AM default
        
        schedule.every().day.at(f"{daily_hour:02d}:00").do(self._schedule_daily_update)
        
        # Also allow manual hourly checks for urgent updates
        if schedule_config.get("enable_hourly_checks", False):
            schedule.every().hour.do(self._schedule_hourly_check)
        
        logger.info(f"📅 Daily updates scheduled for {daily_hour:02d}:00")
        
        # Main scheduler loop
        while self.running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    def _schedule_daily_update(self):
        """Scheduled daily update (sync wrapper)"""
        asyncio.create_task(self.run_daily_update_cycle())
    
    def _schedule_hourly_check(self):
        """Scheduled hourly check for urgent updates (sync wrapper)"""
        asyncio.create_task(self._run_hourly_check())
    
    async def _run_hourly_check(self):
        """Run hourly check for urgent updates"""
        logger.info("Running hourly check for urgent updates...")
        
        # Quick discovery check without full processing
        discovery_result = await self.download_agent.discover_available_files()
        urgent_files = discovery_result.get("urgent_files", [])
        
        if urgent_files:
            logger.info(f"Found {len(urgent_files)} urgent files, triggering immediate update")
            await self.run_daily_update_cycle()

    def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        uptime_seconds = (datetime.now() - self.stats["uptime_start"]).total_seconds()
        
        # Calculate success rate
        total_ops = self.stats["total_operations"] 
        success_rate = (
            (self.stats["successful_operations"] + self.stats["partial_operations"]) / total_ops
        ) if total_ops > 0 else 0.0
        
        return {
            "timestamp": datetime.now(),
            "system_status": "healthy" if success_rate > 0.8 else "degraded" if success_rate > 0.5 else "critical",
            "uptime_hours": uptime_seconds / 3600,
            "statistics": self.stats.copy(),
            "success_rate": success_rate,
            "agent_health": {name: asdict(health) for name, health in self.agent_health.items()},
            "recent_operations": [asdict(op) for op in self.operation_history[-10:]],
            "next_scheduled_run": self._calculate_next_run(),
            "configuration": self.config.get("orchestrator", {})
        }

    async def run_interactive_dashboard(self):
        """Run interactive dashboard for monitoring"""
        logger.info("Starting interactive dashboard...")
        
        with Live(console=console, refresh_per_second=1) as live:
            while self.running:
                try:
                    # Update health check
                    await self.run_health_check()
                    
                    # Generate status report
                    status = self.generate_status_report()
                    
                    # Create dashboard layout
                    dashboard = self._create_dashboard_display(status)
                    live.update(dashboard)
                    
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Dashboard error: {e}")
                    await asyncio.sleep(10)

    def _create_dashboard_display(self, status: Dict[str, Any]) -> Panel:
        """Create dashboard display layout"""
        # System overview table
        overview_table = Table(title="System Overview")
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="green")
        
        overview_table.add_row("System Status", status["system_status"].upper())
        overview_table.add_row("Uptime", f"{status['uptime_hours']:.1f} hours")
        overview_table.add_row("Success Rate", f"{status['success_rate']:.1%}")
        overview_table.add_row("Total Operations", str(status["statistics"]["total_operations"]))
        overview_table.add_row("Files Processed", str(status["statistics"]["total_files_processed"]))
        overview_table.add_row("Records Updated", str(status["statistics"]["total_records_updated"]))
        overview_table.add_row("Next Run", status["next_scheduled_run"].strftime("%Y-%m-%d %H:%M"))
        
        # Agent health table
        health_table = Table(title="Agent Health")
        health_table.add_column("Agent", style="cyan")
        health_table.add_column("Status", style="green")
        health_table.add_column("Success Rate", style="yellow")
        health_table.add_column("Errors", style="red")
        
        for agent_name, health in status["agent_health"].items():
            color = "green" if health["status"] == "healthy" else "yellow" if health["status"] == "degraded" else "red"
            health_table.add_row(
                agent_name,
                f"[{color}]{health['status'].upper()}[/{color}]",
                f"{health['success_rate']:.1%}",
                str(health['error_count'])
            )
        
        # Combine into panel
        dashboard_content = f"{overview_table}\n\n{health_table}"
        
        return Panel(
            dashboard_content,
            title=f"Florida Property Data Agent Orchestrator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue"
        )

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Florida Property Data Agent Orchestrator")
    parser.add_argument("--mode", 
                       choices=["daemon", "single", "dashboard", "health", "config"], 
                       default="single",
                       help="Operation mode")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--log-level", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO",
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        async with FloridaAgentOrchestrator(args.config) as orchestrator:
            if args.mode == "single":
                # Run single daily update cycle
                result = await orchestrator.run_daily_update_cycle()
                console.print_json(json.dumps(asdict(result), indent=2, default=str))
                
            elif args.mode == "daemon":
                # Run as daemon with scheduler
                await orchestrator.run_scheduler()
                
            elif args.mode == "dashboard":
                # Run interactive dashboard
                await orchestrator.run_interactive_dashboard()
                
            elif args.mode == "health":
                # Run health check only
                health = await orchestrator.run_health_check()
                console.print_json(json.dumps({name: asdict(h) for name, h in health.items()}, indent=2, default=str))
                
            elif args.mode == "config":
                # Show configuration
                console.print_json(json.dumps(orchestrator.config, indent=2, default=str))
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Orchestrator stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Orchestrator error: {e}[/red]")
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())