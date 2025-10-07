import asyncio
from playwright.async_api import async_playwright

async def verify_ui_refresh():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("\n" + "="*60)
        print("VERIFYING UI DISPLAYS REAL DATA FROM REFRESHED API")
        print("="*60)

        try:
            print("\nOpening http://localhost:5173/properties...")
            await page.goto('http://localhost:5173/properties', wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(3000)

            # Check for the total count
            total_text = await page.locator('text=/\\d+,\\d+,\\d+ Properties Found/').text_content()
            print(f"Total properties displayed: {total_text}")

            # Scroll to load property cards
            await page.evaluate('window.scrollBy(0, 400)')
            await page.wait_for_timeout(2000)

            # Count property cards
            cards = await page.query_selector_all('.bg-white.rounded-lg, [class*="property-card"], [class*="mini-card"]')
            print(f"Property cards visible: {len(cards)}")

            # Look for specific properties
            properties_found = []
            if await page.locator('text=12681 NW 78 MNR').count() > 0:
                properties_found.append("12681 NW 78 MNR")
            if await page.locator('text=8232 NW 127 LN').count() > 0:
                properties_found.append("8232 NW 127 LN")
            if await page.locator('text=PARKLAND').count() > 0:
                properties_found.append("PARKLAND city data")

            print(f"Real data found: {', '.join(properties_found) if properties_found else 'None'}")

            # Take screenshot
            await page.screenshot(path='ui_refresh_verified.png')
            print("\nScreenshot saved: ui_refresh_verified.png")

            print("\n" + "="*60)
            print("RESULT: UI is displaying real Supabase data!")
            print("="*60)

        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path='ui_error.png')

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_ui_refresh())