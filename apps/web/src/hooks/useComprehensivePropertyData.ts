import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'

export interface ComprehensivePropertyData {
  // Core property data
  bcpaData: any
  floridaParcelsData: any

  // Sales and transaction data
  sdfData: any[]
  salesHistory: any[]
  lastSale: any
  salesTrends: any[]

  // Tax and assessment data
  navData: any[]
  taxCertificates: any[]
  taxDeedData: any[]
  totalNavAssessment: number
  isInCDD: boolean

  // Business entity data
  sunbizData: any[]
  corporateFilings: any[]
  fictitiousNames: any[]

  // Building and development data
  buildingPermits: any[]
  floridaPermits: any[]

  // Legal and foreclosure data
  foreclosureCases: any[]
  taxLienCertificates: any[]

  // Investment analysis
  investmentScore: number
  marketAnalysis: {
    countyMedianValue: number
    cityMedianValue: number
    valuePercentile: number
    pricePerSqft: number
    appreciation: number
    marketTrend: 'up' | 'down' | 'stable'
  }

  // Opportunities and risks
  opportunities: string[]
  riskFactors: string[]

  // Calculations
  calculations: {
    propertyAge: number
    landToValueRatio: number
    taxRate: number
    capRate?: number
    cashFlow?: number
    roi?: number
    paybackPeriod?: number
  }

  // Data quality indicators
  dataQuality: {
    bcpa: boolean
    sdf: boolean
    nav: boolean
    sunbiz: boolean
    permits: boolean
    foreclosure: boolean
    completeness: number
  }

  // Interactive features
  similar_properties: any[]
  neighborhood_stats: any
  growth_projections: any[]
}

