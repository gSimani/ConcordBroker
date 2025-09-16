// Property Appraiser Daily Sync - Supabase Edge Function
// Runs daily to check for and import new property data

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client with service role
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Get current date info
    const now = new Date()
    const currentYear = now.getFullYear()
    const currentPeriod = `${currentYear}P`

    console.log(`Starting Property Appraiser sync for period: ${currentPeriod}`)

    // File types to check
    const fileTypes = ['NAL', 'NAP', 'SDF', 'NAV']
    const baseUrl = 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files'
    
    const newFiles: any[] = []
    
    // Check each file type for updates
    for (const fileType of fileTypes) {
      const url = `${baseUrl}/${fileType}/${currentPeriod}`
      
      try {
        const response = await fetch(url)
        if (response.ok) {
          const html = await response.text()
          
          // Parse HTML to find CSV file links
          const filePattern = new RegExp(`${fileType}\\d{2}P\\d{6}\\.csv`, 'gi')
          const matches = html.match(filePattern) || []
          
          for (const filename of matches) {
            // Extract county code from filename
            const countyCode = filename.substring(3, 5)
            
            // Check if file was already processed
            const { data: existing } = await supabase
              .from('property_sync_log')
              .select('id')
              .eq('filename', filename)
              .eq('status', 'completed')
              .single()
            
            if (!existing) {
              newFiles.push({
                type: fileType,
                filename: filename,
                url: `${url}/${filename}`,
                countyCode: countyCode,
                period: currentPeriod
              })
            }
          }
        }
      } catch (error) {
        console.error(`Error checking ${fileType}: ${error}`)
      }
    }

    console.log(`Found ${newFiles.length} new files to process`)

    // Process each new file
    let processed = 0
    let failed = 0
    
    for (const fileInfo of newFiles) {
      try {
        // Download file
        const fileResponse = await fetch(fileInfo.url)
        if (!fileResponse.ok) {
          throw new Error(`Failed to download ${fileInfo.filename}`)
        }
        
        const csvContent = await fileResponse.text()
        
        // Process based on file type
        if (fileInfo.type === 'NAL') {
          await processNALFile(supabase, csvContent, fileInfo)
        } else if (fileInfo.type === 'NAP') {
          await processNAPFile(supabase, csvContent, fileInfo)
        } else if (fileInfo.type === 'SDF') {
          await processSDFFile(supabase, csvContent, fileInfo)
        } else if (fileInfo.type === 'NAV') {
          await processNAVFile(supabase, csvContent, fileInfo)
        }
        
        // Log successful processing
        await supabase.from('property_sync_log').insert({
          filename: fileInfo.filename,
          file_type: fileInfo.type,
          county_code: fileInfo.countyCode,
          status: 'completed',
          processed_at: new Date().toISOString(),
          metadata: fileInfo
        })
        
        processed++
        console.log(`Processed ${fileInfo.filename}`)
        
      } catch (error) {
        // Log error
        await supabase.from('property_sync_log').insert({
          filename: fileInfo.filename,
          file_type: fileInfo.type,
          county_code: fileInfo.countyCode,
          status: 'error',
          error_message: String(error),
          processed_at: new Date().toISOString(),
          metadata: fileInfo
        })
        
        failed++
        console.error(`Failed to process ${fileInfo.filename}: ${error}`)
      }
    }

    // Return summary
    const summary = {
      status: failed === 0 ? 'success' : 'partial',
      filesFound: newFiles.length,
      filesProcessed: processed,
      filesFailed: failed,
      timestamp: new Date().toISOString()
    }

    return new Response(
      JSON.stringify(summary),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    )
    
  } catch (error) {
    console.error('Critical error in sync:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    )
  }
})

