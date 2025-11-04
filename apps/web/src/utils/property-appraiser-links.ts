/**
 * Property Appraiser URL Generator
 * Generates county-specific Property Appraiser URLs for Florida counties
 */

export interface PropertyAppraiserInfo {
  url: string
  label: string
  searchType: 'direct' | 'search' // direct = has parcel in URL, search = search page only
}

/**
 * Get Property Appraiser URL for a specific Florida county
 * @param county - Florida county name (e.g., 'BROWARD', 'MIAMI-DADE', 'PALM BEACH')
 * @param parcelId - Parcel ID (optional, used for direct links when available)
 * @param address - Property address (optional, for search hints)
 * @returns PropertyAppraiserInfo object with URL and metadata
 */
export function getPropertyAppraiserUrl(
  county: string,
  parcelId?: string,
  address?: string
): PropertyAppraiserInfo {
  const countyUpper = county?.toUpperCase() || ''

  switch (countyUpper) {
    case 'BROWARD':
      // BROWARD requires search - direct parcel links don't work
      return {
        url: 'https://web.bcpa.net/BcpaClient/#/Record-Search',
        label: 'Search BROWARD Property Appraiser',
        searchType: 'search'
      }

    case 'MIAMI-DADE':
    case 'MIAMIDADE':
    case 'MIAMI DADE':
      return {
        url: 'https://www.miamidadepa.gov/pa/home.page',
        label: 'Search MIAMI-DADE Property Appraiser',
        searchType: 'search'
      }

    case 'PALM BEACH':
    case 'PALMBEACH':
    case 'PALM_BEACH':
      return {
        url: 'https://pbcpao.gov/index.htm',
        label: 'Search PALM BEACH Property Appraiser',
        searchType: 'search'
      }

    case 'HILLSBOROUGH':
      // Hillsborough has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.hcpafl.org/Property/PropertyDetail?parcelID=${parcelId}`,
          label: 'View on HILLSBOROUGH Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.hcpafl.org/Property/Search',
        label: 'Search HILLSBOROUGH Property Appraiser',
        searchType: 'search'
      }

    case 'ORANGE':
      // Orange County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.ocpafl.org/searches/ParcelSearch.aspx?s=1&Parcel=${parcelId}`,
          label: 'View on ORANGE Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.ocpafl.org/searches/ParcelSearch.aspx',
        label: 'Search ORANGE Property Appraiser',
        searchType: 'search'
      }

    case 'PINELLAS':
      // Pinellas has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.pcpao.org/PropertySearch/ParcelDetail?parcelID=${parcelId}`,
          label: 'View on PINELLAS Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.pcpao.org/PropertySearch',
        label: 'Search PINELLAS Property Appraiser',
        searchType: 'search'
      }

    case 'DUVAL':
      // Duval (Jacksonville) has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://paopropertysearch.coj.net/Basic/Detail.aspx?RE=${parcelId}`,
          label: 'View on DUVAL Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://paopropertysearch.coj.net/',
        label: 'Search DUVAL Property Appraiser',
        searchType: 'search'
      }

    case 'LEE':
      // Lee County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.leepa.org/Search/Parcel.aspx?strap=${parcelId}`,
          label: 'View on LEE Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.leepa.org/Search',
        label: 'Search LEE Property Appraiser',
        searchType: 'search'
      }

    case 'POLK':
      // Polk County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.polkpa.org/propertysearch/${parcelId}`,
          label: 'View on POLK Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.polkpa.org/propertysearch',
        label: 'Search POLK Property Appraiser',
        searchType: 'search'
      }

    case 'BREVARD':
      // Brevard County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://brevard.county-taxes.com/public/real_estate/parcels/${parcelId}`,
          label: 'View on BREVARD Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://brevardpa.gov/PropertySearch',
        label: 'Search BREVARD Property Appraiser',
        searchType: 'search'
      }

    case 'VOLUSIA':
      // Volusia County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.vcpa.us/search/CommonSearch.aspx?mode=PARID&id=${parcelId}`,
          label: 'View on VOLUSIA Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.vcpa.us/search/CommonSearch.aspx',
        label: 'Search VOLUSIA Property Appraiser',
        searchType: 'search'
      }

    case 'SEMINOLE':
      // Seminole County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.scpafl.org/Search/Parcel/${parcelId}`,
          label: 'View on SEMINOLE Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.scpafl.org/Search',
        label: 'Search SEMINOLE Property Appraiser',
        searchType: 'search'
      }

    case 'COLLIER':
      // Collier County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://collierappraiser.com/parcel-search?parcelId=${parcelId}`,
          label: 'View on COLLIER Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://collierappraiser.com/parcel-search',
        label: 'Search COLLIER Property Appraiser',
        searchType: 'search'
      }

    case 'SARASOTA':
      // Sarasota County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.sc-pa.com/SearchParcels/Detail/${parcelId}`,
          label: 'View on SARASOTA Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.sc-pa.com/SearchParcels',
        label: 'Search SARASOTA Property Appraiser',
        searchType: 'search'
      }

    case 'MANATEE':
      // Manatee County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.manateepao.com/property/${parcelId}`,
          label: 'View on MANATEE Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.manateepao.com/property-search',
        label: 'Search MANATEE Property Appraiser',
        searchType: 'search'
      }

    case 'PASCO':
      // Pasco County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.pascopa.com/Home/PropertyDetail/${parcelId}`,
          label: 'View on PASCO Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.pascopa.com/',
        label: 'Search PASCO Property Appraiser',
        searchType: 'search'
      }

    case 'LAKE':
      // Lake County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.lakecopropappr.com/propertysearch/${parcelId}`,
          label: 'View on LAKE Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.lakecopropappr.com/propertysearch',
        label: 'Search LAKE Property Appraiser',
        searchType: 'search'
      }

    case 'ESCAMBIA':
      // Escambia County has direct parcel lookup
      if (parcelId) {
        return {
          url: `https://www.ecpao.com/search/summary.asp?id=${parcelId}`,
          label: 'View on ESCAMBIA Property Appraiser',
          searchType: 'direct'
        }
      }
      return {
        url: 'https://www.ecpao.com/search/',
        label: 'Search ESCAMBIA Property Appraiser',
        searchType: 'search'
      }

    default:
      // Default fallback - return search page with hint
      return {
        url: `https://www.google.com/search?q=${encodeURIComponent(county + ' Florida Property Appraiser')}`,
        label: `Search ${county} Property Appraiser`,
        searchType: 'search'
      }
  }
}

