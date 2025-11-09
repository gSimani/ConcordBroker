-- ===================================================================
-- NAL DATA MIGRATION SCRIPT
-- Migrate data from existing florida_parcels to new normalized schema
-- Handle 165 NAL fields with proper field mapping
-- ===================================================================

-- ===================================================================
-- MIGRATION CONFIGURATION AND SAFETY CHECKS
-- ===================================================================

-- Check if source table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'florida_parcels') THEN
        RAISE EXCEPTION 'Source table florida_parcels does not exist. Cannot proceed with migration.';
    END IF;
    
    RAISE NOTICE 'Source table florida_parcels found. Proceeding with migration...';
END $$;

-- Create backup table before migration
DROP TABLE IF EXISTS florida_parcels_backup_migration;
CREATE TABLE florida_parcels_backup_migration AS TABLE florida_parcels;

RAISE NOTICE 'Backup table created: florida_parcels_backup_migration';

-- ===================================================================
-- MIGRATION FUNCTIONS
-- ===================================================================

-- Function to map NAL fields to normalized structure
CREATE OR REPLACE FUNCTION migrate_nal_data_to_normalized()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    migration_report TEXT := '';
    record_count INTEGER := 0;
    error_count INTEGER := 0;
    batch_size INTEGER := 10000;
    current_batch INTEGER := 0;
    total_records INTEGER;
