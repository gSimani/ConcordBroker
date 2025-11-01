# 🏗️ Tier 1: Production & Performance - Implementation Plan

**Objective**: Transform the agent system into a production-grade, high-performance platform running 24/7 with fresh data and optimized queries.

---

## 📊 Executive Summary

### What We're Building:
1. **Production Deployment** - 24/7 autonomous operation via Railway
2. **Fresh Data Pipeline** - Daily automated property updates (9.7M records)
3. **Health Monitoring** - GitHub Actions automated checks every 6 hours
4. **Database Optimization** - 10-100x faster queries via indexes, caching, and pooling

### Timeline:
- **Total Effort**: 2-4 hours (AI-assisted)
- **Option 1 (Production)**: 1-2 hours
- **Option 2 (Performance)**: 1-2 hours

### Cost:
- **Railway**: $5/month (24/7 orchestrator)
- **Redis Cloud**: $0/month (free tier)
- **GitHub Actions**: $0/month (free tier)
- **Total**: $5/month

---

## 🎯 Option 1: Complete Production Deployment

### Current State:
- ✅ 11 agents can run on local PC
- ✅ Deployment guides exist
- ❌ Agents stop when PC sleeps/restarts
- ❌ Property data is 35 days old
- ❌ No automated failover

### Target State:
- ✅ 24/7 operation via Railway cloud orchestrator
- ✅ Daily automated data refresh
- ✅ GitHub Actions health checks every 6 hours
- ✅ Automatic alerting on failures
- ✅ Fresh data (<24 hours old)

---

### 1.1: Railway Cloud Orchestrator

**Purpose**: Run cloud-based orchestrator 24/7 to coordinate all agents

**Files to Create**:
1. `railway-orchestrator/Dockerfile` - Container setup
2. `railway-orchestrator/orchestrator.py` - Cloud orchestrator code
3. `railway-orchestrator/railway.json` - Railway configuration
4. `railway-orchestrator/requirements.txt` - Python dependencies

**Features**:
- Connects to Supabase database
- Coordinates with PC-based agents
- Sends heartbeats every 30 seconds
- Health monitoring and recovery
- Runs 24/7 in Railway cloud

**Railway Setup**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# Set environment variables
railway variables --set SUPABASE_URL="..."
railway variables --set SUPABASE_SERVICE_ROLE_KEY="..."

# Deploy
railway up
```

**Cost**: $5/month

---

### 1.2: Property Data Update System

**Purpose**: Keep 9.7M property records fresh with daily automated updates

**Files to Create**:
1. `scripts/daily_property_update.py` - Main update script
2. `scripts/download_latest_nal.py` - Download fresh NAL files
3. `scripts/incremental_update.py` - Update only changed records
4. `.github/workflows/daily-data-update.yml` - GitHub Actions automation

**How It Works**:
```
1. Check Florida Revenue site for updates (all 67 counties)
2. Download changed NAL files only
3. Process and upload to Supabase (batches of 1000)
4. Update metadata (last_updated timestamp)
5. Send notification on completion
6. Alert on failures
```

**Data Sources**:
- Florida Revenue: https://floridarevenue.com/property/dataportal
- 67 counties × 4 file types (NAL, NAP, NAV, SDF)
- ~268 files total

**Schedule**: Daily at 2:00 AM EST (GitHub Actions)

**Expected Runtime**: 1-3 hours (depending on changes)

---

### 1.3: GitHub Actions Health Check System

**Purpose**: Monitor all 11 agents, alert on failures, auto-create GitHub issues

**Files to Create**:
1. `.github/workflows/agent-health-check.yml` - Main workflow
2. `scripts/check_all_agents.py` - Health check script
3. `scripts/restart_failed_agents.py` - Auto-recovery script

**Health Checks**:
- Agent registry: All 11 agents registered?
- Heartbeats: Recent (<5 minutes)?
- Alerts: Any critical alerts active?
- Database: Connection working?
- Performance: Query times acceptable?

**Actions on Failure**:
1. Create GitHub issue with details
2. Send notification (Email/Slack)
3. Attempt auto-recovery (restart agents)
4. Escalate if recovery fails

**Schedule**: Every 6 hours (4× daily)

**Cost**: $0 (within GitHub Actions free tier)

---

### 1.4: Automated Data Refresh Schedule

**Purpose**: Never have stale data again

**Components**:

1. **Daily Property Update** (2:00 AM EST)
   - Downloads latest NAL/NAP/NAV/SDF files
   - Incremental updates only (fast)
   - ~1-2 hours runtime

2. **Daily Sunbiz Update** (3:00 AM EST)
   - Corporate entity updates
   - New filings, status changes
   - ~30-60 minutes runtime

3. **Weekly Full Sync** (Sunday 1:00 AM EST)
   - Complete data validation
   - Fix any inconsistencies
   - Rebuild materialized views
   - ~3-4 hours runtime

4. **Monthly Archive** (1st of month, 4:00 AM EST)
   - Snapshot historical data
   - Clean up old records
   - Database maintenance
   - ~1-2 hours runtime

**All automated via GitHub Actions** - no manual intervention required

---

## 🚀 Option 2: Database Performance Optimization

### Current State:
- ❌ No indexes on critical columns
- ❌ Full table scans for common queries
- ❌ No caching layer
- ❌ Single connection per agent
- ❌ Queries take 2-30 seconds

### Target State:
- ✅ Composite indexes on all hot paths
- ✅ Redis caching for frequent queries
- ✅ Connection pooling (max 100 connections)
- ✅ Materialized views for complex aggregations
- ✅ Queries take 10-500ms (10-100× faster)

---

### 2.1: Critical Index Creation

**Purpose**: Speed up queries by 10-100×

**Files to Create**:
1. `database/critical_indexes.sql` - Index definitions
2. `database/deploy_indexes.py` - Safe deployment script
3. `database/index_analysis.sql` - Performance before/after

**Indexes to Create**:

```sql
-- Property searches (most common)
CREATE INDEX CONCURRENTLY idx_properties_county_year
ON florida_parcels(county, year)
WHERE year = 2025;

