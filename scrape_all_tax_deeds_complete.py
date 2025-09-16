#!/usr/bin/env python3
"""
Comprehensive Tax Deed Auction Scraper for Broward County
Scrapes ALL properties with complete details by clicking expand buttons
"""

import time
import re
import json
from datetime import datetime
from typing import Dict, List, Optional
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

class TaxDeedScraper:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.driver = None
        self.scraped_properties = []
        self.errors = []
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def extract_property_details(self, property_element) -> Dict:
        """Extract detailed property information from a property element"""
        property_data = {
            'tax_deed_number': None,
            'parcel_id': None,
            'legal_situs_address': None,
            'opening_bid': None,
            'item_status': None,
            'applicant_name': None,
            'property_appraisal_url': None,
            'homestead_exemption': False,
            'assessed_value': None,
            'tax_certificate_number': None,
            'legal_description': None,
            'close_time': None,
            'pdf_url': None
        }
        
        try:
            # Get all table cells
            cells = property_element.find_elements(By.TAG_NAME, "td")
            
            # Only process rows with exactly 5 columns (tax deed data rows)
            if len(cells) != 5:
                return property_data
            
            # Extract Tax Deed Number (first column)
            if cells[0]:
                # Check for PDF link first
                try:
                    pdf_link = cells[0].find_element(By.TAG_NAME, "a")
                    property_data['pdf_url'] = pdf_link.get_attribute('href')
                    property_data['tax_deed_number'] = pdf_link.text.strip()
                except NoSuchElementException:
                    property_data['tax_deed_number'] = cells[0].text.strip()
            
            # Extract Opening Bid (second column)
            if cells[1]:
                bid_text = cells[1].text.strip()
                bid_match = re.search(r'\$?([\d,]+\.?\d*)', bid_text)
                if bid_match:
                    property_data['opening_bid'] = float(bid_match.group(1).replace(',', ''))
            
            # Skip Best Bid (third column - usually shows "-")
            
            # Extract Close Time (fourth column)
            if cells[3]:
                property_data['close_time'] = cells[3].text.strip()
            
            # Extract Status (fifth column)
            if cells[4]:
                property_data['item_status'] = cells[4].text.strip()
            
            # Only proceed if we have a valid tax deed number
            if not property_data['tax_deed_number'] or property_data['tax_deed_number'] in ['', 'Tax Deed #']:
                return property_data
            
            # Look for expand button and try to click it
            try:
                # Try multiple ways to find expand button
                expand_button = None
                try:
                    expand_button = property_element.find_element(By.CSS_SELECTOR, "img[src*='expand.gif']")
                except:
                    try:
                        expand_button = property_element.find_element(By.CSS_SELECTOR, "img[alt*='Show item details']")
                    except:
                        # Try to find it in the next row (sometimes details are in following rows)
                        try:
                            next_row = self.driver.execute_script(
                                "return arguments[0].nextElementSibling;", property_element
                            )
                            if next_row:
                                expand_button = next_row.find_element(By.CSS_SELECTOR, "img[src*='expand.gif']")
                        except:
                            pass
                
                if expand_button:
                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", expand_button)
                    time.sleep(1)
                    expand_button.click()
                    time.sleep(3)  # Wait for details to load
                    
                    # Extract detailed information from expanded view
                    self.extract_expanded_details(property_data)
                    
                    # Click collapse button to close details
                    try:
                        collapse_button = self.driver.find_element(By.CSS_SELECTOR, "img[src*='collapse.gif']")
                        collapse_button.click()
                        time.sleep(1)
                    except:
                        pass
                else:
                    # Try to extract additional info from PDF link
                    if property_data['pdf_url']:
                        self.extract_info_from_pdf_link(property_data)
                    
            except Exception as expand_error:
                print(f"Could not expand details for {property_data['tax_deed_number']}: {expand_error}")
            
        except Exception as e:
            self.errors.append(f"Error extracting property details: {str(e)}")
            print(f"Error extracting property: {e}")
        
        return property_data
    
    def extract_expanded_details(self, property_data):
        """Extract details from the expanded property view"""
        try:
            # Look for detailed property information in the expanded section
            detail_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr, td")
            
            for row in detail_rows:
                text = row.text.lower()
                
                # Extract Parcel ID/Number
                if 'parcel' in text and property_data['parcel_id'] is None:
                    parcel_match = re.search(r'parcel[:\s]*([a-z0-9\-]+)', text, re.IGNORECASE)
                    if parcel_match:
                        property_data['parcel_id'] = parcel_match.group(1).strip()
                
                # Extract Address
                if ('address' in text or 'situs' in text) and property_data['legal_situs_address'] is None:
                    # Look for actual street address
                    address_match = re.search(r'(\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|way|circle|cir|court|ct|place|pl))', text, re.IGNORECASE)
                    if address_match:
                        property_data['legal_situs_address'] = address_match.group(1).strip()
                
                # Extract Legal Description
                if 'legal' in text and 'description' in text:
                    # Extract legal description
                    legal_match = re.search(r'legal description[:\s]*(.+)', text, re.IGNORECASE)
                    if legal_match:
                        property_data['legal_description'] = legal_match.group(1).strip()
                
                # Extract Tax Certificate Number
                if 'certificate' in text and property_data['tax_certificate_number'] is None:
                    cert_match = re.search(r'certificate[:\s]*([a-z0-9\-]+)', text, re.IGNORECASE)
                    if cert_match:
                        property_data['tax_certificate_number'] = cert_match.group(1).strip()
                
                # Extract Homestead Status
                if 'homestead' in text:
                    property_data['homestead_exemption'] = 'yes' in text.lower() or 'y' in text.lower()
                
                # Extract Assessed Value
                if 'assessed' in text and 'value' in text:
                    value_match = re.search(r'\$?([\d,]+\.?\d*)', text)
                    if value_match:
                        property_data['assessed_value'] = float(value_match.group(1).replace(',', ''))
                
                # Extract Applicant Name
                if 'applicant' in text or 'holder' in text:
                    applicant_match = re.search(r'(?:applicant|holder)[:\s]*(.+)', text, re.IGNORECASE)
                    if applicant_match:
                        property_data['applicant_name'] = applicant_match.group(1).strip()
            
            # Look for embedded links
            links = property_element.find_elements(By.CSS_SELECTOR, "a[href]")
            for link in links:
                href = link.get_attribute('href')
                if href and 'appraisal' in href.lower():
                    property_data['property_appraisal_url'] = href
                
        except Exception as e:
            print(f"Error extracting expanded details: {e}")
    
    def extract_info_from_pdf_link(self, property_data):
        """Extract information from PDF link filename"""
        try:
            if property_data['pdf_url']:
                # PDF filenames often contain parcel IDs
                filename = property_data['pdf_url'].split('/')[-1]
                # Try to extract parcel ID from filename pattern like "51640_514114-10-6250.pdf"
                parcel_match = re.search(r'(\d{6}-\d{2}-\d{4})', filename)
                if parcel_match:
                    property_data['parcel_id'] = parcel_match.group(1)
        except Exception as e:
            print(f"Error extracting info from PDF link: {e}")
    
    def scrape_all_pages(self):
        """Scrape all pages of the auction"""
        base_url = "https://broward.deedauction.net/auction/110"
        
        try:
            self.driver.get(base_url)
            time.sleep(5)  # Wait for page to load
            
            page_num = 1
            
            while True:
                print(f"Scraping page {page_num}...")
                
                # Wait for properties to load
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tr")))
                except TimeoutException:
                    print("No properties found on this page")
                    break
                
                # Find all property rows - look for table rows with exactly 5 td elements
                all_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr")
                
                # Filter to get only data rows with 5 columns (tax deed data)
                data_rows = []
                for row in all_rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) == 5:
                        # Check if first cell contains a number (tax deed number)
                        first_cell_text = cells[0].text.strip()
                        if first_cell_text and (first_cell_text.isdigit() or first_cell_text.replace('.', '').isdigit()):
                            data_rows.append(row)
                
                print(f"Found {len(data_rows)} properties on page {page_num}")
                
                for i, row in enumerate(data_rows):
                    try:
                        print(f"Processing property {i+1}/{len(data_rows)} on page {page_num}")
                        property_data = self.extract_property_details(row)
                        
                        if property_data['tax_deed_number']:
                            self.scraped_properties.append(property_data)
                            print(f"Successfully scraped: {property_data['tax_deed_number']}")
                        
                    except Exception as e:
                        print(f"Error processing property {i+1}: {e}")
                        self.errors.append(f"Error processing property {i+1} on page {page_num}: {str(e)}")
                
                # Check for next page
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "a[href*='page=']")
                    if 'next' in next_button.text.lower() or '>' in next_button.text:
                        next_button.click()
                        time.sleep(3)
                        page_num += 1
                    else:
                        break
                except NoSuchElementException:
                    print("No more pages to scrape")
                    break
                    
        except Exception as e:
            print(f"Error during scraping: {e}")
            self.errors.append(f"Scraping error: {str(e)}")
    
    def clean_property_data(self, property_data: Dict) -> Dict:
        """Clean and validate property data before database insertion"""
        cleaned = {}
        
        # Required fields with defaults
        cleaned['auction_id'] = 110  # Current auction ID
        cleaned['tax_deed_number'] = property_data.get('tax_deed_number', 'UNKNOWN')
        cleaned['parcel_id'] = property_data.get('parcel_id', 'UNKNOWN')
        cleaned['legal_situs_address'] = property_data.get('legal_situs_address', 'Address not available')
        cleaned['opening_bid'] = float(property_data.get('opening_bid', 0))
        cleaned['item_status'] = property_data.get('item_status', 'Unknown')
        cleaned['applicant_name'] = property_data.get('applicant_name', 'TAX CERTIFICATE HOLDER')
        cleaned['property_appraisal_url'] = property_data.get('property_appraisal_url', '')
        cleaned['homestead_exemption'] = bool(property_data.get('homestead_exemption', False))
        cleaned['assessed_value'] = float(property_data.get('assessed_value', 0))
        
        # Optional fields
        if property_data.get('tax_certificate_number'):
            cleaned['tax_certificate_number'] = property_data['tax_certificate_number']
        
        if property_data.get('close_time'):
            cleaned['close_time'] = property_data['close_time']
        
        # Set timestamps
        now = datetime.now().isoformat()
        cleaned['created_at'] = now
        cleaned['updated_at'] = now
        
        return cleaned
    
    def save_to_database(self):
        """Save all scraped properties to Supabase"""
        print(f"Saving {len(self.scraped_properties)} properties to database...")
        
        saved_count = 0
        updated_count = 0
        
        for property_data in self.scraped_properties:
            try:
                cleaned_data = self.clean_property_data(property_data)
                
                # Check if property already exists
                existing = self.supabase.table('tax_deed_bidding_items').select('id').eq('tax_deed_number', cleaned_data['tax_deed_number']).execute()
                
                if existing.data:
                    # Update existing record
                    result = self.supabase.table('tax_deed_bidding_items').update(cleaned_data).eq('tax_deed_number', cleaned_data['tax_deed_number']).execute()
                    updated_count += 1
                    print(f"Updated property: {cleaned_data['tax_deed_number']}")
                else:
                    # Insert new record
                    result = self.supabase.table('tax_deed_bidding_items').insert(cleaned_data).execute()
                    saved_count += 1
                    print(f"Saved new property: {cleaned_data['tax_deed_number']}")
                
            except Exception as e:
                error_msg = f"Database error for {property_data.get('tax_deed_number', 'unknown')}: {str(e)}"
                print(error_msg)
                self.errors.append(error_msg)
        
        return saved_count, updated_count
    
    def generate_summary_report(self, saved_count: int, updated_count: int):
        """Generate comprehensive summary report"""
        total_scraped = len(self.scraped_properties)
        
        report = {
            'scraping_summary': {
                'total_properties_scraped': total_scraped,
                'properties_with_complete_data': len([p for p in self.scraped_properties if p.get('parcel_id') and p.get('parcel_id') != 'UNKNOWN']),
                'properties_with_addresses': len([p for p in self.scraped_properties if p.get('legal_situs_address') and p.get('legal_situs_address') != 'Address not available']),
                'properties_with_opening_bids': len([p for p in self.scraped_properties if p.get('opening_bid') and p.get('opening_bid') > 0]),
                'homestead_properties': len([p for p in self.scraped_properties if p.get('homestead_exemption')])
            },
            'database_summary': {
                'new_records_inserted': saved_count,
                'existing_records_updated': updated_count,
                'total_database_operations': saved_count + updated_count
            },
            'errors': {
                'total_errors': len(self.errors),
                'error_list': self.errors
            },
            'data_quality': {
                'properties_with_parcel_ids': len([p for p in self.scraped_properties if p.get('parcel_id') and p.get('parcel_id') != 'UNKNOWN']),
                'properties_with_valid_addresses': len([p for p in self.scraped_properties if p.get('legal_situs_address') and 'not available' not in p.get('legal_situs_address', '').lower()]),
                'properties_with_appraisal_urls': len([p for p in self.scraped_properties if p.get('property_appraisal_url')])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report to file
        with open('tax_deed_scraping_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*60)
        print("TAX DEED SCRAPING SUMMARY REPORT")
        print("="*60)
        print(f"Total Properties Scraped: {total_scraped}")
        print(f"Properties with Complete Data: {report['scraping_summary']['properties_with_complete_data']}")
        print(f"Properties with Valid Addresses: {report['data_quality']['properties_with_valid_addresses']}")
        print(f"Properties with Opening Bids: {report['scraping_summary']['properties_with_opening_bids']}")
        print(f"Homestead Properties: {report['scraping_summary']['homestead_properties']}")
        print("\nDatabase Operations:")
        print(f"New Records Inserted: {saved_count}")
        print(f"Existing Records Updated: {updated_count}")
        print(f"Total Errors: {len(self.errors)}")
        print("="*60)
        
        return report
    
    def run(self):
        """Main execution method"""
        print("Starting comprehensive tax deed auction scraping...")
        
        try:
            self.setup_driver()
            print("Browser setup complete")
            
            self.scrape_all_pages()
            print(f"Scraping complete. Found {len(self.scraped_properties)} properties")
            
            saved_count, updated_count = self.save_to_database()
            print(f"Database operations complete. Saved: {saved_count}, Updated: {updated_count}")
            
            report = self.generate_summary_report(saved_count, updated_count)
            
            return report
            
        except Exception as e:
            print(f"Critical error during execution: {e}")
            self.errors.append(f"Critical error: {str(e)}")
            return {'error': str(e), 'errors': self.errors}
        
        finally:
            if self.driver:
                self.driver.quit()
                print("Browser closed")

def main():
    """Main entry point"""
    scraper = TaxDeedScraper()
    
    try:
        report = scraper.run()
        
        if 'error' in report:
            print(f"Scraping failed: {report['error']}")
            return False
        else:
            print("Scraping completed successfully!")
            return True
            
    except Exception as e:
        print(f"Fatal error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)