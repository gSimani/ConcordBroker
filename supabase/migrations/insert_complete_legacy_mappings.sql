-- Complete Legacy Code Mappings for all Florida Counties
-- Maps county-specific codes to standardized FL DOR codes

INSERT INTO dor_code_mappings_std (legacy_code, standard_full_code, county, confidence) VALUES

-- Broward County text codes (already exist, adding more)
('AG', '60-01', 'BROWARD', 'exact'),
('COMM', '11-01', 'BROWARD', 'probable'),

-- Numeric codes found across multiple counties
-- Code 0 - Vacant
('0', '00-01', NULL, 'exact'),
('00', '00-01', NULL, 'exact'),

-- Code 1 - Single Family Residential (most common)
('1', '01-01', NULL, 'exact'),
('01', '01-01', NULL, 'exact'),

-- Code 2 - Manufactured Housing
('2', '02-01', NULL, 'exact'),
('02', '02-01', NULL, 'exact'),

-- Code 3 - Multi-family
('3', '03-01', NULL, 'probable'),
('03', '03-01', NULL, 'probable'),

-- Code 4 - Commercial/Condominium (context-dependent)
('4', '11-01', NULL, 'probable'),  -- Default to commercial store
('04', '04-01', NULL, 'probable'),  -- Or residential condo

-- Code 5 - Cooperatives
('5', '05-01', NULL, 'probable'),
('05', '05-01', NULL, 'probable'),

-- Code 6 - Retirement/Assisted Living
('6', '06-01', NULL, 'probable'),
('06', '06-01', NULL, 'probable'),

-- Code 7 - Migrant Labor
('7', '07-01', NULL, 'probable'),
('07', '07-01', NULL, 'probable'),

-- Code 8 - Multi-family 2-9 units
('8', '08-01', NULL, 'probable'),
('08', '08-01', NULL, 'probable'),

-- Code 9 - Residential Common Areas
('9', '09-01', NULL, 'probable'),
('09', '09-01', NULL, 'probable'),

-- Code 10 - Vacant Commercial
('10', '10-01', NULL, 'exact'),

-- Code 11 - Stores
('11', '11-01', NULL, 'exact'),

-- Code 12 - Offices
('12', '12-01', NULL, 'exact'),

-- Code 13 - Department Stores
('13', '13-01', NULL, 'exact'),

-- Code 14 - Restaurants
('14', '14-01', NULL, 'exact'),

-- Code 15 - Service Stations
('15', '15-01', NULL, 'exact'),

-- Code 16 - Repair Shops
('16', '16-01', NULL, 'exact'),

-- Code 17 - Auto Sales (from database)
('17', '21-01', NULL, 'exact'),

-- Code 20-39 - Commercial
('20', '21-01', NULL, 'probable'),
('21', '21-01', NULL, 'exact'),
('22', '22-01', NULL, 'exact'),
('23', '23-01', NULL, 'exact'),
('24', '24-01', NULL, 'exact'),
('25', '25-01', NULL, 'exact'),
('26', '26-01', NULL, 'exact'),
('27', '27-01', NULL, 'exact'),
('28', '28-01', NULL, 'exact'),
('29', '29-01', NULL, 'exact'),
('30', '30-01', NULL, 'exact'),
('31', '31-01', NULL, 'exact'),
('32', '32-01', NULL, 'exact'),
('33', '33-01', NULL, 'exact'),
('34', '34-01', NULL, 'exact'),
('35', '35-01', NULL, 'exact'),
('36', '36-01', NULL, 'exact'),
('37', '37-01', NULL, 'exact'),
('38', '38-01', NULL, 'exact'),
('39', '39-01', NULL, 'exact'),

-- Code 40-49 - Industrial
('40', '40-01', NULL, 'exact'),
('41', '41-01', NULL, 'exact'),
('42', '42-01', NULL, 'exact'),
('43', '43-01', NULL, 'exact'),
('44', '44-01', NULL, 'exact'),
('45', '45-01', NULL, 'exact'),
('46', '46-01', NULL, 'exact'),
('47', '47-01', NULL, 'exact'),
('48', '48-01', NULL, 'exact'),
('49', '49-01', NULL, 'exact'),

-- Code 50-69 - Agricultural (found in database)
('50', '60-01', NULL, 'probable'),
('51', '51-01', NULL, 'exact'),
('52', '52-01', NULL, 'exact'),
('53', '53-01', NULL, 'exact'),
('54', '54-01', NULL, 'exact'),
('55', '55-01', NULL, 'exact'),
('56', '56-01', NULL, 'exact'),
('57', '57-01', NULL, 'exact'),
('58', '58-01', NULL, 'exact'),
('59', '59-01', NULL, 'exact'),
('60', '60-01', NULL, 'exact'),
('61', '61-01', NULL, 'exact'),
('62', '62-01', NULL, 'exact'),
('63', '63-01', NULL, 'exact'),
('64', '64-01', NULL, 'exact'),
('65', '65-01', NULL, 'exact'),
('66', '66-01', NULL, 'exact'),
('67', '67-01', NULL, 'exact'),
('68', '68-01', NULL, 'exact'),
('69', '69-01', NULL, 'exact'),

-- Code 70-79 - Institutional (found in database)
('70', '71-01', NULL, 'probable'),
('71', '71-01', NULL, 'exact'),
('72', '72-01', NULL, 'exact'),
('73', '73-01', NULL, 'exact'),
('74', '74-01', NULL, 'exact'),
('75', '75-01', NULL, 'exact'),
('76', '76-01', NULL, 'exact'),
('77', '77-01', NULL, 'exact'),
('78', '78-01', NULL, 'exact'),
('79', '79-01', NULL, 'exact'),

-- Code 80-89 - Government (found in database)
('80', '81-01', NULL, 'probable'),
('81', '81-01', NULL, 'exact'),
('82', '82-01', NULL, 'exact'),
('83', '83-01', NULL, 'exact'),
('84', '84-01', NULL, 'exact'),
('85', '85-01', NULL, 'exact'),
('86', '86-01', NULL, 'exact'),
('87', '87-01', NULL, 'exact'),
('88', '88-01', NULL, 'exact'),
('89', '89-01', NULL, 'exact'),

-- Code 90-99 - Vacant/Miscellaneous (found in database)
('90', '90-01', NULL, 'exact'),
('91', '91-01', NULL, 'exact'),
('92', '92-01', NULL, 'exact'),
('93', '93-01', NULL, 'exact'),
('94', '94-01', NULL, 'exact'),
('95', '95-01', NULL, 'exact'),
('96', '96-01', NULL, 'exact'),
('97', '97-01', NULL, 'exact'),
('98', '98-01', NULL, 'exact'),
('99', '99-01', NULL, 'exact')

ON CONFLICT (legacy_code) DO UPDATE SET
  standard_full_code = EXCLUDED.standard_full_code,
  confidence = EXCLUDED.confidence;
