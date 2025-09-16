-- Create Missing Tables for Property Data
-- Run this in Supabase SQL Editor

-- 1. Permits Table
CREATE TABLE IF NOT EXISTS permits (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  permit_number VARCHAR(50) UNIQUE,
  permit_type VARCHAR(100),
  description TEXT,
  issue_date DATE,
  expiration_date DATE,
  status VARCHAR(50),
  contractor VARCHAR(200),
  estimated_cost DECIMAL(12,2),
  actual_cost DECIMAL(12,2),
  inspection_status VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_permits_parcel_id ON permits(parcel_id);
CREATE INDEX idx_permits_issue_date ON permits(issue_date);
CREATE INDEX idx_permits_status ON permits(status);

-- 2. Foreclosure Cases Table
CREATE TABLE IF NOT EXISTS foreclosure_cases (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  case_number VARCHAR(50) UNIQUE,
  filing_date DATE,
  case_status VARCHAR(50),
  case_type VARCHAR(100),
  plaintiff VARCHAR(200),
  defendant VARCHAR(200),
  amount DECIMAL(12,2),
  attorney VARCHAR(200),
  court VARCHAR(100),
  auction_date DATE,
  sale_amount DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_foreclosure_parcel_id ON foreclosure_cases(parcel_id);
CREATE INDEX idx_foreclosure_filing_date ON foreclosure_cases(filing_date);
CREATE INDEX idx_foreclosure_case_status ON foreclosure_cases(case_status);

-- 3. Tax Deed Bidding Items Table
CREATE TABLE IF NOT EXISTS tax_deed_bidding_items (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  certificate_number VARCHAR(50),
  auction_date DATE,
  auction_type VARCHAR(50),
  minimum_bid DECIMAL(12,2),
  winning_bid DECIMAL(12,2),
  bidder_name VARCHAR(200),
  bidder_number VARCHAR(50),
  item_status VARCHAR(50),
  deposit_amount DECIMAL(12,2),
  balance_due DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tax_deed_parcel_id ON tax_deed_bidding_items(parcel_id);
CREATE INDEX idx_tax_deed_auction_date ON tax_deed_bidding_items(auction_date);
CREATE INDEX idx_tax_deed_status ON tax_deed_bidding_items(item_status);

-- 4. Tax Lien Certificates Table
CREATE TABLE IF NOT EXISTS tax_lien_certificates (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  certificate_number VARCHAR(50) UNIQUE,
  tax_year INTEGER,
  certificate_date DATE,
  amount DECIMAL(12,2),
  interest_rate DECIMAL(5,2),
  redemption_date DATE,
  redemption_amount DECIMAL(12,2),
  status VARCHAR(50),
  certificate_holder VARCHAR(200),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tax_lien_parcel_id ON tax_lien_certificates(parcel_id);
CREATE INDEX idx_tax_lien_tax_year ON tax_lien_certificates(tax_year);
CREATE INDEX idx_tax_lien_status ON tax_lien_certificates(status);

-- 5. Property Sales History Table (if not exists)
CREATE TABLE IF NOT EXISTS property_sales_history (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  sale_date DATE,
  sale_price DECIMAL(12,2),
  sale_type VARCHAR(100),
  sale_qualification VARCHAR(50),
  grantor VARCHAR(200),
  grantee VARCHAR(200),
  book_page VARCHAR(50),
  cin VARCHAR(50),
  instrument_number VARCHAR(50),
  verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sales_history_parcel_id ON property_sales_history(parcel_id);
CREATE INDEX idx_sales_history_sale_date ON property_sales_history(sale_date);
CREATE INDEX idx_sales_history_sale_price ON property_sales_history(sale_price);

-- 6. NAV Assessments Table (if not exists)
CREATE TABLE IF NOT EXISTS nav_assessments (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  year INTEGER,
  just_value DECIMAL(12,2),
  assessed_value DECIMAL(12,2),
  taxable_value DECIMAL(12,2),
  land_value DECIMAL(12,2),
  building_value DECIMAL(12,2),
  exemptions DECIMAL(12,2),
  millage_rate DECIMAL(8,4),
  taxes_due DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_nav_parcel_id ON nav_assessments(parcel_id);
CREATE INDEX idx_nav_year ON nav_assessments(year);

-- 7. Sunbiz Corporate Table (if not exists)
CREATE TABLE IF NOT EXISTS sunbiz_corporate (
  id SERIAL PRIMARY KEY,
  document_number VARCHAR(50) UNIQUE,
  corporate_name VARCHAR(500),
  status VARCHAR(50),
  filing_date DATE,
  state VARCHAR(2),
  corporate_type VARCHAR(100),
  principal_address TEXT,
  mailing_address TEXT,
  registered_agent_name VARCHAR(200),
  registered_agent_address TEXT,
  officers JSONB,
  annual_report_date DATE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sunbiz_document_number ON sunbiz_corporate(document_number);
CREATE INDEX idx_sunbiz_corporate_name ON sunbiz_corporate(corporate_name);
CREATE INDEX idx_sunbiz_officers ON sunbiz_corporate USING GIN(officers);

-- 8. Property Comparables Table
CREATE TABLE IF NOT EXISTS property_comparables (
  id SERIAL PRIMARY KEY,
  subject_parcel_id VARCHAR(20),
  comp_parcel_id VARCHAR(20),
  distance_miles DECIMAL(5,2),
  similarity_score DECIMAL(5,2),
  sale_date DATE,
  sale_price DECIMAL(12,2),
  price_per_sqft DECIMAL(10,2),
  year_built INTEGER,
  living_area INTEGER,
  lot_size INTEGER,
  bedrooms INTEGER,
  bathrooms DECIMAL(3,1),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comparables_subject ON property_comparables(subject_parcel_id);
CREATE INDEX idx_comparables_similarity ON property_comparables(similarity_score DESC);

-- 9. Market Analysis Table
CREATE TABLE IF NOT EXISTS market_analysis (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  analysis_date DATE,
  estimated_value DECIMAL(12,2),
  value_trend VARCHAR(20),
  days_on_market INTEGER,
  price_per_sqft DECIMAL(10,2),
  neighborhood_avg_price DECIMAL(12,2),
  neighborhood_trend VARCHAR(20),
  rental_estimate DECIMAL(10,2),
  cap_rate DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_market_analysis_parcel ON market_analysis(parcel_id);
CREATE INDEX idx_market_analysis_date ON market_analysis(analysis_date);

-- 10. Property Notifications Table
CREATE TABLE IF NOT EXISTS property_notifications (
  id SERIAL PRIMARY KEY,
  parcel_id VARCHAR(20),
  notification_type VARCHAR(100),
  title VARCHAR(200),
  message TEXT,
  priority VARCHAR(20),
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  read_at TIMESTAMP
);

CREATE INDEX idx_notifications_parcel ON property_notifications(parcel_id);
CREATE INDEX idx_notifications_unread ON property_notifications(is_read) WHERE is_read = FALSE;

-- Grant permissions (adjust based on your Supabase setup)
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Add RLS policies if needed
ALTER TABLE permits ENABLE ROW LEVEL SECURITY;
ALTER TABLE foreclosure_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_deed_bidding_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_lien_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_sales_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE nav_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_comparables ENABLE ROW LEVEL SECURITY;
ALTER TABLE market_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_notifications ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for read access
CREATE POLICY "Enable read access for all users" ON permits FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON foreclosure_cases FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON tax_deed_bidding_items FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON tax_lien_certificates FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON property_sales_history FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON nav_assessments FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON sunbiz_corporate FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON property_comparables FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON market_analysis FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON property_notifications FOR SELECT USING (true);