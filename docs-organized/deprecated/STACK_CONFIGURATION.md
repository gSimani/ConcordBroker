# ConcordBroker Stack Configuration
**Updated:** January 2025  
**Status:** PRODUCTION READY

## 🏗️ Full Stack Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CONCORDBROKER STACK                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Frontend (Vercel)           Backend (Railway)           │
│  ┌──────────────┐           ┌────────────────┐          │
│  │ concordbroker│           │ ConcordBroker- │          │
│  │    .com      │ ◄────────►│    Railway     │          │
│  └──────────────┘           └────────────────┘          │
│         │                           │                    │
│         └──────────┬────────────────┘                    │
│                    ▼                                     │
│           ┌──────────────┐                               │
│           │   Supabase   │                               │
│           │  PostgreSQL  │                               │
│           └──────────────┘                               │
│                    │                                     │
│      ┌─────────────┼─────────────┐                       │
│      ▼             ▼             ▼                       │
│  ┌────────┐  ┌────────┐  ┌────────────┐                 │
│  │ Twilio │  │SendGrid│  │MCP Server  │                 │
│  │  SMS   │  │ Email  │  │  Twilio    │                 │
│  └────────┘  └────────┘  └────────────┘                 │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 🔑 Production Credentials

### Supabase (Database)
```
URL: https://supabase-concordbroker.supabase.co
Project Ref: supabase-concordbroker
Anon Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Service Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Token: 2ecbca31-7ef7-4b7b-ab71-b44b107b3ae0
Password: Concord@Broker2025! (UPDATE IN DASHBOARD)
```

### Vercel (Frontend)
```
Project ID: prj_7kCqUt53vpDriVoRyHqQKHXDPsVJ
Project Name: concordbroker
URL: https://concordbroker.com
Edge Config: ecfg_ayn43zuykk8yw3qlh0dzdei1gbne
Digest: 5bf6b008a9ec05f6870c476d10b53211797aa000f95aae344ae60f9b422286da
```

### Railway (Backend)
```
Project Name: ConcordBroker-Railway
Project ID: 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb
Environment: concordbrokerproduction
Service ID: 5eeefe12-0a29-43b7-8a7b-6fa4e99e53d7
API URL: https://concordbroker-railway-production.up.railway.app
```

### Twilio (Communications)
```
Account SID: AC4036e1260ef9372999cda002f533d9f1
Phone: +15614755454
Recovery Code: VBBKF381HBYAJWSTHV1L93BV
SendGrid API: SG.c2b3d2dc39de750595eab3979d79c0c0
```

## 🚀 Deployment Commands

### 1. Update Environment Variables

#### Vercel
```bash
vercel env add VITE_API_URL production
# Enter: https://concordbroker-railway-production.up.railway.app

vercel env add NEXT_PUBLIC_SUPABASE_URL production
# Enter: https://supabase-concordbroker.supabase.co

vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
# Enter: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Railway
```bash
railway login
railway link 05f5fbf4-f31c-4bdb-9022-3e987dd80fdb

# Set all environment variables
railway variables set DATABASE_URL="postgres://..."
railway variables set SUPABASE_URL="https://supabase-concordbroker.supabase.co"
railway variables set TWILIO_ACCOUNT_SID="AC4036e1260ef9372999cda002f533d9f1"
```

### 2. Deploy Services

#### Deploy Backend to Railway
```bash
cd C:\Users\gsima\Documents\MyProject\ConcordBroker
railway up --service concordapi
```

#### Deploy Frontend to Vercel
```bash
cd apps\web
vercel --prod
```

#### Setup MCP Server
```bash
cd mcp-server-twilio
npm install
npm run build
```

## 📊 Service URLs

### Production
- **Frontend:** https://concordbroker.com
- **API:** https://concordbroker-railway-production.up.railway.app
- **Database:** https://supabase-concordbroker.supabase.co

### Development
- **Frontend:** http://localhost:5173
- **API:** http://localhost:8000
- **Database:** Same as production (use different schema)

## 🔒 Security Checklist

- [x] Supabase RLS policies enabled
- [x] JWT secret configured
- [x] CORS configured for production domains
- [x] Environment variables secured
- [ ] **ACTION REQUIRED:** Update Supabase password in dashboard
- [ ] **ACTION REQUIRED:** Enable 2FA on all accounts
- [ ] **ACTION REQUIRED:** Set up monitoring alerts

## 📱 MCP Server Configuration

Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "concordbroker-twilio": {
      "command": "node",
      "args": ["C:/Users/gsima/Documents/MyProject/ConcordBroker/mcp-server-twilio/dist/index.js"],
      "env": {
        "TWILIO_ACCOUNT_SID": "AC4036e1260ef9372999cda002f533d9f1",
        "TWILIO_AUTH_TOKEN": "035bd39a6462a4ad22aeca3b422fb01e",
        "TWILIO_PHONE_NUMBER": "+15614755454",
        "SUPABASE_URL": "https://supabase-concordbroker.supabase.co",
        "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZ3VscHNzamRseGp2c3RxZmVlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5NTMyMDEsImV4cCI6MjA2MTUyOTIwMX0.5wzCkw9J3ZZMyNZvEge3ypA_41FmLR5mH6OmN0r8EZg"
      }
    }
  }
}
```

## 🧪 Test Connections

### Test Supabase Connection
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://supabase-concordbroker.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZ3VscHNzamRseGp2c3RxZmVlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5NTMyMDEsImV4cCI6MjA2MTUyOTIwMX0.5wzCkw9J3ZZMyNZvEge3ypA_41FmLR5mH6OmN0r8EZg'
)

const { data, error } = await supabase.from('parcels').select('count')
console.log('Connection:', error ? 'Failed' : 'Success')
```

### Test Railway API
```bash
curl https://concordbroker-railway-production.up.railway.app/health
```

### Test Twilio
```bash
curl -X POST https://api.twilio.com/2010-04-01/Accounts/AC4036e1260ef9372999cda002f533d9f1/Messages.json \
  --data-urlencode "From=+15614755454" \
  --data-urlencode "To=+1234567890" \
  --data-urlencode "Body=Test from ConcordBroker" \
  -u AC4036e1260ef9372999cda002f533d9f1:035bd39a6462a4ad22aeca3b422fb01e
```

## ⚠️ IMPORTANT ACTIONS

### 1. Update Supabase Password
1. Go to https://supabase.com/dashboard/project/supabase-concordbroker
2. Settings → Database → Connection string
3. Reset password to: `Concord@Broker2025!`

### 2. Update All Connection Strings
After changing password, update:
- Railway environment variables
- Local .env files
- Any other services using the database

### 3. Verify Deployments
```bash
# Check frontend
curl https://concordbroker.com

# Check API
curl https://concordbroker-railway-production.up.railway.app/health

# Check database
psql $DATABASE_URL -c "SELECT 1"
```

## 📞 Support Contacts

- **Twilio Support**: https://console.twilio.com
- **Supabase Support**: https://supabase.com/dashboard/support
- **Railway Support**: https://railway.app/help
- **Vercel Support**: https://vercel.com/support

---

**Stack Status:** ✅ CONFIGURED AND READY FOR DEPLOYMENT