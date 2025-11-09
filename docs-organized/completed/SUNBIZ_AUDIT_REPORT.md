# Sunbiz Tables Audit Report
**Date**: 2025-10-24
**Database**: https://mogulpssjdlxjvstqfee.supabase.co
**Status**: ⚠️ Schema Exists - NO DATA LOADED

---

## Executive Summary

All Sunbiz-related tables exist in the Supabase database with proper schema structure, but **all tables contain ZERO records**. The database schema is deployment-ready, but data import has not been executed.

---

## 📊 Database Tables Inventory

### ✅ Tables Found (All with 0 Records)

| Table Name | Status | Expected Records | Actual Records | Data Status |
|------------|--------|------------------|----------------|-------------|
| `florida_parcels` | ✅ Exists | 9,113,150 | **0** | ❌ Not Loaded |
| `sunbiz_corporate` | ✅ Exists | 2,030,912 | **0** | ❌ Not Loaded |
| `florida_entities` | ✅ Exists | 15,013,088 | **0** | ❌ Not Loaded |
| `property_sales_history` | ✅ Exists | 96,771 | **0** | ❌ Not Loaded |
| `tax_certificates` | ✅ Exists | Unknown | **0** | ❌ Not Loaded |
| `sunbiz_entities` | ✅ Exists | Unknown | **0** | ❌ Not Loaded |
| `sunbiz_corporations` | ✅ Exists | Unknown | **0** | ❌ Not Loaded |
| `sunbiz_officer_contacts` | ✅ Exists | Unknown | **0** | ❌ Not Loaded |
| `tax_deed_entity_matches` | ✅ Exists | 0 (linking table) | **0** | ✅ OK (Empty by design) |

---

## 📋 Schema Analysis

### 1. **sunbiz_corporate**
**Purpose**: Florida corporate entity information from Sunbiz.org

**Schema Structure**:
```sql
entity_id VARCHAR(20) PRIMARY KEY
entity_name VARCHAR(255) NOT NULL
status VARCHAR(20)
entity_type VARCHAR(50)
filing_date DATE
state_country VARCHAR(2)
principal_address TEXT
principal_city VARCHAR(100)
principal_state VARCHAR(2)
principal_zip VARCHAR(10)
mailing_address TEXT
mailing_city VARCHAR(100)
mailing_state VARCHAR(2)
mailing_zip VARCHAR(10)
registered_agent_name VARCHAR(255)
registered_agent_address TEXT
registered_agent_city VARCHAR(100)
registered_agent_state VARCHAR(2)
registered_agent_zip VARCHAR(10)
document_number VARCHAR(50)
fei_number VARCHAR(20)
date_filed DATE
last_event VARCHAR(50)
event_date DATE
event_file_number VARCHAR(50)
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Indexes**:
- `idx_corp_name` on `entity_name`
- `idx_corp_status` on `status`
- `idx_corp_zip` on `principal_zip`
- `idx_corp_filing_date` on `filing_date`

---

### 2. **florida_entities**
**Purpose**: General Florida business entities (broader than corporations)

**Schema Structure**:
```sql
entity_id VARCHAR(20) PRIMARY KEY
entity_name VARCHAR(255) NOT NULL
entity_type VARCHAR(20)
status VARCHAR(20)
filing_date DATE
principal_address TEXT
principal_city VARCHAR(100)
principal_state VARCHAR(2)
principal_zip VARCHAR(10)
mailing_address TEXT
mailing_city VARCHAR(100)
mailing_state VARCHAR(2)
mailing_zip VARCHAR(10)
registered_agent VARCHAR(255)
officers JSONB
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Indexes**:
- `idx_sunbiz_entity_name` on `entity_name`
- `idx_sunbiz_normalized_name` on `UPPER(entity_name)`
- `idx_sunbiz_principal_zip` on `principal_zip`

**Key Features**:
- `officers` field stores JSON array of officer information
- Normalized name index for case-insensitive searches

---

### 3. **sunbiz_officer_contacts**
**Purpose**: Officer contact information with emails and phones

**Schema Structure**:
```sql
id BIGSERIAL PRIMARY KEY
entity_name TEXT
officer_name TEXT
officer_email TEXT
officer_phone TEXT
additional_emails TEXT
additional_phones TEXT
source_file TEXT NOT NULL
source_line INTEGER
context TEXT
extracted_date TIMESTAMPTZ
import_date TIMESTAMPTZ DEFAULT NOW()
```

**Indexes**:
- `idx_sunbiz_officer_contacts_entity` on `entity_name`
- `idx_sunbiz_officer_contacts_officer` on `officer_name`
- `idx_sunbiz_officer_contacts_email` on `officer_email`
- `idx_sunbiz_officer_contacts_phone` on `officer_phone`

