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
    const query = q.toLowerCase()
    const mockOwners = []

    if (query.includes('llc') || query.includes('florida') || query.includes('holdings')) {
      mockOwners.push({
        owner_name: "FLORIDA HOLDINGS LLC",
        city: "MIAMI",
        county: "DADE",
        business_entity: {
          name: "FLORIDA HOLDINGS LLC",
          status: "ACTIVE",
          type: "LLC",
          confidence: 0.98
        }
      })
    }

    if (query.includes('beachfront') || query.includes('properties')) {
      mockOwners.push({
        owner_name: "BEACHFRONT PROPERTIES LLC",
        city: "MIAMI BEACH",
        county: "DADE",
        business_entity: {
          name: "BEACHFRONT PROPERTIES LLC",
          status: "ACTIVE",
          type: "LLC",
          confidence: 0.94
        }
      })
    }

    if (query.includes('miami') || query.includes('tower')) {
      mockOwners.push({
        owner_name: "MIAMI TOWER LLC",
        city: "MIAMI",
        county: "DADE",
        business_entity: {
          name: "MIAMI TOWER LLC",
          status: "ACTIVE",
          type: "LLC",
          confidence: 0.92
        }
      })
    }

    return res.status(200).json({
      success: true,
      data: mockOwners.slice(0, parseInt(limit as string))
    })

  } catch (error) {
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      data: []
    })
  }
}