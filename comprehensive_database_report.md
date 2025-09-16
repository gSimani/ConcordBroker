# ConcordBroker Supabase Database Analysis Report

## Executive Summary

The ConcordBroker Supabase database contains **84 tables** with a total of **300 records** currently populated. The database is structured around Florida property data, business entities, tax deed auctions, and monitoring systems.

**Database URL**: `https://pmispwtdngkcmsrsjwbp.supabase.co`

## Database Structure Overview

### Table Categories and Distribution

| Category | Tables | Records | Primary Purpose |
|----------|---------|---------|-----------------|
| **Business Entity** | 27 | 202 | Florida Sunbiz data, corporate records, officer information |
| **Other** | 28 | 44 | General data management, monitoring, staging |
| **Property Appraiser** | 11 | 1 | Florida property appraiser data (NAL, NAP, NAV, SDF) |
| **Property** | 8 | 7 | Property-specific data, assessments, ownership |
| **County Data** | 5 | 4 | County-specific aggregated data |
| **Tax Deed** | 3 | 42 | Tax deed auctions and bidding items |
| **Geographic** | 2 | 0 | Spatial reference systems |

### County Data Distribution

**10 tables** contain county-specific data:
- `florida_parcels` (51 columns) - Main property data
- `property_assessments` (29 columns) - Property valuations
- `property_sales_history` (27 columns) - Sales transactions
- `latest_parcels` (50 columns) - Current property data
- `nav_parcel_assessments` (13 columns) - Assessment details
- `florida_active_entities_with_contacts` (10 columns) - Business entities by county
- `high_value_properties` (9 columns) - Premium properties
- `recent_sales` (8 columns) - Recent transactions
- `data_quality_dashboard` (8 columns) - Data quality metrics
- `florida_contact_summary` (5 columns) - Contact aggregations

## Key Database Tables

### 1. Property Appraiser Tables (Florida Revenue Data)

#### `florida_parcels` (Primary Property Table)
- **Records**: 0 (ready for bulk import)
- **Columns**: 51
- **Key Fields**: `parcel_id`, `county`, `year`, `owner_name`, `phy_addr1`, `just_value`, `land_sqft`
- **Purpose**: Main repository for Florida property appraiser data from all 67 counties
- **Sample**: Jackson County property with parcel ID `044N10033400000060`

#### `nav_assessments` (Property Values)
- **Records**: 1
- **Purpose**: Property valuations and assessments
- **Key Fields**: `parcel_id`, `tax_year`, `just_value`, `assessed_value`, `taxable_value`

#### `property_assessments` (County Property Data)
- **Records**: 0 (structured for import)
- **Columns**: 29
- **Purpose**: Detailed property assessment information by county
- **Sample County**: Alachua

### 2. Tax Deed System

#### `tax_deed_auctions` (Auction Management)
- **Records**: 4
- **Columns**: 19
- **Purpose**: Manages tax deed auction events
- **Sample**: Broward County Tax Deed Sale - January 2025

#### `tax_deed_bidding_items` (Auction Properties)
- **Records**: 19
- **Columns**: 25
- **Purpose**: Individual properties in tax deed auctions
- **Key Fields**: `parcel_id`, `tax_deed_number`, `legal_situs_address`, `assessed_value`, `bid_amount`
- **Sample**: Parcel `514114-10-6250` at 6418 SW 7 ST with assessed value $302,260.82

#### `tax_certificates` (Tax Certificate Tracking)
- **Records**: 10
- **Purpose**: Track tax certificate sales and redemptions
- **Key Fields**: `parcel_id`, `certificate_number`, `tax_year`, `face_amount`, `status`

### 3. Business Entity System (Sunbiz Integration)

#### `sunbiz_contacts` (Business Officer Contacts)
- **Records**: 100
- **Columns**: 15
- **Purpose**: Contact information for Florida business officers
- **Key Fields**: `doc_number`, `officer_name`, `officer_email`, `officer_phone`, `entity_name`

#### `sunbiz_officers` (Corporate Officers)
- **Records**: 100
- **Columns**: 12
- **Purpose**: Detailed officer information for Florida corporations
- **Key Fields**: `doc_number`, `officer_name`, `officer_title`, `officer_address`

#### `sunbiz_corporate` (Corporate Entities)
- **Records**: 0 (structured for import)
- **Columns**: 23
- **Purpose**: Main Florida corporate entity data

#### `florida_active_entities_with_contacts` (Active Businesses)
- **Records**: 0 (view/aggregation table)
- **Purpose**: Active Florida businesses with contact information by county

### 4. Property Analysis Tables

