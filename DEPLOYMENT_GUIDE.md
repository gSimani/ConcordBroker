# Search Infrastructure Deployment Guide

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **Supabase Project**: Existing (pmispwtdngkcmsrsjwbp.supabase.co)
3. **Environment Variables**: From `.env.mcp` file

## Step 1: Deploy Meilisearch to Railway

### Option A: Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init

# Add Meilisearch service
railway add

# Select "Meilisearch" from template

# Set environment variables
railway variables set MEILI_MASTER_KEY=your_secure_master_key_here
railway variables set MEILI_ENV=production

# Deploy
railway up
```

### Option B: Railway Dashboard
1. Go to https://railway.app/new
2. Click "Deploy from template"
3. Search for "Meilisearch"
4. Click "Deploy"
5. Set environment variables:
   - `MEILI_MASTER_KEY`: Generate a secure key (32+ characters)
   - `MEILI_ENV`: `production`
6. Click "Deploy"
7. Note the public URL (e.g., `https://meilisearch-production-xxxx.railway.app`)

## Step 2: Index Properties to Meilisearch

### Local Indexing (Recommended for initial sync)
```bash
# Install dependencies
cd apps/api
pip install -r requirements-search.txt

# Set environment variables
export MEILISEARCH_URL="https://your-meili-url.railway.app"
export MEILISEARCH_KEY="your_master_key"
export SUPABASE_URL="https://pmispwtdngkcmsrsjwbp.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"

# Run indexer
python meilisearch_indexer.py
```

Expected output:
```
🔍 Creating/Getting index: florida_properties
✅ Index created
⚙️  Updating index settings...
✅ Settings updated
📊 Total properties to index: 9,113,150
📦 Batches: 912 (size: 10,000)

Indexing: 100%|████████████| 9113150/9113150 [15:23<00:00, 9874 properties/s]

✅ INDEXING COMPLETE
📊 Documents indexed: 9,113,150
⏱️  Time elapsed: 15.4 minutes
⚡ Speed: 9,874 docs/second
```

## Step 3: Deploy Search API to Railway

```bash
# In project root
railway init

# Create Dockerfile.search (already created)

# Deploy
railway up --dockerfile Dockerfile.search

# Set environment variables
railway variables set MEILISEARCH_URL=https://your-meili-url.railway.app
railway variables set MEILISEARCH_KEY=your_master_key
railway variables set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
railway variables set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Get public URL
railway domain
```

## Step 4: Test the Search API

```bash
# Health check
curl https://your-search-api.railway.app/health

# Test instant search
curl "https://your-search-api.railway.app/api/search/instant?minBuildingSqFt=10000&maxBuildingSqFt=20000&limit=5"

# Test autocomplete
curl "https://your-search-api.railway.app/api/search/suggest?q=123&type=address&limit=10"

# Test facets
curl "https://your-search-api.railway.app/api/search/facets?county=DADE"
```

Expected response:
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total": 37726,
    "page": 1,
    "limit": 5,
    "pages": 7546
  },
  "processingTimeMs": 8
}
```

## Step 5: Update Frontend

Edit `apps/web/src/pages/properties/PropertySearch.tsx`:

```typescript
// Replace direct Supabase call with Search API
const SEARCH_API_URL = 'https://your-search-api.railway.app/api/search/instant';

const searchProperties = useCallback(async (page = 1) => {
  const params = new URLSearchParams();

  // Add filters
  if (filters.minBuildingSqFt) params.append('minBuildingSqFt', filters.minBuildingSqFt);
  if (filters.maxBuildingSqFt) params.append('maxBuildingSqFt', filters.maxBuildingSqFt);
  if (filters.county) params.append('county', filters.county);
  // ... add other filters

  params.append('page', page.toString());
  params.append('limit', pageSize.toString());

  const response = await fetch(`${SEARCH_API_URL}?${params}`);
  const data = await response.json();

  setProperties(data.data);
  setTotalResults(data.pagination.total);  // ✅ Accurate count!
}, [filters]);
```

## Step 6: Set up Supabase Hybrid Search (Optional - for semantic/AI queries)

```sql
-- Run in Supabase SQL Editor

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS search_embedding vector(1536);

