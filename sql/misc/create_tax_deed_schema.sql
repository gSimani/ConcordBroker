-- Tax Deed Sales Schema for ConcordBroker
-- This table stores comprehensive tax deed auction and bidding data

DROP TABLE IF EXISTS public.tax_deed_auctions CASCADE;
DROP TABLE IF EXISTS public.tax_deed_bidding_items CASCADE;
DROP TABLE IF EXISTS public.auction_bidding_history CASCADE;

-- Tax Deed Auctions table
CREATE TABLE public.tax_deed_auctions (
    id SERIAL PRIMARY KEY,
    
    -- Auction Information
    auction_date DATE NOT NULL,
    auction_time TIME,
    description TEXT,
    auction_type VARCHAR(50), -- Online, Live, Hybrid
    status VARCHAR(50), -- Upcoming, Active, Completed, Cancelled
    
    -- Auction Details
    total_items INTEGER DEFAULT 0,
    items_sold INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2),
    location VARCHAR(255),
    auctioneer VARCHAR(255),
    
    -- Online Auction Details
    online_platform VARCHAR(100),
    platform_url TEXT,
    registration_deadline DATE,
    deposit_required DECIMAL(10,2),
    bid_increment DECIMAL(8,2) DEFAULT 25.00,
    
    -- System fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(50) DEFAULT 'County Records'
);