export const useComprehensivePropertyData = (
  addressOrParcelId: string,
  city: string = '',
  options: {
    includeSimilarProperties?: boolean
    includeNeighborhoodStats?: boolean
    includeGrowthProjections?: boolean
  } = {}
) => {
  const [data, setData] = useState<ComprehensivePropertyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchComprehensiveData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Determine if input is parcel ID or address
      const isParcelId = /^\d{12,15}$/.test(addressOrParcelId.replace(/[-\s]/g, ''))

      let parcelId = addressOrParcelId
      let primaryPropertyData: any = null

      // Step 1: Get primary property data
      if (isParcelId) {
        // Direct parcel lookup
        const { data: floridaData } = await supabase
          .from('florida_parcels')
          .select('*')
          .eq('parcel_id', parcelId)
          .single()

        primaryPropertyData = floridaData
      } else {
        // Address-based lookup
        const searchAddress = addressOrParcelId.replace(/-/g, ' ').trim()

        const { data: floridaData } = await supabase
          .from('florida_parcels')
          .select('*')
          .ilike('phy_addr1', `%${searchAddress}%`)
          .limit(5)

        if (floridaData && floridaData.length > 0) {
          // Find best match
          const upperAddress = searchAddress.toUpperCase()
          primaryPropertyData = floridaData.find(p =>
            p.phy_addr1?.toUpperCase() === upperAddress ||
            p.phy_addr1?.toUpperCase().includes(upperAddress)
          ) || floridaData[0]

          parcelId = primaryPropertyData.parcel_id
        }
      }

      if (!primaryPropertyData) {
        throw new Error('Property not found')
      }

      // Step 2: Parallel fetch all related data
      const [
        sdfResponse,
        salesHistoryResponse,
        navResponse,
        sunbizResponse,
        permitsResponse,
        foreclosureResponse,
        taxCertificatesResponse,
        taxDeedResponse,
        taxLienResponse,
        fictitiousResponse,
        corporateFilingsResponse
      ] = await Promise.all([
        // Sales data
        supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false }),

        // Additional sales data (SDF)
        supabase
          .from('fl_sdf_sales')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false }),

        // NAV assessments
        supabase
          .from('nav_assessments')
          .select('*')
          .eq('parcel_id', parcelId),

        // Sunbiz corporate data
        fetchSunbizData(primaryPropertyData.owner_name || ''),

        // Building permits
        supabase
          .from('building_permits')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('issue_date', { ascending: false }),

        // Foreclosure cases
        supabase
          .from('foreclosure_cases')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('case_date', { ascending: false }),

        // Tax certificates
        supabase
          .from('tax_certificates')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('certificate_date', { ascending: false }),

        // Tax deed properties
        supabase
          .from('tax_deed_properties')
          .select('*')
          .eq('parcel_number', parcelId)
          .order('auction_date', { ascending: false }),

        // Tax lien certificates
        supabase
          .from('tax_lien_certificates')
          .select('*')
          .eq('parcel_id', parcelId),

        // Fictitious names
        fetchFictitiousNames(primaryPropertyData.owner_name || ''),

        // Corporate filings
        fetchCorporateFilings(primaryPropertyData.owner_name || '')
      ])

      // Step 3: Process and combine all data
      const salesHistory = [...(sdfResponse.data || []), ...(salesHistoryResponse.data || [])]
        .sort((a, b) => new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime())

      const lastSale = salesHistory.find(sale => parseFloat(sale.sale_price) >= 1000) || null

      // Step 4: Calculate market analysis
      const marketAnalysis = await calculateMarketAnalysis(primaryPropertyData, parcelId)

      // Step 5: Calculate investment metrics
      const calculations = calculateInvestmentMetrics(primaryPropertyData, lastSale, navResponse.data || [])

      // Step 6: Generate investment score
      const investmentScore = calculateInvestmentScore(
        primaryPropertyData,
        lastSale,
        marketAnalysis,
        calculations,
        navResponse.data || []
      )

      // Step 7: Identify opportunities and risks
      const { opportunities, riskFactors } = identifyOpportunitiesAndRisks(
        primaryPropertyData,
        lastSale,
        marketAnalysis,
        calculations,
        sunbizResponse,
        foreclosureResponse.data || [],
        taxCertificatesResponse.data || []
      )

      // Step 8: Optional data (similar properties, neighborhood stats, etc.)
      let similarProperties: any[] = []
      let neighborhoodStats: any = null
      let growthProjections: any[] = []

      if (options.includeSimilarProperties) {
        similarProperties = await fetchSimilarProperties(primaryPropertyData)
      }

      if (options.includeNeighborhoodStats) {
        neighborhoodStats = await fetchNeighborhoodStats(primaryPropertyData.phy_city, primaryPropertyData.county)
      }

      if (options.includeGrowthProjections) {
        growthProjections = await fetchGrowthProjections(primaryPropertyData.county, primaryPropertyData.phy_city)
      }

      // Step 9: Calculate data quality
      const dataQuality = calculateDataQuality({
        bcpa: !!primaryPropertyData,
        sdf: salesHistory.length > 0,
        nav: (navResponse.data || []).length > 0,
        sunbiz: sunbizResponse.length > 0,
        permits: (permitsResponse.data || []).length > 0,
        foreclosure: (foreclosureResponse.data || []).length > 0,
        primaryData: primaryPropertyData
      })

      // Step 10: Assemble final data structure
      const comprehensiveData: ComprehensivePropertyData = {
        bcpaData: primaryPropertyData,
        floridaParcelsData: primaryPropertyData,
        sdfData: sdfResponse.data || [],
        salesHistory,
        lastSale,
        salesTrends: await calculateSalesTrends(salesHistory),
        navData: navResponse.data || [],
        taxCertificates: taxCertificatesResponse.data || [],
        taxDeedData: taxDeedResponse.data || [],
        totalNavAssessment: (navResponse.data || []).reduce((sum: number, nav: any) =>
          sum + (parseFloat(nav.total_assessment) || 0), 0),
        isInCDD: (navResponse.data || []).some((nav: any) =>
          nav.authority_name?.toLowerCase().includes('community development')),
        sunbizData: sunbizResponse,
        corporateFilings: corporateFilingsResponse,
        fictitiousNames: fictitiousResponse,
        buildingPermits: permitsResponse.data || [],
        floridaPermits: [], // Will be populated if table exists
        foreclosureCases: foreclosureResponse.data || [],
        taxLienCertificates: taxLienResponse.data || [],
        investmentScore,
        marketAnalysis,
        opportunities,
        riskFactors,
        calculations,
        dataQuality,
        similar_properties: similarProperties,
        neighborhood_stats: neighborhoodStats,
        growth_projections: growthProjections
      }

      setData(comprehensiveData)

    } catch (err) {
      console.error('Error fetching comprehensive property data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch property data')
    } finally {
      setLoading(false)
    }
  }, [addressOrParcelId, city, options])

  useEffect(() => {
    if (addressOrParcelId) {
      fetchComprehensiveData()
    }
  }, [addressOrParcelId, city, fetchComprehensiveData])

  return {
    data,
    loading,
    error,
    refetch: fetchComprehensiveData
  }
}

