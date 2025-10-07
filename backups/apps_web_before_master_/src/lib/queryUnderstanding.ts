export type ParsedFilters = {
  county?: string
  useCategory?: string
  minValue?: number
  maxValue?: number
  minBeds?: number
  maxBeds?: number
  minBaths?: number
  maxBaths?: number
}

const TYPE_KEYWORDS: Record<string, string[]> = {
  Residential: ['residential', 'single family', 'sfh', 'condo', 'townhouse', 'apartment'],
  Commercial: ['commercial', 'retail', 'office', 'store', 'shopping', 'restaurant'],
  Industrial: ['industrial', 'warehouse', 'manufacturing', 'factory'],
  Agricultural: ['agricultural', 'farm', 'grove', 'orchard'],
  Vacant: ['vacant', 'vacant land', 'empty lot']
}

export function parseQueryToFilters(query: string, counties: string[]): ParsedFilters {
  const result: ParsedFilters = {}
  const q = (query || '').toLowerCase()

  // County detection
  const countyMatch = counties.find(c => q.includes(c.toLowerCase()))
  if (countyMatch && countyMatch !== 'ALL') {
    result.county = countyMatch
  }

  // Type detection
  for (const [type, keywords] of Object.entries(TYPE_KEYWORDS)) {
    if (keywords.some(k => q.includes(k))) {
      result.useCategory = type
      break
    }
  }

  // Beds/Baths pattern like 3/2 or 4-3
  const bb = q.match(/\b(\d{1,2})\s*[\/\-]\s*(\d{1,2})\b/)
  if (bb) {
    const beds = parseInt(bb[1], 10)
    const baths = parseInt(bb[2], 10)
    if (!isNaN(beds)) result.minBeds = beds
    if (!isNaN(baths)) result.minBaths = baths
  }

  // Price extraction: under 600k, <600k, max 600k, up to $600,000
  const priceUnder = q.match(/\b(under|<|max|up to)\s*\$?\s*([\d,.]+)\s*(k|m)?/)
  if (priceUnder) {
    const val = parseFloat(priceUnder[2].replace(/,/g, ''))
    const mult = priceUnder[3] === 'm' ? 1_000_000 : priceUnder[3] === 'k' ? 1_000 : 1
    if (!isNaN(val)) result.maxValue = val * mult
  }

  // Price equals or bare number implies max
  if (!result.maxValue) {
    const bare = q.match(/\$?\s*([\d,.]+)\s*(k|m)\b/)
    if (bare) {
      const val = parseFloat(bare[1].replace(/,/g, ''))
      const mult = bare[2] === 'm' ? 1_000_000 : bare[2] === 'k' ? 1_000 : 1
      if (!isNaN(val)) result.maxValue = val * mult
    }
  }

  // Min price: over 300k / >300k / min 300k
  const priceOver = q.match(/\b(over|>|min|from)\s*\$?\s*([\d,.]+)\s*(k|m)?/)
  if (priceOver) {
    const val = parseFloat(priceOver[2].replace(/,/g, ''))
    const mult = priceOver[3] === 'm' ? 1_000_000 : priceOver[3] === 'k' ? 1_000 : 1
    if (!isNaN(val)) result.minValue = val * mult
  }

  return result
}
