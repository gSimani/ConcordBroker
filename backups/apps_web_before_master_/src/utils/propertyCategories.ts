// Property category utility functions extracted from MiniPropertyCard.tsx
// Updated to handle actual database values from Supabase florida_parcels table

// Map actual database property_use integer values to categories
// Based on actual analysis of florida_parcels table (Dec 2024)
const PROPERTY_USE_TO_CATEGORY: Record<number, string> = {
  0: 'Vacant Land', // Vacant Residential
  1: 'Residential', // Single Family Residential
  2: 'Residential', // Mobile Homes
  4: 'Condo', // Condominiums
  8: 'Multi-Family', // Multi-Family (10 units or more)
  9: 'Residential', // Undefined/Misc Residential
  11: 'Commercial', // Stores, One Story
  19: 'Commercial', // Professional Services Buildings
  28: 'Commercial', // Parking Lots (Mobile Home Parks)
  48: 'Industrial', // Warehousing, Distribution Terminals
  52: 'Industrial', // Other Industrial
  60: 'Industrial', // Light Manufacturing
  71: 'Religious', // Churches, Temples
  80: 'Agricultural', // Undefined Agricultural
  87: 'Agricultural', // Agricultural (Citrus)
  93: 'Government', // Government Municipal Service
  96: 'Government' // Government Federal
};

// Map 3-digit DOR codes to categories (from property_sales_history)
const DOR_CODE_TO_CATEGORY: Record<string, string> = {
  '000': 'Vacant Land', // Match filter button text
  '001': 'Residential',
  '009': 'Residential',
  '094': 'Special'
};

export const getPropertyCategoryFromCode = (propertyUse?: string | number, propertyUseDesc?: string): string => {
  // Handle null/undefined values
  if (propertyUse === null || propertyUse === undefined) {
    return propertyUseDesc?.toLowerCase().includes('vacant') ? 'Vacant Land' : 'Other';
  }

  // Handle integer property_use values from database
  if (typeof propertyUse === 'number') {
    return PROPERTY_USE_TO_CATEGORY[propertyUse] || 'Other';
  }

  // Handle string values
  const code = propertyUse.toString().trim();

  // Handle empty or zero codes
  if (!code || code === '0' || code === '00' || code === '000' || code === '0000') {
    return propertyUseDesc?.toLowerCase().includes('vacant') ? 'Vacant Land' : 'Other';
  }

  // Try integer parsing first (database values)
  const intCode = parseInt(code);
  if (!isNaN(intCode) && PROPERTY_USE_TO_CATEGORY[intCode]) {
    return PROPERTY_USE_TO_CATEGORY[intCode];
  }

  // Try 3-digit DOR code mapping
  if (code.length === 3 && DOR_CODE_TO_CATEGORY[code]) {
    return DOR_CODE_TO_CATEGORY[code];
  }

  // Legacy support for padded codes (fallback)
  const codeStr = code.padStart(4, '0');
  const firstTwo = codeStr.substring(0, 2);
  const firstDigit = codeStr[0];

  // First check specific 4-digit codes
  if (codeStr >= '0100' && codeStr <= '0199') return 'Residential';
  if (codeStr >= '0200' && codeStr <= '0299') return 'Residential';
  if (codeStr >= '0300' && codeStr <= '0399') return 'Multi-Family';
  if (codeStr >= '0400' && codeStr <= '0499') return 'Condo';
  if (codeStr >= '0800' && codeStr <= '0899') return 'Multi-Family';

  // Then check by first two digits
  if (firstTwo === '01' || firstTwo === '02' || firstTwo === '03' || firstTwo === '04' || firstTwo === '05' || firstTwo === '09') return 'Residential';
  if (firstTwo === '08') return 'Multi-Family';
  if (firstTwo === '10' || firstTwo === '11' || firstTwo === '12' || firstTwo === '13' ||
      firstTwo === '14' || firstTwo === '15' || firstTwo === '16' || firstTwo === '17' ||
      firstTwo === '18' || firstTwo === '19') return 'Commercial';
  if (firstTwo === '20' || firstTwo === '21' || firstTwo === '22' || firstTwo === '23' ||
      firstTwo === '24' || firstTwo === '25' || firstTwo === '26' || firstTwo === '27' ||
      firstTwo === '28' || firstTwo === '29' || firstTwo === '30' || firstTwo === '31' ||
      firstTwo === '32' || firstTwo === '33' || firstTwo === '34' || firstTwo === '35' ||
      firstTwo === '36' || firstTwo === '37' || firstTwo === '38' || firstTwo === '39') return 'Industrial';
  if (firstTwo >= '40' && firstTwo <= '49') return 'Industrial';
  if (firstTwo >= '50' && firstTwo <= '69') return 'Agricultural';
  if (firstTwo >= '70' && firstTwo <= '79') return 'Institutional';
  if (firstTwo >= '80' && firstTwo <= '89') return 'Governmental';
  if (firstTwo >= '90' && firstTwo <= '99') return 'Special';

  // Fallback by first digit
  if (firstDigit === '1') return 'Commercial';
  if (firstDigit === '2' || firstDigit === '3' || firstDigit === '4') return 'Industrial';
  if (firstDigit === '5' || firstDigit === '6') return 'Agricultural';
  if (firstDigit === '7') return 'Institutional';
  if (firstDigit === '8') return 'Governmental';
  if (firstDigit === '9') return 'Special';

  return 'Other';
};

