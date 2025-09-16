"""
Live Sunbiz Agent Service
Automatically searches Sunbiz for entities matching property owners
"""

import requests
import re
from typing import Dict, List, Optional
from urllib.parse import quote_plus
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class SunbizEntity:
    entity_name: str
    document_number: str
    entity_type: str
    status: str
    filing_date: str
    principal_address: str = ""
    registered_agent: str = ""
    officers: List[Dict] = None
    
    def __post_init__(self):
        if self.officers is None:
            self.officers = []

class SunbizLiveAgent:
    def __init__(self):
        self.base_url = "https://search.sunbiz.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def clean_owner_name_for_search(self, owner_name: str) -> List[str]:
        """
        Clean property owner name and generate search variations
        Returns list of search terms to try
        """
        if not owner_name:
            return []
        
        # Remove common non-entity suffixes
        cleaned = re.sub(r'\s+(&|AND)\s+[A-Z\s]+$', '', owner_name)  # Remove "& SPOUSE" etc
        cleaned = re.sub(r'\s*,\s*[A-Z\s]*$', '', cleaned)  # Remove trailing comma names
        
        search_terms = []
        
        # If it looks like a business entity
        if any(term in owner_name.upper() for term in ['LLC', 'INC', 'CORP', 'LP', 'LLP', 'CO', 'COMPANY', 'ASSOCIATES', 'GROUP', 'PARTNERS', 'HOLDINGS', 'INVESTMENTS', 'MANAGEMENT', 'PROPERTIES', 'REALTY', 'TRUST']):
            # Add the full cleaned name
            search_terms.append(cleaned.strip())
            
            # Add variations without common suffixes
            for suffix in [' LLC', ' INC', ' CORP', ' CO', ' LP', ' LLP']:
                if suffix in cleaned.upper():
                    search_terms.append(cleaned.upper().replace(suffix, '').strip())
            
            # Extract main business name (before commas)
            main_name = cleaned.split(',')[0].strip()
            if main_name != cleaned:
                search_terms.append(main_name)
        
        return list(set(search_terms))  # Remove duplicates
    
    def search_sunbiz_entity(self, search_term: str) -> List[SunbizEntity]:
        """
        Search Sunbiz for entities matching the search term
        """
        try:
            # URL encode the search term
            encoded_term = quote_plus(search_term)
            
            # Sunbiz entity name search URL
            search_url = f"{self.base_url}/Inquiry/CorporationSearch/ByName"
            
            # Search parameters
            params = {
                'SearchTerm': search_term,
                'SearchType': 'EntityName'
            }
            
            print(f"Searching Sunbiz for: {search_term}")
            
            # Make the search request
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse results
            entities = self._parse_search_results(response.text, search_term)
            
            return entities
            
        except requests.RequestException as e:
            print(f"Error searching Sunbiz for '{search_term}': {e}")
            return []
        except Exception as e:
            print(f"Unexpected error searching Sunbiz: {e}")
            return []
    
    def _parse_search_results(self, html: str, search_term: str) -> List[SunbizEntity]:
        """
        Parse Sunbiz search results HTML
        """
        entities = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for result rows in the table
            result_rows = soup.find_all('tr', class_=['detailRow', 'alternateRow'])
            
            for row in result_rows:
                try:
                    # Extract entity information from the row
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        entity_name = cells[0].get_text(strip=True)
                        document_number = cells[1].get_text(strip=True)
                        entity_type = cells[2].get_text(strip=True)
                        status = cells[3].get_text(strip=True)
                        filing_date = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                        
                        # Check if this entity matches our search
                        if self._is_relevant_match(entity_name, search_term):
                            entity = SunbizEntity(
                                entity_name=entity_name,
                                document_number=document_number,
                                entity_type=entity_type,
                                status=status,
                                filing_date=filing_date
                            )
                            entities.append(entity)
                            
                except Exception as e:
                    print(f"Error parsing entity row: {e}")
                    continue
            
        except Exception as e:
            print(f"Error parsing search results: {e}")
        
        return entities
    
    def _is_relevant_match(self, entity_name: str, search_term: str) -> bool:
        """
        Check if the Sunbiz entity is a relevant match for our search term
        """
        entity_upper = entity_name.upper()
        search_upper = search_term.upper()
        
        # Exact match
        if entity_upper == search_upper:
            return True
        
        # Contains the search term
        if search_upper in entity_upper:
            return True
        
        # Search term contains the entity name
        if entity_upper in search_upper:
            return True
        
        # Word-based matching
        entity_words = set(entity_upper.split())
        search_words = set(search_upper.split())
        
        # If most words match
        if len(entity_words & search_words) >= min(len(entity_words), len(search_words)) * 0.7:
            return True
        
        return False
    
    def get_entity_details(self, document_number: str) -> Optional[Dict]:
        """
        Get detailed information for a specific entity by document number
        """
        try:
            detail_url = f"{self.base_url}/Inquiry/CorporationSearch/SearchResultDetail"
            params = {
                'inquirytype': 'EntityName',
                'directionType': 'Initial',
                'searchNameOrder': document_number,
                'aggregateId': '',  # This would need to be extracted from search results
                'searchTerm': '',
                'listNameOrder': document_number
            }
            
            response = self.session.get(detail_url, params=params, timeout=10)
            response.raise_for_status()
            
            # Parse detailed entity information
            return self._parse_entity_details(response.text)
            
        except Exception as e:
            print(f"Error getting entity details for {document_number}: {e}")
            return None
    
    def _parse_entity_details(self, html: str) -> Dict:
        """
        Parse detailed entity information from Sunbiz detail page
        """
        details = {}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract various fields from the detail page
            # This would need to be customized based on the actual HTML structure
            
            # Look for principal address
            address_section = soup.find('span', string=re.compile(r'Principal Address', re.I))
            if address_section:
                address_text = address_section.find_next('span')
                if address_text:
                    details['principal_address'] = address_text.get_text(strip=True)
            
            # Look for registered agent
            agent_section = soup.find('span', string=re.compile(r'Registered Agent', re.I))
            if agent_section:
                agent_text = agent_section.find_next('span')
                if agent_text:
                    details['registered_agent'] = agent_text.get_text(strip=True)
            
            # Extract officers/directors
            officers_section = soup.find('table', class_='detailSection')
            if officers_section:
                officers = []
                officer_rows = officers_section.find_all('tr')[1:]  # Skip header
                for row in officer_rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        officers.append({
                            'name': cells[0].get_text(strip=True),
                            'title': cells[1].get_text(strip=True),
                            'address': cells[2].get_text(strip=True)
                        })
                details['officers'] = officers
            
        except Exception as e:
            print(f"Error parsing entity details: {e}")
        
        return details
    
    def find_entities_for_property_owner(self, owner_name: str) -> List[Dict]:
        """
        Main method: Find Sunbiz entities for a property owner
        """
        if not owner_name:
            return []
        
        # Get search terms
        search_terms = self.clean_owner_name_for_search(owner_name)
        
        if not search_terms:
            return []
        
        all_entities = []
        
        for search_term in search_terms:
            # Rate limiting - be respectful to Sunbiz
            time.sleep(1)
            
            entities = self.search_sunbiz_entity(search_term)
            
            for entity in entities:
                # Get detailed information if available
                details = self.get_entity_details(entity.document_number)
                
                entity_dict = {
                    'entity_name': entity.entity_name,
                    'document_number': entity.document_number,
                    'entity_type': entity.entity_type,
                    'status': entity.status,
                    'filing_date': entity.filing_date,
                    'search_term_used': search_term,
                    'match_confidence': self._calculate_match_confidence(owner_name, entity.entity_name)
                }
                
                if details:
                    entity_dict.update(details)
                
                all_entities.append(entity_dict)
        
        # Sort by match confidence
        all_entities.sort(key=lambda x: x['match_confidence'], reverse=True)
        
        return all_entities
    
    def _calculate_match_confidence(self, owner_name: str, entity_name: str) -> float:
        """
        Calculate how confident we are that this entity matches the property owner
        """
        owner_upper = owner_name.upper()
        entity_upper = entity_name.upper()
        
        # Exact match
        if owner_upper == entity_upper:
            return 1.0
        
        # Calculate word overlap
        owner_words = set(owner_upper.split())
        entity_words = set(entity_upper.split())
        
        if len(owner_words) == 0:
            return 0.0
        
        overlap = len(owner_words & entity_words)
        confidence = overlap / len(owner_words)
        
        return min(confidence, 0.95)  # Cap at 95% for non-exact matches

# Example usage
if __name__ == "__main__":
    agent = SunbizLiveAgent()
    
    # Test with a property owner name
    test_owner = "IH3 PROPERTY GP"
    print(f"Searching for entities matching: {test_owner}")
    
    entities = agent.find_entities_for_property_owner(test_owner)
    
    print(f"\nFound {len(entities)} entities:")
    for entity in entities:
        print(f"- {entity['entity_name']} ({entity['document_number']}) - {entity['match_confidence']:.2f} confidence")