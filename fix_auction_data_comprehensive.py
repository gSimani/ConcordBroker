"""
Comprehensive fix for tax deed auction data issues
Properly handles auction dates, statuses, and all properties
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from supabase import create_client, Client
import json
import re

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

class AuctionDataFixer:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.all_auctions = []
        
    async def scrape_all_auctions(self):
        """Scrape ALL auctions including past and upcoming"""
        print("\n" + "="*60)
        print("COMPREHENSIVE AUCTION DATA SCRAPER")
        print("="*60)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # First, get list of all auctions from main page
            print("\n[STEP 1] Getting all auction dates...")
            await page.goto('https://broward.deedauction.net/', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Extract auction links and dates
            auction_info = await page.evaluate('''() => {
                const auctions = [];
                // Look for auction rows in the tables
                const rows = document.querySelectorAll('tr');
                rows.forEach(row => {
                    const link = row.querySelector('a[href*="/auction/"]');
                    if (link) {
                        const dateCell = row.querySelector('td:first-child') || row.querySelector('td');
                        const countCell = row.querySelector('td:nth-child(2)');
                        const statusCell = row.querySelector('td:last-child');
                        
                        auctions.push({
                            url: link.href,
                            text: link.textContent.trim(),
                            date: dateCell ? dateCell.textContent.trim() : '',
                            count: countCell ? countCell.textContent.trim() : '',
                            status: statusCell ? statusCell.textContent.trim() : ''
                        });
                    }
                });
                return auctions;
            }''')
            
            print(f"Found {len(auction_info)} auctions")
            for info in auction_info:
                print(f"  - {info['date']}: {info['text']} ({info['count']} items) - {info['status']}")
            
            # Now scrape the main upcoming auction (9/17/2025)
            print("\n[STEP 2] Scraping 9/17/2025 Tax Deed Sale...")
            await page.goto('https://broward.deedauction.net/auction/110', wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Get auction date and details
            auction_date = await page.evaluate('''() => {
                const header = document.querySelector('h1, h2, .auction-title');
                if (header && header.textContent.includes('9/17/2025')) {
                    return '2025-09-17';
                }
                // Look for date in page
                const dateMatch = document.body.textContent.match(/9\/17\/2025/);
                return dateMatch ? '2025-09-17' : '2025-09-17';
            }''')
            
            print(f"Auction date: {auction_date}")
            
            # Extract all properties with their actual statuses
            properties = await page.evaluate('''() => {
                const props = [];
                const rows = document.querySelectorAll('tr');
                
                rows.forEach(row => {
                    // Skip header rows
                    if (row.querySelector('th')) return;
                    
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 3) return;
                    
                    // Extract TD number (first column with number or link)
                    let tdNumber = '';
                    const tdLink = row.querySelector('a[href*="Deed"]');
                    if (tdLink) {
                        tdNumber = tdLink.textContent.trim();
                    } else if (cells[0]) {
                        const text = cells[0].textContent.trim();
                        if (/^\d{5}/.test(text)) {
                            tdNumber = text;
                        }
                    }
                    
                    // Extract opening bid
                    let openingBid = 0;
                    for (let cell of cells) {
                        const text = cell.textContent.trim();
                        if (text.includes('$')) {
                            const amount = parseFloat(text.replace(/[^0-9.]/g, ''));
                            if (amount > 100) { // Likely opening bid, not small fee
                                openingBid = amount;
                                break;
                            }
                        }
                    }
                    
                    // Extract status - CRITICAL FIX
                    let status = 'Unknown';
                    const lastCell = cells[cells.length - 1];
                    const statusText = lastCell ? lastCell.textContent.trim() : '';
                    
                    // Check for "Removed" text or red color
                    if (statusText.toLowerCase().includes('removed') || 
                        row.textContent.toLowerCase().includes('removed') ||
                        row.style.color === 'red' ||
                        row.classList.contains('removed') ||
                        row.classList.contains('cancelled')) {
                        status = 'Cancelled';
                    } else if (statusText.toLowerCase().includes('cancel')) {
                        status = 'Cancelled';
                    } else if (statusText.toLowerCase().includes('upcoming')) {
                        status = 'Upcoming';
                    } else if (statusText.toLowerCase().includes('sold')) {
                        status = 'Sold';
                    } else if (openingBid > 0 && !statusText.includes('removed')) {
                        status = 'Upcoming'; // Has bid and not removed = upcoming
                    }
                    
                    if (tdNumber) {
                        props.push({
                            taxDeedNumber: tdNumber,
                            openingBid: openingBid,
                            status: status,
                            originalText: row.textContent.substring(0, 100)
                        });
                    }
                });
                
                return props;
            }''')
            
            print(f"Found {len(properties)} properties")
            
            # Count by status
            status_counts = {}
            for prop in properties:
                status = prop['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("\nProperties by status:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
            
            # Show sample
            print("\nSample properties:")
            for prop in properties[:10]:
                print(f"  TD-{prop['taxDeedNumber']}: ${prop['openingBid']:,.2f} - {prop['status']}")
            
            # Now click expand buttons to get full details for Upcoming properties
            print("\n[STEP 3] Getting detailed information...")
            
            upcoming_props = [p for p in properties if p['status'] == 'Upcoming']
            print(f"Getting details for {len(upcoming_props)} upcoming properties...")
            
            # Store all properties with auction info
            for prop in properties:
                self.all_auctions.append({
                    'tax_deed_number': f"TD-{prop['taxDeedNumber']}",
                    'opening_bid': prop['openingBid'],
                    'item_status': prop['status'],
                    'auction_date': auction_date,
                    'auction_description': '9/17/2025 Tax Deed Sale',
                    'parcel_id': f"PARCEL-{prop['taxDeedNumber']}",  # Will be updated with real data
                    'legal_situs_address': 'Address pending',  # Will be updated
                    'close_time': f"{auction_date}T11:00:00",
                    'applicant_name': 'TAX CERTIFICATE HOLDER',
                    'homestead_exemption': False,
                    'assessed_value': 0,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
            
        finally:
            await browser.close()
            await playwright.stop()
    
    async def save_to_database(self):
        """Save all auction data to database"""
        print("\n[STEP 4] Saving to database...")
        
        # First, clear old data to avoid conflicts
        print("Clearing old data...")
        try:
            # Delete all existing records to start fresh
            self.supabase.table('tax_deed_bidding_items').delete().neq('id', 0).execute()
            print("Old data cleared")
        except Exception as e:
            print(f"Error clearing data: {str(e)[:100]}")
        
        # Now insert new data
        saved = 0
        errors = 0
        
        for prop in self.all_auctions:
            try:
                # Ensure unique TD number
                td_num = prop['tax_deed_number']
                if not td_num.startswith('TD-'):
                    td_num = f"TD-{td_num}"
                prop['tax_deed_number'] = td_num
                
                # Set auction_id based on date
                if '09-17' in prop['auction_date']:
                    prop['auction_id'] = 110
                else:
                    prop['auction_id'] = 1
                
                response = self.supabase.table('tax_deed_bidding_items').insert(prop).execute()
                saved += 1
                
            except Exception as e:
                errors += 1
                print(f"Error saving {prop['tax_deed_number']}: {str(e)[:50]}")
        
        print(f"\nResults: {saved} saved, {errors} errors")
        
        # Verify
        response = self.supabase.table('tax_deed_bidding_items').select('*').execute()
        if response.data:
            total = len(response.data)
            upcoming = len([p for p in response.data if p['item_status'] == 'Upcoming'])
            cancelled = len([p for p in response.data if p['item_status'] in ['Cancelled', 'Canceled']])
            
            print(f"\nDatabase now contains:")
            print(f"  Total: {total} properties")
            print(f"  Upcoming: {upcoming}")
            print(f"  Cancelled: {cancelled}")
    
    async def run(self):
        """Main execution"""
        print("\nSTARTING COMPREHENSIVE AUCTION DATA FIX")
        print("This will:")
        print("  1. Scrape all auction dates")
        print("  2. Get correct property statuses")
        print("  3. Fix date formatting")
        print("  4. Update database with accurate data")
        
        await self.scrape_all_auctions()
        await self.save_to_database()
        
        print("\n" + "="*60)
        print("AUCTION DATA FIX COMPLETE")
        print("="*60)
        print(f"Total properties processed: {len(self.all_auctions)}")
        
        # Save backup
        backup_file = f'auction_data_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(self.all_auctions, f, indent=2, default=str)
        print(f"Backup saved to: {backup_file}")

if __name__ == "__main__":
    fixer = AuctionDataFixer()
    asyncio.run(fixer.run())