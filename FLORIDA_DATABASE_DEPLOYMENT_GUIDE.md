# Florida Business Database Deployment Guide

## Overview

This guide explains how to upload your 8,434+ Florida Department of State business records to Supabase using a **SQL + RAG Hybrid Architecture** for optimal search performance.

## Architecture Decision: SQL + RAG Hybrid (Recommended)

### Why This Architecture?

**Primary: SQL Database (Supabase PostgreSQL)**
- ✅ **Structured queries** for business intelligence (location, dates, entity types)
- ✅ **Real-time performance** for filtering and sorting
- ✅ **Relationships** between entities, officers, and contacts
- ✅ **ACID compliance** for data integrity

**Secondary: RAG for Enhanced Search**
- ✅ **Semantic search** for business descriptions and fuzzy matching
- ✅ **Natural language queries** ("construction companies in Miami")
- ✅ **Vector similarity** for contextual business relationships
- ✅ **Full-text search** across unstructured content

## Prerequisites

### 1. Supabase Setup

1. **Enable Required Extensions:**
   ```sql
   -- Enable vector similarity search for RAG
   CREATE EXTENSION IF NOT EXISTS vector;
   
   -- Enable full-text search
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   
   -- Enable UUID generation
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

2. **Set Environment Variables:**
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   OPENAI_API_KEY=your-openai-key
   ```

### 2. Install Dependencies

```bash
pip install -r requirements-florida-data.txt
```

## Deployment Steps

### Step 1: Deploy Database Schema

```bash
# Connect to your Supabase database and run the schema
psql "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres" \
  -f florida_business_schema.sql
```

### Step 2: Test Upload with Sample Data

```python
# Test with 50 files first
python florida_data_uploader.py
```

This will:
- Process first 50 files from your database
- Parse fixed-width records
- Extract entities, contacts, and phone/email data
- Upload to structured tables
- Generate embeddings for RAG search

### Step 3: Full Upload

After testing, modify the uploader to process all files:

```python
# In florida_data_uploader.py, change:
await uploader.run()  # Process all 8,434 files
```

**Expected Results:**
- ~16,000+ phone numbers
- ~46,000+ email addresses  
- ~8,400+ business entities
- Full-text and vector search enabled

### Step 4: Enable Search Capabilities

Deploy the search API:

```python
# Test hybrid search functionality
python florida_business_search.py
```

## Data Structure Overview

### Main Tables

1. **`florida_entities`** - Core business information
   - Entity ID, business name, addresses
   - Formation dates, entity types
   - County and city information

2. **`florida_contacts`** - Contact information
   - Phone numbers and emails extracted
   - Officer/principal details
   - Registered agent information

3. **`florida_raw_records`** - For RAG search
   - Full record content for semantic search
   - Vector embeddings for similarity matching
   - Source file tracking

### Performance Features

- **Indexed searches** on name, location, entity type
- **Vector similarity** for semantic queries
- **Full-text search** across all content
- **Row-level security** for access control

## Search Capabilities

### 1. SQL Search (Structured)
```python
# Exact matches and filters
results = await search.sql_search(
    "CONSTRUCTION", 
    {"county": "MIAMI-DADE", "has_phone": True}
)
```

### 2. Semantic Search (RAG)
```python
# Natural language and fuzzy matching
results = await search.semantic_search(
    "companies that do home renovation and remodeling"
)
```

### 3. Hybrid Search (Best Results)
```python
# Combines both approaches
results = await search.hybrid_search(
    "construction contractors", 
    {"county": "BROWARD", "entity_type": "L"}
)
```

## Integration with ConcordBroker

### API Endpoints

Add to your FastAPI backend:

```python
from florida_business_search import FloridaBusinessSearch

@app.get("/api/florida/search")
async def search_florida_businesses(
    q: str,
    county: str = None,
    entity_type: str = None,
    has_contacts: bool = None
):
    search = FloridaBusinessSearch()
    filters = {}
    if county: filters['county'] = county
    if entity_type: filters['entity_type'] = entity_type  
    if has_contacts: filters['has_phone'] = True
    
    results = await search.hybrid_search(q, filters)
    return search.to_dict(results)
```

### Frontend Integration

```typescript
// React component for Florida business search
const searchFloridaBusinesses = async (query: string, filters: any) => {
  const response = await fetch('/api/florida/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ q: query, ...filters })
  });
  return response.json();
};
```

## Data Quality and Performance

### Expected Database Size
- **Entities:** ~8,400 records
- **Contacts:** ~62,400 records  
- **Raw records:** ~8,400 records with embeddings
- **Storage:** ~500MB total (including indexes)

### Performance Optimizations
- Batch uploads (100 records/batch)
- Upsert operations for duplicate prevention
- Indexed searches on key fields
- Vector similarity using ivfflat indexes

## Monitoring and Maintenance

### Processing Log
The `florida_processing_log` table tracks:
- File processing status
- Success/failure rates
- Error details for troubleshooting

### Query Examples

```sql
-- Get contact statistics by county
SELECT 
    business_county,
    COUNT(*) as total_entities,
    COUNT(phone_numbers) as entities_with_phones,
    COUNT(email_addresses) as entities_with_emails
FROM florida_active_entities_with_contacts
GROUP BY business_county
ORDER BY total_entities DESC;

-- Find new businesses in last 30 days
SELECT business_name, formation_date, business_city
FROM florida_entities
WHERE formation_date >= NOW() - INTERVAL '30 days'
ORDER BY formation_date DESC;

-- Search by industry (semantic)
SELECT entity_id, business_name, business_city
FROM florida_raw_records
WHERE to_tsvector('english', raw_content) 
  @@ to_tsquery('english', 'construction & contractor');
```

## Cost Considerations

### Supabase Costs
- **Database storage:** ~$0.125/GB/month
- **API requests:** ~$2.50/million requests  
- **Bandwidth:** ~$0.09/GB

### OpenAI Costs
- **Embeddings:** ~$0.0001 per 1K tokens
- **Total for 8,434 records:** ~$5-10 one-time

### Total Estimated Monthly Cost: $15-25

## Backup and Recovery

```bash
# Backup your database
pg_dump "postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres" \
  --table=florida_entities \
  --table=florida_contacts \
  --table=florida_raw_records \
  > florida_backup.sql
```

## Next Steps

1. **Deploy schema** to Supabase
2. **Test upload** with sample data
3. **Full upload** all 8,434 files
4. **Integrate search API** with ConcordBroker
5. **Add frontend components** for business search
6. **Monitor performance** and optimize queries

## Troubleshooting

### Common Issues

1. **Rate limits:** Use batch processing with delays
2. **Memory issues:** Process files in smaller chunks
3. **Embedding failures:** Implement retry logic
4. **Duplicate data:** Use upsert operations

### Support

- Check `florida_data_upload.log` for detailed error logs
- Monitor `florida_processing_log` table for file status
- Use Supabase dashboard for query performance metrics

---

This architecture gives you both the structured querying power of SQL and the intelligent search capabilities of RAG, making it perfect for business intelligence and contact discovery in your ConcordBroker application.