"""
Fixed Tax Deed Scraper - Clicks expand buttons to get full property details
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from supabase import create_client, Client
import re

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

class PropertyExpandScraper:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.all_properties = []
        self.browser = None
        self.page = None
        
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        print("Initializing browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()
        
    async def scrape_auction(self, url, name):
        """Scrape a single auction by expanding each property"""
        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"URL: {url}")
        print('='*60)
        
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        properties = []
        
        # Find all expand/collapse images
        expand_images = await self.page.query_selector_all('img[src*="expand"], img[src*="collapse"]')
        print(f"Found {len(expand_images)} expandable properties")
        
        # Process each property
        for i in range(min(len(expand_images), 20)):  # Limit to first 20 for testing
            try:
                print(f"\n  Property {i+1}:")
                
                # Re-select the image as DOM might change after clicks
                images = await self.page.query_selector_all('img[src*="expand"], img[src*="collapse"]')
                if i >= len(images):
                    break
                    
                img = images[i]
                src = await img.get_attribute('src')
                
                # Click to expand if needed
                if 'expand' in src:
                    print("    Clicking to expand...")
                    await img.click()
                    await asyncio.sleep(1)
                
                # Extract data from the expanded details
                # Use a simpler extraction method without complex regex
                property_row = await img.evaluate('''(element) => {
                    // Find the main row
                    const mainRow = element.closest('tr');
                    if (!mainRow) return null;
                    
                    const data = {};
                    
                    // Get cells from main row
                    const cells = mainRow.querySelectorAll('td');
                    const cellTexts = [];
                    for (let cell of cells) {
                        cellTexts.push(cell.textContent.trim());
                    }
                    
                    // Extract tax deed number (usually first numeric value)
                    for (let text of cellTexts) {
                        if (/^[0-9]+$/.test(text)) {
                            data.taxDeedNumber = 'TD-' + text;
                            break;
                        }
                    }
                    
                    // Extract money values
                    for (let text of cellTexts) {
                        if (text.includes('$')) {
                            const value = text.replace(/[^0-9.]/g, '');
                            if (value) {
                                if (!data.openingBid) {
                                    data.openingBid = parseFloat(value);
                                } else if (!data.currentBid) {
                                    data.currentBid = parseFloat(value);
                                }
                            }
                        }
                    }
                    
                    // Extract status
                    for (let text of cellTexts) {
                        if (['Upcoming', 'Active', 'Sold', 'Cancelled', 'Canceled'].includes(text)) {
                            data.status = text;
                        }
                    }
                    
                    // Look for expanded details row
                    let detailsRow = mainRow.nextElementSibling;
                    if (detailsRow && (detailsRow.classList.contains('details') || 
                                      detailsRow.querySelector('.details'))) {
                        const detailsText = detailsRow.textContent || '';
                        
                        // Extract parcel number
                        const parcelMatch = detailsText.match(/Parcel[: ]+([0-9]+)/i);
                        if (parcelMatch) data.parcelId = parcelMatch[1];
                        
                        // Extract address
                        const addressMatch = detailsText.match(/(?:Situs Address|Location|Property Address)[: ]+([^\\n]+)/i);
                        if (addressMatch) data.address = addressMatch[1].trim();
                        
                        // Extract owner
                        const ownerMatch = detailsText.match(/Owner[: ]+([^\\n]+)/i);
                        if (ownerMatch) data.owner = ownerMatch[1].trim();
                        
                        // Extract assessed value
                        const assessedMatch = detailsText.match(/Assessed Value[: ]+[$]?([0-9,]+)/i);
                        if (assessedMatch) data.assessedValue = parseFloat(assessedMatch[1].replace(/,/g, ''));
                        
                        // Extract homestead
                        if (detailsText.includes('Homestead: Y')) data.homestead = 'Y';
                        else if (detailsText.includes('Homestead: N')) data.homestead = 'N';
                        
                        // Save snippet of details for debugging
                        data.detailsSnippet = detailsText.substring(0, 200);
                    }
                    
                    return data;
                }''')
                
                if property_row and (property_row.get('taxDeedNumber') or property_row.get('parcelId')):
                    # Convert to database format
                    property_data = {
                        'tax_deed_number': property_row.get('taxDeedNumber', f'TD-AUTO-{i+1}'),
                        'parcel_id': property_row.get('parcelId', f'UNKNOWN-{i+1}'),
                        'legal_situs_address': property_row.get('address', 'Address not available'),
                        'opening_bid': property_row.get('openingBid', 0),
                        'current_bid': property_row.get('currentBid'),
                        'item_status': property_row.get('status', 'Active'),
                        'applicant_name': property_row.get('owner', 'TAX CERTIFICATE HOLDER'),
                        'homestead_exemption': property_row.get('homestead', 'N'),
                        'assessed_value': property_row.get('assessedValue', 0),
                        'auction_id': 1,
                        'close_time': datetime.now().isoformat(),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    properties.append(property_data)
                    
                    print(f"    ✓ Extracted: {property_data['tax_deed_number']}")
                    print(f"      Address: {property_data['legal_situs_address'][:50]}...")
                    print(f"      Parcel: {property_data['parcel_id']}")
                    print(f"      Opening Bid: ${property_data['opening_bid']:,.2f}")
                
                # Click to collapse if expanded
                images_after = await self.page.query_selector_all('img[src*="expand"], img[src*="collapse"]')
                if i < len(images_after):
                    img_after = images_after[i]
                    src_after = await img_after.get_attribute('src')
                    if 'collapse' in src_after:
                        await img_after.click()
                        await asyncio.sleep(0.5)
                        
            except Exception as e:
                print(f"    ✗ Error: {str(e)[:100]}")
                continue
        
        print(f"\n  Total extracted: {len(properties)} properties")
        return properties
        
    async def run(self):
        """Main execution"""
        try:
            await self.initialize_browser()
            
            # Try first auction
            properties = await self.scrape_auction(
                'https://broward.deedauction.net/auction/110',
                '9/17/2025 Tax Deed Sale'
            )
            
            self.all_properties.extend(properties)
            
            # If successful, try another
            if len(properties) < 5:
                print("\nTrying alternative auction...")
                properties2 = await self.scrape_auction(
                    'https://broward.deedauction.net/auction/111',
                    '10/15/2025 Tax Deed Sale'
                )
                self.all_properties.extend(properties2)
            
            # Save to database
            if self.all_properties:
                await self.save_to_database()
            else:
                print("\nNo properties extracted. The website structure may have changed.")
                print("The existing sample data in the database will remain available.")
            
            # Summary
            print("\n" + "="*60)
            print("SCRAPING COMPLETE")
            print("="*60)
            print(f"Total properties scraped: {len(self.all_properties)}")
            
            if self.all_properties:
                print("\nSample of scraped properties:")
                for prop in self.all_properties[:3]:
                    print(f"  - {prop['tax_deed_number']}: {prop['legal_situs_address'][:40]}...")
            
            print("\nTo view all tax deed data:")
            print("1. Go to http://localhost:5173/tax-deed-sales")
            print("2. The page will show all properties from the database")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                
    async def save_to_database(self):
        """Save properties to database"""
        print(f"\nSaving {len(self.all_properties)} properties...")
        
        success = 0
        for prop in self.all_properties:
            try:
                # Remove any undefined fields
                clean_prop = {k: v for k, v in prop.items() if v is not None}
                
                response = self.supabase.table('tax_deed_bidding_items').insert(clean_prop).execute()
                success += 1
                print(f"  ✓ Saved: {prop['tax_deed_number']}")
            except Exception as e:
                if 'duplicate' in str(e):
                    print(f"  - Skipped (exists): {prop['tax_deed_number']}")
                else:
                    print(f"  ✗ Error: {prop['tax_deed_number']} - {str(e)[:50]}")
        
        print(f"\nSuccessfully saved {success} new properties")

if __name__ == "__main__":
    print("Property Expansion Scraper - Fixed Version")
    print("="*60)
    print("Clicks on expand buttons to get full property details")
    print("="*60)
    
    scraper = PropertyExpandScraper()
    asyncio.run(scraper.run())