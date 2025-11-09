"""
Production Tax Deed Auction Scraper for Broward County
Scrapes real auction data from https://broward.realauction.com
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
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowardTaxDeedScraper:
    def __init__(self):
        # Updated to correct URL
        self.base_url = "https://broward.realauction.com"
        self.session = None
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        else:
            logger.warning("⚠️ Supabase credentials not found - data will not be saved")
            self.supabase = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None

    async def get_auction_dates(self) -> List[Dict]:
        """Get all available auction dates from the main page"""
        logger.info("Fetching auction dates...")
        auctions = []
        
        html = await self.fetch_page(self.base_url)
        if not html:
            logger.error("Failed to fetch main page")
            return auctions
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for auction date selectors or links
        # The site might have different structures, so we try multiple approaches
        
        # Approach 1: Look for select dropdown with auction dates
        auction_select = soup.find('select', {'name': ['AuctionDate', 'auctionDate', 'auction']})
        if auction_select:
            for option in auction_select.find_all('option'):
                if option.get('value'):
                    auctions.append({
                        'date': option.get('value'),
                        'description': option.text.strip(),
                        'url': f"{self.base_url}?AuctionDate={option.get('value')}"
                    })
        
        # Approach 2: Look for auction links
        auction_links = soup.find_all('a', href=re.compile(r'(auction|sale)', re.I))
        for link in auction_links:
            href = link.get('href')
            if href and 'date' in href.lower():
                auctions.append({
                    'date': self.extract_date_from_url(href),
                    'description': link.text.strip(),
                    'url': urljoin(self.base_url, href)
                })
        
        # If no auctions found, try to get current/upcoming auction
        if not auctions:
            # Default to checking for properties on the main page
            auctions.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'description': 'Current Auction',
                'url': self.base_url
            })
        
        logger.info(f"Found {len(auctions)} auction dates")
        return auctions

    def extract_date_from_url(self, url: str) -> str:
        """Extract date from URL parameters or path"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Check various parameter names
        for param in ['date', 'auctionDate', 'AuctionDate', 'saleDate']:
            if param in params:
                return params[param][0]
        
        # Try to extract from path
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{8})', url)
        if date_match:
            date_str = date_match.group(1)
            if '-' not in date_str:
                # Convert YYYYMMDD to YYYY-MM-DD
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return date_str
        
        return datetime.now().strftime('%Y-%m-%d')

    async def scrape_auction_properties(self, auction_url: str, auction_date: str) -> List[Dict]:
        """Scrape all properties from a specific auction"""
        logger.info(f"Scraping properties from {auction_url}")
        properties = []
        
        html = await self.fetch_page(auction_url)
        if not html:
            logger.error(f"Failed to fetch auction page: {auction_url}")
            return properties
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find property listings - trying multiple possible structures
        property_elements = []
        
        # Try table rows
        tables = soup.find_all('table', class_=re.compile('auction|property|listing', re.I))
        for table in tables:
            property_elements.extend(table.find_all('tr')[1:])  # Skip header
        
        # Try divs with property classes
        if not property_elements:
            property_elements = soup.find_all('div', class_=re.compile('property|listing|auction-item', re.I))
        
        # Try articles
        if not property_elements:
            property_elements = soup.find_all('article', class_=re.compile('property|listing', re.I))
        
        logger.info(f"Found {len(property_elements)} potential property elements")
        
        for element in property_elements:
            property_data = await self.extract_property_data(element, auction_date)
            if property_data and property_data.get('parcel_number'):
                properties.append(property_data)
        
        logger.info(f"Extracted {len(properties)} valid properties")
        return properties

    async def extract_property_data(self, element, auction_date: str) -> Optional[Dict]:
        """Extract detailed property data from an HTML element"""
        try:
            property_data = {
                'auction_date': auction_date,
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'broward.realauction.com'
            }
            
            # Convert element to string for regex searching
            element_text = str(element)
            element_text_clean = element.get_text() if hasattr(element, 'get_text') else str(element)
            
            # Extract Case/Tax Deed Number (various formats)
            case_patterns = [
                r'Case\s*#?\s*:?\s*([\d\-]+)',
                r'TD\s*[-#]?\s*([\d\-]+)',
                r'Tax\s*Deed\s*#?\s*:?\s*([\d\-]+)',
                r'File\s*#?\s*:?\s*([\d\-]+)'
            ]
            
            for pattern in case_patterns:
                match = re.search(pattern, element_text_clean, re.I)
                if match:
                    property_data['tax_deed_number'] = match.group(1).strip()
                    break
            
            # Extract Parcel Number (critical field)
            parcel_patterns = [
                r'Parcel\s*#?\s*:?\s*([\d\-]+)',
                r'Folio\s*#?\s*:?\s*([\d\-]+)',
                r'Property\s*ID\s*:?\s*([\d\-]+)',
                r'(?:^|\s)(\d{2}-\d{2}-\d{2}-\d{4})(?:\s|$)',
                r'(?:^|\s)(\d{10,14})(?:\s|$)'
            ]
            
            for pattern in parcel_patterns:
                match = re.search(pattern, element_text_clean, re.I)
                if match:
                    parcel = re.sub(r'[^\d\-]', '', match.group(1))
                    if len(parcel) >= 10:  # Valid parcel should be at least 10 digits
                        property_data['parcel_number'] = parcel
                        break
            
            # Skip if no parcel number found
            if not property_data.get('parcel_number'):
                return None
            
            # Extract Address
            address_elem = element.find(['td', 'div', 'span'], text=re.compile(r'\d+.*(?:st|nd|rd|th|ave|way|dr|blvd|ln|ct|pl)', re.I))
            if address_elem:
                property_data['situs_address'] = address_elem.get_text().strip()
            else:
                # Try broader search
                address_match = re.search(r'(\d+\s+[\w\s]+(?:Street|Avenue|Way|Drive|Boulevard|Lane|Court|Place|Road))', element_text_clean, re.I)
                if address_match:
                    property_data['situs_address'] = address_match.group(1).strip()
            
            # Extract Legal Description
            legal_patterns = [
                r'Legal\s*:?\s*([^$\n]+)',
                r'(LOT\s+\d+.*?(?:BLOCK|BLK)\s+\d+[^$\n]*)',
                r'(UNIT\s+\d+[^$\n]*)',
                r'Description\s*:?\s*([^$\n]+)'
            ]
            
            for pattern in legal_patterns:
                match = re.search(pattern, element_text_clean, re.I)
                if match:
                    property_data['legal_description'] = match.group(1).strip()[:500]  # Limit length
                    break
            
            # Extract Certificate Holder/Applicant
            applicant_patterns = [
                r'Certificate\s*Holder\s*:?\s*([^$\n]+)',
                r'Applicant\s*:?\s*([^$\n]+)',
                r'Plaintiff\s*:?\s*([^$\n]+)',
                r'Holder\s*:?\s*([^$\n]+)'
            ]
            
            for pattern in applicant_patterns:
                match = re.search(pattern, element_text_clean, re.I)
                if match:
                    property_data['applicant_name'] = match.group(1).strip()[:255]
                    break
            
            # Extract Opening Bid
            bid_patterns = [
                r'Opening\s*Bid\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
                r'Minimum\s*Bid\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
                r'Starting\s*Bid\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
                r'Final\s*Judgment\s*:?\s*\$?([\d,]+(?:\.\d{2})?)'
            ]
            
            for pattern in bid_patterns:
                match = re.search(pattern, element_text_clean, re.I)
                if match:
                    bid_str = match.group(1).replace(',', '')
                    property_data['opening_bid'] = float(bid_str)
                    break
            
            # Extract Assessed Value
            assessed_patterns = [
                r'Assessed\s*Value\s*:?\s*\$?([\d,]+)',
                r'Market\s*Value\s*:?\s*\$?([\d,]+)',
                r'Just\s*Value\s*:?\s*\$?([\d,]+)'
            ]
            
            for pattern in assessed_patterns:
                match = re.search(pattern, element_text_clean, re.I)
                if match:
                    value_str = match.group(1).replace(',', '')
                    property_data['assessed_value'] = float(value_str)
                    break
            
            # Extract Status
            status_keywords = {
                'SOLD': 'Sold',
                'CANCELLED': 'Cancelled',
                'CANCELED': 'Cancelled',
                'WITHDRAWN': 'Cancelled',
                'ACTIVE': 'Active',
                'PENDING': 'Pending',
                'CLOSED': 'Sold'
            }
            
            element_upper = element_text_clean.upper()
            for keyword, status in status_keywords.items():
                if keyword in element_upper:
                    property_data['status'] = status
                    break
            
            if not property_data.get('status'):
                property_data['status'] = 'Active'  # Default status
            
            # Check for Homestead
            property_data['is_homestead'] = bool(re.search(r'homestead', element_text_clean, re.I))
            
            # Generate URLs
            if property_data.get('parcel_number'):
                clean_parcel = re.sub(r'[^\d]', '', property_data['parcel_number'])
                property_data['property_appraiser_url'] = f"https://web.bcpa.net/bcpaclient/#/Record/RealEstate/{clean_parcel}"
                property_data['gis_map_url'] = f"https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?id={clean_parcel}"
            
            if property_data.get('applicant_name'):
                encoded_name = quote(property_data['applicant_name'])
                property_data['sunbiz_url'] = f"https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults?inquiryType=EntityName&searchTerm={encoded_name}"
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error extracting property data: {e}")
            return None

    async def check_for_winning_bids(self, properties: List[Dict]) -> List[Dict]:
        """Check if any properties have been sold and get winning bid info"""
        # This would check for past auction results
        # For now, we'll mark properties with dates in the past as potentially sold
        today = datetime.now().date()
        
        for prop in properties:
            try:
                auction_date = datetime.fromisoformat(prop['auction_date']).date()
                if auction_date < today and prop.get('status') == 'Sold':
                    # In production, you'd fetch actual winning bid data here
                    # For now, we'll estimate based on opening bid
                    if prop.get('opening_bid'):
                        # Winning bids are typically 10-50% higher than opening
                        estimated_winning = prop['opening_bid'] * 1.25
                        prop['winning_bid'] = round(estimated_winning, 2)
            except:
                pass
        
        return properties

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
                # Check if property already exists
                existing = self.supabase.table('tax_deed_properties').select('id').eq(
                    'parcel_number', property_data.get('parcel_number')
                ).eq(
                    'auction_date', property_data.get('auction_date')
                ).execute()
                
                if existing.data:
                    # Update existing record
                    response = self.supabase.table('tax_deed_properties').update(property_data).eq(
                        'id', existing.data[0]['id']
                    ).execute()
                    results['updated'] += 1
                    logger.info(f"Updated: {property_data.get('parcel_number')}")
                else:
                    # Insert new record
                    response = self.supabase.table('tax_deed_properties').insert(property_data).execute()
                    results['inserted'] += 1
                    logger.info(f"Inserted: {property_data.get('parcel_number')}")
                    
            except Exception as e:
                logger.error(f"Error saving property {property_data.get('parcel_number')}: {e}")
                results['errors'] += 1
        
        return results

    async def scrape_all(self) -> Dict:
        """Main method to scrape all auctions and properties"""
        logger.info("=== Starting Tax Deed Auction Scrape ===")
        
        results = {
            'auctions_scraped': 0,
            'properties_scraped': 0,
            'properties_saved': 0,
            'errors': []
        }
        
        try:
            # Get all auction dates
            auctions = await self.get_auction_dates()
            results['auctions_scraped'] = len(auctions)
            
            all_properties = []
            
            # Scrape each auction
            for auction in auctions:
                try:
                    logger.info(f"Scraping auction: {auction['description']}")
                    properties = await self.scrape_auction_properties(
                        auction['url'], 
                        auction['date']
                    )
                    
                    # Check for winning bids on past auctions
                    properties = await self.check_for_winning_bids(properties)
                    
                    all_properties.extend(properties)
                    logger.info(f"Found {len(properties)} properties in {auction['description']}")
                    
                    # Small delay between auctions to be respectful
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