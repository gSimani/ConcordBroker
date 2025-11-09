# Florida Revenue TPP (Tangible Personal Property) Data Fields

## Data Source
**URL**: https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP/2025P/Broward%2016%20Preliminary%20TPP%202025.zip

**File**: NAP16P202501.csv (90,509 records for Broward County 2025)

## Complete Field List (36 Fields)

| Field Name | Description | Sample Data | Data Type |
|------------|-------------|-------------|-----------|
| **CO_NO** | County Number | "16" | String |
| **ACCT_ID** | Account ID | "474131031040" | String |
| **FILE_T** | File Type | "P" (Preliminary) | String |
| **ASMNT_YR** | Assessment Year | "2025" | String |
| **TAX_AUTH_CD** | Tax Authority Code | "3012" | String |
| **NAICS_CD** | NAICS Industry Code | "531110" | String |
| **JV_F_F_E** | Just Value - Furniture, Fixtures, Equipment | 180 | Numeric |
| **JV_LESE_IMP** | Just Value - Leasehold Improvements | (empty) | Numeric |
| **JV_TOTAL** | Just Value - Total | 180 | Numeric |
| **AV_TOTAL** | Assessed Value - Total | 180 | Numeric |
| **JV_POL_CONTRL** | Just Value - Pollution Control | 0 | Numeric |
| **AV_POL_CONTRL** | Assessed Value - Pollution Control | 0 | Numeric |
| **EXMPT_VAL** | Exempt Value | 180 | Numeric |
| **TAX_VAL** | Taxable Value | 0 | Numeric |
| **PEN_RATE** | Penalty Rate | 0 | Numeric |
| **OWN_NAM** | Owner Name | "INVITATION HOMES" | String |
| **OWN_ADDR** | Owner Address | "PO BOX 4900" | String |
| **OWN_CITY** | Owner City | "SCOTTSDALE" | String |
| **OWN_STATE** | Owner State | "AZ" | String |
| **OWN_ZIPCD** | Owner ZIP Code | "85261" | String |
| **OWN_STATE_DOM** | Owner State of Domicile | (empty) | String |
| **FIDU_NAME** | Fiduciary Name | (empty) | String |
| **FIDU_ADDR** | Fiduciary Address | (empty) | String |
| **FIDU_CITY** | Fiduciary City | (empty) | String |
| **FIDU_STATE** | Fiduciary State | (empty) | String |
| **FIDU_ZIPCD** | Fiduciary ZIP Code | (empty) | String |
| **FIDU_CD** | Fiduciary Code | (empty) | String |
| **PHY_ADDR** | Physical Address | "12681 NW 78 MNR" | String |
| **PHY_CITY** | Physical City | "PARKLAND" | String |
| **PHY_ZIPCD** | Physical ZIP Code | "33076" | String |
| **FIL** | File Code | (empty) | String |
| **ALT_KEY** | Alternate Key | (empty) | String |
| **EXMPT** | Exemption Codes | "M;180" | String |
| **ACCT_ID_CNG** | Account ID Change | (empty) | String |
| **SEQ_NO** | Sequence Number | 1 | Numeric |
| **TS_ID** | Timestamp ID | "14B1" | String |

## Key Business Insights

### Top Property Owners (Investment Companies)
1. **INVITATION HOMES** - 2,376 properties
2. **COLONY STARWOOD** - 1,390 properties  
3. **CERBERUS SFR HOLDINGS II LP** - 267 properties
4. **CSMA FT LLC** - 169 properties
5. **CSMA BLT LLC** - 73 properties

### Business Categories (NAICS Codes)
- **531110** - Real Estate Property Managers (most common)
- Various retail and commercial businesses
- Mobile home parks
- Restaurant chains (Dunkin' Donuts, Subway)
- Telecom (AT&T stores)

## New Database Fields to Add

### Core Property Information
```sql
-- TPP Specific Fields
tpp_account_id VARCHAR(50),
tpp_file_type VARCHAR(10),
tpp_assessment_year VARCHAR(4),
tpp_tax_authority_code VARCHAR(10),
tpp_naics_code VARCHAR(10),

-- Valuation Fields  
tpp_jv_furniture_fixtures DECIMAL(15,2),
tpp_jv_leasehold_improvements DECIMAL(15,2),
tpp_jv_total DECIMAL(15,2),
tpp_av_total DECIMAL(15,2),
tpp_jv_pollution_control DECIMAL(15,2),
tpp_av_pollution_control DECIMAL(15,2),
tpp_exempt_value DECIMAL(15,2),
tpp_taxable_value DECIMAL(15,2),
tpp_penalty_rate DECIMAL(5,4),

-- Owner Information (Enhanced)
tpp_owner_name VARCHAR(200),
tpp_owner_address VARCHAR(200),
tpp_owner_city VARCHAR(100),
tpp_owner_state VARCHAR(2),
tpp_owner_zip VARCHAR(10),
tpp_owner_state_domicile VARCHAR(2),

-- Fiduciary Information
tpp_fiduciary_name VARCHAR(200),
tpp_fiduciary_address VARCHAR(200),
tpp_fiduciary_city VARCHAR(100),
tpp_fiduciary_state VARCHAR(2),
tpp_fiduciary_zip VARCHAR(10),
tpp_fiduciary_code VARCHAR(20),

-- Physical Location
tpp_physical_address VARCHAR(200),
tpp_physical_city VARCHAR(100),
tpp_physical_zip VARCHAR(10),

-- Administrative Fields
tpp_exemption_codes TEXT,
tpp_sequence_number INTEGER,
tpp_timestamp_id VARCHAR(20),
tpp_data_source VARCHAR(50) DEFAULT 'florida_revenue_tpp',
tpp_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
tpp_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

## Data Quality Notes

- **90,509 total records** for Broward County
- **Complete address information** for both owners and physical locations  
- **Rich valuation data** including furniture/fixtures and leasehold improvements
- **NAICS industry classification** for business categorization
- **Exemption tracking** with detailed codes
- **Major institutional investors** clearly identified (Invitation Homes, Colony Starwood)

## Integration Benefits

1. **Investment Company Tracking** - Identify large-scale property acquisitions
2. **Business Property Analysis** - Understand commercial property landscape  
3. **Tax Assessment Data** - Complete valuation and exemption information
4. **Cross-Reference Capability** - Link with existing real estate data
5. **Market Intelligence** - Track institutional investment patterns

## Recommended Next Steps

1. Create database schema migration for new TPP fields
2. Build data pipeline to regularly download updates
3. Implement data matching with existing property records
4. Create analytics dashboards for investment company tracking
5. Set up alerts for high-value transactions and new large investors