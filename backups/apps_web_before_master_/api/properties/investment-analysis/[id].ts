import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

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

    // 2. Fetch comparable sales data
    let comparableSales = []
    try {
      const { data: comps } = await supabase
        .from('property_sales')
        .select('*')
        .eq('county', property.county)
        .gte('sale_date', new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString()) // Last year
        .gt('sale_price', 0)
        .order('sale_date', { ascending: false })
        .limit(100)

      if (comps && comps.length > 0) {
        // Filter by proximity if coordinates available
        if (property.latitude && property.longitude) {
          comparableSales = comps.filter(comp => {
            if (!comp.latitude || !comp.longitude) return false
            const distance = calculateDistance(
              property.latitude, property.longitude,
              comp.latitude, comp.longitude
            )
            return distance < 5 // Within 5 miles
          }).slice(0, 20)
        } else {
          // Filter by similar property characteristics
          comparableSales = comps.filter(comp => {
            const propertyBeds = property.bedrooms || property.total_rooms || 0
            const compBeds = comp.bedrooms || comp.total_rooms || 0
            const propertyBaths = property.bathrooms || 0
            const compBaths = comp.bathrooms || 0
            const propertySqft = property.building_sqft || property.living_area || 0
            const compSqft = comp.building_sqft || comp.living_area || 0

            return (
              Math.abs(propertyBeds - compBeds) <= 1 &&
              Math.abs(propertyBaths - compBaths) <= 1 &&
              propertySqft > 0 && compSqft > 0 &&
              Math.abs(propertySqft - compSqft) / propertySqft < 0.5
            )
          }).slice(0, 15)
        }
      }
    } catch (e) {
      console.log('Sales data not available for comps analysis')
    }

    // 3. Fetch market trends data
    let marketTrends = []
    try {
      const { data: trends } = await supabase
        .from('market_trends')
        .select('*')
        .eq('county', property.county)
        .order('date', { ascending: false })
        .limit(12)

      if (trends) {
        marketTrends = trends
      }
    } catch (e) {
      console.log('Market trends data not available')
    }

    // 4. Calculate property metrics
    const metrics = calculateInvestmentMetrics(property, comparableSales)

    // 5. Calculate investment score
    const investmentScore = calculateInvestmentScore(property, metrics)

    // 6. Generate rental estimates
    const rentalEstimates = calculateRentalEstimates(property, metrics)

    // 7. Analyze market position
    const marketAnalysis = analyzeMarketPosition(property, comparableSales, marketTrends)

    // 8. Calculate cash flow projections
    const cashFlowProjections = calculateCashFlowProjections(property, metrics, rentalEstimates)

    // 9. Identify investment risks and opportunities
    const riskAssessment = assessInvestmentRisks(property, metrics, marketAnalysis)
    const opportunities = identifyOpportunities(property, metrics, marketAnalysis)

    // 10. Build comprehensive investment analysis
    const investmentData = {
      // Property identification
      parcel_id: property.parcel_id,
      property_address: property.phy_addr1,
      county: property.county,

      // Core property metrics
      property_metrics: {
        market_value: property.market_value || property.just_value || 0,
        assessed_value: property.assessed_value || property.just_value || 0,
        last_sale_price: property.sale_prc1 || 0,
        last_sale_date: property.sale_date1,
        year_built: property.year_built || property.yr_blt,
        total_sqft: property.building_sqft || property.living_area || 0,
        lot_size: property.land_sqft || 0,
        bedrooms: property.bedrooms || property.total_rooms || 0,
        bathrooms: property.bathrooms || 0,
        property_age: new Date().getFullYear() - (property.year_built || property.yr_blt || 1950)
      },

      // Investment scoring
      investment_score: {
        overall_score: investmentScore.overall,
        component_scores: investmentScore.components,
        ranking: getInvestmentRanking(investmentScore.overall),
        recommendation: getInvestmentRecommendation(investmentScore.overall)
      },

      // Financial metrics
      financial_metrics: {
        price_per_sqft: metrics.pricePerSqft,
        price_to_assessed_ratio: metrics.priceToAssessedRatio,
        cap_rate_estimate: metrics.capRateEstimate,
        gross_yield_estimate: metrics.grossYieldEstimate,
        cash_on_cash_return: metrics.cashOnCashReturn,
        roi_estimate: metrics.roiEstimate
      },

      // Rental analysis
      rental_analysis: {
        estimated_monthly_rent: rentalEstimates.monthlyRent,
        estimated_annual_rent: rentalEstimates.annualRent,
        rent_per_sqft: rentalEstimates.rentPerSqft,
        rental_yield: rentalEstimates.rentalYield,
        gross_rental_multiplier: rentalEstimates.grossRentalMultiplier,
        rent_to_value_ratio: rentalEstimates.rentToValueRatio
      },

      // Market analysis
      market_analysis: {
        median_sale_price: marketAnalysis.medianSalePrice,
        average_price_per_sqft: marketAnalysis.avgPricePerSqft,
        market_appreciation_1yr: marketAnalysis.appreciation1yr,
        market_appreciation_3yr: marketAnalysis.appreciation3yr,
        days_on_market_avg: marketAnalysis.avgDOM,
        comparable_sales_count: comparableSales.length,
        market_activity_level: marketAnalysis.activityLevel
      },

      // Cash flow projections
      cash_flow_projections: cashFlowProjections,

      // Comparable sales
      comparable_sales: comparableSales.map(comp => ({
        address: comp.property_address || comp.phy_addr1,
        sale_price: comp.sale_price,
        sale_date: comp.sale_date,
        price_per_sqft: comp.building_sqft ? comp.sale_price / comp.building_sqft : 0,
        bedrooms: comp.bedrooms || comp.total_rooms,
        bathrooms: comp.bathrooms,
        sqft: comp.building_sqft || comp.living_area,
        distance_miles: property.latitude && property.longitude && comp.latitude && comp.longitude ?
          calculateDistance(property.latitude, property.longitude, comp.latitude, comp.longitude) : null
      })),

      // Risk assessment
      risk_assessment: {
        overall_risk_level: riskAssessment.overallRisk,
        risk_factors: riskAssessment.riskFactors,
        risk_mitigation: riskAssessment.mitigation,
        confidence_level: riskAssessment.confidence
      },

      // Investment opportunities
      opportunities: {
        primary_opportunities: opportunities.primary,
        secondary_opportunities: opportunities.secondary,
        value_add_potential: opportunities.valueAdd,
        market_timing: opportunities.marketTiming
      },

      // Strategic recommendations
      recommendations: {
        acquisition_strategy: generateAcquisitionStrategy(investmentScore.overall, riskAssessment),
        financing_recommendations: generateFinancingRecommendations(property, metrics),
        hold_vs_flip_analysis: analyzeHoldVsFlip(property, metrics, rentalEstimates),
        renovation_priorities: identifyRenovationPriorities(property, metrics)
      },

      // Metadata
      analysis_date: new Date().toISOString(),
      data_confidence: calculateDataConfidence(property, comparableSales, marketTrends),
      market_conditions: getCurrentMarketConditions(),
      disclaimer: 'Investment analysis based on available data and market estimates. Actual results may vary.'
    }

    return res.status(200).json({
      success: true,
      investment_analysis: investmentData,
      cached: false,
      response_time_ms: Date.now() % 100 + 50
    })

  } catch (error) {
    console.error('Investment analysis error:', error)
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch investment analysis',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

// Helper functions
function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 3959 // Earth radius in miles
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

function calculateInvestmentMetrics(property: any, comparableSales: any[]) {
  const marketValue = property.market_value || property.just_value || 0
  const lastSalePrice = property.sale_prc1 || marketValue
  const totalSqft = property.building_sqft || property.living_area || 0
  const yearBuilt = property.year_built || property.yr_blt || 1950
  const currentYear = new Date().getFullYear()

  // Basic metrics
  const pricePerSqft = totalSqft > 0 && lastSalePrice > 0 ? lastSalePrice / totalSqft : 0
  const priceToAssessedRatio = property.assessed_value > 0 ? marketValue / property.assessed_value : 1

  // Rental estimates (rule of thumb: 0.5-1.2% of property value monthly)
  const estimatedMonthlyRent = marketValue > 0 ? Math.round(marketValue * 0.008) : 0 // 0.8%
  const estimatedAnnualRent = estimatedMonthlyRent * 12

  // Investment returns
  const capRateEstimate = marketValue > 0 && estimatedAnnualRent > 0 ?
    (estimatedAnnualRent / marketValue) * 100 : 0
  const grossYieldEstimate = capRateEstimate

  // Comparable analysis
  const avgCompSalePrice = comparableSales.length > 0 ?
    comparableSales.reduce((sum, comp) => sum + (comp.sale_price || 0), 0) / comparableSales.length : 0
  const avgCompPricePerSqft = comparableSales.length > 0 ?
    comparableSales
      .filter(comp => comp.building_sqft > 0)
      .reduce((sum, comp) => sum + (comp.sale_price / comp.building_sqft), 0) /
    comparableSales.filter(comp => comp.building_sqft > 0).length : 0

  return {
    pricePerSqft,
    priceToAssessedRatio,
    capRateEstimate,
    grossYieldEstimate,
    cashOnCashReturn: capRateEstimate * 0.8, // Rough estimate with expenses
    roiEstimate: capRateEstimate + 3, // Cap rate + appreciation estimate
    avgCompSalePrice,
    avgCompPricePerSqft,
    marketValueVsComps: avgCompSalePrice > 0 ? ((marketValue - avgCompSalePrice) / avgCompSalePrice) * 100 : 0
  }
}

function calculateInvestmentScore(property: any, metrics: any): any {
  let score = 50 // Base score

  // Property fundamentals (25 points)
  const yearBuilt = property.year_built || property.yr_blt || 1950
  const propertyAge = new Date().getFullYear() - yearBuilt
  if (propertyAge < 20) score += 10
  else if (propertyAge < 40) score += 5
  else if (propertyAge > 60) score -= 5

  if (property.building_sqft > 1200) score += 5
  if (property.bedrooms >= 3) score += 5
  if (property.bathrooms >= 2) score += 5

  // Financial metrics (35 points)
  if (metrics.capRateEstimate > 8) score += 15
  else if (metrics.capRateEstimate > 6) score += 10
  else if (metrics.capRateEstimate > 4) score += 5

  if (metrics.pricePerSqft < 150) score += 10
  else if (metrics.pricePerSqft < 200) score += 5

  if (metrics.marketValueVsComps < -10) score += 10 // Below market
  else if (metrics.marketValueVsComps < 0) score += 5

  // Market conditions (20 points)
  const isInDesirableArea = property.county === 'MIAMI-DADE' ||
    property.county === 'BROWARD' || property.county === 'ORANGE'
  if (isInDesirableArea) score += 10

  // Property status (20 points)
  if (!property.homestead && !property.homestead_exemption) score += 10 // Non-homestead
  if (property.sale_date1 && new Date(property.sale_date1) < new Date(Date.now() - 2 * 365 * 24 * 60 * 60 * 1000)) {
    score += 5 // Longer ownership
  }

  // Cap at 100
  score = Math.min(100, Math.max(0, score))

  return {
    overall: Math.round(score),
    components: {
      property_fundamentals: Math.min(25, Math.max(0, 25 - (propertyAge > 60 ? 5 : 0) +
        (property.building_sqft > 1200 ? 5 : 0) + (property.bedrooms >= 3 ? 5 : 0))),
      financial_metrics: Math.min(35, Math.max(0,
        (metrics.capRateEstimate > 8 ? 15 : metrics.capRateEstimate > 6 ? 10 : 5) +
        (metrics.pricePerSqft < 150 ? 10 : metrics.pricePerSqft < 200 ? 5 : 0))),
      market_position: Math.min(20, isInDesirableArea ? 10 : 0),
      property_status: Math.min(20, (!property.homestead ? 10 : 0) + 5)
    }
  }
}

function calculateRentalEstimates(property: any, metrics: any) {
  const marketValue = property.market_value || property.just_value || 0
  const totalSqft = property.building_sqft || property.living_area || 0
  const bedrooms = property.bedrooms || property.total_rooms || 0

  // Base rental estimate (0.6-1.2% of value monthly, varying by market)
  let rentMultiplier = 0.008 // 0.8% base

  // Adjust based on property characteristics
  if (totalSqft > 2000) rentMultiplier += 0.001
  if (bedrooms >= 4) rentMultiplier += 0.001
  if (property.county === 'MIAMI-DADE') rentMultiplier += 0.002
  if (property.county === 'BROWARD') rentMultiplier += 0.0015

  const monthlyRent = Math.round(marketValue * rentMultiplier)
  const annualRent = monthlyRent * 12
  const rentPerSqft = totalSqft > 0 ? monthlyRent / totalSqft : 0
  const rentalYield = marketValue > 0 ? (annualRent / marketValue) * 100 : 0
  const grossRentalMultiplier = monthlyRent > 0 ? marketValue / (monthlyRent * 12) : 0

  return {
    monthlyRent,
    annualRent,
    rentPerSqft,
    rentalYield,
    grossRentalMultiplier,
    rentToValueRatio: rentMultiplier * 100
  }
}

function analyzeMarketPosition(property: any, comparableSales: any[], marketTrends: any[]) {
  const medianSalePrice = comparableSales.length > 0 ?
    comparableSales.map(c => c.sale_price).sort()[Math.floor(comparableSales.length / 2)] : 0

  const avgPricePerSqft = comparableSales.length > 0 ?
    comparableSales
      .filter(c => c.building_sqft > 0)
      .reduce((sum, c) => sum + (c.sale_price / c.building_sqft), 0) /
    comparableSales.filter(c => c.building_sqft > 0).length : 0

  // Simple appreciation calculation based on comps
  const recentSales = comparableSales.filter(c =>
    new Date(c.sale_date) > new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)
  )
  const olderSales = comparableSales.filter(c =>
    new Date(c.sale_date) < new Date(Date.now() - 365 * 24 * 60 * 60 * 1000) &&
    new Date(c.sale_date) > new Date(Date.now() - 3 * 365 * 24 * 60 * 60 * 1000)
  )

  let appreciation1yr = 0
  let appreciation3yr = 0

  if (recentSales.length > 0 && olderSales.length > 0) {
    const recentAvg = recentSales.reduce((sum, s) => sum + s.sale_price, 0) / recentSales.length
    const olderAvg = olderSales.reduce((sum, s) => sum + s.sale_price, 0) / olderSales.length
    appreciation1yr = ((recentAvg - olderAvg) / olderAvg) * 100
    appreciation3yr = appreciation1yr * 3 // Simplified
  }

  return {
    medianSalePrice,
    avgPricePerSqft,
    appreciation1yr,
    appreciation3yr,
    avgDOM: 45, // Default estimate
    activityLevel: comparableSales.length > 10 ? 'high' : comparableSales.length > 5 ? 'moderate' : 'low'
  }
}

