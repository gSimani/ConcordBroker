"""
Meilisearch Index Builder for Florida Properties
Syncs 9.7M properties from Supabase to Meilisearch for instant search
"""
import sys
import asyncio
import meilisearch
from supabase import create_client, Client
from typing import List, Dict, Any
from tqdm import tqdm
import time
from datetime import datetime
import os

# Add parent directory to path for imports
if '__file__' in globals():
    sys.path.append(os.path.dirname(__file__))
else:
    sys.path.append(os.getcwd())

from search_config import (
    MEILISEARCH_URL,
    MEILISEARCH_KEY,
    PROPERTIES_INDEX,
    MEILISEARCH_SETTINGS,
    BATCH_SIZE,
    MAX_CONCURRENT_BATCHES
)

# Supabase connection
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

class MeilisearchIndexer:
    def __init__(self):
        self.meili_client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.index = None

    def create_index(self):
        """Create or get Meilisearch index"""
        print(f" Creating/Getting index: {PROPERTIES_INDEX}")

        try:
            self.index = self.meili_client.get_index(PROPERTIES_INDEX)
            print(f"[OK] Index exists with {self.index.get_stats()['numberOfDocuments']:,} documents")
        except:
            print(" Index doesn't exist, creating...")
            task = self.meili_client.create_index(
                PROPERTIES_INDEX,
                {'primaryKey': 'parcel_id'}
            )
            self.meili_client.wait_for_task(task['taskUid'])
            self.index = self.meili_client.get_index(PROPERTIES_INDEX)
            print(" Index created")

        # Update settings
        print("  Updating index settings...")
        task = self.index.update_settings(MEILISEARCH_SETTINGS)
        self.meili_client.wait_for_task(task['taskUid'])
        print(" Settings updated")

    def transform_property(self, prop: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Supabase property to Meilisearch document"""
        return {
            # IDs
            'parcel_id': str(prop.get('parcel_id', '')),
            'id': str(prop.get('parcel_id', '')),

            # Location
            'address': prop.get('phy_addr1', ''),
            'phy_addr1': prop.get('phy_addr1', ''),
            'city': prop.get('phy_city', ''),
            'phy_city': prop.get('phy_city', ''),
            'county': prop.get('county_name', '') or prop.get('county', ''),
            'zipCode': prop.get('phy_zipcd', ''),
            'state': 'FL',
            'latitude': prop.get('latitude'),
            'longitude': prop.get('longitude'),

            # Owner
            'owner': prop.get('owner_name', '') or prop.get('own_name', ''),
            'owner_name': prop.get('owner_name', '') or prop.get('own_name', ''),
            'ownerAddress': prop.get('owner_addr1', '') or prop.get('own_addr1', ''),

            # Property characteristics
            'propertyType': prop.get('property_type', 'Residential'),
            'landUseCode': prop.get('property_use', '') or prop.get('land_use_code', ''),
            'yearBuilt': prop.get('act_yr_blt') or prop.get('year_built'),
            'bedrooms': prop.get('bedrooms'),
            'bathrooms': prop.get('bathrooms'),

            # Size
            'buildingSqFt': prop.get('tot_lvg_area') or prop.get('total_living_area') or 0,
            'landSqFt': prop.get('lnd_sqfoot') or prop.get('land_sqft') or 0,

            # Financial
            'marketValue': float(prop.get('jv', 0) or prop.get('just_value', 0) or 0),
            'assessedValue': float(prop.get('assessed_value', 0) or 0),
            'taxAmount': float(prop.get('tax_amount', 0) or 0),
            'taxableValue': float(prop.get('tv_sd', 0) or 0),

            # Sales
            'lastSalePrice': prop.get('sale_prc1'),
            'lastSaleDate': prop.get('sale_date'),

            # Investment metrics
            'investmentScore': prop.get('investment_score', 50),
            'capRate': prop.get('cap_rate'),
            'pricePerSqFt': prop.get('price_per_sqft'),

            # Flags
            'isTaxDelinquent': prop.get('is_tax_delinquent', False),
            'hasHomestead': prop.get('has_homestead', False),
            'isDistressed': prop.get('is_distressed', False)
        }

    def fetch_properties_batch(self, offset: int, limit: int) -> List[Dict]:
        """Fetch a batch of properties from Supabase"""
        try:
            response = self.supabase.table('florida_parcels')\
                .select('*')\
                .range(offset, offset + limit - 1)\
                .execute()

            return response.data
        except Exception as e:
            print(f" Error fetching batch at offset {offset}: {e}")
            return []

    def get_total_properties(self) -> int:
        """Get total count of properties in Supabase"""
        try:
            # Use a count query with limit
            response = self.supabase.table('florida_parcels')\
                .select('parcel_id', count='exact')\
                .limit(1)\
                .execute()

            if hasattr(response, 'count') and response.count is not None:
                return response.count

            # Fallback: we know there are ~9.1M
            return 9113150
        except Exception as e:
            print(f"  Could not get exact count: {e}")
            return 9113150

    async def index_batch(self, documents: List[Dict], batch_num: int):
        """Index a batch of documents"""
        if not documents:
            return

        try:
            task = self.index.add_documents(documents)
            # Note: We don't wait for each batch to complete
            # Meilisearch processes them asynchronously
            return task['taskUid']
        except Exception as e:
            print(f"\n Error indexing batch {batch_num}: {e}")
            return None

    def index_all_properties(self):
        """Main indexing function - sync all properties from Supabase to Meilisearch"""
        start_time = time.time()

        # Get total count
        total_properties = self.get_total_properties()
        print(f"\n Total properties to index: {total_properties:,}")

        # Calculate batches
        num_batches = (total_properties + BATCH_SIZE - 1) // BATCH_SIZE
        print(f" Batches: {num_batches} (size: {BATCH_SIZE:,})")
        print(f" Max concurrent: {MAX_CONCURRENT_BATCHES}")
        print()

        indexed_count = 0
        failed_batches = []
        task_uids = []

        # Progress bar
        pbar = tqdm(total=total_properties, desc="Indexing", unit=" properties")

        for batch_num in range(num_batches):
            offset = batch_num * BATCH_SIZE

            # Fetch batch from Supabase
            raw_properties = self.fetch_properties_batch(offset, BATCH_SIZE)

            if not raw_properties:
                print(f"\n  No data for batch {batch_num + 1}/{num_batches}")
                failed_batches.append(batch_num)
                continue

            # Transform properties
            documents = [self.transform_property(prop) for prop in raw_properties]

            # Index batch
            task_uid = asyncio.run(self.index_batch(documents, batch_num + 1))

            if task_uid:
                task_uids.append(task_uid)
                indexed_count += len(documents)
                pbar.update(len(documents))
            else:
                failed_batches.append(batch_num)

            # Rate limiting: wait a bit every few batches
            if (batch_num + 1) % MAX_CONCURRENT_BATCHES == 0:
                time.sleep(0.5)  # Let Meilisearch breathe

        pbar.close()

        # Wait for all tasks to complete
        print(f"\n Waiting for Meilisearch to finish indexing...")
        print(f"   {len(task_uids)} tasks in queue")

        # Check last few tasks to ensure completion
        if task_uids:
            for task_uid in task_uids[-5:]:  # Check last 5 tasks
                try:
                    self.meili_client.wait_for_task(task_uid, timeout_in_ms=120000)
                except:
                    pass

        # Final stats
        elapsed = time.time() - start_time
        stats = self.index.get_stats()

        print(f"\n{'='*80}")
        print(f" INDEXING COMPLETE")
        print(f"{'='*80}")
        print(f" Documents indexed: {stats['numberOfDocuments']:,}")
        print(f"  Time elapsed: {elapsed/60:.1f} minutes")
        print(f" Speed: {indexed_count/elapsed:.0f} docs/second")

        if failed_batches:
            print(f"  Failed batches: {len(failed_batches)} - {failed_batches[:5]}")

        print(f"{'='*80}")

        return {
            'success': True,
            'indexed': stats['numberOfDocuments'],
            'elapsed': elapsed,
            'failed_batches': failed_batches
        }

    def delete_index(self):
        """Delete the index (use with caution!)"""
        print(f"  Deleting index: {PROPERTIES_INDEX}")
        try:
            task = self.meili_client.delete_index(PROPERTIES_INDEX)
            self.meili_client.wait_for_task(task['taskUid'])
            print(" Index deleted")
        except Exception as e:
            print(f" Error deleting index: {e}")

def main():
    """Main entry point"""
    print(f"""
{'='*80}
MEILISEARCH PROPERTY INDEXER
{'='*80}
Meilisearch URL: {MEILISEARCH_URL}
Index Name: {PROPERTIES_INDEX}
Supabase: {SUPABASE_URL}
Batch Size: {BATCH_SIZE:,}
{'='*80}
""")

    indexer = MeilisearchIndexer()

    # Create/update index
    indexer.create_index()

    # Index all properties
    result = indexer.index_all_properties()

    print(f"\nIndexing complete!")
    print(f"Test search at: {MEILISEARCH_URL}/indexes/{PROPERTIES_INDEX}/search")

if __name__ == "__main__":
    main()
