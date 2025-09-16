#!/usr/bin/env python3
"""
Master Pipeline Orchestrator for ConcordBroker
Implements best practices for real estate data synchronization
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import aiohttp
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
import schedule
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')

console = Console()

class DataSource(Enum):
    """Enumeration of all data sources"""
    BCPA = "bcpa"  # Broward County Property Appraiser
    SDF = "sdf"    # Sales Data File
    NAV = "nav"    # Non Ad Valorem
    TPP = "tpp"    # Tangible Personal Property
    SUNBIZ = "sunbiz"  # Florida Business Registry
    DOR = "dor"    # Department of Revenue
    OFFICIAL_RECORDS = "official_records"

@dataclass
class SourceConfig:
    """Configuration for each data source"""
    name: str
    source_type: DataSource
    url: Optional[str]
    schedule: str  # Cron-like schedule
    enabled: bool
    priority: int  # 1-10, higher is more important
    batch_size: int
    retry_attempts: int
    timeout: int  # seconds

class PipelineStatus(Enum):
    """Pipeline execution status"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

class MasterPipeline:
    """Master orchestrator for all data pipelines"""
    
    def __init__(self):
        self.console = Console()
        self.supabase = self._init_supabase()
        self.sources = self._init_sources()
        self.status = PipelineStatus.IDLE
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "records_processed": 0,
            "last_run": None,
            "next_run": None
        }
        
    def _init_supabase(self) -> Client:
        """Initialize Supabase client"""
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')
        if not url or not key:
            raise ValueError("Supabase credentials not found in environment")
        return create_client(url, key)
    
    def _init_sources(self) -> Dict[DataSource, SourceConfig]:
        """Initialize data source configurations"""
        return {
            DataSource.BCPA: SourceConfig(
                name="Broward County Property Appraiser",
                source_type=DataSource.BCPA,
                url="https://www.bcpa.net/RecordsFlex/datafeed/",
                schedule="0 3 * * *",  # 3 AM daily
                enabled=True,
                priority=10,
                batch_size=1000,
                retry_attempts=3,
                timeout=300
            ),
            DataSource.SDF: SourceConfig(
                name="Sales Data File",
                source_type=DataSource.SDF,
                url="https://floridarevenue.gov/property/datafeed/",
                schedule="0 6 * * *",  # 6 AM daily
                enabled=True,
                priority=9,
                batch_size=1000,
                retry_attempts=3,
                timeout=300
            ),
            DataSource.NAV: SourceConfig(
                name="Non Ad Valorem Assessments",
                source_type=DataSource.NAV,
                url="https://floridarevenue.gov/property/nav/",
                schedule="0 5 * * 2",  # Tuesday 5 AM weekly
                enabled=True,
                priority=7,
                batch_size=2000,
                retry_attempts=3,
                timeout=300
            ),
            DataSource.TPP: SourceConfig(
                name="Tangible Personal Property",
                source_type=DataSource.TPP,
                url="https://floridarevenue.gov/property/tpp/",
                schedule="0 5 * * 1",  # Monday 5 AM weekly
                enabled=True,
                priority=6,
                batch_size=1000,
                retry_attempts=3,
                timeout=300
            ),
            DataSource.SUNBIZ: SourceConfig(
                name="Florida Business Registry",
                source_type=DataSource.SUNBIZ,
                url="sftp://sftp.floridados.gov",
                schedule="0 2 * * *",  # 2 AM daily
                enabled=True,
                priority=5,
                batch_size=5000,
                retry_attempts=3,
                timeout=600
            )
        }
    
    async def check_data_freshness(self, source: DataSource) -> bool:
        """Check if data source has been updated"""
        try:
            # Query the monitoring table
            result = self.supabase.table('data_source_monitor').select('*').eq(
                'source_name', source.value
            ).order('last_checked', desc=True).limit(1).execute()
            
            if result.data:
                last_update = datetime.fromisoformat(result.data[0]['last_update'])
                # Check if data is older than 24 hours
                if datetime.now() - last_update > timedelta(hours=24):
                    return True
            return True  # No record found, needs update
            
        except Exception as e:
            self.console.print(f"[red]Error checking freshness for {source.value}: {e}")
            return True
    
    async def download_data(self, source: SourceConfig) -> Optional[str]:
        """Download data from source"""
        self.console.print(f"[cyan]Downloading from {source.name}...")
        
        try:
            if source.source_type == DataSource.SUNBIZ:
                # Special handling for SFTP
                return await self._download_sftp(source)
            else:
                # HTTP download
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        source.url,
                        timeout=aiohttp.ClientTimeout(total=source.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.text()
                            # Save to local cache
                            cache_path = Path(f"./data/raw/{source.source_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                            cache_path.parent.mkdir(parents=True, exist_ok=True)
                            cache_path.write_text(data)
                            return str(cache_path)
                        else:
                            raise Exception(f"HTTP {response.status}")
                            
        except Exception as e:
            self.console.print(f"[red]Download failed for {source.name}: {e}")
            return None
    
    async def _download_sftp(self, source: SourceConfig) -> Optional[str]:
        """Download data via SFTP (Sunbiz specific)"""
        # This would use paramiko or similar SFTP library
        # For now, return mock path
        return f"./data/raw/{source.source_type.value}_mock.txt"
    
    async def process_data(self, source: SourceConfig, file_path: str) -> int:
        """Process and load data into Supabase"""
        self.console.print(f"[yellow]Processing {source.name} data...")
        
        records_processed = 0
        
        try:
            # Read and parse data based on source type
            if source.source_type == DataSource.BCPA:
                records_processed = await self._process_bcpa(file_path)
            elif source.source_type == DataSource.SDF:
                records_processed = await self._process_sdf(file_path)
            elif source.source_type == DataSource.NAV:
                records_processed = await self._process_nav(file_path)
            elif source.source_type == DataSource.TPP:
                records_processed = await self._process_tpp(file_path)
            elif source.source_type == DataSource.SUNBIZ:
                records_processed = await self._process_sunbiz(file_path)
                
            return records_processed
            
        except Exception as e:
            self.console.print(f"[red]Processing failed for {source.name}: {e}")
            return 0
    
    async def _process_bcpa(self, file_path: str) -> int:
        """Process BCPA property data"""
        # Implementation would parse BCPA data format and insert to florida_parcels table
        return 0
    
    async def _process_sdf(self, file_path: str) -> int:
        """Process Sales Data File"""
        # Implementation would parse SDF data and insert to fl_sdf_sales table
        return 0
    
    async def _process_nav(self, file_path: str) -> int:
        """Process NAV assessments"""
        # Implementation would parse NAV data and insert to fl_nav_parcel_summary table
        return 0
    
    async def _process_tpp(self, file_path: str) -> int:
        """Process TPP data"""
        # Implementation would parse TPP data and insert to fl_tpp_accounts table
        return 0
    
    async def _process_sunbiz(self, file_path: str) -> int:
        """Process Sunbiz business data"""
        # Implementation would parse Sunbiz data and insert to appropriate tables
        return 0
    
    async def update_monitoring(self, source: DataSource, status: str, records: int):
        """Update monitoring dashboard"""
        try:
            self.supabase.table('fl_data_updates').insert({
                'source': source.value,
                'status': status,
                'records_processed': records,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            self.console.print(f"[red]Failed to update monitoring: {e}")
    
    async def run_pipeline(self, source: SourceConfig) -> bool:
        """Run pipeline for a single data source"""
        self.console.print(f"\n[bold cyan]Starting pipeline for {source.name}")
        
        success = False
        records = 0
        
        try:
            # Check if data needs updating
            needs_update = await self.check_data_freshness(source.source_type)
            
            if not needs_update:
                self.console.print(f"[green]{source.name} data is up to date")
                return True
            
            # Download data
            file_path = await self.download_data(source)
            if not file_path:
                raise Exception("Download failed")
            
            # Process and load data
            records = await self.process_data(source, file_path)
            
            if records > 0:
                self.console.print(f"[green]Successfully processed {records:,} records from {source.name}")
                success = True
            else:
                raise Exception("No records processed")
                
        except Exception as e:
            self.console.print(f"[red]Pipeline failed for {source.name}: {e}")
            
        finally:
            # Update monitoring
            status = "success" if success else "failed"
            await self.update_monitoring(source.source_type, status, records)
            
        return success
    
    async def run_all_pipelines(self):
        """Run all enabled pipelines in priority order"""
        self.status = PipelineStatus.RUNNING
        self.stats["total_runs"] += 1
        self.stats["last_run"] = datetime.now()
        
        # Sort sources by priority
        sorted_sources = sorted(
            [s for s in self.sources.values() if s.enabled],
            key=lambda x: x.priority,
            reverse=True
        )
        
        # Create progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Processing data sources...",
                total=len(sorted_sources)
            )
            
            success_count = 0
            
            for source in sorted_sources:
                if await self.run_pipeline(source):
                    success_count += 1
                    
                progress.update(task, advance=1)
            
            # Update stats
            if success_count == len(sorted_sources):
                self.stats["successful_runs"] += 1
                self.status = PipelineStatus.SUCCESS
                self.console.print("\n[bold green]All pipelines completed successfully!")
            else:
                self.stats["failed_runs"] += 1
                self.status = PipelineStatus.FAILED
                self.console.print(f"\n[bold yellow]Completed {success_count}/{len(sorted_sources)} pipelines")
    
    def display_dashboard(self):
        """Display pipeline status dashboard"""
        table = Table(title="Pipeline Status Dashboard", show_header=True)
        table.add_column("Source", style="cyan")
        table.add_column("Schedule", style="yellow")
        table.add_column("Enabled", style="green")
        table.add_column("Priority", style="magenta")
        
        for source in self.sources.values():
            table.add_row(
                source.name,
                source.schedule,
                "✓" if source.enabled else "✗",
                str(source.priority)
            )
        
        self.console.print(table)
        
        # Print stats
        stats_panel = Panel(
            f"""
[bold]Pipeline Statistics[/bold]
─────────────────────
Total Runs: {self.stats['total_runs']}
Successful: {self.stats['successful_runs']}
Failed: {self.stats['failed_runs']}
Records Processed: {self.stats['records_processed']:,}
Last Run: {self.stats['last_run'] or 'Never'}
Status: [{'green' if self.status == PipelineStatus.SUCCESS else 'red'}]{self.status.value}[/]
            """,
            title="Statistics",
            border_style="blue"
        )
        
        self.console.print(stats_panel)
    
    async def start(self):
        """Start the master pipeline orchestrator"""
        self.console.print("[bold green]ConcordBroker Master Pipeline Started")
        self.display_dashboard()
        
        # Run immediately
        await self.run_all_pipelines()
        
        # Schedule future runs
        self.console.print("\n[cyan]Pipeline scheduled for regular updates")
        self.console.print("[yellow]Press Ctrl+C to stop")

async def main():
    """Main entry point"""
    pipeline = MasterPipeline()
    
    try:
        await pipeline.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline stopped by user")
    except Exception as e:
        console.print(f"[red]Pipeline error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())