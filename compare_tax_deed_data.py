"""
Compare tax deed data between source website and our localhost
Uses Playwright to verify data accuracy
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

class TaxDeedDataComparator:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.browser = None
        self.context = None
        self.source_data = []
        self.localhost_data = []
        self.database_data = []
        
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        print("Initializing browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Keep visible to see what's happening
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
    async def scrape_source_website(self):
        """Scrape data from the actual Broward County website"""
        print("\n" + "="*60)
        print("STEP 1: Scraping Source Website (Broward County)")
        print("="*60)
        
        page = await self.context.new_page()
        url = 'https://broward.deedauction.net/auction/110'  # 9/17/2025 auction
        
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Take screenshot for reference
        await page.screenshot(path='source_website.png')
        print("Screenshot saved: source_website.png")
        
        # Extract property data
        print("Extracting property data...")
        
        properties = await page.evaluate('''() => {
            const results = [];
            const rows = document.querySelectorAll('table tbody tr');
            
            rows.forEach(row => {
                // Skip header or detail rows
                if (row.classList.contains('details') || !row.querySelector('td')) return;
                
                const cells = row.querySelectorAll('td');
                if (cells.length < 3) return;
                
                const property = {};
                
                // Extract text from each cell
                const cellTexts = Array.from(cells).map(cell => cell.textContent.trim());
                
                // Find tax deed number (usually a 5-digit number)
                for (let text of cellTexts) {
                    if (/^[0-9]{5}$/.test(text)) {
                        property.taxDeedNumber = text;
                        break;
                    }
                }
                
                // Find opening bid (contains $)
                for (let text of cellTexts) {
                    if (text.includes('$')) {
                        const amount = text.replace(/[^0-9.]/g, '');
                        if (amount && !property.openingBid) {
                            property.openingBid = parseFloat(amount);
                        }
                    }
                }
                
                // Find status
                for (let text of cellTexts) {
                    if (['Upcoming', 'Active', 'Sold', 'Cancelled', 'Canceled'].includes(text)) {
                        property.status = text;
                    }
                }
                
                // Find close time
                for (let text of cellTexts) {
                    if (text.includes('AM') || text.includes('PM') || text === '-') {
                        property.closeTime = text;
                    }
                }
                
                // Look for expand button to get more details
                const expandBtn = row.querySelector('img[src*="expand"], img[src*="collapse"]');
                if (expandBtn) {
                    property.hasDetails = true;
                }
                
                if (property.taxDeedNumber) {
                    results.push(property);
                }
            });
            
            return results;
        }''')
        
        self.source_data = properties
        print(f"Found {len(properties)} properties on source website")
        
        # Show first few properties
        print("\nFirst 5 properties from source:")
        for i, prop in enumerate(properties[:5]):
            print(f"  {i+1}. TD-{prop.get('taxDeedNumber', 'N/A')}: ${prop.get('openingBid', 0):,.2f} - {prop.get('status', 'Unknown')}")
        
        await page.close()
        return properties
        
    async def scrape_localhost(self):
        """Scrape data from our localhost website"""
        print("\n" + "="*60)
        print("STEP 2: Scraping Our Website (localhost:5173)")
        print("="*60)
        
        page = await self.context.new_page()
        url = 'http://localhost:5174/tax-deed-sales'  # Updated port
        
        print(f"Navigating to: {url}")
        try:
            await page.goto(url, wait_until='networkidle', timeout=10000)
            await asyncio.sleep(3)
        except:
            print("[ERROR] Could not connect to localhost:5173")
            print("Make sure the development server is running: npm run dev")
            await page.close()
            return []
        
        # Take screenshot
        await page.screenshot(path='localhost_website.png')
        print("Screenshot saved: localhost_website.png")
        
        # Extract property data from our website
        print("Extracting property data from localhost...")
        
        properties = await page.evaluate('''() => {
            const results = [];
            
            // Look for property cards or table rows
            const propertyElements = document.querySelectorAll(
                '.property-card, .tax-deed-item, [class*="property"], table tbody tr'
            );
            
            propertyElements.forEach(element => {
                const property = {};
                
                // Try to extract tax deed number
                const tdMatch = element.textContent.match(/TD-[0-9]+/);
                if (tdMatch) {
                    property.taxDeedNumber = tdMatch[0].replace('TD-', '');
                }
                
                // Try to extract opening bid
                const bidMatch = element.textContent.match(/\$([0-9,]+\.?[0-9]*)/);
                if (bidMatch) {
                    property.openingBid = parseFloat(bidMatch[1].replace(',', ''));
                }
                
                // Try to extract status
                const statusWords = ['Active', 'Sold', 'Cancelled', 'Upcoming'];
                for (let status of statusWords) {
                    if (element.textContent.includes(status)) {
                        property.status = status;
                        break;
                    }
                }
                
                // Try to extract address
                const addressMatch = element.textContent.match(/[0-9]+ [A-Za-z ]+(Street|Avenue|Boulevard|Road|Drive|Way|Court)/i);
                if (addressMatch) {
                    property.address = addressMatch[0];
                }
                
                if (property.taxDeedNumber || property.openingBid) {
                    results.push(property);
                }
            });
            
            // If no properties found, try different selectors
            if (results.length === 0) {
                // Check if there's an error message
                const errorElement = document.querySelector('.error, [class*="error"]');
                if (errorElement) {
                    console.log('Error on page:', errorElement.textContent);
                }
                
                // Check if there's a loading indicator
                const loadingElement = document.querySelector('.loading, [class*="loading"]');
                if (loadingElement) {
                    console.log('Page is still loading');
                }
                
                // Get page text for debugging
                console.log('Page content preview:', document.body.innerText.substring(0, 500));
            }
            
            return results;
        }''')
        
        self.localhost_data = properties
        print(f"Found {len(properties)} properties on localhost")
        
        # Show first few properties
        if properties:
            print("\nFirst 5 properties from localhost:")
            for i, prop in enumerate(properties[:5]):
                td_num = prop.get('taxDeedNumber', 'N/A')
                if not td_num.startswith('TD-'):
                    td_num = f"TD-{td_num}"
                print(f"  {i+1}. {td_num}: ${prop.get('openingBid', 0):,.2f} - {prop.get('status', 'Unknown')}")
        else:
            print("[WARNING] No properties found on localhost page")
            print("Checking page structure...")
            
            # Try to get more info about the page
            page_info = await page.evaluate('''() => {
                return {
                    title: document.title,
                    url: window.location.href,
                    hasReactRoot: !!document.getElementById('root'),
                    bodyText: document.body.innerText.substring(0, 200)
                };
            }''')
            print(f"Page info: {json.dumps(page_info, indent=2)}")
        
        await page.close()
        return properties
        
    async def get_database_data(self):
        """Get data directly from Supabase database"""
        print("\n" + "="*60)
        print("STEP 3: Getting Data from Database")
        print("="*60)
        
        try:
            response = self.supabase.table('tax_deed_bidding_items').select('*').limit(100).execute()
            self.database_data = response.data if response.data else []
            
            print(f"Found {len(self.database_data)} properties in database")
            
            # Show first few properties
            if self.database_data:
                print("\nFirst 5 properties from database:")
                for i, prop in enumerate(self.database_data[:5]):
                    print(f"  {i+1}. {prop.get('tax_deed_number', 'N/A')}: ${prop.get('opening_bid', 0):,.2f} - {prop.get('item_status', 'Unknown')}")
                    
                # Count by status
                status_counts = {}
                for prop in self.database_data:
                    status = prop.get('item_status', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                print("\nDatabase properties by status:")
                for status, count in status_counts.items():
                    print(f"  {status}: {count}")
                    
        except Exception as e:
            print(f"[ERROR] Could not fetch from database: {e}")
            
    async def compare_data(self):
        """Compare data between all three sources"""
        print("\n" + "="*60)
        print("STEP 4: Data Comparison Report")
        print("="*60)
        
        print(f"\nData counts:")
        print(f"  Source website: {len(self.source_data)} properties")
        print(f"  Localhost:      {len(self.localhost_data)} properties")
        print(f"  Database:       {len(self.database_data)} properties")
        
        # Compare tax deed numbers
        source_td_numbers = set([p.get('taxDeedNumber') for p in self.source_data if p.get('taxDeedNumber')])
        localhost_td_numbers = set([p.get('taxDeedNumber', '').replace('TD-', '') for p in self.localhost_data])
        db_td_numbers = set([p.get('tax_deed_number', '').replace('TD-', '') for p in self.database_data])
        
        print(f"\nUnique tax deed numbers:")
        print(f"  Source website: {len(source_td_numbers)}")
        print(f"  Localhost:      {len(localhost_td_numbers)}")
        print(f"  Database:       {len(db_td_numbers)}")
        
        # Find matches and mismatches
        if source_td_numbers and localhost_td_numbers:
            matches = source_td_numbers & localhost_td_numbers
            source_only = source_td_numbers - localhost_td_numbers
            localhost_only = localhost_td_numbers - source_td_numbers
            
            print(f"\nMatching properties: {len(matches)}")
            
            if source_only:
                print(f"\nProperties on source but NOT on localhost ({len(source_only)}):")
                for td in list(source_only)[:10]:
                    print(f"  - TD-{td}")
                    
            if localhost_only:
                print(f"\nProperties on localhost but NOT on source ({len(localhost_only)}):")
                for td in list(localhost_only)[:10]:
                    print(f"  - TD-{td}")
                    
        # Compare opening bids for matching properties
        if source_td_numbers and db_td_numbers:
            print("\nComparing opening bids for matching properties:")
            matches = source_td_numbers & db_td_numbers
            
            for td_num in list(matches)[:5]:
                source_prop = next((p for p in self.source_data if p.get('taxDeedNumber') == td_num), None)
                db_prop = next((p for p in self.database_data if p.get('tax_deed_number', '').replace('TD-', '') == td_num), None)
                
                if source_prop and db_prop:
                    source_bid = source_prop.get('openingBid', 0)
                    db_bid = db_prop.get('opening_bid', 0)
                    
                    if abs(source_bid - db_bid) > 1:  # Allow $1 difference for rounding
                        print(f"  TD-{td_num}:")
                        print(f"    Source: ${source_bid:,.2f}")
                        print(f"    Database: ${db_bid:,.2f}")
                        print(f"    Difference: ${abs(source_bid - db_bid):,.2f}")
                        
        # Generate summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        accuracy_score = 0
        issues = []
        
        if len(self.source_data) > 0:
            if len(self.database_data) > 0:
                accuracy_score += 25
            else:
                issues.append("No data in database")
                
            if len(self.localhost_data) > 0:
                accuracy_score += 25
            else:
                issues.append("No data showing on localhost")
                
            if source_td_numbers and db_td_numbers:
                match_rate = len(source_td_numbers & db_td_numbers) / len(source_td_numbers)
                accuracy_score += int(match_rate * 50)
                
                if match_rate < 0.5:
                    issues.append(f"Only {match_rate*100:.1f}% of source properties in database")
        else:
            issues.append("Could not scrape source website")
            
        print(f"Data Accuracy Score: {accuracy_score}%")
        
        if issues:
            print("\nIssues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n[OK] Data appears to be accurately synchronized!")
            
        # Save comparison report
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_count': len(self.source_data),
            'localhost_count': len(self.localhost_data),
            'database_count': len(self.database_data),
            'accuracy_score': accuracy_score,
            'issues': issues,
            'source_sample': self.source_data[:3],
            'database_sample': self.database_data[:3]
        }
        
        with open('tax_deed_comparison_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print("\nDetailed report saved to: tax_deed_comparison_report.json")
        
    async def run(self):
        """Main execution"""
        try:
            await self.initialize_browser()
            
            # Step 1: Scrape source website
            await self.scrape_source_website()
            
            # Step 2: Scrape localhost
            await self.scrape_localhost()
            
            # Step 3: Get database data
            await self.get_database_data()
            
            # Step 4: Compare all data
            await self.compare_data()
            
            print("\n" + "="*60)
            print("COMPARISON COMPLETE")
            print("="*60)
            print("\nCheck the screenshots:")
            print("  - source_website.png")
            print("  - localhost_website.png")
            print("\nAnd the report:")
            print("  - tax_deed_comparison_report.json")
            
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
    print("Tax Deed Data Comparison Tool")
    print("="*60)
    print("Comparing data between:")
    print("  1. Source: https://broward.deedauction.net")
    print("  2. Our site: http://localhost:5173/tax-deed-sales")
    print("  3. Database: Supabase")
    print("="*60)
    
    comparator = TaxDeedDataComparator()
    asyncio.run(comparator.run())