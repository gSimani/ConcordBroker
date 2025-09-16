"""
SDF (Sales Data File) Agent
Downloads and processes property sales transaction data from Florida Revenue
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
    from .database import SDFSalesDB
    from .config import settings
except ImportError:
    from database import SDFSalesDB
    from config import settings

logger = logging.getLogger(__name__)
console = Console()

class SDFSalesAgent:
    """Agent for SDF (Sales Data File) portal"""
    
    BASE_URL = "https://floridarevenue.com/property/dataportal/Documents/"
    SDF_BASE_PATH = "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/"
    
    def __init__(self, data_dir: str = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = settings.get_data_path()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.db = SDFSalesDB()
    
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
    
    def get_sdf_url(self, year: str, preliminary: bool = True) -> str:
        """Generate URL for SDF data file"""
        year_suffix = "P" if preliminary else "F"  # P=Preliminary, F=Final
        filename = f"Broward%20{settings.BROWARD_COUNTY_CODE}%20{'Preliminary' if preliminary else 'Final'}%20SDF%20{year}.zip"
        return urljoin(
            self.BASE_URL,
            f"{self.SDF_BASE_PATH}{year}{year_suffix}/{filename}"
        )
    
    async def download_sdf_file(self, year: str, preliminary: bool = True) -> Optional[Path]:
        """Download SDF file for specified year"""
        url = self.get_sdf_url(year, preliminary)
        filename = f"broward_sdf_{year}{'P' if preliminary else 'F'}.zip"
        filepath = self.data_dir / filename
        
        console.print(f"[yellow]Downloading {filename}...[/yellow]")
        console.print(f"[dim]URL: {url}[/dim]")
        
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
        """Extract ZIP and parse SDF CSV data"""
        console.print("[yellow]Extracting and parsing SDF data...[/yellow]")
        
        stats = {
            'total_records': 0,
            'records_processed': 0,
            'records_created': 0,
            'records_updated': 0,
            'distressed_sales_found': 0,
            'qualified_sales': 0,
            'bank_sales': 0,
            'data_fields': [],
            'sample_records': [],
            'qual_code_distribution': {},
            'price_analysis': {
                'max_price': 0,
                'min_price': float('inf'),
                'total_volume': 0,
                'sales_over_1m': 0,
                'sales_under_1k': 0
            }
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
            await self.db.create_sdf_tables()
        
        # Parse CSV in batches
        batch_size = settings.BATCH_SIZE
        batch = []
        
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
                    "Processing SDF records", 
                    total=total_lines
                )
                
                for i, row in enumerate(reader):
                    if i < 10:  # Store sample records
                        stats['sample_records'].append(row)
                    
                    # Add to batch
                    batch.append(row)
                    
                    # Analyze qualification codes
                    qual_code = row.get('QUAL_CD', '').strip('"')
                    if qual_code:
                        stats['qual_code_distribution'][qual_code] = \
                            stats['qual_code_distribution'].get(qual_code, 0) + 1
                    
                    # Analyze prices
                    try:
                        price = float(row.get('SALE_PRC', '0').strip('"').replace(',', ''))
                        if price > 0:
                            stats['price_analysis']['max_price'] = max(stats['price_analysis']['max_price'], price)
                            if price > 1000:  # Exclude nominal transfers
                                stats['price_analysis']['min_price'] = min(stats['price_analysis']['min_price'], price)
                                stats['price_analysis']['total_volume'] += price
                            if price >= 1000000:
                                stats['price_analysis']['sales_over_1m'] += 1
                            elif price < 1000:
                                stats['price_analysis']['sales_under_1k'] += 1
                    except (ValueError, TypeError):
                        pass
                    
                    # Process batch when full
                    if len(batch) >= batch_size:
                        if load_to_db:
                            db_stats = await self.db.bulk_insert_sdf_sales(batch)
                            stats['records_created'] += db_stats['created']
                            stats['records_updated'] += db_stats['updated']
                            stats['distressed_sales_found'] += db_stats['distressed']
                            stats['qualified_sales'] += db_stats['qualified']
                            stats['bank_sales'] += db_stats['bank_sales']
                        
                        stats['records_processed'] += len(batch)
                        batch = []
                    
                    stats['total_records'] = i + 1
                    progress.update(task, advance=1)
                
                # Process remaining batch
                if batch and load_to_db:
                    db_stats = await self.db.bulk_insert_sdf_sales(batch)
                    stats['records_created'] += db_stats['created']
                    stats['records_updated'] += db_stats['updated']
                    stats['distressed_sales_found'] += db_stats['distressed']
                    stats['qualified_sales'] += db_stats['qualified']
                    stats['bank_sales'] += db_stats['bank_sales']
                    stats['records_processed'] += len(batch)
        
        # Clean up min_price if no valid sales found
        if stats['price_analysis']['min_price'] == float('inf'):
            stats['price_analysis']['min_price'] = 0
        
        return stats
    
    async def run_sdf_collection(self, year: str = "2025", preliminary: bool = True) -> Dict:
        """Main SDF data collection workflow"""
        console.print(f"[bold green]Starting SDF Sales Data Collection for {year}[/bold green]")
        
        start_time = datetime.now()
        results = {
            'started_at': start_time.isoformat(),
            'year': year,
            'preliminary': preliminary,
            'county_number': settings.BROWARD_COUNTY_CODE,
            'success': False,
            'error': None
        }
        
        try:
            # Download data
            zip_path = await self.download_sdf_file(year, preliminary)
            
            # Extract and parse
            analysis = await self.extract_and_parse(zip_path)
            results.update(analysis)
            
            results['success'] = True
            results['finished_at'] = datetime.now().isoformat()
            results['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            # Calculate distress rate
            if results['total_records'] > 0:
                results['distress_rate'] = round(
                    100.0 * results['distressed_sales_found'] / results['total_records'], 2
                )
                results['bank_sale_rate'] = round(
                    100.0 * results['bank_sales'] / results['total_records'], 2
                )
            
            # Log job to database
            await self.db.log_job({
                'type': 'sdf_sales',
                'county_number': settings.BROWARD_COUNTY_CODE,
                'assessment_year': year,
                'started_at': results['started_at'],
                'finished_at': results['finished_at'],
                'success': results['success'],
                'records_processed': results['records_processed'],
                'records_created': results['records_created'],
                'records_updated': results['records_updated'],
                'distressed_sales_found': results['distressed_sales_found'],
                'qualified_sales': results['qualified_sales'],
                'bank_sales': results['bank_sales']
            })
            
            # Display summary
            self.display_summary(results)
            
        except Exception as e:
            results['error'] = str(e)
            results['success'] = False
            logger.error(f"SDF collection failed: {e}")
            console.print(f"[red]Error: {e}[/red]")
            
            # Still log the failed job
            await self.db.log_job({
                'type': 'sdf_sales',
                'county_number': settings.BROWARD_COUNTY_CODE,
                'assessment_year': year,
                'started_at': results['started_at'],
                'finished_at': datetime.now().isoformat(),
                'success': False,
                'errors': [str(e)]
            })
        
        return results
    
    def display_summary(self, results: Dict):
        """Display collection summary"""
        console.print("\n[bold cyan]SDF Collection Summary:[/bold cyan]")
        console.print(f"Total Records: {results.get('total_records', 0):,}")
        console.print(f"Records Processed: {results.get('records_processed', 0):,}")
        console.print(f"Records Created: {results.get('records_created', 0):,}")
        console.print(f"Records Updated: {results.get('records_updated', 0):,}")
        console.print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        
        console.print(f"\n[bold]Sales Analysis:[/bold]")
        console.print(f"Qualified Sales: {results.get('qualified_sales', 0):,}")
        console.print(f"Distressed Sales: {results.get('distressed_sales_found', 0):,} ({results.get('distress_rate', 0):.1f}%)")
        console.print(f"Bank/REO Sales: {results.get('bank_sales', 0):,} ({results.get('bank_sale_rate', 0):.1f}%)")
        
        if 'price_analysis' in results:
            pa = results['price_analysis']
            console.print(f"\n[bold]Price Analysis:[/bold]")
            console.print(f"Total Sales Volume: ${pa['total_volume']:,.0f}")
            console.print(f"Max Sale Price: ${pa['max_price']:,.0f}")
            console.print(f"Min Sale Price: ${pa['min_price']:,.0f}")
            console.print(f"Sales >= $1M: {pa['sales_over_1m']:,}")
            console.print(f"Sales < $1K: {pa['sales_under_1k']:,} (likely non-monetary)")
        
        if 'qual_code_distribution' in results:
            console.print(f"\n[bold]Top Qualification Codes:[/bold]")
            sorted_codes = sorted(results['qual_code_distribution'].items(), 
                                key=lambda x: x[1], reverse=True)
            for code, count in sorted_codes[:10]:
                qual_info = settings.get_qualification_info(code)
                console.print(f"  {code}: {count:,} - {qual_info['description']}")
    
    async def get_database_analytics(self, year: int = None, month: int = None) -> Dict:
        """Get analytics from database"""
        console.print("[yellow]Getting SDF database analytics...[/yellow]")
        
        try:
            summary = await self.db.get_market_summary(settings.BROWARD_COUNTY_CODE, year, month)
            distressed = await self.db.get_distressed_properties(20)
            flips = await self.db.find_flip_candidates(24)
            
            return {
                'summary': summary,
                'recent_distressed': distressed,
                'potential_flips': flips
            }
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}

async def main_async(year: str, preliminary: bool, analytics: bool):
    """Async main function"""
    async with SDFSalesAgent() as agent:
        if analytics:
            return await agent.get_database_analytics(int(year) if year else None)
        else:
            return await agent.run_sdf_collection(year, preliminary)

@click.command()
@click.option('--year', default='2025', help='Data year to collect')
@click.option('--final', is_flag=True, help='Download final data (default is preliminary)')
@click.option('--analytics', is_flag=True, help='Get analytics from database')
def main(year: str, final: bool, analytics: bool):
    """SDF Sales Data Collector"""
    
    console.print("[bold cyan]SDF Sales Data Collector[/bold cyan]")
    
    # Run async function
    result = asyncio.run(main_async(year, not final, analytics))
    
    if analytics:
        # Display analytics
        if result.get('summary'):
            console.print(f"\n[bold]Market Summary:[/bold]")
            summary = result['summary']
            console.print(f"  Total Sales: {summary.get('total_sales', 0):,}")
            console.print(f"  Unique Properties: {summary.get('unique_properties', 0):,}")
            console.print(f"  Distressed Sales: {summary.get('distressed_sales', 0):,}")
            console.print(f"  Bank Sales: {summary.get('bank_sales', 0):,}")
            console.print(f"  Average Sale Price: ${summary.get('avg_sale_price', 0):,.0f}")
            console.print(f"  Total Volume: ${summary.get('total_volume', 0):,.0f}")
        
        if result.get('recent_distressed'):
            console.print(f"\n[bold]Recent Distressed Sales:[/bold]")
            for prop in result['recent_distressed'][:5]:
                console.print(f"  {prop['parcel_id']}: ${prop['sale_price']:,.0f} - {prop['qualification_description']}")
        
        if result.get('potential_flips'):
            console.print(f"\n[bold]Potential Flips:[/bold]")
            for flip in result['potential_flips'][:5]:
                console.print(f"  {flip['parcel_id']}: ${flip['min_price']:,.0f} -> ${flip['max_price']:,.0f} "
                            f"(+${flip['price_delta']:,.0f}) in {flip['days_held']:.0f} days")
    
    elif result.get('success'):
        console.print(f"[bold green]SDF collection completed successfully![/bold green]")
        console.print(f"\n[yellow]KEY FINDING: {result.get('bank_sale_rate', 0):.1f}% of sales involve financial institutions![/yellow]")
    else:
        console.print(f"[bold red]SDF collection failed: {result.get('error')}[/bold red]")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    main()