CREATE INDEX CONCURRENTLY idx_properties_use_value
ON florida_parcels(standardized_property_use, just_value DESC)
WHERE just_value > 0;

CREATE INDEX CONCURRENTLY idx_properties_owner
ON florida_parcels USING gin(to_tsvector('english', owner_name));

-- Sales queries
CREATE INDEX CONCURRENTLY idx_sales_date_county
ON property_sales_history(sale_date DESC, county);

CREATE INDEX CONCURRENTLY idx_sales_parcel
ON property_sales_history(parcel_id, sale_date DESC);

CREATE INDEX CONCURRENTLY idx_sales_price_range
ON property_sales_history(sale_price DESC)
WHERE sale_price > 0;

-- Foreclosure queries
CREATE INDEX CONCURRENTLY idx_foreclosures_status_date
ON foreclosure_activity(status, auction_date);

CREATE INDEX CONCURRENTLY idx_foreclosures_value
ON foreclosure_activity(final_judgment_amount DESC)
WHERE final_judgment_amount > 100000;

-- Entity queries
CREATE INDEX CONCURRENTLY idx_entities_name
ON sunbiz_corporate USING gin(to_tsvector('english', entity_name));

CREATE INDEX CONCURRENTLY idx_entities_status
ON sunbiz_corporate(status, filing_date DESC);

-- Agent tables
CREATE INDEX CONCURRENTLY idx_agent_metrics_created
ON agent_metrics(created_at DESC, agent_id);

CREATE INDEX CONCURRENTLY idx_agent_alerts_status
ON agent_alerts(status, severity, created_at DESC);
```

**Safety Features**:
- `CONCURRENTLY` - builds without locking table
- Analyze impact before deployment
- Rollback plan for each index
- Monitor index size and usage

**Expected Impact**: 10-100× faster queries

---

### 2.2: Redis Caching Layer

**Purpose**: Cache frequently accessed data in memory

**Files to Create**:
1. `database/redis_cache.py` - Cache manager
2. `database/cache_config.py` - Cache policies
3. `agents/cached_queries.py` - Cache-aware query helpers

**What to Cache**:
1. **Agent Registry** (TTL: 30 seconds)
   - All 11 agent statuses
   - Updated on every heartbeat
   - Hit rate: ~95%

2. **Property Lookups** (TTL: 1 hour)
   - Recently viewed properties
   - LRU eviction (max 10,000 properties)
   - Hit rate: ~70%

3. **County Statistics** (TTL: 1 day)
   - Market health scores
   - Total properties per county
   - Aggregate metrics
   - Hit rate: ~90%

4. **Search Results** (TTL: 15 minutes)
   - Common search queries
   - Paginated results
   - Hit rate: ~60%

**Cache Invalidation**:
- On data updates (property refresh)
- On schema changes
- Manual flush command
- Time-based expiration

**Redis Setup**:
```bash
# Use Redis Cloud (free tier)
# 30MB storage, 30 connections
# Perfect for caching layer
```

**Expected Impact**: 5-10× faster for cached queries

---

### 2.3: Connection Pooling

**Purpose**: Reuse database connections instead of creating new ones

**Files to Create**:
1. `database/connection_pool.py` - Pool manager
2. `agents/pooled_agent_base.py` - Base class with pooling

**Configuration**:
```python
from psycopg2.pool import ThreadedConnectionPool

