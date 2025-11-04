-- M0 Seed Data: DOR Use Codes + Taxonomy
-- PDR: FL-USETAX-PDR-001 v1.0.0
-- Source: Florida Department of Revenue Land Use Codes (00-99)
-- Date: 2025-11-01

-- === Seed DOR Land Use Codes (00–99) ===
insert into public.dor_use_codes (code, group_main, label, summary) values
-- Residential 00–09
(00,'RESIDENTIAL','Vacant residential',null),
(01,'RESIDENTIAL','Single family',null),
(02,'RESIDENTIAL','Mobile homes',null),
(03,'RESIDENTIAL','Multifamily (10+)',null),
(04,'RESIDENTIAL','Condominium',null),
(05,'RESIDENTIAL','Cooperative',null),
(06,'RESIDENTIAL','Retirement homes (non-exempt)',null),
(07,'RESIDENTIAL','Misc. residential',null),
(08,'RESIDENTIAL','Multifamily (<10)',null),
(09,'RESIDENTIAL','Residential common areas',null),

-- Commercial 10–39
(10,'COMMERCIAL','Vacant commercial',null),
(11,'COMMERCIAL','Stores, one story',null),
(12,'COMMERCIAL','Mixed-use (store+office/residential)',null),
(13,'COMMERCIAL','Department stores',null),
(14,'COMMERCIAL','Supermarkets',null),
(15,'COMMERCIAL','Regional shopping center',null),
(16,'COMMERCIAL','Community shopping center',null),
(17,'COMMERCIAL','Office, one story',null),
(18,'COMMERCIAL','Office, multi-story',null),
(19,'COMMERCIAL','Professional service bldg',null),
(20,'COMMERCIAL','Airports/terminals/marinas',null),
(21,'COMMERCIAL','Restaurants',null),
(22,'COMMERCIAL','Drive-in restaurants',null),
(23,'COMMERCIAL','Financial institutions',null),
(24,'COMMERCIAL','Insurance offices',null),
(25,'COMMERCIAL','Repair service shops',null),
(26,'COMMERCIAL','Service stations',null),
(27,'COMMERCIAL','Auto sales/repair/storage',null),
(28,'COMMERCIAL','Parking lots & mobile home parks',null),
(29,'COMMERCIAL','Wholesale outlets',null),
(30,'COMMERCIAL','Florist/greenhouses',null),
(31,'COMMERCIAL','Drive-in theaters/open stadiums',null),
(32,'COMMERCIAL','Enclosed theaters/auditoriums',null),
(33,'COMMERCIAL','Bars/nightclubs',null),
(34,'COMMERCIAL','Bowling/skating/arenas',null),
(35,'COMMERCIAL','Tourist attractions/fairs',null),
(36,'COMMERCIAL','Camps',null),
(37,'COMMERCIAL','Race tracks',null),
(38,'COMMERCIAL','Golf/driving ranges',null),
(39,'COMMERCIAL','Hotels/motels',null),

-- Industrial 40–49
(40,'INDUSTRIAL','Vacant industrial',null),
(41,'INDUSTRIAL','Light manufacturing/printing',null),
(42,'INDUSTRIAL','Heavy industrial/plants',null),
(43,'INDUSTRIAL','Lumber/sawmills',null),
(44,'INDUSTRIAL','Packing plants',null),
(45,'INDUSTRIAL','Canneries/brewers/bottlers',null),
(46,'INDUSTRIAL','Other food processing',null),
(47,'INDUSTRIAL','Mineral/refining/cement',null),
(48,'INDUSTRIAL','Warehousing/distribution/terminals',null),
(49,'INDUSTRIAL','Open storage/junk/fuel yards',null),

-- Agricultural 50–69
(50,'AGRICULTURAL','Improved agricultural',null),
(51,'AGRICULTURAL','Cropland Class I',null),
(52,'AGRICULTURAL','Cropland Class II',null),
(53,'AGRICULTURAL','Cropland Class III',null),
(54,'AGRICULTURAL','Timberland SI ≥90',null),
(55,'AGRICULTURAL','Timberland SI 80–89',null),
(56,'AGRICULTURAL','Timberland SI 70–79',null),
(57,'AGRICULTURAL','Timberland SI 60–69',null),
(58,'AGRICULTURAL','Timberland SI 50–59',null),
(59,'AGRICULTURAL','Timberland (other)',null),
(60,'AGRICULTURAL','Grazing Class I',null),
(61,'AGRICULTURAL','Grazing Class II',null),
(62,'AGRICULTURAL','Grazing Class III',null),
(63,'AGRICULTURAL','Grazing Class IV',null),
(64,'AGRICULTURAL','Grazing Class V',null),
(65,'AGRICULTURAL','Grazing Class VI',null),
(66,'AGRICULTURAL','Orchards/Groves/Citrus',null),
(67,'AGRICULTURAL','Poultry/bees/fish/rabbits',null),
(68,'AGRICULTURAL','Dairies/feed lots',null),
(69,'AGRICULTURAL','Ornamentals/misc ag',null),

