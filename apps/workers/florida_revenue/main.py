"""
Florida Revenue Data Portal Agent
Downloads and processes Tangible Personal Property (TPP) data from floridarevenue.com
"""

import asyncio
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import csv
import aiohttp
import aiofiles
from urllib.parse import urljoin

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

try:
    from .database import FloridaRevenueDB
    from .config import settings
except ImportError:
    # Handle direct execution
    from database import FloridaRevenueDB
    from config import settings

logger = logging.getLogger(__name__)
console = Console()

class FloridaRevenueAgent:
    """Agent for Florida Revenue data portal"""
    
    BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/"
    TPP_BASE_PATH = "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/"
    
    # Broward County code
    BROWARD_COUNTY_CODE = "16"
    
    # Available data types
    DATA_TYPES = {
        'tpp': 'Tangible Personal Property',
        'real': 'Real Estate',
        'mobile': 'Mobile Homes'
    }
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = settings.get_data_path()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.db = FloridaRevenueDB()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        await self.db.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        await self.db.disconnect()
    
    def get_tpp_url(self, year: str, file_type: str = "P") -> str:
        """Generate URL for TPP data file"""
        filename = f"Broward%20{self.BROWARD_COUNTY_CODE}%20Preliminary%20TPP%20{year}.zip"
        return urljoin(
            self.BASE_URL,
            f"{self.TPP_BASE_PATH}{year}{file_type}/{filename}"
        )
    
    async def download_tpp_data(self, year: str = "2025") -> Path:
        """Download TPP data for specified year"""
        url = self.get_tpp_url(year)
        filename = f"broward_tpp_{year}.zip"
        filepath = self.data_dir / filename
        
        console.print(f"[yellow]Downloading {url}[/yellow]")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    ) as progress:
                        
                        task = progress.add_task(
                            f"Downloading {filename}", 
                            total=total_size
                        )
                        
                        async with aiofiles.open(filepath, 'wb') as f:
                            downloaded = 0
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, advance=len(chunk))
                    
                    console.print(f"[green]Downloaded {filepath}[/green]")
                    return filepath
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except Exception as e:
            console.print(f"[red]Download failed: {e}[/red]")
            raise
    
    async def extract_and_parse(self, zip_path: Path, load_to_db: bool = True) -> Dict:
        """Extract ZIP and parse CSV data"""
        console.print("[yellow]Extracting and parsing data...[/yellow]")
        
        stats = {
            'total_records': 0,
            'records_processed': 0,
            'records_created': 0,
            'records_updated': 0,
            'data_fields': [],
            'sample_records': [],
            'owner_analysis': {},
            'naics_codes': {},
            'value_analysis': {}
        }
        
        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            csv_files = [f for f in zip_file.namelist() if f.endswith('.csv')]
            
            if not csv_files:
                raise Exception("No CSV files found in ZIP")
            
            csv_filename = csv_files[0]
            extracted_path = self.data_dir / csv_filename
            
            with zip_file.open(csv_filename) as source, open(extracted_path, 'wb') as target:
                target.write(source.read())
        
        # Create tables if needed
        if load_to_db:
            await self.db.create_tpp_tables()
        
        # Parse CSV in batches
        batch_size = settings.BATCH_SIZE
        batch = []
        owner_counts = {}
        naics_counts = {}
        values = []
        
        with open(extracted_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            stats['data_fields'] = reader.fieldnames
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                
                # Count total lines first
                f.seek(0)
                total_lines = sum(1 for _ in f) - 1  # Subtract header
                f.seek(0)
                reader = csv.DictReader(f)  # Recreate reader
                
                task = progress.add_task(
                    "Processing TPP records", 
                    total=total_lines
                )
                
                for i, row in enumerate(reader):
                    if i < 10:  # Store sample records
                        stats['sample_records'].append(row)
                    
                    # Add to batch
                    batch.append(row)
                    
                    # Count owners for analysis
                    owner = row.get('OWN_NAM', '').strip('"')
                    if owner:
                        owner_counts[owner] = owner_counts.get(owner, 0) + 1
                    
                    # Count NAICS codes
                    naics = row.get('NAICS_CD', '').strip()
                    if naics:
                        naics_counts[naics] = naics_counts.get(naics, 0) + 1
                    
                    # Collect values
                    jv_total = row.get('JV_TOTAL', '').strip()
                    if jv_total and jv_total.replace('.', '').replace('-', '').isdigit():
                        values.append(float(jv_total))
                    
                    # Process batch when full
                    if len(batch) >= batch_size:
                        if load_to_db:
                            db_stats = await self.db.bulk_insert_tpp_records(batch)
                            stats['records_created'] += db_stats['created']
                            stats['records_updated'] += db_stats['updated']
                        
                        stats['records_processed'] += len(batch)
                        batch = []
                    
                    stats['total_records'] = i + 1
                    progress.update(task, advance=1)
                
                # Process remaining batch
                if batch and load_to_db:
                    db_stats = await self.db.bulk_insert_tpp_records(batch)
                    stats['records_created'] += db_stats['created']
                    stats['records_updated'] += db_stats['updated']
                    stats['records_processed'] += len(batch)
        
        # Analyze data
        stats['owner_analysis'] = dict(sorted(owner_counts.items(), key=lambda x: x[1], reverse=True)[:20])
        stats['naics_codes'] = dict(sorted(naics_counts.items(), key=lambda x: x[1], reverse=True)[:20])
        
        if values:
            stats['value_analysis'] = {
                'total_value': sum(values),
                'average_value': sum(values) / len(values),
                'max_value': max(values),
                'min_value': min(values),
                'records_with_value': len(values)
            }
        
        return stats
    
    async def run_data_collection(self, year: str = "2025") -> Dict:
        """Main data collection workflow"""
        console.print(f"[bold green]Starting Florida Revenue TPP Data Collection for {year}[/bold green]")
        
        start_time = datetime.now()
        results = {
            'started_at': start_time.isoformat(),
            'year': year,
            'success': False,
            'error': None
        }
        
        try:
            # Download data
            zip_path = await self.download_tpp_data(year)
            
            # Extract and parse
            analysis = await self.extract_and_parse(zip_path)
            results.update(analysis)
            
            results['success'] = True
            results['finished_at'] = datetime.now().isoformat()
            results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            # Log job to database
            await self.db.log_job({
                'type': 'florida_revenue_tpp',
                'started_at': results['started_at'],
                'finished_at': results['finished_at'],
                'success': results['success'],
                'records_processed': results.get('records_processed', 0),
                'records_created': results.get('records_created', 0),
                'records_updated': results.get('records_updated', 0),
                'year': year,
                'data_fields': results.get('data_fields', []),
                'value_analysis': results.get('value_analysis', {})
            })
            
            # Display summary
            self.display_summary(results)
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Data collection failed: {e}")
            console.print(f"[red]Error: {e}[/red]")
            
            # Still log the failed job
            await self.db.log_job({
                'type': 'florida_revenue_tpp',
                'started_at': results['started_at'],
                'finished_at': datetime.now().isoformat(),
                'success': False,
                'errors': [str(e)],
                'year': year
            })
        
        return results
    
    def display_summary(self, results: Dict):
        """Display collection summary"""
        console.print("\n[bold cyan]Collection Summary:[/bold cyan]")
        console.print(f"Total Records: {results.get('total_records', 0):,}")
        console.print(f"Records Processed: {results.get('records_processed', 0):,}")
        console.print(f"Records Created: {results.get('records_created', 0):,}")
        console.print(f"Records Updated: {results.get('records_updated', 0):,}")
        console.print(f"Data Fields: {len(results.get('data_fields', []))}")
        console.print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        
        if 'value_analysis' in results:
            va = results['value_analysis']
            console.print(f"Total Property Value: ${va['total_value']:,.2f}")
            console.print(f"Average Value: ${va['average_value']:,.2f}")
            console.print(f"Max Value: ${va['max_value']:,.2f}")
        
        console.print(f"\n[bold]Top Property Owners:[/bold]")
        for owner, count in list(results.get('owner_analysis', {}).items())[:10]:
            console.print(f"  {owner}: {count:,} properties")
        
        console.print(f"\n[bold]Top NAICS Codes:[/bold]")  
        for naics, count in list(results.get('naics_codes', {}).items())[:10]:
            console.print(f"  {naics}: {count:,} records")
    
    async def get_database_analytics(self) -> Dict:
        """Get analytics from database"""
        console.print("[yellow]Getting database analytics...[/yellow]")
        
        try:
            top_owners = await self.db.get_top_owners(20)
            naics_analysis = await self.db.get_naics_analysis(20)
            
            return {
                'top_owners': top_owners,
                'naics_analysis': naics_analysis
            }
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}

