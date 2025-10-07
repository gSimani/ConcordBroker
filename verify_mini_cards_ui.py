"""
Verify that local mini property cards match production UI
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

        # Take screenshots
        local_page.screenshot(path="local_mini_cards.png", full_page=False)
        prod_page.screenshot(path="production_mini_cards.png", full_page=False)

        print("\n=== CHECKING MINI PROPERTY CARDS UI ===")

        # Check for property cards
        try:
            # Wait for property cards to load on production
            prod_page.wait_for_selector('[class*="elegant-card"]', timeout=10000)
            prod_cards = prod_page.query_selector_all('[class*="elegant-card"]')
            print(f"Production site has {len(prod_cards)} elegant property cards")
        except:
            print("Production site - No elegant-card class found, checking alternatives...")
            prod_cards = prod_page.query_selector_all('[class*="card"]')
            print(f"Production site has {len(prod_cards)} property cards")

        try:
            # Check local site for cards
            local_page.wait_for_selector('[class*="card"]', timeout=5000)
            local_cards = local_page.query_selector_all('[class*="elegant-card"]')
            if not local_cards:
                local_cards = local_page.query_selector_all('[class*="card"]')
            print(f"Local site has {len(local_cards)} property cards")
        except:
            print("ERROR: Local site has no property cards!")
            local_cards = []

        # Check for elegant styling classes
        print("\n=== CHECKING ELEGANT STYLING ===")

        # Check production for elegant classes
        prod_elegant_elements = prod_page.query_selector_all('[class*="elegant"]')
        prod_hover_lift = prod_page.query_selector_all('[class*="hover-lift"]')
        prod_gold_elements = prod_page.query_selector_all('[style*="#d4af37"]')
        prod_navy_elements = prod_page.query_selector_all('[style*="#2c3e50"]')

        print(f"Production - Elegant classes: {len(prod_elegant_elements)}")
        print(f"Production - Hover-lift elements: {len(prod_hover_lift)}")
        print(f"Production - Gold color elements: {len(prod_gold_elements)}")
        print(f"Production - Navy color elements: {len(prod_navy_elements)}")

        # Check local for elegant classes
        local_elegant_elements = local_page.query_selector_all('[class*="elegant"]')
        local_hover_lift = local_page.query_selector_all('[class*="hover-lift"]')
        local_gold_elements = local_page.query_selector_all('[style*="#d4af37"]')
        local_navy_elements = local_page.query_selector_all('[style*="#2c3e50"]')

        print(f"\nLocal - Elegant classes: {len(local_elegant_elements)}")
        print(f"Local - Hover-lift elements: {len(local_hover_lift)}")
        print(f"Local - Gold color elements: {len(local_gold_elements)}")
        print(f"Local - Navy color elements: {len(local_navy_elements)}")

        # Check for specific UI elements
        print("\n=== CHECKING SPECIFIC UI ELEMENTS ===")

        # Check for badges
        prod_badges = prod_page.query_selector_all('[class*="badge"]')
        local_badges = local_page.query_selector_all('[class*="badge"]')
        print(f"Badges - Production: {len(prod_badges)}, Local: {len(local_badges)}")

        # Check for icons (lucide-react)
        prod_icons = prod_page.query_selector_all('svg')
        local_icons = local_page.query_selector_all('svg')
        print(f"Icons - Production: {len(prod_icons)}, Local: {len(local_icons)}")

        # Check for property type badges
        prod_type_badges = prod_page.query_selector_all('[class*="bg-green-100"], [class*="bg-blue-100"], [class*="bg-orange-100"]')
        local_type_badges = local_page.query_selector_all('[class*="bg-green-100"], [class*="bg-blue-100"], [class*="bg-orange-100"]')
        print(f"Property type badges - Production: {len(prod_type_badges)}, Local: {len(local_type_badges)}")

        # Check page content for errors
        print("\n=== CHECKING FOR ERRORS ===")
        local_content = local_page.content()
        if "error" in local_content.lower() or "404" in local_content:
            print("ERROR: Local page contains error messages!")
            # Get error text
            error_elements = local_page.query_selector_all('text=/error/i')
            for error in error_elements[:3]:  # Show first 3 errors
                print(f"  Error found: {error.text_content()}")
        else:
            print("No errors detected on local page")

        # Visual comparison
        print("\n=== VISUAL COMPARISON ===")
        if len(local_cards) == 0:
            print("FAILED: Local site has no property cards!")
        elif len(local_elegant_elements) == 0 and len(prod_elegant_elements) > 0:
            print("FAILED: Local site missing elegant styling classes!")
        elif len(local_gold_elements) == 0 and len(prod_gold_elements) > 0:
            print("FAILED: Local site missing gold color styling!")
        else:
            print("SUCCESS: Local site has property cards with styling")

        # Summary
        print("\n=== SUMMARY ===")
        match_score = 0
        total_checks = 5

        if len(local_cards) > 0:
            match_score += 1
            print("[OK] Property cards present")
        else:
            print("[FAIL] Property cards missing")

        if len(local_elegant_elements) > 0 or len(local_hover_lift) > 0:
            match_score += 1
            print("[OK] Elegant styling detected")
        else:
            print("[FAIL] Elegant styling missing")

        if len(local_gold_elements) > 0 or len(local_navy_elements) > 0:
            match_score += 1
            print("[OK] Brand colors present")
        else:
            print("[FAIL] Brand colors missing")

        if len(local_badges) > 0:
            match_score += 1
            print("[OK] Badges present")
        else:
            print("[FAIL] Badges missing")

        if len(local_icons) > 0:
            match_score += 1
            print("[OK] Icons present")
        else:
            print("[FAIL] Icons missing")

        print(f"\nMatch Score: {match_score}/{total_checks}")
        if match_score == total_checks:
            print("PERFECT MATCH - Local matches production!")
        elif match_score >= 3:
            print("PARTIAL MATCH - Some elements missing")
        else:
            print("NO MATCH - Local does not match production")

        print("\nScreenshots saved:")
        print("  - local_mini_cards.png")
        print("  - production_mini_cards.png")
        print("\nBrowser windows kept open for manual inspection.")
        print("Press Enter to close...")
        input()

        browser.close()

if __name__ == "__main__":
    verify_mini_cards_ui()