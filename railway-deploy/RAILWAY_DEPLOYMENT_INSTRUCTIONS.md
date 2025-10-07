# Railway Pro Deployment Instructions

## Prerequisites
- Railway Pro Workspace (✅ Confirmed available)
- Railway CLI installed (✅ v4.5.3)
- Railway login completed

## Step 1: Login to Railway (MANUAL)

Run this command in your terminal:
```bash
railway login
```

This will open your browser for authentication. Once logged in, return here.

## Step 2: Create Meilisearch Service

```bash
# Navigate to deployment directory
cd railway-deploy

# Create new Railway project
railway init concordbroker-search

# Link to existing Pro Workspace
railway link

# Deploy Meilisearch service
railway up --dockerfile Dockerfile.meilisearch
```

## Step 3: Configure Meilisearch Environment Variables

In Railway dashboard (or via CLI):
```bash
railway variables set MEILI_MASTER_KEY=concordbroker-meili-railway-prod-key-2025
railway variables set MEILI_ENV=production
railway variables set MEILI_NO_ANALYTICS=true
```

## Step 4: Get Meilisearch Public URL

```bash
# Generate public domain
railway domain

# Or get existing URL
railway status
```

Expected output: `https://concordbroker-meilisearch-production.up.railway.app`

## Step 5: Deploy Search API Service

```bash
# Create new service in same project
railway service create search-api

# Deploy Search API
railway up --dockerfile Dockerfile.search-api --service search-api
```

## Step 6: Configure Search API Environment Variables

```bash
# Set Meilisearch connection
railway variables set MEILISEARCH_URL=https://concordbroker-meilisearch-production.up.railway.app --service search-api
railway variables set MEILISEARCH_KEY=concordbroker-meili-railway-prod-key-2025 --service search-api

# Set Supabase connection
railway variables set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co --service search-api
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0 --service search-api
```

## Step 7: Index Properties to Railway Meilisearch

Create production indexer script that points to Railway:

```python
# railway_indexer.py
import meilisearch
from supabase import create_client
from tqdm import tqdm
import re

# Railway Production URLs
MEILI_URL = 'https://concordbroker-meilisearch-production.up.railway.app'
MEILI_KEY = 'concordbroker-meili-railway-prod-key-2025'

# Supabase
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

# Connect
meili = meilisearch.Client(MEILI_URL, MEILI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Index properties (full 9.7M or filtered subset)
TARGET_COUNT = 100000  # Start with 100K, can increase later

# ... (same indexing logic as quick_test_indexer.py)
```

Run:
```bash
cd apps/api
python railway_indexer.py
```

## Step 8: Update Frontend to Use Railway Search

Update `apps/web/src/pages/properties/PropertySearch.tsx`:

```typescript
// Old: Supabase count query (slow, broken)
const countQuery = supabase.table('florida_parcels')
  .select('parcel_id', { count: 'exact' })
  .limit(1);

// New: Meilisearch via Railway Search API
const response = await fetch('https://concordbroker-search-api-production.up.railway.app/search/count', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filters: {
      tot_lvg_area: { gte: 10000, lte: 20000 }
    }
  })
});

const { count } = await response.json();
// Returns accurate count: 964 (not 7.3M!)
```

## Step 9: Verify Deployment

```bash
# Check Meilisearch health
curl https://concordbroker-meilisearch-production.up.railway.app/health

# Check Search API health
curl https://concordbroker-search-api-production.up.railway.app/health

# Test search
curl -X POST https://concordbroker-search-api-production.up.railway.app/search/instant \
  -H "Content-Type: application/json" \
  -d '{"query": "", "filters": {"tot_lvg_area": {"gte": 10000, "lte": 20000}}, "limit": 5}'
```

## Step 10: Run Playwright Verification

```bash
# Run end-to-end tests
cd apps/web
npx playwright test test_search_complete.spec.ts

# Expected results:
# ✅ Filter applied: Building SqFt 10,000 - 20,000
# ✅ Count accurate: 964 (not 7.3M!)
# ✅ Query speed: <100ms
# ✅ Results match filter criteria
```

## Monitoring & Costs

### Railway Pro Costs:
- **Meilisearch**: $5-8/month (512MB RAM, 1 vCPU shared, 5GB disk)
- **Search API**: $5-7/month (256MB RAM, 0.5 vCPU shared)
- **Total**: $10-15/month

### Monitoring:
- Railway dashboard: https://railway.app/dashboard
- Real-time logs: `railway logs --service meilisearch`
- Metrics: CPU, memory, network usage visible in dashboard

## Rollback Plan

If issues occur:
```bash
# Rollback Meilisearch
railway rollback --service meilisearch

# Rollback Search API
railway rollback --service search-api

# Or revert frontend to Supabase (temporary)
git revert <commit-hash>
```

## Success Criteria

✅ Meilisearch deployed and healthy
✅ Search API deployed and healthy
✅ Properties indexed (100K+ minimum)
✅ Frontend using Railway endpoints
✅ Playwright tests passing
✅ Accurate counts displayed (not 7.3M fallback!)
✅ Query speed <100ms
✅ Costs within $15/month budget

---

**Current Status**: Ready to deploy after `railway login` completes.
