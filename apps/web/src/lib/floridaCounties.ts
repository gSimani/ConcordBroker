/**
 * Static list of Florida's 67 counties
 * Used for instant autocomplete without database queries
 */

export const FLORIDA_COUNTIES = [
  'ALACHUA',
  'BAKER',
  'BAY',
  'BRADFORD',
  'BREVARD',
  'BROWARD',
  'CALHOUN',
  'CHARLOTTE',
  'CITRUS',
  'CLAY',
  'COLLIER',
  'COLUMBIA',
  'DESOTO',
  'DIXIE',
  'DUVAL',
  'ESCAMBIA',
  'FLAGLER',
  'FRANKLIN',
  'GADSDEN',
  'GILCHRIST',
  'GLADES',
  'GULF',
  'HAMILTON',
  'HARDEE',
  'HENDRY',
  'HERNANDO',
  'HIGHLANDS',
  'HILLSBOROUGH',
  'HOLMES',
  'INDIAN_RIVER',
  'JACKSON',
  'JEFFERSON',
  'LAFAYETTE',
  'LAKE',
  'LEE',
  'LEON',
  'LEVY',
  'LIBERTY',
  'MADISON',
  'MANATEE',
  'MARION',
  'MARTIN',
  'MIAMI-DADE',
  'MONROE',
  'NASSAU',
  'OKALOOSA',
  'OKEECHOBEE',
  'ORANGE',
  'OSCEOLA',
  'PALM_BEACH',
  'PASCO',
  'PINELLAS',
  'POLK',
  'PUTNAM',
  'SANTA_ROSA',
  'SARASOTA',
  'SEMINOLE',
  'ST_JOHNS',
  'ST_LUCIE',
  'SUMTER',
  'SUWANNEE',
  'TAYLOR',
  'UNION',
  'VOLUSIA',
  'WAKULLA',
  'WALTON',
  'WASHINGTON'
] as const;

/**
 * Filter counties by search query (instant, no database needed)
 */
export function searchCounties(query: string, limit: number = 5): string[] {
  if (!query || query.length < 2) return [];

  const cleanQuery = query.trim().toUpperCase();

  return FLORIDA_COUNTIES
    .filter(county => county.startsWith(cleanQuery))
    .slice(0, limit);
}

/**
 * Get display name for county (converts underscores to spaces)
 */
export function getCountyDisplayName(county: string): string {
  return county.replace(/_/g, ' ');
}
