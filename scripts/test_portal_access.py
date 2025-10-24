"""
Test Florida Revenue Portal Access
Tests whether we can navigate to the portal and identify file structure using Playwright
"""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Florida Revenue Data Portal URL
PORTAL_URL = "https://floridarevenue.com/property/dataportal/"


async def test_portal_access():
    """Test access to Florida Revenue portal"""

    print("=" * 80)
    print("TESTING FLORIDA REVENUE PORTAL ACCESS")
    print("=" * 80)

    print(f"\n🌐 Portal URL: {PORTAL_URL}")
    print("🤖 Launching browser...")

    async with async_playwright() as p:
        # Launch browser (headless=False to see what's happening)
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            print("\n📡 Navigating to portal...")
            await page.goto(PORTAL_URL, wait_until='networkidle', timeout=30000)

            print("✅ Page loaded successfully")

            # Get page title
            title = await page.title()
            print(f"\n📄 Page title: {title}")

            # Take screenshot
            screenshot_path = Path(__file__).parent.parent / 'test-screenshots' / 'portal-homepage.png'
            screenshot_path.parent.mkdir(exist_ok=True)
            await page.screenshot(path=str(screenshot_path))
            print(f"📸 Screenshot saved: {screenshot_path}")

            # Look for navigation elements
            print("\n🔍 Searching for navigation elements...")

            # Try to find "Tax Roll Data Files" link or folder
            print("   Looking for 'Tax Roll Data Files'...")
            elements = await page.query_selector_all("a, span, div")

            found_links = []
            for element in elements[:100]:  # Check first 100 elements
                text = await element.text_content()
                if text and 'tax roll' in text.lower():
                    found_links.append(text.strip())

            if found_links:
                print(f"   ✅ Found {len(found_links)} related links:")
                for link in found_links[:5]:
                    print(f"      - {link}")
            else:
                print("   ⚠️  'Tax Roll Data Files' not found on page")

            # Look for document library
            print("\n   Looking for document structure...")
            folders = await page.query_selector_all("[role='row'], .ms-List-cell, .od-ItemTile")
            print(f"   Found {len(folders)} potential items")

            # Try to click into data portal if link found
            if found_links:
                print("\n🖱️  Attempting to navigate to Tax Roll Data Files...")
                try:
                    # Look for the specific link
                    link = await page.query_selector("text=/Tax Roll Data Files/i")
                    if link:
                        await link.click()
                        await page.wait_for_load_state('networkidle', timeout=10000)

                        # Take another screenshot
                        screenshot_path2 = Path(__file__).parent.parent / 'test-screenshots' / 'portal-tax-roll.png'
                        await page.screenshot(path=str(screenshot_path2))
                        print(f"   ✅ Navigated successfully")
                        print(f"   📸 Screenshot: {screenshot_path2}")

                        # Try to find county folders
                        print("\n   🔍 Looking for county folders...")
                        county_folders = await page.query_selector_all("a[href*='NAL'], a[href*='NAP'], a[href*='NAV'], a[href*='SDF']")

                        if county_folders:
                            print(f"   ✅ Found {len(county_folders)} file type folders")

                        # Try to find a NAL folder
                        nal_link = await page.query_selector("text=/NAL/i")
                        if nal_link:
                            print("\n   🖱️  Navigating to NAL folder...")
                            await nal_link.click()
                            await page.wait_for_load_state('networkidle', timeout=10000)

                            screenshot_path3 = Path(__file__).parent.parent / 'test-screenshots' / 'portal-nal-folder.png'
                            await page.screenshot(path=str(screenshot_path3))
                            print(f"   ✅ NAL folder accessed")
                            print(f"   📸 Screenshot: {screenshot_path3}")

                            # List files
                            files = await page.query_selector_all("a[href$='.txt'], a[href$='.csv']")
                            if files:
                                print(f"\n   📁 Found {len(files)} data files")
                                for i, file_elem in enumerate(files[:5]):
                                    filename = await file_elem.text_content()
                                    print(f"      {i+1}. {filename.strip()}")

                except Exception as e:
                    print(f"   ⚠️  Could not navigate: {e}")

            # Wait a bit so user can see the browser
            print("\n⏳ Waiting 5 seconds (browser will stay open)...")
            await asyncio.sleep(5)

            print("\n" + "=" * 80)
            print("✅ PORTAL ACCESS TEST COMPLETE")
            print("=" * 80)

            print("\n📊 Summary:")
            print("   - Portal is accessible: ✅")
            print(f"   - Found navigation elements: {'✅' if found_links else '⚠️'}")
            print(f"   - Screenshots saved: test-screenshots/")

            print("\n💡 Next steps:")
            print("   1. Review screenshots to understand portal structure")
            print("   2. Implement file download logic based on findings")
            print("   3. Create file parser for NAL/NAP/NAV/SDF formats")

        except Exception as e:
            print(f"\n❌ Error: {e}")

            # Take error screenshot
            try:
                error_path = Path(__file__).parent.parent / 'test-screenshots' / 'portal-error.png'
                await page.screenshot(path=str(error_path))
                print(f"📸 Error screenshot: {error_path}")
            except:
                pass

        finally:
            # Close browser
            print("\n🔚 Closing browser...")
            await browser.close()


def main():
    """Main entry point"""

    # Check if playwright is installed
    try:
        import playwright
        print("✅ Playwright is installed")
    except ImportError:
        print("❌ Playwright not installed")
        print("\n💡 Install with:")
        print("   pip install playwright")
        print("   playwright install chromium")
        sys.exit(1)

    # Run async test
    asyncio.run(test_portal_access())


if __name__ == '__main__':
    main()
