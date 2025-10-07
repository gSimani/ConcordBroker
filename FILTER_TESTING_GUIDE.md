# Comprehensive Property Filter Testing Guide

## Overview
This guide provides systematic testing for ALL property filter buttons after the recent mapping updates.

### Updated Mappings (December 2024)
Based on analysis of the actual florida_parcels database:

```javascript
PROPERTY_TYPE_TO_DB_VALUES = {
  'Residential': [0, 1, 2, 4, 8, 9], // Includes vacant res + various residential types
  'Commercial': [11, 19, 28],        // Stores, Professional Services, Parking Lots
  'Industrial': [48, 52, 60],        // Warehousing, Other Industrial, Light Manufacturing
  'Agricultural': [80, 87],          // Undefined Agricultural, Citrus
  'Vacant Land': [0],                // Vacant Residential only
  'Multi-Family': [8],               // Multi-Family (10+ units)
  'Condo': [4],                      // Condominiums
  'Government': [93, 96],            // Municipal Service, Federal
  'Religious': [71],                 // Churches, Temples
  'Conservation': [],                // Empty (no matching properties)
  'Vacant/Special': [0]              // Vacant Residential (legacy)
}
```

## Testing Instructions

### Prerequisites
1. Frontend running at: http://localhost:5173
2. Backend API at: http://localhost:3001 (with MCP fallback to 3005)
3. Browser with Developer Tools open (F12)
4. Network tab active to monitor API calls

### Step-by-Step Filter Testing

#### 1. Navigate to Property Search
1. Open http://localhost:5173
2. Go to property search page
3. Ensure "All Properties" is selected initially
4. Open browser DevTools > Network tab
5. Clear existing network logs

---

### Filter Button Tests

#### Test 1: Residential Filter
**Expected property_use_values: [0,1,2,4,8,9]**

1. **Click "Residential" filter button**
2. **Monitor Network tab:**
   - Look for API call to `/api/supabase/florida_parcels`
   - Check query parameters contain: `property_use_values=0,1,2,4,8,9`
3. **Verify Results:**
   - Properties load successfully
   - Property cards show "Residential", "Condo", "Multi-Family" badges
   - Mix of single family homes, condos, mobile homes, multi-family
   - Some vacant residential lots may appear (property_use=0)
4. **Sample Property Types Expected:**
   - Single family homes (property_use=1)
   - Mobile homes (property_use=2)
   - Condominiums (property_use=4)
   - Multi-family (property_use=8)
   - Misc residential (property_use=9)
   - Vacant residential (property_use=0)

---

#### Test 2: Commercial Filter
**Expected property_use_values: [11,19,28]**

1. **Click "Commercial" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=11,19,28`
3. **Verify Results:**
   - Properties show "Commercial" badges
   - Stores, office buildings, professional services
   - Parking lots/commercial parking
4. **Sample Property Types Expected:**
   - Retail stores (property_use=11)
   - Professional services (property_use=19)
   - Parking lots (property_use=28)

---

#### Test 3: Industrial Filter
**Expected property_use_values: [48,52,60]**

1. **Click "Industrial" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=48,52,60`
3. **Verify Results:**
   - Properties show "Industrial" badges
   - Warehouses, manufacturing, distribution centers
4. **Sample Property Types Expected:**
   - Warehousing/distribution (property_use=48)
   - Other industrial (property_use=52)
   - Light manufacturing (property_use=60)

---

#### Test 4: Agricultural Filter
**Expected property_use_values: [80,87]**

1. **Click "Agricultural" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=80,87`
3. **Verify Results:**
   - Properties show "Agricultural" badges
   - Farms, groves, agricultural land
4. **Sample Property Types Expected:**
   - Undefined agricultural (property_use=80)
   - Citrus groves (property_use=87)

---

#### Test 5: Vacant Land Filter
**Expected property_use_values: [0]**

1. **Click "Vacant Land" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=0`
3. **Verify Results:**
   - Properties show "Vacant Land" badges
   - Empty lots, undeveloped land
   - Properties typically have no address or show "No Address"
4. **Sample Property Types Expected:**
   - Vacant residential land (property_use=0)

---

#### Test 6: Multi-Family Filter
**Expected property_use_values: [8]**

1. **Click "Multi-Family" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=8`
3. **Verify Results:**
   - Properties show "Multi-Family" badges
   - Apartment complexes, large residential buildings
4. **Sample Property Types Expected:**
   - Multi-family 10+ units (property_use=8)

---

#### Test 7: Condo Filter
**Expected property_use_values: [4]**

1. **Click "Condo" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=4`
3. **Verify Results:**
   - Properties show "Condo" badges
   - Condominium units
4. **Sample Property Types Expected:**
   - Condominiums (property_use=4)

---

#### Test 8: Government Filter
**Expected property_use_values: [93,96]**

1. **Click "Government" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=93,96`
3. **Verify Results:**
   - Properties show "Government" badges
   - Government buildings, municipal facilities
4. **Sample Property Types Expected:**
   - Municipal services (property_use=93)
   - Federal government (property_use=96)

---

#### Test 9: Religious Filter
**Expected property_use_values: [71]**

1. **Click "Religious" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=71`
3. **Verify Results:**
   - Properties show "Religious" badges
   - Churches, temples, religious facilities
4. **Sample Property Types Expected:**
   - Churches/temples (property_use=71)

---

#### Test 10: Conservation Filter
**Expected: Empty results (no matching properties)**

