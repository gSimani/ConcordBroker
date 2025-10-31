#!/usr/bin/env python3
"""
Intelligent Sales Gap Analyzer & Scraper
Identifies properties missing sales data and scrapes it from county sources
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json
from supabase import create_client, Client
from playwright.async_api import async_playwright, Page
import csv

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://hnrzpyufhgyuxqzwtbptg.supabase.co')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_SERVICE_KEY'))

if not SUPABASE_SERVICE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# County property appraiser URLs
COUNTY_URLS = {
    'BROWARD': 'https://bcpa.net/RecInfo.asp?URL_Folio={}',
    'PALM BEACH': 'https://www.pbcgov.org/papa/Asps/PropertyDetail/PropertyDetail.aspx?parcel={}',
    'MIAMI-DADE': 'https://www.miamidade.gov/Apps/PA/propertysearch/#/property/{}',
}


class SalesGapAnalyzer:
    """Analyzes database to find properties missing sales data"""

    def __init__(self):
        self.stats = {
            'total_parcels': 0,
            'parcels_with_sales': 0,
            'parcels_without_sales': 0,
            'coverage_percent': 0.0
        }

    async def analyze_county(self, county: str) -> Dict:
        """Analyze sales coverage for a specific county"""
        print(f"\n[ANALYZING] {county} County...")

        # Get total parcels
        total_response = supabase.table('florida_parcels').select('count', count='exact').eq('county', county).execute()
        total_parcels = total_response.count or 0

        # Get parcels with sales in property_sales_history
        sales_response = supabase.table('property_sales_history').select('parcel_id', count='exact').eq('county', county).execute()
        unique_parcels_with_sales = len(set(row['parcel_id'] for row in sales_response.data)) if sales_response.data else 0

        parcels_without = total_parcels - unique_parcels_with_sales
        coverage = (unique_parcels_with_sales / total_parcels * 100) if total_parcels > 0 else 0

        stats = {
            'county': county,
            'total_parcels': total_parcels,
            'parcels_with_sales': unique_parcels_with_sales,
            'parcels_without_sales': parcels_without,
            'coverage_percent': round(coverage, 2),
            'gap_percent': round(100 - coverage, 2)
        }

        print(f"  Total Parcels: {total_parcels:,}")
        print(f"  With Sales: {unique_parcels_with_sales:,} ({coverage:.1f}%)")
        print(f"  Without Sales: {parcels_without:,} ({100-coverage:.1f}%)")

        return stats

    async def find_properties_without_sales(self, county: str, limit: int = 100) -> List[Dict]:
        """Find specific properties missing sales data"""
        print(f"\n[FINDING] Properties in {county} without sales data (limit {limit})...")

        # Get all parcels from county
        parcels_response = supabase.table('florida_parcels')\
            .select('parcel_id, owner_name, phy_addr1, phy_city')\
            .eq('county', county)\
            .limit(limit)\
            .execute()

        if not parcels_response.data:
            return []

        # Check which ones have sales
        missing_sales = []
        for parcel in parcels_response.data:
            parcel_id = parcel['parcel_id']

            # Check if sales exist
            sales_check = supabase.table('property_sales_history')\
                .select('parcel_id')\
                .eq('parcel_id', parcel_id)\
                .limit(1)\
                .execute()

            if not sales_check.data:
                missing_sales.append({
                    'parcel_id': parcel_id,
                    'owner_name': parcel.get('owner_name'),
                    'address': parcel.get('phy_addr1'),
                    'city': parcel.get('phy_city'),
                    'county': county
                })

        print(f"  Found {len(missing_sales)} properties without sales data")
        return missing_sales


class IntelligentSalesScraper:
    """Scrapes sales data from county websites for specific properties"""

    def __init__(self):
        self.browser = None
        self.page = None
        self.scraped_count = 0
        self.error_count = 0

    async def setup(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        print("[BROWSER] Launched")

    async def cleanup(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            print("[BROWSER] Closed")

    async def scrape_broward_sales(self, parcel_id: str) -> List[Dict]:
        """Scrape sales from Broward County (BCPA)"""
        url = COUNTY_URLS['BROWARD'].format(parcel_id)

        try:
            await self.page.goto(url, wait_until='networkidle', timeout=15000)

            # Find sales history table
            sales = []
            tables = await self.page.query_selector_all('table')

            for table in tables:
                table_html = await table.inner_html()
                if 'SALES HISTORY' in table_html.upper() or 'SALE DATE' in table_html.upper():
                    rows = await table.query_selector_all('tr')

                    for row in rows:
                        cells = await row.query_selector_all('td')
                        if len(cells) >= 4:
                            cell_texts = [await cell.inner_text() for cell in cells]

                            # Parse sale row
                            date_str = cell_texts[0].strip()
                            type_str = cell_texts[1].strip() if len(cell_texts) > 1 else ''
                            price_str = cell_texts[2].strip() if len(cell_texts) > 2 else ''
                            book_page = cell_texts[3].strip() if len(cell_texts) > 3 else ''

                            # Validate date format
                            if '/' not in date_str or 'Assessed' in date_str:
                                continue

                            # Validate price
                            if not price_str or '$' not in price_str:
                                continue

                            # Parse components
                            price = int(price_str.replace('$', '').replace(',', ''))
                            book = book_page.split('/')[0] if '/' in book_page else ''
                            page = book_page.split('/')[1] if '/' in book_page else ''

                            sales.append({
                                'parcel_id': parcel_id,
                                'sale_date': date_str,
                                'sale_price': price,
                                'quality_code': type_str,
                                'or_book': book,
                                'or_page': page,
                                'county': 'BROWARD'
                            })

            self.scraped_count += 1
            return sales

        except Exception as e:
            print(f"  ERROR scraping {parcel_id}: {e}")
            self.error_count += 1
            return []

    async def scrape_palm_beach_sales(self, parcel_id: str) -> List[Dict]:
        """Scrape sales from Palm Beach County"""
        # Format parcel ID for Palm Beach (remove leading zeros, format with dashes)
        formatted_parcel = parcel_id.lstrip('0')
        url = COUNTY_URLS['PALM BEACH'].format(formatted_parcel)

        try:
            await self.page.goto(url, wait_until='networkidle', timeout=15000)

            # Look for sales history section
            sales = []

            # Palm Beach uses specific div/table structure
            sales_section = await self.page.query_selector('div[id*="sales"], table[id*="sales"]')
            if not sales_section:
                return []

            rows = await sales_section.query_selector_all('tr')

            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 3:
                    cell_texts = [await cell.inner_text() for cell in cells]

                    date_str = cell_texts[0].strip()
                    price_str = cell_texts[1].strip() if len(cell_texts) > 1 else ''
                    doc_str = cell_texts[2].strip() if len(cell_texts) > 2 else ''

                    if '/' in date_str and '$' in price_str:
                        price = int(price_str.replace('$', '').replace(',', ''))

                        sales.append({
                            'parcel_id': parcel_id,
                            'sale_date': date_str,
                            'sale_price': price,
                            'quality_code': '',
                            'or_book': '',
                            'or_page': '',
                            'clerk_no': doc_str,
                            'county': 'PALM BEACH'
                        })

            self.scraped_count += 1
            return sales

        except Exception as e:
            print(f"  ERROR scraping Palm Beach {parcel_id}: {e}")
            self.error_count += 1
            return []

    async def scrape_property(self, parcel_id: str, county: str) -> List[Dict]:
        """Scrape sales for a property based on county"""
        if county == 'BROWARD':
            return await self.scrape_broward_sales(parcel_id)
        elif county == 'PALM BEACH':
            return await self.scrape_palm_beach_sales(parcel_id)
        else:
            print(f"  County {county} not yet supported for scraping")
            return []


class SalesImporter:
    """Import scraped sales data into database"""

    def __init__(self):
        self.imported_count = 0
        self.skipped_count = 0

    def import_sales(self, sales_records: List[Dict]) -> int:
        """Import sales records to property_sales_history"""
        imported = 0

        for sale in sales_records:
            try:
                # Parse date
                date_parts = sale['sale_date'].split('/')
                if len(date_parts) == 3:
                    month, day, year = date_parts
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year

                    sale_date_iso = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    sale_year = int(year)
                    sale_month = int(month)
                else:
                    continue

                # Check if exists
                existing = supabase.table('property_sales_history')\
                    .select('parcel_id')\
                    .eq('parcel_id', sale['parcel_id'])\
                    .eq('sale_date', sale_date_iso)\
                    .eq('sale_price', sale['sale_price'])\
                    .limit(1)\
                    .execute()

                if existing.data:
                    self.skipped_count += 1
                    continue

                # Insert
                county_no = '15' if sale['county'] == 'PALM BEACH' else '06'  # Broward=06, PalmBeach=15

                payload = {
                    'county_no': county_no,
                    'parcel_id': sale['parcel_id'],
                    'sale_date': sale_date_iso,
                    'sale_price': sale['sale_price'],
                    'sale_year': sale_year,
                    'sale_month': sale_month,
                    'quality_code': sale.get('quality_code', ''),
                    'or_book': sale.get('or_book', ''),
                    'or_page': sale.get('or_page', ''),
                    'clerk_no': sale.get('clerk_no', ''),
                    'county': sale['county'],
                    'assessment_year': 2025
                }

                supabase.table('property_sales_history').insert(payload).execute()
                imported += 1
                self.imported_count += 1

            except Exception as e:
                print(f"  ERROR importing sale: {e}")

        return imported


async def main():
    """Main execution"""
    print("=" * 60)
    print("INTELLIGENT SALES GAP ANALYZER & SCRAPER")
    print("=" * 60)

    analyzer = SalesGapAnalyzer()
    scraper = IntelligentSalesScraper()
    importer = SalesImporter()

    # Step 1: Analyze gaps
    print("\n[STEP 1] Analyzing Sales Data Coverage...")
    county_stats = []

    for county in ['BROWARD', 'PALM BEACH']:
        stats = await analyzer.analyze_county(county)
        county_stats.append(stats)

    # Step 2: Find properties without sales
    print("\n[STEP 2] Finding Properties Without Sales...")

    # Start with Palm Beach since user asked about that property
    missing_properties = await analyzer.find_properties_without_sales('PALM BEACH', limit=10)

    if not missing_properties:
        print("No properties found without sales data")
        return

    print(f"\nFound {len(missing_properties)} properties to scrape")

    # Step 3: Scrape missing sales
    print("\n[STEP 3] Scraping Missing Sales Data...")
    await scraper.setup()

    all_sales = []
    for prop in missing_properties[:5]:  # Start with first 5
        parcel_id = prop['parcel_id']
        county = prop['county']

        print(f"\n  Scraping: {parcel_id} ({prop['address']})")
        sales = await scraper.scrape_property(parcel_id, county)

        if sales:
            print(f"    Found {len(sales)} sales")
            all_sales.extend(sales)
        else:
            print(f"    No sales found")

        # Small delay to be respectful
        await asyncio.sleep(1)

    await scraper.cleanup()

    # Step 4: Import to database
    if all_sales:
        print(f"\n[STEP 4] Importing {len(all_sales)} sales to database...")
        imported = importer.import_sales(all_sales)
        print(f"  Imported: {imported}")
        print(f"  Skipped (duplicates): {importer.skipped_count}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for stats in county_stats:
        print(f"{stats['county']}: {stats['coverage_percent']}% coverage ({stats['parcels_without_sales']:,} missing)")
    print(f"\nScraped: {scraper.scraped_count} properties")
    print(f"Errors: {scraper.error_count}")
    print(f"Imported: {importer.imported_count} sales")
    print(f"Skipped: {importer.skipped_count} duplicates")


if __name__ == '__main__':
    asyncio.run(main())
