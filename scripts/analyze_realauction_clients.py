"""
Comprehensive Analysis of RealAuction.com Clients Page
Maps all Florida counties with foreclosure/tax deed/tax lien auction information
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def analyze_realauction_clients():
    print("="*80)
    print("REALAUCTION.COM CLIENTS PAGE - COMPREHENSIVE ANALYSIS")
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
            await page.wait_for_timeout(5000)
            print("✅ Page loaded")
            print()

            # Take screenshot for reference
            await page.screenshot(path='realauction_clients_page.png', full_page=True)
            print("📸 Screenshot saved: realauction_clients_page.png")
            print()

            # Extract all client information
            print("📊 Extracting client data...")

            clients_data = await page.evaluate("""
                () => {
                    const clients = [];

                    // Try to find all links and sections related to counties
                    const allLinks = document.querySelectorAll('a');
                    const allSections = document.querySelectorAll('section, div, article');

                    // Extract from links
                    allLinks.forEach(link => {
                        const text = link.textContent.trim();
                        const href = link.getAttribute('href');

                        // Check if it's related to Florida or counties
                        if (text && href && (
                            text.includes('Florida') ||
                            text.includes('County') ||
                            text.includes('FL') ||
                            href.includes('florida') ||
                            href.includes('.com/') ||
                            href.includes('auction')
                        )) {
                            clients.push({
                                type: 'link',
                                text: text,
                                url: href,
                                fullUrl: link.href
                            });
                        }
                    });

                    // Extract page text for analysis
                    const pageText = document.body.innerText;

                    return {
                        clients: clients,
                        pageText: pageText,
                        totalLinks: allLinks.length,
                        title: document.title
                    };
                }
            """)

            print(f"✅ Found {len(clients_data['clients'])} potential client links")
            print(f"📄 Page title: {clients_data['title']}")
            print()

            # Filter for Florida counties
            florida_clients = []
            florida_keywords = [
                'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD',
                'CALHOUN', 'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA',
                'DESOTO', 'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN',
                'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON', 'HARDEE',
                'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES',
                'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE',
                'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE',
                'MARION', 'MARTIN', 'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA',
                'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS',
                'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA', 'SEMINOLE', 'ST. JOHNS',
                'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
                'WAKULLA', 'WALTON', 'WASHINGTON'
            ]

            for client in clients_data['clients']:
                text_upper = client['text'].upper()
                for county in florida_keywords:
                    if county in text_upper or county.replace(' ', '') in text_upper.replace(' ', ''):
                        florida_clients.append({
                            **client,
                            'county': county,
                            'detected': True
                        })
                        break

            print(f"🏛️  Found {len(florida_clients)} Florida county matches")
            print()

            # Analyze URL patterns
            url_patterns = {}
            for client in florida_clients:
                url = client.get('fullUrl', '')
                if url:
                    # Extract domain pattern
                    if 'realauction.com' in url:
                        pattern = 'realauction.com'
                    elif 'realtaxdeed.com' in url:
                        pattern = 'realtaxdeed.com'
                    elif 'realforeclose.com' in url:
                        pattern = 'realforeclose.com'
                    else:
                        # Extract domain
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        pattern = parsed.netloc if parsed.netloc else 'unknown'

                    if pattern not in url_patterns:
                        url_patterns[pattern] = []
                    url_patterns[pattern].append(client)

            print("🌐 URL Patterns Found:")
            for pattern, matches in url_patterns.items():
                print(f"   {pattern}: {len(matches)} counties")
            print()

            # Print detailed Florida county information
            print("="*80)
            print("FLORIDA COUNTIES DETAILED MAPPING")
            print("="*80)
            print()

            counties_by_name = {}
            for client in florida_clients:
                county = client['county']
                if county not in counties_by_name:
                    counties_by_name[county] = []
                counties_by_name[county].append(client)

            for county, entries in sorted(counties_by_name.items()):
                print(f"📍 {county} COUNTY:")
                for entry in entries:
                    print(f"   Text: {entry['text']}")
                    print(f"   URL: {entry.get('fullUrl', 'N/A')}")
                print()

            # Check for search functionality
            print("="*80)
            print("SEARCHING FOR STATE/COUNTY SELECTION")
            print("="*80)
            print()

            # Look for dropdowns, search boxes, or navigation
            page_structure = await page.evaluate("""
                () => {
                    const structure = {
                        selects: [],
                        searchInputs: [],
                        stateSelectors: [],
                        countySelectors: []
                    };

                    // Find select dropdowns
                    document.querySelectorAll('select').forEach(select => {
                        const label = select.getAttribute('aria-label') || select.name || '';
                        const options = Array.from(select.options).map(opt => opt.text);
                        structure.selects.push({
                            id: select.id,
                            name: select.name,
                            label: label,
                            optionsCount: options.length,
                            sampleOptions: options.slice(0, 5)
                        });
                    });

                    // Find search inputs
                    document.querySelectorAll('input[type="search"], input[type="text"]').forEach(input => {
                        const placeholder = input.placeholder || '';
                        const label = input.getAttribute('aria-label') || '';
                        structure.searchInputs.push({
                            id: input.id,
                            name: input.name,
                            placeholder: placeholder,
                            label: label
                        });
                    });

                    // Look for state/county specific elements
                    document.querySelectorAll('[class*="state"], [class*="State"], [id*="state"], [id*="State"]').forEach(el => {
                        structure.stateSelectors.push({
                            tag: el.tagName,
                            id: el.id,
                            className: el.className,
                            text: el.textContent.substring(0, 100)
                        });
                    });

                    document.querySelectorAll('[class*="county"], [class*="County"], [id*="county"], [id*="County"]').forEach(el => {
                        structure.countySelectors.push({
                            tag: el.tagName,
                            id: el.id,
                            className: el.className,
                            text: el.textContent.substring(0, 100)
                        });
                    });

                    return structure;
                }
            """)

            if page_structure['selects']:
                print(f"Found {len(page_structure['selects'])} select dropdowns:")
                for select in page_structure['selects']:
                    print(f"  - {select['name'] or select['id']}: {select['optionsCount']} options")
                    if select['sampleOptions']:
                        print(f"    Sample: {', '.join(select['sampleOptions'])}")
                print()

            if page_structure['searchInputs']:
                print(f"Found {len(page_structure['searchInputs'])} search inputs:")
                for inp in page_structure['searchInputs']:
                    print(f"  - {inp['placeholder'] or inp['label'] or inp['name']}")
                print()

            # Save comprehensive results
            results = {
                'timestamp': datetime.now().isoformat(),
                'source_url': clients_url,
                'total_clients': len(clients_data['clients']),
                'florida_counties': len(florida_clients),
                'url_patterns': {k: len(v) for k, v in url_patterns.items()},
                'counties_found': list(counties_by_name.keys()),
                'detailed_clients': florida_clients,
                'page_structure': page_structure,
                'raw_data': clients_data
            }

            output_file = f'realauction_florida_counties_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"💾 Complete analysis saved to: {output_file}")
            print()

            # Generate summary
            print("="*80)
            print("ANALYSIS SUMMARY")
            print("="*80)
            print(f"Total clients found: {len(clients_data['clients'])}")
            print(f"Florida counties identified: {len(counties_by_name)}")
            print(f"URL patterns: {len(url_patterns)}")
            print()
            print("Counties mapped:")
            for i, county in enumerate(sorted(counties_by_name.keys()), 1):
                print(f"  {i}. {county}")
            print()

            print("⏳ Keeping browser open for 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='realauction_error.png', full_page=True)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_realauction_clients())
