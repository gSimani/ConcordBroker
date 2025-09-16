"""
Debug scraper to analyze auction page structure
Takes screenshots and extracts raw HTML for analysis
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json

class DebugAuctionScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.context = None
        
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        print("Initializing browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def debug_auction_page(self):
        """Debug a specific auction page"""
        
        # Navigate to a specific auction
        auction_url = 'https://broward.deedauction.net/auction/110'  # 9/17/2025 auction
        print(f"\nNavigating to: {auction_url}")
        
        await self.page.goto(auction_url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Take screenshot
        screenshot_name = f'auction_page_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        await self.page.screenshot(path=screenshot_name, full_page=True)
        print(f"Screenshot saved: {screenshot_name}")
        
        # Extract page structure
        print("\nAnalyzing page structure...")
        
        # Get all table data
        table_info = await self.page.evaluate('''() => {
            const tables = document.querySelectorAll('table');
            const results = [];
            
            tables.forEach((table, tableIndex) => {
                const rows = table.querySelectorAll('tr');
                const tableData = {
                    index: tableIndex,
                    rowCount: rows.length,
                    headers: [],
                    sampleRows: []
                };
                
                // Get headers
                const headerRow = table.querySelector('thead tr') || rows[0];
                if (headerRow) {
                    const headers = headerRow.querySelectorAll('th, td');
                    headers.forEach(h => {
                        tableData.headers.push(h.textContent.trim());
                    });
                }
                
                // Get first 5 data rows
                for (let i = 1; i < Math.min(6, rows.length); i++) {
                    const row = rows[i];
                    const cells = row.querySelectorAll('td');
                    const rowData = [];
                    cells.forEach(cell => {
                        // Get text and any links
                        const link = cell.querySelector('a');
                        if (link) {
                            rowData.push({
                                text: cell.textContent.trim(),
                                href: link.href
                            });
                        } else {
                            rowData.push(cell.textContent.trim());
                        }
                    });
                    if (rowData.length > 0) {
                        tableData.sampleRows.push(rowData);
                    }
                }
                
                if (tableData.rowCount > 0) {
                    results.push(tableData);
                }
            });
            
            return results;
        }''')
        
        # Print table information
        if table_info:
            for table in table_info:
                print(f"\nTable {table['index']}:")
                print(f"  Rows: {table['rowCount']}")
                print(f"  Headers: {table['headers']}")
                print("  Sample rows:")
                for i, row in enumerate(table['sampleRows'][:3]):
                    print(f"    Row {i+1}: {row}")
        
        # Look for specific patterns
        print("\nLooking for tax deed patterns...")
        
        td_data = await self.page.evaluate('''() => {
            const results = [];
            
            // Find all elements containing TD- pattern
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const text = el.textContent;
                if (text && text.includes('TD-')) {
                    // Get parent row if it's in a table
                    const row = el.closest('tr');
                    if (row) {
                        const cells = row.querySelectorAll('td');
                        const rowData = [];
                        cells.forEach(cell => {
                            rowData.push(cell.textContent.trim());
                        });
                        results.push({
                            tdNumber: text.match(/TD-\d{4}-\d+/)?.[0],
                            rowData: rowData,
                            elementTag: el.tagName
                        });
                    }
                }
            });
            
            return results.slice(0, 10);  // Return first 10 matches
        }''')
        
        if td_data:
            print(f"\nFound {len(td_data)} tax deed elements:")
            for item in td_data[:5]:
                print(f"  TD Number: {item.get('tdNumber')}")
                print(f"  Row Data: {item.get('rowData')}")
        
        # Save raw HTML for analysis
        html_content = await self.page.content()
        html_filename = f'auction_html_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\nHTML saved to: {html_filename}")
        
        # Extract using different methods
        print("\nTrying different extraction methods...")
        
        # Method 1: Look for divs with auction items
        div_items = await self.page.query_selector_all('div[class*="auction"], div[class*="item"], div[class*="property"]')
        print(f"Found {len(div_items)} div elements with auction/item/property classes")
        
        # Method 2: Look for links to property details
        property_links = await self.page.query_selector_all('a[href*="parcel"], a[href*="property"], a[href*="item"]')
        print(f"Found {len(property_links)} property links")
        
        for i, link in enumerate(property_links[:5]):
            text = await link.text_content()
            href = await link.get_attribute('href')
            print(f"  Link {i+1}: {text} -> {href}")
            
    async def close_browser(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
            
    async def run(self):
        """Main execution"""
        try:
            await self.initialize_browser()
            await self.debug_auction_page()
            
            print("\n" + "="*60)
            print("DEBUG COMPLETE")
            print("Check the generated files for analysis:")
            print("  - Screenshot: auction_page_*.png")
            print("  - HTML: auction_html_*.html")
            print("="*60)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()

if __name__ == "__main__":
    print("Debug Auction Scraper")
    print("="*60)
    print("This will analyze the structure of auction pages")
    print("="*60)
    
    scraper = DebugAuctionScraper()
    asyncio.run(scraper.run())