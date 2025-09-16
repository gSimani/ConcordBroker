# 🚀 Graphiti Production Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying ConcordBroker's Graphiti integration to production environments. Graphiti adds temporally-aware knowledge graph capabilities to enhance property intelligence and agent memory.

## Architecture Overview

### Core Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   FastAPI App   │    │   Neo4j Graph   │
│   (React + D3)  │◄──►│   (Graphiti)    │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │   Supabase      │    │   Prometheus    │
│    Cache        │    │  (Primary DB)   │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **Property Data**: Supabase → Graphiti → Neo4j Graph
2. **Agent Memory**: LLM Interactions → Graphiti → Neo4j Episodic Nodes
3. **Search Queries**: Frontend → FastAPI → Hybrid Search (Vector + Graph)
4. **Visualizations**: Neo4j → FastAPI → D3.js Frontend

## Prerequisites

### Infrastructure Requirements
- **CPU**: 4+ cores (8+ recommended for production)
- **RAM**: 8GB minimum (16GB+ recommended)
- **Storage**: 100GB+ SSD with backup capabilities
- **Network**: High-speed internet for external API calls

### Required Services
- **Neo4j Database**: v5.0+ (Enterprise recommended)
- **Redis**: v7.0+ for caching
- **PostgreSQL**: via Supabase
- **Docker**: v24.0+ with Docker Compose
- **SSL Certificate**: for HTTPS endpoints

### API Keys & Credentials
```env
# Required
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
NEO4J_PASSWORD=secure_password

# Optional but Recommended
HUGGINGFACE_API_TOKEN=hf_...
LANGSMITH_API_KEY=ls__...
GRAFANA_PASSWORD=secure_password
```

## Deployment Options

### Option 1: Docker Swarm (Recommended)

#### 1. Prepare Environment
```bash
# Create production directory
mkdir /opt/concordbroker-production
cd /opt/concordbroker-production

# Clone repository
git clone https://github.com/your-org/concordbroker.git .

# Create environment file
cp .env.example .env.production
```

#### 2. Configure Environment
```env
# .env.production
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Neo4j Production Settings
NEO4J_PASSWORD=your_secure_password_here
NEO4J_HEAP_INITIAL_SIZE=2G
NEO4J_HEAP_MAX_SIZE=4G
NEO4J_PAGECACHE_SIZE=1G

# Redis Production Settings
REDIS_MAXMEMORY=1gb
REDIS_MAXMEMORY_POLICY=allkeys-lru

# Application Settings
API_WORKERS=4
MAX_CONNECTIONS=100
RATE_LIMIT_PER_MINUTE=1000

# Security
JWT_SECRET_KEY=your_jwt_secret_here
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

#### 3. Production Docker Compose
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.swarmMode=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=admin@yourdomain.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - letsencrypt:/letsencrypt
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - traefik-public
    deploy:
      placement:
        constraints:
          - node.role == manager

  neo4j:
    image: neo4j:5-enterprise
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
      NEO4J_server_memory_heap_initial__size: ${NEO4J_HEAP_INITIAL_SIZE:-2G}
      NEO4J_server_memory_heap_max__size: ${NEO4J_HEAP_MAX_SIZE:-4G}
      NEO4J_server_memory_pagecache_size: ${NEO4J_PAGECACHE_SIZE:-1G}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_db_query__timeout: 30s
      NEO4J_db_transaction_timeout: 60s
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
      - ./backups:/backups
    networks:
      - concordbroker-network
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      labels:
        - traefik.enable=true
        - traefik.http.routers.neo4j.rule=Host(`neo4j.yourdomain.com`)
        - traefik.http.routers.neo4j.tls.certresolver=myresolver
        - traefik.http.services.neo4j.loadbalancer.server.port=7474

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory ${REDIS_MAXMEMORY:-1gb} --maxmemory-policy ${REDIS_MAXMEMORY_POLICY:-allkeys-lru}
    volumes:
      - redis-data:/data
    networks:
      - concordbroker-network
    deploy:
      replicas: 1

  concordbroker-api:
    image: concordbroker:latest
    environment:
      ENVIRONMENT: production
      NEO4J_URI: bolt://neo4j:7687
      REDIS_URL: redis://redis:6379
      WORKERS: ${API_WORKERS:-4}
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
    networks:
      - concordbroker-network
      - traefik-public
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 30s
      labels:
        - traefik.enable=true
        - traefik.http.routers.api.rule=Host(`api.yourdomain.com`)
        - traefik.http.routers.api.tls.certresolver=myresolver
        - traefik.http.services.api.loadbalancer.server.port=8000

  concordbroker-web:
    image: concordbroker-web:latest
    networks:
      - traefik-public
    deploy:
      replicas: 2
      labels:
        - traefik.enable=true
        - traefik.http.routers.web.rule=Host(`yourdomain.com`)
        - traefik.http.routers.web.tls.certresolver=myresolver

volumes:
  neo4j-data:
  redis-data:
  letsencrypt:

networks:
  traefik-public:
    external: true
  concordbroker-network:
    driver: overlay
```

