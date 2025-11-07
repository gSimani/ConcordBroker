#!/usr/bin/env node
// Playwright crawler that inspects all iframes on the Public Records page
// and extracts links to 2024 NAL/SDF zips, then downloads and inspects for Gilchrist (county 31).

import fs from 'fs'
import path from 'path'
import { chromium } from 'playwright'
import { execSync } from 'child_process'

const START_URL = process.env.DOR_PUBLIC_START || 'https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/~Public%20Records'
const OUT_DIR = process.env.DOR_DL_DIR || 'historical_data/public_records_2024_iframe'

function ensureDir(p) { fs.mkdirSync(p, { recursive: true }) }
function unique(arr) { return Array.from(new Set(arr)) }

async function getAllFrameLinks(page) {
  const links = new Set()
  // include main page too
  const pages = [page, ...page.frames()]
  for (const fr of pages) {
    try {
      const frLinks = await fr.$$eval('a', as => as.map(a => a.href))
      for (const l of frLinks) if (l) links.add(l)
    } catch {}
  }
  // refresh frames after potential dynamic loading
  const frames = page.frames()
  for (const fr of frames) {
    try {
      const frLinks2 = await fr.$$eval('a', as => as.map(a => a.href))
      for (const l of frLinks2) if (l) links.add(l)
    } catch {}
  }
  return Array.from(links)
}

async function main() {
  ensureDir(OUT_DIR)
  ensureDir(path.join(OUT_DIR, 'zips'))

  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  await page.goto(START_URL, { waitUntil: 'domcontentloaded', timeout: 90000 })

  // Collect links from main and all frames
  let links = await getAllFrameLinks(page)
  // Heuristic: click any element with text like 'Public Records' or ticket ids to force load
  // then recollect links
  const candidates = await page.$$('a')
  for (const a of candidates) {
    try {
      const txt = (await a.textContent())?.trim() || ''
      if (/^~20\d{6,}/.test(txt) || /Public\s*Records/i.test(txt)) {
        await a.click({ timeout: 1000 })
        await page.waitForTimeout(300)
      }
    } catch {}
  }
  // Re-collect
  const more = await getAllFrameLinks(page)
  links = unique([...links, ...more])

  // Filter for 2024 zip links under Public Records
  const zipLinks = links.filter(h => /~Public%20Records\/.+\/(SDF|NAL)\/(2024F|2024P)\.zip$/i.test(h))
  console.log(`[iframe_crawl] Found ${zipLinks.length} matching 2024 zip links`)

  let found = false
  for (const href of zipLinks) {
    try {
      const name = href.split('/').pop()
      const ticket = href.split('/~')[1]?.split('/')[0] || 'ticket'
      const outZip = path.join(OUT_DIR, 'zips', `${ticket}_${name}`)
      console.log(`[DL] ${href}`)
      const res = await page.request.get(href)
      if (!res.ok()) continue
      const buf = await res.body()
      fs.writeFileSync(outZip, buf)
      const extractDir = path.join(OUT_DIR, ticket)
      ensureDir(extractDir)
      try {
        execSync(`powershell -NoProfile -Command "Expand-Archive -Path '${outZip}' -DestinationPath '${extractDir}' -Force"`, { stdio: 'ignore' })
      } catch {}
      // Scan for Gilchrist / county 31
      const walk = (p) => fs.readdirSync(p, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(p, e.name)) : [path.join(p, e.name)])
      const all = walk(extractDir)
      const hit = all.find(f => /SDF_2024_31|NAL_2024_31|Gilchrist/i.test(path.basename(f)))
      if (hit) {
        console.log(`[FOUND] ${hit}`)
        found = true
        break
      }
    } catch {}
  }

  await browser.close()
  if (!found) console.log('[iframe_crawl] Gilchrist 2024 zip not found yet in visible links')
}

main().catch(err => { console.error(err); process.exit(1) })

