// Vercel serverless proxy for Autocomplete (production)
// Proxies /api/autocomplete-ultra to upstream /api/autocomplete/combined

import type { VercelRequest, VercelResponse } from '@vercel/node'

const DEFAULT_UPSTREAM = process.env.AUTOCOMPLETE_UPSTREAM_URL || 'http://localhost:8003'

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    // CORS preflight (optional safety)
    if (req.method === 'OPTIONS') {
      res.setHeader('Access-Control-Allow-Origin', '*')
      res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS')
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
      return res.status(200).end()
    }

    const upstreamBase = DEFAULT_UPSTREAM.replace(/\/$/, '')

    // Health passthrough: /api/autocomplete-ultra/health
    if (req.url && req.url.endsWith('/health')) {
      const upstreamHealth = `${upstreamBase}/health`
      const r = await fetch(upstreamHealth)
      const text = await r.text()
      res.setHeader('Access-Control-Allow-Origin', '*')
      return res.status(r.status).send(text)
    }

    // Combined suggestions
    const q = (req.query.q as string) || ''
    const limit = (req.query.limit as string) || '20'
    const url = `${upstreamBase}/api/autocomplete/combined?q=${encodeURIComponent(q)}&limit=${encodeURIComponent(limit)}`

    const upstreamRes = await fetch(url, {
      headers: { 'Accept': 'application/json' },
    })

    const contentType = upstreamRes.headers.get('content-type') || 'application/json'
    res.setHeader('Content-Type', contentType)
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Cache-Control', 'public, max-age=30, s-maxage=60')

    if (!upstreamRes.ok) {
      const errText = await upstreamRes.text()
      return res.status(upstreamRes.status).send(errText)
    }

    const data = await upstreamRes.text()
    return res.status(200).send(data)
  } catch (e: any) {
    return res.status(502).json({ success: false, error: e?.message || 'proxy_error' })
  }
}

