/**
 * React hook for PySpark-powered property data
 * Provides comprehensive big data processing for all property tabs
 */

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

// PySpark API Configuration
const PYSPARK_API_BASE = 'http://localhost:8002'

// Types for PySpark processed data
export interface PySparkPropertyData {
  overview: {
    property_details: {
      address: string
      parcel_id: string
      use_code: string
      year_built: number
      living_area: number
      land_area: number
      bedrooms: number
      bathrooms: number
      stories: number
      construction: string
      roof_type: string
      pool: boolean
      garage: number
    }
    owner_info: {
      name: string
      mailing_address: string
      city_state_zip: string
    }
    assessment: {
      just_value: number
      assessed_value: number
      taxable_value: number
      land_value: number
      building_value: number
      year: number
    }
  }
  analysis: {
    metrics: {
      price_per_sqft: number
      estimated_monthly_rent: number
      cap_rate: number
      cash_on_cash_return: number
      noi: number
      annual_cash_flow: number
    }
    investment_score: number
    value_percentile: number
    comp_analysis: {
      avg_comp_value: number
      avg_comp_sqft: number
      avg_similarity: number
    }
  }
  sales: {
    sales_history: Array<{
      sale_date: string
      sale_price: number
      seller_name: string
      buyer_name: string
      sale_type: string
      instrument_number: string
    }>
    statistics: {
      total_sales: number
      avg_price: number
      max_price: number
      min_price: number
      price_stddev: number
    }
    appreciation_rate?: number
  }
  tax: {
    assessments: Array<{
      year: number
      just_value: number
      assessed_value: number
      taxable_value: number
      land_value: number
      building_value: number
    }>
    tax_history: Array<{
      year: number
      value_change_pct: number
    }>
    exemptions: Array<any>
    tax_deed_info?: Array<{
      auction_date: string
      minimum_bid: number
      certificate_number: string
      certificate_year: number
      tax_amount: number
    }>
  }
  comparables: {
    comparables: Array<{
      parcel_id: string
      property_address: string
      owner_name: string
      living_area_sqft: number
      land_sqft: number
      bedrooms: number
      bathrooms: number
      year_built: number
      just_value: number
      similarity_score: number
    }>
    statistics: {
      avg_value: number
      avg_sqft: number
      avg_price_per_sqft: number
      median_value: number
    }
    type_breakdown: Array<{
      property_use_code: string
      count: number
      avg_value: number
    }>
  }
  market: {
    monthly_trends: Array<{
      year_month: string
      num_sales: number
      avg_price: number
      median_price: number
      price_stddev: number
      min_price: number
      max_price: number
      price_change_pct: number
    }>
    property_type_analysis: Array<{
      property_use_code: string
      num_sales: number
      avg_price: number
      avg_price_per_sqft: number
    }>
    quarterly_trends: Array<{
      year: number
      quarter: number
      num_sales: number
      avg_price: number
      total_volume: number
    }>
  }
  portfolio: {
    properties: Array<{
      parcel_id: string
      property_address: string
      just_value: number
      land_sqft: number
      living_area_sqft: number
      year_built: number
      property_use_code: string
      value_category: string
    }>
    statistics: {
      total_properties: number
      total_portfolio_value: number
      avg_property_value: number
      total_land_area: number
      total_living_area: number
    }
    value_distribution: Array<{
      value_category: string
      count: number
      total_value: number
    }>
  }
  documents: {
    available_documents: Array<{
      type: string
      source: string
      status: string
      record_count?: number
      years?: number
    }>
  }
  map: {
    property_location: {
      latitude: number
      longitude: number
      address: string
      parcel_boundaries: any
    }
    nearby_properties: Array<{
      parcel_id: string
      property_address: string
      just_value: number
      latitude: number
      longitude: number
      similarity_score: number
    }>
  }
}

export interface PySparkMetadata {
  property_id: string
  county: string
  processed_at: string
  processor: string
  tabs_processed?: string[]
}

export interface PySparkResponse {
  success: boolean
  data: PySparkPropertyData
  metadata: PySparkMetadata
  processing_time: number
}

export interface InvestmentScoreResponse {
  success: boolean
  property_id: string
  county: string
  investment_score: number
  metrics: any
  comp_analysis: any
  value_percentile: number
  recommendation: string
  timestamp: string
}

export interface ComparablesResponse {
  success: boolean
  property_id: string
  county: string
  comparables_count: number
  comparables: Array<any>
  timestamp: string
}

export interface MarketTrendsResponse {
  success: boolean
  county: string
  trends: any
  timestamp: string
}

