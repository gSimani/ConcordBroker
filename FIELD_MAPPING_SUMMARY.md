# Field Mapping Summary - Quick Reference

## Critical Supabase → UI Mappings

### Property Cards (Search Results)
```
florida_parcels.phy_addr1        → Site Address
florida_parcels.phy_city         → City
florida_parcels.phy_zipcd        → ZIP Code
florida_parcels.owner_name       → Owner Name
florida_parcels.just_value       → Market Value (N/A if null)
florida_parcels.taxable_value    → Taxable Value
florida_parcels.land_value       → Current Land Value (N/A if null)
florida_parcels.total_living_area → Adj. Bldg. S.F. (N/A if null)
florida_parcels.land_sqft        → Total Land Area
florida_parcels.year_built       → Act. Year Built (N/A if null)
florida_parcels.bedrooms         → Beds
florida_parcels.bathrooms        → Baths
florida_parcels.units            → Units
florida_parcels.property_use     → DOR Use Code (determines badge color)
florida_parcels.sale_price       → Last Sale Price
florida_parcels.sale_date        → Last Sale Date
```

### Property Profile Page
```
HEADER SECTION:
florida_parcels.phy_addr1        → Main Address Display
florida_parcels.phy_city + phy_zipcd → City, FL ZIP

OVERVIEW TAB:
florida_parcels.owner_name       → Owner Information
florida_parcels.property_use_desc → Property Type
florida_parcels.subdivision      → Subdivision
florida_parcels.legal_desc       → Legal Description

VALUATION SECTION:
florida_parcels.just_value       → Just (Market) Value
florida_parcels.assessed_value   → Assessed Value
florida_parcels.taxable_value    → Taxable Value (School)
florida_parcels.land_value       → Land Value
florida_parcels.building_value   → Building Value

TAX INFORMATION:
florida_parcels.homestead_exemption → Homestead Exemption (Yes/No)
nav_assessments table            → Non-Ad Valorem Assessments

SALES HISTORY:
property_sales_history table     → Sales Timeline
florida_parcels.sale_price       → Most Recent Sale
florida_parcels.sale_date        → Sale Date

LAND CALCULATIONS:
florida_parcels.land_sqft        → Square Feet
florida_parcels.land_acres       → Acres
```

### Search Filters
```
FILTER INPUT → DATABASE FIELD:
City Select         → florida_parcels.phy_city
Address Search      → florida_parcels.phy_addr1
ZIP Code           → florida_parcels.phy_zipcd
Owner Name         → florida_parcels.owner_name
Property Type      → florida_parcels.property_use_desc
Min/Max Value      → florida_parcels.just_value
Min/Max Building   → florida_parcels.total_living_area
Min/Max Land       → florida_parcels.land_sqft
```

## DOR Use Code → Property Type Badge

```
Code starts with:
'0' → Residential (green badge)
'1','2','3' → Commercial (blue badge)
'4' → Industrial (orange badge)
'5','6' → Agricultural (yellow badge)
'7','8' → Institutional (purple badge)
'9' → Miscellaneous (gray badge)
```

## Common Issues & Solutions

### "N/A" Display Issues
**Problem:** Fields show "N/A" when data exists
**Solution:** Check field mapping:
- Ensure API returns correct field name
- Verify component uses right property name
- Check for null handling in formatter functions

### Missing Data
**Problem:** Some fields always null
**Check:**
1. Does florida_parcels table have this column?
2. Is the column populated with data?
3. Is the API mapping the field correctly?

### Wrong Data Type
**Problem:** Numbers showing as strings or vice versa
**Solution:** 
- Ensure API converts types: `parseInt()`, `parseFloat()`
- Format in component: `formatCurrency()`, `toLocaleString()`

## Element ID Quick Reference

### Property Card IDs
```html
<div id="property-card-{parcelId}">
  <span id="property-card-{parcelId}-address">
  <span id="property-card-{parcelId}-city">
  <span id="property-card-{parcelId}-owner">
  <span id="property-card-{parcelId}-just-value">
  <span id="property-card-{parcelId}-land-value">
  <span id="property-card-{parcelId}-building-sqft">
  <span id="property-card-{parcelId}-year-built">
</div>
```

### Property Profile IDs
```html
<div id="property-profile-container">
  <h1 id="property-profile-address">
  <span id="property-profile-city-state-zip">
  
  <!-- Overview Tab -->
  <div id="property-tab-overview">
    <span id="overview-owner-name">
    <span id="overview-property-type">
    <span id="overview-living-area">
    <span id="overview-land-area">
    <span id="overview-year-built">
  </div>
  
  <!-- Tax Tab -->
  <div id="property-tab-taxes">
    <span id="tax-just-value">
    <span id="tax-taxable-value">
    <span id="tax-homestead-exemption">
  </div>
</div>
```

### Filter IDs
```html
<select id="properties-filter-city">
<input id="properties-filter-address">
<input id="properties-filter-owner">
<input id="properties-filter-min-value">
<input id="properties-filter-max-value">
```

## API Response Format

```javascript
// From /api/properties/search
{
  "properties": [{
    "id": 1234,
    "parcel_id": "504232100001",
    "phy_addr1": "123 MAIN ST",
    "phy_city": "FORT LAUDERDALE",
    "phy_zipcd": "33301",
    "own_name": "SMITH JOHN",
    "property_type": "Single Family",
    "dor_uc": "001",
    "jv": 525000,         // just_value
    "tv_sd": 475000,      // taxable_value
    "lnd_val": 225000,    // land_value
    "tot_lvg_area": 2800, // total_living_area
    "lnd_sqfoot": 8500,   // land_sqft
    "act_yr_blt": 2005,   // year_built
    "sale_prc1": 485000,  // sale_price
    "sale_yr1": "2021"    // sale year
  }]
}
```

## Testing Checklist

- [ ] Property cards display address: `florida_parcels.phy_addr1`
- [ ] Owner name shows: `florida_parcels.owner_name`
- [ ] Just value displays correctly: `florida_parcels.just_value`
- [ ] Land value shows or says N/A: `florida_parcels.land_value`
- [ ] Building sqft shows: `florida_parcels.total_living_area`
- [ ] Year built displays: `florida_parcels.year_built`
- [ ] Property type badge color matches DOR code
- [ ] Filters work with correct database fields
- [ ] All elements have unique IDs following naming convention

---
**Last Updated:** January 9, 2025
**Use this document** when debugging data display issues or adding new fields.