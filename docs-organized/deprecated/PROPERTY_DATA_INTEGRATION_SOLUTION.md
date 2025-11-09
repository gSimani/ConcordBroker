# Property Data Integration Solution

## Current Situation
- **Database**: 121,477 properties loaded in `property_assessments` table
- **Frontend**: Shows 0 properties at http://localhost:5174/properties
- **API**: Running on port 8001, but frontend is calling port 8000
- **Issue**: Frontend is looking for `florida_parcels` table, but data is in `property_assessments`

## Root Causes
1. **Table Mismatch**: Frontend queries `florida_parcels`, data is in `property_assessments`
2. **Port Mismatch**: Frontend calls port 8000, API runs on port 8001
3. **Mock Data Override**: main_simple.py returns mock data instead of real data

## Solution Steps

### Step 1: Run this SQL in Supabase SQL Editor

```sql
-- Create view to map property_assessments to florida_parcels structure
CREATE OR REPLACE VIEW florida_parcels AS
SELECT 
    id,
    parcel_id,
    property_address as phy_addr1,
    property_city as phy_city,
    'FL' as phy_state,
    property_zip as phy_zipcd,
    owner_name as own_name,
    owner_address as own_addr1,
    owner_city as own_city,
    owner_state as own_state,
    owner_zip as own_zipcd,
    property_use_code as dor_uc,
    just_value as jv,
    assessed_value as av,
    taxable_value as tv_sd,
    land_value as lnd_val,
    building_value as bldg_val,
    total_sq_ft as lnd_sqfoot,
    living_area as tot_lvg_area,
    year_built as act_yr_blt,
    bedrooms,
    bathrooms,
    county_code,
    county_name,
    CASE 
        WHEN property_use_code LIKE '0%' THEN 'Residential'
        WHEN property_use_code LIKE '1%' THEN 'Commercial'
        WHEN property_use_code LIKE '2%' THEN 'Industrial'
        WHEN property_use_code LIKE '3%' THEN 'Agricultural'
        WHEN property_use_code LIKE '4%' THEN 'Vacant Land'
        ELSE 'Other'
    END as property_type,
    tax_year,
    created_at,
    updated_at
FROM property_assessments;

-- Grant permissions
GRANT SELECT ON florida_parcels TO anon, authenticated;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_property_assessments_address 
ON property_assessments(property_address);

CREATE INDEX IF NOT EXISTS idx_property_assessments_city 
ON property_assessments(property_city);

CREATE INDEX IF NOT EXISTS idx_property_assessments_owner 
ON property_assessments(owner_name);

CREATE INDEX IF NOT EXISTS idx_property_assessments_parcel 
ON property_assessments(parcel_id);

-- Create text search indexes
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_property_assessments_address_trgm 
ON property_assessments USING gin(property_address gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_property_assessments_owner_trgm 
ON property_assessments USING gin(owner_name gin_trgm_ops);

-- Verify the view works
SELECT COUNT(*) as total_properties FROM florida_parcels;
```

### Step 2: Update Frontend to Use Correct API Port

The frontend is currently calling `http://localhost:8000` but the API is running on port 8001.

Options:
1. **Quick Fix**: Update PropertySearch.tsx to use port 8001
2. **Better Fix**: Use environment variable for API URL

### Step 3: Verify Data Flow

After running the SQL and updating the port:

1. **Test API directly**:
```bash
curl http://localhost:8001/api/properties/search?limit=10
```

2. **Check frontend**:
- Open http://localhost:5174/properties
- Should now show properties from the database

### Step 4: Alternative - Direct Property Appraiser Integration

If you prefer to use the Property Appraiser endpoints directly:

```javascript
// In PropertySearch.tsx, change the API calls to:
const response = await fetch(`http://localhost:8001/api/property-appraiser/search?limit=100`);
```

But note: The Property Appraiser endpoints need the SUPABASE_ANON_KEY environment variable set.

## Verification Queries for Supabase

Run these to verify your data:

```sql
-- Check total properties
SELECT COUNT(*) FROM property_assessments;

-- Check counties
SELECT county_name, COUNT(*) as count 
FROM property_assessments 
GROUP BY county_name 
ORDER BY count DESC;

-- Check if florida_parcels view exists
SELECT * FROM florida_parcels LIMIT 5;

-- Check sample properties
SELECT 
    property_address,
    property_city,
    owner_name,
    taxable_value
FROM property_assessments
WHERE property_address IS NOT NULL
LIMIT 10;
```

## Expected Result

After completing these steps:
- http://localhost:5174/properties should show 121,477 properties
- Search functionality should work
- Properties should be filterable by county, value, etc.

## Current Status
- ✅ 121,477 properties loaded in database
- ✅ API running on port 8001
- ✅ Frontend running on port 5174
- ⏳ Need to create florida_parcels view in Supabase
- ⏳ Need to update frontend to use port 8001