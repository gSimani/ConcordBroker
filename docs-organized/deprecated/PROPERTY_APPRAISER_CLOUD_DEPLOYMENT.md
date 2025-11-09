# Property Appraiser Cloud Sync Deployment Guide

## Overview
Complete cloud-based daily synchronization system for Florida Property Appraiser data, running entirely in Supabase with no local dependencies.

## Architecture
```
Florida Revenue Website
         ↓
    Edge Function
    (Daily Check)
         ↓
    Download CSV
         ↓
    Process & Import
         ↓
    Supabase Database
         ↓
    Your Website
```

## 1. Deploy Database Schema

Run this SQL in Supabase SQL Editor:

```sql
-- Run the property_appraiser_sync_schema.sql file
-- This creates:
-- - property_sync_log table
-- - Monitoring tables
-- - Helper functions
-- - RLS policies
```

## 2. Deploy Edge Function

### Via Supabase CLI:

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref pmispwtdngkcmsrsjwbp

# Deploy the edge function
supabase functions deploy property-appraiser-sync

# Set secrets (if needed)
supabase secrets set PROPERTY_SYNC_KEY=your-secret-key
```

### Via Supabase Dashboard:

1. Go to **Edge Functions** in your Supabase dashboard
2. Click **New Function**
3. Name: `property-appraiser-sync`
4. Paste the TypeScript code from `supabase/functions/property-appraiser-sync/index.ts`
5. Click **Deploy**

## 3. Set Up Daily Schedule

### Option A: Using Supabase Cron (Recommended)

In Supabase SQL Editor:

```sql
-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule daily sync at 2 AM EST
SELECT cron.schedule(
  'property-appraiser-daily-sync',
  '0 2 * * *',
  $$
    SELECT net.http_post(
      url := 'https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/property-appraiser-sync',
      headers := jsonb_build_object(
        'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key'),
        'Content-Type', 'application/json'
      ),
      body := jsonb_build_object('trigger', 'scheduled')
    );
  $$
);
```

### Option B: Using External Scheduler

Use services like:
- **GitHub Actions** (free)
- **Vercel Cron** (if using Vercel)
- **Cloudflare Workers** (with cron triggers)

Example GitHub Actions workflow:

```yaml
name: Property Appraiser Daily Sync

on:
  schedule:
    - cron: '0 7 * * *'  # 2 AM EST (7 AM UTC)
  workflow_dispatch:  # Allow manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Supabase Edge Function
        run: |
          curl -X POST \
            https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/property-appraiser-sync \
            -H "Authorization: Bearer ${{ secrets.SUPABASE_ANON_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"trigger": "github-action"}'
```

## 4. Monitor Sync Status

### Check Last Sync:
```sql
SELECT * FROM get_last_property_sync();
```

### View Sync Statistics:
```sql
SELECT * FROM property_sync_stats
ORDER BY sync_date DESC
LIMIT 30;
```

### Check for Errors:
```sql
SELECT * FROM property_sync_log
WHERE status = 'error'
AND processed_at > CURRENT_DATE - INTERVAL '7 days'
ORDER BY processed_at DESC;
```

## 5. Manual Trigger

### Via cURL:
```bash
curl -X POST \
  https://pmispwtdngkcmsrsjwbp.supabase.co/functions/v1/property-appraiser-sync \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"manual": true}'
```

### Via JavaScript:
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://pmispwtdngkcmsrsjwbp.supabase.co',
  'YOUR_ANON_KEY'
)

const { data, error } = await supabase.functions.invoke('property-appraiser-sync', {
  body: { manual: true }
})
```

## 6. Website Integration

### Display Latest Property Data:
```javascript
// Get properties with latest data
const { data: properties } = await supabase
  .from('property_assessments')
  .select('*')
  .eq('county_code', '16')  // Broward
  .order('taxable_value', { ascending: false })
  .limit(100)
```

### Show Sync Status on Admin Dashboard:
```javascript
// Get sync status
const { data: syncStatus } = await supabase
  .rpc('get_last_property_sync')

// Display in UI
if (syncStatus) {
  console.log(`Last sync: ${syncStatus.last_sync}`)
  console.log(`Files processed: ${syncStatus.files_processed}`)
  console.log(`Next sync: ${syncStatus.next_sync_due}`)
}
```

## 7. Alerts & Monitoring

### Set up email alerts for failures:
```sql
-- Create alert function
CREATE OR REPLACE FUNCTION notify_sync_failure()
RETURNS trigger AS $$
BEGIN
  IF NEW.status = 'error' THEN
    -- Send notification (requires email service setup)
    PERFORM net.http_post(
      url := 'YOUR_WEBHOOK_URL',
      body := jsonb_build_object(
        'error', NEW.error_message,
        'file', NEW.filename
      )
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER sync_error_notification
AFTER INSERT ON property_sync_log
FOR EACH ROW
WHEN (NEW.status = 'error')
EXECUTE FUNCTION notify_sync_failure();
```

## 8. Performance Optimization

### Indexes for common queries:
```sql
-- Already included in schema, but verify they exist:
CREATE INDEX IF NOT EXISTS idx_assessment_county_value 
ON property_assessments(county_code, taxable_value DESC);

CREATE INDEX IF NOT EXISTS idx_assessment_updated 
ON property_assessments(updated_at DESC);
```

### Materialized view for dashboard:
```sql
CREATE MATERIALIZED VIEW property_summary AS
SELECT 
  county_name,
  COUNT(*) as total_properties,
  AVG(taxable_value) as avg_value,
  MAX(taxable_value) as max_value,
  MIN(taxable_value) as min_value,
  MAX(updated_at) as last_updated
FROM property_assessments
GROUP BY county_name;

-- Refresh daily after sync
CREATE OR REPLACE FUNCTION refresh_property_summary()
RETURNS void AS $$
  REFRESH MATERIALIZED VIEW CONCURRENTLY property_summary;
$$ LANGUAGE sql;
```

## 9. Troubleshooting

### Edge Function not running?
1. Check Edge Function logs in Supabase dashboard
2. Verify cron job is scheduled: `SELECT * FROM cron.job;`
3. Test manual trigger with cURL

### Data not updating?
1. Check sync log: `SELECT * FROM property_sync_log ORDER BY processed_at DESC LIMIT 10;`
2. Verify Florida Revenue website is accessible
3. Check for RLS policies blocking inserts

### Performance issues?
1. Ensure indexes are created
2. Consider partitioning large tables by county
3. Use connection pooling for Edge Functions

## 10. Cost Optimization

- Edge Function invocations: ~30/month (daily sync)
- Database storage: Depends on counties synced
- Bandwidth: ~100MB per full county sync

**Estimated monthly cost:** $0-5 for typical usage

## Security Notes

- Edge Function uses service role (bypasses RLS)
- Sync logs are read-only for authenticated users
- No sensitive data exposed in logs
- All connections use SSL

## Support

For issues or questions:
1. Check sync logs first
2. Review Edge Function logs
3. Verify database permissions
4. Test with manual trigger

---

**Status:** Ready for deployment
**Last Updated:** 2025-09-12
**Maintained By:** ConcordBroker Team