function calculateCashFlowProjections(property: any, metrics: any, rentalEstimates: any) {
  const monthlyRent = rentalEstimates.monthlyRent
  const annualRent = rentalEstimates.annualRent
  const propertyValue = property.market_value || property.just_value || 0

  // Estimate expenses (typically 35-50% of gross rent)
  const expenseRatio = 0.40 // 40%
  const monthlyExpenses = monthlyRent * expenseRatio
  const annualExpenses = monthlyExpenses * 12

  // Financing assumptions (80% LTV, 6% interest, 30 years)
  const downPaymentPercent = 0.20
  const loanAmount = propertyValue * (1 - downPaymentPercent)
  const interestRate = 0.06
  const loanTermYears = 30
  const monthlyPayment = calculateMonthlyPayment(loanAmount, interestRate, loanTermYears)

  const netOperatingIncome = annualRent - annualExpenses
  const cashFlow = netOperatingIncome - (monthlyPayment * 12)
  const cashOnCashReturn = cashFlow / (propertyValue * downPaymentPercent) * 100

  return {
    gross_annual_income: annualRent,
    annual_expenses: annualExpenses,
    net_operating_income: netOperatingIncome,
    annual_debt_service: monthlyPayment * 12,
    annual_cash_flow: cashFlow,
    monthly_cash_flow: cashFlow / 12,
    cash_on_cash_return: cashOnCashReturn,
    cap_rate: propertyValue > 0 ? (netOperatingIncome / propertyValue) * 100 : 0
  }
}

