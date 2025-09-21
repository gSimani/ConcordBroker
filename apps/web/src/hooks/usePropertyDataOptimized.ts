import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback, useMemo } from 'react'
import { propertyService, FloridaParcel } from '../lib/supabase-optimized'
import debounce from 'lodash/debounce'

// Optimized property search hook with caching and debouncing
export const usePropertySearch = (initialFilters = {}) => {
  const [filters, setFilters] = useState(initialFilters)
  const queryClient = useQueryClient()

  // Create stable query key
  const queryKey = useMemo(
    () => ['properties', 'search', filters],
    [filters]
  )

  // Debounced filter update
  const debouncedSetFilters = useCallback(
    debounce((newFilters) => {
      setFilters(newFilters)
    }, 300),
    []
  )

  const query = useQuery({
    queryKey,
    queryFn: () => propertyService.searchProperties(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    keepPreviousData: true, // Keep previous data while fetching new
  })

  // Prefetch next page for pagination
  const prefetchNextPage = useCallback(() => {
    const nextOffset = (filters.offset || 0) + (filters.limit || 20)
    queryClient.prefetchQuery({
      queryKey: ['properties', 'search', { ...filters, offset: nextOffset }],
      queryFn: () => propertyService.searchProperties({ ...filters, offset: nextOffset }),
    })
  }, [filters, queryClient])

  return {
    ...query,
    filters,
    setFilters: debouncedSetFilters,
    prefetchNextPage,
  }
}

// Optimized single property hook with related data
export const usePropertyDetails = (parcelId: string | undefined) => {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['property', parcelId],
    queryFn: () => propertyService.getPropertyDetails(parcelId!),
    enabled: !!parcelId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  })

  // Prefetch related properties
  const prefetchRelatedProperties = useCallback(async () => {
    if (query.data?.owner_name) {
      await queryClient.prefetchQuery({
        queryKey: ['properties', 'owner', query.data.owner_name],
        queryFn: () => propertyService.getPropertiesByOwner(query.data.owner_name),
      })
    }
  }, [query.data, queryClient])

  return {
    ...query,
    prefetchRelatedProperties,
  }
}

// Bulk property loader with batching
export const useBulkProperties = () => {
  const [parcelIds, setParcelIds] = useState<string[]>([])
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['properties', 'bulk', parcelIds],
    queryFn: () => propertyService.getMultipleProperties(parcelIds),
    enabled: parcelIds.length > 0,
    staleTime: 5 * 60 * 1000,
  })

  // Add properties to bulk load
  const addProperties = useCallback((ids: string[]) => {
    setParcelIds(prev => [...new Set([...prev, ...ids])])
  }, [])

  // Clear bulk selection
  const clearProperties = useCallback(() => {
    setParcelIds([])
  }, [])

  return {
    ...query,
    parcelIds,
    addProperties,
    clearProperties,
  }
}

// Market analytics hook with caching
export const useMarketAnalytics = (county: string, timeRange: 'month' | 'quarter' | 'year' = 'quarter') => {
  return useQuery({
    queryKey: ['analytics', 'market', county, timeRange],
    queryFn: () => propertyService.getMarketAnalytics(county, timeRange),
    enabled: !!county,
    staleTime: 30 * 60 * 1000, // 30 minutes
    cacheTime: 60 * 60 * 1000, // 1 hour
  })
}

// Property mutations with optimistic updates
export const usePropertyMutations = () => {
  const queryClient = useQueryClient()

  const updateProperty = useMutation({
    mutationFn: async (property: Partial<FloridaParcel>) => {
      // Implement update logic
      const { data, error } = await supabase
        .from('florida_parcels')
        .update(property)
        .eq('parcel_id', property.parcel_id)
        .select()
        .single()

      if (error) throw error
      return data
    },
    onMutate: async (property) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ['property', property.parcel_id] })

      // Snapshot previous value
      const previousProperty = queryClient.getQueryData(['property', property.parcel_id])

      // Optimistically update
      queryClient.setQueryData(['property', property.parcel_id], (old: any) => ({
        ...old,
        ...property,
      }))

      return { previousProperty }
    },
    onError: (err, property, context) => {
      // Rollback on error
      if (context?.previousProperty) {
        queryClient.setQueryData(['property', property.parcel_id], context.previousProperty)
      }
    },
    onSettled: (data, error, property) => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: ['property', property.parcel_id] })
    },
  })

  return {
    updateProperty,
  }
}

