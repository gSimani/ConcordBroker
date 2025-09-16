#!/usr/bin/env python3
"""
Sunbiz Property Matcher
Matches Sunbiz corporate and officer data to property records
Uses fuzzy matching algorithms for name and address matching
"""

import os
import sys
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
from fuzzywuzzy import fuzz, process
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_property_matcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PropertyRecord:
    """Property record for matching"""
    parcel_id: str
    owner_name: str
    owner_address: str
    owner_city: str
    owner_state: str
    owner_zip: str

@dataclass
class SunbizMatch:
    """Sunbiz match result"""
    entity_id: str
    officer_id: Optional[int]
    entity_name: str
    officer_name: Optional[str]
    officer_role: Optional[str]
    match_type: str
    confidence_score: float
    match_details: Dict

class SunbizPropertyMatcher:
    """Main class for matching Sunbiz data to properties"""
    
    def __init__(self, connection_params: Dict = None):
        """Initialize the matcher with database connection"""
        self.connection_params = connection_params or self._get_default_connection()
        self.conn = None
        self.stats = {
            'properties_processed': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'address_matches': 0,
            'no_matches': 0,
            'total_matches_created': 0
        }
        
        # Matching thresholds
        self.name_exact_threshold = 95
        self.name_fuzzy_threshold = 80
        self.address_threshold = 85
        self.combined_threshold = 75
        
    def _get_default_connection(self) -> Dict:
        """Get default database connection parameters"""
        return {
            'host': os.getenv('SUPABASE_DB_HOST'),
            'database': os.getenv('SUPABASE_DB_NAME'),
            'user': os.getenv('SUPABASE_DB_USER'),
            'password': os.getenv('SUPABASE_DB_PASSWORD'),
            'port': int(os.getenv('SUPABASE_DB_PORT', 5432))
        }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def normalize_name(self, name: str) -> str:
        """Normalize name for matching"""
        if not name:
            return ""
        
        # Convert to uppercase
        name = name.upper().strip()
        
        # Remove common business suffixes and prefixes
        business_suffixes = [
            'INC', 'INCORPORATED', 'LLC', 'CORP', 'CORPORATION', 
            'LP', 'LLP', 'PARTNERSHIP', 'CO', 'COMPANY',
            'TRUST', 'TRUSTEE', 'ESTATE'
        ]
        
        # Remove suffixes
        for suffix in business_suffixes:
            if name.endswith(' ' + suffix):
                name = name[:-len(suffix)-1].strip()
            if name.endswith(',' + suffix):
                name = name[:-len(suffix)-1].strip()
        
        # Remove common punctuation and extra spaces
        name = re.sub(r'[,\.&]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def normalize_address(self, address: str) -> str:
        """Normalize address for matching"""
        if not address:
            return ""
        
        address = address.upper().strip()
        
        # Replace common abbreviations
        replacements = {
            ' ST ': ' STREET ',
            ' AVE ': ' AVENUE ',
            ' BLVD ': ' BOULEVARD ',
            ' RD ': ' ROAD ',
            ' DR ': ' DRIVE ',
            ' CT ': ' COURT ',
            ' LN ': ' LANE ',
            ' PL ': ' PLACE ',
            ' CIR ': ' CIRCLE ',
            ' WAY ': ' WAY ',
            ' PKWY ': ' PARKWAY '
        }
        
        for abbr, full in replacements.items():
            address = address.replace(abbr, full)
        
        # Remove extra spaces
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address
    
    def get_properties_batch(self, cursor, offset: int, limit: int) -> List[PropertyRecord]:
        """Get a batch of properties to process"""
        try:
            # Query florida_parcels table for properties
            cursor.execute("""
                SELECT 
                    p.parcel_id,
                    COALESCE(p.owner_name_1, '') as owner_name,
                    COALESCE(p.owner_address_1, '') as owner_address,
                    COALESCE(p.owner_city, '') as owner_city,
                    COALESCE(p.owner_state, '') as owner_state,
                    COALESCE(p.owner_zip, '') as owner_zip
                FROM florida_parcels p
                WHERE p.owner_name_1 IS NOT NULL 
                AND p.owner_name_1 != ''
                AND NOT EXISTS (
                    SELECT 1 FROM sunbiz_property_matches spm 
                    WHERE spm.parcel_id = p.parcel_id
                )
                ORDER BY p.parcel_id
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            properties = []
            for row in cursor.fetchall():
                properties.append(PropertyRecord(
                    parcel_id=row[0],
                    owner_name=row[1],
                    owner_address=row[2],
                    owner_city=row[3],
                    owner_state=row[4],
                    owner_zip=row[5]
                ))
            
            return properties
            
        except Exception as e:
            logger.error(f"Error fetching properties: {e}")
            return []
    
    def find_sunbiz_matches(self, cursor, property_record: PropertyRecord) -> List[SunbizMatch]:
        """Find potential Sunbiz matches for a property"""
        matches = []
        
        # Normalize property data
        norm_owner_name = self.normalize_name(property_record.owner_name)
        norm_owner_address = self.normalize_address(property_record.owner_address)
        
        if not norm_owner_name:
            return matches
        
        try:
            # 1. Exact entity name matches
            cursor.execute("""
                SELECT DISTINCT e.entity_id, e.entity_name, e.record_type
                FROM sunbiz_entities e
                WHERE UPPER(e.entity_name) = %s
                LIMIT 10
            """, (norm_owner_name,))
            
            for row in cursor.fetchall():
                matches.append(SunbizMatch(
                    entity_id=row[0],
                    officer_id=None,
                    entity_name=row[1],
                    officer_name=None,
                    officer_role=None,
                    match_type='EXACT_ENTITY',
                    confidence_score=1.0,
                    match_details={
                        'normalized_property_name': norm_owner_name,
                        'normalized_entity_name': self.normalize_name(row[1])
                    }
                ))
            
            # 2. Fuzzy entity name matches
            cursor.execute("""
                SELECT DISTINCT e.entity_id, e.entity_name, e.record_type
                FROM sunbiz_entities e
                WHERE e.entity_name % %s
                ORDER BY similarity(UPPER(e.entity_name), %s) DESC
                LIMIT 20
            """, (norm_owner_name, norm_owner_name))
            
            for row in cursor.fetchall():
                entity_name_norm = self.normalize_name(row[1])
                similarity = fuzz.ratio(norm_owner_name, entity_name_norm)
                
                if similarity >= self.name_fuzzy_threshold:
                    matches.append(SunbizMatch(
                        entity_id=row[0],
                        officer_id=None,
                        entity_name=row[1],
                        officer_name=None,
                        officer_role=None,
                        match_type='FUZZY_ENTITY',
                        confidence_score=similarity / 100.0,
                        match_details={
                            'normalized_property_name': norm_owner_name,
                            'normalized_entity_name': entity_name_norm,
                            'similarity_score': similarity
                        }
                    ))
            
            # 3. Officer name matches
            cursor.execute("""
                SELECT DISTINCT o.id, o.entity_id, o.full_name, o.officer_role, 
                       e.entity_name, o.street_address, o.city, o.state
                FROM sunbiz_officers o
                JOIN sunbiz_entities e ON o.entity_id = e.entity_id
                WHERE o.full_name % %s
                ORDER BY similarity(UPPER(o.full_name), %s) DESC
                LIMIT 30
            """, (norm_owner_name, norm_owner_name))
            
            for row in cursor.fetchall():
                officer_name_norm = self.normalize_name(row[2])
                name_similarity = fuzz.ratio(norm_owner_name, officer_name_norm)
                
                # Address matching bonus
                address_similarity = 0
                if norm_owner_address and row[5]:
                    norm_sunbiz_address = self.normalize_address(row[5])
                    address_similarity = fuzz.ratio(norm_owner_address, norm_sunbiz_address)
                
                # Combined score
                combined_score = name_similarity
                if address_similarity > 0:
                    # Boost score if addresses match
                    if address_similarity >= self.address_threshold:
                        combined_score = min(100, name_similarity + 20)
                    else:
                        combined_score = (name_similarity * 0.7 + address_similarity * 0.3)
                
                if combined_score >= self.name_fuzzy_threshold:
                    match_type = 'FUZZY_OFFICER'
                    if address_similarity >= self.address_threshold:
                        match_type = 'OFFICER_WITH_ADDRESS'
                    
                    matches.append(SunbizMatch(
                        entity_id=row[1],
                        officer_id=row[0],
                        entity_name=row[4],
                        officer_name=row[2],
                        officer_role=row[3],
                        match_type=match_type,
                        confidence_score=combined_score / 100.0,
                        match_details={
                            'normalized_property_name': norm_owner_name,
                            'normalized_officer_name': officer_name_norm,
                            'name_similarity': name_similarity,
                            'address_similarity': address_similarity,
                            'sunbiz_address': row[5],
                            'property_address': property_record.owner_address
                        }
                    ))
            
            # 4. Address-only matches (for businesses)
            if norm_owner_address and len(norm_owner_address) > 10:
                cursor.execute("""
                    SELECT DISTINCT o.id, o.entity_id, o.full_name, o.officer_role,
                           e.entity_name, o.street_address, o.city, o.state
                    FROM sunbiz_officers o
                    JOIN sunbiz_entities e ON o.entity_id = e.entity_id
                    WHERE o.street_address % %s
                    AND o.city ILIKE %s
                    ORDER BY similarity(UPPER(o.street_address), %s) DESC
                    LIMIT 20
                """, (norm_owner_address, property_record.owner_city, norm_owner_address))
                
                for row in cursor.fetchall():
                    norm_sunbiz_address = self.normalize_address(row[5])
                    address_similarity = fuzz.ratio(norm_owner_address, norm_sunbiz_address)
                    
                    if address_similarity >= self.address_threshold:
                        matches.append(SunbizMatch(
                            entity_id=row[1],
                            officer_id=row[0],
                            entity_name=row[4],
                            officer_name=row[2],
                            officer_role=row[3],
                            match_type='ADDRESS_MATCH',
                            confidence_score=address_similarity / 100.0,
                            match_details={
                                'normalized_property_address': norm_owner_address,
                                'normalized_sunbiz_address': norm_sunbiz_address,
                                'address_similarity': address_similarity,
                                'property_owner': property_record.owner_name,
                                'sunbiz_officer': row[2]
                            }
                        ))
            
        except Exception as e:
            logger.error(f"Error finding matches for {property_record.parcel_id}: {e}")
        
        # Sort matches by confidence score (descending)
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Return top matches only
        return matches[:5]
    
    def save_matches(self, cursor, parcel_id: str, matches: List[SunbizMatch]):
        """Save matches to the database"""
        try:
            for match in matches:
                cursor.execute("""
                    INSERT INTO sunbiz_property_matches 
                    (parcel_id, entity_id, officer_id, match_type, confidence_score, match_details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (parcel_id, entity_id, officer_id) DO UPDATE SET
                        match_type = EXCLUDED.match_type,
                        confidence_score = EXCLUDED.confidence_score,
                        match_details = EXCLUDED.match_details
                """, (
                    parcel_id,
                    match.entity_id,
                    match.officer_id,
                    match.match_type,
                    match.confidence_score,
                    match.match_details
                ))
                
                self.stats['total_matches_created'] += 1
                
        except Exception as e:
            logger.error(f"Error saving matches for {parcel_id}: {e}")
            raise
    
    def process_properties(self, batch_size: int = 1000, max_properties: int = None):
        """Process properties for Sunbiz matching"""
        logger.info("Starting property matching process...")
        
        offset = 0
        processed = 0
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                while True:
                    # Get batch of properties
                    properties = self.get_properties_batch(cursor, offset, batch_size)
                    
                    if not properties:
                        logger.info("No more properties to process")
                        break
                    
                    logger.info(f"Processing batch: {offset+1} to {offset+len(properties)}")
                    
                    for prop in properties:
                        try:
                            # Find matches
                            matches = self.find_sunbiz_matches(cursor, prop)
                            
                            # Categorize matches
                            if matches:
                                best_match = matches[0]
                                if best_match.confidence_score >= 0.95:
                                    self.stats['exact_matches'] += 1
                                elif best_match.match_type == 'ADDRESS_MATCH':
                                    self.stats['address_matches'] += 1
                                else:
                                    self.stats['fuzzy_matches'] += 1
                                
                                # Save matches
                                self.save_matches(cursor, prop.parcel_id, matches)
                            else:
                                self.stats['no_matches'] += 1
                            
                            self.stats['properties_processed'] += 1
                            processed += 1
                            
                            # Progress logging
                            if processed % 100 == 0:
                                logger.info(f"Processed {processed} properties. "
                                          f"Matches: {self.stats['exact_matches'] + self.stats['fuzzy_matches'] + self.stats['address_matches']}")
                            
                            # Check max limit
                            if max_properties and processed >= max_properties:
                                logger.info(f"Reached max properties limit: {max_properties}")
                                return
                                
                        except Exception as e:
                            logger.error(f"Error processing property {prop.parcel_id}: {e}")
                            continue
                    
                    # Commit batch
                    self.conn.commit()
                    offset += batch_size
                    
        except Exception as e:
            logger.error(f"Fatal error in property processing: {e}")
            self.conn.rollback()
            raise
    
    def print_stats(self):
        """Print matching statistics"""
        print("\n" + "="*60)
        print("SUNBIZ PROPERTY MATCHING STATISTICS")
        print("="*60)
        print(f"Properties processed: {self.stats['properties_processed']:,}")
        print(f"Exact matches: {self.stats['exact_matches']:,}")
        print(f"Fuzzy matches: {self.stats['fuzzy_matches']:,}")
        print(f"Address matches: {self.stats['address_matches']:,}")
        print(f"No matches: {self.stats['no_matches']:,}")
        print(f"Total matches created: {self.stats['total_matches_created']:,}")
        
        total_with_matches = (self.stats['exact_matches'] + 
                             self.stats['fuzzy_matches'] + 
                             self.stats['address_matches'])
        
        if self.stats['properties_processed'] > 0:
            match_rate = (total_with_matches / self.stats['properties_processed']) * 100
            print(f"Match rate: {match_rate:.1f}%")
        
        print("="*60)
    
    def create_summary_report(self, cursor):
        """Create summary report of matches"""
        try:
            cursor.execute("""
                SELECT 
                    match_type,
                    COUNT(*) as match_count,
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence
                FROM sunbiz_property_matches
                GROUP BY match_type
                ORDER BY match_count DESC
            """)
            
            print("\nMATCH TYPE SUMMARY:")
            print("-" * 80)
            print(f"{'Match Type':<20} {'Count':<10} {'Avg Conf':<10} {'Min Conf':<10} {'Max Conf':<10}")
            print("-" * 80)
            
            for row in cursor.fetchall():
                print(f"{row[0]:<20} {row[1]:<10} {row[2]:<10.3f} {row[3]:<10.3f} {row[4]:<10.3f}")
            
            print("-" * 80)
            
        except Exception as e:
            logger.error(f"Error creating summary report: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Match Sunbiz data to property records')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Batch size for processing properties')
    parser.add_argument('--max-properties', type=int, default=None,
                       help='Maximum number of properties to process')
    parser.add_argument('--report', action='store_true',
                       help='Generate summary report after processing')
    
    args = parser.parse_args()
    
    # Initialize matcher
    matcher = SunbizPropertyMatcher()
    
    try:
        # Connect to database
        matcher.connect()
        
        # Process properties
        matcher.process_properties(args.batch_size, args.max_properties)
        
        # Generate report if requested
        if args.report:
            with matcher.conn.cursor() as cursor:
                matcher.create_summary_report(cursor)
        
        matcher.print_stats()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        matcher.disconnect()

if __name__ == "__main__":
    main()