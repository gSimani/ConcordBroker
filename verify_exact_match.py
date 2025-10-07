#!/usr/bin/env python3
"""
Verify that local exactly matches production using Playwright
"""
from playwright.sync_api import sync_playwright
import time

def verify_exact_match():
    """Verify exact match between local and production"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})

        print("[TEST] Comparing local exact production copy with live site...")

        # Open production site
        print("\n[1] Opening production site: https://www.concordbroker.com/properties")
        prod_page = context.new_page()
        prod_page.goto('https://www.concordbroker.com/properties')
        time.sleep(5)  # Let it fully load

        # Open local exact copy
        print("[2] Opening local copy: http://localhost:5173/properties.html")
        local_page = context.new_page()
        local_page.goto('http://localhost:5173/properties.html')
        time.sleep(5)  # Let it fully load

        # Take screenshots
        print("\n[SCREENSHOTS] Taking screenshots for comparison...")
        prod_page.screenshot(path='production_exact_match.png', full_page=False)
        local_page.screenshot(path='local_exact_match.png', full_page=False)

        # Check for property cards
        print("\n[PROPERTY CARDS]")
        prod_cards = prod_page.locator('.grid > div, [class*="card"]').count()
        local_cards = local_page.locator('.grid > div, [class*="card"]').count()
        print(f"  Production: {prod_cards} cards")
        print(f"  Local: {local_cards} cards")

        if prod_cards == local_cards and prod_cards > 0:
            print("  [MATCH] Same number of property cards!")
        elif local_cards == 0:
            print("  [ISSUE] No property cards on local")
        else:
            print(f"  [ISSUE] Different card counts")

        # Check for search bar
        print("\n[SEARCH BAR]")
        prod_search = prod_page.locator('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]').count()
        local_search = local_page.locator('input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]').count()
        print(f"  Production: {prod_search} search inputs")
        print(f"  Local: {local_search} search inputs")

        # Check for filter buttons
        print("\n[FILTERS]")
        prod_filters = prod_page.locator('button').count()
        local_filters = local_page.locator('button').count()
        print(f"  Production: {prod_filters} buttons")
        print(f"  Local: {local_filters} buttons")

        # Check for images
        print("\n[IMAGES]")
        prod_images = prod_page.locator('img').count()
        local_images = local_page.locator('img').count()
        print(f"  Production: {prod_images} images")
        print(f"  Local: {local_images} images")

        # Check text content
        print("\n[TEXT CONTENT]")
        prod_text = prod_page.locator('body').inner_text()
        local_text = local_page.locator('body').inner_text()

        # Compare key phrases
        key_phrases = ["Property", "Search", "$", "bed", "bath", "sqft"]
        for phrase in key_phrases:
            prod_has = phrase.lower() in prod_text.lower()
            local_has = phrase.lower() in local_text.lower()
            if prod_has == local_has:
                print(f"  [MATCH] '{phrase}': Both have it" if prod_has else f"  [MATCH] '{phrase}': Neither have it")
            else:
                print(f"  [DIFF] '{phrase}': Prod={prod_has}, Local={local_has}")

        # Final verdict
        print("\n[VERDICT]")
        if prod_cards > 0 and local_cards > 0 and abs(prod_cards - local_cards) < 5:
            print("✓ Sites are visually similar with property listings!")
        elif local_cards == 0:
            print("✗ Local site is missing property listings - needs data connection")
        else:
            print("? Sites have differences - check screenshots for details")

        print("\nCheck 'production_exact_match.png' and 'local_exact_match.png' for visual comparison")
        print("Keep browsers open for manual inspection...")
        time.sleep(30)
        browser.close()

if __name__ == "__main__":
    verify_exact_match()