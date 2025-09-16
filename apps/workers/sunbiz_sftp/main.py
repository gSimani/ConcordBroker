"""
Sunbiz SFTP Data Agent
Downloads and processes daily Florida business filings via SFTP
"""

import asyncio
import logging
import asyncssh
import aiofiles
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import csv
import gzip
import io

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

try:
    from .database import SunbizSFTPDB
    from .config import settings
except ImportError:
    from database import SunbizSFTPDB
    from config import settings

logger = logging.getLogger(__name__)
console = Console()

class SunbizSFTPAgent:
    """Agent for downloading Sunbiz data via SFTP"""
    
    SFTP_HOST = "sftp.floridados.gov"
    SFTP_USERNAME = "Public"
    SFTP_PASSWORD = "PubAccess1845!"
    
    # File types and their descriptions
    FILE_TYPES = {
        'c': 'Corporate Filings',        # yyyymmddc.txt
        'ce': 'Corporate Events',        # yyyymmddce.txt
        'ft': 'Federal Tax Lien Filings', # yyyymmddft.txt
        'fte': 'Federal Tax Lien Events', # yyyymmddfte.txt
        'ftd': 'Federal Tax Lien Debtors', # yyyymmddftd.txt
        'ftsp': 'Federal Tax Lien Secured Parties', # yyyymmddftsp.txt
        'fn': 'Fictitious Name Filings',  # yyyymmddfn.txt
        'fne': 'Fictitious Name Events',  # yyyymmddfne.txt
        'gp': 'General Partnership Filings', # yyyymmddgp.txt
        'gpe': 'General Partnership Events', # yyyymmddgpe.txt
        'mark': 'Trademark/Service Mark' # yyyymmddmark.txt
    }
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = settings.get_data_path()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db = SunbizSFTPDB()
        self.sftp_client = None
        self.ssh_client = None
        
    async def __aenter__(self):
        await self.db.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.sftp_client:
            self.sftp_client.exit()
        if self.ssh_client:
            self.ssh_client.close()
        await self.db.disconnect()
    
    async def connect_sftp(self):
        """Connect to Sunbiz SFTP server"""
        console.print(f"[yellow]Connecting to SFTP server: {self.SFTP_HOST}[/yellow]")
        
        try:
            self.ssh_client = await asyncssh.connect(
                self.SFTP_HOST,
                username=self.SFTP_USERNAME,
                password=self.SFTP_PASSWORD,
                known_hosts=None  # Accept any host key for public server
            )
            
            self.sftp_client = await self.ssh_client.start_sftp_client()
            console.print(f"[green]Connected to Sunbiz SFTP server[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]SFTP connection failed: {e}[/red]")
            raise
    
    async def list_available_files(self, date: datetime = None) -> List[str]:
        """List available files for a specific date"""
        if not self.sftp_client:
            await self.connect_sftp()
        
        if not date:
            date = datetime.now()
        
        date_str = date.strftime('%Y%m%d')
        available_files = []
        
        try:
            # List all files in the root directory
            files = await self.sftp_client.listdir('.')
            
            # Filter files for the specified date
            for filename in files:
                if filename.startswith(date_str):
                    available_files.append(filename)
                    
            console.print(f"[green]Found {len(available_files)} files for {date_str}[/green]")
            return available_files
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def download_file(self, filename: str) -> Optional[Path]:
        """Download a specific file from SFTP"""
        if not self.sftp_client:
            await self.connect_sftp()
        
        local_path = self.data_dir / filename
        
        try:
            console.print(f"[yellow]Downloading {filename}...[/yellow]")
            
            # Get file size for progress tracking
            attrs = await self.sftp_client.stat(filename)
            file_size = attrs.size
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                
                task = progress.add_task(f"Downloading {filename}", total=file_size)
                
                # Download with progress tracking
                async with self.sftp_client.open(filename, 'rb') as remote_file:
                    async with aiofiles.open(local_path, 'wb') as local_file:
                        chunk_size = 8192
                        downloaded = 0
                        
                        while True:
                            chunk = await remote_file.read(chunk_size)
                            if not chunk:
                                break
                            
                            await local_file.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, advance=len(chunk))
            
            console.print(f"[green]Downloaded {filename} ({file_size:,} bytes)[/green]")
            return local_path
            
        except Exception as e:
            console.print(f"[red]Download failed for {filename}: {e}[/red]")
            return None
    
    async def parse_corporate_filings(self, file_path: Path) -> Dict:
        """Parse corporate filings data (yyyymmddc.txt)"""
        stats = {
            'total_records': 0,
            'corporations': 0,
            'llcs': 0,
            'partnerships': 0,
            'foreign_entities': 0,
            'active_entities': 0,
            'inactive_entities': 0,
            'new_filings': 0,
            'amendments': 0,
            'dissolutions': 0,
            'top_registered_agents': {},
            'filings_by_county': {}
        }
        
        records = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Corporate filings are pipe-delimited
            reader = csv.DictReader(f, delimiter='|', fieldnames=[
                'doc_number', 'entity_name', 'entity_type', 'fei_number',
                'filing_date', 'status', 'principal_address', 'principal_city',
                'principal_state', 'principal_zip', 'mailing_address',
                'mailing_city', 'mailing_state', 'mailing_zip',
                'registered_agent_name', 'registered_agent_address',
                'registered_agent_city', 'registered_agent_state',
                'registered_agent_zip', 'officer1_name', 'officer1_title',
                'officer2_name', 'officer2_title', 'officer3_name', 'officer3_title'
            ])
            
            for row in reader:
                stats['total_records'] += 1
                
                # Clean data
                entity_type = row.get('entity_type', '').upper()
                status = row.get('status', '').upper()
                agent_name = row.get('registered_agent_name', '').upper()
                
                # Categorize entity types
                if 'CORP' in entity_type:
                    stats['corporations'] += 1
                elif 'LLC' in entity_type or 'L.L.C' in entity_type:
                    stats['llcs'] += 1
                elif 'PARTNERSHIP' in entity_type or 'LP' in entity_type:
                    stats['partnerships'] += 1
                
                if 'FOREIGN' in entity_type:
                    stats['foreign_entities'] += 1
                
                # Track status
                if status == 'ACTIVE':
                    stats['active_entities'] += 1
                else:
                    stats['inactive_entities'] += 1
                
                # Track registered agents
                if agent_name and len(agent_name) > 3:
                    if agent_name not in stats['top_registered_agents']:
                        stats['top_registered_agents'][agent_name] = 0
                    stats['top_registered_agents'][agent_name] += 1
                
                # Add to records for database
                records.append({
                    'doc_number': row.get('doc_number'),
                    'entity_name': row.get('entity_name'),
                    'entity_type': entity_type,
                    'fei_number': row.get('fei_number'),
                    'filing_date': row.get('filing_date'),
                    'status': status,
                    'registered_agent_name': agent_name,
                    'principal_city': row.get('principal_city'),
                    'principal_state': row.get('principal_state')
                })
        
        # Store in database
        if records:
            db_stats = await self.db.bulk_insert_corporate_filings(records)
            stats.update(db_stats)
        
        return stats
    
    async def parse_corporate_events(self, file_path: Path) -> Dict:
        """Parse corporate events data (yyyymmddce.txt)"""
        stats = {
            'total_events': 0,
            'amendments': 0,
            'annual_reports': 0,
            'dissolutions': 0,
            'mergers': 0,
            'name_changes': 0,
            'address_changes': 0,
            'agent_changes': 0,
            'events_by_type': {}
        }
        
        events = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter='|', fieldnames=[
                'doc_number', 'event_date', 'event_type', 'event_description',
                'filing_number', 'effective_date', 'document_code'
            ])
            
            for row in reader:
                stats['total_events'] += 1
                
                event_type = row.get('event_type', '').upper()
                
                # Categorize events
                if 'AMEND' in event_type:
                    stats['amendments'] += 1
                elif 'ANNUAL' in event_type:
                    stats['annual_reports'] += 1
                elif 'DISSOLV' in event_type or 'DISSOLUT' in event_type:
                    stats['dissolutions'] += 1
                elif 'MERGER' in event_type:
                    stats['mergers'] += 1
                elif 'NAME' in event_type:
                    stats['name_changes'] += 1
                elif 'ADDRESS' in event_type:
                    stats['address_changes'] += 1
                elif 'AGENT' in event_type:
                    stats['agent_changes'] += 1
                
                # Track all event types
                if event_type not in stats['events_by_type']:
                    stats['events_by_type'][event_type] = 0
                stats['events_by_type'][event_type] += 1
                
                events.append({
                    'doc_number': row.get('doc_number'),
                    'event_date': row.get('event_date'),
                    'event_type': event_type,
                    'event_description': row.get('event_description'),
                    'filing_number': row.get('filing_number')
                })
        
        # Store in database
        if events:
            db_stats = await self.db.bulk_insert_corporate_events(events)
            stats.update(db_stats)
        
        return stats
    
    async def run_daily_download(self, date: datetime = None, file_types: List[str] = None) -> Dict:
        """Main workflow to download and process daily Sunbiz data"""
        if not date:
            # Default to previous business day
            date = self.get_previous_business_day()
        
        if not file_types:
            # Default to corporate filings and events
            file_types = ['c', 'ce']
        
        console.print(f"[bold green]Starting Sunbiz SFTP Daily Download for {date.strftime('%Y-%m-%d')}[/bold green]")
        
        start_time = datetime.now()
        results = {
            'date': date.isoformat(),
            'started_at': start_time.isoformat(),
            'files_processed': [],
            'total_records': 0,
            'success': False,
            'errors': []
        }
        
        try:
            # Connect to SFTP
            await self.connect_sftp()
            
            # List available files
            available_files = await self.list_available_files(date)
            
            if not available_files:
                console.print(f"[yellow]No files available for {date.strftime('%Y-%m-%d')}[/yellow]")
                results['errors'].append('No files available')
                return results
            
            # Process each file type
            for file_type in file_types:
                date_str = date.strftime('%Y%m%d')
                filename = f"{date_str}{file_type}.txt"
                
                if filename in available_files:
                    console.print(f"\n[cyan]Processing {self.FILE_TYPES.get(file_type, file_type)}[/cyan]")
                    
                    # Download file
                    local_path = await self.download_file(filename)
                    
                    if local_path:
                        # Parse based on file type
                        if file_type == 'c':
                            stats = await self.parse_corporate_filings(local_path)
                        elif file_type == 'ce':
                            stats = await self.parse_corporate_events(local_path)
                        else:
                            stats = {'message': f'Parser not implemented for {file_type}'}
                        
                        results['files_processed'].append({
                            'filename': filename,
                            'file_type': self.FILE_TYPES.get(file_type, file_type),
                            'stats': stats
                        })
                        
                        results['total_records'] += stats.get('total_records', 0)
                    
            results['success'] = True
            results['finished_at'] = datetime.now().isoformat()
            results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            # Display summary
            self.display_summary(results)
            
            # Log to database
            await self.db.log_job(results)
            
        except Exception as e:
            results['errors'].append(str(e))
            results['success'] = False
            logger.error(f"Daily download failed: {e}")
            console.print(f"[red]Error: {e}[/red]")
        
        return results
    
    def get_previous_business_day(self) -> datetime:
        """Get the previous business day (excluding weekends)"""
        date = datetime.now() - timedelta(days=1)
        
        # If Monday, go back to Friday
        if date.weekday() == 0:  # Monday
            date = date - timedelta(days=2)
        # If Sunday, go back to Friday
        elif date.weekday() == 6:  # Sunday
            date = date - timedelta(days=2)
        
        return date
    
    def display_summary(self, results: Dict):
        """Display download summary"""
        console.print("\n[bold cyan]Sunbiz SFTP Download Summary:[/bold cyan]")
        console.print(f"Date: {results['date'][:10]}")
        console.print(f"Files Processed: {len(results['files_processed'])}")
        console.print(f"Total Records: {results['total_records']:,}")
        console.print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        
        # Display details for each file
        for file_info in results['files_processed']:
            console.print(f"\n[bold]{file_info['file_type']}:[/bold]")
            stats = file_info['stats']
            
            if 'corporations' in stats:
                # Corporate filings stats
                console.print(f"  Corporations: {stats.get('corporations', 0):,}")
                console.print(f"  LLCs: {stats.get('llcs', 0):,}")
                console.print(f"  Active Entities: {stats.get('active_entities', 0):,}")
                
                # Top registered agents
                if stats.get('top_registered_agents'):
                    console.print(f"\n  [bold]Top Registered Agents:[/bold]")
                    top_agents = sorted(stats['top_registered_agents'].items(), 
                                      key=lambda x: x[1], reverse=True)[:5]
                    for agent, count in top_agents:
                        console.print(f"    {agent}: {count:,}")
            
            elif 'total_events' in stats:
                # Corporate events stats
                console.print(f"  Total Events: {stats.get('total_events', 0):,}")
                console.print(f"  Amendments: {stats.get('amendments', 0):,}")
                console.print(f"  Annual Reports: {stats.get('annual_reports', 0):,}")
                console.print(f"  Dissolutions: {stats.get('dissolutions', 0):,}")
    
    async def search_entities_by_name(self, search_term: str) -> List[Dict]:
        """Search for entities by name in downloaded data"""
        return await self.db.search_by_entity_name(search_term)
    
    async def get_registered_agent_portfolio(self, agent_name: str) -> List[Dict]:
        """Get all entities managed by a registered agent"""
        return await self.db.get_entities_by_agent(agent_name)
    
    async def get_daily_analytics(self, date: datetime = None) -> Dict:
        """Get analytics for a specific day's filings"""
        if not date:
            date = self.get_previous_business_day()
        
        return await self.db.get_daily_summary(date)

