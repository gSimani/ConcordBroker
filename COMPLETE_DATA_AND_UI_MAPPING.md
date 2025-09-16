# Complete Data and UI Mapping Documentation

## Current Database Status

Based on our analysis, here's what we have and what's needed:

### ✅ Data We Have (789,884 Florida parcels loaded)
- **florida_parcels**: 789,884 records - Property base data
- **properties**: 3 records - Needs more data
- **property_sales_history**: 3 records - Needs SDF data load
- **nav_assessments**: 1 record - Needs NAV/NAP data load
- **sunbiz_corporate**: 0 records - Needs Sunbiz SFTP download

### ❌ Data We Need to Download

1. **Florida Revenue Portal** (https://floridarevenue.com/property/dataportal/)
   - SDF (Sales Data) - Currently only 3 records, need thousands
   - NAV (Assessments) - Currently only 1 record, need thousands
   - NAP (Non-Ad Valorem) - Missing
   - TPP (Tangible Property) - Missing

2. **Sunbiz SFTP** (sftp.floridados.gov)
   - Business entities - Currently 0 records
   - Officers/Directors - Missing
   - Corporate filings - Missing

3. **Broward County Daily Index**
   - Daily property records - Not loaded
   - Official records - Not loaded

## Complete UI Data Mapping

### 🔍 Property Search Page (`/properties`)

**Data Flow:**
```
User searches → florida_parcels table → Display results
```

**Database Fields → UI Components:**

| UI Component | Database Table | Fields Used | Query |
|-------------|---------------|-------------|-------|
| **Search Bar** | florida_parcels | phy_addr1, owner_name, parcel_id | `SELECT * FROM florida_parcels WHERE phy_addr1 ILIKE '%search%' OR owner_name ILIKE '%search%'` |
| **Property Cards** | florida_parcels | | |
| - Address | florida_parcels | phy_addr1, phy_city, phy_zipcd | Concatenate fields |
| - Price | florida_parcels | assessed_value or sale_price | Display formatted |
| - Owner | florida_parcels | owner_name | Direct display |
| - Details | florida_parcels | bedrooms, bathrooms, total_living_area | Format as "3 bed, 2 bath, 2000 sqft" |
| **Filters** | | | |
| - Price Range | florida_parcels | assessed_value | WHERE assessed_value BETWEEN min AND max |
| - Bedrooms | florida_parcels | bedrooms | WHERE bedrooms >= selected |
| - Year Built | florida_parcels | year_built | WHERE year_built >= selected |
| - Property Type | florida_parcels | property_type | WHERE property_type = selected |

### 🏠 Property Profile Page (`/property/[id]`)

**Tab Structure and Data Sources:**

#### Overview Tab
| Section | Database Fields | Display Format |
|---------|----------------|----------------|
| **Header** | | |
| Address | phy_addr1, phy_city, phy_state, phy_zipcd | "123 Main St, Fort Lauderdale, FL 33301" |
| Parcel ID | parcel_id | "Parcel: 064210010010" |
| Owner | owner_name | "Owner: John Smith LLC" |
| **Values** | | |
| Market Value | just_value | "$450,000" |
| Assessed Value | assessed_value | "$425,000" |
| Taxable Value | taxable_value | "$400,000" |
| Land Value | land_value | "$150,000" |
| Building Value | building_value | "$275,000" |
| **Characteristics** | | |
| Year Built | year_built | "Built: 1995" |
| Living Area | total_living_area | "2,500 sq ft" |
| Lot Size | land_sqft | "8,000 sq ft lot" |
| Beds/Baths | bedrooms, bathrooms | "4 beds, 3 baths" |

#### Sales History Tab
| Field | Database Source | Query |
|-------|----------------|-------|
| Sale Date | property_sales_history.sale_date | `SELECT * FROM property_sales_history WHERE parcel_id = ? ORDER BY sale_date DESC` |
| Sale Price | property_sales_history.sale_price | Format as currency |
| Buyer | property_sales_history.grantee_name | Display name |
| Seller | property_sales_history.grantor_name | Display name |
| Type | property_sales_history.sale_type | "Warranty Deed" |

#### Tax Information Tab
| Field | Database Source | Calculation |
|-------|----------------|-------------|
| Annual Tax | nav_assessments.total_assessment | SUM all assessments |
| Tax Rate | property_tax_info.millage_rate | Display as percentage |
| Exemptions | florida_parcels.homestead_exemption | List all exemptions |
| Special Assessments | nav_assessments.district_name, amount | List each district |

#### Business Entities Tab (Sunbiz)
| Field | Database Source | Query |
|-------|----------------|-------|
| Company Name | sunbiz_corporate.corporate_name | Match by address or owner name |
| Entity Type | sunbiz_corporate.entity_type | "LLC", "Corporation", etc. |
| Status | sunbiz_corporate.status | "Active", "Inactive" |
| Officers | sunbiz_corporate.officers | Parse JSON field |
| Address | sunbiz_corporate.principal_address | Display full address |

### 📊 Dashboard (`/dashboard`)

| Widget | Data Source | Query/Calculation |
|--------|------------|-------------------|
| **Tracked Properties** | tracked_properties JOIN florida_parcels | `SELECT * FROM tracked_properties WHERE user_id = ?` |
| **Market Stats** | | |
| - Avg Price | florida_parcels | `AVG(assessed_value)` |
| - Recent Sales | property_sales_history | `COUNT(*) WHERE sale_date > NOW() - 30 days` |
| - Price Trend | property_sales_history | Month-over-month % change |
| **Alerts** | user_alerts | `SELECT * FROM user_alerts WHERE user_id = ? ORDER BY created_at DESC` |

### 🤖 AI Search (`/ai-search`)

**Natural Language Processing:**
```sql
-- Example: "Find properties owned by LLCs under $500k"
SELECT * FROM florida_parcels p
JOIN sunbiz_corporate s ON p.owner_name ILIKE '%' || s.corporate_name || '%'
WHERE s.entity_type = 'LLC'
AND p.assessed_value < 500000
```

## Database Optimization for Fast Queries

### Required Indexes (MUST CREATE)
```sql
-- Critical for search performance
CREATE INDEX idx_parcels_address_gin ON florida_parcels 
    USING gin(to_tsvector('english', phy_addr1));

CREATE INDEX idx_parcels_owner_gin ON florida_parcels 
    USING gin(to_tsvector('english', owner_name));

CREATE INDEX idx_parcels_county ON florida_parcels(county);
CREATE INDEX idx_parcels_assessed ON florida_parcels(assessed_value);
CREATE INDEX idx_sales_parcel_date ON property_sales_history(parcel_id, sale_date DESC);
CREATE INDEX idx_nav_parcel ON nav_assessments(parcel_id);
CREATE INDEX idx_sunbiz_name ON sunbiz_corporate(corporate_name);
```

### Materialized View for Ultra-Fast Search
```sql
CREATE MATERIALIZED VIEW property_search_fast AS
SELECT 
    p.parcel_id,
    p.phy_addr1 || ', ' || p.phy_city || ', FL ' || p.phy_zipcd as full_address,
    p.owner_name,
    p.assessed_value,
    p.year_built,
    p.bedrooms,
    p.bathrooms,
    p.total_living_area,
    s.sale_price as last_sale_price,
    s.sale_date as last_sale_date,
    n.total_assessment as nav_assessment,
    b.corporate_name as business_entity
FROM florida_parcels p
LEFT JOIN LATERAL (
    SELECT sale_price, sale_date 
    FROM property_sales_history 
    WHERE parcel_id = p.parcel_id 
    ORDER BY sale_date DESC 
    LIMIT 1
) s ON true
LEFT JOIN LATERAL (
    SELECT SUM(total_assessment) as total_assessment
    FROM nav_assessments
    WHERE parcel_id = p.parcel_id
) n ON true
LEFT JOIN sunbiz_corporate b 
    ON p.owner_name ILIKE '%' || b.corporate_name || '%';

CREATE INDEX ON property_search_fast(parcel_id);
CREATE INDEX ON property_search_fast(full_address);
```

## Data Loading Priority

### Immediate (Today)
1. **Run optimization indexes** - Makes 789K parcels searchable
2. **Load SDF sales data** - Property sales history
3. **Load NAV assessments** - Tax information
4. **Load Sunbiz entities** - Business matching

### Tomorrow
1. **Broward daily index** - Recent transactions
2. **TPP tangible property** - Additional assessments
3. **Building permits** - Construction activity

### This Week
1. **Setup automated agents** - Daily/weekly updates
2. **Create data quality checks** - Validation
3. **Performance testing** - Ensure <100ms queries

## Query Examples for Each UI Component

### Property Search
```javascript
// In usePropertyData.ts
const searchProperties = async (searchTerm) => {
  const { data } = await supabase
    .from('property_search_fast')
    .select('*')
    .or(`full_address.ilike.%${searchTerm}%,owner_name.ilike.%${searchTerm}%`)
    .limit(20);
  return data;
};
```

### Property Profile
```javascript
// Get all property data
const getPropertyProfile = async (parcelId) => {
  // Main property data
  const { data: property } = await supabase
    .from('florida_parcels')
    .select('*')
    .eq('parcel_id', parcelId)
    .single();
  
  // Sales history
  const { data: sales } = await supabase
    .from('property_sales_history')
    .select('*')
    .eq('parcel_id', parcelId)
    .order('sale_date', { ascending: false });
  
  // Tax assessments
  const { data: assessments } = await supabase
    .from('nav_assessments')
    .select('*')
    .eq('parcel_id', parcelId);
  
  // Business entities
  const { data: entities } = await supabase
    .from('sunbiz_corporate')
    .select('*')
    .or(`principal_address.ilike.%${property.phy_addr1}%,corporate_name.ilike.%${property.owner_name}%`);
  
  return { property, sales, assessments, entities };
};
```

## Performance Targets

- **Search queries**: < 100ms with indexes
- **Property profile load**: < 200ms for all tabs
- **Dashboard refresh**: < 500ms
- **Pagination**: 20-50 properties per page
- **Concurrent users**: 1000+

## Summary

### Current State
- ✅ 789K Florida parcels loaded
- ❌ Sales data needs loading (only 3 records)
- ❌ Assessment data needs loading (only 1 record)
- ❌ Sunbiz data missing (0 records)
- ❌ No indexes = slow queries

### Required Actions
1. **Run optimization SQL** in Supabase
2. **Load missing data** using agents
3. **Test UI components** with real data
4. **Setup monitoring** for continuous updates

### Expected Results After Optimization
- Property search: Instant (<100ms)
- Full property profiles with all tabs
- Business entity matching working
- Sales history populated
- Tax calculations accurate