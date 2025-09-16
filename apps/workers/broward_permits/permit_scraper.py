"""
Broward County Building and Trade Permits Scraper
Scrapes permit data from multiple Broward County sources
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import re
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BrowardPermitScraper:
    """Scrapes building and trade permits from Broward County sources"""
    
    # Base URLs for different permit systems
    BCS_BASE_URL = "https://dpepp.broward.org/BCS/"
    ACCELA_BASE_URL = "https://aca-prod.accela.com/hollywood/"
    ENVIROS_BASE_URL = "https://dpep.broward.org/Enviros/"
    SFWMD_BASE_URL = "https://www.sfwmd.gov/"
    
    # Permit types and their descriptions
    PERMIT_TYPES = {
        'building': 'Building permits and inspections',
        'electrical': 'Electrical work permits',
        'plumbing': 'Plumbing permits',
        'mechanical': 'HVAC and mechanical permits',
        'roofing': 'Roofing permits',
        'pool': 'Swimming pool permits',
        'fence': 'Fence installation permits',
        'demolition': 'Demolition permits',
        'fire': 'Fire protection systems',
        'environmental': 'Environmental permits',
        'water': 'Water management permits',
        'right_of_way': 'Right-of-way permits'
    }
    
    def __init__(self, data_dir: str = "data/broward_permits"):
        """
        Initialize the permit scraper
        
        Args:
            data_dir: Directory to store scraped data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.metadata_dir = self.data_dir / "metadata"
        
        for dir_path in [self.raw_dir, self.processed_dir, self.metadata_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Scraping history
        self.history_file = self.metadata_dir / "scraping_history.json"
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load scraping history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return {
            "last_scrape": {},
            "scraped_permits": {},
            "errors": []
        }
    
    def _save_history(self):
        """Save scraping history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def scrape_bcs_permits(self, start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Scrape building permits from BCS (Building Code Services)
        
        Args:
            start_date: Start date for permit search
            end_date: End date for permit search
            
        Returns:
            List of permit records
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        logger.info(f"Scraping BCS permits from {start_date.date()} to {end_date.date()}")
        
        permits = []
        
        try:
            # Navigate to BCS permit search
            search_url = f"{self.BCS_BASE_URL}Default.aspx?PossePresentation=ParcelSearchByAddress"
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search form parameters
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstate_value = viewstate['value'] if viewstate else ''
            
            eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
            eventvalidation_value = eventvalidation['value'] if eventvalidation else ''
            
            # Perform date range search
            search_data = {
                '__VIEWSTATE': viewstate_value,
                '__EVENTVALIDATION': eventvalidation_value,
                'ctl00$ContentPlaceHolder1$txtFromDate': start_date.strftime('%m/%d/%Y'),
                'ctl00$ContentPlaceHolder1$txtToDate': end_date.strftime('%m/%d/%Y'),
                'ctl00$ContentPlaceHolder1$btnSearchByDate': 'Search by Date Range'
            }
            
            response = self.session.post(search_url, data=search_data, timeout=30)
            response.raise_for_status()
            
            # Parse permit results
            soup = BeautifulSoup(response.text, 'html.parser')
            permit_table = soup.find('table', class_='grid')
            
            if permit_table:
                rows = permit_table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 6:
                        permit = {
                            'permit_number': cells[0].get_text(strip=True),
                            'address': cells[1].get_text(strip=True),
                            'permit_type': cells[2].get_text(strip=True),
                            'description': cells[3].get_text(strip=True),
                            'issue_date': cells[4].get_text(strip=True),
                            'status': cells[5].get_text(strip=True),
                            'source': 'BCS',
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Get additional details if available
                        detail_link = cells[0].find('a')
                        if detail_link:
                            permit['detail_url'] = urljoin(self.BCS_BASE_URL, detail_link['href'])
                            
                            # Scrape permit details
                            details = self._scrape_bcs_permit_details(permit['detail_url'])
                            if details:
                                permit.update(details)
                        
                        permits.append(permit)
                        
                        # Rate limiting
                        time.sleep(0.5)
            
            logger.info(f"Scraped {len(permits)} BCS permits")
            
        except Exception as e:
            logger.error(f"Error scraping BCS permits: {e}")
            self.history['errors'].append({
                'source': 'BCS',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return permits
    
    def _scrape_bcs_permit_details(self, detail_url: str) -> Optional[Dict]:
        """Scrape additional details from BCS permit detail page"""
        try:
            response = self.session.get(detail_url, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            details = {}
            
            # Extract contractor information
            contractor_section = soup.find('span', string=re.compile('Contractor', re.I))
            if contractor_section:
                contractor_text = contractor_section.parent.get_text()
                details['contractor'] = contractor_text.strip()
            
            # Extract valuation
            valuation_section = soup.find('span', string=re.compile('Valuation', re.I))
            if valuation_section:
                valuation_text = valuation_section.parent.get_text()
                valuation_match = re.search(r'\$?([\d,]+)', valuation_text)
                if valuation_match:
                    details['valuation'] = valuation_match.group(1).replace(',', '')
            
            # Extract inspection information
            inspection_table = soup.find('table', {'id': re.compile('.*Inspection.*')})
            if inspection_table:
                inspections = []
                for row in inspection_table.find_all('tr')[1:]:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        inspection = {
                            'type': cells[0].get_text(strip=True),
                            'date': cells[1].get_text(strip=True),
                            'status': cells[2].get_text(strip=True)
                        }
                        inspections.append(inspection)
                details['inspections'] = inspections
            
            return details
            
        except Exception as e:
            logger.warning(f"Error scraping BCS permit details from {detail_url}: {e}")
            return None
    
    def scrape_hollywood_permits(self, start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Scrape permits from Hollywood's Accela system
        
        Args:
            start_date: Start date for permit search
            end_date: End date for permit search
            
        Returns:
            List of permit records
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        logger.info(f"Scraping Hollywood Accela permits from {start_date.date()} to {end_date.date()}")
        
        permits = []
        
        try:
            # Navigate to Accela search
            search_url = f"{self.ACCELA_BASE_URL}Cap/CapHome.aspx?module=Building&TabName=Building"
            response = self.session.get(search_url, timeout=30)
            
            # Accela requires complex form interaction
            # This is a simplified approach - full implementation would need
            # to handle ASP.NET ViewState and form submissions
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for permit listings (this varies by Accela configuration)
            permit_links = soup.find_all('a', href=re.compile('CapDetail'))
            
            for link in permit_links[:50]:  # Limit to prevent overwhelming
                try:
                    detail_url = urljoin(self.ACCELA_BASE_URL, link['href'])
                    permit_details = self._scrape_accela_permit_details(detail_url)
                    
                    if permit_details:
                        permit_details['source'] = 'Hollywood_Accela'
                        permit_details['scraped_at'] = datetime.now().isoformat()
                        permits.append(permit_details)
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Error processing Accela permit link: {e}")
                    continue
            
            logger.info(f"Scraped {len(permits)} Hollywood permits")
            
        except Exception as e:
            logger.error(f"Error scraping Hollywood permits: {e}")
            self.history['errors'].append({
                'source': 'Hollywood_Accela',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return permits
    
    def _scrape_accela_permit_details(self, detail_url: str) -> Optional[Dict]:
        """Scrape details from Accela permit detail page"""
        try:
            response = self.session.get(detail_url, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            permit = {}
            
            # Extract permit number
            permit_num = soup.find('span', {'id': re.compile('.*PermitNumber.*')})
            if permit_num:
                permit['permit_number'] = permit_num.get_text(strip=True)
            
            # Extract address
            address_span = soup.find('span', {'id': re.compile('.*Address.*')})
            if address_span:
                permit['address'] = address_span.get_text(strip=True)
            
            # Extract permit type
            type_span = soup.find('span', {'id': re.compile('.*PermitType.*')})
            if type_span:
                permit['permit_type'] = type_span.get_text(strip=True)
            
            # Extract status
            status_span = soup.find('span', {'id': re.compile('.*Status.*')})
            if status_span:
                permit['status'] = status_span.get_text(strip=True)
            
            # Extract dates
            issue_date = soup.find('span', {'id': re.compile('.*IssueDate.*')})
            if issue_date:
                permit['issue_date'] = issue_date.get_text(strip=True)
            
            return permit if permit else None
            
        except Exception as e:
            logger.warning(f"Error scraping Accela permit details from {detail_url}: {e}")
            return None
    
    def scrape_environmental_permits(self, start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None) -> List[Dict]:
        """
        Scrape environmental permits from ENVIROS system
        
        Args:
            start_date: Start date for permit search
            end_date: End date for permit search
            
        Returns:
            List of environmental permit records
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=90)  # Longer period for environmental
        if not end_date:
            end_date = datetime.now()
        
        logger.info(f"Scraping ENVIROS permits from {start_date.date()} to {end_date.date()}")
        
        permits = []
        
        try:
            # Navigate to ENVIROS search
            search_url = f"{self.ENVIROS_BASE_URL}default.aspx?PossePresentation=PermitLicenseSearch"
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Similar to BCS, extract ViewState for form submission
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstate_value = viewstate['value'] if viewstate else ''
            
            # Search for recent permits by date
            search_data = {
                '__VIEWSTATE': viewstate_value,
                'ctl00$ContentPlaceHolder1$txtFromDate': start_date.strftime('%m/%d/%Y'),
                'ctl00$ContentPlaceHolder1$txtToDate': end_date.strftime('%m/%d/%Y'),
                'ctl00$ContentPlaceHolder1$btnSearch': 'Search'
            }
            
            response = self.session.post(search_url, data=search_data, timeout=30)
            response.raise_for_status()
            
            # Parse environmental permit results
            soup = BeautifulSoup(response.text, 'html.parser')
            permit_table = soup.find('table', class_='grid')
            
            if permit_table:
                rows = permit_table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        permit = {
                            'permit_number': cells[0].get_text(strip=True),
                            'facility_name': cells[1].get_text(strip=True),
                            'activity_type': cells[2].get_text(strip=True),
                            'issue_date': cells[3].get_text(strip=True),
                            'status': cells[4].get_text(strip=True),
                            'source': 'ENVIROS',
                            'scraped_at': datetime.now().isoformat()
                        }
                        permits.append(permit)
            
            logger.info(f"Scraped {len(permits)} environmental permits")
            
        except Exception as e:
            logger.error(f"Error scraping environmental permits: {e}")
            self.history['errors'].append({
                'source': 'ENVIROS',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return permits
    
    def scrape_all_permits(self, days_back: int = 30) -> Dict[str, List[Dict]]:
        """
        Scrape permits from all sources
        
        Args:
            days_back: Number of days back to search
            
        Returns:
            Dictionary with permits from all sources
        """
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
        
        logger.info(f"Scraping all permit sources for last {days_back} days")
        
        all_permits = {}
        
        # Scrape BCS permits (unincorporated Broward)
        try:
            bcs_permits = self.scrape_bcs_permits(start_date, end_date)
            all_permits['bcs'] = bcs_permits
            self.history['last_scrape']['bcs'] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Failed to scrape BCS permits: {e}")
            all_permits['bcs'] = []
        
        time.sleep(5)  # Rate limiting between sources
        
        # Scrape Hollywood permits
        try:
            hollywood_permits = self.scrape_hollywood_permits(start_date, end_date)
            all_permits['hollywood'] = hollywood_permits
            self.history['last_scrape']['hollywood'] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Failed to scrape Hollywood permits: {e}")
            all_permits['hollywood'] = []
        
        time.sleep(5)  # Rate limiting between sources
        
        # Scrape environmental permits
        try:
            env_permits = self.scrape_environmental_permits(start_date, end_date)
            all_permits['environmental'] = env_permits
            self.history['last_scrape']['environmental'] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Failed to scrape environmental permits: {e}")
            all_permits['environmental'] = []
        
        # Save results
        self._save_permits(all_permits, start_date, end_date)
        self._save_history()
        
        # Log summary
        total_permits = sum(len(permits) for permits in all_permits.values())
        logger.info(f"Total permits scraped: {total_permits}")
        for source, permits in all_permits.items():
            logger.info(f"  {source}: {len(permits)} permits")
        
        return all_permits
    
    def _save_permits(self, permits_data: Dict, start_date: datetime, end_date: datetime):
        """Save scraped permits to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"permits_{timestamp}.json"
        filepath = self.raw_dir / filename
        
        data = {
            'scrape_info': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'scraped_at': datetime.now().isoformat(),
                'total_permits': sum(len(permits) for permits in permits_data.values())
            },
            'permits': permits_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Saved permits to {filepath}")
    
    def get_scraping_status(self) -> Dict:
        """Get current scraping status"""
        status = {
            'last_scrape_times': self.history.get('last_scrape', {}),
            'total_errors': len(self.history.get('errors', [])),
            'recent_errors': self.history.get('errors', [])[-5:],
            'data_files': []
        }
        
        # List available data files
        for file_path in self.raw_dir.glob("permits_*.json"):
            file_stats = {
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            status['data_files'].append(file_stats)
        
        return status


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Broward County Permit Scraper')
    parser.add_argument('--source', choices=['bcs', 'hollywood', 'environmental', 'all'], 
                       default='all', help='Permit source to scrape')
    parser.add_argument('--days', type=int, default=30, help='Number of days back to search')
    parser.add_argument('--status', action='store_true', help='Show scraping status')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = BrowardPermitScraper()
    
    if args.status:
        # Show status
        status = scraper.get_scraping_status()
        print("\nScraping Status:")
        print(f"  Last scrape times: {status['last_scrape_times']}")
        print(f"  Total errors: {status['total_errors']}")
        print(f"  Data files: {len(status['data_files'])}")
        
    else:
        # Run scraper
        if args.source == 'all':
            permits = scraper.scrape_all_permits(args.days)
        elif args.source == 'bcs':
            start_date = datetime.now() - timedelta(days=args.days)
            permits = scraper.scrape_bcs_permits(start_date)
        elif args.source == 'hollywood':
            start_date = datetime.now() - timedelta(days=args.days)
            permits = scraper.scrape_hollywood_permits(start_date)
        elif args.source == 'environmental':
            start_date = datetime.now() - timedelta(days=args.days)
            permits = scraper.scrape_environmental_permits(start_date)
        
        print(f"Scraping completed. Check data files in: {scraper.data_dir}")