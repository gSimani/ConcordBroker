/**
 * Property Field Name Mapping Utility
 *
 * Solves the critical issue of inconsistent field names between:
 * - Database (snake_case): property_use, tv_nsd, no_res_unts
 * - Frontend (camelCase): propertyUse, tvSd, units
 *
 * This utility normalizes all property data to a consistent format.
 */

/**
 * Standard field name mappings
 * Key = standardized name, Value = array of possible variants
 */
export const PROPERTY_FIELD_MAPPINGS = {
  // Property value fields (6 variants)
  justValue: ['just_value', 'jv', 'justValue', 'market_value', 'marketValue', 'appraised_value'],

  // Owner fields (3 variants)
  ownerName: ['owner_name', 'own_name', 'owner', 'ownerName'],
  ownerAddress: ['owner_addr1', 'owner_address', 'ownerAddress'],

  // Land area fields (4 variants)
  landSquareFeet: ['lnd_sqfoot', 'landSqFt', 'land_square_footage', 'land_sqft', 'landSquareFeet'],

  // Building area fields (3 variants)
  totalLivingArea: ['tot_lvg_area', 'living_area', 'totalLivingArea', 'total_living_area'],

  // Property use fields (2 variants)
  propertyUse: ['property_use', 'propertyUse', 'dor_code', 'dorCode'],
  propertyUseDesc: ['property_use_desc', 'propertyUseDesc', 'use_description', 'useDescription'],

  // Tax value fields (3 variants)
  taxableValue: ['tv_sd', 'tv_nsd', 'taxable_value', 'taxableValue'],
  assessedValue: ['assessed_value', 'assessedValue', 'av'],

  // Land value
  landValue: ['lnd_val', 'land_value', 'landValue'],

  // Building value
  buildingValue: ['building_value', 'bldg_val', 'buildingValue'],

  // Units fields (4 variants)
  units: ['units', 'no_res_unts', 'no_units', 'number_of_units'],

  // Address fields
  physicalAddress: ['phy_addr1', 'physical_address', 'physicalAddress', 'situs_address', 'situsAddress'],
  physicalCity: ['phy_city', 'physical_city', 'physicalCity', 'city'],
  physicalZip: ['phy_zipcd', 'physical_zip', 'physicalZip', 'zip_code', 'zipCode'],

  // County
  county: ['county', 'county_name', 'countyName'],

  // Parcel ID
  parcelId: ['parcel_id', 'parcelId', 'folio', 'account_number', 'accountNumber'],

  // Year built
  yearBuilt: ['year_built', 'yearBuilt', 'yr_blt', 'effective_year_built'],

  // Bedrooms/Bathrooms
  bedrooms: ['bedrooms', 'bed', 'no_bed'],
  bathrooms: ['bathrooms', 'bath', 'no_bath'],

  // Sale information
  salePrice: ['sale_price', 'salePrice', 'or_book_sale_price', 'sale_amt'],
  saleDate: ['sale_date', 'saleDate', 'or_date_of_sale'],
  lastSalePrice: ['last_sale_price', 'lastSalePrice', 'latest_sale_price'],
  lastSaleDate: ['last_sale_date', 'lastSaleDate', 'latest_sale_date'],

  // Tax deed fields
  certificateNumber: ['certificate_number', 'certificateNumber', 'cert_no'],
  auctionDate: ['auction_date', 'auctionDate', 'sale_date'],
  winningBid: ['winning_bid', 'winningBid', 'bid_amount'],

  // Building details
  stories: ['stories', 'no_stories', 'number_of_stories'],
  actualAge: ['actual_age', 'actualAge', 'age'],
  effectiveAge: ['effective_age', 'effectiveAge', 'eff_age'],

} as const;

/**
 * Normalized property data interface
 * All fields are optional since source data may be incomplete
 */
export interface NormalizedPropertyData {
  // Core identification
  parcelId?: string;
  county?: string;

