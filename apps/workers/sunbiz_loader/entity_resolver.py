"""
Entity Resolution for Sunbiz Loader
Matches property owners to corporate entities
"""

import logging
from typing import List, Dict, Tuple
import re

from rapidfuzz import fuzz, process
import asyncpg

from .config import settings
from .parser import SunbizParser

logger = logging.getLogger(__name__)


class EntityResolver:
    """Resolve property owners to corporate entities"""
    
    def __init__(self):
        self.parser = SunbizParser()
        self.pool = None
        self.dsn = settings.DATABASE_URL
        self.threshold = settings.ENTITY_MATCH_THRESHOLD
    
    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.dsn)
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def resolve_new_entities(self) -> List[Dict]:
        """Resolve recently added entities to parcels"""
        
        if not self.pool:
            await self.connect()
        
        matches = []
        
        async with self.pool.acquire() as conn:
            # Get recent entities
            entities = await conn.fetch(
                """
                SELECT id, name, document_number 
                FROM entities 
                WHERE created_at > NOW() - INTERVAL '1 day'
                """
            )
            
            for entity in entities:
                # Find matching parcels
                entity_matches = await self._match_entity_to_parcels(
                    conn, 
                    entity['id'], 
                    entity['name']
                )
                matches.extend(entity_matches)
        
        logger.info(f"Created {len(matches)} entity-parcel links")
        return matches
    
    async def resolve_all_entities(self) -> List[Dict]:
        """Resolve all entities to parcels (full refresh)"""
        
        if not self.pool:
            await self.connect()
        
        all_matches = []
        batch_size = 1000
        offset = 0
        
        async with self.pool.acquire() as conn:
            while True:
                # Get batch of entities
                entities = await conn.fetch(
                    """
                    SELECT id, name, document_number 
                    FROM entities 
                    ORDER BY name
                    LIMIT $1 OFFSET $2
                    """,
                    batch_size,
                    offset
                )
                
                if not entities:
                    break
                
                for entity in entities:
                    matches = await self._match_entity_to_parcels(
                        conn,
                        entity['id'],
                        entity['name']
                    )
                    all_matches.extend(matches)
                
                offset += batch_size
                logger.info(f"Processed {offset} entities, found {len(all_matches)} matches")
        
        return all_matches
    
    async def _match_entity_to_parcels(self, conn, entity_id: str, entity_name: str) -> List[Dict]:
        """Match single entity to parcels"""
        
        matches = []
        
        # Normalize entity name
        normalized_entity = self.parser.normalize_entity_name(entity_name)
        
        if not normalized_entity:
            return matches
        
        # Search for similar owner names
        parcels = await conn.fetch(
            """
            SELECT folio, owner_raw 
            FROM parcels 
            WHERE owner_entity_id IS NULL
            AND owner_raw IS NOT NULL
            AND LENGTH(owner_raw) > 3
            """
        )
        
        for parcel in parcels:
            owner = parcel['owner_raw']
            normalized_owner = self.parser.normalize_entity_name(owner)
            
            # Calculate similarity
            if settings.USE_FUZZY_MATCHING:
                similarity = fuzz.token_set_ratio(normalized_entity, normalized_owner) / 100.0
            else:
                # Exact match only
                similarity = 1.0 if normalized_entity == normalized_owner else 0.0
            
            if similarity >= self.threshold:
                # Create link
                try:
                    await conn.execute(
                        """
                        INSERT INTO parcel_entity_links (
                            folio, entity_id, match_method, confidence
                        ) VALUES ($1, $2, $3, $4)
                        ON CONFLICT (folio, entity_id) DO UPDATE
                        SET confidence = EXCLUDED.confidence
                        WHERE parcel_entity_links.confidence < EXCLUDED.confidence
                        """,
                        parcel['folio'],
                        entity_id,
                        'fuzzy' if settings.USE_FUZZY_MATCHING else 'exact',
                        similarity
                    )
                    
                    # Update parcel with entity link
                    await conn.execute(
                        """
                        UPDATE parcels 
                        SET owner_entity_id = $1
                        WHERE folio = $2 AND owner_entity_id IS NULL
                        """,
                        entity_id,
                        parcel['folio']
                    )
                    
                    matches.append({
                        'folio': parcel['folio'],
                        'entity_id': entity_id,
                        'confidence': similarity,
                        'method': 'fuzzy' if settings.USE_FUZZY_MATCHING else 'exact'
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to create link for {parcel['folio']}: {e}")
        
        return matches
    
    async def find_best_matches(self, owner_name: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Find best entity matches for an owner name"""
        
        if not self.pool:
            await self.connect()
        
        normalized_owner = self.parser.normalize_entity_name(owner_name)
        
        async with self.pool.acquire() as conn:
            # Get all entity names
            entities = await conn.fetch(
                "SELECT id, name FROM entities WHERE name IS NOT NULL"
            )
            
            entity_names = {
                e['id']: self.parser.normalize_entity_name(e['name'])
                for e in entities
            }
            
            # Find best matches using rapidfuzz
            matches = process.extract(
                normalized_owner,
                entity_names,
                scorer=fuzz.token_set_ratio,
                limit=limit
            )
            
            # Format results
            results = []
            for match_name, score, entity_id in matches:
                if score >= self.threshold * 100:
                    results.append((entity_id, score / 100.0))
            
            return results
    
    async def resolve_by_address(self) -> List[Dict]:
        """Match entities to parcels by address"""
        
        if not self.pool:
            await self.connect()
        
        matches = []
        
        async with self.pool.acquire() as conn:
            # Get entities with addresses
            entities = await conn.fetch(
                """
                SELECT id, name, principal_addr
                FROM entities
                WHERE principal_addr IS NOT NULL
                """
            )
            
            for entity in entities:
                addr_parts = self._extract_address_parts(entity['principal_addr'])
                
                if addr_parts.get('street'):
                    # Search parcels by address
                    parcels = await conn.fetch(
                        """
                        SELECT folio, situs_addr, mailing_addr
                        FROM parcels
                        WHERE owner_entity_id IS NULL
                        AND (
                            situs_addr ILIKE $1
                            OR mailing_addr ILIKE $1
                        )
                        """,
                        f"%{addr_parts['street']}%"
                    )
                    
                    for parcel in parcels:
                        # Additional validation could go here
                        matches.append({
                            'folio': parcel['folio'],
                            'entity_id': entity['id'],
                            'method': 'address',
                            'confidence': 0.75  # Lower confidence for address match
                        })
        
        return matches
    
    def _extract_address_parts(self, address: str) -> Dict:
        """Extract street, city, state, zip from address"""
        
        if not address:
            return {}
        
        parts = {}
        
        # Try to extract ZIP
        zip_match = re.search(r'\b(\d{5}(-\d{4})?)\b', address)
        if zip_match:
            parts['zip'] = zip_match.group(1)
        
        # Try to extract state
        state_match = re.search(r'\b([A-Z]{2})\b', address)
        if state_match:
            parts['state'] = state_match.group(1)
        
        # Extract street number and name
        street_match = re.search(r'^(\d+\s+[^,]+)', address)
        if street_match:
            parts['street'] = street_match.group(1).strip()
        
        return parts