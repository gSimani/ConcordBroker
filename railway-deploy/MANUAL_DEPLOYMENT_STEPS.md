# Manual Railway Deployment Steps

Since Railway CLI requires interactive browser login, follow these manual steps:

## Step 1: Login to Railway

Open a **new terminal** and run:
```bash
railway login
```

This will open your browser. Login with your Railway Pro account.

---

## Step 2: Deploy Meilisearch Service

After logging in, run these commands:

```bash
cd railway-deploy

# Initialize new project
railway init

# When prompted:
# - Project name: concordbroker-search
# - Link to existing project? No (create new)

# Deploy Meilisearch
railway up --dockerfile Dockerfile.meilisearch

# Set environment variables
railway variables set MEILI_MASTER_KEY=concordbroker-meili-railway-prod-key-2025
railway variables set MEILI_ENV=production
railway variables set MEILI_NO_ANALYTICS=true

# Generate public domain
railway domain

# Copy the URL shown (e.g., https://concordbroker-meilisearch-production.up.railway.app)
```

**Save the Meilisearch URL** - you'll need it for the next steps!

---

## Step 3: Deploy Search API Service

In the same terminal:

```bash
# Create second service
railway service create search-api

# Deploy Search API
railway up --dockerfile Dockerfile.search-api --service search-api

# Set environment variables (REPLACE with your Meilisearch URL from Step 2!)
railway variables set MEILISEARCH_URL=https://YOUR-MEILISEARCH-URL.up.railway.app --service search-api
railway variables set MEILISEARCH_KEY=concordbroker-meili-railway-prod-key-2025 --service search-api
railway variables set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co --service search-api
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0 --service search-api

# Generate public domain
railway domain --service search-api

# Copy the Search API URL shown
```

**Save the Search API URL** - you'll need it for frontend integration!

---

## Step 4: Verify Deployments

Test both services are running:

```bash
# Test Meilisearch (replace with your URL)
curl https://YOUR-MEILISEARCH-URL.up.railway.app/health

# Expected: {"status":"available"}

# Test Search API (replace with your URL)
curl https://YOUR-SEARCH-API-URL.up.railway.app/health

# Expected: {"status":"healthy"}
```

---

## Step 5: Update Railway Indexer Script

Edit `apps/api/railway_indexer.py`:

**Line 12** - Update with your Meilisearch URL:
```python
MEILI_URL = 'https://YOUR-MEILISEARCH-URL.up.railway.app'
```

Save the file.

---

## Step 6: Index Properties to Railway

Run the indexer to populate your Railway Meilisearch:

```bash
cd apps/api

# Index 100K properties (quick start - 2-3 minutes)
python railway_indexer.py 100000

# OR index 500K properties (medium - 10-15 minutes)
python railway_indexer.py 500000

# OR index full 9.7M properties (complete - 1-2 hours)
python railway_indexer.py 9113150
```

You should see:
```
================================================================================
RAILWAY PRODUCTION INDEXER
================================================================================
Meilisearch: https://your-url.up.railway.app
Target: 100,000 properties
...
Documents indexed: 100,000
================================================================================
```

---

## Step 7: Update Frontend PropertySearch.tsx

Edit `apps/web/src/pages/properties/PropertySearch.tsx`:

**Find the count query** (around line 750-800):
```typescript
// OLD: Supabase count query (slow, broken)
const countQuery = supabase.table('florida_parcels')
  .select('parcel_id', { count: 'exact' })
  .limit(1);
```

**Replace with**:
```typescript
// NEW: Meilisearch via Railway Search API
const SEARCH_API_URL = 'https://YOUR-SEARCH-API-URL.up.railway.app';

const getPropertyCount = async (filters: any) => {
  const response = await fetch(`${SEARCH_API_URL}/search/count`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filters })
  });
  const { count } = await response.json();
  return count;
};

// Use in searchProperties function
const count = await getPropertyCount({
  tot_lvg_area: {
    gte: filters.buildingSqFtMin,
    lte: filters.buildingSqFtMax
  }
});
```

---

## Step 8: Run Playwright Tests

Verify everything works:

```bash
cd apps/web

# Run Meilisearch integration tests
npx playwright test test_meilisearch_integration.spec.ts

# Expected results:
# ✅ Filter returned accurate count: 964 (not 7.3M fallback!)
# ✅ Meilisearch returned accurate results
# ✅ Query completed in <100ms
```

---

## Success Criteria

After completing all steps, verify:

✅ Meilisearch service running on Railway
✅ Search API service running on Railway
✅ Properties indexed (100K+ minimum)
✅ Frontend using Railway endpoints
✅ Building SqFt filter returns accurate counts (not 7.3M!)
✅ Query speed <100ms
✅ Playwright tests passing

---

## Troubleshooting

### "Cannot connect to Meilisearch"
- Check the URL is correct (copy from Railway dashboard)
- Verify the service is running: `railway status`
- Check logs: `railway logs`

### "Invalid API key"
- Verify MEILI_MASTER_KEY matches in both services
- Check environment variables: `railway variables`

### "Index not found"
- Run the indexer script first (Step 6)
- Verify indexing completed successfully

### "Frontend still shows 7.3M"
- Make sure you updated PropertySearch.tsx (Step 7)
- Clear browser cache and reload
- Check browser console for API errors

---

## Monitoring

View your Railway services:
- Dashboard: https://railway.app/dashboard
- Logs: `railway logs --service meilisearch`
- Metrics: Check CPU, memory, network in Railway dashboard

---

## Costs

Expected monthly costs on Railway Pro:
- Meilisearch: $5-8/month
- Search API: $5-7/month
- **Total: $10-15/month**

Monitor usage in Railway dashboard to track actual costs.

---

**Ready to proceed? Start with Step 1: `railway login`**
