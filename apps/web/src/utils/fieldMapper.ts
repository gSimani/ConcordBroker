/**
 * Field Standardization Utility
 *
 * Normalizes 85+ field name variants into consistent field names
 * Handles camelCase, snake_case, and abbreviated field names
 *
 * Usage:
 *   const standardized = standardizeFields(propertyData);
 */

export interface StandardizedPropertyFields {
  // Identifiers
  parcel_id: string;
  county: string;
  year: number;

  // Owner Information
  owner_name: string;
  owner_address: string;
  owner_city: string;
  owner_state: string;
  owner_zip: string;

  // Property Address
  phy_addr1: string;
  phy_addr2: string;
  phy_city: string;
  phy_zip: string;

  // Valuation
  just_value: number;
  assessed_value: number;
  land_value: number;
  building_value: number;
  market_value: number;

  // Property Type
  property_use: string;
  dor_use_code: string;
  property_type: string;

  // Square Footage
  land_sqft: number;
  total_living_area: number;
  building_sqft: number;

  // Characteristics
  year_built: number;
  bedrooms: number;
  bathrooms: number;
  stories: number;

  // Additional
  homestead_exemption: boolean;
  tax_amount: number;
}

/**
 * Standardize property data fields from any variant
 */
export function standardizeFields(data: any): Partial<StandardizedPropertyFields> {
  if (!data) return {};

  return {
    // Identifiers
    parcel_id: data.parcel_id || data.parcelId || data.folio || data.id || '',
    county: data.county || data.countyName || data.county_name || '',
    year: parseInt(data.year || data.tax_year || data.taxYear || new Date().getFullYear().toString()),

    // Owner Information
    owner_name: data.owner_name || data.own_name || data.owner || data.ownerName || '',
    owner_address: data.owner_address || data.owner_addr1 || data.own_addr1 || data.ownerAddress || '',
    owner_city: data.owner_city || data.own_city || data.ownerCity || '',
    owner_state: data.owner_state || data.own_state || data.ownerState || '',
    owner_zip: data.owner_zip || data.own_zip || data.ownerZip || '',

    // Property Address
    phy_addr1: data.phy_addr1 || data.address || data.property_address || data.propertyAddress || data.site_addr1 || '',
    phy_addr2: data.phy_addr2 || data.address2 || data.property_address2 || data.site_addr2 || '',
    phy_city: data.phy_city || data.city || data.property_city || data.propertyCity || data.site_city || '',
    phy_zip: data.phy_zip || data.zip || data.zipcode || data.property_zip || data.site_zip || '',

    // Valuation - handle multiple variants
    just_value: parseFloat(
      data.just_value ||
      data.jv ||
      data.justValue ||
      data.market_value ||
      data.marketValue ||
      data.appraised_value ||
      data.appraisedValue ||
      data.total_value ||
      data.totalValue ||
      '0'
    ),
    assessed_value: parseFloat(
      data.assessed_value ||
      data.assessedValue ||
      data.assessed ||
      data.assess_value ||
      '0'
    ),
    land_value: parseFloat(
      data.land_value ||
      data.landValue ||
      data.lnd_val ||
      data.land_val ||
      '0'
    ),
    building_value: parseFloat(
      data.building_value ||
      data.buildingValue ||
      data.bld_val ||
      data.improvement_value ||
      '0'
    ),
    market_value: parseFloat(
      data.market_value ||
      data.marketValue ||
      data.just_value ||
      data.jv ||
      '0'
    ),

    // Property Type
    property_use: data.property_use || data.propertyUse || data.property_type || data.propertyType || data.use_desc || '',
    dor_use_code: data.dor_use_code || data.dor_uc || data.use_code || data.propertyUseCode || data.dorUC || '',
    property_type: data.property_type || data.propertyType || data.property_use || data.propertyUse || '',

    // Square Footage
    land_sqft: parseFloat(
      data.land_sqft ||
      data.lnd_sqfoot ||
      data.landSqFt ||
      data.land_square_footage ||
      data.lot_size ||
      data.lotSize ||
      '0'
    ),
    total_living_area: parseFloat(
      data.total_living_area ||
      data.tot_lvg_area ||
      data.living_area ||
      data.livingArea ||
      data.totalLivingArea ||
      data.heated_area ||
      '0'
    ),
    building_sqft: parseFloat(
      data.building_sqft ||
      data.buildingSqft ||
      data.tot_lvg_area ||
      data.total_living_area ||
      data.building_area ||
      '0'
    ),

    // Characteristics
    year_built: parseInt(
      data.year_built ||
      data.act_yr_blt ||
      data.yearBuilt ||
      data.actualYearBuilt ||
      data.eff_yr_blt ||
      '0'
    ),
    bedrooms: parseInt(
      data.bedrooms ||
      data.beds ||
      data.bed ||
      data.no_bdrm ||
      data.bedroom_count ||
      '0'
    ),
    bathrooms: parseFloat(
      data.bathrooms ||
      data.baths ||
      data.bath ||
      data.no_bath ||
      data.bathroom_count ||
      '0'
    ),
    stories: parseFloat(
      data.stories ||
      data.no_res_unts ||
      data.story_count ||
      '0'
    ),

    // Additional
    homestead_exemption: Boolean(
      data.homestead_exemption ||
      data.homestead ||
      data.exempt ||
      data.is_homestead
    ),
    tax_amount: parseFloat(
      data.tax_amount ||
      data.taxAmount ||
      data.taxes ||
      data.annual_tax ||
      '0'
    ),
  };
}

