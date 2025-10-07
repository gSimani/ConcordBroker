#!/usr/bin/env python3
"""
Detailed comparison between local and production sites using Playwright
"""
from playwright.sync_api import sync_playwright
import time
import json

def detailed_comparison():
    """Do a detailed comparison of local vs production"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})

        # Open production site
        print("[PRODUCTION] Opening https://www.concordbroker.com/properties...")
        prod_page = context.new_page()
        prod_page.goto('https://www.concordbroker.com/properties')
        prod_page.wait_for_load_state('networkidle')
        time.sleep(3)

        # Open local site
        print("[LOCAL] Opening http://localhost:5173/properties...")
        local_page = context.new_page()
        local_page.goto('http://localhost:5173/properties')
        local_page.wait_for_load_state('networkidle')
        time.sleep(3)

        # Take full page screenshots
        print("\n[SCREENSHOTS] Taking full page screenshots...")
        prod_page.screenshot(path='production_full.png', full_page=True)
        local_page.screenshot(path='local_full.png', full_page=True)
        print("[OK] Screenshots saved")

        # Check for property cards on production
        print("\n[PRODUCTION] Analyzing property cards...")
        prod_cards = prod_page.locator('[class*="card"], [class*="property"], .grid > div').all()
        print(f"  Found {len(prod_cards)} potential property cards")

        if len(prod_cards) > 0:
            # Get the HTML structure of first card
            first_card_html = prod_cards[0].inner_html()
            print(f"  First card HTML preview: {first_card_html[:200]}...")

            # Check for specific elements in cards
            prod_images = prod_page.locator('img[alt*="property"], img[alt*="Property"], img[src*="property"], img[src*="maps"]').count()
            prod_prices = prod_page.locator('text=/\\$[0-9,]+/').count()
            prod_addresses = prod_page.locator('text=/[0-9]+ [A-Z]/i').count()

            print(f"  Property images: {prod_images}")
            print(f"  Price displays: {prod_prices}")
            print(f"  Address displays: {prod_addresses}")

        # Check for property cards on local
        print("\n[LOCAL] Analyzing property cards...")
        local_cards = local_page.locator('[class*="card"], [class*="property"], .grid > div').all()
        print(f"  Found {len(local_cards)} potential property cards")

        if len(local_cards) > 0:
            first_local_card_html = local_cards[0].inner_html()
            print(f"  First card HTML preview: {first_local_card_html[:200]}...")

            local_images = local_page.locator('img[alt*="property"], img[alt*="Property"], img[src*="property"], img[src*="maps"]').count()
            local_prices = local_page.locator('text=/\\$[0-9,]+/').count()
            local_addresses = local_page.locator('text=/[0-9]+ [A-Z]/i').count()

            print(f"  Property images: {local_images}")
            print(f"  Price displays: {local_prices}")
            print(f"  Address displays: {local_addresses}")

        # Check search functionality
        print("\n[SEARCH] Comparing search bars...")
        prod_search = prod_page.locator('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]').first
        local_search = local_page.locator('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]').first

        if prod_search.is_visible():
            prod_search_placeholder = prod_search.get_attribute('placeholder')
            print(f"  Production search placeholder: '{prod_search_placeholder}'")

        if local_search.is_visible():
            local_search_placeholder = local_search.get_attribute('placeholder')
            print(f"  Local search placeholder: '{local_search_placeholder}'")

        # Check for filters
        print("\n[FILTERS] Checking filter buttons...")
        prod_filters = prod_page.locator('button:has-text("Filter"), button:has-text("Filters"), [class*="filter"]').all()
        local_filters = local_page.locator('button:has-text("Filter"), button:has-text("Filters"), [class*="filter"]').all()

        print(f"  Production filters: {len(prod_filters)}")
        print(f"  Local filters: {len(local_filters)}")

        # Check CSS/styling
        print("\n[STYLING] Checking main container styles...")
        prod_main = prod_page.locator('main, [role="main"], .container').first
        local_main = local_page.locator('main, [role="main"], .container').first

        if prod_main.is_visible():
            prod_styles = prod_page.evaluate('(el) => window.getComputedStyle(el)', prod_main.element_handle())
            print(f"  Production container background: {prod_styles.get('backgroundColor')}")
            print(f"  Production container padding: {prod_styles.get('padding')}")

        if local_main.is_visible():
            local_styles = local_page.evaluate('(el) => window.getComputedStyle(el)', local_main.element_handle())
            print(f"  Local container background: {local_styles.get('backgroundColor')}")
            print(f"  Local container padding: {local_styles.get('padding')}")

        # Network check - what APIs are being called
        print("\n[NETWORK] Checking API calls...")

        # Reload production and capture network
        print("  Reloading production to capture network...")
        with prod_page.expect_response(lambda response: '/api/' in response.url or 'supabase' in response.url) as response_info:
            prod_page.reload()
            try:
                response = response_info.value
                print(f"  Production API call: {response.url}")
                print(f"  Status: {response.status}")
            except:
                print("  No API calls captured on production")

        # Reload local and capture network
        print("  Reloading local to capture network...")
        with local_page.expect_response(lambda response: '/api/' in response.url or 'supabase' in response.url or ':80' in response.url) as response_info:
            local_page.reload()
            try:
                response = response_info.value
                print(f"  Local API call: {response.url}")
                print(f"  Status: {response.status}")
            except:
                print("  No API calls captured on local")

        # Wait for property data to load
        time.sleep(5)

        # Final comparison
        print("\n[FINAL CHECK] After data load...")
        final_prod_cards = prod_page.locator('.grid > div, [class*="property"][class*="card"]').count()
        final_local_cards = local_page.locator('.grid > div, [class*="property"][class*="card"]').count()

        print(f"  Production property cards: {final_prod_cards}")
        print(f"  Local property cards: {final_local_cards}")

        # Check console errors
        print("\n[CONSOLE] Checking for errors...")
        local_page.on('console', lambda msg: print(f"  Local console: {msg.text}") if msg.type == 'error' else None)
        prod_page.on('console', lambda msg: print(f"  Prod console: {msg.text}") if msg.type == 'error' else None)

        print("\n[COMPLETE] Detailed comparison finished")
        print("Check 'production_full.png' and 'local_full.png' for visual comparison")

        time.sleep(10)  # Keep browser open for manual inspection
        browser.close()

if __name__ == "__main__":
    detailed_comparison()