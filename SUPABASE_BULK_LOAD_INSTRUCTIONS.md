# Supabase Bulk Loading Instructions for Florida Property Appraiser Data

## Critical Issue Summary
- **Expected**: 9,758,470 properties across 62 Florida counties
- **Currently in DB**: Only 61,413 properties (0.6% - just ALACHUA county)
- **Root Cause**: Statement timeout errors (code 57014) causing silent failures

## Data Location & Format
All property data is in CSV format at:
```
C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\{COUNTY}\NAL\*.csv
```

## County Data Sizes (Top 10)
1. **DADE**: 933,276 properties
2. **BROWARD**: 753,242 properties  
3. **PALM BEACH**: 616,436 properties
4. **HILLSBOROUGH**: 524,735 properties
5. **ORANGE**: 445,018 properties
6. **PINELLAS**: 444,821 properties
7. **LEE**: 389,491 properties
8. **POLK**: 309,595 properties
9. **DUVAL**: 305,928 properties
10. **BREVARD**: 283,107 properties

## Recommended Bulk Loading Approach

### 1. Create Staging Table (No Indexes)
```sql
-- Drop existing staging table if exists
DROP TABLE IF EXISTS florida_parcels_staging CASCADE;

-- Create staging table without indexes for fast loading
CREATE TABLE florida_parcels_staging (
    parcel_id VARCHAR(100),
    county VARCHAR(50),
    year INTEGER DEFAULT 2025,
    owner_name VARCHAR(500),
    owner_addr1 VARCHAR(200),
    owner_addr2 VARCHAR(200),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),  -- Note: Only 2 chars
    owner_zip VARCHAR(20),
    phy_addr1 VARCHAR(200),
    phy_addr2 VARCHAR(200),
    phy_city VARCHAR(100),
    phy_state VARCHAR(2),    -- Note: Only 2 chars
    phy_zipcd VARCHAR(20),
    just_value BIGINT,
    taxable_value BIGINT,
    land_value BIGINT,
    land_sqft BIGINT,
    building_value BIGINT,
    land_use_code VARCHAR(10),
    property_use VARCHAR(10),
    property_use_desc VARCHAR(200),
    sale_price BIGINT,
    sale_year INTEGER,
    legal_desc TEXT,
    year_built INTEGER,
    total_living_area INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    data_source VARCHAR(50) DEFAULT 'NAL_2025',
    import_date TIMESTAMP DEFAULT NOW()
);
```

### 2. Session Configuration
```sql
-- Disable timeouts for bulk operations
SET statement_timeout = 0;
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

-- For better performance
SET synchronous_commit = OFF;
SET checkpoint_segments = 100;
SET checkpoint_completion_target = 0.9;
```

### 3. CSV Field Mapping
The CSV files have these column names that map to our database:
- PARCEL_ID → parcel_id
- OWN_NAME → owner_name
- OWN_ADDR1 → owner_addr1
- OWN_ADDR2 → owner_addr2
- OWN_CITY → owner_city
- OWN_STATE → owner_state (TRUNCATE TO 2 CHARS!)
- OWN_ZIPCD → owner_zip
- PHY_ADDR1 → phy_addr1
- PHY_ADDR2 → phy_addr2
- PHY_CITY → phy_city
- PHY_STATE → phy_state (TRUNCATE TO 2 CHARS!)
- PHY_ZIPCD → phy_zipcd
- JV → just_value
- TV_SD → taxable_value
- LND_VAL → land_value
- LND_SQFOOT → land_sqft
- BLD_VAL → building_value
- DOR_UC → land_use_code, property_use
- PA_UC_DESC → property_use_desc
- SALE_PRC1 → sale_price
- SALE_YR1 → sale_year
- LEGAL1 → legal_desc
- ACT_YR_BLT → year_built
- TOT_LVG_AREA → total_living_area
- NO_BDRMS → bedrooms
- NO_BATHS → bathrooms

