/**
 * Property USE to DOR Code Mapping System
 *
 * Maps text property_use codes from Supabase database to numeric DOR use codes
 * for icon mapping and display purposes.
 *
 * Background:
 * - NAL CSV files have DOR_UC column with 3-digit codes (e.g., "082")
 * - Supabase database has property_use TEXT column (e.g., "SFR", "MF_10PLUS")
 * - Icon system expects DOR codes, so we map text → DOR codes
 */

export const PROPERTY_USE_TO_DOR_CODE: Record<string, string> = {
  // ═══════════════════════════════════════════════════
  // RESIDENTIAL (001-009)
  // ═══════════════════════════════════════════════════
  'SFR': '001',              // Single Family Residential
  'SINGLE_FAMILY': '001',    // Alternate name
  'RES': '001',              // Generic residential
  'RESIDENTIAL': '001',      // Generic residential

  'CONDO': '004',            // Condominium
  'CONDOMINIUM': '004',      // Full spelling

  'TIMESHARE': '005',        // Timeshare (actually Co-op in DOR)

  'MOBILE': '002',           // Mobile Home
  'MOBILE_HOME': '002',      // Alternate name
  'MH': '002',               // Abbreviation

  'MF_2-9': '008',           // Multi-Family 2-9 units (less than 10)
  'MF2': '008',              // Alternate format
  'DUPLEX': '008',           // 2 units
  'TRIPLEX': '008',          // 3 units
  'FOURPLEX': '008',         // 4 units

  'MF_10PLUS': '003',        // Multi-Family 10+ units
  'MF10': '003',             // Alternate format
  'APARTMENT': '003',        // Common term
  'APARTMENTS': '003',       // Plural

  // ═══════════════════════════════════════════════════
  // VACANT (000, 010, 040, 070, 080, 099)
  // ═══════════════════════════════════════════════════
  'VAC_RES': '000',          // Vacant Residential
  'VACANT_RES': '000',       // Alternate format

  'VAC': '099',              // Vacant Land (general)
  'VACANT': '099',           // Vacant Land
  'VACANT_LAND': '099',      // Full description

  // ═══════════════════════════════════════════════════
  // COMMERCIAL (003, 010-039)
  // ═══════════════════════════════════════════════════
  'COM': '011',              // Commercial (general)
  'COMMERCIAL': '011',       // Full spelling

  'PARKING': '028',          // Parking Lot/Garage
  'PARKING_LOT': '028',      // Specific type
  'GARAGE': '028',           // Parking garage

  'STORE': '011',            // Retail Store (one story)
  'RETAIL': '011',           // Generic retail
  'SHOP': '011',             // Small store

  'DEPT_STORE': '013',       // Department Store
  'SUPERMARKET': '014',      // Supermarket
  'GROCERY': '014',          // Grocery store

  'SHOPPING_CENTER': '015',  // Regional Shopping Center
  'MALL': '015',             // Shopping mall

  'OFFICE': '017',           // Office Building (one story)
  'OFFICE_BUILDING': '017',  // Full description
  'PROFESSIONAL': '019',     // Professional office

  'OFFICE_MULTI': '018',     // Office Building (multi-story)
  'OFFICE_TOWER': '018',     // High-rise office

  'REST': '021',             // Restaurant/Cafeteria
  'RESTAURANT': '021',       // Full spelling
  'CAFE': '021',             // Cafe
  'EATERY': '021',           // Casual dining

  'DRIVE_IN': '022',         // Drive-in Restaurant
  'FAST_FOOD': '022',        // Fast food

  'BANK': '023',             // Bank/Savings & Loan
  'FINANCIAL': '023',        // Financial institution

  'HOTEL': '039',            // Hotel/Motel
  'MOTEL': '039',            // Motel
  'INN': '039',              // Inn

  // ═══════════════════════════════════════════════════
  // INDUSTRIAL (040-049)
  // ═══════════════════════════════════════════════════
  'IND': '041',              // Industrial (general)
  'INDUSTRIAL': '041',       // Full spelling

  'FACTORY': '041',          // Light Manufacturing
  'MANUFACTURING': '041',    // Manufacturing facility
  'PLANT': '041',            // Industrial plant

  'HEAVY_IND': '042',        // Heavy Industrial
  'HEAVY_INDUSTRIAL': '042', // Full description

  'LUMBER': '043',           // Lumber Yard
  'LUMBERYARD': '043',       // Alternate format

  'PACKING': '044',          // Packing/Processing Plant
  'PROCESSING': '044',       // Processing facility

  'WAREHOUSE': '048',        // Warehouse/Distribution
  'DISTRIBUTION': '048',     // Distribution center
  'STORAGE': '048',          // Storage facility

  // ═══════════════════════════════════════════════════
  // AGRICULTURAL (050-069)
  // ═══════════════════════════════════════════════════
  'AGR': '050',              // Agricultural (general)
  'AGRICULTURAL': '050',     // Full spelling
  'FARM': '050',             // Farm
  'FARMLAND': '050',         // Farmland

  'GROVE': '066',            // Groves/Orchards
  'ORCHARD': '066',          // Orchard
  'CITRUS': '066',           // Citrus grove

  'RANCH': '068',            // Cattle Ranch (actually Dairies/feed lots)
  'CATTLE': '068',           // Cattle operation

  'TIMBER': '054',           // Timberland
  'FOREST': '054',           // Forest land
  'WOODS': '054',            // Wooded area

  // ═══════════════════════════════════════════════════
  // INSTITUTIONAL (070-079)
  // ═══════════════════════════════════════════════════
  'INST': '070',             // Institutional (general)
  'INSTITUTIONAL': '070',    // Full spelling

  'REL': '071',              // Religious
  'RELIGIOUS': '071',        // Full spelling
  'CHURCH': '071',           // Church
  'TEMPLE': '071',           // Temple
  'SYNAGOGUE': '071',        // Synagogue
  'MOSQUE': '071',           // Mosque

  'EDU': '072',              // Educational
  'EDUCATIONAL': '072',      // Full spelling
  'SCHOOL': '072',           // School
  'COLLEGE': '072',          // College
  'UNIVERSITY': '072',       // University

  'HOSP': '073',             // Hospital/Healthcare
  'HOSPITAL': '073',         // Full spelling
  'MEDICAL': '073',          // Medical facility
  'CLINIC': '073',           // Medical clinic
  'HEALTHCARE': '073',       // Healthcare facility

  // ═══════════════════════════════════════════════════
  // GOVERNMENTAL (080-089)
  // ═══════════════════════════════════════════════════
  'GOV': '086',              // Governmental (general)
  'GOVT': '086',             // Abbreviation
  'GOVERNMENT': '086',       // Full spelling
  'MUNICIPAL': '089',        // Municipal building

  'MIL': '081',              // Military
  'MILITARY': '081',         // Full spelling

  'PARK': '082',             // Parks (government-owned)
  'RECREATION': '082',       // Recreation area
  'FOREST_PARK': '082',      // Forest park

  // ═══════════════════════════════════════════════════
  // SPECIAL/OTHER (090-099)
  // ═══════════════════════════════════════════════════
  'UTIL': '091',             // Utility
  'UTILITY': '091',          // Full spelling
  'UTILITIES': '091',        // Plural

  'CEMETERY': '076',         // Cemetery
  'GRAVEYARD': '076',        // Alternate term

  'UNKNOWN': '099',          // Unknown/Other
  'OTHER': '099',            // Other
  'MISC': '099',             // Miscellaneous
};