1. **Click "Conservation" filter button**
2. **Monitor Network tab:**
   - Check API call made (may have empty property_use_values)
3. **Verify Results:**
   - No properties returned (empty list)
   - Message like "No properties found" or empty grid
   - This is expected since Conservation category has no matching property_use values

---

#### Test 11: Vacant/Special Filter
**Expected property_use_values: [0]**

1. **Click "Vacant/Special" filter button**
2. **Monitor Network tab:**
   - Check query parameters: `property_use_values=0`
3. **Verify Results:**
   - Same as Vacant Land (legacy compatibility)
   - Properties show vacant or special use badges
4. **Sample Property Types Expected:**
   - Vacant residential (property_use=0)

---

### Performance Testing

#### Response Time Benchmarks
Monitor and record response times for each filter:

| Filter | Expected Response Time | Actual Time | Status |
|--------|------------------------|-------------|---------|
| Residential | < 2 seconds | _____ | ⬜ |
| Commercial | < 2 seconds | _____ | ⬜ |
| Industrial | < 2 seconds | _____ | ⬜ |
| Agricultural | < 2 seconds | _____ | ⬜ |
| Vacant Land | < 2 seconds | _____ | ⬜ |
| Multi-Family | < 2 seconds | _____ | ⬜ |
| Condo | < 2 seconds | _____ | ⬜ |
| Government | < 2 seconds | _____ | ⬜ |
| Religious | < 2 seconds | _____ | ⬜ |
| Conservation | < 1 second | _____ | ⬜ |
| Vacant/Special | < 2 seconds | _____ | ⬜ |

---

### Error Testing

#### Test API Failures
1. **Test with MCP server down:**
   - Stop MCP server (if running on port 3005)
   - Click filters - should fallback to sample data
   - Verify graceful degradation

2. **Test with invalid county:**
   - Change county to invalid value
   - Click filters - should return empty or error gracefully

---

### Cross-Filter Testing

#### Test Filter Combinations
1. **County + Property Type:**
   - Select different county
   - Click property type filter
   - Verify both filters applied in API call

2. **Property Type + Additional Filters:**
   - Click property type filter
   - Add city or address filter
   - Verify multiple parameters in API call

---

### User Interface Testing

#### Visual Validation
For each filter button clicked:

1. **Button State:**
   - ✅ Button highlights/changes color when active
   - ✅ Button returns to normal when deselected
   - ✅ Only one property type active at a time

2. **Results Display:**
   - ✅ Property cards load properly
   - ✅ Correct category badges on cards
   - ✅ Property count updates
   - ✅ Loading indicators work

3. **Property Card Validation:**
   - ✅ Property use descriptions match filter
   - ✅ Owner names logical for category
   - ✅ Addresses appropriate for property type

---

## Common Issues to Check

### 1. Property Use Value Conflicts
- **Issue:** Vacant Land (0) also included in Residential filter
- **Expected:** This is intentional - vacant residential lots are included in residential
- **Action:** Verify vacant residential lots show appropriate badges

### 2. Missing Properties
- **Issue:** Expected properties not appearing
- **Check:** Database actually contains properties with those property_use values
- **Action:** Query database directly to verify data exists

### 3. Incorrect Categorization
- **Issue:** Properties showing wrong category badges
- **Check:** `getPropertyCategoryFromCode()` function in propertyCategories.ts
- **Action:** Verify property_use values map to correct categories

### 4. API Authentication
- **Issue:** 401 Unauthorized errors
- **Check:** API key header (`x-api-key: concordbroker-mcp-key-claude`)
- **Action:** Verify MCP server running and configured properly

---

## Success Criteria

### ✅ All Filters Working
- [ ] All 11 filter buttons make correct API calls
- [ ] Correct property_use_values sent in query parameters
- [ ] Properties load successfully (or empty for Conservation)
- [ ] Property cards show correct category badges
- [ ] Response times under 2 seconds
- [ ] No JavaScript errors in console
- [ ] Graceful fallback to sample data if APIs fail

### ✅ Mapping Accuracy
- [ ] Residential filter includes all residential types (including vacant)
- [ ] Commercial filter shows business properties only
- [ ] Industrial filter shows warehouses/manufacturing only
- [ ] Vacant Land shows empty lots only
- [ ] Government shows municipal/federal properties only
- [ ] Religious shows churches/temples only
- [ ] Conservation returns empty (as expected)

### ✅ User Experience
- [ ] Filter buttons respond immediately
- [ ] Loading states show appropriately
- [ ] Error messages are user-friendly
- [ ] Property cards are informative
- [ ] Filter combinations work properly

---

## Troubleshooting

### If Filters Don't Work:
1. Check MCP server is running (port 3005 or 3001)
2. Verify API key is correct
3. Check database connectivity
4. Review browser console for errors
5. Test with sample data fallback

### If Properties Show Wrong Categories:
1. Check `PROPERTY_USE_TO_CATEGORY` mapping in propertyCategories.ts
2. Verify `getPropertyCategoryFromCode()` function
3. Check property_use values in database match expectations

### If Performance is Slow:
1. Check database indexes on property_use and county fields
2. Monitor API response times
3. Verify efficient queries (no full table scans)
4. Check for network latency issues

---

## Documentation

After testing, document:
1. Which filters work correctly
2. Which filters need fixes
3. Performance measurements
4. Any mapping adjustments needed
5. User experience improvements

This comprehensive testing ensures all property filter buttons work correctly with the updated database value mappings.