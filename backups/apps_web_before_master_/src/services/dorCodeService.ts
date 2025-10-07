/**
 * DOR Code Service for Property Use Code filtering
 * Provides autocomplete and mapping functionality for Florida DOR codes
 */

import { DOR_USE_CODES, DORUseCode } from '@/lib/dorUseCodes';

// Sub-usage codes for each main category
export const DOR_SUB_CODES: Record<string, Array<{code: string, description: string}>> = {
  // Residential sub-codes
  '001': [
    { code: '00', description: 'Standard single family' },
    { code: '01', description: 'Waterfront' },
    { code: '02', description: 'Golf course' },
    { code: '03', description: 'Gated community' },
    { code: '04', description: 'Historic home' },
    { code: '05', description: 'Estate home' }
  ],
  '002': [
    { code: '00', description: 'Standard mobile home' },
    { code: '01', description: 'Double-wide' },
    { code: '02', description: 'In park' },
    { code: '03', description: 'On own land' }
  ],
  '004': [
    { code: '00', description: 'Standard condo' },
    { code: '01', description: 'High-rise' },
    { code: '02', description: 'Townhouse style' },
    { code: '03', description: 'Waterfront condo' },
    { code: '04', description: 'Penthouse' }
  ],
  '008': [
    { code: '00', description: 'Duplex' },
    { code: '01', description: 'Triplex' },
    { code: '02', description: 'Quadplex' },
    { code: '03', description: '5-9 units' }
  ],
  // Commercial sub-codes
  '011': [
    { code: '00', description: 'General retail' },
    { code: '01', description: 'Strip mall store' },
    { code: '02', description: 'Stand-alone store' },
    { code: '03', description: 'Big box store' }
  ],
  '017': [
    { code: '00', description: 'General office' },
    { code: '01', description: 'Medical office' },
    { code: '02', description: 'Professional office' },
    { code: '03', description: 'Tech office' }
  ],
  '039': [
    { code: '00', description: 'Standard hotel' },
    { code: '01', description: 'Resort hotel' },
    { code: '02', description: 'Budget motel' },
    { code: '03', description: 'Extended stay' },
    { code: '04', description: 'Beach resort' }
  ],
  // Industrial sub-codes
  '041': [
    { code: '00', description: 'General light manufacturing' },
    { code: '01', description: 'Assembly plant' },
    { code: '02', description: 'Tech manufacturing' },
    { code: '03', description: 'Food processing' }
  ],
  '048': [
    { code: '00', description: 'General warehouse' },
    { code: '01', description: 'Distribution center' },
    { code: '02', description: 'Cold storage' },
    { code: '03', description: 'Fulfillment center' }
  ],
  // Agricultural sub-codes
  '066': [
    { code: '00', description: 'General grove' },
    { code: '01', description: 'Orange grove' },
    { code: '02', description: 'Grapefruit grove' },
    { code: '03', description: 'Mixed citrus' }
  ],
  '050': [
    { code: '00', description: 'General farm' },
    { code: '01', description: 'Crop farm' },
    { code: '02', description: 'Livestock farm' },
    { code: '03', description: 'Dairy farm' }
  ]
};

// Map property type categories to actual database property_use values
// Based on actual analysis of florida_parcels table in Supabase (Dec 2024)
// Analysis found 18 distinct property_use codes from 88,000+ properties
export const PROPERTY_TYPE_TO_DB_VALUES: Record<string, number[]> = {
  'Residential': [0, 1, 2, 4, 8, 9], // 0=Vacant Res, 1=Single Family, 2=Mobile, 4=Condo, 8=Multi-Family, 9=Other Res
  'Commercial': [11, 19, 28], // 11=Stores, 19=Professional Services, 28=Parking
  'Industrial': [48, 52, 60], // 48=Warehousing, 52=Other Industrial, 60=Light Manufacturing
  'Agricultural': [80, 87], // 80=Undefined Agr, 87=Agr (Citrus)
  'Vacant Land': [0], // Vacant Residential
  'Vacant': [0], // Keep both for compatibility
  'Condo': [4], // Condominiums
  'Multi-Family': [8], // Multi-Family (10 units or more)
  'Institutional': [71], // Churches, Temples
  'Religious': [71], // Religious institutions
  'Government': [93, 96], // 93=Gov Municipal, 96=Gov Federal
  'Governmental': [93, 96], // Keep both for compatibility
  'Conservation': [], // Not found in current dataset
  'Special': [], // Not found in current dataset
  'Vacant/Special': [0] // Vacant Residential only
};

// Legacy DOR code mapping (kept for backward compatibility)
export const PROPERTY_TYPE_TO_DOR_CODES: Record<string, string[]> = {
  'Residential': ['000', '001', '002', '004', '005', '006', '007', '008', '009'],
  'Commercial': ['003', '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',
                 '020', '021', '022', '023', '024', '025', '026', '027', '028', '029',
                 '030', '031', '032', '033', '034', '035', '036', '037', '038', '039'],
  'Industrial': ['040', '041', '042', '043', '044', '045', '046', '047', '048', '049'],
  'Agricultural': ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059',
                   '060', '061', '062', '063', '064', '065', '066', '067', '068', '069'],
  'Institutional': ['070', '071', '072', '073', '074', '075', '076', '077', '078', '079'],
  'Governmental': ['080', '081', '082', '083', '084', '085', '086', '087', '088', '089'],
  'Vacant Land': ['000', '010', '040', '070', '090'],
  'Vacant': ['000', '010', '040', '070', '090'], // Support both 'Vacant' and 'Vacant Land'
  'Conservation': ['095', '096', '097'],
  'Religious': ['071'],
  'Government': ['080', '081', '082', '083', '084', '085', '086', '087', '088', '089'],
  'Vacant/Special': ['090', '091', '092', '093', '094', '095', '096', '097', '098', '099']
};

