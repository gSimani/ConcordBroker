"""
OPTIMIZED Railway Production Indexer - MUCH FASTER
- Removes unnecessary rate limiting delays
- Parallel batch processing
- Better error handling
"""
import meilisearch
from supabase import create_client
from tqdm import tqdm
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Railway Production Configuration
MEILI_URL = 'https://meilisearch-concordbrokerproduction.up.railway.app'
MEILI_KEY = 'concordbroker-meili-railway-prod-key-2025'

# Supabase
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

INDEX_NAME = 'florida_properties'
BATCH_SIZE = 10000  # Fetch 10K at a time from Supabase
MEILI_BATCH_SIZE = 10000  # Send 10K at a time to Meilisearch
MAX_WORKERS = 4  # Parallel workers for Meilisearch indexing

# Target count
TARGET_COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 9113150

print("="*80)
print("OPTIMIZED RAILWAY PRODUCTION INDEXER")
print("="*80)
print(f"Meilisearch: {MEILI_URL}")
print(f"Target: {TARGET_COUNT:,} properties")
print(f"Batch Size: {BATCH_SIZE:,}")
print(f"Parallel Workers: {MAX_WORKERS}")
print(f"NO ARTIFICIAL DELAYS - Maximum speed!")
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
    sys.exit(1)

# Create/get index
print("Setting up index...")
try:
    index = meili.get_index(INDEX_NAME)
    current_docs = index.get_stats().number_of_documents
    print(f"Index exists with {current_docs:,} documents")
    # Clear existing for fresh start if requested
    if len(sys.argv) > 2 and sys.argv[2] == '--clear':
        print("Clearing existing index...")
        task = index.delete_all_documents()
        meili.wait_for_task(task.task_uid)
        print("Index cleared")
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

def transform_property(prop):
    """Transform a single property for Meilisearch"""
    # Clean parcel_id - Meilisearch only allows: a-z A-Z 0-9 - _
    parcel_id = re.sub(r'[^a-zA-Z0-9-]', '_', str(prop.get('parcel_id', '')))
    return {
        'parcel_id': parcel_id,
        'id': parcel_id,
        'original_parcel_id': str(prop.get('parcel_id', '')),
        'county': prop.get('county', ''),
        'phy_addr1': prop.get('phy_addr1', ''),
        'phy_city': prop.get('phy_city', ''),
        'owner_name': prop.get('owner_name', ''),
        'tot_lvg_area': prop.get('total_living_area'),
        'just_value': prop.get('just_value'),
        'year': prop.get('year', 2025),
    }

def index_batch(docs, batch_num):
    """Index a batch to Meilisearch"""
    try:
        meili_client = meilisearch.Client(MEILI_URL, MEILI_KEY)
        idx = meili_client.get_index(INDEX_NAME)
        task = idx.add_documents(docs)
        return len(docs), None
    except Exception as e:
        return 0, f"Batch {batch_num}: {str(e)}"

# Index data with parallel processing
print("Starting optimized indexing...")
print("Fetching from Supabase and indexing to Meilisearch in parallel...")
print()

num_batches = (TARGET_COUNT + BATCH_SIZE - 1) // BATCH_SIZE
pbar = tqdm(total=TARGET_COUNT, desc="Indexing", unit=" properties")

indexed = 0
errors = []
start_time = time.time()

# Use ThreadPoolExecutor for parallel indexing
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {}

    for batch_num in range(num_batches):
        offset = batch_num * BATCH_SIZE

        # Fetch batch from Supabase
        try:
            resp = supabase.table('florida_parcels')\
                .select('*')\
                .range(offset, offset + BATCH_SIZE - 1)\
                .execute()
        except Exception as e:
            errors.append(f"Fetch error at offset {offset}: {e}")
            continue

        if not resp.data:
            continue

        # Transform documents
        docs = [transform_property(prop) for prop in resp.data]

        # Submit indexing task to thread pool
        future = executor.submit(index_batch, docs, batch_num)
        futures[future] = len(docs)

        # Process completed futures
        for completed in list(futures.keys()):
            if completed.done():
                try:
                    count, error = completed.result()
                    if error:
                        errors.append(error)
                    else:
                        indexed += count
                        pbar.update(count)
                except Exception as e:
                    errors.append(f"Future error: {e}")
                finally:
                    del futures[completed]

    # Wait for remaining futures
    for future in as_completed(futures):
        try:
            count, error = future.result()
            if error:
                errors.append(error)
            else:
                indexed += count
                pbar.update(count)
        except Exception as e:
            errors.append(f"Future error: {e}")

pbar.close()

elapsed = time.time() - start_time
rate = indexed / elapsed if elapsed > 0 else 0

print()
print("="*80)
print("INDEXING COMPLETE")
print("="*80)
print(f"Documents indexed: {indexed:,}")
print(f"Time elapsed: {elapsed:.1f} seconds")
print(f"Average speed: {rate:.1f} properties/second")
print(f"Errors: {len(errors)}")
if errors:
    print("\nFirst 5 errors:")
    for err in errors[:5]:
        print(f"  - {err}")
print(f"Index name: {INDEX_NAME}")
print("="*80)
print()

# Test search
print("Testing search with tot_lvg_area filter (10000-20000)...")
try:
    results = index.search('', {'filter': 'tot_lvg_area >= 10000 AND tot_lvg_area <= 20000', 'limit': 5})
    print(f"Found {results.estimated_total_hits} hits")
    print()
    print("Sample properties:")
    for hit in results.hits[:5]:
        addr = hit.get('phy_addr1', 'No address')
        county = hit.get('county', 'Unknown')
        sqft = hit.get('tot_lvg_area', 0)
        pid = hit.get('original_parcel_id', hit.get('parcel_id'))
        print(f"  - {pid}: {addr}, {county} - {sqft:,} sqft")
except Exception as e:
    print(f"Search test failed: {e}")

print()
print("="*80)
print("RAILWAY PRODUCTION INDEX READY")
print(f"URL: {MEILI_URL}/indexes/{INDEX_NAME}/search")
print("="*80)
