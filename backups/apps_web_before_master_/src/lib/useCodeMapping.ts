/**
 * Florida Department of Revenue (DOR) Use Code Mapping
 * Based on official DOR Field 8 – Column H – DOR_UC documentation
 * Updated to include all 100 use codes (000-099)
 */

export interface UseCodeInfo {
  code: string;
  category: string;
  description: string;
  shortName: string;
}

export const DOR_USE_CODES: Record<string, UseCodeInfo> = {
  // RESIDENTIAL (000-009)
  '000': { code: '000', category: 'Residential', description: 'Vacant Residential – with/without extra features', shortName: 'Vacant Residential' },
  '001': { code: '001', category: 'Residential', description: 'Single Family', shortName: 'Single Family' },
  '002': { code: '002', category: 'Residential', description: 'Mobile Homes', shortName: 'Mobile Home' },
  '003': { code: '003', category: 'Commercial', description: 'Multi-family - 10 units or more', shortName: 'Multi-family 10+' },
  '004': { code: '004', category: 'Residential', description: 'Condominiums', shortName: 'Condominium' },
  '005': { code: '005', category: 'Residential', description: 'Cooperatives', shortName: 'Cooperative' },
  '006': { code: '006', category: 'Residential', description: 'Retirement Homes not eligible for exemption', shortName: 'Retirement Home' },
  '007': { code: '007', category: 'Residential', description: 'Miscellaneous Residential (migrant camps, boarding homes, etc.)', shortName: 'Misc Residential' },
  '008': { code: '008', category: 'Residential', description: 'Multi-family - fewer than 10 units', shortName: 'Multi-family <10' },
  '009': { code: '009', category: 'Residential', description: 'Residential Common Elements/Areas', shortName: 'Common Areas' },

  // COMMERCIAL (010-039)
  '010': { code: '010', category: 'Commercial', description: 'Vacant Commercial - with/without extra features', shortName: 'Vacant Commercial' },
  '011': { code: '011', category: 'Commercial', description: 'Stores, one story', shortName: 'One Story Store' },
  '012': { code: '012', category: 'Commercial', description: 'Mixed use - store and office or store and residential combination', shortName: 'Mixed Use' },
  '013': { code: '013', category: 'Commercial', description: 'Department Stores', shortName: 'Department Store' },
  '014': { code: '014', category: 'Commercial', description: 'Supermarkets', shortName: 'Supermarket' },
  '015': { code: '015', category: 'Commercial', description: 'Regional Shopping Centers', shortName: 'Regional Shopping' },
  '016': { code: '016', category: 'Commercial', description: 'Community Shopping Centers', shortName: 'Community Shopping' },
  '017': { code: '017', category: 'Commercial', description: 'Office buildings, non-professional service buildings, one story', shortName: 'Office 1-Story' },
  '018': { code: '018', category: 'Commercial', description: 'Office buildings, non-professional service buildings, multi-story', shortName: 'Office Multi-Story' },
  '019': { code: '019', category: 'Commercial', description: 'Professional service buildings', shortName: 'Professional Services' },
  '020': { code: '020', category: 'Commercial', description: 'Airports (private or commercial), bus terminals, marine terminals, piers, marinas', shortName: 'Transportation Hub' },
  '021': { code: '021', category: 'Commercial', description: 'Restaurants, cafeterias', shortName: 'Restaurant' },
  '022': { code: '022', category: 'Commercial', description: 'Drive-in Restaurants', shortName: 'Drive-in Restaurant' },
  '023': { code: '023', category: 'Commercial', description: 'Financial institutions (banks, saving and loan companies, mortgage companies, credit services)', shortName: 'Financial Institution' },
  '024': { code: '024', category: 'Commercial', description: 'Insurance company offices', shortName: 'Insurance Office' },
  '025': { code: '025', category: 'Commercial', description: 'Repair service shops (excluding automotive), radio and T.V. repair, refrigeration service, electric repair, laundries, Laundromats', shortName: 'Repair Services' },
  '026': { code: '026', category: 'Commercial', description: 'Service stations', shortName: 'Gas Station' },
  '027': { code: '027', category: 'Commercial', description: 'Auto sales, auto repair and storage, auto service shops, body and fender shops, commercial garages, farm and machinery sales and services, auto rental, marine equipment, trailers and related equipment, mobile home sales, motorcycles, construction vehicle sales', shortName: 'Auto Services' },
  '028': { code: '028', category: 'Commercial', description: 'Parking lots (commercial or patron), mobile home parks', shortName: 'Parking/Mobile Parks' },
  '029': { code: '029', category: 'Commercial', description: 'Wholesale outlets, produce houses, manufacturing outlets', shortName: 'Wholesale' },
  '030': { code: '030', category: 'Commercial', description: 'Florists, greenhouses', shortName: 'Florist/Greenhouse' },
  '031': { code: '031', category: 'Commercial', description: 'Drive-in theaters, open stadiums', shortName: 'Open Entertainment' },
  '032': { code: '032', category: 'Commercial', description: 'Enclosed theaters, enclosed auditoriums', shortName: 'Enclosed Entertainment' },
  '033': { code: '033', category: 'Commercial', description: 'Nightclubs, cocktail lounges, bars', shortName: 'Nightclub/Bar' },
  '034': { code: '034', category: 'Commercial', description: 'Bowling alleys, skating rinks, pool halls, enclosed arenas', shortName: 'Recreation Venue' },
  '035': { code: '035', category: 'Commercial', description: 'Tourist attractions, permanent exhibits, other entertainment facilities, fairgrounds (privately owned)', shortName: 'Tourist Attraction' },
  '036': { code: '036', category: 'Commercial', description: 'Camps', shortName: 'Camps' },
  '037': { code: '037', category: 'Commercial', description: 'Race tracks (horse, auto, or dog)', shortName: 'Race Track' },
  '038': { code: '038', category: 'Commercial', description: 'Golf courses, driving ranges', shortName: 'Golf Course' },
  '039': { code: '039', category: 'Commercial', description: 'Hotels, motels', shortName: 'Hotel/Motel' },

  // INDUSTRIAL (040-049)
  '040': { code: '040', category: 'Industrial', description: 'Vacant Industrial -with/without extra features', shortName: 'Vacant Industrial' },
  '041': { code: '041', category: 'Industrial', description: 'Light manufacturing, small equipment manufacturing plants, small machine shops, instrument manufacturing, printing plants', shortName: 'Light Manufacturing' },
  '042': { code: '042', category: 'Industrial', description: 'Heavy industrial, heavy equipment manufacturing, large machine shops, foundries, steel fabricating plants, auto or aircraft plants', shortName: 'Heavy Industrial' },
  '043': { code: '043', category: 'Industrial', description: 'Lumber yards, sawmills, planing mills', shortName: 'Lumber/Sawmill' },
  '044': { code: '044', category: 'Industrial', description: 'Packing plants, fruit and vegetable packing plants, meat packing plants', shortName: 'Packing Plant' },
  '045': { code: '045', category: 'Industrial', description: 'Canneries, fruit and vegetable, bottlers and brewers, distilleries, wineries', shortName: 'Food Processing' },
  '046': { code: '046', category: 'Industrial', description: 'Other food processing, candy factories, bakeries, potato chip factories', shortName: 'Food Manufacturing' },
  '047': { code: '047', category: 'Industrial', description: 'Mineral processing, phosphate processing, cement plants, refineries, clay plants, rock and gravel plants', shortName: 'Mineral Processing' },
  '048': { code: '048', category: 'Industrial', description: 'Warehousing, distribution terminals, trucking terminals, van and storage warehousing', shortName: 'Warehousing' },
  '049': { code: '049', category: 'Industrial', description: 'Open storage, new and used building supplies, junk yards, auto wrecking, fuel storage, equipment and material storage', shortName: 'Open Storage' },

  // AGRICULTURAL (050-069)
  '050': { code: '050', category: 'Agricultural', description: 'Improved agricultural', shortName: 'Improved Agricultural' },
  '051': { code: '051', category: 'Agricultural', description: 'Cropland soil capability Class I', shortName: 'Cropland Class I' },
  '052': { code: '052', category: 'Agricultural', description: 'Cropland soil capability Class II', shortName: 'Cropland Class II' },
  '053': { code: '053', category: 'Agricultural', description: 'Cropland soil capability Class III', shortName: 'Cropland Class III' },
  '054': { code: '054', category: 'Agricultural', description: 'Timberland - site index 90 and above', shortName: 'Timberland 90+' },
  '055': { code: '055', category: 'Agricultural', description: 'Timberland - site index 80 to 89', shortName: 'Timberland 80-89' },
  '056': { code: '056', category: 'Agricultural', description: 'Timberland - site index 70 to 79', shortName: 'Timberland 70-79' },
  '057': { code: '057', category: 'Agricultural', description: 'Timberland - site index 60 to 69', shortName: 'Timberland 60-69' },
  '058': { code: '058', category: 'Agricultural', description: 'Timberland - site index 50 to 59', shortName: 'Timberland 50-59' },
  '059': { code: '059', category: 'Agricultural', description: 'Timberland not classified by site index to Pines', shortName: 'Timberland Other' },
  '060': { code: '060', category: 'Agricultural', description: 'Grazing land soil capability Class I', shortName: 'Grazing Class I' },
  '061': { code: '061', category: 'Agricultural', description: 'Grazing land soil capability Class II', shortName: 'Grazing Class II' },
  '062': { code: '062', category: 'Agricultural', description: 'Grazing land soil capability Class III', shortName: 'Grazing Class III' },
  '063': { code: '063', category: 'Agricultural', description: 'Grazing land soil capability Class IV', shortName: 'Grazing Class IV' },
  '064': { code: '064', category: 'Agricultural', description: 'Grazing land soil capability Class V', shortName: 'Grazing Class V' },
  '065': { code: '065', category: 'Agricultural', description: 'Grazing land soil capability Class VI', shortName: 'Grazing Class VI' },
  '066': { code: '066', category: 'Agricultural', description: 'Orchard Groves, citrus, etc.', shortName: 'Orchard/Groves' },
  '067': { code: '067', category: 'Agricultural', description: 'Poultry, bees, tropical fish, rabbits, etc.', shortName: 'Poultry/Livestock' },
  '068': { code: '068', category: 'Agricultural', description: 'Dairies, feed lots', shortName: 'Dairy/Feed Lots' },
  '069': { code: '069', category: 'Agricultural', description: 'Ornamentals, miscellaneous agricultural', shortName: 'Ornamentals/Misc Ag' },

  // INSTITUTIONAL (070-079)
  '070': { code: '070', category: 'Institutional', description: 'Vacant Institutional, with or without extra features', shortName: 'Vacant Institutional' },
  '071': { code: '071', category: 'Institutional', description: 'Churches', shortName: 'Church' },
  '072': { code: '072', category: 'Institutional', description: 'Private schools and colleges', shortName: 'Private School' },
  '073': { code: '073', category: 'Institutional', description: 'Privately owned hospitals', shortName: 'Private Hospital' },
  '074': { code: '074', category: 'Institutional', description: 'Homes for the aged', shortName: 'Aged Care Home' },
  '075': { code: '075', category: 'Institutional', description: 'Orphanages, other non-profit or charitable services', shortName: 'Charitable Services' },
  '076': { code: '076', category: 'Institutional', description: 'Mortuaries, cemeteries, crematoriums', shortName: 'Funeral Services' },
  '077': { code: '077', category: 'Institutional', description: 'Clubs, lodges, union halls', shortName: 'Clubs/Lodges' },
  '078': { code: '078', category: 'Institutional', description: 'Sanitariums, convalescent and rest homes', shortName: 'Care Facility' },
  '079': { code: '079', category: 'Institutional', description: 'Cultural organizations, facilities', shortName: 'Cultural Facility' },

  // GOVERNMENTAL (080-089)
  '080': { code: '080', category: 'Governmental', description: 'Vacant Governmental - with/without extra features for municipal, counties, state, federal properties and water management district (including DOT/State of Florida retention and/or detention areas)', shortName: 'Vacant Government' },
  '081': { code: '081', category: 'Governmental', description: 'Military', shortName: 'Military' },
  '082': { code: '082', category: 'Governmental', description: 'Forest, parks, recreational areas', shortName: 'Parks/Recreation' },
  '083': { code: '083', category: 'Governmental', description: 'Public county schools - including all property of Board of Public Instruction', shortName: 'Public School' },
  '084': { code: '084', category: 'Governmental', description: 'Colleges (non-private)', shortName: 'Public College' },
  '085': { code: '085', category: 'Governmental', description: 'Hospitals (non-private)', shortName: 'Public Hospital' },
  '086': { code: '086', category: 'Governmental', description: 'Counties (other than public schools, colleges, hospitals) including non-municipal government', shortName: 'County Government' },
  '087': { code: '087', category: 'Governmental', description: 'State, other than military, forests, parks, recreational areas, colleges, hospitals', shortName: 'State Government' },
  '088': { code: '088', category: 'Governmental', description: 'Federal, other than military, forests, parks, recreational areas, hospitals, colleges', shortName: 'Federal Government' },
  '089': { code: '089', category: 'Governmental', description: 'Municipal, other than parks, recreational areas, colleges, hospitals', shortName: 'Municipal Government' },

  // MISCELLANEOUS (090-099)
  '090': { code: '090', category: 'Miscellaneous', description: 'Leasehold interests (government-owned property leased by a non-governmental lessee)', shortName: 'Leasehold Interest' },
  '091': { code: '091', category: 'Miscellaneous', description: 'Utility, gas and electricity, telephone and telegraph, locally assessed railroads, water and sewer service, pipelines, canals, radio/television communication', shortName: 'Utility' },
  '092': { code: '092', category: 'Miscellaneous', description: 'Mining lands, petroleum lands, or gas lands', shortName: 'Mining/Petroleum' },
  '093': { code: '093', category: 'Miscellaneous', description: 'Subsurface rights', shortName: 'Subsurface Rights' },
  '094': { code: '094', category: 'Miscellaneous', description: 'Right-of-way, streets, roads, irrigation channel, ditch, etc.', shortName: 'Right-of-way' },
  '095': { code: '095', category: 'Miscellaneous', description: 'Rivers and lakes, submerged lands', shortName: 'Water/Submerged' },
  '096': { code: '096', category: 'Miscellaneous', description: 'Sewage disposal, solid waste, borrow pits, drainage reservoirs, waste land, marsh, sand dunes, swamps', shortName: 'Waste/Drainage' },
  '097': { code: '097', category: 'Miscellaneous', description: 'Outdoor recreational or parkland, or high-water recharge subject to classified use assessment', shortName: 'Recreational/Park' },
  '098': { code: '098', category: 'Miscellaneous', description: 'Centrally assessed', shortName: 'Centrally Assessed' },
  '099': { code: '099', category: 'Miscellaneous', description: 'Acreage not zoned agricultural - with/without extra features', shortName: 'Non-Agricultural Acreage' }
};

