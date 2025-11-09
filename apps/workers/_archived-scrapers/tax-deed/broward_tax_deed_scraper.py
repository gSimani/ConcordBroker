"""
Broward County Tax Deed Auction Scraper
Scrapes real auction data from broward.realauction.com
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
import os
from urllib.parse import urljoin, quote, parse_qs, urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowardTaxDeedScraper:
    def __init__(self):
        self.base_url = "https://broward.deedauction.net"
        self.session = None
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        else:
            logger.warning("⚠️ Supabase credentials not found")
            self.supabase = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch a page with retry logic"""
        for attempt in range(retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Status {response.status} for {url}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
        return None

    async def get_current_auctions(self) -> List[Dict]:
        """Get current and upcoming auctions from the main page"""
        logger.info("Fetching current auctions from broward.deedauction.net...")
        
        html = await self.fetch_page(self.base_url)
        if not html:
            logger.error("Failed to fetch main page")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        auctions = []
        
        # Look for auction listings on the page
        # The site structure may vary, so we try multiple approaches
        
        # Method 1: Look for auction date headers
        date_headers = soup.find_all(['h2', 'h3', 'div'], class_=re.compile('auction.*date|date.*auction', re.I))
        for header in date_headers:
            date_text = header.get_text(strip=True)
            if re.search(r'\d{1,2}/\d{1,2}/\d{4}|\w+ \d{1,2}, \d{4}', date_text):
                auctions.append({
                    'date': date_text,
                    'url': self.base_url,
                    'status': 'upcoming'
                })
        
        # Method 2: Look for auction links
        auction_links = soup.find_all('a', href=re.compile(r'auction|sale|bid', re.I))
        for link in auction_links[:10]:  # Limit to first 10 to avoid too many
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                text = link.get_text(strip=True)
                if not any(a['url'] == full_url for a in auctions):
                    auctions.append({
                        'date': text if re.search(r'\d', text) else 'Current',
                        'url': full_url,
                        'status': 'active'
                    })
        
        # If no auctions found, assume current page has active auctions
        if not auctions:
            auctions.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'url': self.base_url,
                'status': 'active'
            })
        
        logger.info(f"Found {len(auctions)} auction dates")
        return auctions

    async def scrape_auction_properties(self, auction_url: str) -> List[Dict]:
        """Scrape properties from an auction page"""
        logger.info(f"Scraping properties from {auction_url}")
        
        html = await self.fetch_page(auction_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        properties = []
        
        # Look for property listings - trying multiple possible structures
        # Real auction sites often use tables or divs with specific classes
        
        # Method 1: Look for table rows with property data
        property_tables = soup.find_all('table', class_=re.compile('property|auction|listing', re.I))
        for table in property_tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                property_data = self.extract_property_from_row(row)
                if property_data:
                    properties.append(property_data)
        
        # Method 2: Look for div-based property cards
        property_cards = soup.find_all('div', class_=re.compile('property.*card|listing.*item|auction.*item', re.I))
        for card in property_cards:
            property_data = self.extract_property_from_card(card)
            if property_data:
                properties.append(property_data)
        
        # Method 3: Look for any element with parcel number pattern
        if not properties:
            parcel_pattern = re.compile(r'\b\d{2}-?\d{2}-?\d{2}-?\d{4}\b|\b\d{10,14}\b')
            potential_properties = soup.find_all(text=parcel_pattern)
            
            for text_node in potential_properties[:20]:  # Limit to prevent too many
                parent = text_node.parent
                if parent:
                    # Try to extract property data from parent element
                    property_data = self.extract_property_from_element(parent)
                    if property_data:
                        properties.append(property_data)
        
        logger.info(f"Extracted {len(properties)} properties")
        return properties

    def extract_property_from_row(self, row) -> Optional[Dict]:
        """Extract property data from a table row"""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                return None
            
            property_data = {
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'broward.realauction.com'
            }
            
            # Try to extract data from cells
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                
                # Look for patterns in cell text
                if re.match(r'TD-?\d+', text):
                    property_data['tax_deed_number'] = text
                elif re.match(r'\d{2}-?\d{2}-?\d{2}-?\d{4}|\d{10,}', text):
                    property_data['parcel_number'] = re.sub(r'[^\d-]', '', text)
                elif '$' in text:
                    # Extract dollar amount
                    amount = re.sub(r'[^\d.]', '', text)
                    if amount:
                        if 'opening_bid' not in property_data:
                            property_data['opening_bid'] = float(amount)
                        else:
                            property_data['winning_bid'] = float(amount)
                elif re.search(r'\d+.*(?:st|nd|rd|th|ave|way|dr|blvd)', text, re.I):
                    property_data['situs_address'] = text
                elif re.search(r'homestead', text, re.I):
                    property_data['is_homestead'] = True
            
            return property_data if property_data.get('parcel_number') else None
            
        except Exception as e:
            logger.debug(f"Error extracting from row: {e}")
            return None

    def extract_property_from_card(self, card) -> Optional[Dict]:
        """Extract property data from a div-based card"""
        try:
            property_data = {
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'broward.realauction.com'
            }
            
            # Extract text content
            text = card.get_text(' ', strip=True)
            
            # Extract using patterns
            patterns = {
                'tax_deed_number': r'TD-?\d+|Tax\s*Deed\s*#?\s*(\d+)',
                'parcel_number': r'\d{2}-?\d{2}-?\d{2}-?\d{4}|\d{10,}',
                'opening_bid': r'Opening\s*Bid:?\s*\$?([\d,]+(?:\.\d{2})?)',
                'winning_bid': r'Winning\s*Bid:?\s*\$?([\d,]+(?:\.\d{2})?)',
                'situs_address': r'(\d+\s+[\w\s]+(?:Street|Avenue|Way|Drive|Boulevard|Lane|Court|Place|Road))',
                'applicant_name': r'Applicant:?\s*([^$\n]+)',
                'status': r'Status:?\s*(\w+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, text, re.I)
                if match:
                    if field in ['opening_bid', 'winning_bid']:
                        property_data[field] = float(match.group(1).replace(',', ''))
                    elif field == 'parcel_number':
                        property_data[field] = re.sub(r'[^\d-]', '', match.group(0))
                    else:
                        property_data[field] = match.group(1) if match.groups() else match.group(0)
            
            # Check for homestead
            if re.search(r'homestead', text, re.I):
                property_data['is_homestead'] = True
            
            return property_data if property_data.get('parcel_number') else None
            
        except Exception as e:
            logger.debug(f"Error extracting from card: {e}")
            return None

    def extract_property_from_element(self, element) -> Optional[Dict]:
        """Extract property data from any element"""
        try:
            # Get parent container (might have more context)
            container = element.parent if element.parent else element
            
            property_data = {
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'broward.realauction.com'
            }
            
            # Get all text from container
            text = container.get_text(' ', strip=True)
            
            # Extract parcel number (required)
            parcel_match = re.search(r'\b(\d{2}-?\d{2}-?\d{2}-?\d{4}|\d{10,14})\b', text)
            if not parcel_match:
                return None
            
            property_data['parcel_number'] = re.sub(r'[^\d-]', '', parcel_match.group(1))
            
            # Extract other fields
            if match := re.search(r'TD-?\d+', text):
                property_data['tax_deed_number'] = match.group(0)
            
            if match := re.search(r'\$\s?([\d,]+(?:\.\d{2})?)', text):
                property_data['opening_bid'] = float(match.group(1).replace(',', ''))
            
            if match := re.search(r'(\d+\s+[\w\s]+(?:Street|Avenue|Way|Drive|Boulevard|Lane|Court|Place|Road))', text, re.I):
                property_data['situs_address'] = match.group(1)
            
            # Look for links
            links = container.find_all('a', href=True)
            for link in links:
                href = link['href']
                if 'bcpa.net' in href:
                    property_data['property_appraiser_url'] = href
                elif 'sunbiz.org' in href:
                    property_data['sunbiz_url'] = href
            
            return property_data
            
        except Exception as e:
            logger.debug(f"Error extracting from element: {e}")
            return None

    def enrich_property_data(self, property_data: Dict) -> Dict:
        """Enrich property data with additional fields and URLs"""
        # Generate Property Appraiser URL if not present
        if property_data.get('parcel_number') and not property_data.get('property_appraiser_url'):
            clean_parcel = re.sub(r'[^\d]', '', property_data['parcel_number'])
            property_data['property_appraiser_url'] = f"https://web.bcpa.net/bcpaclient/#/Record/RealEstate/{clean_parcel}"
            property_data['gis_map_url'] = f"https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id={clean_parcel}"
        
        # Generate Sunbiz URL if applicant name exists
        if property_data.get('applicant_name') and not property_data.get('sunbiz_url'):
            encoded_name = quote(property_data['applicant_name'])
            property_data['sunbiz_url'] = f"https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults?inquiryType=EntityName&searchTerm={encoded_name}"
        
        # Set default status if not present
        if not property_data.get('status'):
            property_data['status'] = 'Active'
        
        # Ensure auction_date is set
        if not property_data.get('auction_date'):
            property_data['auction_date'] = datetime.now().date().isoformat()
        
        return property_data

    async def save_to_supabase(self, properties: List[Dict]) -> Dict:
        """Save scraped properties to Supabase database"""
        results = {
            'inserted': 0,
            'updated': 0,
            'errors': 0
        }
        
        if not self.supabase:
            logger.warning("Supabase client not initialized - skipping save")
            return results
        
        for property_data in properties:
            try:
                # Enrich data before saving
                property_data = self.enrich_property_data(property_data)
                
                # Map to tax_deed_bidding_items table structure
                db_record = {
                    'tax_deed_number': property_data.get('tax_deed_number'),
                    'parcel_id': property_data.get('parcel_number'),
                    'tax_certificate_number': property_data.get('tax_certificate_number'),
                    'legal_situs_address': property_data.get('situs_address'),
                    'homestead_exemption': 'Y' if property_data.get('is_homestead') else 'N',
                    'assessed_value': property_data.get('assessed_value'),
                    'opening_bid': property_data.get('opening_bid', 0),
                    'winning_bid': property_data.get('winning_bid'),
                    'current_bid': property_data.get('best_bid'),
                    'item_status': property_data.get('status', 'Active'),
                    'applicant_name': property_data.get('applicant_name'),
                    'auction_date': property_data.get('auction_date'),
                    'close_time': property_data.get('close_time'),
                    'source': 'broward.realauction.com'
                }
                
                # Check if property already exists
                existing = self.supabase.table('tax_deed_bidding_items').select('id').eq(
                    'parcel_id', db_record['parcel_id']
                ).eq(
                    'auction_date', db_record['auction_date']
                ).execute()
                
                if existing.data:
                    # Update existing record
                    response = self.supabase.table('tax_deed_bidding_items').update(db_record).eq(
                        'id', existing.data[0]['id']
                    ).execute()
                    results['updated'] += 1
                    logger.info(f"Updated: {db_record['parcel_id']}")
                else:
                    # Insert new record
                    response = self.supabase.table('tax_deed_bidding_items').insert(db_record).execute()
                    results['inserted'] += 1
                    logger.info(f"Inserted: {db_record['parcel_id']}")
                    
            except Exception as e:
                logger.error(f"Error saving property {property_data.get('parcel_number')}: {e}")
                results['errors'] += 1
        
        return results

    async def scrape_all(self) -> Dict:
        """Main method to scrape all auctions and properties"""
        logger.info("=== Starting Broward Tax Deed Auction Scrape ===")
        
        results = {
            'auctions_scraped': 0,
            'properties_scraped': 0,
            'properties_saved': 0,
            'errors': []
        }
        
        try:
            # Get current auctions
            auctions = await self.get_current_auctions()
            results['auctions_scraped'] = len(auctions)
            
            all_properties = []
            
            # Scrape each auction
            for auction in auctions:
                try:
                    properties = await self.scrape_auction_properties(auction['url'])
                    
                    # Add auction date to each property
                    for prop in properties:
                        prop['auction_date'] = auction['date']
                        prop['auction_status'] = auction['status']
                    
                    all_properties.extend(properties)
                    logger.info(f"Scraped {len(properties)} properties from {auction['date']} auction")
                    
                    # Small delay between auctions
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error scraping auction {auction['date']}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            results['properties_scraped'] = len(all_properties)
            
            # Save to Supabase
            if all_properties:
                save_results = await self.save_to_supabase(all_properties)
                results['properties_saved'] = save_results['inserted'] + save_results['updated']
                results.update(save_results)
            
            logger.info("=== Scraping Complete ===")
            logger.info(f"Auctions: {results['auctions_scraped']}")
            logger.info(f"Properties scraped: {results['properties_scraped']}")
            logger.info(f"Properties saved: {results['properties_saved']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Fatal error in scrape_all: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results


async def main():
    """Run the scraper"""
    async with BrowardTaxDeedScraper() as scraper:
        results = await scraper.scrape_all()
        
        print("\n=== SCRAPING COMPLETE ===")
        print(f"Auctions scraped: {results['auctions_scraped']}")
        print(f"Properties scraped: {results['properties_scraped']}")
        print(f"Properties saved: {results['properties_saved']}")
        
        if 'inserted' in results:
            print(f"  - New properties: {results['inserted']}")
        if 'updated' in results:
            print(f"  - Updated properties: {results['updated']}")
        
        if results['errors']:
            print("\n⚠️ Errors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
        
        return results


if __name__ == "__main__":
    asyncio.run(main())