// Helper functions

async function fetchSunbizData(ownerName: string) {
  if (!ownerName) return []

  try {
    // Check if it's a company
    const isCompany = /\b(LLC|INC|CORP|CORPORATION|LP|LLP|PROPERTIES|INVESTMENTS|HOLDINGS|CAPITAL|PARTNERS|GROUP|TRUST)\b/i.test(ownerName)

    if (isCompany) {
      const { data } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .ilike('corporate_name', `%${ownerName.replace(/[^a-zA-Z0-9\s]/g, '')}%`)
        .limit(10)

      return data || []
    } else {
      // Search for individual as officer
      const { data } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .ilike('officers', `%${ownerName}%`)
        .limit(10)

      return data || []
    }
  } catch (error) {
    console.error('Error fetching Sunbiz data:', error)
    return []
  }
}

async function fetchFictitiousNames(ownerName: string) {
  if (!ownerName) return []

  try {
    const { data } = await supabase
      .from('sunbiz_fictitious')
      .select('*')
      .ilike('owner_name', `%${ownerName}%`)
      .limit(5)

    return data || []
  } catch (error) {
    return []
  }
}

async function fetchCorporateFilings(ownerName: string) {
  if (!ownerName) return []

  try {
    const { data } = await supabase
      .from('sunbiz_corporate_filings')
      .select('*')
      .ilike('entity_name', `%${ownerName}%`)
      .limit(5)

    return data || []
  } catch (error) {
    return []
  }
}

async function calculateMarketAnalysis(propertyData: any, parcelId: string) {
  try {
    // Get county and city medians
    const [countyStats, cityStats, similarSales] = await Promise.all([
      supabase
        .from('florida_parcels')
        .select('just_value')
        .eq('county', propertyData.county)
        .not('just_value', 'is', null)
        .limit(1000),

      supabase
        .from('florida_parcels')
        .select('just_value')
        .eq('county', propertyData.county)
        .eq('phy_city', propertyData.phy_city)
        .not('just_value', 'is', null)
        .limit(1000),

      supabase
        .from('property_sales_history')
        .select('sale_price, sale_date')
        .eq('parcel_id', parcelId)
        .order('sale_date', { ascending: false })
        .limit(5)
    ])

    const countyValues = (countyStats.data || []).map(p => parseFloat(p.just_value)).filter(v => v > 0)
    const cityValues = (cityStats.data || []).map(p => parseFloat(p.just_value)).filter(v => v > 0)

    const countyMedianValue = countyValues.length > 0 ?
      countyValues.sort((a, b) => a - b)[Math.floor(countyValues.length / 2)] : 0

    const cityMedianValue = cityValues.length > 0 ?
      cityValues.sort((a, b) => a - b)[Math.floor(cityValues.length / 2)] : 0

    const propertyValue = parseFloat(propertyData.just_value || '0')
    const valuePercentile = countyValues.length > 0 ?
      (countyValues.filter(v => v < propertyValue).length / countyValues.length) * 100 : 50

    const pricePerSqft = propertyData.total_living_area && propertyValue > 0 ?
      propertyValue / propertyData.total_living_area : 0

    // Calculate appreciation from recent sales
    const sales = (similarSales.data || []).filter(s => parseFloat(s.sale_price) > 1000)
    let appreciation = 0
    let marketTrend: 'up' | 'down' | 'stable' = 'stable'

    if (sales.length >= 2) {
      const oldest = sales[sales.length - 1]
      const newest = sales[0]
      const yearsApart = (new Date(newest.sale_date).getTime() - new Date(oldest.sale_date).getTime()) / (365 * 24 * 60 * 60 * 1000)

      if (yearsApart > 0) {
        appreciation = ((parseFloat(newest.sale_price) - parseFloat(oldest.sale_price)) / parseFloat(oldest.sale_price)) * 100 / yearsApart
        marketTrend = appreciation > 5 ? 'up' : appreciation < -2 ? 'down' : 'stable'
      }
    }

    return {
      countyMedianValue,
      cityMedianValue,
      valuePercentile,
      pricePerSqft,
      appreciation,
      marketTrend
    }
  } catch (error) {
    console.error('Error calculating market analysis:', error)
    return {
      countyMedianValue: 0,
      cityMedianValue: 0,
      valuePercentile: 50,
      pricePerSqft: 0,
      appreciation: 0,
      marketTrend: 'stable' as const
    }
  }
}

