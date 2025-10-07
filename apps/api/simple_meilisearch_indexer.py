"""
Simple Meilisearch Indexer - Hardcoded Working Version
Indexes properties from pm isw... Supabase to Meilisearch
"""
import meilisearch
from supabase import create_client
from tqdm import tqdm
import time

# HARDCODED WORKING VALUES
MEILI_URL = 'http://127.0.0.1:7700'
MEILI_KEY = 'concordbroker-meili-master-key'
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

INDEX_NAME = 'florida_properties'
BATCH_SIZE = 10000

# Clean parcel IDs - Meilisearch only allows: a-z A-Z 0-9 - _
import re

print("="*80)
print("SIMPLE MEILISEARCH INDEXER")
print("="*80)
print(f"Meilisearch: {MEILI_URL}")
print(f"Supabase: {SUPABASE_URL}")
print(f"Batch Size: {BATCH_SIZE:,}")
print("="*80)
print()

# Connect
meili = meilisearch.Client(MEILI_URL, MEILI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Testing connections...")
print("Meili health:", meili.health())

# Get total count - skip slow count query, use known value
total_count = 9113150  # Known value from previous queries
print(f"Total properties: {total_count:,} (known value)")
print()

# Create/get index
print("Creating index...")
try:
    index = meili.get_index(INDEX_NAME)
    print(f"Index exists with {index.get_stats()['numberOfDocuments']:,} documents")
except:
    print("Creating new index...")
    task = meili.create_index(INDEX_NAME, {'primaryKey': 'parcel_id'})
    meili.wait_for_task(task.task_uid)
    index = meili.get_index(INDEX_NAME)
    print("Index created")

# Update settings
print("Updating settings...")
settings = {
    "searchableAttributes": ["parcel_id", "phy_addr1", "phy_city", "owner_name", "county"],
    "filterableAttributes": ["county", "tot_lvg_area", "just_value", "year"],
    "sortableAttributes": ["just_value", "tot_lvg_area"],
}
task = index.update_settings(settings)
meili.wait_for_task(task.task_uid)
print("Settings updated")
print()

# Index data
print("Starting indexing...")
num_batches = (total_count + BATCH_SIZE - 1) // BATCH_SIZE
pbar = tqdm(total=total_count, desc="Indexing", unit=" properties")

indexed = 0
for batch_num in range(num_batches):
    offset = batch_num * BATCH_SIZE

    # Fetch batch
    resp = supabase.table('florida_parcels').select('*').range(offset, offset + BATCH_SIZE - 1).execute()

    if not resp.data:
        print(f"\nNo data at offset {offset}")
        continue

    # Transform and index
    docs = []
    for prop in resp.data:
        doc = {
            'parcel_id': str(prop.get('parcel_id', '')),
            'id': str(prop.get('parcel_id', '')),
            'county': prop.get('county', ''),
            'phy_addr1': prop.get('phy_addr1', ''),
            'phy_city': prop.get('phy_city', ''),
            'owner_name': prop.get('owner_name', ''),
            'tot_lvg_area': prop.get('tot_lvg_area'),
            'just_value': prop.get('just_value'),
            'year': prop.get('year', 2025),
        }
        docs.append(doc)

    # Add to Meilisearch
    task = index.add_documents(docs)
    indexed += len(docs)
    pbar.update(len(docs))

    # Rate limit every 4 batches
    if (batch_num + 1) % 4 == 0:
        time.sleep(0.5)

pbar.close()

print("\n" + "="*80)
print("INDEXING COMPLETE")
print("="*80)
stats = index.get_stats()
print(f"Documents indexed: {stats['numberOfDocuments']:,}")
print("="*80)