### 4. COPY Command Template
For each county's CSV file:
```sql
\COPY florida_parcels_staging (
    parcel_id, county, owner_name, owner_addr1, owner_addr2,
    owner_city, owner_state, owner_zip, phy_addr1, phy_addr2,
    phy_city, phy_state, phy_zipcd, just_value, taxable_value,
    land_value, land_sqft, building_value, land_use_code,
    property_use, property_use_desc, sale_price, sale_year,
    legal_desc, year_built, total_living_area, bedrooms, bathrooms
) FROM '{csv_path}' WITH (FORMAT CSV, HEADER TRUE, NULL '');
```

### 5. Merge Staging to Main Table
```sql
-- Insert new records (not already in main table)
INSERT INTO florida_parcels
SELECT * FROM florida_parcels_staging s
ON CONFLICT (parcel_id, county, year) 
DO UPDATE SET 
    owner_name = EXCLUDED.owner_name,
    owner_addr1 = EXCLUDED.owner_addr1,
    owner_city = EXCLUDED.owner_city,
    owner_state = EXCLUDED.owner_state,
    owner_zip = EXCLUDED.owner_zip,
    phy_addr1 = EXCLUDED.phy_addr1,
    phy_city = EXCLUDED.phy_city,
    phy_state = EXCLUDED.phy_state,
    phy_zipcd = EXCLUDED.phy_zipcd,
    just_value = EXCLUDED.just_value,
    taxable_value = EXCLUDED.taxable_value,
    land_value = EXCLUDED.land_value,
    building_value = EXCLUDED.building_value,
    sale_price = EXCLUDED.sale_price,
    sale_year = EXCLUDED.sale_year,
    import_date = EXCLUDED.import_date;

-- Clear staging table for next county
TRUNCATE florida_parcels_staging;
```

### 6. Post-Load Indexes
After ALL data is loaded:
```sql
-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county 
    ON florida_parcels(county);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id 
    ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name 
    ON florida_parcels(owner_name);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr 
    ON florida_parcels(phy_addr1, phy_city);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_just_value 
    ON florida_parcels(just_value);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_year 
    ON florida_parcels(sale_year);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_composite 
    ON florida_parcels(county, year, parcel_id);

-- Analyze for query planner
ANALYZE florida_parcels;
```

### 7. Verification Query
```sql
-- Check final counts by county
SELECT 
    county,
    COUNT(*) as property_count,
    MIN(import_date) as first_import,
    MAX(import_date) as last_import
FROM florida_parcels
GROUP BY county
ORDER BY property_count DESC;

-- Total count
SELECT COUNT(*) as total_properties FROM florida_parcels;
-- Expected: ~9.7 million
```

## Alternative: Direct psql Access

If Supabase support can provide direct psql access, we can automate the entire process:

```bash
# For each county
for county in ALACHUA BAKER BAY ...; do
    psql $DATABASE_URL -c "TRUNCATE florida_parcels_staging;"
    
    # Load all CSV files for this county
    for csv in /path/to/$county/NAL/*.csv; do
        psql $DATABASE_URL -c "\COPY florida_parcels_staging (...) FROM '$csv' CSV HEADER;"
    done
    
    # Merge to main table
    psql $DATABASE_URL -c "INSERT INTO florida_parcels SELECT * FROM florida_parcels_staging ON CONFLICT ..."
done
```

## Critical Notes

1. **State Fields**: MUST truncate OWN_STATE and PHY_STATE to 2 characters
2. **Timeout**: Must set statement_timeout=0 to avoid 57014 errors
3. **Connection**: Use direct connection, not pooled, for bulk operations
4. **Batch Size**: Process one county at a time through staging table
5. **Indexes**: Create AFTER all data is loaded for best performance

## Expected Timeline

With proper COPY commands:
- Small counties (<50k records): 1-2 minutes each
- Medium counties (50k-200k): 2-5 minutes each  
- Large counties (>200k): 5-15 minutes each
- Total estimated time: 2-4 hours for all 9.7 million records

## Support Request

Please assist with:
1. Confirming staging table creation
2. Setting up direct database access for COPY operations
3. Monitoring the bulk load progress
4. Verifying final counts match expectations

This approach will resolve the statement timeout issues and successfully load all 9.7 million Florida property records.