/**
 * Florida Department of Revenue (DOR) Property Use Codes
 * Based on 2024 NAL_SDF_NAP Users Guide
 * https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/User%20Guides/2024%20Users%20guide%20and%20quick%20reference/2024_NAL_SDF_NAP_Users_Guide.pdf
 */

export interface DORUseCode {
  code: string;
  category: 'RESIDENTIAL' | 'COMMERCIAL' | 'INDUSTRIAL' | 'AGRICULTURAL' | 'INSTITUTIONAL' | 'GOVERNMENTAL' | 'MISCELLANEOUS';
  description: string;
  shortName: string;
}

export const DOR_USE_CODES: Record<string, DORUseCode> = {
  // RESIDENTIAL (000-009)
  '000': { code: '000', category: 'RESIDENTIAL', description: 'Vacant Residential – with/without extra features', shortName: 'Vacant Residential' },
  '001': { code: '001', category: 'RESIDENTIAL', description: 'Single Family', shortName: 'Single Family' },
  '002': { code: '002', category: 'RESIDENTIAL', description: 'Mobile Homes', shortName: 'Mobile Home' },
  '004': { code: '004', category: 'RESIDENTIAL', description: 'Condominiums', shortName: 'Condo' },
  '005': { code: '005', category: 'RESIDENTIAL', description: 'Cooperatives', shortName: 'Co-op' },
  '006': { code: '006', category: 'RESIDENTIAL', description: 'Retirement Homes not eligible for exemption', shortName: 'Retirement Home' },
  '007': { code: '007', category: 'RESIDENTIAL', description: 'Miscellaneous Residential (migrant camps, boarding homes, etc.)', shortName: 'Misc Residential' },
  '008': { code: '008', category: 'RESIDENTIAL', description: 'Multi-family - fewer than 10 units', shortName: 'Multi-Family <10' },
  '009': { code: '009', category: 'RESIDENTIAL', description: 'Residential Common Elements/Areas', shortName: 'Common Areas' },

  // COMMERCIAL (003, 010-039)
  '003': { code: '003', category: 'COMMERCIAL', description: 'Multi-family - 10 units or more', shortName: 'Multi-Family 10+' },
  '010': { code: '010', category: 'COMMERCIAL', description: 'Vacant Commercial - with/without extra features', shortName: 'Vacant Commercial' },
  '011': { code: '011', category: 'COMMERCIAL', description: 'Stores, one story', shortName: 'Retail Store' },
  '012': { code: '012', category: 'COMMERCIAL', description: 'Mixed use - store and office or store and residential', shortName: 'Mixed Use' },
  '013': { code: '013', category: 'COMMERCIAL', description: 'Department Stores', shortName: 'Department Store' },
  '014': { code: '014', category: 'COMMERCIAL', description: 'Supermarkets', shortName: 'Supermarket' },
  '015': { code: '015', category: 'COMMERCIAL', description: 'Regional Shopping Centers', shortName: 'Regional Mall' },
  '016': { code: '016', category: 'COMMERCIAL', description: 'Community Shopping Centers', shortName: 'Shopping Center' },
  '017': { code: '017', category: 'COMMERCIAL', description: 'Office buildings, non-professional service, one story', shortName: 'Office 1-Story' },
  '018': { code: '018', category: 'COMMERCIAL', description: 'Office buildings, non-professional service, multi-story', shortName: 'Office Multi-Story' },
  '019': { code: '019', category: 'COMMERCIAL', description: 'Professional service buildings', shortName: 'Professional Office' },
  '020': { code: '020', category: 'COMMERCIAL', description: 'Airports, bus terminals, marine terminals, piers, marinas', shortName: 'Transportation' },
  '021': { code: '021', category: 'COMMERCIAL', description: 'Restaurants, cafeterias', shortName: 'Restaurant' },
  '022': { code: '022', category: 'COMMERCIAL', description: 'Drive-in Restaurants', shortName: 'Fast Food' },
  '023': { code: '023', category: 'COMMERCIAL', description: 'Financial institutions', shortName: 'Bank' },
  '024': { code: '024', category: 'COMMERCIAL', description: 'Insurance company offices', shortName: 'Insurance Office' },
  '025': { code: '025', category: 'COMMERCIAL', description: 'Repair service shops', shortName: 'Repair Shop' },
  '026': { code: '026', category: 'COMMERCIAL', description: 'Service stations', shortName: 'Gas Station' },
  '027': { code: '027', category: 'COMMERCIAL', description: 'Auto sales, repair, storage', shortName: 'Auto Sales/Service' },
  '028': { code: '028', category: 'COMMERCIAL', description: 'Parking lots, mobile home parks', shortName: 'Parking/MH Park' },
  '029': { code: '029', category: 'COMMERCIAL', description: 'Wholesale outlets, manufacturing outlets', shortName: 'Wholesale' },
  '030': { code: '030', category: 'COMMERCIAL', description: 'Florists, greenhouses', shortName: 'Florist/Greenhouse' },
  '031': { code: '031', category: 'COMMERCIAL', description: 'Drive-in theaters, open stadiums', shortName: 'Drive-In/Stadium' },
  '032': { code: '032', category: 'COMMERCIAL', description: 'Enclosed theaters, auditoriums', shortName: 'Theater' },
  '033': { code: '033', category: 'COMMERCIAL', description: 'Nightclubs, cocktail lounges, bars', shortName: 'Bar/Nightclub' },
  '034': { code: '034', category: 'COMMERCIAL', description: 'Bowling alleys, skating rinks, pool halls', shortName: 'Recreation' },
  '035': { code: '035', category: 'COMMERCIAL', description: 'Tourist attractions, fairgrounds', shortName: 'Tourist Attraction' },
  '036': { code: '036', category: 'COMMERCIAL', description: 'Camps', shortName: 'Camp' },
  '037': { code: '037', category: 'COMMERCIAL', description: 'Race tracks', shortName: 'Race Track' },
  '038': { code: '038', category: 'COMMERCIAL', description: 'Golf courses, driving ranges', shortName: 'Golf Course' },
  '039': { code: '039', category: 'COMMERCIAL', description: 'Hotels, motels', shortName: 'Hotel/Motel' },

  // INDUSTRIAL (040-049)
  '040': { code: '040', category: 'INDUSTRIAL', description: 'Vacant Industrial - with/without extra features', shortName: 'Vacant Industrial' },
  '041': { code: '041', category: 'INDUSTRIAL', description: 'Light manufacturing', shortName: 'Light Manufacturing' },
  '042': { code: '042', category: 'INDUSTRIAL', description: 'Heavy industrial', shortName: 'Heavy Industrial' },
  '043': { code: '043', category: 'INDUSTRIAL', description: 'Lumber yards, sawmills', shortName: 'Lumber/Sawmill' },
  '044': { code: '044', category: 'INDUSTRIAL', description: 'Packing plants', shortName: 'Packing Plant' },
  '045': { code: '045', category: 'INDUSTRIAL', description: 'Canneries, bottlers, breweries', shortName: 'Food Processing' },
  '046': { code: '046', category: 'INDUSTRIAL', description: 'Other food processing', shortName: 'Food Factory' },
  '047': { code: '047', category: 'INDUSTRIAL', description: 'Mineral processing', shortName: 'Mineral Processing' },
  '048': { code: '048', category: 'INDUSTRIAL', description: 'Warehousing, distribution terminals', shortName: 'Warehouse' },
  '049': { code: '049', category: 'INDUSTRIAL', description: 'Open storage, junk yards', shortName: 'Storage/Junkyard' },

  // AGRICULTURAL (050-069)
  '050': { code: '050', category: 'AGRICULTURAL', description: 'Improved agricultural', shortName: 'Improved Ag' },
  '051': { code: '051', category: 'AGRICULTURAL', description: 'Cropland soil capability Class I', shortName: 'Cropland I' },
  '052': { code: '052', category: 'AGRICULTURAL', description: 'Cropland soil capability Class II', shortName: 'Cropland II' },
  '053': { code: '053', category: 'AGRICULTURAL', description: 'Cropland soil capability Class III', shortName: 'Cropland III' },
  '054': { code: '054', category: 'AGRICULTURAL', description: 'Timberland - site index 90 and above', shortName: 'Timber 90+' },
  '055': { code: '055', category: 'AGRICULTURAL', description: 'Timberland - site index 80 to 89', shortName: 'Timber 80-89' },
  '056': { code: '056', category: 'AGRICULTURAL', description: 'Timberland - site index 70 to 79', shortName: 'Timber 70-79' },
  '057': { code: '057', category: 'AGRICULTURAL', description: 'Timberland - site index 60 to 69', shortName: 'Timber 60-69' },
  '058': { code: '058', category: 'AGRICULTURAL', description: 'Timberland - site index 50 to 59', shortName: 'Timber 50-59' },
  '059': { code: '059', category: 'AGRICULTURAL', description: 'Timberland not classified by site index to Pines', shortName: 'Timber Unclassified' },
  '060': { code: '060', category: 'AGRICULTURAL', description: 'Grazing land soil capability Class I', shortName: 'Grazing I' },
  '061': { code: '061', category: 'AGRICULTURAL', description: 'Grazing land soil capability Class II', shortName: 'Grazing II' },
  '062': { code: '062', category: 'AGRICULTURAL', description: 'Grazing land soil capability Class III', shortName: 'Grazing III' },
  '063': { code: '063', category: 'AGRICULTURAL', description: 'Grazing land soil capability Class IV', shortName: 'Grazing IV' },
  '064': { code: '064', category: 'AGRICULTURAL', description: 'Grazing land soil capability Class V', shortName: 'Grazing V' },
  '065': { code: '065', category: 'AGRICULTURAL', description: 'Grazing land soil capability Class VI', shortName: 'Grazing VI' },
  '066': { code: '066', category: 'AGRICULTURAL', description: 'Orchard Groves, citrus, etc.', shortName: 'Orchard/Grove' },
  '067': { code: '067', category: 'AGRICULTURAL', description: 'Poultry, bees, tropical fish, rabbits', shortName: 'Poultry/Bees' },
  '068': { code: '068', category: 'AGRICULTURAL', description: 'Dairies, feed lots', shortName: 'Dairy/Feed Lot' },
  '069': { code: '069', category: 'AGRICULTURAL', description: 'Ornamentals, miscellaneous agricultural', shortName: 'Ornamentals' },

  // INSTITUTIONAL (070-079)
  '070': { code: '070', category: 'INSTITUTIONAL', description: 'Vacant Institutional', shortName: 'Vacant Institutional' },
  '071': { code: '071', category: 'INSTITUTIONAL', description: 'Churches', shortName: 'Church' },
  '072': { code: '072', category: 'INSTITUTIONAL', description: 'Private schools and colleges', shortName: 'Private School' },
  '073': { code: '073', category: 'INSTITUTIONAL', description: 'Privately owned hospitals', shortName: 'Private Hospital' },
  '074': { code: '074', category: 'INSTITUTIONAL', description: 'Homes for the aged', shortName: 'Nursing Home' },
  '075': { code: '075', category: 'INSTITUTIONAL', description: 'Orphanages, charitable services', shortName: 'Charity' },
  '076': { code: '076', category: 'INSTITUTIONAL', description: 'Mortuaries, cemeteries', shortName: 'Cemetery' },
  '077': { code: '077', category: 'INSTITUTIONAL', description: 'Clubs, lodges, union halls', shortName: 'Club/Lodge' },
  '078': { code: '078', category: 'INSTITUTIONAL', description: 'Sanitariums, convalescent homes', shortName: 'Sanitarium' },
  '079': { code: '079', category: 'INSTITUTIONAL', description: 'Cultural organizations', shortName: 'Cultural' },

  // GOVERNMENTAL (080-089)
  '080': { code: '080', category: 'GOVERNMENTAL', description: 'Vacant Governmental', shortName: 'Vacant Gov' },
  '081': { code: '081', category: 'GOVERNMENTAL', description: 'Military', shortName: 'Military' },
  '082': { code: '082', category: 'GOVERNMENTAL', description: 'Forest, parks, recreational areas', shortName: 'Parks' },
  '083': { code: '083', category: 'GOVERNMENTAL', description: 'Public county schools', shortName: 'Public School' },
  '084': { code: '084', category: 'GOVERNMENTAL', description: 'Colleges (non-private)', shortName: 'Public College' },
  '085': { code: '085', category: 'GOVERNMENTAL', description: 'Hospitals (non-private)', shortName: 'Public Hospital' },
  '086': { code: '086', category: 'GOVERNMENTAL', description: 'County government', shortName: 'County Gov' },
  '087': { code: '087', category: 'GOVERNMENTAL', description: 'State government', shortName: 'State Gov' },
  '088': { code: '088', category: 'GOVERNMENTAL', description: 'Federal government', shortName: 'Federal Gov' },
  '089': { code: '089', category: 'GOVERNMENTAL', description: 'Municipal government', shortName: 'Municipal Gov' },

  // MISCELLANEOUS (090-099)
  '090': { code: '090', category: 'MISCELLANEOUS', description: 'Leasehold interests', shortName: 'Leasehold' },
  '091': { code: '091', category: 'MISCELLANEOUS', description: 'Utilities', shortName: 'Utility' },
  '092': { code: '092', category: 'MISCELLANEOUS', description: 'Mining, petroleum, gas lands', shortName: 'Mining/Oil' },
  '093': { code: '093', category: 'MISCELLANEOUS', description: 'Subsurface rights', shortName: 'Subsurface Rights' },
  '094': { code: '094', category: 'MISCELLANEOUS', description: 'Right-of-way, streets, roads', shortName: 'Right-of-Way' },
  '095': { code: '095', category: 'MISCELLANEOUS', description: 'Rivers, lakes, submerged lands', shortName: 'Water/Submerged' },
  '096': { code: '096', category: 'MISCELLANEOUS', description: 'Sewage disposal, waste land', shortName: 'Waste/Sewage' },
  '097': { code: '097', category: 'MISCELLANEOUS', description: 'Outdoor recreational parkland', shortName: 'Rec Parkland' },
  '098': { code: '098', category: 'MISCELLANEOUS', description: 'Centrally assessed', shortName: 'Central Assessed' },
  '099': { code: '099', category: 'MISCELLANEOUS', description: 'Non-agricultural acreage', shortName: 'Non-Ag Acreage' },
};

