"""
Broward Tax Deed Auction API Scraper
Scrapes auction data from broward.deedauction.net using their API endpoints
"""

import os
import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import re
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowardTaxDeedAPIScraper:
    def __init__(self):
        self.base_url = "https://broward.deedauction.net"
        self.session = None
        
        # Initialize Supabase
        supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        else:
            logger.warning("⚠️ Supabase credentials not found")
            self.supabase = None
    
    async def fetch_auctions(self, auction_type: str = "upcoming") -> List[Dict]:
        """Fetch auction list from API"""
        url = f"{self.base_url}/auctions/{auction_type}"
        
        # DataTables request format
        data = {
            "draw": 1,
            "start": 0,
            "length": 100,
            "order": [{"column": 0, "dir": "asc"}]
        }
        
        async with self.session.post(url, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('data', [])
            else:
                logger.error(f"Failed to fetch {auction_type} auctions: {response.status}")
                return []
    
    async def fetch_auction_details(self, auction_id: str) -> Dict:
        """Fetch detailed properties for a specific auction"""
        # Extract batch ID from auction link
        batch_pattern = r'batch_uid=([^&]+)'
        
        # Try to get auction batch page
        url = f"{self.base_url}/auctions/batch/{auction_id}"
        
        properties = []
        
        async with self.session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                
                # Parse HTML for property data
                # Look for property table or data elements
                import re
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for property rows in tables
                property_rows = soup.find_all('tr', class_=re.compile('property|item'))
                
                for row in property_rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        prop_data = self.parse_property_row(cells)
                        if prop_data:
                            properties.append(prop_data)
                
                # Also check for DataTables AJAX endpoint for this batch
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'ajax' in script.string:
                        # Extract AJAX URL for batch items
                        ajax_match = re.search(r'"url":\s*"([^"]+batch[^"]+)"', script.string)
                        if ajax_match:
                            ajax_url = ajax_match.group(1)
                            # Fetch items via AJAX
                            items = await self.fetch_batch_items(ajax_url)
                            properties.extend(items)
        
        return {
            'auction_id': auction_id,
            'properties': properties
        }
    
    async def fetch_batch_items(self, ajax_url: str) -> List[Dict]:
        """Fetch batch items from AJAX endpoint"""
        full_url = f"{self.base_url}{ajax_url}" if not ajax_url.startswith('http') else ajax_url
        
        data = {
            "draw": 1,
            "start": 0,
            "length": 1000,
            "order": [{"column": 0, "dir": "asc"}]
        }
        
        async with self.session.post(full_url, json=data) as response:
            if response.status == 200:
                result = await response.json()
                items = result.get('data', [])
                
                # Convert items to our property format
                properties = []
                for item in items:
                    prop = self.convert_api_item_to_property(item)
                    if prop:
                        properties.append(prop)
                
                return properties
        
        return []
    
    def convert_api_item_to_property(self, item: Dict) -> Optional[Dict]:
        """Convert API item to our property format"""
        try:
            # Extract data from various possible field names
            property_data = {
                'tax_deed_number': item.get('deed_number', item.get('tax_deed_number', '')),
                'parcel_number': item.get('parcel_id', item.get('parcel_number', '')),
                'tax_certificate_number': item.get('certificate_number', item.get('cert_number', '')),
                'legal_description': item.get('legal_desc', item.get('legal_description', '')),
                'situs_address': item.get('situs_address', item.get('property_address', '')),
                'homestead': item.get('homestead', 'NO'),
                'assessed_value': self.parse_currency(item.get('assessed_value', '0')),
                'land_value': self.parse_currency(item.get('land_value', '0')),
                'building_value': self.parse_currency(item.get('building_value', '0')),
                'applicant_name': item.get('applicant', item.get('applicant_name', '')),
                'opening_bid': self.parse_currency(item.get('opening_bid', item.get('minimum_bid', '0'))),
                'winning_bid': self.parse_currency(item.get('winning_bid', '0')) if item.get('winning_bid') else None,
                'winner_name': item.get('winner', item.get('winner_name', '')),
                'auction_date': item.get('auction_date', item.get('batch_closing_end', '')),
                'close_time': item.get('close_time', item.get('closing_time', '')),
                'status': item.get('status', 'PENDING'),
                'property_use_code': item.get('use_code', ''),
                'year_built': item.get('year_built', ''),
                'bedrooms': item.get('bedrooms', 0),
                'bathrooms': item.get('bathrooms', 0),
                'square_feet': item.get('square_feet', 0),
                'scraped_at': datetime.now().isoformat()
            }
            
            # Only return if we have at least a parcel number
            if property_data['parcel_number']:
                return property_data
                
        except Exception as e:
            logger.error(f"Error converting item: {e}")
        
        return None
    
    def parse_property_row(self, cells) -> Optional[Dict]:
        """Parse property data from table row cells"""
        try:
            if len(cells) < 4:
                return None
            
            # Extract text from cells
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # Try to identify fields based on patterns
            property_data = {
                'parcel_number': '',
                'situs_address': '',
                'opening_bid': 0,
                'status': 'PENDING'
            }
            
            # Look for parcel number pattern
            for text in cell_texts:
                if re.match(r'\d{4}-\d{2}-\d{2}-\d{4}', text):
                    property_data['parcel_number'] = text
                elif '$' in text:
                    property_data['opening_bid'] = self.parse_currency(text)
                elif any(street in text.upper() for street in ['ST', 'AVE', 'RD', 'BLVD', 'DR', 'CT']):
                    property_data['situs_address'] = text
            
            if property_data['parcel_number']:
                property_data['scraped_at'] = datetime.now().isoformat()
                return property_data
                
        except Exception as e:
            logger.error(f"Error parsing row: {e}")
        
        return None
    
    def parse_currency(self, value: str) -> float:
        """Parse currency string to float"""
        if not value:
            return 0.0
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', str(value))
            return float(cleaned)
        except:
            return 0.0
    
    async def save_to_database(self, properties: List[Dict]) -> int:
        """Save properties to Supabase database"""
        if not self.supabase:
            logger.warning("Supabase not configured - cannot save properties")
            return 0
        
        if not properties:
            return 0
        
        saved_count = 0
        
        for prop in properties:
            try:
                # Map to tax_deed_bidding_items table structure
                db_record = {
                    'parcel_number': prop.get('parcel_number'),
                    'tax_deed_number': prop.get('tax_deed_number'),
                    'tax_certificate_number': prop.get('tax_certificate_number'),
                    'legal_description': prop.get('legal_description'),
                    'situs_address': prop.get('situs_address'),
                    'homestead': prop.get('homestead', 'NO'),
                    'assessed_value': prop.get('assessed_value', 0),
                    'land_value': prop.get('land_value', 0),
                    'building_value': prop.get('building_value', 0),
                    'applicant_name': prop.get('applicant_name'),
                    'opening_bid': prop.get('opening_bid', 0),
                    'winning_bid': prop.get('winning_bid'),
                    'winner_name': prop.get('winner_name'),
                    'auction_date': prop.get('auction_date'),
                    'close_time': prop.get('close_time'),
                    'status': prop.get('status', 'PENDING'),
                    'property_use_code': prop.get('property_use_code'),
                    'year_built': prop.get('year_built'),
                    'bedrooms': prop.get('bedrooms'),
                    'bathrooms': prop.get('bathrooms'),
                    'square_feet': prop.get('square_feet'),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Remove None values
                db_record = {k: v for k, v in db_record.items() if v is not None}
                
                # Upsert to database
                self.supabase.table('tax_deed_bidding_items').upsert(
                    db_record,
                    on_conflict='parcel_number'
                ).execute()
                
                saved_count += 1
                logger.info(f"Saved property: {prop.get('parcel_number')}")
                
            except Exception as e:
                logger.error(f"Error saving property {prop.get('parcel_number')}: {e}")
        
        return saved_count
    
    async def scrape_all(self):
        """Main scraping function"""
        logger.info("=== Starting Broward Tax Deed API Scrape ===")
        
        all_properties = []
        
        async with aiohttp.ClientSession() as self.session:
            # Fetch upcoming auctions
            logger.info("Fetching upcoming auctions...")
            upcoming = await self.fetch_auctions("upcoming")
            logger.info(f"Found {len(upcoming)} upcoming auctions")
            
            # Process each auction
            for auction in upcoming:
                try:
                    # Extract auction ID/batch from the link
                    if 'batch_closing_end' in auction:
                        link_data = auction['batch_closing_end']
                        if isinstance(link_data, dict) and 'href' in link_data:
                            href = link_data['href']
                            # Extract batch_uid from URL
                            match = re.search(r'batch_uid=([^&]+)', href)
                            if match:
                                batch_id = match.group(1)
                                logger.info(f"Fetching details for batch: {batch_id}")
                                
                                # Try alternative endpoints
                                endpoints = [
                                    f"/auctions/batch/{batch_id}/items",
                                    f"/api/batch/{batch_id}/items",
                                    f"/batch/{batch_id}/list"
                                ]
                                
                                for endpoint in endpoints:
                                    items = await self.fetch_batch_items(endpoint)
                                    if items:
                                        all_properties.extend(items)
                                        logger.info(f"Found {len(items)} properties in batch {batch_id}")
                                        break
                
                except Exception as e:
                    logger.error(f"Error processing auction: {e}")
            
            # Also fetch past auctions
            logger.info("Fetching past auctions...")
            past = await self.fetch_auctions("past")
            logger.info(f"Found {len(past)} past auctions")
            
            # Save all properties to database
            if all_properties:
                saved = await self.save_to_database(all_properties)
                logger.info(f"✅ Saved {saved} properties to database")
            else:
                logger.warning("No properties found to save")
        
        return {
            'upcoming_auctions': len(upcoming),
            'past_auctions': len(past),
            'properties_found': len(all_properties),
            'properties_saved': len(all_properties)
        }

async def main():
    """Run the scraper"""
    scraper = BrowardTaxDeedAPIScraper()
    results = await scraper.scrape_all()
    
    logger.info("=== SCRAPING COMPLETE ===")
    for key, value in results.items():
        logger.info(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())