// Property comparison hook
export const usePropertyComparison = (parcelIds: string[]) => {
  const queries = useQuery({
    queryKey: ['properties', 'comparison', parcelIds],
    queryFn: async () => {
      const properties = await Promise.all(
        parcelIds.map(id => propertyService.getPropertyDetails(id))
      )
      return properties
    },
    enabled: parcelIds.length > 0 && parcelIds.length <= 5, // Limit comparison to 5 properties
    staleTime: 10 * 60 * 1000,
  })

  const comparisonData = useMemo(() => {
    if (!queries.data) return null

    // Calculate comparison metrics
    const avgValue = queries.data.reduce((sum, p) => sum + (p.just_value || 0), 0) / queries.data.length
    const avgSqft = queries.data.reduce((sum, p) => sum + (p.total_living_area || 0), 0) / queries.data.length
    const avgYear = queries.data.reduce((sum, p) => sum + (p.year_built || 0), 0) / queries.data.length

    return {
      properties: queries.data,
      metrics: {
        averageValue: avgValue,
        averageSqft: avgSqft,
        averageYearBuilt: Math.round(avgYear),
        pricePerSqft: avgValue / avgSqft,
      },
    }
  }, [queries.data])

  return {
    ...queries,
    comparisonData,
  }
}

// Real-time property updates hook
export const usePropertySubscription = (parcelId: string | undefined, onUpdate?: (data: any) => void) => {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!parcelId) return

    const subscription = propertyService.subscribeToPropertyUpdates(parcelId, (payload) => {
      // Update cache
      queryClient.setQueryData(['property', parcelId], payload.new)

      // Call callback if provided
      if (onUpdate) {
        onUpdate(payload.new)
      }
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [parcelId, queryClient, onUpdate])
}

// Property statistics hook
export const usePropertyStatistics = (filters: any) => {
  return useQuery({
    queryKey: ['properties', 'statistics', filters],
    queryFn: async () => {
      const { data } = await propertyService.searchProperties({ ...filters, limit: 1000 })

      if (!data || data.length === 0) return null

      // Calculate statistics
      const values = data.map(p => p.just_value || 0)
      const sqfts = data.map(p => p.total_living_area || 0).filter(v => v > 0)
      const years = data.map(p => p.year_built || 0).filter(v => v > 0)

      const stats = {
        count: data.length,
        value: {
          min: Math.min(...values),
          max: Math.max(...values),
          avg: values.reduce((a, b) => a + b, 0) / values.length,
          median: values.sort((a, b) => a - b)[Math.floor(values.length / 2)],
        },
        sqft: sqfts.length > 0 ? {
          min: Math.min(...sqfts),
          max: Math.max(...sqfts),
          avg: sqfts.reduce((a, b) => a + b, 0) / sqfts.length,
        } : null,
        yearBuilt: years.length > 0 ? {
          min: Math.min(...years),
          max: Math.max(...years),
          avg: Math.round(years.reduce((a, b) => a + b, 0) / years.length),
        } : null,
      }

      return stats
    },
    enabled: !!filters,
    staleTime: 15 * 60 * 1000, // 15 minutes
  })
}

// Export all hooks
export default {
  usePropertySearch,
  usePropertyDetails,
  useBulkProperties,
  useMarketAnalytics,
  usePropertyMutations,
  usePropertyComparison,
  usePropertySubscription,
  usePropertyStatistics,
}