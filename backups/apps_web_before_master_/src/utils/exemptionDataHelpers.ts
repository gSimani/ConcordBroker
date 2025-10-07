/**
 * Helper functions for processing exemption data from the database
 */

export interface ExemptionYearData {
  year: number;
  county_exemption: number;
  county_taxable: number;
  school_exemption: number;
  school_taxable: number;
  city_exemption: number;
  city_taxable: number;
  regional_exemption: number;
  regional_taxable: number;
  homestead_exemption: number;
  additional_homestead: number;
  senior_exemption: number;
  veteran_exemption: number;
  widow_exemption: number;
  disability_exemption: number;
  soh_cap: number;
  assessed_value: number;
  just_value: number;
  market_value: number;
  taxable_value: number;
  tax_amount: number;
}

/**
 * Calculate exemption values from raw database data
 */
export function calculateExemptionValues(data: any): ExemptionYearData {
  const assessed = parseFloat(data?.assessed_value || data?.just_value || '0');
  const market = parseFloat(data?.market_value || data?.just_value || assessed.toString());

  // Calculate homestead exemptions
  const homestead = parseFloat(data?.homestead_exemption || data?.homestead || '0') ||
    (data?.homestead === 'Y' || data?.homestead === true ? 25000 : 0);

  const additionalHomestead = parseFloat(data?.additional_homestead || data?.add_homestead || '0') ||
    (data?.additional_homestead === 'Y' ? 25000 : 0);

  // Calculate other exemptions
  const senior = parseFloat(data?.senior_exemption || data?.senior || '0');
  const veteran = parseFloat(data?.veteran_exemption || data?.veteran || '0');
  const widow = parseFloat(data?.widow_exemption || data?.widow || '0');
  const disability = parseFloat(data?.disability_exemption || data?.disability || '0');

  // Calculate Save Our Homes cap
  const sohCap = parseFloat(data?.soh_cap_current || data?.soh_cap || '0') ||
    (market > assessed ? market - assessed : 0);

  // Calculate taxable values for each authority
  const countyExemption = parseFloat(data?.county_exemption || '0') ||
    (homestead + additionalHomestead + senior + veteran + widow + disability);

  const schoolExemption = parseFloat(data?.school_exemption || '0') || homestead;

  const cityExemption = parseFloat(data?.city_exemption || '0');

  const regionalExemption = parseFloat(data?.regional_exemption || '0') || countyExemption;

  return {
    year: data?.year || new Date().getFullYear(),
    county_exemption: countyExemption,
    county_taxable: parseFloat(data?.county_taxable || '0') || Math.max(0, assessed - countyExemption),
    school_exemption: schoolExemption,
    school_taxable: parseFloat(data?.school_taxable || '0') || Math.max(0, assessed - schoolExemption),
    city_exemption: cityExemption,
    city_taxable: parseFloat(data?.city_taxable || '0') || Math.max(0, assessed - cityExemption),
    regional_exemption: regionalExemption,
    regional_taxable: parseFloat(data?.regional_taxable || '0') || Math.max(0, assessed - regionalExemption),
    homestead_exemption: homestead,
    additional_homestead: additionalHomestead,
    senior_exemption: senior,
    veteran_exemption: veteran,
    widow_exemption: widow,
    disability_exemption: disability,
    soh_cap: sohCap,
    assessed_value: assessed,
    just_value: parseFloat(data?.just_value || '0'),
    market_value: market,
    taxable_value: parseFloat(data?.taxable_value || '0') || Math.max(0, assessed - countyExemption),
    tax_amount: parseFloat(data?.tax_amount || '0')
  };
}

/**
 * Get county-specific exemption URLs
 */
export function getCountyExemptionUrls(county: string): {
  sohUrl: string;
  homesteadUrl: string;
  additionalHomesteadUrl: string;
} {
  const countyUpper = (county || '').toUpperCase();

  switch(countyUpper) {
    case 'MIAMI-DADE':
      return {
        sohUrl: 'https://www.miamidadepa.gov/pa/amendment_10.asp',
        homesteadUrl: 'https://www.miamidadepa.gov/pa/exemptions_homestead.asp',
        additionalHomesteadUrl: 'https://www.miamidadepa.gov/pa/exemptions_homestead_additional.asp'
      };

    case 'BROWARD':
      return {
        sohUrl: 'https://web.bcpa.net/BcpaClient/#/Record-Search',
        homesteadUrl: 'https://web.bcpa.net/BcpaClient/#/Exemptions',
        additionalHomesteadUrl: 'https://web.bcpa.net/BcpaClient/#/Exemptions'
      };

    case 'PALM-BEACH':
    case 'PALM BEACH':
      return {
        sohUrl: 'https://www.pbcgov.org/papa/exemptions.htm',
        homesteadUrl: 'https://www.pbcgov.org/papa/exemptions.htm',
        additionalHomesteadUrl: 'https://www.pbcgov.org/papa/exemptions.htm'
      };

    default:
      return {
        sohUrl: '#',
        homesteadUrl: '#',
        additionalHomesteadUrl: '#'
      };
  }
}

/**
 * Format exemption data for display
 */
export function formatExemptionData(
  exemptionData: Record<number, any>,
  currentYear: number
): {
  current: ExemptionYearData;
  previous: ExemptionYearData;
  twoPrevious: ExemptionYearData;
} {
  return {
    current: calculateExemptionValues(exemptionData[currentYear] || {}),
    previous: calculateExemptionValues(exemptionData[currentYear - 1] || {}),
    twoPrevious: calculateExemptionValues(exemptionData[currentYear - 2] || {})
  };
}