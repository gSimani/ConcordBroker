"""
Broward County Tax Deed Auction Scraper Agent
==============================================
Sophisticated agent to scrape upcoming tax deed auctions from broward.deedauction.net
Extracts comprehensive property data including expanded details for each property.
"""

import asyncio
import aiohttp
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuctionStatus(Enum):
    """Auction status enumeration"""
    UPCOMING = "Upcoming"
    ACTIVE = "Active"
    CLOSED = "Closed"
    CANCELED = "Canceled"

class PropertyStatus(Enum):
    """Property status enumeration"""
    UPCOMING = "Upcoming"
    ACTIVE = "Active"
    SOLD = "Sold"
    CANCELED = "Canceled"
    REMOVED = "Removed"

@dataclass
class PropertyDetail:
    """Data class for property details"""
    item_id: str
    tax_deed_number: str
    parcel_number: str
    parcel_url: Optional[str]
    tax_certificate_number: Optional[str]
    legal_description: str
    situs_address: str
    homestead: bool
    assessed_value: Optional[float]
    soh_value: Optional[float]
    applicant: str
    applicant_companies: List[str]  # Parsed company names for Sunbiz matching
    gis_map_url: Optional[str]
    opening_bid: float
    best_bid: Optional[float]
    close_time: Optional[datetime]
    status: PropertyStatus
    raw_html: Optional[str] = None
    extracted_at: Optional[datetime] = None

@dataclass
class Auction:
    """Data class for auction information"""
    auction_id: str
    description: str
    auction_date: datetime
    total_items: int
    available_items: int
    advertised_items: int
    canceled_items: int
    status: AuctionStatus
    auction_url: str
    properties: List[PropertyDetail]
    last_updated: datetime

