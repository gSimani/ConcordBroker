import type { VercelRequest, VercelResponse } from '@vercel/node'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  const { q, limit = 10 } = req.query

  if (!q || typeof q !== 'string') {
    return res.status(400).json({ success: false, error: 'Query parameter required', data: [] })
  }

  try {
    // Mock AI-enhanced autocomplete data with business entities
    const query = q.toLowerCase()
    const mockSuggestions = []

    if (query.includes('llc') || query.includes('florida') || query.includes('holdings')) {
      mockSuggestions.push({
        full_address: "123 MAIN ST",
        city: "MIAMI",
        zip_code: "33101",
        owner_name: "FLORIDA HOLDINGS LLC",
        property_type: "RESIDENTIAL",
        business_entity: {
          name: "FLORIDA HOLDINGS LLC",
          status: "ACTIVE",
          type: "LLC",
          confidence: 0.95,
          ai_reasoning: "Exact business entity match found"
        }
      })
    }

    if (query.includes('miami') || query.includes('3390')) {
      mockSuggestions.push({
        full_address: "456 OCEAN BLVD",
        city: "MIAMI BEACH",
        zip_code: "33139",
        owner_name: "BEACHFRONT PROPERTIES LLC",
        property_type: "COMMERCIAL",
        business_entity: {
          name: "BEACHFRONT PROPERTIES LLC",
          status: "ACTIVE",
          type: "LLC",
          confidence: 0.88,
          ai_reasoning: "Geographic context and business type alignment"
        }
      })
    }

    if (query.includes('3930') || query.includes('davie')) {
      mockSuggestions.push({
        full_address: "3930 SW 53RD AVE",
        city: "DAVIE",
        zip_code: "33314",
        owner_name: "RESIDENTIAL TRUST LLC",
        property_type: "RESIDENTIAL",
        business_entity: {
          name: "RESIDENTIAL TRUST LLC",
          status: "ACTIVE",
          type: "LLC",
          confidence: 0.92,
          ai_reasoning: "Address pattern match with entity expansion"
        }
      })
    }

    if (query.includes('tower') || query.includes('corporate')) {
      mockSuggestions.push({
        full_address: "789 BISCAYNE BLVD",
        city: "MIAMI",
        zip_code: "33132",
        owner_name: "MIAMI TOWER LLC",
        property_type: "COMMERCIAL",
        business_entity: {
          name: "MIAMI TOWER LLC",
          status: "ACTIVE",
          type: "LLC",
          confidence: 0.91,
          ai_reasoning: "Semantic name expansion: TOWER → CORPORATE"
        }
      })
    }

    return res.status(200).json({
      success: true,
      data: mockSuggestions.slice(0, parseInt(limit as string)),
      ai_enhanced: true,
      cached: true,
      response_time_ms: 15
    })

  } catch (error) {
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      data: []
    })
  }
}