export const getSubUseType = (propertyUseDesc?: string, category?: string): string | null => {
  if (!propertyUseDesc) return null;

  const desc = propertyUseDesc.toLowerCase();

  // Residential subtypes
  if (category === 'Residential') {
    if (desc.includes('waterfront') || desc.includes('water front')) return 'Waterfront';
    if (desc.includes('golf')) return 'Golf Course';
    if (desc.includes('gated')) return 'Gated Community';
    if (desc.includes('historic')) return 'Historic';
    if (desc.includes('mobile home')) return 'Mobile Home';
    if (desc.includes('townhome') || desc.includes('townhouse')) return 'Townhome';
    if (desc.includes('villa')) return 'Villa';
    if (desc.includes('estate')) return 'Estate';
  }

  // Commercial subtypes
  if (category === 'Commercial') {
    if (desc.includes('retail')) return 'Retail';
    if (desc.includes('office')) return 'Office';
    if (desc.includes('restaurant')) return 'Restaurant';
    if (desc.includes('hotel') || desc.includes('motel')) return 'Hotel/Motel';
    if (desc.includes('shopping') || desc.includes('mall')) return 'Shopping Center';
    if (desc.includes('gas station') || desc.includes('service station')) return 'Gas Station';
    if (desc.includes('bank')) return 'Bank';
    if (desc.includes('medical') || desc.includes('clinic')) return 'Medical';
  }

  // Industrial subtypes
  if (category === 'Industrial') {
    if (desc.includes('warehouse')) return 'Warehouse';
    if (desc.includes('manufacturing')) return 'Manufacturing';
    if (desc.includes('distribution')) return 'Distribution';
    if (desc.includes('flex')) return 'Flex Space';
    if (desc.includes('research')) return 'R&D';
    if (desc.includes('storage')) return 'Storage';
  }

  // Agricultural subtypes
  if (category === 'Agricultural') {
    if (desc.includes('citrus') || desc.includes('grove')) return 'Citrus Grove';
    if (desc.includes('ranch')) return 'Ranch';
    if (desc.includes('farm')) return 'Farm';
    if (desc.includes('nursery')) return 'Nursery';
    if (desc.includes('pasture')) return 'Pasture';
    if (desc.includes('timber')) return 'Timber';
  }

  // Multi-family subtypes
  if (category === 'Multi-Family') {
    if (desc.includes('duplex')) return 'Duplex';
    if (desc.includes('triplex')) return 'Triplex';
    if (desc.includes('quadplex') || desc.includes('fourplex')) return 'Quadplex';
    if (desc.includes('apartment')) return 'Apartment';
    if (desc.includes('senior') || desc.includes('assisted')) return 'Senior Living';
  }

  // Vacant subtypes (handle both Vacant and Vacant Land)
  if (category === 'Vacant' || category === 'Vacant Land') {
    if (desc.includes('residential')) return 'Residential Lot';
    if (desc.includes('commercial')) return 'Commercial Lot';
    if (desc.includes('industrial')) return 'Industrial Lot';
    if (desc.includes('agricultural')) return 'Agricultural Land';
  }

  // Government subtypes
  if (category === 'Government' || category === 'Governmental') {
    if (desc.includes('school')) return 'School';
    if (desc.includes('hospital')) return 'Hospital';
    if (desc.includes('fire')) return 'Fire Station';
    if (desc.includes('police')) return 'Police Station';
    if (desc.includes('court')) return 'Courthouse';
    if (desc.includes('municipal')) return 'Municipal';
  }

  // Religious subtypes
  if (category === 'Religious') {
    if (desc.includes('church')) return 'Church';
    if (desc.includes('temple')) return 'Temple';
    if (desc.includes('mosque')) return 'Mosque';
    if (desc.includes('synagogue')) return 'Synagogue';
  }

  // Conservation subtypes
  if (category === 'Conservation') {
    if (desc.includes('park')) return 'Park';
    if (desc.includes('preserve')) return 'Nature Preserve';
    if (desc.includes('wildlife')) return 'Wildlife Area';
    if (desc.includes('wetland')) return 'Wetland';
  }

  return null;
};

export const getPropertyCategory = (useCode?: string | number, propertyType?: string): string => {
  // Use the updated category function that handles actual database values
  if (useCode !== undefined && useCode !== null) {
    return getPropertyCategoryFromCode(useCode);
  }

  // Fallback to property type if provided
  if (propertyType) {
    const type = propertyType.toLowerCase();
    if (type.includes('residential') || type.includes('single') || type.includes('home')) return 'Residential';
    if (type.includes('commercial') || type.includes('retail') || type.includes('office')) return 'Commercial';
    if (type.includes('industrial') || type.includes('warehouse')) return 'Industrial';
    if (type.includes('agricultural') || type.includes('farm') || type.includes('ranch')) return 'Agricultural';
    if (type.includes('vacant') || type.includes('land')) return 'Vacant Land';
    if (type.includes('multi') || type.includes('apartment')) return 'Multi-Family';
    if (type.includes('condo')) return 'Condominium';
    if (type.includes('government') || type.includes('governmental')) return 'Government';
    if (type.includes('religious') || type.includes('church')) return 'Religious';
    if (type.includes('conservation') || type.includes('preserve')) return 'Conservation';
  }

  return 'Other';
};

// Export the mapping objects for use in other modules
export { PROPERTY_USE_TO_CATEGORY, DOR_CODE_TO_CATEGORY };

// Get all property use codes for a given category (for filtering)
export const getPropertyUseCodesForCategory = (category: string): number[] => {
  return Object.entries(PROPERTY_USE_TO_CATEGORY)
    .filter(([_, cat]) => cat === category)
    .map(([code, _]) => parseInt(code));
};

// Get all categories available in the system
export const getAllPropertyCategories = (): string[] => {
  return Array.from(new Set(Object.values(PROPERTY_USE_TO_CATEGORY)));
};