pool = ThreadedConnectionPool(
    minconn=5,        # Minimum connections
    maxconn=100,      # Maximum connections
    host=SUPABASE_HOST,
    database=SUPABASE_DB,
    user=SUPABASE_USER,
    password=SUPABASE_PASSWORD
)
```

**Benefits**:
- No connection overhead (saves 50-200ms per query)
- Better resource utilization
- Automatic connection recycling
- Built-in retry logic

**Expected Impact**: 20-50% faster queries

---

### 2.4: Materialized Views

**Purpose**: Pre-compute expensive aggregations

**Files to Create**:
1. `database/materialized_views.sql` - View definitions
2. `database/refresh_views.py` - Refresh script

**Views to Create**:

```sql
-- Market health by county (refreshed daily)
CREATE MATERIALIZED VIEW mv_market_health AS
SELECT
    county,
    COUNT(*) as total_properties,
    AVG(just_value) as avg_value,
    COUNT(*) FILTER (WHERE sale_date >= CURRENT_DATE - INTERVAL '30 days') as recent_sales,
    -- ... complex calculations
FROM florida_parcels p
LEFT JOIN property_sales_history s ON p.parcel_id = s.parcel_id
GROUP BY county;

CREATE UNIQUE INDEX ON mv_market_health(county);

-- Top opportunities (refreshed hourly)
CREATE MATERIALIZED VIEW mv_top_opportunities AS
SELECT
    f.parcel_id,
    f.final_judgment_amount,
    f.auction_date,
    p.just_value,
    -- ... opportunity score calculation
FROM foreclosure_activity f
JOIN florida_parcels p ON f.parcel_id = p.parcel_id
WHERE f.status = 'PENDING'
ORDER BY opportunity_score DESC
LIMIT 1000;
```

**Refresh Schedule**:
- Market health: Daily at 5:00 AM
- Top opportunities: Hourly
- Via cron job or GitHub Actions

**Expected Impact**: 100-1000× faster for complex aggregations

---

### 2.5: Query Optimization

**Purpose**: Rewrite inefficient queries

**Files to Create**:
1. `database/slow_query_log.sql` - Identify slow queries
2. `database/optimized_queries.py` - Rewritten queries

**Common Optimizations**:

**Before** (slow - 15 seconds):
```sql
SELECT * FROM florida_parcels
WHERE owner_name LIKE '%LLC%';
```

**After** (fast - 200ms):
```sql
SELECT * FROM florida_parcels
WHERE to_tsvector('english', owner_name) @@ to_tsquery('LLC');
```

**Before** (slow - 30 seconds):
```sql
SELECT COUNT(*) FROM property_sales_history
WHERE sale_date >= '2024-01-01';
```

**After** (fast - 50ms):
```sql
SELECT reltuples::bigint FROM pg_class
WHERE relname = 'property_sales_history';
-- Plus filter estimate
```

---

## 📋 Implementation Checklist

### Phase 1: Railway Deployment (30 minutes)
- [ ] Create Dockerfile for cloud orchestrator
- [ ] Write orchestrator.py with health monitoring
- [ ] Configure railway.json
- [ ] Set up Railway project and environment variables
- [ ] Deploy and verify orchestrator is running
- [ ] Test coordination with PC agents

### Phase 2: Data Update System (45 minutes)
- [ ] Create property update script
- [ ] Test download from Florida Revenue site
- [ ] Implement incremental update logic
- [ ] Create GitHub Actions workflow
- [ ] Test manual run
- [ ] Verify automated schedule

### Phase 3: Health Monitoring (30 minutes)
- [ ] Create health check script
- [ ] Set up GitHub Actions workflow
- [ ] Test failure detection
- [ ] Verify issue creation
- [ ] Test notification delivery

### Phase 4: Database Indexes (30 minutes)
- [ ] Analyze current query performance
- [ ] Generate index SQL statements
- [ ] Deploy indexes to Supabase (CONCURRENTLY)
- [ ] Verify index usage with EXPLAIN
- [ ] Measure performance improvement

### Phase 5: Redis Caching (20 minutes)
- [ ] Set up Redis Cloud account (free tier)
- [ ] Create cache manager
- [ ] Implement cache-aware queries
- [ ] Test cache hit rates
- [ ] Monitor memory usage

### Phase 6: Connection Pooling (15 minutes)
- [ ] Implement connection pool
- [ ] Update agents to use pool
- [ ] Test concurrent connections
- [ ] Verify pool statistics

### Phase 7: Testing & Validation (30 minutes)
- [ ] Run all agents with optimizations
- [ ] Benchmark query performance
- [ ] Verify data freshness
- [ ] Check Railway orchestrator status
- [ ] Test health check alerts
- [ ] Validate cache effectiveness

---

## 🎯 Success Metrics

### Before Tier 1:
- Agent uptime: ~50% (PC dependent)
- Data age: 35 days old
- Query times: 2-30 seconds
- Manual monitoring: Required
- Cache hit rate: 0% (no cache)

### After Tier 1:
- Agent uptime: 99%+ (24/7 Railway)
- Data age: <24 hours (daily updates)
- Query times: 10-500ms (10-100× faster)
- Automated monitoring: Every 6 hours
- Cache hit rate: 60-90%

---

## 💰 Cost Breakdown

### Monthly Costs:
- **Railway**: $5/month (cloud orchestrator)
- **Redis Cloud**: $0/month (free tier, 30MB)
- **GitHub Actions**: $0/month (2,000 minutes free)
- **Supabase**: $0/month (using existing plan)
- **Total**: **$5/month**

### ROI:
- **Time Saved**: No manual data updates (2 hours/week → 8 hours/month)
- **Faster Queries**: Better user experience, faster insights
- **Always Online**: Never miss opportunities due to downtime
- **Automated Alerts**: Catch issues before they become problems

**Payback**: Immediate (saves your time from day 1)

---

## 🚀 Deployment Steps

### Step 1: Railway Setup (User Action Required)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Link to this codebase
cd railway-orchestrator
railway link
```

