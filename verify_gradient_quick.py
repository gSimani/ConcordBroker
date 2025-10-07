import asyncio
from playwright.async_api import async_playwright

async def verify_gradient_borders():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        # Test local environment
        print("\n=== Testing Local Environment ===")
        local_page = await browser.new_page()

        try:
            print("Loading local properties page...")
            await local_page.goto('http://localhost:5173/properties', wait_until='domcontentloaded', timeout=10000)
            await local_page.wait_for_timeout(2000)

            # Scroll down to see property cards
            print("Scrolling to view property cards...")
            await local_page.evaluate('window.scrollBy(0, 400)')
            await local_page.wait_for_timeout(1000)

            # Take screenshot
            await local_page.screenshot(path='local_cards_with_gradient.png')
            print("Screenshot saved: local_cards_with_gradient.png")

        except Exception as e:
            print(f"Error testing local: {e}")
            await local_page.screenshot(path='local_error.png')

        # Test production environment
        print("\n=== Testing Production Environment ===")
        prod_page = await browser.new_page()

        try:
            print("Loading production properties page...")
            await prod_page.goto('https://www.concordbroker.com/properties', wait_until='domcontentloaded', timeout=10000)
            await prod_page.wait_for_timeout(2000)

            # Scroll down to see property cards
            print("Scrolling to view property cards...")
            await prod_page.evaluate('window.scrollBy(0, 400)')
            await prod_page.wait_for_timeout(1000)

            # Take screenshot
            await prod_page.screenshot(path='production_cards_reference.png')
            print("Screenshot saved: production_cards_reference.png")

        except Exception as e:
            print(f"Error testing production: {e}")
            await prod_page.screenshot(path='production_error.png')

        print("\n=== Verification Complete ===")
        print("Check screenshots to confirm gradient borders match:")
        print("1. local_cards_with_gradient.png")
        print("2. production_cards_reference.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_gradient_borders())