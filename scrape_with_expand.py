"""
Tax Deed Scraper that expands each property to get full details
Clicks on the plus/expand button for each property to reveal hidden information
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

class ExpandDetailsScraper:
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
            headless=False,  # Set to False to see what's happening
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def scrape_auction_with_expansion(self, auction_url, auction_name):
        """Scrape an auction page by expanding each property"""
        print(f"\n{'='*60}")
        print(f"Processing: {auction_name}")
        print(f"URL: {auction_url}")
        print('='*60)
        
        await self.page.goto(auction_url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        properties_extracted = []
        
        # Find all expand buttons (plus signs)
        # These are typically images with src="/images/expand.gif" or "/images/collapse.gif"
        expand_buttons = await self.page.query_selector_all('img[src*="expand.gif"], img[src*="collapse.gif"]')
        
        print(f"Found {len(expand_buttons)} expandable properties")
        
        for i, button in enumerate(expand_buttons):
            try:
                print(f"\n  Property {i+1}/{len(expand_buttons)}:")
                
                # Check if already expanded (collapse.gif means it's expanded)
                src = await button.get_attribute('src')
                if 'expand.gif' in src:
                    # Need to click to expand
                    print(f"    Clicking to expand property {i+1}...")
                    await button.click()
                    await asyncio.sleep(1)  # Wait for expansion animation
                
                # Now extract the expanded details
                # The details are usually in the next row after the main row
                property_data = await self.page.evaluate('''(buttonIndex) => {
                    const buttons = document.querySelectorAll('img[src*="expand.gif"], img[src*="collapse.gif"]');
                    const button = buttons[buttonIndex];
                    if (!button) return null;
                    
                    // Find the row containing this button
                    const mainRow = button.closest('tr');
                    if (!mainRow) return null;
                    
                    const result = {};
                    
                    // Extract data from main row
                    const mainCells = mainRow.querySelectorAll('td');
                    mainCells.forEach((cell, idx) => {
                        const text = cell.textContent.trim();
                        
                        // Tax deed number (usually first numeric cell)
                        if (idx === 0 || idx === 1) {
                            if (/^\d+$/.test(text)) {
                                result.tax_deed_number = 'TD-' + text;
                            }
                        }
                        
                        // Opening bid (has dollar sign)
                        if (text.includes('$')) {
                            const value = text.replace(/[^0-9.]/g, '');
                            if (!result.opening_bid) {
                                result.opening_bid = parseFloat(value);
                            } else if (!result.current_bid) {
                                result.current_bid = parseFloat(value);
                            }
                        }
                        
                        // Status
                        if (['Upcoming', 'Active', 'Sold', 'Cancelled', 'Canceled'].includes(text)) {
                            result.status = text;
                        }
                    });
                    
                    // Find the details row (usually next sibling with class 'details')
                    let detailsRow = mainRow.nextElementSibling;
                    while (detailsRow && !detailsRow.classList.contains('details')) {
                        if (detailsRow.querySelector('.details')) {
                            break;
                        }
                        detailsRow = detailsRow.nextElementSibling;
                    }
                    
                    if (detailsRow) {
                        const detailsText = detailsRow.textContent;
                        
                        // Extract parcel number
                        const parcelMatch = detailsText.match(/Parcel[:\s]+(\d+)/i);
                        if (parcelMatch) {
                            result.parcel_id = parcelMatch[1];
                        }
                        
                        // Extract situs address
                        const addressMatch = detailsText.match(/Situs Address[:\s]+([^\n]+)/i) ||
                                           detailsText.match(/Location[:\s]+([^\n]+)/i) ||
                                           detailsText.match(/Property Address[:\s]+([^\n]+)/i);
                        if (addressMatch) {
                            result.address = addressMatch[1].trim();
                        }
                        
                        // Extract legal description
                        const legalMatch = detailsText.match(/Legal[:\s]+([^\n]+)/i);
                        if (legalMatch) {
                            result.legal_description = legalMatch[1].trim();
                        }
                        
                        // Extract owner name
                        const ownerMatch = detailsText.match(/Owner[:\s]+([^\n]+)/i);
                        if (ownerMatch) {
                            result.owner_name = ownerMatch[1].trim();
                        }
                        
                        // Extract certificate holder
                        const holderMatch = detailsText.match(/Certificate Holder[:\s]+([^\n]+)/i) ||
                                          detailsText.match(/Applicant[:\s]+([^\n]+)/i);
                        if (holderMatch) {
                            result.certificate_holder = holderMatch[1].trim();
                        }
                        
                        // Extract assessed value
                        const assessedMatch = detailsText.match(/Assessed Value[:\s]+\$?([\d,]+)/i);
                        if (assessedMatch) {
                            result.assessed_value = parseFloat(assessedMatch[1].replace(/,/g, ''));
                        }
                        
                        // Extract tax amount
                        const taxMatch = detailsText.match(/Tax Amount[:\s]+\$?([\d,]+\.?\d*)/i) ||
                                        detailsText.match(/Taxes Owed[:\s]+\$?([\d,]+\.?\d*)/i);
                        if (taxMatch) {
                            result.taxes_owed = parseFloat(taxMatch[1].replace(/,/g, ''));
                        }
                        
                        // Extract homestead
                        const homesteadMatch = detailsText.match(/Homestead[:\s]+([YN])/i);
                        if (homesteadMatch) {
                            result.homestead = homesteadMatch[1];
                        }
                        
                        // Store full details text for reference
                        result.full_details = detailsText.substring(0, 500); // First 500 chars
                    }
                    
                    return result;
                }''', i)
                
                if property_data and (property_data.get('tax_deed_number') or property_data.get('parcel_id')):
                    # Enrich with additional fields
                    property_data['item_status'] = property_data.get('status', 'Active')
                    property_data['legal_situs_address'] = property_data.get('address', 'Address not available')
                    property_data['applicant_name'] = property_data.get('certificate_holder', property_data.get('owner_name', 'TAX CERTIFICATE HOLDER'))
                    property_data['homestead_exemption'] = property_data.get('homestead', 'N')
                    property_data['assessed_value'] = property_data.get('assessed_value', 0)
                    property_data['total_taxes_owed'] = property_data.get('taxes_owed', 0)
                    property_data['auction_id'] = 1
                    property_data['close_time'] = datetime.now().isoformat()
                    property_data['created_at'] = datetime.now().isoformat()
                    property_data['updated_at'] = datetime.now().isoformat()
                    
                    # Ensure required fields
                    if not property_data.get('tax_deed_number'):
                        property_data['tax_deed_number'] = f'TD-AUTO-{i+1}'
                    if not property_data.get('parcel_id'):
                        property_data['parcel_id'] = f'UNKNOWN-{i+1}'
                    if not property_data.get('opening_bid'):
                        property_data['opening_bid'] = 0
                    
                    properties_extracted.append(property_data)
                    
                    print(f"    Extracted: {property_data.get('tax_deed_number')}")
                    print(f"    Address: {property_data.get('legal_situs_address', 'N/A')[:60]}...")
                    print(f"    Parcel: {property_data.get('parcel_id')}")
                    print(f"    Opening Bid: ${property_data.get('opening_bid', 0):,.2f}")
                    
                # Optionally collapse it back to keep page clean
                if 'collapse.gif' in src:
                    await button.click()
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                print(f"    Error extracting property {i+1}: {str(e)[:100]}")
                continue
        
        # Also try clicking on any property links directly
        if len(properties_extracted) == 0:
            print("\n  No properties found via expand buttons, trying alternative method...")
            
            # Look for clickable tax deed numbers or property rows
            property_links = await self.page.query_selector_all('a[href*="item"], td a')
            
            for i, link in enumerate(property_links[:10]):  # Limit to first 10
                try:
                    text = await link.text_content()
                    if text and re.search(r'\d{5,}', text):  # Looks like a property number
                        await link.click()
                        await asyncio.sleep(1)
                        
                        # Extract from expanded view
                        details = await self.page.query_selector('.details, .property-details, [class*="detail"]')
                        if details:
                            detail_text = await details.text_content()
                            print(f"    Found details for property {i+1}")
                            # Process detail_text...
                            
                except Exception as e:
                    continue
        
        print(f"\n  Total properties extracted: {len(properties_extracted)}")
        return properties_extracted
        
    async def scrape_all_auctions(self):
        """Scrape multiple auction pages"""
        
        # Auction URLs to scrape
        auctions = [
            {'url': 'https://broward.deedauction.net/auction/110', 'name': '9/17/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/111', 'name': '10/15/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/109', 'name': '8/20/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/108', 'name': '7/23/2025 Tax Deed Sale'},
            {'url': 'https://broward.deedauction.net/auction/107', 'name': '6/25/2025 Tax Deed Sale'},
        ]
        
        for auction in auctions:
            try:
                properties = await self.scrape_auction_with_expansion(auction['url'], auction['name'])
                self.all_properties.extend(properties)
                
                # Break after first successful auction if we got data
                if len(properties) > 5:
                    print(f"\nSuccessfully scraped {len(properties)} properties, moving to next auction...")
                    
            except Exception as e:
                print(f"Error scraping {auction['name']}: {e}")
                continue
                
    async def save_to_database(self):
        """Save scraped properties to Supabase"""
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
        
        # Save to database
        success_count = 0
        for prop in properties_list:
            try:
                # Remove fields that don't exist in table
                safe_prop = {k: v for k, v in prop.items() 
                           if k not in ['status', 'full_details', 'legal_description', 
                                       'owner_name', 'certificate_holder', 'taxes_owed', 
                                       'homestead', 'address']}
                
                response = self.supabase.table('tax_deed_bidding_items').insert(safe_prop).execute()
                success_count += 1
                print(f"  Saved: {prop.get('tax_deed_number')}")
                
            except Exception as e:
                # Try upsert if insert fails
                try:
                    response = self.supabase.table('tax_deed_bidding_items').upsert(
                        safe_prop,
                        on_conflict='tax_deed_number'
                    ).execute()
                    success_count += 1
                    print(f"  Updated: {prop.get('tax_deed_number')}")
                except:
                    print(f"  Failed: {prop.get('tax_deed_number')} - {str(e)[:50]}")
                    
        print(f"\nSuccessfully saved {success_count} properties!")
        
        # Save backup
        backup_filename = f'tax_deed_expanded_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
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
            print("SCRAPING WITH EXPANSION COMPLETE!")
            print("="*60)
            print(f"Total properties scraped: {len(self.all_properties)}")
            
            if self.all_properties:
                # Show sample of scraped data
                print("\nSample properties scraped:")
                for prop in self.all_properties[:5]:
                    print(f"  - {prop.get('tax_deed_number')}: {prop.get('legal_situs_address', 'N/A')[:50]}...")
                    print(f"    Parcel: {prop.get('parcel_id')}")
                    print(f"    Opening Bid: ${prop.get('opening_bid', 0):,.2f}")
                    print(f"    Status: {prop.get('item_status')}")
                    
            print("\n" + "="*60)
            print("To view the data:")
            print("1. Go to http://localhost:5173/tax-deed-sales")
            print("2. Refresh the page (Ctrl+F5)")
            print("3. The new properties should appear in the appropriate tabs")
            print("="*60)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()

if __name__ == "__main__":
    print("Tax Deed Scraper with Property Expansion")
    print("="*60)
    print("This scraper clicks on each property's expand button to get full details")
    print("="*60)
    
    scraper = ExpandDetailsScraper()
    asyncio.run(scraper.run())