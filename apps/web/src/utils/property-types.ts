/**
 * Property Type Utilities for ConcordBroker
 *
 * Maps Florida DOR (Department of Revenue) property use codes to standardized categories
 * and provides helper functions for property type classification and display.
 *
 * DOR Code Ranges:
 * - 01-09: Residential
 * - 10-39: Commercial
 * - 40-49: Industrial
 * - 51-69: Agricultural
 * - 71-79: Institutional
 * - 81-89: Government
 * - 00, 90-99: Vacant Land
 */

/**
 * Property type filters - maps categories to DOR codes
 * Includes both 2-digit (e.g., "01") and 1-digit (e.g., "1") formats
 * as database contains both formats
 */
export const PROPERTY_TYPE_CODES = {
  residential: [
    // Numeric codes (1 and 2 digit)
    '01', '02', '03', '04', '05', '06', '07', '08', '09',
    '1', '2', '3', '4', '5', '6', '7', '8', '9',
    // 3-digit codes (used by some counties)
    '001', '002', '003', '004', '005', '006', '007', '008', '009',
    // Text codes (Broward and other counties)
    'SFR', 'MFR', 'CONDO'
  ],
  commercial: [
    // Numeric codes
    '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
    '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
    '30', '31', '32', '33', '34', '35', '36', '37', '38', '39',
    // 3-digit codes
    '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',
    '020', '021', '022', '023', '024', '025', '026', '027', '028', '029',
    '030', '031', '032', '033', '034', '035', '036', '037', '038', '039',
    // Text codes (Broward and other counties)
    'COM', 'COMM'
  ],
  industrial: [
    // 2-digit codes
    '40', '41', '42', '43', '44', '45', '46', '47', '48', '49',
    // 3-digit codes (used by some counties like Broward)
    '040', '041', '042', '043', '044', '045', '046', '047', '048', '049',
    // Text code
    'IND'
  ],
  agricultural: [
    // Numeric codes
    '51', '52', '53', '54', '55', '56', '57', '58', '59',
    '60', '61', '62', '63', '64', '65', '66', '67', '68', '69',
    // 3-digit codes
    '051', '052', '053', '054', '055', '056', '057', '058', '059',
    '060', '061', '062', '063', '064', '065', '066', '067', '068', '069',
    // Text codes (Broward and other counties)
    'AGR', 'AG'
  ],
  institutional: [
    // Numeric codes
    '71', '72', '73', '74', '75', '76', '77', '78', '79',
    // 3-digit codes
    '071', '072', '073', '074', '075', '076', '077', '078', '079'
  ],
  government: [
    // Numeric codes
    '81', '82', '83', '84', '85', '86', '87', '88', '89',
    // 3-digit codes
    '081', '082', '083', '084', '085', '086', '087', '088', '089'
  ],
  vacantLand: [
    // Numeric codes
    '00', '0', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99',
    // 3-digit codes
    '000', '090', '091', '092', '093', '094', '095', '096', '097', '098', '099',
    // Text codes (Broward and other counties)
    'VAC', 'VAC_RES'
  ]
} as const;

/**
 * Detailed property subtype mapping for user-friendly display
 * Maps specific DOR codes to descriptive property subtypes
 * Based on Florida DOR Property Use Code Standards (0-99)
 */
