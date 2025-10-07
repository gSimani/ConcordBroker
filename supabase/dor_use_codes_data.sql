-- Insert all Florida Department of Revenue Land Use Codes
-- Based on 2024 NAL Users Guide

-- Clear existing data
TRUNCATE TABLE public.dor_use_codes CASCADE;

-- RESIDENTIAL CODES (000-009)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class, is_residential, is_vacant) VALUES
('000', 'Residential', 'Vacant', 'Vacant Residential - with/without extra features', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, TRUE),
('001', 'Residential', 'Single Family', 'Single Family', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE),
('002', 'Residential', 'Mobile Homes', 'Mobile Homes', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE),
('004', 'Residential', 'Condominiums', 'Condominiums', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE),
('005', 'Residential', 'Cooperatives', 'Cooperatives', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE),
('006', 'Residential', 'Retirement', 'Retirement Homes not eligible for exemption', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE),
('007', 'Residential', 'Miscellaneous', 'Miscellaneous Residential (migrant camps, boarding homes, etc.)', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE),
('008', 'Residential', 'Multi-family', 'Multi-family - fewer than 10 units', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE),
('009', 'Residential', 'Common Areas', 'Residential Common Elements/Areas', 'text-green-800', 'bg-green-100', 'border-green-200', TRUE, FALSE);

