// Florida Property Use Codes and Classifications
// Based on Florida Department of Revenue standards

export const PROPERTY_USE_CODES = {
  // RESIDENTIAL (00-09)
  '00': 'Vacant Residential',
  '01': 'Single Family Residential',
  '02': 'Mobile Home',
  '03': 'Multi-Family (10+ units)',
  '04': 'Condominium',
  '05': 'Cooperative',
  '06': 'Retirement Home',
  '07': 'Miscellaneous Residential',
  '08': 'Multi-Family (2-9 units)',
  '09': 'Timeshare',
  
  // COMMERCIAL (10-39)
  '10': 'Vacant Commercial',
  '11': 'Stores, One Story',
  '12': 'Mixed Use (Store/Office/Residential)',
  '13': 'Department Store',
  '14': 'Supermarket',
  '15': 'Regional Shopping Center',
  '16': 'Community Shopping Center',
  '17': 'Office Building, One Story',
  '18': 'Office Building, Multi-Story',
  '19': 'Professional Service Building',
  '20': 'Airport',
  '21': 'Restaurant/Cafeteria',
  '22': 'Fast Food Restaurant',
  '23': 'Financial Institution',
  '24': 'Insurance Company Office',
  '25': 'Repair Service Garage',
  '26': 'Service Station',
  '27': 'Auto Dealership',
  '28': 'Parking Lot',
  '29': 'Wholesale Outlet',
  '30': 'Florist/Greenhouse',
  '31': 'Drive-In Theater',
  '32': 'Movie Theater',
  '33': 'Night Club/Bar',
  '34': 'Bowling Alley',
  '35': 'Tourist Attraction',
  '36': 'Camp',
  '37': 'Race Track',
  '38': 'Golf Course',
  '39': 'Hotel/Motel',
  
  // INDUSTRIAL (40-49)
  '40': 'Vacant Industrial',
  '41': 'Light Manufacturing',
  '42': 'Heavy Manufacturing',
  '43': 'Lumber Yard',
  '44': 'Packing Plant',
  '45': 'Cannery',
  '46': 'Other Food Processing',
  '47': 'Mineral Processing',
  '48': 'Warehouse',
  '49': 'Open Storage',
  
  // AGRICULTURAL (50-69)
  '50': 'Improved Agricultural',
  '51': 'Crop/Soil',
  '52': 'Timber/Forest',
  '53': 'Livestock/Grazing',
  '54': 'Orchard/Citrus/Grove',
  '55': 'Fish Farm',
  '56': 'Ornamental',
  '57': 'Miscellaneous Agricultural',
  '58': 'Dairies',
  '59': 'Poultry',
  '60': 'Vacant Agricultural with Extra Features',
  '66': 'Orchard Groves',
  '67': 'Poultry/Bees/Tropical Fish',
  '68': 'Dairies/Feed Lots',
  '69': 'Ornamentals/Miscellaneous Agricultural',
  
  // INSTITUTIONAL (70-79)
  '70': 'Vacant Institutional',
  '71': 'Church',
  '72': 'Private School',
  '73': 'Hospital',
  '74': 'Home for the Aged',
  '75': 'Orphanage',
  '76': 'Mortuary/Cemetery',
  '77': 'Club/Lodge/Union Hall',
  '78': 'Sanitarium',
  '79': 'Cultural Organization',
  
  // GOVERNMENT (80-89)
  '80': 'Vacant Government',
  '81': 'Military',
  '82': 'Forest/Park/Recreation',
  '83': 'Public School',
  '84': 'College/University',
  '85': 'Hospital',
  '86': 'Government Office Building',
  '87': 'Government Service',
  '88': 'Public Parking',
  '89': 'Other Government',
  
  // MISCELLANEOUS (90-99)
  '90': 'Leasehold Interest',
  '91': 'Utility',
  '92': 'Mining/Petroleum',
  '93': 'Subsurface Rights',
  '94': 'Right of Way',
  '95': 'Rivers/Lakes',
  '96': 'Sewage Disposal',
  '97': 'Waste Land',
  '98': 'Outdoor Recreation',
  '99': 'Acreage Not Zoned Agricultural',
  
  // CENTRALLY ASSESSED
  '00C': 'Centrally Assessed'
}

