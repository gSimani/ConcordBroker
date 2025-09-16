"""
Comprehensive Tax Deed Data Validator
Compares live website data with Supabase database using Playwright
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

class ComprehensiveValidator:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.source_properties = []
        self.database_properties = []
        self.comparison_results = {
            'timestamp': datetime.now().isoformat(),
            'source_properties': [],
            'database_properties': [],
            'perfect_matches': [],
            'partial_matches': [],
            'missing_from_database': [],
            'extra_in_database': [],
            'field_mismatches': [],
            'accuracy_metrics': {}
        }
        
    async def scrape_source_website(self):
        """Scrape ALL properties from the source website"""
        print("\n[STEP 1] SCRAPING SOURCE WEBSITE")
        print("="*60)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=200
        )
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            url = 'https://broward.deedauction.net/auction/110'
            print(f"Navigating to: {url}")
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Count total expand buttons
            expand_buttons = await page.query_selector_all('img[alt="Show item details"], img[alt="Hide item details"]')
            total_properties = len(expand_buttons)
            print(f"Found {total_properties} properties to process")
            
            # Click each expand button and extract data
            for i in range(min(total_properties, 50)):  # Process up to 50
                try:
                    print(f"\nProcessing property {i+1}/{total_properties}...")
                    
                    # Re-query buttons
                    current_buttons = await page.query_selector_all('img[alt="Show item details"], img[alt="Hide item details"]')
                    if i >= len(current_buttons):
                        break
                    
                    button = current_buttons[i]
                    alt_text = await button.get_attribute('alt')
                    
                    # Expand if needed
                    if alt_text == "Show item details":
                        await button.click()
                        await asyncio.sleep(0.5)
                    
                    # Extract data using JavaScript
                    property_data = await page.evaluate(f'''() => {{
                        const rows = document.querySelectorAll('table tbody tr');
                        let mainRow = null;
                        let detailsRow = null;
                        let rowIndex = 0;
                        
                        // Find the correct row pair
                        for (let row of rows) {{
                            if (row.querySelector('th')) continue;
                            
                            if (row.querySelector('img[alt*="item details"]')) {{
                                if (rowIndex === {i}) {{
                                    mainRow = row;
                                    // Check next row for details
                                    let next = row.nextElementSibling;
                                    if (next && (next.classList.contains('details') || next.querySelector('.details'))) {{
                                        detailsRow = next;
                                    }}
                                    break;
                                }}
                                rowIndex++;
                            }}
                        }}
                        
                        if (!mainRow) return null;
                        
                        const result = {{
                            taxDeedNumber: '',
                            parcelNumber: '',
                            address: '',
                            openingBid: 0,
                            status: 'Unknown',
                            applicant: ''
                        }};
                        
                        // Extract from main row
                        const cells = mainRow.querySelectorAll('td');
                        cells.forEach((cell, idx) => {{
                            const text = cell.textContent.trim();
                            
                            // Tax deed number (usually first cell with numbers)
                            if (idx === 0 && /\\d{{5,}}/.test(text)) {{
                                result.taxDeedNumber = text;
                            }}
                            
                            // Opening bid
                            if (text.includes('$')) {{
                                const amount = parseFloat(text.replace(/[^0-9.]/g, ''));
                                if (amount > 0 && !result.openingBid) {{
                                    result.openingBid = amount;
                                }}
                            }}
                            
                            // Status
                            if (['Upcoming', 'Active', 'Sold', 'Cancelled', 'Canceled'].includes(text)) {{
                                result.status = text;
                            }}
                        }});
                        
                        // Extract from details row if exists
                        if (detailsRow) {{
                            const detailsText = detailsRow.textContent;
                            const detailsHTML = detailsRow.innerHTML;
                            
                            // Parcel number
                            const parcelMatch = detailsText.match(/Parcel\\s*#?:?\\s*([0-9-]+)/i);
                            if (parcelMatch) {{
                                result.parcelNumber = parcelMatch[1];
                            }}
                            
                            // Address
                            const addressMatch = detailsText.match(/Situs\\s*Address:?\\s*([^\\n]+)/i);
                            if (addressMatch) {{
                                result.address = addressMatch[1].trim();
                            }}
                            
                            // Applicant
                            const applicantMatch = detailsText.match(/Applicant:?\\s*([^\\n]+)/i);
                            if (applicantMatch) {{
                                result.applicant = applicantMatch[1].trim();
                            }}
                        }}
                        
                        return result;
                    }}''')
                    
                    if property_data:
                        self.source_properties.append(property_data)
                        print(f"  Extracted: TD-{property_data.get('taxDeedNumber', 'N/A')} - ${property_data.get('openingBid', 0):,.2f}")
                    
                except Exception as e:
                    print(f"  Error: {str(e)[:50]}")
                    continue
            
            print(f"\n[COMPLETE] Scraped {len(self.source_properties)} properties from source")
            
        finally:
            await browser.close()
            await playwright.stop()
    
    def fetch_database_properties(self):
        """Fetch all properties from Supabase database"""
        print("\n[STEP 2] FETCHING DATABASE PROPERTIES")
        print("="*60)
        
        response = self.supabase.table('tax_deed_bidding_items').select('*').execute()
        
        if response.data:
            self.database_properties = response.data
            print(f"Fetched {len(self.database_properties)} properties from database")
            
            # Count by status
            status_counts = {}
            for prop in self.database_properties:
                status = prop.get('item_status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print("\nDatabase properties by status:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
    
    def compare_properties(self):
        """Compare source and database properties"""
        print("\n[STEP 3] COMPARING PROPERTIES")
        print("="*60)
        
        # Create lookup dictionaries
        source_by_td = {p['taxDeedNumber']: p for p in self.source_properties if p.get('taxDeedNumber')}
        db_by_td = {}
        for p in self.database_properties:
            td_num = p['tax_deed_number']
            if td_num and td_num.startswith('TD-'):
                td_num = td_num.replace('TD-', '')
            if td_num:
                db_by_td[td_num] = p
        
        # Find perfect matches
        for td_num, source_prop in source_by_td.items():
            if td_num in db_by_td:
                db_prop = db_by_td[td_num]
                
                # Check if fields match
                bid_match = abs(source_prop['openingBid'] - db_prop.get('opening_bid', 0)) < 1
                status_match = source_prop['status'] == db_prop.get('item_status', '')
                
                if bid_match and status_match:
                    self.comparison_results['perfect_matches'].append({
                        'tax_deed_number': td_num,
                        'opening_bid': source_prop['openingBid']
                    })
                else:
                    self.comparison_results['field_mismatches'].append({
                        'tax_deed_number': td_num,
                        'source_bid': source_prop['openingBid'],
                        'db_bid': db_prop.get('opening_bid', 0),
                        'source_status': source_prop['status'],
                        'db_status': db_prop.get('item_status', '')
                    })
        
        # Find missing from database
        for td_num in source_by_td:
            if td_num not in db_by_td:
                self.comparison_results['missing_from_database'].append(source_by_td[td_num])
        
        # Find extra in database (only Active/Upcoming)
        active_db_tds = {td for td, p in db_by_td.items() if p.get('item_status') in ['Active', 'Upcoming']}
        for td_num in active_db_tds:
            if td_num not in source_by_td:
                self.comparison_results['extra_in_database'].append({
                    'tax_deed_number': td_num,
                    'status': db_by_td[td_num].get('item_status')
                })
        
        # Calculate metrics
        total_source = len(self.source_properties)
        total_db_active = len([p for p in self.database_properties if p.get('item_status') in ['Active', 'Upcoming']])
        perfect_matches = len(self.comparison_results['perfect_matches'])
        
        self.comparison_results['accuracy_metrics'] = {
            'source_count': total_source,
            'database_total': len(self.database_properties),
            'database_active': total_db_active,
            'perfect_matches': perfect_matches,
            'match_percentage': (perfect_matches / max(total_source, 1)) * 100,
            'missing_count': len(self.comparison_results['missing_from_database']),
            'extra_count': len(self.comparison_results['extra_in_database']),
            'mismatch_count': len(self.comparison_results['field_mismatches'])
        }
        
        print(f"\nComparison Results:")
        print(f"  Source properties: {total_source}")
        print(f"  Database total: {len(self.database_properties)}")
        print(f"  Database active: {total_db_active}")
        print(f"  Perfect matches: {perfect_matches}")
        print(f"  Match percentage: {self.comparison_results['accuracy_metrics']['match_percentage']:.1f}%")
        print(f"  Missing from DB: {len(self.comparison_results['missing_from_database'])}")
        print(f"  Extra in DB: {len(self.comparison_results['extra_in_database'])}")
        print(f"  Field mismatches: {len(self.comparison_results['field_mismatches'])}")
    
    def generate_report(self):
        """Generate comprehensive comparison report"""
        print("\n[STEP 4] GENERATING REPORT")
        print("="*60)
        
        # Add source and database summaries
        self.comparison_results['source_properties'] = self.source_properties[:10]  # First 10
        self.comparison_results['database_properties'] = [
            {
                'tax_deed_number': p['tax_deed_number'],
                'opening_bid': p['opening_bid'],
                'status': p['item_status'],
                'address': p.get('legal_situs_address', '')[:50]
            }
            for p in self.database_properties[:10]
        ]
        
        # Save report
        report_file = f'comprehensive_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(self.comparison_results, f, indent=2, default=str)
        
        print(f"Report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        metrics = self.comparison_results['accuracy_metrics']
        
        if metrics['match_percentage'] >= 95:
            print("[SUCCESS] Data validation passed!")
        elif metrics['match_percentage'] >= 80:
            print("[WARNING] Data validation needs attention")
        else:
            print("[ALERT] Significant data discrepancies detected")
        
        print(f"\nAccuracy: {metrics['match_percentage']:.1f}%")
        
        if metrics['missing_count'] > 0:
            print(f"\n[ACTION REQUIRED] Add {metrics['missing_count']} missing properties to database")
        
        if metrics['mismatch_count'] > 0:
            print(f"[ACTION REQUIRED] Fix {metrics['mismatch_count']} properties with incorrect data")
        
        return report_file
    
    async def run(self):
        """Main execution"""
        print("\nCOMPREHENSIVE TAX DEED DATA VALIDATOR")
        print("="*60)
        print("Comparing live source data with Supabase database")
        
        # Scrape source
        await self.scrape_source_website()
        
        # Fetch database
        self.fetch_database_properties()
        
        # Compare
        self.compare_properties()
        
        # Generate report
        report_file = self.generate_report()
        
        print(f"\n[COMPLETE] Validation finished")
        print(f"Check {report_file} for detailed results")

if __name__ == "__main__":
    validator = ComprehensiveValidator()
    asyncio.run(validator.run())