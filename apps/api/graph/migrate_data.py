"""
Data Migration Script for Graphiti
Migrates existing property data from Supabase to Neo4j Knowledge Graph
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from tqdm.asyncio import tqdm

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import required modules
try:
    from supabase import create_client, Client
    from property_graph_service import PropertyGraphService, PropertyNode, OwnerNode, TransactionEdge
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Required modules not available: {e}")
    IMPORTS_AVAILABLE = False


@dataclass
class MigrationStats:
    """Track migration statistics"""
    total_properties: int = 0
    migrated_properties: int = 0
    failed_properties: int = 0
    total_owners: int = 0
    migrated_owners: int = 0
    total_transactions: int = 0
    migrated_transactions: int = 0
    total_relationships: int = 0
    errors: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PropertyDataMigrator:
    """Migrate property data from Supabase to Graphiti"""
    
    def __init__(self, batch_size: int = 100):
        """
        Initialize migrator
        
        Args:
            batch_size: Number of records to process in each batch
        """
        # Initialize Supabase client
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize Graph service
        self.graph_service = PropertyGraphService()
        
        # Migration settings
        self.batch_size = batch_size
        self.stats = MigrationStats()
        
        logger.info(f"Migrator initialized with batch size: {batch_size}")
        
    async def migrate_properties(self, limit: Optional[int] = None) -> MigrationStats:
        """
        Migrate property data from florida_parcels table
        
        Args:
            limit: Optional limit on number of properties to migrate
            
        Returns:
            Migration statistics
        """
        logger.info("Starting property migration...")
        
        try:
            # Count total properties
            count_response = self.supabase.table('florida_parcels').select('*', count='exact').execute()
            total_count = count_response.count if hasattr(count_response, 'count') else 0
            
            if limit:
                total_count = min(total_count, limit)
            
            self.stats.total_properties = total_count
            logger.info(f"Found {total_count} properties to migrate")
            
            # Process in batches
            offset = 0
            
            with tqdm(total=total_count, desc="Migrating properties") as pbar:
                while offset < total_count:
                    # Fetch batch
                    batch_size = min(self.batch_size, total_count - offset)
                    
                    response = self.supabase.table('florida_parcels').select('*').range(
                        offset, 
                        offset + batch_size - 1
                    ).execute()
                    
                    if not response.data:
                        break
                    
                    # Process batch
                    await self._process_property_batch(response.data, pbar)
                    
                    offset += batch_size
                    
                    # Add small delay to avoid overwhelming the API
                    await asyncio.sleep(0.1)
            
            logger.info(f"Property migration completed: {self.stats.migrated_properties}/{self.stats.total_properties}")
            
        except Exception as e:
            logger.error(f"Property migration failed: {e}")
            self.stats.errors.append({
                "stage": "property_migration",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
        return self.stats
        
    async def _process_property_batch(self, properties: List[Dict], pbar: tqdm):
        """Process a batch of properties"""
        
        for prop_data in properties:
            try:
                # Create PropertyNode
                property_node = PropertyNode(
                    parcel_id=prop_data.get('parcel_id', ''),
                    address=prop_data.get('phy_addr1', ''),
                    city=prop_data.get('phy_city', ''),
                    county=prop_data.get('county', 'Broward'),
                    state=prop_data.get('phy_state', 'FL'),
                    property_type=self._map_property_type(prop_data.get('dor_uc')),
                    current_value=float(prop_data.get('jv', 0)) if prop_data.get('jv') else None,
                    land_value=float(prop_data.get('lnd_val', 0)) if prop_data.get('lnd_val') else None,
                    building_value=float(prop_data.get('bld_val', 0)) if prop_data.get('bld_val') else None,
                    year_built=int(prop_data.get('act_yr_blt', 0)) if prop_data.get('act_yr_blt') else None,
                    square_feet=int(prop_data.get('tot_lvg_area', 0)) if prop_data.get('tot_lvg_area') else None,
                    bedrooms=int(prop_data.get('bedrooms', 0)) if prop_data.get('bedrooms') else None,
                    bathrooms=float(prop_data.get('bathrooms', 0)) if prop_data.get('bathrooms') else None
                )
                
                # Add to graph
                await self.graph_service.add_property(property_node)
                
                # Process owner if available
                if prop_data.get('own_name'):
                    await self._process_owner(prop_data)
                
                self.stats.migrated_properties += 1
                pbar.update(1)
                
            except Exception as e:
                logger.warning(f"Failed to migrate property {prop_data.get('parcel_id')}: {e}")
                self.stats.failed_properties += 1
                self.stats.errors.append({
                    "parcel_id": prop_data.get('parcel_id'),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                pbar.update(1)
                
    async def _process_owner(self, prop_data: Dict):
        """Process owner information"""
        
        try:
            owner_name = prop_data.get('own_name', '').strip()
            if not owner_name:
                return
            
            # Determine owner type
            entity_type = self._determine_entity_type(owner_name)
            
            # Create OwnerNode
            owner_node = OwnerNode(
                name=owner_name,
                entity_type=entity_type,
                address=prop_data.get('own_addr1', '')
            )
            
            # Add to graph
            await self.graph_service.add_owner(owner_node)
            
            # Create ownership relationship
            await self.graph_service.add_ownership(
                parcel_id=prop_data.get('parcel_id'),
                owner_name=owner_name,
                ownership_type="current",
                percentage=100.0  # Assume full ownership unless specified
            )
            
            self.stats.migrated_owners += 1
            self.stats.total_relationships += 1
            
        except Exception as e:
            logger.warning(f"Failed to process owner {owner_name}: {e}")
            
    async def migrate_sunbiz_data(self) -> MigrationStats:
        """Migrate Sunbiz corporation data"""
        
        logger.info("Starting Sunbiz data migration...")
        
        try:
            # Check if sunbiz tables exist
            tables = ['sunbiz_corporations', 'sunbiz_officers', 'sunbiz_addresses']
            
            for table in tables:
                try:
                    response = self.supabase.table(table).select('*').limit(1).execute()
                    
                    if response.data:
                        logger.info(f"Found {table} table")
                        
                        if table == 'sunbiz_corporations':
                            await self._migrate_corporations()
                        elif table == 'sunbiz_officers':
                            await self._migrate_officers()
                            
                except Exception as e:
                    logger.warning(f"Table {table} not found or inaccessible: {e}")
                    
        except Exception as e:
            logger.error(f"Sunbiz migration failed: {e}")
            self.stats.errors.append({
                "stage": "sunbiz_migration",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
        return self.stats
        
    async def _migrate_corporations(self):
        """Migrate corporation data"""
        
        response = self.supabase.table('sunbiz_corporations').select('*').limit(1000).execute()
        
        if not response.data:
            return
        
        logger.info(f"Migrating {len(response.data)} corporations...")
        
        for corp in tqdm(response.data, desc="Migrating corporations"):
            try:
                # Create corporation as owner
                owner_node = OwnerNode(
                    name=corp.get('cor_name', ''),
                    entity_type="corporation",
                    sunbiz_id=corp.get('cor_number', ''),
                    address=corp.get('prin_add_1', '')
                )
                
                await self.graph_service.add_owner(owner_node)
                self.stats.migrated_owners += 1
                
            except Exception as e:
                logger.warning(f"Failed to migrate corporation {corp.get('cor_name')}: {e}")
                
    async def _migrate_officers(self):
        """Migrate officer data"""
        
        response = self.supabase.table('sunbiz_officers').select('*').limit(1000).execute()
        
        if not response.data:
            return
        
        logger.info(f"Migrating {len(response.data)} officers...")
        
        for officer in tqdm(response.data, desc="Migrating officers"):
            try:
                # Create officer as owner
                owner_node = OwnerNode(
                    name=officer.get('name', ''),
                    entity_type="person",
                    address=officer.get('address', '')
                )
                
                await self.graph_service.add_owner(owner_node)
                
                # Create relationship to corporation if available
                if officer.get('cor_number'):
                    # This would need to be implemented in the graph service
                    pass
                    
                self.stats.migrated_owners += 1
                
            except Exception as e:
                logger.warning(f"Failed to migrate officer {officer.get('name')}: {e}")
                
    async def migrate_sales_history(self) -> MigrationStats:
        """Migrate sales history and transactions"""
        
        logger.info("Starting sales history migration...")
        
        try:
            # Check for sales tables
            tables = ['sales_history', 'sdf_sales', 'tax_deed_sales']
            
            for table in tables:
                try:
                    response = self.supabase.table(table).select('*').limit(1000).execute()
                    
                    if response.data:
                        logger.info(f"Migrating {len(response.data)} records from {table}")
                        
                        for sale in tqdm(response.data, desc=f"Migrating {table}"):
                            await self._process_sale(sale, table)
                            
                except Exception as e:
                    logger.warning(f"Table {table} not found: {e}")
                    
        except Exception as e:
            logger.error(f"Sales history migration failed: {e}")
            self.stats.errors.append({
                "stage": "sales_migration",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
        return self.stats
        
    async def _process_sale(self, sale_data: Dict, source_table: str):
        """Process a sale transaction"""
        
        try:
            # Extract transaction details based on table structure
            if source_table == 'tax_deed_sales':
                transaction = TransactionEdge(
                    transaction_type="tax_deed",
                    date=datetime.fromisoformat(sale_data.get('sale_date', '')) if sale_data.get('sale_date') else datetime.now(),
                    amount=float(sale_data.get('winning_bid', 0)) if sale_data.get('winning_bid') else None,
                    document_number=sale_data.get('td_number', '')
                )
                parcel_id = sale_data.get('parcel_id', '')
                
            elif source_table == 'sdf_sales':
                transaction = TransactionEdge(
                    transaction_type="sale",
                    date=datetime.fromisoformat(sale_data.get('sale_date', '')) if sale_data.get('sale_date') else datetime.now(),
                    amount=float(sale_data.get('sale_price', 0)) if sale_data.get('sale_price') else None,
                    document_number=sale_data.get('or_book_page', '')
                )
                parcel_id = sale_data.get('parcel_id', '')
                
            else:  # Generic sales_history
                transaction = TransactionEdge(
                    transaction_type="sale",
                    date=datetime.fromisoformat(sale_data.get('sale_date', '')) if sale_data.get('sale_date') else datetime.now(),
                    amount=float(sale_data.get('sale_amount', 0)) if sale_data.get('sale_amount') else None,
                    document_number=sale_data.get('doc_number', '')
                )
                parcel_id = sale_data.get('parcel_id', '')
            
            # Add transaction to graph
            if parcel_id:
                await self.graph_service.add_transaction(
                    from_owner=sale_data.get('seller', 'Unknown Seller'),
                    to_owner=sale_data.get('buyer', 'Unknown Buyer'),
                    parcel_id=parcel_id,
                    transaction=transaction
                )
                
                self.stats.migrated_transactions += 1
                
        except Exception as e:
            logger.warning(f"Failed to process sale: {e}")
            
    def _map_property_type(self, dor_code: Optional[str]) -> str:
        """Map DOR use code to property type"""
        
        if not dor_code:
            return "Unknown"
        
        # Simplified mapping - expand as needed
        residential_codes = ['01', '02', '03', '04', '05', '06', '07', '08', '09']
        commercial_codes = ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19']
        
        if dor_code[:2] in residential_codes:
            return "Residential"
        elif dor_code[:2] in commercial_codes:
            return "Commercial"
        else:
            return "Other"
            
    def _determine_entity_type(self, name: str) -> str:
        """Determine if owner is person or corporation"""
        
        name_upper = name.upper()
        
        # Corporate indicators
        corp_indicators = ['LLC', 'INC', 'CORP', 'LTD', 'LP', 'TRUST', 'ESTATE',
                          'PARTNERSHIP', 'COMPANY', 'HOLDINGS', 'INVESTMENTS']
        
        for indicator in corp_indicators:
            if indicator in name_upper:
                return "corporation"
        
        return "person"
        
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify migration results"""
        
        logger.info("Verifying migration...")
        
        verification = {
            "properties": {
                "source_count": self.stats.total_properties,
                "migrated_count": self.stats.migrated_properties,
                "failed_count": self.stats.failed_properties,
                "success_rate": (self.stats.migrated_properties / max(1, self.stats.total_properties)) * 100
            },
            "owners": {
                "migrated_count": self.stats.migrated_owners
            },
            "transactions": {
                "migrated_count": self.stats.migrated_transactions
            },
            "relationships": {
                "created_count": self.stats.total_relationships
            },
            "errors": len(self.stats.errors)
        }
        
        # Query graph for verification
        sample_results = await self.graph_service.search_properties(
            query="property",
            num_results=5
        )
        
        verification["sample_search_results"] = len(sample_results)
        
        return verification
        
    def save_migration_report(self, filename: str = "migration_report.json"):
        """Save migration report to file"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "properties": {
                    "total": self.stats.total_properties,
                    "migrated": self.stats.migrated_properties,
                    "failed": self.stats.failed_properties
                },
                "owners": {
                    "migrated": self.stats.migrated_owners
                },
                "transactions": {
                    "migrated": self.stats.migrated_transactions
                },
                "relationships": {
                    "created": self.stats.total_relationships
                }
            },
            "errors": self.stats.errors
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Migration report saved to {filename}")


async def main():
    """Main migration function"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        PROPERTY DATA MIGRATION TO GRAPHITI                ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    if not IMPORTS_AVAILABLE:
        logger.error("Required modules not available. Install dependencies first.")
        sys.exit(1)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Migrate property data to Graphiti")
    parser.add_argument('--limit', type=int, help='Limit number of properties to migrate')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for migration')
    parser.add_argument('--skip-properties', action='store_true', help='Skip property migration')
    parser.add_argument('--skip-sunbiz', action='store_true', help='Skip Sunbiz migration')
    parser.add_argument('--skip-sales', action='store_true', help='Skip sales history migration')
    
    args = parser.parse_args()
    
    try:
        # Initialize migrator
        migrator = PropertyDataMigrator(batch_size=args.batch_size)
        
        # Run migrations
        if not args.skip_properties:
            await migrator.migrate_properties(limit=args.limit)
        
        if not args.skip_sunbiz:
            await migrator.migrate_sunbiz_data()
        
        if not args.skip_sales:
            await migrator.migrate_sales_history()
        
        # Verify migration
        verification = await migrator.verify_migration()
        
        # Display results
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        
        print(f"\nProperties:")
        print(f"  Migrated: {migrator.stats.migrated_properties}/{migrator.stats.total_properties}")
        print(f"  Failed: {migrator.stats.failed_properties}")
        print(f"  Success Rate: {verification['properties']['success_rate']:.1f}%")
        
        print(f"\nOwners:")
        print(f"  Migrated: {migrator.stats.migrated_owners}")
        
        print(f"\nTransactions:")
        print(f"  Migrated: {migrator.stats.migrated_transactions}")
        
        print(f"\nRelationships:")
        print(f"  Created: {migrator.stats.total_relationships}")
        
        if migrator.stats.errors:
            print(f"\n⚠️ Errors encountered: {len(migrator.stats.errors)}")
            print("Check migration_report.json for details")
        
        # Save report
        migrator.save_migration_report()
        
        print("\n✅ Migration completed!")
        print("Access Neo4j Browser at http://localhost:7474 to explore the graph")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())