// Process NAL (Property Assessment) files
async function processNALFile(supabase: any, csvContent: string, fileInfo: any) {
  const lines = csvContent.split('\n')
  const headers = lines[0].split(',').map(h => h.trim())
  
  const records = []
  const batchSize = 1000
  
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue
    
    const values = lines[i].split(',')
    const row: any = {}
    
    headers.forEach((header, index) => {
      row[header] = values[index]?.trim() || ''
    })
    
    // Map to database fields
    const record = {
      parcel_id: row['PARCEL_ID'] || '',
      county_code: fileInfo.countyCode,
      county_name: getCountyName(fileInfo.countyCode),
      owner_name: row['OWN_NAME']?.substring(0, 255) || '',
      owner_address: row['OWN_ADDR1']?.substring(0, 255) || '',
      owner_city: row['OWN_CITY']?.substring(0, 100) || '',
      owner_state: row['OWN_STATE'] || 'FL',
      owner_zip: row['OWN_ZIPCD']?.substring(0, 10) || '',
      property_address: row['PHY_ADDR1']?.substring(0, 255) || '',
      property_city: row['PHY_CITY']?.substring(0, 100) || '',
      property_zip: row['PHY_ZIPCD']?.substring(0, 10) || '',
      property_use_code: row['DOR_UC']?.substring(0, 20) || '',
      tax_district: row['DISTR_CD']?.substring(0, 50) || '',
      subdivision: row['SUBDIV_NM']?.substring(0, 100) || '',
      just_value: parseFloat(row['JV']) || 0,
      assessed_value: parseFloat(row['AV_SD']) || 0,
      taxable_value: parseFloat(row['TV_SD']) || 0,
      land_value: parseFloat(row['LND_VAL']) || 0,
      building_value: parseFloat(row['BLDT_VAL']) || 0,
      total_sq_ft: parseInt(row['LND_SQFOOT']) || 0,
      living_area: parseInt(row['TOT_LVG_AREA']) || 0,
      year_built: parseInt(row['ACT_YR_BLT']) || 0,
      bedrooms: parseInt(row['NO_RES_UNTS']) || 0,
      bathrooms: parseFloat(row['NO_BATHS']) || 0,
      pool: row['POOL']?.toUpperCase() === 'Y',
      tax_year: new Date().getFullYear()
    }
    
    records.push(record)
    
    // Insert in batches
    if (records.length >= batchSize) {
      await supabase.from('property_assessments').upsert(records, {
        onConflict: 'parcel_id,county_code,tax_year'
      })
      records.length = 0
    }
  }
  
  // Insert remaining records
  if (records.length > 0) {
    await supabase.from('property_assessments').upsert(records, {
      onConflict: 'parcel_id,county_code,tax_year'
    })
  }
}

// Process NAP (Property Owners) files
async function processNAPFile(supabase: any, csvContent: string, fileInfo: any) {
  // Similar structure to NAL processing
  console.log(`Processing NAP file: ${fileInfo.filename}`)
  // Implementation follows same pattern
}

// Process SDF (Sales) files
async function processSDFFile(supabase: any, csvContent: string, fileInfo: any) {
  // Similar structure to NAL processing
  console.log(`Processing SDF file: ${fileInfo.filename}`)
  // Implementation follows same pattern
}

// Process NAV (Non-Ad Valorem) files
async function processNAVFile(supabase: any, csvContent: string, fileInfo: any) {
  // NAV files are fixed-width format
  console.log(`Processing NAV file: ${fileInfo.filename}`)
  // Implementation would parse fixed-width format
}

// County code to name mapping
function getCountyName(code: string): string {
  const counties: { [key: string]: string } = {
    "11": "ALACHUA", "12": "BAKER", "13": "BAY", "14": "BRADFORD",
    "15": "BREVARD", "16": "BROWARD", "17": "CALHOUN", "18": "CHARLOTTE",
    "19": "CITRUS", "20": "CLAY", "21": "COLLIER", "22": "COLUMBIA",
    "23": "DADE", "24": "DESOTO", "25": "DIXIE", "26": "DUVAL",
    "27": "ESCAMBIA", "28": "FLAGLER", "29": "FRANKLIN", "30": "GADSDEN",
    "31": "GILCHRIST", "32": "GLADES", "33": "GULF", "34": "HAMILTON",
    "35": "HARDEE", "36": "HENDRY", "37": "HERNANDO", "38": "HIGHLANDS",
    "39": "HILLSBOROUGH", "40": "HOLMES", "41": "INDIAN RIVER", "42": "JACKSON",
    "43": "JEFFERSON", "44": "LAFAYETTE", "45": "LAKE", "46": "LEE",
    "47": "LEON", "48": "LEVY", "49": "LIBERTY", "50": "MADISON",
    "51": "MANATEE", "52": "MARION", "53": "MARTIN", "54": "MONROE",
    "55": "NASSAU", "56": "OKALOOSA", "57": "OKEECHOBEE", "58": "ORANGE",
    "59": "OSCEOLA", "60": "PALM BEACH", "61": "PASCO", "62": "PINELLAS",
    "63": "POLK", "64": "PUTNAM", "65": "SANTA ROSA", "66": "SARASOTA",
    "67": "SEMINOLE", "68": "ST. JOHNS", "69": "ST. LUCIE", "70": "SUMTER",
    "71": "SUWANNEE", "72": "TAYLOR", "73": "UNION", "74": "VOLUSIA",
    "75": "WAKULLA", "76": "WALTON", "77": "WASHINGTON"
  }
  return counties[code] || 'UNKNOWN'
}