/**
 * Get use code information by code
 */
export function getUseCodeInfo(code: string | number): UseCodeInfo | null {
  const codeStr = String(code).padStart(3, '0');
  return DOR_USE_CODES[codeStr] || null;
}

/**
 * Get use code short name for display
 */
export function getUseCodeName(code: string | number): string {
  const info = getUseCodeInfo(code);
  return info?.shortName || `Use Code: ${code}`;
}

/**
 * Get use code full description
 */
export function getUseCodeDescription(code: string | number): string {
  const info = getUseCodeInfo(code);
  return info?.description || `Unknown use code: ${code}`;
}

/**
 * Get use code category
 */
export function getUseCodeCategory(code: string | number): string {
  const info = getUseCodeInfo(code);
  return info?.category || 'Unknown';
}

/**
 * Get all use codes by category
 */
export function getUseCodesByCategory(): Record<string, UseCodeInfo[]> {
  const categories: Record<string, UseCodeInfo[]> = {};

  Object.values(DOR_USE_CODES).forEach(info => {
    if (!categories[info.category]) {
      categories[info.category] = [];
    }
    categories[info.category].push(info);
  });

  return categories;
}

/**
 * Active Stratum Definitions (for ATV_STRT field)
 */
export const ACTIVE_STRATA: Record<string, { number: number; definition: string; useCodes: string[] }> = {
  '1': {
    number: 1,
    definition: 'Residential property consisting of one primary living unit, including, but not limited to, single-family residences, condominiums, cooperatives, and mobile homes',
    useCodes: ['001', '002', '004', '005']
  },
  '2': {
    number: 2,
    definition: 'Retirement homes and residential property that consists of two to nine primary living units',
    useCodes: ['006', '008']
  },
  '3': {
    number: 3,
    definition: 'Non-homestead agricultural and other use-valued property',
    useCodes: ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059', '060', '061', '062', '063', '064', '065', '066', '067', '068', '069', '097']
  },
  '4': {
    number: 4,
    definition: 'Vacant and miscellaneous residential',
    useCodes: ['000', '007']
  },
  '5': {
    number: 5,
    definition: 'Non-agricultural acreage and other undeveloped parcels',
    useCodes: ['010', '040', '099']
  },
  '6': {
    number: 6,
    definition: 'Improved commercial and industrial property (including multi-family residential with 10 units or more)',
    useCodes: ['003', '011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021', '022', '023', '024', '025', '026', '027', '028', '029', '030', '031', '032', '033', '034', '035', '036', '037', '038', '039', '041', '042', '043', '044', '045', '046', '047', '048', '049']
  },
  '7': {
    number: 7,
    definition: 'Taxable institutional or governmental, utility, locally assessed railroad, oil, gas and mineral land, subsurface rights, and other real property',
    useCodes: ['070', '071', '072', '073', '074', '075', '076', '077', '078', '079', '080', '081', '082', '083', '084', '085', '086', '087', '088', '089', '090', '091', '092', '093', '094', '095', '096', '098']
  },
  '8': {
    number: 8,
    definition: 'When one or more of the above strata constitutes less than 5% of the total assessed value of all suitable real property in a county',
    useCodes: ['All use codes, if conditions are met']
  }
};

/**
 * Get active stratum for a use code
 */
export function getActiveStratum(useCode: string | number): number | null {
  const codeStr = String(useCode).padStart(3, '0');

  for (const [stratumNum, stratum] of Object.entries(ACTIVE_STRATA)) {
    if (stratum.useCodes.includes(codeStr)) {
      return parseInt(stratumNum);
    }
  }

  return null;
}