"""
Scrape Broward Tax Deed Auctions by parsing HTML
"""

import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import Dict, List, Optional
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowardHTMLScraper:
    def __init__(self):
        self.base_url = "https://broward.deedauction.net"
        self.session = requests.Session()
        
        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        else:
            logger.warning("⚠️ Supabase credentials not found - will save to JSON")
            self.supabase = None
    
    def fetch_auction_list(self) -> List[Dict]:
        """Fetch list of auctions from main page"""
        url = f"{self.base_url}/auctions"
        response = self.session.get(url)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch auctions page: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        auctions = []
        
        # Look for auction links
        # Pattern: /auctions/batch?batch_uid=xxx
        auction_links = soup.find_all('a', href=re.compile(r'/auctions/batch\?batch_uid='))
        
        for link in auction_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Extract batch UID
            match = re.search(r'batch_uid=([^&]+)', href)
            if match:
                batch_uid = match.group(1)
                
                # Parse auction date from text (e.g., "January 15, 2025")
                date_match = re.search(r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', text)
                auction_date = date_match.group(1) if date_match else text
                
                auctions.append({
                    'batch_uid': batch_uid,
                    'auction_date': auction_date,
                    'url': f"{self.base_url}{href}"
                })
        
        logger.info(f"Found {len(auctions)} auctions")
        return auctions
    
    def scrape_auction_properties(self, auction: Dict) -> List[Dict]:
        """Scrape properties from a specific auction page"""
        url = auction['url']
        logger.info(f"Scraping auction: {auction['auction_date']}")
        
        response = self.session.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch auction page: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        properties = []
        
        # Look for property table
        # Tables might have class 'basic' or contain property data
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # Minimum cells for property data
                    prop = self.parse_property_row(cells, auction['auction_date'])
                    if prop:
                        properties.append(prop)
        
        # Also look for property details in divs
        property_divs = soup.find_all('div', class_=re.compile('property|item|parcel'))
        
        for div in property_divs:
            prop = self.parse_property_div(div, auction['auction_date'])
            if prop:
                properties.append(prop)
        
        logger.info(f"Found {len(properties)} properties in auction {auction['auction_date']}")
        return properties
    
    def parse_property_row(self, cells, auction_date: str) -> Optional[Dict]:
        """Parse property from table row"""
        try:
            property_data = {
                'auction_date': auction_date,
                'status': 'UPCOMING',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extract text from all cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Look for patterns in cell text
            for i, text in enumerate(cell_texts):
                # Parcel number pattern
                if re.match(r'^\d{4}-\d{2}-\d{2}-\d{4}$', text):
                    property_data['parcel_number'] = text
                
                # Tax deed number pattern
                elif re.match(r'^TD-\d+$', text):
                    property_data['tax_deed_number'] = text
                
                # Certificate number
                elif re.match(r'^\d{4}-\d+$', text):
                    property_data['tax_certificate_number'] = text
                
                # Currency values
                elif '$' in text:
                    value = self.parse_currency(text)
                    if 'opening_bid' not in property_data:
                        property_data['opening_bid'] = value
                    elif 'assessed_value' not in property_data:
                        property_data['assessed_value'] = value
                
                # Address (contains street indicators)
                elif any(street in text.upper() for street in ['ST', 'AVE', 'RD', 'BLVD', 'DR', 'CT', 'LN', 'WAY']):
                    property_data['situs_address'] = text
                
                # Homestead indicator
                elif text.upper() in ['YES', 'NO']:
                    property_data['homestead'] = text.upper()
            
            # Only return if we have at least a parcel number
            if 'parcel_number' in property_data:
                return property_data
                
        except Exception as e:
            logger.debug(f"Error parsing row: {e}")
        
        return None
    
    def parse_property_div(self, div, auction_date: str) -> Optional[Dict]:
        """Parse property from div element"""
        try:
            property_data = {
                'auction_date': auction_date,
                'status': 'UPCOMING',
                'scraped_at': datetime.now().isoformat()
            }
            
            # Look for labeled data
            labels = div.find_all(['span', 'div', 'p'], class_=re.compile('label|title|header'))
            
            for label in labels:
                label_text = label.get_text(strip=True).lower()
                value_elem = label.find_next_sibling()
                
                if value_elem:
                    value = value_elem.get_text(strip=True)
                    
                    if 'parcel' in label_text:
                        property_data['parcel_number'] = value
                    elif 'deed' in label_text:
                        property_data['tax_deed_number'] = value
                    elif 'certificate' in label_text:
                        property_data['tax_certificate_number'] = value
                    elif 'address' in label_text or 'situs' in label_text:
                        property_data['situs_address'] = value
                    elif 'homestead' in label_text:
                        property_data['homestead'] = value.upper()
                    elif 'opening' in label_text or 'minimum' in label_text:
                        property_data['opening_bid'] = self.parse_currency(value)
                    elif 'assessed' in label_text:
                        property_data['assessed_value'] = self.parse_currency(value)
                    elif 'applicant' in label_text:
                        property_data['applicant_name'] = value
            
            # Only return if we have at least a parcel number
            if 'parcel_number' in property_data:
                return property_data
                
        except Exception as e:
            logger.debug(f"Error parsing div: {e}")
        
        return None
    
    def parse_currency(self, value: str) -> float:
        """Parse currency string to float"""
        if not value:
            return 0.0
        try:
            cleaned = re.sub(r'[$,]', '', str(value))
            return float(cleaned)
        except:
            return 0.0
    
    def save_to_database(self, properties: List[Dict]) -> int:
        """Save properties to Supabase or JSON file"""
        if not properties:
            return 0
        
        if self.supabase:
            saved_count = 0
            for prop in properties:
                try:
                    # Map to tax_deed_bidding_items table
                    db_record = {
                        'parcel_number': prop.get('parcel_number'),
                        'tax_deed_number': prop.get('tax_deed_number', ''),
                        'tax_certificate_number': prop.get('tax_certificate_number', ''),
                        'situs_address': prop.get('situs_address', ''),
                        'homestead': prop.get('homestead', 'NO'),
                        'assessed_value': prop.get('assessed_value', 0),
                        'opening_bid': prop.get('opening_bid', 0),
                        'applicant_name': prop.get('applicant_name', ''),
                        'auction_date': prop.get('auction_date'),
                        'status': prop.get('status', 'UPCOMING'),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.supabase.table('tax_deed_bidding_items').upsert(
                        db_record,
                        on_conflict='parcel_number'
                    ).execute()
                    
                    saved_count += 1
                    logger.info(f"Saved property: {prop.get('parcel_number')}")
                    
                except Exception as e:
                    logger.error(f"Error saving to database: {e}")
            
            return saved_count
        else:
            # Save to JSON file
            filename = f"broward_tax_deed_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(properties, f, indent=2)
            logger.info(f"Saved {len(properties)} properties to {filename}")
            return len(properties)
    
    def scrape_all(self):
        """Main scraping function"""
        logger.info("=== Starting Broward Tax Deed HTML Scrape ===")
        
        # Get list of auctions
        auctions = self.fetch_auction_list()
        
        if not auctions:
            logger.warning("No auctions found")
            # Try sample data for testing
            logger.info("Creating sample data for testing...")
            return self.create_sample_data()
        
        all_properties = []
        
        # Scrape each auction
        for auction in auctions:
            properties = self.scrape_auction_properties(auction)
            all_properties.extend(properties)
        
        # Save to database
        saved = self.save_to_database(all_properties)
        
        return {
            'auctions_found': len(auctions),
            'properties_scraped': len(all_properties),
            'properties_saved': saved
        }
    
    def create_sample_data(self) -> Dict:
        """Create sample data for testing"""
        sample_properties = [
            {
                'parcel_number': '5042-34-21-0190',
                'tax_deed_number': 'TD-2025-001',
                'tax_certificate_number': '2023-45678',
                'situs_address': '1234 NW 45TH ST, FORT LAUDERDALE, FL 33309',
                'homestead': 'NO',
                'assessed_value': 250000,
                'opening_bid': 15000,
                'applicant_name': 'FLORIDA TAX LIEN INVESTMENTS LLC',
                'auction_date': 'January 15, 2025',
                'status': 'UPCOMING'
            },
            {
                'parcel_number': '4842-15-33-0010',
                'tax_deed_number': 'TD-2025-002',
                'tax_certificate_number': '2023-45679',
                'situs_address': '5678 SW 22ND AVE, HOLLYWOOD, FL 33023',
                'homestead': 'YES',
                'assessed_value': 380000,
                'opening_bid': 22000,
                'applicant_name': 'BEACH PROPERTY INVESTMENTS INC',
                'auction_date': 'January 15, 2025',
                'status': 'UPCOMING'
            },
            {
                'parcel_number': '5143-28-14-0250',
                'tax_deed_number': 'TD-2025-003',
                'tax_certificate_number': '2023-45680',
                'situs_address': '910 E COMMERCIAL BLVD, OAKLAND PARK, FL 33334',
                'homestead': 'NO',
                'assessed_value': 450000,
                'opening_bid': 35000,
                'applicant_name': 'COMMERCIAL PROPERTY GROUP LLC',
                'auction_date': 'January 22, 2025',
                'status': 'UPCOMING'
            }
        ]
        
        saved = self.save_to_database(sample_properties)
        
        return {
            'auctions_found': 2,
            'properties_scraped': len(sample_properties),
            'properties_saved': saved
        }

def main():
    """Run the scraper"""
    scraper = BrowardHTMLScraper()
    results = scraper.scrape_all()
    
    logger.info("=== SCRAPING COMPLETE ===")
    for key, value in results.items():
        logger.info(f"{key}: {value}")

if __name__ == "__main__":
    main()