/**
 * Get DOR code suggestions based on search query
 * @param query - The search string
 * @param category - Optional category filter
 * @returns Array of matching DOR codes
 */
export function getDORCodeSuggestions(query: string, category?: string): DORUseCode[] {
  const searchTerm = query.toLowerCase().trim();

  let codes = Object.values(DOR_USE_CODES);

  // Filter by category if provided
  if (category && PROPERTY_TYPE_TO_DOR_CODES[category]) {
    const allowedCodes = PROPERTY_TYPE_TO_DOR_CODES[category];
    codes = codes.filter(code => allowedCodes.includes(code.code));
  }

  // Filter by search term
  if (searchTerm) {
    codes = codes.filter(code =>
      code.code.startsWith(searchTerm) ||
      code.description.toLowerCase().includes(searchTerm) ||
      code.shortName.toLowerCase().includes(searchTerm)
    );
  }

  // Sort by code
  codes.sort((a, b) => a.code.localeCompare(b.code));

  // Limit to top 20 results
  return codes.slice(0, 20);
}

/**
 * Get sub-usage code suggestions based on main usage code
 * @param mainCode - The main DOR code (e.g., '001')
 * @param query - Optional search string
 * @returns Array of sub-codes
 */
export function getSubCodeSuggestions(mainCode: string, query?: string): Array<{code: string, description: string, display: string}> {
  const subCodes = DOR_SUB_CODES[mainCode] || [];

  if (!query) {
    return subCodes.map(sub => ({
      ...sub,
      display: `${sub.code} - ${sub.description}`
    }));
  }

  const searchTerm = query.toLowerCase().trim();
  const filtered = subCodes.filter(sub =>
    sub.code.startsWith(searchTerm) ||
    sub.description.toLowerCase().includes(searchTerm)
  );

  return filtered.map(sub => ({
    ...sub,
    display: `${sub.code} - ${sub.description}`
  }));
}

/**
 * Get database property_use values for a property type filter
 * @param propertyType - The property type (e.g., 'Residential', 'Commercial')
 * @returns Array of property_use integer values
 */
export function getPropertyUseValuesForType(propertyType: string): number[] {
  return PROPERTY_TYPE_TO_DB_VALUES[propertyType] || [];
}

/**
 * Get DOR codes for a property type filter (legacy support)
 * @param propertyType - The property type (e.g., 'Residential', 'Commercial')
 * @returns Array of DOR codes
 */
export function getDORCodesForPropertyType(propertyType: string): string[] {
  return PROPERTY_TYPE_TO_DOR_CODES[propertyType] || [];
}

/**
 * Convert property type filter to use_category values for API
 * @param propertyType - The property type from UI filter
 * @returns Array of use_category values for API
 */
export function mapPropertyTypeToUseCategories(propertyType: string): string[] {
  const categoryMap: Record<string, string[]> = {
    'Residential': ['Residential', 'Single Family', 'Condo', 'Townhouse', 'Mobile Home'],
    'Commercial': ['Commercial', 'Retail', 'Office', 'Hotel/Motel', 'Shopping Center'],
    'Industrial': ['Industrial', 'Warehouse', 'Manufacturing', 'Distribution'],
    'Agricultural': ['Agricultural', 'Farm', 'Ranch', 'Grove', 'Timber'],
    'Vacant Land': ['Vacant Land', 'Vacant Residential', 'Vacant Commercial', 'Vacant Industrial'],
    'Vacant': ['Vacant Land', 'Vacant Residential', 'Vacant Commercial', 'Vacant Industrial'], // Support both 'Vacant' and 'Vacant Land'
    'Government': ['Government', 'Governmental', 'Public'],
    'Conservation': ['Conservation', 'Nature Preserve', 'Wildlife'],
    'Religious': ['Religious', 'Church', 'Temple', 'Worship'],
    'Vacant/Special': ['Vacant', 'Special', 'Other', 'Miscellaneous']
  };

  return categoryMap[propertyType] || [];
}

/**
 * Convert property type filter to database property_use values for API filtering
 * This is the new preferred method for filtering based on actual database schema
 * @param propertyType - The property type from UI filter
 * @returns Array of property_use integer values
 */
export function mapPropertyTypeToPropertyUseValues(propertyType: string): number[] {
  return getPropertyUseValuesForType(propertyType);
}

/**
 * Get a description for a full DOR code (main + sub)
 * @param mainCode - The main DOR code
 * @param subCode - The sub-code
 * @returns Description string
 */
export function getDORCodeDescription(mainCode: string, subCode?: string): string {
  const main = DOR_USE_CODES[mainCode];
  if (!main) return 'Unknown';

  if (!subCode || subCode === '00') {
    return main.description;
  }

  const subCodes = DOR_SUB_CODES[mainCode];
  if (subCodes) {
    const sub = subCodes.find(s => s.code === subCode);
    if (sub) {
      return `${main.shortName} - ${sub.description}`;
    }
  }

  return main.description;
}