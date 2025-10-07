# Search Architecture - ConcordBroker Property Search

## Overview
Multi-layered search system for 9.7M Florida properties with instant facets, typo tolerance, and semantic search.

## Data Profile
- **Current**: 9,113,150 properties across 67 Florida counties
- **12-month target**: 12M+ properties (adding multi-state support)
- **Update frequency**: Daily (Florida Department of Revenue data)
- **Critical fields**:
  - Location: county, city, address, zipCode, lat/lng
  - Property: propertyType, landUseCode, yearBuilt, bedrooms, bathrooms
  - Size: buildingSqFt (total_living_area), landSqFt
  - Financial: marketValue, assessedValue, taxAmount, lastSalePrice
  - Owner: owner_name, owner_addr1, isTaxDelinquent

## Architecture Layers

### Layer 1: Instant Faceted Search (Meilisearch)
**Purpose**: Primary search interface - instant results with facets and typo tolerance

**Use Cases**:
- Property grid/list view with filters
- Autocomplete for addresses, cities, owners
- Faceted navigation (county, price ranges, property types)
- Quick filters and sorting

**Configuration**:
```json
{
  "searchableAttributes": [
    "parcel_id",
    "address",
    "city",
    "owner_name",
    "county"
  ],
  "filterableAttributes": [
    "county",
    "propertyType",
    "yearBuilt",
    "buildingSqFt",
    "landSqFt",
    "marketValue",
    "isTaxDelinquent",
    "hasHomestead"
  ],
  "sortableAttributes": [
    "marketValue",
    "buildingSqFt",
    "yearBuilt",
    "lastSaleDate"
  ],
  "rankingRules": [
    "words",
    "typo",
    "proximity",
    "attribute",
    "sort",
    "exactness"
  ],
  "typoTolerance": {
    "enabled": true,
    "minWordSizeForTypos": {
      "oneTypo": 4,
      "twoTypos": 8
    }
  },
  "pagination": {
    "maxTotalHits": 1000000
  }
}
```

**Why Meilisearch**:
- ✅ Handles 10M+ docs easily
- ✅ Sub-20ms search response
- ✅ Built-in typo tolerance and synonyms
- ✅ Faceted search out of the box
- ✅ Simple REST API
- ✅ Low memory footprint (can run on Railway $5/month)

### Layer 2: Semantic/RAG Search (Supabase pgvector + FTS)
**Purpose**: Natural language queries and AI-powered search

**Use Cases**:
- "Find me waterfront properties under $1M with boat access"
- "3 bedroom homes near good schools in Fort Lauderdale"
- "Investment properties with high ROI potential"
- AI Property Intelligence queries

**Implementation**:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to florida_parcels
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS search_embedding vector(1536);

-- Create hybrid search function
CREATE OR REPLACE FUNCTION hybrid_property_search(
  query_text TEXT,
  query_embedding vector(1536),
  match_limit INT DEFAULT 20,
  semantic_weight FLOAT DEFAULT 0.5
)
RETURNS TABLE (
  parcel_id TEXT,
  address TEXT,
  city TEXT,
  county TEXT,
  score FLOAT
) AS $$
BEGIN
  RETURN QUERY
  WITH semantic_search AS (
    SELECT
      p.parcel_id,
      1 - (p.search_embedding <=> query_embedding) AS similarity
    FROM florida_parcels p
    WHERE p.search_embedding IS NOT NULL
    ORDER BY p.search_embedding <=> query_embedding
    LIMIT match_limit * 2
  ),
  keyword_search AS (
    SELECT
      p.parcel_id,
      ts_rank(
        to_tsvector('english',
          COALESCE(p.phy_addr1, '') || ' ' ||
          COALESCE(p.phy_city, '') || ' ' ||
          COALESCE(p.owner_name, '')
        ),
        plainto_tsquery('english', query_text)
      ) AS rank
    FROM florida_parcels p
    WHERE to_tsvector('english',
      COALESCE(p.phy_addr1, '') || ' ' ||
      COALESCE(p.phy_city, '') || ' ' ||
      COALESCE(p.owner_name, '')
    ) @@ plainto_tsquery('english', query_text)
    LIMIT match_limit * 2
  )
  SELECT
    p.parcel_id,
    p.phy_addr1,
    p.phy_city,
    p.county_name,
    (
      COALESCE(ss.similarity * semantic_weight, 0) +
      COALESCE(ks.rank * (1 - semantic_weight), 0)
    ) AS score
  FROM florida_parcels p
  LEFT JOIN semantic_search ss ON p.parcel_id = ss.parcel_id
  LEFT JOIN keyword_search ks ON p.parcel_id = ks.parcel_id
  WHERE ss.parcel_id IS NOT NULL OR ks.parcel_id IS NOT NULL
  ORDER BY score DESC
  LIMIT match_limit;
END;
$$ LANGUAGE plpgsql;

-- Create FTS index
CREATE INDEX IF NOT EXISTS florida_parcels_fts_idx ON florida_parcels
USING gin(to_tsvector('english',
  COALESCE(phy_addr1, '') || ' ' ||
  COALESCE(phy_city, '') || ' ' ||
  COALESCE(owner_name, '')
));

-- Create vector index (HNSW for fast approximate search)
CREATE INDEX IF NOT EXISTS florida_parcels_embedding_idx ON florida_parcels
USING ivfflat (search_embedding vector_cosine_ops)
WITH (lists = 1000);
```

**Why Supabase Hybrid**:
- ✅ Data already in Supabase
- ✅ No data duplication
- ✅ Combines keyword + semantic in one query
- ✅ Native PostgreSQL performance
- ✅ Free with existing Supabase plan

### Layer 3: API Gateway (FastAPI)
**Purpose**: Unified API exposing both search backends

**Endpoints**:
```python
# Instant search (Meilisearch)
GET /api/search/instant
  ?q=query
  &county=DADE
  &minValue=100000
  &maxValue=500000
  &minBuildingSqFt=2000
  &limit=100

