/**
 * Complete property data hook for all tabs
 * Connects to Vercel API endpoints for comprehensive property information
 */

import { useState, useEffect, useCallback } from 'react'

// Extended interface for complete property data
export interface CompletePropertyData {
  // Overview data
  overview: any

  // Core property information
  coreInfo: any

  // Tax information
  taxInfo: any

  // Sales history
  salesHistory: any

  // Ownership information
  ownershipInfo: any

  // Investment analysis
  investmentAnalysis: any

  // Sunbiz data
  sunbizData: any

  // Loading states for each section
  loading: {
    overview: boolean
    coreInfo: boolean
    taxInfo: boolean
    salesHistory: boolean
    ownershipInfo: boolean
    investmentAnalysis: boolean
    sunbizData: boolean
  }

  // Error states
  errors: {
    overview: string | null
    coreInfo: string | null
    taxInfo: string | null
    salesHistory: string | null
    ownershipInfo: string | null
    investmentAnalysis: string | null
    sunbizData: string | null
  }

  // Overall loading and error states
  isLoading: boolean
  hasError: boolean

  // Data quality indicators
  dataQuality: {
    completeness: number
    confidence: string
    lastUpdated: string
  }
}

export const useCompletePropertyData = (propertyId: string) => {
  const [data, setData] = useState<CompletePropertyData>({
    overview: null,
    coreInfo: null,
    taxInfo: null,
    salesHistory: null,
    ownershipInfo: null,
    investmentAnalysis: null,
    sunbizData: null,
    loading: {
      overview: false,
      coreInfo: false,
      taxInfo: false,
      salesHistory: false,
      ownershipInfo: false,
      investmentAnalysis: false,
      sunbizData: false
    },
    errors: {
      overview: null,
      coreInfo: null,
      taxInfo: null,
      salesHistory: null,
      ownershipInfo: null,
      investmentAnalysis: null,
      sunbizData: null
    },
    isLoading: false,
    hasError: false,
    dataQuality: {
      completeness: 0,
      confidence: 'LOW',
      lastUpdated: new Date().toISOString()
    }
  })

  // API base URL configuration
  const getApiUrl = (endpoint: string) => {
    const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost'
    const baseUrl = isLocalhost ? 'http://localhost:8001' : ''
    return `${baseUrl}/api/properties/${endpoint}/${propertyId}`
  }

  // Generic fetch function with error handling
  const fetchWithErrorHandling = async (endpoint: string): Promise<any> => {
    try {
      const response = await fetch(getApiUrl(endpoint), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || 'API request failed')
      }

      return result
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error)
      throw error
    }
  }

  // Fetch individual data sections
  const fetchOverview = useCallback(async () => {
    setData(prev => ({
      ...prev,
      loading: { ...prev.loading, overview: true },
      errors: { ...prev.errors, overview: null }
    }))

    try {
      const result = await fetchWithErrorHandling('overview')
      setData(prev => ({
        ...prev,
        overview: result.overview,
        loading: { ...prev.loading, overview: false }
      }))
      return result.overview
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: { ...prev.loading, overview: false },
        errors: { ...prev.errors, overview: error instanceof Error ? error.message : 'Failed to fetch overview' }
      }))
      return null
    }
  }, [propertyId])

  const fetchCoreInfo = useCallback(async () => {
    setData(prev => ({
      ...prev,
      loading: { ...prev.loading, coreInfo: true },
      errors: { ...prev.errors, coreInfo: null }
    }))

    try {
      const result = await fetchWithErrorHandling('enhanced')
      setData(prev => ({
        ...prev,
        coreInfo: result.property,
        loading: { ...prev.loading, coreInfo: false }
      }))
      return result.property
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: { ...prev.loading, coreInfo: false },
        errors: { ...prev.errors, coreInfo: error instanceof Error ? error.message : 'Failed to fetch core info' }
      }))
      return null
    }
  }, [propertyId])

  const fetchTaxInfo = useCallback(async () => {
    setData(prev => ({
      ...prev,
      loading: { ...prev.loading, taxInfo: true },
      errors: { ...prev.errors, taxInfo: null }
    }))

    try {
      const result = await fetchWithErrorHandling('tax-info')
      setData(prev => ({
        ...prev,
        taxInfo: result.tax,
        loading: { ...prev.loading, taxInfo: false }
      }))
      return result.tax
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: { ...prev.loading, taxInfo: false },
        errors: { ...prev.errors, taxInfo: error instanceof Error ? error.message : 'Failed to fetch tax info' }
      }))
      return null
    }
  }, [propertyId])

  const fetchSalesHistory = useCallback(async () => {
    setData(prev => ({
      ...prev,
      loading: { ...prev.loading, salesHistory: true },
      errors: { ...prev.errors, salesHistory: null }
    }))

    try {
      const result = await fetchWithErrorHandling('sales-history')
      setData(prev => ({
        ...prev,
        salesHistory: result.sales_history,
        loading: { ...prev.loading, salesHistory: false }
      }))
      return result.sales_history
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: { ...prev.loading, salesHistory: false },
        errors: { ...prev.errors, salesHistory: error instanceof Error ? error.message : 'Failed to fetch sales history' }
      }))
      return null
    }
  }, [propertyId])

  const fetchOwnershipInfo = useCallback(async () => {
    setData(prev => ({
      ...prev,
      loading: { ...prev.loading, ownershipInfo: true },
      errors: { ...prev.errors, ownershipInfo: null }
    }))

    try {
      const result = await fetchWithErrorHandling('ownership')
      setData(prev => ({
        ...prev,
        ownershipInfo: result.ownership,
        loading: { ...prev.loading, ownershipInfo: false }
      }))
      return result.ownership
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: { ...prev.loading, ownershipInfo: false },
        errors: { ...prev.errors, ownershipInfo: error instanceof Error ? error.message : 'Failed to fetch ownership info' }
      }))
      return null
    }
  }, [propertyId])

  const fetchInvestmentAnalysis = useCallback(async () => {
    setData(prev => ({
      ...prev,
      loading: { ...prev.loading, investmentAnalysis: true },
      errors: { ...prev.errors, investmentAnalysis: null }
    }))

    try {
      const result = await fetchWithErrorHandling('investment-analysis')
      setData(prev => ({
        ...prev,
        investmentAnalysis: result.investment_analysis,
        loading: { ...prev.loading, investmentAnalysis: false }
      }))
      return result.investment_analysis
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: { ...prev.loading, investmentAnalysis: false },
        errors: { ...prev.errors, investmentAnalysis: error instanceof Error ? error.message : 'Failed to fetch investment analysis' }
      }))
      return null
    }
  }, [propertyId])

  const fetchSunbizData = useCallback(async () => {
    setData(prev => ({
      ...prev,
      loading: { ...prev.loading, sunbizData: true },
      errors: { ...prev.errors, sunbizData: null }
    }))

    try {
      const result = await fetchWithErrorHandling('sunbiz')
      setData(prev => ({
        ...prev,
        sunbizData: result.sunbiz,
        loading: { ...prev.loading, sunbizData: false }
      }))
      return result.sunbiz
    } catch (error) {
      setData(prev => ({
        ...prev,
        loading: { ...prev.loading, sunbizData: false },
        errors: { ...prev.errors, sunbizData: error instanceof Error ? error.message : 'Failed to fetch Sunbiz data' }
      }))
      return null
    }
  }, [propertyId])

  // Fetch all data concurrently
  const fetchAllData = useCallback(async () => {
    if (!propertyId) return

    setData(prev => ({ ...prev, isLoading: true, hasError: false }))

    try {
      // Fetch all data sections concurrently for better performance
      const results = await Promise.allSettled([
        fetchOverview(),
        fetchCoreInfo(),
        fetchTaxInfo(),
        fetchSalesHistory(),
        fetchOwnershipInfo(),
        fetchInvestmentAnalysis(),
        fetchSunbizData()
      ])

      // Calculate data quality based on successful fetches
      const successfulFetches = results.filter(result => result.status === 'fulfilled').length
      const completeness = Math.round((successfulFetches / results.length) * 100)

      let confidence = 'LOW'
      if (completeness >= 85) confidence = 'HIGH'
      else if (completeness >= 60) confidence = 'MEDIUM'

      setData(prev => ({
        ...prev,
        isLoading: false,
        hasError: successfulFetches === 0,
        dataQuality: {
          completeness,
          confidence,
          lastUpdated: new Date().toISOString()
        }
      }))

    } catch (error) {
      setData(prev => ({
        ...prev,
        isLoading: false,
        hasError: true
      }))
    }
  }, [propertyId, fetchOverview, fetchCoreInfo, fetchTaxInfo, fetchSalesHistory, fetchOwnershipInfo, fetchInvestmentAnalysis, fetchSunbizData])

  // Refresh specific data section
  const refreshSection = useCallback(async (section: keyof typeof data.loading) => {
    switch (section) {
      case 'overview':
        return await fetchOverview()
      case 'coreInfo':
        return await fetchCoreInfo()
      case 'taxInfo':
        return await fetchTaxInfo()
      case 'salesHistory':
        return await fetchSalesHistory()
      case 'ownershipInfo':
        return await fetchOwnershipInfo()
      case 'investmentAnalysis':
        return await fetchInvestmentAnalysis()
      case 'sunbizData':
        return await fetchSunbizData()
      default:
        return null
    }
  }, [fetchOverview, fetchCoreInfo, fetchTaxInfo, fetchSalesHistory, fetchOwnershipInfo, fetchInvestmentAnalysis, fetchSunbizData])

  // Initial data fetch
  useEffect(() => {
    fetchAllData()
  }, [fetchAllData])

  // Helper functions for easier data access
  const getTabData = useCallback((tabName: string) => {
    switch (tabName.toLowerCase()) {
      case 'overview':
        return {
          data: data.overview,
          loading: data.loading.overview,
          error: data.errors.overview
        }
      case 'core':
      case 'coreinfo':
        return {
          data: data.coreInfo,
          loading: data.loading.coreInfo,
          error: data.errors.coreInfo
        }
      case 'tax':
      case 'taxinfo':
        return {
          data: data.taxInfo,
          loading: data.loading.taxInfo,
          error: data.errors.taxInfo
        }
      case 'sales':
      case 'saleshistory':
        return {
          data: data.salesHistory,
          loading: data.loading.salesHistory,
          error: data.errors.salesHistory
        }
      case 'ownership':
        return {
          data: data.ownershipInfo,
          loading: data.loading.ownershipInfo,
          error: data.errors.ownershipInfo
        }
      case 'investment':
      case 'analysis':
        return {
          data: data.investmentAnalysis,
          loading: data.loading.investmentAnalysis,
          error: data.errors.investmentAnalysis
        }
      case 'sunbiz':
        return {
          data: data.sunbizData,
          loading: data.loading.sunbizData,
          error: data.errors.sunbizData
        }
      default:
        return { data: null, loading: false, error: 'Unknown tab' }
    }
  }, [data])

  // Check if any critical data is missing
  const hasCriticalData = useCallback(() => {
    return !!(data.overview || data.coreInfo)
  }, [data.overview, data.coreInfo])

  // Get overall loading state
  const isAnyLoading = useCallback(() => {
    return Object.values(data.loading).some(loading => loading)
  }, [data.loading])

  // Get summary of errors
  const getErrorSummary = useCallback(() => {
    const errors = Object.entries(data.errors)
      .filter(([_, error]) => error !== null)
      .map(([section, error]) => ({ section, error }))

    return errors
  }, [data.errors])

  return {
    ...data,

    // Convenience getters
    isAnyLoading: isAnyLoading(),
    hasCriticalData: hasCriticalData(),
    errorSummary: getErrorSummary(),

    // Methods
    fetchAllData,
    refreshSection,
    getTabData,

    // Fallback data structure for backward compatibility
    fallbackData: {
      bcpaData: data.coreInfo || {},
      lastSale: data.salesHistory?.recent_sales?.[0] || {},
      investmentScore: data.investmentAnalysis?.investment_score?.overall_score || 0,
      opportunities: data.investmentAnalysis?.opportunities?.primary_opportunities || [],
      riskFactors: data.investmentAnalysis?.risk_assessment?.risk_factors || [],
      sdfData: data.salesHistory?.sales_records || [],
      sunbizData: data.sunbizData?.corporate_entities || [],
      ownershipData: data.ownershipInfo || {},
      taxData: data.taxInfo || {}
    }
  }
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

// Export helper functions
export const formatCurrency = (value?: number): string => {
  if (!value || value === 0) return 'N/A'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}

export const formatDate = (dateString?: string): string => {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch {
    return 'Invalid Date'
  }
}

export const formatPercentage = (value?: number): string => {
  if (value === undefined || value === null) return 'N/A'
  return `${value.toFixed(1)}%`
}