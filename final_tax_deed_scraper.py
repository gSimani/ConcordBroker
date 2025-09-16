"""
Final Tax Deed Auction Scraper - Properly extracts all properties
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

class FinalTaxDeedScraper:
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
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def scrape_auction_page(self, url, auction_name):
        """Scrape a single auction page"""
        print(f"\nProcessing: {auction_name}")
        print(f"URL: {url}")
        
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Extract property data using JavaScript evaluation
        properties = await self.page.evaluate('''() => {
            const results = [];
            
            // Find all table rows that contain property data
            const rows = document.querySelectorAll('table tbody tr');
            
            rows.forEach(row => {
                // Skip header rows and empty rows
                if (!row.textContent || row.textContent.includes('Tax Deed #')) {
                    return;
                }
                
                // Look for rows with numbers (these are property rows)
                const firstCell = row.querySelector('td');
                if (!firstCell) return;
                
                const firstText = firstCell.textContent.trim();
                
                // Check if this looks like a tax deed number (just numbers)
                if (/^\d+$/.test(firstText)) {
                    const cells = row.querySelectorAll('td');
                    
                    // Extract data from cells
                    const property = {
                        tax_deed_number: 'TD-2025-' + firstText,
                        opening_bid_text: '',
                        best_bid_text: '',
                        close_time_text: '',
                        status_text: ''
                    };
                    
                    // Get all cell texts
                    const cellTexts = [];
                    cells.forEach((cell, index) => {
                        const text = cell.textContent.trim();
                        cellTexts.push(text);
                        
                        // Identify columns by position and content
                        if (index === 0) {
                            // Tax deed number (already handled)
                        } else if (text.includes('$')) {
                            // Money value
                            if (!property.opening_bid_text) {
                                property.opening_bid_text = text;
                            } else if (!property.best_bid_text || text === '-') {
                                property.best_bid_text = text;
                            }
                        } else if (text.includes('AM') || text.includes('PM') || text === '-') {
                            // Time
                            property.close_time_text = text;
                        } else if (text === 'Upcoming' || text === 'Canceled' || text === 'Cancelled' || 
                                  text === 'Active' || text === 'Sold' || text === 'Closed') {
                            // Status
                            property.status_text = text;
                        }
                    });
                    
                    // Also look for expanded details (if row is expanded)
                    const nextRow = row.nextElementSibling;
                    if (nextRow && nextRow.classList.contains('details')) {
                        const detailText = nextRow.textContent;
                        
                        // Extract parcel number
                        const parcelMatch = detailText.match(/Parcel[:\s]+(\d+)/i);
                        if (parcelMatch) {
                            property.parcel_id = parcelMatch[1];
                        }
                        
                        // Extract address
                        const addressMatch = detailText.match(/Location[:\s]+([^\\n]+)/i);
                        if (addressMatch) {
                            property.address = addressMatch[1].trim();
                        }
                        
                        // Extract certificate holder
                        const holderMatch = detailText.match(/Certificate Holder[:\s]+([^\\n]+)/i);
                        if (holderMatch) {
                            property.certificate_holder = holderMatch[1].trim();
                        }
                    }
                    
                    results.push(property);
                }
            });
            
            return results;
        }''')
        
        # Process extracted properties
        processed_properties = []
        for prop in properties:
            # Parse money values
            opening_bid = 0
            if prop.get('opening_bid_text'):
                match = re.search(r'[\d,]+\.?\d*', prop['opening_bid_text'])
                if match:
                    opening_bid = float(match.group().replace(',', ''))
            
            current_bid = None
            if prop.get('best_bid_text') and prop['best_bid_text'] != '-':
                match = re.search(r'[\d,]+\.?\d*', prop['best_bid_text'])
                if match:
                    current_bid = float(match.group().replace(',', ''))
            
            # Determine status
            status = prop.get('status_text', 'Active')
            if status == 'Canceled':
                status = 'Cancelled'
            elif status == 'Closed':
                status = 'Sold'
            elif status == 'Upcoming':
                status = 'Active'
            
            # Create property record
            property_data = {
                'tax_deed_number': prop.get('tax_deed_number'),
                'parcel_id': prop.get('parcel_id', f"UNKNOWN-{prop.get('tax_deed_number', '')}"),
                'legal_situs_address': prop.get('address', 'Address not available'),
                'opening_bid': opening_bid,
                'current_bid': current_bid,
                'item_status': status,
                'close_time': prop.get('close_time_text', ''),
                'applicant_name': prop.get('certificate_holder', 'TAX CERTIFICATE HOLDER'),
                'auction_name': auction_name,
                'homestead_exemption': 'N',
                'assessed_value': 0,
                'soh_value': 0,
                'auction_id': 1,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Add winning bid for sold properties
            if status == 'Sold' and current_bid:
                property_data['winning_bid'] = current_bid
                property_data['winner_name'] = 'BUYER'
            
            processed_properties.append(property_data)
        
        print(f"  Extracted {len(processed_properties)} properties")
        return processed_properties
        
    async def scrape_all_auctions(self):
        """Scrape all auction pages"""
        
        # List of auction URLs to scrape
        auctions = [
            {'url': 'https://broward.deedauction.net/auction/110', 'name': '9/17/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/111', 'name': '10/15/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/109', 'name': '8/20/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/108', 'name': '7/23/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/107', 'name': '6/25/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/106', 'name': '5/21/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/105', 'name': '4/16/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/104', 'name': '3/19/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/103', 'name': '2/19/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/102', 'name': '1/22/2025 Tax Deed Sale'},
        ]
        
        for auction in auctions:
            try:
                properties = await self.scrape_auction_page(auction['url'], auction['name'])
                self.all_properties.extend(properties)
            except Exception as e:
                print(f"  Error scraping {auction['name']}: {e}")
                continue
                
        # Also try to click on expanded details for each property
        print("\nExpanding property details for additional information...")
        await self.expand_property_details()
        
    async def expand_property_details(self):
        """Click on properties to expand details and extract more information"""
        
        # Go to the first auction page with properties
        await self.page.goto('https://broward.deedauction.net/auction/110', wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Click on first few properties to expand details
        try:
            property_links = await self.page.query_selector_all('td a')
            
            for i, link in enumerate(property_links[:5]):  # Limit to first 5
                try:
                    # Click to expand
                    await link.click()
                    await asyncio.sleep(1)
                    
                    # Extract expanded details
                    details = await self.page.evaluate('''() => {
                        const detailsRow = document.querySelector('tr.details:not([style*="display: none"])');
                        if (!detailsRow) return null;
                        
                        const text = detailsRow.textContent;
                        const result = {};
                        
                        // Extract parcel
                        const parcelMatch = text.match(/Parcel[:\s]+(\d+)/i);
                        if (parcelMatch) result.parcel_id = parcelMatch[1];
                        
                        // Extract address
                        const addressMatch = text.match(/Situs Address[:\s]+([^\\n]+)/i) || 
                                           text.match(/Location[:\s]+([^\\n]+)/i);
                        if (addressMatch) result.address = addressMatch[1].trim();
                        
                        // Extract owner
                        const ownerMatch = text.match(/Owner[:\s]+([^\\n]+)/i);
                        if (ownerMatch) result.owner = ownerMatch[1].trim();
                        
                        // Extract assessed value
                        const assessedMatch = text.match(/Assessed Value[:\s]+\$?([\d,]+)/i);
                        if (assessedMatch) result.assessed_value = assessedMatch[1].replace(/,/g, '');
                        
                        return result;
                    }''')
                    
                    if details:
                        print(f"  Got details for property {i+1}: {details}")
                        
                        # Update existing property if we have a match
                        for prop in self.all_properties:
                            if details.get('parcel_id') and prop['parcel_id'] == details['parcel_id']:
                                if details.get('address'):
                                    prop['legal_situs_address'] = details['address']
                                if details.get('assessed_value'):
                                    prop['assessed_value'] = float(details['assessed_value'])
                                if details.get('owner'):
                                    prop['applicant_name'] = details['owner']
                                break
                    
                except Exception as e:
                    print(f"  Could not expand property {i+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"  Error expanding details: {e}")
            
    async def save_to_database(self):
        """Save all properties to Supabase"""
        if not self.all_properties:
            print("\nNo properties to save")
            return
            
        print(f"\n{'='*60}")
        print(f"Saving {len(self.all_properties)} properties to database...")
        print('='*60)
        
        # Remove duplicates
        unique_properties = {}
        for prop in self.all_properties:
            key = prop.get('tax_deed_number')
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
                    print(f"  Added: {prop.get('tax_deed_number')} - {prop.get('item_status')}")
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
        
        # Save backup
        backup_filename = f'tax_deed_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_filename, 'w') as f:
            json.dump(properties_list, f, indent=2, default=str)
        print(f"Backup saved to {backup_filename}")
        
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
            await self.scrape_all_auctions()
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
                
            # Show sample properties
            print("\nSample properties:")
            for prop in self.all_properties[:3]:
                print(f"  {prop['tax_deed_number']}: ${prop['opening_bid']:,.2f} - {prop['item_status']}")
                
            print("\n" + "="*60)
            print("To view the data:")
            print("1. Go to http://localhost:5173/tax-deed-sales")
            print("2. Refresh the page (Ctrl+F5)")
            print("3. Check all tabs:")
            print("   - Upcoming tab: Active properties")
            print("   - Past tab: Sold properties") 
            print("   - Cancelled tab: Cancelled properties")
            print("="*60)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()

if __name__ == "__main__":
    print("Final Tax Deed Auction Scraper")
    print("="*60)
    print("Extracting ALL properties from Broward County auctions")
    print("="*60)
    
    scraper = FinalTaxDeedScraper()
    asyncio.run(scraper.run())