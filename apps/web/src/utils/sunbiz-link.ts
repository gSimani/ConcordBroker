/**
 * SUNBIZ (Florida Department of State) linking utility
 * Generates search URLs for companies in the Florida business database
 */

export interface SunbizLinkInfo {
  isSunbiz: boolean
  companyType?: string
  searchUrl?: string
  searchName: string
}

/**
 * Detect if a name is likely a company and generate SUNBIZ search URL
 */
export function getSunbizLink(name: string | null | undefined): SunbizLinkInfo {
  if (!name) {
    return {
      isSunbiz: false,
      searchName: ''
    }
  }

  const upperName = name.toUpperCase()

  // Company type indicators
  const companyIndicators = [
    { type: 'LLC', pattern: /\bLLC\b/ },
    { type: 'INC', pattern: /\bINC\.?\b/ },
    { type: 'CORP', pattern: /\bCORP\.?\b/ },
    { type: 'CORPORATION', pattern: /\bCORPORATION\b/ },
    { type: 'LTD', pattern: /\bLTD\.?\b/ },
    { type: 'LIMITED', pattern: /\bLIMITED\b/ },
    { type: 'LP', pattern: /\bLP\b/ },
    { type: 'PARTNERSHIP', pattern: /\bPARTNERSHIP\b/ },
    { type: 'PA', pattern: /\bPA\b/ },
    { type: 'PC', pattern: /\bPC\b/ },
    { type: 'PLLC', pattern: /\bPLLC\b/ }
  ]

  // Check for company indicators
  for (const indicator of companyIndicators) {
    if (indicator.pattern.test(upperName)) {
      // Clean the name for searching
      let searchName = name.trim()

      // Remove common suffixes for better search results
      searchName = searchName.replace(/,?\s+(LLC|INC\.?|CORP\.?|CORPORATION|LTD\.?|LIMITED|LP|PARTNERSHIP|PA|PC|PLLC)$/i, '')

      // Generate SUNBIZ search URL
      const encodedName = encodeURIComponent(searchName)
      const searchUrl = `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResults?inquirytype=EntityName&searchNameOrder=TRUE&searchTerm=${encodedName}`

      return {
        isSunbiz: true,
        companyType: indicator.type,
        searchUrl,
        searchName
      }
    }
  }

  // Not a company
  return {
    isSunbiz: false,
    searchName: name
  }
}

/**
 * Get SUNBIZ direct entity URL (if you have the entity number)
 */
export function getSunbizEntityUrl(entityNumber: string): string {
  return `https://search.sunbiz.org/Inquiry/CorporationSearch/SearchResultDetail?inquirytype=EntityName&directionType=Initial&searchNameOrder=TRUE&aggregateId=${entityNumber}`
}

/**
 * Format company name with type badge
 */
export function formatCompanyName(name: string | null | undefined): { displayName: string, badge?: string } {
  if (!name) {
    return { displayName: '' }
  }

  const sunbizInfo = getSunbizLink(name)

  if (sunbizInfo.isSunbiz && sunbizInfo.companyType) {
    return {
      displayName: name,
      badge: sunbizInfo.companyType
    }
  }

  return { displayName: name }
}
