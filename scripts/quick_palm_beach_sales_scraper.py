#!/usr/bin/env python3
"""
Quick Palm Beach Sales Scraper for specific property
Uses Playwright to scrape from Palm Beach County Property Appraiser
"""

import asyncio
from playwright.async_api import async_playwright
import sys

async def scrape_palm_beach_sales(parcel_id: str):
    """Scrape sales history for a Palm Beach property"""

    # Format parcel - Palm Beach uses format like 04-42-47-16-14-001-0000
    # From: 00424716140010000
    # To:   04-42-47-16-14-001-0000

    if len(parcel_id) == 17:
        formatted = f"{parcel_id[2:4]}-{parcel_id[4:6]}-{parcel_id[6:8]}-{parcel_id[8:10]}-{parcel_id[10:12]}-{parcel_id[12:15]}-{parcel_id[15:19]}"
    else:
        formatted = parcel_id

    print(f"Scraping Palm Beach parcel: {formatted}")
    print(f"Original: {parcel_id}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible so you can see
        page = await browser.new_page()

        # Try the property search page
        base_url = "https://www.pbcgov.org/papa/Asps/PropertySearch/PropertySearch.aspx"

        try:
            print(f"\nNavigating to Palm Beach PA...")
            await page.goto(base_url, wait_until='networkidle', timeout=30000)

            # Enter parcel ID
            print(f"Entering parcel ID: {formatted}")
            await page.fill('input[name="txtParcelID"]', formatted)
            await page.click('input[name="btnSearch"]')

            # Wait for results
            await page.wait_for_load_state('networkidle', timeout=15000)

            # Look for property detail link
            detail_link = await page.query_selector('a[href*="PropertyDetail"]')
            if detail_link:
                await detail_link.click()
                await page.wait_for_load_state('networkidle', timeout=15000)

            # Now look for Sales tab or section
            print("Looking for sales history...")

            # Try clicking Sales tab if it exists
            sales_tab = await page.query_selector('a:has-text("Sales"), span:has-text("Sales")')
            if sales_tab:
                await sales_tab.click()
                await asyncio.sleep(2)

            # Take screenshot for debugging
            await page.screenshot(path=f'palm_beach_sales_{parcel_id}.png')
            print(f"Screenshot saved: palm_beach_sales_{parcel_id}.png")

            # Try to extract sales data
            sales_tables = await page.query_selector_all('table')

            print(f"\nFound {len(sales_tables)} tables on page")

            sales_data = []
            for i, table in enumerate(sales_tables):
                table_html = await table.inner_html()
                if 'SALE' in table_html.upper() or 'DATE' in table_html.upper():
                    print(f"\nTable {i} might contain sales:")
                    rows = await table.query_selector_all('tr')

                    for row in rows:
                        cells = await row.query_selector_all('td, th')
                        if cells:
                            cell_texts = []
                            for cell in cells:
                                text = await cell.inner_text()
                                cell_texts.append(text.strip())

                            if any('/' in text or '$' in text for text in cell_texts):
                                print(f"  Row: {' | '.join(cell_texts)}")

                                # Try to parse as sale
                                if len(cell_texts) >= 2:
                                    date_cell = cell_texts[0]
                                    price_cell = cell_texts[1] if len(cell_texts) > 1 else ''

                                    if '/' in date_cell and ('$' in price_cell or price_cell.replace(',', '').isdigit()):
                                        sales_data.append({
                                            'date': date_cell,
                                            'price': price_cell,
                                            'raw': cell_texts
                                        })

            print(f"\n\nFound {len(sales_data)} potential sales:")
            for sale in sales_data:
                print(f"  {sale['date']}: {sale['price']}")

            # Keep browser open for 10 seconds so you can see
            print("\nKeeping browser open for 10 seconds...")
            await asyncio.sleep(10)

            await browser.close()
            return sales_data

        except Exception as e:
            print(f"ERROR: {e}")
            await page.screenshot(path=f'error_{parcel_id}.png')
            await browser.close()
            return []


if __name__ == '__main__':
    parcel = sys.argv[1] if len(sys.argv) > 1 else '00424716140010000'
    asyncio.run(scrape_palm_beach_sales(parcel))
