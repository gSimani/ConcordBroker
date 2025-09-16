"""
NAV (Non Ad Valorem) Assessments Data Portal Agent
Downloads and processes NAV assessment data from Florida Revenue portal
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import re
import aiohttp
import aiofiles
from urllib.parse import urljoin

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

try:
    from .database import NAVAssessmentsDB
    from .config import settings
except ImportError:
    from database import NAVAssessmentsDB
    from config import settings

logger = logging.getLogger(__name__)
console = Console()

class NAVAssessmentsAgent:
    """Agent for NAV (Non Ad Valorem) Assessments data portal"""
    
    BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/"
    NAV_BASE_PATH = "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/"
    
    # Priority counties for processing
    PRIORITY_COUNTIES = {
        "16": "Broward",
        "25": "Miami-Dade", 
        "50": "Palm Beach"
    }
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = settings.get_data_path()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.db = NAVAssessmentsDB()
    
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
    
    def get_nav_url(self, table_type: str, year: str) -> str:
        """Generate URL for NAV data files"""
        # URL structure: /NAV/2024/NAV D/ or /NAV/2024/NAV N/
        return urljoin(
            self.BASE_URL,
            f"{self.NAV_BASE_PATH}{year}/NAV%20{table_type.upper()}/"
        )
    
    async def discover_nav_files(self, table_type: str, year: str = "2024") -> List[str]:
        """Discover available NAV files for a given year and table type"""
        console.print(f"[yellow]Discovering NAV {table_type.upper()} files for {year}...[/yellow]")
        
        # For now, generate expected filenames based on priority counties
        # In production, this would parse the directory listing
        files = []
        
        for county_code, county_name in self.PRIORITY_COUNTIES.items():
            filename = settings.generate_nav_filename(table_type, county_code, year)
            files.append({
                'filename': filename,
                'county_code': county_code,
                'county_name': county_name,
                'url': self.get_nav_url(table_type, year) + filename
            })
        
        console.print(f"[green]Discovered {len(files)} potential files[/green]")
        return files
    
    async def download_nav_file(self, file_info: Dict) -> Optional[Path]:
        """Download a single NAV file"""
        local_path = self.data_dir / file_info['filename']
        
        if local_path.exists():
            console.print(f"[dim]File already exists: {file_info['filename']}[/dim]")
            return local_path
        
        try:
            console.print(f"[yellow]Downloading {file_info['filename']}...[/yellow]")
            
            async with self.session.get(file_info['url']) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    
                    async with aiofiles.open(local_path, 'wb') as f:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                    
                    console.print(f"[green]Downloaded {file_info['filename']} ({downloaded:,} bytes)[/green]")
                    return local_path
                else:
                    console.print(f"[red]HTTP {response.status} for {file_info['filename']}[/red]")
                    return None
                    
        except Exception as e:
            console.print(f"[red]Download failed for {file_info['filename']}: {e}[/red]")
            return None
    
    async def parse_nav_file(self, file_path: Path, table_type: str, county_code: str, year: str) -> Dict:
        """Parse a NAV file and extract records"""
        console.print(f"[yellow]Parsing {file_path.name}...[/yellow]")
        
        stats = {
            'filename': file_path.name,
            'table_type': table_type.upper(),
            'county_code': county_code,
            'county_name': settings.get_county_name(county_code),
            'year': year,
            'total_records': 0,
            'records_processed': 0,
            'records_created': 0,
            'records_updated': 0,
            'sample_records': [],
            'errors': []
        }
        
        if not file_path.exists():
            stats['errors'].append(f"File not found: {file_path}")
            return stats
        
        try:
            # Create tables if needed
            await self.db.create_nav_tables()
            
            records = []
            batch_size = settings.BATCH_SIZE
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                
                # Count total lines first
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines = sum(1 for _ in f)
                
                task = progress.add_task(
                    f"Processing {file_path.name}",
                    total=total_lines
                )
                
                # Process file
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    
                    for line_num, row in enumerate(reader, 1):
                        if line_num <= 5:  # Store sample records
                            stats['sample_records'].append(row)
                        
                        records.append(row)
                        stats['total_records'] += 1
                        
                        # Process batch when full
                        if len(records) >= batch_size:
                            batch_stats = await self._process_batch(records, table_type, year)
                            stats['records_created'] += batch_stats.get('created', 0)
                            stats['records_updated'] += batch_stats.get('updated', 0)
                            stats['records_processed'] += len(records)
                            records = []
                        
                        progress.update(task, advance=1)
                
                # Process remaining records
                if records:
                    batch_stats = await self._process_batch(records, table_type, year)
                    stats['records_created'] += batch_stats.get('created', 0)
                    stats['records_updated'] += batch_stats.get('updated', 0)
                    stats['records_processed'] += len(records)
        
        except Exception as e:
            error_msg = f"Error parsing {file_path.name}: {e}"
            stats['errors'].append(error_msg)
            logger.error(error_msg)
        
        return stats
    
    async def _process_batch(self, records: List, table_type: str, year: str) -> Dict:
        """Process a batch of records"""
        if table_type.upper() == 'N':
            return await self.db.bulk_insert_nav_parcels(records, year)
        elif table_type.upper() == 'D':
            return await self.db.bulk_insert_nav_details(records, year)
        else:
            return {'created': 0, 'updated': 0, 'failed': len(records)}
    
    async def run_nav_collection(self, table_type: str = "N", year: str = "2024", 
                                counties: List[str] = None) -> Dict:
        """Main NAV data collection workflow"""
        console.print(f"[bold green]Starting NAV {table_type.upper()} Data Collection for {year}[/bold green]")
        
        start_time = datetime.now()
        results = {
            'started_at': start_time.isoformat(),
            'table_type': table_type.upper(),
            'year': year,
            'success': False,
            'files_processed': 0,
            'total_records': 0,
            'records_created': 0,
            'records_updated': 0,
            'counties': counties or list(self.PRIORITY_COUNTIES.keys()),
            'errors': [],
            'file_results': []
        }
        
        try:
            # Discover available files
            available_files = await self.discover_nav_files(table_type, year)
            
            # Filter by requested counties if specified
            if counties:
                available_files = [f for f in available_files if f['county_code'] in counties]
            
            console.print(f"[cyan]Processing {len(available_files)} files...[/cyan]")
            
            for file_info in available_files:
                try:
                    # Download file
                    local_path = await self.download_nav_file(file_info)
                    
                    if local_path:
                        # Parse file
                        parse_stats = await self.parse_nav_file(
                            local_path, 
                            table_type, 
                            file_info['county_code'], 
                            year
                        )
                        
                        results['file_results'].append(parse_stats)
                        results['files_processed'] += 1
                        results['total_records'] += parse_stats.get('total_records', 0)
                        results['records_created'] += parse_stats.get('records_created', 0)
                        results['records_updated'] += parse_stats.get('records_updated', 0)
                        
                        if parse_stats.get('errors'):
                            results['errors'].extend(parse_stats['errors'])
                    
                except Exception as e:
                    error_msg = f"Error processing {file_info['filename']}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            results['success'] = results['files_processed'] > 0
            results['finished_at'] = datetime.now().isoformat()
            results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            # Log job to database
            await self.db.log_job({
                'type': 'nav_assessments',
                'table_type': table_type.upper(),
                'county_number': ','.join(results['counties']),
                'tax_year': year,
                'started_at': results['started_at'],
                'finished_at': results['finished_at'],
                'success': results['success'],
                'records_processed': results['total_records'],
                'records_created': results['records_created'],
                'records_updated': results['records_updated'],
                'errors': results['errors'],
                'counties': results['counties'],
                'files_processed': results['files_processed']
            })
            
            # Display summary
            self.display_summary(results)
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"NAV collection failed: {e}")
            console.print(f"[red]Error: {e}[/red]")
        
        return results
    
    def display_summary(self, results: Dict):
        """Display collection summary"""
        console.print(f"\n[bold cyan]NAV {results.get('table_type', '')} Collection Summary:[/bold cyan]")
        console.print(f"Files Processed: {results.get('files_processed', 0)}")
        console.print(f"Total Records: {results.get('total_records', 0):,}")
        console.print(f"Records Created: {results.get('records_created', 0):,}")
        console.print(f"Records Updated: {results.get('records_updated', 0):,}")
        console.print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        
        if results.get('errors'):
            console.print(f"[red]Errors: {len(results['errors'])}[/red]")
            for error in results['errors'][:5]:  # Show first 5 errors
                console.print(f"  [red]- {error}[/red]")
        
        if results.get('file_results'):
            console.print(f"\n[bold]File Processing Results:[/bold]")
            for file_result in results['file_results']:
                console.print(f"  {file_result['filename']}: {file_result.get('total_records', 0):,} records")
    
    async def get_database_analytics(self, county_number: str = None, tax_year: str = None) -> Dict:
        """Get analytics from database"""
        console.print("[yellow]Getting NAV database analytics...[/yellow]")
        
        try:
            summary = await self.db.get_assessment_summary(county_number, tax_year)
            top_parcels = await self.db.get_top_assessed_parcels(county_number, tax_year, 10)
            function_analysis = await self.db.get_function_analysis(county_number, tax_year)
            
            return {
                'summary': summary,
                'top_parcels': top_parcels,
                'function_analysis': function_analysis
            }
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}

async def main_async(table_type: str, year: str, counties: List[str], analytics: bool):
    """Async main function"""
    async with NAVAssessmentsAgent() as agent:
        if analytics:
            county_filter = counties[0] if counties and len(counties) == 1 else None
            return await agent.get_database_analytics(county_filter, year)
        else:
            return await agent.run_nav_collection(table_type, year, counties)

@click.command()
@click.option('--table-type', type=click.Choice(['N', 'D', 'both']), default='N', 
              help='NAV table type: N (parcels), D (details), or both')
@click.option('--year', default='2024', help='Data year to collect')
@click.option('--counties', help='Comma-separated county codes (e.g., 16,25,50)')
@click.option('--analytics', is_flag=True, help='Get analytics from database')
def main(table_type: str, year: str, counties: str, analytics: bool):
    """NAV Assessments Data Collector"""
    
    console.print("[bold cyan]NAV Assessments Data Collector[/bold cyan]")
    
    # Parse counties
    county_list = []
    if counties:
        county_list = [c.strip() for c in counties.split(',')]
    
    async def run_async():
        """Run the appropriate async function"""
        if table_type == 'both':
            # Run both N and D tables
            results = {}
            
            # Run N table first
            async with NAVAssessmentsAgent() as agent:
                results['N'] = await agent.run_nav_collection('N', year, county_list)
            
            # Run D table second  
            async with NAVAssessmentsAgent() as agent:
                results['D'] = await agent.run_nav_collection('D', year, county_list)
            
            return results
        else:
            return await main_async(table_type, year, county_list, analytics)
    
    # Run async function
    result = asyncio.run(run_async())
    
    if analytics:
        # Display analytics
        if result.get('summary'):
            console.print(f"\n[bold]Assessment Summary:[/bold]")
            summary = result['summary']
            console.print(f"  Total Parcels: {summary.get('total_parcels', 0):,}")
            console.print(f"  Total Assessment Amount: ${summary.get('total_assessment_amount', 0):,.2f}")
            console.print(f"  Average Assessment: ${summary.get('avg_assessment_amount', 0):,.2f}")
            console.print(f"  Max Assessment: ${summary.get('max_assessment_amount', 0):,.2f}")
        
        if result.get('top_parcels'):
            console.print(f"\n[bold]Top Assessed Parcels:[/bold]")
            for parcel in result['top_parcels'][:5]:
                console.print(f"  {parcel['pa_parcel_number']}: ${parcel['total_assessments']:,.2f}")
        
        if result.get('function_analysis'):
            console.print(f"\n[bold]Assessment by Function:[/bold]")
            for func in result['function_analysis'][:5]:
                console.print(f"  {func['function_description']}: ${func['total_amount']:,.2f} ({func['assessment_count']:,} assessments)")
    
    elif isinstance(result, dict):
        if 'N' in result and 'D' in result:
            # Both tables processed
            console.print(f"\n[bold green]Both NAV tables processed successfully![/bold green]")
        elif result.get('success'):
            console.print(f"[bold green]NAV {result.get('table_type', '')} collection completed successfully![/bold green]")
        else:
            console.print(f"[bold red]NAV collection failed: {result.get('error')}[/bold red]")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    main()