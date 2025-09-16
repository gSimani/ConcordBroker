"""
Supabase Data Pipeline Orchestrator
Continuously monitors Florida Revenue data sources for updates and syncs to Supabase
"""

import asyncio
import logging
import hashlib
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import schedule
import time

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.logging import RichHandler

# Import all agents
from tpp.main import TPPAgent
from nav_assessments.main import NAVAgent
from sdf_sales.main import SDFSalesAgent
from sunbiz.main import SunbizAgent
from bcpa.main import BCPASearchAgent
from official_records.main import OfficialRecordsAgent
from dor_processor.main import DORProcessor

from supabase_config import supabase_config, SupabaseUpdateMonitor

logger = logging.getLogger(__name__)
console = Console()

class SupabaseOrchestrator:
    """Master orchestrator for all data pipeline agents with Supabase"""
    
    def __init__(self):
        self.agents = {
            'tpp': TPPAgent,
            'nav': NAVAgent,
            'sdf_sales': SDFSalesAgent,
            'sunbiz': SunbizAgent,
            'bcpa': BCPASearchAgent,
            'official_records': OfficialRecordsAgent,
            'dor_processor': DORProcessor
        }
        self.active_agents = {}
        self.monitor = None
        self.session = None
        self.running = False
        self.update_check_interval = supabase_config.UPDATE_CHECK_INTERVAL
        
    async def initialize(self):
        """Initialize orchestrator and database connections"""
        console.print("[bold green]Initializing Supabase Data Pipeline Orchestrator[/bold green]")
        
        # Initialize database pool
        pool = await supabase_config.get_db_pool()
        self.monitor = SupabaseUpdateMonitor(pool)
        await self.monitor.initialize_tracking_tables()
        
        # Initialize HTTP session for checking updates
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'ConcordBroker/1.0'}
        )
        
        # Initialize active agents based on configuration
        for agent_name, agent_class in self.agents.items():
            if self.is_agent_enabled(agent_name):
                self.active_agents[agent_name] = {
                    'class': agent_class,
                    'instance': None,
                    'schedule': supabase_config.AGENT_SCHEDULES.get(agent_name, {})
                }
                console.print(f"[green]✓[/green] Agent enabled: {agent_name}")
        
        self.running = True
        console.print("[bold green]Orchestrator initialized successfully![/bold green]")
    
    def is_agent_enabled(self, agent_name: str) -> bool:
        """Check if agent is enabled in configuration"""
        schedule = supabase_config.AGENT_SCHEDULES.get(agent_name, {})
        return schedule.get('frequency') is not None
    
    async def check_for_data_updates(self, agent_name: str) -> Dict[str, Any]:
        """Check if data source has been updated"""
        updates = {}
        
        if agent_name == 'tpp':
            # Check TPP data updates
            for county, config in supabase_config.COUNTIES.items():
                if config['active']:
                    url = f"{supabase_config.FLORIDA_REVENUE_BASE_URL}TPP/{config['code']}/2025"
                    updates[f"tpp_{county}"] = await self.check_url_update(url)
                    
        elif agent_name == 'nav':
            # Check NAV data updates
            for county, config in supabase_config.COUNTIES.items():
                if config['active']:
                    url = f"{supabase_config.FLORIDA_REVENUE_BASE_URL}NAV/{config['code']}/2025"
                    updates[f"nav_{county}"] = await self.check_url_update(url)
                    
        elif agent_name == 'sdf_sales':
            # Check SDF data updates
            for county, config in supabase_config.COUNTIES.items():
                if config['active']:
                    url = f"{supabase_config.FLORIDA_REVENUE_BASE_URL}SDF/{config['code']}/2025P"
                    updates[f"sdf_{county}"] = await self.check_url_update(url)
                    
        elif agent_name == 'sunbiz':
            # Sunbiz updates daily
            updates['sunbiz'] = {'needs_update': True, 'reason': 'Daily refresh'}
            
        elif agent_name == 'bcpa':
            # BCPA updates daily
            updates['bcpa'] = {'needs_update': True, 'reason': 'Daily property updates'}
            
        elif agent_name == 'official_records':
            # Official records update continuously
            updates['official_records'] = {'needs_update': True, 'reason': 'Continuous updates'}
            
        elif agent_name == 'dor_processor':
            # DOR processor runs monthly
            updates['dor'] = {'needs_update': self.is_monthly_update_due(agent_name)}
        
        return updates
    
    async def check_url_update(self, url: str) -> Dict[str, Any]:
        """Check if a URL has been updated since last check"""
        try:
            async with self.session.head(url) as response:
                if response.status == 200:
                    last_modified = response.headers.get('Last-Modified')
                    content_length = response.headers.get('Content-Length')
                    etag = response.headers.get('ETag')
                    
                    # Check against stored values
                    needs_update = await self.monitor.check_for_update(
                        agent_name='url_check',
                        source_url=url,
                        current_hash=etag,
                        current_size=int(content_length) if content_length else None
                    )
                    
                    return {
                        'needs_update': needs_update,
                        'last_modified': last_modified,
                        'size': content_length,
                        'etag': etag
                    }
                else:
                    return {'needs_update': False, 'error': f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Error checking URL {url}: {e}")
            return {'needs_update': False, 'error': str(e)}
    
    def is_monthly_update_due(self, agent_name: str) -> bool:
        """Check if monthly update is due"""
        schedule = supabase_config.AGENT_SCHEDULES.get(agent_name, {})
        if schedule.get('frequency') == 'monthly':
            day = schedule.get('day', 1)
            return datetime.now().day == day
        return False
    
    async def run_agent(self, agent_name: str, force: bool = False) -> Dict[str, Any]:
        """Run a specific agent"""
        console.print(f"\n[yellow]Running agent: {agent_name}[/yellow]")
        start_time = datetime.now()
        
        try:
            # Check for updates unless forced
            if not force:
                updates = await self.check_for_data_updates(agent_name)
                has_updates = any(u.get('needs_update', False) for u in updates.values())
                
                if not has_updates:
                    console.print(f"[dim]No updates found for {agent_name}, skipping...[/dim]")
                    return {'status': 'skipped', 'reason': 'No updates'}
            
            # Get agent configuration
            agent_config = self.active_agents.get(agent_name)
            if not agent_config:
                return {'status': 'error', 'error': 'Agent not configured'}
            
            # Initialize agent
            agent_class = agent_config['class']
            
            # Run agent based on type
            if agent_name == 'tpp':
                async with agent_class() as agent:
                    results = await agent.run_tpp_collection()
                    
            elif agent_name == 'nav':
                async with agent_class() as agent:
                    results = await agent.run_nav_collection()
                    
            elif agent_name == 'sdf_sales':
                async with agent_class() as agent:
                    results = await agent.run_sdf_collection()
                    
            elif agent_name == 'sunbiz':
                # Sunbiz has different interface
                agent = agent_class()
                results = await agent.search_bulk_owners(['INVITATION HOMES'])
                
            elif agent_name == 'bcpa':
                async with agent_class() as agent:
                    results = await agent.search_by_owner('INVITATION HOMES')
                    
            elif agent_name == 'official_records':
                agent = agent_class()
                results = await agent.search_records(
                    instrument_type='DEED',
                    date_from=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                )
                
            elif agent_name == 'dor_processor':
                agent = agent_class()
                results = await agent.process_all_counties()
            
            else:
                return {'status': 'error', 'error': f'Unknown agent: {agent_name}'}
            
            # Calculate runtime
            runtime = (datetime.now() - start_time).total_seconds()
            
            # Update agent status
            await self.monitor.update_agent_status(agent_name, {
                'last_run': datetime.now(),
                'average_runtime_seconds': runtime,
                'last_error': None
            })
            
            console.print(f"[green]✓[/green] {agent_name} completed in {runtime:.2f}s")
            
            return {
                'status': 'success',
                'runtime': runtime,
                'results': results
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent {agent_name} failed: {error_msg}")
            
            # Update agent status with error
            await self.monitor.update_agent_status(agent_name, {
                'last_run': datetime.now(),
                'last_error': error_msg
            })
            
            return {
                'status': 'error',
                'error': error_msg,
                'runtime': (datetime.now() - start_time).total_seconds()
            }
    
    async def run_scheduled_agents(self):
        """Run agents based on their schedules"""
        while self.running:
            try:
                # Get current time
                now = datetime.now()
                current_hour = now.strftime('%H:%M')
                
                # Check each agent's schedule
                for agent_name, config in self.active_agents.items():
                    schedule = config['schedule']
                    
                    # Check if it's time to run
                    should_run = False
                    
                    if schedule.get('frequency') == 'daily':
                        if schedule.get('time') == current_hour:
                            should_run = True
                            
                    elif schedule.get('frequency') == 'weekly':
                        if (now.strftime('%A').lower() == schedule.get('day', '').lower() 
                            and schedule.get('time') == current_hour):
                            should_run = True
                            
                    elif schedule.get('frequency') == 'monthly':
                        if (now.day == schedule.get('day', 1) 
                            and schedule.get('time') == current_hour):
                            should_run = True
                    
                    if should_run:
                        console.print(f"\n[bold blue]Scheduled run for {agent_name}[/bold blue]")
                        await self.run_agent(agent_name)
                
                # Wait before next check (1 minute)
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def continuous_monitoring(self):
        """Continuously monitor for updates"""
        console.print("[bold cyan]Starting continuous monitoring...[/bold cyan]")
        
        while self.running:
            try:
                # Check for updates every interval
                console.print(f"\n[dim]Checking for updates... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
                
                for agent_name in self.active_agents:
                    updates = await self.check_for_data_updates(agent_name)
                    
                    for source, update_info in updates.items():
                        if update_info.get('needs_update'):
                            console.print(f"[yellow]⚠[/yellow] Update detected for {source}")
                            
                            # Run agent immediately if update detected
                            if supabase_config.ENABLE_AUTO_UPDATES:
                                await self.run_agent(agent_name, force=True)
                
                # Wait before next check
                await asyncio.sleep(self.update_check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def display_status(self):
        """Display real-time status dashboard"""
        table = Table(title="Florida Data Pipeline Status", show_header=True)
        table.add_column("Agent", style="cyan", width=20)
        table.add_column("Status", width=15)
        table.add_column("Last Run", width=20)
        table.add_column("Next Run", width=20)
        table.add_column("Records", width=15)
        table.add_column("Updates", width=10)
        
        # Get status for each agent
        async with await supabase_config.get_db_pool() as pool:
            async with pool.acquire() as conn:
                statuses = await conn.fetch("""
                    SELECT * FROM fl_agent_status
                    ORDER BY agent_name
                """)
                
                for status in statuses:
                    status_color = "green" if status['is_active'] else "red"
                    status_text = "Active" if status['is_active'] else "Inactive"
                    
                    table.add_row(
                        status['agent_name'],
                        f"[{status_color}]{status_text}[/{status_color}]",
                        status['last_run'].strftime('%Y-%m-%d %H:%M') if status['last_run'] else "Never",
                        status['next_run'].strftime('%Y-%m-%d %H:%M') if status['next_run'] else "N/A",
                        str(status['total_runs']),
                        f"{status['successful_runs']}/{status['total_runs']}"
                    )
        
        console.print(table)
    
    async def run(self):
        """Main orchestrator run loop"""
        await self.initialize()
        
        try:
            # Create tasks for parallel execution
            tasks = [
                asyncio.create_task(self.run_scheduled_agents()),
                asyncio.create_task(self.continuous_monitoring())
            ]
            
            # Display status periodically
            while self.running:
                await self.display_status()
                await asyncio.sleep(300)  # Update display every 5 minutes
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down orchestrator...[/yellow]")
            self.running = False
            
        finally:
            if self.session:
                await self.session.close()
            
            console.print("[green]Orchestrator shutdown complete[/green]")

async def main():
    """Main entry point"""
    orchestrator = SupabaseOrchestrator()
    await orchestrator.run()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    
    # Print startup banner
    console.print(Panel.fit(
        "[bold cyan]ConcordBroker Supabase Data Pipeline[/bold cyan]\n"
        "[dim]Continuous monitoring and synchronization of Florida Revenue data[/dim]",
        border_style="cyan"
    ))
    
    # Run orchestrator
    asyncio.run(main())