async def main_async(year: str):
    """Async main function"""
    async with FloridaRevenueAgent() as agent:
        return await agent.run_data_collection(year)

@click.command()
@click.option('--year', default='2025', help='Data year to collect')
@click.option('--analyze', is_flag=True, help='Analyze existing data without downloading')
@click.option('--analytics', is_flag=True, help='Get analytics from database')
def main(year: str, analyze: bool, analytics: bool):
    """Florida Revenue TPP Data Collector"""
    
    console.print("[bold cyan]Florida Revenue Data Collector[/bold cyan]")
    
    async def run_async():
        """Run the appropriate async function"""
        async with FloridaRevenueAgent() as agent:
            if analytics:
                return await agent.get_database_analytics()
            else:
                return await agent.run_data_collection(year)
    
    # Run async function
    result = asyncio.run(run_async())
    
    if analytics:
        # Display analytics
        if result.get('top_owners'):
            console.print(f"\n[bold]Top Property Owners from Database:[/bold]")
            for owner in result['top_owners'][:10]:
                console.print(f"  {owner['owner_name']}: {owner['property_count']:,} properties, ${owner['total_value']:,.0f} total value")
        
        if result.get('naics_analysis'):
            console.print(f"\n[bold]NAICS Analysis from Database:[/bold]")
            for naics in result['naics_analysis'][:10]:
                console.print(f"  {naics['naics_code']}: {naics['record_count']:,} records")
    
    elif result.get('success'):
        console.print("[bold green]✓ Collection completed successfully![/bold green]")
    else:
        console.print(f"[bold red]✗ Collection failed: {result.get('error')}[/bold red]")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    main()