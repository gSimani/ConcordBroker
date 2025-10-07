-- Capital Planning System for ConcordBroker
-- Stores custom capital expense plans per property with property-type-specific templates

-- =====================================================
-- Table: capital_expense_templates
-- Stores predefined templates for different property types
-- =====================================================
CREATE TABLE IF NOT EXISTS capital_expense_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  template_name TEXT NOT NULL,
  property_type TEXT NOT NULL, -- RESIDENTIAL, COMMERCIAL, INDUSTRIAL, HOTEL, CHURCH, etc.
  category TEXT NOT NULL, -- Roof, HVAC, etc.
  icon TEXT DEFAULT 'Building',
  lifecycle_years INTEGER NOT NULL CHECK (lifecycle_years > 0),
  cost_per_sqft DECIMAL(10, 2),
  cost_per_unit DECIMAL(12, 2),
  priority TEXT CHECK (priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
  description TEXT,
  applicable_dor_codes TEXT[], -- Array of DOR use codes this applies to
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups by property type
CREATE INDEX idx_capital_templates_property_type ON capital_expense_templates(property_type);
CREATE INDEX idx_capital_templates_dor_codes ON capital_expense_templates USING GIN(applicable_dor_codes);

-- =====================================================
-- Table: property_capital_plans
-- Main table for storing capital plans per property
-- =====================================================
CREATE TABLE IF NOT EXISTS property_capital_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parcel_id TEXT NOT NULL,
  county TEXT NOT NULL,
  property_type TEXT NOT NULL,
  dor_use_code TEXT,
  planning_timeframe INTEGER DEFAULT 5 CHECK (planning_timeframe IN (5, 10, 15, 20)),
  total_reserves_needed DECIMAL(12, 2) DEFAULT 0,
  annual_contribution DECIMAL(12, 2) DEFAULT 0,
  monthly_contribution DECIMAL(12, 2) DEFAULT 0,
  current_reserve_balance DECIMAL(12, 2) DEFAULT 0,
  property_age INTEGER,
  property_sqft DECIMAL(10, 2),
  property_value DECIMAL(12, 2),
  created_by TEXT, -- User ID or system
  last_updated_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Ensure one plan per property
  CONSTRAINT unique_property_plan UNIQUE (parcel_id, county)
);

-- Indexes for property lookup
CREATE INDEX idx_capital_plans_parcel ON property_capital_plans(parcel_id, county);
CREATE INDEX idx_capital_plans_property_type ON property_capital_plans(property_type);
CREATE INDEX idx_capital_plans_updated ON property_capital_plans(updated_at DESC);

