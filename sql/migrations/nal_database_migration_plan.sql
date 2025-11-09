-- =====================================================================
-- NAL DATABASE MIGRATION PLAN
-- =====================================================================
-- Migration from current 51-field florida_parcels table to optimized 
-- normalized structure with all 165 NAL fields
-- =====================================================================

-- =====================================================================
-- PHASE 1: BACKUP AND PREPARATION
-- =====================================================================

-- Create backup of existing data
CREATE TABLE florida_parcels_backup_pre_migration AS 
SELECT * FROM florida_parcels;

-- Create staging table for NAL data validation
CREATE TABLE nal_staging_data (
    parcel_id VARCHAR(30),
    raw_data JSONB,
    validation_status VARCHAR(20),
    error_messages TEXT[],
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- PHASE 2: DATA MAPPING FROM CURRENT STRUCTURE
-- =====================================================================

-- Mapping function to migrate existing data to new structure
CREATE OR REPLACE FUNCTION migrate_existing_property_data()
RETURNS INTEGER AS $$
DECLARE
    migration_count INTEGER := 0;
    rec RECORD;
BEGIN
    -- Insert data into florida_properties_core from existing table
    INSERT INTO florida_properties_core (
        parcel_id,
        county_code,
        county_name, 
        assessment_year,
        file_type,
        
        -- Location mapping
        physical_address_1,
        physical_city,
        physical_state,
        physical_zipcode,
        
        -- Owner mapping
        owner_name,
        owner_address_1,
        owner_city,
        owner_state,
        owner_zipcode,
        
        -- Property characteristics
        dor_use_code,
        property_appraiser_use_code,
        
        -- Valuations
        just_value,
        assessed_value_school_district,
        taxable_value_school_district,
        land_value,
        
        -- Building info
        year_built,
        total_living_area,
        
        -- Metadata
        data_source
    )
    SELECT 
        parcel_id,
        county,
        CASE 
            WHEN county = '12' THEN 'Broward'
            ELSE 'Unknown'
        END as county_name,
        COALESCE(year, 2025) as assessment_year,
        'R' as file_type, -- Default for residential
        
        -- Map location fields
        phy_addr1,
        phy_city,
        COALESCE(phy_state, 'FL'),
        phy_zipcd,
        
        -- Map owner fields  
        owner_name,
        owner_addr1,
        owner_city,
        owner_state,
        owner_zip,
        
        -- Map property codes (if available)
        property_use,
        property_use,
        
        -- Map valuations
        COALESCE(just_value, 0),
        COALESCE(assessed_value, 0),
        COALESCE(taxable_value, 0),
        COALESCE(land_value, 0),
        
        -- Map building data
        year_built,
        total_living_area,
        
        'migration' as data_source
    FROM florida_parcels
    WHERE parcel_id IS NOT NULL
    ON CONFLICT (parcel_id) DO NOTHING;
    
    GET DIAGNOSTICS migration_count = ROW_COUNT;
    
    -- Insert basic exemption data if available
    INSERT INTO property_exemptions (
        parcel_id,
        has_homestead,
        total_exemption_amount,
        all_exemptions
    )
    SELECT 
        parcel_id,
        false as has_homestead, -- Will be updated with NAL data
        0 as total_exemption_amount,
        '{}' as all_exemptions
    FROM florida_parcels
    WHERE parcel_id IS NOT NULL
    ON CONFLICT DO NOTHING;
    
    -- Insert basic sales data if available
    INSERT INTO property_sales_enhanced (
        parcel_id,
        latest_sale_date,
        latest_sale_price
    )
    SELECT 
        parcel_id,
        sale_date,
        sale_price
    FROM florida_parcels
    WHERE parcel_id IS NOT NULL 
      AND sale_date IS NOT NULL
    ON CONFLICT DO NOTHING;
    
    RETURN migration_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- PHASE 3: NAL DATA IMPORT MAPPING
-- =====================================================================

-- Complete field mapping for NAL import
CREATE OR REPLACE FUNCTION import_nal_data_batch(nal_records JSONB)
RETURNS TABLE(
    processed_count INTEGER,
    error_count INTEGER,
    warning_count INTEGER
) AS $$
DECLARE
    record JSONB;
    processed_count INTEGER := 0;
    error_count INTEGER := 0;
    warning_count INTEGER := 0;
BEGIN
    -- Process each NAL record
    FOR record IN SELECT jsonb_array_elements(nal_records)
    LOOP
        BEGIN
            -- Insert into core properties table
            INSERT INTO florida_properties_core (
                parcel_id,
                county_code,
                county_name,
                assessment_year,
                file_type,
                group_number,
                
                -- Physical location
                physical_address_1,
                physical_address_2,
                physical_city,
                physical_state,
                physical_zipcode,
                
                -- Owner information
                owner_name,
                owner_address_1,
                owner_city,
                owner_state,
                owner_zipcode,
                
                -- Property classification
                dor_use_code,
                property_appraiser_use_code,
                neighborhood_code,
                tax_authority_code,
                
                -- Core valuations
                just_value,
                assessed_value_school_district,
                taxable_value_school_district,
                land_value,
                
                -- Building basics
                year_built,
                total_living_area,
                number_of_buildings,
                land_square_footage,
                
                data_source
            )
            VALUES (
                (record->>'PARCEL_ID')::VARCHAR(30),
                (record->>'CO_NO')::VARCHAR(3),
                'Broward',
                (record->>'ASMNT_YR')::INTEGER,
                (record->>'FILE_T')::VARCHAR(5),
                (record->>'GRP_NO')::INTEGER,
                
                (record->>'PHY_ADDR1')::VARCHAR(60),
                (record->>'PHY_ADDR2')::VARCHAR(60),
                (record->>'PHY_CITY')::VARCHAR(45),
                COALESCE((record->>'PHY_STATE')::VARCHAR(2), 'FL'),
                (record->>'PHY_ZIPCD')::VARCHAR(10),
                
                (record->>'OWN_NAME')::VARCHAR(70),
                (record->>'OWN_ADDR1')::VARCHAR(60),
                (record->>'OWN_CITY')::VARCHAR(45),
                (record->>'OWN_STATE')::VARCHAR(50),
                (record->>'OWN_ZIPCD')::VARCHAR(10),
                
                (record->>'DOR_UC')::VARCHAR(3),
                (record->>'PA_UC')::VARCHAR(3),
                (record->>'NBRHD_CD')::VARCHAR(10),
                (record->>'TAX_AUTH_CD')::VARCHAR(3),
                
                COALESCE((record->>'JV')::NUMERIC(12,2), 0),
                COALESCE((record->>'AV_SD')::NUMERIC(12,2), 0),
                COALESCE((record->>'TV_SD')::NUMERIC(12,2), 0),
                COALESCE((record->>'LND_VAL')::NUMERIC(12,2), 0),
                
                (record->>'ACT_YR_BLT')::INTEGER,
                (record->>'TOT_LVG_AREA')::NUMERIC(8,2),
                COALESCE((record->>'NO_BULDNG')::INTEGER, 0),
                (record->>'LND_SQFOOT')::NUMERIC(12,0),
                
                'nal'
            )
            ON CONFLICT (parcel_id) DO UPDATE SET
                county_code = EXCLUDED.county_code,
                assessment_year = EXCLUDED.assessment_year,
                physical_address_1 = EXCLUDED.physical_address_1,
                physical_city = EXCLUDED.physical_city,
                physical_zipcode = EXCLUDED.physical_zipcode,
                owner_name = EXCLUDED.owner_name,
                dor_use_code = EXCLUDED.dor_use_code,
                just_value = EXCLUDED.just_value,
                assessed_value_school_district = EXCLUDED.assessed_value_school_district,
                taxable_value_school_district = EXCLUDED.taxable_value_school_district,
                land_value = EXCLUDED.land_value,
                year_built = EXCLUDED.year_built,
                total_living_area = EXCLUDED.total_living_area,
                updated_at = NOW();
            
            -- Insert detailed valuations
            INSERT INTO property_valuations (
                parcel_id,
                assessed_value_non_school_district,
                taxable_value_non_school_district,
                just_value_non_homestead_residential,
                assessed_value_non_homestead_residential,
                just_value_residential_non_residential,
                assessed_value_residential_non_residential,
                new_construction_value,
                deleted_value,
                special_features_value,
                just_value_change_flag,
                just_value_change_code
            )
            VALUES (
                (record->>'PARCEL_ID')::VARCHAR(30),
                COALESCE((record->>'AV_NSD')::NUMERIC(12,2), 0),
                COALESCE((record->>'TV_NSD')::NUMERIC(12,2), 0),
                (record->>'JV_NON_HMSTD_RESD')::NUMERIC(12,2),
                (record->>'AV_NON_HMSTD_RESD')::NUMERIC(12,2),
                (record->>'JV_RESD_NON_RESD')::NUMERIC(12,2),
                (record->>'AV_RESD_NON_RESD')::NUMERIC(12,2),
                COALESCE((record->>'NCONST_VAL')::NUMERIC(12,2), 0),
                COALESCE((record->>'DEL_VAL')::NUMERIC(12,2), 0),
                COALESCE((record->>'SPEC_FEAT_VAL')::NUMERIC(12,2), 0),
                (record->>'JV_CHNG')::VARCHAR(1),
                (record->>'JV_CHNG_CD')::VARCHAR(3)
            )
            ON CONFLICT (parcel_id) DO UPDATE SET
                assessed_value_non_school_district = EXCLUDED.assessed_value_non_school_district,
                taxable_value_non_school_district = EXCLUDED.taxable_value_non_school_district,
                updated_at = NOW();
            
            -- Process exemptions into JSONB structure
            INSERT INTO property_exemptions (
                parcel_id,
                previous_homestead_owner,
                all_exemptions,
                total_exemption_amount,
                active_exemption_count,
                has_homestead
            )
            SELECT 
                (record->>'PARCEL_ID')::VARCHAR(30),
                (record->>'PREV_HMSTD_OWN')::VARCHAR(1),
                exemption_json,
                total_amount,
                active_count,
                has_homestead_exemption
            FROM (
                SELECT 
                    jsonb_object_agg(
                        exemption_field, 
                        exemption_value
                    ) FILTER (WHERE exemption_value IS NOT NULL AND exemption_value != '0') as exemption_json,
                    COALESCE(SUM(exemption_value::NUMERIC), 0) as total_amount,
                    COUNT(*) FILTER (WHERE exemption_value IS NOT NULL AND exemption_value != '0') as active_count,
                    CASE WHEN EXISTS(
                        SELECT 1 FROM jsonb_each_text(record) 
                        WHERE key LIKE 'EXMPT_0%' AND value::NUMERIC > 0
                    ) THEN true ELSE false END as has_homestead_exemption
                FROM (
                    SELECT 
                        key as exemption_field,
                        CASE 
                            WHEN value = '' OR value = '0' OR value IS NULL THEN NULL 
                            ELSE value 
                        END as exemption_value
                    FROM jsonb_each_text(record)
                    WHERE key LIKE 'EXMPT_%'
                ) exemptions
            ) exemption_summary
            ON CONFLICT (parcel_id) DO UPDATE SET
                all_exemptions = EXCLUDED.all_exemptions,
                total_exemption_amount = EXCLUDED.total_exemption_amount,
                active_exemption_count = EXCLUDED.active_exemption_count,
                has_homestead = EXCLUDED.has_homestead,
                updated_at = NOW();
            
            -- Insert property characteristics
            INSERT INTO property_characteristics (
                parcel_id,
                effective_year_built,
                actual_year_built,
                improvement_quality,
                construction_class,
                number_residential_units,
                land_units_code,
                land_units_count,
                public_land_indicator,
                quality_code_1,
                vacancy_indicator_1,
                quality_code_2,
                vacancy_indicator_2,
                short_legal_description,
                market_area,
                township,
                range_info,
                section_info,
                census_block
            )
            VALUES (
                (record->>'PARCEL_ID')::VARCHAR(30),
                (record->>'EFF_YR_BLT')::INTEGER,
                (record->>'ACT_YR_BLT')::INTEGER,
                (record->>'IMP_QUAL')::INTEGER,
                (record->>'CONST_CLASS')::INTEGER,
                (record->>'NO_RES_UNTS')::INTEGER,
                (record->>'LND_UNTS_CD')::VARCHAR(3),
                (record->>'NO_LND_UNTS')::NUMERIC(12,0),
                (record->>'PUBLIC_LND')::VARCHAR(1),
                (record->>'QUAL_CD1')::INTEGER,
                (record->>'VI_CD1')::VARCHAR(1),
                (record->>'QUAL_CD2')::INTEGER,
                (record->>'VI_CD2')::VARCHAR(1),
                (record->>'S_LEGAL')::VARCHAR(50),
                (record->>'MKT_AR')::VARCHAR(5),
                (record->>'TWN')::VARCHAR(10),
                (record->>'RNG')::VARCHAR(10),
                (record->>'SEC')::VARCHAR(10),
                (record->>'CENSUS_BK')::VARCHAR(15)
            )
            ON CONFLICT (parcel_id) DO UPDATE SET
                actual_year_built = EXCLUDED.actual_year_built,
                improvement_quality = EXCLUDED.improvement_quality,
                land_units_count = EXCLUDED.land_units_count,
                updated_at = NOW();
            
            -- Insert sales history
            INSERT INTO property_sales_enhanced (
                parcel_id,
                multiple_parcel_sale_1,
                sale_price_1,
                sale_year_1,
                sale_month_1,
                clerk_number_1,
                multiple_parcel_sale_2,
                sale_price_2,
                sale_year_2,
                sale_month_2,
                clerk_number_2,
                latest_sale_date,
                latest_sale_price
            )
            VALUES (
                (record->>'PARCEL_ID')::VARCHAR(30),
                (record->>'MULTI_PAR_SAL1')::VARCHAR(1),
                (record->>'SALE_PRC1')::NUMERIC(12,2),
                (record->>'SALE_YR1')::INTEGER,
                (record->>'SALE_MO1')::INTEGER,
                (record->>'CLERK_NO1')::NUMERIC(15,0),
                (record->>'MULTI_PAR_SAL2')::VARCHAR(1),
                (record->>'SALE_PRC2')::NUMERIC(12,2),
                (record->>'SALE_YR2')::INTEGER,
                (record->>'SALE_MO2')::INTEGER,
                (record->>'CLERK_NO2')::NUMERIC(15,0),
                -- Calculate latest sale date
                CASE 
                    WHEN (record->>'SALE_YR1')::INTEGER > (record->>'SALE_YR2')::INTEGER 
                    THEN make_date(
                        (record->>'SALE_YR1')::INTEGER, 
                        COALESCE((record->>'SALE_MO1')::INTEGER, 1), 
                        1
                    )
                    ELSE make_date(
                        COALESCE((record->>'SALE_YR2')::INTEGER, 1900), 
                        COALESCE((record->>'SALE_MO2')::INTEGER, 1), 
                        1
                    )
                END,
                -- Calculate latest sale price
                CASE 
                    WHEN (record->>'SALE_YR1')::INTEGER > (record->>'SALE_YR2')::INTEGER 
                    THEN (record->>'SALE_PRC1')::NUMERIC(12,2)
                    ELSE (record->>'SALE_PRC2')::NUMERIC(12,2)
                END
            )
            ON CONFLICT (parcel_id) DO UPDATE SET
                sale_price_1 = EXCLUDED.sale_price_1,
                sale_year_1 = EXCLUDED.sale_year_1,
                latest_sale_date = EXCLUDED.latest_sale_date,
                latest_sale_price = EXCLUDED.latest_sale_price,
                updated_at = NOW();
            
            -- Insert administrative data
            INSERT INTO property_admin_data (
                parcel_id,
                appraisal_status,
                sequence_number,
                real_personal_status_id,
                multiple_parcel_id,
                state_parcel_id,
                last_inspection_date,
                parcel_split,
                base_start,
                active_value_start
            )
            VALUES (
                (record->>'PARCEL_ID')::VARCHAR(30),
                (record->>'APP_STAT')::VARCHAR(3),
                (record->>'SEQ_NO')::INTEGER,
                (record->>'RS_ID')::VARCHAR(10),
                (record->>'MP_ID')::VARCHAR(10),
                (record->>'STATE_PAR_ID')::VARCHAR(25),
                (record->>'DT_LAST_INSPT')::VARCHAR(10),
                (record->>'PAR_SPLT')::NUMERIC(10,0),
                (record->>'BAS_STRT')::INTEGER,
                (record->>'ATV_STRT')::INTEGER
            )
            ON CONFLICT (parcel_id) DO UPDATE SET
                appraisal_status = EXCLUDED.appraisal_status,
                state_parcel_id = EXCLUDED.state_parcel_id,
                updated_at = NOW();
            
            processed_count := processed_count + 1;
            
        EXCEPTION WHEN OTHERS THEN
            error_count := error_count + 1;
            -- Log the error
            INSERT INTO nal_staging_data (parcel_id, raw_data, validation_status, error_messages)
            VALUES (
                (record->>'PARCEL_ID')::VARCHAR(30),
                record,
                'error',
                ARRAY[SQLERRM]
            );
        END;
    END LOOP;
    
    RETURN QUERY SELECT processed_count, error_count, warning_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- PHASE 4: DATA VALIDATION AND CLEANUP
-- =====================================================================

-- Validation function to check data integrity
CREATE OR REPLACE FUNCTION validate_migrated_data()
RETURNS TABLE(
    table_name TEXT,
    record_count BIGINT,
    validation_status TEXT,
    issues TEXT[]
) AS $$
BEGIN
    -- Validate core properties
    RETURN QUERY
    SELECT 
        'florida_properties_core'::TEXT,
        COUNT(*)::BIGINT,
        CASE 
            WHEN COUNT(*) > 0 THEN 'SUCCESS'
            ELSE 'ERROR'
        END::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN ARRAY['No records found']
            ELSE ARRAY[]::TEXT[]
        END
    FROM florida_properties_core;
    
    -- Validate valuations
    RETURN QUERY
    SELECT 
        'property_valuations'::TEXT,
        COUNT(*)::BIGINT,
        CASE 
            WHEN COUNT(*) > 0 AND COUNT(*) = (SELECT COUNT(*) FROM florida_properties_core) 
            THEN 'SUCCESS'
            ELSE 'WARNING'
        END::TEXT,
        CASE 
            WHEN COUNT(*) = 0 THEN ARRAY['No valuation records']
            WHEN COUNT(*) < (SELECT COUNT(*) FROM florida_properties_core) 
            THEN ARRAY['Missing valuation records for some properties']
            ELSE ARRAY[]::TEXT[]
        END
    FROM property_valuations;
    
    -- Validate exemptions
    RETURN QUERY
    SELECT 
        'property_exemptions'::TEXT,
        COUNT(*)::BIGINT,
        'SUCCESS'::TEXT,
        ARRAY[]::TEXT[]
    FROM property_exemptions;
    
    -- Check for duplicate parcel IDs
    RETURN QUERY
    SELECT 
        'duplicate_parcels'::TEXT,
        COUNT(*)::BIGINT,
        CASE 
            WHEN COUNT(*) = 0 THEN 'SUCCESS'
            ELSE 'ERROR'
        END::TEXT,
        CASE 
            WHEN COUNT(*) > 0 THEN ARRAY['Duplicate parcel IDs found']
            ELSE ARRAY[]::TEXT[]
        END
    FROM (
        SELECT parcel_id, COUNT(*) 
        FROM florida_properties_core 
        GROUP BY parcel_id 
        HAVING COUNT(*) > 1
    ) duplicates;
    
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- PHASE 5: PERFORMANCE OPTIMIZATION POST-MIGRATION
-- =====================================================================

-- Post-migration optimization function
CREATE OR REPLACE FUNCTION optimize_after_migration()
RETURNS TEXT AS $$
DECLARE
    result_message TEXT := '';
BEGIN
    -- Update statistics
    ANALYZE florida_properties_core;
    ANALYZE property_valuations;
    ANALYZE property_exemptions;
    ANALYZE property_characteristics;
    ANALYZE property_sales_enhanced;
    ANALYZE property_addresses;
    ANALYZE property_admin_data;
    
    result_message := result_message || 'Statistics updated. ';
    
    -- Refresh materialized view
    REFRESH MATERIALIZED VIEW property_summary_view;
    result_message := result_message || 'Materialized view refreshed. ';
    
    -- Check index usage
    PERFORM pg_stat_reset();
    result_message := result_message || 'Statistics reset for monitoring. ';
    
    -- Log completion
    INSERT INTO maintenance_log (operation, notes)
    VALUES ('post_migration_optimization', 'Migration optimization completed successfully');
    
    RETURN result_message || 'Migration optimization completed successfully.';
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- PHASE 6: ROLLBACK PROCEDURES (SAFETY)
-- =====================================================================

-- Rollback function in case of issues
CREATE OR REPLACE FUNCTION rollback_migration()
RETURNS TEXT AS $$
DECLARE
    backup_count INTEGER;
BEGIN
    -- Check if backup exists
    SELECT COUNT(*) INTO backup_count 
    FROM information_schema.tables 
    WHERE table_name = 'florida_parcels_backup_pre_migration';
    
    IF backup_count = 0 THEN
        RETURN 'ERROR: No backup table found. Cannot rollback.';
    END IF;
    
    -- Drop new tables (careful!)
    DROP TABLE IF EXISTS property_admin_data CASCADE;
    DROP TABLE IF EXISTS property_addresses CASCADE;
    DROP TABLE IF EXISTS property_sales_enhanced CASCADE;
    DROP TABLE IF EXISTS property_characteristics CASCADE;
    DROP TABLE IF EXISTS property_exemptions CASCADE;
    DROP TABLE IF EXISTS property_valuations CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS property_summary_view CASCADE;
    DROP TABLE IF EXISTS florida_properties_core CASCADE;
    
    -- Restore original table structure
    CREATE TABLE florida_parcels AS 
    SELECT * FROM florida_parcels_backup_pre_migration;
    
    RETURN 'Migration rolled back successfully. Original data restored.';
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- MIGRATION EXECUTION PLAN
-- =====================================================================

/*
RECOMMENDED EXECUTION STEPS:

1. PRE-MIGRATION:
   -- Run backup
   SELECT migrate_existing_property_data();
   
2. NAL DATA IMPORT:
   -- Load NAL data in batches
   SELECT * FROM import_nal_data_batch('[NAL_JSON_DATA]');
   
3. VALIDATION:
   -- Check data integrity
   SELECT * FROM validate_migrated_data();
   
4. OPTIMIZATION:
   -- Optimize performance
   SELECT optimize_after_migration();
   
5. MONITORING:
   -- Monitor performance for 24-48 hours
   -- Check query performance
   
6. CLEANUP:
   -- Remove backup tables after validation
   -- Archive old data if needed

ROLLBACK IF NEEDED:
   SELECT rollback_migration();

PERFORMANCE TESTING:
   -- Test common queries
   -- Monitor index usage
   -- Check materialized view performance
*/