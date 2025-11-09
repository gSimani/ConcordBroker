# 🔄 IMPORTANT: Update Supabase Keys

Since your Supabase project is `supabase-concordbroker` (not `mogulpssjdlxjvstqfee`), you need to update the API keys as well.

## Current Keys (Likely Incorrect)
These keys are for the old project `mogulpssjdlxjvstqfee`:
```
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZ3VscHNzamRseGp2c3RxZmVlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5NTMyMDEsImV4cCI6MjA2MTUyOTIwMX0.5wzCkw9J3ZZMyNZvEge3ypA_41FmLR5mH6OmN0r8EZg

SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZ3VscHNzamRseGp2c3RxZmVlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTk1MzIwMSwiZXhwIjoyMDYxNTI5MjAxfQ.fTsIz7fTwvbhqJNp1KVIEM_qAghf25HDNiwUXxA3Bkg
```

## How to Get Your Correct Keys

1. **Go to your Supabase Dashboard:**
   https://supabase.com/dashboard/project/supabase-concordbroker

2. **Navigate to Settings → API**

3. **Copy the following keys:**
   - **Project URL:** Should be `https://supabase-concordbroker.supabase.co`
   - **Anon/Public Key:** Starts with `eyJhbGciOiJIUzI1NiI...` (safe to use in browser)
   - **Service Role Key:** Starts with `eyJhbGciOiJIUzI1NiI...` (keep secret, server-side only)

4. **Also get the Database Password:**
   - Go to Settings → Database
   - Note the connection string
   - Update password to: `Concord@Broker2025!`

## Files to Update

After getting your correct keys, update these files:

### 1. `.env`
```env
SUPABASE_URL=https://supabase-concordbroker.supabase.co
SUPABASE_ANON_KEY=YOUR_NEW_ANON_KEY_HERE
SUPABASE_SERVICE_ROLE_KEY=YOUR_NEW_SERVICE_ROLE_KEY_HERE
```

### 2. `.env.production`
```env
SUPABASE_URL=https://supabase-concordbroker.supabase.co
SUPABASE_ANON_KEY=YOUR_NEW_ANON_KEY_HERE
SUPABASE_SERVICE_ROLE_KEY=YOUR_NEW_SERVICE_ROLE_KEY_HERE
```

### 3. `mcp-server-twilio/.env`
```env
SUPABASE_URL=https://supabase-concordbroker.supabase.co
SUPABASE_ANON_KEY=YOUR_NEW_ANON_KEY_HERE
SUPABASE_SERVICE_KEY=YOUR_NEW_SERVICE_ROLE_KEY_HERE
```

### 4. Update Connection Strings
The database URL should follow this pattern:
```
postgres://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

For your project:
```
DATABASE_URL=postgres://postgres.supabase-concordbroker:Concord%40Broker2025!@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

## Quick Command to Test

After updating, test your connection:

```javascript
// Test in browser console or Node.js
const SUPABASE_URL = 'https://supabase-concordbroker.supabase.co'
const SUPABASE_ANON_KEY = 'YOUR_NEW_ANON_KEY_HERE'

fetch(`${SUPABASE_URL}/rest/v1/`, {
  headers: {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
  }
}).then(r => console.log('Status:', r.status))
```

## Action Required

⚠️ **You must get the correct keys from your Supabase dashboard** for the `supabase-concordbroker` project and update all configuration files.

The keys in the current configuration are for a different project and won't work!