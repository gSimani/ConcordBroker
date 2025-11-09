-- Florida Parcels Table Schema
-- Comprehensive property data from NAL (Name and Address Listing) files
-- Designed to support all frontend requirements and fast queries

DROP TABLE IF EXISTS florida_parcels CASCADE;

CREATE TABLE florida_parcels (
    -- Primary identifier
    id BIGSERIAL PRIMARY KEY,
    
    -- Core identifiers from NAL file
    co_no INTEGER,                    -- County number
    parcel_id TEXT NOT NULL,          -- Primary parcel identifier
    file_t TEXT,                      -- File type
    asmnt_yr INTEGER,                 -- Assessment year
    
    -- Geographic identifiers
    twn TEXT,                         -- Township
    rng TEXT,                         -- Range 
    sec TEXT,                         -- Section
    census_bk TEXT,                   -- Census block
    
    -- Physical address (what users see)
    phy_addr1 TEXT,                   -- Primary physical address
    phy_addr2 TEXT,                   -- Secondary address info
    phy_city TEXT,                    -- City
    phy_zipcd TEXT,                   -- ZIP code
    
    -- Owner information
    owner_name TEXT,                  -- Property owner name (mapped from own_name)
    owner_addr1 TEXT,                 -- Owner address line 1 (mapped from own_addr1)
    owner_addr2 TEXT,                 -- Owner address line 2 (mapped from own_addr2)
    owner_city TEXT,                  -- Owner city (mapped from own_city)
    owner_state TEXT,                 -- Owner state (mapped from own_state)
    owner_zip TEXT,                   -- Owner ZIP (mapped from own_zipcd)
    owner_state_dom TEXT,             -- Owner state of domicile
    
    -- Fiduciary information (if applicable)
    fidu_name TEXT,                   -- Fiduciary name
    fidu_addr1 TEXT,                  -- Fiduciary address line 1
    fidu_addr2 TEXT,                  -- Fiduciary address line 2
    fidu_city TEXT,                   -- Fiduciary city
    fidu_state TEXT,                  -- Fiduciary state
    fidu_zipcd TEXT,                  -- Fiduciary ZIP
    fidu_cd TEXT,                     -- Fiduciary code
    
    -- Property values (all as BIGINT for precision)
    just_value BIGINT,                -- Just/Market value (mapped from jv)
    taxable_value BIGINT,             -- Taxable value (mapped from tv_sd)
    assessed_value BIGINT,            -- Assessed value (mapped from av_sd)
    land_value BIGINT,                -- Land value (mapped from lnd_val)
    building_value BIGINT,            -- Building/improvement value
    
    -- Homestead and exemptions
    jv_hmstd BIGINT,                  -- Homestead just value
    av_hmstd BIGINT,                  -- Homestead assessed value
    homestead_exemption TEXT,         -- Homestead exemption flag
    other_exemptions TEXT,            -- Other exemptions
    
    -- Property characteristics
    property_use TEXT,                -- Property use code (mapped from dor_uc)
    property_use_desc TEXT,           -- Property use description
    pa_uc TEXT,                       -- Property appraiser use code
    
    -- Building details
    year_built INTEGER,               -- Actual year built (mapped from act_yr_blt)
    eff_year_built INTEGER,           -- Effective year built (mapped from eff_yr_blt)
    total_living_area INTEGER,        -- Total living area sqft (mapped from tot_lvg_area)
    heated_area INTEGER,              -- Heated area
    no_buldng INTEGER,                -- Number of buildings
    no_res_unts INTEGER,              -- Number of residential units
    
    -- Land characteristics
    land_sqft BIGINT,                 -- Land square footage (mapped from lnd_sqfoot)
    lnd_unts_cd TEXT,                 -- Land units code
    no_lnd_unts INTEGER,              -- Number of land units
    
    -- Building quality and features
    imp_qual TEXT,                    -- Improvement quality
    const_class TEXT,                 -- Construction class
    spec_feat_val BIGINT,             -- Special features value
    
    -- Sale information (most recent sale from NAL)
    sale_price BIGINT,                -- Most recent sale price (mapped from sale_prc1)
    sale_date DATE,                   -- Sale date (constructed from sale_yr1 and sale_mo1)
    sale_yr1 INTEGER,                 -- Sale year
    sale_mo1 INTEGER,                 -- Sale month
    qual_cd1 TEXT,                    -- Sale qualification code
    vi_cd1 TEXT,                      -- Validity indicator code
    or_book1 TEXT,                    -- Official records book
    or_page1 TEXT,                    -- Official records page
    clerk_no1 TEXT,                   -- Clerk number
    sal_chng_cd1 TEXT,                -- Sale change code
    multi_par_sal1 TEXT,              -- Multi-parcel sale flag
    
    -- Second sale information (if available)
    sale_prc2 BIGINT,                 -- Second sale price
    sale_yr2 INTEGER,                 -- Second sale year
    sale_mo2 INTEGER,                 -- Second sale month
    qual_cd2 TEXT,                    -- Second sale qualification
    vi_cd2 TEXT,                      -- Second validity indicator
    or_book2 TEXT,                    -- Second OR book
    or_page2 TEXT,                    -- Second OR page
    clerk_no2 TEXT,                   -- Second clerk number
    
    -- Legal description
    s_legal TEXT,                     -- Legal description
    subdivision TEXT,                 -- Subdivision name
    lot TEXT,                         -- Lot number
    block TEXT,                       -- Block number
    
    -- Assessment and market info
    app_stat TEXT,                    -- Appraiser status
    co_app_stat TEXT,                 -- County appraiser status
    mkt_ar TEXT,                      -- Market area
    nbrhd_cd TEXT,                    -- Neighborhood code
    
    -- Additional fields
    alt_key TEXT,                     -- Alternative key
    public_lnd TEXT,                  -- Public land indicator
    tax_auth_cd TEXT,                 -- Tax authority code
    dt_last_inspt TEXT,               -- Date of last inspection
    
    -- Assessment transfer info
    ass_trnsfr_fg TEXT,               -- Assessment transfer flag
    prev_hmstd_own TEXT,              -- Previous homestead owner
    ass_dif_trns BIGINT,              -- Assessment difference transfer
    cono_prv_hm TEXT,                 -- County previous home
    parcel_id_prv_hmstd TEXT,         -- Previous homestead parcel ID
    yr_val_trnsf INTEGER,             -- Year value transferred
    
    -- All exemption codes (for comprehensive exemption tracking)
    exmpt_01 BIGINT, exmpt_02 BIGINT, exmpt_03 BIGINT, exmpt_04 BIGINT, exmpt_05 BIGINT,
    exmpt_06 BIGINT, exmpt_07 BIGINT, exmpt_08 BIGINT, exmpt_09 BIGINT, exmpt_10 BIGINT,
    exmpt_11 BIGINT, exmpt_12 BIGINT, exmpt_13 BIGINT, exmpt_14 BIGINT, exmpt_15 BIGINT,
    exmpt_16 BIGINT, exmpt_17 BIGINT, exmpt_18 BIGINT, exmpt_19 BIGINT, exmpt_20 BIGINT,
    exmpt_21 BIGINT, exmpt_22 BIGINT, exmpt_23 BIGINT, exmpt_24 BIGINT, exmpt_25 BIGINT,
    exmpt_26 BIGINT, exmpt_27 BIGINT, exmpt_28 BIGINT, exmpt_29 BIGINT, exmpt_30 BIGINT,
    exmpt_31 BIGINT, exmpt_32 BIGINT, exmpt_33 BIGINT, exmpt_34 BIGINT, exmpt_35 BIGINT,
    exmpt_36 BIGINT, exmpt_37 BIGINT, exmpt_38 BIGINT, exmpt_39 BIGINT, exmpt_40 BIGINT,
    exmpt_41 BIGINT, exmpt_42 BIGINT, exmpt_43 BIGINT, exmpt_44 BIGINT, exmpt_45 BIGINT,
    exmpt_46 BIGINT, exmpt_80 BIGINT, exmpt_81 BIGINT, exmpt_82 BIGINT,
    
    -- Special records
    seq_no INTEGER,                   -- Sequence number
    rs_id TEXT,                       -- Record ID
    mp_id TEXT,                       -- Map ID
    state_par_id TEXT,                -- State parcel ID
    spc_cir_cd TEXT,                  -- Special circumstances code
    spc_cir_yr INTEGER,               -- Special circumstances year
    spc_cir_txt TEXT,                 -- Special circumstances text
    
    -- Additional derived fields for frontend compatibility
    property_address_full TEXT,       -- Full formatted address
    market_value BIGINT,              -- Market value (alias for just_value)
    bedrooms INTEGER,                 -- Bedrooms (derived or estimated)
    bathrooms DECIMAL(3,1),           -- Bathrooms (derived or estimated)
    stories INTEGER,                  -- Number of stories
    units INTEGER,                    -- Number of units (default 1)
    zoning TEXT,                      -- Zoning information
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(parcel_id)
);

-- Indexes for fast queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_addr1 ON florida_parcels(phy_addr1);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name ON florida_parcels(owner_name);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_city ON florida_parcels(phy_city);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_zipcd ON florida_parcels(phy_zipcd);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_property_use ON florida_parcels(property_use);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_just_value ON florida_parcels(just_value);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_year_built ON florida_parcels(year_built);

-- Text search indexes for address searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_addr1_gin ON florida_parcels USING gin(phy_addr1 gin_trgm_ops);

-- Enable Row Level Security (but allow all for now)
ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed)
CREATE POLICY "Allow all operations on florida_parcels" ON florida_parcels
    FOR ALL USING (true) WITH CHECK (true);

-- Add a comment describing the table
COMMENT ON TABLE florida_parcels IS 'Comprehensive Florida property data from NAL (Name and Address Listing) files. Contains parcel details, ownership, values, and building characteristics.';