BEGIN
    -- Get total record count
    SELECT COUNT(*) INTO total_records FROM florida_parcels;
    
    migration_report := migration_report || format('Starting migration of %s records from florida_parcels...' || chr(10), total_records);
    
    -- ===================================================================
    -- PHASE 1: MIGRATE TO FLORIDA_PROPERTIES_CORE
    -- Map existing fields to core property table
    -- ===================================================================
    
    migration_report := migration_report || 'Phase 1: Migrating to florida_properties_core...' || chr(10);
    
    INSERT INTO florida_properties_core (
        parcel_id,
        co_no,
        county_code,
        assessment_year,
        owner_name,
        physical_address_1,
        physical_address_2,
        physical_city,
        physical_state,
        physical_zipcode,
        just_value,
        assessed_value_school_district,
        assessed_value_non_school_district,
        taxable_value_school_district,
        taxable_value_non_school_district,
        land_value,
        dor_use_code,
        property_appraiser_use_code,
        year_built,
        total_living_area,
        land_square_footage,
        number_of_buildings,
        created_at,
        updated_at,
        source
    )
    SELECT 
        COALESCE(parcel_id, ''),
        CASE 
            WHEN county = 'BROWARD' THEN 16
            WHEN county = 'MIAMI-DADE' THEN 13
            WHEN county = 'PALM BEACH' THEN 50
            ELSE 16 -- Default to Broward
        END as co_no,
        CASE 
            WHEN county = 'BROWARD' THEN '16'
            WHEN county = 'MIAMI-DADE' THEN '13'
            WHEN county = 'PALM BEACH' THEN '50'
            ELSE '16'
        END as county_code,
        COALESCE(year, 2025),
        NULLIF(TRIM(owner_name), ''),
        NULLIF(TRIM(phy_addr1), ''),
        NULLIF(TRIM(phy_addr2), ''),
        NULLIF(TRIM(phy_city), ''),
        COALESCE(NULLIF(TRIM(phy_state), ''), 'FL'),
        NULLIF(TRIM(phy_zipcd), ''),
        CASE WHEN just_value >= 0 THEN just_value ELSE NULL END,
        CASE WHEN assessed_value >= 0 THEN assessed_value ELSE NULL END,
        CASE WHEN assessed_value >= 0 THEN assessed_value ELSE NULL END, -- Use same value for both school/non-school
        CASE WHEN taxable_value >= 0 THEN taxable_value ELSE NULL END,
        CASE WHEN taxable_value >= 0 THEN taxable_value ELSE NULL END,
        CASE WHEN land_value >= 0 THEN land_value ELSE NULL END,
        CASE 
            WHEN property_use IS NOT NULL AND property_use != '' THEN property_use::INTEGER
            ELSE NULL
        END,
        NULL, -- property_appraiser_use_code - not available in source
        CASE 
            WHEN year_built BETWEEN 1800 AND 2030 THEN year_built
            ELSE NULL
        END,
        CASE WHEN total_living_area > 0 THEN total_living_area ELSE NULL END,
        NULL, -- land_square_footage - not available in source
        NULL, -- number_of_buildings - not available in source
        COALESCE(import_date, NOW()),
        NOW(),
        'florida_parcels_migration'
    FROM florida_parcels
    WHERE parcel_id IS NOT NULL AND TRIM(parcel_id) != ''
    ON CONFLICT (parcel_id) DO UPDATE SET
        owner_name = EXCLUDED.owner_name,
        just_value = EXCLUDED.just_value,
        updated_at = NOW();
    
    GET DIAGNOSTICS record_count = ROW_COUNT;
    migration_report := migration_report || format('  Migrated %s records to florida_properties_core' || chr(10), record_count);
    
    -- ===================================================================
    -- PHASE 2: CREATE PROPERTY_VALUATIONS RECORDS
    -- Extract valuation data from existing fields
    -- ===================================================================
    
    migration_report := migration_report || 'Phase 2: Creating property_valuations records...' || chr(10);
    
    INSERT INTO property_valuations (
        parcel_id,
        assessment_year,
        just_value,
        assessed_value_school_district,
        assessed_value_non_school_district,
        taxable_value_school_district,
        taxable_value_non_school_district,
        land_value,
        construction_value,
        created_at,
        updated_at
    )
    SELECT 
        p.parcel_id,
        COALESCE(fp.year, 2025),
        CASE WHEN fp.just_value >= 0 THEN fp.just_value ELSE NULL END,
        CASE WHEN fp.assessed_value >= 0 THEN fp.assessed_value ELSE NULL END,
        CASE WHEN fp.assessed_value >= 0 THEN fp.assessed_value ELSE NULL END,
        CASE WHEN fp.taxable_value >= 0 THEN fp.taxable_value ELSE NULL END,
        CASE WHEN fp.taxable_value >= 0 THEN fp.taxable_value ELSE NULL END,
        CASE WHEN fp.land_value >= 0 THEN fp.land_value ELSE NULL END,
        CASE WHEN fp.building_value >= 0 THEN fp.building_value ELSE NULL END,
        NOW(),
        NOW()
    FROM florida_properties_core p
    JOIN florida_parcels fp ON p.parcel_id = fp.parcel_id
    ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
        just_value = EXCLUDED.just_value,
        assessed_value_school_district = EXCLUDED.assessed_value_school_district,
        updated_at = NOW();
    
    GET DIAGNOSTICS record_count = ROW_COUNT;
    migration_report := migration_report || format('  Created %s property_valuations records' || chr(10), record_count);
    
    -- ===================================================================
    -- PHASE 3: CREATE PROPERTY_EXEMPTIONS RECORDS
    -- Initialize exemption records (will be populated with NAL import)
    -- ===================================================================
    
    migration_report := migration_report || 'Phase 3: Creating property_exemptions records...' || chr(10);
    
    INSERT INTO property_exemptions (
        parcel_id,
        assessment_year,
        has_any_exemption,
        all_exemptions,
        created_at,
        updated_at
    )
    SELECT 
        p.parcel_id,
        COALESCE(fp.year, 2025),
        false, -- Will be updated when NAL data is imported
        '{}'::jsonb,
        NOW(),
        NOW()
    FROM florida_properties_core p
    JOIN florida_parcels fp ON p.parcel_id = fp.parcel_id
    ON CONFLICT (parcel_id, assessment_year) DO NOTHING;
    
    GET DIAGNOSTICS record_count = ROW_COUNT;
    migration_report := migration_report || format('  Created %s property_exemptions records' || chr(10), record_count);
    
    -- ===================================================================
    -- PHASE 4: CREATE PROPERTY_CHARACTERISTICS RECORDS
    -- Extract building and property characteristics
    -- ===================================================================
    
    migration_report := migration_report || 'Phase 4: Creating property_characteristics records...' || chr(10);
    
    INSERT INTO property_characteristics (
        parcel_id,
        assessment_year,
        total_living_area,
        actual_year_built,
        created_at,
        updated_at
    )
    SELECT 
        p.parcel_id,
        COALESCE(fp.year, 2025),
        CASE WHEN fp.total_living_area > 0 THEN fp.total_living_area ELSE NULL END,
        CASE 
            WHEN fp.year_built BETWEEN 1800 AND 2030 THEN fp.year_built
            ELSE NULL
        END,
        NOW(),
        NOW()
    FROM florida_properties_core p
    JOIN florida_parcels fp ON p.parcel_id = fp.parcel_id
    ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
        total_living_area = EXCLUDED.total_living_area,
        actual_year_built = EXCLUDED.actual_year_built,
        updated_at = NOW();
    
    GET DIAGNOSTICS record_count = ROW_COUNT;
    migration_report := migration_report || format('  Created %s property_characteristics records' || chr(10), record_count);
    
    -- ===================================================================
    -- PHASE 5: CREATE PROPERTY_SALES_ENHANCED RECORDS
    -- Extract sales data if available
    -- ===================================================================
    
    migration_report := migration_report || 'Phase 5: Creating property_sales_enhanced records...' || chr(10);
    
    INSERT INTO property_sales_enhanced (
        parcel_id,
        assessment_year,
        sale_1_price,
        sale_1_year,
        sale_1_month,
        created_at,
        updated_at
    )
    SELECT 
        p.parcel_id,
        COALESCE(fp.year, 2025),
        CASE WHEN fp.sale_price > 0 THEN fp.sale_price ELSE NULL END,
        CASE 
            WHEN fp.sale_date IS NOT NULL THEN EXTRACT(YEAR FROM fp.sale_date)::INTEGER
            ELSE NULL
        END,
        CASE 
            WHEN fp.sale_date IS NOT NULL THEN EXTRACT(MONTH FROM fp.sale_date)::INTEGER
            ELSE NULL
        END,
        NOW(),
        NOW()
    FROM florida_properties_core p
    JOIN florida_parcels fp ON p.parcel_id = fp.parcel_id
    ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
        sale_1_price = EXCLUDED.sale_1_price,
        sale_1_year = EXCLUDED.sale_1_year,
        sale_1_month = EXCLUDED.sale_1_month,
        updated_at = NOW();
    
    GET DIAGNOSTICS record_count = ROW_COUNT;
    migration_report := migration_report || format('  Created %s property_sales_enhanced records' || chr(10), record_count);
    
    -- ===================================================================
    -- PHASE 6: CREATE PROPERTY_ADDRESSES RECORDS
    -- Extract owner and address information
    -- ===================================================================
    
    migration_report := migration_report || 'Phase 6: Creating property_addresses records...' || chr(10);
    
    INSERT INTO property_addresses (
        parcel_id,
        assessment_year,
        owner_address_1,
        owner_address_2,
        owner_city,
        owner_state,
        owner_zipcode,
        created_at,
        updated_at
    )
    SELECT 
        p.parcel_id,
        COALESCE(fp.year, 2025),
        NULLIF(TRIM(fp.owner_addr1), ''),
        NULL, -- owner_addr2 not available in source
        NULLIF(TRIM(fp.owner_city), ''),
        NULLIF(TRIM(fp.owner_state), ''),
        NULLIF(TRIM(fp.owner_zip), ''),
        NOW(),
        NOW()
    FROM florida_properties_core p
    JOIN florida_parcels fp ON p.parcel_id = fp.parcel_id
    ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
        owner_address_1 = EXCLUDED.owner_address_1,
        owner_city = EXCLUDED.owner_city,
        owner_state = EXCLUDED.owner_state,
        owner_zipcode = EXCLUDED.owner_zipcode,
        updated_at = NOW();
    
    GET DIAGNOSTICS record_count = ROW_COUNT;
    migration_report := migration_report || format('  Created %s property_addresses records' || chr(10), record_count);
    
    -- ===================================================================
    -- PHASE 7: CREATE PROPERTY_ADMIN_DATA RECORDS
    -- Initialize administrative records
    -- ===================================================================
    
    migration_report := migration_report || 'Phase 7: Creating property_admin_data records...' || chr(10);
    
    INSERT INTO property_admin_data (
        parcel_id,
        assessment_year,
        import_batch_id,
        data_quality_score,
        created_at,
        updated_at
    )
    SELECT 
        p.parcel_id,
        COALESCE(fp.year, 2025),
        'florida_parcels_migration_' || to_char(NOW(), 'YYYYMMDD_HH24MISS'),
        CASE 
            WHEN fp.owner_name IS NOT NULL 
                 AND fp.just_value IS NOT NULL 
                 AND fp.just_value > 0 
                 AND fp.parcel_id IS NOT NULL 
            THEN 0.8
            WHEN fp.parcel_id IS NOT NULL AND fp.owner_name IS NOT NULL 
            THEN 0.6
            ELSE 0.4
        END,
        NOW(),
        NOW()
    FROM florida_properties_core p
    JOIN florida_parcels fp ON p.parcel_id = fp.parcel_id
    ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
        data_quality_score = EXCLUDED.data_quality_score,
        updated_at = NOW();
    
    GET DIAGNOSTICS record_count = ROW_COUNT;
    migration_report := migration_report || format('  Created %s property_admin_data records' || chr(10), record_count);
    
    -- ===================================================================
    -- POST-MIGRATION TASKS
    -- ===================================================================
    
    -- Update statistics
    ANALYZE florida_properties_core;
    ANALYZE property_valuations;
    ANALYZE property_exemptions;
    ANALYZE property_characteristics;
    ANALYZE property_sales_enhanced;
    ANALYZE property_addresses;
    ANALYZE property_admin_data;
    
    migration_report := migration_report || 'Statistics updated for all tables' || chr(10);
    
    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW property_summary_view;
    REFRESH MATERIALIZED VIEW property_value_statistics;
    
    migration_report := migration_report || 'Materialized views refreshed' || chr(10);
    
    migration_report := migration_report || format('Migration completed at %s', NOW()::timestamp) || chr(10);
    
    RETURN migration_report;
