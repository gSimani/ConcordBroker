"""
Enhanced Tax Deed Auction Scraper using API endpoints
======================================================
Fetches auction data directly from API endpoints for better reliability
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
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
    applicant_companies: List[str]
    gis_map_url: Optional[str]
    opening_bid: float
    best_bid: Optional[float]
    close_time: Optional[datetime]
    status: PropertyStatus
    raw_data: Optional[Dict] = None
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
    raw_data: Optional[Dict] = None

class TaxDeedAPIScraper:
    """Enhanced scraper using API endpoints"""
    
    BASE_URL = "https://broward.deedauction.net"
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """Initialize the scraper"""
        self.session = session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.BASE_URL}/auctions'
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
            
    async def fetch_upcoming_auctions(self) -> List[Dict]:
        """Fetch upcoming auctions from API"""
        url = f"{self.BASE_URL}/auctions/upcoming"
        
        # DataTables request parameters
        data = {
            'draw': '1',
            'start': '0',
            'length': '100',  # Get up to 100 auctions
            'search[value]': '',
            'search[regex]': 'false',
            'order[0][column]': '0',
            'order[0][dir]': 'asc'
        }
        
        try:
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    json_data = await response.json()
                    return json_data.get('data', [])
                else:
                    logger.error(f"Failed to fetch auctions: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching auctions: {e}")
            return []
            
    async def fetch_auction_properties(self, auction_id: str) -> List[Dict]:
        """Fetch properties for a specific auction"""
        url = f"{self.BASE_URL}/auction/{auction_id}/items"
        
        # DataTables request for auction items
        data = {
            'draw': '1',
            'start': '0',
            'length': '1000',  # Get up to 1000 properties
            'search[value]': '',
            'search[regex]': 'false',
            'order[0][column]': '0',
            'order[0][dir]': 'asc'
        }
        
        try:
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    json_data = await response.json()
                    return json_data.get('data', [])
                else:
                    # Try alternate URL format
                    url = f"{self.BASE_URL}/items/{auction_id}"
                    async with self.session.post(url, data=data) as response2:
                        if response2.status == 200:
                            json_data = await response2.json()
                            return json_data.get('data', [])
                    logger.warning(f"Failed to fetch properties for auction {auction_id}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching properties: {e}")
            return []
            
    async def fetch_property_details(self, auction_id: str, item_id: str) -> Optional[Dict]:
        """Fetch detailed information for a specific property"""
        url = f"{self.BASE_URL}/auction/{auction_id}/{item_id}/details"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    # This might return HTML, so we'll parse it
                    text = await response.text()
                    # For now, return basic info
                    return {'html': text}
                else:
                    return None
        except Exception as e:
            logger.error(f"Error fetching property details: {e}")
            return None
            
    def parse_auction_data(self, raw_auction: Dict) -> Auction:
        """Parse raw auction data into Auction object"""
        # Parse date from batch_closing_start or description
        auction_date = datetime.now(timezone.utc)
        if 'batch_closing_start' in raw_auction:
            try:
                auction_date = datetime.strptime(raw_auction['batch_closing_start'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        elif 'description' in raw_auction:
            # Extract date from description like "9/17/2025 Tax Deed Sale"
            import re
            date_match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})', raw_auction['description'])
            if date_match:
                try:
                    auction_date = datetime.strptime(date_match.group(1), '%m/%d/%Y')
                except:
                    pass
                    
        # Build auction URL
        auction_url = f"{self.BASE_URL}/auction/{raw_auction['id']}"
        if 'batch_closing_end' in raw_auction and isinstance(raw_auction['batch_closing_end'], dict):
            auction_url = f"{self.BASE_URL}{raw_auction['batch_closing_end'].get('href', '')}"
            
        return Auction(
            auction_id=str(raw_auction.get('id', '')),
            description=raw_auction.get('description', ''),
            auction_date=auction_date,
            total_items=int(raw_auction.get('item_count', 0)),
            available_items=int(raw_auction.get('item_count', 0)),
            advertised_items=0,
            canceled_items=0,
            status=AuctionStatus(raw_auction.get('auction_status', 'Upcoming')),
            auction_url=auction_url,
            properties=[],
            last_updated=datetime.now(timezone.utc),
            raw_data=raw_auction
        )
        
    def parse_property_data(self, raw_property: Dict) -> PropertyDetail:
        """Parse raw property data into PropertyDetail object"""
        # Extract companies from applicant field
        applicant = raw_property.get('applicant', '')
        companies = []
        if applicant:
            for line in applicant.split('\n'):
                line = line.strip()
                if line and any(keyword in line.upper() for keyword in ['LLC', 'INC', 'CORP', 'TRUST', 'LP', 'LLP']):
                    companies.append(line)
                    
        # Parse status
        status = PropertyStatus.UPCOMING
        status_str = str(raw_property.get('status', '')).upper()
        if 'CANCEL' in status_str:
            status = PropertyStatus.CANCELED
        elif 'SOLD' in status_str:
            status = PropertyStatus.SOLD
        elif 'ACTIVE' in status_str:
            status = PropertyStatus.ACTIVE
        elif 'REMOVED' in status_str:
            status = PropertyStatus.REMOVED
            
        # Parse close time
        close_time = None
        if 'close_time' in raw_property:
            try:
                close_time = datetime.strptime(raw_property['close_time'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
                
        return PropertyDetail(
            item_id=str(raw_property.get('id', raw_property.get('item_id', ''))),
            tax_deed_number=raw_property.get('tax_deed_number', ''),
            parcel_number=raw_property.get('parcel_number', ''),
            parcel_url=raw_property.get('parcel_url'),
            tax_certificate_number=raw_property.get('tax_certificate_number'),
            legal_description=raw_property.get('legal_description', ''),
            situs_address=raw_property.get('situs_address', raw_property.get('address', '')),
            homestead=raw_property.get('homestead', False),
            assessed_value=self.parse_float(raw_property.get('assessed_value')),
            soh_value=self.parse_float(raw_property.get('soh_value')),
            applicant=applicant,
            applicant_companies=companies,
            gis_map_url=raw_property.get('gis_map_url'),
            opening_bid=self.parse_float(raw_property.get('opening_bid', 0)),
            best_bid=self.parse_float(raw_property.get('best_bid')),
            close_time=close_time,
            status=status,
            raw_data=raw_property,
            extracted_at=datetime.now(timezone.utc)
        )
        
    def parse_float(self, value: Any) -> Optional[float]:
        """Parse a value to float"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove $ and , from string
            value = value.replace('$', '').replace(',', '').strip()
            try:
                return float(value)
            except:
                return None
        return None
        
    async def scrape_all_auctions(self) -> List[Auction]:
        """Main method to scrape all upcoming auctions and their properties"""
        logger.info("Starting API-based auction scraping...")
        
        # Fetch upcoming auctions
        raw_auctions = await self.fetch_upcoming_auctions()
        logger.info(f"Found {len(raw_auctions)} upcoming auctions")
        
        auctions = []
        
        for raw_auction in raw_auctions:
            try:
                # Parse auction data
                auction = self.parse_auction_data(raw_auction)
                logger.info(f"Processing auction {auction.auction_id}: {auction.description}")
                
                # Fetch properties for this auction
                raw_properties = await self.fetch_auction_properties(auction.auction_id)
                logger.info(f"Found {len(raw_properties)} properties for auction {auction.auction_id}")
                
                # Parse properties
                for raw_prop in raw_properties:
                    try:
                        property_detail = self.parse_property_data(raw_prop)
                        auction.properties.append(property_detail)
                    except Exception as e:
                        logger.error(f"Error parsing property: {e}")
                        continue
                        
                auctions.append(auction)
                
                # Add delay between auctions
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing auction: {e}")
                continue
                
        return auctions
        
    def save_to_json(self, auctions: List[Auction], filename: str = 'tax_deed_auctions_api.json'):
        """Save auction data to JSON file"""
        data = []
        for auction in auctions:
            auction_dict = {
                'auction_id': auction.auction_id,
                'description': auction.description,
                'auction_date': auction.auction_date.isoformat() if auction.auction_date else None,
                'total_items': auction.total_items,
                'available_items': auction.available_items,
                'status': auction.status.value,
                'auction_url': auction.auction_url,
                'last_updated': auction.last_updated.isoformat() if auction.last_updated else None,
                'properties': []
            }
            
            for prop in auction.properties:
                prop_dict = asdict(prop)
                # Convert datetime objects
                if prop_dict.get('close_time'):
                    prop_dict['close_time'] = prop_dict['close_time'].isoformat()
                if prop_dict.get('extracted_at'):
                    prop_dict['extracted_at'] = prop_dict['extracted_at'].isoformat()
                # Convert enum
                if prop_dict.get('status'):
                    prop_dict['status'] = prop.status.value
                # Remove raw_data to keep file smaller
                prop_dict.pop('raw_data', None)
                    
                auction_dict['properties'].append(prop_dict)
                
            data.append(auction_dict)
            
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Saved {len(auctions)} auctions to {filename}")
        
