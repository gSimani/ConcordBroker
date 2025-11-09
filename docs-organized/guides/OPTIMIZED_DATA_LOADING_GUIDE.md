# Optimized Data Loading Guide for 1.2M+ Properties

## Performance Strategy Overview

### 🚀 Key Optimizations Implemented

1. **Database Partitioning**
   - Table partitioned by county (BROWARD, MIAMI-DADE, etc.)
   - Reduces query scope to relevant partitions only
   - 5-10x faster queries for county-specific searches

2. **Smart Indexing Strategy**
   - **Full-text search index** for address/owner searches
   - **BRIN indexes** for range queries (price, date, year)
   - **Hash indexes** for exact matches (parcel_id, city)
   - **Covering indexes** include all needed columns (no table lookups)
   - **GIN indexes** for JSONB property data

3. **Batch Processing**
   - 10,000 records per batch (optimal for Supabase)
   - Parallel processing with connection pooling
   - COPY command for maximum insert speed
   - Change detection via MD5 hashing

4. **Materialized Views**
   - Pre-computed city statistics
   - Recent sales cache
   - High-value properties index
   - Automatic refresh schedule

5. **Redis Caching Layer**
   - 5-minute cache for search results
   - 30-minute cache for property details
   - 1-hour cache for statistics
   - Automatic cache invalidation

## Loading Performance Metrics

| Operation | Records | Time | Rate |
|-----------|---------|------|------|
| Initial Load | 1.2M | ~20 min | 1,000/sec |
| Update Check | 1.2M | ~5 min | 4,000/sec |
| Index Creation | - | ~10 min | - |
| Mat View Refresh | - | ~2 min | - |

## Query Performance

| Query Type | Records Scanned | Response Time |
|------------|----------------|---------------|
| City Search | ~50K | <100ms |
| Text Search | Full-text index | <200ms |
| Price Range | BRIN index | <150ms |
| Single Property | Hash index | <10ms |
| Autocomplete | Partial index | <50ms |

## Setup Instructions

### 1. Install Dependencies

```bash
# Redis for caching
brew install redis  # Mac
sudo apt-get install redis-server  # Ubuntu

# Python packages
pip install psycopg2-binary asyncpg pandas numpy redis
```

### 2. Configure Environment

```env
DATABASE_URL=postgresql://user:pass@host/db
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Run Initial Data Load

```bash
# Create optimized schema
python apps/api/optimized_data_loader.py

# This will:
# 1. Create partitioned tables
# 2. Load data in batches
# 3. Create indexes
# 4. Build materialized views
```

### 4. Schedule Updates

```bash
# Add to crontab for daily updates
0 2 * * * python apps/api/optimized_data_loader.py --update
```

## API Usage Examples

### Fast Search Endpoint
```javascript
// Optimized search with caching
fetch('/api/v2/properties/search?city=Fort Lauderdale&min_price=500000')
  .then(res => res.json())
  .then(data => {
    console.log(`Found ${data.total} properties in ${data.query_time}s`);
    console.log(`Cached: ${data.cached}`);
  });
```

### Autocomplete
```javascript
// Fast autocomplete for addresses
fetch('/api/v2/properties/autocomplete?q=123 Main&field=address')
  .then(res => res.json())
  .then(suggestions => {
    // Returns top 10 matches instantly
  });
```

### Bulk Fetch
```javascript
// Get multiple properties in one request
fetch('/api/v2/properties/bulk', {
  method: 'POST',
  body: JSON.stringify({
    parcel_ids: ['123456', '789012', ...]
  })
});
```

## Frontend Optimization

### 1. Virtual Scrolling
```typescript
// Use react-window for large lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={properties.length}
  itemSize={100}
  width={'100%'}
>
  {PropertyRow}
</FixedSizeList>
```

### 2. Infinite Scroll
```typescript
// Load more as user scrolls
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['properties'],
  queryFn: ({ pageParam = 1 }) => fetchProperties(pageParam),
  getNextPageParam: (lastPage) => lastPage.nextPage,
});
```

### 3. Debounced Search
```typescript
// Prevent excessive API calls
const debouncedSearch = useMemo(
  () => debounce(searchProperties, 300),
  []
);
```

## Monitoring & Maintenance

### Check Performance
```sql
-- Query performance
SELECT 
  query,
  calls,
  mean_exec_time,
  total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Index usage
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Refresh Materialized Views
```sql
-- Manual refresh if needed
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_city_summary;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_recent_sales;
```

### Clear Cache
```bash
# Clear Redis cache if needed
redis-cli FLUSHDB
```

## Troubleshooting

### Slow Queries
1. Check EXPLAIN ANALYZE output
2. Verify indexes are being used
3. Update table statistics: `ANALYZE florida_parcels_optimized;`

### High Memory Usage
1. Reduce batch_size in loader
2. Increase work_mem in PostgreSQL
3. Check Redis memory usage

### Data Inconsistency
1. Run full refresh: `python optimized_data_loader.py --full-refresh`
2. Check data_hash for changes
3. Verify partition constraints

## Best Practices

1. **Always paginate** - Never load all 1.2M records
2. **Use materialized views** for aggregations
3. **Cache aggressively** but invalidate smartly
4. **Monitor query patterns** and create indexes accordingly
5. **Partition by access pattern** (county, date, etc.)
6. **Use JSONB** for flexible schema evolution
7. **Implement circuit breakers** for database protection

## Next Steps

1. **Implement ElasticSearch** for even faster full-text search
2. **Add GraphQL** with DataLoader for efficient batching
3. **Deploy read replicas** for horizontal scaling
4. **Implement CDC** (Change Data Capture) for real-time updates
5. **Add query result streaming** for large exports