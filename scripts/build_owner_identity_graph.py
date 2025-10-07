"""
Owner Identity Resolution for ConcordBroker
Purpose: Match property owners to Sunbiz entities and create identity clusters

Algorithm:
1. Extract unique owner names from florida_parcels
2. Extract entity names from florida_entities
3. Fuzzy match owners to entities (85%+ confidence)
4. Build identity graph using networkx
5. Find connected components (identity clusters)
6. Create canonical identities in owner_identities table
7. Link properties via property_ownership table
8. Link entities via entity_principals table
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from fuzzywuzzy import fuzz
import networkx as nx
from collections import defaultdict
import re
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from .env.mcp
env_path = Path(__file__).parent.parent / '.env.mcp'
load_dotenv(env_path, override=True)

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://pmispwtdngkcmsrsjwbp.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_KEY:
    print("❌ Error: SUPABASE_SERVICE_ROLE_KEY environment variable not set")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# CONFIGURATION
# ============================================================================

FUZZY_MATCH_THRESHOLD = 85  # Minimum similarity score (0-100)
BATCH_SIZE = 1000
MAX_OWNERS_TO_PROCESS = 50000  # Start with subset for testing

# ============================================================================
# NAME NORMALIZATION
# ============================================================================

def normalize_name(name: str) -> str:
    """Normalize name for better matching"""
    if not name:
        return ""

    # Convert to uppercase
    name = name.upper()

    # Remove common suffixes
    suffixes = [
        'LLC', 'L.L.C', 'INC', 'CORP', 'CORPORATION', 'LTD', 'LIMITED',
        'TRUST', 'TRUSTEE', 'ESTATE', 'CO', 'COMPANY', 'GROUP',
        'PROPERTIES', 'INVESTMENTS', 'HOLDINGS', 'PARTNERS', 'PARTNERSHIP'
    ]

    for suffix in suffixes:
        # Remove as whole word
        name = re.sub(rf'\b{suffix}\b\.?', '', name)

    # Remove punctuation except spaces
    name = re.sub(r'[^\w\s]', ' ', name)

    # Normalize whitespace
    name = ' '.join(name.split())

    return name.strip()

def extract_person_name(name: str) -> tuple:
    """
    Extract first and last name from various formats
    Returns: (first_name, last_name) or (None, None)
    """
    if not name:
        return (None, None)

    # Common patterns
    patterns = [
        r'(\w+),\s*(\w+)',  # "Smith, John"
        r'(\w+)\s+(\w+)',   # "John Smith"
    ]

    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            if ',' in name:
                # Last, First format
                return (match.group(2), match.group(1))
            else:
                # First Last format
                return (match.group(1), match.group(2))

    return (None, None)

# ============================================================================
# IDENTITY MATCHING
# ============================================================================

def fuzzy_match_names(name1: str, name2: str) -> int:
    """Calculate fuzzy similarity score between two names"""
    if not name1 or not name2:
        return 0

    # Normalize both names
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)

    if not norm1 or not norm2:
        return 0

    # Calculate multiple similarity scores
    ratio = fuzz.ratio(norm1, norm2)
    partial = fuzz.partial_ratio(norm1, norm2)
    token_sort = fuzz.token_sort_ratio(norm1, norm2)

    # Return highest score
    return max(ratio, partial, token_sort)

def match_owners_to_entities(limit=MAX_OWNERS_TO_PROCESS):
    """
    Match property owner names to Sunbiz entity names

    Returns: List of match dictionaries
    """
    print(f"\n📊 Step 1: Extracting owner names from florida_parcels (limit: {limit})...")

    # Get unique owner names
    owners_result = supabase.table('florida_parcels')\
        .select('owner_name, county')\
        .not_.is_('owner_name', 'null')\
        .limit(limit)\
        .execute()

    owners = owners_result.data
    unique_owners = {}  # owner_name -> [counties]

    for row in owners:
        name = row['owner_name']
        county = row['county']
        if name:
            if name not in unique_owners:
                unique_owners[name] = []
            if county not in unique_owners[name]:
                unique_owners[name].append(county)

    print(f"   Found {len(unique_owners)} unique owner names")

    print("\n📊 Step 2: Extracting entity names from sunbiz_corporate...")

    # Get entity names from Sunbiz (sample for testing)
    entities_result = supabase.table('sunbiz_corporate')\
        .select('doc_number, entity_name')\
        .not_.is_('entity_name', 'null')\
        .limit(50000)\
        .execute()

    entities = entities_result.data
    # Map to expected format
    entities = [{'entity_id': e['doc_number'], 'entity_name': e['entity_name'].strip()} for e in entities]
    print(f"   Found {len(entities)} entities")

    print(f"\n🔍 Step 3: Fuzzy matching owners to entities (threshold: {FUZZY_MATCH_THRESHOLD})...")

    matches = []
    processed = 0

    for owner_name in list(unique_owners.keys())[:10000]:  # Start with 10K for testing
        processed += 1
        if processed % 100 == 0:
            print(f"   Processed {processed} owners, found {len(matches)} matches...")

        # Match against entities
        for entity in entities:
            score = fuzzy_match_names(owner_name, entity['entity_name'])

            if score >= FUZZY_MATCH_THRESHOLD:
                matches.append({
                    'owner_name': owner_name,
                    'entity_id': entity['entity_id'],
                    'entity_name': entity['entity_name'],
                    'confidence': score / 100.0,
                    'counties': unique_owners[owner_name]
                })

    print(f"\n   ✅ Found {len(matches)} high-confidence matches")
    return matches

# ============================================================================
# IDENTITY GRAPH CONSTRUCTION
# ============================================================================

def build_identity_graph(matches):
    """
    Build identity graph from matches
    Returns: networkx.Graph with owner names and entity IDs as nodes
    """
    print("\n🕸️  Step 4: Building identity graph...")

    G = nx.Graph()

    for match in matches:
        # Add edge between owner name and entity ID
        G.add_edge(
            f"OWNER:{match['owner_name']}",
            f"ENTITY:{match['entity_id']}",
            confidence=match['confidence'],
            entity_name=match['entity_name']
        )

    print(f"   Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    # Find connected components (identity clusters)
    clusters = list(nx.connected_components(G))
    print(f"   Found {len(clusters)} identity clusters")

    return G, clusters

def select_canonical_name(cluster, G):
    """
    Select the most representative name from a cluster

    Priority:
    1. Most common owner name
    2. Shortest clean name
    3. Alphabetically first
    """
    owner_nodes = [n for n in cluster if n.startswith('OWNER:')]
    entity_nodes = [n for n in cluster if n.startswith('ENTITY:')]

    if not owner_nodes and not entity_nodes:
        return None

    # Prefer owner names over entity names
    if owner_nodes:
        # Remove "OWNER:" prefix
        names = [n.replace('OWNER:', '') for n in owner_nodes]
        # Sort by length (shorter is cleaner) then alphabetically
        names.sort(key=lambda x: (len(x), x))
        return names[0]
    else:
        # Fall back to entity name
        entity_id = entity_nodes[0].replace('ENTITY:', '')
        # Get entity name from graph edge
        for neighbor in G.neighbors(entity_nodes[0]):
            edge_data = G.get_edge_data(entity_nodes[0], neighbor)
            if 'entity_name' in edge_data:
                return edge_data['entity_name']
        return entity_id

# ============================================================================
# DATABASE POPULATION
# ============================================================================

def populate_owner_identities(clusters, G, matches):
    """Create owner_identities records from clusters"""
    print("\n💾 Step 5: Populating owner_identities table...")

    identities_created = 0

    for cluster in clusters:
        # Select canonical name
        canonical = select_canonical_name(cluster, G)
        if not canonical:
            continue

        # Extract all variant names
        owner_nodes = [n.replace('OWNER:', '') for n in cluster if n.startswith('OWNER:')]
        entity_nodes = [n.replace('ENTITY:', '') for n in cluster if n.startswith('ENTITY:')]

        variant_names = [n for n in owner_nodes if n != canonical]

        # Determine identity type
        identity_type = 'person'
        if any(keyword in canonical.upper() for keyword in ['LLC', 'INC', 'CORP', 'TRUST']):
            identity_type = 'company'

        # Calculate cluster confidence (average of all matches in cluster)
        cluster_matches = [m for m in matches if m['owner_name'] in owner_nodes or m['entity_id'] in [n.replace('ENTITY:', '') for n in entity_nodes]]
        avg_confidence = sum(m['confidence'] for m in cluster_matches) / len(cluster_matches) if cluster_matches else 0.8

        # Insert owner identity
        try:
            result = supabase.table('owner_identities').insert({
                'canonical_name': canonical,
                'variant_names': variant_names,
                'identity_type': identity_type,
                'confidence_score': round(avg_confidence, 2)
            }).execute()

            if result.data:
                owner_identity_id = result.data[0]['id']
                identities_created += 1

                # Link properties
                populate_property_ownership(owner_identity_id, owner_nodes, entity_nodes)

                # Link entities
                populate_entity_principals(owner_identity_id, entity_nodes, matches)

        except Exception as e:
            print(f"   ⚠️  Error creating identity for {canonical}: {e}")
            continue

    print(f"   ✅ Created {identities_created} owner identities")

def populate_property_ownership(owner_identity_id, owner_names, entity_ids):
    """Link properties to owner identity"""
    # Get properties for these owner names
    for owner_name in owner_names:
        try:
            properties = supabase.table('florida_parcels')\
                .select('parcel_id, county, owner_name')\
                .eq('owner_name', owner_name)\
                .limit(100)\
                .execute()

            for prop in properties.data:
                # Determine if owned via entity
                entity_id = None
                entity_name = None
                ownership_type = 'individual'

                # Check if this owner name matches an entity
                for ent_id in [e.replace('ENTITY:', '') for e in entity_ids]:
                    entity_result = supabase.table('sunbiz_corporate')\
                        .select('entity_name')\
                        .eq('doc_number', ent_id)\
                        .limit(1)\
                        .execute()

                    if entity_result.data:
                        entity_name = entity_result.data[0]['entity_name'].strip()
                        if fuzzy_match_names(owner_name, entity_name) > 85:
                            entity_id = ent_id
                            ownership_type = 'corporation'
                            break

                # Map county name to code for property_ownership table
                county_map = {
                    'ALACHUA': 1, 'BAKER': 2, 'BAY': 3, 'BRADFORD': 4, 'BREVARD': 5,
                    'BROWARD': 6, 'CALHOUN': 7, 'CHARLOTTE': 8, 'CITRUS': 9, 'CLAY': 10,
                    'COLLIER': 11, 'COLUMBIA': 12, 'MIAMI-DADE': 13, 'DESOTO': 14, 'DIXIE': 15,
                    'DUVAL': 16, 'ESCAMBIA': 17, 'FLAGLER': 18, 'FRANKLIN': 19, 'GADSDEN': 20,
                    'GILCHRIST': 21, 'GLADES': 22, 'GULF': 23, 'HAMILTON': 24, 'HARDEE': 25,
                    'HENDRY': 26, 'HERNANDO': 27, 'HIGHLANDS': 28, 'HILLSBOROUGH': 29, 'HOLMES': 30,
                    'INDIAN RIVER': 31, 'JACKSON': 32, 'JEFFERSON': 33, 'LAFAYETTE': 34, 'LAKE': 35,
                    'LEE': 36, 'LEON': 37, 'LEVY': 38, 'LIBERTY': 39, 'MADISON': 40,
                    'MANATEE': 41, 'MARION': 42, 'MARTIN': 43, 'MONROE': 44, 'NASSAU': 45,
                    'OKALOOSA': 46, 'OKEECHOBEE': 47, 'ORANGE': 48, 'OSCEOLA': 49, 'PALM BEACH': 50,
                    'PASCO': 51, 'PINELLAS': 52, 'POLK': 53, 'PUTNAM': 54, 'ST. JOHNS': 55,
                    'ST. LUCIE': 56, 'SANTA ROSA': 57, 'SARASOTA': 58, 'SEMINOLE': 59, 'SUMTER': 60,
                    'SUWANNEE': 61, 'TAYLOR': 62, 'UNION': 63, 'VOLUSIA': 64, 'WAKULLA': 65,
                    'WALTON': 66, 'WASHINGTON': 67
                }
                county_code = county_map.get(prop['county'], 0)

                # Insert property ownership record
                supabase.table('property_ownership').insert({
                    'parcel_id': prop['parcel_id'],
                    'county_code': county_code,
                    'owner_identity_id': owner_identity_id,
                    'ownership_type': ownership_type,
                    'entity_id': entity_id,
                    'entity_name': entity_name if entity_name else prop['owner_name']
                }).execute()

        except Exception as e:
            print(f"   ⚠️  Error linking properties for {owner_name}: {e}")
            continue

def populate_entity_principals(owner_identity_id, entity_ids, matches):
    """Link Sunbiz entities to owner identity"""
    for entity_node in entity_ids:
        entity_id = entity_node.replace('ENTITY:', '')

        # Get entity details
        try:
            entity_result = supabase.table('sunbiz_corporate')\
                .select('entity_name')\
                .eq('doc_number', entity_id)\
                .limit(1)\
                .execute()

            if not entity_result.data:
                continue

            entity_name = entity_result.data[0]['entity_name'].strip()

            # Insert entity principal record
            supabase.table('entity_principals').insert({
                'entity_id': entity_id,
                'entity_name': entity_name,
                'owner_identity_id': owner_identity_id,
                'principal_name': entity_name,  # Will be enhanced with officer data later
                'role': 'owner'
            }).execute()

        except Exception as e:
            print(f"   ⚠️  Error linking entity {entity_id}: {e}")
            continue

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("="*80)
    print("CONCORDBROKER OWNER IDENTITY RESOLUTION")
    print("="*80)

    start_time = datetime.now()

    try:
        # Step 1-2: Extract and match
        matches = match_owners_to_entities(limit=MAX_OWNERS_TO_PROCESS)

        if not matches:
            print("\n❌ No matches found. Try lowering FUZZY_MATCH_THRESHOLD or increasing limits.")
            return

        # Step 3-4: Build graph
        G, clusters = build_identity_graph(matches)

        # Step 5: Populate database
        populate_owner_identities(clusters, G, matches)

        # Step 6: Refresh stats
        print("\n🔄 Step 6: Refreshing owner statistics...")
        supabase.rpc('refresh_owner_stats', {}).execute()

        # Summary
        duration = (datetime.now() - start_time).total_seconds()

        print("\n" + "="*80)
        print("✅ IDENTITY RESOLUTION COMPLETE")
        print("="*80)
        print(f"Duration: {duration:.1f} seconds")
        print(f"Matches found: {len(matches)}")
        print(f"Identity clusters: {len(clusters)}")
        print("\nNext steps:")
        print("1. Query owner_portfolio_summary to see aggregated portfolios")
        print("2. Test with: SELECT * FROM get_owner_portfolio('<owner_id>');")
        print("3. Run full resolution with higher limits for production")

    except Exception as e:
        print(f"\n❌ Error during identity resolution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
