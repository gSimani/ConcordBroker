import React, { useEffect, useState } from 'react'

type Check = {
  name: string
  url: string
  status: 'pending' | 'ok' | 'fail'
  code?: number
  message?: string
  durationMs?: number
}

function makeChecks(parcelId: string): Check[] {
  return [
    { name: 'Health', url: 'http://localhost:8001/health', status: 'pending' },
    { name: 'Search', url: 'http://localhost:8001/api/properties/search?limit=1', status: 'pending' },
    { name: 'Autocomplete 8003 (combined)', url: 'http://localhost:8003/api/autocomplete/combined?q=test&limit=1', status: 'pending' },
    { name: 'Autocomplete 8003 (health)', url: 'http://localhost:8003/health', status: 'pending' },
    { name: 'Property Detail', url: `http://localhost:8001/api/properties/${encodeURIComponent(parcelId)}`, status: 'pending' },
    { name: 'Sales History', url: `http://localhost:8001/api/properties/${encodeURIComponent(parcelId)}/sales-history`, status: 'pending' },
  ]
}

export default function DiagnosticsProperties() {
  const [parcelId, setParcelId] = useState<string>('514124070600')
  const [checks, setChecks] = useState<Check[]>(makeChecks('514124070600'))
  const [running, setRunning] = useState(false)
  const [thresholdMs, setThresholdMs] = useState<number>(500)

  const runChecks = async () => {
    setRunning(true)
    const results: Check[] = []
    for (const c of makeChecks(parcelId)) {
      try {
        const controller = new AbortController()
        const id = setTimeout(() => controller.abort(), 8000)
        const t0 = performance.now()
        const res = await fetch(c.url, { signal: controller.signal })
        const t1 = performance.now()
        clearTimeout(id)
        if (res.ok) {
          results.push({ ...c, status: 'ok', code: res.status, durationMs: Math.round(t1 - t0) })
        } else {
          results.push({ ...c, status: 'fail', code: res.status, message: res.statusText, durationMs: Math.round(t1 - t0) })
        }
      } catch (e: any) {
        results.push({ ...c, status: 'fail', message: e?.message })
      }
    }
    setChecks(results)
    setRunning(false)
  }

  useEffect(() => {
    runChecks()
  }, [])

  const ok = checks.every(c => c.status === 'ok')

  return (
    <div className="container mx-auto p-6 max-w-3xl">
      <h1 className="text-2xl font-bold mb-2">Property Search Diagnostics</h1>
      <p className="text-sm text-gray-600 mb-6">Verifies backend endpoints required by /properties.</p>

      <div className="mb-4 flex items-center gap-3 flex-wrap">
        <label className="text-sm text-gray-700">Parcel ID:</label>
        <input
          className="border rounded px-2 py-1 text-sm"
          value={parcelId}
          onChange={e => setParcelId(e.target.value)}
          placeholder="Enter parcel id"
          style={{ minWidth: '220px' }}
        />
        <label className="text-sm text-gray-700">Slow threshold (ms):</label>
        <input
          type="number"
          min={0}
          className="border rounded px-2 py-1 text-sm w-24"
          value={thresholdMs}
          onChange={e => setThresholdMs(parseInt(e.target.value || '0', 10))}
        />
        <button
          className={`px-3 py-1.5 rounded text-sm font-medium ${running ? 'bg-gray-200 text-gray-500' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
          onClick={runChecks}
          disabled={running}
        >
          {running ? 'Running…' : 'Re-run Checks'}
        </button>
        <button
          className="px-3 py-1.5 rounded text-sm font-medium bg-gray-100 text-gray-800 hover:bg-gray-200 border"
          onClick={() => {
            const headers = ['name','url','status','code','message','durationMs']
            const rows = checks.map(c => [
              c.name,
              c.url,
              c.status,
              c.code ?? '',
              (c.message ?? '').replaceAll(',', ';'),
              c.durationMs ?? ''
            ])
            const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `diagnostics_properties_${new Date().toISOString().replace(/[:.]/g,'-')}.csv`
            a.click()
            URL.revokeObjectURL(url)
          }}
        >
          Export CSV
        </button>
      </div>

      <div className="space-y-2">
        {checks.map((c, i) => (
          <div key={i} className="flex items-center justify-between p-3 rounded border bg-white">
            <div>
              <div className="font-medium">{c.name}</div>
              <div className="text-xs text-gray-600">{c.url}</div>
            </div>
            <div className="text-sm font-semibold text-right">
              {c.status === 'pending' && <span className="text-gray-500">…</span>}
              {c.status === 'ok' && (
                <span className={
                  c.durationMs && c.durationMs > thresholdMs ? 'text-yellow-700' : 'text-green-600'
                }>
                  {c.durationMs && c.durationMs > thresholdMs ? 'SLOW' : 'OK'} {c.code ? `(${c.code})` : ''}{typeof c.durationMs === 'number' ? ` • ${c.durationMs} ms` : ''}
                </span>
              )}
              {c.status === 'fail' && (
                <span className="text-red-600">FAIL {c.code ? `(${c.code})` : ''}{c.message ? ` – ${c.message}` : ''}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 rounded border bg-gray-50">
        <div className="text-sm">
          Overall Status: {ok ? (
            <span className="text-green-700 font-semibold">Ready</span>
          ) : (
            <span className="text-red-700 font-semibold">Issues Detected</span>
          )}
        </div>
      </div>
    </div>
  )
}
