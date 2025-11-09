# Phase 1 Deployment Guide - ConcordBroker Ownership System

**Date**: October 5, 2025
**Status**: Ready for Deployment
**Focus**: Multi-corporation ownership tracking + Agent Lion foundation

---

## What We're Deploying

### Core Features
1. **Multi-Corporation Ownership Schema** - Track owners across multiple LLCs
2. **Owner Identity Resolution** - Match property owners to Sunbiz entities
3. **RAG System Foundation** - For Agent Lion documentation queries
4. **Agent Lion Conversation Memory** - Persistent chat history

### Why This Matters
Currently, ConcordBroker shows:
- Owner: "Smith Investment Group LLC"

After deployment, it will show:
- Owner: "John Smith"
- Controls: 4 entities with 23 properties worth $10M
- [Show Portfolio] button → See all properties across all entities

---

## Step-by-Step Deployment

### Step 1: Deploy Ownership Schema (5 minutes)

**Action**: Run SQL migration in Supabase

1. Open Supabase SQL Editor:
   ```
   https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new
   ```

2. Open file:
   ```
   supabase/migrations/20251005_concordbroker_ownership_schema.sql
   ```

3. Copy entire contents and paste in SQL Editor

4. Click **"Run"**

5. Verify success message:
   ```
   ✅ ConcordBroker ownership schema deployed successfully!
   Created tables: owner_identities, property_ownership, entity_principals, ...
   ```

**What This Creates**:
- `owner_identities` - Canonical owner names
- `property_ownership` - Property → Owner → Entity linking
- `entity_principals` - Sunbiz entity officers
- `concordbroker_docs` - RAG embeddings
- `agent_lion_conversations` - Chat memory
- `agent_lion_analyses` - Cached investment analyses
- `owner_portfolio_summary` - Materialized view of portfolios

---

### Step 2: Run Owner Identity Resolution (10 minutes)

**Action**: Match property owners to Sunbiz entities

1. Install required Python packages:
   ```bash
   pip install fuzzywuzzy python-Levenshtein networkx
   ```

2. Run identity resolution script:
   ```bash
   python scripts/build_owner_identity_graph.py
   ```

3. Watch progress:
   ```
   📊 Step 1: Extracting owner names from florida_parcels (limit: 50000)...
      Found 45,231 unique owner names

   📊 Step 2: Extracting entity names from florida_entities...
      Found 50,000 entities

   🔍 Step 3: Fuzzy matching owners to entities (threshold: 85)...
      Processed 10000 owners, found 3,456 matches...
      ✅ Found 3,456 high-confidence matches

   🕸️  Step 4: Building identity graph...
      Graph has 6,912 nodes and 3,456 edges
      Found 2,789 identity clusters

   💾 Step 5: Populating owner_identities table...
      ✅ Created 2,789 owner identities

   🔄 Step 6: Refreshing owner statistics...

   ✅ IDENTITY RESOLUTION COMPLETE
   Duration: 327.3 seconds
   ```

4. Verify results:
   ```sql
   -- Check created identities
   SELECT COUNT(*) FROM owner_identities;
   -- Should return ~2,789

   -- Check portfolio summary
   SELECT * FROM owner_portfolio_summary
   WHERE total_properties > 5
   ORDER BY total_portfolio_value DESC
   LIMIT 10;
   ```

---

### Step 3: Test Owner Portfolio Lookup (2 minutes)

**Action**: Verify multi-corporation tracking works

1. Find an owner with multiple properties:
   ```sql
   SELECT
       canonical_name,
       total_properties,
       total_entities,
       total_portfolio_value
   FROM owner_portfolio_summary
   WHERE total_entities > 1
   LIMIT 5;
   ```

2. Get full portfolio for an owner:
   ```sql
   SELECT get_owner_portfolio('<owner_identity_id_from_above>');
   ```

3. Expected result (JSON):
   ```json
   {
     "owner": {
       "id": "abc-123",
       "name": "John Smith",
       "type": "person"
     },
     "summary": {
       "total_properties": 23,
       "total_entities": 4,
       "total_portfolio_value": 10000000
     },
     "properties": [
       {
         "parcel_id": "504203060330",
         "county": "BROWARD",
         "value": 450000,
         "entity_name": "JS Properties LLC"
       },
       ...
     ],
     "entities": [
       {
         "entity_id": "L12000045678",
         "entity_name": "JS Properties LLC",
         "role": "owner"
       },
       ...
     ]
   }
   ```

