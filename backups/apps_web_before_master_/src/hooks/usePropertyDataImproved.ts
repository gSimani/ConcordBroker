import { useState, useEffect, useCallback } from 'react'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
)

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

// Helper function to extract individual names from owner string
function extractIndividualNames(ownerName: string): string[] {
  if (!ownerName) return []
  
  // Remove common suffixes
  let cleanName = ownerName
    .replace(/\s+(LLC|INC|CORP|CORPORATION|LP|LLP|TRUST|ESTATE|REVOCABLE|IRREVOCABLE|LIVING)\b/gi, '')
    .replace(/\s+H\/E\b/gi, '') // Remove H/E (Husband/Estate)
    .replace(/\s+W\/E\b/gi, '') // Remove W/E (Wife/Estate)
    .replace(/\s+ET\s+AL\b/gi, '') // Remove ET AL
    .replace(/\s+ETAL\b/gi, '') // Remove ETAL
    .trim()
  
  // If it looks like a company name, return empty
  if (/\b(LLC|INC|CORP|CORPORATION|LP|PROPERTIES|INVESTMENTS|HOLDINGS|CAPITAL|PARTNERS|GROUP)\b/i.test(ownerName)) {
    return []
  }
  
  // Split by common delimiters
  const names = cleanName
    .split(/[&,;]/)
    .map(n => n.trim())
    .filter(n => n.length > 0)
  
  // Further process each name to handle formats like "SMITH JOHN & MARY"
  const individualNames: string[] = []
  
  names.forEach(name => {
    // If name has both first and last components
    if (name.includes(' ')) {
      individualNames.push(name)
      
      // Also try to extract if it's in format "LASTNAME FIRSTNAME"
      const parts = name.split(/\s+/)
      if (parts.length === 2) {
        // Add reversed version too
        individualNames.push(`${parts[1]} ${parts[0]}`)
      }
    }
  })
  
  return individualNames
}

