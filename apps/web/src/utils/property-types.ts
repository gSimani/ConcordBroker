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
 */
const PROPERTY_SUBTYPE_MAP: Record<string, string> = {
  // Residential (01-09)
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

  // Commercial (10-39) - Key subtypes
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
  '27': 'Hotel/Motel',
  '28': 'Bowling Alley',
  '29': 'Theater',
  '30': 'Nightclub/Bar',
  '31': 'Marina',
  '32': 'Parking Lot',
  '33': 'Mobile Home Park (Commercial)',
  '34': 'Campground/RV Park',
  '35': 'Race Track',
  '36': 'Golf Course',
  '37': 'Enclosed Mall',
  '38': 'Open Mall',
  '39': 'Special Commercial',

  // Industrial (40-49)
  '40': 'Distribution Terminal',
  '41': 'Heavy Manufacturing',
  '42': 'Light Manufacturing',
  '43': 'Lumber Yard',
  '44': 'Packing Plant',
  '45': 'Cannery',
  '46': 'Other Food Processing',
  '47': 'Mineral Processing',
  '48': 'Solid Waste/Landfill',
  '49': 'Special Industrial',

  // Agricultural (51-69) - Key subtypes
  '51': 'Crop/Pasture',
  '52': 'Timberland',
  '53': 'Poultry/Bees',
  '54': 'Dairies/Feed Lots',
  '55': 'Ornamentals/Nursery',
  '56': 'Specialty Farm',
  '57': 'Agricultural - Other',
  '58': 'Vacant Agricultural',
  '59': 'Residential with Ag Exemption',
  '60': 'Grazing Land',
  '61': 'Forest Land',
  '62': 'Improved Agricultural',
  '63': 'Unimproved Agricultural',

  // Institutional (71-79)
  '71': 'Church/Synagogue',
  '72': 'Private School',
  '73': 'Private Hospital',
  '74': 'Convalescent/Nursing Home',
  '75': 'Cultural Organization',
  '76': 'Charitable Service',
  '77': 'Mortuary/Cemetery',
  '78': 'Private Recreational',
  '79': 'Special Institutional',

  // Government (81-89)
  '81': 'Military',
  '82': 'Forest/Parks',
  '83': 'Public School',
  '84': 'Public Hospital',
  '85': 'Government Office',
  '86': 'Government Service',
  '87': 'Government Airport',
  '88': 'Government Housing',
  '89': 'Special Government',

  // Vacant Land (00, 90-99)
  '00': 'Vacant Land',
  '0': 'Vacant Land',
  '90': 'Vacant Residential',
  '91': 'Vacant Commercial',
  '92': 'Vacant Industrial',
  '93': 'Vacant Institutional',
  '94': 'Vacant Government',
  '95': 'Vacant Agricultural',
  '96': 'Vacant Subsurface Rights',
  '97': 'Vacant Right-of-Way',
  '98': 'Vacant Easement',
  '99': 'Special Vacant'
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
 * Updated 2025-10-31 based on comprehensive database audit of 10.3M properties
 */
export const STANDARDIZED_PROPERTY_USE_MAP: Record<string, string[]> = {
  'Residential': [
    'Single Family Residential',  // 3.3M properties
    'Condominium',                 // 958K properties
    'Multi-Family',                // 594K properties
    'Multi-Family 10+ Units',
    'Mobile Home'
  ],
  'Commercial': [
    'Commercial',                  // 323K properties
    'Retail',
    'Office',
    'Warehouse',
    'Mixed Use'
  ],
  'Industrial': [
    'Industrial',                  // 19K properties
    'Warehouse'                    // Note: Warehouse maps to both Commercial and Industrial
  ],
  'Agricultural': [
    'Agricultural'                 // 186K properties
  ],
  'Vacant': [
    'Vacant Residential',
    'Vacant Commercial',
    'Vacant Industrial',
    'Vacant Land'
  ],
  'Government': [
    'Governmental'                 // 56K properties (note: 'Governmental' not 'Government')
  ],
  'Conservation': [
    'Institutional',               // 71K properties (includes conservation, parks, etc.)
    'Common Area'                  // 124K properties
  ],
  'Religious': [
    'Institutional',               // 71K properties (churches, religious institutions)
    'Church'
  ],
  'Vacant/Special': [
    'Vacant Residential',
    'Vacant Commercial',
    'Vacant Industrial',
    'Vacant Land',
    'Other',                       // 142 properties
    'Parking'                      // 7.5K properties
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
 */
export const EXPECTED_PROPERTY_COUNTS = {
  residential: 3647262,
  commercial: 157008,
  industrial: 41964,
  agricultural: 127476,
  institutional: 22454,
  government: 91016,
  vacantLand: 923643
} as const;
