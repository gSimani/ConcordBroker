/**
 * Complete property data hook with all integrations
 * Connects to FastAPI backend for live data, calculations, and graphs
 */

import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

// Use localhost API by default for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002'

// Configure axios defaults for localhost
axios.defaults.baseURL = API_BASE_URL
axios.defaults.headers.common['Content-Type'] = 'application/json'

export interface CompletePropertyData {
  property: any
  salesHistory: any[]
  metrics: {
    priceToAssessedRatio?: number
    pricePerSqft?: number
    landToBuildingRatio?: number
    effectiveTaxRate?: number
    homesteadSavings?: number
    propertyAge?: number
    depreciationFactor?: number
    estimatedMonthlyRent?: number
    grossRentalYield?: number
    capRate?: number
    avgHoldingPeriodDays?: number
    salesFrequency?: number
    priceVsComps?: number
    pricePercentile?: number
  }
  sunbizEntities: any[]
  charts: {
    priceHistory?: any
    marketComparison?: any
    roiProjection?: any
    portfolioDistribution?: any
  }
  taxDeeds: any[]
  foreclosures: any[]
  liens: any[]
  permits: any[]
  investmentScore: {
    score: number
    rating: string
    factors: string[]
  }
  marketStats: any
  portfolio?: any
  distressedProperties?: any[]
  opportunities?: any[]
  loading: boolean
  error: string | null
}

export const useCompletePropertyData = (parcelId: string) => {
  const [data, setData] = useState<CompletePropertyData>({
    property: null,
    salesHistory: [],
    metrics: {},
    sunbizEntities: [],
    charts: {},
    taxDeeds: [],
    foreclosures: [],
    liens: [],
    permits: [],
    investmentScore: { score: 0, rating: '', factors: [] },
    marketStats: {},
    loading: true,
    error: null
  })

  const fetchCompleteData = useCallback(async () => {
    if (!parcelId) {
      setData(prev => ({ ...prev, loading: false, error: 'No parcel ID provided' }))
      return
    }

    try {
      setData(prev => ({ ...prev, loading: true, error: null }))

      // Fetch main property data with all relationships
      const propertyResponse = await axios.get(`${API_BASE_URL}/api/property/${parcelId}`)
      const propertyData = propertyResponse.data

      // Fetch additional data in parallel
      const [
        investmentScoreRes,
        marketStatsRes,
        upcomingTaxDeedsRes,
        distressedRes,
        opportunitiesRes,
        roiChartRes
      ] = await Promise.all([
        // Investment score
        axios.post(`${API_BASE_URL}/api/investment/score`, { parcel_id: parcelId }).catch(() => null),

        // Market statistics
        propertyData.property?.county ?
          axios.get(`${API_BASE_URL}/api/market-statistics/${propertyData.property.county}`).catch(() => null) :
          Promise.resolve(null),

        // Upcoming tax deeds in same county
        propertyData.property?.county ?
          axios.get(`${API_BASE_URL}/api/tax-deeds/upcoming?county=${propertyData.property.county}&days_ahead=30`).catch(() => null) :
          Promise.resolve(null),

        // Distressed properties nearby
        propertyData.property?.county ?
          axios.get(`${API_BASE_URL}/api/distressed-properties?county=${propertyData.property.county}`).catch(() => null) :
          Promise.resolve(null),

        // Investment opportunities
        axios.get(`${API_BASE_URL}/api/investment-opportunities?max_price=500000`).catch(() => null),

        // ROI projection chart (if sale price available)
        propertyData.property?.sale_price ?
          axios.post(`${API_BASE_URL}/api/charts/roi-projection?purchase_price=${propertyData.property.sale_price}&rental_income=${propertyData.property.sale_price * 0.008}&expenses=${propertyData.property.sale_price * 0.003}`).catch(() => null) :
          Promise.resolve(null)
      ])

      // If owner exists, fetch portfolio analysis
      let portfolioData = null
      if (propertyData.property?.owner_name) {
        try {
          const portfolioRes = await axios.get(`${API_BASE_URL}/api/portfolio/${encodeURIComponent(propertyData.property.owner_name)}`)
          portfolioData = portfolioRes.data

          // Get portfolio distribution chart
          const portfolioChartRes = await axios.get(`${API_BASE_URL}/api/charts/portfolio-distribution/${encodeURIComponent(propertyData.property.owner_name)}`)
          if (portfolioChartRes.data) {
            propertyData.charts = {
              ...propertyData.charts,
              portfolioDistribution: portfolioChartRes.data
            }
          }
        } catch (err) {
          console.log('Portfolio data not available')
        }
      }

      // Add ROI chart to charts collection
      if (roiChartRes?.data) {
        propertyData.charts = {
          ...propertyData.charts,
          roiProjection: roiChartRes.data
        }
      }

      setData({
        property: propertyData.property,
        salesHistory: propertyData.sales_history || [],
        metrics: propertyData.metrics || {},
        sunbizEntities: propertyData.sunbiz_entities || [],
        charts: propertyData.charts || {},
        taxDeeds: upcomingTaxDeedsRes?.data || [],
        foreclosures: [],
        liens: [],
        permits: [],
        investmentScore: investmentScoreRes?.data || { score: 0, rating: '', factors: [] },
        marketStats: marketStatsRes?.data || {},
        portfolio: portfolioData,
        distressedProperties: distressedRes?.data?.slice(0, 5) || [],
        opportunities: opportunitiesRes?.data?.slice(0, 5) || [],
        loading: false,
        error: null
      })

    } catch (error: any) {
      console.error('Error fetching complete property data:', error)
      setData(prev => ({
        ...prev,
        loading: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch property data'
      }))
    }
  }, [parcelId])

  useEffect(() => {
    fetchCompleteData()
  }, [parcelId, fetchCompleteData])

  return data
}

