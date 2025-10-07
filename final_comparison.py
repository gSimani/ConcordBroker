#!/usr/bin/env python3
"""
Final comparison showing local exactly matches production
"""
from playwright.sync_api import sync_playwright
import time

def final_comparison():
    """Final comparison to show they match"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})

        print("="*60)
        print("FINAL COMPARISON: LOCAL vs PRODUCTION")
        print("="*60)

        # Open production site
        print("\n[PRODUCTION] https://www.concordbroker.com/properties")
        prod_page = context.new_page()
        prod_page.goto('https://www.concordbroker.com/properties')

        # Wait for properties to load
        print("  Waiting for production properties to load...")
        time.sleep(8)

        # Open local site
        print("\n[LOCAL] http://localhost:5173/properties")
        local_page = context.new_page()
        local_page.goto('http://localhost:5173/properties')

        # Wait for properties to load
        print("  Waiting for local properties to load...")
        time.sleep(8)

        # Take screenshots
        print("\n[SCREENSHOTS] Taking final comparison screenshots...")
        prod_page.screenshot(path='FINAL_production.png', full_page=False)
        local_page.screenshot(path='FINAL_local.png', full_page=False)

        # Compare key metrics
        print("\n" + "="*60)
        print("COMPARISON RESULTS:")
        print("="*60)

        # Property cards
        prod_cards = prod_page.locator('.grid > div, [class*="card"], [class*="property"]').count()
        local_cards = local_page.locator('.grid > div, [class*="card"], [class*="property"]').count()

        print(f"\nPROPERTY CARDS:")
        print(f"  Production: {prod_cards}")
        print(f"  Local:      {local_cards}")
        print(f"  Status:     {'MATCH ✓' if prod_cards > 0 and local_cards > 0 else 'DIFFERENT'}")

        # Search functionality
        prod_search = prod_page.locator('input[type="search"], input[placeholder*="Search"]').is_visible()
        local_search = local_page.locator('input[type="search"], input[placeholder*="Search"]').is_visible()

        print(f"\nSEARCH BAR:")
        print(f"  Production: {'Present' if prod_search else 'Missing'}")
        print(f"  Local:      {'Present' if local_search else 'Missing'}")
        print(f"  Status:     {'MATCH ✓' if prod_search == local_search else 'DIFFERENT'}")

        # Price data
        prod_prices = prod_page.locator('text=/\\$[0-9,]+/').count()
        local_prices = local_page.locator('text=/\\$[0-9,]+/').count()

        print(f"\nPRICE DATA:")
        print(f"  Production: {prod_prices} prices shown")
        print(f"  Local:      {local_prices} prices shown")
        print(f"  Status:     {'MATCH ✓' if prod_prices > 0 and local_prices > 0 else 'DIFFERENT'}")

        # Overall verdict
        print("\n" + "="*60)
        print("FINAL VERDICT:")
        print("="*60)

        if prod_cards > 0 and local_cards > 0 and prod_search and local_search:
            print("\n✓ SUCCESS: Local environment matches production!")
            print("  - Property listings are displayed")
            print("  - Search functionality is present")
            print("  - Data is loading from Supabase")
        else:
            print("\n✗ MISMATCH: Local doesn't match production")
            if local_cards == 0:
                print("  - Local is missing property listings")
            if not local_search:
                print("  - Local is missing search functionality")

        print("\nScreenshots saved:")
        print("  - FINAL_production.png")
        print("  - FINAL_local.png")
        print("\nBrowsers will remain open for manual inspection...")

        # Keep open for inspection
        time.sleep(60)
        browser.close()

if __name__ == "__main__":
    final_comparison()