-- =====================================================
-- Table: capital_expense_items
-- Individual expense items within a capital plan
-- =====================================================
CREATE TABLE IF NOT EXISTS capital_expense_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  capital_plan_id UUID NOT NULL REFERENCES property_capital_plans(id) ON DELETE CASCADE,
  template_id UUID REFERENCES capital_expense_templates(id) ON DELETE SET NULL,
  category TEXT NOT NULL,
  icon TEXT DEFAULT 'Building',
  lifecycle_years INTEGER NOT NULL CHECK (lifecycle_years > 0),
  last_replaced_year INTEGER,
  replacement_year INTEGER,
  remaining_life_years INTEGER,
  cost_per_sqft DECIMAL(10, 2),
  cost_per_unit DECIMAL(12, 2),
  estimated_cost DECIMAL(12, 2) NOT NULL,
  actual_cost DECIMAL(12, 2), -- Filled when expense is completed
  priority TEXT CHECK (priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
  condition TEXT CHECK (condition IN ('good', 'fair', 'poor', 'unknown')) DEFAULT 'good',
  urgency TEXT CHECK (urgency IN ('immediate', 'soon', 'future')) DEFAULT 'future',
  status TEXT CHECK (status IN ('planned', 'in_progress', 'completed', 'deferred', 'cancelled')) DEFAULT 'planned',
  notes TEXT,
  is_custom BOOLEAN DEFAULT false, -- True if user-created, false if from template
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for expense items
CREATE INDEX idx_capital_items_plan ON capital_expense_items(capital_plan_id);
CREATE INDEX idx_capital_items_replacement_year ON capital_expense_items(replacement_year);
CREATE INDEX idx_capital_items_urgency ON capital_expense_items(urgency);
CREATE INDEX idx_capital_items_status ON capital_expense_items(status);

-- =====================================================
-- Table: capital_expense_history
-- Tracks changes and actual expenses over time
-- =====================================================
CREATE TABLE IF NOT EXISTS capital_expense_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  expense_item_id UUID NOT NULL REFERENCES capital_expense_items(id) ON DELETE CASCADE,
  action TEXT NOT NULL, -- 'created', 'updated', 'completed', 'deferred'
  previous_cost DECIMAL(12, 2),
  new_cost DECIMAL(12, 2),
  previous_year INTEGER,
  new_year INTEGER,
  changed_by TEXT,
  change_reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for history tracking
CREATE INDEX idx_capital_history_item ON capital_expense_history(expense_item_id);
CREATE INDEX idx_capital_history_date ON capital_expense_history(created_at DESC);

-- =====================================================
-- Table: reserve_fund_transactions
-- Tracks reserve fund deposits and withdrawals
-- =====================================================
CREATE TABLE IF NOT EXISTS reserve_fund_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  capital_plan_id UUID NOT NULL REFERENCES property_capital_plans(id) ON DELETE CASCADE,
  transaction_type TEXT NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'adjustment')),
  amount DECIMAL(12, 2) NOT NULL,
  transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
  related_expense_id UUID REFERENCES capital_expense_items(id) ON DELETE SET NULL,
  description TEXT,
  balance_after DECIMAL(12, 2),
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for transactions
CREATE INDEX idx_reserve_transactions_plan ON reserve_fund_transactions(capital_plan_id);
CREATE INDEX idx_reserve_transactions_date ON reserve_fund_transactions(transaction_date DESC);

-- =====================================================
-- Trigger: Update timestamps
-- =====================================================
CREATE OR REPLACE FUNCTION update_capital_planning_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_capital_templates_timestamp
  BEFORE UPDATE ON capital_expense_templates
  FOR EACH ROW EXECUTE FUNCTION update_capital_planning_timestamp();

CREATE TRIGGER update_capital_plans_timestamp
  BEFORE UPDATE ON property_capital_plans
  FOR EACH ROW EXECUTE FUNCTION update_capital_planning_timestamp();

CREATE TRIGGER update_capital_items_timestamp
  BEFORE UPDATE ON capital_expense_items
  FOR EACH ROW EXECUTE FUNCTION update_capital_planning_timestamp();

-- =====================================================
-- Function: Calculate remaining life and urgency
-- =====================================================
CREATE OR REPLACE FUNCTION calculate_expense_urgency()
RETURNS TRIGGER AS $$
DECLARE
  current_year INTEGER := EXTRACT(YEAR FROM CURRENT_DATE);
BEGIN
  -- Calculate remaining life
  IF NEW.last_replaced_year IS NOT NULL THEN
    NEW.remaining_life_years := NEW.lifecycle_years - (current_year - NEW.last_replaced_year);
    NEW.replacement_year := NEW.last_replaced_year + NEW.lifecycle_years;
  ELSE
    NEW.remaining_life_years := NEW.lifecycle_years;
    NEW.replacement_year := current_year + NEW.lifecycle_years;
  END IF;

  -- Ensure remaining life is not negative
  IF NEW.remaining_life_years < 0 THEN
    NEW.remaining_life_years := 0;
  END IF;

  -- Calculate urgency
  IF NEW.remaining_life_years <= 2 THEN
    NEW.urgency := 'immediate';
  ELSIF NEW.remaining_life_years <= 5 THEN
    NEW.urgency := 'soon';
  ELSE
    NEW.urgency := 'future';
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_expense_urgency_trigger
  BEFORE INSERT OR UPDATE ON capital_expense_items
  FOR EACH ROW EXECUTE FUNCTION calculate_expense_urgency();

