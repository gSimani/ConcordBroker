"""
Tax Deed Auction Database Integration
======================================
Manages storage and retrieval of tax deed auction data in Supabase
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
import asyncio
from dataclasses import asdict

logger = logging.getLogger(__name__)

class TaxDeedDatabase:
    """Database manager for tax deed auction data"""
    
    def __init__(self):
        """Initialize database connection"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment")
            
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
    def ensure_tables(self):
        """Ensure necessary tables exist"""
        # This would normally be done via migrations
        # Tables needed:
        # - tax_deed_auctions
        # - tax_deed_properties
        # - tax_deed_property_history
        pass
        
    async def upsert_auction(self, auction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update auction data"""
        try:
            # Prepare auction record
            auction_record = {
                'auction_id': auction_data['auction_id'],
                'description': auction_data['description'],
                'auction_date': auction_data['auction_date'],
                'total_items': auction_data['total_items'],
                'available_items': auction_data['available_items'],
                'advertised_items': auction_data['advertised_items'],
                'canceled_items': auction_data['canceled_items'],
                'status': auction_data['status'],
                'auction_url': auction_data['auction_url'],
                'last_updated': auction_data.get('last_updated', datetime.now(timezone.utc).isoformat()),
                'metadata': {
                    'scraper_version': '1.0',
                    'extraction_timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Upsert to database
            result = self.client.table('tax_deed_auctions').upsert(
                auction_record,
                on_conflict='auction_id'
            ).execute()
            
            logger.info(f"Upserted auction {auction_data['auction_id']}")
            return result.data[0] if result.data else auction_record
            
        except Exception as e:
            logger.error(f"Error upserting auction: {e}")
            raise
            
    async def upsert_properties(self, auction_id: str, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insert or update property data for an auction"""
        try:
            results = []
            
            for prop in properties:
                # Prepare property record
                property_record = {
                    'auction_id': auction_id,
                    'item_id': prop['item_id'],
                    'tax_deed_number': prop['tax_deed_number'],
                    'parcel_number': prop.get('parcel_number', ''),
                    'parcel_url': prop.get('parcel_url'),
                    'tax_certificate_number': prop.get('tax_certificate_number'),
                    'legal_description': prop.get('legal_description', ''),
                    'situs_address': prop.get('situs_address', ''),
                    'homestead': prop.get('homestead', False),
                    'assessed_value': prop.get('assessed_value'),
                    'soh_value': prop.get('soh_value'),
                    'applicant': prop.get('applicant', ''),
                    'applicant_companies': prop.get('applicant_companies', []),
                    'gis_map_url': prop.get('gis_map_url'),
                    'opening_bid': prop.get('opening_bid', 0.0),
                    'best_bid': prop.get('best_bid'),
                    'close_time': prop.get('close_time'),
                    'status': prop.get('status', 'Upcoming'),
                    'extracted_at': prop.get('extracted_at', datetime.now(timezone.utc).isoformat()),
                    'metadata': {
                        'is_disabled': prop.get('is_disabled', False),
                        'removal_message': prop.get('removal_message')
                    }
                }
                
                # Create composite key for upsert
                property_record['composite_key'] = f"{auction_id}_{prop['item_id']}"
                
                # Upsert property
                result = self.client.table('tax_deed_properties').upsert(
                    property_record,
                    on_conflict='composite_key'
                ).execute()
                
                results.append(result.data[0] if result.data else property_record)
                
                # Also insert into history table for tracking changes
                history_record = property_record.copy()
                history_record['snapshot_time'] = datetime.now(timezone.utc).isoformat()
                
                self.client.table('tax_deed_property_history').insert(history_record).execute()
                
            logger.info(f"Upserted {len(results)} properties for auction {auction_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error upserting properties: {e}")
            raise
            
    async def get_auction(self, auction_id: str) -> Optional[Dict[str, Any]]:
        """Get auction by ID"""
        try:
            result = self.client.table('tax_deed_auctions').select("*").eq(
                'auction_id', auction_id
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting auction: {e}")
            return None
            
    async def get_upcoming_auctions(self) -> List[Dict[str, Any]]:
        """Get all upcoming auctions"""
        try:
            result = self.client.table('tax_deed_auctions').select("*").eq(
                'status', 'Upcoming'
            ).order('auction_date').execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting upcoming auctions: {e}")
            return []
            
    async def get_auction_properties(self, auction_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get properties for an auction"""
        try:
            query = self.client.table('tax_deed_properties').select("*").eq(
                'auction_id', auction_id
            )
            
            if status:
                query = query.eq('status', status)
                
            result = query.order('close_time').execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting auction properties: {e}")
            return []
            
    async def search_properties_by_address(self, address: str) -> List[Dict[str, Any]]:
        """Search properties by address"""
        try:
            result = self.client.table('tax_deed_properties').select("*").ilike(
                'situs_address', f'%{address}%'
            ).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error searching properties by address: {e}")
            return []
            
    async def search_properties_by_parcel(self, parcel_number: str) -> List[Dict[str, Any]]:
        """Search properties by parcel number"""
        try:
            result = self.client.table('tax_deed_properties').select("*").eq(
                'parcel_number', parcel_number
            ).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error searching properties by parcel: {e}")
            return []
            
    async def get_property_history(self, auction_id: str, item_id: str) -> List[Dict[str, Any]]:
        """Get historical data for a property"""
        try:
            composite_key = f"{auction_id}_{item_id}"
            
            result = self.client.table('tax_deed_property_history').select("*").eq(
                'composite_key', composite_key
            ).order('snapshot_time', desc=True).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting property history: {e}")
            return []
            
    async def get_properties_by_applicant(self, company_name: str) -> List[Dict[str, Any]]:
        """Get properties by applicant company name (for Sunbiz matching)"""
        try:
            result = self.client.table('tax_deed_properties').select("*").contains(
                'applicant_companies', [company_name]
            ).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error searching properties by applicant: {e}")
            return []
            
    async def get_high_value_properties(self, min_value: float = 100000) -> List[Dict[str, Any]]:
        """Get properties with opening bid above threshold"""
        try:
            result = self.client.table('tax_deed_properties').select("*").gte(
                'opening_bid', min_value
            ).eq('status', 'Upcoming').order('opening_bid', desc=True).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting high value properties: {e}")
            return []
            
    async def get_homestead_properties(self) -> List[Dict[str, Any]]:
        """Get homestead properties"""
        try:
            result = self.client.table('tax_deed_properties').select("*").eq(
                'homestead', True
            ).eq('status', 'Upcoming').execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting homestead properties: {e}")
            return []
            
    async def get_auction_statistics(self, auction_id: str) -> Dict[str, Any]:
        """Get statistics for an auction"""
        try:
            properties = await self.get_auction_properties(auction_id)
            
            stats = {
                'total_properties': len(properties),
                'upcoming': len([p for p in properties if p['status'] == 'Upcoming']),
                'canceled': len([p for p in properties if p['status'] == 'Canceled']),
                'removed': len([p for p in properties if p['status'] == 'Removed']),
                'total_opening_bid': sum(p.get('opening_bid', 0) for p in properties),
                'average_opening_bid': sum(p.get('opening_bid', 0) for p in properties) / len(properties) if properties else 0,
                'homestead_count': len([p for p in properties if p.get('homestead')]),
                'high_value_count': len([p for p in properties if p.get('opening_bid', 0) > 100000])
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting auction statistics: {e}")
            return {}
            
    async def save_scraped_data(self, auctions: List[Any]) -> Dict[str, Any]:
        """Save complete scraped data from scraper"""
        try:
            results = {
                'auctions_saved': 0,
                'properties_saved': 0,
                'errors': []
            }
            
            for auction in auctions:
                try:
                    # Convert to dict if it's a dataclass
                    if hasattr(auction, '__dataclass_fields__'):
                        auction_dict = asdict(auction)
                    else:
                        auction_dict = auction
                        
                    # Save auction
                    await self.upsert_auction(auction_dict)
                    results['auctions_saved'] += 1
                    
                    # Save properties
                    properties = auction_dict.get('properties', [])
                    if properties:
                        # Convert properties to dicts if needed
                        props_data = []
                        for prop in properties:
                            if hasattr(prop, '__dataclass_fields__'):
                                props_data.append(asdict(prop))
                            else:
                                props_data.append(prop)
                                
                        await self.upsert_properties(
                            auction_dict['auction_id'],
                            props_data
                        )
                        results['properties_saved'] += len(props_data)
                        
                except Exception as e:
                    error_msg = f"Error saving auction {auction_dict.get('auction_id', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    
            return results
            
        except Exception as e:
            logger.error(f"Error saving scraped data: {e}")
            raise