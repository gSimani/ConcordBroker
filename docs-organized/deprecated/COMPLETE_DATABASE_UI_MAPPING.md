# Complete Database to UI Mapping Document

## Executive Summary

This document provides the complete mapping between database tables/fields and UI components in ConcordBroker. Based on analysis of the codebase, the UI expects specific table names and field structures that must be implemented exactly as specified.

## Critical Findings

### Current Database State
- **Status**: COMPLETELY EMPTY (0 tables)
- **Supabase URL**: https://mogulpssjdlxjvstqfee.supabase.co
- **Connection**: Working with proper credentials

### UI Expectations
The React frontend (`usePropertyData.ts`) expects these specific tables:
1. `florida_parcels` - Main property data
2. `properties` - Enhanced property information  
3. `property_sales_history` - Sales records
4. `nav_assessments` - Non-ad valorem assessments
5. `sunbiz_corporate` - Business entity data

## Database Schema Requirements

### 1. florida_parcels (PRIMARY TABLE)
```sql
CREATE TABLE florida_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Physical Address
    phy_addr1 TEXT,
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    
    -- Owner Information
    owner_name TEXT,
    owner_addr1 TEXT,
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Values (UI expects these exact names)
    assessed_value DECIMAL(15,2),
    taxable_value DECIMAL(15,2),
    just_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    land_value DECIMAL(15,2),
    building_value DECIMAL(15,2),
    improvement_value DECIMAL(15,2),
    
    -- Building Details
    year_built INTEGER,
    eff_year_built INTEGER,
    total_living_area INTEGER,
    living_area INTEGER,
    heated_area INTEGER,
    land_sqft DECIMAL(12,2),
    lot_size DECIMAL(12,2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    units INTEGER,
    total_units INTEGER,
    
    -- Property Classification
    property_use VARCHAR(20),
    usage_code VARCHAR(20),
    use_code VARCHAR(20),
    property_use_desc TEXT,
    property_type VARCHAR(100),
    use_description TEXT,
    
    -- Tax Information
    tax_amount DECIMAL(15,2),
    homestead_exemption VARCHAR(1),
    homestead VARCHAR(1),
    other_exemptions TEXT,
    exemption_codes TEXT,
    
    -- Sale Information
    sale_price DECIMAL(15,2),
    sale_date DATE,
    sale_type VARCHAR(50),
    deed_type VARCHAR(50),
    or_book VARCHAR(20),
    or_page VARCHAR(20),
    book_page VARCHAR(50),
    recording_book_page VARCHAR(50),
    cin VARCHAR(50),
    clerk_instrument_number VARCHAR(50),
    
    -- Additional Fields
    sketch_url TEXT,
    record_link TEXT,
    vi_code VARCHAR(10),
    is_distressed BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    land_factors JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Critical indexes for UI queries
CREATE INDEX idx_florida_parcels_parcel ON florida_parcels(parcel_id);
CREATE INDEX idx_florida_parcels_address ON florida_parcels(phy_addr1);
CREATE INDEX idx_florida_parcels_owner ON florida_parcels(owner_name);
```

