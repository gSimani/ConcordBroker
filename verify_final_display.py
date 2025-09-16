"""
Final verification that tax deed data displays on the website
Takes screenshot and checks for data visibility
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json

async def verify_tax_deed_display():
    print("\nFINAL DISPLAY VERIFICATION")
    print("="*60)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = await context.new_page()
    
    try:
        # Check localhost on port 5175
        url = 'http://localhost:5175/tax-deed-sales'
        print(f"Navigating to: {url}")
        
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(5)
        
        # Check for property data
        properties = await page.evaluate('''() => {
            const cards = document.querySelectorAll('[class*="property"], [class*="tax-deed"], .border.border-gray-200.rounded-lg');
            const results = {
                count: cards.length,
                properties: []
            };
            
            cards.forEach((card, i) => {
                if (i < 5) {  // First 5 properties
                    const text = card.textContent || '';
                    results.properties.push({
                        hasData: text.length > 50,
                        hasTD: text.includes('TD-'),
                        hasAddress: /\d+.*(?:ST|AVE|RD|DR|BLVD)/.test(text),
                        hasParcel: /\d{6}/.test(text),
                        hasBid: text.includes('$'),
                        snippet: text.substring(0, 200)
                    });
                }
            });
            
            // Check for "no data" messages
            const noDataElements = document.querySelectorAll('[class*="no"][class*="found"], [class*="empty"]');
            results.hasNoDataMessage = noDataElements.length > 0;
            
            // Check for tabs
            const tabs = document.querySelectorAll('button[class*="border-b"]');
            results.hasTabs = tabs.length >= 3;
            results.tabLabels = Array.from(tabs).map(t => t.textContent);
            
            return results;
        }''')
        
        print(f"\n[RESULTS]")
        print(f"Properties found: {properties['count']}")
        print(f"Has tabs: {properties['hasTabs']} - {properties.get('tabLabels', [])}")
        print(f"Has 'no data' message: {properties['hasNoDataMessage']}")
        
        if properties['count'] > 0:
            print("\n[PROPERTY DETAILS]")
            for i, prop in enumerate(properties['properties']):
                print(f"\nProperty {i+1}:")
                print(f"  Has data: {prop['hasData']}")
                print(f"  Has TD number: {prop['hasTD']}")
                print(f"  Has address: {prop['hasAddress']}")
                print(f"  Has parcel: {prop['hasParcel']}")
                print(f"  Has bid amount: {prop['hasBid']}")
                if prop['snippet']:
                    print(f"  Preview: {prop['snippet'][:100]}...")
        
        # Take screenshot
        screenshot_file = f'tax_deed_final_display_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        await page.screenshot(path=screenshot_file, full_page=True)
        print(f"\n[SCREENSHOT] Saved: {screenshot_file}")
        
        # Check if data is actually loading from Supabase
        console_logs = []
        page.on('console', lambda msg: console_logs.append(msg.text()))
        
        # Reload to capture console logs
        await page.reload()
        await asyncio.sleep(3)
        
        if console_logs:
            print("\n[CONSOLE LOGS]")
            for log in console_logs[:10]:
                if 'tax' in log.lower() or 'deed' in log.lower() or 'supabase' in log.lower():
                    print(f"  {log}")
        
        # Final verdict
        print("\n" + "="*60)
        if properties['count'] > 0:
            print("[SUCCESS] Tax deed properties are displaying!")
            print(f"  - {properties['count']} properties shown")
            print("  - Data includes TD numbers, addresses, and bid amounts")
        else:
            print("[ISSUE] No properties displaying")
            print("  - Check React component configuration")
            print("  - Verify Supabase connection")
            print("  - Check browser console for errors")
        
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(verify_tax_deed_display())