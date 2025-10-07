// County-specific URLs for Property Appraiser and Tax Collector websites
// Covers all 67 Florida counties

interface CountyUrls {
  propertyAppraiser: string;
  taxCollector: string;
}

interface CountyConfig {
  [county: string]: CountyUrls;
}

// Florida County Property Appraiser and Tax Collector URLs
export const FLORIDA_COUNTY_URLS: CountyConfig = {
  'ALACHUA': {
    propertyAppraiser: 'https://www.acpafl.org/property/{parcelId}',
    taxCollector: 'https://www.alachuacollector.com/property/{parcelId}'
  },
  'BAKER': {
    propertyAppraiser: 'https://www.bakerpa.com/property/{parcelId}',
    taxCollector: 'https://www.bakertaxcollector.com/property/{parcelId}'
  },
  'BAY': {
    propertyAppraiser: 'https://www.baypa.net/property/{parcelId}',
    taxCollector: 'https://www.baytaxcollector.com/property/{parcelId}'
  },
  'BRADFORD': {
    propertyAppraiser: 'https://www.bradfordappraiser.com/property/{parcelId}',
    taxCollector: 'https://www.bradfordtaxcollector.com/property/{parcelId}'
  },
  'BREVARD': {
    propertyAppraiser: 'https://www.bcpao.us/PropertySearch/#/parcel/{parcelId}',
    taxCollector: 'https://www.brevardtaxcollector.com/property/{parcelId}'
  },
  'BROWARD': {
    propertyAppraiser: 'https://www.bcpa.net/RecInfo.asp?URL_Folio={parcelId}',
    taxCollector: 'https://broward.county-taxes.com/public/real_estate/parcels/{parcelId}'
  },
  'CALHOUN': {
    propertyAppraiser: 'https://www.calhounpa.com/property/{parcelId}',
    taxCollector: 'https://www.calhouncollector.com/property/{parcelId}'
  },
  'CHARLOTTE': {
    propertyAppraiser: 'https://www.ccappraiser.com/property/{parcelId}',
    taxCollector: 'https://www.charlottetax.com/property/{parcelId}'
  },
  'CITRUS': {
    propertyAppraiser: 'https://www.pa.citrus.fl.us/property/{parcelId}',
    taxCollector: 'https://www.citrusTaxCollector.com/property/{parcelId}'
  },
  'CLAY': {
    propertyAppraiser: 'https://www.ccpao.com/property/{parcelId}',
    taxCollector: 'https://www.claytaxcollector.com/property/{parcelId}'
  },
  'COLLIER': {
    propertyAppraiser: 'https://www.collierappraiser.com/property/{parcelId}',
    taxCollector: 'https://www.colliertax.com/property/{parcelId}'
  },
  'COLUMBIA': {
    propertyAppraiser: 'https://www.columbiacountyfla.com/PropertyAppraiser/property/{parcelId}',
    taxCollector: 'https://www.columbiataxcollector.com/property/{parcelId}'
  },
  'DESOTO': {
    propertyAppraiser: 'https://www.desotopa.com/property/{parcelId}',
    taxCollector: 'https://www.desototaxcollector.com/property/{parcelId}'
  },
  'DIXIE': {
    propertyAppraiser: 'https://www.dixiepa.com/property/{parcelId}',
    taxCollector: 'https://www.dixietaxcollector.com/property/{parcelId}'
  },
  'DUVAL': {
    propertyAppraiser: 'https://www.coj.net/departments/property-appraiser/property-search?parcel={parcelId}',
    taxCollector: 'https://www.duvaltaxcollector.net/property/{parcelId}'
  },
  'ESCAMBIA': {
    propertyAppraiser: 'https://www.escpa.org/property/{parcelId}',
    taxCollector: 'https://www.escambiataxcollector.com/property/{parcelId}'
  },
  'FLAGLER': {
    propertyAppraiser: 'https://www.flaglerpa.com/property/{parcelId}',
    taxCollector: 'https://www.flaglertax.com/property/{parcelId}'
  },
  'FRANKLIN': {
    propertyAppraiser: 'https://www.franklinclerk.com/property/{parcelId}',
    taxCollector: 'https://www.franklintaxcollector.com/property/{parcelId}'
  },
  'GADSDEN': {
    propertyAppraiser: 'https://www.gadsdenproperty.com/property/{parcelId}',
    taxCollector: 'https://www.gadsdentaxcollector.com/property/{parcelId}'
  },
  'GILCHRIST': {
    propertyAppraiser: 'https://www.gilchristcounty.com/property/{parcelId}',
    taxCollector: 'https://www.gilchristtaxcollector.com/property/{parcelId}'
  },
  'GLADES': {
    propertyAppraiser: 'https://www.gladespa.com/property/{parcelId}',
    taxCollector: 'https://www.gladestaxcollector.com/property/{parcelId}'
  },
  'GULF': {
    propertyAppraiser: 'https://www.gulfpa.com/property/{parcelId}',
    taxCollector: 'https://www.gulftaxcollector.com/property/{parcelId}'
  },
  'HAMILTON': {
    propertyAppraiser: 'https://www.hamiltonpa.com/property/{parcelId}',
    taxCollector: 'https://www.hamiltontaxcollector.com/property/{parcelId}'
  },
  'HARDEE': {
    propertyAppraiser: 'https://www.hardeepa.com/property/{parcelId}',
    taxCollector: 'https://www.hardeetaxcollector.com/property/{parcelId}'
  },
  'HENDRY': {
    propertyAppraiser: 'https://www.hendrypa.com/property/{parcelId}',
    taxCollector: 'https://www.hendrytaxcollector.com/property/{parcelId}'
  },
  'HERNANDO': {
    propertyAppraiser: 'https://www.hernandocounty.us/property/{parcelId}',
    taxCollector: 'https://www.hernandotaxcollector.com/property/{parcelId}'
  },
  'HIGHLANDS': {
    propertyAppraiser: 'https://www.appraiser.co.highlands.fl.us/property/{parcelId}',
    taxCollector: 'https://www.hctaxcollector.com/property/{parcelId}'
  },
  'HILLSBOROUGH': {
    propertyAppraiser: 'https://www.hcpafl.org/Property/ParcelID/{parcelId}',
    taxCollector: 'https://www.hillstax.org/property/{parcelId}'
  },
  'HOLMES': {
    propertyAppraiser: 'https://www.holmespa.com/property/{parcelId}',
    taxCollector: 'https://www.holmestaxcollector.com/property/{parcelId}'
  },
  'INDIAN RIVER': {
    propertyAppraiser: 'https://www.ircpa.org/property/{parcelId}',
    taxCollector: 'https://www.irctax.com/property/{parcelId}'
  },
  'JACKSON': {
    propertyAppraiser: 'https://www.jacksonpa.com/property/{parcelId}',
    taxCollector: 'https://www.jacksontaxcollector.com/property/{parcelId}'
  },
  'JEFFERSON': {
    propertyAppraiser: 'https://www.jeffersonpa.net/property/{parcelId}',
    taxCollector: 'https://www.jeffersontaxcollector.com/property/{parcelId}'
  },
  'LAFAYETTE': {
    propertyAppraiser: 'https://www.lafayettepa.com/property/{parcelId}',
    taxCollector: 'https://www.lafayettetaxcollector.com/property/{parcelId}'
  },
  'LAKE': {
    propertyAppraiser: 'https://www.lakecopropappr.com/property/{parcelId}',
    taxCollector: 'https://www.laketax.com/property/{parcelId}'
  },
  'LEE': {
    propertyAppraiser: 'https://www.leepa.org/Search/PropertySearch.aspx?pid={parcelId}',
    taxCollector: 'https://www.leetc.com/property/{parcelId}'
  },
  'LEON': {
    propertyAppraiser: 'https://www.leonpa.org/property/{parcelId}',
    taxCollector: 'https://www.leontaxcollector.net/property/{parcelId}'
  },
  'LEVY': {
    propertyAppraiser: 'https://www.levypa.com/property/{parcelId}',
    taxCollector: 'https://www.levytaxcollector.com/property/{parcelId}'
  },
  'LIBERTY': {
    propertyAppraiser: 'https://www.libertypa.com/property/{parcelId}',
    taxCollector: 'https://www.libertytaxcollector.com/property/{parcelId}'
  },
  'MADISON': {
    propertyAppraiser: 'https://www.madisonpa.com/property/{parcelId}',
    taxCollector: 'https://www.madisontaxcollector.com/property/{parcelId}'
  },
  'MANATEE': {
    propertyAppraiser: 'https://www.manateepao.com/property/{parcelId}',
    taxCollector: 'https://www.taxcollector.com/property/{parcelId}'
  },
  'MARION': {
    propertyAppraiser: 'https://www.pa.marion.fl.us/property/{parcelId}',
    taxCollector: 'https://www.mariontaxcollector.com/property/{parcelId}'
  },
  'MARTIN': {
    propertyAppraiser: 'https://www.pa.martin.fl.us/property/{parcelId}',
    taxCollector: 'https://www.martintaxcollector.com/property/{parcelId}'
  },
  'MIAMI-DADE': {
    propertyAppraiser: 'https://www.miamidade.gov/Apps/PA/propertysearch/#/property/{parcelId}',
    taxCollector: 'https://miamidade.county-taxes.com/public/real_estate/parcels/{parcelId}',
    taxCollectorFormat: 'hyphenated'  // Special format for Miami-Dade
  },
  'MONROE': {
    propertyAppraiser: 'https://www.mcpafl.org/property/{parcelId}',
    taxCollector: 'https://www.monroetaxcollector.com/property/{parcelId}'
  },
  'NASSAU': {
    propertyAppraiser: 'https://www.nassauflpa.com/property/{parcelId}',
    taxCollector: 'https://www.nassautaxfl.com/property/{parcelId}'
  },
  'OKALOOSA': {
    propertyAppraiser: 'https://www.okaloosaPA.com/property/{parcelId}',
    taxCollector: 'https://www.okaloosatax.com/property/{parcelId}'
  },
  'OKEECHOBEE': {
    propertyAppraiser: 'https://www.okeechobeepa.com/property/{parcelId}',
    taxCollector: 'https://www.okeechobeetaxcollector.com/property/{parcelId}'
  },
  'ORANGE': {
    propertyAppraiser: 'https://www.ocpafl.org/property/{parcelId}',
    taxCollector: 'https://www.octaxcol.com/property/{parcelId}'
  },
  'OSCEOLA': {
    propertyAppraiser: 'https://www.osceolapropertytax.com/property/{parcelId}',
    taxCollector: 'https://www.osceolataxcollector.org/property/{parcelId}'
  },
  'PALM BEACH': {
    propertyAppraiser: 'https://www.pbcpao.gov/property/{parcelId}',
    taxCollector: 'https://www.pbctax.com/property/{parcelId}'
  },
  'PASCO': {
    propertyAppraiser: 'https://www.pascopa.com/property/{parcelId}',
    taxCollector: 'https://www.pascotaxes.com/property/{parcelId}'
  },
  'PINELLAS': {
    propertyAppraiser: 'https://www.pcpao.org/property/{parcelId}',
    taxCollector: 'https://www.taxcollect.com/property/{parcelId}'
  },
  'POLK': {
    propertyAppraiser: 'https://www.polkpa.org/property/{parcelId}',
    taxCollector: 'https://www.polktaxes.com/property/{parcelId}'
  },
  'PUTNAM': {
    propertyAppraiser: 'https://www.putnam-fl.com/property-appraiser/property/{parcelId}',
    taxCollector: 'https://www.putnamtaxcollector.com/property/{parcelId}'
  },
  'ST. JOHNS': {
    propertyAppraiser: 'https://www.sjcpa.us/property/{parcelId}',
    taxCollector: 'https://www.sjctax.us/property/{parcelId}'
  },
  'ST. LUCIE': {
    propertyAppraiser: 'https://www.paslc.gov/property/{parcelId}',
    taxCollector: 'https://www.stlucietax.com/property/{parcelId}'
  },
  'SANTA ROSA': {
    propertyAppraiser: 'https://www.srcpa.org/property/{parcelId}',
    taxCollector: 'https://www.srctax.com/property/{parcelId}'
  },
  'SARASOTA': {
    propertyAppraiser: 'https://www.scpa.sc-govern.com/property/{parcelId}',
    taxCollector: 'https://www.sarasotataxcollector.com/property/{parcelId}'
  },
  'SEMINOLE': {
    propertyAppraiser: 'https://www.scpafl.org/property/{parcelId}',
    taxCollector: 'https://www.seminoletax.org/property/{parcelId}'
  },
  'SUMTER': {
    propertyAppraiser: 'https://www.sumterpa.com/property/{parcelId}',
    taxCollector: 'https://www.sumtertaxcollector.com/property/{parcelId}'
  },
  'SUWANNEE': {
    propertyAppraiser: 'https://www.suwanneepa.com/property/{parcelId}',
    taxCollector: 'https://www.suwanneetaxcollector.com/property/{parcelId}'
  },
  'TAYLOR': {
    propertyAppraiser: 'https://www.taylorpa.com/property/{parcelId}',
    taxCollector: 'https://www.taylortaxcollector.com/property/{parcelId}'
  },
  'UNION': {
    propertyAppraiser: 'https://www.unionflpa.com/property/{parcelId}',
    taxCollector: 'https://www.uniontaxcollector.com/property/{parcelId}'
  },
  'VOLUSIA': {
    propertyAppraiser: 'https://www.volusia.org/services/property-appraiser/property/{parcelId}',
    taxCollector: 'https://www.volusiataxcollector.gov/property/{parcelId}'
  },
  'WAKULLA': {
    propertyAppraiser: 'https://www.wakullaappraiser.com/property/{parcelId}',
    taxCollector: 'https://www.wakullataxcollector.com/property/{parcelId}'
  },
  'WALTON': {
    propertyAppraiser: 'https://www.waltonpa.com/property/{parcelId}',
    taxCollector: 'https://www.waltontaxcollector.com/property/{parcelId}'
  },
  'WASHINGTON': {
    propertyAppraiser: 'https://www.washingtonpa.com/property/{parcelId}',
    taxCollector: 'https://www.washingtontaxcollector.com/property/{parcelId}'
  }
};

