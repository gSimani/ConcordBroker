-- Florida Department of Revenue Land Use Codes Table
-- Based on 2024 NAL Users Guide
-- https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2024%20Users%20guide%20and%20quick%20reference/2024_NAL_SDF_NAP_Users_Guide.pdf

-- Drop existing table if it exists
DROP TABLE IF EXISTS public.dor_use_codes CASCADE;

-- Create the DOR use codes table
CREATE TABLE public.dor_use_codes (
    code CHAR(3) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    description TEXT NOT NULL,
    color_class VARCHAR(50),
    bg_color_class VARCHAR(50),
    border_color_class VARCHAR(50),
    is_residential BOOLEAN DEFAULT FALSE,
    is_commercial BOOLEAN DEFAULT FALSE,
    is_industrial BOOLEAN DEFAULT FALSE,
    is_agricultural BOOLEAN DEFAULT FALSE,
    is_institutional BOOLEAN DEFAULT FALSE,
    is_governmental BOOLEAN DEFAULT FALSE,
    is_vacant BOOLEAN DEFAULT FALSE,
    typical_use TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient lookups
CREATE INDEX idx_dor_use_codes_category ON public.dor_use_codes(category);
CREATE INDEX idx_dor_use_codes_subcategory ON public.dor_use_codes(subcategory);
CREATE INDEX idx_dor_use_codes_is_residential ON public.dor_use_codes(is_residential) WHERE is_residential = TRUE;
CREATE INDEX idx_dor_use_codes_is_commercial ON public.dor_use_codes(is_commercial) WHERE is_commercial = TRUE;
CREATE INDEX idx_dor_use_codes_is_vacant ON public.dor_use_codes(is_vacant) WHERE is_vacant = TRUE;

-- Add comments for documentation
COMMENT ON TABLE public.dor_use_codes IS 'Florida Department of Revenue Land Use Codes - Official classification system for property types';
COMMENT ON COLUMN public.dor_use_codes.code IS 'Three-digit DOR use code (000-099)';
COMMENT ON COLUMN public.dor_use_codes.category IS 'Main category (Residential, Commercial, Industrial, etc.)';
COMMENT ON COLUMN public.dor_use_codes.subcategory IS 'Specific subcategory within the main category';
COMMENT ON COLUMN public.dor_use_codes.description IS 'Official description from DOR guidelines';

-- Enable Row Level Security
ALTER TABLE public.dor_use_codes ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow public read access (these are public codes)
CREATE POLICY "Allow public read access to DOR codes"
    ON public.dor_use_codes
    FOR SELECT
    TO public
    USING (true);

-- Create a function to get DOR use code details
CREATE OR REPLACE FUNCTION public.get_dor_use_code(p_code TEXT)
RETURNS TABLE (
    code CHAR(3),
    category VARCHAR(50),
    subcategory VARCHAR(50),
    description TEXT,
    is_residential BOOLEAN,
    is_commercial BOOLEAN,
    is_industrial BOOLEAN,
    is_agricultural BOOLEAN,
    is_vacant BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Pad the code with zeros if needed
    p_code := LPAD(p_code::TEXT, 3, '0');

    RETURN QUERY
    SELECT
        d.code,
        d.category,
        d.subcategory,
        d.description,
        d.is_residential,
        d.is_commercial,
        d.is_industrial,
        d.is_agricultural,
        d.is_vacant
    FROM public.dor_use_codes d
    WHERE d.code = p_code;
END;
$$;

-- Create a function to categorize property by code
CREATE OR REPLACE FUNCTION public.categorize_property_by_dor_code(p_code TEXT)
RETURNS VARCHAR(50)
LANGUAGE plpgsql
AS $$
DECLARE
    v_category VARCHAR(50);
BEGIN
    -- Pad the code with zeros if needed
    p_code := LPAD(p_code::TEXT, 3, '0');

    SELECT category INTO v_category
    FROM public.dor_use_codes
    WHERE code = p_code;

    RETURN COALESCE(v_category, 'Unknown');
END;
$$;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_dor_use_codes_updated_at
    BEFORE UPDATE ON public.dor_use_codes
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();