const PROPERTY_SUBTYPE_MAP: Record<string, string> = {
  // Residential (01-09) - Primary dwelling units
  '01': 'Single Family',
  '1': 'Single Family',
  '02': 'Manufactured/Modular',
  '2': 'Manufactured/Modular',
  '03': 'Multi-Family (10+ units)',
  '3': 'Multi-Family (10+ units)',
  '04': 'Condominium',
  '4': 'Condominium',
  '05': 'Cooperative',
  '5': 'Cooperative',
  '06': 'Retirement/Assisted Living',
  '6': 'Retirement/Assisted Living',
  '07': 'Migrant Labor Camp',
  '7': 'Migrant Labor Camp',
  '08': 'Multi-Family (2-9 units)',
  '8': 'Multi-Family (2-9 units)',
  '09': 'Mobile Home Park',
  '9': 'Mobile Home Park',

  // Commercial (10-39) - Retail, Office, Hospitality & Entertainment
  '10': 'Retail Store',
  '11': 'Multi-Story Store',
  '12': 'Mixed Use',
  '13': 'Department Store',
  '14': 'Supermarket',
  '15': 'Regional Shopping Center',
  '16': 'Community Shopping Center',
  '17': 'Professional Office',
  '18': 'Parking Garage',
  '19': 'Restaurant/Cafeteria',
  '20': 'Drive-In Restaurant',
  '21': 'Fast Food',
  '22': 'Drive-Thru',
  '23': 'Financial Institution',
  '24': 'Drive-In Bank',
  '25': 'Repair Service',
  '26': 'Service Station',
  '27': 'Hotel/Motel',                    // DOR 27 - Hospitality
  '28': 'Bowling Alley',
  '29': 'Theater',
  '30': 'Nightclub/Bar',
  '31': 'Entertainment/Amusement',        // DOR 31 - Entertainment venues
  '32': 'Parking Lot',
  '33': 'Mobile Home Park (Commercial)',
  '34': 'Campground/RV Park',             // DOR 34 - Tourist/recreation
  '35': 'Tourist Attraction',             // DOR 35 - Theme parks, attractions
  '36': 'Golf Course',
  '37': 'Enclosed Mall',
  '38': 'Golf Course (Private)',          // DOR 38 - Private golf courses
  '39': 'Special Commercial',

  // Industrial (40-49) - Manufacturing, Utilities, Infrastructure
  '40': 'Distribution Terminal',
  '41': 'Light Manufacturing',            // DOR 41 - Light industrial/manufacturing
  '42': 'Heavy Industrial',               // DOR 42 - Heavy industrial operations
  '43': 'Railroad Property',              // DOR 43 - Rail yards, terminals
  '44': 'Utility - Electric',             // DOR 44 - Electric utilities
  '45': 'Utility - Gas',                  // DOR 45 - Gas utilities
  '46': 'Utility - Telephone',            // DOR 46 - Telecom infrastructure
  '47': 'Utility - Water/Sewer',          // DOR 47 - Water/wastewater facilities
  '48': 'Utility - Other',                // DOR 48 - Other utility types
  '49': 'Landfill/Solid Waste',           // DOR 49 - Waste management facilities

  // Agricultural (51-69) - Farms, Timberland, Marine
  // NOTE: DOR codes 50-56 are crop/livestock production
  '51': 'Crop/Pasture',
  '52': 'Timberland',
  '53': 'Poultry/Bees',
  '54': 'Dairies/Feed Lots',
  '55': 'Ornamentals/Nursery',
  '56': 'Specialty Farm',
  '57': 'Marine Services/Docks',          // DOR 57 - Marine-related ag/commercial
  '58': 'Marina/Boatyard',                // DOR 58 - Commercial marinas
  '59': 'Residential with Ag Exemption',
  '60': 'Grazing Land',

  // Agricultural (60-69) - Extended agricultural uses
  '61': 'Forest Land',
  '62': 'Improved Agricultural',
  '63': 'Unimproved Agricultural',
  '64': 'Agricultural Buildings',
  '65': 'Agricultural Processing',
  '66': 'Livestock Operations',
  '67': 'Aquaculture',
  '68': 'Citrus Groves',
  '69': 'Specialty Agricultural',

  // Institutional (71-79) - Private non-profit
  // NOTE: DOR code 70 is Vacant Institutional (classified under vacant)
  '71': 'Church/Synagogue',
  '72': 'Private School',
  '73': 'Private Hospital',
  '74': 'Convalescent/Nursing Home',
  '75': 'Cultural Organization',
  '76': 'Charitable Service',
  '77': 'Mortuary/Cemetery',
  '78': 'Private Recreational',
  '79': 'Special Institutional',

  // Agricultural (80-89) - Primary agricultural production
  // NOTE: DOR codes 80-89 are specific crop/livestock types
  '80': 'Crop Land',                      // DOR 80 - Row crops, vegetables
  '81': 'Timberland (Commercial)',        // DOR 81 - Commercial timber production
  '82': 'Fruit Orchards',
  '83': 'Cattle Ranch',                   // DOR 83 - Beef cattle operations
  '84': 'Dairy Farm',                     // DOR 84 - Dairy operations
  '85': 'Livestock Farm',                 // DOR 85 - General livestock
  '86': 'Orchard/Grove',                  // DOR 86 - Fruit/nut orchards
  '87': 'Ornamental Horticulture',        // DOR 87 - Nurseries, landscaping
  '88': 'Vacant Agricultural',            // DOR 88 - Undeveloped ag land

  // Vacant Land (00, 90-99) - Undeveloped properties by intended use
  '00': 'Vacant Land',                    // DOR 00 - General vacant
  '0': 'Vacant Land',
  '90': 'Vacant Residential',             // DOR 90 - Zoned/intended for residential
  '91': 'Military/Defense',               // DOR 91 - Military installations
  '92': 'Parks/Recreation',               // DOR 92 - Public parks, forests
  '93': 'Schools/Universities',           // DOR 93 - Educational facilities
  '94': 'Universities/Colleges',          // DOR 94 - Higher education
  '95': 'Hospitals (Public)',             // DOR 95 - Public hospitals
  '96': 'County Government',              // DOR 96 - County-owned property
  '97': 'State Government',               // DOR 97 - State-owned property
  '98': 'Federal Government',             // DOR 98 - Federal property
  '99': 'Municipal Government',           // DOR 99 - City-owned property

  // 3-digit code support for counties using leading zeros
  '001': 'Single Family',
  '002': 'Manufactured/Modular',
  '003': 'Multi-Family (10+ units)',
  '004': 'Condominium',
  '005': 'Cooperative',
  '006': 'Retirement/Assisted Living',
  '007': 'Migrant Labor Camp',
  '008': 'Multi-Family (2-9 units)',
  '009': 'Mobile Home Park',

  // Add 3-digit support for other key codes
  '040': 'Distribution Terminal',
  '041': 'Light Manufacturing',
  '042': 'Heavy Industrial',
  '043': 'Railroad Property',
  '044': 'Utility - Electric',
  '045': 'Utility - Gas',
  '046': 'Utility - Telephone',
  '047': 'Utility - Water/Sewer',
  '048': 'Utility - Other',
  '049': 'Landfill/Solid Waste',

  '080': 'Crop Land',
  '081': 'Timberland (Commercial)',
  '083': 'Cattle Ranch',
  '084': 'Dairy Farm',
  '085': 'Livestock Farm',
  '086': 'Orchard/Grove',
  '087': 'Ornamental Horticulture',
  '088': 'Vacant Agricultural',

  '090': 'Vacant Residential',
  '091': 'Military/Defense',
  '092': 'Parks/Recreation',
  '093': 'Schools/Universities',
  '094': 'Universities/Colleges',
  '095': 'Hospitals (Public)',
  '096': 'County Government',
  '097': 'State Government',
  '098': 'Federal Government',
  '099': 'Municipal Government'
};