export const PROPERTY_CATEGORIES = {
  RESIDENTIAL: {
    name: 'Residential',
    codes: ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09'],
    fields: ['beds', 'baths', 'sqft', 'yearBuilt', 'stories', 'pool', 'garage', 'hoa', 'waterfront']
  },
  COMMERCIAL: {
    name: 'Commercial',
    codes: ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39'],
    fields: ['buildingSqft', 'landSqft', 'yearBuilt', 'stories', 'parkingSpaces', 'tenants', 'occupancyRate', 'netOperatingIncome', 'capRate', 'zoning']
  },
  INDUSTRIAL: {
    name: 'Industrial',
    codes: ['40', '41', '42', '43', '44', '45', '46', '47', '48', '49'],
    fields: ['buildingSqft', 'landSqft', 'clearHeight', 'dockDoors', 'railAccess', 'power', 'zoning', 'environmentalStatus']
  },
  AGRICULTURAL: {
    name: 'Agricultural',
    codes: ['50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '66', '67', '68', '69'],
    fields: ['acres', 'irrigated', 'cropType', 'soilType', 'waterRights', 'buildings', 'equipment', 'productivity']
  },
  INSTITUTIONAL: {
    name: 'Institutional',
    codes: ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'],
    fields: ['buildingSqft', 'landSqft', 'yearBuilt', 'capacity', 'parkingSpaces', 'specialUse', 'taxExempt']
  },
  GOVERNMENT: {
    name: 'Government',
    codes: ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89'],
    fields: ['buildingSqft', 'landSqft', 'publicUse', 'specialPurpose']
  },
  VACANT_LAND: {
    name: 'Vacant Land',
    codes: ['00', '10', '40', '70', '80'],
    fields: ['acres', 'zoning', 'utilities', 'roadAccess', 'topography', 'wetlands', 'futureUse', 'entitlements']
  },
  MISCELLANEOUS: {
    name: 'Miscellaneous',
    codes: ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '00C'],
    fields: ['specialUse', 'landSqft', 'description']
  }
}