// Custom hook for PySpark property data
export function usePySparkPropertyData(propertyId: string, county: string, tabs?: string[]) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Build API URL
  const apiUrl = tabs
    ? `${PYSPARK_API_BASE}/property/process`
    : `${PYSPARK_API_BASE}/property/${propertyId}/${county}`

  // Query key for React Query
  const queryKey = ['pyspark-property', propertyId, county, tabs]

  // Fetch function
  const fetchPropertyData = async (): Promise<PySparkResponse> => {
    setIsLoading(true)
    setError(null)

    try {
      let response: Response

      if (tabs) {
        // POST request for specific tabs
        response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            property_id: propertyId,
            county: county,
            tabs: tabs
          })
        })
      } else {
        // GET request for all data
        response = await fetch(apiUrl)
      }

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`)
      }

      const data = await response.json()

      if (!data.success) {
        throw new Error(data.error || 'PySpark processing failed')
      }

      return data

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      throw err
    } finally {
      setIsLoading(false)
    }
  }

  // Use React Query for caching and background updates
  const query = useQuery({
    queryKey,
    queryFn: fetchPropertyData,
    enabled: Boolean(propertyId && county),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  })

  return {
    data: query.data?.data,
    metadata: query.data?.metadata,
    processingTime: query.data?.processing_time,
    isLoading: query.isLoading || isLoading,
    error: error || (query.error as Error)?.message,
    isError: query.isError || Boolean(error),
    refetch: query.refetch,
    isFetching: query.isFetching
  }
}

// Hook for investment score only
export function usePySparkInvestmentScore(propertyId: string, county: string) {
  const apiUrl = `${PYSPARK_API_BASE}/property/investment-score/${propertyId}/${county}`
  const queryKey = ['pyspark-investment-score', propertyId, county]

  const fetchScore = async (): Promise<InvestmentScoreResponse> => {
    const response = await fetch(apiUrl)

    if (!response.ok) {
      throw new Error(`Failed to fetch investment score: ${response.statusText}`)
    }

    return response.json()
  }

  const query = useQuery({
    queryKey,
    queryFn: fetchScore,
    enabled: Boolean(propertyId && county),
    staleTime: 10 * 60 * 1000, // 10 minutes
    cacheTime: 60 * 60 * 1000, // 1 hour
  })

  return {
    score: query.data?.investment_score,
    metrics: query.data?.metrics,
    recommendation: query.data?.recommendation,
    valuePercentile: query.data?.value_percentile,
    compAnalysis: query.data?.comp_analysis,
    isLoading: query.isLoading,
    error: query.error as Error,
    refetch: query.refetch
  }
}

// Hook for comparables
export function usePySparkComparables(propertyId: string, county: string, limit: number = 20) {
  const apiUrl = `${PYSPARK_API_BASE}/property/comparables/${propertyId}/${county}?limit=${limit}`
  const queryKey = ['pyspark-comparables', propertyId, county, limit]

  const fetchComparables = async (): Promise<ComparablesResponse> => {
    const response = await fetch(apiUrl)

    if (!response.ok) {
      throw new Error(`Failed to fetch comparables: ${response.statusText}`)
    }

    return response.json()
  }

  const query = useQuery({
    queryKey,
    queryFn: fetchComparables,
    enabled: Boolean(propertyId && county),
    staleTime: 15 * 60 * 1000, // 15 minutes
    cacheTime: 60 * 60 * 1000, // 1 hour
  })

  return {
    comparables: query.data?.comparables || [],
    count: query.data?.comparables_count || 0,
    isLoading: query.isLoading,
    error: query.error as Error,
    refetch: query.refetch
  }
}

// Hook for market trends
export function usePySparkMarketTrends(county: string) {
  const apiUrl = `${PYSPARK_API_BASE}/market/trends/${county}`
  const queryKey = ['pyspark-market-trends', county]

  const fetchTrends = async (): Promise<MarketTrendsResponse> => {
    const response = await fetch(apiUrl)

    if (!response.ok) {
      throw new Error(`Failed to fetch market trends: ${response.statusText}`)
    }

    return response.json()
  }

  const query = useQuery({
    queryKey,
    queryFn: fetchTrends,
    enabled: Boolean(county),
    staleTime: 30 * 60 * 1000, // 30 minutes
    cacheTime: 2 * 60 * 60 * 1000, // 2 hours
  })

  return {
    trends: query.data?.trends,
    monthlyTrends: query.data?.trends?.monthly_stats || [],
    propertyTypeAnalysis: query.data?.trends?.type_stats || [],
    quarterlyTrends: query.data?.trends?.quarterly_stats || [],
    isLoading: query.isLoading,
    error: query.error as Error,
    refetch: query.refetch
  }
}

// Hook for API health check
export function usePySparkHealth() {
  const apiUrl = `${PYSPARK_API_BASE}/health`
  const queryKey = ['pyspark-health']

  const fetchHealth = async () => {
    const response = await fetch(apiUrl)

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`)
    }

    return response.json()
  }

  const query = useQuery({
    queryKey,
    queryFn: fetchHealth,
    refetchInterval: 30000, // Check every 30 seconds
    staleTime: 10000, // 10 seconds
    retry: 1
  })

  return {
    isHealthy: query.data?.status === 'healthy',
    sparkStatus: query.data?.spark,
    lastCheck: query.data?.timestamp,
    isLoading: query.isLoading,
    error: query.error as Error
  }
}

// Utility function to format PySpark data for display
export function formatPySparkCurrency(value: number | null | undefined): string {
  if (!value || isNaN(value)) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

export function formatPySparkPercentage(value: number | null | undefined): string {
  if (!value || isNaN(value)) return 'N/A'
  return `${value.toFixed(2)}%`
}

export function formatPySparkNumber(value: number | null | undefined): string {
  if (!value || isNaN(value)) return 'N/A'
  return new Intl.NumberFormat('en-US').format(value)
}

// Investment score color helper
export function getInvestmentScoreColor(score: number): string {
  if (score >= 80) return '#16a34a' // green-600
  if (score >= 60) return '#3b82f6' // blue-500
  if (score >= 40) return '#f59e0b' // amber-500
  if (score >= 20) return '#ea580c' // orange-600
  return '#dc2626' // red-600
}

// Investment score badge text
export function getInvestmentScoreBadge(score: number): string {
  if (score >= 80) return 'EXCELLENT'
  if (score >= 60) return 'GOOD'
  if (score >= 40) return 'FAIR'
  if (score >= 20) return 'POOR'
  return 'AVOID'
}