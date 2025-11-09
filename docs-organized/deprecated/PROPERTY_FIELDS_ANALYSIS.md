# Property Profile Missing Fields Analysis
## Property: 6390 NW 95 LN, Parkland

### Current Data Status from Supabase

#### ✅ Available Fields (12 fields with data):
- `parcel_id`: 484104011450
- `owner_name`: BESSELL,PAUL & LAUREN
- `phy_addr1`: 6390 NW 95 LN
- `phy_city`: PARKLAND
- `phy_state`: FL
- `phy_zipcd`: 33076
- `property_use`: 001
- `county`: BROWARD
- `year`: 2025
- `data_source`: NAL_2025
- `import_date`: 2025-09-07
- `id`: 102513

#### ❌ Missing/Empty Fields (38 fields):
Critical fields that are empty but needed for the UI tabs:

**Property Details:**
- `year_built` - Required for Overview, Core Property tabs
- `total_living_area` - Required for Overview, Core Property, Analysis tabs
- `bedrooms` - Required for Overview, Core Property tabs
- `bathrooms` - Required for Overview, Core Property tabs
- `stories` - Required for Core Property tab
- `units` - Required for Core Property tab

**Valuation Data:**
- `just_value` - Required for Overview, Tax, Analysis tabs
- `assessed_value` - Required for Overview, Tax, Analysis tabs
- `taxable_value` - Required for Tax tab
- `land_value` - Required for Overview, Core Property tabs
- `building_value` - Required for Overview, Core Property tabs

**Land Information:**
- `land_sqft` - Required for Overview, Core Property tabs
- `land_acres` - Required for Core Property tab
- `lot` - Required for Core Property tab
- `block` - Required for Core Property tab
- `subdivision` - Required for Core Property tab
- `legal_desc` - Required for Core Property tab
- `zoning` - Required for Core Property tab

**Sales History:**
- `sale_date` - Required for Overview, Core Property, Analysis tabs
- `sale_price` - Required for Overview, Core Property, Analysis tabs
- `sale_qualification` - Required for Core Property tab

**Owner Information:**
- `owner_addr1` - Required for Core Property, Ownership tabs
- `owner_addr2` - Required for Ownership tab
- `owner_city` - Required for Ownership tab
- `owner_state` - Required for Ownership tab
- `owner_zip` - Required for Ownership tab

**Geographic Data:**
- `geometry` - Required for mapping features
- `centroid` - Required for mapping features
- `area_sqft` - Required for Analysis tab
- `perimeter_ft` - Required for Analysis tab

### Tab-by-Tab Field Requirements

## 1. Overview Tab
**Currently Displays:**
- Property address ✅ (using `phy_addr1`, `phy_city`)
- Property type ✅ (using `property_use`)
- Owner name ✅

**Missing Data:**
- Market Value ❌ (`just_value` or `market_value`)
- Assessed Value ❌ (`assessed_value`)
- Land Value ❌ (`land_value`)
- Building Value ❌ (`building_value`)
- Living Area ❌ (`total_living_area`)
- Year Built ❌ (`year_built`)
- Lot Size ❌ (`land_sqft`)
- Bedrooms ❌ (`bedrooms`)
- Bathrooms ❌ (`bathrooms`)
- Last Sale Price ❌ (`sale_price`)
- Last Sale Date ❌ (`sale_date`)

## 2. Core Property Info Tab
**Currently Displays:**
- Basic address info ✅
- Owner name ✅

**Missing Data:**
- Legal Description ❌ (`legal_desc`)
- Subdivision ❌ (`subdivision`)
- Lot/Block ❌ (`lot`, `block`)
- Property Use Description ❌ (`property_use_desc`)
- Zoning ❌ (`zoning`)
- Year Built ❌ (`year_built`)
- Living Area ❌ (`total_living_area`)
- Bedrooms/Bathrooms ❌
- Stories ❌ (`stories`)
- Building Count ❌ (`units`)
- Sales History ❌ (requires `property_sales_history` table data)

## 3. Property Tax Info Tab
**Missing Data:**
- Taxable Value ❌ (`taxable_value`)
- Assessed Value ❌ (`assessed_value`)
- Just Value ❌ (`just_value`)
- Tax Amount ❌ (calculated field)
- Exemptions ❌ (requires additional data)
- Millage Rate ❌ (requires additional data)
- Tax History ❌ (requires historical data)

