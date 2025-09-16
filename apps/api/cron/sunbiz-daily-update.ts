/**
 * Vercel Cron Job - Sunbiz Daily Update
 * Runs daily at 2 AM EST to update Florida business data
 * Completely cloud-based, no PC dependency
 */

import { NextApiRequest, NextApiResponse } from 'next'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!
const supabase = createClient(supabaseUrl, supabaseServiceKey)

export const config = {
  maxDuration: 300, // 5 minutes max execution time
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // Verify cron secret (security)
    const authHeader = req.headers.authorization
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return res.status(401).json({ error: 'Unauthorized' })
    }

    console.log('[CRON] Starting Sunbiz daily update at', new Date().toISOString())

    // Call Supabase Edge Function
    const { data, error } = await supabase.functions.invoke('sunbiz-daily-update', {
      body: {
        days_back: 1, // Check yesterday's files
        force: false, // Don't reprocess existing files
      },
    })

    if (error) {
      console.error('[CRON] Supabase function error:', error)
      
      // Log error to database
      await supabase.from('sunbiz_supervisor_status').insert({
        status: 'error',
        metrics: {
          error: error.message,
          timestamp: new Date().toISOString(),
        },
      })

      // Send error notification
      await sendNotification({
        type: 'error',
        message: `Sunbiz daily update failed: ${error.message}`,
      })

      return res.status(500).json({ 
        success: false, 
        error: error.message 
      })
    }

    console.log('[CRON] Daily update completed:', data)

    // Log success to database
    await supabase.from('sunbiz_supervisor_status').insert({
      status: 'completed',
      metrics: data.stats,
      last_update: new Date().toISOString(),
    })

    // Send success notification
    await sendNotification({
      type: 'success',
      message: `Sunbiz daily update completed: ${data.stats.files_processed} files, ${data.stats.records_processed} records`,
      stats: data.stats,
    })

    return res.status(200).json({
      success: true,
      data,
    })

  } catch (error) {
    console.error('[CRON] Fatal error:', error)
    
    return res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    })
  }
}

/**
 * Send notifications via configured channels
 */
async function sendNotification(notification: {
  type: 'success' | 'error'
  message: string
  stats?: any
}) {
  // Webhook notification (Slack, Discord, etc.)
  const webhookUrl = process.env.WEBHOOK_URL
  if (webhookUrl) {
    try {
      await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: notification.message,
          type: notification.type,
          stats: notification.stats,
          timestamp: new Date().toISOString(),
        }),
      })
    } catch (error) {
      console.error('[CRON] Webhook notification failed:', error)
    }
  }

  // Email notification (using SendGrid, Resend, etc.)
  if (process.env.SENDGRID_API_KEY && process.env.ALERT_EMAIL) {
    // Implementation depends on email service
    // Example with SendGrid:
    /*
    const sgMail = require('@sendgrid/mail')
    sgMail.setApiKey(process.env.SENDGRID_API_KEY)
    
    await sgMail.send({
      to: process.env.ALERT_EMAIL,
      from: 'noreply@concordbroker.com',
      subject: `Sunbiz Update: ${notification.type}`,
      text: notification.message,
      html: `<p>${notification.message}</p>`,
    })
    */
  }
}