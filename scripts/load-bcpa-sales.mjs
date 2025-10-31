#!/usr/bin/env node
// Load BCPA sales CSV into Supabase property_sales_history
import 'dotenv/config'
// Usage: node scripts/load-bcpa-sales.mjs --file path/to/bcpa_sales.csv --county BROWARD

import { createClient } from '@supabase/supabase-js'
import fs from 'fs'
import path from 'path'
import { parse } from 'csv-parse/sync'

function log(msg, ...rest) { console.log(`[bcpa-loader] ${msg}`, ...rest) }
function warn(msg, ...rest) { console.warn(`[bcpa-loader] ${msg}`, ...rest) }

function getArg(name, def = undefined) {
  const idx = process.argv.indexOf(`--${name}`)
  if (idx !== -1 && idx + 1 < process.argv.length) return process.argv[idx + 1]
  return def
}

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.VITE_SUPABASE_URL
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('[bcpa-loader] Missing SUPABASE_URL or SUPABASE_SERVICE_KEY env vars')
  process.exit(1)
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

const file = getArg('file')
const county = (getArg('county', 'BROWARD') || '').toUpperCase()
if (!file) {
  console.error('Usage: node scripts/load-bcpa-sales.mjs --file path/to/bcpa_sales.csv [--county BROWARD]')
  process.exit(1)
}

function formatBrowardFolioVariants(folio) {
  const raw = (folio || '').replace(/\D/g, '')
  if (!raw) return []
  const dashed = raw.length === 12 ? `${raw.slice(0,4)}-${raw.slice(4,6)}-${raw.slice(6,8)}-${raw.slice(8)}` : null
  const spaced = raw.length === 12 ? `${raw.slice(0,4)} ${raw.slice(4,6)} ${raw.slice(6,8)} ${raw.slice(8)}` : null
  return [raw, dashed, spaced].filter(Boolean)
}

async function resolveParcelId(folioOrParcel) {
  const candidates = formatBrowardFolioVariants(folioOrParcel)
  for (const candidate of candidates) {
    const { data, error } = await supabase
      .from('florida_parcels')
      .select('parcel_id')
      .eq('county', county)
      .eq('parcel_id', candidate)
      .limit(1)
    if (!error && data && data.length > 0) return data[0].parcel_id
  }
  return folioOrParcel
}

async function recordExists(parcel_id, sale_date, sale_price) {
  const { data, error } = await supabase
    .from('property_sales_history')
    .select('parcel_id')
    .eq('parcel_id', parcel_id)
    .eq('sale_date', sale_date)
    .eq('sale_price', sale_price)
    .limit(1)
  if (error) return false
  return data && data.length > 0
}

function toISODate(input) {
  if (!input) return null
  const d = new Date(input)
  if (Number.isNaN(d.getTime())) return null
  return d.toISOString()
}

async function run() {
  log(`Loading CSV: ${file} (county=${county})`)
  const abs = path.resolve(process.cwd(), file)
  if (!fs.existsSync(abs)) {
    console.error(`[bcpa-loader] File not found: ${abs}`)
    process.exit(1)
  }
  const content = fs.readFileSync(abs, 'utf8')
  const rows = parse(content, { columns: true, skip_empty_lines: true, trim: true })
  log(`Parsed ${rows.length} rows`)

  let inserted = 0, skipped = 0, failed = 0

  for (const row of rows) {
    try {
      const folio = row.folio || row.parcel_id || row.FOLIO
      const parcel_id = await resolveParcelId(folio)
      const sale_price = row.sale_price ? Number(String(row.sale_price).replace(/[$,]/g, '')) : 0
      const sale_date_raw = row.sale_date || row.date || row.SALE_DATE
      const sale_date_iso = toISODate(sale_date_raw)
      const quality_code = (row.quality_code || row.type || row.qualified || '').toString().toUpperCase().startsWith('Q') ? 'Q' : (row.quality_code || '').toUpperCase() || null
      const or_book = row.or_book || row.book || null
      const or_page = row.or_page || row.page || null
      const clerk_no = row.clerk_no || row.doc_no || row.document_number || row.cin || null

      if (!parcel_id || !sale_date_iso || !(sale_price > 0)) {
        warn('Skipping row (missing key fields):', { folio, sale_date_raw, sale_price })
        skipped++
        continue
      }

      if (await recordExists(parcel_id, sale_date_iso, sale_price)) {
        skipped++
        continue
      }

      const d = new Date(sale_date_iso)
      const sale_year = d.getUTCFullYear()
      const sale_month = d.getUTCMonth() + 1

      // County number mapping (Broward = 06)
      const county_no = county === 'BROWARD' ? '06' : '06'

      const payload = {
        county_no,
        parcel_id,
        sale_date: sale_date_iso,
        sale_price,
        sale_year,
        sale_month,
        quality_code,
        or_book,
        or_page,
        clerk_no,
        county,
        assessment_year: 2025  // Default assessment year
      }

      const { error: insertError } = await supabase.from('property_sales_history').insert(payload)
      if (insertError) {
        failed++
        warn('Insert failed:', insertError.message || insertError)
      } else {
        inserted++
      }
    } catch (e) {
      failed++
      warn('Row failed:', e?.message || e)
    }
  }

  log(`Done. Inserted=${inserted}, Skipped=${skipped}, Failed=${failed}`)
}

run().catch(err => {
  console.error('[bcpa-loader] Fatal error:', err)
  process.exit(1)
})
