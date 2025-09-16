-- ============================================================
-- SUPABASE FTP PROXY SETUP
-- Creates infrastructure to fetch Sunbiz data through Supabase
-- ============================================================

-- 1. Create storage bucket for Sunbiz data
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'sunbiz-data',
    'sunbiz-data',
    false,
    5368709120, -- 5GB limit
    ARRAY['text/plain', 'application/zip', 'application/x-zip-compressed']
)
ON CONFLICT (id) DO NOTHING;

-- 2. Create table to track download jobs
CREATE TABLE IF NOT EXISTS public.sunbiz_download_jobs (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL, -- 'off', 'annual', 'llc', 'AG'
    status VARCHAR(20) DEFAULT 'pending', -- pending, downloading, completed, failed
    file_count INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Create table for officer data (if emails are found)
CREATE TABLE IF NOT EXISTS public.sunbiz_officers (
    id SERIAL PRIMARY KEY,
    doc_number VARCHAR(12),
    entity_name VARCHAR(255),
    officer_name VARCHAR(255),
    officer_title VARCHAR(100),
    officer_address VARCHAR(500),
    officer_city VARCHAR(100),
    officer_state VARCHAR(2),
    officer_zip VARCHAR(10),
    officer_email VARCHAR(255), -- THIS IS WHAT WE WANT!
    officer_phone VARCHAR(20),   -- THIS TOO!
    filing_date DATE,
    source_file VARCHAR(100),
    import_date TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (doc_number) REFERENCES sunbiz_corporate(doc_number)
);

-- Create indexes for officer table
CREATE INDEX IF NOT EXISTS idx_sunbiz_officers_doc_number 
    ON sunbiz_officers(doc_number);

CREATE INDEX IF NOT EXISTS idx_sunbiz_officers_email 
    ON sunbiz_officers(officer_email) 
    WHERE officer_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sunbiz_officers_name 
    ON sunbiz_officers(officer_name);

-- 4. Create function to fetch FTP data via HTTP
CREATE OR REPLACE FUNCTION fetch_sunbiz_data(
    data_type TEXT,
    use_edge_function BOOLEAN DEFAULT false
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    result JSONB;
BEGIN
    -- Log the download request
    INSERT INTO sunbiz_download_jobs (data_type, status, started_at)
    VALUES (data_type, 'downloading', NOW());
    
    IF use_edge_function THEN
        -- Call edge function (requires deployment)
        result := jsonb_build_object(
            'status', 'edge_function_required',
            'message', 'Deploy edge function first with: supabase functions deploy fetch-sunbiz',
            'data_type', data_type
        );
    ELSE
        -- Alternative: Direct HTTP request to known mirrors
        result := jsonb_build_object(
            'status', 'manual_download_required',
            'instructions', ARRAY[
                'Option 1: Use wget from command line',
                'wget -r ftp://ftp.dos.state.fl.us/public/doc/' || data_type || '/',
                'Option 2: Use cloud server to download',
                'Option 3: Contact sunbiz@dos.myflorida.com for bulk access'
            ],
            'data_type', data_type,
            'ftp_url', 'ftp://ftp.dos.state.fl.us/public/doc/' || data_type || '/'
        );
    END IF;
    
    RETURN result;
END;
$$;

-- 5. Create function to search for emails in existing data
CREATE OR REPLACE FUNCTION find_contact_info_in_data()
RETURNS TABLE (
    table_name TEXT,
    column_name TEXT,
    sample_value TEXT,
    count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Search all text columns for email patterns
    RETURN QUERY
    SELECT 
        'sunbiz_corporate'::TEXT as table_name,
        'registered_agent'::TEXT as column_name,
        registered_agent::TEXT as sample_value,
        COUNT(*)::BIGINT as count
    FROM sunbiz_corporate
    WHERE registered_agent LIKE '%@%'
    GROUP BY registered_agent
    LIMIT 10;
END;
$$;

-- 6. Grant permissions
GRANT EXECUTE ON FUNCTION fetch_sunbiz_data TO authenticated;
GRANT EXECUTE ON FUNCTION find_contact_info_in_data TO authenticated;
GRANT ALL ON TABLE sunbiz_download_jobs TO authenticated;
GRANT ALL ON TABLE sunbiz_officers TO authenticated;

-- ============================================================
-- USAGE INSTRUCTIONS
-- ============================================================
-- 1. Check for existing email data:
--    SELECT * FROM find_contact_info_in_data();
--
-- 2. Request FTP download:
--    SELECT fetch_sunbiz_data('off');  -- Officers/Directors
--    SELECT fetch_sunbiz_data('annual');  -- Annual Reports
--
-- 3. After manual download, load officer data:
--    Use the sunbiz loader scripts to process /off/ directory
-- ============================================================