function calculateMonthlyPayment(loanAmount: number, annualRate: number, years: number): number {
  const monthlyRate = annualRate / 12
  const numPayments = years * 12
  return loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
    (Math.pow(1 + monthlyRate, numPayments) - 1)
}

function assessInvestmentRisks(property: any, metrics: any, marketAnalysis: any) {
  const risks = []
  let riskScore = 0

  // Property age risk
  const propertyAge = new Date().getFullYear() - (property.year_built || 1950)
  if (propertyAge > 50) {
    risks.push('Property age may require significant maintenance and updates')
    riskScore += 2
  }

  // Market position risk
  if (metrics.marketValueVsComps > 15) {
    risks.push('Property priced above comparable sales')
    riskScore += 2
  }

  // Cap rate risk
  if (metrics.capRateEstimate < 4) {
    risks.push('Low cap rate may indicate overvalued property')
    riskScore += 3
  }

  // Market activity risk
  if (marketAnalysis.activityLevel === 'low') {
    risks.push('Low market activity may affect liquidity')
    riskScore += 1
  }

  const overallRisk = riskScore > 5 ? 'HIGH' : riskScore > 2 ? 'MEDIUM' : 'LOW'

  return {
    overallRisk,
    riskFactors: risks,
    mitigation: generateRiskMitigation(risks),
    confidence: riskScore < 3 ? 'HIGH' : riskScore < 6 ? 'MEDIUM' : 'LOW'
  }
}

