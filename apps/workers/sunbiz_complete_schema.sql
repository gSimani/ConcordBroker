
        -- Corporations table
        CREATE TABLE IF NOT EXISTS sunbiz_corporations (
            entity_id VARCHAR(20) PRIMARY KEY,
            entity_name VARCHAR(255) NOT NULL,
            status VARCHAR(20),
            entity_type VARCHAR(50),
            filing_date DATE,
            state_country VARCHAR(2),
            principal_address TEXT,
            principal_city VARCHAR(100),
            principal_state VARCHAR(2),
            principal_zip VARCHAR(10),
            mailing_address TEXT,
            mailing_city VARCHAR(100),
            mailing_state VARCHAR(2),
            mailing_zip VARCHAR(10),
            registered_agent_name VARCHAR(255),
            registered_agent_address TEXT,
            registered_agent_city VARCHAR(100),
            registered_agent_state VARCHAR(2),
            registered_agent_zip VARCHAR(10),
            document_number VARCHAR(50),
            fei_number VARCHAR(20),
            date_filed DATE,
            last_event VARCHAR(50),
            event_date DATE,
            event_file_number VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Fictitious names table
        CREATE TABLE IF NOT EXISTS sunbiz_fictitious_names (
            registration_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            owner_name VARCHAR(255),
            owner_address TEXT,
            owner_city VARCHAR(100),
            owner_state VARCHAR(2),
            owner_zip VARCHAR(10),
            registration_date DATE,
            expiration_date DATE,
            status VARCHAR(20),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Registered agents table
        CREATE TABLE IF NOT EXISTS sunbiz_registered_agents (
            agent_id VARCHAR(20) PRIMARY KEY,
            agent_name VARCHAR(255) NOT NULL,
            agent_type VARCHAR(50),
            address TEXT,
            city VARCHAR(100),
            state VARCHAR(2),
            zip_code VARCHAR(10),
            entity_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Entity name search table (for fast lookups)
        CREATE TABLE IF NOT EXISTS sunbiz_entity_search (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            entity_id VARCHAR(20),
            entity_name VARCHAR(255),
            normalized_name VARCHAR(255),
            entity_type VARCHAR(50),
            source_table VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_corp_name ON sunbiz_corporations(entity_name);
        CREATE INDEX IF NOT EXISTS idx_corp_status ON sunbiz_corporations(status);
        CREATE INDEX IF NOT EXISTS idx_corp_zip ON sunbiz_corporations(principal_zip);
        CREATE INDEX IF NOT EXISTS idx_corp_filing_date ON sunbiz_corporations(filing_date);
        
        CREATE INDEX IF NOT EXISTS idx_fic_name ON sunbiz_fictitious_names(name);
        CREATE INDEX IF NOT EXISTS idx_fic_owner ON sunbiz_fictitious_names(owner_name);
        
        CREATE INDEX IF NOT EXISTS idx_agent_name ON sunbiz_registered_agents(agent_name);
        
        CREATE INDEX IF NOT EXISTS idx_search_normalized ON sunbiz_entity_search(normalized_name);
        CREATE INDEX IF NOT EXISTS idx_search_entity_id ON sunbiz_entity_search(entity_id);
        