  // Property values
  justValue?: number;
  assessedValue?: number;
  taxableValue?: number;
  landValue?: number;
  buildingValue?: number;

  // Property use
  propertyUse?: string;
  propertyUseDesc?: string;

  // Owner information
  ownerName?: string;
  ownerAddress?: string;

  // Physical location
  physicalAddress?: string;
  physicalCity?: string;
  physicalZip?: string;

  // Building details
  totalLivingArea?: number;
  landSquareFeet?: number;
  units?: number;
  bedrooms?: number;
  bathrooms?: number;
  yearBuilt?: number;
  stories?: number;
  actualAge?: number;
  effectiveAge?: number;

  // Sale information
  salePrice?: number;
  saleDate?: string;
  lastSalePrice?: number;
  lastSaleDate?: string;

  // Tax deed
  certificateNumber?: string;
  auctionDate?: string;
  winningBid?: number;

  // Keep original data for reference
  _raw?: any;
}

/**
 * Normalize property data from any source format to standard format
 *
 * @param data - Raw property data from database/API (any format)
 * @returns Normalized property data with consistent field names
 *
 * @example
 * const rawData = { property_use: '0100', tv_nsd: 250000, own_name: 'John Doe' };
 * const normalized = normalizePropertyData(rawData);
 * // Returns: { propertyUse: '0100', taxableValue: 250000, ownerName: 'John Doe' }
 */
export function normalizePropertyData(data: any): NormalizedPropertyData {
  if (!data) return {};

  const normalized: NormalizedPropertyData = {
    _raw: data, // Keep original for debugging
  };

  // Map each standard field to its first matching variant in the source data
  for (const [standardName, variants] of Object.entries(PROPERTY_FIELD_MAPPINGS)) {
    const value = findFirstValue(data, variants);
    if (value !== undefined && value !== null) {
      (normalized as any)[standardName] = value;
    }
  }

  return normalized;
}

/**
 * Find the first non-null value from a list of field name variants
 *
 * @param data - Source object
 * @param variants - Array of possible field names
 * @returns First found value or undefined
 */
function findFirstValue(data: any, variants: readonly string[]): any {
  for (const variant of variants) {
    if (data[variant] !== undefined && data[variant] !== null) {
      return data[variant];
    }
  }
  return undefined;
}

/**
 * Normalize an array of property objects
 *
 * @param dataArray - Array of raw property data
 * @returns Array of normalized property data
 */
export function normalizePropertyArray(dataArray: any[]): NormalizedPropertyData[] {
  if (!Array.isArray(dataArray)) return [];
  return dataArray.map(item => normalizePropertyData(item));
}

/**
 * Type guard to check if data has been normalized
 */
export function isNormalizedProperty(data: any): data is NormalizedPropertyData {
  return data && typeof data === 'object' && '_raw' in data;
}

/**
 * Get a specific field value with fallback variants
 * Useful for components that need just one field
 *
 * @example
 * const propertyUse = getFieldValue(property, 'propertyUse');
 * // Checks: property_use, propertyUse, dor_code, dorCode
 */
export function getFieldValue(data: any, standardFieldName: keyof typeof PROPERTY_FIELD_MAPPINGS): any {
  if (!data) return undefined;

  const variants = PROPERTY_FIELD_MAPPINGS[standardFieldName];
  if (!variants) return undefined;

  return findFirstValue(data, variants);
}

/**
 * Format helpers for normalized data
 */
export const formatters = {
  currency: (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  },

  number: (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US').format(value);
  },

  squareFeet: (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `${new Intl.NumberFormat('en-US').format(value)} sq ft`;
  },

  address: (property: NormalizedPropertyData) => {
    const parts = [
      property.physicalAddress,
      property.physicalCity,
      property.physicalZip,
    ].filter(Boolean);
    return parts.join(', ') || 'N/A';
  },
};