export const FIELD_DEFINITIONS = {
  // Residential Fields
  beds: { label: 'Bedrooms', type: 'number', icon: 'Bed' },
  baths: { label: 'Bathrooms', type: 'number', icon: 'Bath' },
  sqft: { label: 'Square Feet', type: 'number', icon: 'Square' },
  yearBuilt: { label: 'Year Built', type: 'number', icon: 'Calendar' },
  stories: { label: 'Stories', type: 'number', icon: 'Building' },
  pool: { label: 'Pool', type: 'boolean', icon: 'Droplets' },
  garage: { label: 'Garage Spaces', type: 'number', icon: 'Car' },
  hoa: { label: 'HOA Fee', type: 'currency', icon: 'DollarSign' },
  waterfront: { label: 'Waterfront', type: 'boolean', icon: 'Waves' },
  
  // Commercial Fields
  buildingSqft: { label: 'Building Sq Ft', type: 'number', icon: 'Building2' },
  landSqft: { label: 'Land Sq Ft', type: 'number', icon: 'MapPin' },
  parkingSpaces: { label: 'Parking Spaces', type: 'number', icon: 'ParkingCircle' },
  tenants: { label: 'Number of Tenants', type: 'number', icon: 'Users' },
  occupancyRate: { label: 'Occupancy Rate', type: 'percentage', icon: 'BarChart' },
  netOperatingIncome: { label: 'Net Operating Income', type: 'currency', icon: 'TrendingUp' },
  capRate: { label: 'Cap Rate', type: 'percentage', icon: 'Percent' },
  zoning: { label: 'Zoning', type: 'text', icon: 'FileText' },
  
  // Industrial Fields
  clearHeight: { label: 'Clear Height (ft)', type: 'number', icon: 'ArrowUp' },
  dockDoors: { label: 'Dock Doors', type: 'number', icon: 'Package' },
  railAccess: { label: 'Rail Access', type: 'boolean', icon: 'Train' },
  power: { label: 'Power (Amps)', type: 'text', icon: 'Zap' },
  environmentalStatus: { label: 'Environmental Status', type: 'text', icon: 'Leaf' },
  
  // Agricultural Fields
  acres: { label: 'Acres', type: 'number', icon: 'Trees' },
  irrigated: { label: 'Irrigated', type: 'boolean', icon: 'Droplets' },
  cropType: { label: 'Crop Type', type: 'text', icon: 'Wheat' },
  soilType: { label: 'Soil Type', type: 'text', icon: 'Mountain' },
  waterRights: { label: 'Water Rights', type: 'boolean', icon: 'Droplets' },
  buildings: { label: 'Farm Buildings', type: 'number', icon: 'Barn' },
  equipment: { label: 'Equipment Included', type: 'boolean', icon: 'Tractor' },
  productivity: { label: 'Annual Production', type: 'text', icon: 'TrendingUp' },
  
  // Institutional Fields
  capacity: { label: 'Capacity', type: 'number', icon: 'Users' },
  specialUse: { label: 'Special Use', type: 'text', icon: 'Star' },
  taxExempt: { label: 'Tax Exempt', type: 'boolean', icon: 'Shield' },
  
  // Vacant Land Fields
  utilities: { label: 'Utilities Available', type: 'text', icon: 'Zap' },
  roadAccess: { label: 'Road Access', type: 'text', icon: 'Road' },
  topography: { label: 'Topography', type: 'text', icon: 'Mountain' },
  wetlands: { label: 'Wetlands', type: 'boolean', icon: 'Waves' },
  futureUse: { label: 'Future Land Use', type: 'text', icon: 'Target' },
  entitlements: { label: 'Entitlements', type: 'text', icon: 'FileCheck' },
  
  // Government Fields
  publicUse: { label: 'Public Use', type: 'text', icon: 'Building' },
  specialPurpose: { label: 'Special Purpose', type: 'text', icon: 'Flag' },
  
  // Miscellaneous Fields
  description: { label: 'Description', type: 'text', icon: 'FileText' }
}

export const ZONING_CODES = {
  // Residential
  'RS-1': 'Single Family Residential - Low Density',
  'RS-2': 'Single Family Residential - Medium Density', 
  'RS-3': 'Single Family Residential - High Density',
  'RM-1': 'Multi-Family Residential - Low Density',
  'RM-2': 'Multi-Family Residential - Medium Density',
  'RM-3': 'Multi-Family Residential - High Density',
  'MH': 'Mobile Home',
  
  // Commercial
  'C-1': 'Neighborhood Commercial',
  'C-2': 'General Commercial',
  'C-3': 'Highway Commercial',
  'CBD': 'Central Business District',
  'MU': 'Mixed Use',
  
  // Industrial
  'I-1': 'Light Industrial',
  'I-2': 'Heavy Industrial',
  'I-3': 'Industrial Park',
  
  // Agricultural
  'A-1': 'Agricultural - General',
  'A-2': 'Agricultural - Restricted',
  
  // Special
  'PUD': 'Planned Unit Development',
  'OS': 'Open Space',
  'P': 'Public/Institutional',
  'CON': 'Conservation'
}

export const PROPERTY_STATUS = {
  'ACTIVE': 'For Sale',
  'PENDING': 'Under Contract',
  'SOLD': 'Sold',
  'LEASE': 'For Lease',
  'LEASED': 'Leased',
  'OFF_MARKET': 'Off Market',
  'COMING_SOON': 'Coming Soon'
}