/**
 * Get safe value with fallback
 */
export function safeValue<T>(value: T | null | undefined, fallback: T): T {
  return value ?? fallback;
}

/**
 * Format currency value
 */
export function formatCurrency(value: number | string | null | undefined): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (!num || isNaN(num)) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(num);
}

/**
 * Format square footage
 */
export function formatSqFt(value: number | string | null | undefined): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (!num || isNaN(num) || num === 0) return 'N/A';

  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 0
  }).format(num) + ' sqft';
}

/**
 * Get property type display name
 * Now supports detailed lookup from dor_use_codes_std table via dorCodeService
 */
export function getPropertyTypeDisplay(dorCode: string | null | undefined): string {
  if (!dorCode) return 'Unknown';

  const code = dorCode.toString().padStart(2, '0');

  // Residential
  if (code >= '00' && code <= '09') return 'Residential';
  // Commercial
  if (code >= '10' && code <= '39') return 'Commercial';
  // Industrial
  if (code >= '40' && code <= '49') return 'Industrial';
  // Agricultural
  if (code >= '50' && code <= '69') return 'Agricultural';
  // Institutional
  if (code >= '70' && code <= '79') return 'Institutional';
  // Government
  if (code >= '80' && code <= '89') return 'Government';
  // Vacant
  if (code >= '90' && code <= '99') return 'Vacant Land';

  return 'Unknown';
}

/**
 * Get detailed property use description
 * This is an async version that fetches from dor_use_codes_std
 * For use in components with async support
 */
export async function getDetailedPropertyUse(
  propertyUse: string | number | null | undefined,
  county?: string | null
): Promise<{ category: string; description: string; fullCode: string } | null> {
  if (!propertyUse) return null;

  // Dynamic import to avoid circular dependencies and allow tree-shaking
  const { getPropertyUseInfo } = await import('@/services/dorCodeService');

  const info = await getPropertyUseInfo(propertyUse, county);

  if (info) {
    return {
      category: info.category,
      description: info.description,
      fullCode: info.full_code
    };
  }

  return null;
}

/**
 * Ensure valid year
 */
export function normalizeYear(year: number | string | null | undefined): number {
  const num = typeof year === 'string' ? parseInt(year) : year;
  if (!num || isNaN(num) || num < 1800 || num > 2100) {
    return new Date().getFullYear();
  }
  return num;
}

export default {
  standardizeFields,
  safeValue,
  formatCurrency,
  formatSqFt,
  getPropertyTypeDisplay,
  getDetailedPropertyUse,
  normalizeYear,
};
