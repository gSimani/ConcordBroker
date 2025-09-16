"""
Integrate Sunbiz Entity Matching with Tax Deed Properties
Matches tax deed applicants with Sunbiz corporation entities
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import asyncio

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from workers.sunbiz_data_processor import SunbizDataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SunbizTaxDeedIntegration:
    def __init__(self):
        # Initialize Sunbiz processor
        self.sunbiz_processor = SunbizDataProcessor()
        self.matches = []
    
    async def load_and_process(self):
        """Load Sunbiz data and tax deed properties, then match them"""
        
        # Load Sunbiz corporation data
        logger.info("=== LOADING SUNBIZ DATA ===")
        entities_loaded = self.sunbiz_processor.load_corporation_data(limit=100000)  # Load 100k entities
        
        if entities_loaded == 0:
            logger.error("No Sunbiz entities loaded")
            return
        
        logger.info(f"✅ Loaded {entities_loaded} Sunbiz entities")
        
        # Load tax deed properties from JSON file (since Supabase isn't configured)
        tax_deed_files = list(Path('.').glob('broward_tax_deed_properties_*.json'))
        
        if not tax_deed_files:
            logger.warning("No tax deed property files found, creating test data...")
            properties = self.create_test_properties()
        else:
            # Load most recent file
            tax_deed_files.sort()
            latest_file = tax_deed_files[-1]
            logger.info(f"Loading tax deed properties from {latest_file}")
            
            with open(latest_file, 'r') as f:
                properties = json.load(f)
            
            logger.info(f"Loaded {len(properties)} tax deed properties")
        
        # Match each property with Sunbiz entities
        logger.info("\n=== MATCHING PROPERTIES WITH SUNBIZ ENTITIES ===")
        
        for prop in properties:
            applicant = prop.get('applicant_name', '')
            if not applicant:
                continue
            
            # Find matches
            entity_matches = self.sunbiz_processor.match_entity(
                name=applicant,
                address=prop.get('situs_address')
            )
            
            if entity_matches:
                logger.info(f"\n✅ Property: {prop.get('parcel_number')}")
                logger.info(f"   Applicant: {applicant}")
                
                for match in entity_matches:
                    entity = self.sunbiz_processor.entities.get(match['entity_id'])
                    if entity:
                        logger.info(f"   → Matched: {match['entity_name']} (ID: {match['entity_id']})")
                        logger.info(f"     Type: {entity.get('entity_type', 'N/A')}")
                        logger.info(f"     Status: {entity.get('status', 'N/A')}")
                        logger.info(f"     Address: {entity.get('principal_address', 'N/A')}")
                        logger.info(f"     Confidence: {match['confidence']}")
                        
                        # Store match
                        self.matches.append({
                            'parcel_number': prop.get('parcel_number'),
                            'applicant_name': applicant,
                            'entity_id': match['entity_id'],
                            'entity_name': match['entity_name'],
                            'entity_type': entity.get('entity_type'),
                            'entity_status': entity.get('status'),
                            'match_type': match['match_type'],
                            'confidence': match['confidence'],
                            'sunbiz_url': f"https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults/EntityName/{match['entity_id']}/Page1",
                            'property_appraiser_url': f"https://web.bcpa.net/bcpaclient/#/Record-Search?parcel={prop.get('parcel_number')}"
                        })
            else:
                logger.info(f"\n❌ No match for: {applicant} (Parcel: {prop.get('parcel_number')})")
        
        # Save matches to file
        if self.matches:
            output_file = f"sunbiz_tax_deed_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(self.matches, f, indent=2)
            
            logger.info(f"\n✅ Saved {len(self.matches)} matches to {output_file}")
        
        # Generate summary report
        self.generate_report()
    
    def create_test_properties(self):
        """Create test properties with various entity names"""
        return [
            {
                'parcel_number': '5042-34-21-0190',
                'applicant_name': 'FLORIDA TAX LIEN INVESTMENTS LLC',
                'situs_address': '1234 NW 45TH ST, FORT LAUDERDALE, FL 33309'
            },
            {
                'parcel_number': '4842-15-33-0010',
                'applicant_name': 'BEACH PROPERTY INVESTMENTS INC',
                'situs_address': '5678 SW 22ND AVE, HOLLYWOOD, FL 33023'
            },
            {
                'parcel_number': '5143-28-14-0250',
                'applicant_name': 'COMMERCIAL PROPERTY GROUP LLC',
                'situs_address': '910 E COMMERCIAL BLVD, OAKLAND PARK, FL 33334'
            },
            {
                'parcel_number': '5243-12-45-0100',
                'applicant_name': 'JOHN SMITH',
                'situs_address': '123 MAIN ST, POMPANO BEACH, FL 33060'
            },
            {
                'parcel_number': '5343-22-15-0200',
                'applicant_name': 'REAL ESTATE HOLDINGS CORP',
                'situs_address': '456 OCEAN BLVD, DEERFIELD BEACH, FL 33441'
            }
        ]
    
    def generate_report(self):
        """Generate summary report of matching results"""
        logger.info("\n" + "="*60)
        logger.info("SUNBIZ TAX DEED INTEGRATION REPORT")
        logger.info("="*60)
        
        # Count statistics
        total_entities = len(self.sunbiz_processor.entities)
        total_matches = len(self.matches)
        
        # Group by confidence
        high_confidence = [m for m in self.matches if m['confidence'] >= 0.8]
        medium_confidence = [m for m in self.matches if 0.5 <= m['confidence'] < 0.8]
        low_confidence = [m for m in self.matches if m['confidence'] < 0.5]
        
        # Group by entity type
        entity_types = {}
        for match in self.matches:
            entity_type = match.get('entity_type', 'Unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        logger.info(f"\n📊 STATISTICS:")
        logger.info(f"  Total Sunbiz Entities Loaded: {total_entities:,}")
        logger.info(f"  Total Matches Found: {total_matches}")
        logger.info(f"\n  By Confidence:")
        logger.info(f"    High (≥0.8): {len(high_confidence)}")
        logger.info(f"    Medium (0.5-0.8): {len(medium_confidence)}")
        logger.info(f"    Low (<0.5): {len(low_confidence)}")
        logger.info(f"\n  By Entity Type:")
        for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {entity_type}: {count}")
        
        # Show top matches
        if high_confidence:
            logger.info(f"\n🏆 TOP HIGH-CONFIDENCE MATCHES:")
            for match in high_confidence[:5]:
                logger.info(f"  • {match['applicant_name']} → {match['entity_name']}")
                logger.info(f"    Parcel: {match['parcel_number']}, Confidence: {match['confidence']}")
        
        logger.info("\n" + "="*60)

async def main():
    """Run the integration"""
    integration = SunbizTaxDeedIntegration()
    await integration.load_and_process()

if __name__ == "__main__":
    asyncio.run(main())