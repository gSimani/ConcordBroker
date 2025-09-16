// Supabase Edge Function - Sunbiz Daily Update
// Runs entirely in the cloud, no PC dependency
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { Client } from 'https://deno.land/x/ssh2@1.0.0/mod.ts'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// SFTP Configuration
const SFTP_CONFIG = {
  host: 'sftp.floridados.gov',
  port: 22,
  username: 'Public',
  password: 'PubAccess1845!',
}

// Data directories to check
const DATA_DIRECTORIES = [
  { path: '/Corporate_Data/Daily', type: 'corporate' },
  { path: '/Fictitious_Name_Data/Daily', type: 'fictitious' },
  { path: '/General_Partnership_Data/Daily', type: 'partnership' },
  { path: '/Federal_Tax_Lien_Data/Daily', type: 'lien' },
  { path: '/Mark_Data/Daily', type: 'mark' },
]

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // Parse request
    const { days_back = 1, force = false } = await req.json().catch(() => ({}))

    console.log(`Starting Sunbiz daily update - checking last ${days_back} days`)

    // Statistics
    const stats = {
      start_time: new Date().toISOString(),
      files_processed: 0,
      records_processed: 0,
      entities_created: 0,
      entities_updated: 0,
      errors: [] as string[],
    }

    // Connect to SFTP
    const sftpClient = new Client()
    
    try {
      await sftpClient.connect({
        host: SFTP_CONFIG.host,
        port: SFTP_CONFIG.port,
        username: SFTP_CONFIG.username,
        password: SFTP_CONFIG.password,
      })

      console.log('Connected to Florida SFTP server')

      // Calculate date range
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - days_back)

      // Find and process daily files
      for (const directory of DATA_DIRECTORIES) {
        try {
          const files = await sftpClient.list(directory.path)
          
          for (const file of files) {
            if (!file.name.endsWith('.txt')) continue

            // Parse date from filename (YYYYMMDD format)
            const dateMatch = file.name.match(/^(\d{8})/)
            if (!dateMatch) continue

            const fileDate = new Date(
              parseInt(dateMatch[1].substring(0, 4)),
              parseInt(dateMatch[1].substring(4, 6)) - 1,
              parseInt(dateMatch[1].substring(6, 8))
            )

            // Check if file is within date range
            if (fileDate < cutoffDate && !force) continue

            // Check if already processed
            const { data: existingFile } = await supabase
              .from('florida_daily_processed_files')
              .select('id')
              .eq('file_name', file.name)
              .eq('status', 'completed')
              .single()

            if (existingFile && !force) {
              console.log(`File ${file.name} already processed, skipping`)
              continue
            }

            console.log(`Processing file: ${file.name}`)

            // Download and process file
            const filePath = `${directory.path}/${file.name}`
            const fileContent = await sftpClient.get(filePath)
            
            // Process file content
            const result = await processFile(
              supabase,
              file.name,
              fileContent,
              directory.type,
              fileDate
            )

            stats.files_processed++
            stats.records_processed += result.records
            stats.entities_created += result.created
            stats.entities_updated += result.updated

            // Log successful processing
            await supabase.from('florida_daily_processed_files').upsert({
              file_name: file.name,
              file_type: directory.type,
              file_date: fileDate.toISOString().split('T')[0],
              records_processed: result.records,
              entities_created: result.created,
              entities_updated: result.updated,
              status: 'completed',
              processed_at: new Date().toISOString(),
            })
          }
        } catch (error) {
          console.error(`Error processing directory ${directory.path}:`, error)
          stats.errors.push(`${directory.path}: ${error.message}`)
        }
      }

      // Disconnect from SFTP
      sftpClient.end()

    } catch (sftpError) {
      console.error('SFTP connection error:', sftpError)
      stats.errors.push(`SFTP: ${sftpError.message}`)
    }

    // Calculate duration
    const duration = (new Date().getTime() - new Date(stats.start_time).getTime()) / 1000

    // Log completion to supervisor status
    await supabase.from('sunbiz_supervisor_status').insert({
      status: stats.errors.length > 0 ? 'completed_with_errors' : 'completed',
      metrics: {
        ...stats,
        duration_seconds: duration,
      },
      last_update: new Date().toISOString(),
    })

    // Send webhook notification if configured
    const webhookUrl = Deno.env.get('WEBHOOK_URL')
    if (webhookUrl) {
      await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: `Sunbiz Daily Update Complete`,
          stats,
          duration: `${duration.toFixed(2)}s`,
        }),
      })
    }

    return new Response(
      JSON.stringify({
        success: true,
        stats,
        duration: `${duration.toFixed(2)}s`,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('Fatal error in daily update:', error)
    
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
})

// Process a single file
async function processFile(
  supabase: any,
  fileName: string,
  content: string,
  fileType: string,
  fileDate: Date
): Promise<{ records: number; created: number; updated: number }> {
  const lines = content.split('\n').filter(line => line.length > 50)
  const records: any[] = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (line.length < 100) continue
    
    const record = parseRecord(line, i + 1, fileName, fileDate)
    if (record) {
      records.push(record)
    }
    
    // Process in batches of 500
    if (records.length >= 500) {
      await batchUpsert(supabase, records)
      records.length = 0
    }
  }
  
  // Process remaining records
  if (records.length > 0) {
    await batchUpsert(supabase, records)
  }
  
  return {
    records: lines.length,
    created: lines.length, // Simplified for now
    updated: 0,
  }
}

