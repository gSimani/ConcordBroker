# DATABASE TO UI MAPPING - Complete Data Flow Analysis

## 🎯 Purpose
This document maps EXACTLY where each database table's data appears in the UI, ensuring no data is lost during migration.

---

## 📊 TABLE: `florida_parcels` / `latest_parcels` → Should be `parcels`

### Current Usage in Code:
- **Frontend:** `apps/web/src/lib/supabase.ts` - Lines 93, 183, 195, 218, 240
- **Frontend:** `apps/web/src/pages/properties/PropertySearchSupabase.tsx` - Line 102
- **Backend:** `apps/api/entity_matching_service.py` - Line 490

### Where Data Displays in UI:

#### 1. **Property Search Page** (`/properties`)
```typescript
// PropertySearchSupabase.tsx - Line 102
const { data } = await supabase
  .from('florida_parcels')  // ← NEEDS CHANGE TO 'parcels'
  .select('*')
```
**UI Elements:**
- Property cards grid
- Search results list
- Map markers

**Fields Displayed:**
- `parcel_id` → Property ID badge
- `site_address` → Card title
- `site_city`, `site_zip` → Location info
- `owner_name` → Owner section
- `assessed_value` → Price display
- `total_square_feet` → Size info
- `year_built` → Property age
- `property_use_code` → Property type badge

#### 2. **Property Detail Page** (`/property/:id`)
```typescript
// lib/supabase.ts - getPropertyById()
.from('florida_parcels')
.select('*')
.eq('parcel_id', id)
```
**UI Elements:**
- Property header
- Overview tab
- Details sidebar
- Map view

**Fields Displayed:**
- ALL fields from parcels table
- Geometry data for map display

#### 3. **Dashboard Statistics** (`/dashboard`)
```typescript
// lib/supabase.ts - getPropertyStats()
.from('florida_parcels')
.select('assessed_value, site_city')
```
**UI Elements:**
- Total value card
- Properties by city chart
- Average values

---

## 📊 TABLE: `property_sales_history` → Should be `sales_history`

### Current Usage:
- **Backend:** Expected as `sales_history` in multiple places
- **Frontend:** Property detail tabs expect this data

### Where Data SHOULD Display:

#### 1. **Property Detail - Sales History Tab**
```typescript
// PropertyProfile.tsx - Sales History Section
<div id="sales-history-tab">
  <table id="sales-history-table">
    <!-- Each row needs: -->
    <!-- sale_date, sale_price, buyer_name, seller_name -->
  </table>
</div>
```
**Currently Shows:** "No sales data available" ❌

#### 2. **Market Analysis Dashboard**
```typescript
// MarketTrends.tsx
<div id="market-trends-chart">
  <!-- Needs aggregated sales data -->
</div>
```
**Currently Shows:** Empty chart ❌

#### 3. **Property Card - Last Sale Info**
```typescript
// PropertyCard.tsx
<div id="property-card-last-sale">
  <span>Last Sale: {last_sale_date}</span>
  <span>Price: ${last_sale_price}</span>
</div>
```
**Currently Shows:** "N/A" ❌

---

## 📊 TABLE: `nav_assessments` → Tax Assessment Data

### Where Data SHOULD Display:

#### 1. **Property Tax Tab**
```typescript
// PropertyProfile.tsx - Tax Information Tab
<div id="property-tax-tab">
  <div id="assessed-value">{assessed_value}</div>
  <div id="taxable-value">{taxable_value}</div>
  <div id="tax-amount">{tax_amount}</div>
  <div id="millage-rate">{millage_rate}</div>
</div>
```
**Currently Shows:** Only 1 record exists ❌

#### 2. **Tax Calculator Component**
```typescript
// TaxCalculator.tsx
<div id="tax-calculator">
  <!-- Needs assessment data for calculations -->
</div>
```
**Currently Shows:** Cannot calculate ❌

---

## 📊 TABLE: `sunbiz_corporate` / `sunbiz_partnerships` → Business Entities

### Current Usage:
- **Backend:** `entity_matching_service.py` uses extensively
- **Frontend:** Business entity section in property details

### Where Data SHOULD Display:

#### 1. **Property Detail - Business Entity Tab**
```typescript
// BusinessEntitySection.tsx
<div id="business-entity-tab">
  <div id="entity-name">{corp_name}</div>
  <div id="entity-status">{status}</div>
  <div id="filing-date">{filing_date}</div>
  <div id="registered-agent">{agent_name}</div>
  <div id="principal-address">{principal_addr}</div>
</div>
```
**Currently Shows:** "No business entity found" ❌

