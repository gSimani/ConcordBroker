# Sales History Import - Final Instructions

## Current Status

✅ **Data Ready**: 90,061+ sales records parsed from Broward County SDF file
✅ **All Counties Downloaded**: SDF files for all 67 Florida counties already extracted
✅ **Import Script Ready**: Tested and working
❌ **Schema Issue**: `property_sales_history` table missing `county` column

## STEP 1: Fix Table Schema (REQUIRED)

The `property_sales_history` table exists but has `county_no` instead of `county` column.

### Run this SQL in Supabase Dashboard:

1. Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql/new
2. Paste this SQL:

```sql
-- Add county column to property_sales_history table
ALTER TABLE property_sales_history
ADD COLUMN IF NOT EXISTS county TEXT;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_sales_county
ON property_sales_history(county);

-- Verify the column was added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'property_sales_history'
ORDER BY ordinal_position;
```

3. Click "Run" button
4. Verify output shows `county | text` in the results

## STEP 2: Import Broward County (Test)

Run this command to import Broward County sales data (~90K records):

```bash
export SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0
python scripts/import_broward_sdf_auto.py
```

**Expected**:
- Parse: ~90,061 sales records
- Import: ~90,061 records to Supabase
- Time: ~5 minutes

## STEP 3: Import All Counties (Full Dataset)

After Broward succeeds, import all 67 counties:

```bash
export SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0
python scripts/import_sdf_csv_to_supabase.py
```

**Expected**:
- Process: All 67 counties with SDF files
- Import: Estimated 1-5 million sales records
- Time: 1-3 hours

## STEP 4: Verify in UI

1. Start web app: `cd apps/web && npm run dev`
2. Navigate to: http://localhost:5178/property/474119000000
3. Check "Core Property Info" tab → "Sales History" section
4. Should see sales data with dates, prices, and clickable Book/Page links

## What the Import Does

### Data Mapping:
- **Parcel ID**: Converts scientific notation (4.74119E+11) → string (474119000000)
- **Sale Price**: Stores in cents ($450,000 → 45000000 cents)
- **Sale Date**: Formats as YYYY-MM-01
- **OR Book/Page**: Maps to clickable Miami-Dade Clerk links
- **Quality Code**: Q=Qualified, U=Unqualified

### Example Record:
```json
{
  "parcel_id": "474119000000",
  "county": "BROWARD",
  "sale_date": "2024-09-01",
  "sale_price": 5250000000,  // $52.5M in cents
  "sale_year": 2024,
  "sale_month": 9,
  "quality_code": "Q",
  "clerk_no": "119795010",
  "or_book": "29485",
  "or_page": "3721",
  "data_source": "florida_sdf_broward_2025"
}
```

## Troubleshooting

### Import fails with "county column not found"
→ Run STEP 1 SQL to add the column

### Import succeeds but sales still don't show in UI
→ Check browser console for errors
→ Verify parcel ID matches (e.g., 474119000000 vs 4.74119E+11)

### Some counties have no SDF folder
→ Normal - not all counties have sales data files
→ Script will skip them automatically

## Files Created

| File | Purpose |
|------|---------|
| `scripts/import_broward_sdf_auto.py` | Import single county (Broward) |
| `scripts/import_sdf_csv_to_supabase.py` | Import all 67 counties |
| `ALTER_SALES_TABLE.sql` | SQL to fix table schema |
| `SALES_HISTORY_DATA_ISSUE.md` | Detailed problem analysis |

## Quick Summary

1. ✅ SDF files already downloaded
2. ❌ Add `county` column to table (SQL above)
3. ▶️ Run `python scripts/import_broward_sdf_auto.py`
4. ✅ Verify sales appear in UI
5. ▶️ Run `python scripts/import_sdf_csv_to_supabase.py` for all counties

---

**Ready to proceed?** Run the SQL in Supabase Dashboard, then execute the import script.