-- COMMERCIAL CODES (003, 010-039)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class, is_commercial, is_vacant) VALUES
('003', 'Commercial', 'Multi-family', 'Multi-family - 10 units or more', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('010', 'Commercial', 'Vacant', 'Vacant Commercial - with/without extra features', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, TRUE),
('011', 'Commercial', 'Retail', 'Stores, one story', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('012', 'Commercial', 'Mixed Use', 'Mixed use - store and office or store and residential combination', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('013', 'Commercial', 'Retail', 'Department Stores', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('014', 'Commercial', 'Retail', 'Supermarkets', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('015', 'Commercial', 'Retail', 'Regional Shopping Centers', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('016', 'Commercial', 'Retail', 'Community Shopping Centers', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('017', 'Commercial', 'Office', 'Office buildings, non-professional service buildings, one story', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('018', 'Commercial', 'Office', 'Office buildings, non-professional service buildings, multi-story', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('019', 'Commercial', 'Office', 'Professional service buildings', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('020', 'Commercial', 'Transportation', 'Airports (private or commercial), bus terminals, marine terminals, piers, marinas', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('021', 'Commercial', 'Restaurant', 'Restaurants, cafeterias', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('022', 'Commercial', 'Restaurant', 'Drive-in Restaurants', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('023', 'Commercial', 'Financial', 'Financial institutions (banks, saving and loan companies, mortgage companies, credit services)', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('024', 'Commercial', 'Office', 'Insurance company offices', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('025', 'Commercial', 'Service', 'Repair service shops (excluding automotive), radio and T.V. repair, refrigeration service, electric repair, laundries, laundromats', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('026', 'Commercial', 'Automotive', 'Service stations', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('027', 'Commercial', 'Automotive', 'Auto sales, auto repair and storage, auto service shops, body and fender shops, commercial garages, farm and machinery sales and services, auto rental, marine equipment, trailers and related equipment, mobile home sales, motorcycles, construction vehicle sales', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('028', 'Commercial', 'Parking', 'Parking lots (commercial or patron), mobile home parks', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('029', 'Commercial', 'Wholesale', 'Wholesale outlets, produce houses, manufacturing outlets', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('030', 'Commercial', 'Nursery', 'Florists, greenhouses', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('031', 'Commercial', 'Entertainment', 'Drive-in theaters, open stadiums', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('032', 'Commercial', 'Entertainment', 'Enclosed theaters, enclosed auditoriums', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('033', 'Commercial', 'Entertainment', 'Nightclubs, cocktail lounges, bars', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('034', 'Commercial', 'Entertainment', 'Bowling alleys, skating rinks, pool halls, enclosed arenas', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('035', 'Commercial', 'Entertainment', 'Tourist attractions, permanent exhibits, other entertainment facilities, fairgrounds (privately owned)', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('036', 'Commercial', 'Recreation', 'Camps', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('037', 'Commercial', 'Entertainment', 'Race tracks (horse, auto, or dog)', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('038', 'Commercial', 'Recreation', 'Golf courses, driving ranges', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE),
('039', 'Commercial', 'Hospitality', 'Hotels, motels', 'text-blue-800', 'bg-blue-100', 'border-blue-200', TRUE, FALSE);

-- INDUSTRIAL CODES (040-049)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class, is_industrial, is_vacant) VALUES
('040', 'Industrial', 'Vacant', 'Vacant Industrial - with/without extra features', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, TRUE),
('041', 'Industrial', 'Light Manufacturing', 'Light manufacturing, small equipment manufacturing plants, small machine shops, instrument manufacturing, printing plants', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('042', 'Industrial', 'Heavy Industrial', 'Heavy industrial, heavy equipment manufacturing, large machine shops, foundries, steel fabricating plants, auto or aircraft plants', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('043', 'Industrial', 'Lumber', 'Lumber yards, sawmills, planing mills', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('044', 'Industrial', 'Food Processing', 'Packing plants, fruit and vegetable packing plants, meat packing plants', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('045', 'Industrial', 'Food Processing', 'Canneries, fruit and vegetable, bottlers and brewers, distilleries, wineries', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('046', 'Industrial', 'Food Processing', 'Other food processing, candy factories, bakeries, potato chip factories', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('047', 'Industrial', 'Mineral Processing', 'Mineral processing, phosphate processing, cement plants, refineries, clay plants, rock and gravel plants', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('048', 'Industrial', 'Warehousing', 'Warehousing, distribution terminals, trucking terminals, van and storage warehousing', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE),
('049', 'Industrial', 'Storage', 'Open storage, new and used building supplies, junk yards, auto wrecking, fuel storage, equipment and material storage', 'text-orange-800', 'bg-orange-100', 'border-orange-200', TRUE, FALSE);

-- AGRICULTURAL CODES (050-069)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class, is_agricultural) VALUES
('050', 'Agricultural', 'Improved', 'Improved agricultural', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('051', 'Agricultural', 'Cropland I', 'Cropland soil capability Class I', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('052', 'Agricultural', 'Cropland II', 'Cropland soil capability Class II', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('053', 'Agricultural', 'Cropland III', 'Cropland soil capability Class III', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('054', 'Agricultural', 'Timberland 90+', 'Timberland - site index 90 and above', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('055', 'Agricultural', 'Timberland 80-89', 'Timberland - site index 80 to 89', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('056', 'Agricultural', 'Timberland 70-79', 'Timberland - site index 70 to 79', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('057', 'Agricultural', 'Timberland 60-69', 'Timberland - site index 60 to 69', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('058', 'Agricultural', 'Timberland 50-59', 'Timberland - site index 50 to 59', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('059', 'Agricultural', 'Timberland', 'Timberland not classified by site index to Pines', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('060', 'Agricultural', 'Grazing I', 'Grazing land soil capability Class I', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('061', 'Agricultural', 'Grazing II', 'Grazing land soil capability Class II', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('062', 'Agricultural', 'Grazing III', 'Grazing land soil capability Class III', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('063', 'Agricultural', 'Grazing IV', 'Grazing land soil capability Class IV', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('064', 'Agricultural', 'Grazing V', 'Grazing land soil capability Class V', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('065', 'Agricultural', 'Grazing VI', 'Grazing land soil capability Class VI', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('066', 'Agricultural', 'Orchard', 'Orchard Groves, citrus, etc.', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('067', 'Agricultural', 'Poultry/Bees', 'Poultry, bees, tropical fish, rabbits, etc.', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('068', 'Agricultural', 'Dairies', 'Dairies, feed lots', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE),
('069', 'Agricultural', 'Ornamental', 'Ornamentals, miscellaneous agricultural', 'text-yellow-800', 'bg-yellow-100', 'border-yellow-200', TRUE);

-- INSTITUTIONAL CODES (070-079)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class, is_institutional, is_vacant) VALUES
('070', 'Institutional', 'Vacant', 'Vacant Institutional, with or without extra features', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, TRUE),
('071', 'Institutional', 'Religious', 'Churches', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('072', 'Institutional', 'Education', 'Private schools and colleges', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('073', 'Institutional', 'Medical', 'Privately owned hospitals', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('074', 'Institutional', 'Care Facility', 'Homes for the aged', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('075', 'Institutional', 'Charitable', 'Orphanages, other non-profit or charitable services', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('076', 'Institutional', 'Cemetery', 'Mortuaries, cemeteries, crematoriums', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('077', 'Institutional', 'Social', 'Clubs, lodges, union halls', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('078', 'Institutional', 'Medical', 'Sanitariums, convalescent and rest homes', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE),
('079', 'Institutional', 'Cultural', 'Cultural organizations, facilities', 'text-purple-800', 'bg-purple-100', 'border-purple-200', TRUE, FALSE);

-- GOVERNMENTAL CODES (080-089)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class, is_governmental, is_vacant) VALUES
('080', 'Governmental', 'Vacant', 'Vacant Governmental - with/without extra features for municipal, counties, state, federal properties and water management district', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, TRUE),
('081', 'Governmental', 'Military', 'Military', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('082', 'Governmental', 'Parks', 'Forest, parks, recreational areas', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('083', 'Governmental', 'Education', 'Public county schools - including all property of Board of Public Instruction', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('084', 'Governmental', 'Education', 'Colleges (non-private)', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('085', 'Governmental', 'Medical', 'Hospitals (non-private)', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('086', 'Governmental', 'County', 'Counties (other than public schools, colleges, hospitals) including non-municipal government', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('087', 'Governmental', 'State', 'State, other than military, forests, parks, recreational areas, colleges, hospitals', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('088', 'Governmental', 'Federal', 'Federal, other than military, forests, parks, recreational areas, hospitals, colleges', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE),
('089', 'Governmental', 'Municipal', 'Municipal, other than parks, recreational areas, colleges, hospitals', 'text-indigo-800', 'bg-indigo-100', 'border-indigo-200', TRUE, FALSE);

-- MISCELLANEOUS CODES (090-097)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class) VALUES
('090', 'Miscellaneous', 'Leasehold', 'Leasehold interests (government-owned property leased by a non-governmental lessee)', 'text-gray-800', 'bg-gray-100', 'border-gray-200'),
('091', 'Miscellaneous', 'Utility', 'Utility, gas and electricity, telephone and telegraph, locally assessed railroads, water and sewer service, pipelines, canals, radio/television communication', 'text-gray-800', 'bg-gray-100', 'border-gray-200'),
('092', 'Miscellaneous', 'Mining', 'Mining lands, petroleum lands, or gas lands', 'text-gray-800', 'bg-gray-100', 'border-gray-200'),
('093', 'Miscellaneous', 'Rights', 'Subsurface rights', 'text-gray-800', 'bg-gray-100', 'border-gray-200'),
('094', 'Miscellaneous', 'Right-of-way', 'Right-of-way, streets, roads, irrigation channel, ditch, etc.', 'text-gray-800', 'bg-gray-100', 'border-gray-200'),
('095', 'Miscellaneous', 'Submerged', 'Rivers and lakes, submerged lands', 'text-gray-800', 'bg-gray-100', 'border-gray-200'),
('096', 'Miscellaneous', 'Waste', 'Sewage disposal, solid waste, borrow pits, drainage reservoirs, waste land, marsh, sand dunes, swamps', 'text-gray-800', 'bg-gray-100', 'border-gray-200'),
('097', 'Miscellaneous', 'Recreation', 'Outdoor recreational or parkland, or high-water recharge subject to classified use assessment', 'text-gray-800', 'bg-gray-100', 'border-gray-200');

-- CENTRALLY ASSESSED (098)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class) VALUES
('098', 'Centrally Assessed', NULL, 'Centrally assessed', 'text-red-800', 'bg-red-100', 'border-red-200');

-- NON-AGRICULTURAL ACREAGE (099)
INSERT INTO public.dor_use_codes (code, category, subcategory, description, color_class, bg_color_class, border_color_class) VALUES
('099', 'Non-Agricultural Acreage', NULL, 'Acreage not zoned agricultural - with/without extra features', 'text-amber-800', 'bg-amber-100', 'border-amber-200');

-- Add some useful views for common queries

-- View to get all residential properties
CREATE OR REPLACE VIEW public.v_dor_residential_codes AS
SELECT * FROM public.dor_use_codes
WHERE is_residential = TRUE
ORDER BY code;

-- View to get all commercial properties
CREATE OR REPLACE VIEW public.v_dor_commercial_codes AS
SELECT * FROM public.dor_use_codes
WHERE is_commercial = TRUE
ORDER BY code;

-- View to get all vacant properties
CREATE OR REPLACE VIEW public.v_dor_vacant_codes AS
SELECT * FROM public.dor_use_codes
WHERE is_vacant = TRUE
ORDER BY code;

-- Create a materialized view for quick category counts
CREATE MATERIALIZED VIEW public.mv_dor_category_summary AS
SELECT
    category,
    COUNT(*) as code_count,
    array_agg(code ORDER BY code) as codes
FROM public.dor_use_codes
GROUP BY category
ORDER BY category;

-- Create index on materialized view
CREATE INDEX idx_mv_dor_category ON public.mv_dor_category_summary(category);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION public.refresh_dor_category_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_dor_category_summary;
END;
$$ LANGUAGE plpgsql;

-- Grant appropriate permissions
GRANT SELECT ON public.dor_use_codes TO anon;
GRANT SELECT ON public.dor_use_codes TO authenticated;
GRANT SELECT ON public.v_dor_residential_codes TO anon;
GRANT SELECT ON public.v_dor_commercial_codes TO anon;
GRANT SELECT ON public.v_dor_vacant_codes TO anon;
GRANT SELECT ON public.mv_dor_category_summary TO anon;
GRANT SELECT ON public.v_dor_residential_codes TO authenticated;
GRANT SELECT ON public.v_dor_commercial_codes TO authenticated;
GRANT SELECT ON public.v_dor_vacant_codes TO authenticated;
GRANT SELECT ON public.mv_dor_category_summary TO authenticated;