
-- NAP (Property Characteristics) Table
CREATE TABLE IF NOT EXISTS nap_characteristics (
    id BIGSERIAL PRIMARY KEY,
    parcel_id TEXT NOT NULL,
    county TEXT NOT NULL,
    year INTEGER NOT NULL,

    -- Building characteristics
    year_built INTEGER,
    effective_year_built INTEGER,
    total_living_area INTEGER,
    heated_area INTEGER,
    gross_area INTEGER,
    adjusted_area INTEGER,

    -- Rooms
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    half_bathrooms INTEGER,
    full_bathrooms INTEGER,

    -- Structure
    stories DECIMAL(3,1),
    units INTEGER,
    buildings INTEGER,

    -- Construction
    construction_type TEXT,
    exterior_wall TEXT,
    roof_type TEXT,
    roof_material TEXT,
    foundation_type TEXT,

    -- Features
    pool BOOLEAN,
    garage_spaces INTEGER,
    carport_spaces INTEGER,
    fireplace_count INTEGER,

    -- Quality and condition
    quality_grade TEXT,
    condition_code TEXT,

    -- Land
    lot_size_sqft BIGINT,
    lot_size_acres DECIMAL(10,4),
    frontage INTEGER,
    depth INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(parcel_id, county, year)
);

CREATE INDEX idx_nap_parcel_county_year ON nap_characteristics(parcel_id, county, year);
CREATE INDEX idx_nap_county_year ON nap_characteristics(county, year);
CREATE INDEX idx_nap_year_built ON nap_characteristics(year_built);
