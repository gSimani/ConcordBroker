"""
Tax Deed Supabase Integration Agent
====================================
Specialized agent for synchronizing tax deed auction data with Supabase
"""

import os
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from supabase import create_client, Client
import asyncio
from dataclasses import asdict
import re

from tax_deed_auction_scraper import TaxDeedAuctionScraper, Auction, PropertyDetail

logger = logging.getLogger(__name__)

class TaxDeedSupabaseAgent:
    """Agent for managing tax deed data in Supabase"""
    
    def __init__(self):
        """Initialize the Supabase agent"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment")
            
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Tax Deed Supabase Agent initialized")
        
    def parse_address_components(self, address: str) -> Dict[str, str]:
        """Parse address into components"""
        components = {
            'city': '',
            'state': 'FL',
            'zip_code': ''
        }
        
        if address:
            # Try to extract ZIP code
            zip_match = re.search(r'\b(\d{5})(?:-\d{4})?\b', address)
            if zip_match:
                components['zip_code'] = zip_match.group(1)
                
            # Common Florida cities in Broward
            cities = ['FORT LAUDERDALE', 'HOLLYWOOD', 'PEMBROKE PINES', 'MIRAMAR', 
                     'CORAL SPRINGS', 'POMPANO BEACH', 'DAVIE', 'PLANTATION', 
                     'SUNRISE', 'TAMARAC', 'MARGATE', 'COCONUT CREEK', 'DEERFIELD BEACH',
                     'WESTON', 'OAKLAND PARK', 'LAUDERHILL', 'NORTH LAUDERDALE']
            
            address_upper = address.upper()
            for city in cities:
                if city in address_upper:
                    components['city'] = city
                    break
                    
        return components
        
    async def match_sunbiz_entities(self, applicant: str, companies: List[str]) -> Tuple[List[str], List[str], Dict]:
        """Match applicant companies with Sunbiz entities"""
        sunbiz_data = {
            'matched': False,
            'entities': [],
            'search_terms': companies
        }
        
        entity_names = []
        entity_ids = []
        
        try:
            # Search for each company in Sunbiz data
            for company in companies:
                if not company:
                    continue
                    
                # Clean company name for search
                clean_name = company.strip().upper()
                
                # Search in sunbiz_entities table
                result = self.client.table('sunbiz_entities').select(
                    'entity_name, document_number, status, principal_address'
                ).ilike('entity_name', f'%{clean_name}%').limit(5).execute()
                
                if result.data:
                    sunbiz_data['matched'] = True
                    for entity in result.data:
                        entity_names.append(entity['entity_name'])
                        entity_ids.append(entity['document_number'])
                        sunbiz_data['entities'].append({
                            'name': entity['entity_name'],
                            'id': entity['document_number'],
                            'status': entity.get('status'),
                            'address': entity.get('principal_address')
                        })
                        
        except Exception as e:
            logger.error(f"Error matching Sunbiz entities: {e}")
            
        return entity_names, entity_ids, sunbiz_data
        
    async def upsert_auction(self, auction: Auction) -> Dict[str, Any]:
        """Insert or update auction data"""
        try:
            auction_data = {
                'auction_id': auction.auction_id,
                'description': auction.description,
                'auction_date': auction.auction_date.isoformat() if auction.auction_date else None,
                'total_items': auction.total_items,
                'available_items': auction.available_items,
                'advertised_items': auction.advertised_items,
                'canceled_items': auction.canceled_items,
                'status': auction.status.value,
                'auction_url': auction.auction_url,
                'last_updated': auction.last_updated.isoformat() if auction.last_updated else datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'scraper_version': '2.0',
                    'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
                    'property_count': len(auction.properties)
                }
            }
            
            # Upsert auction
            result = self.client.table('tax_deed_auctions').upsert(
                auction_data,
                on_conflict='auction_id'
            ).execute()
            
            logger.info(f"Upserted auction {auction.auction_id}: {auction.description}")
            return result.data[0] if result.data else auction_data
            
        except Exception as e:
            logger.error(f"Error upserting auction {auction.auction_id}: {e}")
            raise
            
    async def upsert_property(self, auction_id: str, property_detail: PropertyDetail) -> Dict[str, Any]:
        """Insert or update a single property with all details"""
        try:
            # Parse address components
            address_components = self.parse_address_components(property_detail.situs_address)
            
            # Match Sunbiz entities
            entity_names, entity_ids, sunbiz_data = await self.match_sunbiz_entities(
                property_detail.applicant,
                property_detail.applicant_companies
            )
            
            # Prepare property data
            property_data = {
                'composite_key': f"{auction_id}_{property_detail.item_id}",
                'auction_id': auction_id,
                'item_id': property_detail.item_id,
                'tax_deed_number': property_detail.tax_deed_number,
                'parcel_number': property_detail.parcel_number,
                'parcel_url': property_detail.parcel_url,
                'tax_certificate_number': property_detail.tax_certificate_number,
                'legal_description': property_detail.legal_description,
                'situs_address': property_detail.situs_address,
                'city': address_components['city'],
                'state': address_components['state'],
                'zip_code': address_components['zip_code'],
                'homestead': property_detail.homestead,
                'assessed_value': float(property_detail.assessed_value) if property_detail.assessed_value else None,
                'soh_value': float(property_detail.soh_value) if property_detail.soh_value else None,
                'applicant': property_detail.applicant,
                'applicant_companies': property_detail.applicant_companies,
                'gis_map_url': property_detail.gis_map_url,
                'opening_bid': float(property_detail.opening_bid) if property_detail.opening_bid else 0,
                'best_bid': float(property_detail.best_bid) if property_detail.best_bid else None,
                'close_time': property_detail.close_time.isoformat() if property_detail.close_time else None,
                'status': property_detail.status.value,
                'sunbiz_matched': sunbiz_data['matched'],
                'sunbiz_entity_names': entity_names,
                'sunbiz_entity_ids': entity_ids,
                'sunbiz_data': sunbiz_data,
                'extracted_at': property_detail.extracted_at.isoformat() if property_detail.extracted_at else datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'has_parcel_link': bool(property_detail.parcel_url),
                    'has_gis_map': bool(property_detail.gis_map_url),
                    'company_count': len(property_detail.applicant_companies),
                    'sunbiz_match_count': len(entity_names)
                }
            }
            
            # Upsert property
            result = self.client.table('tax_deed_properties').upsert(
                property_data,
                on_conflict='composite_key'
            ).execute()
            
            if result.data:
                property_id = result.data[0]['id']
                
                # Create or update contact record
                contact_data = {
                    'property_id': property_id,
                    'composite_key': property_data['composite_key'],
                    'contact_status': 'Not Contacted',
                    'owner_name': property_detail.applicant,
                    'notes': f"Tax Deed #{property_detail.tax_deed_number}\n"
                            f"Opening Bid: ${property_detail.opening_bid:,.2f}\n"
                            f"Homestead: {'Yes' if property_detail.homestead else 'No'}"
                }
                
                # Check if contact exists
                existing_contact = self.client.table('tax_deed_contacts').select('id').eq(
                    'property_id', property_id
                ).execute()
                
                if not existing_contact.data:
                    # Insert new contact
                    self.client.table('tax_deed_contacts').insert(contact_data).execute()
                    
                # Add to history
                await self.add_property_history(property_id, property_data, 'initial_import')
                
            logger.info(f"Upserted property {property_detail.tax_deed_number} at {property_detail.situs_address}")
            return result.data[0] if result.data else property_data
            
        except Exception as e:
            logger.error(f"Error upserting property {property_detail.item_id}: {e}")
            raise
            
    async def add_property_history(self, property_id: str, property_data: Dict, change_type: str):
        """Add property history record"""
        try:
            history_data = {
                'property_id': property_id,
                'composite_key': property_data['composite_key'],
                'auction_id': property_data['auction_id'],
                'item_id': property_data['item_id'],
                'tax_deed_number': property_data['tax_deed_number'],
                'parcel_number': property_data['parcel_number'],
                'status': property_data['status'],
                'opening_bid': property_data['opening_bid'],
                'best_bid': property_data.get('best_bid'),
                'change_type': change_type,
                'change_details': {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data_snapshot': property_data
                }
            }
            
            self.client.table('tax_deed_property_history').insert(history_data).execute()
            
        except Exception as e:
            logger.error(f"Error adding property history: {e}")
            
    async def sync_auction_data(self, auctions: List[Auction]) -> Dict[str, Any]:
        """Sync all auction data to Supabase"""
        results = {
            'auctions_synced': 0,
            'properties_synced': 0,
            'errors': [],
            'sunbiz_matches': 0
        }
        
        try:
            for auction in auctions:
                try:
                    # Upsert auction
                    await self.upsert_auction(auction)
                    results['auctions_synced'] += 1
                    
                    # Upsert properties
                    for property_detail in auction.properties:
                        try:
                            prop_result = await self.upsert_property(
                                auction.auction_id,
                                property_detail
                            )
                            results['properties_synced'] += 1
                            
                            if prop_result.get('sunbiz_matched'):
                                results['sunbiz_matches'] += 1
                                
                        except Exception as e:
                            error_msg = f"Error syncing property {property_detail.item_id}: {e}"
                            logger.error(error_msg)
                            results['errors'].append(error_msg)
                            
                except Exception as e:
                    error_msg = f"Error syncing auction {auction.auction_id}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    
            # Create alerts for high-value and homestead properties
            await self.create_property_alerts(auctions)
            
            logger.info(f"Sync completed: {results['auctions_synced']} auctions, "
                       f"{results['properties_synced']} properties, "
                       f"{results['sunbiz_matches']} Sunbiz matches")
            
        except Exception as e:
            logger.error(f"Error in sync_auction_data: {e}")
            results['errors'].append(str(e))
            
        return results
        
    async def create_property_alerts(self, auctions: List[Auction]):
        """Create alerts for notable properties"""
        try:
            alerts = []
            
            for auction in auctions:
                for prop in auction.properties:
                    # High-value property alert
                    if prop.opening_bid > 100000:
                        alerts.append({
                            'alert_type': 'HIGH_VALUE_PROPERTY',
                            'priority': 'HIGH',
                            'title': f'High Value: ${prop.opening_bid:,.2f}',
                            'details': f'{prop.situs_address}\nTax Deed: {prop.tax_deed_number}',
                            'auction_id': auction.auction_id
                        })
                        
                    # Homestead property alert
                    if prop.homestead:
                        alerts.append({
                            'alert_type': 'HOMESTEAD_PROPERTY',
                            'priority': 'MEDIUM',
                            'title': 'Homestead Property Available',
                            'details': f'{prop.situs_address}\nOpening Bid: ${prop.opening_bid:,.2f}',
                            'auction_id': auction.auction_id
                        })
                        
            # Insert alerts
            if alerts:
                self.client.table('tax_deed_alerts').insert(alerts).execute()
                logger.info(f"Created {len(alerts)} property alerts")
                
        except Exception as e:
            logger.error(f"Error creating property alerts: {e}")
            
    async def get_properties_for_display(self, 
                                        status: Optional[str] = None,
                                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get properties formatted for website display"""
        try:
            query = self.client.table('tax_deed_properties_with_contacts').select('*')
            
            if status:
                query = query.eq('status', status)
                
            query = query.order('opening_bid', desc=True).limit(limit)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting properties for display: {e}")
            return []
            
    async def update_contact_info(self, property_id: str, contact_data: Dict[str, Any]) -> bool:
        """Update contact information for a property"""
        try:
            # Check if contact exists
            existing = self.client.table('tax_deed_contacts').select('id').eq(
                'property_id', property_id
            ).execute()
            
            if existing.data:
                # Update existing
                result = self.client.table('tax_deed_contacts').update(
                    contact_data
                ).eq('property_id', property_id).execute()
            else:
                # Insert new
                contact_data['property_id'] = property_id
                result = self.client.table('tax_deed_contacts').insert(
                    contact_data
                ).execute()
                
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating contact info: {e}")
            return False
            
async def run_sync():
    """Run the synchronization process"""
    logger.info("Starting Tax Deed Supabase synchronization...")
    
    # Initialize components
    agent = TaxDeedSupabaseAgent()
    
    # Run scraper
    async with TaxDeedAuctionScraper() as scraper:
        auctions = await scraper.scrape_all_auctions()
        
        if auctions:
            # Sync to Supabase
            results = await agent.sync_auction_data(auctions)
            
            print(f"\nSync Results:")
            print(f"- Auctions synced: {results['auctions_synced']}")
            print(f"- Properties synced: {results['properties_synced']}")
            print(f"- Sunbiz matches: {results['sunbiz_matches']}")
            
            if results['errors']:
                print(f"- Errors: {len(results['errors'])}")
                for error in results['errors'][:5]:
                    print(f"  - {error}")
                    
            # Save backup
            scraper.save_to_json(auctions, 'tax_deed_sync_backup.json')
            
        else:
            print("No auctions found to sync")
            
if __name__ == "__main__":
    asyncio.run(run_sync())