"""
Verify that local production build matches live website
"""
from playwright.sync_api import sync_playwright
import time

def verify_production_parity():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Open two browser contexts for comparison
        context1 = browser.new_context(viewport={'width': 1280, 'height': 800})
        context2 = browser.new_context(viewport={'width': 1280, 'height': 800})

        # Open local and production pages
        local_page = context1.new_page()
        prod_page = context2.new_page()

        print("Opening local site...")
        local_page.goto("http://localhost:5173/properties")
        time.sleep(3)  # Wait for page to fully load

        print("Opening production site...")
        prod_page.goto("https://www.concordbroker.com/properties")
        time.sleep(3)  # Wait for page to fully load

        # Take screenshots
        local_page.screenshot(path="local_properties_page.png")
        prod_page.screenshot(path="production_properties_page.png")

        # Compare page titles
        local_title = local_page.title()
        prod_title = prod_page.title()
        print(f"Local title: {local_title}")
        print(f"Production title: {prod_title}")

        # Check for main elements
        try:
            # Check if search bar exists
            local_search = local_page.query_selector('input[placeholder*="Search"]')
            prod_search = prod_page.query_selector('input[placeholder*="Search"]')
            print(f"Search bar present - Local: {local_search is not None}, Production: {prod_search is not None}")

            # Check for property cards
            local_cards = len(local_page.query_selector_all('[class*="card"]'))
            prod_cards = len(prod_page.query_selector_all('[class*="card"]'))
            print(f"Property cards - Local: {local_cards}, Production: {prod_cards}")

            # Check for navigation
            local_nav = local_page.query_selector('nav')
            prod_nav = prod_page.query_selector('nav')
            print(f"Navigation present - Local: {local_nav is not None}, Production: {prod_nav is not None}")

            # Check for any error messages
            local_error = local_page.query_selector('text=/error/i')
            prod_error = prod_page.query_selector('text=/error/i')

            if local_error:
                print("ERROR: Local site shows error message!")
                error_text = local_page.text_content('body')[:500]
                print(f"Error content: {error_text}")
            else:
                print("✓ No errors on local site")

            if prod_error:
                print("ERROR: Production site shows error message!")
            else:
                print("✓ No errors on production site")

            # Visual comparison summary
            print("\n=== VISUAL COMPARISON SUMMARY ===")
            if local_title == prod_title and local_search and prod_search and not local_error:
                print("✅ Local and production sites appear to match!")
            else:
                print("❌ Sites do not match - see details above")

        except Exception as e:
            print(f"Error during comparison: {e}")

        # Keep browser open for manual inspection
        print("\nBrowser windows kept open for manual inspection.")
        print("Press Enter to close...")
        input()

        browser.close()

if __name__ == "__main__":
    verify_production_parity()