async def main():
    """Main function"""
    import click
    
    @click.command()
    @click.option('--date', type=click.DateTime(['%Y-%m-%d']), 
                  help='Date to download (default: previous business day)')
    @click.option('--file-types', multiple=True, 
                  help='File types to download (c, ce, fn, etc.)')
    @click.option('--search', help='Search for entities by name')
    @click.option('--agent', help='Get portfolio for registered agent')
    @click.option('--analytics', is_flag=True, help='Get daily analytics')
    async def run(date, file_types, search, agent, analytics):
        """Sunbiz SFTP Data Downloader"""
        
        async with SunbizSFTPAgent() as agent_obj:
            if search:
                # Search mode
                results = await agent_obj.search_entities_by_name(search)
                console.print(f"[bold]Found {len(results)} entities matching '{search}':[/bold]")
                for entity in results[:10]:
                    console.print(f"  {entity['doc_number']}: {entity['entity_name']} ({entity['status']})")
            
            elif agent:
                # Agent portfolio mode
                results = await agent_obj.get_registered_agent_portfolio(agent)
                console.print(f"[bold]Registered Agent Portfolio for {agent}:[/bold]")
                console.print(f"Total Entities: {len(results)}")
                
            elif analytics:
                # Analytics mode
                stats = await agent_obj.get_daily_analytics(date)
                console.print("[bold]Daily Analytics:[/bold]")
                console.print(f"  New Corporations: {stats.get('new_corporations', 0):,}")
                console.print(f"  New LLCs: {stats.get('new_llcs', 0):,}")
                console.print(f"  Dissolutions: {stats.get('dissolutions', 0):,}")
                
            else:
                # Download mode
                await agent_obj.run_daily_download(date, list(file_types) if file_types else None)
    
    await run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())