#### 2. **Owner Network Visualization**
```typescript
// OwnerNetwork.tsx
<div id="owner-network-graph">
  <!-- Needs entity relationships -->
</div>
```
**Currently Shows:** No connections ❌

---

## 📊 TABLE: `florida_permits` / `building_permits`

### Where Data SHOULD Display:

#### 1. **Property Detail - Permits Tab**
```typescript
// PermitsTab.tsx
<div id="permits-tab">
  <table id="permits-table">
    <tr>
      <td>{permit_number}</td>
      <td>{permit_type}</td>
      <td>{issue_date}</td>
      <td>{estimated_value}</td>
      <td>{status}</td>
    </tr>
  </table>
</div>
```
**Currently Shows:** Only 1 permit ❌

---

## 🔄 DATA FLOW PATHS

### Path 1: Property Search Flow
```
User Search Input
    ↓
PropertySearchSupabase.tsx (Line 102)
    ↓
supabase.from('florida_parcels')  ← BREAKS HERE
    ↓
Property Cards Grid
```

### Path 2: Property Detail Flow
```
Click Property Card
    ↓
Router: /property/:id
    ↓
EnhancedPropertyProfile.tsx
    ↓
usePropertyData hook
    ↓
supabase.from('florida_parcels')  ← NEEDS 'parcels'
    ↓
Tabs: Overview | Details | Sales | Tax | Permits | Entities
         ↓         ↓        ↓      ↓      ↓         ↓
    [ALL NEED THEIR RESPECTIVE DATA TABLES]
```

### Path 3: Dashboard Analytics Flow
```
Dashboard Page Load
    ↓
getPropertyStats()
    ↓
Aggregate from 'florida_parcels'  ← NEEDS 'parcels'
    ↓
Stats Cards & Charts
```

---

## 🚨 CRITICAL UI COMPONENTS AFFECTED BY TABLE CHANGES

### Components Reading from `florida_parcels` (Must Update):
1. **PropertySearchSupabase.tsx** - Line 102
2. **supabase.ts** - Lines 93, 183, 195, 218, 240
3. **populate-data.ts** - Lines 118, 126, 135, 231
4. **test-property-data.ts** - Line 45
5. **ParcelMonitor.tsx** - Line 94

### Components Expecting `sales_history` (Currently Broken):
1. **PropertyProfile Sales Tab**
2. **Market Trends Dashboard**
3. **Property Value History Chart**

### Components Expecting `tax_assessments` (Currently Broken):
1. **Property Tax Tab**
2. **Tax Calculator**
3. **Assessment History**

### Components Expecting Business Entities (Currently Broken):
1. **Business Entity Tab**
2. **Owner Network Graph**
3. **Entity Search**

---

## ✅ VALIDATION CHECKLIST

Before making ANY table changes:

### For `florida_parcels` → `parcels`:
- [ ] Update PropertySearchSupabase.tsx line 102
- [ ] Update all 5 references in supabase.ts
- [ ] Update populate-data.ts references
- [ ] Update ParcelMonitor.tsx
- [ ] Test property search still works
- [ ] Test property detail page loads
- [ ] Test dashboard statistics calculate

### For `property_sales_history` → `sales_history`:
- [ ] Create view or rename table
- [ ] Test sales history tab populates
- [ ] Test last sale info shows on cards
- [ ] Test market trends chart works

### For Loading New Data:
- [ ] Load into correct table names
- [ ] Verify data appears in UI
- [ ] Test all dependent components
- [ ] Check performance impact

---

## 🎯 PRIORITY FIX ORDER

1. **Fix parcels table** (Most critical - breaks search)
2. **Fix sales_history** (Needed for property values)
3. **Load tax_assessments** (Needed for tax info)
4. **Load sunbiz data** (Needed for entity matching)
5. **Load permits** (Enhancement feature)

---

## 📝 TESTING ENDPOINTS

After each change, test these URLs:
1. `/properties` - Search should work
2. `/property/494824100000020` - Detail page should load
3. `/dashboard` - Stats should calculate
4. Property tabs should show data:
   - Sales History Tab
   - Tax Information Tab
   - Permits Tab
   - Business Entity Tab