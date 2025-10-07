-- Add DOR use code relationships to existing property tables
-- This migration adds foreign keys to link properties with DOR use codes

-- Add foreign key constraint to florida_parcels table if it exists
DO $$
BEGIN
    -- Check if florida_parcels table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'florida_parcels') THEN

        -- Add foreign key constraint for dor_uc column if it exists
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'florida_parcels' AND column_name = 'dor_uc') THEN

            -- First, pad any existing dor_uc values to 3 digits
            UPDATE public.florida_parcels
            SET dor_uc = LPAD(dor_uc::TEXT, 3, '0')
            WHERE dor_uc IS NOT NULL AND LENGTH(dor_uc::TEXT) < 3;

            -- Check if constraint already exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_type = 'FOREIGN KEY'
                AND table_name = 'florida_parcels'
                AND constraint_name = 'fk_florida_parcels_dor_uc'
            ) THEN
                -- Add the foreign key constraint (with ON DELETE SET NULL for safety)
                ALTER TABLE public.florida_parcels
                ADD CONSTRAINT fk_florida_parcels_dor_uc
                FOREIGN KEY (dor_uc) REFERENCES public.dor_use_codes(code)
                ON DELETE SET NULL
                ON UPDATE CASCADE;

                RAISE NOTICE 'Added foreign key constraint fk_florida_parcels_dor_uc';
            END IF;
        END IF;
    END IF;
END $$;

-- Add indexes for better join performance
DO $$
BEGIN
    -- Index on florida_parcels.dor_uc if not exists
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND tablename = 'florida_parcels' AND indexname = 'idx_florida_parcels_dor_uc') THEN
        CREATE INDEX idx_florida_parcels_dor_uc ON public.florida_parcels(dor_uc);
        RAISE NOTICE 'Created index idx_florida_parcels_dor_uc';
    END IF;
END $$;

-- Create a function to enrich property data with DOR use code details
CREATE OR REPLACE FUNCTION public.get_property_with_dor_details(p_parcel_id TEXT)
RETURNS TABLE (
    parcel_id TEXT,
    county TEXT,
    owner_name TEXT,
    property_address TEXT,
    dor_uc CHAR(3),
    dor_category VARCHAR(50),
    dor_subcategory VARCHAR(50),
    dor_description TEXT,
    is_residential BOOLEAN,
    is_commercial BOOLEAN,
    is_vacant BOOLEAN,
    just_value NUMERIC,
    assessed_value NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fp.parcel_id,
        fp.county,
        fp.owner_name,
        fp.phy_addr1 as property_address,
        fp.dor_uc,
        duc.category as dor_category,
        duc.subcategory as dor_subcategory,
        duc.description as dor_description,
        duc.is_residential,
        duc.is_commercial,
        duc.is_vacant,
        fp.just_value,
        fp.assessed_value
    FROM public.florida_parcels fp
    LEFT JOIN public.dor_use_codes duc ON fp.dor_uc = duc.code
    WHERE fp.parcel_id = p_parcel_id;
END;
$$;

-- Create a function to get property statistics by DOR category
CREATE OR REPLACE FUNCTION public.get_property_stats_by_dor_category(p_county TEXT DEFAULT NULL)
RETURNS TABLE (
    category VARCHAR(50),
    property_count BIGINT,
    total_just_value NUMERIC,
    avg_just_value NUMERIC,
    total_assessed_value NUMERIC,
    avg_assessed_value NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        duc.category,
        COUNT(fp.parcel_id) as property_count,
        SUM(fp.just_value) as total_just_value,
        AVG(fp.just_value) as avg_just_value,
        SUM(fp.assessed_value) as total_assessed_value,
        AVG(fp.assessed_value) as avg_assessed_value
    FROM public.florida_parcels fp
    JOIN public.dor_use_codes duc ON fp.dor_uc = duc.code
    WHERE (p_county IS NULL OR fp.county = p_county)
    GROUP BY duc.category
    ORDER BY property_count DESC;
END;
$$;

-- Create a view for commonly needed property + DOR code data
CREATE OR REPLACE VIEW public.v_properties_with_dor AS
SELECT
    fp.parcel_id,
    fp.county,
    fp.year,
    fp.owner_name,
    fp.owner_addr1,
    fp.owner_addr2,
    fp.owner_city,
    fp.owner_state,
    fp.owner_zipcode,
    fp.phy_addr1,
    fp.phy_addr2,
    fp.phy_city,
    fp.phy_zipcd,
    fp.dor_uc,
    duc.category as dor_category,
    duc.subcategory as dor_subcategory,
    duc.description as dor_description,
    duc.is_residential,
    duc.is_commercial,
    duc.is_industrial,
    duc.is_agricultural,
    duc.is_institutional,
    duc.is_governmental,
    duc.is_vacant,
    fp.pa_uc,
    fp.just_value,
    fp.assessed_value,
    fp.taxable_value,
    fp.land_value,
    fp.building_value,
    fp.tot_lvg_area,
    fp.land_sqft,
    fp.act_yr_blt,
    fp.eff_yr_blt
FROM public.florida_parcels fp
LEFT JOIN public.dor_use_codes duc ON fp.dor_uc = duc.code;

-- Create indexes on the view's base tables for better performance
CREATE INDEX IF NOT EXISTS idx_florida_parcels_county_dor ON public.florida_parcels(county, dor_uc);
CREATE INDEX IF NOT EXISTS idx_florida_parcels_dor_year ON public.florida_parcels(dor_uc, year);

-- Grant permissions on new functions and views
GRANT EXECUTE ON FUNCTION public.get_property_with_dor_details(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION public.get_property_with_dor_details(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_property_stats_by_dor_category(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION public.get_property_stats_by_dor_category(TEXT) TO authenticated;
GRANT SELECT ON public.v_properties_with_dor TO anon;
GRANT SELECT ON public.v_properties_with_dor TO authenticated;

-- Add comments for documentation
COMMENT ON VIEW public.v_properties_with_dor IS 'Comprehensive view joining florida_parcels with DOR use codes for easy access to property categorization';
COMMENT ON FUNCTION public.get_property_with_dor_details IS 'Returns detailed property information enriched with DOR use code classifications';
COMMENT ON FUNCTION public.get_property_stats_by_dor_category IS 'Returns aggregate statistics for properties grouped by DOR category, optionally filtered by county';