END;
$$;

-- ===================================================================
-- NAL FIELD MAPPING FUNCTIONS
-- Functions to map the complete 165 NAL fields to normalized structure
-- ===================================================================

-- Function to parse and store NAL exemption fields as JSONB
CREATE OR REPLACE FUNCTION parse_nal_exemptions(nal_record RECORD)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    exemptions JSONB := '{}';
    field_name TEXT;
    field_value NUMERIC;
BEGIN
    -- Map all 48 exemption fields (EXMPT_01 through EXMPT_82)
    FOR i IN 1..46
    LOOP
        field_name := format('EXMPT_%02d', i);
        EXECUTE format('SELECT ($1).%I', field_name) INTO field_value USING nal_record;
        
        IF field_value IS NOT NULL AND field_value > 0 THEN
            exemptions := jsonb_set(exemptions, ARRAY[field_name], to_jsonb(field_value));
        END IF;
    END LOOP;
    
    -- Handle special exemption codes (80, 81, 82)
    FOR i IN ARRAY[80, 81, 82]
    LOOP
        field_name := format('EXMPT_%02d', i);
        EXECUTE format('SELECT ($1).%I', field_name) INTO field_value USING nal_record;
        
        IF field_value IS NOT NULL AND field_value > 0 THEN
            exemptions := jsonb_set(exemptions, ARRAY[field_name], to_jsonb(field_value));
        END IF;
    END LOOP;
    
    RETURN exemptions;
