#!/usr/bin/env node
// Headless crawl of Florida DOR Public Records to locate 2024 NAL/SDF zips and retrieve county-specific files.
// Strategy:
// 1) Enumerate Public Records listing pages (paged by ~ticket folders)
// 2) Collect links that contain /NAL/2024F.zip and /SDF/2024F.zip
// 3) Download all 2024F zips, extract CSVs, and detect county (e.g., SDF_2024_31Gilchrist_F.csv)

import fs from 'fs'
import path from 'path'
import { chromium } from 'playwright'
import { execSync } from 'child_process'

const START_URL = process.env.DOR_PUBLIC_START || 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/~Public%20Records'
const OUT_DIR = process.env.DOR_DL_DIR || 'historical_data/public_records_2024'

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }) }

async function collectTicketLinks(page) {
  const anchors = await page.$$eval('a', as => as.map(a => ({ href: a.href, text: a.textContent?.trim() })))
  // Keep only links under Public Records tickets
  const links = anchors.filter(a => /~Public%20Records\/.+/.test(a.href) && /\/(SDF|NAL)\//i.test(a.href))
  return links
}

function unique(arr, key) { const seen = new Set(); return arr.filter(x => (k => !seen.has(k) && seen.add(k))(key(x))) }

async function main() {
  ensureDir(OUT_DIR)
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  await page.goto(START_URL, { waitUntil: 'domcontentloaded', timeout: 60000 })

  let collected = []
  collected.push(...await collectTicketLinks(page))

  // Try clicking into folders that look like tickets (~2025...)
  const ticketLinks = await page.$$eval('a', as => as.map(a => a.href).filter(h => /~Public%20Records\/~20\d{6,}/.test(h)))
  for (const t of unique(ticketLinks, x => x)) {
    try {
      await page.goto(t, { waitUntil: 'domcontentloaded', timeout: 30000 })
      const links = await collectTicketLinks(page)
      collected.push(...links)
    } catch {}
  }

  // Filter for 2024 zips (NAL/SDF)
  const zips2024 = collected.filter(l => /\/(SDF|NAL)\/(2024F|2024P)\.zip$/i.test(l.href))
  const uniq = unique(zips2024, x => x.href)

  console.log(`[crawl_public_records_2024] Found ${uniq.length} 2024 zip links`)
  ensureDir(path.join(OUT_DIR, 'zips'))

  let foundGilchrist = false
  for (const { href } of uniq) {
    try {
      const name = href.split('/').pop()
      const ticket = href.split('/~')[1]?.split('/')[0] || 'ticket'
      const outZip = path.join(OUT_DIR, 'zips', `${ticket}_${name}`)
      console.log(`[DL] ${href}`)
      const res = await fetch(href)
      if (!res.ok) continue
      const buf = Buffer.from(await res.arrayBuffer())
      fs.writeFileSync(outZip, buf)
      const extractDir = path.join(OUT_DIR, ticket)
      ensureDir(extractDir)
      // Use PowerShell Expand-Archive or .NET Zip when available
      try {
        execSync(`powershell -NoProfile -Command "Expand-Archive -Path '${outZip}' -DestinationPath '${extractDir}' -Force"`, { stdio: 'ignore' })
      } catch {
        // fallback to Node unzip not implemented here due to environment constraints
      }
      // Scan extracted for Gilchrist
      const files = fs.readdirSync(extractDir, { withFileTypes: true })
      function walk(p) {
        const out = []
        for (const e of fs.readdirSync(p, { withFileTypes: true })) {
          const full = path.join(p, e.name)
          if (e.isDirectory()) out.push(...walk(full))
          else out.push(full)
        }
        return out
      }
      const all = walk(extractDir)
      const hit = all.find(f => /SDF_2024_31|Gilchrist/i.test(path.basename(f)))
      if (hit) {
        console.log(`[FOUND] Gilchrist 2024: ${hit}`)
        foundGilchrist = true
        break
      }
    } catch {}
  }

  await browser.close()
  if (!foundGilchrist) console.log('[crawl_public_records_2024] Did not locate Gilchrist 2024 zips yet')
}

main().catch(err => { console.error(err); process.exit(1) })

