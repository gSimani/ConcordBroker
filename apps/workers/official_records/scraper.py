"""
Broward County Official Records Web Scraper
Scrapes property transfer records from the Clerk's website
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class PropertyTransfer:
    """Represents a property transfer record"""
    recording_date: str
    doc_type: str
    book_page: str
    instrument_number: str
    grantor: str  # Seller
    grantee: str  # Buyer
    consideration: Optional[float]
    legal_description: str
    parcel_id: Optional[str]
    doc_stamps: Optional[float]
    mortgage_amount: Optional[float]
    
class OfficialRecordsScraper:
    """Scrapes Broward County Official Records"""
    
    BASE_URL = "https://officialrecords.broward.org/AcclaimWeb"
    SEARCH_URL = f"{BASE_URL}/search/SearchTypeDocType"
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def initialize(self):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        self.page = await context.new_page()
        
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            
    async def search_transfers(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        doc_types: List[str] = None
    ) -> List[PropertyTransfer]:
        """
        Search for property transfers within date range
        
        Args:
            start_date: Start of search period
            end_date: End of search period (default: today)
            doc_types: Document types to search (default: deeds and mortgages)
        """
        if not end_date:
            end_date = datetime.now()
            
        if not doc_types:
            doc_types = [
                'WARRANTY DEED',
                'QUIT CLAIM DEED',
                'SPECIAL WARRANTY DEED',
                'DEED',
                'MORTGAGE',
                'ASSIGNMENT OF MORTGAGE',
                'SATISFACTION OF MORTGAGE'
            ]
            
        transfers = []
        
        try:
            # Navigate to search page
            await self.page.goto(self.SEARCH_URL, wait_until='networkidle')
            
            # Select document types
            for doc_type in doc_types:
                await self._select_doc_type(doc_type)
                
            # Set date range
            await self._set_date_range(start_date, end_date)
            
            # Submit search
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state('networkidle')
            
            # Process results
            transfers = await self._extract_results()
            
        except Exception as e:
            logger.error(f"Error searching transfers: {e}")
            
        return transfers
        
    async def _select_doc_type(self, doc_type: str):
        """Select a document type in the search form"""
        try:
            # Look for checkbox or select option
            selector = f'input[value="{doc_type}"], option:text("{doc_type}")'
            element = await self.page.query_selector(selector)
            
            if element:
                await element.click()
            else:
                logger.warning(f"Document type not found: {doc_type}")
                
        except Exception as e:
            logger.error(f"Error selecting doc type {doc_type}: {e}")
            
    async def _set_date_range(self, start_date: datetime, end_date: datetime):
        """Set the date range in the search form"""
        try:
            # Format dates as MM/DD/YYYY
            start_str = start_date.strftime('%m/%d/%Y')
            end_str = end_date.strftime('%m/%d/%Y')
            
            # Fill date inputs
            await self.page.fill('input[name="RecordingDateFrom"]', start_str)
            await self.page.fill('input[name="RecordingDateTo"]', end_str)
            
        except Exception as e:
            logger.error(f"Error setting date range: {e}")
            
    async def _extract_results(self) -> List[PropertyTransfer]:
        """Extract transfer records from results page"""
        transfers = []
        
        try:
            # Wait for results table
            await self.page.wait_for_selector('table.results-table', timeout=10000)
            
            # Get all result rows
            rows = await self.page.query_selector_all('table.results-table tr:not(:first-child)')
            
            for row in rows:
                transfer = await self._parse_result_row(row)
                if transfer:
                    transfers.append(transfer)
                    
            # Check for pagination
            next_button = await self.page.query_selector('a.next-page')
            if next_button:
                # Recursively get next page results
                await next_button.click()
                await self.page.wait_for_load_state('networkidle')
                more_transfers = await self._extract_results()
                transfers.extend(more_transfers)
                
        except Exception as e:
            logger.error(f"Error extracting results: {e}")
            
        return transfers
        
    async def _parse_result_row(self, row) -> Optional[PropertyTransfer]:
        """Parse a single result row into PropertyTransfer"""
        try:
            cells = await row.query_selector_all('td')
            if len(cells) < 7:
                return None
                
            # Extract cell text
            recording_date = await cells[0].inner_text()
            doc_type = await cells[1].inner_text()
            book_page = await cells[2].inner_text()
            instrument_num = await cells[3].inner_text()
            grantor = await cells[4].inner_text()
            grantee = await cells[5].inner_text()
            
            # Click for details if available
            detail_link = await cells[0].query_selector('a')
            if detail_link:
                # Open in new tab to get additional details
                details = await self._get_transfer_details(instrument_num)
            else:
                details = {}
                
            return PropertyTransfer(
                recording_date=recording_date.strip(),
                doc_type=doc_type.strip(),
                book_page=book_page.strip(),
                instrument_number=instrument_num.strip(),
                grantor=grantor.strip(),
                grantee=grantee.strip(),
                consideration=details.get('consideration'),
                legal_description=details.get('legal', ''),
                parcel_id=details.get('parcel_id'),
                doc_stamps=details.get('doc_stamps'),
                mortgage_amount=details.get('mortgage_amount')
            )
            
        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            return None
            
    async def _get_transfer_details(self, instrument_number: str) -> Dict[str, Any]:
        """Get additional details for a transfer"""
        details = {}
        
        try:
            # Open detail page in new tab
            detail_url = f"{self.BASE_URL}/Details/GetDetails?id={instrument_number}"
            new_page = await self.browser.new_page()
            await new_page.goto(detail_url, wait_until='networkidle')
            
            # Extract consideration amount
            consideration_elem = await new_page.query_selector('span:text("Consideration:") + span')
            if consideration_elem:
                text = await consideration_elem.inner_text()
                # Parse amount from text like "$500,000.00"
                amount = self._parse_money(text)
                if amount:
                    details['consideration'] = amount
                    
            # Extract parcel ID
            parcel_elem = await new_page.query_selector('span:text("Parcel ID:") + span')
            if parcel_elem:
                details['parcel_id'] = await parcel_elem.inner_text()
                
            # Extract legal description
            legal_elem = await new_page.query_selector('div.legal-description')
            if legal_elem:
                details['legal'] = await legal_elem.inner_text()
                
            # Extract doc stamps (indicates sale price)
            stamps_elem = await new_page.query_selector('span:text("Doc Stamps:") + span')
            if stamps_elem:
                text = await stamps_elem.inner_text()
                amount = self._parse_money(text)
                if amount:
                    details['doc_stamps'] = amount
                    # Estimate sale price from stamps (stamps = $0.70 per $100)
                    details['estimated_price'] = amount / 0.007
                    
            await new_page.close()
            
        except Exception as e:
            logger.error(f"Error getting transfer details: {e}")
            
        return details
        
    def _parse_money(self, text: str) -> Optional[float]:
        """Parse money amount from text"""
        try:
            # Remove $ and commas
            clean = text.replace('$', '').replace(',', '').strip()
            return float(clean)
        except:
            return None
            
    async def get_recent_high_value_transfers(
        self,
        days_back: int = 30,
        min_value: float = 1000000
    ) -> List[PropertyTransfer]:
        """
        Get recent high-value property transfers
        
        Args:
            days_back: Number of days to look back
            min_value: Minimum consideration/mortgage amount
        """
        start_date = datetime.now() - timedelta(days=days_back)
        transfers = await self.search_transfers(start_date)
        
        # Filter by value
        high_value = []
        for transfer in transfers:
            if transfer.consideration and transfer.consideration >= min_value:
                high_value.append(transfer)
            elif transfer.mortgage_amount and transfer.mortgage_amount >= min_value:
                high_value.append(transfer)
                
        return high_value
        
    async def track_entity_activity(
        self,
        entity_names: List[str],
        days_back: int = 365
    ) -> Dict[str, List[PropertyTransfer]]:
        """
        Track property transfers for specific entities
        
        Args:
            entity_names: List of entity names to track
            days_back: Number of days to look back
        """
        start_date = datetime.now() - timedelta(days=days_back)
        transfers = await self.search_transfers(start_date)
        
        # Group by entity
        entity_transfers = {name: [] for name in entity_names}
        
        for transfer in transfers:
            for entity in entity_names:
                # Check if entity is grantor or grantee
                if entity.lower() in transfer.grantor.lower():
                    entity_transfers[entity].append(transfer)
                elif entity.lower() in transfer.grantee.lower():
                    entity_transfers[entity].append(transfer)
                    
        return entity_transfers


async def main():
    """Test the scraper"""
    scraper = OfficialRecordsScraper()
    
    try:
        await scraper.initialize()
        
        # Get transfers from last 7 days
        start_date = datetime.now() - timedelta(days=7)
        transfers = await scraper.search_transfers(start_date)
        
        print(f"Found {len(transfers)} transfers in last 7 days")
        
        # Show first 5
        for transfer in transfers[:5]:
            print(f"\n{transfer.recording_date}: {transfer.doc_type}")
            print(f"  From: {transfer.grantor}")
            print(f"  To: {transfer.grantee}")
            if transfer.consideration:
                print(f"  Amount: ${transfer.consideration:,.2f}")
                
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())