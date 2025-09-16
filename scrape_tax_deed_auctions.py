"""
Scrape Broward County Tax Deed Auctions and save to Supabase
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import re
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Supabase configuration  
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU0ODI2MzQsImV4cCI6MjA0MTA1ODYzNH0.nArQA_3BKm8wPq3eOYUQJpYZMgTPh0Tz_4CvpEfww1A')

class TaxDeedAuctionScraper:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.browser = None
        self.page = None
        self.context = None
        self.scraped_properties = []
        
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        print("Initializing browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()
        
    async def navigate_to_auctions(self):
        """Navigate to the auctions page"""
        print("Navigating to Broward County Tax Deed Auctions...")
        await self.page.goto('https://broward.deedauction.net/auctions', wait_until='networkidle')
        await asyncio.sleep(3)
        
    async def scrape_upcoming_auctions(self):
        """Scrape upcoming auctions"""
        print("\nScraping UPCOMING auctions...")
        
        # Check if we're on the upcoming auctions tab
        try:
            # Look for upcoming auctions table
            await self.page.wait_for_selector('#upcoming_auctions', timeout=5000)
            
            # Extract upcoming auction properties
            upcoming_properties = await self.page.evaluate('''
                () => {
                    const properties = [];
                    const table = document.querySelector('#upcoming_auctions');
                    if (!table) return properties;
                    
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 7) {
                            // Extract parcel link
                            const parcelLink = cells[1].querySelector('a');
                            const parcelNumber = parcelLink ? parcelLink.textContent.trim() : cells[1].textContent.trim();
                            const parcelUrl = parcelLink ? parcelLink.href : null;
                            
                            // Extract Sunbiz links
                            const sunbizLinks = Array.from(cells[5].querySelectorAll('a')).map(a => ({
                                text: a.textContent.trim(),
                                url: a.href
                            }));
                            
                            properties.push({
                                tax_deed_number: cells[0].textContent.trim(),
                                parcel_number: parcelNumber,
                                parcel_url: parcelUrl,
                                legal_description: cells[2].textContent.trim(),
                                situs_address: cells[3].textContent.trim(),
                                opening_bid: parseFloat(cells[4].textContent.replace(/[$,]/g, '')) || 0,
                                applicant: cells[5].textContent.trim(),
                                sunbiz_links: sunbizLinks,
                                close_time: cells[6].textContent.trim(),
                                status: 'Upcoming',
                                auction_type: 'upcoming'
                            });
                        }
                    });
                    return properties;
                }
            ''')
            
            print(f"Found {len(upcoming_properties)} upcoming properties")
            for prop in upcoming_properties:
                prop['composite_key'] = f"{prop['tax_deed_number']}_{prop['parcel_number']}"
                # Extract Sunbiz entity IDs from links
                prop['sunbiz_entity_ids'] = []
                prop['sunbiz_entity_names'] = []
                for link in prop.get('sunbiz_links', []):
                    prop['sunbiz_entity_names'].append(link['text'])
                    # Extract entity ID from URL if possible
                    match = re.search(r'aggregateId=([^&]+)', link.get('url', ''))
                    if match:
                        prop['sunbiz_entity_ids'].append(match.group(1))
                prop['sunbiz_matched'] = len(prop['sunbiz_entity_ids']) > 0
                
            self.scraped_properties.extend(upcoming_properties)
            
        except Exception as e:
            print(f"Could not scrape upcoming auctions: {e}")
            
    async def scrape_past_auctions(self):
        """Scrape past auctions"""
        print("\nScraping PAST auctions...")
        
        try:
            # Click on Past Auctions tab if it exists
            past_tab = await self.page.query_selector('text="Past Auctions"')
            if past_tab:
                await past_tab.click()
                await asyncio.sleep(2)
            
            # Look for past auctions table
            await self.page.wait_for_selector('#past_auctions', timeout=5000)
            
            # Extract past auction properties
            past_properties = await self.page.evaluate('''
                () => {
                    const properties = [];
                    const table = document.querySelector('#past_auctions');
                    if (!table) return properties;
                    
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 8) {
                            // Extract parcel link
                            const parcelLink = cells[1].querySelector('a');
                            const parcelNumber = parcelLink ? parcelLink.textContent.trim() : cells[1].textContent.trim();
                            const parcelUrl = parcelLink ? parcelLink.href : null;
                            
                            // Extract Sunbiz links
                            const sunbizLinks = Array.from(cells[5].querySelectorAll('a')).map(a => ({
                                text: a.textContent.trim(),
                                url: a.href
                            }));
                            
                            properties.push({
                                tax_deed_number: cells[0].textContent.trim(),
                                parcel_number: parcelNumber,
                                parcel_url: parcelUrl,
                                legal_description: cells[2].textContent.trim(),
                                situs_address: cells[3].textContent.trim(),
                                opening_bid: parseFloat(cells[4].textContent.replace(/[$,]/g, '')) || 0,
                                applicant: cells[5].textContent.trim(),
                                sunbiz_links: sunbizLinks,
                                close_time: cells[6].textContent.trim(),
                                winning_bid: cells[7] ? parseFloat(cells[7].textContent.replace(/[$,]/g, '')) || 0 : null,
                                status: 'Sold',
                                auction_type: 'past'
                            });
                        }
                    });
                    return properties;
                }
            ''')
            
            print(f"Found {len(past_properties)} past auction properties")
            for prop in past_properties:
                prop['composite_key'] = f"{prop['tax_deed_number']}_{prop['parcel_number']}"
                # Extract Sunbiz info
                prop['sunbiz_entity_ids'] = []
                prop['sunbiz_entity_names'] = []
                for link in prop.get('sunbiz_links', []):
                    prop['sunbiz_entity_names'].append(link['text'])
                    match = re.search(r'aggregateId=([^&]+)', link.get('url', ''))
                    if match:
                        prop['sunbiz_entity_ids'].append(match.group(1))
                prop['sunbiz_matched'] = len(prop['sunbiz_entity_ids']) > 0
                prop['best_bid'] = prop.get('winning_bid')
                
            self.scraped_properties.extend(past_properties)
            
        except Exception as e:
            print(f"Could not scrape past auctions: {e}")
            
    async def scrape_cancelled_auctions(self):
        """Scrape cancelled auctions"""
        print("\nScraping CANCELLED auctions...")
        
        try:
            # Click on Cancelled Auctions tab if it exists
            cancelled_tab = await self.page.query_selector('text="Cancelled Auctions"')
            if not cancelled_tab:
                cancelled_tab = await self.page.query_selector('text="Canceled Auctions"')
            
            if cancelled_tab:
                await cancelled_tab.click()
                await asyncio.sleep(2)
                
                # Look for cancelled auctions table
                cancelled_properties = await self.page.evaluate('''
                    () => {
                        const properties = [];
                        // Try different possible table IDs
                        const table = document.querySelector('#cancelled_auctions') || 
                                     document.querySelector('#canceled_auctions') ||
                                     document.querySelector('table:nth-of-type(3)');
                        if (!table) return properties;
                        
                        const rows = table.querySelectorAll('tbody tr');
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 6) {
                                // Extract parcel link
                                const parcelLink = cells[1].querySelector('a');
                                const parcelNumber = parcelLink ? parcelLink.textContent.trim() : cells[1].textContent.trim();
                                const parcelUrl = parcelLink ? parcelLink.href : null;
                                
                                properties.push({
                                    tax_deed_number: cells[0].textContent.trim(),
                                    parcel_number: parcelNumber,
                                    parcel_url: parcelUrl,
                                    legal_description: cells[2].textContent.trim(),
                                    situs_address: cells[3].textContent.trim(),
                                    opening_bid: parseFloat(cells[4].textContent.replace(/[$,]/g, '')) || 0,
                                    applicant: cells[5] ? cells[5].textContent.trim() : 'N/A',
                                    status: 'Cancelled',
                                    auction_type: 'cancelled'
                                });
                            }
                        });
                        return properties;
                    }
                ''')
                
                print(f"Found {len(cancelled_properties)} cancelled properties")
                for prop in cancelled_properties:
                    prop['composite_key'] = f"{prop['tax_deed_number']}_{prop['parcel_number']}"
                    prop['sunbiz_matched'] = False
                    prop['sunbiz_entity_ids'] = []
                    prop['sunbiz_entity_names'] = []
                    
                self.scraped_properties.extend(cancelled_properties)
                
        except Exception as e:
            print(f"Could not scrape cancelled auctions: {e}")
            
    async def extract_additional_details(self):
        """Extract additional details like homestead status from property details"""
        print("\nExtracting additional property details...")
        
        for prop in self.scraped_properties[:5]:  # Limit to first 5 for testing
            try:
                # Parse address to extract city, state, zip
                address_parts = prop['situs_address'].split(',')
                if len(address_parts) >= 2:
                    prop['city'] = address_parts[-2].strip() if len(address_parts) > 2 else 'Fort Lauderdale'
                    state_zip = address_parts[-1].strip().split()
                    prop['state'] = state_zip[0] if state_zip else 'FL'
                    prop['zip_code'] = state_zip[1] if len(state_zip) > 1 else ''
                else:
                    prop['city'] = 'Fort Lauderdale'
                    prop['state'] = 'FL'
                    prop['zip_code'] = ''
                    
                # Check for homestead (simplified - would need property appraiser data for accurate info)
                prop['homestead'] = 'HOMESTEAD' in prop.get('legal_description', '').upper()
                
                # Generate GIS map URL
                prop['gis_map_url'] = f"https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id={prop['parcel_number']}"
                
                # Set auction date (would need to extract from page or use current date)
                prop['auction_date'] = datetime.now().strftime('%Y-%m-%d')
                prop['auction_id'] = f"AUCTION-{datetime.now().strftime('%Y-%m')}"
                prop['auction_description'] = f"{datetime.now().strftime('%B %Y')} Tax Deed Sale"
                
            except Exception as e:
                print(f"Error extracting details for {prop.get('parcel_number')}: {e}")
                
    async def save_to_supabase(self):
        """Save scraped data to Supabase"""
        print("\nSaving to Supabase...")
        
        if not self.scraped_properties:
            print("No properties to save")
            return
            
        # Prepare data for Supabase
        for prop in self.scraped_properties:
            # Remove temporary fields
            prop.pop('sunbiz_links', None)
            prop.pop('winning_bid', None)
            prop.pop('auction_type', None)
            
            # Ensure all required fields exist
            prop.setdefault('tax_certificate_number', None)
            prop.setdefault('assessed_value', None)
            prop.setdefault('best_bid', None)
            prop.setdefault('applicant_companies', [])
            
        try:
            # Insert data into Supabase (using upsert to handle duplicates)
            response = self.supabase.table('tax_deed_properties_with_contacts').upsert(
                self.scraped_properties,
                on_conflict='composite_key'
            ).execute()
            
            print(f"Successfully saved {len(self.scraped_properties)} properties to Supabase")
            
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            # Save to local file as backup
            backup_file = f"tax_deed_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(self.scraped_properties, f, indent=2, default=str)
            print(f"Saved backup to {backup_file}")
            
    async def close_browser(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()
            
    async def run(self):
        """Main execution function"""
        try:
            await self.initialize_browser()
            await self.navigate_to_auctions()
            
            # Scrape all auction types
            await self.scrape_upcoming_auctions()
            await self.scrape_past_auctions()
            await self.scrape_cancelled_auctions()
            
            # Extract additional details
            await self.extract_additional_details()
            
            # Save to Supabase
            await self.save_to_supabase()
            
            print(f"\nTotal properties scraped: {len(self.scraped_properties)}")
            print(f"   - Upcoming: {len([p for p in self.scraped_properties if p['status'] == 'Upcoming'])}")
            print(f"   - Past/Sold: {len([p for p in self.scraped_properties if p['status'] == 'Sold'])}")
            print(f"   - Cancelled: {len([p for p in self.scraped_properties if p['status'] == 'Cancelled'])}")
            
            # Save summary
            summary = {
                'scrape_date': datetime.now().isoformat(),
                'total_properties': len(self.scraped_properties),
                'upcoming': len([p for p in self.scraped_properties if p['status'] == 'Upcoming']),
                'past': len([p for p in self.scraped_properties if p['status'] == 'Sold']),
                'cancelled': len([p for p in self.scraped_properties if p['status'] == 'Cancelled']),
                'properties': self.scraped_properties
            }
            
            with open(f"tax_deed_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                json.dump(summary, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await self.close_browser()
            
if __name__ == "__main__":
    scraper = TaxDeedAuctionScraper()
    asyncio.run(scraper.run())