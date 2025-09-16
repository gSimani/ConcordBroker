"""
Complete Tax Deed Scraper - Clicks expand buttons and extracts ALL details
Including embedded hyperlinks, parcel numbers, legal descriptions, etc.
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

class CompleteDetailsScraper:
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
            headless=False,  # Keep visible to see the scraping
            args=['--disable-blink-features=AutomationControlled'],
            slow_mo=500  # Slow down actions to ensure page loads
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()
        
    async def scrape_auction_complete(self, url, auction_name):
        """Scrape auction by clicking each expand button to get full details"""
        print(f"\n{'='*60}")
        print(f"Processing: {auction_name}")
        print(f"URL: {url}")
        print('='*60)
        
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        properties = []
        
        # First, count how many expand buttons we have
        expand_buttons = await self.page.query_selector_all('img[alt="Show item details"], img[alt="Hide item details"]')
        total_properties = len(expand_buttons)
        print(f"\nFound {total_properties} properties to process")
        
        # Process each property by clicking its expand button
        for i in range(min(total_properties, 30)):  # Limit to 30 for testing
            try:
                print(f"\n{'='*40}")
                print(f"Property {i+1}/{total_properties}:")
                
                # Re-query buttons as DOM changes after each click
                current_buttons = await self.page.query_selector_all('img[alt="Show item details"], img[alt="Hide item details"]')
                
                if i >= len(current_buttons):
                    print("  No more buttons found")
                    break
                
                button = current_buttons[i]
                
                # Check if we need to expand (alt="Show item details") or already expanded
                alt_text = await button.get_attribute('alt')
                
                if alt_text == "Show item details":
                    print("  Clicking to expand property details...")
                    await button.click()
                    await asyncio.sleep(1.5)  # Wait for expansion
                else:
                    print("  Property already expanded")
                
                # Now extract the detailed information
                property_data = await self.extract_expanded_details(i)
                
                if property_data:
                    properties.append(property_data)
                    print(f"  [SUCCESS] Extracted complete details")
                    self.print_property_summary(property_data)
                else:
                    print("  [WARNING] Could not extract details")
                
                # Optionally collapse to keep page clean (comment out if not needed)
                # current_buttons = await self.page.query_selector_all('img[alt="Hide item details"]')
                # if i < len(current_buttons):
                #     await current_buttons[i].click()
                #     await asyncio.sleep(0.5)
                    
            except Exception as e:
                print(f"  [ERROR] {str(e)[:100]}")
                continue
        
        print(f"\n{'='*60}")
        print(f"Total extracted: {len(properties)} properties with complete details")
        return properties
        
    async def extract_expanded_details(self, index):
        """Extract all details from the expanded property view"""
        
        # Use JavaScript to extract all the detailed information
        property_data = await self.page.evaluate('''(index) => {
            // Find all table rows
            const allRows = document.querySelectorAll('table tbody tr');
            
            // Find the main row (not details row)
            let mainRow = null;
            let detailsRow = null;
            let rowCounter = 0;
            
            for (let row of allRows) {
                // Skip header rows
                if (row.querySelector('th')) continue;
                
                // Check if this is a details row
                if (row.classList.contains('details') || row.querySelector('.details')) {
                    detailsRow = row;
                } else if (row.querySelector('img[alt*="item details"]')) {
                    if (rowCounter === index) {
                        mainRow = row;
                        // The details row should be the next sibling
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
            
            const result = {};
            
            // Extract from main row
            const mainCells = mainRow.querySelectorAll('td');
            mainCells.forEach((cell, idx) => {
                const text = cell.textContent.trim();
                
                // Tax deed number
                if (/^\\d{5,}$/.test(text)) {
                    result.taxDeedNumber = text;
                }
                
                // Find links in main row
                const link = cell.querySelector('a');
                if (link && link.href.includes('Deeds')) {
                    result.taxDeedLink = link.href;
                }
                
                // Opening bid
                if (text.includes('$')) {
                    const amount = parseFloat(text.replace(/[^0-9.]/g, ''));
                    if (!result.openingBid) {
                        result.openingBid = amount;
                    }
                }
                
                // Status
                if (['Upcoming', 'Active', 'Sold', 'Cancelled', 'Canceled'].includes(text)) {
                    result.status = text;
                }
                
                // Close time
                if (text.includes('AM') || text.includes('PM')) {
                    result.closeTime = text;
                }
            });
            
            // Extract from details row if it exists
            if (detailsRow) {
                const detailsContent = detailsRow.innerHTML;
                const detailsText = detailsRow.textContent;
                
                // Extract Parcel Number with link
                const parcelMatch = detailsContent.match(/Parcel #:.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)<\\/a>/i);
                if (parcelMatch) {
                    result.parcelUrl = parcelMatch[1];
                    result.parcelNumber = parcelMatch[2].trim();
                } else {
                    // Try alternative pattern
                    const parcelTextMatch = detailsText.match(/Parcel #?:?\\s*([0-9-]+)/i);
                    if (parcelTextMatch) {
                        result.parcelNumber = parcelTextMatch[1];
                    }
                }
                
                // Extract Tax Certificate Number
                const taxCertMatch = detailsText.match(/Tax Certificate #?:?\\s*([0-9]+)/i);
                if (taxCertMatch) {
                    result.taxCertificateNumber = taxCertMatch[1];
                }
                
                // Extract Legal Description
                const legalMatch = detailsContent.match(/Legal:.*?<td[^>]*class="value"[^>]*>([^<]+(?:<[^/]|[^<])*?)<\\/td>/is);
                if (legalMatch) {
                    result.legalDescription = legalMatch[1].replace(/<[^>]*>/g, ' ').replace(/\\s+/g, ' ').trim();
                }
                
                // Extract Situs Address
                const situsMatch = detailsText.match(/Situs Address:?\\s*([^\\n]+)/i);
                if (situsMatch) {
                    result.situsAddress = situsMatch[1].trim();
                }
                
                // Extract Homestead
                const homesteadMatch = detailsText.match(/Homestead:?\\s*(Yes|No|Y|N)/i);
                if (homesteadMatch) {
                    result.homestead = homesteadMatch[1].toUpperCase().startsWith('Y') ? 'Y' : 'N';
                }
                
                // Extract Assessed Value
                const assessedMatch = detailsText.match(/Assessed Value:?\\s*\\$?([0-9,]+)/i);
                if (assessedMatch) {
                    result.assessedValue = parseFloat(assessedMatch[1].replace(/,/g, ''));
                }
                
                // Extract Applicant (for Sunbiz matching)
                const applicantMatch = detailsText.match(/Applicant:?\\s*([^\\n]+)/i);
                if (applicantMatch) {
                    result.applicant = applicantMatch[1].trim();
                }
                
                // Extract all links from details
                const allLinks = detailsRow.querySelectorAll('a');
                result.additionalLinks = [];
                allLinks.forEach(link => {
                    result.additionalLinks.push({
                        text: link.textContent.trim(),
                        href: link.href
                    });
                });
            }
            
            return result;
        }''', index)
        
        if not property_data:
            return None
        
        # Format for database
        formatted_data = {
            'tax_deed_number': f"TD-{property_data.get('taxDeedNumber')}" if property_data.get('taxDeedNumber') else f"TD-AUTO-{index+1}",
            'parcel_id': property_data.get('parcelNumber', f'UNKNOWN-{index+1}'),
            'tax_certificate_number': property_data.get('taxCertificateNumber'),
            'legal_situs_address': property_data.get('situsAddress', 'Address not available'),
            'legal_description': property_data.get('legalDescription'),
            'homestead_exemption': property_data.get('homestead', 'N'),
            'assessed_value': float(property_data.get('assessedValue', 0)),
            'opening_bid': float(property_data.get('openingBid', 0)),
            'item_status': property_data.get('status', 'Active'),
            'close_time': datetime.now().isoformat(),  # Convert time string later
            'applicant_name': property_data.get('applicant', 'TAX CERTIFICATE HOLDER'),
            'property_appraisal_url': property_data.get('parcelUrl', ''),
            'tax_deed_document_url': property_data.get('taxDeedLink', ''),
            'auction_id': 1,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'soh_value': 0,
            'total_taxes_owed': 0,
            'tax_years_included': '',
            'total_bids': 0,
            'unique_bidders': 0
        }
        
        # Store additional links as JSON string
        if property_data.get('additionalLinks'):
            formatted_data['additional_links_json'] = json.dumps(property_data['additionalLinks'])
        
        return formatted_data
        
    def print_property_summary(self, prop):
        """Print a summary of extracted property data"""
        print(f"    Tax Deed: {prop.get('tax_deed_number')}")
        print(f"    Parcel: {prop.get('parcel_id')}")
        print(f"    Address: {prop.get('legal_situs_address', 'N/A')[:50]}...")
        print(f"    Applicant: {prop.get('applicant_name', 'N/A')[:50]}...")
        print(f"    Opening Bid: ${prop.get('opening_bid', 0):,.2f}")
        print(f"    Homestead: {prop.get('homestead_exemption')}")
        if prop.get('property_appraisal_url'):
            print(f"    Appraisal URL: {prop['property_appraisal_url'][:60]}...")
            
    async def check_sunbiz_match(self, applicant_name):
        """Check if applicant exists in Sunbiz database"""
        if not applicant_name or applicant_name == 'TAX CERTIFICATE HOLDER':
            return False
            
        try:
            # Query Sunbiz entities table for matching names
            response = self.supabase.table('sunbiz_entities').select('*').ilike('entity_name', f'%{applicant_name}%').limit(1).execute()
            if response.data and len(response.data) > 0:
                return True
        except:
            pass
        return False
        
    async def save_to_database(self):
        """Save properties to database"""
        if not self.all_properties:
            print("\nNo properties to save")
            return
            
        print(f"\n{'='*60}")
        print(f"Saving {len(self.all_properties)} properties to database...")
        print('='*60)
        
        success = 0
        updated = 0
        
        for prop in self.all_properties:
            try:
                # Check for Sunbiz match
                if await self.check_sunbiz_match(prop.get('applicant_name')):
                    prop['sunbiz_matched'] = True
                    print(f"  [SUNBIZ MATCH] {prop['applicant_name']}")
                
                # Remove fields that don't exist in table
                safe_prop = {k: v for k, v in prop.items() 
                           if k not in ['additional_links_json', 'legal_description', 'tax_deed_document_url', 'sunbiz_matched'] 
                           and v is not None}
                
                # Try to insert
                response = self.supabase.table('tax_deed_bidding_items').insert(safe_prop).execute()
                success += 1
                print(f"  [SAVED] {prop['tax_deed_number']}")
                
            except Exception as e:
                if 'duplicate' in str(e):
                    try:
                        # Update existing record
                        response = self.supabase.table('tax_deed_bidding_items').update(
                            safe_prop
                        ).eq('tax_deed_number', prop['tax_deed_number']).execute()
                        updated += 1
                        print(f"  [UPDATED] {prop['tax_deed_number']}")
                    except:
                        print(f"  [SKIPPED] {prop['tax_deed_number']}")
                else:
                    print(f"  [ERROR] {prop['tax_deed_number']}: {str(e)[:50]}")
        
        print(f"\nResults: {success} saved, {updated} updated")
        
        # Save complete backup
        backup_file = f'complete_tax_deed_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w') as f:
            json.dump(self.all_properties, f, indent=2, default=str)
        print(f"Complete backup saved to: {backup_file}")
        
    async def run(self):
        """Main execution"""
        try:
            await self.initialize_browser()
            
            # Scrape the main auction
            properties = await self.scrape_auction_complete(
                'https://broward.deedauction.net/auction/110',
                '9/17/2025 Tax Deed Sale'
            )
            self.all_properties.extend(properties)
            
            # Save to database
            await self.save_to_database()
            
            # Summary
            print("\n" + "="*60)
            print("COMPLETE DETAIL EXTRACTION FINISHED")
            print("="*60)
            print(f"Total properties with full details: {len(self.all_properties)}")
            
            if self.all_properties:
                # Count by status
                status_counts = {}
                for prop in self.all_properties:
                    status = prop.get('item_status', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print("\nProperties by status:")
                for status, count in status_counts.items():
                    print(f"  {status}: {count}")
                
                # Show sample
                print("\nSample property with full details:")
                if self.all_properties:
                    sample = self.all_properties[0]
                    print(json.dumps(sample, indent=2, default=str)[:500] + "...")
            
            print("\n[SUCCESS] Data extracted with all embedded links and details!")
            print("View at: http://localhost:5174/tax-deed-sales")
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()

if __name__ == "__main__":
    print("Complete Tax Deed Detail Scraper")
    print("="*60)
    print("This scraper:")
    print("  1. Clicks on each expand button (plus sign)")
    print("  2. Extracts ALL detailed fields including:")
    print("     - Parcel # with embedded URL")
    print("     - Tax Certificate #")
    print("     - Legal description")
    print("     - Situs Address")
    print("     - Homestead status")
    print("     - Assessed Value")
    print("     - Applicant name (for Sunbiz matching)")
    print("     - All embedded hyperlinks")
    print("="*60)
    
    scraper = CompleteDetailsScraper()
    asyncio.run(scraper.run())