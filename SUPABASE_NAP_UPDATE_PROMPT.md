# Supabase Request: Prepare florida_parcels Table for NAP Data Import

## Context
We are importing NAP (Property Characteristics) data from Florida DOR for all 67 counties to populate missing bedroom, bathroom, and property use code data in the `florida_parcels` table.

## Required Information from Supabase

### 1. Current Table Schema
Please provide the current schema for the `florida_parcels` table, specifically:
- All column names and their data types
- Any indexes on `parcel_id` and `county` columns
- Current row count
- Any RLS policies that might affect bulk updates

### 2. Index Optimization
We will be performing UPDATE operations matching on `(parcel_id, county)` pairs for ~9.1M records.

**Question**: Do we have a composite index on `(parcel_id, county)`?

If not, please create one:
```sql
CREATE INDEX CONCURRENTLY idx_florida_parcels_parcel_county
ON florida_parcels(parcel_id, county);
```

### 3. Timeout Configuration
NAP import will update records in batches of 1,000. Each batch may take 1-2 seconds.

**Question**: What is the current `statement_timeout` setting for the `service_role`?

If needed, temporarily increase it:
```sql
ALTER ROLE service_role SET statement_timeout = '300s';
```

### 4. RLS Policy Check
**Question**: Does the `florida_parcels` table have Row Level Security (RLS) enabled?

If yes, we need to ensure the `service_role` can UPDATE all rows:
```sql
-- Check RLS status
SELECT tablename, rowsecurity
FROM pg_tables
WHERE tablename = 'florida_parcels';

-- Check existing policies
SELECT * FROM pg_policies
WHERE tablename = 'florida_parcels';
```

### 5. Missing Columns
NAP data includes these fields. Please confirm all exist in `florida_parcels`:
- `bedrooms` (integer)
- `bathrooms` (integer)
- `units` (integer)
- `stories` (integer)
- `property_use` (text/varchar) - for DOR use codes like "01-05"
- `land_use_code` (text/varchar)
- `total_living_area` (numeric/float)

If any are missing, please add them:
```sql
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS bedrooms INTEGER,
ADD COLUMN IF NOT EXISTS bathrooms INTEGER,
ADD COLUMN IF NOT EXISTS units INTEGER,
ADD COLUMN IF NOT EXISTS stories INTEGER,
ADD COLUMN IF NOT EXISTS property_use VARCHAR(10),
ADD COLUMN IF NOT EXISTS land_use_code VARCHAR(10);
```

### 6. Update Performance Estimate
Given:
- ~9.1M total records in `florida_parcels`
- Updating in batches of 1,000
- ~67 counties to process
- Average 136,000 records per county

**Question**: What is the expected duration for this operation?
**Question**: Should we use a different batch size for better performance?

### 7. Backup Recommendation
Before running the import, should we:
- Create a backup of the `florida_parcels` table?
- Use a staging table first, then merge?
- Run updates directly on the production table?

Please advise on best practices for this large-scale UPDATE operation.

---

## Import Script Details

The Python script will:
1. Download NAP ZIP files from Florida DOR for each county
2. Extract CSV files from each ZIP
3. Parse CSV and map columns:
   - `PARCEL_ID` → `parcel_id`
   - `BEDROOMS` → `bedrooms`
   - `BATHROOMS` → `bathrooms`
   - `NO_BULDNG` → `units`
   - `DOR_UC` → `property_use`
   - etc.
4. Execute UPDATE statements:
   ```python
   supabase.table('florida_parcels')
       .update({'bedrooms': 5, 'bathrooms': 4, ...})
       .eq('parcel_id', '474130030430')
       .eq('county', 'BROWARD')
       .execute()
   ```

## Expected Outcome

After import, the `florida_parcels` table should have:
- Accurate bedroom/bathroom counts for properties
- Correct DOR use codes (e.g., "01-05" instead of "MF_10PLUS")
- Complete building characteristics
- No "Data Not Available" messages in the UI for properties with NAP data