#### 4. Deploy with Docker Swarm
```bash
# Initialize swarm (on manager node)
docker swarm init

# Create external network
docker network create -d overlay traefik-public

# Build images
docker build -t concordbroker:latest .
docker build -t concordbroker-web:latest ./apps/web

# Deploy stack
docker stack deploy -c docker-compose.production.yml concordbroker

# Verify deployment
docker service ls
docker stack ps concordbroker
```

### Option 2: Kubernetes (Advanced)

#### 1. Kubernetes Manifests
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: concordbroker

---
# k8s/neo4j-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
  namespace: concordbroker
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5-enterprise
        env:
        - name: NEO4J_AUTH
          value: "neo4j/production_password"
        - name: NEO4J_ACCEPT_LICENSE_AGREEMENT
          value: "yes"
        ports:
        - containerPort: 7474
        - containerPort: 7687
        volumeMounts:
        - name: neo4j-data
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: neo4j-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

#### 2. Deploy to Kubernetes
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n concordbroker
kubectl logs -f deployment/concordbroker-api -n concordbroker
```

## Configuration & Security

### Neo4j Security Hardening
```bash
# Connect to Neo4j container
docker exec -it concordbroker_neo4j_1 bash

# Create additional security settings
echo "dbms.security.auth_enabled=true" >> conf/neo4j.conf
echo "dbms.security.procedures.unrestricted=jwt.*" >> conf/neo4j.conf
echo "dbms.security.procedures.allowlist=apoc.*,gds.*" >> conf/neo4j.conf

# Restart container
docker restart concordbroker_neo4j_1
```

### API Rate Limiting
```python
# In main_simple.py, add rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/graph/search")
@limiter.limit("100/minute")
async def search_graph(request: Request, query: str):
    # ... existing code
```

### Database Connection Pooling
```python
# Enhanced connection management
from contextlib import asynccontextmanager
from sqlalchemy.pool import QueuePool

@asynccontextmanager
async def get_db_connection():
    pool = QueuePool(
        creator=create_connection,
        max_overflow=20,
        pool_size=10,
        pool_timeout=30,
        pool_recycle=3600
    )
    connection = await pool.connect()
    try:
        yield connection
    finally:
        await connection.close()
