"""
Miami-Dade County Permit Scraper
Scrapes building permits from Miami-Dade County's permit system
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class MiamiDadePermitScraper:
    """Scrapes permits from Miami-Dade County building department"""
    
    def __init__(self):
        self.base_url = "https://www.miamidade.gov"
        self.permit_search_url = f"{self.base_url}/permits/search"
        self.session = None
        self.rate_limit_delay = 2.0  # seconds between requests
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=300)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scrape_permits(self, days_back: int = 7) -> List[Dict]:
        """
        Scrape permits from Miami-Dade County
        
        Args:
            days_back: Number of days to look back for permits
            
        Returns:
            List of permit dictionaries
        """
        logger.info(f"Scraping Miami-Dade permits for last {days_back} days")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        permits = []
        
        try:
            # Miami-Dade has multiple permit search interfaces
            # 1. Building permits
            building_permits = await self._scrape_building_permits(start_date, end_date)
            permits.extend(building_permits)
            
            # 2. Electrical permits  
            electrical_permits = await self._scrape_electrical_permits(start_date, end_date)
            permits.extend(electrical_permits)
            
            # 3. Plumbing permits
            plumbing_permits = await self._scrape_plumbing_permits(start_date, end_date)
            permits.extend(plumbing_permits)
            
            # 4. HVAC permits
            hvac_permits = await self._scrape_hvac_permits(start_date, end_date)
            permits.extend(hvac_permits)
            
            logger.info(f"Found {len(permits)} total permits from Miami-Dade")
            
        except Exception as e:
            logger.error(f"Error scraping Miami-Dade permits: {e}")
        
        return permits
    
    async def _scrape_building_permits(self, start_date, end_date) -> List[Dict]:
        """Scrape building permits specifically"""
        logger.info("Scraping Miami-Dade building permits")
        
        permits = []
        
        # Miami-Dade building permit search
        search_url = f"{self.base_url}/planning/building-permits/search"
        
        try:
            # Get search form
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to access building permit search: {response.status}")
                    return permits
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
            
            # Find search form and submit with date range
            form_data = {
                'start_date': start_date.strftime('%m/%d/%Y'),
                'end_date': end_date.strftime('%m/%d/%Y'),
                'permit_type': 'Building',
                'status': 'All'
            }
            
            # Look for CSRF token or ViewState
            csrf_token = soup.find('input', {'name': '_token'})
            if csrf_token:
                form_data['_token'] = csrf_token.get('value')
            
            # Submit search form
            async with self.session.post(search_url, data=form_data) as response:
                if response.status != 200:
                    logger.error(f"Building permit search failed: {response.status}")
                    return permits
                
                results_html = await response.text()
                results_soup = BeautifulSoup(results_html, 'html.parser')
            
            # Parse permit results from table
            permit_rows = results_soup.find_all('tr', class_='permit-row')
            
            for row in permit_rows:
                try:
                    permit = self._parse_building_permit_row(row)
                    if permit:
                        permits.append(permit)
                except Exception as e:
                    logger.error(f"Error parsing building permit row: {e}")
                    continue
            
            # Handle pagination if present
            next_page = results_soup.find('a', {'class': 'next-page'})
            if next_page and len(permits) < 1000:  # Limit to prevent infinite loops
                # Recursively get next page
                # Implementation would continue here...
                pass
            
            await asyncio.sleep(self.rate_limit_delay)
            
        except Exception as e:
            logger.error(f"Error scraping building permits: {e}")
        
        logger.info(f"Found {len(permits)} building permits")
        return permits
    
    def _parse_building_permit_row(self, row) -> Optional[Dict]:
        """Parse a building permit table row"""
        try:
            cells = row.find_all('td')
            if len(cells) < 8:
                return None
            
            # Extract permit details from table cells
            permit_number = cells[0].get_text(strip=True)
            permit_type = cells[1].get_text(strip=True)
            property_address = cells[2].get_text(strip=True)
            applicant_name = cells[3].get_text(strip=True)
            contractor_name = cells[4].get_text(strip=True)
            issue_date = cells[5].get_text(strip=True)
            status = cells[6].get_text(strip=True)
            valuation_text = cells[7].get_text(strip=True)
            
            # Parse valuation
            valuation = None
            if valuation_text:
                valuation_match = re.search(r'[\d,]+\.?\d*', valuation_text.replace('$', '').replace(',', ''))
                if valuation_match:
                    valuation = float(valuation_match.group())
            
            # Parse issue date
            parsed_date = None
            try:
                parsed_date = datetime.strptime(issue_date, '%m/%d/%Y').date().isoformat()
            except ValueError:
                pass
            
            # Look for permit details link
            details_link = row.find('a', {'class': 'permit-details'})
            source_url = None
            if details_link:
                source_url = f"{self.base_url}{details_link.get('href')}"
            
            permit = {
                'permit_number': permit_number,
                'permit_type': permit_type,
                'description': f"{permit_type} permit",
                'status': status,
                'applicant_name': applicant_name,
                'contractor_name': contractor_name,
                'property_address': property_address,
                'issue_date': parsed_date,
                'valuation': valuation,
                'source_system': 'miami_dade_building',
                'source_url': source_url,
                'scraped_at': datetime.now().isoformat(),
                'raw_data': {
                    'permit_number': permit_number,
                    'permit_type': permit_type,
                    'address': property_address,
                    'applicant': applicant_name,
                    'contractor': contractor_name,
                    'issue_date': issue_date,
                    'status': status,
                    'valuation': valuation_text
                }
            }
            
            return permit
            
        except Exception as e:
            logger.error(f"Error parsing permit row: {e}")
            return None
    
    async def _scrape_electrical_permits(self, start_date, end_date) -> List[Dict]:
        """Scrape electrical permits from Miami-Dade"""
        logger.info("Scraping Miami-Dade electrical permits")
        
        permits = []
        
        # Electrical permit search would be similar but for electrical permits
        # Implementation would follow similar pattern to building permits
        
        try:
            # Electrical permits may have different search endpoint
            electrical_url = f"{self.base_url}/planning/electrical-permits/search"
            
            # Similar search and parsing logic as building permits
            # but tailored for electrical permit data structure
            
            await asyncio.sleep(self.rate_limit_delay)
            
        except Exception as e:
            logger.error(f"Error scraping electrical permits: {e}")
        
        return permits
    
    async def _scrape_plumbing_permits(self, start_date, end_date) -> List[Dict]:
        """Scrape plumbing permits from Miami-Dade"""
        logger.info("Scraping Miami-Dade plumbing permits")
        
        permits = []
        
        try:
            # Plumbing permit search logic
            plumbing_url = f"{self.base_url}/planning/plumbing-permits/search"
            
            # Implementation would be similar to building permits
            
            await asyncio.sleep(self.rate_limit_delay)
            
        except Exception as e:
            logger.error(f"Error scraping plumbing permits: {e}")
        
        return permits
    
    async def _scrape_hvac_permits(self, start_date, end_date) -> List[Dict]:
        """Scrape HVAC permits from Miami-Dade"""
        logger.info("Scraping Miami-Dade HVAC permits")
        
        permits = []
        
        try:
            # HVAC permit search logic
            hvac_url = f"{self.base_url}/planning/hvac-permits/search"
            
            # Implementation would be similar to building permits
            
            await asyncio.sleep(self.rate_limit_delay)
            
        except Exception as e:
            logger.error(f"Error scraping HVAC permits: {e}")
        
        return permits
    
    async def get_permit_details(self, permit_number: str) -> Optional[Dict]:
        """Get detailed information for a specific permit"""
        logger.info(f"Getting details for permit {permit_number}")
        
        try:
            details_url = f"{self.base_url}/permits/details/{permit_number}"
            
            async with self.session.get(details_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to get permit details: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
            
            # Parse detailed permit information
            details = {
                'permit_number': permit_number,
                'detailed_description': None,
                'parcel_id': None,
                'folio_number': None,
                'contractor_license': None,
                'permit_fee': None,
                'inspections': []
            }
            
            # Extract additional details from the permit detail page
            # This would include parsing specific fields like:
            # - Detailed project description
            # - Parcel ID/Folio number
            # - Contractor license numbers
            # - Permit fees
            # - Inspection schedules and results
            
            await asyncio.sleep(self.rate_limit_delay)
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting permit details for {permit_number}: {e}")
            return None

# Example usage and testing
async def test_miami_dade_scraper():
    """Test the Miami-Dade permit scraper"""
    async with MiamiDadePermitScraper() as scraper:
        permits = await scraper.scrape_permits(days_back=3)
        
        print(f"Found {len(permits)} permits")
        
        if permits:
            print("\nSample permit:")
            print(json.dumps(permits[0], indent=2, default=str))
            
            # Test getting details for first permit
            if permits[0]['permit_number']:
                details = await scraper.get_permit_details(permits[0]['permit_number'])
                if details:
                    print("\nSample permit details:")
                    print(json.dumps(details, indent=2, default=str))

if __name__ == "__main__":
    # Test the scraper
    asyncio.run(test_miami_dade_scraper())