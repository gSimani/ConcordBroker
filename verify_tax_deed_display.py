"""
Verify that scraped tax deed data with complete details is properly displayed on the frontend
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

class TaxDeedDisplayVerifier:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.verification_results = {
            'timestamp': datetime.now().isoformat(),
            'database_properties': [],
            'displayed_properties': [],
            'missing_properties': [],
            'field_verification': {
                'parcel_numbers': [],
                'addresses': [],
                'applicant_names': [],
                'opening_bids': [],
                'links_found': []
            }
        }
        
    async def get_database_properties(self):
        """Get properties with detailed info from database"""
        print("\n[DATABASE CHECK]")
        print("="*60)
        
        # Get properties that have detailed information
        response = self.supabase.table('tax_deed_bidding_items').select('*').neq('parcel_id', 'UNKNOWN-1').order('tax_deed_number').execute()
        
        if response.data:
            print(f"[OK] Found {len(response.data)} properties with details in database")
            
            # Show sample of properties with complete details
            for prop in response.data[:5]:
                if prop.get('parcel_id') and not prop['parcel_id'].startswith('UNKNOWN'):
                    print(f"\n  Property: {prop['tax_deed_number']}")
                    print(f"    Parcel: {prop['parcel_id']}")
                    print(f"    Address: {prop.get('legal_situs_address', 'N/A')[:50]}...")
                    print(f"    Applicant: {prop.get('applicant_name', 'N/A')}")
                    print(f"    Opening Bid: ${prop.get('opening_bid', 0):,.2f}")
                    if prop.get('property_appraisal_url'):
                        print(f"    Appraisal Link: Yes")
                        
            self.verification_results['database_properties'] = response.data
            return response.data
        else:
            print("[WARNING] No properties found in database")
            return []
            
    async def verify_frontend_display(self):
        """Check if data displays properly on frontend"""
        print("\n[FRONTEND VERIFICATION]")
        print("="*60)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Try different ports
            for port in [5173, 5174, 5175]:
                url = f'http://localhost:{port}/tax-deed-sales'
                print(f"\nChecking {url}...")
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=10000)
                    await asyncio.sleep(3)
                    
                    # Check if page loaded
                    title = await page.title()
                    print(f"  Page title: {title}")
                    
                    # Look for property cards or list items
                    properties_found = await page.evaluate('''() => {
                        const results = {
                            cards: [],
                            hasData: false,
                            errorMessage: null
                        };
                        
                        // Check for property cards
                        const cards = document.querySelectorAll('.property-card, [class*="property"], [class*="tax-deed"]');
                        if (cards.length > 0) {
                            results.hasData = true;
                            cards.forEach(card => {
                                const text = card.textContent;
                                // Extract TD number
                                const tdMatch = text.match(/TD-\d+/);
                                // Extract parcel
                                const parcelMatch = text.match(/\d{6}-\d{2}-\d{4}/);
                                // Extract address
                                const addressMatch = text.match(/\d+\s+[A-Z\s]+(?:ST|AVE|RD|DR|BLVD|LN|CT|PL)/i);
                                // Extract bid amount
                                const bidMatch = text.match(/\$[\d,]+\.?\d*/);
                                
                                results.cards.push({
                                    tdNumber: tdMatch ? tdMatch[0] : null,
                                    parcel: parcelMatch ? parcelMatch[0] : null,
                                    address: addressMatch ? addressMatch[0] : null,
                                    bid: bidMatch ? bidMatch[0] : null,
                                    fullText: text.substring(0, 200)
                                });
                            });
                        }
                        
                        // Check for error messages
                        const noData = document.querySelector('[class*="no-data"], [class*="empty"], [class*="not-found"]');
                        if (noData) {
                            results.errorMessage = noData.textContent;
                        }
                        
                        // Check for loading state
                        const loading = document.querySelector('[class*="loading"], [class*="spinner"]');
                        if (loading) {
                            results.errorMessage = "Page is still loading";
                        }
                        
                        return results;
                    }''')
                    
                    if properties_found['hasData']:
                        print(f"  [SUCCESS] Found {len(properties_found['cards'])} properties displayed")
                        
                        # Verify detailed fields
                        for i, card in enumerate(properties_found['cards'][:3]):
                            print(f"\n  Property {i+1}:")
                            if card['tdNumber']:
                                print(f"    TD Number: {card['tdNumber']}")
                                self.verification_results['field_verification']['parcel_numbers'].append(card['tdNumber'])
                            if card['parcel']:
                                print(f"    Parcel: {card['parcel']}")
                            if card['address']:
                                print(f"    Address: {card['address']}")
                                self.verification_results['field_verification']['addresses'].append(card['address'])
                            if card['bid']:
                                print(f"    Bid: {card['bid']}")
                                self.verification_results['field_verification']['opening_bids'].append(card['bid'])
                        
                        self.verification_results['displayed_properties'] = properties_found['cards']
                        
                        # Check for hyperlinks
                        links = await page.evaluate('''() => {
                            const links = [];
                            document.querySelectorAll('a[href*="bcpa.net"], a[href*="RecInfo"], a[href*="Folio"]').forEach(link => {
                                links.push({
                                    text: link.textContent.trim(),
                                    href: link.href
                                });
                            });
                            return links;
                        }''')
                        
                        if links:
                            print(f"\n  [LINKS] Found {len(links)} property appraisal links")
                            for link in links[:3]:
                                print(f"    {link['text']}: {link['href'][:60]}...")
                            self.verification_results['field_verification']['links_found'] = links
                        
                        # Take screenshot
                        screenshot_path = f'tax_deed_display_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                        await page.screenshot(path=screenshot_path, full_page=True)
                        print(f"\n  Screenshot saved: {screenshot_path}")
                        
                        break  # Success, exit loop
                        
                    else:
                        if properties_found.get('errorMessage'):
                            print(f"  [ERROR] {properties_found['errorMessage']}")
                        else:
                            print(f"  [WARNING] No properties found on page")
                            
                except Exception as e:
                    print(f"  [ERROR] Could not access {url}: {str(e)[:50]}")
                    continue
                    
        finally:
            await browser.close()
            await playwright.stop()
            
    async def compare_data(self):
        """Compare database vs displayed data"""
        print("\n[DATA COMPARISON]")
        print("="*60)
        
        db_count = len(self.verification_results['database_properties'])
        display_count = len(self.verification_results['displayed_properties'])
        
        print(f"Database properties: {db_count}")
        print(f"Displayed properties: {display_count}")
        
        if db_count > 0 and display_count > 0:
            # Check which properties are missing
            db_tds = {p['tax_deed_number'] for p in self.verification_results['database_properties']}
            displayed_tds = {p['tdNumber'] for p in self.verification_results['displayed_properties'] if p['tdNumber']}
            
            missing = db_tds - displayed_tds
            if missing:
                print(f"\n[WARNING] {len(missing)} properties in database but not displayed:")
                for td in list(missing)[:5]:
                    print(f"  - {td}")
                self.verification_results['missing_properties'] = list(missing)
                
        # Field completeness check
        print("\n[FIELD COMPLETENESS]")
        print(f"Parcel numbers found: {len(self.verification_results['field_verification']['parcel_numbers'])}")
        print(f"Addresses found: {len(self.verification_results['field_verification']['addresses'])}")
        print(f"Opening bids found: {len(self.verification_results['field_verification']['opening_bids'])}")
        print(f"Hyperlinks found: {len(self.verification_results['field_verification']['links_found'])}")
        
    async def run(self):
        """Main verification process"""
        print("\nTAX DEED DISPLAY VERIFICATION")
        print("="*60)
        print("Verifying that scraped detailed property data displays correctly")
        
        # Get database data
        await self.get_database_properties()
        
        # Check frontend display
        await self.verify_frontend_display()
        
        # Compare
        await self.compare_data()
        
        # Save results
        report_file = f'tax_deed_verification_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(self.verification_results, f, indent=2, default=str)
        print(f"\n[REPORT] Verification report saved: {report_file}")
        
        # Summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        if self.verification_results['displayed_properties']:
            print("[SUCCESS] Properties are displaying on frontend")
            print(f"  - {len(self.verification_results['displayed_properties'])} properties shown")
            print(f"  - {len(self.verification_results['field_verification']['addresses'])} addresses displayed")
            print(f"  - {len(self.verification_results['field_verification']['links_found'])} hyperlinks found")
        else:
            print("[ISSUE] Properties not displaying properly")
            print("  Check React component configuration")
            print("  Verify API endpoint is working")
            
if __name__ == "__main__":
    verifier = TaxDeedDisplayVerifier()
    asyncio.run(verifier.run())