END;
$$;

-- Function to insert/update property from NAL record
CREATE OR REPLACE FUNCTION insert_nal_property_record(nal_record RECORD)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
DECLARE
    core_parcel_id VARCHAR(30);
    exemptions_jsonb JSONB;
    success BOOLEAN := TRUE;
BEGIN
    -- Extract parcel ID (clean format)
    core_parcel_id := TRIM(REGEXP_REPLACE(nal_record.PARCEL_ID::TEXT, '[^0-9]', '', 'g'));
    
    IF core_parcel_id = '' OR core_parcel_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    BEGIN
        -- ===================================================================
        -- INSERT/UPDATE FLORIDA_PROPERTIES_CORE
        -- ===================================================================
        
        INSERT INTO florida_properties_core (
            parcel_id,
            co_no,
            assessment_year,
            owner_name,
            physical_address_1,
            physical_address_2,
            physical_city,
            physical_zipcode,
            just_value,
            assessed_value_school_district,
            assessed_value_non_school_district,
            taxable_value_school_district,
            taxable_value_non_school_district,
            land_value,
            dor_use_code,
            property_appraiser_use_code,
            neighborhood_code,
            year_built,
            effective_year_built,
            total_living_area,
            land_square_footage,
            number_of_buildings,
            source
        ) VALUES (
            core_parcel_id,
            COALESCE(nal_record.CO_NO, 16),
            COALESCE(nal_record.ASMNT_YR, 2025),
            NULLIF(TRIM(nal_record.OWN_NAME), ''),
            NULLIF(TRIM(nal_record.PHY_ADDR1), ''),
            NULLIF(TRIM(nal_record.PHY_ADDR2), ''),
            NULLIF(TRIM(nal_record.PHY_CITY), ''),
            NULLIF(TRIM(nal_record.PHY_ZIPCD), ''),
            CASE WHEN nal_record.JV >= 0 THEN nal_record.JV ELSE NULL END,
            CASE WHEN nal_record.AV_SD >= 0 THEN nal_record.AV_SD ELSE NULL END,
            CASE WHEN nal_record.AV_NSD >= 0 THEN nal_record.AV_NSD ELSE NULL END,
            CASE WHEN nal_record.TV_SD >= 0 THEN nal_record.TV_SD ELSE NULL END,
            CASE WHEN nal_record.TV_NSD >= 0 THEN nal_record.TV_NSD ELSE NULL END,
            CASE WHEN nal_record.LND_VAL >= 0 THEN nal_record.LND_VAL ELSE NULL END,
            nal_record.DOR_UC,
            nal_record.PA_UC,
            nal_record.NBRHD_CD,
            CASE WHEN nal_record.ACT_YR_BLT BETWEEN 1800 AND 2030 THEN nal_record.ACT_YR_BLT ELSE NULL END,
            CASE WHEN nal_record.EFF_YR_BLT BETWEEN 1800 AND 2030 THEN nal_record.EFF_YR_BLT ELSE NULL END,
            CASE WHEN nal_record.TOT_LVG_AREA > 0 THEN nal_record.TOT_LVG_AREA ELSE NULL END,
            CASE WHEN nal_record.LND_SQFOOT > 0 THEN nal_record.LND_SQFOOT ELSE NULL END,
            CASE WHEN nal_record.NO_BULDNG > 0 THEN nal_record.NO_BULDNG ELSE NULL END,
            'florida_nal'
        )
        ON CONFLICT (parcel_id) DO UPDATE SET
            owner_name = EXCLUDED.owner_name,
            physical_address_1 = EXCLUDED.physical_address_1,
            physical_city = EXCLUDED.physical_city,
            just_value = EXCLUDED.just_value,
            assessed_value_school_district = EXCLUDED.assessed_value_school_district,
            updated_at = NOW();
        
        -- ===================================================================
        -- INSERT/UPDATE PROPERTY_VALUATIONS
        -- ===================================================================
        
        INSERT INTO property_valuations (
            parcel_id,
            assessment_year,
            just_value,
            just_value_change_flag,
            just_value_change_code,
            assessed_value_school_district,
            assessed_value_non_school_district,
            taxable_value_school_district,
            taxable_value_non_school_district,
            just_value_homestead,
            assessed_value_homestead,
            just_value_non_homestead_residential,
            assessed_value_non_homestead_residential,
            just_value_residential_non_residential,
            assessed_value_residential_non_residential,
            just_value_class_use,
            assessed_value_class_use,
            land_value,
            construction_value,
            deleted_value,
            special_features_value
        ) VALUES (
            core_parcel_id,
            COALESCE(nal_record.ASMNT_YR, 2025),
            nal_record.JV,
            nal_record.JV_CHNG,
            nal_record.JV_CHNG_CD,
            nal_record.AV_SD,
            nal_record.AV_NSD,
            nal_record.TV_SD,
            nal_record.TV_NSD,
            nal_record.JV_HMSTD,
            nal_record.AV_HMSTD,
            nal_record.JV_NON_HMSTD_RESD,
            nal_record.AV_NON_HMSTD_RESD,
            nal_record.JV_RESD_NON_RESD,
            nal_record.AV_RESD_NON_RESD,
            nal_record.JV_CLASS_USE,
            nal_record.AV_CLASS_USE,
            nal_record.LND_VAL,
            nal_record.NCONST_VAL,
            nal_record.DEL_VAL,
            nal_record.SPEC_FEAT_VAL
        )
        ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
            just_value = EXCLUDED.just_value,
            assessed_value_school_district = EXCLUDED.assessed_value_school_district,
            updated_at = NOW();
        
        -- ===================================================================
        -- INSERT/UPDATE PROPERTY_EXEMPTIONS
        -- ===================================================================
        
        exemptions_jsonb := parse_nal_exemptions(nal_record);
        
        INSERT INTO property_exemptions (
            parcel_id,
            assessment_year,
            homestead_exemption,
            all_exemptions,
            has_homestead,
            has_any_exemption,
            total_exemption_amount,
            previous_homestead_owner,
            previous_homestead_parcel_id
        ) VALUES (
            core_parcel_id,
            COALESCE(nal_record.ASMNT_YR, 2025),
            CASE WHEN nal_record.EXMPT_05 > 0 THEN nal_record.EXMPT_05 ELSE NULL END,
            exemptions_jsonb,
            COALESCE(nal_record.EXMPT_05 > 0, false),
            jsonb_object_keys_count(exemptions_jsonb) > 0,
            (SELECT SUM(value::numeric) FROM jsonb_each_text(exemptions_jsonb)),
            nal_record.PREV_HMSTD_OWN,
            nal_record.PARCEL_ID_PRV_HMSTD
        )
        ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
            homestead_exemption = EXCLUDED.homestead_exemption,
            all_exemptions = EXCLUDED.all_exemptions,
            has_homestead = EXCLUDED.has_homestead,
            has_any_exemption = EXCLUDED.has_any_exemption,
            total_exemption_amount = EXCLUDED.total_exemption_amount,
            updated_at = NOW();
        
        -- ===================================================================
        -- INSERT/UPDATE PROPERTY_CHARACTERISTICS
        -- ===================================================================
        
        INSERT INTO property_characteristics (
            parcel_id,
            assessment_year,
            number_of_buildings,
            number_of_residential_units,
            total_living_area,
            improvement_quality,
            construction_class,
            actual_year_built,
            effective_year_built,
            land_square_footage,
            land_units_code,
            number_of_land_units,
            public_land_code,
            short_legal_description,
            market_area,
            township,
            range_section,
            section_number,
            census_block,
            date_last_inspection,
            state_parcel_id,
            real_personal_status_id,
            multiple_parcel_id
        ) VALUES (
            core_parcel_id,
            COALESCE(nal_record.ASMNT_YR, 2025),
            nal_record.NO_BULDNG,
            nal_record.NO_RES_UNTS,
            nal_record.TOT_LVG_AREA,
            nal_record.IMP_QUAL,
            nal_record.CONST_CLASS,
            CASE WHEN nal_record.ACT_YR_BLT BETWEEN 1800 AND 2030 THEN nal_record.ACT_YR_BLT ELSE NULL END,
            CASE WHEN nal_record.EFF_YR_BLT BETWEEN 1800 AND 2030 THEN nal_record.EFF_YR_BLT ELSE NULL END,
            nal_record.LND_SQFOOT,
            nal_record.LND_UNTS_CD,
            nal_record.NO_LND_UNTS,
            nal_record.PUBLIC_LND,
            nal_record.S_LEGAL,
            nal_record.MKT_AR,
            nal_record.TWN,
            nal_record.RNG,
            nal_record.SEC,
            nal_record.CENSUS_BK,
            nal_record.DT_LAST_INSPT,
            nal_record.STATE_PAR_ID,
            nal_record.RS_ID,
            nal_record.MP_ID
        )
        ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
            actual_year_built = EXCLUDED.actual_year_built,
            total_living_area = EXCLUDED.total_living_area,
            land_square_footage = EXCLUDED.land_square_footage,
            updated_at = NOW();
        
        -- ===================================================================
        -- INSERT/UPDATE PROPERTY_SALES_ENHANCED
        -- ===================================================================
        
        INSERT INTO property_sales_enhanced (
            parcel_id,
            assessment_year,
            sale_1_is_multi_parcel,
            sale_1_qualification_code,
            sale_1_validity_code,
            sale_1_price,
            sale_1_year,
            sale_1_month,
            sale_1_or_book,
            sale_1_or_page,
            sale_1_clerk_number,
            sale_1_change_code,
            sale_2_is_multi_parcel,
            sale_2_qualification_code,
            sale_2_validity_code,
            sale_2_price,
            sale_2_year,
            sale_2_month,
            sale_2_or_book,
            sale_2_or_page,
            sale_2_clerk_number,
            sale_2_change_code
        ) VALUES (
            core_parcel_id,
            COALESCE(nal_record.ASMNT_YR, 2025),
            nal_record.MULTI_PAR_SAL1,
            nal_record.QUAL_CD1,
            nal_record.VI_CD1,
            nal_record.SALE_PRC1,
            nal_record.SALE_YR1,
            nal_record.SALE_MO1,
            nal_record.OR_BOOK1,
            nal_record.OR_PAGE1,
            nal_record.CLERK_NO1,
            nal_record.SAL_CHNG_CD1,
            nal_record.MULTI_PAR_SAL2,
            nal_record.QUAL_CD2,
            nal_record.VI_CD2,
            nal_record.SALE_PRC2,
            nal_record.SALE_YR2,
            nal_record.SALE_MO2,
            nal_record.OR_BOOK2,
            nal_record.OR_PAGE2,
            nal_record.CLERK_NO2,
            nal_record.SAL_CHNG_CD2
        )
        ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
            sale_1_price = EXCLUDED.sale_1_price,
            sale_1_year = EXCLUDED.sale_1_year,
            sale_1_month = EXCLUDED.sale_1_month,
            updated_at = NOW();
        
        -- ===================================================================
        -- INSERT/UPDATE PROPERTY_ADDRESSES
        -- ===================================================================
        
        INSERT INTO property_addresses (
            parcel_id,
            assessment_year,
            owner_address_1,
            owner_address_2,
            owner_city,
            owner_state,
            owner_zipcode,
            owner_state_domicile,
            fiduciary_code,
            fiduciary_name,
            fiduciary_address_1,
            fiduciary_address_2,
            fiduciary_city,
            fiduciary_state,
            fiduciary_zipcode,
            fiduciary_state_domicile,
            previous_owner_name,
            vacancy_indicator
        ) VALUES (
            core_parcel_id,
            COALESCE(nal_record.ASMNT_YR, 2025),
            NULLIF(TRIM(nal_record.OWN_ADDR1), ''),
            NULLIF(TRIM(nal_record.OWN_ADDR2), ''),
            NULLIF(TRIM(nal_record.OWN_CITY), ''),
            NULLIF(TRIM(nal_record.OWN_STATE), ''),
            NULLIF(TRIM(nal_record.OWN_ZIPCD), ''),
            NULLIF(TRIM(nal_record.OWN_STATE_DOM), ''),
            nal_record.FIDU_CD,
            NULLIF(TRIM(nal_record.FIDU_NAME), ''),
            NULLIF(TRIM(nal_record.FIDU_ADDR1), ''),
            NULLIF(TRIM(nal_record.FIDU_ADDR2), ''),
            NULLIF(TRIM(nal_record.FIDU_CITY), ''),
            NULLIF(TRIM(nal_record.FIDU_STATE), ''),
            NULLIF(TRIM(nal_record.FIDU_ZIPCD), ''),
            NULLIF(TRIM(nal_record.FIDU_STATE_DOM), ''),
            NULLIF(TRIM(nal_record.OWNER_PREV), ''),
            nal_record.VI_CD1
        )
        ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
            owner_address_1 = EXCLUDED.owner_address_1,
            owner_city = EXCLUDED.owner_city,
            owner_state = EXCLUDED.owner_state,
            owner_zipcode = EXCLUDED.owner_zipcode,
            updated_at = NOW();
        
        -- ===================================================================
        -- INSERT/UPDATE PROPERTY_ADMIN_DATA
        -- ===================================================================
        
        INSERT INTO property_admin_data (
            parcel_id,
            assessment_year,
            base_strata,
            active_strata,
            group_number,
            sequence_number,
            parcel_split,
            special_assessment_pass_code,
            class_use_code,
            taxing_district,
            tax_authority_code,
            land_units_code,
            assessment_transfer_flag,
            assessment_difference_transfer,
            import_batch_id,
            data_quality_score
        ) VALUES (
            core_parcel_id,
            COALESCE(nal_record.ASMNT_YR, 2025),
            nal_record.BAS_STRT,
            nal_record.ATV_STRT,
            nal_record.GRP_NO,
            nal_record.SEQ_NO,
            nal_record.PAR_SPLT,
            nal_record.SPASS_CD,
            nal_record.CLASS_USE_CD,
            nal_record.TAXING_DIST,
            nal_record.TAX_AUTH_CD,
            nal_record.LND_UNTS_CD,
            nal_record.ASS_TRNSFR_FG,
            nal_record.ASS_DIF_TRNS,
            'nal_import_' || to_char(NOW(), 'YYYYMMDD_HH24MISS'),
            CASE 
                WHEN nal_record.OWN_NAME IS NOT NULL 
                     AND nal_record.JV > 0 
                     AND nal_record.PHY_ADDR1 IS NOT NULL 
                THEN 0.95
                WHEN nal_record.OWN_NAME IS NOT NULL AND nal_record.JV > 0 
                THEN 0.85
                ELSE 0.70
            END
        )
        ON CONFLICT (parcel_id, assessment_year) DO UPDATE SET
            data_quality_score = EXCLUDED.data_quality_score,
            updated_at = NOW();
        
    EXCEPTION WHEN OTHERS THEN
        RAISE WARNING 'Error inserting NAL record for parcel %: %', core_parcel_id, SQLERRM;
        success := FALSE;
    END;
    
    RETURN success;
