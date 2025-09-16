/**
 * Vercel Cron Job - Sunbiz Daily Update
 * Runs daily at 2 AM EST to update Florida business data
 * Completely cloud-based, no PC dependency
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  try {
    // Verify cron secret (security)
    const authHeader = req.headers.authorization;
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    console.log('[CRON] Starting Sunbiz daily update at', new Date().toISOString());

    // Call Supabase Edge Function
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
    
    const response = await fetch(`${supabaseUrl}/functions/v1/sunbiz-daily-update`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${supabaseServiceKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        days_back: 1, // Check yesterday's files
        force: false, // Don't reprocess existing files
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error('[CRON] Supabase function error:', data);
      
      // Send error notification
      await sendNotification({
        type: 'error',
        message: `Sunbiz daily update failed: ${data.error || 'Unknown error'}`,
      });

      return res.status(500).json({ 
        success: false, 
        error: data.error || 'Edge function failed'
      });
    }

    console.log('[CRON] Daily update completed:', data);

    // Send success notification
    await sendNotification({
      type: 'success',
      message: `Sunbiz daily update completed: ${data.stats?.files_processed || 0} files, ${data.stats?.records_processed || 0} records`,
      stats: data.stats,
    });

    return res.status(200).json({
      success: true,
      data,
    });

  } catch (error) {
    console.error('[CRON] Fatal error:', error);
    
    return res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    });
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
  const webhookUrl = process.env.WEBHOOK_URL;
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
      });
    } catch (error) {
      console.error('[CRON] Webhook notification failed:', error);
    }
  }
}