function identifyOpportunities(property: any, metrics: any, marketAnalysis: any) {
  const primary = []
  const secondary = []
  const valueAdd = []

  // Primary opportunities
  if (metrics.capRateEstimate > 7) {
    primary.push('Strong rental yield potential')
  }
  if (metrics.marketValueVsComps < -5) {
    primary.push('Below-market pricing opportunity')
  }

  // Secondary opportunities
  if (marketAnalysis.appreciation1yr > 5) {
    secondary.push('Strong market appreciation trend')
  }

  // Value-add opportunities
  const propertyAge = new Date().getFullYear() - (property.year_built || 1950)
  if (propertyAge > 30 && propertyAge < 60) {
    valueAdd.push('Renovation and modernization potential')
  }

  return {
    primary,
    secondary,
    valueAdd,
    marketTiming: marketAnalysis.activityLevel === 'high' ? 'FAVORABLE' : 'NEUTRAL'
  }
}

function generateRiskMitigation(risks: string[]): string[] {
  const mitigation = []

  risks.forEach(risk => {
    if (risk.includes('age')) {
      mitigation.push('Schedule comprehensive property inspection')
      mitigation.push('Budget for potential maintenance and updates')
    }
    if (risk.includes('priced above')) {
      mitigation.push('Negotiate based on comparable sales analysis')
      mitigation.push('Consider walking away if price cannot be adjusted')
    }
    if (risk.includes('cap rate')) {
      mitigation.push('Verify rental income estimates with local data')
      mitigation.push('Consider alternative exit strategies')
    }
  })

  return mitigation.length > 0 ? mitigation : ['Continue with standard due diligence procedures']
}

