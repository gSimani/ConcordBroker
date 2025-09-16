#!/usr/bin/env python3
"""
Florida Update Orchestrator Agent
Coordinates all Florida data update agents for daily automated updates.
Handles scheduling, error recovery, notifications, and overall workflow management.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import sqlite3
import smtplib
import sys
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
import signal
import os
import traceback

# Import our agents
from .monitor import FloridaDataMonitor, MonitorResult, FileInfo
from .downloader import FloridaDataDownloader, DownloadResult, display_progress
from .processor import FloridaDataProcessor, ProcessingResult
from .database_updater import FloridaDatabaseUpdater, UpdateResult

logger = logging.getLogger(__name__)

@dataclass
class OrchestrationResult:
    """Result of complete orchestration run"""
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    files_monitored: int
    files_downloaded: int
    files_processed: int
    files_updated: int
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, Any]

@dataclass
class AgentStatus:
    """Status of individual agent"""
    name: str
    status: str  # running, completed, failed, pending
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    progress: float  # 0-100
    message: str
    error: Optional[str]

class FloridaUpdateOrchestrator:
    """Orchestrates daily Florida property data updates"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        
        # Agent configurations
        self.monitor_config = config.get('monitor', {})
        self.downloader_config = config.get('downloader', {})
        self.processor_config = config.get('processor', {})
        self.database_config = config.get('database', {})
        
        # Orchestration settings
        self.max_concurrent_files = config.get('max_concurrent_files', 3)
        self.retry_failed_steps = config.get('retry_failed_steps', True)
        self.max_retries = config.get('max_retries', 2)
        self.retry_delay = config.get('retry_delay', 300)  # 5 minutes
        self.continue_on_error = config.get('continue_on_error', True)
        
        # Notification settings
        self.notification_config = config.get('notifications', {})
        self.enable_notifications = self.notification_config.get('enabled', False)
        
        # State management
        self.db_path = Path(config.get('state_db_path', 'florida_orchestrator_state.db'))
        self.log_dir = Path(config.get('log_directory', 'florida_daily_updates/logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Agent instances
        self.monitor = None
        self.downloader = None
        self.processor = None
        self.database_updater = None
        
        # Runtime state
        self.current_run_id = None
        self.agent_status = {}
        self.running = False
        self.shutdown_requested = False
        
        # Initialize database
        self._init_database()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Statistics
        self.orchestration_stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_files_processed': 0,
            'total_records_updated': 0,
            'total_runtime': 0.0,
            'last_successful_run': None,
            'average_runtime': 0.0
        }
    
    def _init_database(self):
        """Initialize SQLite database for orchestration state"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS orchestration_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration REAL,
                    success BOOLEAN,
                    files_monitored INTEGER DEFAULT 0,
                    files_downloaded INTEGER DEFAULT 0,
                    files_processed INTEGER DEFAULT 0,
                    files_updated INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    warning_count INTEGER DEFAULT 0,
                    summary TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    file_path TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration REAL,
                    success BOOLEAN,
                    error TEXT,
                    result_data TEXT
                )
            ''')
            
            conn.commit()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    async def run_daily_update(self) -> OrchestrationResult:
        """Run complete daily update process"""
        self.current_run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = datetime.now()
        
        logger.info(f"Starting Florida daily update run: {self.current_run_id}")
        
        # Initialize result
        result = OrchestrationResult(
            start_time=start_time,
            end_time=start_time,  # Will be updated
            duration=0.0,
            success=False,
            files_monitored=0,
            files_downloaded=0,
            files_processed=0,
            files_updated=0,
            errors=[],
            warnings=[],
            summary={}
        )
        
        try:
            self.running = True
            
            # Initialize agents
            await self._initialize_agents()
            
            # Step 1: Monitor for new/updated files
            monitor_result = await self._run_monitor_step()
            result.files_monitored = len(monitor_result.new_files + monitor_result.updated_files)
            
            if not monitor_result.success:
                result.errors.extend(monitor_result.errors)
                if not self.continue_on_error:
                    raise Exception("Monitor step failed")
            
            if self.shutdown_requested:
                raise Exception("Shutdown requested")
            
            # Get files to process
            files_to_process = monitor_result.new_files + monitor_result.updated_files
            
            if not files_to_process:
                logger.info("No new or updated files found")
                result.success = True
                result.summary['message'] = "No updates needed"
                return result
            
            logger.info(f"Found {len(files_to_process)} files to process")
            
            # Step 2: Download files
            download_results = await self._run_download_step(files_to_process)
            result.files_downloaded = sum(1 for r in download_results if r.success)
            
            if self.shutdown_requested:
                raise Exception("Shutdown requested")
            
            # Step 3: Process downloaded files
            processing_results = await self._run_processing_step(download_results)
            result.files_processed = sum(1 for r in processing_results if r.success)
            
            if self.shutdown_requested:
                raise Exception("Shutdown requested")
            
            # Step 4: Update database
            update_results = await self._run_database_update_step(processing_results)
            result.files_updated = sum(1 for r in update_results if r.success)
            
            # Collect errors and warnings
            for results_list in [download_results, processing_results, update_results]:
                for res in results_list:
                    if hasattr(res, 'error') and res.error:
                        result.errors.append(res.error)
                    if hasattr(res, 'validation_errors') and res.validation_errors:
                        result.warnings.extend(res.validation_errors)
            
            # Determine overall success
            result.success = (
                result.files_monitored > 0 and
                result.files_downloaded >= result.files_monitored * 0.8 and  # 80% success rate
                result.files_processed >= result.files_downloaded * 0.8 and
                result.files_updated >= result.files_processed * 0.8
            )
            
            # Calculate summary
            result.summary = {
                'run_id': self.current_run_id,
                'counties_processed': list(set(f.county for f in files_to_process)),
                'file_types_processed': list(set(f.file_type for f in files_to_process)),
                'total_records_updated': sum(
                    getattr(r, 'inserted_records', 0) + getattr(r, 'updated_records', 0)
                    for r in update_results
                ),
                'performance': {
                    'avg_download_speed': self._calculate_avg_download_speed(download_results),
                    'avg_processing_rate': self._calculate_avg_processing_rate(processing_results),
                    'avg_update_rate': self._calculate_avg_update_rate(update_results)
                }
            }
            
            logger.info(f"Daily update completed: {result.success}")
            
        except Exception as e:
            error_msg = f"Orchestration failed: {str(e)}\\n{traceback.format_exc()}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
        
        finally:
            # Cleanup
            await self._cleanup_agents()
            
            # Finalize result
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
            
            # Save orchestration result
            await self._save_orchestration_result(result)
            
            # Update statistics
            self._update_orchestration_stats(result)
            
            # Send notifications
            if self.enable_notifications:
                await self._send_notification(result)
            
            self.running = False
        
        return result
    
    async def _initialize_agents(self):
        """Initialize all agent instances"""
        self.monitor = FloridaDataMonitor(self.monitor_config)
        self.downloader = FloridaDataDownloader(self.downloader_config)
        self.processor = FloridaDataProcessor(self.processor_config)
        self.database_updater = FloridaDatabaseUpdater(self.database_config)
        
        logger.debug("All agents initialized")
    
    async def _cleanup_agents(self):
        """Cleanup agent instances"""
        if self.database_updater:
            try:
                await self.database_updater.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error cleaning up database updater: {e}")
        
        logger.debug("Agents cleaned up")
    
    async def _run_monitor_step(self) -> MonitorResult:
        """Run monitoring step"""
        self._update_agent_status('monitor', 'running', 0, "Checking for new files...")
        
        try:
            async with self.monitor as monitor:
                result = await monitor.check_for_updates()
            
            if result.success:
                self._update_agent_status('monitor', 'completed', 100, 
                                        f"Found {len(result.new_files)} new, {len(result.updated_files)} updated files")
            else:
                self._update_agent_status('monitor', 'failed', 0, "Monitor check failed")
            
            return result
            
        except Exception as e:
            error_msg = f"Monitor step failed: {e}"
            self._update_agent_status('monitor', 'failed', 0, error_msg)
            
            # Return failed result
            return MonitorResult(
                timestamp=datetime.now(),
                new_files=[],
                updated_files=[],
                errors=[error_msg],
                total_files_checked=0,
                success=False
            )
    
    async def _run_download_step(self, files_to_download: List[FileInfo]) -> List[DownloadResult]:
        """Run download step for multiple files"""
        self._update_agent_status('downloader', 'running', 0, f"Downloading {len(files_to_download)} files...")
        
        results = []
        
        try:
            # Add progress callback
            downloaded_count = [0]  # Use list for closure
            
            def update_progress(progress):
                downloaded_count[0] += 1
                percent = (downloaded_count[0] / len(files_to_download)) * 100
                self._update_agent_status('downloader', 'running', percent, 
                                        f"Downloaded {downloaded_count[0]}/{len(files_to_download)} files")
            
            self.downloader.add_progress_callback(update_progress)
            
            # Download files
            urls = [file_info.url for file_info in files_to_download]
            results = await self.downloader.download_multiple(urls, self.max_concurrent_files)
            
            # Update status
            successful = sum(1 for r in results if r.success)
            if successful == len(results):
                self._update_agent_status('downloader', 'completed', 100, 
                                        f"Downloaded {successful}/{len(results)} files")
            else:
                failed = len(results) - successful
                self._update_agent_status('downloader', 'completed', 100, 
                                        f"Downloaded {successful}/{len(results)} files, {failed} failed")
            
            return results
            
        except Exception as e:
            error_msg = f"Download step failed: {e}"
            self._update_agent_status('downloader', 'failed', 0, error_msg)
            
            # Return failed results
            return [
                DownloadResult(
                    url=file_info.url,
                    filename=file_info.filename,
                    local_path="",
                    size=0,
                    duration=0.0,
                    success=False,
                    error=error_msg
                )
                for file_info in files_to_download
            ]
    
    async def _run_processing_step(self, download_results: List[DownloadResult]) -> List[ProcessingResult]:
        """Run processing step for downloaded files"""
        successful_downloads = [r for r in download_results if r.success]
        
        self._update_agent_status('processor', 'running', 0, f"Processing {len(successful_downloads)} files...")
        
        results = []
        
        for i, download_result in enumerate(successful_downloads):
            if self.shutdown_requested:
                break
            
            try:
                # Detect file type and county from filename or path
                file_type = self._detect_file_type(download_result.filename)
                county = self._detect_county(download_result.filename)
                
                # Process file
                processing_result = await self.processor.process_file(
                    download_result.local_path, file_type, county
                )
                
                results.append(processing_result)
                
                # Update progress
                progress = ((i + 1) / len(successful_downloads)) * 100
                self._update_agent_status('processor', 'running', progress, 
                                        f"Processed {i + 1}/{len(successful_downloads)} files")
                
            except Exception as e:
                error_msg = f"Processing failed for {download_result.filename}: {e}"
                logger.error(error_msg)
                
                # Create failed result
                results.append(ProcessingResult(
                    file_path=download_result.local_path,
                    file_type=self._detect_file_type(download_result.filename),
                    county=self._detect_county(download_result.filename),
                    total_records=0,
                    valid_records=0,
                    invalid_records=0,
                    new_records=0,
                    updated_records=0,
                    duplicates=0,
                    processing_time=0.0,
                    success=False,
                    error=error_msg,
                    validation_errors=[]
                ))
        
        # Update final status
        successful = sum(1 for r in results if r.success)
        if successful == len(results):
            self._update_agent_status('processor', 'completed', 100, 
                                    f"Processed {successful}/{len(results)} files")
        else:
            failed = len(results) - successful
            self._update_agent_status('processor', 'completed', 100, 
                                    f"Processed {successful}/{len(results)} files, {failed} failed")
        
        return results
    
    async def _run_database_update_step(self, processing_results: List[ProcessingResult]) -> List[UpdateResult]:
        """Run database update step"""
        successful_processing = [r for r in processing_results if r.success and r.output_file]
        
        self._update_agent_status('database', 'running', 0, f"Updating database with {len(successful_processing)} files...")
        
        results = []
        
        async with self.database_updater as db_updater:
            for i, processing_result in enumerate(successful_processing):
                if self.shutdown_requested:
                    break
                
                try:
                    # Update database
                    update_result = await db_updater.update_from_file(
                        processing_result.output_file,
                        processing_result.file_type,
                        processing_result.county
                    )
                    
                    results.append(update_result)
                    
                    # Update progress
                    progress = ((i + 1) / len(successful_processing)) * 100
                    self._update_agent_status('database', 'running', progress, 
                                            f"Updated {i + 1}/{len(successful_processing)} files")
                    
                except Exception as e:
                    error_msg = f"Database update failed for {processing_result.output_file}: {e}"
                    logger.error(error_msg)
                    
                    # Create failed result
                    results.append(UpdateResult(
                        file_path=processing_result.output_file,
                        file_type=processing_result.file_type,
                        county=processing_result.county,
                        total_records=0,
                        inserted_records=0,
                        updated_records=0,
                        skipped_records=0,
                        error_records=0,
                        update_time=0.0,
                        success=False,
                        error=error_msg
                    ))
        
        # Update final status
        successful = sum(1 for r in results if r.success)
        total_records = sum(r.inserted_records + r.updated_records for r in results if r.success)
        
        if successful == len(results):
            self._update_agent_status('database', 'completed', 100, 
                                    f"Updated {successful}/{len(results)} files, {total_records:,} records")
        else:
            failed = len(results) - successful
            self._update_agent_status('database', 'completed', 100, 
                                    f"Updated {successful}/{len(results)} files, {failed} failed, {total_records:,} records")
        
        return results
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename"""
        filename_lower = filename.lower()
        if 'nal' in filename_lower:
            return 'NAL'
        elif 'nap' in filename_lower:
            return 'NAP'
        elif 'sdf' in filename_lower:
            return 'SDF'
        else:
            return 'UNKNOWN'
    
    def _detect_county(self, filename: str) -> str:
        """Detect county from filename"""
        filename_lower = filename.lower()
        
        county_mappings = {
            'broward': 'broward',
            'miami_dade': 'miami-dade',
            'palm_beach': 'palm-beach',
            'hillsborough': 'hillsborough',
            'orange': 'orange',
            'pinellas': 'pinellas'
        }
        
        for county_key, county_name in county_mappings.items():
            if county_key in filename_lower:
                return county_name
        
        return 'unknown'
    
    def _update_agent_status(self, agent_name: str, status: str, progress: float, message: str, error: str = None):
        """Update agent status"""
        if agent_name not in self.agent_status:
            self.agent_status[agent_name] = AgentStatus(
                name=agent_name,
                status='pending',
                start_time=None,
                end_time=None,
                duration=None,
                progress=0.0,
                message='',
                error=None
            )
        
        agent = self.agent_status[agent_name]
        
        if status == 'running' and agent.status != 'running':
            agent.start_time = datetime.now()
        elif status in ['completed', 'failed'] and agent.status == 'running':
            agent.end_time = datetime.now()
            if agent.start_time:
                agent.duration = (agent.end_time - agent.start_time).total_seconds()
        
        agent.status = status
        agent.progress = progress
        agent.message = message
        agent.error = error
        
        logger.debug(f"{agent_name}: {status} - {message}")
    
    def _calculate_avg_download_speed(self, download_results: List[DownloadResult]) -> float:
        """Calculate average download speed in MB/s"""
        total_bytes = sum(r.size for r in download_results if r.success and r.size)
        total_time = sum(r.duration for r in download_results if r.success and r.duration)
        
        if total_time > 0:
            return (total_bytes / total_time) / (1024 * 1024)  # MB/s
        return 0.0
    
    def _calculate_avg_processing_rate(self, processing_results: List[ProcessingResult]) -> float:
        """Calculate average processing rate in records/s"""
        total_records = sum(r.total_records for r in processing_results if r.success)
        total_time = sum(r.processing_time for r in processing_results if r.success)
        
        if total_time > 0:
            return total_records / total_time
        return 0.0
    
    def _calculate_avg_update_rate(self, update_results: List[UpdateResult]) -> float:
        """Calculate average update rate in records/s"""
        total_records = sum(r.total_records for r in update_results if r.success)
        total_time = sum(r.update_time for r in update_results if r.success)
        
        if total_time > 0:
            return total_records / total_time
        return 0.0
    
    async def _save_orchestration_result(self, result: OrchestrationResult):
        """Save orchestration result to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO orchestration_runs 
                (run_id, start_time, end_time, duration, success, files_monitored, 
                 files_downloaded, files_processed, files_updated, error_count, 
                 warning_count, summary, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.current_run_id,
                result.start_time.isoformat(),
                result.end_time.isoformat(),
                result.duration,
                result.success,
                result.files_monitored,
                result.files_downloaded,
                result.files_processed,
                result.files_updated,
                len(result.errors),
                len(result.warnings),
                json.dumps(result.summary),
                json.dumps(asdict(result), default=str)
            ))
            conn.commit()
    
    def _update_orchestration_stats(self, result: OrchestrationResult):
        """Update orchestration statistics"""
        self.orchestration_stats['total_runs'] += 1
        
        if result.success:
            self.orchestration_stats['successful_runs'] += 1
            self.orchestration_stats['last_successful_run'] = result.end_time
        else:
            self.orchestration_stats['failed_runs'] += 1
        
        self.orchestration_stats['total_files_processed'] += result.files_processed
        self.orchestration_stats['total_records_updated'] += result.summary.get('total_records_updated', 0)
        self.orchestration_stats['total_runtime'] += result.duration
        
        if self.orchestration_stats['total_runs'] > 0:
            self.orchestration_stats['average_runtime'] = (
                self.orchestration_stats['total_runtime'] / self.orchestration_stats['total_runs']
            )
    
    async def _send_notification(self, result: OrchestrationResult):
        """Send notification about orchestration result"""
        try:
            if self.notification_config.get('email', {}).get('enabled', False):
                await self._send_email_notification(result)
            
            if self.notification_config.get('slack', {}).get('enabled', False):
                await self._send_slack_notification(result)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def _send_email_notification(self, result: OrchestrationResult):
        """Send email notification"""
        email_config = self.notification_config.get('email', {})
        
        # Create message
        msg = MimeMultipart()
        msg['From'] = email_config.get('from_address', 'noreply@concordbroker.com')
        msg['To'] = ', '.join(email_config.get('to_addresses', []))
        msg['Subject'] = f"Florida Data Update {'Completed' if result.success else 'Failed'} - {self.current_run_id}"
        
        # Create body
        body = f"""
Florida Property Data Daily Update Report
Run ID: {self.current_run_id}
Status: {'SUCCESS' if result.success else 'FAILED'}
Duration: {result.duration:.1f} seconds

Summary:
- Files Monitored: {result.files_monitored}
- Files Downloaded: {result.files_downloaded}
- Files Processed: {result.files_processed}
- Files Updated: {result.files_updated}
- Errors: {len(result.errors)}
- Warnings: {len(result.warnings)}

Performance:
{json.dumps(result.summary.get('performance', {}), indent=2)}

Counties Processed: {', '.join(result.summary.get('counties_processed', []))}
File Types: {', '.join(result.summary.get('file_types_processed', []))}
Total Records Updated: {result.summary.get('total_records_updated', 0):,}
        """
        
        if result.errors:
            body += "\\n\\nErrors:\\n" + "\\n".join(result.errors[:10])
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        smtp_server = email_config.get('smtp_server', 'localhost')
        smtp_port = email_config.get('smtp_port', 587)
        username = email_config.get('username')
        password = email_config.get('password')
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if username and password:
                server.starttls()
                server.login(username, password)
            server.send_message(msg)
        
        logger.info("Email notification sent")
    
    async def _send_slack_notification(self, result: OrchestrationResult):
        """Send Slack notification (placeholder)"""
        # TODO: Implement Slack notification
        logger.info("Slack notification would be sent here")
    
    def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics"""
        return self.orchestration_stats.copy()
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        return {
            'running': self.running,
            'current_run_id': self.current_run_id,
            'agent_status': {name: asdict(status) for name, status in self.agent_status.items()},
            'shutdown_requested': self.shutdown_requested
        }
    
    def display_status(self):
        """Display current status using Rich"""
        if not self.running:
            self.console.print(Panel("No orchestration currently running", title="Status"))
            return
        
        # Create status table
        table = Table(title=f"Florida Data Update - Run {self.current_run_id}")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Progress", style="yellow")
        table.add_column("Message", style="white")
        
        for agent_name, status in self.agent_status.items():
            progress_bar = f"{status.progress:.1f}%" if status.progress > 0 else "0%"
            
            status_color = {
                'pending': 'yellow',
                'running': 'blue',
                'completed': 'green',
                'failed': 'red'
            }.get(status.status, 'white')
            
            table.add_row(
                agent_name.title(),
                f"[{status_color}]{status.status.upper()}[/{status_color}]",
                progress_bar,
                status.message
            )
        
        self.console.print(table)

# Standalone execution for testing
async def main():
    """Test the orchestrator"""
    config = {
        'monitor': {
            'counties': ['broward'],
            'file_types': ['NAL', 'NAP', 'SDF'],
            'current_year': '2025P'
        },
        'downloader': {
            'download_directory': 'test_downloads',
            'max_concurrent_downloads': 2
        },
        'processor': {
            'output_directory': 'test_processed',
            'batch_size': 1000
        },
        'database': {
            'batch_size': 5000,
            'create_tables': True
        },
        'max_concurrent_files': 3,
        'continue_on_error': True,
        'notifications': {
            'enabled': False
        }
    }
    
    orchestrator = FloridaUpdateOrchestrator(config)
    
    print("Starting Florida data update orchestration...")
    result = await orchestrator.run_daily_update()
    
    print(f"\\nOrchestration Result:")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration:.1f}s")
    print(f"  Files Monitored: {result.files_monitored}")
    print(f"  Files Downloaded: {result.files_downloaded}")
    print(f"  Files Processed: {result.files_processed}")
    print(f"  Files Updated: {result.files_updated}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    if result.errors:
        print("\\nErrors:")
        for error in result.errors[:5]:
            print(f"  - {error}")

if __name__ == "__main__":
    asyncio.run(main())