"""
BROWARD County Tax Deed Scraper (DeedAuction.net Platform)
Different platform from Palm Beach/Miami-Dade
"""

import os
import sys
import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv('.env.mcp')

# BROWARD configuration
BROWARD_URL = os.getenv('BROWARD_TAX_DEED_URL', 'https://broward.deedauction.net/')
USERNAME = os.getenv('TAX_DEED_USERNAME')
PASSWORD = os.getenv('TAX_DEED_PASSWORD')

def clean_currency(value: str) -> float:
    """Convert currency string to float"""
    if not value or value == '-' or value.lower() == 'n/a':
        return None
    # Remove $, commas, and whitespace
    cleaned = re.sub(r'[$,\s]', '', value)
    try:
        return float(cleaned)
    except:
        return None

async def scrape_broward_auctions() -> List[Dict[str, Any]]:
    """Scrape BROWARD tax deed auctions from DeedAuction.net"""

    print("="*80)
    print("BROWARD COUNTY TAX DEED SCRAPER (DeedAuction.net)")
    print("="*80)

    async with async_playwright() as playwright:
        # Launch browser
        print("[1/6] Launching browser...")
        browser = await playwright.chromium.launch(headless=False)  # Visible for testing
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        try:
            # Navigate to BROWARD tax deed site
            print(f"[2/6] Navigating to {BROWARD_URL}...")
            await page.goto(BROWARD_URL, wait_until='networkidle')
            await asyncio.sleep(2)

            # Check if login is required
            print("[3/6] Checking login requirements...")
            login_needed = await page.locator('input[type="text"], input[type="email"], input[name*="user"], input[name*="login"]').count() > 0

            if login_needed and USERNAME and PASSWORD:
                print("    Login required - attempting to authenticate...")

                # Try to find username field
                username_selectors = [
                    'input[name="username"]',
                    'input[name="email"]',
                    'input[type="text"]',
                    'input[id*="user"]'
                ]

                for selector in username_selectors:
                    if await page.locator(selector).count() > 0:
                        await page.fill(selector, USERNAME)
                        print(f"    ✓ Filled username field")
                        break

                # Try to find password field
                password_selectors = [
                    'input[name="password"]',
                    'input[type="password"]'
                ]

                for selector in password_selectors:
                    if await page.locator(selector).count() > 0:
                        await page.fill(selector, PASSWORD)
                        print(f"    ✓ Filled password field")
                        break

                # Find and click login button
                login_button_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")'
                ]

                for selector in login_button_selectors:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector)
                        print(f"    ✓ Clicked login button")
                        await page.wait_for_load_state('networkidle')
                        await asyncio.sleep(2)
                        break

            # Navigate to auctions page
            print("[4/6] Looking for auctions...")

            # Try to find auction listings
            auction_link_selectors = [
                'a:has-text("Auctions")',
                'a:has-text("Tax Deed")',
                'a:has-text("Properties")',
                'a[href*="auction"]',
                'a[href*="property"]'
            ]

            for selector in auction_link_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"    Found auction link: {selector}")
                    await page.click(selector)
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                    break

            # Take screenshot for debugging (optional)
            try:
                await page.screenshot(path='broward_auction_page.png', timeout=5000)
                print("    Screenshot saved: broward_auction_page.png")
            except:
                print("    Screenshot skipped (page still loading)")

            # Extract auction data (both upcoming and past)
            print("[5/6] Extracting auction data...")

            auctions = await page.evaluate("""
                () => {
                    const results = {
                        upcoming: [],
                        past: []
                    };

                    // Find the "Past Auctions" heading and get the table that follows it
                    const allText = document.body.innerText;
                    const hasPastAuctions = allText.includes('Past Auctions');

                    if (hasPastAuctions) {
                        // Get all tables
                        const tables = document.querySelectorAll('table');

                        tables.forEach(table => {
                            // Check if table has the right column headers
                            const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                            const isPastTable = headers.some(h => h.includes('Description') || h === '# of Items');

                            if (isPastTable) {
                                const rows = table.querySelectorAll('tbody tr');
                                rows.forEach(row => {
                                    const cells = row.querySelectorAll('td');
                                    if (cells.length >= 3) {
                                        const description = cells[0]?.innerText?.trim() || '';
                                        const itemCountText = cells[1]?.innerText?.trim() || '0';
                                        const status = cells[2]?.innerText?.trim() || 'Unknown';

                                        // Only process if it looks like a past auction (has date and "Sale" in description)
                                        const dateMatch = description.match(/(\\d{1,2}\\/\\d{1,2}\\/\\d{4})/);
                                        const hasSale = description.toLowerCase().includes('sale');

                                        if (dateMatch && hasSale) {
                                            const auctionDate = dateMatch[1];
                                            const itemCount = parseInt(itemCountText) || 0;

                                            results.past.push({
                                                description: description,
                                                auction_date: auctionDate,
                                                item_count: itemCount,
                                                status: status,
                                                type: 'Past Auction'
                                            });
                                        }
                                    }
                                });
                            }
                        });
                    }

                    return results;
                }
            """)

            print(f"    Upcoming auctions: {len(auctions.get('upcoming', []))}")
            print(f"    Past auctions: {len(auctions.get('past', []))}")

            # Process past auction summary data
            structured_auctions = []

            for idx, past_auction in enumerate(auctions.get('past', []), 1):
                try:
                    # Create a summary entry for this past auction
                    auction_entry = {
                        'case_number': f"BROWARD-PAST-{past_auction['auction_date'].replace('/', '')}",
                        'parcel_id': None,
                        'address': f"Past Auction: {past_auction['description']}",
                        'full_address': past_auction['description'],
                        'opening_bid_clean': 0,
                        'assessed_value_clean': 0,
                        'county': 'BROWARD',
                        'status': 'Past',
                        'item_status': past_auction['status'],
                        'source_url': BROWARD_URL,
                        'scraped_at': datetime.now().isoformat(),
                        'auction_date': past_auction['auction_date'],
                        'certificate': f"{past_auction['item_count']} items",
                        'auction_description': f"{past_auction['description']} - {past_auction['item_count']} items ({past_auction['status']})"
                    }
                    structured_auctions.append(auction_entry)
                    print(f"    [{idx}] {past_auction['auction_date']}: {past_auction['item_count']} items - {past_auction['status']}")

                except Exception as e:
                    print(f"    ✗ Error processing past auction {idx}: {e}")
                    continue

            print(f"\n[6/6] Extraction complete!")
            print(f"    ✓ Past auction summaries: {len(structured_auctions)}")

            return structured_auctions

        finally:
            await browser.close()

