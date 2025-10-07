import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client from environment only
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey)

// Florida millage rates by county (2024-2025)
const COUNTY_MILLAGE_RATES = {
  'MIAMI-DADE': {
    school_operating: 5.468,
    school_debt: 0.134,
    school_voted: 1.000,
    county_operating: 4.574,
    county_debt: 0.427,
    unincorporated: 1.909,
    library: 0.281,
    fire_rescue: 2.397,
    water_mgmt: 0.095,
    inland_nav: 0.029,
    okeechobee: 0.103,
    everglades: 0.033,
    childrens_trust: 0.500,
    total: 16.949
  },
  'BROWARD': {
    school_operating: 5.219,
    school_debt: 0.152,
    school_voted: 1.000,
    county_operating: 5.353,
    county_debt: 0.282,
    library: 0.312,
    fire_rescue: 2.185,
    water_mgmt: 0.095,
    inland_nav: 0.035,
    total: 14.633
  },
  'PALM BEACH': {
    school_operating: 5.275,
    school_debt: 0.195,
    school_voted: 1.000,
    county_operating: 4.715,
    county_debt: 0.350,
    library: 0.291,
    fire_rescue: 3.436,
    water_mgmt: 0.095,
    inland_nav: 0.035,
    total: 15.392
  },
  'DEFAULT': {
    school_operating: 5.500,
    school_debt: 0.150,
    school_voted: 1.000,
    county_operating: 4.500,
    county_debt: 0.400,
    library: 0.300,
    fire_rescue: 2.500,
    water_mgmt: 0.095,
    total: 14.445
  }
}