/**
 * Text code to numeric DOR code mapping
 * Database contains both numeric codes ('01', '043') and text codes ('SFR', 'MFR')
 */
const TEXT_CODE_MAP: Record<string, number> = {
  'SFR': 1,    // Single Family Residential
  'MFR': 3,    // Multi-Family Residential
  'CONDO': 4,  // Condominium
  'COM': 10,   // Commercial
  'IND': 40,   // Industrial
  'AGR': 51,   // Agricultural
  'VAC': 90,   // Vacant Land
};

/**
 * Get property category from DOR code
 * Returns the main category (e.g., "Residential", "Commercial")
 * Handles both numeric codes ('01', '043') and text codes ('SFR', 'MFR')
 */
export function getPropertyCategory(propertyUse: string | null | undefined): string {
  if (!propertyUse) return 'Unknown';

  // Check if it's a text code first
  const upperCode = propertyUse.toUpperCase().trim();
  if (TEXT_CODE_MAP[upperCode]) {
    const numericCode = TEXT_CODE_MAP[upperCode];
    return getPropertyCategory(String(numericCode));
  }

  // Parse as numeric code
  const code = parseInt(propertyUse) || 0;

  if (code >= 1 && code <= 9) return 'Residential';
  if (code >= 10 && code <= 39) return 'Commercial';
  if (code >= 40 && code <= 49) return 'Industrial';
  if (code >= 51 && code <= 69) return 'Agricultural';
  if (code >= 71 && code <= 79) return 'Institutional';
  if (code >= 81 && code <= 89) return 'Government';
  if (code === 0 || code >= 90) return 'Vacant Land';

  return 'Unknown';
}

/**
 * Get property subtype for display (e.g., "Single Family", "Condominium")
 * Returns detailed subtype if available, otherwise falls back to category
 * Handles both numeric codes ('01', '043') and text codes ('SFR', 'MFR')
 */
export function getPropertySubtype(propertyUse: string | null | undefined): string {
  if (!propertyUse) return 'Unknown';

  // Check for text codes first
  const upperCode = propertyUse.toUpperCase().trim();
  if (TEXT_CODE_MAP[upperCode]) {
    const numericCode = TEXT_CODE_MAP[upperCode];
    // Get the text description for common codes
    if (upperCode === 'SFR') return 'Single Family';
    if (upperCode === 'MFR') return 'Multi-Family';
    if (upperCode === 'CONDO') return 'Condominium';
    // Otherwise use numeric code
    return getPropertySubtype(String(numericCode));
  }

  // Try to get specific subtype from numeric code
  const subtype = PROPERTY_SUBTYPE_MAP[propertyUse];
  if (subtype) return subtype;

  // Fall back to general category
  return getPropertyCategory(propertyUse);
}

