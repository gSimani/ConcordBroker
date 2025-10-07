import type { VercelRequest, VercelResponse } from '@vercel/node'

// Proxy to production property API - NO MOCK DATA
export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  try {
    // Proxy to production API (real Supabase data only)
    const API_BASE = process.env.PRODUCTION_API_URL || 'http://localhost:8004'
    const queryString = new URLSearchParams(req.query as Record<string, string>).toString()
    const apiUrl = `${API_BASE}/api/properties/search${queryString ? `?${queryString}` : ''}`

    const response = await fetch(apiUrl, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`API responded with status ${response.status}`)
    }

    const data = await response.json()
    return res.status(200).json(data)

  } catch (error) {
    console.error('Production API Error:', error)
    return res.status(500).json({
      error: 'Failed to fetch from production API',
      message: error instanceof Error ? error.message : 'Unknown error',
      properties: [],
      total_found: 0
    })
  }
}