/**
 * Get DOR code from property_use (handles both numeric DOR codes and text codes)
 *
 * @param propertyUse - Can be:
 *   - Numeric DOR code: "1", "2", "55", "082" (will be formatted to "001", "002", "055", "082")
 *   - Text code: "SFR", "MF_10PLUS", "Condo" (will be mapped to DOR codes)
 * @returns DOR use code (e.g., "001", "002", "055", "082")
 */
export function getDorCodeFromPropertyUse(propertyUse: string | undefined | null): string {
  if (!propertyUse) return '001'; // Default to Single Family Residential

  // Normalize input: uppercase and trim
  const upperUse = propertyUse.toUpperCase().trim();

  // CHECK 1: Is this already a numeric DOR code? (e.g., "1", "55", "082")
  if (/^\d+$/.test(upperUse)) {
    // It's a number - format it as 3-digit DOR code with leading zeros
    return upperUse.padStart(3, '0');
  }

  // CHECK 2: Direct text code lookup (e.g., "SFR" -> "001", "CONDO" -> "004")
  const dorCode = PROPERTY_USE_TO_DOR_CODE[upperUse];
  if (dorCode) return dorCode;

  // CHECK 3: Partial text matching for fallback
  if (upperUse.includes('RESIDENTIAL') || upperUse.includes('FAMILY')) return '001';
  if (upperUse.includes('CONDO')) return '004';
  if (upperUse.includes('MOBILE')) return '002';
  if (upperUse.includes('MULTI') || upperUse.includes('APART')) return '003';
  if (upperUse.includes('VACANT') || upperUse.includes('VAC')) return '000';
  if (upperUse.includes('COMMERCIAL') || upperUse.includes('COM')) return '011';
  if (upperUse.includes('RETAIL') || upperUse.includes('STORE')) return '011';
  if (upperUse.includes('OFFICE')) return '017';
  if (upperUse.includes('RESTAURANT') || upperUse.includes('REST')) return '021';
  if (upperUse.includes('HOTEL') || upperUse.includes('MOTEL')) return '039';
  if (upperUse.includes('INDUSTRIAL') || upperUse.includes('IND')) return '041';
  if (upperUse.includes('WAREHOUSE')) return '048';
  if (upperUse.includes('AGRICULTURAL') || upperUse.includes('FARM')) return '050';
  if (upperUse.includes('RELIGIOUS') || upperUse.includes('CHURCH')) return '071';
  if (upperUse.includes('SCHOOL') || upperUse.includes('EDUCATION')) return '072';
  if (upperUse.includes('HOSPITAL') || upperUse.includes('MEDICAL')) return '073';
  if (upperUse.includes('GOVERNMENT') || upperUse.includes('GOV')) return '086';

  // Final fallback
  return '001'; // Default to Single Family Residential
}

