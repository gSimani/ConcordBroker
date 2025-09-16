
        -- Create Sunbiz entities table
        CREATE TABLE IF NOT EXISTS sunbiz_entities (
            entity_id VARCHAR(20) PRIMARY KEY,
            entity_name VARCHAR(255) NOT NULL,
            entity_type VARCHAR(20),
            status VARCHAR(20),
            filing_date DATE,
            principal_address TEXT,
            principal_city VARCHAR(100),
            principal_state VARCHAR(2),
            principal_zip VARCHAR(10),
            mailing_address TEXT,
            mailing_city VARCHAR(100),
            mailing_state VARCHAR(2),
            mailing_zip VARCHAR(10),
            registered_agent VARCHAR(255),
            officers JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create index for faster searches
        CREATE INDEX IF NOT EXISTS idx_sunbiz_entity_name ON sunbiz_entities(entity_name);
        CREATE INDEX IF NOT EXISTS idx_sunbiz_normalized_name ON sunbiz_entities(UPPER(entity_name));
        CREATE INDEX IF NOT EXISTS idx_sunbiz_principal_zip ON sunbiz_entities(principal_zip);
        
        -- Create entity matches table for tax deed properties
        CREATE TABLE IF NOT EXISTS tax_deed_entity_matches (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            property_id UUID,
            parcel_number VARCHAR(50),
            applicant_name VARCHAR(255),
            entity_id VARCHAR(20),
            entity_name VARCHAR(255),
            match_type VARCHAR(50),
            confidence DECIMAL(3,2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (entity_id) REFERENCES sunbiz_entities(entity_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_entity_matches_property ON tax_deed_entity_matches(property_id);
        CREATE INDEX IF NOT EXISTS idx_entity_matches_parcel ON tax_deed_entity_matches(parcel_number);
        