#### `property_tax_certificate_summary` (Certificate Analytics)
- **Records**: 7
- **Columns**: 6
- **Purpose**: Aggregated tax certificate data per property
- **Key Fields**: `parcel_id`, `certificate_count`, `total_active_amount`, `latest_tax_year`

### 5. Monitoring and Quality Control

#### `fl_agent_status` (System Monitoring)
- **Records**: 7
- **Purpose**: Track automated data collection agents
- **Key Fields**: `agent_name`, `agent_type`, `is_enabled`, `current_status`

#### `florida_contact_summary` (Contact Aggregations)
- **Records**: 4
- **Purpose**: Summarize business contacts by county and entity type

## Data Import Status

### Property Appraiser Data (Florida Revenue)
- **Status**: Tables created, ready for bulk import
- **Expected Volume**: ~9.7M properties across 67 Florida counties
- **File Types**: NAL (names/addresses), NAP (characteristics), NAV (values), SDF (sales)
- **Import Schema**: Configured for 2025 data with proper column mappings

### Business Entity Data (Sunbiz)
- **Status**: Partial data loaded (200 records)
- **Expected Volume**: ~3.5M Florida business entities
- **File Types**: Corporate, Officer, Contact data
- **Current Tables**: `sunbiz_contacts`, `sunbiz_officers` with sample data

### Tax Deed Data
- **Status**: Active with live data
- **Current Data**: 42 records across auction and bidding tables
- **Source**: Broward County tax deed auctions

## Database Performance Characteristics

### Indexing Strategy
- Primary keys on all major tables
- Unique constraints on `(parcel_id, county, year)` for florida_parcels
- Geographic indexes for spatial data

### Optimization Features
- Timeout management for bulk operations
- Batch insert capabilities (1000 records/batch)
- Parallel processing support (4 workers)
- Upsert functionality for data updates

## County Coverage Analysis

### Current County Data
- **Jackson County**: Property data available
- **Broward County**: Tax deed auction data active
- **Alachua County**: Sample property assessment data

### Target Coverage
- **All 67 Florida Counties**: Property appraiser data
- **Statewide**: Business entity data
- **Selected Counties**: Tax deed monitoring

## Data Quality and Validation

### Column Mapping Standards
- `land_sqft` (not land_square_footage)
- `phy_addr1/phy_addr2` (not property_address)
- `owner_addr1/owner_addr2` (not owner_address)
- `owner_state` (2 chars: "FL" not "FLORIDA")
- `sale_date` (timestamp or NULL, never empty string)

### Error Handling
- Timeout management for large operations
- Data validation on required fields
- Duplicate handling via upsert operations
- Rate limiting protection

## API Access Patterns

### Authentication
- **API Key**: Required for all operations
- **Header**: `x-api-key: concordbroker-mcp-key-claude`
- **Base URL**: `https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/`

### Query Examples
```bash
# Get property data
curl -H "apikey: [KEY]" "https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/florida_parcels?county=eq.BROWARD&limit=10"

# Get tax deed auctions
curl -H "apikey: [KEY]" "https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/tax_deed_auctions?status=eq.upcoming"

# Get business entities by county
curl -H "apikey: [KEY]" "https://pmispwtdngkcmsrsjwbp.supabase.co/rest/v1/florida_active_entities_with_contacts?business_county=eq.MIAMI-DADE"
```

## Recommendations

### Immediate Actions
1. **Complete Property Data Import**: Load remaining Florida parcels data
2. **Expand County Coverage**: Add Miami-Dade, Palm Beach, Hillsborough
3. **Business Entity Integration**: Complete Sunbiz data import
4. **Index Optimization**: Add performance indexes for common queries

### Data Pipeline Enhancements
1. **Automated Monitoring**: Set up daily checks for Florida Revenue updates
2. **Quality Validation**: Implement comprehensive data validation rules
3. **Change Detection**: Monitor file checksums for updates
4. **Error Recovery**: Robust error handling for failed imports

### Performance Optimization
1. **Batch Processing**: Maintain 1000-record batch sizes
2. **Parallel Workers**: Use 4 concurrent threads for imports
3. **Memory Management**: Monitor 2-4 GB usage during bulk operations
4. **Connection Pooling**: Optimize database connections

## Technical Specifications

### Database Configuration
- **Platform**: Supabase (PostgreSQL)
- **Authentication**: JWT tokens with row-level security
- **API**: PostgREST with automatic OpenAPI documentation
- **Extensions**: PostGIS for geographic data

### Import Specifications
- **Bulk Import Rate**: 2,000-4,000 records/second (4 workers)
- **Memory Usage**: 2-4 GB for full dataset
- **Estimated Import Time**: 1.5-3 hours for 9.7M records
- **Batch Configuration**: 1000 records per batch with exponential backoff

---

*Report generated on 2025-09-16 by automated database analysis*