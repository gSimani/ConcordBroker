# Graphiti Integration Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Graphiti and required packages
pip install graphiti-core neo4j python-dotenv

# Or use the requirements file
pip install -r requirements-graphiti.txt
```

### 2. Set Up Neo4j Database

#### Option A: Docker (Recommended)
```bash
# Pull and run Neo4j container
docker run -d \
    --name concordbroker-neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/ConcordBroker2024! \
    -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
    -v $PWD/neo4j/data:/data \
    -v $PWD/neo4j/logs:/logs \
    neo4j:5-enterprise
```

#### Option B: Neo4j Desktop
1. Download [Neo4j Desktop](https://neo4j.com/download/)
2. Create new project "ConcordBroker"
3. Create database with password
4. Install APOC and GDS plugins

#### Option C: Neo4j AuraDB (Cloud)
1. Sign up at [Neo4j Aura](https://neo4j.com/cloud/aura/)
2. Create free instance
3. Save connection URI and credentials

### 3. Configure Environment Variables

Add to `.env` file:
```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ConcordBroker2024!

# Graphiti Configuration
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_EMBEDDING_MODEL=text-embedding-3-small
GRAPHITI_RERANK_MODEL=gpt-4o-mini

# Enable Graphiti Integration
ENABLE_GRAPHITI=true
GRAPHITI_AUTO_INDEX=true
GRAPHITI_CACHE_TTL=3600
```

### 4. Initialize Graphiti Integration

```python
# Run initialization script
python -m apps.api.graph.init_graphiti
```

Or manually:

```python
from apps.api.graph.property_graph_service import PropertyGraphService
from apps.api.graph.enhanced_rag_service import EnhancedRAGService

# Initialize services
graph_service = PropertyGraphService()
rag_service = EnhancedRAGService(graph_service)

# Test connection
await graph_service.graphiti.build_indices()
print("Graphiti initialized successfully!")
```

## 📊 Data Migration

### Migrate Existing Property Data

```python
from apps.api.graph.migrate_to_graph import migrate_properties

# Migrate from Supabase to Graph
async def migrate_data():
    # Connect to Supabase
    supabase = get_supabase_client()
    
    # Fetch properties
    properties = supabase.table('florida_parcels').select('*').execute()
    
    # Initialize graph service
    graph_service = PropertyGraphService()
    
    # Migrate each property
    for prop in properties.data:
        await graph_service.add_property(
            PropertyNode(
                parcel_id=prop['parcel_id'],
                address=prop['phy_addr1'],
                city=prop['phy_city'],
                county=prop['county'],
                current_value=prop['jv'],
                year_built=prop['act_yr_blt']
            )
        )
    
    print(f"Migrated {len(properties.data)} properties")

# Run migration
asyncio.run(migrate_data())
```

## 🔧 Integration Points

### 1. Update Main API

```python
# apps/api/main_simple.py

from apps.api.graph.property_graph_service import PropertyGraphService
from apps.api.graph.enhanced_rag_service import EnhancedRAGService

# Initialize Graphiti services
if os.getenv("ENABLE_GRAPHITI", "false").lower() == "true":
    try:
        graph_service = PropertyGraphService()
        rag_service = EnhancedRAGService(graph_service)
        app.state.graph_service = graph_service
        app.state.rag_service = rag_service
        print("✅ Graphiti integration enabled")
    except Exception as e:
        print(f"⚠️ Graphiti initialization failed: {e}")
```

### 2. Add Graph Endpoints

```python
# apps/api/routes/graph_routes.py

from fastapi import APIRouter, Depends, Query
from typing import List, Optional

router = APIRouter(prefix="/api/graph", tags=["graph"])

@router.get("/search")
async def graph_search(
    query: str = Query(..., description="Search query"),
    num_results: int = Query(10, ge=1, le=50),
    search_type: str = Query("hybrid", regex="^(vector|graph|hybrid)$")
):
    """Perform hybrid search using Graphiti"""
    rag_service = app.state.rag_service
    
    results = await rag_service.hybrid_search(
        query=query,
        num_results=num_results,
        search_type=search_type
    )
    
    return {
        "query": query,
        "results": [r.__dict__ for r in results],
        "count": len(results)
    }

@router.get("/property/{parcel_id}/history")
async def get_property_history(parcel_id: str):
    """Get temporal history of a property"""
    graph_service = app.state.graph_service
    
    history = await graph_service.get_property_history(parcel_id)
    
    return history

