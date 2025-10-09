import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'

export interface PropertyData {
  bcpaData: any
  sdfData: any[]
  navData: any[]
  tppData: any[]
  sunbizData: any[]
  lastSale: any
  totalNavAssessment: number
  isInCDD: boolean
  investmentScore: number
  opportunities: string[]
  riskFactors: string[]
  dataQuality: {
    bcpa: boolean
    sdf: boolean
    nav: boolean
    tpp: boolean
    sunbiz: boolean
  }
}

export const usePropertyData = (addressOrParcelId: string, city: string = '') => {
  const [data, setData] = useState<PropertyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPropertyData = useCallback(async () => {
    console.log('usePropertyData - fetchPropertyData called with:', { addressOrParcelId, city });

    if (!addressOrParcelId) {
      console.log('usePropertyData - No addressOrParcelId provided, skipping fetch');
      setLoading(false);
      return;
    }

    try {
      setLoading(true)
      setError(null)

      // Check if it's a parcel ID (alphanumeric pattern, typically longer than 8 chars) or an address
      // Parcel IDs can contain letters and numbers (like 2806S01W000000100000)
      const isParcelId = /^[A-Z0-9-]+$/i.test(addressOrParcelId.replace(/\s/g, '')) &&
                        addressOrParcelId.length > 8 &&
                        !/\b(st|street|rd|road|ave|avenue|ln|lane|ct|court|dr|drive|blvd|boulevard|pl|place|way|nw|ne|sw|se|north|south|east|west)\b/i.test(addressOrParcelId)

      console.log('Fetching property data for:', addressOrParcelId, 'City:', city, 'IsParcelId:', isParcelId)

      let bcpaData: any = null
      let sdfData: any[] = []

      // Fetch comprehensive property data from enhanced API
      if (isParcelId) {
        // Get property by parcel ID using enhanced endpoint
        let apiAvailable = false;

        // Quick API health check (100ms timeout) - saves 2-3 seconds if API down
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 100);
          const healthCheck = await fetch('http://localhost:8000/health', {
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          apiAvailable = healthCheck.ok;
          console.log('API health check:', apiAvailable ? 'UP' : 'DOWN');
        } catch {
          apiAvailable = false;
          console.log('API health check: FAILED - will query Supabase directly');
        }

        if (apiAvailable) {
          try {
            // Try the property API endpoint (port 8000)
            const enhancedResponse = await fetch(`http://localhost:8000/api/properties/${encodeURIComponent(addressOrParcelId)}`)
          if (enhancedResponse.ok) {
            const enhancedResult = await enhancedResponse.json()
            console.log('Fast API response:', enhancedResult)

            if (enhancedResult.success && enhancedResult.property) {
              // The API now returns complete property data structure
              const propertyData = enhancedResult.property

              // Extract the individual components
              bcpaData = propertyData.bcpaData
              sdfData = propertyData.sdfData || []

              console.log('Fast API data loaded:', {
                bcpaData: bcpaData,
                sdfData: sdfData,
                dataStructure: Object.keys(propertyData)
              })

              // Skip transformation since data is already in correct format
              const finalData = {
                bcpaData: propertyData.bcpaData,
                sdfData: propertyData.sdfData,
                navData: propertyData.navData,
                tppData: propertyData.tppData,
                sunbizData: propertyData.sunbizData,
                lastSale: propertyData.lastSale,
                totalNavAssessment: propertyData.totalNavAssessment,
                isInCDD: propertyData.isInCDD,
                investmentScore: propertyData.investmentScore,
                opportunities: propertyData.opportunities,
                riskFactors: propertyData.riskFactors,
                dataQuality: propertyData.dataQuality
              }

              console.log('usePropertyData - Setting enhanced data:', finalData)
              setData(finalData)
              setLoading(false)
              return
            }
          }

          // Fallback to old API if new one fails
          if (!bcpaData) {
            const response = await fetch(`http://localhost:8000/api/properties/search?q=${encodeURIComponent(addressOrParcelId)}&limit=1`)
            if (response.ok) {
              const result = await response.json()
              if (result.data && result.data.length > 0) {
                bcpaData = result.data[0]
              } else if (result.properties && result.properties.length > 0) {
                bcpaData = result.properties[0]
              }
            }
          }
        } catch (err) {
          console.error('Error fetching property by parcel ID:', err)
        }
        }
      } else {
        // Search by address
        try {
          const searchQuery = city
            ? `http://localhost:8000/api/properties/search?address=${encodeURIComponent(addressOrParcelId)}&city=${encodeURIComponent(city)}&limit=1`
            : `http://localhost:8000/api/properties/search?q=${encodeURIComponent(addressOrParcelId)}&limit=1`

          const response = await fetch(searchQuery)
          if (response.ok) {
            const result = await response.json()
            if (result.data && result.data.length > 0) {
              bcpaData = result.data[0]
            } else if (result.properties && result.properties.length > 0) {
              bcpaData = result.properties[0]
            }
          }

          // If we found a property, fetch enhanced data
          if (bcpaData && bcpaData.parcel_id) {
            try {
              const enhancedResponse = await fetch(`http://localhost:8000/api/properties/${encodeURIComponent(bcpaData.parcel_id)}`)
              if (enhancedResponse.ok) {
                const enhancedResult = await enhancedResponse.json()
                console.log('Fast API response for address search:', enhancedResult)

                if (enhancedResult.success && enhancedResult.property) {
                  // Use the complete property data structure from enhanced API
                  const propertyData = enhancedResult.property

                  const finalData = {
                    bcpaData: propertyData.bcpaData,
                    sdfData: propertyData.sdfData,
                    navData: propertyData.navData,
                    tppData: propertyData.tppData,
                    sunbizData: propertyData.sunbizData,
                    lastSale: propertyData.lastSale,
                    totalNavAssessment: propertyData.totalNavAssessment,
                    isInCDD: propertyData.isInCDD,
                    investmentScore: propertyData.investmentScore,
                    opportunities: propertyData.opportunities,
                    riskFactors: propertyData.riskFactors,
                    dataQuality: propertyData.dataQuality
                  }

                  console.log('usePropertyData - Setting enhanced data for address search:', finalData)
                  setData(finalData)
                  setLoading(false)
                  return
                }
              }
            } catch (err) {
              console.error('Error fetching enhanced data:', err)
            }
          }
        } catch (err) {
          console.error('Error searching property:', err)
        }
      }

      console.log('API result:', { bcpaData, sdfData })

      // CRITICAL FIX: If API failed, query Supabase directly (guarantees data loads)
      if (!bcpaData && isParcelId) {
        console.log('⚡ API failed - querying Supabase directly for parcel:', addressOrParcelId);

        try {
          const { data: supabaseProperty, error: supabaseError } = await supabase
            .from('florida_parcels')
            .select('*')
            .eq('parcel_id', addressOrParcelId)
            .single();

          if (!supabaseError && supabaseProperty) {
            bcpaData = supabaseProperty;
            console.log('✅ Loaded property directly from Supabase:', {
              parcel_id: bcpaData.parcel_id,
              owner: bcpaData.owner_name,
              value: bcpaData.just_value
            });

            // Fetch sales history directly from Supabase
            const { data: salesHistory } = await supabase
              .from('property_sales_history')
              .select('*')
              .eq('parcel_id', addressOrParcelId)
              .order('sale_date', { ascending: false })
              .limit(20);

            if (salesHistory && salesHistory.length > 0) {
              sdfData = salesHistory;
              console.log(`✅ Loaded ${salesHistory.length} sales records from Supabase`);
            }
          } else {
            console.error('Supabase query failed:', supabaseError);
          }
        } catch (err) {
          console.error('Error querying Supabase directly:', err);
        }
      }

      // Convert API data to expected format for backward compatibility
      // Skip transformation if data came from enhanced API (already transformed)
      if (bcpaData && !bcpaData.sales_history) {
        // Parse and format values properly
        const parseNumber = (val: any) => {
          if (!val) return null
          const num = typeof val === 'string' ? parseFloat(val.replace(/[^0-9.-]/g, '')) : val
          return isNaN(num) ? null : num
        }

        // Transform the API response to the expected bcpaData format
        const transformedData = {
          // Core identifiers
          parcel_id: bcpaData.parcel_id || bcpaData.id,

          // Address information - use both old and new field names
          property_address_full: `${bcpaData.address || bcpaData.phy_addr1 || ''}, ${bcpaData.city || bcpaData.phy_city || ''}, FL ${bcpaData.zipCode || bcpaData.phy_zipcd || ''}`.trim(),
          property_address_street: bcpaData.address || bcpaData.phy_addr1,
          property_address_city: bcpaData.city || bcpaData.phy_city,
          property_address_state: bcpaData.state || bcpaData.phy_state || 'FL',
          property_address_zip: bcpaData.zipCode || bcpaData.phy_zipcd,

          // Address fields expected by UI components
          phy_addr1: bcpaData.address || bcpaData.phy_addr1,
          phy_city: bcpaData.city || bcpaData.phy_city,
          phy_zipcd: bcpaData.zipCode || bcpaData.phy_zipcd,

          // Owner information
          owner_name: bcpaData.owner || bcpaData.owner_name,
          own_name: bcpaData.owner || bcpaData.owner_name, // Legacy field name expected by UI
          owner_address: bcpaData.ownerAddress || `${bcpaData.owner_addr1 || ''}, ${bcpaData.owner_city || ''}, ${bcpaData.owner_state || ''} ${bcpaData.owner_zip || ''}`.trim(),

          // Values - map to both new and legacy field names
          assessed_value: parseNumber(bcpaData.assessedValue) || parseNumber(bcpaData.assessed_value) || parseNumber(bcpaData.taxableValue),
          taxable_value: parseNumber(bcpaData.taxableValue) || parseNumber(bcpaData.taxable_value),
          market_value: parseNumber(bcpaData.marketValue) || parseNumber(bcpaData.justValue) || parseNumber(bcpaData.just_value),
          just_value: parseNumber(bcpaData.justValue) || parseNumber(bcpaData.marketValue) || parseNumber(bcpaData.just_value),
          land_value: parseNumber(bcpaData.landValue) || parseNumber(bcpaData.land_value),
          building_value: parseNumber(bcpaData.buildingValue) || parseNumber(bcpaData.building_value),

          // Legacy field names expected by UI components
          jv: parseNumber(bcpaData.justValue) || parseNumber(bcpaData.marketValue) || parseNumber(bcpaData.just_value), // Just Value
          tv_sd: parseNumber(bcpaData.taxableValue) || parseNumber(bcpaData.taxable_value), // Taxable Value School District
          lnd_val: parseNumber(bcpaData.landValue) || parseNumber(bcpaData.land_value), // Land Value

          // Building details
          year_built: bcpaData.yearBuilt || bcpaData.year_built,
          act_yr_blt: bcpaData.yearBuilt || bcpaData.year_built, // Legacy field name
          eff_year_built: bcpaData.yearBuilt || bcpaData.year_built,
          living_area: parseNumber(bcpaData.buildingSqFt) || parseNumber(bcpaData.total_living_area),
          tot_lvg_area: parseNumber(bcpaData.buildingSqFt) || parseNumber(bcpaData.total_living_area), // Legacy field name
          lot_size_sqft: parseNumber(bcpaData.landSqFt) || parseNumber(bcpaData.land_sqft),
          lnd_sqfoot: parseNumber(bcpaData.landSqFt) || parseNumber(bcpaData.land_sqft), // Legacy field name
          bedrooms: bcpaData.bedrooms,
          bathrooms: bcpaData.bathrooms,
          units: bcpaData.units || 1,
          stories: bcpaData.stories,

          // Property classification
          property_use_code: bcpaData.propertyUse || bcpaData.property_use,
          property_type: bcpaData.propertyType || bcpaData.property_use_desc,
          dor_uc: bcpaData.propertyUse || bcpaData.property_use, // Legacy field name

          // Legal information
          legal_desc: bcpaData.legal_desc,
          subdivision: bcpaData.subdivision,
          lot: bcpaData.lot,
          block: bcpaData.block,
          zoning: bcpaData.zoning,

          // Tax and exemptions
          tax_amount: Math.round((parseNumber(bcpaData.taxable_value) || 0) * 0.02),
          homestead_exemption: bcpaData.is_redacted === false,
          other_exemptions: null,

          // Sale information
          sale_price: parseNumber(bcpaData.lastSalePrice) || parseNumber(bcpaData.sale_price),
          sale_date: bcpaData.lastSaleDate || bcpaData.sale_date,
          sale_prc1: parseNumber(bcpaData.lastSalePrice) || parseNumber(bcpaData.sale_price), // Legacy field name
          sale_yr1: (bcpaData.lastSaleDate || bcpaData.sale_date) ? new Date(bcpaData.lastSaleDate || bcpaData.sale_date).getFullYear() : null,
          sale_mo1: (bcpaData.lastSaleDate || bcpaData.sale_date) ? new Date(bcpaData.lastSaleDate || bcpaData.sale_date).getMonth() + 1 : null,
          qual_cd1: bcpaData.sale_qualification || 'Q', // Default to qualified

          // Additional fields for links
          property_sketch_link: null,
          land_factors: null
        }

        bcpaData = transformedData
      }
      // If data came from enhanced API, sales_history is already included
      else if (bcpaData && bcpaData.sales_history) {
        sdfData = bcpaData.sales_history || sdfData
      }
      
      // Fetch additional data from Supabase if available
      let sunbizData: any[] = []
      const navData: any[] = []
      const tppData: any[] = []

      // Try to fetch Sunbiz data if owner name exists
      if (bcpaData?.owner_name) {
        try {
          const { data: sunbizResponse } = await supabase
            .from('sunbiz_corporate')
            .select('*')
            .ilike('entity_name', `%${bcpaData.owner_name}%`)
            .limit(5)

          if (sunbizResponse) {
            sunbizData = sunbizResponse
          }
        } catch (error) {
          console.log('Sunbiz query failed:', error)
        }
      }

      // Try to fetch NAV data
      if (bcpaData?.parcel_id) {
        try {
          const { data: navResponse } = await supabase
            .from('nav_assessments')
            .select('*')
            .eq('parcel_id', bcpaData.parcel_id)

          if (navResponse) {
            navData.push(...navResponse)
          }
        } catch (error) {
          console.log('NAV query failed:', error)
        }
      }

      // Calculate derived data - use sales history from API or database
      let lastSale = null

      // Find the most recent sale over $1000 from sales history
      if (sdfData.length > 0) {
        lastSale = sdfData.find(sale => {
          const salePrice = parseFloat(String(sale.sale_price || '0'))
          return salePrice >= 1000
        })

        // Transform sales record to expected format
        if (lastSale) {
          lastSale = {
            sale_date: lastSale.sale_date,
            sale_price: String(lastSale.sale_price),
            sale_type: lastSale.deed_type || 'Warranty Deed',
            qualified_sale: lastSale.sale_qualification === 'Q',
            is_distressed: false,
            is_bank_sale: false,
            is_cash_sale: false,
            book: lastSale.book,
            page: lastSale.page,
            document_type: lastSale.deed_type || 'Warranty Deed',
            grantor_name: lastSale.grantor,
            grantee_name: lastSale.grantee,
            vi_code: null,
            sale_reason: null,
            book_page: lastSale.book && lastSale.page ? `${lastSale.book}/${lastSale.page}` : null,
            cin: lastSale.instrument_number,
            record_link: 'https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx'
          }
        }
      }

      // If no sales history but we have sale info in property data, use that
      if (!lastSale && bcpaData?.sale_price) {
        const salePrice = parseFloat(String(bcpaData.sale_price))
        if (salePrice >= 1000) {
          lastSale = {
            sale_date: bcpaData.sale_date,
            sale_price: String(bcpaData.sale_price),
            sale_type: 'Warranty Deed',
            qualified_sale: true,
            is_distressed: false,
            is_bank_sale: false,
            is_cash_sale: false,
            book: null,
            page: null,
            document_type: 'Warranty Deed',
            grantor_name: null,
            grantee_name: bcpaData.owner_name,
            vi_code: null,
            sale_reason: null,
            book_page: null,
            cin: null,
            record_link: null
          }
        }
      }
      const totalNavAssessment = navData.reduce((sum: number, nav: any) => 
        sum + (parseFloat(nav.total_assessment) || 0), 0
      )
      const isInCDD = totalNavAssessment > 1000

      // Calculate investment score
      let investmentScore = 50
      if (lastSale?.is_distressed) investmentScore += 15
      if (lastSale?.is_bank_sale) investmentScore += 10
      if (bcpaData?.property_use_code === 'SINGLE FAMILY') investmentScore += 5
      if (isInCDD) investmentScore -= 5
      if (totalNavAssessment > 5000) investmentScore -= 10

      const salePrice = parseFloat(lastSale?.sale_price || '0')
      const livingArea = parseFloat(bcpaData?.living_area || '0')
      if (livingArea > 0) {
        const pricePerSqft = salePrice / livingArea
        if (pricePerSqft < 200) investmentScore += 5
        if (pricePerSqft > 400) investmentScore -= 5
      }

      investmentScore = Math.max(0, Math.min(100, investmentScore))

      // Identify opportunities
      const opportunities = []
      if (lastSale?.is_distressed) opportunities.push('🔴 Distressed property - potential below-market opportunity')
      if (lastSale?.is_bank_sale) opportunities.push('🏦 Bank-owned (REO) - motivated seller situation')
      if (sunbizData.length > 0) opportunities.push('🏢 Business owner - potential bulk portfolio opportunity')
      if (salePrice && salePrice < 300000) opportunities.push('💰 Below $300K - strong cash flow potential')

      // Identify risk factors
      const riskFactors = []
      if (isInCDD) riskFactors.push(`⚠️ Property in CDD - additional assessments $${totalNavAssessment.toFixed(0)}/year`)
      if (bcpaData?.year_built && bcpaData.year_built < 1970) riskFactors.push('⚠️ Built before 1970 - potential structural/code issues')
      if (sdfData.length === 0) riskFactors.push('⚠️ No recent sales history - difficult to establish market value')

      // Data quality indicators
      const dataQuality = {
        bcpa: !!bcpaData,
        sdf: sdfData.length > 0,
        nav: navData.length > 0,
        tpp: tppData.length > 0,
        sunbiz: sunbizData.length > 0
      }

      const finalData = {
        bcpaData,
        sdfData,
        navData,
        tppData,
        sunbizData,
        lastSale,
        totalNavAssessment,
        isInCDD,
        investmentScore,
        opportunities,
        riskFactors,
        dataQuality
      };

      console.log('usePropertyData - Setting final data:', finalData);
      setData(finalData)
    } catch (err) {
      console.error('Error fetching property data:', err)
      setError('Failed to fetch property data from database')
    } finally {
      setLoading(false)
    }
  }, [addressOrParcelId, city])

  useEffect(() => {
    if (addressOrParcelId) {
      fetchPropertyData()
    }
  }, [addressOrParcelId, city, fetchPropertyData])

  // Set up real-time subscriptions for data updates
  useEffect(() => {
    if (!data?.bcpaData?.parcel_id) return

    const parcelId = data.bcpaData.parcel_id

    // Subscribe to BCPA property updates
    const bcpaSubscription = supabase
      .channel(`bcpa-${parcelId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'fl_properties',
          filter: `parcel_id=eq.${parcelId}`
        },
        (payload) => {
          console.log('BCPA data updated:', payload)
          fetchPropertyData()
        }
      )
      .subscribe()

    // Subscribe to SDF sales updates
    const sdfSubscription = supabase
      .channel(`sdf-${parcelId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'fl_sdf_sales',
          filter: `parcel_id=eq.${parcelId}`
        },
        (payload) => {
          console.log('SDF data updated:', payload)
          fetchPropertyData()
        }
      )
      .subscribe()

    // Subscribe to NAV assessment updates
    const navSubscription = supabase
      .channel(`nav-${parcelId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'fl_nav_assessment_detail',
          filter: `parcel_id=eq.${parcelId}`
        },
        (payload) => {
          console.log('NAV data updated:', payload)
          fetchPropertyData()
        }
      )
      .subscribe()

    return () => {
      bcpaSubscription.unsubscribe()
      sdfSubscription.unsubscribe()
      navSubscription.unsubscribe()
    }
  }, [data?.bcpaData?.parcel_id, fetchPropertyData])

  return {
    data,
    loading,
    error,
    refetch: fetchPropertyData
  }
}
// Updated to use fast API
