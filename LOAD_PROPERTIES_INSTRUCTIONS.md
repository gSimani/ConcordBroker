# How to Load All 753,243 Properties into Supabase

You currently have 86,149 properties. To get ALL properties, follow these steps:

## Method 1: Direct CSV Import in Supabase (RECOMMENDED - Fastest)

1. **Go to Supabase Dashboard**
   - https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp
   
2. **Navigate to Table Editor**
   - Click "Table Editor" in the left sidebar
   - Select `florida_parcels` table

3. **Import CSV**
   - Click the "Import data" button (or three dots menu → Import data from CSV)
   - Upload the file: `NAL16P202501.csv` (387 MB)

4. **Map Columns** (IMPORTANT - Use these exact mappings):
   ```
   PARCEL_ID → parcel_id
   OWN_NAME → owner_name
   OWN_ADDR1 → owner_addr1
   OWN_CITY → owner_city
   OWN_STATE → owner_state
   OWN_ZIPCD → owner_zip
   PHY_ADDR1 → phy_addr1
   PHY_CITY → phy_city
   PHY_ZIPCD → phy_zipcd
   DOR_UC → property_use
   TV_SD → taxable_value
   TV_NSD → taxable_value (if TV_SD is empty)
   JV → just_value
   LND_VAL → land_value
   ACT_YR_BLT → year_built
   TOT_LVG_AREA → total_living_area
   LND_SQFOOT → land_sqft
   S_LEGAL → legal_desc
   SUBDIVISION → subdivision
   SALE_PRC1 → sale_price
   ```

5. **Set Import Options**:
   - Check "Replace duplicate rows" or "Upsert"
   - Primary key: `parcel_id`
   - Set default values:
     - county: 'BROWARD'
     - year: 2025
     - is_redacted: false
     - data_source: 'NAL_2025'

6. **Start Import**
   - Click "Import"
   - This will take 5-10 minutes for 753k records

## Method 2: Use Python Script (If CSV Import Fails)

Run this command:
```bash
python load_all_florida_properties.py
```

## Why You Need All Properties

With all 753,243 properties, you'll have:
- **Complete Coverage**: Every single property in Broward County
- **Better Search**: Find any address, owner, or parcel ID
- **Full Market Data**: Accurate statistics and filters
- **No Missing Properties**: Users can find ANY property they search for

## After Loading

Once loaded, refresh your properties page:
- http://localhost:5174/properties

You should see:
- Total count shows 753,243 properties
- Search works for ANY address in Broward
- Filters show accurate counts
- Autocomplete finds all addresses

## Troubleshooting

If the count still shows 86,149:
1. Check if import completed successfully in Supabase logs
2. Clear browser cache (Ctrl+Shift+R)
3. Check database directly:
   ```sql
   SELECT COUNT(*) FROM florida_parcels;
   ```

The NAL file is your complete source with ALL properties. Once loaded, your app will have complete coverage of Broward County!