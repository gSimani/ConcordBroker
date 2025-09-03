"""
BCPA Web Scraper - Broward County Property Appraiser
Uses Playwright to scrape property data from web.bcpa.net
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

import click
from playwright.async_api import async_playwright, Page
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

logger = logging.getLogger(__name__)
console = Console()


class BCPAScraper:
    """Scraper for Broward County Property Appraiser website"""
    
    BASE_URL = "https://web.bcpa.net/BcpaClient/"
    SEARCH_URL = "https://web.bcpa.net/BcpaClient/#/Search/Advanced"
    
    # Broward County cities
    CITIES = [
        'COCONUT CREEK', 'COOPER CITY', 'CORAL SPRINGS', 'DANIA BEACH',
        'DAVIE', 'DEERFIELD BEACH', 'FORT LAUDERDALE', 'HALLANDALE BEACH',
        'HILLSBORO BEACH', 'HOLLYWOOD', 'LAUDERDALE-BY-THE-SEA',
        'LAUDERDALE LAKES', 'LAUDERHILL', 'LAZY LAKE', 'LIGHTHOUSE POINT',
        'MARGATE', 'MIRAMAR', 'NORTH LAUDERDALE', 'OAKLAND PARK',
        'PARKLAND', 'PEMBROKE PARK', 'PEMBROKE PINES', 'PLANTATION',
        'POMPANO BEACH', 'SEA RANCH LAKES', 'SOUTHWEST RANCHES', 'SUNRISE',
        'TAMARAC', 'WEST PARK', 'WESTON', 'WILTON MANORS'
    ]
    
    # High-value use codes
    PRIORITY_USE_CODES = {
        '48': 'Industrial Warehouses',
        '43': 'Lumber Yards',
        '39': 'Hotels/Motels',
        '17': 'Office Buildings',
        '03': 'Multi-family 10+ units',
        '04': 'Condominiums',
        '00': 'Vacant Land',
    }
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.cache_dir = Path("/data/cache/bcpa")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def setup_browser(self):
        """Initialize browser with anti-detection measures"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=site-per-process',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            java_script_enabled=True,
        )
        
        # Add stealth scripts
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
        """)
        
        self.page = await context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(30000)
        
        logger.info("Browser setup complete")
    
    async def search_by_city_and_use(self, city: str, use_code: str) -> List[Dict]:
        """Search properties by city and use code"""
        results = []
        
        try:
            console.print(f"[yellow]Searching {city} - Use Code {use_code}[/yellow]")
            
            # Navigate to search page
            await self.page.goto(self.SEARCH_URL, wait_until='networkidle')
            await asyncio.sleep(2)  # Let page fully load
            
            # Fill search form
            await self.page.select_option('select#city', city)
            await asyncio.sleep(0.5)
            
            await self.page.fill('input#useCode', use_code)
            await asyncio.sleep(0.5)
            
            # Click search
            await self.page.click('button#searchButton')
            
            # Wait for results
            await self.page.wait_for_selector('div.results-container', timeout=10000)
            await asyncio.sleep(2)
            
            # Extract results with pagination
            page_num = 1
            while True:
                console.print(f"[dim]Processing page {page_num}[/dim]")
                
                # Extract property data from current page
                properties = await self.extract_properties_from_page()
                results.extend(properties)
                
                # Check for next page
                next_button = await self.page.query_selector('button.next-page:not([disabled])')
                if not next_button:
                    break
                
                await next_button.click()
                await asyncio.sleep(2)
                page_num += 1
                
                # Limit pages to prevent infinite loops
                if page_num > 100:
                    logger.warning("Reached maximum page limit")
                    break
            
            console.print(f"[green]Found {len(results)} properties[/green]")
            
        except Exception as e:
            logger.error(f"Search failed for {city}/{use_code}: {e}")
        
        return results
    
    async def extract_properties_from_page(self) -> List[Dict]:
        """Extract property data from current results page"""
        properties = []
        
        # Get all property rows
        rows = await self.page.query_selector_all('tr.property-row')
        
        for row in rows:
            try:
                property_data = {}
                
                # Extract folio
                folio_elem = await row.query_selector('.folio-link')
                if folio_elem:
                    property_data['folio'] = await folio_elem.inner_text()
                
                # Extract owner
                owner_elem = await row.query_selector('.owner-name')
                if owner_elem:
                    property_data['owner'] = await owner_elem.inner_text()
                
                # Extract address
                addr_elem = await row.query_selector('.property-address')
                if addr_elem:
                    property_data['address'] = await addr_elem.inner_text()
                
                # Extract values
                value_elem = await row.query_selector('.just-value')
                if value_elem:
                    value_text = await value_elem.inner_text()
                    property_data['just_value'] = self.parse_currency(value_text)
                
                # Extract year built
                year_elem = await row.query_selector('.year-built')
                if year_elem:
                    property_data['year_built'] = await year_elem.inner_text()
                
                # Add metadata
                property_data['scraped_at'] = datetime.now().isoformat()
                
                if property_data.get('folio'):
                    properties.append(property_data)
                    
            except Exception as e:
                logger.debug(f"Failed to extract row: {e}")
        
        return properties
    
    async def get_property_details(self, folio: str) -> Dict:
        """Get detailed information for a specific property"""
        details = {'folio': folio}
        
        try:
            # Navigate to property page
            url = f"{self.BASE_URL}#/Property/{folio}"
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Extract detailed information
            details['owner'] = await self.safe_get_text('.owner-info')
            details['mailing_address'] = await self.safe_get_text('.mailing-address')
            details['situs_address'] = await self.safe_get_text('.situs-address')
            
            # Values
            details['just_value'] = await self.safe_get_currency('.just-value')
            details['assessed_value'] = await self.safe_get_currency('.assessed-value')
            details['taxable_value'] = await self.safe_get_currency('.taxable-value')
            
            # Property characteristics
            details['land_area'] = await self.safe_get_text('.land-area')
            details['building_area'] = await self.safe_get_text('.building-area')
            details['year_built'] = await self.safe_get_text('.year-built')
            details['bedrooms'] = await self.safe_get_text('.bedrooms')
            details['bathrooms'] = await self.safe_get_text('.bathrooms')
            
            # Sales history
            sales = await self.extract_sales_history()
            details['sales'] = sales
            
            # Save to cache
            await self.save_to_cache(folio, details)
            
        except Exception as e:
            logger.error(f"Failed to get details for {folio}: {e}")
        
        return details
    
    async def extract_sales_history(self) -> List[Dict]:
        """Extract sales history from property page"""
        sales = []
        
        try:
            # Wait for sales table
            await self.page.wait_for_selector('table.sales-history', timeout=5000)
            
            rows = await self.page.query_selector_all('table.sales-history tr')
            
            for row in rows[1:]:  # Skip header
                sale = {}
                cells = await row.query_selector_all('td')
                
                if len(cells) >= 3:
                    sale['date'] = await cells[0].inner_text()
                    sale['price'] = self.parse_currency(await cells[1].inner_text())
                    sale['type'] = await cells[2].inner_text()
                    
                    if sale['date'] and sale['price']:
                        sales.append(sale)
                        
        except Exception as e:
            logger.debug(f"No sales history found: {e}")
        
        return sales
    
    async def safe_get_text(self, selector: str) -> Optional[str]:
        """Safely get text from element"""
        try:
            elem = await self.page.query_selector(selector)
            if elem:
                return await elem.inner_text()
        except:
            pass
        return None
    
    async def safe_get_currency(self, selector: str) -> Optional[float]:
        """Safely get currency value from element"""
        text = await self.safe_get_text(selector)
        if text:
            return self.parse_currency(text)
        return None
    
    def parse_currency(self, text: str) -> Optional[float]:
        """Parse currency string to float"""
        if not text:
            return None
        
        try:
            # Remove $ and commas
            cleaned = text.replace('$', '').replace(',', '').strip()
            return float(cleaned)
        except:
            return None
    
    async def save_to_cache(self, folio: str, data: Dict):
        """Save property data to cache"""
        cache_file = self.cache_dir / f"{folio}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def run_sweep(self, cities: List[str] = None, 
                       use_codes: List[str] = None) -> Dict:
        """Run a comprehensive sweep of cities and use codes"""
        
        if not cities:
            cities = self.CITIES[:5]  # Start with first 5 cities
        if not use_codes:
            use_codes = list(self.PRIORITY_USE_CODES.keys())
        
        await self.setup_browser()
        
        all_results = []
        stats = {
            'started_at': datetime.now().isoformat(),
            'cities_processed': 0,
            'use_codes_processed': 0,
            'properties_found': 0,
        }
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                task = progress.add_task(
                    f"Sweeping {len(cities)} cities x {len(use_codes)} use codes",
                    total=len(cities) * len(use_codes)
                )
                
                for city in cities:
                    for use_code in use_codes:
                        results = await self.search_by_city_and_use(city, use_code)
                        all_results.extend(results)
                        
                        stats['properties_found'] += len(results)
                        progress.advance(task)
                    
                    stats['cities_processed'] += 1
                
                stats['use_codes_processed'] = len(use_codes)
            
        finally:
            if self.browser:
                await self.browser.close()
        
        stats['finished_at'] = datetime.now().isoformat()
        stats['success'] = True
        
        # Save results
        output_file = self.cache_dir / f"sweep_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'stats': stats,
                'results': all_results
            }, f, indent=2)
        
        console.print(f"[green]Sweep complete! Found {stats['properties_found']} properties[/green]")
        console.print(f"Results saved to {output_file}")
        
        return stats


@click.command()
@click.option('--city', help='Specific city to search')
@click.option('--use-code', help='Specific use code to search')
@click.option('--folio', help='Get details for specific folio')
@click.option('--sweep', is_flag=True, help='Run full sweep of priority properties')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
def main(city: str, use_code: str, folio: str, sweep: bool, headless: bool):
    """BCPA Property Scraper CLI"""
    
    console.print("""
[bold cyan]╔════════════════════════════════════╗
║     BCPA Property Scraper          ║
╚════════════════════════════════════╝[/bold cyan]
    """)
    
    scraper = BCPAScraper(headless=headless)
    
    async def run():
        if folio:
            # Get specific property
            await scraper.setup_browser()
            details = await scraper.get_property_details(folio)
            console.print(details)
            await scraper.browser.close()
            
        elif sweep:
            # Run comprehensive sweep
            await scraper.run_sweep()
            
        elif city and use_code:
            # Search specific combination
            await scraper.setup_browser()
            results = await scraper.search_by_city_and_use(city, use_code)
            console.print(f"Found {len(results)} properties")
            for prop in results[:10]:  # Show first 10
                console.print(prop)
            await scraper.browser.close()
        else:
            console.print("[red]Please specify --folio, --sweep, or --city with --use-code[/red]")
    
    asyncio.run(run())


if __name__ == "__main__":
    main()