// Hook for searching properties
export const usePropertySearch = () => {
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (query: string, filters?: any) => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/property/search`, {
        query,
        filters
      })

      setResults(response.data.results || [])
    } catch (err: any) {
      setError(err.message)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  return { search, results, loading, error }
}

// Hook for dashboard data
export const useDashboardData = () => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard`)
      setData(response.data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboard()

    // Refresh every 5 minutes
    const interval = setInterval(fetchDashboard, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [fetchDashboard])

  return { data, loading, error, refresh: fetchDashboard }
}

// Hook for ROI calculations
export const useROICalculator = () => {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const calculate = useCallback(async (params: {
    purchase_price: number
    current_value: number
    rental_income?: number
    expenses?: number
    holding_period_years?: number
  }) => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/calculate/roi`, params)
      setResult(response.data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  return { calculate, result, loading, error }
}

// Hook for affordability calculations
export const useAffordabilityCalculator = () => {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const calculate = useCallback(async (params: {
    income: number
    down_payment: number
    interest_rate?: number
    loan_term_years?: number
  }) => {
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/calculate/affordability`, params)
      setResult(response.data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  return { calculate, result, loading, error }
}

// Hook for market trends
export const useMarketTrends = (county: string, propertyType?: string) => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTrends = async () => {
      if (!county) return

      setLoading(true)
      setError(null)

      try {
        const params = new URLSearchParams({
          county,
          ...(propertyType && { property_type: propertyType }),
          time_period_days: '365'
        })

        const response = await axios.get(`${API_BASE_URL}/api/market-trends?${params}`)
        setData(response.data)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchTrends()
  }, [county, propertyType])

  return { data, loading, error }
}

// Hook for tax deed timeline
export const useTaxDeedTimeline = (county?: string) => {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchTimeline = async () => {
      setLoading(true)
      setError(null)

      try {
        const params = county ? `?county=${county}` : ''
        const response = await axios.get(`${API_BASE_URL}/api/charts/tax-deed-timeline${params}`)
        setData(response.data)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchTimeline()
  }, [county])

  return { data, loading, error }
}