// Florida Department of Revenue Land Use Codes
// Based on 2024 NAL Users Guide

export interface DORUseCode {
  code: string;
  category: string;
  subcategory?: string;
  description: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

export const DOR_USE_CODES: Record<string, DORUseCode> = {
  // Residential
  '000': {
    code: '000',
    category: 'Residential',
    subcategory: 'Vacant',
    description: 'Vacant Residential - with/without extra features',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '001': {
    code: '001',
    category: 'Residential',
    subcategory: 'Single Family',
    description: 'Single Family',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '002': {
    code: '002',
    category: 'Residential',
    subcategory: 'Mobile Homes',
    description: 'Mobile Homes',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '004': {
    code: '004',
    category: 'Residential',
    subcategory: 'Condominiums',
    description: 'Condominiums',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '005': {
    code: '005',
    category: 'Residential',
    subcategory: 'Cooperatives',
    description: 'Cooperatives',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '006': {
    code: '006',
    category: 'Residential',
    subcategory: 'Retirement',
    description: 'Retirement Homes not eligible for exemption',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '007': {
    code: '007',
    category: 'Residential',
    subcategory: 'Miscellaneous',
    description: 'Miscellaneous Residential (migrant camps, boarding homes, etc.)',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '008': {
    code: '008',
    category: 'Residential',
    subcategory: 'Multi-family',
    description: 'Multi-family - fewer than 10 units',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },
  '009': {
    code: '009',
    category: 'Residential',
    subcategory: 'Common Areas',
    description: 'Residential Common Elements/Areas',
    color: 'text-green-800',
    bgColor: 'bg-green-100',
    borderColor: 'border-green-200'
  },

  // Commercial
  '003': {
    code: '003',
    category: 'Commercial',
    subcategory: 'Multi-family',
    description: 'Multi-family - 10 units or more',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '010': {
    code: '010',
    category: 'Commercial',
    subcategory: 'Vacant',
    description: 'Vacant Commercial - with/without extra features',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '011': {
    code: '011',
    category: 'Commercial',
    subcategory: 'Retail',
    description: 'Stores, one story',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '012': {
    code: '012',
    category: 'Commercial',
    subcategory: 'Mixed Use',
    description: 'Mixed use - store and office or store and residential combination',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '013': {
    code: '013',
    category: 'Commercial',
    subcategory: 'Retail',
    description: 'Department Stores',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '014': {
    code: '014',
    category: 'Commercial',
    subcategory: 'Retail',
    description: 'Supermarkets',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '015': {
    code: '015',
    category: 'Commercial',
    subcategory: 'Retail',
    description: 'Regional Shopping Centers',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '016': {
    code: '016',
    category: 'Commercial',
    subcategory: 'Retail',
    description: 'Community Shopping Centers',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '017': {
    code: '017',
    category: 'Commercial',
    subcategory: 'Office',
    description: 'Office buildings, non-professional service buildings, one story',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '018': {
    code: '018',
    category: 'Commercial',
    subcategory: 'Office',
    description: 'Office buildings, non-professional service buildings, multi-story',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '019': {
    code: '019',
    category: 'Commercial',
    subcategory: 'Office',
    description: 'Professional service buildings',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '020': {
    code: '020',
    category: 'Commercial',
    subcategory: 'Transportation',
    description: 'Airports, bus terminals, marine terminals, piers, marinas',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '021': {
    code: '021',
    category: 'Commercial',
    subcategory: 'Restaurant',
    description: 'Restaurants, cafeterias',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '022': {
    code: '022',
    category: 'Commercial',
    subcategory: 'Restaurant',
    description: 'Drive-in Restaurants',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '023': {
    code: '023',
    category: 'Commercial',
    subcategory: 'Financial',
    description: 'Financial institutions (banks, saving and loan, mortgage companies)',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '024': {
    code: '024',
    category: 'Commercial',
    subcategory: 'Office',
    description: 'Insurance company offices',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '025': {
    code: '025',
    category: 'Commercial',
    subcategory: 'Service',
    description: 'Repair service shops, laundries, laundromats',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '026': {
    code: '026',
    category: 'Commercial',
    subcategory: 'Automotive',
    description: 'Service stations',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '027': {
    code: '027',
    category: 'Commercial',
    subcategory: 'Automotive',
    description: 'Auto sales, repair, service, mobile home sales',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '028': {
    code: '028',
    category: 'Commercial',
    subcategory: 'Parking',
    description: 'Parking lots, mobile home parks',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '029': {
    code: '029',
    category: 'Commercial',
    subcategory: 'Wholesale',
    description: 'Wholesale outlets, produce houses, manufacturing outlets',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '030': {
    code: '030',
    category: 'Commercial',
    subcategory: 'Nursery',
    description: 'Florists, greenhouses',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '031': {
    code: '031',
    category: 'Commercial',
    subcategory: 'Entertainment',
    description: 'Drive-in theaters, open stadiums',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '032': {
    code: '032',
    category: 'Commercial',
    subcategory: 'Entertainment',
    description: 'Enclosed theaters, enclosed auditoriums',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '033': {
    code: '033',
    category: 'Commercial',
    subcategory: 'Entertainment',
    description: 'Nightclubs, cocktail lounges, bars',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '034': {
    code: '034',
    category: 'Commercial',
    subcategory: 'Entertainment',
    description: 'Bowling alleys, skating rinks, pool halls',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '035': {
    code: '035',
    category: 'Commercial',
    subcategory: 'Entertainment',
    description: 'Tourist attractions, permanent exhibits',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '036': {
    code: '036',
    category: 'Commercial',
    subcategory: 'Recreation',
    description: 'Camps',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '037': {
    code: '037',
    category: 'Commercial',
    subcategory: 'Entertainment',
    description: 'Race tracks (horse, auto, or dog)',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '038': {
    code: '038',
    category: 'Commercial',
    subcategory: 'Recreation',
    description: 'Golf courses, driving ranges',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },
  '039': {
    code: '039',
    category: 'Commercial',
    subcategory: 'Hospitality',
    description: 'Hotels, motels',
    color: 'text-blue-800',
    bgColor: 'bg-blue-100',
    borderColor: 'border-blue-200'
  },

  // Industrial
  '040': {
    code: '040',
    category: 'Industrial',
    subcategory: 'Vacant',
    description: 'Vacant Industrial - with/without extra features',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '041': {
    code: '041',
    category: 'Industrial',
    subcategory: 'Light Manufacturing',
    description: 'Light manufacturing, small equipment plants',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '042': {
    code: '042',
    category: 'Industrial',
    subcategory: 'Heavy Industrial',
    description: 'Heavy industrial, heavy equipment manufacturing',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '043': {
    code: '043',
    category: 'Industrial',
    subcategory: 'Lumber',
    description: 'Lumber yards, sawmills, planing mills',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '044': {
    code: '044',
    category: 'Industrial',
    subcategory: 'Food Processing',
    description: 'Packing plants, fruit and vegetable packing',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '045': {
    code: '045',
    category: 'Industrial',
    subcategory: 'Food Processing',
    description: 'Canneries, bottlers, brewers, distilleries',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '046': {
    code: '046',
    category: 'Industrial',
    subcategory: 'Food Processing',
    description: 'Other food processing, candy factories, bakeries',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '047': {
    code: '047',
    category: 'Industrial',
    subcategory: 'Mineral Processing',
    description: 'Mineral processing, phosphate, cement plants',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '048': {
    code: '048',
    category: 'Industrial',
    subcategory: 'Warehousing',
    description: 'Warehousing, distribution terminals, trucking',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },
  '049': {
    code: '049',
    category: 'Industrial',
    subcategory: 'Storage',
    description: 'Open storage, junk yards, auto wrecking',
    color: 'text-orange-800',
    bgColor: 'bg-orange-100',
    borderColor: 'border-orange-200'
  },

  // Agricultural
  '050': {
    code: '050',
    category: 'Agricultural',
    subcategory: 'Improved',
    description: 'Improved agricultural',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '051': {
    code: '051',
    category: 'Agricultural',
    subcategory: 'Cropland I',
    description: 'Cropland soil capability Class I',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '052': {
    code: '052',
    category: 'Agricultural',
    subcategory: 'Cropland II',
    description: 'Cropland soil capability Class II',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '053': {
    code: '053',
    category: 'Agricultural',
    subcategory: 'Cropland III',
    description: 'Cropland soil capability Class III',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '054': {
    code: '054',
    category: 'Agricultural',
    subcategory: 'Timberland 90+',
    description: 'Timberland - site index 90 and above',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '055': {
    code: '055',
    category: 'Agricultural',
    subcategory: 'Timberland 80-89',
    description: 'Timberland - site index 80 to 89',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '056': {
    code: '056',
    category: 'Agricultural',
    subcategory: 'Timberland 70-79',
    description: 'Timberland - site index 70 to 79',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '057': {
    code: '057',
    category: 'Agricultural',
    subcategory: 'Timberland 60-69',
    description: 'Timberland - site index 60 to 69',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '058': {
    code: '058',
    category: 'Agricultural',
    subcategory: 'Timberland 50-59',
    description: 'Timberland - site index 50 to 59',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '059': {
    code: '059',
    category: 'Agricultural',
    subcategory: 'Timberland',
    description: 'Timberland not classified by site index to Pines',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '060': {
    code: '060',
    category: 'Agricultural',
    subcategory: 'Grazing I',
    description: 'Grazing land soil capability Class I',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '061': {
    code: '061',
    category: 'Agricultural',
    subcategory: 'Grazing II',
    description: 'Grazing land soil capability Class II',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '062': {
    code: '062',
    category: 'Agricultural',
    subcategory: 'Grazing III',
    description: 'Grazing land soil capability Class III',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '063': {
    code: '063',
    category: 'Agricultural',
    subcategory: 'Grazing IV',
    description: 'Grazing land soil capability Class IV',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '064': {
    code: '064',
    category: 'Agricultural',
    subcategory: 'Grazing V',
    description: 'Grazing land soil capability Class V',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '065': {
    code: '065',
    category: 'Agricultural',
    subcategory: 'Grazing VI',
    description: 'Grazing land soil capability Class VI',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '066': {
    code: '066',
    category: 'Agricultural',
    subcategory: 'Orchard',
    description: 'Orchard Groves, citrus, etc.',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '067': {
    code: '067',
    category: 'Agricultural',
    subcategory: 'Poultry/Bees',
    description: 'Poultry, bees, tropical fish, rabbits',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '068': {
    code: '068',
    category: 'Agricultural',
    subcategory: 'Dairies',
    description: 'Dairies, feed lots',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },
  '069': {
    code: '069',
    category: 'Agricultural',
    subcategory: 'Ornamental',
    description: 'Ornamentals, miscellaneous agricultural',
    color: 'text-yellow-800',
    bgColor: 'bg-yellow-100',
    borderColor: 'border-yellow-200'
  },

  // Institutional
  '070': {
    code: '070',
    category: 'Institutional',
    subcategory: 'Vacant',
    description: 'Vacant Institutional',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '071': {
    code: '071',
    category: 'Institutional',
    subcategory: 'Religious',
    description: 'Churches',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '072': {
    code: '072',
    category: 'Institutional',
    subcategory: 'Education',
    description: 'Private schools and colleges',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '073': {
    code: '073',
    category: 'Institutional',
    subcategory: 'Medical',
    description: 'Privately owned hospitals',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '074': {
    code: '074',
    category: 'Institutional',
    subcategory: 'Care Facility',
    description: 'Homes for the aged',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '075': {
    code: '075',
    category: 'Institutional',
    subcategory: 'Charitable',
    description: 'Orphanages, non-profit or charitable services',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '076': {
    code: '076',
    category: 'Institutional',
    subcategory: 'Cemetery',
    description: 'Mortuaries, cemeteries, crematoriums',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '077': {
    code: '077',
    category: 'Institutional',
    subcategory: 'Social',
    description: 'Clubs, lodges, union halls',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '078': {
    code: '078',
    category: 'Institutional',
    subcategory: 'Medical',
    description: 'Sanitariums, convalescent and rest homes',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },
  '079': {
    code: '079',
    category: 'Institutional',
    subcategory: 'Cultural',
    description: 'Cultural organizations, facilities',
    color: 'text-purple-800',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200'
  },

  // Governmental
  '080': {
    code: '080',
    category: 'Governmental',
    subcategory: 'Vacant',
    description: 'Vacant Governmental',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '081': {
    code: '081',
    category: 'Governmental',
    subcategory: 'Military',
    description: 'Military',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '082': {
    code: '082',
    category: 'Governmental',
    subcategory: 'Parks',
    description: 'Forest, parks, recreational areas',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '083': {
    code: '083',
    category: 'Governmental',
    subcategory: 'Education',
    description: 'Public county schools',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '084': {
    code: '084',
    category: 'Governmental',
    subcategory: 'Education',
    description: 'Colleges (non-private)',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '085': {
    code: '085',
    category: 'Governmental',
    subcategory: 'Medical',
    description: 'Hospitals (non-private)',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '086': {
    code: '086',
    category: 'Governmental',
    subcategory: 'County',
    description: 'Counties (other than schools, colleges, hospitals)',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '087': {
    code: '087',
    category: 'Governmental',
    subcategory: 'State',
    description: 'State (other than military, forests, parks)',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '088': {
    code: '088',
    category: 'Governmental',
    subcategory: 'Federal',
    description: 'Federal (other than military, forests, parks)',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },
  '089': {
    code: '089',
    category: 'Governmental',
    subcategory: 'Municipal',
    description: 'Municipal (other than parks, recreational)',
    color: 'text-indigo-800',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200'
  },

  // Miscellaneous
  '090': {
    code: '090',
    category: 'Miscellaneous',
    subcategory: 'Leasehold',
    description: 'Leasehold interests',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },
  '091': {
    code: '091',
    category: 'Miscellaneous',
    subcategory: 'Utility',
    description: 'Utility, gas, electricity, telephone, water, sewer',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },
  '092': {
    code: '092',
    category: 'Miscellaneous',
    subcategory: 'Mining',
    description: 'Mining lands, petroleum lands, gas lands',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },
  '093': {
    code: '093',
    category: 'Miscellaneous',
    subcategory: 'Rights',
    description: 'Subsurface rights',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },
  '094': {
    code: '094',
    category: 'Miscellaneous',
    subcategory: 'Right-of-way',
    description: 'Right-of-way, streets, roads, irrigation',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },
  '095': {
    code: '095',
    category: 'Miscellaneous',
    subcategory: 'Submerged',
    description: 'Rivers and lakes, submerged lands',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },
  '096': {
    code: '096',
    category: 'Miscellaneous',
    subcategory: 'Waste',
    description: 'Sewage disposal, solid waste, borrow pits',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },
  '097': {
    code: '097',
    category: 'Miscellaneous',
    subcategory: 'Recreation',
    description: 'Outdoor recreational or parkland',
    color: 'text-gray-800',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200'
  },

  // Centrally Assessed
  '098': {
    code: '098',
    category: 'Centrally Assessed',
    description: 'Centrally assessed',
    color: 'text-red-800',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-200'
  },

  // Non-Agricultural Acreage
  '099': {
    code: '099',
    category: 'Non-Agricultural Acreage',
    description: 'Acreage not zoned agricultural',
    color: 'text-amber-800',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-200'
  }
};

export function getDORUseCode(code: string | number | null | undefined): DORUseCode | null {
  if (!code && code !== 0) return null;

  // Convert to string and pad with zeros if needed
  const codeStr = String(code).padStart(3, '0');

  return DOR_USE_CODES[codeStr] || null;
}

export function formatDORCode(code: string | number | null | undefined): string {
  if (!code && code !== 0) return '---';
  return String(code).padStart(3, '0');
}