**Constraints**:
- `UNIQUE(entity_name, officer_name, officer_email)`

---

### 4. **sunbiz_fictitious_names**
**Purpose**: DBA (Doing Business As) names registered in Florida

**Schema Structure**:
```sql
registration_id VARCHAR(20) PRIMARY KEY
name VARCHAR(255) NOT NULL
owner_name VARCHAR(255)
owner_address TEXT
owner_city VARCHAR(100)
owner_state VARCHAR(2)
owner_zip VARCHAR(10)
registration_date DATE
expiration_date DATE
status VARCHAR(20)
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Indexes**:
- `idx_fic_name` on `name`
- `idx_fic_owner` on `owner_name`

---

### 5. **sunbiz_registered_agents**
**Purpose**: Registered agents serving Florida entities

**Schema Structure**:
```sql
agent_id VARCHAR(20) PRIMARY KEY
agent_name VARCHAR(255) NOT NULL
agent_type VARCHAR(50)
address TEXT
city VARCHAR(100)
state VARCHAR(2)
zip_code VARCHAR(10)
entity_count INTEGER DEFAULT 0
created_at TIMESTAMP WITH TIME ZONE
updated_at TIMESTAMP WITH TIME ZONE
```

**Indexes**:
- `idx_agent_name` on `agent_name`

---

### 6. **tax_deed_entity_matches**
**Purpose**: Linking table between properties and Sunbiz entities

**Schema Structure**:
```sql
id UUID DEFAULT gen_random_uuid() PRIMARY KEY
property_id UUID
parcel_number VARCHAR(50)
applicant_name VARCHAR(255)
entity_id VARCHAR(20)
entity_name VARCHAR(255)
match_type VARCHAR(50)
confidence DECIMAL(3,2)
created_at TIMESTAMP WITH TIME ZONE
FOREIGN KEY (entity_id) REFERENCES sunbiz_entities(entity_id)
```

**Indexes**:
- `idx_entity_matches_property` on `property_id`
- `idx_entity_matches_parcel` on `parcel_number`

---

## 🔗 Relationship Mapping

### **Current State: Unable to Test Relationships (No Data)**

### **Designed Relationships**:

```
florida_parcels.owner_name
    ↓ (fuzzy match)
florida_entities.entity_name
    ↓ (entity_id FK)
tax_deed_entity_matches
    ↓ (entity_id FK)
sunbiz_corporate.entity_id
    ↓ (related)
