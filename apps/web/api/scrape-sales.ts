import type { VercelRequest, VercelResponse } from '@vercel/node'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execAsync = promisify(exec)

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const { parcel_id, county } = req.body

    if (!parcel_id || !county) {
      return res.status(400).json({ error: 'Missing parcel_id or county' })
    }

    // Log the request
    console.log(`[SCRAPE-SALES] Request for ${parcel_id} (${county})`)

    // Only support counties we have scrapers for
    const supportedCounties = ['BROWARD', 'PALM BEACH']
    if (!supportedCounties.includes(county.toUpperCase())) {
      return res.status(400).json({
        error: 'County not supported for scraping',
        supported: supportedCounties
      })
    }

    // Return immediate response - scraping happens in background
    res.status(202).json({
      status: 'accepted',
      message: 'Scraping started in background',
      parcel_id,
      county,
      estimated_time: '5-10 seconds'
    })

    // Trigger background scraping (non-blocking)
    setImmediate(async () => {
      try {
        await scrapeAndImportSales(parcel_id, county)
      } catch (error) {
        console.error(`[SCRAPE-SALES] Background error for ${parcel_id}:`, error)
      }
    })

  } catch (error) {
    console.error('[SCRAPE-SALES] Error:', error)
    return res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

async function scrapeAndImportSales(parcelId: string, county: string) {
  console.log(`[SCRAPE-SALES] Background scraping started for ${parcelId}`)

  try {
    // Path to scraper script
    const scriptPath = path.join(process.cwd(), 'scripts', 'scrape_bcpa_sales_for_parcel.py')

    // Run scraper
    const { stdout, stderr } = await execAsync(
      `python "${scriptPath}" ${parcelId}`,
      { timeout: 30000 } // 30 second timeout
    )

    if (stderr) {
      console.error(`[SCRAPE-SALES] Stderr: ${stderr}`)
    }

    console.log(`[SCRAPE-SALES] Stdout: ${stdout}`)

    // Check if CSV was created
    const csvPath = path.join(process.cwd(), `bcpa_sales_history_${parcelId}.csv`)

    // Import the CSV to database
    const importScript = path.join(process.cwd(), 'scripts', 'load-bcpa-sales.mjs')

    const { stdout: importOut, stderr: importErr } = await execAsync(
      `node "${importScript}" --file "${csvPath}" --county ${county}`,
      { timeout: 10000 }
    )

    if (importErr) {
      console.error(`[SCRAPE-SALES] Import stderr: ${importErr}`)
    }

    console.log(`[SCRAPE-SALES] Import stdout: ${importOut}`)
    console.log(`[SCRAPE-SALES] ✅ Complete for ${parcelId}`)

  } catch (error) {
    console.error(`[SCRAPE-SALES] ❌ Failed for ${parcelId}:`, error)
    throw error
  }
}
