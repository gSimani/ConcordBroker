"""
Sunbiz SFTP Loader - Main Entry Point
Connects to sftp.floridados.gov and downloads corporate entity data
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler

from .sftp_client import SunbizSFTPClient
from .parser import SunbizParser
from .database import DatabaseLoader
from .entity_resolver import EntityResolver
from .config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)
console = Console()


class SunbizLoader:
    """Main orchestrator for Sunbiz data loading pipeline"""
    
    def __init__(self):
        self.sftp_client = SunbizSFTPClient()
        self.parser = SunbizParser()
        self.db_loader = DatabaseLoader()
        self.entity_resolver = EntityResolver()
        self.data_path = Path(settings.DATA_RAW_PATH) / "sunbiz"
        
    async def run_daily(self) -> dict:
        """Execute daily incremental load"""
        console.print("[bold green]Starting Sunbiz Daily Load[/bold green]")
        start_time = datetime.now()
        stats = {
            "started_at": start_time.isoformat(),
            "type": "daily",
            "files_downloaded": 0,
            "records_processed": 0,
            "entities_created": 0,
            "entities_updated": 0,
            "errors": []
        }
        
        try:
            # 1. Download daily files
            console.print("[yellow]Connecting to SFTP...[/yellow]")
            daily_files = await self.sftp_client.download_daily_files(self.data_path)
            stats["files_downloaded"] = len(daily_files)
            console.print(f"[green]Downloaded {len(daily_files)} files[/green]")
            
            # 2. Parse each file
            for filepath in daily_files:
                console.print(f"[yellow]Parsing {filepath.name}...[/yellow]")
                records = await self.parser.parse_file(filepath)
                stats["records_processed"] += len(records)
                
                # 3. Load to database
                result = await self.db_loader.load_entities(records)
                stats["entities_created"] += result["created"]
                stats["entities_updated"] += result["updated"]
                
            # 4. Run entity resolution
            console.print("[yellow]Running entity resolution...[/yellow]")
            matches = await self.entity_resolver.resolve_new_entities()
            stats["entity_matches"] = len(matches)
            
            stats["success"] = True
            stats["finished_at"] = datetime.now().isoformat()
            stats["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            logger.error(f"Daily load failed: {e}")
            stats["success"] = False
            stats["errors"].append(str(e))
            
        finally:
            # Log job completion
            await self.db_loader.log_job(stats)
            
        return stats
    
    async def run_quarterly(self) -> dict:
        """Execute quarterly full refresh"""
        console.print("[bold green]Starting Sunbiz Quarterly Full Load[/bold green]")
        start_time = datetime.now()
        stats = {
            "started_at": start_time.isoformat(),
            "type": "quarterly",
            "files_downloaded": 0,
            "records_processed": 0,
            "entities_created": 0,
            "entities_updated": 0,
            "errors": []
        }
        
        try:
            # 1. Download quarterly files
            console.print("[yellow]Downloading quarterly dataset...[/yellow]")
            quarterly_files = await self.sftp_client.download_quarterly_files(self.data_path)
            stats["files_downloaded"] = len(quarterly_files)
            
            # 2. Process in batches
            for filepath in quarterly_files:
                console.print(f"[yellow]Processing {filepath.name}...[/yellow]")
                
                # Parse in chunks for large files
                async for batch in self.parser.parse_file_chunked(filepath, chunk_size=10000):
                    stats["records_processed"] += len(batch)
                    
                    # Load batch
                    result = await self.db_loader.load_entities(batch)
                    stats["entities_created"] += result["created"]
                    stats["entities_updated"] += result["updated"]
                    
                    # Show progress
                    console.print(f"[dim]Processed {stats['records_processed']:,} records[/dim]")
            
            # 3. Full entity resolution
            console.print("[yellow]Running complete entity resolution...[/yellow]")
            matches = await self.entity_resolver.resolve_all_entities()
            stats["entity_matches"] = len(matches)
            
            stats["success"] = True
            stats["finished_at"] = datetime.now().isoformat()
            stats["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            logger.error(f"Quarterly load failed: {e}")
            stats["success"] = False
            stats["errors"].append(str(e))
            
        finally:
            await self.db_loader.log_job(stats)
            
        return stats
    
    async def test_connection(self) -> bool:
        """Test SFTP connection"""
        console.print("[yellow]Testing SFTP connection...[/yellow]")
        try:
            result = await self.sftp_client.test_connection()
            if result:
                console.print("[green]✓ SFTP connection successful![/green]")
                return True
            else:
                console.print("[red]✗ SFTP connection failed[/red]")
                return False
        except Exception as e:
            console.print(f"[red]✗ Connection error: {e}[/red]")
            return False


@click.command()
@click.option('--mode', type=click.Choice(['daily', 'quarterly', 'test']), 
              default='daily', help='Load mode')
@click.option('--date', type=str, help='Specific date to process (YYYY-MM-DD)')
@click.option('--dry-run', is_flag=True, help='Download and parse only, no database writes')
def main(mode: str, date: Optional[str], dry_run: bool):
    """Sunbiz SFTP Data Loader CLI"""
    
    console.print(f"""
[bold cyan]╔════════════════════════════════════╗
║     Sunbiz SFTP Data Loader        ║
║     Mode: {mode:24} ║
║     Dry Run: {str(dry_run):22} ║
╚════════════════════════════════════╝[/bold cyan]
    """)
    
    loader = SunbizLoader()
    
    async def run():
        if mode == 'test':
            return await loader.test_connection()
        elif mode == 'daily':
            return await loader.run_daily()
        elif mode == 'quarterly':
            return await loader.run_quarterly()
    
    # Run async function
    result = asyncio.run(run())
    
    if isinstance(result, dict):
        # Display summary
        console.print("\n[bold cyan]Load Summary:[/bold cyan]")
        console.print(f"Files Downloaded: {result.get('files_downloaded', 0)}")
        console.print(f"Records Processed: {result.get('records_processed', 0):,}")
        console.print(f"Entities Created: {result.get('entities_created', 0):,}")
        console.print(f"Entities Updated: {result.get('entities_updated', 0):,}")
        console.print(f"Duration: {result.get('duration_seconds', 0):.2f} seconds")
        
        if result.get('success'):
            console.print("[bold green]✓ Load completed successfully![/bold green]")
        else:
            console.print(f"[bold red]✗ Load failed: {result.get('errors')}[/bold red]")


if __name__ == "__main__":
    main()