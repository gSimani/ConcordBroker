"""
Entity Matching Service
Matches property owners from Florida Property Appraiser data with Sunbiz business entities
Uses multiple matching strategies including exact, fuzzy, and pattern-based matching
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from fuzzywuzzy import fuzz, process
import pandas as pd
from supabase import create_client, Client
import hashlib
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MatchResult:
    """Represents a match between property owner and business entity"""
    confidence_score: float  # 0-100
    match_type: str  # exact, fuzzy, pattern, address, agent
    property_owner: str
    entity_name: str
    entity_doc_number: str
    entity_type: str  # corporate, fictitious, partnership
    entity_status: str
    additional_info: Dict

class PropertyEntityMatcher:
    """
    Intelligent matching service for linking property owners to business entities
    """
    
    # Common business entity suffixes and their variations
    ENTITY_SUFFIXES = {
        'LLC': ['LLC', 'L.L.C.', 'L L C', 'LIMITED LIABILITY COMPANY', 'LIMITED LIABILITY CO'],
        'INC': ['INC', 'INC.', 'INCORPORATED', 'INCORPORATION'],
        'CORP': ['CORP', 'CORP.', 'CORPORATION'],
        'LP': ['LP', 'L.P.', 'LIMITED PARTNERSHIP', 'LTD PARTNERSHIP'],
        'LLP': ['LLP', 'L.L.P.', 'LIMITED LIABILITY PARTNERSHIP'],
        'PA': ['PA', 'P.A.', 'PROFESSIONAL ASSOCIATION', 'PROF ASSN'],
        'PC': ['PC', 'P.C.', 'PROFESSIONAL CORPORATION', 'PROF CORP'],
        'TRUST': ['TRUST', 'TR', 'REVOCABLE TRUST', 'LIVING TRUST', 'FAMILY TRUST'],
        'ESTATE': ['ESTATE', 'EST', 'ESTATE OF']
    }
    
    # Keywords indicating business entities
    BUSINESS_KEYWORDS = [
        'PROPERTIES', 'PROPERTY', 'HOLDINGS', 'INVESTMENTS', 'INVESTMENT',
        'CAPITAL', 'PARTNERS', 'GROUP', 'ENTERPRISES', 'VENTURES',
        'MANAGEMENT', 'DEVELOPMENT', 'DEVELOPERS', 'BUILDERS', 'CONSTRUCTION',
        'REALTY', 'REAL ESTATE', 'LAND', 'ASSETS', 'ACQUISITION'
    ]
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
        self.entity_cache = {}
        self.match_cache = {}
        self.load_entity_cache()
    
    def load_entity_cache(self):
        """Pre-load business entities for faster matching"""
        try:
            # Load active corporate entities
            corps = self.supabase.table('sunbiz_corporate').select(
                'doc_number,entity_name,status,registered_agent,prin_addr1,prin_city'
            ).eq('status', 'ACTIVE').execute()
            
            for corp in corps.data:
                normalized = self.normalize_name(corp['entity_name'])
                self.entity_cache[normalized] = {
                    'type': 'corporate',
                    'data': corp
                }
            
            # Load fictitious names
            fictitious = self.supabase.table('sunbiz_fictitious').select(
                'doc_number,name,owner_name,county'
            ).execute()
            
            for fic in fictitious.data:
                normalized = self.normalize_name(fic['name'])
                self.entity_cache[normalized] = {
                    'type': 'fictitious',
                    'data': fic
                }
            
            logger.info(f"Loaded {len(self.entity_cache)} entities into cache")
            
        except Exception as e:
            logger.error(f"Error loading entity cache: {e}")
    
    def normalize_name(self, name: str) -> str:
        """Normalize business name for matching"""
        if not name:
            return ""
        
        # Convert to uppercase
        normalized = name.upper().strip()
        
        # Remove common punctuation
        normalized = re.sub(r'[.,\-\'"]', ' ', normalized)
        
        # Standardize spacing
        normalized = ' '.join(normalized.split())
        
        # Expand common abbreviations
        abbreviations = {
            '&': 'AND',
            '@': 'AT',
            '#': 'NUMBER',
            'CO': 'COMPANY',
            'ASSOC': 'ASSOCIATES',
            'MGMT': 'MANAGEMENT',
            'PROP': 'PROPERTY',
            'RE': 'REAL ESTATE'
        }
        
        for abbr, full in abbreviations.items():
            normalized = re.sub(r'\b' + abbr + r'\b', full, normalized)
        
        return normalized
    
    def extract_business_indicators(self, owner_name: str) -> Dict:
        """Extract business entity indicators from owner name"""
        indicators = {
            'has_suffix': False,
            'suffix_type': None,
            'has_keywords': False,
            'keywords_found': [],
            'likely_business': False,
            'clean_name': owner_name
        }
        
        normalized = self.normalize_name(owner_name)
        
        # Check for entity suffixes
        for suffix_type, variations in self.ENTITY_SUFFIXES.items():
            for variant in variations:
                if normalized.endswith(variant) or f' {variant} ' in normalized:
                    indicators['has_suffix'] = True
                    indicators['suffix_type'] = suffix_type
                    # Remove suffix for clean name
                    indicators['clean_name'] = normalized.replace(variant, '').strip()
                    break
        
        # Check for business keywords
        for keyword in self.BUSINESS_KEYWORDS:
            if keyword in normalized:
                indicators['has_keywords'] = True
                indicators['keywords_found'].append(keyword)
        
        # Determine if likely business
        indicators['likely_business'] = (
            indicators['has_suffix'] or 
            indicators['has_keywords'] or
            len(normalized.split()) > 3  # Multi-word names often businesses
        )
        
        return indicators
    
    def match_property_owner(self, property_data: Dict) -> List[MatchResult]:
        """
        Match a property owner to business entities
        Returns list of potential matches with confidence scores
        """
        owner_name = property_data.get('owner_name', '')
        owner_addr = property_data.get('owner_addr1', '')
        
        if not owner_name:
            return []
        
        matches = []
        
        # Extract business indicators
        indicators = self.extract_business_indicators(owner_name)
        
        if not indicators['likely_business']:
            # Check if individual might own through business
            matches.extend(self.find_individual_businesses(owner_name, owner_addr))
        else:
            # Business entity matching strategies
            
            # 1. Exact match
            exact_matches = self.exact_match(owner_name)
            matches.extend(exact_matches)
            
            # 2. Fuzzy match
            if not exact_matches:
                fuzzy_matches = self.fuzzy_match(owner_name, threshold=80)
                matches.extend(fuzzy_matches)
            
            # 3. Pattern-based match (without suffix)
            if indicators['has_suffix']:
                pattern_matches = self.pattern_match(indicators['clean_name'])
                matches.extend(pattern_matches)
            
            # 4. Address-based match
            if owner_addr:
                addr_matches = self.address_match(owner_addr)
                matches.extend(addr_matches)
            
            # 5. Registered agent match
            agent_matches = self.registered_agent_match(owner_name)
            matches.extend(agent_matches)
        
        # Sort by confidence and deduplicate
        matches = self.deduplicate_matches(matches)
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return matches[:10]  # Return top 10 matches
    
    def exact_match(self, owner_name: str) -> List[MatchResult]:
        """Exact name matching"""
        matches = []
        normalized = self.normalize_name(owner_name)
        
        if normalized in self.entity_cache:
            entity = self.entity_cache[normalized]
            matches.append(MatchResult(
                confidence_score=100.0,
                match_type='exact',
                property_owner=owner_name,
                entity_name=entity['data'].get('entity_name') or entity['data'].get('name'),
                entity_doc_number=entity['data']['doc_number'],
                entity_type=entity['type'],
                entity_status=entity['data'].get('status', 'ACTIVE'),
                additional_info={'method': 'exact_name_match'}
            ))
        
        return matches
    
    def fuzzy_match(self, owner_name: str, threshold: int = 80) -> List[MatchResult]:
        """Fuzzy string matching for similar names"""
        matches = []
        normalized = self.normalize_name(owner_name)
        
        # Get all entity names
        entity_names = list(self.entity_cache.keys())
        
        # Find best fuzzy matches
        fuzzy_results = process.extract(normalized, entity_names, scorer=fuzz.token_sort_ratio, limit=5)
        
        for match_name, score in fuzzy_results:
            if score >= threshold:
                entity = self.entity_cache[match_name]
                matches.append(MatchResult(
                    confidence_score=score,
                    match_type='fuzzy',
                    property_owner=owner_name,
                    entity_name=entity['data'].get('entity_name') or entity['data'].get('name'),
                    entity_doc_number=entity['data']['doc_number'],
                    entity_type=entity['type'],
                    entity_status=entity['data'].get('status', 'ACTIVE'),
                    additional_info={'fuzzy_score': score, 'method': 'fuzzy_match'}
                ))
        
        return matches
    
    def pattern_match(self, clean_name: str) -> List[MatchResult]:
        """Match based on name patterns (e.g., without suffixes)"""
        matches = []
        
        # Search for entities starting with the clean name
        for entity_name, entity_data in self.entity_cache.items():
            if entity_name.startswith(clean_name):
                confidence = 85.0  # Base confidence for pattern match
                
                # Adjust confidence based on how much extra text there is
                extra_length = len(entity_name) - len(clean_name)
                if extra_length < 5:
                    confidence = 90.0
                elif extra_length > 20:
                    confidence = 75.0
                
                matches.append(MatchResult(
                    confidence_score=confidence,
                    match_type='pattern',
                    property_owner=clean_name,
                    entity_name=entity_data['data'].get('entity_name') or entity_data['data'].get('name'),
                    entity_doc_number=entity_data['data']['doc_number'],
                    entity_type=entity_data['type'],
                    entity_status=entity_data['data'].get('status', 'ACTIVE'),
                    additional_info={'method': 'pattern_match', 'pattern': 'name_prefix'}
                ))
        
        return matches
    
    def address_match(self, property_address: str) -> List[MatchResult]:
        """Match entities by address"""
        matches = []
        
        try:
            # Search corporate entities by address
            corps = self.supabase.table('sunbiz_corporate').select('*').ilike(
                'prin_addr1', f'%{property_address[:20]}%'
            ).limit(5).execute()
            
            for corp in corps.data:
                matches.append(MatchResult(
                    confidence_score=70.0,  # Lower confidence for address-only match
                    match_type='address',
                    property_owner=property_address,
                    entity_name=corp['entity_name'],
                    entity_doc_number=corp['doc_number'],
                    entity_type='corporate',
                    entity_status=corp['status'],
                    additional_info={'method': 'address_match', 'matched_address': corp['prin_addr1']}
                ))
        except Exception as e:
            logger.error(f"Address match error: {e}")
        
        return matches
    
    def registered_agent_match(self, owner_name: str) -> List[MatchResult]:
        """Match by registered agent name"""
        matches = []
        
        try:
            # Search for entities where owner might be the registered agent
            normalized = self.normalize_name(owner_name)
            
            # Query corporate entities
            corps = self.supabase.table('sunbiz_corporate').select('*').ilike(
                'registered_agent', f'%{normalized[:30]}%'
            ).limit(5).execute()
            
            for corp in corps.data:
                matches.append(MatchResult(
                    confidence_score=60.0,  # Lower confidence for agent match
                    match_type='agent',
                    property_owner=owner_name,
                    entity_name=corp['entity_name'],
                    entity_doc_number=corp['doc_number'],
                    entity_type='corporate',
                    entity_status=corp['status'],
                    additional_info={'method': 'registered_agent', 'agent': corp['registered_agent']}
                ))
        except Exception as e:
            logger.error(f"Agent match error: {e}")
        
        return matches
    
    def find_individual_businesses(self, individual_name: str, address: str = None) -> List[MatchResult]:
        """Find businesses owned by an individual"""
        matches = []
        
        try:
            # Search fictitious names by owner
            normalized = self.normalize_name(individual_name)
            
            fics = self.supabase.table('sunbiz_fictitious').select('*').ilike(
                'owner_name', f'%{normalized}%'
            ).limit(5).execute()
            
            for fic in fics.data:
                confidence = fuzz.token_sort_ratio(normalized, self.normalize_name(fic['owner_name']))
                
                matches.append(MatchResult(
                    confidence_score=confidence,
                    match_type='individual_owner',
                    property_owner=individual_name,
                    entity_name=fic['name'],
                    entity_doc_number=fic['doc_number'],
                    entity_type='fictitious',
                    entity_status='ACTIVE',
                    additional_info={
                        'method': 'individual_business',
                        'owner_name': fic['owner_name'],
                        'county': fic.get('county')
                    }
                ))
        except Exception as e:
            logger.error(f"Individual business search error: {e}")
        
        return matches
    
    def deduplicate_matches(self, matches: List[MatchResult]) -> List[MatchResult]:
        """Remove duplicate matches, keeping highest confidence"""
        seen_entities = {}
        unique_matches = []
        
        for match in matches:
            key = match.entity_doc_number
            if key not in seen_entities or match.confidence_score > seen_entities[key].confidence_score:
                seen_entities[key] = match
        
        return list(seen_entities.values())
    
    def batch_match_properties(self, properties: List[Dict]) -> Dict[str, List[MatchResult]]:
        """Batch process multiple properties"""
        results = {}
        
        for prop in properties:
            parcel_id = prop.get('parcel_id')
            if parcel_id:
                matches = self.match_property_owner(prop)
                if matches:
                    results[parcel_id] = matches
        
        return results
    
    def create_match_record(self, property_data: Dict, match: MatchResult):
        """Store successful match in database for future reference"""
        try:
            record = {
                'parcel_id': property_data.get('parcel_id'),
                'owner_name': property_data.get('owner_name'),
                'entity_doc_number': match.entity_doc_number,
                'entity_name': match.entity_name,
                'entity_type': match.entity_type,
                'confidence_score': match.confidence_score,
                'match_type': match.match_type,
                'match_metadata': json.dumps(match.additional_info),
                'created_at': datetime.now().isoformat()
            }
            
            self.supabase.table('property_entity_matches').insert(record).execute()
            logger.info(f"Stored match: {property_data.get('parcel_id')} -> {match.entity_doc_number}")
            
        except Exception as e:
            logger.error(f"Error storing match record: {e}")
    
    def get_entity_details(self, doc_number: str) -> Dict:
        """Get full entity details for display"""
        try:
            # Try corporate first
            corp = self.supabase.table('sunbiz_corporate').select('*').eq(
                'doc_number', doc_number
            ).single().execute()
            
            if corp.data:
                # Get events
                events = self.supabase.table('sunbiz_corporate_events').select('*').eq(
                    'doc_number', doc_number
                ).order('event_date', desc=True).execute()
                
                return {
                    'entity': corp.data,
                    'events': events.data,
                    'type': 'corporate'
                }
            
            # Try fictitious names
            fic = self.supabase.table('sunbiz_fictitious').select('*').eq(
                'doc_number', doc_number
            ).single().execute()
            
            if fic.data:
                return {
                    'entity': fic.data,
                    'events': [],
                    'type': 'fictitious'
                }
            
        except Exception as e:
            logger.error(f"Error getting entity details: {e}")
        
        return None


class PropertyEntityAnalyzer:
    """Analyze property-entity relationships and patterns"""
    
    def __init__(self, matcher: PropertyEntityMatcher):
        self.matcher = matcher
        self.supabase = matcher.supabase
    
    def analyze_portfolio(self, entity_doc_number: str) -> Dict:
        """Analyze all properties owned by an entity"""
        try:
            # Get entity details
            entity = self.matcher.get_entity_details(entity_doc_number)
            
            if not entity:
                return None
            
            # Find all properties linked to this entity
            matches = self.supabase.table('property_entity_matches').select('*').eq(
                'entity_doc_number', entity_doc_number
            ).execute()
            
            property_ids = [m['parcel_id'] for m in matches.data]
            
            # Get property details
            properties = self.supabase.table('florida_parcels').select('*').in_(
                'parcel_id', property_ids
            ).execute()
            
            # Calculate portfolio metrics
            total_value = sum(p.get('taxable_value', 0) for p in properties.data)
            total_sqft = sum(p.get('total_living_area', 0) for p in properties.data)
            property_count = len(properties.data)
            
            # Group by city
            city_breakdown = {}
            for prop in properties.data:
                city = prop.get('phy_city', 'Unknown')
                if city not in city_breakdown:
                    city_breakdown[city] = {'count': 0, 'value': 0}
                city_breakdown[city]['count'] += 1
                city_breakdown[city]['value'] += prop.get('taxable_value', 0)
            
            return {
                'entity': entity,
                'portfolio': {
                    'property_count': property_count,
                    'total_value': total_value,
                    'total_sqft': total_sqft,
                    'avg_value': total_value / property_count if property_count > 0 else 0,
                    'city_breakdown': city_breakdown,
                    'properties': properties.data[:10]  # First 10 properties
                }
            }
            
        except Exception as e:
            logger.error(f"Portfolio analysis error: {e}")
            return None
    
    def find_related_entities(self, entity_doc_number: str) -> List[Dict]:
        """Find related business entities (same agent, address, etc.)"""
        try:
            entity = self.matcher.get_entity_details(entity_doc_number)
            
            if not entity or entity['type'] != 'corporate':
                return []
            
            corp_data = entity['entity']
            related = []
            
            # Find entities with same registered agent
            if corp_data.get('registered_agent'):
                same_agent = self.supabase.table('sunbiz_corporate').select('*').eq(
                    'registered_agent', corp_data['registered_agent']
                ).neq('doc_number', entity_doc_number).limit(10).execute()
                
                for corp in same_agent.data:
                    related.append({
                        'doc_number': corp['doc_number'],
                        'entity_name': corp['entity_name'],
                        'relationship': 'same_registered_agent',
                        'status': corp['status']
                    })
            
            # Find entities at same address
            if corp_data.get('prin_addr1'):
                same_addr = self.supabase.table('sunbiz_corporate').select('*').eq(
                    'prin_addr1', corp_data['prin_addr1']
                ).neq('doc_number', entity_doc_number).limit(5).execute()
                
                for corp in same_addr.data:
                    related.append({
                        'doc_number': corp['doc_number'],
                        'entity_name': corp['entity_name'],
                        'relationship': 'same_address',
                        'status': corp['status']
                    })
            
            return related
            
        except Exception as e:
            logger.error(f"Related entities search error: {e}")
            return []


# Usage example
if __name__ == "__main__":
    # Initialize matcher
    matcher = PropertyEntityMatcher(
        supabase_url="your-supabase-url",
        supabase_key="your-supabase-key"
    )
    
    # Example property
    property_data = {
        'parcel_id': 'B123456',
        'owner_name': 'CONCORD HOLDINGS LLC',
        'owner_addr1': '123 MAIN ST',
        'phy_city': 'FORT LAUDERDALE'
    }
    
    # Find matches
    matches = matcher.match_property_owner(property_data)
    
    for match in matches:
        print(f"Found: {match.entity_name} ({match.entity_type}) - Confidence: {match.confidence_score}%")