---

## What's Different Now

### Before Deployment
```
Property: 504203060330
Owner: JS Properties LLC
```

### After Deployment
```
Property: 504203060330
Owner: John Smith
Entity: JS Properties LLC → View on Sunbiz

⚠️ This owner controls 4 entities with 23 total properties
[Show Portfolio] button
```

---

## Next Steps (Phase 1 Continued)

### Immediate (Week 1)
1. ✅ Deploy ownership schema
2. ✅ Run identity resolution
3. ⏳ Set up RAG system with investment documents
4. ⏳ Deploy Agent Lion with ConcordBroker tools
5. ⏳ Update UI to show multi-entity portfolios

### This Week
- **RAG Setup**: Embed DOR documentation, investment formulas, FL statutes
- **Agent Lion**: Deploy with investment analysis capabilities
- **UI Updates**: Build enhanced property owner section

---

## Testing the System

### Test Query 1: Find Multi-Corporation Owners
```sql
SELECT
    canonical_name,
    total_properties,
    total_entities,
    total_portfolio_value,
    entities
FROM owner_portfolio_summary
WHERE total_entities > 2
ORDER BY total_portfolio_value DESC
LIMIT 20;
```

### Test Query 2: Property Ownership Lookup
```sql
-- Find owner by property
SELECT
    oi.canonical_name,
    oi.total_properties,
    po.entity_name,
    po.entity_id
FROM property_ownership po
JOIN owner_identities oi ON po.owner_identity_id = oi.id
WHERE po.parcel_id = '504203060330'
AND po.county_code = 6;
```

### Test Query 3: Entity Portfolio
```sql
-- All properties owned by a specific entity
SELECT
    p.parcel_id,
    p.phy_addr1,
    p.just_value,
    oi.canonical_name as ultimate_owner
FROM property_ownership po
JOIN florida_parcels p ON po.parcel_id = p.parcel_id
JOIN owner_identities oi ON po.owner_identity_id = oi.id
WHERE po.entity_id = 'L12000045678'
ORDER BY p.just_value DESC;
```

---

## Performance Expectations

### Identity Resolution
- **10K owners**: ~2-3 minutes
- **50K owners**: ~10-15 minutes
- **500K owners** (full dataset): ~2-3 hours

### Query Performance
- Owner portfolio lookup: <100ms
- Multi-property search: <200ms
- Portfolio summary view: Instant (materialized)

---

## Troubleshooting

### Issue: No matches found
**Solution**: Lower `FUZZY_MATCH_THRESHOLD` from 85 to 75 in script

### Issue: Too many false matches
**Solution**: Raise threshold to 90 or add more normalization rules

### Issue: Slow performance
**Solution**: Reduce `MAX_OWNERS_TO_PROCESS` for initial testing

### Issue: Duplicate identities
**Solution**: Run `REFRESH MATERIALIZED VIEW owner_portfolio_summary;`

---

## Success Criteria

Phase 1 is successful when:
- ✅ owner_identities table has >1,000 records
- ✅ property_ownership links exist
- ✅ entity_principals links exist
- ✅ owner_portfolio_summary shows aggregated portfolios
- ✅ Can find owners with multiple corporations
- ✅ Portfolio lookup returns complete JSON

---

## Files Reference

**SQL Migration**:
- `supabase/migrations/20251005_concordbroker_ownership_schema.sql`

**Python Scripts**:
- `scripts/build_owner_identity_graph.py`

**Documentation**:
- `CONCORDBROKER_AGENT_LION_SPECIFICATION.md`
- `MULTI_AGENT_ARCHITECTURE.md`
- `COMPLETE_EXECUTION_PLAN.md`

---

## Cost Impact

**Additional Monthly Costs**:
- Supabase storage: ~100MB (within free tier)
- Compute: Negligible (materialized views refresh daily)
- **Total**: $0 additional

**One-Time Costs**:
- Identity resolution compute: $0 (runs locally)
- Initial data processing: ~30 minutes

---

## Ready to Deploy?

**Prerequisites**:
- ✅ Supabase access
- ✅ Python environment with packages
- ✅ SUPABASE_SERVICE_ROLE_KEY set

**Deployment Time**: ~20 minutes total
**Risk**: Low (new tables, no changes to existing data)
**Rollback**: Simple (drop new tables if needed)

---

**Status**: READY FOR DEPLOYMENT
**First Action**: Run Step 1 - Deploy ownership schema to Supabase
