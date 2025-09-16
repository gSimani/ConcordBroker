"""
Comprehensive Sunbiz Integration System
This integrates Sunbiz entity data with tax certificates and property ownership
"""

import os
from supabase import create_client
from dotenv import load_dotenv
import re
from difflib import SequenceMatcher

load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('VITE_SUPABASE_ANON_KEY')

supabase = create_client(url, key)

class SunbizIntegration:
    def __init__(self):
        self.common_entity_types = {
            'LLC': 'Limited Liability Company',
            'LP': 'Limited Partnership', 
            'LLP': 'Limited Liability Partnership',
            'CORP': 'Corporation',
            'INC': 'Corporation',
            'CO': 'Company',
            'COMPANY': 'Company',
            'ASSOCIATION': 'Association',
            'NATIONAL ASSOCIATION': 'National Association'
        }
        
    def extract_entity_info(self, buyer_name):
        """Extract entity type and clean name from buyer string"""
        buyer_upper = buyer_name.upper()
        entity_type = None
        clean_name = buyer_name
        
        for suffix, full_type in self.common_entity_types.items():
            if suffix in buyer_upper:
                entity_type = full_type
                break
                
        # Clean common suffixes
        clean_patterns = [
            r',?\s*(LLC|LP|LLP|CORP|INC|CO\.?|COMPANY)\.?\s*$',
            r',?\s*A\s+FLORIDA\s+(LIMITED\s+)?(LIABILITY\s+)?(COMPANY|PARTNERSHIP|CORPORATION)\.?\s*$',
            r',?\s*\(USA\)\.?\s*$'
        ]
        
        for pattern in clean_patterns:
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE).strip()
            
        return {
            'original_name': buyer_name,
            'clean_name': clean_name,
            'entity_type': entity_type,
            'is_entity': entity_type is not None
        }
    
    def similarity_score(self, str1, str2):
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, str1.upper(), str2.upper()).ratio()
    
    def find_matching_entities(self, buyer_name, threshold=0.8):
        """Find Sunbiz entities that match a tax certificate buyer"""
        buyer_info = self.extract_entity_info(buyer_name)
        
        try:
            # Search in sunbiz_entities table
            entities = supabase.table('sunbiz_entities').select('*').execute()
            
            matches = []
            for entity in entities.data:
                entity_name = entity.get('entity_name', '')
                
                # Exact match
                if buyer_info['clean_name'].upper() == entity_name.upper():
                    matches.append({
                        'entity': entity,
                        'match_type': 'exact',
                        'confidence': 1.0
                    })
                
                # High similarity match
                elif self.similarity_score(buyer_info['clean_name'], entity_name) >= threshold:
                    matches.append({
                        'entity': entity,
                        'match_type': 'similar',
                        'confidence': self.similarity_score(buyer_info['clean_name'], entity_name)
                    })
            
            return {
                'buyer_info': buyer_info,
                'matches': sorted(matches, key=lambda x: x['confidence'], reverse=True)
            }
            
        except Exception as e:
            print(f"Error searching entities: {e}")
            return {'buyer_info': buyer_info, 'matches': []}
    
    def update_tax_certificate_entities(self):
        """Update all tax certificates with matching Sunbiz entity data"""
        try:
            # Get all tax certificates
            certificates = supabase.table('tax_certificates').select('*').execute()
            
            updated_count = 0
            for cert in certificates.data:
                buyer_name = cert.get('buyer_name', '')
                if not buyer_name:
                    continue
                
                matches = self.find_matching_entities(buyer_name)
                if matches['matches']:
                    best_match = matches['matches'][0]
                    entity = best_match['entity']
                    
                    # Update the certificate with entity info
                    entity_data = {
                        'entity_name': entity.get('entity_name'),
                        'document_number': entity.get('document_number'),
                        'entity_type': entity.get('entity_type'),
                        'status': entity.get('status'),
                        'principal_address': entity.get('principal_address'),
                        'registered_agent': entity.get('registered_agent_name'),
                        'officers': entity.get('officers', [])
                    }
                    
                    # Update the tax certificate
                    supabase.table('tax_certificates').update({
                        'buyer_entity': entity_data
                    }).eq('id', cert['id']).execute()
                    
                    updated_count += 1
                    print(f"Updated certificate {cert['certificate_number']} with {entity['entity_name']}")
            
            print(f"Updated {updated_count} tax certificates with Sunbiz entity data")
            return updated_count
            
        except Exception as e:
            print(f"Error updating certificates: {e}")
            return 0

def main():
    print("=" * 80)
    print("SUNBIZ INTEGRATION SYSTEM")
    print("=" * 80)
    
    integration = SunbizIntegration()
    
    # Test with known tax certificate buyers
    test_buyers = [
        "IH3 PROPERTY GP",
        "CAPITAL ONE, NATIONAL ASSOCIATION",
        "5T WEALTH PARTNERS LP",
        "TLGFY, LLC"
    ]
    
    print("\nTesting entity matching:")
    for buyer in test_buyers:
        print(f"\n--- Testing: {buyer} ---")
        buyer_info = integration.extract_entity_info(buyer)
        print(f"Clean name: {buyer_info['clean_name']}")
        print(f"Entity type: {buyer_info['entity_type']}")
        print(f"Is entity: {buyer_info['is_entity']}")
        
        matches = integration.find_matching_entities(buyer)
        if matches['matches']:
            print(f"Found {len(matches['matches'])} matches:")
            for match in matches['matches'][:3]:  # Show top 3
                print(f"  - {match['entity']['entity_name']} ({match['confidence']:.2f})")
        else:
            print("  No matches found")
    
    print("\n" + "=" * 80)
    print("ENTITY MATCHING REPORT")
    print("=" * 80)
    
    # Show suggestions for entities to add
    print("\nSuggested entities to add to Sunbiz database:")
    print("1. IH3 PROPERTY GP (Document: M13000005449)")
    print("   - URL provided by user")
    print("   - Type: Florida Limited Partnership")
    
    print("\n2. CAPITAL ONE, NATIONAL ASSOCIATION")
    print("   - Large national bank")
    print("   - Document number: Search Sunbiz for Virginia corp")
    
    print("\n3. 5T WEALTH PARTNERS LP")
    print("   - Investment/wealth management firm")
    print("   - Search Sunbiz for Limited Partnership")
    
    print("\n4. TLGFY, LLC")
    print("   - Florida Limited Liability Company")
    print("   - Search Sunbiz for recent LLC filings")

if __name__ == "__main__":
    main()