function calculateInvestmentMetrics(propertyData: any, lastSale: any, navData: any[]) {
  const currentYear = new Date().getFullYear()
  const yearBuilt = propertyData.year_built || currentYear
  const propertyAge = currentYear - yearBuilt

  const justValue = parseFloat(propertyData.just_value || '0')
  const landValue = parseFloat(propertyData.land_value || '0')
  const landToValueRatio = justValue > 0 ? landValue / justValue : 0

  const taxableValue = parseFloat(propertyData.taxable_value || '0')
  const totalTaxes = navData.reduce((sum, nav) => sum + parseFloat(nav.total_assessment || '0'), 0)
  const estimatedTaxes = (taxableValue * 0.015) + totalTaxes // Estimate 1.5% + NAV
  const taxRate = taxableValue > 0 ? (estimatedTaxes / taxableValue) * 100 : 0

  // Investment calculations
  let capRate: number | undefined
  let cashFlow: number | undefined
  let roi: number | undefined
  let paybackPeriod: number | undefined

  if (lastSale && propertyData.total_living_area) {
    const purchasePrice = parseFloat(lastSale.sale_price)
    const estimatedRent = (justValue * 0.008) // Estimate 0.8% of value as monthly rent
    const annualRent = estimatedRent * 12
    const annualExpenses = estimatedTaxes + (annualRent * 0.3) // 30% of rent for expenses

    if (purchasePrice > 0) {
      capRate = ((annualRent - annualExpenses) / purchasePrice) * 100
      cashFlow = annualRent - annualExpenses

      const downPayment = purchasePrice * 0.25 // 25% down
      roi = cashFlow > 0 ? (cashFlow / downPayment) * 100 : undefined
      paybackPeriod = cashFlow > 0 ? downPayment / cashFlow : undefined
    }
  }

  return {
    propertyAge,
    landToValueRatio,
    taxRate,
    capRate,
    cashFlow,
    roi,
    paybackPeriod
  }
}

function calculateInvestmentScore(
  propertyData: any,
  lastSale: any,
  marketAnalysis: any,
  calculations: any,
  navData: any[]
): number {
  let score = 50 // Base score

  // Value-based scoring
  if (marketAnalysis.valuePercentile < 25) score += 15 // Below market
  else if (marketAnalysis.valuePercentile > 75) score -= 10 // Above market

  // Age-based scoring
  if (calculations.propertyAge < 10) score += 10
  else if (calculations.propertyAge > 50) score -= 5

  // Market trend scoring
  if (marketAnalysis.marketTrend === 'up') score += 10
  else if (marketAnalysis.marketTrend === 'down') score -= 10

  // Cap rate scoring
  if (calculations.capRate) {
    if (calculations.capRate > 8) score += 15
    else if (calculations.capRate > 6) score += 10
    else if (calculations.capRate < 3) score -= 10
  }

  // CDD penalty
  const isInCDD = navData.some(nav =>
    nav.authority_name?.toLowerCase().includes('community development'))
  if (isInCDD) score -= 10

  // Homestead penalty (less attractive for investment)
  if (propertyData.homestead === 'Y') score -= 5

  // Ensure score is 0-100
  return Math.max(0, Math.min(100, score))
}

