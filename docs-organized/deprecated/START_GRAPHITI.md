# 🚀 Quick Start Guide for Graphiti Integration

## Prerequisites
- Docker and Docker Compose installed
- Python 3.10+ installed
- OpenAI API key

## 🎯 Quick Start (5 minutes)

### 1. Set Environment Variables
Create or update `.env` file:
```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
ENABLE_GRAPHITI=true

# Optional (defaults provided)
NEO4J_PASSWORD=ConcordBroker2024!
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_EMBEDDING_MODEL=text-embedding-3-small

# Your existing Supabase credentials
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
```

### 2. Start Services with Docker Compose
```bash
# Start all services (Neo4j, Redis, API)
docker-compose -f docker-compose.graphiti.yml up -d

# Check services are running
docker-compose -f docker-compose.graphiti.yml ps

# View logs
docker-compose -f docker-compose.graphiti.yml logs -f
```

### 3. Initialize Graphiti
```bash
# Wait for Neo4j to be ready (30 seconds)
sleep 30

# Run initialization
python apps/api/graph/init_graphiti.py

# Expected output:
# ✅ Neo4j connection successful!
# ✅ Graphiti initialized successfully!
# ✅ Property indices created successfully!
# 🎉 Graphiti is ready to use!
```

### 4. Migrate Existing Data (Optional)
```bash
# Migrate first 1000 properties as a test
python apps/api/graph/migrate_data.py --limit 1000

# Full migration (may take time)
python apps/api/graph/migrate_data.py
```

### 5. Test the Integration
```bash
# Test API health
curl http://localhost:8000/health

# Test graph health
curl http://localhost:8000/api/graph/health

# Search properties
curl "http://localhost:8000/api/graph/search/properties?q=Hollywood&limit=5"

# Get property history
curl http://localhost:8000/api/graph/property/064210010010/history
```

## 🖥️ Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| API Documentation | http://localhost:8000/docs | None |
| Neo4j Browser | http://localhost:7474 | neo4j / ConcordBroker2024! |
| Grafana Dashboard | http://localhost:3001 | admin / admin |
| Prometheus Metrics | http://localhost:9090 | None |

## 📊 Neo4j Browser Queries

Connect to http://localhost:7474 and try these queries:

```cypher
// Count all nodes
MATCH (n) RETURN count(n);

// Show property relationships
MATCH (p:Property)-[r]->(o:Owner)
RETURN p, r, o LIMIT 25;

// Find properties by city
MATCH (p:Property {city: "Hollywood"})
RETURN p LIMIT 10;

// Show ownership network
MATCH path = (o:Owner)-[:OWNS*1..2]-(p:Property)
RETURN path LIMIT 50;
```

## 🔧 Alternative: Manual Setup (Without Docker)

### 1. Install Neo4j Locally
```bash
# macOS
brew install neo4j

# Windows (PowerShell as Admin)
choco install neo4j-community

# Linux
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 5' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
```

### 2. Start Neo4j
```bash
# Start Neo4j
neo4j start

# Set initial password (first time only)
neo4j-admin dbms set-initial-password ConcordBroker2024!
```

### 3. Install Python Dependencies
```bash
pip install -r requirements-graphiti.txt
```

### 4. Run API Locally
```bash
# Set environment variables
export ENABLE_GRAPHITI=true
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=ConcordBroker2024!

# Start API
python apps/api/main_simple.py
```

## 🧪 Test Graph Features

### Test Enhanced Search
```python
import asyncio
from apps.api.graph.enhanced_rag_service import EnhancedRAGService
from apps.api.graph.property_graph_service import PropertyGraphService

async def test():
    graph_service = PropertyGraphService()
    rag_service = EnhancedRAGService(graph_service)
    
    # Hybrid search
    results = await rag_service.hybrid_search(
        query="luxury properties in Hollywood with pool",
        num_results=5
    )
    
    for r in results:
        print(f"Score: {r.confidence:.2f} - {r.content[:100]}...")

asyncio.run(test())
```

### Test Graph Agents
```python
from apps.api.agents.graph_enhanced_agents import GraphAgentOrchestrator

async def test_agents():
    orchestrator = GraphAgentOrchestrator()
    
    result = await orchestrator.route_request({
        "type": "property_analysis",
        "query": "Find investment opportunities in Fort Lauderdale"
    })
    
    print(result)

asyncio.run(test_agents())
```

## 🛑 Stop Services
```bash
# Stop all services
docker-compose -f docker-compose.graphiti.yml down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose -f docker-compose.graphiti.yml down -v
```

## 🔍 Troubleshooting

### Neo4j Won't Start
```bash
# Check logs
docker logs concordbroker-neo4j

# Common fix: increase memory
docker-compose -f docker-compose.graphiti.yml down
# Edit docker-compose.graphiti.yml to increase heap size
# Restart
```

### Connection Refused
```bash
# Ensure Neo4j is running
docker ps | grep neo4j

# Test connection
curl http://localhost:7474

# Check firewall/ports
netstat -an | grep 7687
```

### Graphiti Import Error
```bash
# Reinstall Graphiti
pip uninstall graphiti-core
pip install graphiti-core --upgrade
```

## 📈 Monitor Performance

### View Graph Metrics
```bash
# API endpoint
curl http://localhost:8000/api/graph/monitoring/dashboard

# Grafana dashboard
# http://localhost:3001 (admin/admin)
```

### Check Graph Statistics
```bash
curl http://localhost:8000/api/graph/stats
```

## ✅ Success Indicators

You know Graphiti is working when:
1. ✅ `/health` endpoint shows `"graphiti_enabled": true`
2. ✅ Neo4j Browser shows nodes and relationships
3. ✅ Graph search returns results with confidence scores
4. ✅ Property history shows temporal timeline
5. ✅ Monitoring dashboard displays metrics

## 🎉 Next Steps

1. **Explore the API**: http://localhost:8000/docs
2. **Query the Graph**: Use Neo4j Browser
3. **Monitor Performance**: Check Grafana dashboards
4. **Test Agents**: Try graph-enhanced agents
5. **Build Relationships**: Add more data connections

---

**Need help?** Check the logs:
```bash
docker-compose -f docker-compose.graphiti.yml logs neo4j
docker-compose -f docker-compose.graphiti.yml logs concordbroker-api
```

**Ready to code?** The graph is now powering your property intelligence! 🚀