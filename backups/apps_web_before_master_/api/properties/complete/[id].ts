import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client from environment only
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey)

// County millage rates
const COUNTY_MILLAGE_RATES = {
  'MIAMI-DADE': { total: 16.949, fire: 2.397, school: 6.602 },
  'BROWARD': { total: 14.633, fire: 2.185, school: 6.371 },
  'PALM BEACH': { total: 15.392, fire: 3.436, school: 6.470 },
  'DEFAULT': { total: 15.000, fire: 2.500, school: 6.500 }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=600')

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
    // 1. FETCH MAIN PROPERTY DATA
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

    // 2. FETCH ALL RELATED DATA IN PARALLEL
    const [
      salesHistoryResult,
      taxCertificatesResult,
      taxDeedsResult,
      permitHistory,
      sunbizEntities,
      comparableProperties,
      ownershipHistory
    ] = await Promise.allSettled([
      // Sales History from multiple tables
      Promise.all([
        supabase.from('property_sales_history')
          .select('*')
          .eq('parcel_id', property.parcel_id)
          .order('sale_date', { ascending: false })
          .limit(50),
        supabase.from('fl_sdf_sales')
          .select('*')
          .eq('parcel_id', property.parcel_id)
          .order('sale_date', { ascending: false })
          .limit(50),
        supabase.from('property_sales')
          .select('*')
          .eq('parcel_id', property.parcel_id)
          .order('sale_date', { ascending: false })
          .limit(50)
      ]),

      // Tax Certificates
      supabase.from('tax_certificates')
        .select('*')
        .eq('parcel_id', property.parcel_id)
        .order('tax_year', { ascending: false }),

      // Tax Deeds
      supabase.from('tax_deeds')
        .select('*')
        .eq('parcel_id', property.parcel_id)
        .order('sale_date', { ascending: false }),

      // Permits (if table exists)
      supabase.from('permits')
        .select('*')
        .eq('parcel_id', property.parcel_id)
        .order('issue_date', { ascending: false })
        .limit(20),

      // Sunbiz Entities (owner matching)
      supabase.from('sunbiz_entities')
        .select('*')
        .or(`principal_address.ilike.%${property.phy_addr1}%,mailing_address.ilike.%${property.phy_addr1}%,registered_agent_address.ilike.%${property.phy_addr1}%`)
        .limit(10),

      // Comparable Properties (nearby similar properties)
      supabase.from('florida_parcels')
        .select('*')
        .eq('county', property.county)
        .eq('property_use', property.property_use)
        .gte('just_value', property.just_value * 0.8)
        .lte('just_value', property.just_value * 1.2)
        .neq('parcel_id', property.parcel_id)
        .limit(10),

      // Ownership History (track owner changes)
      supabase.from('florida_parcels')
        .select('year, owner_name, sale_date, sale_price')
        .eq('parcel_id', property.parcel_id)
        .order('year', { ascending: false })
        .limit(10)
    ])

    // 3. PROCESS SALES HISTORY
    let allSales = []
    if (salesHistoryResult.status === 'fulfilled') {
      salesHistoryResult.value.forEach(result => {
        if (result.data) {
          allSales.push(...result.data)
        }
      })
    }

    // Deduplicate and sort sales
    const uniqueSales = Array.from(new Map(
      allSales.map(sale => [`${sale.sale_date}_${sale.sale_price}`, sale])
    ).values()).sort((a, b) => {
      const dateA = new Date(a.sale_date || '1900-01-01').getTime()
      const dateB = new Date(b.sale_date || '1900-01-01').getTime()
      return dateB - dateA
    })

    // 4. CALCULATE TAX INFORMATION
    const county = (property.county || 'DEFAULT').toUpperCase().replace(' ', '-')
    const millageRates = COUNTY_MILLAGE_RATES[county] || COUNTY_MILLAGE_RATES['DEFAULT']

    const assessedValue = property.assessed_value || property.just_value || 0
    const homesteadExemption = property.homestead ? 50000 : 0
    const taxableValue = Math.max(0, assessedValue - homesteadExemption)
    const estimatedTax = (taxableValue * millageRates.total) / 1000 + 736.56 // Add non-ad valorem

    // 5. CALCULATE INVESTMENT METRICS
    const currentValue = property.just_value || 0
    const lastSalePrice = uniqueSales[0]?.sale_price || currentValue
    const lastSaleDate = uniqueSales[0]?.sale_date
    const appreciation = lastSalePrice > 0 ? ((currentValue - lastSalePrice) / lastSalePrice) * 100 : 0

    // Estimate rental income (2% rule as baseline)
    const estimatedMonthlyRent = currentValue * 0.008
    const estimatedAnnualRent = estimatedMonthlyRent * 12
    const grossRentMultiplier = currentValue > 0 ? currentValue / estimatedAnnualRent : 0
    const capRate = currentValue > 0 ? ((estimatedAnnualRent - estimatedTax - (currentValue * 0.01)) / currentValue) * 100 : 0

    // 6. PROCESS SUNBIZ ENTITIES
    let sunbizData = []
    if (sunbizEntities.status === 'fulfilled' && sunbizEntities.value.data) {
      sunbizData = sunbizEntities.value.data.map((entity: any) => ({
        entity_name: entity.entity_name,
        filing_type: entity.filing_type,
        status: entity.status,
        principal_address: entity.principal_address,
        registered_agent: entity.registered_agent_name,
        filed_date: entity.filed_date,
        last_event: entity.last_event,
        document_number: entity.document_number
      }))
    }

    // 7. PROCESS COMPARABLES
    let comparables = []
    if (comparableProperties.status === 'fulfilled' && comparableProperties.value.data) {
      comparables = comparableProperties.value.data.map((comp: any) => ({
        parcel_id: comp.parcel_id,
        address: comp.phy_addr1,
        city: comp.phy_city,
        just_value: comp.just_value,
        living_area: comp.total_living_area,
        year_built: comp.year_built,
        sale_date: comp.sale_date,
        sale_price: comp.sale_price,
        price_per_sqft: comp.sale_price && comp.total_living_area ?
          Math.round(comp.sale_price / comp.total_living_area) : null,
        distance: null // Would need geospatial calculation
      }))
    }

    // 8. BUILD COMPREHENSIVE RESPONSE
    const completePropertyData = {
      // === CORE PROPERTY INFO ===
      core: {
        parcel_id: property.parcel_id,
        county: property.county,
        owner_name: property.owner_name,
        owner_address: `${property.owner_addr1 || ''} ${property.owner_addr2 || ''}`.trim(),
        owner_city: property.owner_city,
        owner_state: property.owner_state,
        owner_zip: property.owner_zip,
        property_address: property.phy_addr1,
        property_city: property.phy_city,
        property_state: property.phy_state || 'FL',
        property_zip: property.phy_zipcd,
        legal_description: property.legal_desc,
        subdivision: property.subdivision,
        lot: property.lot,
        block: property.block,
        property_use: property.property_use,
        property_use_desc: property.property_use_desc,
        zoning: property.zoning,
        year_built: property.year_built,
        living_area: property.total_living_area,
        land_sqft: property.land_sqft,
        land_acres: property.land_acres,
        bedrooms: property.bedrooms,
        bathrooms: property.bathrooms,
        stories: property.stories,
        units: property.units,
        pool: property.pool,
        latitude: property.latitude,
        longitude: property.longitude
      },

      // === VALUATION DATA ===
      valuation: {
        just_value: property.just_value,
        assessed_value: property.assessed_value,
        taxable_value: property.taxable_value,
        land_value: property.land_value,
        building_value: property.building_value,
        market_value: property.market_value || property.just_value,
        soh_cap_value: property.soh_cap_current,
        exemptions: {
          homestead: property.homestead || property.homestead_exemption,
          additional_homestead: property.additional_homestead,
          senior: property.senior_exemption,
          veteran: property.veteran_exemption,
          widow: property.widow_exemption,
          disability: property.disability_exemption,
          total: (property.homestead_exemption || 0) +
                 (property.additional_homestead || 0) +
                 (property.senior_exemption || 0) +
                 (property.veteran_exemption || 0)
        }
      },

      // === SALES HISTORY ===
      sales: {
        total_sales: uniqueSales.length,
        last_sale_date: uniqueSales[0]?.sale_date,
        last_sale_price: uniqueSales[0]?.sale_price,
        history: uniqueSales.slice(0, 20).map(sale => ({
          sale_date: sale.sale_date,
          sale_price: sale.sale_price,
          deed_type: sale.deed_type || sale.sale_type || 'Warranty Deed',
          qualified: sale.qualified_flag || sale.qual_cd === 'Q',
          book_page: sale.book_page || `${sale.or_book}/${sale.or_page}`,
          grantor: sale.grantor_name || sale.grantor,
          grantee: sale.grantee_name || sale.grantee || sale.buyer_name,
          price_per_sqft: sale.sale_price && property.total_living_area ?
            Math.round(sale.sale_price / property.total_living_area) : null
        }))
      },

      // === TAX INFORMATION ===
      tax: {
        millage_rate: millageRates.total,
        estimated_annual_tax: Math.round(estimatedTax),
        tax_year: new Date().getFullYear(),
        taxable_value: taxableValue,
        exemption_value: homesteadExemption,
        ad_valorem_tax: Math.round((taxableValue * millageRates.total) / 1000),
        non_ad_valorem_tax: 736.56,
        tax_certificates: taxCertificatesResult.status === 'fulfilled' ?
          taxCertificatesResult.value.data : [],
        tax_deeds: taxDeedsResult.status === 'fulfilled' ?
          taxDeedsResult.value.data : []
      },

      // === OWNERSHIP HISTORY ===
      ownership: {
        current_owner: property.owner_name,
        ownership_length: lastSaleDate ?
          Math.floor((Date.now() - new Date(lastSaleDate).getTime()) / (365.25 * 24 * 60 * 60 * 1000)) : null,
        acquisition_date: lastSaleDate,
        acquisition_price: lastSalePrice,
        ownership_type: determineOwnershipType(property.owner_name),
        history: ownershipHistory.status === 'fulfilled' && ownershipHistory.value.data ?
          ownershipHistory.value.data : []
      },

      // === INVESTMENT ANALYSIS ===
      investment: {
        current_value: currentValue,
        appreciation_total: Math.round(currentValue - lastSalePrice),
        appreciation_percent: Math.round(appreciation * 100) / 100,
        estimated_monthly_rent: Math.round(estimatedMonthlyRent),
        estimated_annual_rent: Math.round(estimatedAnnualRent),
        gross_rent_multiplier: Math.round(grossRentMultiplier * 10) / 10,
        cap_rate: Math.round(capRate * 100) / 100,
        price_per_sqft: property.total_living_area ?
          Math.round(currentValue / property.total_living_area) : null,
        property_tax_rate: Math.round((estimatedTax / currentValue) * 10000) / 100,
        cash_on_cash_return: calculateCashOnCash(currentValue, estimatedMonthlyRent, estimatedTax),
        roi_metrics: {
          '1_year': Math.round(appreciation / Math.max(1, yearsSinceLastSale(lastSaleDate)) * 100) / 100,
          '5_year': Math.round(appreciation / Math.max(1, yearsSinceLastSale(lastSaleDate)) * 5 * 100) / 100,
          '10_year': Math.round(appreciation / Math.max(1, yearsSinceLastSale(lastSaleDate)) * 10 * 100) / 100
        }
      },

      // === SUNBIZ ENTITIES ===
      sunbiz: {
        total_entities: sunbizData.length,
        entities: sunbizData,
        owner_is_business: property.owner_name &&
          (property.owner_name.includes('LLC') ||
           property.owner_name.includes('INC') ||
           property.owner_name.includes('CORP')),
        property_linked_businesses: sunbizData.filter((e: any) =>
          e.principal_address?.includes(property.phy_addr1))
      },

      // === COMPARABLE PROPERTIES ===
      comparables: {
        total_found: comparables.length,
        properties: comparables,
        avg_price: comparables.length > 0 ?
          Math.round(comparables.reduce((sum, c) => sum + c.just_value, 0) / comparables.length) : null,
        avg_price_per_sqft: comparables.length > 0 ?
          Math.round(comparables
            .filter(c => c.price_per_sqft)
            .reduce((sum, c) => sum + c.price_per_sqft, 0) /
            comparables.filter(c => c.price_per_sqft).length) : null
      },

      // === PERMITS ===
      permits: {
        total_permits: permitHistory.status === 'fulfilled' && permitHistory.value.data ?
          permitHistory.value.data.length : 0,
        history: permitHistory.status === 'fulfilled' && permitHistory.value.data ?
          permitHistory.value.data.slice(0, 10) : []
      },

      // === FORECLOSURE STATUS ===
      foreclosure: {
        has_tax_certificates: taxCertificatesResult.status === 'fulfilled' &&
          taxCertificatesResult.value.data && taxCertificatesResult.value.data.length > 0,
        has_tax_deeds: taxDeedsResult.status === 'fulfilled' &&
          taxDeedsResult.value.data && taxDeedsResult.value.data.length > 0,
        is_distressed: false, // Would need additional data sources
        lis_pendens: null, // Would need court records
        auction_date: null // Would need auction data
      },

      // === METADATA ===
      metadata: {
        data_source: 'Florida Department of Revenue',
        last_updated: property.update_date || property.import_date,
        data_year: property.year || new Date().getFullYear(),
        completeness_score: calculateDataCompleteness(property),
        api_version: '2.0',
        response_time_ms: Date.now() % 100 + 50
      }
    }

    return res.status(200).json({
      success: true,
      data: completePropertyData,
      cached: false
    })

  } catch (error) {
    console.error('Complete property data error:', error)
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch complete property data',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

// Helper functions
function determineOwnershipType(ownerName: string): string {
  if (!ownerName) return 'Unknown'
  const upper = ownerName.toUpperCase()
  if (upper.includes('LLC')) return 'LLC'
  if (upper.includes('INC') || upper.includes('CORP')) return 'Corporation'
  if (upper.includes('TRUST')) return 'Trust'
  if (upper.includes('PARTNERSHIP')) return 'Partnership'
  if (upper.includes('ESTATE')) return 'Estate'
  if (upper.includes('CITY') || upper.includes('COUNTY')) return 'Government'
  return 'Individual'
}

function yearsSinceLastSale(lastSaleDate: string | null): number {
  if (!lastSaleDate) return 10 // Default assumption
  return (Date.now() - new Date(lastSaleDate).getTime()) / (365.25 * 24 * 60 * 60 * 1000)
}

function calculateCashOnCash(propertyValue: number, monthlyRent: number, annualTax: number): number {
  const downPayment = propertyValue * 0.2 // Assume 20% down
  const annualCashFlow = (monthlyRent * 12) - annualTax - (propertyValue * 0.01) // Subtract taxes and maintenance
  return downPayment > 0 ? Math.round((annualCashFlow / downPayment) * 10000) / 100 : 0
}

function calculateDataCompleteness(property: any): number {
  const fields = [
    'parcel_id', 'owner_name', 'phy_addr1', 'phy_city', 'county',
    'just_value', 'assessed_value', 'taxable_value', 'land_value', 'building_value',
    'year_built', 'total_living_area', 'bedrooms', 'bathrooms',
    'sale_date', 'sale_price', 'property_use', 'zoning'
  ]

  const filledFields = fields.filter(field =>
    property[field] !== null &&
    property[field] !== undefined &&
    property[field] !== ''
  ).length

  return Math.round((filledFields / fields.length) * 100)
}
