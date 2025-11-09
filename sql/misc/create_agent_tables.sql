-- Additional tables needed by agents

-- SDF Jobs tracking table
CREATE TABLE IF NOT EXISTS sdf_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE,
    county VARCHAR(50),
    year INTEGER,
    status VARCHAR(50),
    file_path TEXT,
    records_processed INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- NAV Jobs tracking table  
CREATE TABLE IF NOT EXISTS nav_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE,
    county VARCHAR(50),
    year INTEGER,
    status VARCHAR(50),
    file_path TEXT,
    records_processed INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- TPP Jobs tracking table
CREATE TABLE IF NOT EXISTS tpp_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE,
    county VARCHAR(50),
    year INTEGER,
    status VARCHAR(50),
    file_path TEXT,
    records_processed INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sunbiz SFTP tracking
CREATE TABLE IF NOT EXISTS sunbiz_sftp_downloads (
    id BIGSERIAL PRIMARY KEY,
    file_name VARCHAR(255) UNIQUE,
    file_type VARCHAR(50),
    file_size BIGINT,
    download_date TIMESTAMP,
    process_date TIMESTAMP,
    status VARCHAR(50),
    records_processed INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent configuration table
CREATE TABLE IF NOT EXISTS agent_config (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100) UNIQUE,
    config_key VARCHAR(100),
    config_value TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;