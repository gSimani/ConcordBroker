-- Mortgage Analytics Database Schema for Supabase
-- Supports FRED PMMS rate tracking and loan amortization calculations

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: properties (extend existing or create new)
-- Stores property mortgage information
CREATE TABLE IF NOT EXISTS properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address TEXT NOT NULL,
    purchase_date DATE NOT NULL,
    orig_loan_amount NUMERIC(14,2) NOT NULL CHECK (orig_loan_amount > 0),
    loan_term_months INTEGER NOT NULL CHECK (loan_term_months > 0),
    loan_type TEXT NOT NULL CHECK (loan_type IN ('30Y_FIXED', '15Y_FIXED')),
    payment_start_date DATE,
    extra_principal_paid_to_date NUMERIC(14,2) DEFAULT 0 CHECK (extra_principal_paid_to_date >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for properties table
CREATE INDEX IF NOT EXISTS idx_properties_purchase_date ON properties(purchase_date);
CREATE INDEX IF NOT EXISTS idx_properties_loan_type ON properties(loan_type);

-- Table: mortgage_rates_monthly
-- Stores monthly average mortgage rates from FRED PMMS
CREATE TABLE IF NOT EXISTS mortgage_rates_monthly (
    yyyymm INTEGER NOT NULL,
    rate_type TEXT NOT NULL CHECK (rate_type IN ('30Y_FIXED', '15Y_FIXED')),
    avg_rate_pct NUMERIC(6,3) NOT NULL CHECK (avg_rate_pct >= 0 AND avg_rate_pct <= 30),
    source TEXT NOT NULL DEFAULT 'FRED_PMMS',
    asof_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (yyyymm, rate_type)
);

-- Create index for efficient rate lookups
CREATE INDEX IF NOT EXISTS idx_mortgage_rates_yyyymm ON mortgage_rates_monthly(yyyymm);

-- Table: loan_snapshots
-- Stores point-in-time loan calculations for properties
CREATE TABLE IF NOT EXISTS loan_snapshots (
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    scenario TEXT NOT NULL CHECK (scenario IN ('historical_origination_rate', 'current_market_rate')),
    annual_rate_pct NUMERIC(6,3) NOT NULL,
    monthly_payment NUMERIC(14,2) NOT NULL,
    remaining_balance NUMERIC(14,2) NOT NULL,
    months_elapsed INTEGER NOT NULL,
    pct_principal_paid NUMERIC(6,3) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (property_id, snapshot_date, scenario)
);

-- Create indexes for loan snapshots
CREATE INDEX IF NOT EXISTS idx_loan_snapshots_property_id ON loan_snapshots(property_id);
CREATE INDEX IF NOT EXISTS idx_loan_snapshots_scenario ON loan_snapshots(scenario);
CREATE INDEX IF NOT EXISTS idx_loan_snapshots_date ON loan_snapshots(snapshot_date);

-- Table: loan_amortization
-- Stores detailed amortization schedules
CREATE TABLE IF NOT EXISTS loan_amortization (
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    period_index INTEGER NOT NULL CHECK (period_index > 0),
    period_date DATE NOT NULL,
    payment NUMERIC(14,2) NOT NULL,
    interest NUMERIC(14,2) NOT NULL,
    principal NUMERIC(14,2) NOT NULL,
    extra_principal NUMERIC(14,2) DEFAULT 0,
    remaining_balance NUMERIC(14,2) NOT NULL,
    scenario TEXT NOT NULL CHECK (scenario IN ('historical_origination_rate', 'current_market_rate')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (property_id, period_index, scenario)
);

-- Create indexes for loan amortization
CREATE INDEX IF NOT EXISTS idx_loan_amortization_property_id ON loan_amortization(property_id);
CREATE INDEX IF NOT EXISTS idx_loan_amortization_scenario ON loan_amortization(scenario);
CREATE INDEX IF NOT EXISTS idx_loan_amortization_period_date ON loan_amortization(period_date);

-- Function: Update timestamps automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_properties_updated_at
    BEFORE UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mortgage_rates_monthly_updated_at
    BEFORE UPDATE ON mortgage_rates_monthly
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: Calculate loan metrics for a property
CREATE OR REPLACE FUNCTION calculate_loan_metrics(
    p_property_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    property_id UUID,
    orig_loan_amount NUMERIC,
    current_balance NUMERIC,
    pct_paid_off NUMERIC,
    months_elapsed INTEGER,
    monthly_payment NUMERIC,
    total_interest_paid NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ls.property_id,
        p.orig_loan_amount,
        ls.remaining_balance AS current_balance,
        ls.pct_principal_paid AS pct_paid_off,
        ls.months_elapsed,
        ls.monthly_payment,
        SUM(la.interest) AS total_interest_paid
    FROM loan_snapshots ls
    JOIN properties p ON p.id = ls.property_id
    LEFT JOIN loan_amortization la ON la.property_id = ls.property_id
        AND la.scenario = ls.scenario
        AND la.period_date <= p_as_of_date
    WHERE ls.property_id = p_property_id
        AND ls.scenario = 'historical_origination_rate'
        AND ls.snapshot_date = (
            SELECT MAX(snapshot_date)
            FROM loan_snapshots
            WHERE property_id = p_property_id
                AND scenario = 'historical_origination_rate'
                AND snapshot_date <= p_as_of_date
        )
    GROUP BY ls.property_id, p.orig_loan_amount, ls.remaining_balance,
             ls.pct_principal_paid, ls.months_elapsed, ls.monthly_payment;
END;
$$ LANGUAGE plpgsql;

-- Function: Get current market payment for a property
CREATE OR REPLACE FUNCTION get_current_market_payment(
    p_property_id UUID,
    p_rate_override NUMERIC DEFAULT NULL
)
RETURNS TABLE (
    property_id UUID,
    current_rate NUMERIC,
    monthly_payment NUMERIC,
    remaining_balance NUMERIC,
    remaining_months INTEGER
) AS $$
DECLARE
    v_current_rate NUMERIC;
    v_loan_type TEXT;
    v_current_yyyymm INTEGER;
BEGIN
    -- Get loan type
    SELECT loan_type INTO v_loan_type
    FROM properties
    WHERE id = p_property_id;

    -- Determine rate to use
    IF p_rate_override IS NOT NULL THEN
        v_current_rate := p_rate_override;
    ELSE
        -- Get latest rate from mortgage_rates_monthly
        v_current_yyyymm := EXTRACT(YEAR FROM CURRENT_DATE) * 100 + EXTRACT(MONTH FROM CURRENT_DATE);

        SELECT avg_rate_pct INTO v_current_rate
        FROM mortgage_rates_monthly
        WHERE yyyymm <= v_current_yyyymm
            AND rate_type = v_loan_type
        ORDER BY yyyymm DESC
        LIMIT 1;

        -- Default if no rate found
        IF v_current_rate IS NULL THEN
            v_current_rate := 6.5;
        END IF;
    END IF;

    -- Return calculated values
    RETURN QUERY
    SELECT
        ls.property_id,
        v_current_rate AS current_rate,
        ls.monthly_payment,
        ls.remaining_balance,
        p.loan_term_months - ls.months_elapsed AS remaining_months
    FROM loan_snapshots ls
    JOIN properties p ON p.id = ls.property_id
    WHERE ls.property_id = p_property_id
        AND ls.scenario = 'current_market_rate'
        AND ls.snapshot_date = (
            SELECT MAX(snapshot_date)
            FROM loan_snapshots
            WHERE property_id = p_property_id
                AND scenario = 'current_market_rate'
        );
END;
$$ LANGUAGE plpgsql;

-- View: Property loan summary
CREATE OR REPLACE VIEW v_property_loan_summary AS
SELECT
    p.id,
    p.address,
    p.purchase_date,
    p.orig_loan_amount,
    p.loan_term_months,
    p.loan_type,
    ls_hist.annual_rate_pct AS origination_rate,
    ls_hist.monthly_payment AS original_payment,
    ls_hist.remaining_balance AS current_balance,
    ls_hist.pct_principal_paid,
    ls_hist.months_elapsed,
    ls_curr.annual_rate_pct AS current_market_rate,
    ls_curr.monthly_payment AS current_market_payment,
    CASE
        WHEN ls_hist.monthly_payment > 0
        THEN ROUND((ls_curr.monthly_payment - ls_hist.monthly_payment) / ls_hist.monthly_payment * 100, 2)
        ELSE 0
    END AS payment_change_pct
FROM properties p
LEFT JOIN LATERAL (
    SELECT * FROM loan_snapshots
    WHERE property_id = p.id
        AND scenario = 'historical_origination_rate'
    ORDER BY snapshot_date DESC
    LIMIT 1
) ls_hist ON true
LEFT JOIN LATERAL (
    SELECT * FROM loan_snapshots
    WHERE property_id = p.id
        AND scenario = 'current_market_rate'
    ORDER BY snapshot_date DESC
    LIMIT 1
) ls_curr ON true;

-- Sample data insert for testing (commented out)
/*
-- Insert sample FRED PMMS rates
INSERT INTO mortgage_rates_monthly (yyyymm, rate_type, avg_rate_pct, source, asof_date) VALUES
    (202301, '30Y_FIXED', 6.42, 'FRED_PMMS', '2023-01-31'),
    (202302, '30Y_FIXED', 6.50, 'FRED_PMMS', '2023-02-28'),
    (202303, '30Y_FIXED', 6.54, 'FRED_PMMS', '2023-03-31'),
    (202401, '30Y_FIXED', 6.62, 'FRED_PMMS', '2024-01-31'),
    (202402, '30Y_FIXED', 6.78, 'FRED_PMMS', '2024-02-29'),
    (202403, '30Y_FIXED', 6.79, 'FRED_PMMS', '2024-03-31'),
    (202301, '15Y_FIXED', 5.56, 'FRED_PMMS', '2023-01-31'),
    (202302, '15Y_FIXED', 5.61, 'FRED_PMMS', '2023-02-28'),
    (202303, '15Y_FIXED', 5.67, 'FRED_PMMS', '2023-03-31');

-- Insert sample property
INSERT INTO properties (
    id, address, purchase_date, orig_loan_amount,
    loan_term_months, loan_type, payment_start_date
) VALUES (
    uuid_generate_v4(),
    '123 Main St, Miami, FL 33101',
    '2023-01-15',
    400000.00,
    360,
    '30Y_FIXED',
    '2023-02-01'
);
*/

-- Grant necessary permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Enable Row Level Security (optional, adjust as needed)
-- ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE loan_snapshots ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE loan_amortization ENABLE ROW LEVEL SECURITY;