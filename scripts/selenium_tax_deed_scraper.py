#!/usr/bin/env python3
"""
Complete Selenium-Based Tax Deed Scraper
==========================================
Properly navigates into auctions, expands properties, and extracts all details.

Features:
- Clicks into individual auction pages
- Expands each property to get detailed data
- Progress tracking for counties, auctions, and properties
- Handles both upcoming and past auctions
- Comprehensive error handling
- Stores data in Supabase
"""

import os
import sys
import time
import re
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/selenium_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ykyvzkxlxrwopwlwpqwv.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')


class SeleniumTaxDeedScraper:
    """Complete Selenium-based scraper that navigates and expands properties"""

    def __init__(self, dry_run: bool = True):
        """Initialize the scraper

        Args:
            dry_run: If True, don't write to database
        """
        self.dry_run = dry_run
        self.driver = None
        self.wait = None
        self.supabase: Optional[Client] = None

        # Statistics
        self.stats = {
            'total_auctions': 0,
            'total_properties': 0,
            'successful_properties': 0,
            'failed_properties': 0,
            'start_time': datetime.now(timezone.utc)
        }

        # Initialize Supabase if not dry run
        if not dry_run and SUPABASE_KEY:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Supabase client initialized")
        elif not dry_run:
            logger.warning("⚠️  No Supabase key - forcing dry-run mode")
            self.dry_run = True

        logger.info(f"🚀 Selenium Tax Deed Scraper initialized (dry_run={self.dry_run})")

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        logger.info("✅ Chrome WebDriver initialized")

    def teardown_driver(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Chrome WebDriver closed")

    def scrape_broward_auctions(self) -> Dict:
        """Scrape all Broward County auctions (both upcoming and past)

        Returns:
            Dict with scraping results
        """
        logger.info("=" * 80)
        logger.info("🏛️  SCRAPING BROWARD COUNTY TAX DEED AUCTIONS")
        logger.info("=" * 80)

        url = "https://broward.deedauction.net/auctions"

        try:
            self.setup_driver()

            # Navigate to auctions page
            logger.info(f"📍 Navigating to {url}")
            self.driver.get(url)
            time.sleep(3)

            # Get all auction links
            auctions = self.get_auction_links()
            logger.info(f"📋 Found {len(auctions)} total auctions")

            all_properties = []

            # Process each auction
            for i, auction in enumerate(auctions, 1):
                logger.info(f"\n{'=' * 60}")
                logger.info(f"📊 Auction {i} of {len(auctions)} ({i/len(auctions)*100:.1f}%)")
                logger.info(f"📍 {auction['description']}")
                logger.info(f"🔗 {auction['url']}")
                logger.info(f"{'=' * 60}")

                properties = self.scrape_auction_page(auction)
                all_properties.extend(properties)

                logger.info(f"✅ Extracted {len(properties)} properties from this auction")
                logger.info(f"📊 Running total: {len(all_properties)} properties")

            self.stats['total_auctions'] = len(auctions)
            self.stats['total_properties'] = len(all_properties)
            self.stats['end_time'] = datetime.now(timezone.utc)

            # Store results
            if not self.dry_run and self.supabase:
                self.store_results(all_properties)

            return {
                'success': True,
                'county': 'BROWARD',
                'auction_count': len(auctions),
                'property_count': len(all_properties),
                'properties': all_properties,
                'stats': self.stats
            }

        except Exception as e:
            logger.error(f"❌ Error scraping Broward: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.teardown_driver()

    def get_auction_links(self) -> List[Dict]:
        """Get all auction links from the auctions page

        Returns:
            List of dicts with auction info
        """
        auctions = []

        # Get past auctions - find table by caption text
        try:
            past_table = self.driver.find_element(By.XPATH, "//table[.//caption[contains(text(), 'Past Auctions')]]")
            rows = past_table.find_elements(By.CSS_SELECTOR, 'tbody tr')

            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 3:
                        # Try to find link in first cell
                        links = cells[0].find_elements(By.TAG_NAME, 'a')
                        if links:
                            link = links[0]
                            auctions.append({
                                'description': link.text.strip(),
                                'url': link.get_attribute('href'),
                                'items': cells[1].text.strip(),
                                'status': cells[2].text.strip(),
                                'type': 'past'
                            })
                except Exception as e:
                    logger.warning(f"⚠️  Could not parse past auction row: {e}")
                    continue

            logger.info(f"✅ Found {len([a for a in auctions if a['type'] == 'past'])} past auctions")
        except NoSuchElementException:
            logger.info("ℹ️  No past auctions table found")

        # Get upcoming auctions - find table by caption text
        try:
            upcoming_table = self.driver.find_element(By.XPATH, "//table[.//caption[contains(text(), 'Upcoming Auctions')]]")
            rows = upcoming_table.find_elements(By.CSS_SELECTOR, 'tbody tr')

            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 3:
                        # Try to find link in first cell
                        links = cells[0].find_elements(By.TAG_NAME, 'a')
                        if links:
                            link = links[0]
                            auctions.append({
                                'description': link.text.strip(),
                                'url': link.get_attribute('href'),
                                'items': cells[1].text.strip(),
                                'status': cells[2].text.strip(),
                                'type': 'upcoming'
                            })
                except Exception as e:
                    logger.warning(f"⚠️  Could not parse upcoming auction row: {e}")
                    continue

            logger.info(f"✅ Found {len([a for a in auctions if a['type'] == 'upcoming'])} upcoming auctions")
        except NoSuchElementException:
            logger.info("ℹ️  No upcoming auctions table found")

        return auctions

    def scrape_auction_page(self, auction: Dict) -> List[Dict]:
        """Scrape all properties from a single auction page

        Args:
            auction: Dict with auction info (url, description, etc.)

        Returns:
            List of property dicts
        """
        properties = []

        try:
            # Navigate to auction page
            self.driver.get(auction['url'])
            time.sleep(3)

            # Find all property rows in the table - get count first
            table_rows = self.driver.find_elements(By.CSS_SELECTOR, 'table tr')
            property_rows = [r for r in table_rows if self.is_property_row(r)]
            num_properties = len(property_rows)

            logger.info(f"🔍 Found {num_properties} property rows")

            # Process each property by INDEX to avoid stale element references
            for i in range(num_properties):
                logger.info(f"   📦 Property {i+1} of {num_properties} ({(i+1)/num_properties*100:.1f}%)")

                try:
                    # RE-FIND the property rows each time to avoid stale references
                    table_rows = self.driver.find_elements(By.CSS_SELECTOR, 'table tr')
                    current_property_rows = [r for r in table_rows if self.is_property_row(r)]

                    if i >= len(current_property_rows):
                        logger.warning(f"      ⚠️  Property index {i} out of range, skipping")
                        continue

                    row = current_property_rows[i]

                    property_data = self.extract_property_from_row(row, auction)
                    if property_data:
                        properties.append(property_data)
                        self.stats['successful_properties'] += 1
                        logger.info(f"      ✅ Extracted: {property_data.get('tax_deed_number', 'N/A')}")
                    else:
                        self.stats['failed_properties'] += 1

                except Exception as e:
                    logger.error(f"      ❌ Error extracting property: {e}")
                    self.stats['failed_properties'] += 1
                    continue

                # Small delay to avoid overloading
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"❌ Error scraping auction page: {e}")

        return properties

    def is_property_row(self, row) -> bool:
        """Check if a table row is a property row

        Args:
            row: Selenium WebElement for table row

        Returns:
            True if this is a property row
        """
        try:
            # First check: must have expand/collapse button image
            expand_imgs = row.find_elements(By.CSS_SELECTOR, 'img[src*="expand.gif"], img[src*="collapse.gif"]')
            if not expand_imgs:
                return False

            # Second check: must have valid tax deed number in second cell
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) >= 2:
                second_cell_text = cells[1].text.strip()
                # Check if it has a tax deed number (numeric, 4-6 digits)
                if second_cell_text and second_cell_text.isdigit() and 4 <= len(second_cell_text) <= 6:
                    return True

            return False
        except:
            return False

    def extract_property_from_row(self, row, auction: Dict) -> Optional[Dict]:
        """Extract property details from a table row (with expansion)

        Args:
            row: Selenium WebElement for the property row
            auction: Dict with auction info

        Returns:
            Dict with property data or None
        """
        property_data = {
            'auction_id': auction['url'].split('/')[-1],
            'auction_description': auction['description'],
            'auction_type': auction['type'],
            'tax_deed_number': None,
            'parcel_number': None,
            'tax_certificate_number': None,
            'legal_description': None,
            'situs_address': None,
            'homestead': False,
            'assessed_value': None,
            'soh_value': None,
            'applicant': None,
            'opening_bid': None,
            'status': None,
            'gis_url': None,
            'bid_details_url': None,
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }

        try:
            # Get basic info from collapsed row
            cells = row.find_elements(By.TAG_NAME, 'td')
            # Cell 0 = expand button, Cell 1 = Tax Deed #, Cell 2 = Num Bids
            # Cell 3 = Opening Bid, Cell 4 = Winning Bid, Cell 5 = Details link, Cell 6 = Status
            if len(cells) >= 2:
                property_data['tax_deed_number'] = cells[1].text.strip()  # Tax Deed # is in second cell
            if len(cells) >= 4:
                property_data['opening_bid'] = cells[3].text.strip()  # Opening Bid
            if len(cells) >= 7:
                property_data['status'] = cells[6].text.strip()  # Status (Removed/Active)

            # Try to find and click expand button
            try:
                expand_btn = row.find_element(By.CSS_SELECTOR, 'img[src*="expand"], img[alt*="expand"], a[href*="javascript"]')

                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView(true);", expand_btn)
                time.sleep(0.5)

                # Click expand
                expand_btn.click()
                time.sleep(2)  # Wait for expansion

                # Extract detailed info from expanded view
                self.extract_expanded_details(row, property_data)

                # Click collapse to clean up
                try:
                    collapse_btn = row.find_element(By.CSS_SELECTOR, 'img[src*="collapse"]')
                    collapse_btn.click()
                    time.sleep(0.5)
                except:
                    pass  # Collapse not critical

            except NoSuchElementException:
                logger.warning(f"      ⚠️  No expand button found for {property_data['tax_deed_number']}")
                # Try to extract what we can from the row
                self.extract_basic_details(row, property_data)

            return property_data if property_data['tax_deed_number'] else None

        except Exception as e:
            logger.error(f"      ❌ Error extracting property: {e}")
            return None

    def extract_expanded_details(self, row, property_data: Dict):
        """Extract details from expanded property row

        Args:
            row: Selenium WebElement for the row
            property_data: Dict to populate with extracted data
        """
        try:
            # Get all text from the expanded area
            expanded_text = row.text

            # Parse fields using regex
            # Parcel #
            parcel_match = re.search(r'Parcel\s*#?:?\s*([^\n]+)', expanded_text, re.IGNORECASE)
            if parcel_match:
                property_data['parcel_number'] = parcel_match.group(1).strip()

            # Tax Certificate #
            cert_match = re.search(r'Tax\s+Certificate\s*#?:?\s*([^\n]+)', expanded_text, re.IGNORECASE)
            if cert_match:
                property_data['tax_certificate_number'] = cert_match.group(1).strip()

            # Legal Description
            legal_match = re.search(r'Legal:?\s*([^\n]+)', expanded_text, re.IGNORECASE)
            if legal_match:
                property_data['legal_description'] = legal_match.group(1).strip()

            # Situs Address
            situs_match = re.search(r'Situs\s+Address:?\s*([^\n]+)', expanded_text, re.IGNORECASE)
            if situs_match:
                property_data['situs_address'] = situs_match.group(1).strip()

            # Homestead
            if 'homestead:?\s*yes' in expanded_text.lower():
                property_data['homestead'] = True

            # Assessed Value
            assessed_match = re.search(r'Assessed[^:]*:\s*\$?\s*([\d,]+)', expanded_text, re.IGNORECASE)
            if assessed_match:
                property_data['assessed_value'] = float(assessed_match.group(1).replace(',', ''))

            # SOH Value
            soh_match = re.search(r'SOH\s+Value:?\s*\$?\s*([\d,]+)', expanded_text, re.IGNORECASE)
            if soh_match:
                property_data['soh_value'] = float(soh_match.group(1).replace(',', ''))

            # Applicant
            applicant_match = re.search(r'Applicant:?\s*([^\n]+)', expanded_text, re.IGNORECASE)
            if applicant_match:
                property_data['applicant'] = applicant_match.group(1).strip()

            # Status (Removed, Active, etc.)
            if 'removed' in expanded_text.lower():
                property_data['status'] = 'Removed'
            elif 'active' in expanded_text.lower():
                property_data['status'] = 'Active'
            elif 'sold' in expanded_text.lower():
                property_data['status'] = 'Sold'

            # Try to find links
            try:
                links = row.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    href = link.get_attribute('href')
                    text = link.text.lower()
                    if 'gis' in text or 'map' in text:
                        property_data['gis_url'] = href
                    elif 'bid' in text or 'details' in text:
                        property_data['bid_details_url'] = href
            except:
                pass

        except Exception as e:
            logger.warning(f"      ⚠️  Error parsing expanded details: {e}")

    def extract_basic_details(self, row, property_data: Dict):
        """Extract basic details from collapsed row (fallback)

        Args:
            row: Selenium WebElement for the row
            property_data: Dict to populate
        """
        try:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) >= 2:
                # Usually: Tax Deed #, Opening Bid, Status
                property_data['tax_deed_number'] = cells[0].text.strip()
                if len(cells) >= 3:
                    property_data['status'] = cells[-1].text.strip()
        except Exception as e:
            logger.warning(f"      ⚠️  Error parsing basic details: {e}")

    def store_results(self, properties: List[Dict]):
        """Store scraped properties in Supabase

        Args:
            properties: List of property dicts
        """
        if not self.supabase:
            logger.warning("⚠️  No Supabase client - skipping storage")
            return

        logger.info(f"💾 Storing {len(properties)} properties in database...")

        stored_count = 0
        error_count = 0

        for prop in properties:
            try:
                # Convert to database format for tax_deed_bidding_items table
                # Combine legal description and situs address
                legal_situs = prop.get('legal_description') or prop.get('situs_address') or ''

                # Parse currency strings to numeric values
                def parse_currency(value):
                    """Convert currency string like '$10,795.51' to float 10795.51"""
                    if not value:
                        return None
                    if isinstance(value, (int, float)):
                        return float(value)
                    # Remove $ and commas, then convert to float
                    cleaned = str(value).replace('$', '').replace(',', '').strip()
                    try:
                        return float(cleaned) if cleaned else None
                    except ValueError:
                        return None

                db_record = {
                    'auction_id': prop['auction_id'],
                    'composite_key': f"{prop['auction_id']}_{prop['tax_deed_number']}",
                    'tax_deed_number': prop['tax_deed_number'],
                    'parcel_id': prop.get('parcel_number'),  # parcel_number -> parcel_id
                    'tax_certificate_number': prop.get('tax_certificate_number'),
                    'legal_situs_address': legal_situs,  # Combined field
                    'homestead_exemption': prop.get('homestead', False),  # homestead -> homestead_exemption
                    'assessed_value': parse_currency(prop.get('assessed_value')),
                    'soh_value': parse_currency(prop.get('soh_value')),
                    'opening_bid': parse_currency(prop.get('opening_bid')),  # Parse currency string
                    'item_status': prop.get('status'),  # status -> item_status
                    'applicant_name': prop.get('applicant'),  # applicant -> applicant_name
                    'gis_parcel_map_url': prop.get('gis_url'),  # gis_url -> gis_parcel_map_url
                    'source_url': prop.get('bid_details_url'),  # Add source URL
                    'county': 'BROWARD',  # Add county
                    'scraped_at': prop['scraped_at'],
                    'auction_description': prop.get('auction_description')
                }

                # Upsert to database
                self.supabase.table('tax_deed_bidding_items').upsert(
                    db_record,
                    on_conflict='composite_key'
                ).execute()

                stored_count += 1

            except Exception as e:
                logger.error(f"❌ Error storing property {prop.get('tax_deed_number')}: {e}")
                error_count += 1

        logger.info(f"✅ Stored {stored_count} properties")
        if error_count > 0:
            logger.warning(f"⚠️  {error_count} properties failed to store")

    def print_summary(self):
        """Print final summary statistics"""
        duration = (self.stats.get('end_time', datetime.now(timezone.utc)) -
                   self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("📊 SCRAPING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"📋 Total Auctions: {self.stats['total_auctions']}")
        logger.info(f"🏠 Total Properties: {self.stats['total_properties']}")
        logger.info(f"✅ Successfully Extracted: {self.stats['successful_properties']}")
        logger.info(f"❌ Failed: {self.stats['failed_properties']}")
        logger.info(f"{'🔒 DRY RUN - No database writes' if self.dry_run else '✅ Data stored in database'}")
        logger.info("=" * 80)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Selenium-based tax deed scraper')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Run without writing to database (default: True)')
    parser.add_argument('--live', action='store_true',
                        help='Write data to database (opposite of dry-run)')

    args = parser.parse_args()

    # If --live is specified, override dry_run
    dry_run = not args.live if args.live else args.dry_run

    # Create scraper
    scraper = SeleniumTaxDeedScraper(dry_run=dry_run)

    # Scrape Broward County
    results = scraper.scrape_broward_auctions()

    # Print summary
    scraper.print_summary()

    # Save results to file
    os.makedirs('logs', exist_ok=True)
    results_file = f"logs/selenium_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Convert datetime objects for JSON
    if 'stats' in results:
        if 'start_time' in results['stats']:
            results['stats']['start_time'] = results['stats']['start_time'].isoformat()
        if 'end_time' in results['stats']:
            results['stats']['end_time'] = results['stats']['end_time'].isoformat()

    # Remove full property list from saved results (too large)
    results_summary = results.copy()
    if 'properties' in results_summary:
        results_summary['property_sample'] = results_summary['properties'][:5]
        del results_summary['properties']

    with open(results_file, 'w') as f:
        json.dump(results_summary, f, indent=2)

    logger.info(f"📄 Results saved to: {results_file}")

    return 0 if results.get('success') else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