/**
 * Get GIS Map URL for a specific Florida county
 * @param county - Florida county name
 * @param parcelId - Parcel ID (optional)
 * @returns GIS Map URL or null if not available
 */
export function getGISMapUrl(county: string, parcelId?: string): string | null {
  const countyUpper = county?.toUpperCase() || ''

  switch (countyUpper) {
    case 'BROWARD':
      if (parcelId) {
        return `https://bcpa.maps.arcgis.com/apps/webappviewer/index.html?find=${encodeURIComponent(parcelId)}`
      }
      return 'https://bcpa.maps.arcgis.com/apps/webappviewer/index.html'

    case 'MIAMI-DADE':
    case 'MIAMIDADE':
    case 'MIAMI DADE':
      if (parcelId) {
        return `https://gisweb.miamidade.gov/gismap/?parcel=${encodeURIComponent(parcelId)}`
      }
      return 'https://gisweb.miamidade.gov/gismap/'

    case 'PALM BEACH':
    case 'PALMBEACH':
    case 'PALM_BEACH':
      if (parcelId) {
        return `https://www.pbcgov.org/papa/Asps/PropertySearchResult.aspx?parcel=${encodeURIComponent(parcelId)}`
      }
      return 'https://discover.pbcgov.org/pzb/Pages/default.aspx'

    default:
      return null
  }
}
