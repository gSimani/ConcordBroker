"""
Tax Deed Sales Page - Playwright MCP Inspector
Navigates to and analyzes the tax deed sales page at localhost:5173
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaxDeedSalesMCP:
    def __init__(self):
        self.url = "http://localhost:5173/tax-deed-sales"
        self.output_dir = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\TAX_DEED_SALES")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def run(self):
        """Main execution"""
        async with async_playwright() as p:
            # Launch browser in headed mode so you can see what's happening
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to the tax deed sales page
                logger.info(f"Navigating to {self.url}")
                response = await page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                if response:
                    logger.info(f"Response status: {response.status}")
                
                # Wait for the page to fully load
                await asyncio.sleep(3)
                
                # Take initial screenshot
                screenshot_path = self.output_dir / f"tax_deed_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved: {screenshot_path}")
                
                # Get page title
                title = await page.title()
                logger.info(f"Page title: {title}")
                
                # Save page content
                content = await page.content()
                content_file = self.output_dir / f"page_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Page content saved: {content_file}")
                
                # Extract tax deed sales data
                logger.info("Extracting tax deed sales data...")
                
                # Look for common elements in tax deed sales pages
                data = await self.extract_page_data(page)
                
                # Save extracted data
                data_file = self.output_dir / f"tax_deed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(data_file, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Data saved: {data_file}")
                
                # Try to interact with filters or search if available
                await self.interact_with_page(page)
                
                # Keep browser open for manual inspection
                logger.info("Browser will remain open for 60 seconds for manual inspection...")
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error: {e}")
                # Take error screenshot
                error_screenshot = self.output_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(error_screenshot))
                logger.info(f"Error screenshot saved: {error_screenshot}")
                raise
                
            finally:
                await browser.close()
                logger.info("Browser closed")
                
    async def extract_page_data(self, page):
        """Extract structured data from the page"""
        data = {}
        
        try:
            # Extract all text content
            text_content = await page.inner_text('body')
            data['text_content'] = text_content[:1000]  # First 1000 chars
            
            # Look for tables
            tables = await page.query_selector_all('table')
            data['table_count'] = len(tables)
            
            if tables:
                logger.info(f"Found {len(tables)} tables")
                # Extract data from first table
                first_table_data = await self.extract_table_data(page, 'table')
                if first_table_data:
                    data['first_table'] = first_table_data
            
            # Look for property cards or listings
            property_cards = await page.query_selector_all('[class*="card"], [class*="property"], [class*="listing"]')
            data['property_count'] = len(property_cards)
            logger.info(f"Found {len(property_cards)} property elements")
            
            # Look for specific tax deed elements
            tax_deed_elements = await page.query_selector_all('[class*="tax"], [class*="deed"], [class*="sale"]')
            data['tax_deed_elements'] = len(tax_deed_elements)
            
            # Extract all links
            links = await page.evaluate('''
                () => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links.map(link => ({
                        text: link.textContent.trim(),
                        href: link.href
                    })).filter(link => link.text);
                }
            ''')
            data['links'] = links[:10]  # First 10 links
            
            # Extract all buttons
            buttons = await page.evaluate('''
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    return buttons.map(btn => btn.textContent.trim()).filter(text => text);
                }
            ''')
            data['buttons'] = buttons
            
            # Look for filters or search inputs
            inputs = await page.query_selector_all('input[type="text"], input[type="search"], select')
            data['input_count'] = len(inputs)
            
            # Check for any error messages
            error_elements = await page.query_selector_all('[class*="error"], [class*="alert"]')
            if error_elements:
                errors = []
                for elem in error_elements[:3]:  # First 3 errors
                    error_text = await elem.inner_text()
                    errors.append(error_text)
                data['errors'] = errors
                
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            data['extraction_error'] = str(e)
            
        return data
        
    async def extract_table_data(self, page, selector):
        """Extract data from a table"""
        try:
            table_data = await page.evaluate(f'''
                (selector) => {{
                    const table = document.querySelector(selector);
                    if (!table) return null;
                    
                    const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
                    const rows = Array.from(table.querySelectorAll('tbody tr')).slice(0, 10); // First 10 rows
                    
                    const data = rows.map(row => {{
                        const cells = Array.from(row.querySelectorAll('td'));
                        const rowData = {{}};
                        cells.forEach((cell, index) => {{
                            const header = headers[index] || `col_${{index}}`;
                            rowData[header] = cell.textContent.trim();
                        }});
                        return rowData;
                    }});
                    
                    return {{
                        headers: headers,
                        rows: data,
                        row_count: table.querySelectorAll('tbody tr').length
                    }};
                }}
            ''', selector)
            
            return table_data
            
        except Exception as e:
            logger.error(f"Error extracting table: {e}")
            return None
            
    async def interact_with_page(self, page):
        """Try to interact with page elements"""
        try:
            # Look for search input
            search_inputs = await page.query_selector_all('input[type="search"], input[placeholder*="search" i], input[placeholder*="filter" i]')
            if search_inputs:
                logger.info("Found search input, entering test query...")
                await search_inputs[0].fill("Miami")
                await page.keyboard.press('Enter')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Take screenshot after search
                search_screenshot = self.output_dir / f"after_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(search_screenshot), full_page=True)
                logger.info(f"Search screenshot saved: {search_screenshot}")
            
            # Look for filter dropdowns
            selects = await page.query_selector_all('select')
            if selects:
                logger.info(f"Found {len(selects)} dropdown filters")
                for i, select in enumerate(selects[:2]):  # First 2 dropdowns
                    options = await select.evaluate('(el) => Array.from(el.options).map(opt => opt.value)')
                    logger.info(f"Dropdown {i+1} options: {options[:5]}")  # First 5 options
            
            # Look for date pickers
            date_inputs = await page.query_selector_all('input[type="date"]')
            if date_inputs:
                logger.info(f"Found {len(date_inputs)} date inputs")
                
            # Click on first property/sale item if available
            property_items = await page.query_selector_all('tr[onclick], div[onclick], a[href*="property"], a[href*="sale"]')
            if property_items:
                logger.info(f"Found {len(property_items)} clickable property items")
                # Click first item
                await property_items[0].click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)
                
                # Take screenshot of detail view
                detail_screenshot = self.output_dir / f"property_detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(detail_screenshot), full_page=True)
                logger.info(f"Detail screenshot saved: {detail_screenshot}")
                
                # Go back
                await page.go_back()
                await page.wait_for_load_state('networkidle')
                
        except Exception as e:
            logger.error(f"Error during interaction: {e}")

async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("TAX DEED SALES - PLAYWRIGHT MCP INSPECTOR")
    print("="*60)
    print(f"Target URL: http://localhost:5173/tax-deed-sales")
    print(f"Output directory: C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\TAX_DEED_SALES")
    print("-"*60)
    
    inspector = TaxDeedSalesMCP()
    await inspector.run()
    
    print("\n" + "="*60)
    print("INSPECTION COMPLETE")
    print("="*60)
    print("Check the output directory for:")
    print("- Screenshots")
    print("- Page content (HTML)")
    print("- Extracted data (JSON)")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())