async def main():
    """Test the API scraper"""
    async with TaxDeedAPIScraper() as scraper:
        auctions = await scraper.scrape_all_auctions()
        
        # Print summary
        for auction in auctions:
            print(f"\n{'='*60}")
            print(f"Auction: {auction.description}")
            print(f"Date: {auction.auction_date}")
            print(f"Status: {auction.status.value}")
            print(f"Total Items: {auction.total_items}")
            print(f"Properties scraped: {len(auction.properties)}")
            
            # Show sample properties if any
            if auction.properties:
                print("\nSample properties:")
                for i, prop in enumerate(auction.properties[:3]):
                    print(f"\n  Property {i+1}:")
                    print(f"    ID: {prop.item_id}")
                    print(f"    Tax Deed #: {prop.tax_deed_number}")
                    print(f"    Parcel: {prop.parcel_number}")
                    print(f"    Address: {prop.situs_address}")
                    print(f"    Opening Bid: ${prop.opening_bid:,.2f}" if prop.opening_bid else "    Opening Bid: N/A")
                    print(f"    Status: {prop.status.value}")
                    
        # Save to JSON
        if auctions:
            scraper.save_to_json(auctions)
            print(f"\nData saved to tax_deed_auctions_api.json")
        
if __name__ == "__main__":
    asyncio.run(main())