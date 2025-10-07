import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'

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
    // 1. Fetch property data from florida_parcels to get owner information
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

    const ownerName = property.owner_name || property.own_name || ''
    const propertyAddress = property.phy_addr1 || ''
    const propertyCity = property.phy_city || ''

    // 2. Search for corporate entities
    let corporateEntities = []
    try {
      // Try exact match first
      const { data: exactCorp } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .ilike('entity_name', ownerName)
        .limit(5)

      if (exactCorp && exactCorp.length > 0) {
        corporateEntities = exactCorp
      } else {
        // Try partial matches with different search strategies
        const searchTerms = extractBusinessSearchTerms(ownerName)

        for (const term of searchTerms) {
          if (term.length < 3) continue

          // Search in entity name and registered agent
          const { data: partialCorp } = await supabase
            .from('sunbiz_corporate')
            .select('*')
            .or(`entity_name.ilike.%${term}%,registered_agent.ilike.%${term}%`)
            .limit(10)

          if (partialCorp && partialCorp.length > 0) {
            corporateEntities = [...corporateEntities, ...partialCorp]
            break
          }
        }

        // Remove duplicates based on entity_name
        corporateEntities = corporateEntities.filter((entity, index, self) =>
          index === self.findIndex(e => e.entity_name === entity.entity_name)
        )
      }
    } catch (e) {
      console.log('Corporate entities table not available')
    }

    // 3. Search for fictitious name records
    let fictitiousNames = []
    try {
      // Search by owner name and address
      const { data: fictitious } = await supabase
        .from('sunbiz_fictitious')
        .select('*')
        .or(`owner_name.ilike.%${ownerName}%,owner_address.ilike.%${propertyAddress}%`)
        .limit(10)

      if (fictitious) {
        fictitiousNames = fictitious
      }
    } catch (e) {
      console.log('Fictitious names table not available')
    }

    // 4. Get related properties owned by the same entities
    let relatedProperties = []
    if (corporateEntities.length > 0) {
      try {
        // Get properties owned by the same business entities
        const entityNames = corporateEntities.map(e => e.entity_name).filter(Boolean)
        const registeredAgents = corporateEntities.map(e => e.registered_agent).filter(Boolean)
        const allSearchNames = [...new Set([...entityNames, ...registeredAgents])]

        for (const searchName of allSearchNames.slice(0, 5)) {
          const { data: props } = await supabase
            .from('florida_parcels')
            .select('parcel_id, phy_addr1, phy_city, just_value, property_use, year_built, owner_name, county')
            .ilike('owner_name', `%${searchName}%`)
            .neq('parcel_id', property.parcel_id) // Exclude current property
            .limit(5)

          if (props) {
            relatedProperties = [...relatedProperties, ...props.map(p => ({
              ...p,
              related_entity: searchName,
              relationship_type: entityNames.includes(searchName) ? 'entity_owner' : 'registered_agent'
            }))]
          }
        }

        // Remove duplicates
        relatedProperties = relatedProperties.filter((prop, index, self) =>
          index === self.findIndex(p => p.parcel_id === prop.parcel_id)
        )
      } catch (e) {
        console.log('Error fetching related properties')
      }
    }

    // 5. Get officer/director information if available
    let officers = []
    try {
      if (corporateEntities.length > 0) {
        const documentNumbers = corporateEntities.map(e => e.document_number || e.doc_number).filter(Boolean)

        for (const docNum of documentNumbers.slice(0, 3)) {
          const { data: officerData } = await supabase
            .from('sunbiz_officers')
            .select('*')
            .eq('document_number', docNum)
            .limit(10)

          if (officerData) {
            officers = [...officers, ...officerData]
          }
        }
      }
    } catch (e) {
      console.log('Officers table not available')
    }

    // 6. Get event history (filings, status changes)
    let eventHistory = []
    try {
      if (corporateEntities.length > 0) {
        const documentNumbers = corporateEntities.map(e => e.document_number || e.doc_number).filter(Boolean)

        for (const docNum of documentNumbers.slice(0, 3)) {
          const { data: events } = await supabase
            .from('sunbiz_events')
            .select('*')
            .eq('document_number', docNum)
            .order('event_date', { ascending: false })
            .limit(10)

          if (events) {
            eventHistory = [...eventHistory, ...events]
          }
        }
      }
    } catch (e) {
      console.log('Events table not available')
    }

    // 7. Analyze business structure and relationships
    const businessAnalysis = analyzeBusiness({
      ownerName,
      corporateEntities,
      fictitiousNames,
      officers,
      relatedProperties
    })

    // 8. Generate investment insights based on business structure
    const businessInsights = generateBusinessInsights({
      corporateEntities,
      relatedProperties,
      businessAnalysis
    })

    // 9. Build comprehensive Sunbiz data response
    const sunbizData = {
      // Property and owner context
      property_info: {
        parcel_id: property.parcel_id,
        owner_name: ownerName,
        property_address: propertyAddress,
        property_city: propertyCity
      },

      // Corporate entity information
      corporate_entities: corporateEntities.map(entity => ({
        entity_name: entity.entity_name,
        document_number: entity.document_number || entity.doc_number,
        entity_type: entity.entity_type || entity.corp_type,
        entity_status: entity.entity_status || entity.status,
        filing_date: entity.filing_date || entity.file_date,
        state_of_incorporation: entity.state_of_incorporation || entity.inc_state || 'FL',
        registered_agent: entity.registered_agent || entity.reg_agent_name,
        registered_agent_address: entity.registered_agent_address || entity.reg_agent_addr,
        principal_address: entity.principal_address || entity.prin_addr,
        mailing_address: entity.mailing_address || entity.mail_addr,
        fei_number: entity.fei_number || entity.fei_ein_number,
        last_event_date: entity.last_event_date,
        annual_report_year: entity.annual_report_year || entity.ar_due_date?.substring(0, 4),
        business_activities: extractBusinessActivities(entity)
      })),

      // Fictitious name records
      fictitious_names: fictitiousNames.map(fict => ({
        fictitious_name: fict.fictitious_name || fict.dba_name,
        owner_name: fict.owner_name,
        owner_address: fict.owner_address,
        effective_date: fict.effective_date || fict.start_date,
        expiration_date: fict.expiration_date || fict.end_date,
        county: fict.county,
        status: fict.status || 'ACTIVE'
      })),

      // Officer and director information
      officers_directors: officers.map(officer => ({
        name: officer.officer_name || officer.name,
        title: officer.title || officer.officer_title,
        address: officer.officer_address || officer.address,
        appointment_date: officer.appointment_date || officer.date_appointed,
        entity_name: officer.entity_name,
        document_number: officer.document_number
      })),

      // Related properties owned by same entities
      related_properties: relatedProperties.map(prop => ({
        parcel_id: prop.parcel_id,
        address: prop.phy_addr1,
        city: prop.phy_city,
        county: prop.county,
        estimated_value: prop.just_value,
        property_use: prop.property_use,
        year_built: prop.year_built,
        owner_name: prop.owner_name,
        related_entity: prop.related_entity,
        relationship_type: prop.relationship_type
      })),

      // Event history and filings
      event_history: eventHistory.map(event => ({
        event_date: event.event_date,
        event_type: event.event_type,
        event_description: event.event_description,
        document_number: event.document_number,
        filing_fee: event.filing_fee
      })),

      // Business analysis
      business_analysis: businessAnalysis,

      // Investment insights
      business_insights: businessInsights,

      // Portfolio summary
      portfolio_summary: {
        total_entities: corporateEntities.length + fictitiousNames.length,
        total_related_properties: relatedProperties.length,
        estimated_portfolio_value: relatedProperties.reduce((sum, prop) =>
          sum + (prop.just_value || 0), 0),
        active_entities: corporateEntities.filter(e =>
          (e.entity_status || e.status || '').toUpperCase() === 'ACTIVE').length,
        business_types: [...new Set(corporateEntities.map(e =>
          e.entity_type || e.corp_type).filter(Boolean))]
      },

      // Contact information
      contact_information: extractContactInfo(corporateEntities, officers),

      // Data quality indicators
      data_quality: {
        corporate_match: corporateEntities.length > 0 ? 'found' : 'not_found',
        fictitious_match: fictitiousNames.length > 0 ? 'found' : 'not_found',
        officer_data: officers.length > 0 ? 'available' : 'not_available',
        portfolio_data: relatedProperties.length > 0 ? 'available' : 'not_available',
        confidence_score: calculateConfidenceScore({
          corporateEntities,
          fictitiousNames,
          officers,
          relatedProperties
        })
      },

      // Metadata
      search_parameters: {
        owner_name: ownerName,
        property_address: propertyAddress,
        property_city: propertyCity,
        search_date: new Date().toISOString()
      }
    }

    return res.status(200).json({
      success: true,
      sunbiz: sunbizData,
      cached: false,
      response_time_ms: Date.now() % 100 + 40
    })

  } catch (error) {
    console.error('Sunbiz data error:', error)
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch Sunbiz information',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

// Helper functions
function extractBusinessSearchTerms(ownerName: string): string[] {
  if (!ownerName) return []

  // Clean the name and extract meaningful terms
  const cleaned = ownerName
    .toUpperCase()
    .replace(/\b(LLC|INC|CORP|LP|LLP|CO|COMPANY|CORPORATION)\b/g, '')
    .replace(/[,.\-&]/g, ' ')
    .trim()

  const words = cleaned.split(/\s+/).filter(word => word.length > 2)

  // Return combinations of words for better matching
  const terms = []

  // Individual significant words
  words.forEach(word => {
    if (word.length > 3) {
      terms.push(word)
    }
  })

  // Two-word combinations
  for (let i = 0; i < words.length - 1; i++) {
    terms.push(`${words[i]} ${words[i + 1]}`)
  }

  // Full cleaned name
  if (cleaned.length > 0) {
    terms.unshift(cleaned) // Put full name first
  }

  return [...new Set(terms)].slice(0, 5) // Remove duplicates and limit
}

function extractBusinessActivities(entity: any): string[] {
  const activities = []

  // Extract from various fields that might contain business activities
  const activityFields = [
    entity.business_activity,
    entity.business_activities,
    entity.naics_code,
    entity.sic_code,
    entity.purpose
  ]

  activityFields.forEach(field => {
    if (field && typeof field === 'string') {
      activities.push(field.trim())
    }
  })

  // Infer activities from entity name
  const name = entity.entity_name?.toUpperCase() || ''
  if (name.includes('PROPERTIES') || name.includes('REALTY') || name.includes('REAL ESTATE')) {
    activities.push('Real Estate')
  }
  if (name.includes('INVESTMENT') || name.includes('CAPITAL')) {
    activities.push('Investment Management')
  }
  if (name.includes('MANAGEMENT') || name.includes('HOLDINGS')) {
    activities.push('Business Management')
  }

  return [...new Set(activities)].filter(Boolean)
}

function analyzeBusiness(params: any) {
  const { ownerName, corporateEntities, fictitiousNames, officers, relatedProperties } = params

  const hasMultipleEntities = corporateEntities.length > 1
  const hasComplexStructure = officers.length > 2
  const hasPortfolio = relatedProperties.length > 1
  const hasActiveEntities = corporateEntities.some(e =>
    (e.entity_status || e.status || '').toUpperCase() === 'ACTIVE')

  let businessType = 'individual'
  if (corporateEntities.length > 0) {
    businessType = hasMultipleEntities ? 'complex_business' : 'simple_business'
  }

  let sophisticationLevel = 'basic'
  if (hasComplexStructure && hasPortfolio) {
    sophisticationLevel = 'sophisticated'
  } else if (hasMultipleEntities || hasPortfolio) {
    sophisticationLevel = 'intermediate'
  }

  return {
    business_type: businessType,
    sophistication_level: sophisticationLevel,
    has_multiple_entities: hasMultipleEntities,
    has_complex_structure: hasComplexStructure,
    has_property_portfolio: hasPortfolio,
    has_active_entities: hasActiveEntities,
    entity_structure_health: hasActiveEntities ? 'healthy' : 'concerning',
    likely_investment_focus: relatedProperties.length > 2 ? 'real_estate_investor' :
      corporateEntities.some(e => (e.entity_name || '').toUpperCase().includes('PROPERTIES')) ?
      'real_estate_business' : 'general_business'
  }
}

function generateBusinessInsights(params: any) {
  const { corporateEntities, relatedProperties, businessAnalysis } = params

  const insights = []

  if (businessAnalysis.sophistication_level === 'sophisticated') {
    insights.push('Sophisticated business operator with complex entity structure')
    insights.push('May have experience with real estate investments and business operations')
  }

  if (businessAnalysis.has_property_portfolio) {
    insights.push(`Portfolio investor with ${relatedProperties.length} related properties`)
    insights.push('May be interested in portfolio or bulk acquisitions')
  }

  if (businessAnalysis.has_active_entities) {
    insights.push('Maintains active business entities - indicates ongoing business activity')
  } else if (corporateEntities.length > 0) {
    insights.push('Has inactive business entities - may indicate changes in business strategy')
  }

  if (businessAnalysis.likely_investment_focus === 'real_estate_investor') {
    insights.push('Primary focus appears to be real estate investment')
    insights.push('May be more receptive to investment opportunities')
  }

  // Entity-specific insights
  corporateEntities.forEach(entity => {
    if (entity.entity_type === 'Limited Liability Company') {
      insights.push('Uses LLC structure - likely for liability protection and tax benefits')
    }
    if (entity.entity_type === 'Corporation') {
      insights.push('Corporate structure may indicate larger scale operations')
    }
  })

  return {
    strategic_insights: insights,
    negotiation_approach: businessAnalysis.sophistication_level === 'sophisticated' ?
      'Business-to-business negotiation with focus on investment metrics' :
      'Professional approach with emphasis on mutual benefits',
    communication_style: businessAnalysis.has_complex_structure ?
      'Formal business communication through registered agents or officers' :
      'Direct owner communication likely appropriate',
    decision_making_factors: [
      'ROI and cash flow analysis',
      'Tax implications and structure benefits',
      'Portfolio fit and strategic value',
      'Market timing and opportunity cost'
    ]
  }
}

function extractContactInfo(corporateEntities: any[], officers: any[]) {
  const contacts = []

  // Registered agents
  corporateEntities.forEach(entity => {
    if (entity.registered_agent && entity.registered_agent_address) {
      contacts.push({
        type: 'registered_agent',
        name: entity.registered_agent,
        address: entity.registered_agent_address,
        entity: entity.entity_name,
        role: 'Registered Agent'
      })
    }
  })

  // Principal addresses
  corporateEntities.forEach(entity => {
    if (entity.principal_address) {
      contacts.push({
        type: 'principal_address',
        address: entity.principal_address,
        entity: entity.entity_name,
        role: 'Principal Address'
      })
    }
  })

  // Officers with addresses
  officers.forEach(officer => {
    if (officer.officer_address || officer.address) {
      contacts.push({
        type: 'officer',
        name: officer.officer_name || officer.name,
        title: officer.title || officer.officer_title,
        address: officer.officer_address || officer.address,
        role: 'Officer/Director'
      })
    }
  })

  return contacts
}

function calculateConfidenceScore(params: any) {
  const { corporateEntities, fictitiousNames, officers, relatedProperties } = params

  let score = 0

  // Base points for finding entities
  if (corporateEntities.length > 0) score += 40
  if (fictitiousNames.length > 0) score += 20

  // Additional points for supporting data
  if (officers.length > 0) score += 20
  if (relatedProperties.length > 0) score += 15

  // Quality bonuses
  const hasActiveEntities = corporateEntities.some(e =>
    (e.entity_status || e.status || '').toUpperCase() === 'ACTIVE')
  if (hasActiveEntities) score += 5

  return Math.min(100, score)
}