/**
 * Get human-readable description from property_use code
 *
 * @param propertyUse - Text code from database (e.g., "SFR", "MF_10PLUS")
 * @returns Human-readable description (e.g., "Single Family", "Apartment Complex")
 */
export function getPropertyUseDescription(propertyUse: string | undefined | null): string {
  if (!propertyUse) return 'Residential';

  const descriptions: Record<string, string> = {
    // Residential
    'SFR': 'Single Family',
    'SINGLE_FAMILY': 'Single Family',
    'MF_2-9': 'Multi-Family',
    'MF_10PLUS': 'Apartment Complex',
    'CONDO': 'Condominium',
    'CONDOMINIUM': 'Condominium',
    'MOBILE': 'Mobile Home',
    'MOBILE_HOME': 'Mobile Home',
    'TIMESHARE': 'Timeshare',

    // Vacant
    'VAC_RES': 'Vacant Residential',
    'VACANT_RES': 'Vacant Residential',
    'VAC': 'Vacant Land',
    'VACANT': 'Vacant Land',
    'VACANT_LAND': 'Vacant Land',

    // Commercial
    'COM': 'Commercial',
    'COMMERCIAL': 'Commercial',
    'STORE': 'Retail Store',
    'RETAIL': 'Retail',
    'OFFICE': 'Office',
    'OFFICE_BUILDING': 'Office Building',
    'REST': 'Restaurant',
    'RESTAURANT': 'Restaurant',
    'BANK': 'Bank',
    'FINANCIAL': 'Financial',
    'HOTEL': 'Hotel',
    'MOTEL': 'Motel',
    'PARKING': 'Parking',
    'MALL': 'Shopping Center',

    // Industrial
    'IND': 'Industrial',
    'INDUSTRIAL': 'Industrial',
    'FACTORY': 'Factory',
    'MANUFACTURING': 'Manufacturing',
    'WAREHOUSE': 'Warehouse',
    'DISTRIBUTION': 'Distribution Center',

    // Agricultural
    'AGR': 'Agricultural',
    'AGRICULTURAL': 'Agricultural',
    'FARM': 'Farm',
    'GROVE': 'Grove',
    'RANCH': 'Ranch',

    // Institutional
    'INST': 'Institutional',
    'INSTITUTIONAL': 'Institutional',
    'REL': 'Religious',
    'RELIGIOUS': 'Religious',
    'CHURCH': 'Church',
    'EDU': 'Educational',
    'EDUCATIONAL': 'Educational',
    'SCHOOL': 'School',
    'HOSP': 'Hospital',
    'HOSPITAL': 'Hospital',
    'MEDICAL': 'Medical',

    // Governmental
    'GOV': 'Government',
    'GOVT': 'Government',
    'GOVERNMENT': 'Government',
    'MIL': 'Military',
    'PARK': 'Park',

    // Other
    'UTIL': 'Utility',
    'UTILITY': 'Utility',
    'CEMETERY': 'Cemetery',
    'UNKNOWN': 'Other',
  };

  const upperUse = propertyUse.toUpperCase();
  return descriptions[upperUse] || 'Property';
}

/**
 * Get category from property_use code (for filtering)
 *
 * @param propertyUse - Text code from database
 * @returns Category name (e.g., "Residential", "Commercial")
 */
export function getPropertyCategory(propertyUse: string | undefined | null): string {
  if (!propertyUse) return 'Residential';

  const upperUse = propertyUse.toUpperCase();

  // Residential
  if (['SFR', 'SINGLE_FAMILY', 'MF_2-9', 'MF_10PLUS', 'CONDO', 'MOBILE', 'TIMESHARE'].includes(upperUse)) {
    return 'Residential';
  }

  // Vacant
  if (['VAC', 'VACANT', 'VAC_RES', 'VACANT_RES', 'VACANT_LAND'].includes(upperUse)) {
    return 'Vacant';
  }

  // Commercial
  if (upperUse.includes('COM') || upperUse.includes('STORE') || upperUse.includes('OFFICE') ||
      upperUse.includes('REST') || upperUse.includes('BANK') || upperUse.includes('HOTEL')) {
    return 'Commercial';
  }

  // Industrial
  if (upperUse.includes('IND') || upperUse.includes('FACTORY') || upperUse.includes('WAREHOUSE')) {
    return 'Industrial';
  }

  // Agricultural
  if (upperUse.includes('AGR') || upperUse.includes('FARM') || upperUse.includes('GROVE') || upperUse.includes('RANCH')) {
    return 'Agricultural';
  }

  // Institutional
  if (upperUse.includes('REL') || upperUse.includes('CHURCH') || upperUse.includes('EDU') ||
      upperUse.includes('SCHOOL') || upperUse.includes('HOSP')) {
    return 'Institutional';
  }

  // Governmental
  if (upperUse.includes('GOV') || upperUse.includes('MIL') || upperUse.includes('PARK')) {
    return 'Governmental';
  }

  return 'Other';
}