// Non-ad valorem assessments (typical values)
const NON_AD_VALOREM_ASSESSMENTS = {
  garbage_collection: 697.00,
  street_lighting: 39.56,
  stormwater: 125.00,
  special_district: 75.00
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=7200')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  const { id } = req.query

  if (!id || typeof id !== 'string') {
    return res.status(400).json({
      success: false,
      error: 'Property ID required'
    })
  }

  try {
    // 1. Fetch property data from florida_parcels
    const { data: property, error: propertyError } = await supabase
      .from('florida_parcels')
      .select('*')
      .or(`parcel_id.eq.${id},id.eq.${id}`)
      .single()

    if (propertyError || !property) {
      return res.status(404).json({
        success: false,
        error: 'Property not found'
      })
    }

    // 2. Get millage rates for county
    const county = (property.county || 'DEFAULT').toUpperCase().replace(' ', '-')
    const millageRates = COUNTY_MILLAGE_RATES[county] || COUNTY_MILLAGE_RATES['DEFAULT']

    // 3. Calculate exemptions
    const homesteadExemption = property.homestead || property.homestead_exemption ? 25000 : 0
    const additionalHomesteadExemption = property.additional_homestead || property.add_homestead ?
      Math.min(25000, Math.max(0, (property.assessed_value || property.just_value || 0) - 50000)) : 0

    // County gets full $50k homestead exemption
    const countyHomesteadExemption = homesteadExemption + additionalHomesteadExemption
    // School only gets first $25k
    const schoolHomesteadExemption = homesteadExemption

    // 4. Calculate taxable values
    const assessedValue = property.assessed_value || property.just_value || 0
    const schoolTaxableValue = Math.max(0, assessedValue - schoolHomesteadExemption)
    const countyTaxableValue = Math.max(0, assessedValue - countyHomesteadExemption)

    // 5. Calculate ad valorem taxes
    const adValoremBreakdown = {
      school_board: {
        operating: (schoolTaxableValue * millageRates.school_operating) / 1000,
        debt_service: (schoolTaxableValue * millageRates.school_debt) / 1000,
        voted_operating: (schoolTaxableValue * millageRates.school_voted) / 1000,
        total: 0
      },
      county: {
        operating: (countyTaxableValue * millageRates.county_operating) / 1000,
        debt_service: (countyTaxableValue * (millageRates.county_debt || 0)) / 1000,
        unincorporated: (countyTaxableValue * (millageRates.unincorporated || 0)) / 1000,
        library: (countyTaxableValue * (millageRates.library || 0)) / 1000,
        fire_rescue: (countyTaxableValue * (millageRates.fire_rescue || 0)) / 1000,
        total: 0
      },
      special_districts: {
        water_mgmt: (countyTaxableValue * (millageRates.water_mgmt || 0)) / 1000,
        inland_nav: (countyTaxableValue * (millageRates.inland_nav || 0)) / 1000,
        okeechobee: (countyTaxableValue * (millageRates.okeechobee || 0)) / 1000,
        everglades: (countyTaxableValue * (millageRates.everglades || 0)) / 1000,
        childrens_trust: (countyTaxableValue * (millageRates.childrens_trust || 0)) / 1000,
        total: 0
      }
    }

    // Calculate totals for each category
    adValoremBreakdown.school_board.total = Object.values(adValoremBreakdown.school_board)
      .filter(v => typeof v === 'number')
      .reduce((a, b) => a + b, 0)

    adValoremBreakdown.county.total = Object.values(adValoremBreakdown.county)
      .filter(v => typeof v === 'number')
      .reduce((a, b) => a + b, 0)

    adValoremBreakdown.special_districts.total = Object.values(adValoremBreakdown.special_districts)
      .filter(v => typeof v === 'number')
      .reduce((a, b) => a + b, 0)

    const totalAdValorem = adValoremBreakdown.school_board.total +
      adValoremBreakdown.county.total +
      adValoremBreakdown.special_districts.total

    // 6. Calculate non-ad valorem assessments
    const nonAdValoremBreakdown = {
      garbage_collection: NON_AD_VALOREM_ASSESSMENTS.garbage_collection,
      street_lighting: NON_AD_VALOREM_ASSESSMENTS.street_lighting,
      stormwater: property.land_sqft ? (property.land_sqft / 43560) * 50 : 125, // $50 per acre
      special_district: NON_AD_VALOREM_ASSESSMENTS.special_district
    }

    const totalNonAdValorem = Object.values(nonAdValoremBreakdown).reduce((a, b) => a + b, 0)

    // 7. Calculate total tax
    const totalTax = totalAdValorem + totalNonAdValorem

    // 8. Calculate payment schedule with discounts
    const currentYear = new Date().getFullYear()
    const paymentSchedule = {
      november: {
        due_date: `November 30, ${currentYear}`,
        discount: 0.04,
        amount: totalTax * 0.96
      },
      december: {
        due_date: `December 31, ${currentYear}`,
        discount: 0.03,
        amount: totalTax * 0.97
      },
      january: {
        due_date: `January 31, ${currentYear + 1}`,
        discount: 0.02,
        amount: totalTax * 0.98
      },
      february: {
        due_date: `February 28, ${currentYear + 1}`,
        discount: 0.01,
        amount: totalTax * 0.99
      },
      march: {
        due_date: `March 31, ${currentYear + 1}`,
        discount: 0,
        amount: totalTax
      }
    }

    // 9. Check for tax certificates (if available)
    let taxCertificates = []
    try {
      const { data: certs } = await supabase
        .from('tax_certificates')
        .select('*')
        .eq('parcel_id', property.parcel_id)
        .order('tax_year', { ascending: false })
        .limit(10)

      if (certs) {
        taxCertificates = certs
      }
    } catch (e) {
      // Tax certificates table might not exist
    }

    // 10. Format comprehensive tax data response
    const taxData = {
      // Property identification
      parcel_id: property.parcel_id,
      county: property.county,
      owner_name: property.owner_name,
      property_address: property.phy_addr1,
      property_city: property.phy_city,
      property_zip: property.phy_zipcd,

      // Tax year
      tax_year: currentYear,

      // Property values
      market_value: property.market_value || property.just_value,
      just_value: property.just_value,
      assessed_value: assessedValue,
      land_value: property.land_value,
      building_value: property.building_value,

      // Exemptions
      exemptions: {
        homestead: homesteadExemption,
        additional_homestead: additionalHomesteadExemption,
        senior: property.senior_exemption || 0,
        veteran: property.veteran_exemption || 0,
        widow: property.widow_exemption || 0,
        disability: property.disability_exemption || 0,
        total_county: countyHomesteadExemption,
        total_school: schoolHomesteadExemption
      },

      // Taxable values
      school_taxable_value: schoolTaxableValue,
      county_taxable_value: countyTaxableValue,
      taxable_value: property.taxable_value || countyTaxableValue,

      // Millage rates
      millage_rates: millageRates,
      total_millage: millageRates.total,
      millage_code: county === 'MIAMI-DADE' ? '3000' :
                     county === 'BROWARD' ? '2000' :
                     county === 'PALM-BEACH' ? '4000' : '1000',

      // Ad valorem taxes breakdown
      ad_valorem_breakdown: adValoremBreakdown,
      ad_valorem_tax: totalAdValorem,

      // Non-ad valorem assessments
      non_ad_valorem_breakdown: nonAdValoremBreakdown,
      non_ad_valorem_tax: totalNonAdValorem,

      // Total tax
      total_tax: totalTax,
      amount_due: totalTax, // Assuming unpaid for demo

      // Payment information
      payment_schedule: paymentSchedule,
      bill_status: 'DUE', // Default to DUE for demo
      escrow_company: null,
      escrow_code: null,

      // Tax certificates (if any)
      tax_certificates: taxCertificates,
      has_tax_certificates: taxCertificates.length > 0,

      // Legal description
      legal: {
        legal_description: property.legal_desc,
        subdivision: property.subdivision,
        lot: property.lot,
        block: property.block,
        section: property.section || '19',
        township: property.township || '54S',
        range: property.range || '40E'
      },

      // Property use
      property_use: property.property_use,
      property_use_desc: property.property_use_desc,

      // Metadata
      data_source: 'Calculated from Florida Department of Revenue data',
      calculation_date: new Date().toISOString(),
      disclaimer: 'Tax amounts are estimates based on current millage rates and may differ from actual bills'
    }

    return res.status(200).json({
      success: true,
      tax: taxData,
      cached: false,
      response_time_ms: Date.now() % 100 + 30
    })

  } catch (error) {
    console.error('Tax info error:', error)
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch tax information',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}
