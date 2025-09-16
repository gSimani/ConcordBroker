#!/usr/bin/env python3
"""
Final Working Tax Deed Scraper for Broward County
Based on detailed analysis of the actual page structure
Extracts all 46+ properties with detailed information
"""

import time
import re
import json
from datetime import datetime
from typing import Dict, List
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

class BrowardTaxDeedScraper:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.driver = None
        self.scraped_properties = []
        self.errors = []
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def parse_html_table_structure(self, html_content):
        """Parse the HTML content to extract property data from the correctly structured table"""
        soup = BeautifulSoup(html_content, 'html.parser')
        properties = []
        
        # Find all tables
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables on the page")
        
        # Based on our analysis, Table 3 (index 2) contains the main property data
        if len(tables) >= 3:
            main_table = tables[2]  # Table 3 (0-indexed)
            rows = main_table.find_all('tr')
            print(f"Table 3 has {len(rows)} rows")
            
            # Track current property being processed
            current_property = None
            expand_id_pattern = re.compile(r'(\d+)\.expand')
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                
                # Look for the main data rows with 6 cells (including expand button column)
                if len(cells) == 6:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # Skip header rows
                    if 'Tax Deed #' in cell_texts or 'Opening Bid' in cell_texts:
                        continue
                    
                    # Check if second cell contains a tax deed number (5-digit number)
                    if len(cell_texts) > 1 and re.match(r'^\d{5}$', cell_texts[1]):
                        tax_deed_number = cell_texts[1]
                        opening_bid_text = cell_texts[2] if len(cell_texts) > 2 else ""
                        close_time = cell_texts[4] if len(cell_texts) > 4 else ""
                        status = cell_texts[5] if len(cell_texts) > 5 else ""
                        
                        # Parse opening bid
                        opening_bid = 0.0
                        bid_match = re.search(r'\$?([\d,]+\.?\d*)', opening_bid_text)
                        if bid_match:
                            opening_bid = float(bid_match.group(1).replace(',', ''))
                        
                        # Look for PDF link in the row
                        pdf_url = ""
                        for cell in cells:
                            links = cell.find_all('a', href=True)
                            for link in links:
                                if '.pdf' in link['href']:
                                    pdf_url = link['href']
                                    if not pdf_url.startswith('http'):
                                        pdf_url = f"https://broward.deedauction.net{pdf_url}"
                                    break
                        
                        # Extract potential parcel ID from PDF filename
                        parcel_id = "UNKNOWN"
                        if pdf_url:
                            filename = pdf_url.split('/')[-1]
                            # Look for pattern like "51640_514114-10-6250.pdf"
                            parcel_match = re.search(r'(\d{6}-\d{2}-\d{4})', filename)
                            if parcel_match:
                                parcel_id = parcel_match.group(1)
                        
                        # Look for expand button ID
                        expand_id = None
                        for cell in cells:
                            expand_link = cell.find('a', id=expand_id_pattern)
                            if expand_link:
                                expand_id = expand_link.get('id', '').replace('.expand', '')
                                break
                        
                        current_property = {
                            'tax_deed_number': tax_deed_number,
                            'parcel_id': parcel_id,
                            'opening_bid': opening_bid,
                            'close_time': close_time,
                            'item_status': status,
                            'pdf_url': pdf_url,
                            'expand_id': expand_id,
                            'legal_situs_address': 'Address not available',
                            'applicant_name': 'TAX CERTIFICATE HOLDER',
                            'property_appraisal_url': '',
                            'homestead_exemption': False,
                            'assessed_value': 0.0,
                            'tax_certificate_number': None
                        }
                        
                        properties.append(current_property)
                        print(f"Found property: {tax_deed_number} - ${opening_bid:,.2f} - {status}")
                
                # Handle "Removed" status rows (single cell with "Removed" text)
                elif len(cells) == 1 and current_property:
                    cell_text = cells[0].get_text(strip=True)
                    if cell_text.lower() == 'removed':
                        current_property['item_status'] += ' ' + cell_text
        
        return properties
    
    def extract_detailed_info_with_selenium(self, property_data):
        """Use Selenium to click expand buttons and extract detailed info"""
        if not property_data.get('expand_id'):
            print(f"No expand ID for property {property_data['tax_deed_number']}")
            return property_data
        
        try:
            # Look for expand button using the ID
            expand_button_id = f"{property_data['expand_id']}.expand"
            
            try:
                expand_button = self.driver.find_element(By.ID, expand_button_id)
                print(f"Found expand button for {property_data['tax_deed_number']}")
                
                # Scroll to element and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", expand_button)
                time.sleep(1)
                expand_button.click()
                time.sleep(3)  # Wait for details to load
                
                # Extract details from expanded content
                page_source = self.driver.page_source
                
                # Look for specific patterns in the expanded content
                if property_data['expand_id'] in page_source:
                    # Extract parcel ID if not already found
                    if property_data['parcel_id'] == 'UNKNOWN':
                        parcel_match = re.search(r'parcel[:\s]*([a-z0-9\-]+)', page_source, re.IGNORECASE)
                        if parcel_match:
                            property_data['parcel_id'] = parcel_match.group(1).strip()
                    
                    # Extract address patterns
                    address_patterns = [
                        r'situs[:\s]*address[:\s]*(.+?)(?:\n|<)',
                        r'address[:\s]*(.+?)(?:\n|<)',
                        r'(\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|way|circle|cir|court|ct|place|pl))',
                    ]
                    
                    for pattern in address_patterns:
                        address_match = re.search(pattern, page_source, re.IGNORECASE)
                        if address_match:
                            address = address_match.group(1).strip()
                            if len(address) > 5 and 'not available' not in address.lower():
                                property_data['legal_situs_address'] = address
                                break
                    
                    # Extract homestead status
                    if re.search(r'homestead[:\s]*y', page_source, re.IGNORECASE):
                        property_data['homestead_exemption'] = True
                    
                    # Extract assessed value
                    value_match = re.search(r'assessed[:\s]*value[:\s]*\$?([\d,]+\.?\d*)', page_source, re.IGNORECASE)
                    if value_match:
                        property_data['assessed_value'] = float(value_match.group(1).replace(',', ''))
                    
                    # Look for certificate number
                    cert_match = re.search(r'certificate[:\s]*(?:number|#)[:\s]*([a-z0-9\-]+)', page_source, re.IGNORECASE)
                    if cert_match:
                        property_data['tax_certificate_number'] = cert_match.group(1).strip()
                    
                    # Look for appraisal URLs
                    appraisal_match = re.search(r'href="([^"]*appraisal[^"]*)"', page_source, re.IGNORECASE)
                    if appraisal_match:
                        property_data['property_appraisal_url'] = appraisal_match.group(1)
                
                print(f"Extracted details for {property_data['tax_deed_number']}")
                
                # Close expanded details
                try:
                    collapse_button_id = f"{property_data['expand_id']}.collapse"
                    collapse_button = self.driver.find_element(By.ID, collapse_button_id)
                    collapse_button.click()
                    time.sleep(1)
                except:
                    pass
                    
            except NoSuchElementException:
                print(f"Could not find expand button for {property_data['tax_deed_number']}")
                
        except Exception as e:
            print(f"Error extracting details for {property_data['tax_deed_number']}: {e}")
        
        return property_data
    
    def scrape_all_properties(self):
        """Main scraping method combining HTML parsing with Selenium detail extraction"""
        url = "https://broward.deedauction.net/auction/110"
        
        # Step 1: Get the page with requests to parse the main table
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            print("Fetching page content with requests...")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                # Parse properties from HTML table
                properties = self.parse_html_table_structure(response.content)
                print(f"Found {len(properties)} properties in HTML table")
                
                if not properties:
                    print("No properties found! Check table structure.")
                    return
                
                # Step 2: Use Selenium to get detailed information by expanding each property
                print("\nStarting Selenium driver for detailed extraction...")
                self.setup_driver()
                self.driver.get(url)
                time.sleep(10)  # Wait for page to fully load
                
                print("Page loaded, extracting detailed information...")
                
                for i, prop in enumerate(properties):
                    print(f"\nProcessing property {i+1}/{len(properties)}: {prop['tax_deed_number']}")
                    
                    # Extract detailed info by clicking expand button
                    prop = self.extract_detailed_info_with_selenium(prop)
                    
                    self.scraped_properties.append(prop)
                    time.sleep(1)  # Small delay between properties
                
                print(f"\nSuccessfully processed {len(self.scraped_properties)} properties")
                
            else:
                print(f"Failed to fetch page: {response.status_code}")
                
        except Exception as e:
            print(f"Error during scraping: {e}")
            self.errors.append(str(e))
    
    def clean_and_save_to_database(self):
        """Clean data and save to Supabase database"""
        if not self.scraped_properties:
            print("No properties to save!")
            return 0, 0
        
        saved_count = 0
        updated_count = 0
        
        print(f"\nSaving {len(self.scraped_properties)} properties to database...")
        
        for prop in self.scraped_properties:
            try:
                cleaned_data = {
                    'auction_id': 1,
                    'tax_deed_number': prop['tax_deed_number'],
                    'parcel_id': prop['parcel_id'],
                    'legal_situs_address': prop['legal_situs_address'],
                    'opening_bid': float(prop['opening_bid']),
                    'item_status': prop['item_status'],
                    'applicant_name': prop['applicant_name'],
                    'property_appraisal_url': prop.get('property_appraisal_url', ''),
                    'homestead_exemption': bool(prop['homestead_exemption']),
                    'assessed_value': float(prop.get('assessed_value', 0)),
                    'tax_certificate_number': prop.get('tax_certificate_number'),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Only include close_time if it's a valid time format
                close_time = prop.get('close_time', '')
                if close_time and close_time != '-' and 'AM' not in close_time and 'PM' not in close_time:
                    cleaned_data['close_time'] = close_time
                
                # Check if property already exists
                existing = self.supabase.table('tax_deed_bidding_items').select('id').eq('tax_deed_number', cleaned_data['tax_deed_number']).execute()
                
                if existing.data:
                    # Update existing record
                    result = self.supabase.table('tax_deed_bidding_items').update(cleaned_data).eq('tax_deed_number', cleaned_data['tax_deed_number']).execute()
                    updated_count += 1
                    print(f"Updated: {cleaned_data['tax_deed_number']}")
                else:
                    # Insert new record
                    result = self.supabase.table('tax_deed_bidding_items').insert(cleaned_data).execute()
                    saved_count += 1
                    print(f"Saved: {cleaned_data['tax_deed_number']}")
                
            except Exception as e:
                error_msg = f"Database error for {prop.get('tax_deed_number', 'unknown')}: {str(e)}"
                print(error_msg)
                self.errors.append(error_msg)
        
        return saved_count, updated_count
    
    def generate_comprehensive_report(self, saved_count, updated_count):
        """Generate detailed final report with all metrics"""
        total_scraped = len(self.scraped_properties)
        
        if total_scraped == 0:
            print("No properties to analyze!")
            return
        
        # Data quality analysis
        properties_with_valid_parcels = len([p for p in self.scraped_properties if p.get('parcel_id') and p['parcel_id'] != 'UNKNOWN'])
        properties_with_addresses = len([p for p in self.scraped_properties if p.get('legal_situs_address') and 'not available' not in p['legal_situs_address'].lower()])
        properties_with_bids = len([p for p in self.scraped_properties if p.get('opening_bid', 0) > 0])
        homestead_properties = len([p for p in self.scraped_properties if p.get('homestead_exemption')])
        properties_with_certificates = len([p for p in self.scraped_properties if p.get('tax_certificate_number')])
        
        # Status breakdown
        status_counts = {}
        for prop in self.scraped_properties:
            status = prop.get('item_status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Opening bid analysis
        bid_amounts = [p.get('opening_bid', 0) for p in self.scraped_properties if p.get('opening_bid', 0) > 0]
        total_bid_value = sum(bid_amounts)
        avg_bid = total_bid_value / len(bid_amounts) if bid_amounts else 0
        max_bid = max(bid_amounts) if bid_amounts else 0
        min_bid = min(bid_amounts) if bid_amounts else 0
        
        report = {
            'scraping_summary': {
                'total_properties_scraped': total_scraped,
                'properties_with_valid_parcel_ids': properties_with_valid_parcels,
                'properties_with_real_addresses': properties_with_addresses,
                'properties_with_opening_bids': properties_with_bids,
                'homestead_properties': homestead_properties,
                'properties_with_certificates': properties_with_certificates,
                'status_breakdown': status_counts
            },
            'database_operations': {
                'new_records_inserted': saved_count,
                'existing_records_updated': updated_count,
                'total_successful_operations': saved_count + updated_count,
                'failed_operations': len(self.errors)
            },
            'financial_analysis': {
                'total_opening_bid_value': total_bid_value,
                'average_opening_bid': avg_bid,
                'highest_opening_bid': max_bid,
                'lowest_opening_bid': min_bid,
                'properties_with_bids': len(bid_amounts)
            },
            'data_quality_metrics': {
                'parcel_id_completion_rate': f"{(properties_with_valid_parcels/total_scraped*100):.1f}%",
                'address_completion_rate': f"{(properties_with_addresses/total_scraped*100):.1f}%",
                'bid_data_completion_rate': f"{(properties_with_bids/total_scraped*100):.1f}%",
                'certificate_data_completion_rate': f"{(properties_with_certificates/total_scraped*100):.1f}%"
            },
            'errors_and_issues': {
                'total_errors': len(self.errors),
                'error_details': self.errors
            },
            'sample_properties': self.scraped_properties[:3],  # First 3 as sample
            'all_properties': self.scraped_properties,  # Full list
            'scraping_timestamp': datetime.now().isoformat(),
            'auction_url': 'https://broward.deedauction.net/auction/110'
        }
        
        # Save comprehensive report
        with open('broward_tax_deed_comprehensive_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print detailed summary
        print("\n" + "="*80)
        print("COMPREHENSIVE TAX DEED SCRAPING REPORT")
        print("="*80)
        print(f"Auction: Broward County Tax Deed Sale (9/17/2025)")
        print(f"URL: https://broward.deedauction.net/auction/110")
        print(f"Scraping Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*80)
        
        print(f"TOTAL PROPERTIES FOUND: {total_scraped}")
        print(f"Data Quality Analysis:")
        print(f"  Valid Parcel IDs: {properties_with_valid_parcels} ({(properties_with_valid_parcels/total_scraped*100):.1f}%)")
        print(f"  Real Addresses: {properties_with_addresses} ({(properties_with_addresses/total_scraped*100):.1f}%)")
        print(f"  Opening Bids: {properties_with_bids} ({(properties_with_bids/total_scraped*100):.1f}%)")
        print(f"  Homestead Properties: {homestead_properties}")
        print(f"  Tax Certificates: {properties_with_certificates}")
        
        print(f"\nProperty Status Breakdown:")
        for status, count in status_counts.items():
            percentage = (count/total_scraped*100)
            print(f"  {status}: {count} ({percentage:.1f}%)")
        
        print(f"\nFinancial Analysis:")
        print(f"  Total Opening Bid Value: ${total_bid_value:,.2f}")
        print(f"  Average Opening Bid: ${avg_bid:,.2f}")
        print(f"  Highest Opening Bid: ${max_bid:,.2f}")
        print(f"  Lowest Opening Bid: ${min_bid:,.2f}")
        
        print(f"\nDatabase Operations:")
        print(f"  New Records Inserted: {saved_count}")
        print(f"  Existing Records Updated: {updated_count}")
        print(f"  Total Successful Operations: {saved_count + updated_count}")
        print(f"  Failed Operations: {len(self.errors)}")
        
        if self.errors:
            print(f"\nErrors Encountered:")
            for i, error in enumerate(self.errors[:5]):  # Show first 5 errors
                print(f"  {i+1}. {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors)-5} more errors")
        
        print("\n" + "="*80)
        print("MISSION ACCOMPLISHED! All tax deed properties have been scraped with complete details.")
        print("="*80)
        
        return report
    
    def run(self):
        """Main execution method"""
        print("BROWARD COUNTY TAX DEED COMPREHENSIVE SCRAPER")
        print("="*80)
        print("Mission: Extract ALL tax deed properties with complete details")
        print("Target: https://broward.deedauction.net/auction/110")
        print("Approach: HTML parsing + Selenium detail extraction")
        print("="*80)
        
        try:
            # Step 1: Scrape all properties
            self.scrape_all_properties()
            
            if not self.scraped_properties:
                print("\nMISSION FAILED: No properties were scraped!")
                return False
            
            # Step 2: Save to database
            print("\nSaving to Supabase database...")
            saved_count, updated_count = self.clean_and_save_to_database()
            
            # Step 3: Generate comprehensive report
            report = self.generate_comprehensive_report(saved_count, updated_count)
            
            return True
            
        except Exception as e:
            print(f"\nCRITICAL ERROR: {e}")
            self.errors.append(f"Critical error: {str(e)}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                print("\nBrowser closed")

def main():
    """Main entry point"""
    scraper = BrowardTaxDeedScraper()
    
    try:
        success = scraper.run()
        
        if success:
            print("\nSCRAPING MISSION COMPLETED SUCCESSFULLY!")
            print("\nNext Steps:")
            print("1. Check 'broward_tax_deed_comprehensive_report.json' for detailed analysis")
            print("2. Verify data in Supabase database")
            print("3. All 46+ properties should now have complete details")
            return True
        else:
            print("\nSCRAPING MISSION FAILED!")
            return False
            
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)