### Step 2: Set Environment Variables
```bash
railway variables --set SUPABASE_URL="https://xxx.supabase.co"
railway variables --set SUPABASE_SERVICE_ROLE_KEY="eyJ..."
railway variables --set SUPABASE_HOST="db.xxx.supabase.co"
railway variables --set SUPABASE_PASSWORD="your_password"
```

### Step 3: Deploy
```bash
railway up
```

### Step 4: GitHub Actions Setup (User Action Required)
1. Go to GitHub repository → Settings → Secrets
2. Add repository secrets:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_HOST`
   - `SUPABASE_PASSWORD`

### Step 5: Trigger First Run
```bash
# Manually trigger property update
gh workflow run daily-data-update.yml

# Manually trigger health check
gh workflow run agent-health-check.yml
```

### Step 6: Verify Everything
```bash
# Check Railway logs
railway logs

# Check agent status
python check_agent_activity.py

# Check database performance
python scripts/benchmark_queries.py
```

---

## 📚 Files to Create

### Railway Orchestrator:
1. `railway-orchestrator/Dockerfile`
2. `railway-orchestrator/orchestrator.py`
3. `railway-orchestrator/railway.json`
4. `railway-orchestrator/requirements.txt`
5. `railway-orchestrator/.dockerignore`

### Property Update System:
6. `scripts/daily_property_update.py`
7. `scripts/download_latest_nal.py`
8. `scripts/incremental_update.py`
9. `.github/workflows/daily-data-update.yml`

### Health Monitoring:
10. `.github/workflows/agent-health-check.yml`
11. `scripts/check_all_agents.py`
12. `scripts/restart_failed_agents.py`

### Database Performance:
13. `database/critical_indexes.sql`
14. `database/deploy_indexes.py`
15. `database/index_analysis.sql`
16. `database/redis_cache.py`
17. `database/cache_config.py`
18. `database/connection_pool.py`
19. `database/materialized_views.sql`
20. `database/refresh_views.py`
21. `database/slow_query_log.sql`
22. `database/optimized_queries.py`

### Testing & Documentation:
23. `scripts/benchmark_queries.py`
24. `TIER_1_DEPLOYMENT_GUIDE.md`
25. `TIER_1_PERFORMANCE_REPORT.md`

**Total**: 25 new files

---

## ⚡ Quick Start

Once I implement everything, you'll just need to:

1. **Run setup script** (5 minutes):
   ```bash
   python setup_tier1.py
   ```

2. **Deploy to Railway** (5 minutes):
   ```bash
   cd railway-orchestrator
   railway up
   ```

3. **Add GitHub secrets** (5 minutes):
   - Copy values from `.env.mcp`
   - Paste into GitHub → Settings → Secrets

4. **Done!** Everything runs automatically from there.

---

## 🎉 Expected Results

### Day 1:
- ✅ Railway orchestrator running 24/7
- ✅ GitHub Actions monitoring every 6 hours
- ✅ Database indexes deployed
- ✅ Redis cache active

### Day 2:
- ✅ First automated property update complete
- ✅ Fresh data (<24 hours old)
- ✅ Queries 10-100× faster
- ✅ Cache hit rate >60%

### Week 1:
- ✅ 99%+ uptime
- ✅ Zero manual interventions
- ✅ All data fresh and up-to-date
- ✅ System running smoothly

---

**Ready to implement! Let me start building... 🚀**
