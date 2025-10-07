import type { VercelRequest, VercelResponse } from '@vercel/node'

const DEFAULT_UPSTREAM = process.env.PROPERTY_API_UPSTREAM_URL || 'http://localhost:8001'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    const { id } = req.query
    const parcelId = Array.isArray(id) ? id[0] : id
    if (!parcelId) {
      return res.status(400).json({ success: false, error: 'missing_id' })
    }

    const upstreamBase = DEFAULT_UPSTREAM.replace(/\/$/, '')
    const upstreamUrl = `${upstreamBase}/api/properties/${encodeURIComponent(parcelId)}`

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