END;
$$;

-- ===================================================================
-- VALIDATION FUNCTIONS
-- ===================================================================

-- Function to validate migration results
CREATE OR REPLACE FUNCTION validate_migration_results()
RETURNS TABLE (
    validation_check TEXT,
    source_count BIGINT,
    target_count BIGINT,
    status TEXT,
    details TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check core properties migration
    RETURN QUERY
    SELECT 
        'Core Properties Migration' as validation_check,
        (SELECT COUNT(*) FROM florida_parcels WHERE parcel_id IS NOT NULL) as source_count,
        (SELECT COUNT(*) FROM florida_properties_core) as target_count,
        CASE 
            WHEN (SELECT COUNT(*) FROM florida_properties_core) >= (SELECT COUNT(*) FROM florida_parcels WHERE parcel_id IS NOT NULL) * 0.95
            THEN 'PASS' 
            ELSE 'FAIL' 
        END as status,
        'Migration of core property records' as details;
    
    -- Check valuation records
    RETURN QUERY
    SELECT 
        'Valuation Records' as validation_check,
        (SELECT COUNT(*) FROM florida_parcels WHERE just_value IS NOT NULL) as source_count,
        (SELECT COUNT(*) FROM property_valuations WHERE just_value IS NOT NULL) as target_count,
        CASE 
            WHEN (SELECT COUNT(*) FROM property_valuations WHERE just_value IS NOT NULL) >= (SELECT COUNT(*) FROM florida_parcels WHERE just_value IS NOT NULL) * 0.90
            THEN 'PASS' 
            ELSE 'WARN' 
        END as status,
        'Migration of valuation data' as details;
    
    -- Check data consistency
    RETURN QUERY
    SELECT 
        'Data Consistency' as validation_check,
        0::BIGINT as source_count,
        (SELECT COUNT(*) FROM florida_properties_core p 
         LEFT JOIN property_valuations v ON p.parcel_id = v.parcel_id 
         WHERE v.parcel_id IS NULL) as target_count,
        CASE 
            WHEN (SELECT COUNT(*) FROM florida_properties_core p 
                  LEFT JOIN property_valuations v ON p.parcel_id = v.parcel_id 
                  WHERE v.parcel_id IS NULL) = 0
            THEN 'PASS' 
            ELSE 'WARN' 
        END as status,
        'Properties missing valuation records' as details;
END;
$$;

-- ===================================================================
-- ROLLBACK FUNCTION
-- ===================================================================

-- Function to rollback migration if needed
CREATE OR REPLACE FUNCTION rollback_migration()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    rollback_report TEXT := '';
BEGIN
    -- Drop all new tables
    DROP TABLE IF EXISTS property_admin_data CASCADE;
    DROP TABLE IF EXISTS property_addresses CASCADE;
    DROP TABLE IF EXISTS property_sales_enhanced CASCADE;
    DROP TABLE IF EXISTS property_characteristics CASCADE;
    DROP TABLE IF EXISTS property_exemptions CASCADE;
    DROP TABLE IF EXISTS property_valuations CASCADE;
    DROP TABLE IF EXISTS florida_properties_core CASCADE;
    
    -- Drop materialized views
    DROP MATERIALIZED VIEW IF EXISTS property_summary_view;
    DROP MATERIALIZED VIEW IF EXISTS property_value_statistics;
    
    rollback_report := 'All normalized tables and views dropped' || chr(10);
    
    -- Restore original table if backup exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'florida_parcels_backup_migration') THEN
        DROP TABLE IF EXISTS florida_parcels;
        ALTER TABLE florida_parcels_backup_migration RENAME TO florida_parcels;
        rollback_report := rollback_report || 'Original florida_parcels table restored from backup' || chr(10);
    END IF;
    
    rollback_report := rollback_report || 'Migration rollback completed at ' || NOW()::timestamp;
    
    RETURN rollback_report;
