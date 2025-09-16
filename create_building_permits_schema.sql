-- Building Permits Schema for ConcordBroker
-- This table stores comprehensive building permit data for properties

DROP TABLE IF EXISTS public.building_permits CASCADE;
DROP TABLE IF EXISTS public.permit_inspections CASCADE;
DROP TABLE IF EXISTS public.contractor_performance CASCADE;

-- Main building permits table
CREATE TABLE public.building_permits (
    id SERIAL PRIMARY KEY,
    
    -- Property identification
    parcel_id VARCHAR(50),
    property_address TEXT,
    property_city VARCHAR(100),
    property_state VARCHAR(2) DEFAULT 'FL',
    property_zip VARCHAR(10),
    
    -- Site Information
    permit_number VARCHAR(50) UNIQUE NOT NULL,
    master_permit VARCHAR(50),
    job_value DECIMAL(12,2),
    square_footage INTEGER,
    
    -- Permit Information
    application_type VARCHAR(100),
    job_name TEXT,
    film_number VARCHAR(50),
    application_date DATE,
    permit_date DATE,
    co_cc_date DATE, -- Certificate of Occupancy/Completion
    expiration_date DATE,
    
    -- Financial Information
    total_fees DECIMAL(10,2),
    recorded_payments DECIMAL(10,2),
    balance DECIMAL(10,2),
    
    -- Status Information
    status VARCHAR(50), -- Active, Completed, Expired, Cancelled, Pending
    permit_type VARCHAR(100), -- Building, Electrical, Plumbing, Mechanical, etc.
    description TEXT,
    
    -- Applicant Information
    applicant_name VARCHAR(255),
    applicant_address TEXT,
    applicant_phone VARCHAR(20),
    applicant_email VARCHAR(255),
    
    -- Contact Information (if different from applicant)
    contact_name VARCHAR(255),
    contact_address TEXT,
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    
    -- Contractor Information
    contractor_name VARCHAR(255),
    contractor_address TEXT,
    contractor_phone VARCHAR(20),
    contractor_email VARCHAR(255),
    contractor_license VARCHAR(50),
    contractor_type VARCHAR(100), -- General, Electrical, Plumbing, HVAC, Roofing, etc.
    
    -- Inspection Information
    inspection_status VARCHAR(50), -- Pending, Scheduled, Passed, Failed, Final Approved
    last_inspection_date DATE,
    next_inspection_date DATE,
    inspector_name VARCHAR(255),
    
    -- Additional fields
    building_code VARCHAR(20),
    zoning VARCHAR(50),
    lot_size DECIMAL(10,2),
    construction_type VARCHAR(100),
    occupancy_type VARCHAR(100),
    fire_district VARCHAR(50),
    flood_zone VARCHAR(20),
    
    -- System fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50) DEFAULT 'Manual Entry'
);

