-- Florida RealAuction Sites Migration
-- Created: 2025-01-05
-- Purpose: Store foreclosure and tax-deed auction site information for all Florida counties

-- Create auction_sites table
CREATE TABLE IF NOT EXISTS public.auction_sites (
    id BIGSERIAL PRIMARY KEY,
    county TEXT NOT NULL UNIQUE,

    -- Foreclosure auction information
    foreclosure_url TEXT,
    has_foreclosure BOOLEAN NOT NULL DEFAULT false,

    -- Tax deed auction information
    tax_deed_url TEXT,
    has_tax_deed BOOLEAN NOT NULL DEFAULT false,

    -- Site configuration
    site_type TEXT NOT NULL CHECK (site_type IN ('separate', 'combined', 'foreclosure_only', 'tax_deed_only', 'coming_soon')),
    platform_family TEXT NOT NULL DEFAULT 'RealAuction',

    -- Login information (same for all RealAuction sites)
    login_location TEXT NOT NULL DEFAULT 'Upper-left corner beneath county banner',
    login_fields JSONB NOT NULL DEFAULT '{"username_field": "User Name", "password_field": "User Password", "submit_button": "Submit"}'::jsonb,

    -- Additional metadata
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_verified_at TIMESTAMPTZ,

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_auction_sites_county ON public.auction_sites(county);
CREATE INDEX IF NOT EXISTS idx_auction_sites_has_foreclosure ON public.auction_sites(has_foreclosure) WHERE has_foreclosure = true;
CREATE INDEX IF NOT EXISTS idx_auction_sites_has_tax_deed ON public.auction_sites(has_tax_deed) WHERE has_tax_deed = true;
CREATE INDEX IF NOT EXISTS idx_auction_sites_site_type ON public.auction_sites(site_type);
CREATE INDEX IF NOT EXISTS idx_auction_sites_is_active ON public.auction_sites(is_active) WHERE is_active = true;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION public.update_auction_sites_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auction_sites_updated_at
    BEFORE UPDATE ON public.auction_sites
    FOR EACH ROW
    EXECUTE FUNCTION public.update_auction_sites_updated_at();

-- Insert all 47 Florida counties
INSERT INTO public.auction_sites (county, foreclosure_url, tax_deed_url, site_type, has_foreclosure, has_tax_deed, notes) VALUES
('ALACHUA', 'https://alachua.realforeclose.com', 'https://alachua.realtaxdeed.com', 'separate', true, true, 'Separate sites for foreclosure and tax‑deed sales'),
('BAKER', NULL, 'https://baker.realtaxdeed.com', 'tax_deed_only', false, true, 'Only tax‑deed auctions'),
('BAY', 'https://bay.realforeclose.com', 'https://bay.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('BREVARD', NULL, 'https://brevard.realforeclose.com', 'tax_deed_only', false, true, 'RealAuction hosts only tax‑deed auctions for Brevard on the RealForeclose domain'),
('BROWARD', 'https://broward.realforeclose.com', NULL, 'foreclosure_only', true, false, 'Broward uses RealAuction only for foreclosure sales'),
('CALHOUN', 'https://calhoun.realforeclose.com', 'https://calhoun.realforeclose.com', 'combined', true, true, 'Combined site for foreclosure and tax‑deed sales'),
('CHARLOTTE', 'https://charlotte.realforeclose.com', 'https://charlotte.realforeclose.com', 'combined', true, true, 'Combined site'),
('CITRUS', 'https://citrus.realforeclose.com', 'https://citrus.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('CLAY', 'https://clay.realforeclose.com', 'https://clay.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('COLUMBIA', NULL, NULL, 'coming_soon', false, false, 'Sites not active yet - coming soon'),
('DUVAL', 'https://duval.realforeclose.com', 'https://duval.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('ESCAMBIA', 'https://escambia.realforeclose.com', 'https://escambia.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('FLAGLER', 'https://flagler.realforeclose.com', 'https://flagler.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('GILCHRIST', 'https://gilchrist.realforeclose.com', 'https://gilchrist.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('GULF', 'https://gulf.realforeclose.com', 'https://gulf.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('HENDRY', NULL, 'https://hendry.realtaxdeed.com', 'tax_deed_only', false, true, 'Only tax‑deed auctions'),
('HERNANDO', NULL, 'https://hernando.realtaxdeed.com', 'tax_deed_only', false, true, 'Only tax‑deed auctions'),
('HIGHLANDS', NULL, 'https://highlands.realtaxdeed.com', 'tax_deed_only', false, true, 'Only tax‑deed auctions'),
('HILLSBOROUGH', 'https://hillsborough.realforeclose.com', 'https://hillsborough.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('INDIAN RIVER', 'https://indian-river.realforeclose.com', 'https://indian-river.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('JACKSON', 'https://jackson.realforeclose.com', 'https://jackson.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('LAKE', 'https://lake.realforeclose.com', 'https://lake.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('LEE', 'https://lee.realforeclose.com', 'https://lee.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('LEON', 'https://leon.realforeclose.com', 'https://leon.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('MANATEE', 'https://manatee.realforeclose.com', 'https://manatee.realforeclose.com', 'combined', true, true, 'Combined site'),
('MARION', 'https://marion.realforeclose.com', 'https://marion.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('MARTIN', 'https://martin.realforeclose.com', 'https://martin.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('MIAMI-DADE', 'https://miami-dade.realforeclose.com', 'https://miami-dade.realtaxdeed.com', 'combined', true, true, 'Combined site - both URLs point to same site'),
('MONROE', NULL, 'https://monroe.realtaxdeed.com', 'tax_deed_only', false, true, 'Only tax‑deed auctions'),
('NASSAU', 'https://nassau.realforeclose.com', 'https://nassau.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('OKALOOSA', 'https://okaloosa.realforeclose.com', 'https://okaloosa.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('OKEECHOBEE', 'https://okeechobee.realforeclose.com', 'https://okeechobee.realforeclose.com', 'combined', true, true, 'Combined site'),
('ORANGE', 'https://orange.realforeclose.com', 'https://orange.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('OSCEOLA', 'https://osceola.realforeclose.com', 'https://osceola.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('PALM BEACH', 'https://palmbeach.realforeclose.com', 'https://palmbeach.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('PASCO', 'https://pasco.realforeclose.com', 'https://pasco.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('PINELLAS', 'https://pinellas.realforeclose.com', 'https://pinellas.realtaxdeed.com', 'separate', true, true, 'Separate sites with cross-links'),
('POLK', 'https://polk.realforeclose.com', 'https://polk.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('PUTNAM', 'https://putnam.realforeclose.com', 'https://putnam.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('SAINT JOHNS', 'https://saintjohns.realforeclose.com', 'https://saintjohns.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('ST. LUCIE', 'https://stlucie.realforeclose.com', 'https://stlucie.realforeclose.com', 'combined', true, true, 'Combined site'),
('SANTA ROSA', 'https://santarosa.realforeclose.com', 'https://santarosa.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('SARASOTA', 'https://sarasota.realforeclose.com', 'https://sarasota.realtaxdeed.com', 'separate', true, true, 'Separate sites with cross-links'),
('SEMINOLE', 'https://seminole.realforeclose.com', 'https://seminole.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('SUWANNEE', NULL, 'https://suwannee.realtaxdeed.com', 'tax_deed_only', false, true, 'Only tax‑deed auctions'),
('VOLUSIA', 'https://volusia.realforeclose.com', 'https://volusia.realtaxdeed.com', 'separate', true, true, 'Separate sites'),
('WALTON', 'https://walton.realforeclose.com', 'https://walton.realforeclose.com', 'combined', true, true, 'Combined site'),
('WASHINGTON', 'https://washington.realforeclose.com', 'https://washington.realtaxdeed.com', 'separate', true, true, 'Separate sites')
ON CONFLICT (county) DO NOTHING;

-- Create RLS policies
ALTER TABLE public.auction_sites ENABLE ROW LEVEL SECURITY;

-- Allow public read access (sites are publicly accessible)
CREATE POLICY "Allow public read access to auction sites"
    ON public.auction_sites
    FOR SELECT
    USING (true);

-- Only authenticated users can modify
CREATE POLICY "Only authenticated users can modify auction sites"
    ON public.auction_sites
    FOR ALL
    USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

-- Create helper function to get auction URLs by county
CREATE OR REPLACE FUNCTION public.get_auction_urls(county_name TEXT)
RETURNS TABLE (
    county TEXT,
    foreclosure_url TEXT,
    tax_deed_url TEXT,
    site_type TEXT,
    has_foreclosure BOOLEAN,
    has_tax_deed BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.county,
        a.foreclosure_url,
        a.tax_deed_url,
        a.site_type,
        a.has_foreclosure,
        a.has_tax_deed
    FROM public.auction_sites a
    WHERE UPPER(a.county) = UPPER(county_name)
    AND a.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on function
GRANT EXECUTE ON FUNCTION public.get_auction_urls(TEXT) TO anon, authenticated;

COMMENT ON TABLE public.auction_sites IS 'Florida county foreclosure and tax-deed auction sites hosted by RealAuction platform family';
COMMENT ON COLUMN public.auction_sites.county IS 'Florida county name in uppercase';
COMMENT ON COLUMN public.auction_sites.foreclosure_url IS 'URL for foreclosure auction site (typically realforeclose.com subdomain)';
COMMENT ON COLUMN public.auction_sites.tax_deed_url IS 'URL for tax-deed auction site (typically realtaxdeed.com subdomain)';
COMMENT ON COLUMN public.auction_sites.site_type IS 'Type of site configuration: separate, combined, foreclosure_only, tax_deed_only, or coming_soon';
COMMENT ON COLUMN public.auction_sites.login_location IS 'Physical location of login form on the auction site pages';
COMMENT ON COLUMN public.auction_sites.login_fields IS 'JSON object containing form field labels and button text';