async def main():
    """Main execution"""

    print(f"\nBROWARD Credentials:")
    print(f"  Username: {USERNAME}")
    print(f"  Password: {'*' * len(PASSWORD) if PASSWORD else 'Not set'}")
    print()

    # Scrape auctions
    auctions = await scrape_broward_auctions()

    if not auctions:
        print("\n⚠️  No auctions found!")
        print("This could mean:")
        print("  - No active auctions currently")
        print("  - Website structure changed")
        print("  - Login credentials needed")
        print("  - Different page navigation required")
        print("\nCheck screenshot: broward_auction_page.png")
        return

    # Save to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'broward_tax_deed_auctions_{timestamp}.json'

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(auctions, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*80}")
    print(f"✓ Total auctions: {len(auctions)}")
    print(f"✓ Saved to: {filename}")
    print(f"✓ Screenshot: broward_auction_page.png")

    # Summary
    print(f"\nCounty Breakdown:")
    print(f"  BROWARD: {len(auctions)} auctions")

    if auctions:
        total_bids = sum(a['opening_bid_clean'] for a in auctions if a.get('opening_bid_clean'))
        avg_bid = total_bids / len([a for a in auctions if a.get('opening_bid_clean')]) if any(a.get('opening_bid_clean') for a in auctions) else 0

        print(f"\nBid Statistics:")
        print(f"  Total Opening Bids: ${total_bids:,.2f}")
        print(f"  Average Bid: ${avg_bid:,.2f}")

    print(f"\n✅ Next step: Upload with `python scripts/upload_tax_deed_fixed_env.py`")

if __name__ == "__main__":
    asyncio.run(main())