// Parse a single record
function parseRecord(
  line: string,
  lineNum: number,
  fileName: string,
  fileDate: Date
): any {
  try {
    const entityId = `CLOUD_${fileDate.toISOString().split('T')[0]}_${line.substring(0, 12).trim()}_${lineNum}`.substring(0, 50)
    const businessName = line.substring(12, 212).trim()
    
    if (!businessName) return null
    
    return {
      entity_id: entityId,
      entity_type: line.length > 218 ? line.substring(218, 219) : 'C',
      business_name: businessName.substring(0, 255),
      entity_status: line.length > 212 ? line.substring(212, 218).trim().substring(0, 50) : 'ACTIVE',
      business_address_line1: line.length > 238 ? line.substring(238, 338).trim().substring(0, 255) : '',
      business_city: line.length > 338 ? line.substring(338, 388).trim().substring(0, 100) : '',
      business_state: line.length > 388 ? line.substring(388, 390).trim().substring(0, 2) : 'FL',
      business_zip: line.length > 390 ? line.substring(390, 400).trim().substring(0, 10) : '',
      mailing_address_line1: line.length > 400 ? line.substring(400, 500).trim().substring(0, 255) : '',
      mailing_city: line.length > 500 ? line.substring(500, 550).trim().substring(0, 100) : '',
      mailing_state: line.length > 550 ? line.substring(550, 552).trim().substring(0, 2) : '',
      mailing_zip: line.length > 552 ? line.substring(552, 562).trim().substring(0, 10) : '',
      source_file: fileName,
      source_record_line: lineNum,
      last_update_date: new Date().toISOString(),
    }
  } catch (error) {
    console.error(`Parse error line ${lineNum}:`, error)
    return null
  }
}

// Batch upsert records
async function batchUpsert(supabase: any, records: any[]): Promise<void> {
  // Deduplicate records by entity_id
  const seen = new Set()
  const uniqueRecords = records.filter(r => {
    if (seen.has(r.entity_id)) return false
    seen.add(r.entity_id)
    return true
  })
  
  // Upsert to database
  const { error } = await supabase
    .from('florida_entities')
    .upsert(uniqueRecords, {
      onConflict: 'entity_id',
      ignoreDuplicates: false,
    })
  
  if (error) {
    console.error('Batch upsert error:', error)
    throw error
  }
}