-- =====================================================
-- Function: Update reserve fund balance
-- =====================================================
CREATE OR REPLACE FUNCTION update_reserve_fund_balance()
RETURNS TRIGGER AS $$
BEGIN
  -- Update the capital plan's current reserve balance
  UPDATE property_capital_plans
  SET current_reserve_balance = (
    SELECT COALESCE(SUM(
      CASE
        WHEN transaction_type = 'deposit' THEN amount
        WHEN transaction_type = 'withdrawal' THEN -amount
        ELSE amount
      END
    ), 0)
    FROM reserve_fund_transactions
    WHERE capital_plan_id = NEW.capital_plan_id
  )
  WHERE id = NEW.capital_plan_id;

  -- Store balance after transaction
  NEW.balance_after := (
    SELECT current_reserve_balance
    FROM property_capital_plans
    WHERE id = NEW.capital_plan_id
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_reserve_balance_trigger
  BEFORE INSERT ON reserve_fund_transactions
  FOR EACH ROW EXECUTE FUNCTION update_reserve_fund_balance();

-- =====================================================
-- Seed Data: Default Templates
-- =====================================================

-- Residential Templates
INSERT INTO capital_expense_templates (template_name, property_type, category, icon, lifecycle_years, cost_per_sqft, cost_per_unit, priority, applicable_dor_codes, description) VALUES
('Residential Roof', 'RESIDENTIAL', 'Roof', 'Building', 20, 8.00, NULL, 'high', ARRAY['001', '002', '004', '005', '006', '007', '008'], 'Asphalt shingle or tile roof replacement'),
('Residential HVAC', 'RESIDENTIAL', 'HVAC System', 'Wind', 15, NULL, 7000.00, 'high', ARRAY['001', '002', '004', '005', '006', '007', '008'], 'Central air conditioning and heating system'),
('Exterior Paint', 'RESIDENTIAL', 'Exterior Paint', 'Paintbrush', 10, 3.00, NULL, 'medium', ARRAY['001', '004', '005', '006', '007', '008'], 'Complete exterior painting'),
('Flooring', 'RESIDENTIAL', 'Flooring', 'Hammer', 15, 5.00, NULL, 'medium', ARRAY['001', '004', '005', '006', '007', '008'], 'Carpet, tile, or hardwood replacement'),
('Plumbing System', 'RESIDENTIAL', 'Plumbing', 'Droplets', 30, NULL, 10000.00, 'low', ARRAY['001', '002', '004', '005', '006', '007', '008'], 'Water heater and plumbing fixtures'),
('Electrical System', 'RESIDENTIAL', 'Electrical', 'Zap', 30, NULL, 8000.00, 'low', ARRAY['001', '002', '004', '005', '006', '007', '008'], 'Panel upgrade and rewiring'),
('Windows', 'RESIDENTIAL', 'Windows', 'Shield', 20, NULL, 15000.00, 'medium', ARRAY['001', '004', '005', '006', '007', '008'], 'Energy-efficient window replacement'),
('Appliances', 'RESIDENTIAL', 'Appliances', 'Settings', 10, NULL, 5000.00, 'medium', ARRAY['001', '004', '005', '006', '007', '008'], 'Kitchen and laundry appliances');

-- Commercial Templates
INSERT INTO capital_expense_templates (template_name, property_type, category, icon, lifecycle_years, cost_per_sqft, cost_per_unit, priority, applicable_dor_codes, description) VALUES
('Commercial Roof System', 'COMMERCIAL', 'Commercial Roof System', 'Building', 25, 12.00, NULL, 'high', ARRAY['003', '011', '012', '013', '014', '015', '016', '017', '018', '019'], 'TPO, EPDM, or modified bitumen roofing'),
('Commercial HVAC', 'COMMERCIAL', 'Commercial HVAC', 'Wind', 20, NULL, 25000.00, 'high', ARRAY['003', '011', '012', '013', '014', '015', '016', '017', '018', '019'], 'Commercial rooftop or central HVAC'),
('Parking Lot', 'COMMERCIAL', 'Parking Lot/Asphalt', 'Building', 15, 4.00, NULL, 'high', ARRAY['011', '012', '013', '014', '015', '016', '017', '018', '019'], 'Asphalt resurfacing and striping'),
('Elevator System', 'COMMERCIAL', 'Elevator System', 'Settings', 25, NULL, 50000.00, 'high', ARRAY['013', '015', '018'], 'Elevator modernization or replacement'),
('Fire Safety', 'COMMERCIAL', 'Fire Safety Systems', 'Shield', 20, NULL, 20000.00, 'high', ARRAY['003', '011', '012', '013', '014', '015', '016', '017', '018', '019'], 'Sprinkler and alarm systems'),
('Building Facade', 'COMMERCIAL', 'Building Facade', 'Building', 30, 15.00, NULL, 'medium', ARRAY['013', '015', '017', '018'], 'Exterior facade repair and painting');

-- Industrial Templates
INSERT INTO capital_expense_templates (template_name, property_type, category, icon, lifecycle_years, cost_per_sqft, cost_per_unit, priority, applicable_dor_codes, description) VALUES
('Industrial Roof', 'INDUSTRIAL', 'Industrial Roof', 'Building', 30, 15.00, NULL, 'high', ARRAY['041', '042', '043', '044', '045', '046', '047', '048'], 'Metal or single-ply membrane roofing'),
('Industrial HVAC', 'INDUSTRIAL', 'Industrial HVAC/Ventilation', 'Wind', 25, NULL, 50000.00, 'high', ARRAY['041', '042', '043', '044', '045', '046', '047', '048'], 'Industrial ventilation and climate control'),
('Loading Dock', 'INDUSTRIAL', 'Loading Dock Equipment', 'Building', 20, NULL, 30000.00, 'high', ARRAY['048'], 'Dock levelers, doors, and seals'),
('Floor Coating', 'INDUSTRIAL', 'Epoxy Floor Coating', 'Hammer', 10, 6.00, NULL, 'medium', ARRAY['041', '042', '048'], 'Industrial epoxy or urethane flooring');

-- Hotel Templates
INSERT INTO capital_expense_templates (template_name, property_type, category, icon, lifecycle_years, cost_per_sqft, cost_per_unit, priority, applicable_dor_codes, description) VALUES
('Hotel Roof', 'HOTEL', 'Hotel Roof', 'Building', 20, 10.00, NULL, 'high', ARRAY['039'], 'Commercial roofing for hospitality'),
('Guest Room HVAC', 'HOTEL', 'Guest Room HVAC Units', 'Wind', 15, NULL, 35000.00, 'high', ARRAY['039'], 'PTAC or split system units'),
('Hotel Elevators', 'HOTEL', 'Passenger Elevators', 'Settings', 25, NULL, 60000.00, 'high', ARRAY['039'], 'Guest and service elevators'),
('Pool & Spa', 'HOTEL', 'Pool & Spa Equipment', 'Droplets', 15, NULL, 25000.00, 'medium', ARRAY['039'], 'Pool pumps, heaters, and finishes'),
('FF&E', 'HOTEL', 'Furniture, Fixtures & Equipment', 'Settings', 7, NULL, 150000.00, 'high', ARRAY['039'], 'Guest room and common area furnishings');

-- Church/Institutional Templates
INSERT INTO capital_expense_templates (template_name, property_type, category, icon, lifecycle_years, cost_per_sqft, cost_per_unit, priority, applicable_dor_codes, description) VALUES
('Church Roof', 'CHURCH', 'Church Roof', 'Building', 25, 12.00, NULL, 'high', ARRAY['071'], 'Traditional or contemporary roofing'),
('Sanctuary HVAC', 'CHURCH', 'Sanctuary HVAC', 'Wind', 20, NULL, 40000.00, 'high', ARRAY['071'], 'Large-space climate control'),
('Audio/Visual', 'CHURCH', 'Audio/Visual System', 'Settings', 10, NULL, 50000.00, 'medium', ARRAY['071'], 'Sound, projection, and streaming equipment'),
('Seating', 'CHURCH', 'Pews/Seating', 'Building', 30, NULL, 30000.00, 'low', ARRAY['071'], 'Pew or chair replacement');

-- =====================================================
-- Row Level Security (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE capital_expense_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE property_capital_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE capital_expense_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE capital_expense_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE reserve_fund_transactions ENABLE ROW LEVEL SECURITY;

-- Public read access to templates
CREATE POLICY "Templates are viewable by everyone"
  ON capital_expense_templates FOR SELECT
  USING (true);

-- Authenticated users can create/update templates (admins only in production)
CREATE POLICY "Authenticated users can manage templates"
  ON capital_expense_templates FOR ALL
  USING (auth.role() = 'authenticated');

-- Users can view all capital plans (adjust for multi-tenancy as needed)
CREATE POLICY "Capital plans are viewable by authenticated users"
  ON property_capital_plans FOR SELECT
  USING (auth.role() = 'authenticated');

-- Users can create/update capital plans
CREATE POLICY "Authenticated users can manage capital plans"
  ON property_capital_plans FOR ALL
  USING (auth.role() = 'authenticated');

-- Users can view expense items for their accessible plans
CREATE POLICY "Expense items are viewable by authenticated users"
  ON capital_expense_items FOR SELECT
  USING (auth.role() = 'authenticated');

-- Users can manage expense items
CREATE POLICY "Authenticated users can manage expense items"
  ON capital_expense_items FOR ALL
  USING (auth.role() = 'authenticated');

-- History and transactions follow same pattern
CREATE POLICY "History is viewable by authenticated users"
  ON capital_expense_history FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Transactions are viewable by authenticated users"
  ON reserve_fund_transactions FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can manage transactions"
  ON reserve_fund_transactions FOR ALL
  USING (auth.role() = 'authenticated');

-- =====================================================
-- Helpful Views
-- =====================================================

-- View: Complete capital plan with all expenses
CREATE OR REPLACE VIEW v_property_capital_plans_complete AS
SELECT
  pcp.*,
  COUNT(cei.id) as total_expense_items,
  COUNT(cei.id) FILTER (WHERE cei.urgency = 'immediate') as immediate_items,
  COUNT(cei.id) FILTER (WHERE cei.urgency = 'soon') as soon_items,
  SUM(cei.estimated_cost) FILTER (WHERE cei.urgency = 'immediate') as immediate_cost,
  SUM(cei.estimated_cost) FILTER (WHERE cei.urgency = 'soon') as soon_cost,
  SUM(cei.estimated_cost) as total_estimated_cost
FROM property_capital_plans pcp
LEFT JOIN capital_expense_items cei ON cei.capital_plan_id = pcp.id
WHERE cei.status NOT IN ('completed', 'cancelled') OR cei.status IS NULL
GROUP BY pcp.id;

-- View: Upcoming expenses by property
CREATE OR REPLACE VIEW v_upcoming_capital_expenses AS
SELECT
  pcp.parcel_id,
  pcp.county,
  pcp.property_type,
  cei.category,
  cei.replacement_year,
  cei.remaining_life_years,
  cei.estimated_cost,
  cei.urgency,
  cei.priority,
  cei.condition
FROM property_capital_plans pcp
JOIN capital_expense_items cei ON cei.capital_plan_id = pcp.id
WHERE cei.status = 'planned'
  AND cei.replacement_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 10
ORDER BY cei.replacement_year, cei.urgency DESC;

-- Grant permissions on views
GRANT SELECT ON v_property_capital_plans_complete TO authenticated;
GRANT SELECT ON v_upcoming_capital_expenses TO authenticated;

-- =====================================================
-- Comments for Documentation
-- =====================================================

COMMENT ON TABLE capital_expense_templates IS 'Predefined capital expense templates categorized by property type and DOR use codes';
COMMENT ON TABLE property_capital_plans IS 'Master capital planning records per property with financial summaries';
COMMENT ON TABLE capital_expense_items IS 'Individual capital expense line items within property plans';
COMMENT ON TABLE capital_expense_history IS 'Audit trail of all changes to capital expense items';
COMMENT ON TABLE reserve_fund_transactions IS 'Reserve fund deposit/withdrawal tracking with running balances';