@router.get("/property/{parcel_id}/related")
async def get_related_properties(
    parcel_id: str,
    max_hops: int = Query(2, ge=1, le=3)
):
    """Find properties related through ownership or transactions"""
    graph_service = app.state.graph_service
    
    related = await graph_service.find_related_properties(
        parcel_id=parcel_id,
        max_hops=max_hops
    )
    
    return {
        "parcel_id": parcel_id,
        "related_properties": related,
        "count": len(related)
    }
```

### 3. Enhance Agents with Graph Memory

```python
# apps/api/agents/enhanced_agents.py

from apps.api.graph.enhanced_rag_service import GraphEnhancedAgent

# Create graph-enhanced agent
graph_agent = GraphEnhancedAgent(rag_service)

# Use in orchestrator
orchestrator.register_agent(graph_agent)
```

## 🧪 Testing

### Run Integration Tests

```bash
# Test Graphiti connection
pytest tests/test_graphiti_integration.py

# Test property graph operations
pytest tests/test_property_graph.py

# Test enhanced RAG
pytest tests/test_enhanced_rag.py
```

### Manual Testing

```python
# Test script
async def test_graphiti():
    from apps.api.graph.property_graph_service import PropertyGraphService
    
    service = PropertyGraphService()
    
    # Test search
    results = await service.search_properties(
        query="properties in Hollywood",
        num_results=5
    )
    
    print(f"Found {len(results)} properties")
    
    # Test relationships
    related = await service.find_related_properties(
        parcel_id="064210010010",
        max_hops=2
    )
    
    print(f"Found {len(related)} related properties")

asyncio.run(test_graphiti())
```

## 📈 Monitoring

### Neo4j Browser

Access at http://localhost:7474

Useful Cypher queries:

```cypher
// Count nodes by type
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
ORDER BY count DESC;

// Show property relationships
MATCH (p:Property)-[r]->(o:Owner)
RETURN p, r, o
LIMIT 50;

// Find properties with most connections
MATCH (p:Property)-[r]-()
RETURN p.parcel_id, count(r) as connections
ORDER BY connections DESC
LIMIT 10;
```

### Graphiti Metrics

```python
# Get graph statistics
stats = await graph_service.graphiti.get_statistics()
print(f"Nodes: {stats['node_count']}")
print(f"Edges: {stats['edge_count']}")
print(f"Properties: {stats['property_count']}")
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Neo4j Connection Failed
```
Error: Unable to connect to Neo4j
```
**Solution:**
- Check Neo4j is running: `docker ps`
- Verify credentials in `.env`
- Test with Neo4j Browser

#### 2. Graphiti Import Error
```
ImportError: No module named 'graphiti_core'
```
**Solution:**
```bash
pip install graphiti-core --upgrade
```

#### 3. Slow Graph Queries
**Solution:**
- Create indices:
```cypher
CREATE INDEX property_idx FOR (p:Property) ON (p.parcel_id);
CREATE INDEX owner_idx FOR (o:Owner) ON (o.name);
```

#### 4. Memory Issues with Large Graphs
**Solution:**
- Increase Neo4j heap size:
```bash
docker run -e NEO4J_server_memory_heap_max__size=4G ...
```

## 🚦 Production Deployment

### 1. Use Neo4j AuraDB
- Managed cloud service
- Automatic backups
- High availability

### 2. Configure Connection Pool
```python
from neo4j import AsyncGraphDatabase

driver = AsyncGraphDatabase.driver(
    uri,
    auth=(user, password),
    max_connection_pool_size=50,
    connection_acquisition_timeout=30
)
```

### 3. Enable Caching
```python
from functools import lru_cache
from aiocache import Cache

cache = Cache(Cache.REDIS)

@cached(ttl=3600)
async def get_property_cached(parcel_id: str):
    return await graph_service.get_property(parcel_id)
```

### 4. Monitor Performance
- Use Neo4j metrics
- Track query performance
- Monitor memory usage

## 📚 Additional Resources

- [Graphiti Documentation](https://github.com/gSimani/graphiti)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)

## ✅ Verification Checklist

- [ ] Neo4j is running and accessible
- [ ] Environment variables configured
- [ ] Graphiti package installed
- [ ] Test connection successful
- [ ] Sample data indexed
- [ ] Search queries working
- [ ] Relationship traversal working
- [ ] API endpoints responding
- [ ] Agents using graph context
- [ ] Performance acceptable

---

*Once all steps are complete, your ConcordBroker system will be enhanced with powerful knowledge graph capabilities!*