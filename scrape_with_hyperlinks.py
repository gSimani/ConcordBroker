"""
Tax Deed Scraper - Extracts hyperlinks and expands properties for full details
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

class HyperlinkPropertyScraper:
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
        
    async def scrape_auction_with_links(self, url, name):
        """Scrape auction extracting all hyperlinks and expanding properties"""
        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"URL: {url}")
        print('='*60)
        
        await self.page.goto(url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        properties = []
        
        # First, extract all property data including hyperlinks
        print("\nExtracting property rows with hyperlinks...")
        
        property_data_list = await self.page.evaluate('''() => {
            const results = [];
            
            // Find all table rows that likely contain property data
            const rows = document.querySelectorAll('table tbody tr');
            
            rows.forEach((row, rowIndex) => {
                // Skip if this is a details row
                if (row.classList.contains('details') || row.style.display === 'none') {
                    return;
                }
                
                const cells = row.querySelectorAll('td');
                if (cells.length < 3) return; // Skip rows with too few cells
                
                const rowData = {
                    rowIndex: rowIndex,
                    cellData: [],
                    links: [],
                    hasExpandButton: false
                };
                
                // Check for expand/collapse button
                const expandImg = row.querySelector('img[src*="expand"], img[src*="collapse"]');
                if (expandImg) {
                    rowData.hasExpandButton = true;
                    rowData.expandState = expandImg.src.includes('collapse') ? 'expanded' : 'collapsed';
                }
                
                // Extract data from each cell
                cells.forEach((cell, cellIndex) => {
                    const cellInfo = {
                        text: cell.textContent.trim(),
                        links: []
                    };
                    
                    // Find all hyperlinks in this cell
                    const links = cell.querySelectorAll('a');
                    links.forEach(link => {
                        const linkInfo = {
                            text: link.textContent.trim(),
                            href: link.href,
                            title: link.title || '',
                            target: link.target || ''
                        };
                        
                        // Identify link type based on URL or text
                        if (link.href.includes('parcel') || link.href.includes('property')) {
                            linkInfo.type = 'property';
                        } else if (link.href.includes('tax')) {
                            linkInfo.type = 'tax';
                        } else if (link.href.includes('appraiser')) {
                            linkInfo.type = 'appraiser';
                        } else if (link.href.includes('deed')) {
                            linkInfo.type = 'deed';
                        } else {
                            linkInfo.type = 'other';
                        }
                        
                        cellInfo.links.push(linkInfo);
                        rowData.links.push(linkInfo);
                    });
                    
                    rowData.cellData.push(cellInfo);
                });
                
                // Try to identify what type of data is in each cell
                rowData.cellData.forEach((cell, index) => {
                    const text = cell.text;
                    
                    // Tax deed number (numeric only)
                    if (/^\\d{5,}$/.test(text)) {
                        rowData.taxDeedNumber = 'TD-' + text;
                    }
                    
                    // Parcel number (could be in link text)
                    if (cell.links.length > 0 && cell.links[0].type === 'property') {
                        rowData.parcelId = cell.links[0].text;
                        rowData.parcelUrl = cell.links[0].href;
                    }
                    
                    // Money values
                    if (text.includes('$')) {
                        const value = parseFloat(text.replace(/[^0-9.]/g, ''));
                        if (!rowData.openingBid && value > 0) {
                            rowData.openingBid = value;
                        } else if (!rowData.currentBid && value > 0) {
                            rowData.currentBid = value;
                        }
                    }
                    
                    // Status
                    if (['Upcoming', 'Active', 'Sold', 'Cancelled', 'Canceled'].includes(text)) {
                        rowData.status = text;
                    }
                    
                    // Time
                    if (text.includes('AM') || text.includes('PM')) {
                        rowData.closeTime = text;
                    }
                });
                
                // Only include rows that look like property rows
                if (rowData.taxDeedNumber || rowData.parcelId || rowData.links.length > 0) {
                    results.push(rowData);
                }
            });
            
            return results;
        }''')
        
        print(f"Found {len(property_data_list)} property rows")
        
        # Process each property row
        for i, row_data in enumerate(property_data_list[:30]):  # Limit to first 30
            try:
                print(f"\n  Property {i+1}:")
                
                # Display basic info
                if row_data.get('taxDeedNumber'):
                    print(f"    Tax Deed: {row_data['taxDeedNumber']}")
                if row_data.get('parcelId'):
                    print(f"    Parcel: {row_data['parcelId']}")
                if row_data.get('openingBid'):
                    print(f"    Opening Bid: ${row_data['openingBid']:,.2f}")
                
                # Display links found
                if row_data.get('links'):
                    print(f"    Links found: {len(row_data['links'])}")
                    for link in row_data['links'][:3]:  # Show first 3 links
                        print(f"      - {link['type']}: {link['text'][:30]}... -> {link['href'][:50]}...")
                
                # If row has expand button, click it to get more details
                if row_data.get('hasExpandButton'):
                    print(f"    Has expand button (currently {row_data.get('expandState', 'unknown')})")
                    
                    if row_data.get('expandState') == 'collapsed':
                        # Find and click the expand button
                        expand_buttons = await self.page.query_selector_all('img[src*="expand"]')
                        if len(expand_buttons) > 0:
                            # Find the right button for this row
                            for button in expand_buttons:
                                button_row = await button.evaluate('(el) => el.closest("tr").rowIndex')
                                if button_row and abs(button_row - row_data['rowIndex']) <= 1:
                                    print("    Clicking to expand...")
                                    await button.click()
                                    await asyncio.sleep(1)
                                    
                                    # Extract expanded details
                                    expanded_data = await self.page.evaluate(f'''(rowIndex) => {{
                                        const rows = document.querySelectorAll('table tbody tr');
                                        const targetRow = rows[rowIndex];
                                        if (!targetRow) return null;
                                        
                                        // Look for details in next row
                                        const nextRow = targetRow.nextElementSibling;
                                        if (!nextRow || !nextRow.classList.contains('details')) {{
                                            // Try to find details within current row
                                            const details = targetRow.querySelector('.details');
                                            if (details) {{
                                                return {{text: details.textContent, html: details.innerHTML}};
                                            }}
                                            return null;
                                        }}
                                        
                                        const detailsText = nextRow.textContent || '';
                                        const detailsHtml = nextRow.innerHTML || '';
                                        
                                        const data = {{text: detailsText, html: detailsHtml}};
                                        
                                        // Extract specific fields
                                        const addressMatch = detailsText.match(/Situs Address[: ]+([^\\n]+)/i);
                                        if (addressMatch) data.address = addressMatch[1].trim();
                                        
                                        const legalMatch = detailsText.match(/Legal[: ]+([^\\n]+)/i);
                                        if (legalMatch) data.legal = legalMatch[1].trim();
                                        
                                        const ownerMatch = detailsText.match(/Owner[: ]+([^\\n]+)/i);
                                        if (ownerMatch) data.owner = ownerMatch[1].trim();
                                        
                                        const assessedMatch = detailsText.match(/Assessed Value[: ]+[$]?([0-9,]+)/i);
                                        if (assessedMatch) data.assessedValue = parseFloat(assessedMatch[1].replace(/,/g, ''));
                                        
                                        // Extract any additional links from details
                                        const detailLinks = [];
                                        const linkElements = nextRow.querySelectorAll('a');
                                        linkElements.forEach(link => {{
                                            detailLinks.push({{
                                                text: link.textContent.trim(),
                                                href: link.href,
                                                type: link.href.includes('appraiser') ? 'appraiser' : 
                                                      link.href.includes('tax') ? 'tax' : 'other'
                                            }});
                                        }});
                                        data.links = detailLinks;
                                        
                                        return data;
                                    }}''', row_data['rowIndex'])
                                    
                                    if expanded_data:
                                        print("    [OK] Extracted expanded details")
                                        if expanded_data.get('address'):
                                            print(f"      Address: {expanded_data['address'][:50]}...")
                                        if expanded_data.get('owner'):
                                            print(f"      Owner: {expanded_data['owner']}")
                                        if expanded_data.get('assessedValue'):
                                            print(f"      Assessed: ${expanded_data['assessedValue']:,.2f}")
                                        if expanded_data.get('links'):
                                            print(f"      Additional links: {len(expanded_data['links'])}")
                                        
                                        # Merge expanded data with row data
                                        row_data.update(expanded_data)
                                    
                                    break
                
                # Create property record
                property_record = {
                    'tax_deed_number': row_data.get('taxDeedNumber', f'TD-AUTO-{i+1}'),
                    'parcel_id': row_data.get('parcelId', f'UNKNOWN-{i+1}'),
                    'legal_situs_address': row_data.get('address', row_data.get('legal', 'Address not available')),
                    'opening_bid': float(row_data.get('openingBid', 0)),
                    'current_bid': float(row_data.get('currentBid')) if row_data.get('currentBid') else None,
                    'item_status': row_data.get('status', 'Active'),
                    'applicant_name': row_data.get('owner', 'TAX CERTIFICATE HOLDER'),
                    'assessed_value': float(row_data.get('assessedValue', 0)),
                    'property_appraisal_url': row_data.get('parcelUrl', ''),
                    'close_time': datetime.now().isoformat(),
                    'auction_id': 1,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Add to list if it has meaningful data
                if row_data.get('taxDeedNumber') or row_data.get('parcelId') or len(row_data.get('links', [])) > 0:
                    properties.append(property_record)
                    
                    # Store the hyperlinks separately for reference
                    if row_data.get('links'):
                        property_record['extracted_links'] = json.dumps(row_data['links'][:5])  # Store first 5 links as JSON
                    
            except Exception as e:
                print(f"    [ERROR] Processing property {i+1}: {str(e)[:100]}")
                continue
        
        print(f"\n  Total extracted: {len(properties)} properties with hyperlinks")
        return properties
        
    async def run(self):
        """Main execution"""
        try:
            await self.initialize_browser()
            
            # Scrape first auction
            properties = await self.scrape_auction_with_links(
                'https://broward.deedauction.net/auction/110',
                '9/17/2025 Tax Deed Sale'
            )
            self.all_properties.extend(properties)
            
            # Try another auction if needed
            if len(properties) < 10:
                print("\nTrying another auction...")
                properties2 = await self.scrape_auction_with_links(
                    'https://broward.deedauction.net/auction/111',
                    '10/15/2025 Tax Deed Sale'
                )
                self.all_properties.extend(properties2)
            
            # Save results
            if self.all_properties:
                await self.save_to_database()
                
                # Save detailed backup with all links
                backup_file = f'tax_deed_with_links_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(backup_file, 'w') as f:
                    json.dump(self.all_properties, f, indent=2, default=str)
                print(f"\nDetailed backup saved to: {backup_file}")
            
            # Summary
            print("\n" + "="*60)
            print("HYPERLINK EXTRACTION COMPLETE")
            print("="*60)
            print(f"Total properties processed: {len(self.all_properties)}")
            
            if self.all_properties:
                print("\nSample properties with links:")
                for prop in self.all_properties[:3]:
                    print(f"\n  {prop['tax_deed_number']}:")
                    print(f"    Address: {prop['legal_situs_address'][:50]}...")
                    print(f"    Parcel: {prop['parcel_id']}")
                    if prop.get('property_appraisal_url'):
                        print(f"    Appraisal URL: {prop['property_appraisal_url'][:60]}...")
                    if prop.get('extracted_links'):
                        links = json.loads(prop['extracted_links'])
                        print(f"    Extracted {len(links)} hyperlinks")
            
            print("\n[OK] Data available at: http://localhost:5173/tax-deed-sales")
            
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
        print(f"\nSaving {len(self.all_properties)} properties with hyperlinks...")
        
        success = 0
        for prop in self.all_properties:
            try:
                # Remove fields that don't exist in table
                safe_prop = {k: v for k, v in prop.items() 
                           if k not in ['extracted_links'] and v is not None}
                
                # Ensure URL fields are not too long
                if safe_prop.get('property_appraisal_url') and len(safe_prop['property_appraisal_url']) > 500:
                    safe_prop['property_appraisal_url'] = safe_prop['property_appraisal_url'][:500]
                
                response = self.supabase.table('tax_deed_bidding_items').insert(safe_prop).execute()
                success += 1
                print(f"  [SAVED] {prop['tax_deed_number']}")
                
            except Exception as e:
                if 'duplicate' in str(e):
                    # Try to update with new hyperlink data
                    try:
                        response = self.supabase.table('tax_deed_bidding_items').update(
                            safe_prop
                        ).eq('tax_deed_number', prop['tax_deed_number']).execute()
                        print(f"  [UPDATED] {prop['tax_deed_number']} with new links")
                        success += 1
                    except:
                        print(f"  - Skipped: {prop['tax_deed_number']} (exists)")
                else:
                    print(f"  [ERROR] {prop['tax_deed_number']} - {str(e)[:50]}")
        
        print(f"\nSuccessfully saved/updated {success} properties with hyperlinks")

if __name__ == "__main__":
    print("Tax Deed Scraper with Hyperlink Extraction")
    print("="*60)
    print("Extracts all embedded hyperlinks and expands properties for details")
    print("="*60)
    
    scraper = HyperlinkPropertyScraper()
    asyncio.run(scraper.run())