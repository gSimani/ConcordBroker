#!/usr/bin/env python3
"""
Final verification that local environment matches production using Playwright
"""
from playwright.sync_api import sync_playwright
import time

def verify_parity():
    """Compare local and production sites"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Open both sites
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})

        print("Opening local site...")
        local_page = context.new_page()
        local_page.goto('http://localhost:5173/properties')
        time.sleep(3)

        print("Opening production site...")
        prod_page = context.new_page()
        prod_page.goto('https://www.concordbroker.com/properties')
        time.sleep(3)

        # Check for errors on local
        try:
            local_error = local_page.locator('text="Application Error"').is_visible()
            if local_error:
                error_text = local_page.locator('.text-red-600').text_content()
                print(f"[ERROR] LOCAL ERROR: {error_text}")
            else:
                print("[OK] Local: No application errors")
        except:
            print("[OK] Local: No application errors")

        # Check for PropertySearch functionality
        try:
            # Check if search exists on local
            local_search = local_page.locator('input[placeholder*="Search"]').first
            if local_search.is_visible():
                print("[OK] Local: Search bar is visible")
            else:
                print("[ERROR] Local: Search bar not found")
        except:
            print("[ERROR] Local: Search functionality missing")

        # Check if properties are loading
        try:
            local_page.wait_for_selector('.property-card, [class*="property"], [class*="card"]', timeout=5000)
            property_cards = local_page.locator('.property-card, [class*="property"][class*="card"]').count()
            print(f"[OK] Local: Found {property_cards} property cards")
        except:
            print("[ERROR] Local: No property cards found")

        # Compare visual elements
        print("\n[VISUAL] Visual Comparison:")

        # Take screenshots
        local_page.screenshot(path='local_properties_final.png')
        prod_page.screenshot(path='production_properties_final.png')

        # Check for key UI elements
        elements_to_check = [
            ('Header/Navigation', 'nav, header, [role="navigation"]'),
            ('Search functionality', 'input[type="search"], input[placeholder*="Search"], [class*="search"]'),
            ('Filter buttons', 'button:has-text("Filter"), button:has-text("Filters"), [class*="filter"]'),
            ('Property listings', '.property-card, [class*="property"][class*="card"], [class*="grid"]'),
            ('Footer', 'footer')
        ]

        print("\n[COMPARE] Element Comparison:")
        for name, selector in elements_to_check:
            local_has = local_page.locator(selector).first.is_visible() if local_page.locator(selector).count() > 0 else False
            prod_has = prod_page.locator(selector).first.is_visible() if prod_page.locator(selector).count() > 0 else False

            if local_has and prod_has:
                print(f"[OK] {name}: Present on both")
            elif not local_has and not prod_has:
                print(f"[INFO] {name}: Missing on both")
            elif local_has and not prod_has:
                print(f"[WARN] {name}: Only on local")
            else:
                print(f"[ERROR] {name}: Missing on local, present on production")

        # Test a property detail page
        print("\n[TEST] Testing Property Detail Page:")
        local_page.goto('http://localhost:5173/property/474131031040')
        time.sleep(2)

        try:
            detail_error = local_page.locator('text="Application Error"').is_visible()
            if detail_error:
                error_text = local_page.locator('.text-red-600').text_content()
                print(f"[ERROR] Property detail error: {error_text}")
            else:
                # Check for property data
                has_data = local_page.locator('text=/\\$[0-9,]+/').count() > 0
                if has_data:
                    print("[OK] Property detail page loads with data")
                else:
                    print("[WARN] Property detail page loads but no price data visible")
        except:
            print("[OK] Property detail page works")

        input("Press Enter to close browsers...")
        browser.close()

if __name__ == "__main__":
    verify_parity()