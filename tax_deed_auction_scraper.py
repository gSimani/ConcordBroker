"""
Tax Deed Auction Scraper for Broward County
Scrapes auction data from https://broward.deedauction.net
Includes Opening Bid and Winning Bid extraction for past auctions
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client
import os
from urllib.parse import urljoin, quote

class TaxDeedAuctionScraper:
    def __init__(self):
        self.base_url = "https://broward.deedauction.net"
        self.session = None
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL', 'https://pmmkfrohclzpwpnbtajc.supabase.co')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        if supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            print("Warning: Supabase credentials not found")
            self.supabase = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> str:
        """Fetch a page from the auction website"""
        async with self.session.get(url) as response:
            return await response.text()

    async def get_auction_list(self) -> List[Dict]:
        """Get list of all auctions (upcoming and past)"""
        auctions = []
        
        # Fetch upcoming auctions
        upcoming_url = f"{self.base_url}/auctions"
        html = await self.fetch_page(upcoming_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Parse auction list
        auction_elements = soup.find_all('div', class_='auction-item')
        for elem in auction_elements:
            auction_link = elem.find('a', href=True)
            if auction_link:
                auction_data = {
                    'url': urljoin(self.base_url, auction_link['href']),
                    'date': elem.find('span', class_='auction-date').text.strip() if elem.find('span', class_='auction-date') else '',
                    'status': 'upcoming'
                }
                auctions.append(auction_data)
        
        # Fetch past auctions
        past_url = f"{self.base_url}/past-auctions"
        html = await self.fetch_page(past_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        past_auction_elements = soup.find_all('div', class_='past-auction-item')
        for elem in past_auction_elements:
            auction_link = elem.find('a', href=True)
            if auction_link:
                auction_data = {
                    'url': urljoin(self.base_url, auction_link['href']),
                    'date': elem.find('span', class_='auction-date').text.strip() if elem.find('span', class_='auction-date') else '',
                    'status': 'past'
                }
                auctions.append(auction_data)
        
        return auctions

    async def scrape_auction_properties(self, auction_url: str, auction_status: str = 'upcoming') -> List[Dict]:
        """Scrape all properties from a specific auction"""
        properties = []
        html = await self.fetch_page(auction_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all property cards/rows
        property_elements = soup.find_all(['tr', 'div'], class_=re.compile('property|parcel|auction-item'))
        
        for elem in property_elements:
            property_data = await self.extract_property_data(elem, auction_status)
            if property_data:
                properties.append(property_data)
        
        return properties

    async def extract_property_data(self, element, auction_status: str) -> Optional[Dict]:
        """Extract detailed property data from an element"""
        try:
            property_data = {
                'auction_status': auction_status,
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            # Extract Tax Deed Number
            tax_deed = element.find(text=re.compile(r'TD-\d+'))
            if tax_deed:
                property_data['tax_deed_number'] = tax_deed.strip()
            
            # Extract Parcel Number
            parcel = element.find(text=re.compile(r'\d{2}-\d{2}-\d{2}-\d{4}'))
            if not parcel:
                parcel = element.find(text=re.compile(r'\d{10,}'))
            if parcel:
                property_data['parcel_number'] = re.sub(r'[^\d-]', '', parcel.strip())
            
            # Extract Tax Certificate Number
            cert = element.find(text=re.compile(r'Cert.*?\d+'))
            if cert:
                cert_match = re.search(r'\d+', cert)
                if cert_match:
                    property_data['tax_certificate_number'] = cert_match.group()
            
            # Extract Legal Description
            legal = element.find(text=re.compile(r'(LOT|BLOCK|PLAT|UNIT)'))
            if legal:
                property_data['legal_description'] = legal.strip()
            
            # Extract Situs Address
            address_elem = element.find(['td', 'div', 'span'], class_=re.compile('address|situs'))
            if address_elem:
                property_data['situs_address'] = address_elem.text.strip()
            
            # Extract Homestead Status
            homestead = element.find(text=re.compile(r'homestead', re.IGNORECASE))
            property_data['is_homestead'] = bool(homestead and 'yes' in homestead.lower())
            
            # Extract Assessed Values
            assessed = element.find(text=re.compile(r'\$[\d,]+'))
            if assessed:
                value_text = re.sub(r'[^\d]', '', assessed)
                property_data['assessed_value'] = int(value_text) if value_text else 0
            
            # Extract Applicant Name
            applicant = element.find(['td', 'div'], class_=re.compile('applicant|certificate-holder'))
            if applicant:
                property_data['applicant_name'] = applicant.text.strip()
            
            # Extract Opening Bid
            opening_bid = element.find(text=re.compile(r'opening.*bid.*\$[\d,]+', re.IGNORECASE))
            if not opening_bid:
                opening_bid = element.find(['td', 'div'], class_=re.compile('opening-bid|min-bid'))
            if opening_bid:
                bid_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', str(opening_bid))
                if bid_match:
                    property_data['opening_bid'] = float(bid_match.group(1).replace(',', ''))
            
            # Extract Winning Bid (for past auctions)
            if auction_status == 'past':
                winning_bid = element.find(text=re.compile(r'(winning|sold|final).*bid.*\$[\d,]+', re.IGNORECASE))
                if not winning_bid:
                    winning_bid = element.find(['td', 'div'], class_=re.compile('winning-bid|sold-price|final-bid'))
                if winning_bid:
                    bid_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', str(winning_bid))
                    if bid_match:
                        property_data['winning_bid'] = float(bid_match.group(1).replace(',', ''))
                
                # Extract Winner Name (if available)
                winner = element.find(['td', 'div'], class_=re.compile('winner|buyer|purchaser'))
                if winner:
                    property_data['winner_name'] = winner.text.strip()
            
            # Extract Status
            status = element.find(['td', 'div', 'span'], class_=re.compile('status'))
            if status:
                status_text = status.text.strip().lower()
                if 'cancel' in status_text:
                    property_data['status'] = 'cancelled'
                elif 'sold' in status_text:
                    property_data['status'] = 'sold'
                elif 'active' in status_text or 'available' in status_text:
                    property_data['status'] = 'active'
                else:
                    property_data['status'] = status_text
            
            # Extract Close Time
            close_time = element.find(text=re.compile(r'\d{1,2}:\d{2}\s*(AM|PM)'))
            if close_time:
                property_data['close_time'] = close_time.strip()
            
            # Generate Sunbiz URL if applicant name exists
            if property_data.get('applicant_name'):
                encoded_name = quote(property_data['applicant_name'])
                property_data['sunbiz_url'] = f"https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults?inquiryType=EntityName&searchTerm={encoded_name}"
            
            # Generate Property Appraiser URL if parcel exists
            if property_data.get('parcel_number'):
                clean_parcel = re.sub(r'[^\d]', '', property_data['parcel_number'])
                property_data['property_appraiser_url'] = f"https://web.bcpa.net/bcpaclient/#/Record/RealEstate/{clean_parcel}"
            
            return property_data if property_data.get('parcel_number') else None
            
        except Exception as e:
            print(f"Error extracting property data: {e}")
            return None

    async def save_to_supabase(self, properties: List[Dict]) -> None:
        """Save scraped properties to Supabase database"""
        if not self.supabase:
            print("Supabase client not initialized")
            return
        
        for property_data in properties:
            try:
                # Check if property already exists
                existing = self.supabase.table('tax_deed_properties').select('*').eq(
                    'parcel_number', property_data.get('parcel_number')
                ).execute()
                
                if existing.data:
                    # Update existing record
                    self.supabase.table('tax_deed_properties').update(property_data).eq(
                        'parcel_number', property_data.get('parcel_number')
                    ).execute()
                    print(f"Updated property: {property_data.get('parcel_number')}")
                else:
                    # Insert new record
                    self.supabase.table('tax_deed_properties').insert(property_data).execute()
                    print(f"Inserted property: {property_data.get('parcel_number')}")
                    
            except Exception as e:
                print(f"Error saving property {property_data.get('parcel_number')}: {e}")

    async def scrape_all(self) -> Dict:
        """Main method to scrape all auctions and properties"""
        results = {
            'auctions_scraped': 0,
            'properties_scraped': 0,
            'properties_with_winning_bids': 0,
            'errors': []
        }
        
        try:
            # Get all auctions
            auctions = await self.get_auction_list()
            results['auctions_scraped'] = len(auctions)
            
            all_properties = []
            
            # Scrape each auction
            for auction in auctions:
                try:
                    properties = await self.scrape_auction_properties(
                        auction['url'], 
                        auction['status']
                    )
                    
                    # Add auction date to each property
                    for prop in properties:
                        prop['auction_date'] = auction['date']
                        if prop.get('winning_bid'):
                            results['properties_with_winning_bids'] += 1
                    
                    all_properties.extend(properties)
                    print(f"Scraped {len(properties)} properties from {auction['date']} auction")
                    
                except Exception as e:
                    error_msg = f"Error scraping auction {auction['date']}: {e}"
                    print(error_msg)
                    results['errors'].append(error_msg)
            
            results['properties_scraped'] = len(all_properties)
            
            # Save to Supabase
            if all_properties:
                await self.save_to_supabase(all_properties)
            
            return results
            
        except Exception as e:
            results['errors'].append(f"Fatal error: {e}")
            return results


async def main():
    """Run the scraper"""
    async with TaxDeedAuctionScraper() as scraper:
        results = await scraper.scrape_all()
        
        print("\n=== SCRAPING COMPLETE ===")
        print(f"Auctions scraped: {results['auctions_scraped']}")
        print(f"Properties scraped: {results['properties_scraped']}")
        print(f"Properties with winning bids: {results['properties_with_winning_bids']}")
        
        if results['errors']:
            print("\nErrors encountered:")
            for error in results['errors']:
                print(f"  - {error}")
        
        return results


if __name__ == "__main__":
    asyncio.run(main())