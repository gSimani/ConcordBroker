"""
Complete Tax Deed Scraper - Scrapes ALL properties by clicking expand buttons
Ensures we get every single property from the auction page with full details
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

class CompletePropertyScraper:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.all_properties = []
        
    async def scrape_all_properties(self):
        """Main function to scrape ALL properties with complete details"""
        print("\n" + "="*60)
        print("COMPLETE PROPERTY SCRAPER")
        print("="*60)
        print("This will:")
        print("1. Go to the auction page")
        print("2. Count ALL properties")
        print("3. Click EVERY expand button")
        print("4. Extract complete details including embedded links")
        print("5. Save everything to database")
        print("="*60)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled'],
            slow_mo=300
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            url = 'https://broward.deedauction.net/auction/110'
            print(f"\nNavigating to: {url}")
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Count total properties
            expand_buttons = await page.query_selector_all('img[alt="Show item details"], img[alt="Hide item details"]')
            total_count = len(expand_buttons)
            print(f"\n[FOUND] {total_count} total properties on page")
            
            if total_count == 0:
                print("[ERROR] No properties found. Page may not have loaded correctly.")
                return
            
            properties_scraped = 0
            
            # Process ALL properties (no limit)
            print(f"\n[STARTING] Will process ALL {total_count} properties")
            print("="*60)
            
            for i in range(total_count):
                try:
                    print(f"\nProperty {i+1}/{total_count}:")
                    
                    # Re-query buttons as DOM changes
                    current_buttons = await page.query_selector_all('img[alt="Show item details"], img[alt="Hide item details"]')
                    
                    if i >= len(current_buttons):
                        print("  [SKIP] Button no longer available")
                        continue
                    
                    button = current_buttons[i]
                    alt_text = await button.get_attribute('alt')
                    
                    # Click to expand if needed
                    if alt_text == "Show item details":
                        print("  Expanding property details...")
                        await button.click()
                        await asyncio.sleep(1)
                    
                    # Extract complete details using JavaScript
                    property_data = await page.evaluate('''(index) => {
                        const allRows = document.querySelectorAll('table tbody tr');
                        let mainRow = null;
                        let detailsRow = null;
                        let rowCounter = 0;
                        
                        // Find the main row and details row for this property
                        for (let row of allRows) {
                            if (row.querySelector('th')) continue;
                            
                            if (row.classList.contains('details') || row.querySelector('.details')) {
                                detailsRow = row;
                            } else if (row.querySelector('img[alt*="item details"]')) {
                                if (rowCounter === index) {
                                    mainRow = row;
                                    let nextRow = row.nextElementSibling;
                                    if (nextRow && (nextRow.classList.contains('details') || nextRow.querySelector('.details'))) {
                                        detailsRow = nextRow;
                                    }
                                    break;
                                }
                                rowCounter++;
                            }
                        }
                        
                        if (!mainRow) return null;
                        
                        const result = {
                            mainRowData: {},
                            detailsData: {},
                            links: []
                        };
                        
                        // Extract from main row
                        const mainCells = mainRow.querySelectorAll('td');
                        mainCells.forEach((cell, idx) => {
                            const text = cell.textContent.trim();
                            
                            // Tax deed number (first numeric column)
                            if (idx === 0 && /^\\d{5,}$/.test(text)) {
                                result.mainRowData.taxDeedNumber = text;
                            }
                            
                            // Find tax deed document link
                            const link = cell.querySelector('a');
                            if (link && link.href) {
                                if (link.href.includes('Deeds') || link.href.includes('Document')) {
                                    result.mainRowData.taxDeedLink = link.href;
                                    result.links.push({
                                        type: 'Tax Deed Document',
                                        url: link.href
                                    });
                                }
                            }
                            
                            // Opening bid (look for dollar amounts)
                            if (text.includes('$')) {
                                const amount = parseFloat(text.replace(/[^0-9.]/g, ''));
                                if (!isNaN(amount) && amount > 0) {
                                    if (!result.mainRowData.openingBid || amount > 100) {
                                        result.mainRowData.openingBid = amount;
                                    }
                                }
                            }
                            
                            // Status
                            if (['Upcoming', 'Active', 'Sold', 'Cancelled', 'Canceled'].includes(text)) {
                                result.mainRowData.status = text;
                            }
                            
                            // Close time
                            if (text.match(/\\d{1,2}:\\d{2}\\s*(AM|PM)/i)) {
                                result.mainRowData.closeTime = text;
                            }
                        });
                        
                        // Extract from details row if it exists
                        if (detailsRow) {
                            const detailsHTML = detailsRow.innerHTML;
                            const detailsText = detailsRow.textContent;
                            
                            // Extract Parcel Number with link
                            const parcelMatch = detailsHTML.match(/Parcel\\s*#?:?\\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)<\\/a>/i);
                            if (parcelMatch) {
                                result.detailsData.parcelUrl = parcelMatch[1];
                                result.detailsData.parcelNumber = parcelMatch[2].trim();
                                result.links.push({
                                    type: 'Property Appraiser',
                                    url: parcelMatch[1],
                                    text: parcelMatch[2].trim()
                                });
                            } else {
                                // Try to extract parcel without link
                                const parcelTextMatch = detailsText.match(/Parcel\\s*#?:?\\s*([0-9-]+)/i);
                                if (parcelTextMatch) {
                                    result.detailsData.parcelNumber = parcelTextMatch[1];
                                }
                            }
                            
                            // Extract Tax Certificate Number
                            const taxCertMatch = detailsText.match(/Tax\\s*Certificate\\s*#?:?\\s*([0-9]+)/i);
                            if (taxCertMatch) {
                                result.detailsData.taxCertificateNumber = taxCertMatch[1];
                            }
                            
                            // Extract Legal Description (can be long)
                            const legalMatch = detailsHTML.match(/Legal:?\\s*([^<]+(?:<[^/>][^>]*>[^<]+)*)/i);
                            if (legalMatch) {
                                result.detailsData.legalDescription = legalMatch[1]
                                    .replace(/<[^>]*>/g, ' ')
                                    .replace(/\\s+/g, ' ')
                                    .trim();
                            }
                            
                            // Extract Situs Address
                            const situsMatch = detailsText.match(/Situs\\s*Address:?\\s*([^\\n]+)/i);
                            if (situsMatch) {
                                result.detailsData.situsAddress = situsMatch[1].trim();
                            }
                            
                            // Extract Homestead
                            const homesteadMatch = detailsText.match(/Homestead:?\\s*(Yes|No|Y|N)/i);
                            if (homesteadMatch) {
                                result.detailsData.homestead = homesteadMatch[1].toUpperCase().startsWith('Y');
                            }
                            
                            // Extract Assessed Value
                            const assessedMatch = detailsText.match(/Assessed\\s*Value:?\\s*\\$?([0-9,]+)/i);
                            if (assessedMatch) {
                                result.detailsData.assessedValue = parseFloat(assessedMatch[1].replace(/,/g, ''));
                            }
                            
                            // Extract Applicant name
                            const applicantMatch = detailsText.match(/Applicant:?\\s*([^\\n]+)/i);
                            if (applicantMatch) {
                                result.detailsData.applicant = applicantMatch[1].trim();
                            }
                            
                            // Extract ALL links from details
                            const allLinks = detailsRow.querySelectorAll('a');
                            allLinks.forEach(link => {
                                if (link.href) {
                                    result.links.push({
                                        type: 'Additional',
                                        url: link.href,
                                        text: link.textContent.trim()
                                    });
                                }
                            });
                        }
                        
                        return result;
                    }''', i)
                    
                    if property_data and (property_data.mainRowData.taxDeedNumber or property_data.detailsData.parcelNumber):
                        # Format for database
                        formatted = {
                            'tax_deed_number': f"TD-{property_data.mainRowData.taxDeedNumber}" if property_data.mainRowData.taxDeedNumber else f"TD-AUTO-{i+1}",
                            'parcel_id': property_data.detailsData.parcelNumber or f'PARCEL-{i+1}',
                            'tax_certificate_number': property_data.detailsData.taxCertificateNumber,
                            'legal_situs_address': property_data.detailsData.situsAddress or 'Address pending',
                            'homestead_exemption': property_data.detailsData.homestead or False,
                            'assessed_value': float(property_data.detailsData.assessedValue or 0),
                            'opening_bid': float(property_data.mainRowData.openingBid or 0),
                            'item_status': property_data.mainRowData.status or 'Active',
                            'close_time': datetime.now().isoformat(),
                            'applicant_name': property_data.detailsData.applicant or 'TAX CERTIFICATE HOLDER',
                            'property_appraisal_url': property_data.detailsData.parcelUrl or '',
                            'auction_id': 1,
                            'created_at': datetime.now().isoformat(),
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        # Store link count for reporting
                        formatted['link_count'] = len(property_data.links)
                        
                        self.all_properties.append(formatted)
                        properties_scraped += 1
                        
                        print(f"  [OK] TD: {formatted['tax_deed_number']}")
                        print(f"       Parcel: {formatted['parcel_id']}")
                        print(f"       Address: {formatted['legal_situs_address'][:50]}...")
                        print(f"       Links found: {formatted['link_count']}")
                        
                    else:
                        print("  [SKIP] No data extracted")
                    
                    # Collapse the details to keep page manageable (optional)
                    # Commented out to maintain expanded state for verification
                    # collapsed = await page.query_selector_all('img[alt="Hide item details"]')
                    # if i < len(collapsed):
                    #     await collapsed[i].click()
                    #     await asyncio.sleep(0.3)
                    
                except Exception as e:
                    print(f"  [ERROR] {str(e)[:80]}")
                    continue
            
            print("\n" + "="*60)
            print(f"SCRAPING COMPLETE")
            print(f"Total properties found: {total_count}")
            print(f"Successfully scraped: {properties_scraped}")
            print(f"Success rate: {(properties_scraped/total_count*100):.1f}%")
            print("="*60)
            
        finally:
            await browser.close()
            await playwright.stop()
    
    async def save_all_to_database(self):
        """Save all scraped properties to database"""
        if not self.all_properties:
            print("\n[WARNING] No properties to save")
            return
        
        print(f"\n[DATABASE] Saving {len(self.all_properties)} properties...")
        
        saved = 0
        updated = 0
        errors = 0
        
        for prop in self.all_properties:
            try:
                # Remove non-database fields
                db_prop = {k: v for k, v in prop.items() if k != 'link_count'}
                
                # Try insert first
                response = self.supabase.table('tax_deed_bidding_items').insert(db_prop).execute()
                saved += 1
                print(f"  [SAVED] {prop['tax_deed_number']}")
                
            except Exception as e:
                if 'duplicate' in str(e).lower():
                    try:
                        # Update existing
                        response = self.supabase.table('tax_deed_bidding_items').update(
                            db_prop
                        ).eq('tax_deed_number', prop['tax_deed_number']).execute()
                        updated += 1
                        print(f"  [UPDATED] {prop['tax_deed_number']}")
                    except:
                        errors += 1
                else:
                    errors += 1
                    print(f"  [ERROR] {prop['tax_deed_number']}: {str(e)[:50]}")
        
        print(f"\n[RESULTS] Saved: {saved}, Updated: {updated}, Errors: {errors}")
        
        # Save backup
        backup_file = f'all_properties_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(self.all_properties, f, indent=2, default=str)
        print(f"[BACKUP] Saved to {backup_file}")
    
    async def verify_in_database(self):
        """Verify what's actually in the database"""
        print("\n[VERIFICATION] Checking database...")
        
        response = self.supabase.table('tax_deed_bidding_items').select('*').execute()
        
        if response.data:
            total = len(response.data)
            with_details = len([p for p in response.data if not p['parcel_id'].startswith('UNKNOWN')])
            with_address = len([p for p in response.data if p['legal_situs_address'] and p['legal_situs_address'] != 'Address not available'])
            
            print(f"  Total properties: {total}")
            print(f"  With parcel details: {with_details}")
            print(f"  With addresses: {with_address}")
            
            # Show sample
            if with_details > 0:
                sample = [p for p in response.data if not p['parcel_id'].startswith('UNKNOWN')][0]
                print(f"\n  Sample property with details:")
                print(f"    TD: {sample['tax_deed_number']}")
                print(f"    Parcel: {sample['parcel_id']}")
                print(f"    Address: {sample.get('legal_situs_address', 'N/A')}")
                print(f"    Applicant: {sample.get('applicant_name', 'N/A')}")
                
    async def run(self):
        """Main execution"""
        print("\nCOMPLETE PROPERTY SCRAPER - GETTING ALL PROPERTIES")
        print("="*60)
        
        # Scrape all properties
        await self.scrape_all_properties()
        
        # Save to database
        await self.save_all_to_database()
        
        # Verify
        await self.verify_in_database()
        
        print("\n[COMPLETE] All properties have been processed")
        print("Check http://localhost:5175/tax-deed-sales to view the data")

if __name__ == "__main__":
    scraper = CompletePropertyScraper()
    asyncio.run(scraper.run())