/**
 * Get DOR codes for a property type category
 * Used for filtering properties by type
 */
export function getCodesForPropertyType(propertyType: string): string[] {
  const normalized = propertyType.toLowerCase().replace(/\s+/g, '');

  // Handle common variations
  const normalizedKey = normalized === 'vacant' ? 'vacantLand' : normalized;

  const codes = PROPERTY_TYPE_CODES[normalizedKey as keyof typeof PROPERTY_TYPE_CODES];
  return codes ? [...codes] : []; // Convert readonly array to mutable array
}

/**
 * Map display name to internal key
 */
export function mapPropertyTypeToKey(propertyType: string): keyof typeof PROPERTY_TYPE_CODES | null {
  const normalized = propertyType.toLowerCase().replace(/\s+/g, '');

  const mapping: Record<string, keyof typeof PROPERTY_TYPE_CODES> = {
    'residential': 'residential',
    'commercial': 'commercial',
    'industrial': 'industrial',
    'agricultural': 'agricultural',
    'institutional': 'institutional',
    'government': 'government',
    'vacantland': 'vacantLand',
    'vacant': 'vacantLand'
  };

  return mapping[normalized] || null;
}

/**
 * Maps property type categories to their standardized_property_use values
 * These are the actual values stored in the database standardized_property_use column
 * Updated 2025-11-03 - Comprehensive subtype mappings based on DOR codes 0-99
 */
export const STANDARDIZED_PROPERTY_USE_MAP: Record<string, string[]> = {
  'Residential': [
    'Single Family Residential',  // DOR 01 - 3.3M properties
    'Condominium',                 // DOR 04 - 958K properties
    'Multi-Family',                // DOR 08 - 594K properties - small multi-family (2-9 units)
    'Mobile Home',                 // DOR 02, 09
    'Cooperative',                 // DOR 05
    'Retirement/Assisted Living',  // DOR 06
    'Manufactured/Modular'         // DOR 02
    // NOTE: 'Multi-Family 10+ Units' moved to Commercial - these are commercial-scale properties
  ],
  'Commercial': [
    'Commercial',                  // DOR 10-39 - 323K properties
    'Retail',                      // DOR 10-16
    'Office',                      // DOR 17
    'Warehouse',                   // DOR 40 (also in Industrial)
    'Mixed Use',                   // DOR 12
    'Multi-Family 10+ Units',      // DOR 03 - Large apartment buildings (commercial investments)
    'Hotel/Motel',                 // DOR 27 - Hospitality
    'Restaurant',                  // DOR 19-21
    'Financial Institution',       // DOR 23-24
    'Entertainment',               // DOR 28-31 - Theaters, bowling, amusement
    'Tourist Attraction',          // DOR 35 - Theme parks, attractions
    'Golf Course',                 // DOR 36, 38
    'Shopping Center',             // DOR 15-16, 37-38
    'Parking'                      // DOR 18, 32 - 7.5K properties
  ],
  'Industrial': [
    'Industrial',                  // DOR 40-49 - 19K properties
    'Warehouse',                   // DOR 40 - Also maps to Commercial
    'Light Manufacturing',         // DOR 41
    'Heavy Industrial',            // DOR 42
    'Railroad Property',           // DOR 43
    'Utility - Electric',          // DOR 44
    'Utility - Gas',               // DOR 45
    'Utility - Telephone',         // DOR 46
    'Utility - Water/Sewer',       // DOR 47
    'Utility - Other',             // DOR 48
    'Landfill/Solid Waste'         // DOR 49
  ],
  'Agricultural': [
    'Agricultural',                // DOR 51-69, 80-88 - 186K properties
    'Crop Land',                   // DOR 80
    'Timberland',                  // DOR 52, 81
    'Livestock',                   // DOR 53-54, 83-85
    'Orchard/Grove',               // DOR 82, 86
    'Ornamental Horticulture',     // DOR 55, 87
    'Marine Services',             // DOR 57-58
    'Specialty Farm',              // DOR 56
    'Grazing Land',                // DOR 60
    'Forest Land',                 // DOR 61
    'Aquaculture',                 // DOR 67
    'Citrus Groves'                // DOR 68
  ],
  'Vacant': [
    'Vacant Residential',          // DOR 90
    'Vacant Commercial',           // DOR 10 (when vacant)
    'Vacant Industrial',           // DOR 40 (when vacant)
    'Vacant Agricultural',         // DOR 88
    'Vacant Institutional',        // DOR 70
    'Vacant Land',                 // DOR 00
    'Vacant Government'            // DOR 90-99 (when undeveloped)
  ],
  'Government': [
    'Governmental',                // DOR 91-99 - 56K properties (note: 'Governmental' not 'Government')
    'Military/Defense',            // DOR 91
    'Parks/Recreation',            // DOR 92
    'Schools/Universities',        // DOR 93-94
    'Hospitals (Public)',          // DOR 95
    'County Government',           // DOR 96
    'State Government',            // DOR 97
    'Federal Government',          // DOR 98
    'Municipal Government'         // DOR 99
  ],
  'Institutional': [
    'Institutional',               // DOR 71-79 - 71K properties (private non-profit)
    'Church',                      // DOR 71
    'Private School',              // DOR 72
    'Private Hospital',            // DOR 73
    'Nursing Home',                // DOR 74
    'Cultural Organization',       // DOR 75
    'Charitable Service',          // DOR 76
    'Cemetery',                    // DOR 77
    'Private Recreational',        // DOR 78
    'Common Area'                  // 124K properties (HOA, shared spaces)
  ],
  'Conservation': [
    'Institutional',               // DOR 71-79 (includes conservation, parks, etc.)
    'Common Area',                 // 124K properties
    'Parks/Recreation',            // DOR 92 (public parks)
    'Forest Land'                  // DOR 61 (conservation easements)
  ],
  'Religious': [
    'Institutional',               // DOR 71-79 (churches, religious institutions)
    'Church'                       // DOR 71
  ],
  'Vacant/Special': [
    'Vacant Residential',          // DOR 90
    'Vacant Commercial',           // DOR 10 (vacant)
    'Vacant Industrial',           // DOR 40 (vacant)
    'Vacant Agricultural',         // DOR 88
    'Vacant Land',                 // DOR 00
    'Other',                       // 142 properties
    'Parking'                      // DOR 18, 32 - 7.5K properties
  ]
};