/**
 * Get use code information
 */
export function getUseCodeInfo(code: string | undefined | null): DORUseCode | null {
  if (!code) return null;

  // Ensure code is 3 digits with leading zeros
  const formattedCode = String(code).padStart(3, '0');
  return DOR_USE_CODES[formattedCode] || null;
}

/**
 * Get property category from use code
 */
export function getPropertyCategory(code: string | undefined | null): string {
  const info = getUseCodeInfo(code);
  return info?.category || 'UNKNOWN';
}

/**
 * Get short name for display
 */
export function getUseCodeShortName(code: string | undefined | null): string {
  const info = getUseCodeInfo(code);
  return info?.shortName || 'Unknown';
}

/**
 * Get full description
 */
export function getUseCodeDescription(code: string | undefined | null): string {
  const info = getUseCodeInfo(code);
  return info?.description || 'Unknown Property Type';
}

/**
 * Map simplified property types to DOR categories
 */
export function getPropertyTypeFilter(propertyType: string): string[] {
  const normalizedType = propertyType.toUpperCase();

  switch (normalizedType) {
    case 'RESIDENTIAL':
      return ['000', '001', '002', '004', '005', '006', '007', '008', '009'];
    case 'COMMERCIAL':
      return ['003', '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',
              '020', '021', '022', '023', '024', '025', '026', '027', '028', '029',
              '030', '031', '032', '033', '034', '035', '036', '037', '038', '039'];
    case 'INDUSTRIAL':
      return ['040', '041', '042', '043', '044', '045', '046', '047', '048', '049'];
    case 'AGRICULTURAL':
      return ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059',
              '060', '061', '062', '063', '064', '065', '066', '067', '068', '069'];
    case 'VACANT':
    case 'VACANT LAND':
      return ['000', '010', '040', '070', '080', '099']; // All vacant categories
    case 'GOVERNMENT':
    case 'GOVERNMENTAL':
      return ['082', '083', '084', '086', '087', '088', '089'];
    case 'INSTITUTIONAL':
      return ['071', '072', '073', '074', '075', '076', '077', '078', '079'];
    case 'RELIGIOUS':
      return ['077']; // Churches, temples, synagogues
    case 'CONSERVATION':
      return ['093', '094', '095', '096']; // Conservation lands, parks, preserves
    case 'VACANT/SPECIAL':
      return ['000', '091', '092', '097', '098', '099']; // Vacant and special categories
    case 'MISCELLANEOUS':
      return ['090', '091', '092', '093', '094', '095', '096', '097', '098', '099'];
    default:
      return [];
  }
}

/**
 * Check if a use code matches a property type filter
 */
export function matchesPropertyTypeFilter(code: string | undefined | null, propertyType: string): boolean {
  if (!propertyType) return true; // No filter applied

  // If no code is provided, exclude from filtered results (don't show "Unknown" properties when filtering)
  if (!code) return false;

  const validCodes = getPropertyTypeFilter(propertyType);
  const formattedCode = String(code).padStart(3, '0');

  return validCodes.includes(formattedCode);
}

/**
 * Special Assessment Codes
 */
export const SPECIAL_ASSESSMENT_CODES: Record<string, string> = {
  '1': 'Pollution Control Device(s)',
  '2': 'Conservation Easement/Environmental/Recreation',
  '3': 'Building Moratorium',
};

/**
 * Get special assessment description
 */
export function getSpecialAssessment(code: string | undefined | null): string | null {
  if (!code) return null;
  return SPECIAL_ASSESSMENT_CODES[code] || null;
}