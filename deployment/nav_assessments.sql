
-- NAV (Assessed Values) Table
CREATE TABLE IF NOT EXISTS nav_assessments (
    id BIGSERIAL PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    county TEXT NOT NULL,
    year INTEGER NOT NULL,

    -- Values
    just_value BIGINT,
    assessed_value BIGINT,
    taxable_value BIGINT,
    land_value BIGINT,
    building_value BIGINT,

    -- Exemptions
    homestead_exemption BIGINT,
    other_exemptions BIGINT,
    total_exemptions BIGINT,

    -- Additional fields
    special_assessments BIGINT,
    tax_district TEXT,
    millage_rate DECIMAL(10,4),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(parcel_id, county, year)
);

CREATE INDEX idx_nav_parcel_county_year ON nav_assessments(parcel_id, county, year);
CREATE INDEX idx_nav_county_year ON nav_assessments(county, year);