/**
 * Get standardized property use values for filtering
 * Returns array of standardized_property_use values for the given category
 * Used for filtering on standardized_property_use column (NOT property_use DOR codes)
 */
export function getStandardizedPropertyUseValues(propertyType: string): string[] {
  // Handle variations of property type names
  const normalized = propertyType.trim();

  // Direct match
  if (STANDARDIZED_PROPERTY_USE_MAP[normalized]) {
    return STANDARDIZED_PROPERTY_USE_MAP[normalized];
  }

  // Try case-insensitive match
  const key = Object.keys(STANDARDIZED_PROPERTY_USE_MAP).find(
    k => k.toLowerCase() === normalized.toLowerCase()
  );

  if (key) {
    return STANDARDIZED_PROPERTY_USE_MAP[key];
  }

  // Return empty array if no match found
  return [];
}

/**
 * Expected property counts by type (from database audit)
 * Used for validation and testing
 *
 * DATABASE TOTALS (as of 2025-11-03):
 * - Total properties in florida_parcels: 9,113,150
 * - Main categories (below): 5,010,823 (55%)
 * - Additional categories: 131,500 (1.4%)
 * - Unclassified/NULL: 3,970,827 (43.5%)
 *
 * NOTE: ~1.4M properties have NULL standardized_property_use (not yet standardized from DOR data)
 * NOTE: ~2.5M properties are in undocumented property type categories
 */
export const EXPECTED_PROPERTY_COUNTS = {
  // Main property categories (from previous audit)
  residential: 3647262,      // Single Family, Condo, Multi-Family 2-9, Mobile Home
  commercial: 157008,        // Commercial, Retail, Office, Mixed Use, Multi-Family 10+
  industrial: 41964,         // Industrial, Warehouse
  agricultural: 127476,      // Agricultural, Farms
  institutional: 22454,      // Institutional, Churches, Parks
  government: 91016,         // Governmental properties
  vacantLand: 923643,        // Vacant Residential/Commercial/Industrial/Land

  // Additional documented categories (from 2025-10-31 audit comments)
  commonArea: 124000,        // Common Area (HOA, shared spaces)
  parking: 7500,             // Parking lots

  // Unclassified properties (NULL + undocumented types)
  // This includes ~1.4M with NULL standardized_property_use + ~2.5M in undocumented types
  unclassified: 3970827      // NULL values + undocumented property types (balances to 9.1M total)
} as const;
