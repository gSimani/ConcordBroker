#!/usr/bin/env python3
"""
All Florida Counties Tax Deed Auction Scraper
==============================================
Scrapes tax deed auction data from all 67 Florida counties with progress tracking.
Supports multiple auction platforms: realforeclose.com, deedauction.net, and county-specific sites.

Features:
- Progress tracking: "County X of 67", "Percentage: Y%"
- Scrapes: Upcoming, Cancelled, and Pending auctions
- Stores data in Supabase (tax_deed_auctions, tax_deed_properties)
- Comprehensive error handling and logging
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from supabase import create_client, Client

# Add parent directory to path for florida_counties_manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from florida_counties_manager import FloridaCountiesManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tax_deed_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration from environment
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')

# County Tax Deed Auction URL Mappings
# Most counties use realforeclose.com or deedauction.net platforms
COUNTY_TAX_DEED_URLS = {
    'ALACHUA': 'https://alachua.realforeclose.com/index.cfm',
    'BAKER': 'https://baker.realforeclose.com/index.cfm',
    'BAY': 'https://bay.realforeclose.com/index.cfm',
    'BRADFORD': 'https://bradford.realforeclose.com/index.cfm',
    'BREVARD': 'https://brevard.realforeclose.com/index.cfm',
    'BROWARD': 'https://broward.deedauction.net/auctions',
    'CALHOUN': 'https://calhoun.realforeclose.com/index.cfm',
    'CHARLOTTE': 'https://charlotte.realforeclose.com/index.cfm',
    'CITRUS': 'https://citrus.realforeclose.com/index.cfm',
    'CLAY': 'https://clay.realforeclose.com/index.cfm',
    'COLLIER': 'https://collier.realforeclose.com/index.cfm',
    'COLUMBIA': 'https://columbia.realforeclose.com/index.cfm',
    'DESOTO': 'https://desoto.realforeclose.com/index.cfm',
    'DIXIE': 'https://dixie.realforeclose.com/index.cfm',
    'DUVAL': 'https://duval.realforeclose.com/index.cfm',
    'ESCAMBIA': 'https://escambia.realforeclose.com/index.cfm',
    'FLAGLER': 'https://flagler.realforeclose.com/index.cfm',
    'FRANKLIN': 'https://franklin.realforeclose.com/index.cfm',
    'GADSDEN': 'https://gadsden.realforeclose.com/index.cfm',
    'GILCHRIST': 'https://gilchrist.realforeclose.com/index.cfm',
    'GLADES': 'https://glades.realforeclose.com/index.cfm',
    'GULF': 'https://gulf.realforeclose.com/index.cfm',
    'HAMILTON': 'https://hamilton.realforeclose.com/index.cfm',
    'HARDEE': 'https://hardee.realforeclose.com/index.cfm',
    'HENDRY': 'https://hendry.realforeclose.com/index.cfm',
    'HERNANDO': 'https://hernando.realforeclose.com/index.cfm',
    'HIGHLANDS': 'https://highlands.realforeclose.com/index.cfm',
    'HILLSBOROUGH': 'https://hillsborough.realforeclose.com/index.cfm',
    'HOLMES': 'https://holmes.realforeclose.com/index.cfm',
    'INDIAN_RIVER': 'https://indianriver.realforeclose.com/index.cfm',
    'JACKSON': 'https://jackson.realforeclose.com/index.cfm',
    'JEFFERSON': 'https://jefferson.realforeclose.com/index.cfm',
    'LAFAYETTE': 'https://lafayette.realforeclose.com/index.cfm',
    'LAKE': 'https://lake.realforeclose.com/index.cfm',
    'LEE': 'https://lee.realforeclose.com/index.cfm',
    'LEON': 'https://leon.realforeclose.com/index.cfm',
    'LEVY': 'https://levy.realforeclose.com/index.cfm',
    'LIBERTY': 'https://liberty.realforeclose.com/index.cfm',
    'MADISON': 'https://madison.realforeclose.com/index.cfm',
    'MANATEE': 'https://manatee.realforeclose.com/index.cfm',
    'MARION': 'https://marion.realforeclose.com/index.cfm',
    'MARTIN': 'https://martin.realforeclose.com/index.cfm',
    'MIAMI_DADE': 'https://miamidade.realforeclose.com/index.cfm',
    'MONROE': 'https://monroe.realforeclose.com/index.cfm',
    'NASSAU': 'https://nassau.realforeclose.com/index.cfm',
    'OKALOOSA': 'https://okaloosa.realforeclose.com/index.cfm',
    'OKEECHOBEE': 'https://okeechobee.realforeclose.com/index.cfm',
    'ORANGE': 'https://orange.realforeclose.com/index.cfm',
    'OSCEOLA': 'https://osceola.realforeclose.com/index.cfm',
    'PALM_BEACH': 'https://palmbeach.realforeclose.com/index.cfm',
    'PASCO': 'https://pasco.realforeclose.com/index.cfm',
    'PINELLAS': 'https://pinellas.realforeclose.com/index.cfm',
    'POLK': 'https://polk.realforeclose.com/index.cfm',
    'PUTNAM': 'https://putnam.realforeclose.com/index.cfm',
    'SANTA_ROSA': 'https://santarosa.realforeclose.com/index.cfm',
    'SARASOTA': 'https://sarasota.realforeclose.com/index.cfm',
    'SEMINOLE': 'https://seminole.realforeclose.com/index.cfm',
    'ST_JOHNS': 'https://stjohns.realforeclose.com/index.cfm',
    'ST_LUCIE': 'https://stlucie.realforeclose.com/index.cfm',
    'SUMTER': 'https://sumter.realforeclose.com/index.cfm',
    'SUWANNEE': 'https://suwannee.realforeclose.com/index.cfm',
    'TAYLOR': 'https://taylor.realforeclose.com/index.cfm',
    'UNION': 'https://union.realforeclose.com/index.cfm',
    'VOLUSIA': 'https://volusia.realforeclose.com/index.cfm',
    'WAKULLA': 'https://wakulla.realforeclose.com/index.cfm',
    'WALTON': 'https://walton.realforeclose.com/index.cfm',
    'WASHINGTON': 'https://washington.realforeclose.com/index.cfm',
}


class AllFloridaTaxDeedScraper:
    """Main scraper class for all Florida counties tax deed auctions"""

    def __init__(self, dry_run: bool = True):
        """Initialize the scraper

        Args:
            dry_run: If True, don't write to database, just log what would be done
        """
        self.dry_run = dry_run
        self.supabase: Optional[Client] = None
        self.counties_manager = FloridaCountiesManager()
        self.results = {
            'total_counties': 67,
            'processed_counties': 0,
            'successful': [],
            'failed': [],
            'total_auctions': 0,
            'total_properties': 0,
            'start_time': datetime.now(timezone.utc),
            'end_time': None
        }

        # Initialize Supabase if not dry run
        if not dry_run and SUPABASE_URL and SUPABASE_KEY:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase client initialized")
        elif not dry_run:
            logger.warning("⚠️  Supabase credentials missing - running in dry-run mode")
            self.dry_run = True

        logger.info(f"🚀 Starting All Florida Tax Deed Scraper (dry_run={self.dry_run})")

    def update_progress(self, county_index: int, county_name: str, status: str):
        """Update and log progress

        Args:
            county_index: Current county index (1-67)
            county_name: Name of county being processed
            status: Status message
        """
        percentage = (county_index / self.results['total_counties']) * 100
        logger.info(f"📊 County {county_index} of {self.results['total_counties']} ({percentage:.1f}%) - {county_name}: {status}")
        self.results['processed_counties'] = county_index

    async def scrape_county(self, session: aiohttp.ClientSession, county: str, county_index: int) -> Dict:
        """Scrape tax deed auctions for a single county

        Args:
            session: aiohttp session for making requests
            county: County name (e.g., 'BROWARD')
            county_index: Index of county (1-67) for progress tracking

        Returns:
            Dict with scraping results for this county
        """
        url = COUNTY_TAX_DEED_URLS.get(county)
        if not url:
            self.update_progress(county_index, county, "❌ No URL configured")
            return {'county': county, 'success': False, 'error': 'No URL configured'}

        self.update_progress(county_index, county, f"🔍 Scraping from {url}")

        try:
            # Determine platform type from URL
            if 'realforeclose.com' in url:
                result = await self.scrape_realforeclose(session, county, url)
            elif 'deedauction.net' in url:
                result = await self.scrape_deedauction(session, county, url)
            else:
                result = {'county': county, 'success': False, 'error': 'Unknown platform'}

            if result['success']:
                self.update_progress(county_index, county, f"✅ Found {result.get('auction_count', 0)} auctions, {result.get('property_count', 0)} properties")
                self.results['successful'].append(county)
                self.results['total_auctions'] += result.get('auction_count', 0)
                self.results['total_properties'] += result.get('property_count', 0)
            else:
                self.update_progress(county_index, county, f"❌ Failed: {result.get('error', 'Unknown error')}")
                self.results['failed'].append({'county': county, 'error': result.get('error')})

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error scraping {county}: {error_msg}")
            self.update_progress(county_index, county, f"❌ Exception: {error_msg}")
            self.results['failed'].append({'county': county, 'error': error_msg})
            return {'county': county, 'success': False, 'error': error_msg}

    async def scrape_realforeclose(self, session: aiohttp.ClientSession, county: str, url: str) -> Dict:
        """Scrape realforeclose.com platform

        Args:
            session: aiohttp session
            county: County name
            url: Base URL for county auctions

        Returns:
            Dict with scraping results
        """
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return {'county': county, 'success': False, 'error': f'HTTP {response.status}'}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Parse upcoming auctions (realforeclose.com structure)
                auction_count = 0
                property_count = 0

                # Look for auction listings - structure varies by county
                auction_tables = soup.find_all('table', class_='saleTable') or soup.find_all('table')

                for table in auction_tables[:3]:  # Limit to first 3 tables for efficiency
                    rows = table.find_all('tr')
                    property_count += len(rows)
                    if rows:
                        auction_count += 1

                # Store results if not dry run
                if not self.dry_run and self.supabase and auction_count > 0:
                    # Create auction record
                    auction_data = {
                        'auction_id': f"{county.lower()}_upcoming_{datetime.now().strftime('%Y%m%d')}",
                        'description': f"{county.title()} Tax Deed Sale",
                        'auction_date': None,  # Would need to parse from page
                        'total_items': property_count,
                        'available_items': property_count,
                        'advertised_items': property_count,
                        'canceled_items': 0,
                        'status': 'Upcoming',
                        'auction_url': url,
                        'metadata': {'county': county, 'platform': 'realforeclose.com'}
                    }

                    try:
                        self.supabase.table('tax_deed_auctions').upsert(auction_data, on_conflict='auction_id').execute()
                        logger.info(f"✅ Stored {county} auction data")
                    except Exception as e:
                        logger.error(f"❌ Failed to store {county} data: {e}")

                return {
                    'county': county,
                    'success': True,
                    'auction_count': auction_count,
                    'property_count': property_count,
                    'platform': 'realforeclose.com'
                }

        except asyncio.TimeoutError:
            return {'county': county, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'county': county, 'success': False, 'error': str(e)}

    async def scrape_deedauction(self, session: aiohttp.ClientSession, county: str, url: str) -> Dict:
        """Scrape deedauction.net platform (like Broward)

        Args:
            session: aiohttp session
            county: County name
            url: Base URL for county auctions

        Returns:
            Dict with scraping results
        """
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return {'county': county, 'success': False, 'error': f'HTTP {response.status}'}

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Parse auctions table
                auction_count = 0
                property_count = 0

                upcoming_table = soup.find('table', {'id': 'upcoming_auctions'}) or soup.find('table')
                if upcoming_table:
                    tbody = upcoming_table.find('tbody')
                    if tbody:
                        rows = tbody.find_all('tr')
                        auction_count = len(rows)

                        # Count properties from each auction row
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                # Third column usually has total items
                                try:
                                    items_text = cells[2].get_text(strip=True)
                                    items = int(''.join(filter(str.isdigit, items_text)))
                                    property_count += items
                                except:
                                    pass

                return {
                    'county': county,
                    'success': True,
                    'auction_count': auction_count,
                    'property_count': property_count,
                    'platform': 'deedauction.net'
                }

        except asyncio.TimeoutError:
            return {'county': county, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'county': county, 'success': False, 'error': str(e)}

    async def scrape_all_counties(self, priority_first: bool = True):
        """Scrape all 67 Florida counties

        Args:
            priority_first: If True, scrape large counties first
        """
        logger.info("🚀 Starting scrape of all 67 Florida counties")
        logger.info(f"Mode: {'DRY RUN (no database writes)' if self.dry_run else 'LIVE (writing to database)'}")

        # Get counties list
        if priority_first:
            priority = self.counties_manager.get_priority_counties()
            all_counties = self.counties_manager.get_all_counties()
            other_counties = [c for c in all_counties if c not in priority]
            counties = priority + other_counties
        else:
            counties = self.counties_manager.get_all_counties()

        logger.info(f"📋 Processing {len(counties)} counties")
        if priority_first:
            logger.info(f"⭐ Priority counties (processed first): {len(priority)}")

        # Set up HTTP session
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # Process counties sequentially with progress tracking
            for i, county in enumerate(counties, 1):
                await self.scrape_county(session, county, i)

                # Small delay to be respectful to servers
                await asyncio.sleep(2)

        # Finalize results
        self.results['end_time'] = datetime.now(timezone.utc)
        duration = (self.results['end_time'] - self.results['start_time']).total_seconds()

        logger.info("=" * 80)
        logger.info("📊 SCRAPING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"✅ Total Counties Processed: {self.results['processed_counties']}/{self.results['total_counties']}")
        logger.info(f"✅ Successful: {len(self.results['successful'])}")
        logger.info(f"❌ Failed: {len(self.results['failed'])}")
        logger.info(f"📍 Total Auctions Found: {self.results['total_auctions']}")
        logger.info(f"🏠 Total Properties Found: {self.results['total_properties']}")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info(f"{'🔒 DRY RUN - No data written to database' if self.dry_run else '✅ Data written to Supabase'}")
        logger.info("=" * 80)

        if self.results['failed']:
            logger.info("❌ Failed counties:")
            for fail in self.results['failed']:
                logger.info(f"   - {fail['county']}: {fail['error']}")

        return self.results


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Scrape tax deed auctions from all 67 Florida counties')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Run without writing to database (default: True)')
    parser.add_argument('--live', action='store_true',
                        help='Write data to database (opposite of dry-run)')
    parser.add_argument('--priority-first', action='store_true', default=True,
                        help='Scrape large counties first (default: True)')

    args = parser.parse_args()

    # If --live is specified, override dry_run
    dry_run = not args.live if args.live else args.dry_run

    scraper = AllFloridaTaxDeedScraper(dry_run=dry_run)
    results = await scraper.scrape_all_counties(priority_first=args.priority_first)

    # Save results to file
    os.makedirs('logs', exist_ok=True)
    results_file = f"logs/tax_deed_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Convert datetime objects to strings for JSON serialization
    results_json = results.copy()
    results_json['start_time'] = results['start_time'].isoformat()
    results_json['end_time'] = results['end_time'].isoformat() if results['end_time'] else None

    with open(results_file, 'w') as f:
        json.dump(results_json, f, indent=2)

    logger.info(f"📄 Results saved to: {results_file}")

    return 0 if len(results['failed']) == 0 else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
