#!/usr/bin/env python3
"""
Test frontend to see if owner names are being displayed correctly
"""

import asyncio
from playwright.async_api import async_playwright
import time
import json

async def test_frontend_owner_names():
    """Test frontend owner name display"""

    print("TESTING FRONTEND OWNER NAME DISPLAY")
    print("=" * 50)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()

    try:
        # Enable console logging
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

        # Navigate to properties page
        print("1. Navigating to http://localhost:5174/properties")
        await page.goto("http://localhost:5174/properties", wait_until='networkidle', timeout=15000)

        # Wait for page to load
        await page.wait_for_timeout(3000)

        # Check if properties are displayed
        print("\n2. Checking for property cards...")

        # Look for property cards
        property_cards = await page.query_selector_all('.elegant-card, .property-card, [data-testid="property-card"]')

        if property_cards:
            print(f"Found {len(property_cards)} property cards")

            # Extract owner information from first few cards
            for i, card in enumerate(property_cards[:3], 1):
                print(f"\n--- Property Card {i} ---")

                # Try to extract owner name using different selectors
                owner_selectors = [
                    # From MiniPropertyCard.tsx line 372
                    'text=Owner',
                    # Look for elements that contain owner data
                    '[class*="owner"]',
                    # Generic text content
                    'div'
                ]

                card_text = await card.text_content()
                print(f"Card full text: {card_text[:200]}...")

                # Look for "Owner" label and check what follows
                if "Owner" in card_text:
                    print("Found 'Owner' label in card")

                    # Extract the specific owner section
                    owner_section = await card.query_selector('text=Owner')
                    if owner_section:
                        parent = await owner_section.query_selector('..')
                        if parent:
                            owner_text = await parent.text_content()
                            print(f"Owner section text: '{owner_text}'")

                            # Check if it shows "Unknown"
                            if "Unknown" in owner_text:
                                print("ISSUE: Owner shows as 'Unknown'")
                            else:
                                print("SUCCESS: Owner name is displayed")
                else:
                    print("No 'Owner' label found in this card")

        else:
            print("No property cards found on page")

            # Take screenshot for debugging
            await page.screenshot(path="no_properties_found.png")
            print("Screenshot saved: no_properties_found.png")

        # 3. Test with a specific search to see if owner names appear
        print("\n3. Testing search functionality...")

        search_input = await page.query_selector('input[placeholder*="Search"]')
        if search_input:
            print("Found search bar")

            # Search for "Charlotte" to get some results
            await search_input.clear()
            await search_input.fill("Charlotte")
            await search_input.press("Enter")

            # Wait for results
            await page.wait_for_timeout(3000)

            # Check results
            search_results = await page.query_selector_all('.elegant-card, .property-card')
            print(f"Search returned {len(search_results)} results")

            if search_results:
                # Check first result for owner name
                first_result = search_results[0]
                result_text = await first_result.text_content()
                print(f"First search result: {result_text[:300]}...")

                if "Owner" in result_text and "Unknown" in result_text:
                    print("CONFIRMED ISSUE: Search results show owners as 'Unknown'")
                elif "Owner" in result_text:
                    print("Owner information appears to be present")

        # 4. Check browser console for any errors
        print("\n4. Checking for JavaScript errors...")

        # Evaluate some JavaScript to check data
        data_check = await page.evaluate("""
            () => {
                // Check if there are any property cards and their data
                const cards = document.querySelectorAll('.elegant-card, .property-card');
                if (cards.length > 0) {
                    const firstCard = cards[0];
                    const ownerElements = firstCard.querySelectorAll('*');
                    let ownerData = [];

                    for (let el of ownerElements) {
                        if (el.textContent.includes('Owner') || el.textContent.includes('Unknown')) {
                            ownerData.push({
                                tag: el.tagName,
                                class: el.className,
                                text: el.textContent
                            });
                        }
                    }

                    return {
                        totalCards: cards.length,
                        ownerData: ownerData,
                        hasOwnerLabel: firstCard.textContent.includes('Owner'),
                        hasUnknown: firstCard.textContent.includes('Unknown')
                    };
                }
                return { totalCards: 0, ownerData: [], hasOwnerLabel: false, hasUnknown: false };
            }
        """)

        print(f"JavaScript data check: {json.dumps(data_check, indent=2)}")

        # Final screenshot
        await page.screenshot(path="frontend_owner_test.png")
        print("\nFinal screenshot saved: frontend_owner_test.png")

    except Exception as e:
        print(f"Error during test: {e}")
        await page.screenshot(path="error_screenshot.png")

    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_frontend_owner_names())