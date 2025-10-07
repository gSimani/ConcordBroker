"""
Railway Production Indexer - Index properties to Railway-hosted Meilisearch
Run this AFTER deploying Meilisearch to Railway
"""
import meilisearch
from supabase import create_client
from tqdm import tqdm
import time
import re
import sys

# Railway Production Configuration
# UPDATE THESE AFTER DEPLOYMENT:
MEILI_URL = 'https://meilisearch-concordbrokerproduction.up.railway.app'  # Replace with actual Railway URL
MEILI_KEY = 'concordbroker-meili-railway-prod-key-2025'  # Same key set in Railway env vars

# Supabase (stays the same)
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

INDEX_NAME = 'florida_properties'
BATCH_SIZE = 10000

# How many properties to index? Options:
# - 100000: Quick start (100K properties)
# - 500000: Medium dataset (500K properties)
# - 9113150: Full dataset (all 9.7M properties - takes 1-2 hours)
TARGET_COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 100000

print("="*80)
print("RAILWAY PRODUCTION INDEXER")
print("="*80)
print(f"Meilisearch: {MEILI_URL}")
print(f"Target: {TARGET_COUNT:,} properties")
print(f"Batch Size: {BATCH_SIZE:,}")
print("="*80)
print()

# Connect
print("Connecting to services...")
meili = meilisearch.Client(MEILI_URL, MEILI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Testing connections...")
try:
    health = meili.health()
    print(f"Meilisearch health: {health}")
except Exception as e:
    print(f"ERROR: Cannot connect to Meilisearch: {e}")
    print("Did you update MEILI_URL with your actual Railway URL?")
    sys.exit(1)

# Create/get index
print("Setting up index...")
try:
    index = meili.get_index(INDEX_NAME)
    current_docs = index.get_stats().number_of_documents
    print(f"Index exists with {current_docs:,} documents")
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
    "typoTolerance": {
        "enabled": True,
        "minWordSizeForTypos": {"oneTypo": 4, "twoTypos": 8}
    },
    "pagination": {
        "maxTotalHits": 10000
    }
}
task = index.update_settings(settings)
meili.wait_for_task(task.task_uid)
print("Settings updated")
print()

# Index data
print("Starting indexing...")
num_batches = (TARGET_COUNT + BATCH_SIZE - 1) // BATCH_SIZE
pbar = tqdm(total=TARGET_COUNT, desc="Indexing", unit=" properties")

indexed = 0
for batch_num in range(num_batches):
    offset = batch_num * BATCH_SIZE

    # Fetch batch
    try:
        resp = supabase.table('florida_parcels')\
            .select('*')\
            .range(offset, offset + BATCH_SIZE - 1)\
            .execute()
    except Exception as e:
        print(f"\nError fetching batch at offset {offset}: {e}")
        continue

    if not resp.data:
        print(f"\nNo data at offset {offset}")
        continue

    # Transform and index
    docs = []
    for prop in resp.data:
        # Clean parcel_id - Meilisearch only allows: a-z A-Z 0-9 - _
        parcel_id = re.sub(r'[^a-zA-Z0-9-]', '_', str(prop.get('parcel_id', '')))
        doc = {
            'parcel_id': parcel_id,
            'id': parcel_id,
            'original_parcel_id': str(prop.get('parcel_id', '')),  # Keep original for display
            'county': prop.get('county', ''),
            'phy_addr1': prop.get('phy_addr1', ''),
            'phy_city': prop.get('phy_city', ''),
            'owner_name': prop.get('owner_name', ''),
            'tot_lvg_area': prop.get('total_living_area'),  # Note: column is total_living_area
            'just_value': prop.get('just_value'),
            'year': prop.get('year', 2025),
        }
        docs.append(doc)

    # Add to Meilisearch
    try:
        task = index.add_documents(docs)
        indexed += len(docs)
        pbar.update(len(docs))
    except Exception as e:
        print(f"\nError indexing batch {batch_num}: {e}")
        continue

    # Rate limit every 4 batches to avoid overwhelming Railway
    if (batch_num + 1) % 4 == 0:
        time.sleep(0.5)

pbar.close()

print("\n" + "="*80)
print("INDEXING COMPLETE")
print("="*80)
stats = index.get_stats()
print(f"Documents indexed: {stats.number_of_documents:,}")
print(f"Index name: {INDEX_NAME}")
print("="*80)
print()

# Test search
print("Testing search with tot_lvg_area filter (10000-20000)...")
try:
    results = index.search('', {
        'filter': 'tot_lvg_area >= 10000 AND tot_lvg_area <= 20000',
        'limit': 5
    })
    print(f"Found {results['estimatedTotalHits']} hits")
    print("\nSample properties:")
    for hit in results['hits'][:5]:
        print(f"  - {hit['original_parcel_id']}: {hit.get('phy_addr1', 'N/A')}, {hit.get('county', 'N/A')} - {hit.get('tot_lvg_area', 0):,} sqft")
except Exception as e:
    print(f"Error testing search: {e}")

print("\n" + "="*80)
print("RAILWAY PRODUCTION INDEX READY")
print(f"URL: {MEILI_URL}/indexes/{INDEX_NAME}/search")
print("="*80)
