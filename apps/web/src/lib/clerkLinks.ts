// County clerk link builder for Official Records deep links
// Extend this mapping as portal patterns are confirmed per county.

export interface ClerkLinkResult {
  url: string | null
  text: string
  isDeep: boolean
}

function normalizeCounty(input?: string): string {
  if (!input) return ''
  return input.trim().toUpperCase()
}

export function buildClerkLink(countyRaw: string | undefined, sale: any): ClerkLinkResult {
  const county = normalizeCounty(countyRaw)
  const book = sale?.or_book || sale?.book || sale?.orb || sale?.deed_book
  const page = sale?.or_page || sale?.page || sale?.deed_page
  const doc = sale?.doc_no || sale?.document_no || sale?.document_number || sale?.cin

  const bookPage = book && page ? `${book}/${page}` : null
  const text = bookPage || (doc ? String(doc) : '-')

  // Broward (AcclaimWeb) deep links
  if (county === 'BROWARD') {
    if (book && page) {
      return {
        url: `https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeBookPage?Book=${encodeURIComponent(book)}&Page=${encodeURIComponent(page)}`,
        text: bookPage as string,
        isDeep: true
      }
    }
    if (doc) {
      return {
        url: `https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeInstrumentNumber?InstrumentNumber=${encodeURIComponent(doc)}`,
        text,
        isDeep: true
      }
    }
    return { url: 'https://officialrecords.broward.org/AcclaimWeb/', text: text || '-', isDeep: false }
  }

  // Known Florida county portals (roots). Replace with deep-link templates as confirmed.
  const portalByCounty: Record<string, string> = {
    'MIAMI-DADE': 'https://onlineservices.miamidadeclerk.gov/officialrecords/',
    'DADE': 'https://onlineservices.miamidadeclerk.gov/officialrecords/',
    'PALM BEACH': 'https://www.mypalmbeachclerk.com/official-records',
    'ORANGE': 'https://or.occompt.com/recorder/web/',
    'HILLSBOROUGH': 'https://www.hillsclerk.com/Records-and-Reports/Official-Records-Search',
    'PINELLAS': 'https://officialrecords.mypinellasclerk.org/',
    'LEE': 'https://or.leeclerk.org/OR/Search.aspx',
    'DUVAL': 'https://core.duvalclerk.com/OfficialRecords/',
    'POLK': 'https://orsearch.polkcountyclerk.net/search',
    'SARASOTA': 'https://www.sarasotaclerk.com/records/official-records',
    'COLLIER': 'https://or.collierclerk.com/',
    'PASCO': 'https://ori.pascoclerk.com/',
    'SEMINOLE': 'https://records.seminoleclerk.org/',
    'VOLUSIA': 'https://app02.clerk.org/recorder/eagleweb/docSearch.jsp',
    'BREVARD': 'https://brevardclerk.us/official-records',
    'ALACHUA': 'https://www.alachuaclerk.org/recording/official-records',
    'LEON': 'https://cvweb.leonclerk.com/official_records/',
    'ST LUCIE': 'https://stlucieclerk.com/records-search/',
    'ST. LUCIE': 'https://stlucieclerk.com/records-search/',
    'MANATEE': 'https://records.manateeclerk.com/OfficialRecords/',
    'OSCEOLA': 'https://officialrecords.osceolaclerk.com/'
  }

  const portal = portalByCounty[county]
  if (portal) {
    return { url: portal, text: text || '-', isDeep: false }
  }

  // Unknown county: return reference without link
  return { url: null, text: text || '-', isDeep: false }
}

export function buildClerkPortalDomain(countyRaw: string | undefined): string | null {
  const county = normalizeCounty(countyRaw)
  const portalUrl = buildClerkLink(county, {}).url
  if (!portalUrl) return null
  try {
    const u = new URL(portalUrl)
    return u.hostname || null
  } catch {
    return null
  }
}

export function buildSearchByReferenceUrl(countyRaw: string | undefined, reference: string): string | null {
  if (!reference) return null
  const domain = buildClerkPortalDomain(countyRaw)
  const q = domain ? `site:${domain} "${reference}"` : `"${reference}"`
  return `https://www.google.com/search?q=${encodeURIComponent(q)}`
}
