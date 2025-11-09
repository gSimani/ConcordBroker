# Complete Supabase to UI Field Mapping Documentation

## Table of Contents
1. [Database Tables Overview](#database-tables-overview)
2. [Properties Search Page](#properties-search-page)
3. [Property Profile Page](#property-profile-page)
4. [Dashboard Page](#dashboard-page)
5. [Field Mapping Reference](#field-mapping-reference)

---

## Database Tables Overview

### Primary Table: `florida_parcels`
Main property data table with 50+ columns containing property information.

### Secondary Tables:
- `properties` - Alternative property table with simplified schema
- `property_sales_history` - Historical sales transactions
- `nav_assessments` - Non-ad valorem assessments
- `sunbiz_corporate` - Business entity data
- `florida_permits` - Building permits
- `fl_sdf_sales` - Sales data feed

---

## Properties Search Page
**URL:** `/properties`
**Component:** `apps/web/src/pages/properties/PropertySearch.tsx`

### Search Filters Section

#### City Filter
- **UI Element ID:** `city-filter-select`
- **Supabase Field:** `florida_parcels.phy_city`
- **Data Type:** String
- **Example Values:** "FORT LAUDERDALE", "HOLLYWOOD", "MIAMI"

#### Address Search
- **UI Element ID:** `address-search-input`
- **Supabase Field:** `florida_parcels.phy_addr1`
- **Data Type:** String
- **Example Values:** "123 OCEAN BLVD", "456 SUNRISE AVE"

#### Zip Code Filter
- **UI Element ID:** `zip-code-filter-input`
- **Supabase Field:** `florida_parcels.phy_zipcd`
- **Data Type:** String (5 digits)
- **Example Values:** "33301", "33019", "33131"

#### Owner Name Search
- **UI Element ID:** `owner-name-search-input`
- **Supabase Field:** `florida_parcels.owner_name`
- **Data Type:** String
- **Example Values:** "SMITH JOHN", "ABC PROPERTIES LLC"

#### Property Type Filter
- **UI Element ID:** `property-type-filter-select`
- **Supabase Field:** `florida_parcels.property_use_desc`
- **Related Field:** `florida_parcels.property_use` (DOR code)
- **Data Type:** String
- **Example Values:** "Single Family", "Condominium", "Office Building"

#### Price Range Filters
- **Min Value ID:** `min-value-filter-input`
- **Max Value ID:** `max-value-filter-input`
- **Supabase Field:** `florida_parcels.just_value`
- **Data Type:** Decimal(15,2)
- **Example Range:** $100,000 - $10,000,000

#### Building Size Filters
- **Min Size ID:** `min-building-sqft-filter-input`
- **Max Size ID:** `max-building-sqft-filter-input`
- **Supabase Field:** `florida_parcels.total_living_area`
- **Data Type:** Integer
- **Example Range:** 1,000 - 50,000 sqft

#### Land Size Filters
- **Min Land ID:** `min-land-sqft-filter-input`
- **Max Land ID:** `max-land-sqft-filter-input`
- **Supabase Field:** `florida_parcels.land_sqft`
- **Data Type:** Integer
- **Example Range:** 5,000 - 100,000 sqft

### Property Card Display (MiniPropertyCard)
**Component:** `apps/web/src/components/property/MiniPropertyCard.tsx`

#### Card Header
- **Parcel ID Display**
  - **UI Element ID:** `property-card-{parcelId}-parcel`
  - **Supabase Field:** `florida_parcels.parcel_id`
  - **Data Type:** String

- **Property Type Badge**
  - **UI Element ID:** `property-card-{parcelId}-type-badge`
  - **Supabase Field:** `florida_parcels.property_use` (DOR code)
  - **Mapping:** Use code to determine category (Residential/Commercial/Industrial)

#### Address Section
- **Street Address**
  - **UI Element ID:** `property-card-{parcelId}-address`
  - **Supabase Field:** `florida_parcels.phy_addr1`
  - **Display Format:** "123 MAIN ST"

- **City, State, Zip**
  - **UI Element ID:** `property-card-{parcelId}-city-state-zip`
  - **Supabase Fields:** `phy_city`, `phy_state`, `phy_zipcd`
  - **Display Format:** "FORT LAUDERDALE, FL 33301"

#### Owner Information
- **Owner Name**
  - **UI Element ID:** `property-card-{parcelId}-owner`
  - **Supabase Field:** `florida_parcels.owner_name`
  - **Display Format:** Truncated if > 30 chars

#### Value Display
- **Just (Market) Value**
  - **UI Element ID:** `property-card-{parcelId}-just-value`
  - **Supabase Field:** `florida_parcels.just_value`
  - **Display Format:** "$1,250,000" or "$1.25M"

- **Taxable Value**
  - **UI Element ID:** `property-card-{parcelId}-taxable-value`
  - **Supabase Field:** `florida_parcels.taxable_value`
  - **Display Format:** Currency with commas

- **Land Value**
  - **UI Element ID:** `property-card-{parcelId}-land-value`
  - **Supabase Field:** `florida_parcels.land_value`
  - **Display Format:** Currency

#### Property Details
- **Building Square Feet**
  - **UI Element ID:** `property-card-{parcelId}-building-sqft`
  - **Supabase Field:** `florida_parcels.total_living_area`
  - **Display Format:** "2,500 sqft"

- **Land Square Feet**
  - **UI Element ID:** `property-card-{parcelId}-land-sqft`
  - **Supabase Field:** `florida_parcels.land_sqft`
  - **Display Format:** "8,500 sqft"

- **Year Built**
  - **UI Element ID:** `property-card-{parcelId}-year-built`
  - **Supabase Field:** `florida_parcels.year_built`
  - **Display Format:** "2005"

#### Sales Information
- **Last Sale Price**
  - **UI Element ID:** `property-card-{parcelId}-sale-price`
  - **Supabase Field:** `florida_parcels.sale_price`
  - **Display Format:** Currency

- **Last Sale Date**
  - **UI Element ID:** `property-card-{parcelId}-sale-date`
  - **Supabase Field:** `florida_parcels.sale_date`
  - **Display Format:** "MM/YYYY"

---

## Property Profile Page
**URL:** `/property/{parcelId}`
**Component:** `apps/web/src/pages/property/PropertyProfile.tsx`

### Executive Header Section
- **Property Address**
  - **UI Element ID:** `property-profile-address`
  - **Supabase Field:** `florida_parcels.phy_addr1`

- **City, State, Zip**
  - **UI Element ID:** `property-profile-city-state-zip`
  - **Supabase Fields:** `phy_city`, `phy_state`, `phy_zipcd`

- **Property Use Description**
  - **UI Element ID:** `property-profile-use-desc`
  - **Supabase Field:** `florida_parcels.property_use_desc`

- **Parcel ID**
  - **UI Element ID:** `property-profile-parcel-id`
  - **Supabase Field:** `florida_parcels.parcel_id`

### Overview Tab
**Tab ID:** `property-tab-overview`

#### Owner Information Section
- **Owner Name**
  - **UI Element ID:** `overview-owner-name`
  - **Supabase Field:** `florida_parcels.owner_name`

- **Owner Address**
  - **UI Element ID:** `overview-owner-address`
  - **Supabase Fields:** `owner_addr1`, `owner_city`, `owner_state`, `owner_zip`

#### Property Characteristics
- **Property Type**
  - **UI Element ID:** `overview-property-type`
  - **Supabase Field:** `florida_parcels.property_use_desc`

- **Year Built**
  - **UI Element ID:** `overview-year-built`
  - **Supabase Field:** `florida_parcels.year_built`

- **Effective Year Built**
  - **UI Element ID:** `overview-eff-year-built`
  - **Supabase Field:** `florida_parcels.eff_yr_blt` (if available)

- **Total Living Area**
  - **UI Element ID:** `overview-living-area`
  - **Supabase Field:** `florida_parcels.total_living_area`

- **Land Area**
  - **UI Element ID:** `overview-land-area`
  - **Supabase Field:** `florida_parcels.land_sqft`

- **Land Acres**
  - **UI Element ID:** `overview-land-acres`
  - **Supabase Field:** `florida_parcels.land_acres`

#### Residential Details (if applicable)
- **Bedrooms**
  - **UI Element ID:** `overview-bedrooms`
  - **Supabase Field:** `florida_parcels.bedrooms`

- **Bathrooms**
  - **UI Element ID:** `overview-bathrooms`
  - **Supabase Field:** `florida_parcels.bathrooms`

- **Number of Units**
  - **UI Element ID:** `overview-units`
  - **Supabase Field:** `florida_parcels.units`

### Core Property Info Tab
**Tab ID:** `property-tab-core-info`

#### Valuation Section
- **Just (Market) Value**
  - **UI Element ID:** `core-just-value`
  - **Supabase Field:** `florida_parcels.just_value`
  - **Display Format:** "$X,XXX,XXX"

- **Assessed Value**
  - **UI Element ID:** `core-assessed-value`
  - **Supabase Field:** `florida_parcels.assessed_value`

- **Taxable Value**
  - **UI Element ID:** `core-taxable-value`
  - **Supabase Field:** `florida_parcels.taxable_value`

- **Land Value**
  - **UI Element ID:** `core-land-value`
  - **Supabase Field:** `florida_parcels.land_value`

- **Building Value**
  - **UI Element ID:** `core-building-value`
  - **Supabase Field:** `florida_parcels.building_value`

#### Legal Description
- **Subdivision**
  - **UI Element ID:** `core-subdivision`
  - **Supabase Field:** `florida_parcels.subdivision`

- **Legal Description**
  - **UI Element ID:** `core-legal-desc`
  - **Supabase Field:** `florida_parcels.legal_desc`

- **Block**
  - **UI Element ID:** `core-block`
  - **Supabase Field:** `florida_parcels.block`

- **Lot**
  - **UI Element ID:** `core-lot`
  - **Supabase Field:** `florida_parcels.lot`

### Property Tax Info Tab
**Tab ID:** `property-tab-tax-info`

#### Tax Values
- **Total Tax Amount**
  - **UI Element ID:** `tax-total-amount`
  - **Supabase Field:** `florida_parcels.tax_amount` (calculated)

- **Homestead Exemption**
  - **UI Element ID:** `tax-homestead-exemption`
  - **Supabase Field:** `florida_parcels.homestead_exemption`
  - **Display:** "Yes/No" or amount

- **Tax Rate**
  - **UI Element ID:** `tax-rate`
  - **Calculation:** Tax Amount / Taxable Value

#### Non-Ad Valorem Assessments
- **NAV List**
  - **UI Element ID:** `tax-nav-list`
  - **Supabase Table:** `nav_assessments`
  - **Fields:** `assessment_name`, `amount`, `units`

### Sales History Tab
**Tab ID:** `property-tab-sales-history`

#### Sales Timeline
- **Sale Entries**
  - **UI Element ID:** `sales-entry-{index}`
  - **Supabase Table:** `property_sales_history`
  - **Fields:**
    - `sale_date` → Display as "MM/DD/YYYY"
    - `sale_price` → Display as currency
    - `grantor` → Seller name
    - `grantee` → Buyer name
    - `sale_qualification` → Sale type

#### Current Sale Information
- **Last Sale Price**
  - **UI Element ID:** `sales-last-price`
  - **Supabase Field:** `florida_parcels.sale_price`

- **Last Sale Date**
  - **UI Element ID:** `sales-last-date`
  - **Supabase Field:** `florida_parcels.sale_date`

### Sunbiz Info Tab
**Tab ID:** `property-tab-sunbiz`

#### Business Entity Information
- **Corporate Name**
  - **UI Element ID:** `sunbiz-corp-name`
  - **Supabase Table:** `sunbiz_corporate`
  - **Field:** `corporate_name`

- **Entity Status**
  - **UI Element ID:** `sunbiz-status`
  - **Field:** `status`

- **Officers/Directors**
  - **UI Element ID:** `sunbiz-officers-list`
  - **Field:** `officers` (JSON array)

- **Registration Date**
  - **UI Element ID:** `sunbiz-reg-date`
  - **Field:** `filing_date`

---

## Dashboard Page
**URL:** `/dashboard`
**Component:** `apps/web/src/pages/dashboard.tsx`

### Statistics Cards
- **Total Properties**
  - **UI Element ID:** `dashboard-total-properties`
  - **Query:** `COUNT(*) FROM florida_parcels`

- **Total Portfolio Value**
  - **UI Element ID:** `dashboard-total-value`
  - **Query:** `SUM(just_value) FROM florida_parcels WHERE owner_name = {user}`

- **Average Property Value**
  - **UI Element ID:** `dashboard-avg-value`
  - **Calculation:** Total Value / Property Count

### Property Distribution Chart
- **By Type**
  - **UI Element ID:** `dashboard-chart-by-type`
  - **Grouping:** `property_use_desc`
  - **Aggregation:** COUNT by type

- **By City**
  - **UI Element ID:** `dashboard-chart-by-city`
  - **Grouping:** `phy_city`
  - **Aggregation:** COUNT and SUM(just_value)

---

## Field Mapping Reference

### Supabase → UI Field Quick Reference

| Supabase Field | UI Display Name | Location | Element ID Pattern |
|----------------|-----------------|----------|-------------------|
| `parcel_id` | Parcel ID | All property displays | `*-parcel-id` |
| `phy_addr1` | Site Address | Property cards, profile | `*-address` |
| `phy_city` | City | Address displays | `*-city` |
| `phy_state` | State | Address displays | `*-state` |
| `phy_zipcd` | ZIP Code | Address displays | `*-zip` |
| `owner_name` | Owner Name | Owner section | `*-owner-name` |
| `owner_addr1` | Owner Address | Owner details | `*-owner-address` |
| `property_use` | DOR Use Code | Type badges | `*-use-code` |
| `property_use_desc` | Property Type | Type descriptions | `*-property-type` |
| `just_value` | Market Value | Valuation displays | `*-just-value` |
| `assessed_value` | Assessed Value | Tax calculations | `*-assessed-value` |
| `taxable_value` | Taxable Value | Tax displays | `*-taxable-value` |
| `land_value` | Land Value | Valuation breakdowns | `*-land-value` |
| `building_value` | Building Value | Valuation breakdowns | `*-building-value` |
| `total_living_area` | Building Sq Ft | Size displays | `*-building-sqft` |
| `land_sqft` | Land Sq Ft | Land size | `*-land-sqft` |
| `land_acres` | Acres | Land size alternative | `*-land-acres` |
| `year_built` | Year Built | Property details | `*-year-built` |
| `bedrooms` | Beds | Residential details | `*-bedrooms` |
| `bathrooms` | Baths | Residential details | `*-bathrooms` |
| `sale_price` | Last Sale Price | Sales history | `*-sale-price` |
| `sale_date` | Last Sale Date | Sales history | `*-sale-date` |
| `subdivision` | Subdivision | Legal description | `*-subdivision` |
| `legal_desc` | Legal Description | Legal section | `*-legal-desc` |
| `county` | County | Location info | `*-county` |

### DOR Use Code Categories

| Code Range | Category | Display Color | Badge Class |
|------------|----------|---------------|-------------|
| 000-099 | Residential | Green | `bg-green-100 text-green-800` |
| 100-399 | Commercial | Blue | `bg-blue-100 text-blue-800` |
| 400-499 | Industrial | Orange | `bg-orange-100 text-orange-800` |
| 500-699 | Agricultural | Yellow | `bg-yellow-100 text-yellow-800` |
| 700-899 | Institutional | Purple | `bg-purple-100 text-purple-800` |
| 900-999 | Miscellaneous | Gray | `bg-gray-100 text-gray-800` |

### Common DOR Use Codes

| Code | Description | Category |
|------|-------------|----------|
| 000 | Vacant Residential | Residential |
| 001 | Single Family | Residential |
| 002 | Mobile Home | Residential |
| 003 | Multi-Family (2-9) | Residential |
| 004 | Condominium | Residential |
| 011 | Stores/Office | Commercial |
| 039 | Hotel/Motel | Commercial |
| 100 | Vacant Commercial | Commercial |
| 401 | Light Manufacturing | Industrial |
| 402 | Warehouse | Industrial |

---

## API Endpoints and Data Flow

### Search Properties
**Endpoint:** `GET /api/properties/search`

**Query Parameters:**
- `city` → `florida_parcels.phy_city`
- `address` → `florida_parcels.phy_addr1`
- `zip_code` → `florida_parcels.phy_zipcd`
- `owner` → `florida_parcels.owner_name`
- `min_value` → `florida_parcels.just_value >= X`
- `max_value` → `florida_parcels.just_value <= X`
- `property_type` → `florida_parcels.property_use_desc`
- `limit` → Result limit (default: 20)
- `offset` → Pagination offset

**Response Mapping:**
```javascript
{
  "properties": [
    {
      "id": "florida_parcels.id",
      "parcel_id": "florida_parcels.parcel_id",
      "phy_addr1": "florida_parcels.phy_addr1",
      "phy_city": "florida_parcels.phy_city",
      "phy_zipcd": "florida_parcels.phy_zipcd",
      "own_name": "florida_parcels.owner_name",
      "property_type": "florida_parcels.property_use_desc",
      "dor_uc": "florida_parcels.property_use",
      "jv": "florida_parcels.just_value",
      "tv_sd": "florida_parcels.taxable_value",
      "lnd_val": "florida_parcels.land_value",
      "tot_lvg_area": "florida_parcels.total_living_area",
      "lnd_sqfoot": "florida_parcels.land_sqft",
      "act_yr_blt": "florida_parcels.year_built",
      "sale_prc1": "florida_parcels.sale_price",
      "sale_yr1": "YEAR(florida_parcels.sale_date)"
    }
  ],
  "total": "COUNT",
  "limit": "limit",
  "offset": "offset"
}
```

### Get Property Details
**Endpoint:** `GET /api/property/{parcel_id}`

**Response includes:**
- Main property data from `florida_parcels`
- Sales history from `property_sales_history`
- NAV assessments from `nav_assessments`
- Sunbiz data from `sunbiz_corporate`
- Permits from `florida_permits`

---

## Implementation Checklist

### Frontend Components
- [ ] Add unique IDs to all div elements in PropertySearch.tsx
- [ ] Add unique IDs to all div elements in MiniPropertyCard.tsx
- [ ] Add unique IDs to all div elements in PropertyProfile.tsx
- [ ] Add unique IDs to all tab components
- [ ] Add unique IDs to filter elements
- [ ] Add unique IDs to form inputs

### Data Mapping
- [ ] Verify all Supabase fields are correctly mapped in API
- [ ] Ensure data transformations maintain data types
- [ ] Handle null/undefined values gracefully
- [ ] Format currency and date values consistently

### Testing
- [ ] Test all filter combinations
- [ ] Verify data displays correctly in cards
- [ ] Check property profile tab data
- [ ] Validate search functionality
- [ ] Test pagination and sorting

---

## Notes for Development

1. **Always use the field mapping** when adding new features
2. **Maintain unique IDs** for all interactive elements
3. **Handle null values** - Many fields may be null in database
4. **Format consistently** - Use the same formatters across components
5. **Cache frequently used data** - Property types, cities, etc.
6. **Validate data types** - Ensure numbers are numbers, dates are dates

---

## Version History
- v1.0.0 (2025-01-09): Initial comprehensive mapping
- Created by: AI Assistant
- Purpose: Complete field mapping between Supabase and UI

---

**For AI Assistants:** Use this document as the authoritative source for all data field mappings. When implementing features or debugging, refer to the element IDs and Supabase fields specified here.