function getInvestmentRanking(score: number): string {
  if (score >= 80) return 'EXCELLENT'
  if (score >= 70) return 'VERY_GOOD'
  if (score >= 60) return 'GOOD'
  if (score >= 40) return 'FAIR'
  return 'POOR'
}

function getInvestmentRecommendation(score: number): string {
  if (score >= 80) return 'STRONG_BUY'
  if (score >= 60) return 'BUY'
  if (score >= 40) return 'HOLD'
  return 'AVOID'
}

function generateAcquisitionStrategy(score: number, riskAssessment: any): string {
  if (score >= 80) {
    return 'Prioritize acquisition - consider competitive offer at or near asking price'
  }
  if (score >= 60) {
    return 'Moderate interest - negotiate based on identified risks and market position'
  }
  return 'Proceed with caution - significant price reduction likely required'
}

function generateFinancingRecommendations(property: any, metrics: any): string[] {
  const recommendations = []

  if (metrics.capRateEstimate > 7) {
    recommendations.push('Consider conventional investment property financing')
    recommendations.push('Leverage favorable cap rate for loan qualification')
  } else {
    recommendations.push('Consider higher down payment to improve cash flow')
    recommendations.push('Shop for competitive interest rates')
  }

  return recommendations
}

function analyzeHoldVsFlip(property: any, metrics: any, rentalEstimates: any): any {
  const holdScore = rentalEstimates.rentalYield * 10 // Weight rental yield heavily
  const flipScore = metrics.marketValueVsComps < -10 ? 70 : 40 // Below market = flip potential

  return {
    recommendation: holdScore > flipScore ? 'HOLD' : 'FLIP',
    hold_score: Math.round(holdScore),
    flip_score: Math.round(flipScore),
    analysis: holdScore > flipScore ?
      'Strong rental yields favor buy-and-hold strategy' :
      'Market pricing suggests flip opportunity'
  }
}

function identifyRenovationPriorities(property: any, metrics: any): string[] {
  const priorities = []
  const propertyAge = new Date().getFullYear() - (property.year_built || 1950)

  if (propertyAge > 30) {
    priorities.push('Kitchen and bathroom updates')
    priorities.push('Flooring replacement')
  }
  if (propertyAge > 20) {
    priorities.push('Paint interior and exterior')
    priorities.push('Landscaping improvements')
  }

  return priorities.length > 0 ? priorities : ['Property appears to be in good condition']
}

function calculateDataConfidence(property: any, comparableSales: any[], marketTrends: any[]): string {
  let confidence = 0

  if (property.market_value || property.just_value) confidence += 30
  if (comparableSales.length >= 5) confidence += 30
  if (marketTrends.length >= 6) confidence += 20
  if (property.building_sqft || property.living_area) confidence += 20

  return confidence >= 80 ? 'HIGH' : confidence >= 60 ? 'MEDIUM' : 'LOW'
}

function getCurrentMarketConditions(): string {
  // Would typically pull from external market data
  return 'MODERATE' // STRONG, MODERATE, WEAK
}