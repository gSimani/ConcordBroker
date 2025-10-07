#!/usr/bin/env python3
"""
Property-Entity Linking Service
================================
Links properties to business entities for comprehensive ownership analysis
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import re
from fuzzywuzzy import fuzz
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PropertyEntityLinker:
    def __init__(self):
        """Initialize the property-entity linking service"""
        # Supabase connection
        self.supabase_url = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # SQLAlchemy for bulk operations
        db_url = os.getenv('DATABASE_URL', '')
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
        self.engine = create_engine(db_url)

    def clean_entity_name(self, name: str) -> str:
        """Clean and normalize entity names for matching"""
        if not name:
            return ""

        # Convert to uppercase
        name = name.upper()

        # Remove common suffixes
        suffixes = [' LLC', ' INC', ' CORP', ' CORPORATION', ' LP', ' LLP', ' PA',
                   ' PLLC', ' PC', ' TRUST', ' TRUSTEE', ' ESTATE', ' REV TR',
                   ' REVOCABLE TRUST', ' LIVING TRUST', ' FAMILY TRUST']

        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Remove special characters and extra spaces
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())

        return name

    def match_property_to_entity(self, owner_name: str) -> Optional[Dict]:
        """Match a property owner to business entities"""
        if not owner_name:
            return None

        # Clean the owner name
        clean_owner = self.clean_entity_name(owner_name)

        # Skip individual names (likely not business entities)
        if len(clean_owner.split()) <= 2 and not any(word in owner_name.upper() for word in ['LLC', 'INC', 'CORP', 'TRUST']):
            return None

        try:
            # Search in florida_entities
            result = self.supabase.table('florida_entities') \
                .select('*') \
                .ilike('entity_name', f'%{clean_owner}%') \
                .limit(5) \
                .execute()

            if result.data:
                # Calculate match scores
                best_match = None
                best_score = 0

                for entity in result.data:
                    entity_clean = self.clean_entity_name(entity.get('entity_name', ''))
                    score = fuzz.ratio(clean_owner, entity_clean)

                    if score > best_score:
                        best_score = score
                        best_match = entity

                if best_score >= 70:  # 70% similarity threshold
                    return {
                        'entity_id': best_match.get('entity_id'),
                        'entity_name': best_match.get('entity_name'),
                        'entity_type': best_match.get('entity_type'),
                        'status': best_match.get('status'),
                        'match_score': best_score,
                        'match_type': 'florida_entities'
                    }

            # Search in sunbiz_corporate
            result = self.supabase.table('sunbiz_corporate') \
                .select('*') \
                .ilike('entity_name', f'%{clean_owner}%') \
                .limit(5) \
                .execute()

            if result.data:
                best_match = None
                best_score = 0

                for entity in result.data:
                    entity_clean = self.clean_entity_name(entity.get('entity_name', ''))
                    score = fuzz.ratio(clean_owner, entity_clean)

                    if score > best_score:
                        best_score = score
                        best_match = entity

                if best_score >= 70:
                    return {
                        'entity_id': best_match.get('filing_number'),
                        'entity_name': best_match.get('entity_name'),
                        'entity_type': best_match.get('filing_type'),
                        'status': best_match.get('status'),
                        'match_score': best_score,
                        'match_type': 'sunbiz_corporate'
                    }

        except Exception as e:
            logger.error(f"Error matching entity for {owner_name}: {e}")

        return None

    def link_properties_batch(self, county: str = None, limit: int = 1000):
        """Process a batch of properties and link them to entities"""
        logger.info(f"Starting property-entity linking for {county or 'all counties'}")

        # Build query
        query = """
            SELECT DISTINCT parcel_id, owner_name, county, year
            FROM florida_parcels
            WHERE owner_name IS NOT NULL
            AND owner_name != ''
            AND owner_name != '-'
        """

        if county:
            query += f" AND county = '{county.upper()}'"

        query += f" LIMIT {limit}"

        try:
            # Fetch properties
            with self.engine.connect() as conn:
                properties = pd.read_sql(query, conn)

            logger.info(f"Processing {len(properties)} properties")

            # Process each property
            links = []
            for _, prop in properties.iterrows():
                entity_match = self.match_property_to_entity(prop['owner_name'])

                if entity_match:
                    links.append({
                        'parcel_id': prop['parcel_id'],
                        'county': prop['county'],
                        'year': prop['year'],
                        'owner_name': prop['owner_name'],
                        'entity_id': entity_match['entity_id'],
                        'entity_name': entity_match['entity_name'],
                        'entity_type': entity_match['entity_type'],
                        'entity_status': entity_match['status'],
                        'match_score': entity_match['match_score'],
                        'match_type': entity_match['match_type'],
                        'created_at': datetime.now().isoformat()
                    })

            logger.info(f"Found {len(links)} entity matches")

            # Store results in property_entity_matches table
            if links:
                # Create table if not exists
                create_table_sql = """
                    CREATE TABLE IF NOT EXISTS property_entity_matches (
                        id SERIAL PRIMARY KEY,
                        parcel_id VARCHAR(50),
                        county VARCHAR(50),
                        year INTEGER,
                        owner_name TEXT,
                        entity_id VARCHAR(100),
                        entity_name TEXT,
                        entity_type VARCHAR(100),
                        entity_status VARCHAR(50),
                        match_score INTEGER,
                        match_type VARCHAR(50),
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(parcel_id, county, year, entity_id)
                    );

                    CREATE INDEX IF NOT EXISTS idx_property_entity_parcel
                    ON property_entity_matches(parcel_id);

                    CREATE INDEX IF NOT EXISTS idx_property_entity_entity
                    ON property_entity_matches(entity_id);

                    CREATE INDEX IF NOT EXISTS idx_property_entity_score
                    ON property_entity_matches(match_score);
                """

                with self.engine.connect() as conn:
                    conn.execute(text(create_table_sql))
                    conn.commit()

                # Insert links
                df_links = pd.DataFrame(links)
                df_links.to_sql('property_entity_matches', self.engine,
                               if_exists='append', index=False, method='multi')

                logger.info(f"Successfully stored {len(links)} property-entity links")

            return {
                'processed': len(properties),
                'matched': len(links),
                'match_rate': len(links) / len(properties) * 100 if len(properties) > 0 else 0,
                'sample_matches': links[:10] if links else []
            }

        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return None

    def get_entity_properties(self, entity_id: str) -> List[Dict]:
        """Get all properties owned by an entity"""
        try:
            result = self.supabase.table('property_entity_matches') \
                .select('*') \
                .eq('entity_id', entity_id) \
                .execute()

            if result.data:
                # Get full property details
                properties = []
                for match in result.data:
                    prop_result = self.supabase.table('florida_parcels') \
                        .select('*') \
                        .eq('parcel_id', match['parcel_id']) \
                        .eq('county', match['county']) \
                        .single() \
                        .execute()

                    if prop_result.data:
                        properties.append({
                            **prop_result.data,
                            'match_score': match['match_score'],
                            'match_type': match['match_type']
                        })

                return properties

        except Exception as e:
            logger.error(f"Error getting entity properties: {e}")

        return []

    def get_property_entities(self, parcel_id: str) -> List[Dict]:
        """Get all entities associated with a property"""
        try:
            result = self.supabase.table('property_entity_matches') \
                .select('*') \
                .eq('parcel_id', parcel_id) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting property entities: {e}")

        return []

def main():
    """Main execution function"""
    linker = PropertyEntityLinker()

    # Process top counties
    counties = ['MIAMI-DADE', 'BROWARD', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH']

    for county in counties:
        logger.info(f"\nProcessing {county} county...")
        result = linker.link_properties_batch(county=county, limit=500)

        if result:
            print(f"\n{county} Results:")
            print(f"  Processed: {result['processed']}")
            print(f"  Matched: {result['matched']}")
            print(f"  Match Rate: {result['match_rate']:.1f}%")

            if result['sample_matches']:
                print(f"\n  Sample matches:")
                for match in result['sample_matches'][:3]:
                    print(f"    - {match['owner_name']} → {match['entity_name']} (Score: {match['match_score']})")

    # Generate summary report
    with linker.engine.connect() as conn:
        summary = pd.read_sql("""
            SELECT
                COUNT(DISTINCT parcel_id) as total_properties_linked,
                COUNT(DISTINCT entity_id) as total_entities,
                AVG(match_score) as avg_match_score,
                match_type,
                COUNT(*) as count
            FROM property_entity_matches
            GROUP BY match_type
        """, conn)

        print("\n" + "="*60)
        print("PROPERTY-ENTITY LINKING SUMMARY")
        print("="*60)
        print(summary.to_string(index=False))

if __name__ == "__main__":
    main()