"""
Interactive Analysis of RealAuction.com - Select Florida and Extract All Counties
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def analyze_florida_counties_interactive():
    print("="*80)
    print("REALAUCTION.COM - FLORIDA COUNTIES INTERACTIVE ANALYSIS")
    print("="*80)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            # Navigate to clients page
            clients_url = 'https://www.realauction.com/clients'
            print(f"📍 Step 1: Navigating to {clients_url}")
            await page.goto(clients_url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            print("✅ Page loaded")
            print()

            # Take screenshot before interaction
            await page.screenshot(path='realauction_before_florida_select.png', full_page=True)
            print("📸 Screenshot (before): realauction_before_florida_select.png")
            print()

            # Find and select Florida from dropdown
            print("📍 Step 2: Finding state dropdown...")

            # Look for the select element
            state_select = await page.query_selector('select[name="stateid"], select#stateid, select[id*="state"]')

            if state_select:
                print("✅ Found state dropdown")

                # Get all options
                options = await page.evaluate("""
                    (select) => {
                        return Array.from(select.options).map(opt => ({
                            value: opt.value,
                            text: opt.text
                        }));
                    }
                """, state_select)

                print(f"   Options available: {len(options)}")
                for opt in options:
                    print(f"     - {opt['text']}: {opt['value']}")
                print()

                # Find Florida option
                florida_option = None
                for opt in options:
                    if 'florida' in opt['text'].lower() or opt['value'].lower() == 'fl':
                        florida_option = opt
                        break

                if florida_option:
                    print(f"📍 Step 3: Selecting Florida (value: {florida_option['value']})")

                    # Select Florida
                    await page.select_option('select[name="stateid"]', florida_option['value'])
                    print("✅ Florida selected")

                    # Wait for page to update
                    await page.wait_for_timeout(5000)

                    # Take screenshot after selection
                    await page.screenshot(path='realauction_after_florida_select.png', full_page=True)
                    print("📸 Screenshot (after): realauction_after_florida_select.png")
                    print()

                    # Extract county information
                    print("📍 Step 4: Extracting Florida county data...")

                    florida_data = await page.evaluate("""
                        () => {
                            const counties = [];

                            // Look for county links, tables, or lists
                            const allLinks = document.querySelectorAll('a');
                            const allRows = document.querySelectorAll('tr');
                            const allDivs = document.querySelectorAll('div');

                            // Extract from links
                            allLinks.forEach(link => {
                                const text = link.textContent.trim();
                                const href = link.getAttribute('href');

                                if (text && href) {
                                    counties.push({
                                        type: 'link',
                                        name: text,
                                        url: href,
                                        fullUrl: link.href
                                    });
                                }
                            });

                            // Extract from table rows
                            allRows.forEach(row => {
                                const cells = row.querySelectorAll('td, th');
                                if (cells.length > 0) {
                                    const rowData = {
                                        type: 'table_row',
                                        cells: Array.from(cells).map(cell => ({
                                            text: cell.textContent.trim(),
                                            links: Array.from(cell.querySelectorAll('a')).map(a => ({
                                                text: a.textContent.trim(),
                                                href: a.href
                                            }))
                                        }))
                                    };
                                    counties.push(rowData);
                                }
                            });

                            // Get full page text for analysis
                            const pageText = document.body.innerText;

                            return {
                                counties: counties,
                                pageText: pageText,
                                totalLinks: allLinks.length,
                                totalRows: allRows.length
                            };
                        }
                    """)

                    print(f"✅ Extracted {len(florida_data['counties'])} elements")
                    print(f"   Total links: {florida_data['totalLinks']}")
                    print(f"   Total table rows: {florida_data['totalRows']}")
                    print()

                    # Analyze and categorize
                    print("="*80)
                    print("FLORIDA COUNTIES FOUND")
                    print("="*80)
                    print()

                    # Filter for actual county data
                    county_keywords = [
                        'county', 'tax', 'deed', 'foreclosure', 'lien', 'auction',
                        'broward', 'miami', 'palm', 'hillsborough', 'orange', 'pinellas'
                    ]

                    relevant_items = []
                    for item in florida_data['counties']:
                        if item['type'] == 'link':
                            text_lower = item['name'].lower()
                            url_lower = item['url'].lower() if item['url'] else ''

                            # Check if it's relevant to counties/auctions
                            is_relevant = any(keyword in text_lower or keyword in url_lower for keyword in county_keywords)

                            if is_relevant:
                                relevant_items.append(item)
                                print(f"📍 {item['name']}")
                                print(f"   URL: {item['fullUrl']}")
                                print()

                    print(f"✅ Found {len(relevant_items)} relevant county items")
                    print()

                    # Check if there's a county-specific dropdown or search that appeared
                    print("📍 Step 5: Checking for county dropdown...")

                    county_selects = await page.query_selector_all('select')
                    print(f"   Found {len(county_selects)} select elements")

                    for i, select in enumerate(county_selects):
                        select_info = await page.evaluate("""
                            (select) => {
                                const opts = Array.from(select.options).map(opt => opt.text);
                                return {
                                    id: select.id,
                                    name: select.name,
                                    optionsCount: opts.length,
                                    sampleOptions: opts.slice(0, 10)
                                };
                            }
                        """, select)

                        print(f"\n   Select #{i+1}:")
                        print(f"     ID: {select_info['id']}")
                        print(f"     Name: {select_info['name']}")
                        print(f"     Options: {select_info['optionsCount']}")
                        if select_info['sampleOptions']:
                            print(f"     Sample: {', '.join(select_info['sampleOptions'][:5])}")

                    print()

                    # Save comprehensive results
                    results = {
                        'timestamp': datetime.now().isoformat(),
                        'source_url': clients_url,
                        'state_selected': 'Florida',
                        'relevant_counties': relevant_items,
                        'all_data': florida_data,
                        'selects_found': len(county_selects)
                    }

                    output_file = f'realauction_florida_detailed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)

                    print(f"💾 Complete data saved to: {output_file}")
                    print()

                    print("="*80)
                    print("SUMMARY")
                    print("="*80)
                    print(f"State: Florida")
                    print(f"Relevant county items found: {len(relevant_items)}")
                    print(f"Additional select dropdowns: {len(county_selects)}")
                    print()

                    print("⏳ Keeping browser open for 60 seconds for manual inspection...")
                    print("   You can click around to see if there are more counties...")
                    await page.wait_for_timeout(60000)

                else:
                    print("❌ Florida option not found in dropdown")
            else:
                print("❌ State dropdown not found")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='realauction_florida_error.png', full_page=True)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_florida_counties_interactive())
