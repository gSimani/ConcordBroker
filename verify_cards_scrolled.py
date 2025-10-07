"""
Verify that local mini property cards match production UI with proper scrolling
"""
from playwright.sync_api import sync_playwright
import time

def verify_mini_cards_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Create two contexts for comparison
        local_context = browser.new_context(viewport={'width': 1280, 'height': 800})
        prod_context = browser.new_context(viewport={'width': 1280, 'height': 800})

        local_page = local_context.new_page()
        prod_page = prod_context.new_page()

        print("Opening local site at http://localhost:5173/properties...")
        local_page.goto("http://localhost:5173/properties")

        print("Opening production site at https://www.concordbroker.com/properties...")
        prod_page.goto("https://www.concordbroker.com/properties")

        # Wait for content to load
        time.sleep(5)

        # Scroll down to see property cards on both pages
        print("Scrolling to view property cards...")
        local_page.evaluate("window.scrollBy(0, 800)")
        prod_page.evaluate("window.scrollBy(0, 800)")

        # Wait for cards to be visible after scrolling
        time.sleep(3)

        # Take screenshots after scrolling
        local_page.screenshot(path="local_cards_after_scroll.png", full_page=False)
        prod_page.screenshot(path="production_cards_after_scroll.png", full_page=False)

        print("\nScreenshots saved:")
        print("  - local_cards_after_scroll.png (should show white cards)")
        print("  - production_cards_after_scroll.png (beautiful white cards)")
        
        print("\nBrowsers kept open for manual inspection.")
        print("Check if LOCAL now matches PRODUCTION's beautiful white card design!")
        
        # Keep browsers open for 10 seconds
        time.sleep(10)

        browser.close()

if __name__ == "__main__":
    verify_mini_cards_ui()