export const usePropertyDataImproved = (addressOrParcelId: string, city: string = '') => {
  const [data, setData] = useState<PropertyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPropertyData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Check if it's a parcel ID (usually starts with numbers) or an address
      const isParcelId = /^\d/.test(addressOrParcelId)
      
      const normalizedAddress = addressOrParcelId.toLowerCase().replace(/[^\\w\\s]/g, '').replace(/\\s+/g, ' ').trim()
      const normalizedCity = city.toLowerCase().replace(/[^\\w\\s]/g, '').replace(/\\s+/g, ' ').trim()

      // Log for debugging
      console.log('Fetching property data for:', addressOrParcelId, 'City:', city, 'IsParcelId:', isParcelId);
      
      // Build queries with better handling
      let floridaParcelsQuery;
      let bcpaQuery;
      
      if (isParcelId) {
        // Query by parcel ID directly
        floridaParcelsQuery = supabase
          .from('florida_parcels')
          .select('*')
          .eq('parcel_id', addressOrParcelId)
          .limit(1);
          
        bcpaQuery = supabase
          .from('properties')
          .select('*')
          .eq('parcel_id', addressOrParcelId)
          .limit(1);
      } else {
        // Query by address - try multiple variations
        floridaParcelsQuery = supabase
          .from('florida_parcels')
          .select('*')
          .or(`phy_addr1.ilike.%${addressOrParcelId}%,parcel_id.eq.${addressOrParcelId}`)
          .limit(1);
          
        bcpaQuery = supabase
          .from('properties')
          .select('*')
          .or(`property_address.ilike.%${normalizedAddress}%,parcel_id.eq.${addressOrParcelId}`)
          .limit(1);
      }
      
      // Parallel data fetching - check florida_parcels first, then properties
      const [floridaParcelsResponse, bcpaResponse, sdfResponse, navResponse] = await Promise.all([
        // Try florida_parcels table first (our loaded data)
        floridaParcelsQuery,
        
        // Fallback to properties if exists
        bcpaQuery,
        
        // Try to fetch from property_sales_history table
        isParcelId ? 
          supabase
            .from('property_sales_history')
            .select('*')
            .eq('parcel_id', addressOrParcelId)
            .order('sale_date', { ascending: false }) :
          supabase
            .from('property_sales_history')
            .select('*')
            .eq('parcel_id', addressOrParcelId)
            .order('sale_date', { ascending: false }),
        
        supabase
          .from('nav_assessments')
          .select('*')
          .eq('parcel_id', isParcelId ? addressOrParcelId : '')
      ])

      // Log responses for debugging
      console.log('Florida Parcels Response:', floridaParcelsResponse);
      console.log('BCPA Response:', bcpaResponse);
      
      // Use florida_parcels data if available, otherwise fallback to properties
      const floridaParcel = floridaParcelsResponse.data?.[0] || null
      let bcpaData = bcpaResponse.data?.[0] || null
      
      // Convert florida_parcels to bcpaData format if needed
      if (floridaParcel && !bcpaData) {
        // Parse and format values properly
        const parseNumber = (val: any) => {
          if (!val) return null;
          const num = typeof val === 'string' ? parseFloat(val.replace(/[^0-9.-]/g, '')) : val;
          return isNaN(num) ? null : num;
        };

        bcpaData = {
          parcel_id: floridaParcel.parcel_id,
          property_address_full: `${floridaParcel.phy_addr1 || ''}, ${floridaParcel.phy_city || ''}, FL ${floridaParcel.phy_zipcd || ''}`.trim(),
          property_address_street: floridaParcel.phy_addr1,
          property_address_city: floridaParcel.phy_city,
          property_address_state: floridaParcel.phy_state || 'FL',
          property_address_zip: floridaParcel.phy_zipcd,
          owner_name: floridaParcel.owner_name,
          owner_address: `${floridaParcel.owner_addr1 || ''}, ${floridaParcel.owner_city || ''}, ${floridaParcel.owner_state || ''} ${floridaParcel.owner_zip || ''}`.trim(),
          
          // Values - ensure proper parsing
          assessed_value: parseNumber(floridaParcel.assessed_value) || parseNumber(floridaParcel.taxable_value),
          taxable_value: parseNumber(floridaParcel.taxable_value),
          market_value: parseNumber(floridaParcel.just_value) || parseNumber(floridaParcel.market_value) || parseNumber(floridaParcel.taxable_value),
          just_value: parseNumber(floridaParcel.just_value) || parseNumber(floridaParcel.taxable_value),
          land_value: parseNumber(floridaParcel.land_value),
          building_value: parseNumber(floridaParcel.building_value) || parseNumber(floridaParcel.improvement_value),
          
          // Building details
          year_built: floridaParcel.year_built,
          eff_year_built: floridaParcel.eff_year_built || floridaParcel.year_built,
          living_area: parseNumber(floridaParcel.total_living_area) || parseNumber(floridaParcel.living_area) || parseNumber(floridaParcel.heated_area),
          lot_size_sqft: parseNumber(floridaParcel.land_sqft) || parseNumber(floridaParcel.lot_size),
          bedrooms: floridaParcel.bedrooms,
          bathrooms: floridaParcel.bathrooms,
          units: floridaParcel.units || floridaParcel.total_units || 1,
          
          // Property classification
          property_use_code: floridaParcel.property_use || floridaParcel.usage_code || floridaParcel.use_code,
          property_type: floridaParcel.property_use_desc || floridaParcel.property_type || floridaParcel.use_description,
          
          // Tax and exemptions
          tax_amount: parseNumber(floridaParcel.tax_amount) || Math.round((parseNumber(floridaParcel.taxable_value) || 0) * 0.02),
          homestead_exemption: floridaParcel.homestead_exemption === 'Y' || floridaParcel.homestead_exemption === true || floridaParcel.homestead === 'Y',
          other_exemptions: floridaParcel.other_exemptions || floridaParcel.exemption_codes,
          
          // Sale information
          sale_price: parseNumber(floridaParcel.sale_price),
          sale_date: floridaParcel.sale_date,
          
          // Additional fields for links
          property_sketch_link: floridaParcel.sketch_url || null,
          
          // Land factors if available
          land_factors: floridaParcel.land_factors ? JSON.parse(floridaParcel.land_factors) : null
        }
      }
      // If we have properties table data, map it correctly
      else if (bcpaData) {
        // Remap properties table fields to expected format
        const tempData = bcpaData;
        bcpaData = {
          parcel_id: tempData.parcel_id,
          property_address_full: `${tempData.property_address || ''}, ${tempData.city || ''}, ${tempData.state || 'FL'} ${tempData.zip_code || ''}`.trim(),
          property_address_street: tempData.property_address,
          property_address_city: tempData.city,
          property_address_state: tempData.state || 'FL',
          property_address_zip: tempData.zip_code,
          owner_name: tempData.owner_name,
          owner_address: null,
          
          // Values
          assessed_value: tempData.assessed_value,
          taxable_value: tempData.assessed_value,
          market_value: tempData.market_value,
          just_value: tempData.market_value,
          land_value: null,
          building_value: null,
          
          // Building details
          year_built: tempData.year_built,
          eff_year_built: tempData.year_built,
          living_area: tempData.total_sqft,
          lot_size_sqft: tempData.lot_size_sqft,
          bedrooms: tempData.bedrooms,
          bathrooms: tempData.bathrooms,
          units: 1,
          
          // Property classification
          property_use_code: tempData.property_type,
          property_type: tempData.property_type,
          
          // Tax and exemptions
          tax_amount: null,
          homestead_exemption: false,
          other_exemptions: null,
          
          // Sale information
          sale_price: tempData.last_sale_price,
          sale_date: tempData.last_sale_date,
          
          // Additional fields for links
          property_sketch_link: null,
          
          // Land factors if available
          land_factors: null
        }
      }
      
      // Now fetch Sunbiz data with improved matching logic
      let sunbizData: any[] = []
      
      if (bcpaData?.owner_name) {
        const ownerName = bcpaData.owner_name
        console.log('Searching Sunbiz for owner:', ownerName)
        
        // First, check if the owner name looks like a company
        const isCompany = /\b(LLC|INC|CORP|CORPORATION|LP|LLP|PROPERTIES|INVESTMENTS|HOLDINGS|CAPITAL|PARTNERS|GROUP|TRUST)\b/i.test(ownerName)
        
        if (isCompany) {
          // Search for the company directly
          const { data: companyData } = await supabase
            .from('sunbiz_corporate')
            .select('*')
            .or(`corporate_name.ilike.%${ownerName.replace(/[^a-zA-Z0-9\s]/g, '')}%`)
            .limit(10)
          
          if (companyData && companyData.length > 0) {
            console.log(`Found ${companyData.length} matching companies`)
            sunbizData = companyData
          }
        } else {
          // It's an individual - search for them as officers
          const individualNames = extractIndividualNames(ownerName)
          console.log('Extracted individual names:', individualNames)
          
          if (individualNames.length > 0) {
            // Build query to search officers field
            const queries = individualNames.map(name => {
              // Search in officers JSONB field for the name
              return supabase
                .from('sunbiz_corporate')
                .select('*')
                .textSearch('officers', name, { type: 'plain' })
                .limit(5)
            })
            
            // Also try a simpler approach - search for names in the officers field as text
            const alternativeQueries = individualNames.map(name => {
              return supabase
                .from('sunbiz_corporate')
                .select('*')
                .ilike('officers', `%${name}%`)
                .limit(5)
            })
            
            // Execute all queries
            const allQueries = [...queries, ...alternativeQueries]
            const results = await Promise.all(allQueries)
            
            // Combine and deduplicate results
            const allResults: any[] = []
            const seenIds = new Set()
            
            results.forEach(result => {
              if (result.data) {
                result.data.forEach((item: any) => {
                  if (!seenIds.has(item.id)) {
                    seenIds.add(item.id)
                    allResults.push(item)
                  }
                })
              }
            })
            
            if (allResults.length > 0) {
              console.log(`Found ${allResults.length} companies where owner is an officer`)
              sunbizData = allResults
            }
          }
        }
        
        // If still no results, try matching by address
        if (sunbizData.length === 0 && bcpaData.property_address_street) {
          const { data: addressMatches } = await supabase
            .from('sunbiz_corporate')
            .select('*')
            .or(`principal_address.ilike.%${bcpaData.property_address_street}%,mailing_address.ilike.%${bcpaData.property_address_street}%`)
            .limit(5)
          
          if (addressMatches && addressMatches.length > 0) {
            console.log(`Found ${addressMatches.length} companies at property address`)
            sunbizData = addressMatches
          }
        }
      }
      
      let sdfData = sdfResponse.data || []
      const navData = navResponse.data || []
      const tppData = [] // Not queried in this version
      
      // Calculate derived data
      let lastSale = sdfData[0]
      
      // If no SDF data but we have sale info in florida_parcels, use that
      if (sdfData.length === 0 && floridaParcel?.sale_price) {
        // Create a sales record from florida_parcels data
        const saleRecord = {
          sale_date: floridaParcel.sale_date,
          sale_price: String(floridaParcel.sale_price),
          sale_type: floridaParcel.sale_type || floridaParcel.deed_type || 'Warranty Deed',
          qualified_sale: true,
          is_distressed: floridaParcel.is_distressed || false,
          is_bank_sale: floridaParcel.is_bank_sale || false,
          is_cash_sale: false,
          book: floridaParcel.or_book || null,
          page: floridaParcel.or_page || null,
          document_type: floridaParcel.deed_type || 'Warranty Deed',
          grantor_name: null,
          grantee_name: floridaParcel.owner_name || null,
          vi_code: floridaParcel.vi_code || null,
          sale_reason: null,
          book_page: floridaParcel.book_page || floridaParcel.recording_book_page,
          cin: floridaParcel.cin || floridaParcel.clerk_instrument_number,
          record_link: floridaParcel.record_link || 'https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx'
        }
        sdfData = [saleRecord]
        lastSale = saleRecord
      } else if (sdfData.length > 0) {
        lastSale = sdfData[0]
      }
      
      const totalNavAssessment = navData.reduce((sum: number, nav: any) => 
        sum + (parseFloat(nav.total_assessment || nav.assessment_amount) || 0), 0
      )
      const isInCDD = totalNavAssessment > 1000

      // Calculate investment score
      let investmentScore = 50
      if (lastSale?.is_distressed) investmentScore += 15
      if (lastSale?.is_bank_sale) investmentScore += 10
      if (bcpaData?.property_use_code === 'SINGLE FAMILY' || bcpaData?.property_use_code === '001') investmentScore += 5
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

      setData({
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
      })
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

  return {
    data,
    loading,
    error,
    refetch: fetchPropertyData
  }
}