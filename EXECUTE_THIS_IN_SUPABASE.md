# 🗄️ Execute This SQL in Supabase Dashboard

## Quick Steps:

1. **Open Supabase SQL Editor:**
   - Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql
   - Or: Dashboard → SQL Editor → New Query

2. **Copy and paste this SQL:**

```sql
-- Make parcel_id nullable in tax_deed_bidding_items
-- This allows past auction summaries without individual parcel IDs (e.g., BROWARD aggregate data)

-- Make parcel_id nullable
ALTER TABLE tax_deed_bidding_items
ALTER COLUMN parcel_id DROP NOT NULL;

-- Verify the change
DO $$
BEGIN
    -- Check if parcel_id is now nullable
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tax_deed_bidding_items'
        AND column_name = 'parcel_id'
        AND is_nullable = 'YES'
    ) THEN
        RAISE NOTICE '✅ Success: parcel_id is now nullable';
    ELSE
        RAISE EXCEPTION '❌ Failed: parcel_id is still NOT NULL';
    END IF;
END $$;

-- Add comment explaining why this is nullable
COMMENT ON COLUMN tax_deed_bidding_items.parcel_id IS
'Parcel ID for individual properties. Nullable to support aggregate auction summaries (e.g., BROWARD past sales: "64 items sold" without individual parcel data)';
```

3. **Click "Run"** (or press Ctrl/Cmd + Enter)

4. **Verify Success:**
   - You should see: ✅ Success: parcel_id is now nullable

5. **Then run upload:**
   ```bash
   python scripts/upload_tax_deed_fixed_env.py
   ```

## What This Does:

- Makes `parcel_id` column nullable
- Allows BROWARD past auction summaries to be uploaded (they don't have individual parcel IDs)
- Adds documentation comment explaining why
- Includes verification to confirm the change worked

## After Execution:

Once successful, the upload script will add 5 BROWARD past auction records:
- 10/15/2025 Tax Deed Sale - 64 items
- 9/17/2025 Tax Deed Sale - 46 items
- 8/20/2025 Tax Deed Sale - 31 items
- 7/23/2025 Tax Deed Sale - 31 items
- 6/25/2025 Tax Deed Sale - 47 items

Then BROWARD will show in the Tax Deed Sales page with historical data!