class TaxDeedAuctionScraper:
    """Main scraper class for tax deed auctions"""
    
    BASE_URL = "https://broward.deedauction.net"
    AUCTIONS_URL = f"{BASE_URL}/auctions"
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the scraper"""
        self.session = session
        self.auctions_data = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def fetch_page(self, url: str, retry_count: int = 3) -> Optional[str]:
        """Fetch a page with retry logic"""
        for attempt in range(retry_count):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Status {response.status} for {url}")
                        
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    
        return None
        
    def parse_upcoming_auctions(self, html: str) -> List[Dict[str, Any]]:
        """Parse the upcoming auctions table"""
        soup = BeautifulSoup(html, 'html.parser')
        auctions = []
        
        # Find the upcoming auctions table
        upcoming_table = soup.find('table', {'id': 'upcoming_auctions'})
        if not upcoming_table:
            logger.error("Could not find upcoming auctions table")
            return auctions
            
        tbody = upcoming_table.find('tbody')
        if not tbody:
            return auctions
            
        for row in tbody.find_all('tr'):
            try:
                auction_data = {}
                
                # Get auction ID from row
                auction_data['auction_id'] = row.get('id', '')
                
                # Get cells
                cells = row.find_all('td')
                if len(cells) >= 4:
                    # Description with link
                    desc_cell = cells[0]
                    link = desc_cell.find('a')
                    if link:
                        auction_data['description'] = link.text.strip()
                        auction_data['url'] = urljoin(self.BASE_URL, link['href'])
                        
                        # Extract date from description (e.g., "9/17/2025 Tax Deed Sale")
                        date_match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})', auction_data['description'])
                        if date_match:
                            auction_data['date'] = date_match.group(1)
                    
                    # Number of items
                    auction_data['total_items'] = int(cells[1].text.strip())
                    
                    # Status
                    auction_data['status'] = cells[2].text.strip()
                    
                    # Deposit status
                    auction_data['deposit_status'] = cells[3].text.strip()
                    
                    auctions.append(auction_data)
                    
            except Exception as e:
                logger.error(f"Error parsing auction row: {e}")
                continue
                
        return auctions
        
    async def fetch_auction_details(self, auction_url: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a specific auction"""
        html = await self.fetch_page(auction_url)
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        auction_details = {
            'properties': [],
            'statistics': {}
        }
        
        # Parse auction header information
        content_header = soup.find('div', {'id': 'content_header'})
        if content_header:
            subtitle = content_header.find('span', {'class': 'subtitle'})
            headline = content_header.find('span', {'class': 'headline'})
            page_desc = content_header.find('div', {'class': 'page_desc'})
            
            if subtitle:
                auction_details['title'] = subtitle.text.strip()
            if headline:
                auction_details['date'] = headline.text.strip()
            if page_desc:
                # Extract "14 properties available for sale"
                match = re.search(r'(\d+) properties available for sale', page_desc.text)
                if match:
                    auction_details['available_count'] = int(match.group(1))
                    
        # Parse statistics (Advertised, Canceled, Available)
        stats_div = soup.find('div', {'id': 'bid_table_stats'})
        if stats_div:
            stats_text = stats_div.text
            advertised_match = re.search(r'Advertised:\s*(\d+)', stats_text)
            canceled_match = re.search(r'Canceled:\s*(\d+)', stats_text)
            available_match = re.search(r'Available for Sale:\s*(\d+)', stats_text)
            
            if advertised_match:
                auction_details['statistics']['advertised'] = int(advertised_match.group(1))
            if canceled_match:
                auction_details['statistics']['canceled'] = int(canceled_match.group(1))
            if available_match:
                auction_details['statistics']['available'] = int(available_match.group(1))
                
        # Parse properties table
        properties_table = soup.find('table', {'id': 'results'})
        if properties_table:
            tbody = properties_table.find('tbody')
            if tbody:
                # Find all property rows (summary rows)
                property_rows = tbody.find_all('tr', id=re.compile(r'\d+\.summary'))
                
                for row in property_rows:
                    property_data = await self.parse_property_row(row, auction_url)
                    if property_data:
                        auction_details['properties'].append(property_data)
                        
        return auction_details
        
    async def parse_property_row(self, row, auction_url: str) -> Optional[Dict[str, Any]]:
        """Parse a single property row"""
        try:
            property_data = {}
            
            # Get property ID from row ID
            row_id = row.get('id', '')
            if row_id:
                property_id = row_id.split('.')[0]
                property_data['item_id'] = property_id
                
            # Get cells
            cells = row.find_all('td')
            
            # Tax Deed Number (column 1)
            if len(cells) > 1:
                property_data['tax_deed_number'] = cells[1].text.strip()
                
            # Opening Bid (column 2)
            if len(cells) > 2:
                opening_bid_text = cells[2].text.strip().replace('$', '').replace(',', '')
                try:
                    property_data['opening_bid'] = float(opening_bid_text)
                except:
                    property_data['opening_bid'] = 0.0
                    
            # Best Bid (column 3)
            if len(cells) > 3:
                best_bid_text = cells[3].text.strip()
                if best_bid_text != '-':
                    best_bid_text = best_bid_text.replace('$', '').replace(',', '')
                    try:
                        property_data['best_bid'] = float(best_bid_text)
                    except:
                        property_data['best_bid'] = None
                else:
                    property_data['best_bid'] = None
                    
            # Close Time (column 4)
            if len(cells) > 4:
                time_cell = cells[4]
                time_span = time_cell.find('span', id=re.compile(r'time_remaining'))
                if time_span:
                    property_data['close_time'] = time_span.text.strip()
                    
                # Get actual end time from hidden input
                end_time_input = time_cell.find('input', id=re.compile(r'end_time'))
                if end_time_input:
                    property_data['end_time'] = end_time_input.get('value', '')
                    
            # Status (column 5)
            if len(cells) > 5:
                property_data['status'] = cells[5].text.strip()
                
            # Check if property is disabled (canceled/removed)
            if 'disabled' in row.get('class', []):
                property_data['is_disabled'] = True
                
                # Check for removal message
                message_row = row.find_next_sibling('tr', id=re.compile(r'\d+\.message'))
                if message_row:
                    removal_div = message_row.find('div', id=re.compile(r'removal_message'))
                    if removal_div:
                        property_data['removal_message'] = removal_div.text.strip()
                        
            # Fetch expanded details
            if property_data.get('item_id'):
                expanded_details = await self.fetch_property_details(
                    auction_url,
                    property_data['item_id']
                )
                if expanded_details:
                    property_data.update(expanded_details)
                    
            return property_data
            
        except Exception as e:
            logger.error(f"Error parsing property row: {e}")
            return None
            
    async def fetch_property_details(self, auction_url: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Fetch expanded property details by simulating the expand action"""
        try:
            # Extract auction ID from URL
            auction_id = auction_url.split('/')[-1]
            
            # Construct the detail URL
            detail_url = f"{self.BASE_URL}/auction/{auction_id}/{item_id}/details"
            
            html = await self.fetch_page(detail_url)
            if not html:
                # Try alternative URL format
                detail_url = f"{self.BASE_URL}/item_details/{auction_id}/{item_id}"
                html = await self.fetch_page(detail_url)
                
            if not html:
                return None
                
            return self.parse_property_details(html)
            
        except Exception as e:
            logger.error(f"Error fetching property details for {item_id}: {e}")
            return None
            
    def parse_property_details(self, html: str) -> Dict[str, Any]:
        """Parse the expanded property details HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        details = {}
        
        # Find the details table
        details_table = soup.find('table', class_='bare wrap')
        if not details_table:
            details_table = soup.find('table')
            
        if details_table:
            for row in details_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].text.strip().replace(':', '')
                    value_cell = cells[1]
                    
                    if label == 'Parcel #':
                        details['parcel_number'] = value_cell.text.strip()
                        # Get parcel URL
                        parcel_link = value_cell.find('a')
                        if parcel_link:
                            details['parcel_url'] = parcel_link.get('href', '')
                            # Clean up parcel number
                            details['parcel_number'] = parcel_link.text.strip()
                            
                    elif label == 'Tax Certificate #':
                        details['tax_certificate_number'] = value_cell.text.strip()
                        
                    elif label == 'Legal':
                        details['legal_description'] = ' '.join(value_cell.text.split())
                        
                    elif label == 'Situs Address':
                        details['situs_address'] = value_cell.text.strip()
                        
                    elif label == 'Homestead':
                        details['homestead'] = value_cell.text.strip().lower() == 'yes'
                        
                    elif label == 'Assessed / SOH Value':
                        value_text = value_cell.text.strip().replace('$', '').replace(',', '')
                        try:
                            details['assessed_value'] = float(value_text)
                        except:
                            details['assessed_value'] = value_text
                            
                    elif label == 'Applicant':
                        applicant_text = value_cell.text.strip()
                        details['applicant'] = applicant_text
                        
                        # Parse company names for Sunbiz matching
                        companies = []
                        for line in applicant_text.split('\n'):
                            line = line.strip()
                            if line and any(keyword in line.upper() for keyword in ['LLC', 'INC', 'CORP', 'TRUST', 'LP', 'LLP']):
                                companies.append(line)
                        details['applicant_companies'] = companies
                        
                    elif label == 'Links':
                        # Get GIS map link
                        gis_link = value_cell.find('a', text=re.compile('GIS'))
                        if gis_link:
                            details['gis_map_url'] = urljoin(self.BASE_URL, gis_link.get('href', ''))
                            
        return details
        
    async def scrape_all_auctions(self) -> List[Auction]:
        """Main method to scrape all upcoming auctions and their properties"""
        logger.info("Starting auction scraping...")
        
        # Fetch the main auctions page
        html = await self.fetch_page(self.AUCTIONS_URL)
        if not html:
            logger.error("Failed to fetch auctions page")
            return []
            
        # Parse upcoming auctions
        upcoming_auctions = self.parse_upcoming_auctions(html)
        logger.info(f"Found {len(upcoming_auctions)} upcoming auctions")
        
        auctions = []
        
        # Fetch details for each auction
        for auction_info in upcoming_auctions:
            try:
                logger.info(f"Fetching details for auction: {auction_info['description']}")
                
                auction_details = await self.fetch_auction_details(auction_info['url'])
                if auction_details:
                    # Create Auction object
                    auction = Auction(
                        auction_id=auction_info['auction_id'],
                        description=auction_info['description'],
                        auction_date=self.parse_date(auction_info.get('date', '')),
                        total_items=auction_info['total_items'],
                        available_items=auction_details.get('available_count', 0),
                        advertised_items=auction_details.get('statistics', {}).get('advertised', 0),
                        canceled_items=auction_details.get('statistics', {}).get('canceled', 0),
                        status=AuctionStatus(auction_info['status']),
                        auction_url=auction_info['url'],
                        properties=self.convert_properties(auction_details.get('properties', [])),
                        last_updated=datetime.now(timezone.utc)
                    )
                    
                    auctions.append(auction)
                    logger.info(f"Successfully scraped auction {auction.auction_id} with {len(auction.properties)} properties")
                    
                # Add delay between auctions to avoid rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing auction {auction_info.get('description', '')}: {e}")
                continue
                
        return auctions
        
    def parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object"""
        try:
            return datetime.strptime(date_str, '%m/%d/%Y')
        except:
            return datetime.now(timezone.utc)
            
    def convert_properties(self, properties_data: List[Dict]) -> List[PropertyDetail]:
        """Convert raw property data to PropertyDetail objects"""
        properties = []
        
        for prop_data in properties_data:
            try:
                # Parse close time
                close_time = None
                if prop_data.get('end_time'):
                    try:
                        close_time = datetime.strptime(prop_data['end_time'], '%m/%d/%Y %I:%M:%S %p')
                    except:
                        pass
                        
                # Determine property status
                status = PropertyStatus.UPCOMING
                if prop_data.get('status'):
                    status_str = prop_data['status'].upper()
                    if 'CANCEL' in status_str:
                        status = PropertyStatus.CANCELED
                    elif 'SOLD' in status_str:
                        status = PropertyStatus.SOLD
                    elif 'ACTIVE' in status_str:
                        status = PropertyStatus.ACTIVE
                    elif prop_data.get('removal_message'):
                        status = PropertyStatus.REMOVED
                        
                property_detail = PropertyDetail(
                    item_id=prop_data.get('item_id', ''),
                    tax_deed_number=prop_data.get('tax_deed_number', ''),
                    parcel_number=prop_data.get('parcel_number', ''),
                    parcel_url=prop_data.get('parcel_url'),
                    tax_certificate_number=prop_data.get('tax_certificate_number'),
                    legal_description=prop_data.get('legal_description', ''),
                    situs_address=prop_data.get('situs_address', ''),
                    homestead=prop_data.get('homestead', False),
                    assessed_value=prop_data.get('assessed_value'),
                    soh_value=prop_data.get('soh_value'),
                    applicant=prop_data.get('applicant', ''),
                    applicant_companies=prop_data.get('applicant_companies', []),
                    gis_map_url=prop_data.get('gis_map_url'),
                    opening_bid=prop_data.get('opening_bid', 0.0),
                    best_bid=prop_data.get('best_bid'),
                    close_time=close_time,
                    status=status,
                    extracted_at=datetime.now(timezone.utc)
                )
                
                properties.append(property_detail)
                
            except Exception as e:
                logger.error(f"Error converting property data: {e}")
                continue
                
        return properties
        
    def save_to_json(self, auctions: List[Auction], filename: str = 'tax_deed_auctions.json'):
        """Save auction data to JSON file"""
        data = []
        for auction in auctions:
            auction_dict = {
                'auction_id': auction.auction_id,
                'description': auction.description,
                'auction_date': auction.auction_date.isoformat() if auction.auction_date else None,
                'total_items': auction.total_items,
                'available_items': auction.available_items,
                'advertised_items': auction.advertised_items,
                'canceled_items': auction.canceled_items,
                'status': auction.status.value,
                'auction_url': auction.auction_url,
                'last_updated': auction.last_updated.isoformat() if auction.last_updated else None,
                'properties': []
            }
            
            for prop in auction.properties:
                prop_dict = asdict(prop)
                # Convert datetime objects to ISO format
                if prop_dict.get('close_time'):
                    prop_dict['close_time'] = prop_dict['close_time'].isoformat()
                if prop_dict.get('extracted_at'):
                    prop_dict['extracted_at'] = prop_dict['extracted_at'].isoformat()
                # Convert enum to string
                if prop_dict.get('status'):
                    prop_dict['status'] = prop.status.value
                    
                auction_dict['properties'].append(prop_dict)
                
            data.append(auction_dict)
            
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Saved {len(auctions)} auctions to {filename}")
        
async def main():
    """Main function to run the scraper"""
    async with TaxDeedAuctionScraper() as scraper:
        auctions = await scraper.scrape_all_auctions()
        
        # Print summary
        for auction in auctions:
            print(f"\n{'='*60}")
            print(f"Auction: {auction.description}")
            print(f"Date: {auction.auction_date}")
            print(f"Status: {auction.status.value}")
            print(f"Total Items: {auction.total_items}")
            print(f"Available: {auction.available_items}")
            print(f"Canceled: {auction.canceled_items}")
            print(f"Properties scraped: {len(auction.properties)}")
            
            # Show sample properties
            for i, prop in enumerate(auction.properties[:3]):
                print(f"\n  Property {i+1}:")
                print(f"    Tax Deed #: {prop.tax_deed_number}")
                print(f"    Parcel: {prop.parcel_number}")
                print(f"    Address: {prop.situs_address}")
                print(f"    Opening Bid: ${prop.opening_bid:,.2f}")
                print(f"    Status: {prop.status.value}")
                
        # Save to JSON
        scraper.save_to_json(auctions)
        
if __name__ == "__main__":
    asyncio.run(main())