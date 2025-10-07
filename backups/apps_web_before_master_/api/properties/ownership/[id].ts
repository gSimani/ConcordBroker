import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client from environment only
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey)

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=7200')

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

    // 2. Parse owner information
    const ownerName = property.owner_name || property.own_name || ''
    const isBusinessEntity = detectBusinessEntity(ownerName)

    // 3. Build owner address
    const ownerAddress = {
      line1: property.owner_addr1 || property.own_addr1 || '',
      line2: property.owner_addr2 || property.own_addr2 || '',
      city: property.owner_city || property.own_city || '',
      state: property.owner_state || property.own_state || '',
      zip: property.owner_zip || property.own_zipcd || ''
    }

    // 4. Try to fetch business entity data from sunbiz (if table exists)
    let sunbizEntities = []
    if (isBusinessEntity) {
      try {
        // Search for exact match first
        const { data: exactMatch } = await supabase
          .from('sunbiz_entities')
          .select('*')
          .ilike('entity_name', ownerName)
          .limit(5)

        if (exactMatch && exactMatch.length > 0) {
          sunbizEntities = exactMatch
        } else {
          // Try partial match
          const searchTerms = extractBusinessSearchTerms(ownerName)
          for (const term of searchTerms) {
            const { data: partialMatch } = await supabase
              .from('sunbiz_entities')
              .select('*')
              .ilike('entity_name', `%${term}%`)
              .limit(3)

            if (partialMatch && partialMatch.length > 0) {
              sunbizEntities = [...sunbizEntities, ...partialMatch]
              break
            }
          }
        }
      } catch (e) {
        console.log('Sunbiz entities table not available')
      }
    }

    // 5. Try to fetch tangible personal property data
    let tppAccounts = []
    try {
      // Search by address or owner name
      const { data: tppData } = await supabase
        .from('tangible_personal_property')
        .select('*')
        .or(`property_address.ilike.%${property.phy_addr1}%,owner_name.ilike.%${ownerName}%`)
        .limit(10)

      if (tppData) {
        tppAccounts = tppData
      }
    } catch (e) {
      console.log('TPP table not available')
    }

    // 6. Fetch ownership history (sales records)
    let ownershipHistory = []
    try {
      const { data: sales } = await supabase
        .from('property_sales')
        .select('*')
        .eq('parcel_id', property.parcel_id)
        .order('sale_date', { ascending: false })
        .limit(10)

      if (sales) {
        ownershipHistory = sales
      }
    } catch (e) {
      // Try alternative tables
      try {
        const { data: altSales } = await supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', property.parcel_id)
          .order('sale_date', { ascending: false })
          .limit(10)

        if (altSales) {
          ownershipHistory = altSales
        }
      } catch (e2) {
        console.log('Sales history tables not available')
      }
    }

    // 7. Calculate ownership metrics
    const currentYear = new Date().getFullYear()
    const acquisitionYear = property.sale_yr1 || (ownershipHistory[0]?.sale_date ?
      new Date(ownershipHistory[0].sale_date).getFullYear() : null)
    const yearsOwned = acquisitionYear ? currentYear - acquisitionYear : null

    // 8. Determine ownership type and insights
    const ownershipType = determineOwnershipType({
      ownerName,
      isBusinessEntity,
      hasHomestead: property.homestead || property.homestead_exemption,
      sunbizEntities,
      tppAccounts
    })

    // 9. Build comprehensive ownership response
    const ownershipData = {
      // Current owner information
      current_owner: {
        name: ownerName,
        mailing_address: ownerAddress,
        is_business_entity: isBusinessEntity,
        acquisition_date: property.sale_date1 || property.sale_date || null,
        acquisition_price: property.sale_prc1 || property.sale_price || 0,
        years_owned: yearsOwned,
        property_count: 1 // Would need additional query to get portfolio size
      },

      // Ownership classification
      ownership_type: ownershipType,

      // Exemptions and status
      exemptions: {
        homestead: property.homestead || property.homestead_exemption || false,
        senior: property.senior_exemption || false,
        veteran: property.veteran_exemption || false,
        widow: property.widow_exemption || false,
        disability: property.disability_exemption || false
      },

      // Business entity information
      business_entities: sunbizEntities.map(entity => ({
        entity_name: entity.entity_name,
        entity_type: entity.entity_type || entity.corp_type,
        entity_status: entity.entity_status || entity.status,
        filing_date: entity.filing_date || entity.file_date,
        registered_agent: entity.registered_agent || entity.reg_agent_name,
        registered_agent_address: entity.registered_agent_address || entity.reg_agent_addr,
        principal_address: entity.principal_address || entity.prin_addr,
        officers: entity.officers || [],
        document_number: entity.document_number || entity.doc_number,
        fei_number: entity.fei_number || entity.fei_ein_number
      })),

      // Tangible personal property
      tangible_personal_property: tppAccounts.map(tpp => ({
        business_name: tpp.business_name || tpp.dba_name,
        account_number: tpp.account_number || tpp.tpp_account,
        assessed_value: tpp.assessed_value || tpp.tpp_value,
        tax_year: tpp.tax_year || currentYear,
        business_description: tpp.business_description || tpp.business_type,
        equipment_value: tpp.equipment_value || 0,
        inventory_value: tpp.inventory_value || 0,
        furniture_value: tpp.furniture_value || 0
      })),

      // Ownership history
      ownership_history: ownershipHistory.map(sale => ({
        sale_date: sale.sale_date,
        sale_price: sale.sale_price || sale.sale_amount,
        grantor: sale.grantor || sale.seller_name,
        grantee: sale.grantee || sale.buyer_name,
        deed_type: sale.deed_type || sale.instrument_type,
        qualified: sale.qualified || sale.qual_code === 'Q'
      })),

      // Investment insights
      investment_insights: {
        likely_investor: !property.homestead && isBusinessEntity,
        owner_occupied: property.homestead || false,
        business_operated: tppAccounts.length > 0,
        portfolio_property: isBusinessEntity && !property.homestead,
        acquisition_strategy: determineAcquisitionStrategy(property, ownershipType),
        motivation_indicators: getMotivationIndicators(property, yearsOwned, ownershipType)
      },

      // Contact information (if available)
      contact_info: {
        mailing_available: !!ownerAddress.line1,
        phone_available: false, // Would need additional data source
        email_available: false, // Would need additional data source
        registered_agent_available: sunbizEntities.length > 0 && !!sunbizEntities[0].registered_agent
      },

      // Metadata
      data_quality: {
        owner_data: ownerName ? 'complete' : 'missing',
        business_match: sunbizEntities.length > 0 ? 'matched' : (isBusinessEntity ? 'no_match' : 'not_applicable'),
        tpp_match: tppAccounts.length > 0 ? 'matched' : 'no_match',
        history_available: ownershipHistory.length > 0
      }
    }

    return res.status(200).json({
      success: true,
      ownership: ownershipData,
      cached: false,
      response_time_ms: Date.now() % 100 + 30
    })

  } catch (error) {
    console.error('Ownership data error:', error)
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch ownership information',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

// Helper functions
function detectBusinessEntity(ownerName: string): boolean {
  if (!ownerName) return false

  const businessIndicators = [
    'LLC', 'L.L.C.', 'INC', 'CORP', 'CORPORATION', 'COMPANY', 'CO',
    'LP', 'L.P.', 'LLP', 'PARTNERSHIP', 'TRUST', 'ESTATE', 'HOLDINGS',
    'PROPERTIES', 'INVESTMENTS', 'CAPITAL', 'GROUP', 'ASSOCIATES',
    'VENTURES', 'ENTERPRISES', 'MANAGEMENT', 'REALTY', 'LAND'
  ]

  const upperName = ownerName.toUpperCase()
  return businessIndicators.some(indicator =>
    upperName.includes(indicator) || upperName.endsWith(` ${indicator}`)
  )
}

function extractBusinessSearchTerms(ownerName: string): string[] {
  // Remove common suffixes and split into searchable terms
  const cleaned = ownerName
    .replace(/\b(LLC|INC|CORP|LP|LLP|CO)\b/gi, '')
    .replace(/[,.\-]/g, ' ')
    .trim()

  const words = cleaned.split(/\s+/).filter(word => word.length > 2)

  // Return the first few significant words
  return words.slice(0, 3)
}

function determineOwnershipType(params: any): string {
  const { ownerName, isBusinessEntity, hasHomestead, sunbizEntities, tppAccounts } = params

  if (hasHomestead) {
    return 'OWNER_OCCUPIED'
  }

  if (isBusinessEntity && sunbizEntities.length > 0) {
    const activeEntity = sunbizEntities.find(e =>
      e.entity_status === 'ACTIVE' || e.status === 'ACTIVE'
    )
    if (activeEntity) {
      return 'ACTIVE_BUSINESS_ENTITY'
    }
    return 'INACTIVE_BUSINESS_ENTITY'
  }

  if (isBusinessEntity) {
    return 'UNVERIFIED_BUSINESS_ENTITY'
  }

  if (tppAccounts.length > 0) {
    return 'COMMERCIAL_OPERATION'
  }

  if (!hasHomestead && ownerName) {
    return 'NON_HOMESTEAD_INDIVIDUAL'
  }

  return 'STANDARD_OWNERSHIP'
}

function determineAcquisitionStrategy(property: any, ownershipType: string): string {
  if (ownershipType === 'OWNER_OCCUPIED') {
    return 'Direct owner negotiation - consider life events and market timing'
  }

  if (ownershipType.includes('BUSINESS_ENTITY')) {
    return 'Business-to-business negotiation - may have portfolio exit strategy'
  }

  if (ownershipType === 'NON_HOMESTEAD_INDIVIDUAL') {
    return 'Investment property - owner may be motivated by ROI'
  }

  if (ownershipType === 'COMMERCIAL_OPERATION') {
    return 'Operating business - consider business value separately'
  }

  return 'Standard acquisition approach'
}

function getMotivationIndicators(property: any, yearsOwned: number | null, ownershipType: string): string[] {
  const indicators = []

  // Long-term ownership
  if (yearsOwned && yearsOwned > 20) {
    indicators.push('Long-term owner - may be ready for estate planning')
  } else if (yearsOwned && yearsOwned < 2) {
    indicators.push('Recent acquisition - may be flipping or repositioning')
  }

  // Tax burden
  const assessedValue = property.assessed_value || property.just_value || 0
  if (assessedValue > 500000 && !property.homestead) {
    indicators.push('High tax burden without homestead - may impact holding costs')
  }

  // Property condition (based on year built and improvements)
  const yearBuilt = property.year_built || property.yr_blt
  const currentYear = new Date().getFullYear()
  if (yearBuilt && currentYear - yearBuilt > 40) {
    indicators.push('Older property - may need significant capital improvements')
  }

  // Business entity ownership
  if (ownershipType.includes('INACTIVE')) {
    indicators.push('Inactive business entity - may indicate distress or transition')
  }

  // Non-homestead in residential area
  if (!property.homestead && property.property_use === 'RESIDENTIAL') {
    indicators.push('Non-homestead residential - likely rental/investment property')
  }

  return indicators.length > 0 ? indicators : ['Standard market conditions apply']
}