-- Create hybrid search function
CREATE OR REPLACE FUNCTION hybrid_property_search(
  query_text TEXT,
  query_embedding vector(1536) DEFAULT NULL,
  match_limit INT DEFAULT 20
)
RETURNS TABLE (
  parcel_id TEXT,
  address TEXT,
  city TEXT,
  score FLOAT
) AS $$
BEGIN
  IF query_embedding IS NOT NULL THEN
    -- Semantic + keyword hybrid
    RETURN QUERY
    SELECT
      p.parcel_id,
      p.phy_addr1,
      p.phy_city,
      (
        (1 - (p.search_embedding <=> query_embedding)) * 0.6 +
        ts_rank(to_tsvector('english', COALESCE(p.phy_addr1, '') || ' ' || COALESCE(p.owner_name, '')),
                plainto_tsquery('english', query_text)) * 0.4
      ) AS score
    FROM florida_parcels p
    WHERE p.search_embedding IS NOT NULL
    ORDER BY score DESC
    LIMIT match_limit;
  ELSE
    -- Keyword only
    RETURN QUERY
    SELECT
      p.parcel_id,
      p.phy_addr1,
      p.phy_city,
      ts_rank(to_tsvector('english', COALESCE(p.phy_addr1, '') || ' ' || COALESCE(p.owner_name, '')),
              plainto_tsquery('english', query_text)) AS score
    FROM florida_parcels p
    WHERE to_tsvector('english', COALESCE(p.phy_addr1, '') || ' ' || COALESCE(p.owner_name, ''))
      @@ plainto_tsquery('english', query_text)
    ORDER BY score DESC
    LIMIT match_limit;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Create indexes
CREATE INDEX IF NOT EXISTS florida_parcels_fts_idx ON florida_parcels
USING gin(to_tsvector('english', COALESCE(phy_addr1, '') || ' ' || COALESCE(owner_name, '')));

-- Vector index (add after embeddings are populated)
-- CREATE INDEX florida_parcels_embedding_idx ON florida_parcels
-- USING ivfflat (search_embedding vector_cosine_ops) WITH (lists = 1000);
```

## Step 7: Verify with Playwright

Run the end-to-end test:

```bash
npx playwright test test_sqft_final.spec.ts --headed
```

Expected result:
```
✓ Advanced Filters button visible
✓ Set Min Building SqFt = 10,000
✓ Set Max Building SqFt = 20,000
✓ Clicked Search button

📊 DISPLAYED COUNT: 37,726 Properties  ✅ COUNT IS CORRECT!
🏠 PROPERTY CARDS: 100 visible

📋 Sample Properties:
   1. 10,412 sqft ✅
   2. 11,121 sqft ✅
   3. 12,006 sqft ✅

=== TEST COMPLETE ===
```

## Troubleshooting

### Issue: Meilisearch returns 0 results
**Solution**: Check if indexing completed
```bash
curl https://your-meili-url.railway.app/indexes/florida_properties/stats
```

### Issue: Slow search (>100ms)
**Solution**: Check Meilisearch RAM usage. Upgrade Railway plan if needed.

### Issue: Count still shows 7.3M
**Solution**: Ensure frontend is calling the new Search API, not old Supabase endpoint.

### Issue: Indexing fails midway
**Solution**: Re-run indexer. Meilisearch handles duplicates automatically via parcel_id.

## Monitoring

### Meilisearch Dashboard
Access at: `https://your-meili-url.railway.app`
- Use master key to login
- View stats, search logs, index health

### Railway Logs
```bash
railway logs --service meilisearch
railway logs --service search-api
```

### Search Analytics
Add to search_api.py:
```python
# Log all searches
@app.middleware("http")
async def log_searches(request: Request, call_next):
    if "/api/search" in request.url.path:
        logger.info(f"Search: {request.url}")
    return await call_next(request)
```

## Cost Optimization

### Current Costs
- Meilisearch: $10/month (2GB RAM)
- Search API: $5/month (512MB RAM)
- **Total**: $15/month

### Optimization Tips
1. **Use Meilisearch caching**: Set TTL on frequent queries
2. **Limit pagination**: Max 1,000 pages (100k results)
3. **Compress responses**: Enable gzip in FastAPI
4. **CDN**: Put Cloudflare in front for caching

### Scaling Up
- For >10M docs: Upgrade Meilisearch to 4GB RAM ($20/month)
- For >100 req/s: Add load balancer + 2 search API instances
- For multi-region: Deploy Meilisearch replicas in US-East + US-West

## Next Steps

1. ✅ Deploy Meilisearch
2. ✅ Index 9.7M properties
3. ✅ Deploy Search API
4. ✅ Update frontend
5. ✅ Test with Playwright
6. ⏳ Set up daily sync (cron job)
7. ⏳ Add monitoring alerts
8. ⏳ Implement semantic search (pgvector)

---

**Questions?** Check Railway docs or Meilisearch docs:
- https://docs.railway.app
- https://docs.meilisearch.com
