#!/usr/bin/env python3
"""
Scrape sales history for a specific parcel from BCPA website
and create a CSV file ready to import with load-bcpa-sales.mjs

Usage:
  python scripts/scrape_bcpa_sales_for_parcel.py --folio 504230050040
  python scripts/scrape_bcpa_sales_for_parcel.py --folio 504230050040 --output sales.csv
"""

import asyncio
import logging
import csv
import argparse
from datetime import datetime
from playwright.async_api import async_playwright
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BCPASalesHistoryScraper:
    """Lightweight scraper to extract sales history from BCPA RecInfo page"""

    BASE_URL = "https://bcpa.net/RecInfo.asp?URL_Folio={folio}"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.page = None

    async def setup_browser(self):
        """Initialize browser"""
        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        self.page = await context.new_page()
        self.page.set_default_timeout(30000)

        logger.info("✅ Browser setup complete")

    async def scrape_sales_history(self, folio: str) -> list:
        """Scrape sales history for a specific folio"""
        url = self.BASE_URL.format(folio=folio)
        logger.info(f"📡 Navigating to: {url}")

        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(2)

        # Take screenshot for debugging
        await self.page.screenshot(path=f'bcpa_sales_{folio}.png', full_page=True)
        logger.info(f"📸 Screenshot saved: bcpa_sales_{folio}.png")

        # Extract sales history table
        sales = []

        try:
            # Method 1: Find table by text content "Sales History"
            tables = await self.page.query_selector_all('table')

            for table in tables:
                table_html = await table.inner_html()

                if 'Sales History' in table_html or 'sales history' in table_html.lower():
                    logger.info("Found Sales History table")

                    rows = await table.query_selector_all('tr')

                    for row in rows:
                        cells = await row.query_selector_all('td')

                        if len(cells) >= 4:
                            # Extract cell text
                            cell_texts = []
                            for cell in cells:
                                text = await cell.inner_text()
                                cell_texts.append(text.strip())

                            # Skip header row and invalid data
                            if 'Date' in cell_texts[0] or cell_texts[0] == '' or not cell_texts[0]:
                                continue

                            # Only parse rows with date format (MM/DD/YYYY)
                            if '/' not in cell_texts[0]:
                                continue

                            # Parse sale record
                            date_str = cell_texts[0].strip()
                            sale_type = cell_texts[1].strip()
                            price_str = cell_texts[2].strip()
                            book_page = cell_texts[3].strip() if len(cell_texts) > 3 else ''

                            # Only process if we have valid price
                            if date_str and price_str and '$' in price_str:
                                sale = {
                                    'folio': folio,
                                    'date': self.parse_date(date_str),
                                    'type': sale_type,
                                    'price': self.parse_price(price_str),
                                    'book_page': book_page
                                }

                                # Extract book and page if present
                                if '/' in book_page:
                                    parts = book_page.split('/')
                                    sale['or_book'] = parts[0].strip()
                                    sale['or_page'] = parts[1].strip()
                                else:
                                    sale['or_book'] = ''
                                    sale['or_page'] = ''

                                sales.append(sale)
                                logger.info(f"  ✓ {sale['date']} - {sale['type']} - ${sale['price']:,}")

                    break

            if not sales:
                logger.warning("⚠️  No sales history found in tables")

        except Exception as e:
            logger.error(f"❌ Failed to extract sales history: {e}")

        return sales

    def parse_date(self, date_str: str) -> str:
        """Parse date from MM/DD/YYYY to YYYY-MM-DD"""
        try:
            # Handle MM/DD/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    # Pad month and day with zeros
                    month = month.zfill(2)
                    day = day.zfill(2)
                    return f"{year}-{month}-{day}"

            # Try parsing with datetime as fallback
            dt = datetime.strptime(date_str, '%m/%d/%Y')
            return dt.strftime('%Y-%m-%d')

        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return date_str

    def parse_price(self, price_str: str) -> int:
        """Parse price from $XXX,XXX format to integer"""
        try:
            # Remove $, commas, and whitespace
            cleaned = price_str.replace('$', '').replace(',', '').strip()
            return int(float(cleaned))
        except Exception as e:
            logger.warning(f"Could not parse price '{price_str}': {e}")
            return 0

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()


def save_to_csv(sales: list, output_file: str):
    """Save sales data to CSV file compatible with load-bcpa-sales.mjs"""

    fieldnames = ['folio', 'sale_date', 'sale_price', 'quality_code', 'or_book', 'or_page', 'doc_no', 'cin']

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for sale in sales:
            row = {
                'folio': sale['folio'],
                'sale_date': sale['date'],
                'sale_price': sale['price'],
                'quality_code': sale['type'].upper() if sale['type'] else '',
                'or_book': sale.get('or_book', ''),
                'or_page': sale.get('or_page', ''),
                'doc_no': '',
                'cin': ''
            }
            writer.writerow(row)

    logger.info(f"💾 Saved {len(sales)} sales to {output_file}")


async def main():
    parser = argparse.ArgumentParser(description='Scrape BCPA sales history for a parcel')
    parser.add_argument('--folio', required=True, help='Parcel folio number (e.g., 504230050040)')
    parser.add_argument('--output', default='bcpa_sales_history.csv', help='Output CSV file')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')

    args = parser.parse_args()

    print('='*80)
    print('BCPA SALES HISTORY SCRAPER')
    print('='*80)
    print(f'Folio: {args.folio}')
    print(f'Output: {args.output}')
    print('='*80)
    print()

    scraper = BCPASalesHistoryScraper(headless=args.headless)

    try:
        await scraper.setup_browser()
        sales = await scraper.scrape_sales_history(args.folio)

        if sales:
            print()
            print(f"SUCCESS: Found {len(sales)} sales transactions:")
            print('-'*80)
            for i, sale in enumerate(sales, 1):
                book_page = f"{sale.get('or_book')}/{sale.get('or_page')}" if sale.get('or_book') else 'N/A'
                print(f"{i}. {sale['date']} - {sale['type']} - ${sale['price']:,} - Book/Page: {book_page}")
            print('-'*80)
            print()

            save_to_csv(sales, args.output)

            print()
            print("NEXT STEPS:")
            print(f"   1. Review the CSV file: {args.output}")
            print(f"   2. Import to database:")
            print(f"      node scripts/load-bcpa-sales.mjs --file {args.output} --county BROWARD")
            print()

        else:
            print("WARNING: No sales history found for this parcel")
            print("   Check the screenshot for details: bcpa_sales_{}.png".format(args.folio))

    finally:
        await scraper.close()


if __name__ == '__main__':
    asyncio.run(main())
