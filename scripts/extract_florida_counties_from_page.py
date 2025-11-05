"""
Extract All Florida County Auction Data from RealAuction.com Clients Page
The page already displays all counties - no dropdown interaction needed!
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def extract_florida_counties():
    print("="*80)
    print("REALAUCTION.COM - FLORIDA COUNTIES EXTRACTION")
    print("="*80)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            # Navigate to clients page
            clients_url = 'https://www.realauction.com/clients'
            print(f"📍 Navigating to: {clients_url}")
            await page.goto(clients_url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            print("✅ Page loaded")
            print()

            # Extract all Florida county data
            print("📊 Extracting Florida county auction data...")

            florida_data = await page.evaluate("""
                () => {
                    const floridaCounties = [];

                    // Find the FLORIDA heading
                    const headings = Array.from(document.querySelectorAll('h3, h4, .heading, [class*="state"], [class*="State"]'));
                    let floridaSection = null;

                    for (const heading of headings) {
                        if (heading.textContent.toUpperCase().includes('FLORIDA')) {
                            floridaSection = heading;
                            break;
                        }
                    }

                    if (!floridaSection) {
                        // Try finding by looking for Florida county names
                        const allText = document.body.innerText;
                        if (allText.includes('Broward County') || allText.includes('Miami')) {
                            console.log('Florida content found but no heading');
                        }
                    }

                    // Get all county entries (look for "County" text followed by auction type links)
                    const allElements = document.querySelectorAll('*');
                    const countyPattern = /([A-Z][a-z]+(\s[A-Z][a-z]+)*)\s+County/;

                    const floridaCountyNames = [
                        'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD',
                        'CALHOUN', 'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA',
                        'DESOTO', 'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN',
                        'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON', 'HARDEE',
                        'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES',
                        'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE',
                        'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE',
                        'MARION', 'MARTIN', 'MIAMI-DADE', 'MIAMI DADE', 'MONROE', 'NASSAU', 'OKALOOSA',
                        'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS',
                        'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA', 'SEMINOLE', 'ST. JOHNS', 'ST JOHNS',
                        'ST. LUCIE', 'ST LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
                        'WAKULLA', 'WALTON', 'WASHINGTON'
                    ];

                    // Find all rows/items in the page
                    const rows = document.querySelectorAll('tr, .row, .item, .client-item, li');

                    rows.forEach(row => {
                        const text = row.innerText || row.textContent;
                        const upperText = text.toUpperCase();

                        // Check if this row contains a Florida county name
                        let countyFound = null;
                        for (const county of floridaCountyNames) {
                            if (upperText.includes(county + ' COUNTY')) {
                                countyFound = county;
                                break;
                            }
                        }

                        if (countyFound) {
                            // Extract all links in this row
                            const links = row.querySelectorAll('a');
                            const auctionTypes = [];

                            links.forEach(link => {
                                const linkText = link.textContent.trim();
                                const href = link.href;

                                // Determine auction type from link text
                                let auctionType = 'unknown';
                                if (linkText.toLowerCase().includes('foreclosure')) {
                                    auctionType = 'foreclosure';
                                } else if (linkText.toLowerCase().includes('tax deed')) {
                                    auctionType = 'tax_deed';
                                } else if (linkText.toLowerCase().includes('tax lien') || linkText.toLowerCase().includes('tax certificate')) {
                                    auctionType = 'tax_lien';
                                } else if (linkText.toLowerCase().includes('investment')) {
                                    auctionType = 'investment';
                                }

                                auctionTypes.push({
                                    type: auctionType,
                                    linkText: linkText,
                                    url: href
                                });
                            });

                            floridaCounties.push({
                                county: countyFound,
                                rawText: text,
                                auctionTypes: auctionTypes
                            });
                        }
                    });

                    return {
                        floridaCounties: floridaCounties,
                        totalFound: floridaCounties.length
                    };
                }
            """)

            print(f"✅ Found {florida_data['totalFound']} Florida county entries")
            print()

            # Organize by county (some counties have multiple auction types)
            counties_map = {}
            for entry in florida_data['floridaCounties']:
                county = entry['county']
                if county not in counties_map:
                    counties_map[county] = {
                        'county': county,
                        'foreclosures': [],
                        'tax_deeds': [],
                        'tax_liens': [],
                        'other': []
                    }

                for auction in entry['auctionTypes']:
                    if auction['type'] == 'foreclosure':
                        counties_map[county]['foreclosures'].append(auction)
                    elif auction['type'] == 'tax_deed':
                        counties_map[county]['tax_deeds'].append(auction)
                    elif auction['type'] == 'tax_lien':
                        counties_map[county]['tax_liens'].append(auction)
                    else:
                        counties_map[county]['other'].append(auction)

            # Display results
            print("="*80)
            print("FLORIDA COUNTIES - COMPREHENSIVE MAPPING")
            print("="*80)
            print()

            for county, data in sorted(counties_map.items()):
                print(f"📍 {county} COUNTY:")

                if data['foreclosures']:
                    print(f"   🏛️  Foreclosures: {len(data['foreclosures'])} platform(s)")
                    for fc in data['foreclosures']:
                        print(f"      - {fc['linkText']}")
                        print(f"        URL: {fc['url']}")

                if data['tax_deeds']:
                    print(f"   📋 Tax Deed Sales: {len(data['tax_deeds'])} platform(s)")
                    for td in data['tax_deeds']:
                        print(f"      - {td['linkText']}")
                        print(f"        URL: {td['url']}")

                if data['tax_liens']:
                    print(f"   💰 Tax Liens: {len(data['tax_liens'])} platform(s)")
                    for tl in data['tax_liens']:
                        print(f"      - {tl['linkText']}")
                        print(f"        URL: {tl['url']}")

                if data['other']:
                    print(f"   📊 Other: {len(data['other'])} platform(s)")
                    for ot in data['other']:
                        print(f"      - {ot['linkText']}")
                        print(f"        URL: {ot['url']}")

                print()

            # Save results
            results = {
                'timestamp': datetime.now().isoformat(),
                'source_url': clients_url,
                'total_counties_found': len(counties_map),
                'counties': counties_map,
                'raw_data': florida_data
            }

            output_file = f'florida_counties_complete_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"💾 Complete data saved to: {output_file}")
            print()

            # Summary
            print("="*80)
            print("SUMMARY")
            print("="*80)
            print(f"Total Florida counties found: {len(counties_map)}")

            foreclosure_count = sum(1 for c in counties_map.values() if c['foreclosures'])
            tax_deed_count = sum(1 for c in counties_map.values() if c['tax_deeds'])
            tax_lien_count = sum(1 for c in counties_map.values() if c['tax_liens'])

            print(f"Counties with foreclosures: {foreclosure_count}")
            print(f"Counties with tax deed sales: {tax_deed_count}")
            print(f"Counties with tax liens: {tax_lien_count}")
            print()

            print("⏳ Keeping browser open for 30 seconds for inspection...")
            await page.wait_for_timeout(30000)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='florida_extraction_error.png', full_page=True)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_florida_counties())
