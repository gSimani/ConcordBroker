"""
Comprehensive Tax Deed Auction Scraper for Broward County
Scrapes ALL properties from https://broward.deedauction.net/auctions
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from supabase import create_client, Client
import re
import time

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

class ComprehensiveTaxDeedScraper:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.all_properties = []
        self.browser = None
        self.page = None
        self.context = None
        
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        print("Initializing browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True in production
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def navigate_to_site(self):
        """Navigate to the Broward tax deed auction site"""
        print("Navigating to Broward County Tax Deed Auctions...")
        url = 'https://broward.deedauction.net/auctions'
        
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Take screenshot for debugging
        await self.page.screenshot(path='tax_deed_page.png')
        print("Screenshot saved as tax_deed_page.png")
        
    async def scrape_all_auctions(self):
        """Scrape all auction types - upcoming, active, past, cancelled"""
        
        # Check for different sections on the page
        sections = [
            ('upcoming', 'Upcoming Auctions'),
            ('active', 'Active Auctions'),
            ('current', 'Current Auctions'),
            ('past', 'Past Auctions'),
            ('cancelled', 'Cancelled Auctions'),
            ('canceled', 'Canceled Auctions')
        ]
        
        for section_id, section_name in sections:
            print(f"\nChecking for {section_name}...")
            
            # Try different ways to find the section
            properties = await self.extract_properties_from_section(section_id, section_name)
            if properties:
                print(f"Found {len(properties)} properties in {section_name}")
                self.all_properties.extend(properties)
                
        # Also try to get properties from any visible tables
        print("\nLooking for any additional property tables...")
        all_tables = await self.page.query_selector_all('table')
        
        for i, table in enumerate(all_tables):
            print(f"Processing table {i+1}...")
            properties = await self.extract_properties_from_table(table)
            if properties:
                print(f"Found {len(properties)} properties in table {i+1}")
                self.all_properties.extend(properties)
                
    async def extract_properties_from_section(self, section_id, section_name):
        """Extract properties from a specific section"""
        properties = []
        
        # Try to find section by ID, class, or text
        selectors = [
            f'#{section_id}_auctions',
            f'.{section_id}-auctions',
            f'[data-section="{section_id}"]',
            f'h2:has-text("{section_name}")',
            f'h3:has-text("{section_name}")'
        ]
        
        for selector in selectors:
            try:
                section = await self.page.wait_for_selector(selector, timeout=2000)
                if section:
                    # Find the table within or after this section
                    table = await self.page.evaluate('''(selector) => {
                        const element = document.querySelector(selector);
                        if (!element) return null;
                        
                        // Look for table as sibling or within parent
                        let table = element.nextElementSibling;
                        while (table && table.tagName !== 'TABLE') {
                            table = table.nextElementSibling;
                        }
                        
                        if (!table) {
                            // Look within the parent element
                            const parent = element.parentElement;
                            table = parent.querySelector('table');
                        }
                        
                        return table ? table.outerHTML : null;
                    }''', selector)
                    
                    if table:
                        # Parse the table HTML
                        properties = await self.parse_table_html(table, section_name)
                        if properties:
                            return properties
            except:
                continue
                
        return properties
        
    async def extract_properties_from_table(self, table):
        """Extract properties from a table element"""
        properties = []
        
        try:
            # Get all rows
            rows = await table.query_selector_all('tbody tr')
            if not rows:
                rows = await table.query_selector_all('tr')
                
            for row in rows:
                # Get all cells
                cells = await row.query_selector_all('td')
                if len(cells) >= 4:  # Minimum expected columns
                    
                    property_data = {}
                    
                    # Extract text from each cell
                    cell_texts = []
                    for cell in cells:
                        text = await cell.text_content()
                        cell_texts.append(text.strip() if text else '')
                        
                    # Try to identify columns based on content
                    if cell_texts[0] and ('TD-' in cell_texts[0] or 'TC-' in cell_texts[0]):
                        # Looks like a tax deed number
                        property_data['tax_deed_number'] = cell_texts[0]
                        
                        # Try to extract other fields
                        for i, text in enumerate(cell_texts):
                            # Parcel number (usually numeric)
                            if re.match(r'^\d{10,}$', text):
                                property_data['parcel_id'] = text
                                
                            # Address (contains street name)
                            elif any(word in text.upper() for word in ['ST', 'AVE', 'BLVD', 'RD', 'DR', 'WAY', 'CT', 'PL']):
                                property_data['legal_situs_address'] = text
                                
                            # Opening bid (contains dollar sign or is numeric)
                            elif '$' in text or (text.replace(',', '').replace('.', '').isdigit() and len(text) > 3):
                                value = float(re.sub(r'[^\d.]', '', text))
                                if 'opening_bid' not in property_data:
                                    property_data['opening_bid'] = value
                                elif 'current_bid' not in property_data:
                                    property_data['current_bid'] = value
                                    
                            # Status
                            elif text.upper() in ['ACTIVE', 'SOLD', 'CANCELLED', 'CANCELED', 'UPCOMING', 'CLOSED']:
                                property_data['item_status'] = text.title()
                                
                            # Date/time
                            elif '/' in text or '-' in text and len(text) >= 8:
                                property_data['close_time'] = text
                                
                        if property_data.get('tax_deed_number'):
                            properties.append(property_data)
                            
        except Exception as e:
            print(f"Error extracting from table: {e}")
            
        return properties
        
    async def parse_table_html(self, html, section_name):
        """Parse HTML table string"""
        properties = []
        
        # Use page.evaluate to parse HTML in browser context
        parsed = await self.page.evaluate('''(html, sectionName) => {
            const div = document.createElement('div');
            div.innerHTML = html;
            const table = div.querySelector('table');
            if (!table) return [];
            
            const rows = table.querySelectorAll('tbody tr, tr');
            const results = [];
            
            rows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 4) {
                    const property = {};
                    
                    // Extract data from cells
                    cells.forEach((cell, index) => {
                        const text = cell.textContent.trim();
                        const link = cell.querySelector('a');
                        
                        // Tax deed number (usually first column)
                        if (index === 0 && text) {
                            property.tax_deed_number = text;
                        }
                        
                        // Parcel number (often has link)
                        if (link && link.href && link.href.includes('parcel')) {
                            property.parcel_id = link.textContent.trim();
                            property.parcel_url = link.href;
                        } else if (/^\d{10,}$/.test(text)) {
                            property.parcel_id = text;
                        }
                        
                        // Address
                        if (/(ST|AVE|BLVD|RD|DR|WAY|CT|PL|LN)/i.test(text) && text.length > 10) {
                            property.legal_situs_address = text;
                        }
                        
                        // Opening bid
                        if (text.includes('$')) {
                            const value = parseFloat(text.replace(/[^0-9.]/g, ''));
                            if (!property.opening_bid) {
                                property.opening_bid = value;
                            } else if (!property.current_bid) {
                                property.current_bid = value;
                            }
                        }
                        
                        // Applicant
                        if (text.includes('LLC') || text.includes('INC') || text.includes('CORP')) {
                            property.applicant_name = text;
                        }
                    });
                    
                    if (property.tax_deed_number || property.parcel_id) {
                        property.item_status = sectionName.includes('Past') ? 'Sold' : 
                                              sectionName.includes('Cancel') ? 'Cancelled' : 'Active';
                        results.push(property);
                    }
                }
            });
            
            return results;
        }''', html, section_name)
        
        return parsed
        
    async def enrich_property_data(self):
        """Add additional fields to properties"""
        print(f"\nEnriching {len(self.all_properties)} properties...")
        
        for prop in self.all_properties:
            # Ensure all required fields exist
            prop.setdefault('tax_deed_number', f'TD-{datetime.now().year}-{len(self.all_properties)}')
            prop.setdefault('parcel_id', 'UNKNOWN')
            prop.setdefault('legal_situs_address', 'Address not available')
            prop.setdefault('opening_bid', 0)
            prop.setdefault('item_status', 'Active')
            prop.setdefault('homestead_exemption', 'N')
            prop.setdefault('assessed_value', 0)
            prop.setdefault('soh_value', 0)
            prop.setdefault('applicant_name', 'TAX CERTIFICATE HOLDER')
            prop.setdefault('close_time', datetime.now().isoformat())
            prop.setdefault('auction_id', 1)
            prop.setdefault('created_at', datetime.now().isoformat())
            prop.setdefault('updated_at', datetime.now().isoformat())
            
    async def save_to_database(self):
        """Save all properties to Supabase"""
        if not self.all_properties:
            print("No properties to save")
            return
            
        print(f"\nSaving {len(self.all_properties)} properties to database...")
        
        # Remove duplicates based on tax_deed_number
        unique_properties = {}
        for prop in self.all_properties:
            key = prop.get('tax_deed_number', prop.get('parcel_id'))
            if key and key not in unique_properties:
                unique_properties[key] = prop
                
        properties_list = list(unique_properties.values())
        print(f"Unique properties: {len(properties_list)}")
        
        # Save in batches
        batch_size = 10
        success_count = 0
        
        for i in range(0, len(properties_list), batch_size):
            batch = properties_list[i:i+batch_size]
            
            for prop in batch:
                try:
                    # Try to insert
                    response = self.supabase.table('tax_deed_bidding_items').insert(prop).execute()
                    success_count += 1
                    print(f"  Added: {prop.get('tax_deed_number')} - {prop.get('legal_situs_address', 'N/A')[:40]}...")
                except Exception as e:
                    # Try update if insert fails
                    try:
                        response = self.supabase.table('tax_deed_bidding_items').upsert(
                            prop,
                            on_conflict='tax_deed_number'
                        ).execute()
                        success_count += 1
                        print(f"  Updated: {prop.get('tax_deed_number')}")
                    except:
                        print(f"  Failed: {prop.get('tax_deed_number')} - {str(e)[:50]}")
                        
        print(f"\nSuccessfully saved {success_count} properties!")
        
        # Save backup to JSON
        with open(f'tax_deed_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(properties_list, f, indent=2, default=str)
        print("Backup saved to JSON file")
        
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
            await self.navigate_to_site()
            await self.scrape_all_auctions()
            await self.enrich_property_data()
            await self.save_to_database()
            
            # Summary
            print("\n" + "="*60)
            print("SCRAPING COMPLETE!")
            print("="*60)
            print(f"Total properties scraped: {len(self.all_properties)}")
            
            status_counts = {}
            for prop in self.all_properties:
                status = prop.get('item_status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
            print("\nProperties by status:")
            for status, count in status_counts.items():
                print(f"  - {status}: {count}")
                
            print("\n" + "="*60)
            print("To view the data:")
            print("1. Go to http://localhost:5173/tax-deed-sales")
            print("2. Refresh the page (Ctrl+F5)")
            print("3. You should see all the scraped properties")
            print("="*60)
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()

if __name__ == "__main__":
    print("Comprehensive Tax Deed Auction Scraper")
    print("="*60)
    print("Target: https://broward.deedauction.net/auctions")
    print("="*60)
    
    scraper = ComprehensiveTaxDeedScraper()
    asyncio.run(scraper.run())