## 4. Sunbiz Info Tab
**Current Status:**
- Shows "No business entities found" (expected as `sunbiz_corporate` table is empty)
- Needs data from `sunbiz_corporate` table matching owner name or address

## 5. Analysis Tab
**Missing Data for Calculations:**
- Market Value ❌
- Assessed Value ❌
- Sale Price ❌
- Living Area ❌
- Land Size ❌
- Year Built ❌
- Comparable Sales ❌ (requires neighborhood data)
- Price per Sq Ft ❌ (calculated)
- Cap Rate ❌ (requires rental data)

## 6. Permit Tab
**Current Status:**
- Shows demo data only
- Needs data from `building_permits` table (table doesn't exist)

## 7. Foreclosure Tab
**Current Status:**
- No foreclosure data available
- Needs data from foreclosure tables (not created)

## 8. Sales/Tax Deed Tab
**Current Status:**
- Shows calculated estimates only
- Needs actual tax deed sale data

## 9. Tax Lien Tab
**Current Status:**
- Shows risk assessment only
- Needs actual tax certificate data

### Data Sources Required

To populate all missing fields, data needs to come from:

1. **NAV (Non-Ad Valorem) Data** - For assessed values, taxable values
2. **SDF (Sales Data File)** - For sales history, sale prices
3. **TPP (Tangible Personal Property)** - For business property data
4. **Property Appraiser Data** - For detailed property characteristics
5. **Sunbiz Data** - For business entity information
6. **Permit Data** - From local building departments
7. **Tax Certificate Data** - From tax collector

### Immediate Action Items

1. **Load NAV Assessment Data**
   - Will provide: assessed_value, taxable_value, just_value
   - Table: `nav_parcel_assessments`

2. **Load SDF Sales Data**
   - Will provide: sale_date, sale_price, sale_qualification
   - Table: `fl_sdf_sales` or `property_sales_history`

3. **Load Property Details from TPP**
   - Will provide: year_built, living_area, bedrooms, bathrooms
   - Table: `fl_tpp_accounts`

4. **Update florida_parcels Table**
   - Add missing columns for property characteristics
   - Run data enrichment scripts to populate fields

5. **Load Sunbiz Corporate Data**
   - Match entities to properties by owner name/address
   - Table: `sunbiz_corporate`

### SQL to Add Missing Columns

```sql
ALTER TABLE florida_parcels
ADD COLUMN IF NOT EXISTS year_built INTEGER,
ADD COLUMN IF NOT EXISTS total_living_area INTEGER,
ADD COLUMN IF NOT EXISTS bedrooms INTEGER,
ADD COLUMN IF NOT EXISTS bathrooms DECIMAL(3,1),
ADD COLUMN IF NOT EXISTS stories INTEGER,
ADD COLUMN IF NOT EXISTS just_value DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS assessed_value DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS taxable_value DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS land_value DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS building_value DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS sale_date DATE,
ADD COLUMN IF NOT EXISTS sale_price DECIMAL(15,2),
ADD COLUMN IF NOT EXISTS legal_desc TEXT,
ADD COLUMN IF NOT EXISTS subdivision VARCHAR(255),
ADD COLUMN IF NOT EXISTS lot VARCHAR(50),
ADD COLUMN IF NOT EXISTS block VARCHAR(50),
ADD COLUMN IF NOT EXISTS zoning VARCHAR(50),
ADD COLUMN IF NOT EXISTS owner_addr1 VARCHAR(255),
ADD COLUMN IF NOT EXISTS owner_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS owner_state VARCHAR(2),
ADD COLUMN IF NOT EXISTS owner_zip VARCHAR(10);
```

### Summary

**Total Fields Needed**: ~50 fields
**Currently Available**: 12 fields (24%)
**Missing Critical Fields**: 38 fields (76%)

The property profile tabs are currently showing mostly empty or mock data because the `florida_parcels` table only contains basic NAL (Name, Address, Legal) data. To fully populate all tabs, you need to:

1. Load assessment data (NAV)
2. Load sales history (SDF)
3. Load property characteristics (TPP)
4. Load business entities (Sunbiz)
5. Create and populate permit/foreclosure/tax tables

This will transform the property profiles from 24% complete to nearly 100% complete with real, actionable data.