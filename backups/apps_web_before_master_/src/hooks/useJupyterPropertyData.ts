import { useState, useEffect, useCallback } from 'react'

export interface JupyterPropertyData {
  property_id: string
  address: {
    street: string
    city: string
    state: string
    zip: string
    formatted: string
  }
  overview: {
    property_location: any
    valuation_summary: any
    recent_sale: any
    property_details: any
  }
  sales_history: any[]
  tax_information: {
    current: any
    millage_rates: any
    history: any[]
    annual_tax: number
    monthly_tax: number
  }
  investment_analysis: {
    metrics: any
    monthly_expenses: any
    recommendation: string
  }
  core_property: {
    ownership: any
    building_details: any
  }
  metadata: {
    last_updated: string
    data_source: string
    completeness_score: number
  }
}

export const useJupyterPropertyData = (city: string, address: string) => {
  const [data, setData] = useState<JupyterPropertyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchJupyterData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Use the Jupyter analysis API endpoint on port 8005
      const response = await fetch(`http://localhost:8005/api/property/${city}/${address}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      if (result.success && result.data) {
        setData(result.data)
      } else {
        throw new Error(result.message || 'Failed to fetch data')
      }
    } catch (err) {
      console.error('Error fetching Jupyter property data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch property data')
    } finally {
      setLoading(false)
    }
  }, [city, address])

  useEffect(() => {
    if (city && address) {
      fetchJupyterData()
    }
  }, [city, address, fetchJupyterData])

  return {
    data,
    loading,
    error,
    refetch: fetchJupyterData
  }
}