```

## Monitoring & Observability

### 1. Prometheus Configuration
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'concordbroker-api'
    static_configs:
      - targets: ['concordbroker-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j:2004']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### 2. Grafana Dashboards
```json
{
  "dashboard": {
    "title": "ConcordBroker Graphiti Performance",
    "panels": [
      {
        "title": "Graph Query Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(graph_query_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Neo4j Memory Usage",
        "type": "graph", 
        "targets": [
          {
            "expr": "neo4j_memory_heap_used_bytes / neo4j_memory_heap_max_bytes * 100",
            "legendFormat": "Heap Usage %"
          }
        ]
      }
    ]
  }
}
```

### 3. Alert Rules
```yaml
# prometheus/alert_rules.yml
groups:
  - name: concordbroker_alerts
    rules:
      - alert: HighGraphQueryLatency
        expr: histogram_quantile(0.95, rate(graph_query_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High graph query latency detected"
          description: "95th percentile latency is {{ $value }}s"

      - alert: Neo4jMemoryHigh
        expr: neo4j_memory_heap_used_bytes / neo4j_memory_heap_max_bytes * 100 > 80
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Neo4j memory usage is high"
          description: "Memory usage is {{ $value }}%"
```

### 4. Health Checks
```python
# apps/api/routes/health.py
@router.get("/health/detailed")
async def detailed_health():
    checks = {
        "neo4j": await check_neo4j_health(),
        "redis": await check_redis_health(),
        "supabase": await check_supabase_health(),
        "openai": await check_openai_health()
    }
    
    overall_status = "healthy" if all(
        check["status"] == "healthy" for check in checks.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": checks
    }
```

## Backup & Recovery

### 1. Automated Backup Script
```bash
#!/bin/bash
# scripts/backup-production.sh

set -e

BACKUP_DIR="/opt/backups/concordbroker"
DATE=$(date +%Y%m%d_%H%M%S)
NEO4J_CONTAINER="concordbroker_neo4j_1"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Neo4j
echo "Starting Neo4j backup..."
docker exec "$NEO4J_CONTAINER" neo4j-admin database dump --to-path=/backups neo4j
docker cp "$NEO4J_CONTAINER":/backups/neo4j.dump "$BACKUP_DIR/neo4j_$DATE.dump"

# Backup Redis
echo "Starting Redis backup..."
docker exec concordbroker_redis_1 redis-cli BGSAVE
docker cp concordbroker_redis_1:/data/dump.rdb "$BACKUP_DIR/redis_$DATE.rdb"

# Compress backups
echo "Compressing backups..."
tar -czf "$BACKUP_DIR/full_backup_$DATE.tar.gz" -C "$BACKUP_DIR" neo4j_$DATE.dump redis_$DATE.rdb

# Upload to cloud storage (optional)
if [ ! -z "$AWS_S3_BUCKET" ]; then
    aws s3 cp "$BACKUP_DIR/full_backup_$DATE.tar.gz" "s3://$AWS_S3_BUCKET/backups/"
fi

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: full_backup_$DATE.tar.gz"
```

### 2. Disaster Recovery Procedure
```bash
#!/bin/bash
# scripts/restore-production.sh

BACKUP_FILE="$1"
NEO4J_CONTAINER="concordbroker_neo4j_1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Stop services
docker stack rm concordbroker

# Extract backup
tar -xzf "$BACKUP_FILE" -C /tmp/

# Restore Neo4j
docker run --rm -v neo4j-data:/data neo4j:5-enterprise \
    neo4j-admin database load --from-path=/tmp neo4j

# Restart services
docker stack deploy -c docker-compose.production.yml concordbroker

echo "Recovery completed"
```

### 3. Backup Scheduling
```cron
# Add to crontab
# Daily backup at 2 AM
0 2 * * * /opt/concordbroker-production/scripts/backup-production.sh

# Weekly full backup on Sunday at 1 AM
0 1 * * 0 /opt/concordbroker-production/scripts/full-backup-production.sh
```

## Performance Optimization

### 1. Neo4j Index Creation
```cypher
// Create property indices
CREATE INDEX property_parcel_id FOR (p:Property) ON (p.parcel_id);
CREATE INDEX property_city FOR (p:Property) ON (p.city);
CREATE INDEX property_county FOR (p:Property) ON (p.county);

// Create owner indices
CREATE INDEX owner_name FOR (o:Owner) ON (o.name);
CREATE INDEX owner_entity_id FOR (o:Owner) ON (o.entity_id);

// Create composite indices
CREATE INDEX property_location FOR (p:Property) ON (p.city, p.county);
CREATE INDEX transaction_date_price FOR (t:Transaction) ON (t.date, t.price);

// Create full-text search indices
CREATE FULLTEXT INDEX property_search FOR (p:Property) ON EACH [p.address, p.city, p.owner_name];
CREATE FULLTEXT INDEX owner_search FOR (o:Owner) ON EACH [o.name, o.address];
```

### 2. Connection Pooling
```python
# Enhanced connection management
from neo4j import GraphDatabase
from contextlib import asynccontextmanager

class Neo4jManager:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_lifetime=30 * 60,  # 30 minutes
            max_connection_pool_size=50,
            connection_acquisition_timeout=30
        )
    
    @asynccontextmanager
    async def session(self):
        session = self.driver.session()
        try:
            yield session
        finally:
            await session.close()
```

### 3. Caching Strategy
```python
# Redis caching with expiration
import redis.asyncio as redis
from functools import wraps

redis_client = redis.Redis.from_url(REDIS_URL)

def cache_result(expire_seconds=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try cache first
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await redis_client.setex(
                cache_key, 
                expire_seconds, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

@cache_result(expire_seconds=600)  # 10 minutes
async def get_property_network(parcel_id: str, depth: int = 2):
    # ... expensive graph query
```

## Maintenance

### 1. Database Maintenance
```cypher
// Weekly maintenance queries
CALL gds.graph.drop('property-network', false);
CALL apoc.periodic.iterate(
    'MATCH (n) WHERE n.updated_at < date() - duration("P30D") RETURN n',
    'DELETE n',
    {batchSize: 1000}
);

// Optimize storage
CALL db.index.fulltext.drop('old_index');
CALL db.resampleOutdatedIndexes();
```

### 2. Log Rotation
```yaml
# docker-compose override for log rotation
services:
  concordbroker-api:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

### 3. Monitoring Script
```bash
#!/bin/bash
# scripts/health-check.sh

# Check service health
services=("concordbroker_neo4j_1" "concordbroker_redis_1" "concordbroker_api_1")

for service in "${services[@]}"; do
    if ! docker ps | grep -q "$service"; then
        echo "ALERT: $service is not running"
        # Send alert notification
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 Service $service is down!\"}"
    fi
done

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "ALERT: Disk usage is $DISK_USAGE%"
fi
```

## Troubleshooting

### Common Issues

#### 1. Neo4j Memory Issues
```bash
# Increase heap size
echo "NEO4J_server_memory_heap_max__size=8G" >> .env.production

# Clear query cache
docker exec concordbroker_neo4j_1 cypher-shell -u neo4j -p password "CALL db.clearQueryCaches();"
```

#### 2. Connection Pool Exhaustion
```python
# Add connection monitoring
@app.middleware("http")
async def monitor_connections(request: Request, call_next):
    active_connections = len(app.state.graph_service.active_connections)
    if active_connections > 40:  # 80% of max pool
        logger.warning(f"High connection count: {active_connections}")
    
    response = await call_next(request)
    return response
```

#### 3. Graph Query Performance
```cypher
// Analyze slow queries
CALL db.stats.retrieve('QUERY') YIELD data
RETURN data.query, data.executionTimeMillis
ORDER BY data.executionTimeMillis DESC
LIMIT 10;

// Add query timeout
:param timeout => 10000
```

### Support Contacts
- **Infrastructure**: ops@yourdomain.com
- **Application**: dev@yourdomain.com  
- **Database**: dba@yourdomain.com

## Updates & Upgrades

### Rolling Updates
```bash
# Update API service with zero downtime
docker service update --image concordbroker:v2.0 concordbroker_concordbroker-api

# Update web frontend
docker service update --image concordbroker-web:v2.0 concordbroker_concordbroker-web
```

### Migration Scripts
```python
# apps/api/migrations/graph_migration_v2.py
async def migrate_graph_schema():
    """Migrate graph schema to v2"""
    async with neo4j_session() as session:
        # Add new node labels
        await session.run("MATCH (p:Property) SET p:PropertyV2")
        
        # Create new relationships
        await session.run("""
            MATCH (p:Property)-[:OLD_RELATION]->(o:Owner)
            CREATE (p)-[:CURRENT_OWNER]->(o)
        """)
```

---

**Production Checklist:**
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups scheduled
- [ ] Monitoring alerts configured
- [ ] Performance indices created
- [ ] Security hardening applied
- [ ] Load testing completed
- [ ] Disaster recovery tested

**Go-Live Ready** ✅