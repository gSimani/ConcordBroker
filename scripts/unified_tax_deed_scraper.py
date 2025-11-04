"""
Unified Tax Deed Auction Scraper for Florida Counties
Handles Palm Beach and Miami-Dade (RealForeclose platform)
"""

import os
import sys
import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.async_api import async_playwright

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv('.env.mcp')

# Initialize Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(url, key)

# County configurations with known auction dates
COUNTIES = {
    'PALM BEACH': {
        'url': os.getenv('PALM_BEACH_TAX_DEED_URL', 'https://palmbeach.realtaxdeed.com/index.cfm'),
        'name': 'Palm Beach County',
        'enabled': True,
        'auction_dates': ['11/05/2025']  # Known active auction dates
    },
    'MIAMI-DADE': {
        'url': os.getenv('MIAMI_DADE_TAX_DEED_URL', 'https://www.miamidade.realforeclose.com/index.cfm'),
        'name': 'Miami-Dade County',
        'enabled': True,
        'auction_dates': ['11/13/2025', '11/20/2025']  # Known active auction dates
    }
}

async def scrape_county_auctions(playwright, county_key: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape all auction data for a specific county"""

    print(f"\n{'='*80}")
    print(f"{config['name'].upper()} TAX DEED SCRAPER")
    print(f"{'='*80}")

    all_auctions = []

    # Initialize browser
    print(f"[1/5] Initializing browser...")
    browser = await playwright.chromium.launch(headless=True)  # Headless for batch processing
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
    page = await context.new_page()

    try:
        # Use known auction dates from configuration
        auction_dates = config.get('auction_dates', [])

        if not auction_dates:
            print(f"    ⚠ No auction dates configured for {config['name']}")
            return all_auctions

        print(f"[2/5] Found {len(auction_dates)} configured auction dates")

        # Process each configured auction date
        for idx, auction_date in enumerate(auction_dates, 1):
            try:
                print(f"\n  [{idx}/{len(auction_dates)}] Processing auction: {auction_date}")

                # Navigate to auction preview
                auction_url = f"{config['url']}?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE={auction_date}"
                print(f"      Navigating to {auction_url}...")
                await page.goto(auction_url, wait_until='networkidle')
                await asyncio.sleep(3)

                # Extract auction data using JavaScript
                print(f"      Extracting auction data...")

                auction_data = await page.evaluate("""
                () => {
                  const auctions = [];
                  const allRows = document.querySelectorAll('table tr');
                  let currentAuction = null;

                  allRows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 2) {
                      const label = cells[0].innerText.trim();
                      const value = cells[1].innerText.trim();

                      if (label === 'Case #:') {
                        if (currentAuction && currentAuction.case_number) {
                          auctions.push(currentAuction);
                        }
                        currentAuction = {
                          case_number: value,
                          scraped_at: new Date().toISOString()
                        };
                      } else if (currentAuction) {
                        if (label === 'Certificate #:') {
                          currentAuction.certificate = value;
                        } else if (label === 'Opening Bid:') {
                          currentAuction.opening_bid = value;
                        } else if (label === 'Parcel ID:') {
                          currentAuction.parcel_id = value;
                        } else if (label === 'Property Address:') {
                          currentAuction.address = value;
                        } else if (label === 'Assessed Value:') {
                          currentAuction.assessed_value = value;
                        } else if (label === '' && value.includes('FL-')) {
                          currentAuction.location = value;
                        } else if (label === 'Auction Status') {
                          currentAuction.status = value;
                        } else if (label === 'Auction Type:' && value === 'TAXDEED') {
                          currentAuction.auction_type = 'TAXDEED';
                        }
                      }
                    }
                  });

                  if (currentAuction && currentAuction.case_number) {
                    auctions.push(currentAuction);
                  }

                  return auctions;
                }
                """)

                print(f"      ✓ Found {len(auction_data)} auctions on this date")

                # Process and clean data
                for auction in auction_data:
                    # Clean currency values
                    if 'opening_bid' in auction:
                        bid_str = auction['opening_bid'].replace('$', '').replace(',', '')
                        try:
                            auction['opening_bid_clean'] = float(bid_str)
                        except:
                            auction['opening_bid_clean'] = None

                    if 'assessed_value' in auction:
                        assessed_str = auction['assessed_value'].replace('$', '').replace(',', '')
                        try:
                            auction['assessed_value_clean'] = float(assessed_str)
                        except:
                            auction['assessed_value_clean'] = None

                    # Build full address
                    if 'address' in auction and 'location' in auction:
                        auction['full_address'] = f"{auction['address']}, {auction['location']}"

                    # Add county and metadata
                    auction['county'] = county_key
                    auction['auction_date'] = auction_date
                    auction['source_url'] = auction_url

                    all_auctions.append(auction)

            except Exception as e:
                print(f"      ✗ Error processing date {idx}: {e}")
                continue

        print(f"\n[3/5] Scraping complete for {config['name']}!")
        print(f"      Total auctions collected: {len(all_auctions)}")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.close()

    return all_auctions


def save_to_database(auctions: List[Dict[str, Any]]) -> Dict[str, int]:
    """Save auctions to Supabase database"""

    if not auctions:
        print("\nNo auctions to save")
        return {'saved': 0, 'errors': 0}

    print(f"\n{'='*80}")
    print(f"SAVING {len(auctions)} AUCTIONS TO DATABASE")
    print(f"{'='*80}")

    saved_count = 0
    error_count = 0

    for auction in auctions:
        try:
            # Generate composite key
            composite_key = f"{auction.get('case_number', 'UNKNOWN')}_{auction.get('parcel_id', 'UNKNOWN')}_{auction.get('county', 'UNKNOWN')}"

            # Prepare data for database
            data = {
                'composite_key': composite_key,
                'county': auction.get('county'),
                'tax_deed_number': auction.get('case_number'),
                'parcel_id': auction.get('parcel_id'),
                'legal_situs_address': auction.get('full_address', auction.get('address')),
                'opening_bid': auction.get('opening_bid_clean'),
                'assessed_value': auction.get('assessed_value_clean'),
                'item_status': auction.get('status', 'Active' if 'Redeemed' not in auction.get('status', '') else 'Closed'),
                'source_url': auction.get('source_url'),
                'scraped_at': auction.get('scraped_at'),
                'close_time': auction.get('auction_date'),
                'auction_description': f"Certificate: {auction.get('certificate', 'N/A')}"
            }

            # Upsert to database
            supabase.table('tax_deed_bidding_items').upsert(
                data,
                on_conflict='composite_key'
            ).execute()

            saved_count += 1

            if saved_count % 5 == 0:
                print(f"  Saved {saved_count}/{len(auctions)}...")

        except Exception as e:
            error_count += 1
            print(f"  ✗ Error saving {auction.get('case_number', 'unknown')}: {e}")

    print(f"\n✓ Successfully saved: {saved_count}")
    print(f"✗ Errors: {error_count}")

    return {'saved': saved_count, 'errors': error_count}


async def main():
    """Main scraper orchestrator"""

    print("="*80)
    print("UNIFIED TAX DEED AUCTION SCRAPER")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Counties: Palm Beach, Miami-Dade")
    print("="*80)

    all_auctions = []

    async with async_playwright() as playwright:
        # Scrape each enabled county
        for county_key, config in COUNTIES.items():
            if config['enabled']:
                auctions = await scrape_county_auctions(playwright, county_key, config)
                all_auctions.extend(auctions)

    # Save JSON backup
    if all_auctions:
        backup_file = f"unified_tax_deed_auctions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(all_auctions, f, indent=2, ensure_ascii=False)
        print(f"\n✓ JSON backup saved: {backup_file}")

        # Save to database
        stats = save_to_database(all_auctions)

        # Print summary
        print(f"\n{'='*80}")
        print("FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Total Auctions Scraped: {len(all_auctions)}")
        print(f"Successfully Saved: {stats['saved']}")
        print(f"Errors: {stats['errors']}")
        print(f"JSON Backup: {backup_file}")

        # County breakdown
        print(f"\nCounty Breakdown:")
        for county_key in COUNTIES.keys():
            county_auctions = [a for a in all_auctions if a.get('county') == county_key]
            print(f"  {county_key}: {len(county_auctions)} auctions")

        # Top auctions by value
        print(f"\nTop 5 Auctions by Opening Bid:")
        sorted_auctions = sorted(
            [a for a in all_auctions if a.get('opening_bid_clean')],
            key=lambda x: x.get('opening_bid_clean', 0),
            reverse=True
        )[:5]

        for idx, auction in enumerate(sorted_auctions, 1):
            print(f"  {idx}. {auction.get('county')}: {auction.get('case_number')} - ${auction.get('opening_bid_clean', 0):,.2f}")

    else:
        print("\n⚠ No auctions collected from any county")

    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETE")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