### 2. properties (FALLBACK TABLE)
```sql
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    property_address TEXT,
    city VARCHAR(100),
    state VARCHAR(2) DEFAULT 'FL',
    zip_code VARCHAR(10),
    owner_name TEXT,
    
    -- Values
    assessed_value DECIMAL(15,2),
    market_value DECIMAL(15,2),
    
    -- Building Info
    year_built INTEGER,
    total_sqft INTEGER,
    lot_size_sqft DECIMAL(12,2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    property_type VARCHAR(100),
    
    -- Sale Info
    last_sale_price DECIMAL(15,2),
    last_sale_date DATE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3. property_sales_history
```sql
CREATE TABLE property_sales_history (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    sale_date DATE,
    sale_price VARCHAR(20), -- UI expects string
    sale_type VARCHAR(100),
    qualified_sale BOOLEAN DEFAULT TRUE,
    is_distressed BOOLEAN DEFAULT FALSE,
    is_bank_sale BOOLEAN DEFAULT FALSE,
    is_cash_sale BOOLEAN DEFAULT FALSE,
    book VARCHAR(20),
    page VARCHAR(20),
    document_type VARCHAR(100),
    grantor_name TEXT,
    grantee_name TEXT,
    vi_code VARCHAR(10),
    sale_reason TEXT,
    book_page VARCHAR(50),
    cin VARCHAR(50),
    record_link TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sales_history_parcel ON property_sales_history(parcel_id);
CREATE INDEX idx_sales_history_date ON property_sales_history(sale_date DESC);
```

### 4. nav_assessments
```sql
CREATE TABLE nav_assessments (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    assessment_year INTEGER,
    district_name VARCHAR(200),
    assessment_type VARCHAR(100),
    total_assessment DECIMAL(15,2),
    unit_amount DECIMAL(15,2),
    units INTEGER,
    description TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_nav_parcel ON nav_assessments(parcel_id);
```

### 5. sunbiz_corporate
```sql
CREATE TABLE sunbiz_corporate (
    id SERIAL PRIMARY KEY,
    corporate_name TEXT,
    entity_type VARCHAR(100),
    status VARCHAR(50),
    filing_date DATE,
    principal_address TEXT,
    mailing_address TEXT,
    registered_agent TEXT,
    officers TEXT, -- UI searches within this field
    document_number VARCHAR(50),
    fei_number VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sunbiz_name ON sunbiz_corporate(corporate_name);
CREATE INDEX idx_sunbiz_officers ON sunbiz_corporate USING GIN(to_tsvector('english', officers));
CREATE INDEX idx_sunbiz_addresses ON sunbiz_corporate(principal_address, mailing_address);
```

## UI Component Data Requirements

### 1. Property Search Component (`PropertySearch.tsx`)

**Expected Query Pattern:**
```javascript
// Search by parcel ID
supabase.from('florida_parcels')
  .select('*')
  .eq('parcel_id', searchValue)

// Search by address
supabase.from('florida_parcels')
  .select('*')
  .or(`phy_addr1.ilike.%${address}%,parcel_id.eq.${address}`)
```

**Required Fields:**
- `parcel_id`
- `phy_addr1`, `phy_city`, `phy_zipcd`
- `owner_name`
- `total_value` or `taxable_value`
- `property_use_desc` or `property_type`
- `year_built`
- `living_area` or `total_living_area`
- `bedrooms`, `bathrooms`

### 2. Property Profile Hook (`usePropertyData.ts`)

**Data Flow:**
1. First tries `florida_parcels` table
2. Falls back to `properties` table
3. Fetches related data from:
   - `property_sales_history`
   - `nav_assessments`
   - `sunbiz_corporate`

**Field Mapping in Code:**
```javascript
bcpaData = {
  parcel_id: floridaParcel.parcel_id,
  property_address_full: `${floridaParcel.phy_addr1}, ${floridaParcel.phy_city}, FL ${floridaParcel.phy_zipcd}`,
  assessed_value: parseNumber(floridaParcel.assessed_value),
  taxable_value: parseNumber(floridaParcel.taxable_value),
  market_value: parseNumber(floridaParcel.just_value),
  // ... etc
}
```

### 3. Dashboard Components

**Tracked Properties:**
```sql
CREATE TABLE tracked_properties (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    parcel_id VARCHAR(50),
    tracking_type VARCHAR(50),
    alert_preferences JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**User Alerts:**
```sql
CREATE TABLE user_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    alert_type VARCHAR(50),
    message TEXT,
    property_id VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Data Loading Priority

### Phase 1: Critical Tables (IMMEDIATE)
1. `florida_parcels` - Load at least 1000 records
2. `property_sales_history` - Recent sales data
3. `sunbiz_corporate` - Business entities

### Phase 2: Supporting Tables (Day 2)
1. `nav_assessments` - Tax assessments
2. `properties` - Backup property data
3. `tracked_properties` - User tracking

### Phase 3: Enhancement (Week 1)
1. Full Florida parcel data
2. Historical sales (5 years)
3. Complete Sunbiz dataset

## Implementation Script

```sql
-- Run this IMMEDIATELY in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create all required tables
-- [Include all CREATE TABLE statements from above]

-- Enable Row Level Security
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;

-- Create public read policies
CREATE POLICY "Public read access" ON florida_parcels FOR SELECT USING (true);
CREATE POLICY "Public read access" ON properties FOR SELECT USING (true);
CREATE POLICY "Public read access" ON property_sales_history FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nav_assessments FOR SELECT USING (true);
CREATE POLICY "Public read access" ON sunbiz_corporate FOR SELECT USING (true);

-- Create real-time publication
ALTER PUBLICATION supabase_realtime ADD TABLE florida_parcels;
ALTER PUBLICATION supabase_realtime ADD TABLE property_sales_history;
```

## Sample Data Loader

```python
# load_sample_data.py
import os
from supabase import create_client
from datetime import datetime, timedelta
import random

# Initialize Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Sample data for florida_parcels
sample_parcels = []
for i in range(100):
    parcel = {
        "parcel_id": f"064210010{i:04d}",
        "phy_addr1": f"{random.randint(100,9999)} SW {random.randint(1,200)} ST",
        "phy_city": random.choice(["FORT LAUDERDALE", "HOLLYWOOD", "PEMBROKE PINES"]),
        "phy_state": "FL",
        "phy_zipcd": f"333{random.randint(10,99)}",
        "owner_name": f"OWNER {i} LLC",
        "assessed_value": random.randint(100000, 1000000),
        "taxable_value": random.randint(80000, 900000),
        "just_value": random.randint(120000, 1200000),
        "year_built": random.randint(1960, 2023),
        "bedrooms": random.randint(2, 5),
        "bathrooms": random.randint(1, 4),
        "living_area": random.randint(1000, 5000),
        "property_type": random.choice(["SINGLE FAMILY", "CONDO", "TOWNHOUSE"])
    }
    sample_parcels.append(parcel)

# Insert sample data
response = supabase.table('florida_parcels').insert(sample_parcels).execute()
print(f"Inserted {len(sample_parcels)} sample parcels")
```

## Verification Checklist

- [ ] All tables created in Supabase
- [ ] Indexes applied for performance
- [ ] RLS policies configured
- [ ] Sample data loaded
- [ ] API endpoints tested
- [ ] UI components loading data
- [ ] Search functionality working
- [ ] Property profiles displaying
- [ ] Real-time subscriptions active

## Common Issues & Solutions

### Issue: "relation does not exist"
**Solution**: Tables not created. Run the SQL script in Supabase.

### Issue: UI shows no data
**Solution**: Check table names match exactly (case-sensitive).

### Issue: Slow queries
**Solution**: Ensure indexes are created on searched fields.

### Issue: Permission denied
**Solution**: Check RLS policies allow public read access.

## Support Resources

- Supabase Dashboard: Check table viewer
- Query Logs: Monitor slow queries
- Real-time Inspector: Verify subscriptions
- API Logs: Check for errors

## Next Steps

1. **Immediate**: Copy SQL to Supabase and execute
2. **Today**: Load sample data using Python script
3. **Tomorrow**: Import full Florida dataset
4. **This Week**: Complete all data migrations
5. **Next Week**: Optimize queries and add caching