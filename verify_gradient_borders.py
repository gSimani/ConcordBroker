import asyncio
from playwright.async_api import async_playwright
import time

async def verify_gradient_borders():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        # Test local environment
        print("\n=== Testing Local Environment ===")
        local_page = await browser.new_page()

        try:
            print("Loading local properties page...")
            await local_page.goto('http://localhost:5173/properties', wait_until='networkidle')
            await local_page.wait_for_timeout(3000)

            # Scroll down to see property cards
            print("Scrolling to view property cards...")
            await local_page.evaluate('window.scrollBy(0, 400)')
            await local_page.wait_for_timeout(2000)

            # Check for elegant cards with gradient borders
            cards = await local_page.query_selector_all('.elegant-card, .card-executive, [class*="property-card"], [class*="mini-card"], .bg-white.rounded-lg')

            if cards:
                print(f"Found {len(cards)} cards on local")

                # Check the styling of first card
                first_card = cards[0]

                # Get computed styles
                has_gradient = await local_page.evaluate('''(element) => {
                    const styles = window.getComputedStyle(element, '::before');
                    const bg = styles.background || styles.backgroundImage;
                    return bg && bg.includes('gradient');
                }''', first_card)

                bg_color = await local_page.evaluate('''(element) => {
                    return window.getComputedStyle(element).backgroundColor;
                }''', first_card)

                print(f"Card has gradient border: {has_gradient}")
                print(f"Card background color: {bg_color}")

                # Take screenshot
                await local_page.screenshot(path='local_cards_verified.png')
                print("Screenshot saved: local_cards_verified.png")
            else:
                print("No property cards found - checking page structure...")
                await local_page.screenshot(path='local_page_debug.png')

        except Exception as e:
            print(f"Error testing local: {e}")
            await local_page.screenshot(path='local_error.png')

        # Test production environment
        print("\n=== Testing Production Environment ===")
        prod_page = await browser.new_page()

        try:
            print("Loading production properties page...")
            await prod_page.goto('https://www.concordbroker.com/properties', wait_until='networkidle')
            await prod_page.wait_for_timeout(3000)

            # Scroll down to see property cards
            print("Scrolling to view property cards...")
            await prod_page.evaluate('window.scrollBy(0, 400)')
            await prod_page.wait_for_timeout(2000)

            # Check for cards
            cards = await prod_page.query_selector_all('.elegant-card, .card-executive, [class*="property-card"], [class*="mini-card"], .bg-white.rounded-lg')

            if cards:
                print(f"Found {len(cards)} cards on production")

                # Take screenshot
                await prod_page.screenshot(path='production_cards_verified.png')
                print("Screenshot saved: production_cards_verified.png")
            else:
                print("No property cards found on production")
                await prod_page.screenshot(path='production_page_debug.png')

        except Exception as e:
            print(f"Error testing production: {e}")
            await prod_page.screenshot(path='production_error.png')

        print("\n=== Verification Complete ===")
        print("Please check the screenshots to confirm:")
        print("1. local_cards_verified.png - Should show cards with gradient top borders")
        print("2. production_cards_verified.png - Should show the same design")

        # Keep browser open for manual inspection
        print("\nBrowser will remain open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_gradient_borders())