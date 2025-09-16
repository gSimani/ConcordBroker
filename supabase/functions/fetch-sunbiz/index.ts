import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3'

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
    const { data_type, filename, action } = await req.json()
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    if (action === 'list') {
      // List available files in FTP directory
      const ftpUrl = `ftp://ftp.dos.state.fl.us/public/doc/${data_type}/`
      
      // Try HTTP mirror first (more reliable)
      const httpUrl = ftpUrl.replace('ftp://', 'http://')
      const response = await fetch(httpUrl, { 
        method: 'GET',
        headers: { 'User-Agent': 'Mozilla/5.0' }
      })
      
      if (response.ok) {
        const html = await response.text()
        
        // Parse directory listing
        const files = []
        const linkRegex = /<a href="([^"]+\.(txt|zip))">([^<]+)<\/a>/gi
        let match
        
        while ((match = linkRegex.exec(html)) !== null) {
          files.push({
            filename: match[1],
            display: match[3],
            type: match[2]
          })
        }
        
        // Store listing in database
        await supabase.from('sunbiz_download_jobs').insert({
          data_type,
          status: 'listing_found',
          file_count: files.length,
          error_message: JSON.stringify(files.slice(0, 10)) // Sample
        })
        
        return new Response(JSON.stringify({
          success: true,
          data_type,
          file_count: files.length,
          files: files.slice(0, 100), // Return first 100 files
          message: 'Directory listing retrieved'
        }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
      }
    }
    
    if (action === 'download') {
      // Download specific file to Supabase Storage
      const ftpUrl = `ftp://ftp.dos.state.fl.us/public/doc/${data_type}/${filename}`
      const httpUrl = ftpUrl.replace('ftp://', 'http://')
      
      console.log(`Downloading: ${httpUrl}`)
      
      // Stream download
      const response = await fetch(httpUrl, {
        method: 'GET',
        headers: { 'User-Agent': 'Mozilla/5.0' }
      })
      
      if (response.ok) {
        const arrayBuffer = await response.arrayBuffer()
        const uint8Array = new Uint8Array(arrayBuffer)
        
        // Upload to Supabase Storage
        const storagePath = `${data_type}/${filename}`
        const { data: uploadData, error: uploadError } = await supabase
          .storage
          .from('sunbiz-data')
          .upload(storagePath, uint8Array, {
            contentType: filename.endsWith('.zip') ? 'application/zip' : 'text/plain',
            upsert: true
          })
        
        if (uploadError) throw uploadError
        
        // Check for emails in text files
        let emailCount = 0
        let phoneCount = 0
        
        if (filename.endsWith('.txt')) {
          const text = new TextDecoder().decode(uint8Array)
          emailCount = (text.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g) || []).length
          phoneCount = (text.match(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g) || []).length
        }
        
        // Update database
        await supabase.from('sunbiz_download_jobs').insert({
          data_type,
          status: 'downloaded',
          file_count: 1,
          total_size_bytes: arrayBuffer.byteLength,
          error_message: JSON.stringify({
            filename,
            size: arrayBuffer.byteLength,
            emailCount,
            phoneCount,
            storagePath
          }),
          completed_at: new Date().toISOString()
        })
        
        return new Response(JSON.stringify({
          success: true,
          filename,
          size: arrayBuffer.byteLength,
          emailCount,
          phoneCount,
          storagePath,
          message: `File uploaded to Supabase Storage`
        }), { headers: { ...corsHeaders, 'Content-Type': 'application/json' } })
      }
    }
    
    if (action === 'stream') {
      // Stream directly for memvid processing
      const ftpUrl = `ftp://ftp.dos.state.fl.us/public/doc/${data_type}/${filename}`
      const httpUrl = ftpUrl.replace('ftp://', 'http://')
      
      const response = await fetch(httpUrl, {
        method: 'GET',
        headers: { 'User-Agent': 'Mozilla/5.0' }
      })
      
      if (response.ok) {
        // Return streaming response for direct pipeline processing
        return new Response(response.body, {
          headers: {
            ...corsHeaders,
            'Content-Type': filename.endsWith('.zip') ? 'application/zip' : 'text/plain',
            'X-Email-Count': '0', // Will be updated by pipeline
            'X-Data-Type': data_type,
            'X-Filename': filename
          }
        })
      }
    }
    
    return new Response(JSON.stringify({
      error: 'Invalid action or request failed',
      validActions: ['list', 'download', 'stream']
    }), { 
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
    })
    
  } catch (error) {
    console.error('Edge function error:', error)
    return new Response(JSON.stringify({
      error: error.message
    }), { 
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
    })
  }
})