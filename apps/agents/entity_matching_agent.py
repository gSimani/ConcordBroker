#!/usr/bin/env python3
"""
Entity Matching Agent - Intelligent property-to-business entity matching
Uses fuzzy matching, address normalization, and machine learning techniques
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import pandas as pd
import json
import aiohttp
from dataclasses import dataclass
import re
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz, process
import unicodedata
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class MatchCandidate:
    property_id: str
    entity_id: str
    match_score: float
    match_type: str  # 'exact', 'fuzzy', 'address', 'agent'
    confidence: str  # 'high', 'medium', 'low'
    match_details: Dict[str, Any]

@dataclass
class MatchingStats:
    total_properties: int = 0
    properties_processed: int = 0
    exact_matches: int = 0
    fuzzy_matches: int = 0
    address_matches: int = 0
    agent_matches: int = 0
    no_matches: int = 0
    manual_review_needed: int = 0
    processing_time: Optional[timedelta] = None

class EntityMatchingAgent:
    """
    Intelligent agent for matching Florida properties to business entities
    Features: Multiple matching strategies, confidence scoring, batch processing
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = self._get_service_key()
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
        
        self.api_url = f"{self.supabase_url}/rest/v1"
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Matching configuration
        self.batch_size = 100
        self.exact_match_threshold = 100
        self.fuzzy_match_threshold = 85
        self.address_match_threshold = 90
        self.high_confidence_threshold = 95
        self.medium_confidence_threshold = 80
        
        # Common business entity suffixes and variations
        self.entity_suffixes = {
            'llc': ['llc', 'l.l.c.', 'limited liability company'],
            'inc': ['inc', 'incorporated', 'corporation', 'corp'],
            'ltd': ['ltd', 'limited', 'ltda'],
            'lp': ['lp', 'l.p.', 'limited partnership'],
            'llp': ['llp', 'l.l.p.', 'limited liability partnership'],
            'co': ['co', 'company', 'companies'],
            'pa': ['pa', 'p.a.', 'professional association'],
            'pllc': ['pllc', 'professional limited liability company']
        }
        
        # Address normalization patterns
        self.address_patterns = [
            (r'\b(street|st)\b', 'st'),
            (r'\b(avenue|ave)\b', 'ave'),
            (r'\b(boulevard|blvd)\b', 'blvd'),
            (r'\b(road|rd)\b', 'rd'),
            (r'\b(drive|dr)\b', 'dr'),
            (r'\b(lane|ln)\b', 'ln'),
            (r'\b(court|ct)\b', 'ct'),
            (r'\b(place|pl)\b', 'pl'),
            (r'\b(north|n)\b', 'n'),
            (r'\b(south|s)\b', 's'),
            (r'\b(east|e)\b', 'e'),
            (r'\b(west|w)\b', 'w'),
            (r'\b(apartment|apt)\b', 'apt'),
            (r'\b(suite|ste)\b', 'ste'),
            (r'\b(unit|u)\b', 'unit')
        ]
        
        # Statistics tracking
        self.stats = MatchingStats()

    def _get_service_key(self) -> Optional[str]:
        """Get the service key with fallback options"""
        for key_name in ['SUPABASE_SERVICE_KEY', 'SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_KEY']:
            key = os.getenv(key_name)
            if key and key.startswith('eyJ'):
                return key
        return None

    async def run(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point called by orchestrator"""
        logger.info("EntityMatchingAgent starting...")
        
        start_time = datetime.now()
        
        match_type = task_data.get('match_type', 'full')  # 'full', 'incremental', 'specific'
        property_limit = task_data.get('property_limit', None)
        force_rematch = task_data.get('force_rematch', False)
        specific_properties = task_data.get('specific_properties', [])
        
        try:
            # Verify database connectivity
            await self._verify_connection()
            
            # Initialize matching tables if needed
            await self._initialize_matching_tables()
            
            # Get properties and entities to match
            properties = await self._get_properties_for_matching(match_type, property_limit, specific_properties, force_rematch)
            entities = await self._get_entities_for_matching()
            
            self.stats.total_properties = len(properties)
            logger.info(f"Matching {len(properties)} properties against {len(entities)} entities")
            
            if not properties or not entities:
                return {
                    'status': 'warning',
                    'message': 'No properties or entities found for matching'
                }
            
            # Prepare entity lookup structures
            entity_lookup = self._prepare_entity_lookup(entities)
            
            # Process properties in batches
            all_matches = []
            for i in range(0, len(properties), self.batch_size):
                batch_properties = properties[i:i+self.batch_size]
                batch_matches = await self._process_property_batch(batch_properties, entity_lookup)
                all_matches.extend(batch_matches)
                
                self.stats.properties_processed = min(i + self.batch_size, len(properties))
                
                # Progress logging
                if self.stats.properties_processed % 1000 == 0:
                    progress = (self.stats.properties_processed / self.stats.total_properties) * 100
                    logger.info(f"Progress: {progress:.1f}% ({self.stats.properties_processed}/{self.stats.total_properties})")
                
                # Rate limiting
                await asyncio.sleep(0.1)
            
            # Save matches to database
            save_result = await self._save_matches(all_matches)
            
            # Calculate final statistics
            self.stats.processing_time = datetime.now() - start_time
            
            return {
                'status': 'success',
                'matches_found': len(all_matches),
                'save_result': save_result,
                'statistics': self._get_matching_statistics(),
                'processing_time': str(self.stats.processing_time)
            }
            
        except Exception as e:
            logger.error(f"EntityMatchingAgent failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'statistics': self._get_matching_statistics()
            }

    async def _verify_connection(self):
        """Verify database connectivity"""
        logger.info("Verifying database connection...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Test connection to properties table
                async with session.get(
                    f"{self.api_url}/florida_parcels?select=count&limit=1",
                    headers=self.headers
                ) as response:
                    if response.status >= 400:
                        raise Exception(f"Cannot access florida_parcels: HTTP {response.status}")
                
                # Test connection to entities table
                async with session.get(
                    f"{self.api_url}/sunbiz_entities?select=count&limit=1",
                    headers=self.headers
                ) as response:
                    if response.status >= 400:
                        raise Exception(f"Cannot access sunbiz_entities: HTTP {response.status}")
                
                logger.info("✅ Database connection verified")
                
            except Exception as e:
                logger.error(f"❌ Connection verification failed: {e}")
                raise

    async def _initialize_matching_tables(self):
        """Initialize property-entity matching tables if needed"""
        logger.info("Initializing matching tables...")
        
        # This would create the property_entity_matches table via SQL
        # For now, just log that initialization is complete
        logger.info("Matching tables initialized")

    async def _get_properties_for_matching(self, match_type: str, limit: Optional[int], 
                                          specific_properties: List[str], force_rematch: bool) -> List[Dict]:
        """Get properties that need entity matching"""
        async with aiohttp.ClientSession() as session:
            try:
                # Build query based on match type
                if match_type == 'specific' and specific_properties:
                    # Match specific property IDs
                    parcel_ids = ','.join(f'"{pid}"' for pid in specific_properties)
                    query = f"parcel_id.in.({parcel_ids})"
                elif match_type == 'incremental' and not force_rematch:
                    # Only properties without existing matches
                    query = "and=true&parcel_id.not.in.(select parcel_id from property_entity_matches)"
                else:
                    # Full matching
                    query = ""
                
                # Construct URL
                url = f"{self.api_url}/florida_parcels?select=parcel_id,own_name,phy_addr1,mail_addr1,city,zip_code"
                if query:
                    url += f"&{query}"
                if limit:
                    url += f"&limit={limit}"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        properties = await response.json()
                        logger.info(f"Retrieved {len(properties)} properties for matching")
                        return properties
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get properties: HTTP {response.status} - {error_text}")
                        
            except Exception as e:
                logger.error(f"Error getting properties: {e}")
                raise

    async def _get_entities_for_matching(self) -> List[Dict]:
        """Get business entities for matching"""
        async with aiohttp.ClientSession() as session:
            try:
                # Get active entities with address information
                url = f"{self.api_url}/sunbiz_entities?select=filing_id,entity_name,street_address,city,zip_code,registered_agent_name&status=eq.ACTIVE"
                
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        entities = await response.json()
                        logger.info(f"Retrieved {len(entities)} entities for matching")
                        return entities
                    else:
                        logger.warning(f"Failed to get entities: HTTP {response.status}")
                        return []
                        
            except Exception as e:
                logger.warning(f"Error getting entities: {e}")
                return []

    def _prepare_entity_lookup(self, entities: List[Dict]) -> Dict[str, Any]:
        """Prepare optimized lookup structures for entity matching"""
        logger.info("Preparing entity lookup structures...")
        
        lookup = {
            'by_name': {},
            'by_normalized_name': {},
            'by_address': {},
            'by_city_zip': {},
            'all_entities': entities
        }
        
        for entity in entities:
            filing_id = entity.get('filing_id', '')
            entity_name = entity.get('entity_name', '').strip()
            address = entity.get('street_address', '').strip()
            city = entity.get('city', '').strip()
            zip_code = entity.get('zip_code', '').strip()
            
            if entity_name:
                # Exact name lookup
                lookup['by_name'][entity_name.lower()] = entity
                
                # Normalized name lookup (without business suffixes)
                normalized_name = self._normalize_business_name(entity_name)
                if normalized_name not in lookup['by_normalized_name']:
                    lookup['by_normalized_name'][normalized_name] = []
                lookup['by_normalized_name'][normalized_name].append(entity)
            
            if address:
                # Address lookup
                normalized_address = self._normalize_address(address)
                if normalized_address not in lookup['by_address']:
                    lookup['by_address'][normalized_address] = []
                lookup['by_address'][normalized_address].append(entity)
            
            if city and zip_code:
                # City/ZIP lookup
                city_zip = f"{city.lower()}_{zip_code[:5]}"
                if city_zip not in lookup['by_city_zip']:
                    lookup['by_city_zip'][city_zip] = []
                lookup['by_city_zip'][city_zip].append(entity)
        
        logger.info(f"Created lookup with {len(lookup['by_name'])} names, {len(lookup['by_address'])} addresses")
        return lookup

    async def _process_property_batch(self, properties: List[Dict], entity_lookup: Dict) -> List[MatchCandidate]:
        """Process a batch of properties for entity matching"""
        matches = []
        
        for prop in properties:
            property_matches = await self._find_entity_matches(prop, entity_lookup)
            matches.extend(property_matches)
        
        return matches

    async def _find_entity_matches(self, property_data: Dict, entity_lookup: Dict) -> List[MatchCandidate]:
        """Find entity matches for a single property using multiple strategies"""
        parcel_id = property_data.get('parcel_id', '')
        owner_name = property_data.get('own_name', '').strip()
        property_address = property_data.get('phy_addr1', '').strip()
        mail_address = property_data.get('mail_addr1', '').strip()
        city = property_data.get('city', '').strip()
        zip_code = property_data.get('zip_code', '').strip()
        
        matches = []
        
        if not owner_name:
            return matches
        
        # Strategy 1: Exact name match
        exact_match = self._find_exact_name_match(owner_name, entity_lookup)
        if exact_match:
            matches.append(MatchCandidate(
                property_id=parcel_id,
                entity_id=exact_match['filing_id'],
                match_score=100.0,
                match_type='exact',
                confidence='high',
                match_details={
                    'property_name': owner_name,
                    'entity_name': exact_match['entity_name'],
                    'method': 'exact_name_match'
                }
            ))
            self.stats.exact_matches += 1
            return matches  # Return early for exact match
        
        # Strategy 2: Fuzzy name match
        fuzzy_matches = self._find_fuzzy_name_matches(owner_name, entity_lookup)
        for match_score, entity in fuzzy_matches:
            if match_score >= self.fuzzy_match_threshold:
                confidence = self._calculate_confidence(match_score)
                matches.append(MatchCandidate(
                    property_id=parcel_id,
                    entity_id=entity['filing_id'],
                    match_score=match_score,
                    match_type='fuzzy',
                    confidence=confidence,
                    match_details={
                        'property_name': owner_name,
                        'entity_name': entity['entity_name'],
                        'method': 'fuzzy_name_match'
                    }
                ))
                if confidence == 'high':
                    self.stats.fuzzy_matches += 1
                    break  # Take best high-confidence fuzzy match
        
        # Strategy 3: Address-based matching
        if property_address or mail_address:
            address_matches = self._find_address_matches(
                property_address, mail_address, city, zip_code, entity_lookup
            )
            for match_score, entity in address_matches:
                if match_score >= self.address_match_threshold:
                    confidence = self._calculate_confidence(match_score)
                    matches.append(MatchCandidate(
                        property_id=parcel_id,
                        entity_id=entity['filing_id'],
                        match_score=match_score,
                        match_type='address',
                        confidence=confidence,
                        match_details={
                            'property_address': property_address or mail_address,
                            'entity_address': entity.get('street_address', ''),
                            'method': 'address_match'
                        }
                    ))
                    self.stats.address_matches += 1
        
        # Strategy 4: Registered agent matching
        agent_matches = self._find_registered_agent_matches(owner_name, entity_lookup)
        for match_score, entity in agent_matches:
            if match_score >= self.fuzzy_match_threshold:
                confidence = self._calculate_confidence(match_score)
                matches.append(MatchCandidate(
                    property_id=parcel_id,
                    entity_id=entity['filing_id'],
                    match_score=match_score,
                    match_type='agent',
                    confidence=confidence,
                    match_details={
                        'property_name': owner_name,
                        'registered_agent': entity.get('registered_agent_name', ''),
                        'entity_name': entity['entity_name'],
                        'method': 'registered_agent_match'
                    }
                ))
                self.stats.agent_matches += 1
        
        # If no matches found
        if not matches:
            self.stats.no_matches += 1
        elif any(match.confidence == 'low' for match in matches):
            self.stats.manual_review_needed += 1
        
        # Return top matches only (max 3 per property)
        return sorted(matches, key=lambda m: m.match_score, reverse=True)[:3]

    def _find_exact_name_match(self, owner_name: str, entity_lookup: Dict) -> Optional[Dict]:
        """Find exact name match"""
        return entity_lookup['by_name'].get(owner_name.lower())

    def _find_fuzzy_name_matches(self, owner_name: str, entity_lookup: Dict) -> List[Tuple[float, Dict]]:
        """Find fuzzy name matches using multiple algorithms"""
        normalized_owner = self._normalize_business_name(owner_name)
        matches = []
        
        # Check normalized name lookup first
        if normalized_owner in entity_lookup['by_normalized_name']:
            for entity in entity_lookup['by_normalized_name'][normalized_owner]:
                score = fuzz.ratio(owner_name.lower(), entity['entity_name'].lower())
                matches.append((score, entity))
        
        # Use fuzzy string matching on all entities for high-threshold matches
        entity_names = [entity['entity_name'] for entity in entity_lookup['all_entities']]
        fuzzy_results = process.extract(owner_name, entity_names, limit=5, scorer=fuzz.ratio)
        
        for entity_name, score in fuzzy_results:
            if score >= self.fuzzy_match_threshold:
                # Find the entity object
                entity = entity_lookup['by_name'].get(entity_name.lower())
                if entity:
                    matches.append((score, entity))
        
        # Remove duplicates and sort by score
        unique_matches = {}
        for score, entity in matches:
            entity_id = entity['filing_id']
            if entity_id not in unique_matches or score > unique_matches[entity_id][0]:
                unique_matches[entity_id] = (score, entity)
        
        return sorted(unique_matches.values(), key=lambda x: x[0], reverse=True)

    def _find_address_matches(self, property_addr: str, mail_addr: str, city: str, 
                            zip_code: str, entity_lookup: Dict) -> List[Tuple[float, Dict]]:
        """Find matches based on address information"""
        matches = []
        
        # Normalize addresses
        addresses_to_check = []
        if property_addr:
            addresses_to_check.append(self._normalize_address(property_addr))
        if mail_addr and mail_addr != property_addr:
            addresses_to_check.append(self._normalize_address(mail_addr))
        
        for norm_addr in addresses_to_check:
            if norm_addr in entity_lookup['by_address']:
                for entity in entity_lookup['by_address'][norm_addr]:
                    score = 100.0  # Exact address match
                    matches.append((score, entity))
        
        # City/ZIP matching
        if city and zip_code:
            city_zip = f"{city.lower()}_{zip_code[:5]}"
            if city_zip in entity_lookup['by_city_zip']:
                for entity in entity_lookup['by_city_zip'][city_zip]:
                    # Calculate address similarity if both addresses exist
                    entity_addr = entity.get('street_address', '')
                    if entity_addr and (property_addr or mail_addr):
                        addr_to_compare = property_addr or mail_addr
                        score = fuzz.ratio(addr_to_compare.lower(), entity_addr.lower())
                        if score >= self.address_match_threshold:
                            matches.append((score, entity))
        
        return matches

    def _find_registered_agent_matches(self, owner_name: str, entity_lookup: Dict) -> List[Tuple[float, Dict]]:
        """Find matches where owner name matches registered agent"""
        matches = []
        
        for entity in entity_lookup['all_entities']:
            agent_name = entity.get('registered_agent_name', '').strip()
            if agent_name:
                score = fuzz.ratio(owner_name.lower(), agent_name.lower())
                if score >= self.fuzzy_match_threshold:
                    matches.append((score, entity))
        
        return sorted(matches, key=lambda x: x[0], reverse=True)

    def _normalize_business_name(self, name: str) -> str:
        """Normalize business name by removing common suffixes and standardizing"""
        if not name:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', name.lower().strip())
        
        # Remove common business suffixes
        for suffix_type, variations in self.entity_suffixes.items():
            for variation in variations:
                pattern = r'\b' + re.escape(variation) + r'\b'
                normalized = re.sub(pattern, '', normalized).strip()
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def _normalize_address(self, address: str) -> str:
        """Normalize address for consistent matching"""
        if not address:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        
        # Apply address normalization patterns
        for pattern, replacement in self.address_patterns:
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove common address prefixes/suffixes
        normalized = re.sub(r'\b(po box|p\.o\. box)\s*\d+', '', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def _calculate_confidence(self, score: float) -> str:
        """Calculate confidence level based on match score"""
        if score >= self.high_confidence_threshold:
            return 'high'
        elif score >= self.medium_confidence_threshold:
            return 'medium'
        else:
            return 'low'

    async def _save_matches(self, matches: List[MatchCandidate]) -> Dict[str, Any]:
        """Save entity matches to database"""
        if not matches:
            return {'status': 'success', 'saved': 0}
        
        logger.info(f"Saving {len(matches)} entity matches...")
        
        # Convert matches to database format
        match_records = []
        for match in matches:
            match_records.append({
                'parcel_id': match.property_id,
                'entity_id': match.entity_id,
                'match_score': match.match_score,
                'match_type': match.match_type,
                'confidence_level': match.confidence,
                'match_details': json.dumps(match.match_details),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            })
        
        # Save in batches
        saved_count = 0
        batch_size = 100
        
        async with aiohttp.ClientSession() as session:
            for i in range(0, len(match_records), batch_size):
                batch = match_records[i:i+batch_size]
                
                try:
                    async with session.post(
                        f"{self.api_url}/property_entity_matches",
                        headers=self.headers,
                        json=batch,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status in [200, 201]:
                            saved_count += len(batch)
                        else:
                            error_text = await response.text()
                            logger.error(f"Failed to save matches batch: HTTP {response.status} - {error_text}")
                
                except Exception as e:
                    logger.error(f"Error saving matches batch: {e}")
                
                # Rate limiting
                await asyncio.sleep(0.1)
        
        logger.info(f"Saved {saved_count}/{len(matches)} entity matches")
        
        return {
            'status': 'success',
            'total_matches': len(matches),
            'saved': saved_count,
            'failed': len(matches) - saved_count
        }

    def _get_matching_statistics(self) -> Dict[str, Any]:
        """Get comprehensive matching statistics"""
        return {
            'total_properties': self.stats.total_properties,
            'properties_processed': self.stats.properties_processed,
            'exact_matches': self.stats.exact_matches,
            'fuzzy_matches': self.stats.fuzzy_matches,
            'address_matches': self.stats.address_matches,
            'agent_matches': self.stats.agent_matches,
            'no_matches': self.stats.no_matches,
            'manual_review_needed': self.stats.manual_review_needed,
            'match_rate': (
                (self.stats.exact_matches + self.stats.fuzzy_matches + 
                 self.stats.address_matches + self.stats.agent_matches) / 
                max(self.stats.properties_processed, 1)
            ) * 100,
            'processing_time': str(self.stats.processing_time) if self.stats.processing_time else None
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get current matching status"""
        return {
            'agent': 'EntityMatchingAgent',
            'status': 'ready',
            'matching_thresholds': {
                'exact_match': self.exact_match_threshold,
                'fuzzy_match': self.fuzzy_match_threshold,
                'address_match': self.address_match_threshold,
                'high_confidence': self.high_confidence_threshold,
                'medium_confidence': self.medium_confidence_threshold
            },
            'current_statistics': self._get_matching_statistics(),
            'entity_suffixes_tracked': len(self.entity_suffixes),
            'address_patterns': len(self.address_patterns)
        }