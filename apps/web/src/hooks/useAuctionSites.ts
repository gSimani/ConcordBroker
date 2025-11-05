import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export interface AuctionSite {
  county: string
  foreclosure_url: string | null
  tax_deed_url: string | null
  site_type: 'separate' | 'combined' | 'foreclosure_only' | 'tax_deed_only' | 'coming_soon'
  has_foreclosure: boolean
  has_tax_deed: boolean
  login_location: string
  login_fields: {
    username_field: string
    password_field: string
    submit_button: string
  }
  notes: string | null
  is_active: boolean
}

export interface AuctionSiteCredentials {
  username: string
  password: string
}

// Unified credentials for all RealAuction sites
export const AUCTION_CREDENTIALS: AuctionSiteCredentials = {
  username: 'gSimani',
  password: '12261226'
}

export function useAuctionSites(county?: string | null) {
  const [auctionSite, setAuctionSite] = useState<AuctionSite | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!county) {
      setLoading(false)
      setAuctionSite(null)
      return
    }

    const fetchAuctionSite = async () => {
      try {
        setLoading(true)
        setError(null)

        // Normalize county name to uppercase for consistent lookup
        const normalizedCounty = county.toUpperCase()

        const { data, error: queryError } = await supabase
          .from('auction_sites')
          .select('*')
          .eq('county', normalizedCounty)
          .eq('is_active', true)
          .single()

        if (queryError) {
          // Not finding a county is not an error - just means no auction site
          if (queryError.code === 'PGRST116') {
            setAuctionSite(null)
          } else {
            throw queryError
          }
        } else {
          setAuctionSite(data)
        }
      } catch (err) {
        console.error('Error fetching auction site:', err)
        setError(err instanceof Error ? err : new Error('Unknown error'))
      } finally {
        setLoading(false)
      }
    }

    fetchAuctionSite()
  }, [county])

  return { auctionSite, loading, error, credentials: AUCTION_CREDENTIALS }
}

/**
 * Alternative: Use the database helper function
 * This is slightly more efficient as it uses the pre-defined RPC
 */
export function useAuctionSitesRPC(county?: string | null) {
  const [auctionSite, setAuctionSite] = useState<AuctionSite | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!county) {
      setLoading(false)
      setAuctionSite(null)
      return
    }

    const fetchAuctionSite = async () => {
      try {
        setLoading(true)
        setError(null)

        const { data, error: queryError } = await supabase
          .rpc('get_auction_urls', { county_name: county })
          .single()

        if (queryError) {
          if (queryError.code === 'PGRST116') {
            setAuctionSite(null)
          } else {
            throw queryError
          }
        } else {
          setAuctionSite(data)
        }
      } catch (err) {
        console.error('Error fetching auction site:', err)
        setError(err instanceof Error ? err : new Error('Unknown error'))
      } finally {
        setLoading(false)
      }
    }

    fetchAuctionSite()
  }, [county])

  return { auctionSite, loading, error, credentials: AUCTION_CREDENTIALS }
}