# Semantic search (Supabase hybrid)
POST /api/search/semantic
  {
    "query": "waterfront homes near schools under $1M",
    "filters": {"county": "BROWARD"},
    "limit": 20
  }

# Autocomplete (Meilisearch)
GET /api/search/suggest
  ?q=1234 Main
  &type=address|city|owner
  &limit=10

# Facets (Meilisearch)
GET /api/search/facets
  ?field=county|propertyType|priceRange
```

## Data Flow

### Initial Sync (One-time)
```
Supabase (9.7M properties)
  ↓
Index Builder Script
  ↓
Meilisearch (full dataset)
```

### Continuous Sync (Daily)
```
Florida Dept of Revenue → Download Script → Supabase Staging
  ↓
Change Detection
  ↓
Bulk Update → Supabase Production + Meilisearch
```

### Search Request Flow
```
User Query
  ↓
React Frontend
  ↓
FastAPI Gateway
  ├→ Meilisearch (90% of queries - filters, list view)
  └→ Supabase Hybrid (10% of queries - AI, semantic)
  ↓
Combined Results
  ↓
Frontend Display
```

## Deployment Architecture

### Railway Services
1. **Meilisearch Service**
   - Image: `getmeili/meilisearch:v1.6`
   - RAM: 2GB (sufficient for 10M docs)
   - Storage: 10GB
   - Cost: ~$10/month
   - Env: `MEILI_MASTER_KEY`, `MEILI_ENV=production`

2. **FastAPI Search Service**
   - Runtime: Python 3.12
   - RAM: 512MB
   - Cost: ~$5/month
   - Env: `MEILISEARCH_URL`, `MEILISEARCH_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`

3. **Sync Worker** (Cron)
   - Runs daily at 2 AM EST
   - Checks for FL Dept of Revenue updates
   - Syncs changes to Meilisearch
   - Cost: $0 (runs 10 min/day)

### Supabase
- Uses existing free tier
- Add pgvector extension
- Create hybrid search function
- Add embedding column (populated async)

### Vercel (Frontend)
- Existing deployment
- No changes needed
- Calls FastAPI gateway

## Performance Targets

| Metric | Target | Actual (Expected) |
|--------|--------|-------------------|
| Search latency (instant) | <50ms | ~20ms |
| Search latency (semantic) | <500ms | ~200ms |
| Facet computation | <100ms | ~30ms |
| Autocomplete | <20ms | ~10ms |
| Index update (full) | <30min | ~15min |
| Index update (delta) | <2min | ~30sec |
| Concurrent users | 100+ | Limited by Railway tier |

## Migration Plan

### Phase 1: Meilisearch Setup (Week 1)
- ✅ Deploy Meilisearch to Railway
- ✅ Create index schema
- ✅ Build initial sync script
- ✅ Populate 9.7M properties
- ✅ Test search performance

### Phase 2: API Integration (Week 1-2)
- ✅ Create FastAPI search endpoints
- ✅ Implement Meilisearch client
- ✅ Add facets and filters
- ✅ Build autocomplete
- ✅ Deploy to Railway

### Phase 3: Frontend Integration (Week 2)
- ✅ Update PropertySearch component
- ✅ Replace direct Supabase calls
- ✅ Add faceted navigation UI
- ✅ Implement autocomplete
- ✅ Fix count query bug

### Phase 4: Semantic Search (Week 3)
- ✅ Add pgvector to Supabase
- ✅ Create hybrid search function
- ✅ Generate embeddings (async)
- ✅ Integrate with AI Intelligence tab
- ✅ Test semantic queries

### Phase 5: Sync & Monitoring (Week 4)
- ✅ Build continuous sync service
- ✅ Add monitoring and alerts
- ✅ Create health checks
- ✅ Document API
- ✅ Performance testing

## Cost Breakdown

| Service | Cost/Month | Purpose |
|---------|------------|---------|
| Meilisearch (Railway) | $10 | Instant search |
| FastAPI (Railway) | $5 | API gateway |
| Supabase | $0 (free tier) | Database + pgvector |
| Vercel | $0 (hobby) | Frontend hosting |
| **Total** | **$15/month** | Full search infrastructure |

## Monitoring & Observability

### Metrics to Track
- Search query latency (p50, p95, p99)
- Index freshness (last sync timestamp)
- Error rates by endpoint
- Cache hit rates
- Query patterns (popular searches)

### Alerts
- Meilisearch index lag > 1 hour
- Search latency p95 > 200ms
- Error rate > 1%
- Sync job failures

### Logging
- All search queries (for analytics)
- Slow queries (>500ms)
- Failed syncs
- User search patterns

## Security Considerations

- ✅ API key authentication for Meilisearch
- ✅ Rate limiting (100 req/min per IP)
- ✅ No PII in search logs
- ✅ HTTPS only
- ✅ CORS configured for concordbroker.com only
- ✅ Supabase RLS for sensitive data

## Future Enhancements

### Quarter 2
- Add geo-search for map-based queries
- Implement search personalization
- Add synonym support (e.g., "apt" = "apartment")
- Multi-language support (Spanish)

### Quarter 3
- Expand to Georgia, Texas properties
- Add saved searches and alerts
- Implement ML-based ranking
- Add search analytics dashboard

### Quarter 4
- Advanced filters (HOA, school districts)
- Property recommendations
- Price prediction in search results
- Search-to-CRM integration

---

**Document Version**: 1.0
**Last Updated**: 2025-09-30
**Owner**: ConcordBroker Engineering Team
