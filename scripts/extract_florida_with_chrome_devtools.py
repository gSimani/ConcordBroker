"""
Extract ALL Florida Counties from RealAuction.com using Chrome DevTools MCP
Navigates through all 5 pages to capture complete county list
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def extract_all_florida_counties():
    print("="*80)
    print("REALAUCTION.COM - COMPLETE FLORIDA COUNTIES EXTRACTION")
    print("="*80)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        all_florida_counties = {}

        try:
            # Navigate to clients page
            clients_url = 'https://www.realauction.com/clients'
            print(f"📍 Navigating to: {clients_url}")
            await page.goto(clients_url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            print("✅ Page loaded")
            print()

            # Extract data from all pages (1-5)
            for page_num in range(1, 6):
                print(f"📄 Extracting Page {page_num}/5...")

                # Extract Florida county data from current page
                florida_data = await page.evaluate("""
                    () => {
                        const entries = [];

                        // Find all static text elements
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );

                        const texts = [];
                        let node;
                        while (node = walker.nextNode()) {
                            const text = node.textContent.trim();
                            if (text) {
                                texts.push(text);
                            }
                        }

                        // Look for Florida section and extract counties
                        let inFloridaSection = false;
                        let currentCounty = null;

                        for (let i = 0; i < texts.length; i++) {
                            const text = texts[i];

                            // Check if we've entered Florida section
                            if (text === 'FLORIDA') {
                                inFloridaSection = true;
                                continue;
                            }

                            // Check if we've left Florida section (next state)
                            if (inFloridaSection && (
                                text === 'GEORGIA' ||
                                text === 'IDAHO' ||
                                text === 'ILLINOIS' ||
                                text === 'INDIANA' ||
                                text === 'LOUISIANA' ||
                                text === 'MICHIGAN' ||
                                text === 'NEW JERSEY' ||
                                text === 'NEW YORK' ||
                                text === 'OHIO' ||
                                text === 'PENNSYLVANIA' ||
                                text === 'TEXAS' ||
                                text === 'WASHINGTON' ||
                                text === 'Location'
                            )) {
                                inFloridaSection = false;
                                break;
                            }

                            if (inFloridaSection) {
                                // Check if this is a county name (ends with "County " or "County")
                                if (text.includes('County')) {
                                    currentCounty = text.replace('County', '').trim();
                                } else if (currentCounty) {
                                    // This is likely an auction type for the current county
                                    if (text.includes('Foreclosure') ||
                                        text.includes('Tax Deed') ||
                                        text.includes('Tax Lien') ||
                                        text.includes('Sale')) {
                                        entries.push({
                                            county: currentCounty,
                                            auctionType: text
                                        });
                                    }
                                }
                            }
                        }

                        return entries;
                    }
                """)

                # Add to consolidated data
                for entry in florida_data:
                    county = entry['county']
                    auction_type = entry['auctionType']

                    if county not in all_florida_counties:
                        all_florida_counties[county] = {
                            'county': county,
                            'foreclosures': [],
                            'tax_deeds': [],
                            'tax_liens': [],
                            'other': []
                        }

                    # Categorize auction type
                    if 'Foreclosure' in auction_type:
                        if auction_type not in [a['type'] for a in all_florida_counties[county]['foreclosures']]:
                            all_florida_counties[county]['foreclosures'].append({
                                'type': auction_type,
                                'source_page': page_num
                            })

                    if 'Tax Deed' in auction_type:
                        if auction_type not in [a['type'] for a in all_florida_counties[county]['tax_deeds']]:
                            all_florida_counties[county]['tax_deeds'].append({
                                'type': auction_type,
                                'source_page': page_num
                            })

                    if 'Tax Lien' in auction_type or 'Tax Certificate' in auction_type:
                        if auction_type not in [a['type'] for a in all_florida_counties[county]['tax_liens']]:
                            all_florida_counties[county]['tax_liens'].append({
                                'type': auction_type,
                                'source_page': page_num
                            })

                print(f"   ✅ Found {len(florida_data)} entries on page {page_num}")

                # Navigate to next page (if not last page)
                if page_num < 5:
                    next_button = await page.query_selector(f'button:has-text("{page_num + 1}")')
                    if next_button:
                        await next_button.click()
                        await page.wait_for_timeout(2000)

            print()
            print("="*80)
            print("FLORIDA COUNTIES - COMPLETE EXTRACTION")
            print("="*80)
            print()

            # Display results
            for county, data in sorted(all_florida_counties.items()):
                print(f"📍 {county.upper()} COUNTY:")

                total_platforms = (
                    len(data['foreclosures']) +
                    len(data['tax_deeds']) +
                    len(data['tax_liens'])
                )

                if data['foreclosures']:
                    print(f"   🏛️  Foreclosures: {len(data['foreclosures'])} platform(s)")
                    for fc in data['foreclosures']:
                        print(f"      - {fc['type']} (Page {fc['source_page']})")

                if data['tax_deeds']:
                    print(f"   📋 Tax Deed Sales: {len(data['tax_deeds'])} platform(s)")
                    for td in data['tax_deeds']:
                        print(f"      - {td['type']} (Page {td['source_page']})")

                if data['tax_liens']:
                    print(f"   💰 Tax Liens: {len(data['tax_liens'])} platform(s)")
                    for tl in data['tax_liens']:
                        print(f"      - {tl['type']} (Page {tl['source_page']})")

                print()

            # Save results
            results = {
                'timestamp': datetime.now().isoformat(),
                'source_url': clients_url,
                'total_counties_found': len(all_florida_counties),
                'counties': all_florida_counties
            }

            output_file = f'florida_counties_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"💾 Complete data saved to: {output_file}")
            print()

            # Summary statistics
            print("="*80)
            print("EXTRACTION SUMMARY")
            print("="*80)
            print(f"Total Florida counties found: {len(all_florida_counties)}")

            foreclosure_count = sum(1 for c in all_florida_counties.values() if c['foreclosures'])
            tax_deed_count = sum(1 for c in all_florida_counties.values() if c['tax_deeds'])
            tax_lien_count = sum(1 for c in all_florida_counties.values() if c['tax_liens'])

            print(f"Counties with foreclosures: {foreclosure_count}")
            print(f"Counties with tax deed sales: {tax_deed_count}")
            print(f"Counties with tax liens: {tax_lien_count}")
            print()

            print("All counties mapped:")
            for i, county in enumerate(sorted(all_florida_counties.keys()), 1):
                print(f"  {i}. {county}")
            print()

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='florida_extraction_error.png', full_page=True)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_all_florida_counties())
