"""
Quick Search Bar Test
Tests the search functionality at http://localhost:5174/properties immediately
"""

import asyncio
from playwright.async_api import async_playwright
import time
import json

async def test_search_bar():
    """Quick test of the search bar functionality"""

    print("🔍 Testing Search Bar at http://localhost:5174/properties")
    print("="*60)

    # Launch browser
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    try:
        # Navigate to the page
        print("📍 Navigating to properties page...")
        await page.goto("http://localhost:5174/properties", wait_until='networkidle', timeout=10000)

        # Check if search bar exists
        search_input = await page.query_selector('input[placeholder*="Search"]')
        if not search_input:
            print("❌ Search bar not found!")
            return

        print("✅ Search bar found!")

        # Get search bar info
        placeholder = await search_input.get_attribute('placeholder')
        print(f"📝 Placeholder text: {placeholder}")

        # Test cases
        test_searches = [
            "Miami",
            "123 Main",
            "Smith",
            "33101"
        ]

        for i, search_term in enumerate(test_searches, 1):
            print(f"\n🔍 Test {i}: Searching for '{search_term}'")

            # Clear and enter search term
            await search_input.clear()
            await search_input.fill(search_term)
            print(f"   ✓ Entered: {search_term}")

            # Wait a moment for any autocomplete
            await page.wait_for_timeout(1000)

            # Press Enter to search
            await search_input.press("Enter")
            print(f"   ✓ Pressed Enter")

            # Wait for results
            await page.wait_for_timeout(3000)

            # Check for results
            # Look for various possible result containers
            result_selectors = [
                '.property-card',
                '[data-testid="property-card"]',
                '[class*="property"]',
                '.search-result',
                'div[role="listitem"]',
                '.grid > div',
                '.list-item'
            ]

            results_found = False
            result_count = 0

            for selector in result_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    result_count = len(elements)
                    results_found = True
                    print(f"   ✅ Found {result_count} results using selector: {selector}")
                    break

            if not results_found:
                # Check for "no results" message
                page_content = await page.content()
                if "no results" in page_content.lower() or "not found" in page_content.lower():
                    print(f"   ℹ️  No results found for '{search_term}'")
                else:
                    print(f"   ❓ Results unclear - checking page content...")

                    # Take screenshot for manual inspection
                    screenshot_path = f"search_test_{search_term.replace(' ', '_')}_{int(time.time())}.png"
                    await page.screenshot(path=screenshot_path)
                    print(f"   📷 Screenshot saved: {screenshot_path}")

            # Get current URL to see if it changed
            current_url = page.url
            print(f"   📍 Current URL: {current_url}")

            # Extract any visible text that might indicate search is working
            try:
                search_info = await page.evaluate("""
                    () => {
                        const searchInput = document.querySelector('input[placeholder*="Search"]');
                        const resultsArea = document.querySelector('main, .results, .content, [role="main"]');

                        return {
                            searchValue: searchInput ? searchInput.value : 'not found',
                            hasResultsArea: !!resultsArea,
                            visibleText: resultsArea ? resultsArea.textContent.substring(0, 200) : 'no results area',
                            totalElements: document.querySelectorAll('div').length
                        };
                    }
                """)

                print(f"   📊 Search input value: {search_info['searchValue']}")
                print(f"   📊 Has results area: {search_info['hasResultsArea']}")
                print(f"   📊 Page elements: {search_info['totalElements']}")

                if search_info['visibleText']:
                    print(f"   📊 Visible content: {search_info['visibleText'][:100]}...")

            except Exception as e:
                print(f"   ❌ Error extracting search info: {e}")

        # Test with empty search
        print(f"\n🔍 Test {len(test_searches)+1}: Empty search")
        await search_input.clear()
        await search_input.press("Enter")
        await page.wait_for_timeout(2000)
        print("   ✓ Empty search test completed")

        # Final assessment
        print("\n" + "="*60)
        print("📋 SEARCH BAR ASSESSMENT")
        print("="*60)
        print("✅ Search bar is present and interactive")
        print("✅ Can enter search terms")
        print("✅ Can trigger search with Enter key")
        print("ℹ️  Check screenshots for visual confirmation of results")

        # Check if database connection seems to be working
        try:
            # Test if we can see any property data at all
            all_text = await page.evaluate("() => document.body.textContent")

            # Look for indicators that data is loading
            data_indicators = ['property', 'address', 'owner', 'value', '$', 'parcel']
            data_found = any(indicator in all_text.lower() for indicator in data_indicators)

            if data_found:
                print("✅ Property data appears to be loaded")
            else:
                print("❓ Property data may not be loaded - check database connection")

        except Exception as e:
            print(f"❌ Error checking data: {e}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        await browser.close()
        await playwright.stop()

async def main():
    await test_search_bar()

if __name__ == "__main__":
    asyncio.run(main())