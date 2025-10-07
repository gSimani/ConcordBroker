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
    // Proxy to production API ONLY - NO FALLBACK MOCK DATA
    const productionUrl = process.env.PRODUCTION_API_URL || 'http://localhost:8004'
    const apiUrl = `${productionUrl}/api/autocomplete?q=${encodeURIComponent(q)}&limit=${limit}`

    const response = await fetch(apiUrl)
    if (!response.ok) {
      throw new Error(`Production API responded with status ${response.status}`)
    }

    const data = await response.json()
    return res.status(200).json(data)

  } catch (error) {
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      data: []
    })
  }
}