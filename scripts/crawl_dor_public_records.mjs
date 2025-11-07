#!/usr/bin/env node
// Crawl the Florida DOR SharePoint Public Records subtree and emit a manifest of files.
// Filters to datasets NAL/NAP/SDF and includes year/county guesses from filename/path.

import fs from 'fs'
import path from 'path'

const BASE_WEB = process.env.SP_BASE_WEB || 'https://floridarevenue.com/property/dataportal'
const START_SERVER_REL = process.env.SP_START_FOLDER || '/property/dataportal/Documents/PTO Data Portal/~Public Records'
const OUT_PATH = process.env.DOR_MANIFEST_OUT || 'data/manifests/dor_public_records_manifest.json'
const MAX_DEPTH = Number(process.env.SP_MAX_DEPTH || 8)

async function spGet(url) {
  const res = await fetch(url, { headers: { 'Accept': 'application/json;odata=nometadata' } })
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`)
  return res.json()
}

function toApiUrlFoldersByPath(serverRel) {
  const enc = encodeURIComponent(serverRel)
  return `${BASE_WEB}/_api/web/GetFolderByServerRelativePath(decodedurl='${enc}')/Folders`
}
function toApiUrlFilesByPath(serverRel) {
  const enc = encodeURIComponent(serverRel)
  return `${BASE_WEB}/_api/web/GetFolderByServerRelativePath(decodedurl='${enc}')/Files`
}
function absUrl(serverRel) {
  try { return new URL(serverRel, BASE_WEB).href } catch { return `${BASE_WEB}${serverRel}` }
}

async function listFiles(serverRel) {
  try {
    const data = await spGet(toApiUrlFilesByPath(serverRel))
    return data.value || []
  } catch { return [] }
}
async function listFolders(serverRel) {
  try {
    const data = await spGet(toApiUrlFoldersByPath(serverRel))
    return data.value || []
  } catch { return [] }
}

function classify(url) {
  const decoded = decodeURIComponent(url)
  const parts = decoded.split('/')
  const name = parts[parts.length - 1]
  const datasetMatch = decoded.match(/\b(NAL|SDF|NAP)\b/i)
  const dataset = datasetMatch ? datasetMatch[1].toUpperCase() : undefined
  const yearMatch = decoded.match(/\b(20\d{2})\b/)
  const year = yearMatch ? yearMatch[1] : undefined
  let county
  for (const seg of parts) {
    const s = seg.replace(/%20/g, ' ').trim()
    if (/^[A-Z .]+$/.test(s) && s.length >= 4 && !/DEFAULT|PAGES|DOCUMENTS|PORTAL|DATA|TAX|ROLL|FILES|PROPERTY|PTO|GUIDES|QUICK|REFERENCE|PUBLIC|RECORDS|FINAL|PRELIM/i.test(s)) {
      if (!/\d/.test(s)) county = s.toUpperCase()
    }
  }
  return { name, url, year, county, dataset }
}

async function walk(serverRel, depth, collector) {
  if (depth > MAX_DEPTH) return
  const files = await listFiles(serverRel)
  for (const f of files) {
    const rel = f.ServerRelativeUrl || f.ServerRelativePath?.DecodedUrl
    const name = f.Name || ''
    if ((name.toLowerCase().endsWith('.csv') || name.toLowerCase().endsWith('.zip')) && rel) {
      const u = absUrl(rel)
      const meta = classify(u)
      collector.push(meta)
    }
  }
  const folders = await listFolders(serverRel)
  for (const fol of folders) {
    const sub = fol.ServerRelativeUrl || fol.ServerRelativePath?.DecodedUrl
    if (sub) await walk(sub, depth + 1, collector)
  }
}

async function main() {
  const outDir = path.dirname(OUT_PATH)
  fs.mkdirSync(outDir, { recursive: true })
  const items = []
  await walk(START_SERVER_REL, 0, items)
  const byYear = {}
  for (const it of items) {
    const y = it.year || 'unknown'
    const c = it.county || 'unknown'
    const d = it.dataset || 'unknown'
    byYear[y] = byYear[y] || {}
    byYear[y][c] = byYear[y][c] || {}
    byYear[y][c][d] = byYear[y][c][d] || []
    byYear[y][c][d].push({ name: it.name, url: it.url })
  }
  fs.writeFileSync(OUT_PATH, JSON.stringify({ baseWeb: BASE_WEB, startFolder: START_SERVER_REL, manifest: byYear }, null, 2))
  console.log(`[crawl_dor_public_records] Wrote manifest with ${Object.keys(byYear).length} year groups -> ${OUT_PATH}`)
}

main().catch(err => { console.error(err); process.exit(1) })