function identifyOpportunitiesAndRisks(
  propertyData: any,
  lastSale: any,
  marketAnalysis: any,
  calculations: any,
  sunbizData: any[],
  foreclosureData: any[],
  taxCertificates: any[]
) {
  const opportunities: string[] = []
  const riskFactors: string[] = []

  // Opportunities
  if (marketAnalysis.valuePercentile < 25) {
    opportunities.push('🎯 Below market value - potential undervalued property')
  }

  if (calculations.capRate && calculations.capRate > 8) {
    opportunities.push('💰 High cap rate - excellent cash flow potential')
  }

  if (marketAnalysis.marketTrend === 'up' && marketAnalysis.appreciation > 5) {
    opportunities.push('📈 Strong appreciation trend - capital gains potential')
  }

  if (sunbizData.length > 0) {
    opportunities.push('🏢 Business owner - potential portfolio expansion opportunity')
  }

  if (foreclosureData.length > 0) {
    opportunities.push('🏛️ Foreclosure history - may indicate motivated sellers nearby')
  }

  if (calculations.propertyAge < 5) {
    opportunities.push('🏗️ New construction - minimal repair needs')
  }

  // Risk factors
  if (marketAnalysis.valuePercentile > 85) {
    riskFactors.push('⚠️ Premium pricing - limited upside potential')
  }

  if (calculations.propertyAge > 60) {
    riskFactors.push('⚠️ Older property - potential maintenance and code issues')
  }

  if (taxCertificates.length > 0) {
    riskFactors.push('🚨 Tax certificate history - tax payment issues')
  }

  if (calculations.taxRate > 3) {
    riskFactors.push('💸 High tax burden - impacts cash flow')
  }

  if (marketAnalysis.marketTrend === 'down') {
    riskFactors.push('📉 Declining market - potential value loss')
  }

  if (!lastSale || (lastSale && new Date().getTime() - new Date(lastSale.sale_date).getTime() > 7 * 365 * 24 * 60 * 60 * 1000)) {
    riskFactors.push('📊 No recent sales data - difficult to establish current market value')
  }

  return { opportunities, riskFactors }
}

async function calculateSalesTrends(salesHistory: any[]) {
  if (salesHistory.length < 2) return []

  const trends = []
  const validSales = salesHistory.filter(sale => parseFloat(sale.sale_price) > 1000)

  for (let i = 1; i < validSales.length; i++) {
    const current = validSales[i-1]
    const previous = validSales[i]

    const currentPrice = parseFloat(current.sale_price)
    const previousPrice = parseFloat(previous.sale_price)
    const percentChange = ((currentPrice - previousPrice) / previousPrice) * 100

    trends.push({
      from_date: previous.sale_date,
      to_date: current.sale_date,
      from_price: previousPrice,
      to_price: currentPrice,
      percent_change: percentChange,
      trend: percentChange > 5 ? 'up' : percentChange < -5 ? 'down' : 'stable'
    })
  }

  return trends
}

async function fetchSimilarProperties(propertyData: any) {
  try {
    const { data } = await supabase
      .from('florida_parcels')
      .select('*')
      .eq('county', propertyData.county)
      .eq('phy_city', propertyData.phy_city)
      .eq('dor_uc', propertyData.dor_uc)
      .gte('just_value', parseFloat(propertyData.just_value || '0') * 0.8)
      .lte('just_value', parseFloat(propertyData.just_value || '0') * 1.2)
      .neq('parcel_id', propertyData.parcel_id)
      .limit(10)

    return data || []
  } catch (error) {
    return []
  }
}

async function fetchNeighborhoodStats(city: string, county: string) {
  try {
    const { data } = await supabase
      .rpc('get_neighborhood_stats', {
        p_city: city,
        p_county: county
      })

    return data?.[0] || null
  } catch (error) {
    return null
  }
}

async function fetchGrowthProjections(county: string, city: string) {
  // This would typically call an external API or calculated view
  // For now, return mock projections
  return [
    { year: 2024, projected_growth: 3.2 },
    { year: 2025, projected_growth: 2.8 },
    { year: 2026, projected_growth: 2.5 },
    { year: 2027, projected_growth: 2.2 },
    { year: 2028, projected_growth: 2.0 }
  ]
}

function calculateDataQuality(sources: any) {
  let score = 0
  let maxScore = 0

  // Core data (40% weight)
  if (sources.bcpa) score += 40
  maxScore += 40

  // Sales data (20% weight)
  if (sources.sdf) score += 20
  maxScore += 20

  // Assessment data (15% weight)
  if (sources.nav) score += 15
  maxScore += 15

  // Business data (10% weight)
  if (sources.sunbiz) score += 10
  maxScore += 10

  // Building data (10% weight)
  if (sources.permits) score += 10
  maxScore += 10

  // Legal data (5% weight)
  if (sources.foreclosure) score += 5
  maxScore += 5

  const completeness = maxScore > 0 ? (score / maxScore) * 100 : 0

  return {
    bcpa: sources.bcpa,
    sdf: sources.sdf,
    nav: sources.nav,
    sunbiz: sources.sunbiz,
    permits: sources.permits,
    foreclosure: sources.foreclosure,
    completeness: Math.round(completeness)
  }
}