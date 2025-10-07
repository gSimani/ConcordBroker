import type { VercelRequest, VercelResponse } from '@vercel/node'

const DEFAULT_UPSTREAM = process.env.PROPERTY_API_UPSTREAM_URL || 'http://localhost:8001'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    if (req.method === 'OPTIONS') {
      res.setHeader('Access-Control-Allow-Origin', '*')
      res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS')
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
      return res.status(200).end()
    }

    const upstreamBase = DEFAULT_UPSTREAM.replace(/\/$/, '')
    const qs = req.url?.split('?')[1] || ''
    const upstreamUrl = `${upstreamBase}/api/properties/search${qs ? `?${qs}` : ''}`

    const upstreamRes = await fetch(upstreamUrl, {
      headers: { 'Accept': 'application/json' },
    })

    const contentType = upstreamRes.headers.get('content-type') || 'application/json'
    res.setHeader('Content-Type', contentType)
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Cache-Control', 'public, max-age=15, s-maxage=30')

    const body = await upstreamRes.text()
    return res.status(upstreamRes.status).send(body)
  } catch (e: any) {
    return res.status(502).json({ success: false, error: e?.message || 'proxy_error' })
  }
}

