/**
 * Property Routing Utilities
 * Generates unique, SEO-friendly URLs for all 7.41M Florida properties
 */

export interface PropertyRouteParams {
  parcelId: string;
  county?: string;
  city?: string;
  address?: string;
  ownerName?: string;
}

/**
 * Generates a unique, SEO-friendly URL for a property
 * Format: /property/{county}/{parcel-id-slug}/{address-slug}
 */
export function generatePropertyUrl(params: PropertyRouteParams): string {
  const { parcelId, county, city, address, ownerName } = params;

  // Sanitize and create URL-safe slugs
  const countySlug = sanitizeForUrl(county || 'unknown');
  const parcelSlug = sanitizeParcelId(parcelId);

  // Create address slug from either address or city
  let addressSlug = '';
  if (address && address !== '-' && address !== 'No Street Address') {
    addressSlug = sanitizeForUrl(address);
  } else if (city) {
    addressSlug = sanitizeForUrl(city);
  } else if (ownerName) {
    // For properties without addresses, use first two words of owner name
    const ownerWords = ownerName.split(' ').slice(0, 2).join('-');
    addressSlug = sanitizeForUrl(ownerWords);
  } else {
    addressSlug = 'property';
  }

  return `/property/${countySlug}/${parcelSlug}/${addressSlug}`;
}

/**
 * Generates a unique property ID that can be used in URLs
 * Combines parcel ID with county for true uniqueness across Florida
 */
export function generateUniquePropertyId(parcelId: string, county?: string): string {
  const countyCode = getCountyCode(county);
  return `${countyCode}-${sanitizeParcelId(parcelId)}`;
}

/**
 * Sanitizes text for URL usage
 */
function sanitizeForUrl(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // Remove special characters except spaces and hyphens
    .replace(/\s+/g, '-')         // Replace spaces with hyphens
    .replace(/-+/g, '-')          // Replace multiple hyphens with single hyphen
    .replace(/^-|-$/g, '')        // Remove leading/trailing hyphens
    .substring(0, 50);            // Limit length
}

/**
 * Sanitizes parcel ID for URL usage
 */
function sanitizeParcelId(parcelId: string): string {
  return parcelId
    .replace(/[^a-zA-Z0-9-]/g, '-') // Replace non-alphanumeric with hyphens
    .replace(/-+/g, '-')            // Replace multiple hyphens with single
    .replace(/^-|-$/g, '')          // Remove leading/trailing hyphens
    .toLowerCase();
}

/**
 * Gets a 2-letter county code for URL optimization
 */
function getCountyCode(county?: string): string {
  const countyCodes: Record<string, string> = {
    'alachua': 'al',
    'baker': 'bk',
    'bay': 'by',
    'bradford': 'br',
    'brevard': 'bv',
    'broward': 'bw',
    'calhoun': 'ch',
    'charlotte': 'cr',
    'citrus': 'ct',
    'clay': 'cl',
    'collier': 'co',
    'columbia': 'cm',
    'desoto': 'ds',
    'dixie': 'dx',
    'duval': 'dv',
    'escambia': 'es',
    'flagler': 'fl',
    'franklin': 'fr',
    'gadsden': 'gd',
    'gilchrist': 'gi',
    'glades': 'gl',
    'gulf': 'gu',
    'hamilton': 'hm',
    'hardee': 'hd',
    'hendry': 'he',
    'hernando': 'hn',
    'highlands': 'hi',
    'hillsborough': 'hs',
    'holmes': 'ho',
    'indian-river': 'ir',
    'jackson': 'ja',
    'jefferson': 'je',
    'lafayette': 'lf',
    'lake': 'lk',
    'lee': 'le',
    'leon': 'ln',
    'levy': 'lv',
    'liberty': 'li',
    'madison': 'md',
    'manatee': 'mn',
    'marion': 'ma',
    'martin': 'mt',
    'miami-dade': 'md',
    'monroe': 'mo',
    'nassau': 'na',
    'okaloosa': 'ok',
    'okeechobee': 'oe',
    'orange': 'or',
    'osceola': 'os',
    'palm-beach': 'pb',
    'pasco': 'pa',
    'pinellas': 'pi',
    'polk': 'po',
    'putnam': 'pu',
    'santa-rosa': 'sr',
    'sarasota': 'sa',
    'seminole': 'se',
    'st-johns': 'sj',
    'st-lucie': 'sl',
    'sumter': 'su',
    'suwannee': 'sw',
    'taylor': 'ta',
    'union': 'un',
    'volusia': 'vo',
    'wakulla': 'wa',
    'walton': 'wt',
    'washington': 'ws'
  };

  if (!county) return 'fl';

  const normalized = county.toLowerCase().replace(/\s+/g, '-');
  return countyCodes[normalized] || normalized.substring(0, 2);
}

