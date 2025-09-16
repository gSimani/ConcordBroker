-- ConcordBroker Database Schema
-- Run this in Supabase SQL Editor


        CREATE TABLE IF NOT EXISTS parcels (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) UNIQUE NOT NULL,
            county_code VARCHAR(10),
            property_address TEXT,
            owner_name TEXT,
            owner_address TEXT,
            property_use_code VARCHAR(20),
            property_type VARCHAR(50),
            total_value DECIMAL(15,2),
            assessed_value DECIMAL(15,2),
            land_value DECIMAL(15,2),
            building_value DECIMAL(15,2),
            year_built INTEGER,
            living_area INTEGER,
            lot_size DECIMAL(10,2),
            bedrooms INTEGER,
            bathrooms DECIMAL(3,1),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS properties (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) REFERENCES parcels(parcel_id),
            property_name TEXT,
            property_description TEXT,
            zoning_code VARCHAR(20),
            neighborhood VARCHAR(100),
            school_district VARCHAR(100),
            latitude DECIMAL(10,7),
            longitude DECIMAL(10,7),
            features JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS sales_history (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            sale_date DATE,
            sale_price DECIMAL(15,2),
            seller_name TEXT,
            buyer_name TEXT,
            sale_type VARCHAR(50),
            qualified_sale BOOLEAN,
            deed_type VARCHAR(50),
            book_page VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS property_tax_info (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            tax_year INTEGER,
            millage_rate DECIMAL(8,4),
            taxable_value DECIMAL(15,2),
            exemptions DECIMAL(15,2),
            tax_amount DECIMAL(15,2),
            paid_amount DECIMAL(15,2),
            payment_status VARCHAR(20),
            due_date DATE,
            created_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS building_permits (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            permit_number VARCHAR(50) UNIQUE,
            permit_type VARCHAR(100),
            description TEXT,
            issue_date DATE,
            completion_date DATE,
            status VARCHAR(50),
            contractor_name TEXT,
            estimated_value DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS sunbiz_entities (
            id SERIAL PRIMARY KEY,
            entity_id VARCHAR(50) UNIQUE,
            entity_name TEXT,
            entity_type VARCHAR(100),
            status VARCHAR(50),
            filing_date DATE,
            registered_agent TEXT,
            principal_address TEXT,
            mailing_address TEXT,
            officers JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS property_entities (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50),
            entity_id VARCHAR(50),
            relationship_type VARCHAR(50),
            confidence_score DECIMAL(3,2),
            match_details JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS tracked_properties (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50),
            parcel_id VARCHAR(50),
            tracking_type VARCHAR(50),
            alert_preferences JSONB,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        


        CREATE TABLE IF NOT EXISTS fl_data_updates (
            id SERIAL PRIMARY KEY,
            data_source VARCHAR(100),
            update_type VARCHAR(50),
            records_processed INTEGER,
            status VARCHAR(50),
            error_message TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            metadata JSONB
        );
        


        CREATE TABLE IF NOT EXISTS property_profiles (
            id SERIAL PRIMARY KEY,
            parcel_id VARCHAR(50) UNIQUE,
            profile_data JSONB,
            market_analysis JSONB,
            investment_score DECIMAL(3,2),
            last_updated TIMESTAMP DEFAULT NOW()
        );
        


        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_parcels_county ON parcels(county_code);
        CREATE INDEX IF NOT EXISTS idx_parcels_owner ON parcels(owner_name);
        CREATE INDEX IF NOT EXISTS idx_parcels_address ON parcels(property_address);
        CREATE INDEX IF NOT EXISTS idx_sales_parcel ON sales_history(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_history(sale_date);
        CREATE INDEX IF NOT EXISTS idx_permits_parcel ON building_permits(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_tax_parcel ON property_tax_info(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON sunbiz_entities(entity_name);
        