-- Tax Deed Bidding Items table
CREATE TABLE public.tax_deed_bidding_items (
    id SERIAL PRIMARY KEY,
    auction_id INTEGER REFERENCES tax_deed_auctions(id) ON DELETE CASCADE,
    
    -- Property Identification
    parcel_id VARCHAR(50) NOT NULL,
    tax_deed_number VARCHAR(50) UNIQUE,
    tax_certificate_number VARCHAR(50),
    
    -- Property Address
    legal_situs_address TEXT,
    property_city VARCHAR(100),
    property_state VARCHAR(2) DEFAULT 'FL',
    property_zip VARCHAR(10),
    
    -- Property Details
    homestead_exemption BOOLEAN DEFAULT FALSE,
    assessed_value DECIMAL(12,2),
    soh_value DECIMAL(12,2), -- Save Our Homes Value
    land_use_code VARCHAR(20),
    property_type VARCHAR(100),
    lot_size DECIMAL(10,2),
    building_sqft INTEGER,
    year_built INTEGER,
    
    -- Bidding Information
    opening_bid DECIMAL(10,2) NOT NULL,
    current_bid DECIMAL(10,2),
    winning_bid DECIMAL(10,2),
    reserve_met BOOLEAN DEFAULT FALSE,
    
    -- Auction Status
    item_status VARCHAR(50), -- Active, Sold, Passed, Withdrawn
    close_time TIMESTAMP, -- Auction close time EDT
    
    -- Bidding Activity
    total_bids INTEGER DEFAULT 0,
    unique_bidders INTEGER DEFAULT 0,
    
    -- Applicant Information
    applicant_name VARCHAR(255),
    applicant_type VARCHAR(100), -- Individual, LLC, Corporation, Trust
    
    -- Winner Information (if sold)
    winning_bidder VARCHAR(255),
    winning_bidder_number VARCHAR(50),
    sale_confirmed BOOLEAN DEFAULT FALSE,
    
    -- Tax Information
    tax_years_included VARCHAR(50), -- e.g., "2019-2022"
    total_taxes_owed DECIMAL(10,2),
    interest_rate DECIMAL(5,2),
    
    -- Links and References
    gis_parcel_map_url TEXT,
    property_appraisal_url TEXT,
    deed_book VARCHAR(20),
    deed_page VARCHAR(20),
    
    -- System fields
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Auction Bidding History table
CREATE TABLE public.auction_bidding_history (
    id SERIAL PRIMARY KEY,
    bidding_item_id INTEGER REFERENCES tax_deed_bidding_items(id) ON DELETE CASCADE,
    
    -- Bid Information
    bid_amount DECIMAL(10,2) NOT NULL,
    bid_time TIMESTAMP DEFAULT NOW(),
    bidder_number VARCHAR(50),
    bidder_name VARCHAR(255), -- May be anonymous
    
    -- Bid Status
    bid_status VARCHAR(20) DEFAULT 'Active', -- Active, Outbid, Winning
    auto_bid BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_tax_deed_auctions_date ON tax_deed_auctions(auction_date DESC);
CREATE INDEX idx_tax_deed_auctions_status ON tax_deed_auctions(status);
CREATE INDEX idx_bidding_items_parcel_id ON tax_deed_bidding_items(parcel_id);
CREATE INDEX idx_bidding_items_auction_id ON tax_deed_bidding_items(auction_id);
CREATE INDEX idx_bidding_items_status ON tax_deed_bidding_items(item_status);
CREATE INDEX idx_bidding_items_close_time ON tax_deed_bidding_items(close_time);
CREATE INDEX idx_bidding_history_item_id ON auction_bidding_history(bidding_item_id);
CREATE INDEX idx_bidding_history_bid_time ON auction_bidding_history(bid_time DESC);

-- Create trigger to update current bid automatically
CREATE OR REPLACE FUNCTION update_current_bid()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the current bid on the bidding item
    UPDATE tax_deed_bidding_items 
    SET 
        current_bid = NEW.bid_amount,
        total_bids = total_bids + 1,
        updated_at = NOW()
    WHERE id = NEW.bidding_item_id;
    
    -- Mark previous bids as outbid
    UPDATE auction_bidding_history 
    SET bid_status = 'Outbid'
    WHERE bidding_item_id = NEW.bidding_item_id 
    AND id != NEW.id 
    AND bid_status = 'Active';
    
    -- Set new bid as active/winning
    NEW.bid_status = CASE 
        WHEN EXISTS (
            SELECT 1 FROM tax_deed_bidding_items 
            WHERE id = NEW.bidding_item_id 
            AND close_time > NOW()
        ) THEN 'Active'
        ELSE 'Winning'
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_current_bid
    BEFORE INSERT ON auction_bidding_history
    FOR EACH ROW EXECUTE FUNCTION update_current_bid();

-- Sample data for testing
INSERT INTO tax_deed_auctions (
    auction_date, auction_time, description, auction_type, status,
    total_items, location, auctioneer, online_platform, platform_url,
    registration_deadline, deposit_required, bid_increment
) VALUES 
-- Upcoming auction
('2025-01-15', '10:00:00', 'Broward County Tax Deed Sale - January 2025', 'Online', 'Upcoming',
 245, 'Online Platform', 'Broward County Tax Collector', 'BidOnPropertyTax.com', 'https://www.bidonpropertytax.com',
 '2025-01-10', 5000.00, 25.00),

-- Past auction
('2024-11-20', '10:00:00', 'Broward County Tax Deed Sale - November 2024', 'Online', 'Completed',
 187, 'Online Platform', 'Broward County Tax Collector', 'BidOnPropertyTax.com', 'https://www.bidonpropertytax.com',
 '2024-11-15', 5000.00, 25.00),

-- Another past auction
('2024-09-18', '10:00:00', 'Broward County Tax Deed Sale - September 2024', 'Online', 'Completed',
 156, 'Online Platform', 'Broward County Tax Collector', 'BidOnPropertyTax.com', 'https://www.bidonpropertytax.com',
 '2024-09-13', 5000.00, 25.00);

-- Sample bidding items for upcoming auction
INSERT INTO tax_deed_bidding_items (
    auction_id, parcel_id, tax_deed_number, tax_certificate_number,
    legal_situs_address, property_city, property_zip,
    homestead_exemption, assessed_value, soh_value,
    opening_bid, current_bid, item_status, close_time,
    applicant_name, applicant_type, tax_years_included, total_taxes_owed,
    gis_parcel_map_url, property_appraisal_url,
    land_use_code, property_type, lot_size, building_sqft, year_built
) VALUES 
-- Active item for upcoming auction
(1, '064210010010', 'TD-2025-00123', 'TC-2022-05847',
 '1234 SAMPLE ST, FORT LAUDERDALE, FL 33301', 'FORT LAUDERDALE', '33301',
 FALSE, 285000.00, 275000.00,
 8500.00, 12750.00, 'Active', '2025-01-15 17:00:00',
 'Investment Holdings LLC', 'LLC', '2020-2022', 8234.50,
 'https://gis.broward.org/parcel/064210010010', 'https://bcpa.broward.org/property/064210010010',
 '0100', 'Single Family Residential', 0.25, 2450, 1987),

-- Another active item
(1, '064210010011', 'TD-2025-00124', 'TC-2022-05848',
 '1236 SAMPLE ST, FORT LAUDERDALE, FL 33301', 'FORT LAUDERDALE', '33301',
 TRUE, 195000.00, 185000.00,
 3200.00, 3200.00, 'Active', '2025-01-15 17:00:00',
 'John Smith', 'Individual', '2021-2022', 3156.75,
 'https://gis.broward.org/parcel/064210010011', 'https://bcpa.broward.org/property/064210010011',
 '0100', 'Single Family Residential', 0.22, 1875, 1992),

-- Sold item from past auction
(2, '064210015020', 'TD-2024-00987', 'TC-2021-08934',
 '5678 EXAMPLE AVE, PEMBROKE PINES, FL 33028', 'PEMBROKE PINES', '33028',
 FALSE, 425000.00, 405000.00,
 12500.00, 67500.00, 'Sold', '2024-11-20 17:00:00',
 'Sunshine Investments Corp', 'Corporation', '2019-2021', 12234.80,
 'https://gis.broward.org/parcel/064210015020', 'https://bcpa.broward.org/property/064210015020',
 '0100', 'Single Family Residential', 0.18, 3200, 2003),

-- Passed item from past auction
(2, '064210025030', 'TD-2024-00988', 'TC-2021-08935',
 '9012 TEST BLVD, HOLLYWOOD, FL 33021', 'HOLLYWOOD', '33021',
 FALSE, 95000.00, 89000.00,
 18500.00, 18500.00, 'Passed', '2024-11-20 17:00:00',
 'Miami Property Trust', 'Trust', '2019-2021', 18345.25,
 'https://gis.broward.org/parcel/064210025030', 'https://bcpa.broward.org/property/064210025030',
 '0200', 'Commercial', 0.45, 2800, 1985);

-- Sample bidding history
INSERT INTO auction_bidding_history (
    bidding_item_id, bid_amount, bid_time, bidder_number, bidder_name, bid_status
) VALUES 
-- Bidding on first active item
(1, 8500.00, '2025-01-10 09:00:00', 'B001', 'Bidder #001', 'Outbid'),
(1, 9250.00, '2025-01-10 14:30:00', 'B015', 'Bidder #015', 'Outbid'),
(1, 10500.00, '2025-01-11 11:15:00', 'B007', 'Bidder #007', 'Outbid'),
(1, 12750.00, '2025-01-12 16:45:00', 'B003', 'Bidder #003', 'Active'),

-- Bidding history for sold item
(3, 12500.00, '2024-11-18 09:00:00', 'B025', 'Bidder #025', 'Outbid'),
(3, 25000.00, '2024-11-19 13:20:00', 'B012', 'Bidder #012', 'Outbid'),
(3, 45000.00, '2024-11-20 15:30:00', 'B034', 'Bidder #034', 'Outbid'),
(3, 67500.00, '2024-11-20 16:58:00', 'B018', 'Bidder #018', 'Winning');

-- Update winning information for sold item
UPDATE tax_deed_bidding_items 
SET 
    winning_bid = 67500.00,
    winning_bidder = 'Bidder #018',
    winning_bidder_number = 'B018',
    sale_confirmed = TRUE,
    total_bids = 4,
    unique_bidders = 4
WHERE id = 3;

-- Create a view for easy querying with property details
CREATE OR REPLACE VIEW tax_deed_items_view AS
SELECT 
    tdi.*,
    tda.auction_date,
    tda.auction_time,
    tda.description as auction_description,
    tda.auction_type,
    tda.online_platform,
    tda.platform_url,
    tda.deposit_required,
    tda.bid_increment,
    -- Calculate bid statistics
    CASE 
        WHEN tdi.current_bid > tdi.opening_bid THEN 
            ROUND(((tdi.current_bid - tdi.opening_bid) / tdi.opening_bid * 100), 2)
        ELSE 0 
    END as bid_increase_percentage,
    -- Time remaining (for active auctions)
    CASE 
        WHEN tdi.close_time > NOW() THEN 
            EXTRACT(EPOCH FROM (tdi.close_time - NOW()))
        ELSE 0 
    END as seconds_remaining
FROM tax_deed_bidding_items tdi
JOIN tax_deed_auctions tda ON tdi.auction_id = tda.id;

-- Grant permissions
GRANT ALL ON tax_deed_auctions TO anon, authenticated;
GRANT ALL ON tax_deed_bidding_items TO anon, authenticated;
GRANT ALL ON auction_bidding_history TO anon, authenticated;
GRANT ALL ON tax_deed_items_view TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;