-- Institutional 70–79
(70,'INSTITUTIONAL','Vacant institutional',null),
(71,'INSTITUTIONAL','Churches',null),
(72,'INSTITUTIONAL','Private schools/colleges',null),
(73,'INSTITUTIONAL','Private hospitals',null),
(74,'INSTITUTIONAL','Homes for the aged',null),
(75,'INSTITUTIONAL','Orphanages/charitable',null),
(76,'INSTITUTIONAL','Mortuaries/cemeteries',null),
(77,'INSTITUTIONAL','Clubs/lodges',null),
(78,'INSTITUTIONAL','Sanitariums/rest homes',null),
(79,'INSTITUTIONAL','Cultural facilities',null),

-- Government 80–89
(80,'GOVERNMENT','Vacant governmental',null),
(81,'GOVERNMENT','Military',null),
(82,'GOVERNMENT','Forests/parks/recreation',null),
(83,'GOVERNMENT','Public county schools',null),
(84,'GOVERNMENT','Public colleges',null),
(85,'GOVERNMENT','Public hospitals',null),
(86,'GOVERNMENT','County properties (other)',null),
(87,'GOVERNMENT','State properties (other)',null),
(88,'GOVERNMENT','Federal properties (other)',null),
(89,'GOVERNMENT','Municipal properties (other)',null),

-- Misc/Centrally assessed/Acreage 90–99
(90,'MISC','Government leasehold interest',null),
(91,'MISC','Utilities/rail/water/sewer',null),
(92,'MISC','Mining/petroleum/gas lands',null),
(93,'MISC','Subsurface rights',null),
(94,'MISC','Right-of-way',null),
(95,'MISC','Rivers/lakes/submerged',null),
(96,'MISC','Waste/disposal/drainage/marsh',null),
(97,'MISC','Outdoor recreation/high-water recharge',null),
(98,'CENTRAL','Centrally assessed',null),
(99,'NONAG','Non-agricultural acreage',null)
on conflict (code) do nothing;

-- === Seed hierarchical taxonomy ===
-- Level 1 (Main USE categories)
insert into public.use_taxonomy (code, name, level, parent_code) values
('RESIDENTIAL','Residential',1,null),
('COMMERCIAL','Commercial',1,null),
('INDUSTRIAL','Industrial',1,null),
('AGRICULTURAL','Agricultural',1,null),
('INSTITUTIONAL','Institutional',1,null),
('GOVERNMENT','Government',1,null),
('MISC','Miscellaneous',1,null),
('CENTRAL','Centrally Assessed',1,null),
('NONAG','Non-Agricultural Acreage',1,null)
on conflict (code) do nothing;

-- Level 2 (SUBUSE categories) — starter set
insert into public.use_taxonomy (code, name, level, parent_code) values
-- Commercial SUBUSE
('HOTEL','Hotel/Motel',2,'COMMERCIAL'),
('RETAIL_STORE','Retail Store',2,'COMMERCIAL'),
('SHOPPING_CENTER','Shopping Center',2,'COMMERCIAL'),
('OFFICE','Office',2,'COMMERCIAL'),
('RESTAURANT','Restaurant',2,'COMMERCIAL'),
('AUTO_SALES_SERVICE','Auto Sales/Service',2,'COMMERCIAL'),
('GOLF','Golf Course/Range',2,'COMMERCIAL'),
('RACETRACK','Race Track',2,'COMMERCIAL'),
('CAMP','Camp',2,'COMMERCIAL'),

-- Industrial SUBUSE
('WAREHOUSE','Warehouse/Distribution',2,'INDUSTRIAL'),
('LIGHT_MANUFACTURING','Light Manufacturing',2,'INDUSTRIAL'),
('HEAVY_INDUSTRY','Heavy Industry',2,'INDUSTRIAL'),
('LUMBER','Lumber/Sawmill',2,'INDUSTRIAL'),
('PACKING_PLANT','Packing Plant',2,'INDUSTRIAL'),

-- Agricultural SUBUSE
('AG_GRAZING','Grazing',2,'AGRICULTURAL'),
('AG_CROPLAND','Cropland',2,'AGRICULTURAL'),
('AG_TIMBER','Timberland',2,'AGRICULTURAL'),

-- Institutional SUBUSE
('RELIGIOUS','Religious Facility',2,'INSTITUTIONAL'),
('PRIVATE_HOSPITAL','Private Hospital',2,'INSTITUTIONAL'),
('SCHOOL_PRIVATE','Private School/College',2,'INSTITUTIONAL'),

-- Government SUBUSE
('PUBLIC_SCHOOL','Public School',2,'GOVERNMENT'),
('PUBLIC_COLLEGE','Public College',2,'GOVERNMENT'),
('PUBLIC_HOSPITAL','Public Hospital',2,'GOVERNMENT')
on conflict (code) do nothing;
