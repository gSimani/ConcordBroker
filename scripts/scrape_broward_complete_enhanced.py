"""
BROWARD Tax Deed Complete Enhanced Scraper
Extracts ALL available fields including Tax Certificate #, Legal, Homestead, and URLs
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import sys
import re
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv('.env.mcp')

# Initialize Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(url, key)

BROWARD_AUCTION_BASE = 'https://broward.deedauction.net'

async def scrape_property_complete_details(page, property_row, auction_id):
    """Expand a property and extract ALL detailed information"""
    try:
        # Click the expand button in the first cell
        expand_button = await property_row.locator('td').first().locator('a, button').first()

        if expand_button:
            await expand_button.click()
            await page.wait_for_timeout(1500)  # Wait for expansion

            # Extract ALL details from expanded section
            details = await page.evaluate("""
                (row) => {
                    // Find the expanded details row (next sibling)
                    let detailsRow = row.nextElementSibling;
                    if (!detailsRow) return null;

                    const text = detailsRow.innerText;

                    // Extract Parcel ID
                    const parcelMatch = text.match(/Parcel #?\\s*:\\s*([\\d-]+)/i);
                    const parcel_id = parcelMatch ? parcelMatch[1].trim() : null;

                    // Extract Tax Certificate Number
                    const taxCertMatch = text.match(/Tax Certificate #?\\s*:\\s*(\\d+)/i);
                    const tax_certificate_number = taxCertMatch ? taxCertMatch[1].trim() : null;

                    // Extract Legal Description
                    const legalMatch = text.match(/Legal\\s*:\\s*(.+?)(?:\\n|Situs|Homestead|Assessed|$)/i);
                    const legal_description = legalMatch ? legalMatch[1].trim() : null;

                    // Extract Situs Address (different from legal)
                    const situsMatch = text.match(/Situs Address\\s*:\\s*(.+?)(?:\\n|Homestead|Assessed|$)/i);
                    const situs_address = situsMatch ? situsMatch[1].trim() : null;

                    // Extract Homestead Status
                    const homesteadMatch = text.match(/Homestead\\s*:\\s*(Yes|No)/i);
                    const homestead = homesteadMatch ? homesteadMatch[1].toUpperCase() : null;

                    // Extract Assessed / SOH Value
                    const valueMatch = text.match(/Assessed[^:]*Value\\s*:\\s*\\$([\\d,]+)/i);
                    const assessed_value = valueMatch ? valueMatch[1].replace(/,/g, '') : null;

                    // Extract Applicant Name
                    const applicantMatch = text.match(/Applicant\\s*:\\s*(.+?)(?:\\n|Links|$)/i);
                    const applicant = applicantMatch ? applicantMatch[1].trim() : null;

                    // Extract GIS Map and Bid Details links
                    const gisLink = detailsRow.querySelector('a[href*="/gis"]');
                    const bidLink = detailsRow.querySelector('a[href*="/auction/"]');

                    const gis_map_path = gisLink ? gisLink.getAttribute('href') : null;
                    const bid_details_path = bidLink ? bidLink.getAttribute('href') : null;

                    return {
                        parcel_id,
                        tax_certificate_number,
                        legal_description,
                        situs_address,
                        homestead,
                        assessed_value: assessed_value ? parseFloat(assessed_value) : null,
                        applicant,
                        gis_map_path,
                        bid_details_path
                    };
                }
            """, await property_row.element_handle())

            # Click again to collapse
            await expand_button.click()
            await page.wait_for_timeout(500)

            # Construct full URLs for links
            if details:
                if details.get('gis_map_path'):
                    details['gis_map_url'] = f"{BROWARD_AUCTION_BASE}{details['gis_map_path']}"
                if details.get('bid_details_path'):
                    details['bid_details_url'] = f"{BROWARD_AUCTION_BASE}{details['bid_details_path']}"

            return details

    except Exception as e:
        print(f"  ⚠️  Error extracting details: {e}")
        return None


def detect_company_type(applicant_name):
    """Detect if applicant is a company and what type"""
    if not applicant_name:
        return None

    upper_name = applicant_name.upper()

    # Check for company indicators
    company_indicators = ['LLC', 'INC', 'CORP', 'CORPORATION', 'LTD', 'LIMITED', 'LP', 'PARTNERSHIP']

    for indicator in company_indicators:
        if indicator in upper_name:
            return {
                'is_company': True,
                'company_type': indicator,
                'search_name': applicant_name
            }

    return {
        'is_company': False,
        'company_type': None,
        'search_name': applicant_name
    }


async def scrape_broward_complete_enhanced():
    print("="*80)
    print("BROWARD COMPLETE ENHANCED TAX DEED SCRAPER")
    print("Extracts: Parcel #, Tax Cert #, Legal, Situs, Homestead, Assessed Value,")
    print("          Applicant, GIS Map URL, Bid Details URL")
    print("="*80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        all_properties = []

        try:
            # Step 1: Get past auction links
            auctions_url = f'{BROWARD_AUCTION_BASE}/auctions'
            print(f"\n📍 Step 1: Getting auction list from {auctions_url}")
            await page.goto(auctions_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Get past auction links
            past_auctions = await page.evaluate("""
                () => {
                    const auctions = [];
                    const links = document.querySelectorAll('a[href*="/auction/"]');

                    links.forEach(link => {
                        const text = link.innerText.trim();
                        if (text.includes('2025') || text.includes('Tax Deed Sale')) {
                            auctions.push({
                                date: text,
                                url: link.href,
                                id: link.href.split('/auction/')[1]
                            });
                        }
                    });

                    return auctions;
                }
            """)

            print(f"✅ Found {len(past_auctions)} past auctions")

            # Limit to first 2 auctions for testing
            for idx, auction in enumerate(past_auctions[:2], 1):
                print(f"\n{'='*80}")
                print(f"📋 Scraping Auction {idx}: {auction['date']}")
                print(f"{'='*80}")
                print(f"URL: {auction['url']}")
                print(f"Auction ID: {auction['id']}")

                await page.goto(auction['url'], wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)

                # Get summary statistics
                summary = await page.evaluate("""
                    () => {
                        const stats = {
                            advertised: 0,
                            canceled: 0,
                            sold: 0
                        };

                        const tables = document.querySelectorAll('table');
                        for (const table of tables) {
                            const text = table.innerText;

                            if (text.includes('Items') && text.includes('Count')) {
                                const rows = table.querySelectorAll('tr');
                                rows.forEach(row => {
                                    const cells = row.querySelectorAll('td');
                                    if (cells.length === 2) {
                                        const label = cells[0].innerText.trim();
                                        const value = parseInt(cells[1].innerText.trim());

                                        if (label === 'Advertised') stats.advertised = value;
                                        if (label === 'Canceled') stats.canceled = value;
                                        if (label === 'Sold') stats.sold = value;
                                    }
                                });
                                break;
                            }
                        }

                        return stats;
                    }
                """)

                print(f"📊 Summary: Advertised={summary['advertised']}, Canceled={summary['canceled']}, Sold={summary['sold']}")

                # Extract properties with complete details
                page_num = 1
                all_auction_properties = []

                while True:
                    print(f"\n  📄 Scraping page {page_num}...")

                    # Get basic property info
                    properties = await page.evaluate("""
                        () => {
                            const props = [];
                            const allRows = Array.from(document.querySelectorAll('tr'));

                            for (let i = 0; i < allRows.length; i++) {
                                const row = allRows[i];
                                const cells = row.querySelectorAll('td');

                                if (cells.length === 7) {
                                    const taxDeedNum = cells[1].innerText.trim();

                                    if (!taxDeedNum || !taxDeedNum.match(/^\\d+$/)) continue;

                                    const prop = {
                                        tax_deed_number: taxDeedNum,
                                        num_bids: cells[2].innerText.trim(),
                                        opening_bid: cells[3].innerText.trim().replace(/[$,]/g, ''),
                                        winning_bid: cells[4].innerText.trim().replace(/[$,]/g, ''),
                                        winner_name: cells[5].innerText.trim(),
                                        status: 'Unknown',
                                        row_index: i
                                    };

                                    // Check next row for status
                                    if (i + 1 < allRows.length) {
                                        const statusText = allRows[i + 1].innerText.trim();

                                        if (statusText === 'Removed' || statusText.includes('Removed')) {
                                            prop.status = 'Cancelled';
                                        } else if (statusText.includes('Sold')) {
                                            prop.status = 'Sold';
                                        }
                                    }

                                    props.push(prop);
                                }
                            }

                            return props;
                        }
                    """)

                    print(f"    ✅ Found {len(properties)} properties")

                    # Now expand each property to get complete details
                    print(f"    🔍 Extracting complete property details...")

                    for prop_idx, prop in enumerate(properties, 1):
                        # Get the property row
                        property_rows = await page.query_selector_all('tr')

                        # Find the row with this tax deed number
                        for row in property_rows:
                            text = await row.inner_text()
                            if prop['tax_deed_number'] in text:
                                # Extract complete details
                                details = await scrape_property_complete_details(page, row, auction['id'])

                                if details:
                                    # Merge all details
                                    prop['parcel_id'] = details.get('parcel_id')
                                    prop['tax_certificate_number'] = details.get('tax_certificate_number')
                                    prop['legal_description'] = details.get('legal_description')
                                    prop['situs_address'] = details.get('situs_address')
                                    prop['homestead'] = details.get('homestead')
                                    prop['assessed_value'] = details.get('assessed_value')
                                    prop['applicant'] = details.get('applicant')
                                    prop['gis_map_url'] = details.get('gis_map_url')
                                    prop['bid_details_url'] = details.get('bid_details_url')
                                    prop['gis_map_path'] = details.get('gis_map_path')
                                    prop['bid_details_path'] = details.get('bid_details_path')

                                    # Detect company type for SUNBIZ linking
                                    company_info = detect_company_type(prop.get('applicant'))
                                    prop['company_info'] = company_info

                                    # Add auction metadata
                                    prop['auction_id'] = auction['id']
                                    prop['auction_date'] = auction['date']
                                    prop['auction_url'] = auction['url']
                                    prop['county'] = 'BROWARD'

                                    print(f"      {prop_idx}. TD-{prop['tax_deed_number']}:")
                                    print(f"          Parcel: {prop['parcel_id']}")
                                    print(f"          Tax Cert #: {prop['tax_certificate_number']}")
                                    print(f"          Legal: {prop['legal_description'][:50] if prop.get('legal_description') else 'N/A'}...")
                                    print(f"          Situs: {prop['situs_address']}")
                                    print(f"          Homestead: {prop['homestead']}")
                                    print(f"          Assessed Value: ${prop['assessed_value']:,.2f}" if prop.get('assessed_value') else "N/A")
                                    print(f"          Applicant: {prop['applicant']} {('('+company_info['company_type']+')') if company_info['is_company'] else ''}")
                                    print(f"          GIS Map: {prop['gis_map_url'] if prop.get('gis_map_url') else 'N/A'}")
                                    print(f"          Bid Details: {prop['bid_details_url'] if prop.get('bid_details_url') else 'N/A'}")
                                else:
                                    print(f"      {prop_idx}. TD-{prop['tax_deed_number']}: No details available")

                                break

                        # Small delay between expansions
                        await page.wait_for_timeout(300)

                    all_auction_properties.extend(properties)

                    # Check for next page
                    has_next = await page.evaluate("""
                        () => {
                            const nextLink = document.querySelector('.paginate_button.next');
                            return nextLink && !nextLink.classList.contains('disabled');
                        }
                    """)

                    if not has_next:
                        print(f"    📌 No more pages")
                        break

                    # Click next page
                    await page.click('.paginate_button.next')
                    await page.wait_for_timeout(2000)
                    page_num += 1

                print(f"\n✅ Auction Complete: {len(all_auction_properties)} total properties")
                print(f"  🔴 Cancelled: {len([p for p in all_auction_properties if p['status'] == 'Cancelled'])}")
                print(f"  ✅ Sold: {len([p for p in all_auction_properties if p['status'] == 'Sold'])}")
                print(f"  📍 With Parcel IDs: {len([p for p in all_auction_properties if p.get('parcel_id')])}")
                print(f"  🏢 With Companies: {len([p for p in all_auction_properties if p.get('company_info', {}).get('is_company')])}")

                all_properties.append({
                    'auction_date': auction['date'],
                    'auction_url': auction['url'],
                    'auction_id': auction['id'],
                    'summary': summary,
                    'properties': all_auction_properties,
                    'total_properties': len(all_auction_properties),
                    'total_cancelled': len([p for p in all_auction_properties if p['status'] == 'Cancelled']),
                    'total_sold': len([p for p in all_auction_properties if p['status'] == 'Sold']),
                    'total_companies': len([p for p in all_auction_properties if p.get('company_info', {}).get('is_company')])
                })

            # Save JSON results
            results = {
                'timestamp': datetime.now().isoformat(),
                'total_auctions': len(all_properties),
                'total_properties': sum(a['total_properties'] for a in all_properties),
                'total_cancelled': sum(a['total_cancelled'] for a in all_properties),
                'total_sold': sum(a['total_sold'] for a in all_properties),
                'total_companies': sum(a['total_companies'] for a in all_properties),
                'auctions': all_properties
            }

            output_file = f'broward_complete_enhanced_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"\n{'='*80}")
            print("📊 SCRAPING COMPLETE - SUMMARY")
            print(f"{'='*80}")
            print(f"📊 Total auctions: {results['total_auctions']}")
            print(f"📊 Total properties: {results['total_properties']}")
            print(f"🔴 Total cancelled: {results['total_cancelled']}")
            print(f"✅ Total sold: {results['total_sold']}")
            print(f"🏢 Total companies detected: {results['total_companies']}")
            print(f"💾 Saved to: {output_file}")

            # Upload to database
            print(f"\n{'='*80}")
            print("📤 UPLOADING TO DATABASE")
            print(f"{'='*80}")

            uploaded_count = 0
            error_count = 0

            for auction in all_properties:
                for prop in auction['properties']:
                    try:
                        # Prepare data for database
                        data = {
                            'composite_key': f"{prop['tax_deed_number']}_{prop.get('parcel_id', 'UNKNOWN')}_{prop.get('county', 'BROWARD')}",
                            'county': prop.get('county', 'BROWARD'),
                            'auction_id': prop.get('auction_id'),
                            'tax_deed_number': prop.get('tax_deed_number'),
                            'parcel_id': prop.get('parcel_id'),
                            'tax_certificate_number': prop.get('tax_certificate_number'),
                            'legal_description': prop.get('legal_description'),
                            'legal_situs_address': prop.get('situs_address'),
                            'homestead_exemption': 'Y' if prop.get('homestead') == 'YES' else ('N' if prop.get('homestead') == 'NO' else None),
                            'assessed_value': float(prop.get('assessed_value')) if prop.get('assessed_value') else None,
                            'opening_bid': float(prop.get('opening_bid')) if prop.get('opening_bid') else None,
                            'winning_bid': float(prop.get('winning_bid')) if prop.get('winning_bid') else None,
                            'applicant_name': prop.get('applicant'),
                            'company_detected': prop.get('company_info', {}).get('is_company', False),
                            'company_type': prop.get('company_info', {}).get('company_type'),
                            'gis_map_url': prop.get('gis_map_url'),
                            'bid_details_url': prop.get('bid_details_url'),
                            'item_status': prop.get('status', 'Active'),
                            'source_url': prop.get('auction_url'),
                            'scraped_at': datetime.now().isoformat()
                        }

                        # Upsert to database
                        supabase.table('tax_deed_bidding_items').upsert(
                            data,
                            on_conflict='composite_key'
                        ).execute()

                        uploaded_count += 1

                        if uploaded_count % 10 == 0:
                            print(f"  Uploaded {uploaded_count}/{results['total_properties']}...")

                    except Exception as e:
                        error_count += 1
                        print(f"  ✗ Error uploading TD-{prop.get('tax_deed_number')}: {e}")

            print(f"\n✓ Successfully uploaded: {uploaded_count}")
            print(f"✗ Errors: {error_count}")

            print("\n⏳ Keeping browser open for 10 seconds...")
            await page.wait_for_timeout(10000)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path='broward_complete_enhanced_error.png', full_page=True)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_broward_complete_enhanced())