END;
$$;

-- ===================================================================
-- MIGRATION EXECUTION COMMANDS
-- ===================================================================

-- Execute the migration (uncomment to run)
/*
DO $$
DECLARE
    migration_result TEXT;
    validation_results RECORD;
BEGIN
    -- Run the migration
    SELECT migrate_nal_data_to_normalized() INTO migration_result;
    RAISE NOTICE '%', migration_result;
    
    -- Validate results
    RAISE NOTICE 'VALIDATION RESULTS:';
    FOR validation_results IN SELECT * FROM validate_migration_results()
    LOOP
        RAISE NOTICE '% | Source: % | Target: % | Status: % | %', 
            validation_results.validation_check,
            validation_results.source_count,
            validation_results.target_count,
            validation_results.status,
            validation_results.details;
    END LOOP;
END $$;
*/

-- ===================================================================
-- FINAL COMMENTS
-- ===================================================================

COMMENT ON FUNCTION migrate_nal_data_to_normalized() IS 'Migrates existing florida_parcels data to normalized 7-table structure';
COMMENT ON FUNCTION parse_nal_exemptions(RECORD) IS 'Parses NAL exemption fields into JSONB format';
COMMENT ON FUNCTION insert_nal_property_record(RECORD) IS 'Inserts/updates property from complete NAL record with all 165 fields';
COMMENT ON FUNCTION validate_migration_results() IS 'Validates migration results and data integrity';
COMMENT ON FUNCTION rollback_migration() IS 'Rollback migration and restore original structure';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'NAL DATA MIGRATION SCRIPT READY';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Migration functions created and ready for execution';
    RAISE NOTICE 'Backup table will be created: florida_parcels_backup_migration';
    RAISE NOTICE 'To execute migration, uncomment the DO block at the end';
    RAISE NOTICE 'Rollback function available if needed';
    RAISE NOTICE '=================================================================';
END $$;