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
