"""
Final verification that ALL scraped tax deed properties display correctly
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

async def verify_all_properties():
    print("\nFINAL VERIFICATION - ALL PROPERTIES DISPLAY")
    print("="*60)
    
    # First check database
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n[DATABASE CHECK]")
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    
    if response.data:
        total_props = len(response.data)
        with_addresses = len([p for p in response.data if p['legal_situs_address'] and p['legal_situs_address'] != 'Address not available'])
        active_props = len([p for p in response.data if p['item_status'] in ['Active', 'Upcoming']])
        
        print(f"Total properties in database: {total_props}")
        print(f"Properties with real addresses: {with_addresses}")
        print(f"Active/Upcoming properties: {active_props}")
        
        # Show sample properties
        print("\nSample properties with complete data:")
        complete_props = [p for p in response.data if p['legal_situs_address'] and p['legal_situs_address'] != 'Address not available' and not p['parcel_id'].startswith('UNKNOWN')][:5]
        for prop in complete_props:
            print(f"  - {prop['tax_deed_number']}: {prop['legal_situs_address'][:50]}... (${prop['opening_bid']:,.2f})")
    
    # Now check website display
    print("\n[WEBSITE VERIFICATION]")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = await context.new_page()
    
    try:
        url = 'http://localhost:5175/tax-deed-sales'
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(5)
        
        # Count properties on each tab
        tabs = ['Upcoming Auctions', 'Past Auctions', 'Cancelled Auctions']
        total_displayed = 0
        
        for tab_name in tabs:
            # Click on tab
            tab_button = page.locator(f'button:has-text("{tab_name}")')
            if await tab_button.count() > 0:
                await tab_button.click()
                await asyncio.sleep(2)
                
                # Count properties in this tab
                properties = await page.locator('.border.border-gray-200.rounded-lg').count()
                total_displayed += properties
                print(f"\n{tab_name}: {properties} properties")
                
                # Get sample property details
                if properties > 0:
                    first_prop = await page.locator('.border.border-gray-200.rounded-lg').first.text_content()
                    if first_prop:
                        # Extract key info
                        if 'TD-' in first_prop:
                            td_num = first_prop[first_prop.find('TD-'):first_prop.find('TD-')+10]
                            print(f"  First property: {td_num}")
                        if '$' in first_prop:
                            # Find opening bid
                            idx = first_prop.find('$')
                            end_idx = first_prop.find(' ', idx)
                            if end_idx == -1:
                                end_idx = idx + 20
                            amount = first_prop[idx:end_idx]
                            print(f"  Opening bid: {amount}")
        
        print(f"\n[SUMMARY]")
        print(f"Total properties displayed across all tabs: {total_displayed}")
        
        # Take screenshot
        screenshot_file = f'all_properties_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        await page.screenshot(path=screenshot_file, full_page=True)
        print(f"Screenshot saved: {screenshot_file}")
        
        # Final comparison
        print("\n" + "="*60)
        print("VERIFICATION RESULTS")
        print("="*60)
        
        if response.data:
            expected_active = len([p for p in response.data if p['item_status'] in ['Active', 'Upcoming'] and p['legal_situs_address'] != 'Address not available'])
            
            print(f"Expected Active/Upcoming properties: {expected_active}")
            print(f"Actually displayed properties: {total_displayed}")
            
            if total_displayed >= expected_active:
                print("\n[SUCCESS] All expected properties are displaying!")
            else:
                print(f"\n[ISSUE] Missing {expected_active - total_displayed} properties")
                print("Possible causes:")
                print("  - Frontend filtering logic")
                print("  - Data quality issues")
                print("  - Component limit settings")
        
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(verify_all_properties())