/**
 * Parses a property URL back to its components
 */
export function parsePropertyUrl(url: string): PropertyRouteParams | null {
  const match = url.match(/\/property\/([^\/]+)\/([^\/]+)\/([^\/]+)/);
  if (!match) return null;

  const [, countySlug, parcelSlug, addressSlug] = match;

  return {
    parcelId: parcelSlug.replace(/-/g, ''), // Convert back from URL format
    county: countySlug.replace(/-/g, ' '),
    address: addressSlug.replace(/-/g, ' ')
  };
}

/**
 * Generates SEO-friendly property title for the page
 */
export function generatePropertyTitle(params: PropertyRouteParams): string {
  const { parcelId, county, city, address, ownerName } = params;

  let title = '';

  if (address && address !== '-' && address !== 'No Street Address') {
    title = `${address}`;
    if (city) title += `, ${city}`;
  } else if (city) {
    title = `Property in ${city}`;
  } else if (ownerName) {
    title = `Property owned by ${ownerName}`;
  } else {
    title = `Property ${parcelId}`;
  }

  if (county) {
    title += `, ${county} County, FL`;
  } else {
    title += ', Florida';
  }

  return title;
}

/**
 * Generates property meta description for SEO
 */
export function generatePropertyDescription(params: PropertyRouteParams & {
  propertyType?: string;
  appraisedValue?: number;
  yearBuilt?: number;
}): string {
  const { address, city, county, propertyType, appraisedValue, yearBuilt } = params;

  let description = '';

  if (address && address !== '-' && address !== 'No Street Address') {
    description = `Property details for ${address}`;
    if (city) description += ` in ${city}`;
  } else if (city) {
    description = `Property details for ${city}`;
  } else {
    description = 'Property details';
  }

  if (county) description += `, ${county} County`;
  description += ', Florida.';

  const details = [];
  if (propertyType) details.push(propertyType.toLowerCase());
  if (appraisedValue) details.push(`$${appraisedValue.toLocaleString()} appraised value`);
  if (yearBuilt) details.push(`built in ${yearBuilt}`);

  if (details.length > 0) {
    description += ` ${details.join(', ')}.`;
  }

  description += ' View property tax records, ownership history, and market analysis.';

  return description;
}

/**
 * Legacy route compatibility - converts old URLs to new format
 */
export function convertLegacyUrl(oldUrl: string): string | null {
  // Handle /property/:folio format
  const folioMatch = oldUrl.match(/\/property\/([^\/]+)$/);
  if (folioMatch) {
    const folio = folioMatch[1];
    return `/property/fl/${folio}/property`;
  }

  // Handle /properties/:city/:address format
  const cityAddressMatch = oldUrl.match(/\/properties\/([^\/]+)\/([^\/]+)$/);
  if (cityAddressMatch) {
    const [, city, address] = cityAddressMatch;
    return `/property/fl/${address}/${city}`;
  }

  return null;
}

/**
 * Validates if a property URL is properly formatted
 */
export function isValidPropertyUrl(url: string): boolean {
  return /^\/property\/[a-z0-9-]+\/[a-z0-9-]+\/[a-z0-9-]+$/.test(url);
}