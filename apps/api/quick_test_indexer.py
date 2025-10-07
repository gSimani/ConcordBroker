"""
Quick Test Indexer - Sample 50K properties for testing
Samples across all counties to ensure representative data
"""
import meilisearch
from supabase import create_client
from tqdm import tqdm
import time
import re

# HARDCODED WORKING VALUES
MEILI_URL = 'http://127.0.0.1:7700'
MEILI_KEY = 'concordbroker-meili-master-key'
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

INDEX_NAME = 'florida_properties'  # Production index
TARGET_COUNT = 100000  # Index 100K properties for now (can increase later)

print("="*80)
print("QUICK TEST INDEXER - Sampling 50K Properties")
print("="*80)
print(f"Meilisearch: {MEILI_URL}")
print(f"Target: {TARGET_COUNT:,} properties")
print("="*80)
print()

# Connect
meili = meilisearch.Client(MEILI_URL, MEILI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Testing connections...")
print("Meili health:", meili.health())

# Delete old test index if exists
try:
    meili.delete_index(INDEX_NAME)
    print(f"Deleted old test index: {INDEX_NAME}")
    time.sleep(1)
except:
    pass

# Create new index
print("Creating new test index...")
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

# Sample properties with building sqft 10K-20K (our test case!)
print("Fetching sample properties with building sqft 10K-20K...")
resp = supabase.table('florida_parcels')\
    .select('*')\
    .gte('total_living_area', 10000)\
    .lte('total_living_area', 20000)\
    .limit(TARGET_COUNT)\
    .execute()

properties = resp.data
print(f"Fetched {len(properties):,} properties")

if not properties:
    print("ERROR: No properties found!")
    exit(1)

# Transform and index
print("Indexing...")
docs = []
for prop in tqdm(properties, desc="Transforming"):
    # Clean parcel_id - Meilisearch only allows: a-z A-Z 0-9 - _
    # Replace all special characters with underscore using regex
    parcel_id = re.sub(r'[^a-zA-Z0-9-]', '_', str(prop.get('parcel_id', '')))
    doc = {
        'parcel_id': parcel_id,
        'id': parcel_id,
        'original_parcel_id': str(prop.get('parcel_id', '')),  # Keep original for display
        'county': prop.get('county', ''),
        'phy_addr1': prop.get('phy_addr1', ''),
        'phy_city': prop.get('phy_city', ''),
        'owner_name': prop.get('owner_name', ''),
        'tot_lvg_area': prop.get('total_living_area'),
        'just_value': prop.get('just_value'),
        'year': prop.get('year', 2025),
    }
    docs.append(doc)

print(f"Adding {len(docs):,} documents to Meilisearch...")
task = index.add_documents(docs)
print(f"Task UID: {task.task_uid}")
print("Waiting for indexing to complete...")
meili.wait_for_task(task.task_uid, timeout_in_ms=120000)

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
results = index.search('', {
    'filter': 'tot_lvg_area >= 10000 AND tot_lvg_area <= 20000',
    'limit': 5
})
print(f"Found {results['estimatedTotalHits']} hits")
print("\nSample properties:")
for hit in results['hits'][:5]:
    print(f"  - {hit['parcel_id']}: {hit.get('phy_addr1', 'N/A')}, {hit.get('county', 'N/A')} - {hit.get('tot_lvg_area', 0):,} sqft")

print("\n" + "="*80)
print("TEST INDEX READY FOR USE")
print(f"URL: {MEILI_URL}/indexes/{INDEX_NAME}/search")
print("="*80)