-- Sub-permits table for permits that have multiple components
CREATE TABLE public.permit_sub_permits (
    id SERIAL PRIMARY KEY,
    parent_permit_id INTEGER REFERENCES building_permits(id) ON DELETE CASCADE,
    sub_permit_number VARCHAR(50),
    sub_permit_type VARCHAR(100), -- Electrical, Plumbing, Mechanical, etc.
    status VARCHAR(50),
    permit_date DATE,
    completion_date DATE,
    contractor_name VARCHAR(255),
    contractor_license VARCHAR(50),
    fees DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Permit inspections table for tracking inspection history
CREATE TABLE public.permit_inspections (
    id SERIAL PRIMARY KEY,
    permit_id INTEGER REFERENCES building_permits(id) ON DELETE CASCADE,
    inspection_type VARCHAR(100), -- Foundation, Framing, Electrical Rough, Plumbing Rough, Final, etc.
    inspection_date DATE,
    inspection_status VARCHAR(50), -- Scheduled, Passed, Failed, Cancelled
    inspector_name VARCHAR(255),
    inspection_notes TEXT,
    reinspection_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Contractor performance tracking
CREATE TABLE public.contractor_performance (
    id SERIAL PRIMARY KEY,
    contractor_license VARCHAR(50) UNIQUE,
    contractor_name VARCHAR(255),
    total_permits INTEGER DEFAULT 0,
    active_permits INTEGER DEFAULT 0,
    completed_permits INTEGER DEFAULT 0,
    passed_inspections INTEGER DEFAULT 0,
    failed_inspections INTEGER DEFAULT 0,
    pass_rate DECIMAL(5,2), -- Calculated percentage
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_building_permits_parcel_id ON building_permits(parcel_id);
CREATE INDEX idx_building_permits_permit_number ON building_permits(permit_number);
CREATE INDEX idx_building_permits_contractor_license ON building_permits(contractor_license);
CREATE INDEX idx_building_permits_status ON building_permits(status);
CREATE INDEX idx_building_permits_permit_date ON building_permits(permit_date DESC);
CREATE INDEX idx_building_permits_address ON building_permits USING GIN(to_tsvector('english', property_address));

-- Create trigger to update contractor performance
CREATE OR REPLACE FUNCTION update_contractor_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update contractor performance stats when permit status changes
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        INSERT INTO contractor_performance (contractor_license, contractor_name)
        VALUES (NEW.contractor_license, NEW.contractor_name)
        ON CONFLICT (contractor_license) DO UPDATE SET
            contractor_name = EXCLUDED.contractor_name;
            
        -- Update performance metrics
        UPDATE contractor_performance SET
            total_permits = (
                SELECT COUNT(*) FROM building_permits 
                WHERE contractor_license = NEW.contractor_license
            ),
            active_permits = (
                SELECT COUNT(*) FROM building_permits 
                WHERE contractor_license = NEW.contractor_license 
                AND status IN ('Active', 'In Progress', 'Open')
            ),
            completed_permits = (
                SELECT COUNT(*) FROM building_permits 
                WHERE contractor_license = NEW.contractor_license 
                AND status IN ('Completed', 'Closed', 'Final Approved')
            ),
            passed_inspections = (
                SELECT COUNT(*) FROM permit_inspections i
                JOIN building_permits p ON i.permit_id = p.id
                WHERE p.contractor_license = NEW.contractor_license 
                AND i.inspection_status = 'Passed'
            ),
            failed_inspections = (
                SELECT COUNT(*) FROM permit_inspections i
                JOIN building_permits p ON i.permit_id = p.id
                WHERE p.contractor_license = NEW.contractor_license 
                AND i.inspection_status = 'Failed'
            ),
            last_updated = NOW()
        WHERE contractor_license = NEW.contractor_license;
        
        -- Calculate pass rate
        UPDATE contractor_performance SET
            pass_rate = CASE 
                WHEN (passed_inspections + failed_inspections) > 0 
                THEN ROUND((passed_inspections::DECIMAL / (passed_inspections + failed_inspections)) * 100, 2)
                ELSE 0 
            END
        WHERE contractor_license = NEW.contractor_license;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_contractor_performance
    AFTER INSERT OR UPDATE OR DELETE ON building_permits
    FOR EACH ROW EXECUTE FUNCTION update_contractor_performance();

-- Sample data for testing
INSERT INTO building_permits (
    parcel_id, property_address, property_city, permit_number, master_permit,
    job_value, square_footage, application_type, job_name, film_number,
    application_date, permit_date, co_cc_date, total_fees, recorded_payments, balance,
    status, permit_type, description,
    applicant_name, applicant_address, applicant_phone,
    contractor_name, contractor_address, contractor_license, contractor_type,
    inspection_status
) VALUES 
-- Sample permit 1: Kitchen renovation
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '2024-BP-12345', '2024-MP-5678',
 85000.00, 2500, 'Building Alteration', 'Kitchen and Master Bath Renovation', 'F-2024-1234',
 '2024-01-05', '2024-01-15', '2024-06-20', 2850.00, 2850.00, 0.00,
 'Completed', 'Building', 'Complete kitchen renovation including new cabinets, countertops, appliances. Master bathroom remodel with new fixtures.',
 'John Smith', '1234 SAMPLE ST, FORT LAUDERDALE, FL 33301', '(954) 555-0100',
 'Premier Renovations LLC', '1234 Construction Blvd, Fort Lauderdale, FL 33301', 'CGC1234567', 'General Contractor',
 'Final Approved'),

-- Sample permit 2: HVAC replacement
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '2024-HVAC-67890', NULL,
 12500.00, 2000, 'Mechanical', 'HVAC System Replacement', 'F-2024-5678',
 '2024-01-08', '2024-01-10', '2024-01-25', 450.00, 450.00, 0.00,
 'Completed', 'Mechanical', '5-ton split system AC replacement with new air handler',
 'John Smith', '1234 SAMPLE ST, FORT LAUDERDALE, FL 33301', '(954) 555-0100',
 'Cool Air Systems Inc', '5678 AC Drive, Pompano Beach, FL 33060', 'CAC1234567', 'Mechanical Contractor',
 'Final Approved'),

-- Sample permit 3: Active pool installation
('064210010010', '1234 SAMPLE ST', 'FORT LAUDERDALE', '2024-POOL-11111', '2024-MP-9999',
 65000.00, 600, 'Pool/Spa', 'In-ground Pool Installation', 'F-2024-9999',
 '2024-10-15', '2024-10-25', NULL, 1850.00, 1850.00, 0.00,
 'Active', 'Pool/Spa', 'New 15x30 in-ground pool with spa and deck',
 'John Smith', '1234 SAMPLE ST, FORT LAUDERDALE, FL 33301', '(954) 555-0100',
 'Aqua Dreams Pools LLC', '3456 Pool Plaza, Plantation, FL 33324', 'CPC1234567', 'Pool Contractor',
 'In Progress');

-- Sample sub-permits
INSERT INTO permit_sub_permits (parent_permit_id, sub_permit_number, sub_permit_type, status, permit_date, contractor_name, contractor_license, fees)
VALUES 
(1, '2024-EL-1001', 'Electrical', 'Completed', '2024-01-16', 'Bright Electric LLC', 'EC1234567', 350.00),
(1, '2024-PL-1002', 'Plumbing', 'Completed', '2024-01-18', 'Pro Plumbing Co', 'CFC1234567', 275.00),
(3, '2024-EL-1003', 'Electrical', 'Active', '2024-10-26', 'Pool Electric Pro', 'EC2345678', 450.00),
(3, '2024-PL-1004', 'Plumbing', 'Active', '2024-10-27', 'Aqua Plumbing LLC', 'CFC2345678', 320.00);

-- Sample inspections
INSERT INTO permit_inspections (permit_id, inspection_type, inspection_date, inspection_status, inspector_name, inspection_notes)
VALUES 
(1, 'Foundation', '2024-01-20', 'Passed', 'Inspector Johnson', 'Foundation meets code requirements'),
(1, 'Framing', '2024-02-15', 'Passed', 'Inspector Johnson', 'Framing inspection passed'),
(1, 'Final', '2024-06-18', 'Passed', 'Inspector Smith', 'Final inspection approved'),
(2, 'Rough', '2024-01-12', 'Passed', 'Inspector Brown', 'HVAC rough-in approved'),
(2, 'Final', '2024-01-24', 'Passed', 'Inspector Brown', 'HVAC final inspection passed'),
(3, 'Layout', '2024-10-28', 'Passed', 'Inspector Wilson', 'Pool layout approved'),
(3, 'Steel', '2024-11-15', 'Scheduled', 'Inspector Wilson', 'Steel inspection scheduled');

-- Create a view for easy permit lookup with contractor performance
CREATE OR REPLACE VIEW permit_details_view AS
SELECT 
    bp.*,
    cp.total_permits as contractor_total_permits,
    cp.active_permits as contractor_active_permits,
    cp.completed_permits as contractor_completed_permits,
    cp.passed_inspections as contractor_passed_inspections,
    cp.failed_inspections as contractor_failed_inspections,
    cp.pass_rate as contractor_pass_rate
FROM building_permits bp
LEFT JOIN contractor_performance cp ON bp.contractor_license = cp.contractor_license;

-- Grant permissions
GRANT ALL ON building_permits TO anon, authenticated;
GRANT ALL ON permit_sub_permits TO anon, authenticated;
GRANT ALL ON permit_inspections TO anon, authenticated;
GRANT ALL ON contractor_performance TO anon, authenticated;
GRANT ALL ON permit_details_view TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;