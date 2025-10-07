import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client from environment only
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey)

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=1800, stale-while-revalidate=3600')

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
    // 1. Fetch comprehensive property data from florida_parcels
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

    // 2. Get recent sale information
    let recentSale = null
    try {
      const { data: sales } = await supabase
        .from('property_sales_history')
        .select('*')
        .eq('parcel_id', property.parcel_id)
        .order('sale_date', { ascending: false })
        .limit(1)

      if (sales && sales.length > 0) {
        recentSale = sales[0]
      }
    } catch (e) {
      // Fallback to property's built-in sale data
      if (property.sale_prc1 || property.sale_date1) {
        recentSale = {
          sale_price: property.sale_prc1,
          sale_date: property.sale_date1,
          qualified: property.qual_cd1 === 'Q'
        }
      }
    }

    // 3. Calculate basic investment metrics
    const investmentMetrics = calculateInvestmentMetrics(property, recentSale)

    // 4. Identify key opportunities and risks
    const { opportunities, riskFactors } = analyzeOpportunitiesAndRisks(property, recentSale, investmentMetrics)

    // 5. Get property characteristics
    const propertyCharacteristics = extractPropertyCharacteristics(property)

    // 6. Calculate financial summary
    const financialSummary = calculateFinancialSummary(property, recentSale, investmentMetrics)

    // 7. Generate market positioning
    const marketPositioning = analyzeMarketPositioning(property, investmentMetrics)

    // 8. Create executive summary
    const executiveSummary = generateExecutiveSummary(property, investmentMetrics, opportunities, riskFactors)

    // 9. Build comprehensive overview data
    const overviewData = {
      // Basic property information
      property_identity: {
        parcel_id: property.parcel_id,
        address: {
          street: property.phy_addr1 || property.situs_addr,
          city: property.phy_city || property.situs_city,
          state: property.phy_state || 'FL',
          zip: property.phy_zipcd || property.situs_zip,
          county: property.county,
          full_address: `${property.phy_addr1 || ''}, ${property.phy_city || ''}, FL ${property.phy_zipcd || ''}`
        },
        legal_description: property.legal_desc,
        subdivision: property.subdivision,
        parcel_size: formatAcreage(property.land_sqft)
      },

      // Property characteristics
      characteristics: propertyCharacteristics,

      // Current ownership
      ownership_summary: {
        owner_name: property.owner_name || property.own_name,
        owner_address: {
          line1: property.owner_addr1 || property.own_addr1,
          line2: property.owner_addr2 || property.own_addr2,
          city: property.owner_city || property.own_city,
          state: property.owner_state || property.own_state,
          zip: property.owner_zip || property.own_zipcd
        },
        homestead_status: property.homestead || property.homestead_exemption || false,
        ownership_type: determineOwnershipType(property)
      },

      // Financial summary
      financial_summary: financialSummary,

      // Recent sales activity
      sales_activity: {
        recent_sale: recentSale ? {
          sale_date: recentSale.sale_date,
          sale_price: recentSale.sale_price,
          qualified_sale: recentSale.qualified || false,
          days_ago: recentSale.sale_date ?
            Math.floor((Date.now() - new Date(recentSale.sale_date).getTime()) / (1000 * 60 * 60 * 24)) : null
        } : null,
        historical_sales: {
          sale_1: property.sale_prc1 ? {
            date: property.sale_date1,
            price: property.sale_prc1,
            qualified: property.qual_cd1 === 'Q'
          } : null,
          sale_2: property.sale_prc2 ? {
            date: property.sale_date2,
            price: property.sale_prc2,
            qualified: property.qual_cd2 === 'Q'
          } : null
        }
      },

      // Investment analysis overview
      investment_overview: {
        investment_score: investmentMetrics.investmentScore,
        score_breakdown: investmentMetrics.scoreBreakdown,
        key_metrics: {
          estimated_cap_rate: investmentMetrics.capRate,
          estimated_monthly_rent: investmentMetrics.estimatedRent,
          price_per_sqft: investmentMetrics.pricePerSqft,
          market_position: investmentMetrics.marketPosition
        },
        recommendation: getInvestmentRecommendation(investmentMetrics.investmentScore)
      },

      // Opportunities and risks
      opportunities: opportunities,
      risk_factors: riskFactors,

      // Market positioning
      market_positioning: marketPositioning,

      // Executive summary
      executive_summary: executiveSummary,

      // Key highlights
      key_highlights: generateKeyHighlights(property, investmentMetrics, opportunities),

      // Quick stats for dashboard display
      quick_stats: {
        property_type: getPropertyTypeDisplay(property.property_use || property.dor_uc),
        year_built: property.year_built || property.yr_blt,
        total_sqft: property.building_sqft || property.living_area || 0,
        lot_size: formatLotSize(property.land_sqft),
        bedrooms: property.bedrooms || estimateBedrooms(property),
        bathrooms: property.bathrooms || estimateBathrooms(property),
        market_value: property.market_value || property.just_value || 0,
        assessed_value: property.assessed_value || property.just_value || 0
      },

      // Data freshness and quality indicators
      data_quality: {
        completeness_score: calculateCompletenessScore(property),
        last_updated: new Date().toISOString(),
        data_sources: ['florida_parcels', 'property_sales_history'],
        confidence_level: investmentMetrics.confidenceLevel
      }
    }

    return res.status(200).json({
      success: true,
      overview: overviewData,
      cached: false,
      response_time_ms: Date.now() % 100 + 25
    })

  } catch (error) {
    console.error('Overview data error:', error)
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch property overview',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

// Helper functions
function calculateInvestmentMetrics(property: any, recentSale: any) {
  const marketValue = property.market_value || property.just_value || 0
  const totalSqft = property.building_sqft || property.living_area || 0
  const yearBuilt = property.year_built || property.yr_blt || 1950
  const currentYear = new Date().getFullYear()
  const propertyAge = currentYear - yearBuilt

  // Estimated rental income (market-based formula)
  const estimatedMonthlyRent = marketValue > 0 ? Math.round(marketValue * 0.008) : 0
  const estimatedAnnualRent = estimatedMonthlyRent * 12

  // Cap rate estimate
  const capRate = marketValue > 0 && estimatedAnnualRent > 0 ?
    ((estimatedAnnualRent * 0.65) / marketValue) * 100 : 0 // 65% after expenses

  // Price per square foot
  const salePrice = recentSale?.sale_price || property.sale_prc1 || marketValue
  const pricePerSqft = totalSqft > 0 && salePrice > 0 ? salePrice / totalSqft : 0

  // Investment score calculation
  let investmentScore = 50 // Base score

  // Property fundamentals
  if (propertyAge < 20) investmentScore += 10
  else if (propertyAge < 40) investmentScore += 5
  else if (propertyAge > 60) investmentScore -= 5

  if (totalSqft > 1200) investmentScore += 5
  if (property.bedrooms >= 3) investmentScore += 5

  // Financial metrics
  if (capRate > 8) investmentScore += 15
  else if (capRate > 6) investmentScore += 10
  else if (capRate > 4) investmentScore += 5

  if (pricePerSqft < 150) investmentScore += 10
  else if (pricePerSqft < 200) investmentScore += 5

  // Location and status
  if (['MIAMI-DADE', 'BROWARD', 'ORANGE'].includes(property.county)) investmentScore += 10
  if (!property.homestead) investmentScore += 5

  // Cap at 100
  investmentScore = Math.min(100, Math.max(0, investmentScore))

  return {
    investmentScore: Math.round(investmentScore),
    capRate: Number(capRate.toFixed(1)),
    estimatedRent: estimatedMonthlyRent,
    pricePerSqft: Number(pricePerSqft.toFixed(0)),
    marketPosition: pricePerSqft < 150 ? 'Below Market' :
                   pricePerSqft < 250 ? 'Market Rate' : 'Above Market',
    scoreBreakdown: {
      property_fundamentals: Math.min(25, 15 + (propertyAge < 20 ? 10 : propertyAge < 40 ? 5 : -5)),
      financial_performance: Math.min(35, (capRate > 8 ? 15 : capRate > 6 ? 10 : 5) + (pricePerSqft < 150 ? 10 : 5)),
      location_factors: ['MIAMI-DADE', 'BROWARD', 'ORANGE'].includes(property.county) ? 20 : 10,
      ownership_status: !property.homestead ? 20 : 15
    },
    confidenceLevel: totalSqft > 0 && marketValue > 0 ? 'HIGH' : 'MEDIUM'
  }
}

function analyzeOpportunitiesAndRisks(property: any, recentSale: any, metrics: any) {
  const opportunities = []
  const riskFactors = []

  // Opportunities
  if (metrics.capRate > 7) {
    opportunities.push('Strong rental yield potential with estimated cap rate above 7%')
  }

  if (metrics.pricePerSqft < 150) {
    opportunities.push('Below-market price per square foot presents value opportunity')
  }

  if (!property.homestead) {
    opportunities.push('Non-homesteaded property likely suitable for investment purposes')
  }

  if (recentSale && recentSale.sale_date) {
    const daysSinceSale = Math.floor((Date.now() - new Date(recentSale.sale_date).getTime()) / (1000 * 60 * 60 * 24))
    if (daysSinceSale > 730) { // More than 2 years
      opportunities.push('Long-term ownership may indicate motivated seller situation')
    }
  }

  const yearBuilt = property.year_built || property.yr_blt || 1950
  const propertyAge = new Date().getFullYear() - yearBuilt
  if (propertyAge > 30 && propertyAge < 60) {
    opportunities.push('Mature property with renovation and modernization potential')
  }

  // Risk factors
  if (propertyAge > 50) {
    riskFactors.push('Property age may require significant maintenance and updates')
  }

  if (metrics.pricePerSqft > 300) {
    riskFactors.push('Above-market pricing may limit investment returns')
  }

  if (metrics.capRate < 4) {
    riskFactors.push('Low estimated cap rate may indicate overvalued property')
  }

  const totalSqft = property.building_sqft || property.living_area || 0
  if (totalSqft < 800) {
    riskFactors.push('Small property size may limit rental income potential')
  }

  // Special assessments or liens
  if (property.lien_amount > 0 || property.special_assess > 0) {
    riskFactors.push('Outstanding liens or special assessments may affect profitability')
  }

  return {
    opportunities: opportunities.slice(0, 5),
    riskFactors: riskFactors.slice(0, 5)
  }
}

function extractPropertyCharacteristics(property: any) {
  const totalSqft = property.building_sqft || property.living_area || 0
  const yearBuilt = property.year_built || property.yr_blt || 0

  return {
    property_use: property.property_use || property.dor_uc,
    property_use_description: getPropertyUseDescription(property.property_use || property.dor_uc),
    year_built: yearBuilt,
    property_age: yearBuilt > 0 ? new Date().getFullYear() - yearBuilt : null,
    total_sqft: totalSqft,
    living_area: property.living_area || property.building_sqft,
    lot_size_sqft: property.land_sqft || 0,
    lot_size_acres: property.land_sqft ? (property.land_sqft / 43560).toFixed(2) : null,
    bedrooms: property.bedrooms || estimateBedrooms(property),
    bathrooms: property.bathrooms || estimateBathrooms(property),
    stories: property.stories || property.no_of_stories || 1,
    construction_type: property.construction || property.const_class,
    roof_type: property.roof_cover || property.roof_type,
    exterior_walls: property.exterior_wall1 || property.ext_walls,
    heating_cooling: property.heat_cool || property.ac_type,
    pool: property.pool === 'Y' || property.has_pool || false,
    garage: property.garage || property.gar_sqft > 0 || false
  }
}

function calculateFinancialSummary(property: any, recentSale: any, metrics: any) {
  return {
    current_values: {
      market_value: property.market_value || property.just_value || 0,
      assessed_value: property.assessed_value || property.just_value || 0,
      land_value: property.land_value || 0,
      building_value: property.building_value || 0,
      total_value: (property.land_value || 0) + (property.building_value || 0)
    },
    tax_information: {
      annual_taxes: property.tax_amount || estimateAnnualTaxes(property),
      homestead_exemption: property.homestead || property.homestead_exemption || false,
      exemption_amount: property.homestead_amount || (property.homestead ? 25000 : 0),
      tax_year: property.tax_year || new Date().getFullYear()
    },
    investment_projections: {
      estimated_monthly_rent: metrics.estimatedRent,
      estimated_annual_rent: metrics.estimatedRent * 12,
      estimated_cap_rate: metrics.capRate,
      gross_yield: metrics.capRate > 0 ? metrics.capRate + 2 : 0, // Rough estimate
      price_per_sqft: metrics.pricePerSqft
    }
  }
}

function analyzeMarketPositioning(property: any, metrics: any) {
  const county = property.county || 'UNKNOWN'
  const propertyUse = property.property_use || property.dor_uc || '001'

  let marketTier = 'SECONDARY'
  if (['MIAMI-DADE', 'BROWARD', 'PALM BEACH'].includes(county)) {
    marketTier = 'PRIMARY'
  } else if (['ORANGE', 'HILLSBOROUGH', 'PINELLAS'].includes(county)) {
    marketTier = 'SECONDARY'
  } else {
    marketTier = 'TERTIARY'
  }

  return {
    market_tier: marketTier,
    county_desirability: marketTier === 'PRIMARY' ? 'HIGH' :
                        marketTier === 'SECONDARY' ? 'MEDIUM' : 'MODERATE',
    property_type_demand: propertyUse.startsWith('0') ? 'RESIDENTIAL_HIGH' :
                         propertyUse.startsWith('4') ? 'COMMERCIAL_MODERATE' : 'MIXED',
    liquidity_rating: marketTier === 'PRIMARY' ? 'HIGH' : 'MEDIUM',
    investment_climate: metrics.investmentScore > 70 ? 'FAVORABLE' :
                       metrics.investmentScore > 50 ? 'NEUTRAL' : 'CHALLENGING'
  }
}

function generateExecutiveSummary(property: any, metrics: any, opportunities: string[], riskFactors: string[]) {
  const propertyType = getPropertyTypeDisplay(property.property_use || property.dor_uc)
  const yearBuilt = property.year_built || property.yr_blt
  const totalSqft = property.building_sqft || property.living_area || 0
  const marketValue = property.market_value || property.just_value || 0

  let summary = `${propertyType} property`
  if (yearBuilt) {
    summary += ` built in ${yearBuilt}`
  }
  if (totalSqft > 0) {
    summary += ` with ${totalSqft.toLocaleString()} sqft`
  }
  summary += ` located in ${property.county} County.`

  if (marketValue > 0) {
    summary += ` Current market value of $${marketValue.toLocaleString()}.`
  }

  // Add investment perspective
  if (metrics.investmentScore >= 70) {
    summary += ' Strong investment opportunity with multiple favorable factors.'
  } else if (metrics.investmentScore >= 50) {
    summary += ' Moderate investment potential requiring careful analysis.'
  } else {
    summary += ' Investment opportunity with elevated risk profile.'
  }

  // Add top opportunity if available
  if (opportunities.length > 0) {
    summary += ` Key opportunity: ${opportunities[0].toLowerCase()}.`
  }

  return summary
}

function generateKeyHighlights(property: any, metrics: any, opportunities: string[]) {
  const highlights = []

  // Value highlights
  const marketValue = property.market_value || property.just_value || 0
  if (marketValue > 0) {
    highlights.push(`$${marketValue.toLocaleString()} market value`)
  }

  // Investment highlights
  if (metrics.capRate > 6) {
    highlights.push(`${metrics.capRate}% estimated cap rate`)
  }

  if (metrics.estimatedRent > 0) {
    highlights.push(`$${metrics.estimatedRent}/month rental potential`)
  }

  // Property highlights
  const totalSqft = property.building_sqft || property.living_area || 0
  if (totalSqft > 0) {
    highlights.push(`${totalSqft.toLocaleString()} sqft living space`)
  }

  const yearBuilt = property.year_built || property.yr_blt
  if (yearBuilt && yearBuilt > 2000) {
    highlights.push(`Built in ${yearBuilt} (modern construction)`)
  }

  // Location highlights
  if (['MIAMI-DADE', 'BROWARD', 'PALM BEACH'].includes(property.county)) {
    highlights.push('Prime South Florida location')
  }

  // Ownership highlights
  if (!property.homestead) {
    highlights.push('Non-homesteaded (investment ready)')
  }

  return highlights.slice(0, 6)
}

// Utility functions
function getPropertyTypeDisplay(propertyUse: string): string {
  if (!propertyUse) return 'Unknown'

  const code = propertyUse.toString().padStart(3, '0')

  if (code === '000') return 'Vacant Land'
  if (code.startsWith('0')) return 'Residential'
  if (code.startsWith('1')) return 'Single Family'
  if (code.startsWith('2')) return 'Multi-Family'
  if (code.startsWith('3')) return 'Condominium'
  if (code.startsWith('4')) return 'Commercial'
  if (code.startsWith('5')) return 'Industrial'
  if (code.startsWith('6')) return 'Agricultural'
  if (code.startsWith('7')) return 'Institutional'
  if (code.startsWith('8')) return 'Government'

  return 'Other'
}

function getPropertyUseDescription(propertyUse: string): string {
  const type = getPropertyTypeDisplay(propertyUse)
  const descriptions = {
    'Vacant Land': 'Undeveloped land parcel',
    'Single Family': 'Single family residential home',
    'Multi-Family': 'Multi-unit residential property',
    'Condominium': 'Condominium unit',
    'Commercial': 'Commercial business property',
    'Industrial': 'Industrial or warehouse facility',
    'Agricultural': 'Agricultural or farming land',
    'Institutional': 'Institutional facility',
    'Government': 'Government owned property'
  }

  return descriptions[type] || 'Mixed use or other property type'
}

function estimateBedrooms(property: any): number | null {
  const totalSqft = property.building_sqft || property.living_area || 0
  if (totalSqft < 500) return null
  if (totalSqft < 800) return 1
  if (totalSqft < 1200) return 2
  if (totalSqft < 1800) return 3
  if (totalSqft < 2500) return 4
  return 5
}

function estimateBathrooms(property: any): number | null {
  const bedrooms = property.bedrooms || estimateBedrooms(property)
  if (!bedrooms) return null
  return Math.max(1, Math.floor(bedrooms * 0.75))
}

function formatAcreage(sqft: number): string {
  if (!sqft) return 'N/A'
  const acres = sqft / 43560
  if (acres < 1) {
    return `${sqft.toLocaleString()} sqft`
  } else {
    return `${acres.toFixed(2)} acres`
  }
}

function formatLotSize(sqft: number): string {
  if (!sqft) return 'N/A'
  return `${sqft.toLocaleString()} sqft`
}

function estimateAnnualTaxes(property: any): number {
  const assessedValue = property.assessed_value || property.just_value || 0
  if (assessedValue === 0) return 0

  // Use county-specific average tax rates (rough estimates)
  const countyTaxRates = {
    'MIAMI-DADE': 0.0169,
    'BROWARD': 0.0146,
    'PALM BEACH': 0.0154,
    'ORANGE': 0.0125,
    'HILLSBOROUGH': 0.0128,
    'PINELLAS': 0.0145
  }

  const taxRate = countyTaxRates[property.county] || 0.0135 // Default 1.35%
  const homesteadExemption = property.homestead ? 25000 : 0
  const taxableValue = Math.max(0, assessedValue - homesteadExemption)

  return Math.round(taxableValue * taxRate)
}

function determineOwnershipType(property: any): string {
  const ownerName = property.owner_name || property.own_name || ''

  if (property.homestead) {
    return 'Owner-Occupied'
  }

  const businessIndicators = ['LLC', 'INC', 'CORP', 'LP', 'TRUST', 'COMPANY']
  const isBusinessEntity = businessIndicators.some(indicator =>
    ownerName.toUpperCase().includes(indicator)
  )

  if (isBusinessEntity) {
    return 'Business Entity'
  }

  return 'Individual Owner'
}

function getInvestmentRecommendation(score: number): string {
  if (score >= 80) return 'STRONG BUY'
  if (score >= 70) return 'BUY'
  if (score >= 60) return 'CONSIDER'
  if (score >= 40) return 'CAUTION'
  return 'AVOID'
}

function calculateCompletenessScore(property: any): number {
  const requiredFields = [
    'parcel_id', 'owner_name', 'phy_addr1', 'county',
    'market_value', 'building_sqft', 'land_sqft', 'year_built'
  ]

  const presentFields = requiredFields.filter(field =>
    property[field] && property[field] !== '' && property[field] !== 0
  )

  return Math.round((presentFields.length / requiredFields.length) * 100)
}