/**
 * Get Property Appraiser URL for a specific county and parcel ID
 */
export function getPropertyAppraiserUrl(county: string, parcelId: string): string {
  const countyUpper = county?.toUpperCase().trim();
  const countyConfig = FLORIDA_COUNTY_URLS[countyUpper];

  if (!countyConfig) {
    // Fallback to generic Florida property search
    return `https://www.floridaproperty.gov/search?parcel=${parcelId}`;
  }

  // Replace {parcelId} placeholder with actual parcel ID
  return countyConfig.propertyAppraiser.replace('{parcelId}', parcelId);
}

/**
 * Get Tax Collector URL for a specific county and parcel ID
 */
export function getTaxCollectorUrl(county: string, parcelId: string): string {
  const countyUpper = county?.toUpperCase().trim();
  const countyConfig = FLORIDA_COUNTY_URLS[countyUpper];

  if (!countyConfig) {
    // Fallback to county-taxes.com with county prefix
    const countySlug = county?.toLowerCase().replace(/\s+/g, '-') || 'florida';
    return `https://${countySlug}.county-taxes.com/public/real_estate/parcels/${parcelId}`;
  }

  // Format parcel ID based on county requirements
  let formattedParcelId = parcelId;

  // Miami-Dade requires hyphenated format: 30-4019-001-2860
  if (countyUpper === 'MIAMI-DADE' && parcelId) {
    // Convert 3040190012860 to 30-4019-001-2860
    const cleaned = parcelId.replace(/[^0-9]/g, '');
    if (cleaned.length === 13) {
      formattedParcelId = `${cleaned.slice(0, 2)}-${cleaned.slice(2, 6)}-${cleaned.slice(6, 9)}-${cleaned.slice(9)}`;
    }
  }

  // Replace {parcelId} placeholder with formatted parcel ID
  return countyConfig.taxCollector.replace('{parcelId}', formattedParcelId);
}

/**
 * Get both Property Appraiser and Tax Collector URLs
 */
export function getCountyPropertyUrls(county: string, parcelId: string): CountyUrls {
  return {
    propertyAppraiser: getPropertyAppraiserUrl(county, parcelId),
    taxCollector: getTaxCollectorUrl(county, parcelId)
  };
}