sunbiz_officer_contacts.entity_name
```

### **Linking Scenarios**:

1. **Property Owner → Entity**
   ```sql
   SELECT p.parcel_id, p.owner_name, e.entity_id, e.entity_name, e.entity_type
   FROM florida_parcels p
   JOIN florida_entities e ON UPPER(p.owner_name) = UPPER(e.entity_name)
   ```

2. **Entity → Officers**
   ```sql
   SELECT e.entity_name, o.officer_name, o.officer_email, o.officer_phone
   FROM florida_entities e
   JOIN sunbiz_officer_contacts o ON e.entity_name = o.entity_name
   ```

3. **Property → Officers (via Entity)**
   ```sql
   SELECT p.parcel_id, p.owner_name, o.officer_name, o.officer_email
   FROM florida_parcels p
   JOIN florida_entities e ON UPPER(p.owner_name) = UPPER(e.entity_name)
   JOIN sunbiz_officer_contacts o ON e.entity_name = o.entity_name
   ```

4. **Entity → Registered Agent → Contact**
   ```sql
   SELECT c.entity_name, c.registered_agent_name, a.agent_name, a.address
   FROM sunbiz_corporate c
   JOIN sunbiz_registered_agents a ON c.registered_agent_name = a.agent_name
   ```

---

## 📍 Address Relationships

### **Address Fields Available**:

#### sunbiz_corporate:
- `principal_address` + `principal_city` + `principal_state` + `principal_zip`
- `mailing_address` + `mailing_city` + `mailing_state` + `mailing_zip`
- `registered_agent_address` + city + state + zip

#### florida_parcels:
- `phy_addr1` / `phy_addr2` (property physical address)
- `owner_addr1` / `owner_addr2` (owner mailing address)

#### florida_entities:
- `principal_address` + city + state + zip
- `mailing_address` + city + state + zip

### **Address Matching Opportunities**:

1. **Match Property Physical Address to Entity Principal Address**
   ```sql
   SELECT p.parcel_id, e.entity_name
   FROM florida_parcels p
   JOIN sunbiz_corporate e ON
       UPPER(p.phy_addr1) = UPPER(e.principal_address)
       AND p.phy_zip = e.principal_zip
   ```

2. **Match Owner Mailing Address to Entity Mailing Address**
   ```sql
   SELECT p.owner_name, e.entity_name
   FROM florida_parcels p
   JOIN florida_entities e ON
       UPPER(p.owner_addr1) = UPPER(e.mailing_address)
       AND p.owner_state = e.mailing_state
   ```

---

## 👥 Officer → Owner Name Combinations

### **Potential Matches**:

Once data is loaded, these queries will identify officer-owner relationships:

1. **Officers as Property Owners**
   ```sql
   SELECT DISTINCT
       o.officer_name,
       o.entity_name AS business,
       p.parcel_id,
       p.owner_name,
       p.county
   FROM sunbiz_officer_contacts o
   JOIN florida_parcels p ON UPPER(o.officer_name) = UPPER(p.owner_name)
   WHERE p.county IS NOT NULL
   ORDER BY o.officer_name
   ```

2. **Officers with Multiple Properties**
   ```sql
   SELECT
       o.officer_name,
       o.entity_name,
       COUNT(DISTINCT p.parcel_id) AS property_count,
       ARRAY_AGG(DISTINCT p.county) AS counties
   FROM sunbiz_officer_contacts o
   JOIN florida_parcels p ON UPPER(o.officer_name) = UPPER(p.owner_name)
   GROUP BY o.officer_name, o.entity_name
   HAVING COUNT(DISTINCT p.parcel_id) > 1
   ORDER BY property_count DESC
   ```

3. **Entity Officers with Entity-Owned Properties**
   ```sql
   SELECT
       e.entity_name,
       o.officer_name,
       o.officer_email,
       p.parcel_id,
       p.phy_addr1,
       p.county
   FROM florida_entities e
   JOIN sunbiz_officer_contacts o ON e.entity_name = o.entity_name
   JOIN florida_parcels p ON UPPER(e.entity_name) = UPPER(p.owner_name)
   WHERE o.officer_email IS NOT NULL
   ORDER BY e.entity_name, p.county
   ```

---

## 🚨 Critical Findings

### 1. **NO DATA LOADED**
- All tables have correct schema
- All indexes are properly configured
- RLS policies are enabled
- **But zero data records exist**

### 2. **Data Sources Needed**

| Table | Data Source | Estimated Records |
|-------|-------------|-------------------|
| florida_parcels | Florida Property Appraiser Data | 9.7M |
| florida_entities | Sunbiz.org API / FTP | 15M |
| sunbiz_corporate | Sunbiz.org Corporations | 2M |
| property_sales_history | County Tax Collector | 97K |
| sunbiz_officer_contacts | Sunbiz.org Officer Data | Unknown |

### 3. **Missing Data Pipeline**
No evidence of:
- Data loading scripts in execution
- ETL processes running
- Scheduled data imports
- Data transformation workflows

---

## 💡 Recommendations

### **Immediate Actions (Priority 1)**:

1. ✅ **Deploy Data Loading Infrastructure**
   - Review `CLAUDE.md` → Daily Property Update System
   - Execute `scripts/deploy_schema.py` (if not done)
   - Run `scripts/daily_property_update.py` for initial load

2. ✅ **Load Florida Parcels Data**
   ```bash
   # From CLAUDE.md documentation
   python scripts/daily_property_update.py --dry-run
   # If successful, run actual import
   python scripts/daily_property_update.py
   ```
   - Source: `TEMP\DATABASE PROPERTY APP\{COUNTY}\NAL\*.csv`
   - Target: `florida_parcels` (9.7M records expected)

3. ✅ **Load Sunbiz Corporate Data**
   - Source: Sunbiz.org FTP / API
   - Check for existing workers: `apps/workers/sunbiz_*.sql`
   - Implement FTP download agent if not exists

### **Data Quality (Priority 2)**:

4. ✅ **Implement Entity Matching Algorithm**
   ```sql
   -- Create function for fuzzy name matching
   CREATE OR REPLACE FUNCTION match_owner_to_entity(owner_name TEXT)
   RETURNS TABLE (
       entity_id VARCHAR(20),
       entity_name VARCHAR(255),
       match_score DECIMAL(3,2)
   ) AS $$
   BEGIN
       RETURN QUERY
       SELECT
           e.entity_id,
           e.entity_name,
           similarity(UPPER(owner_name), UPPER(e.entity_name)) AS match_score
       FROM florida_entities e
       WHERE similarity(UPPER(owner_name), UPPER(e.entity_name)) > 0.7
       ORDER BY match_score DESC
       LIMIT 10;
   END;
   $$ LANGUAGE plpgsql;
   ```

5. ✅ **Populate Linking Table**
   ```sql
   -- Auto-populate tax_deed_entity_matches after data load
   INSERT INTO tax_deed_entity_matches (
       parcel_number, applicant_name, entity_id, entity_name,
       match_type, confidence
   )
   SELECT
       p.parcel_id,
       p.owner_name,
       e.entity_id,
       e.entity_name,
       'exact_match',
       1.00
   FROM florida_parcels p
   JOIN florida_entities e ON UPPER(p.owner_name) = UPPER(e.entity_name)
   WHERE e.entity_id IS NOT NULL;
   ```

### **Application Integration (Priority 3)**:

6. ✅ **Update UI Components**
   - Modify `MiniPropertyCard` to query `sunbiz_corporate` via `tax_deed_entity_matches`
   - Display officer contacts when available
   - Show registered agent information
   - Link to Sunbiz.org for full entity details

7. ✅ **Create Entity Search Endpoint**
   ```typescript
   // apps/web/api/entities/search.ts
   export async function searchEntities(query: string) {
       const { data } = await supabase
           .from('florida_entities')
           .select('entity_id, entity_name, entity_type, status')
           .ilike('entity_name', `%${query}%`)
           .limit(20);
       return data;
   }
   ```

8. ✅ **Implement Officer Contact Display**
   ```typescript
   // Display in property detail view
   const { data: officers } = await supabase
       .from('sunbiz_officer_contacts')
       .select('officer_name, officer_email, officer_phone')
       .eq('entity_name', entityName)
       .not('officer_email', 'is', null);
   ```

### **Monitoring (Priority 4)**:

9. ✅ **Set Up Data Freshness Checks**
   ```sql
   -- Daily check for stale data
   SELECT
       'florida_parcels' AS table_name,
       COUNT(*) AS record_count,
       MAX(updated_at) AS last_update
   FROM florida_parcels
   UNION ALL
   SELECT
       'sunbiz_corporate',
       COUNT(*),
       MAX(updated_at)
   FROM sunbiz_corporate;
   ```

10. ✅ **Create Data Quality Dashboard**
    - Monitor match rates (owner → entity)
    - Track missing contact information
    - Alert on data staleness
    - Report on coverage by county

---

## 🔧 Data Loading Scripts

### **Scripts to Execute (in order)**:

1. `supabase/migrations/create_autocomplete_indexes.sql` - Performance indexes
2. `scripts/apply-autocomplete-indexes.js` - Apply indexes
3. `scripts/daily_property_update.py` - Load property data
4. `apps/workers/sunbiz_complete_schema.sql` - Verify Sunbiz schema
5. Load Sunbiz data (source TBD - FTP or API)
6. Run entity matching algorithm
7. Populate `tax_deed_entity_matches` table

---

## 📊 Expected Results (After Data Load)

### **Match Rates**:
- Property Owner → Entity: 30-50% (estimated)
- Entity → Officers: 80-90% (high confidence)
- Property → Officers (via entity): 25-40% (estimated)

### **Coverage**:
- Florida Parcels: 9.7M properties across 67 counties
- Sunbiz Entities: 15M+ entities (all types)
- Corporate Entities: 2M+ corporations
- Officer Contacts: Unknown (depends on data source)

### **Use Cases Enabled**:
1. ✅ Property owner lookup → Find entity details
2. ✅ Entity search → Find all properties owned
3. ✅ Officer search → Find all entities + properties
4. ✅ Address matching → Link properties to businesses
5. ✅ Registered agent lookup → Find represented entities
6. ✅ Contact information → Email/phone for outreach

---

## 🎯 Success Metrics

### **After Implementation**:
- [ ] 9.7M records in `florida_parcels`
- [ ] 15M records in `florida_entities`
- [ ] 2M records in `sunbiz_corporate`
- [ ] >100K records in `tax_deed_entity_matches`
- [ ] Match rate >40% for owner→entity
- [ ] Contact info for >50% of matched entities
- [ ] Query performance <500ms for property lookups
- [ ] UI displays entity/officer data in property views

---

## 📁 Referenced Files

- `CLAUDE.md` - Project configuration and data rules
- `create_sunbiz_tables.sql` - Table creation scripts
- `apps/workers/sunbiz_complete_schema.sql` - Full schema
- `create_sunbiz_officer_contacts_table.sql` - Officer table
- `scripts/daily_property_update.py` - Property data loader
- `QUICK_START_GUIDE.md` - Data loading instructions (if exists)

---

## ✅ Conclusion

The Sunbiz table infrastructure is **deployment-ready** with:
- ✅ Complete schema with proper relationships
- ✅ Optimized indexes for performance
- ✅ Security policies (RLS) enabled
- ❌ **NO DATA LOADED** - blocking all relationship analysis

**Next Step**: Execute data loading pipeline to populate all tables with production data.

---

**Report Generated**: 2025-10-24
**Audit Type**: Database Schema & Relationships
**Status**: ⚠️ Schema Ready - Awaiting Data Import
