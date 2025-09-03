export const CITIES = [
  'COCONUT CREEK',
  'COOPER CITY',
  'CORAL SPRINGS',
  'DANIA BEACH',
  'DAVIE',
  'DEERFIELD BEACH',
  'FORT LAUDERDALE',
  'HALLANDALE BEACH',
  'HILLSBORO BEACH',
  'HOLLYWOOD',
  'LAUDERDALE-BY-THE-SEA',
  'LAUDERDALE LAKES',
  'LAUDERHILL',
  'LAZY LAKE',
  'LIGHTHOUSE POINT',
  'MARGATE',
  'MIRAMAR',
  'NORTH LAUDERDALE',
  'OAKLAND PARK',
  'PARKLAND',
  'PEMBROKE PARK',
  'PEMBROKE PINES',
  'PLANTATION',
  'POMPANO BEACH',
  'SEA RANCH LAKES',
  'SOUTHWEST RANCHES',
  'SUNRISE',
  'TAMARAC',
  'WEST PARK',
  'WESTON',
  'WILTON MANORS',
] as const

export const USE_CODES: Record<string, string> = {
  '00': 'Vacant Residential',
  '01': 'Single Family',
  '02': 'Mobile Homes',
  '03': 'Multi-family (10+ units)',
  '04': 'Condominiums',
  '08': 'Multi-family (<10 units)',
  '10': 'Vacant Commercial',
  '11': 'Stores',
  '12': 'Mixed Use (Store/Res)',
  '13': 'Department Stores',
  '14': 'Supermarkets',
  '15': 'Regional Shopping',
  '16': 'Community Shopping',
  '17': 'Office Buildings',
  '18': 'Office Buildings (Multi)',
  '19': 'Professional Service',
  '21': 'Restaurants',
  '22': 'Drive-in Restaurants',
  '23': 'Financial Institutions',
  '26': 'Service Stations',
  '27': 'Auto Sales/Service',
  '28': 'Parking Lots',
  '29': 'Wholesale Outlets',
  '33': 'Nightclubs/Bars',
  '38': 'Golf Courses',
  '39': 'Hotels/Motels',
  '40': 'Vacant Industrial',
  '41': 'Light Manufacturing',
  '42': 'Heavy Manufacturing',
  '43': 'Lumber Yards',
  '48': 'Warehousing',
  '49': 'Open Storage',
}

export const SCORE_COLORS = {
  excellent: 'text-green-600 bg-green-50',
  good: 'text-blue-600 bg-blue-50',
  moderate: 'text-yellow-600 bg-yellow-50',
  poor: 'text-red-600 bg-red-50',
} as const

export const getScoreColor = (score: number) => {
  if (score >= 80) return SCORE_COLORS.excellent
  if (score >= 60) return SCORE_COLORS.good
  if (score >= 40) return SCORE_COLORS.moderate
  return SCORE_COLORS.poor
}

export const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export const formatNumber = (value: number) => {
  return new Intl.NumberFormat('en-US').format(value)
}