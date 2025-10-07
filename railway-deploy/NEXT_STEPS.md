# ConcordBroker Railway Deployment - Next Steps

## ✅ Completed

### 1. Meilisearch Service
- ✅ Deployed to Railway: https://meilisearch-concordbrokerproduction.up.railway.app
- ✅ Health check passing
- ✅ Test index completed (1,000 properties in 3 seconds)
- ✅ Full index RUNNING (9,113,150 properties - ETA: 2 hours)

### 2. Indexer Fixed
- ✅ Fixed Railway URL in `apps/api/railway_indexer.py`
- ✅ Tested connection to production Meilisearch
- ✅ Verified search filters working correctly

### 3. API Domain Setup
- ✅ Created `api.concordbroker.com` subdomain in Railway
- ✅ Railway generated domain: `dtd0xw9s.up.railway.app`

---

## 🔧 Action Required

### DNS Configuration Needed
Add this CNAME record to your DNS provider (Cloudflare/Namecheap/etc):

```
Type: CNAME
Name: api
Value: dtd0xw9s.up.railway.app
TTL: Auto/3600
```

**Once DNS propagates (5-60 minutes):**
- API will be available at: https://api.concordbroker.com
- Test with: `curl https://api.concordbroker.com/health`

---

## 📊 Current Status

### Services Running:
1. **Frontend (Vercel)**
   - URL: https://www.concordbroker.com
   - Status: ✅ Live

2. **Meilisearch (Railway)**
   - URL: https://meilisearch-concordbrokerproduction.up.railway.app
   - Status: ✅ Live & Indexing
   - Progress: 9.1M properties being indexed

3. **API (Railway)**
   - Primary URL: https://api.concordbroker.com (DNS setup pending)
   - Direct URL: https://dtd0xw9s.up.railway.app
   - Status: ⏳ Deployed, waiting for DNS

---

## 🚀 Next Steps

### Step 1: Add DNS Record (5 minutes)
1. Log into your DNS provider
2. Go to concordbroker.com DNS settings
3. Add CNAME record:
   - Name: `api`
   - Value: `dtd0xw9s.up.railway.app`
4. Save changes

### Step 2: Wait for DNS Propagation (5-60 minutes)
- Check status: https://dnschecker.org/#CNAME/api.concordbroker.com
- Test API: `curl https://api.concordbroker.com/health`

### Step 3: Update Frontend Environment Variables
Update `apps/web/.env.local`:
```bash
VITE_API_URL=https://api.concordbroker.com
NEXT_PUBLIC_API_URL=https://api.concordbroker.com
VITE_MEILISEARCH_URL=https://meilisearch-concordbrokerproduction.up.railway.app
VITE_MEILISEARCH_KEY=concordbroker-meili-railway-prod-key-2025
```

### Step 4: Deploy Frontend with New URLs
```bash
cd apps/web
npm run build
vercel --prod
```

### Step 5: Verify End-to-End
```bash
# Test Meilisearch
curl -H "Authorization: Bearer concordbroker-meili-railway-prod-key-2025" \
  https://meilisearch-concordbrokerproduction.up.railway.app/stats

# Test API
curl https://api.concordbroker.com/api/dataset/summary

# Test search
curl "https://api.concordbroker.com/api/properties/search?q=miami&limit=5"

# Test frontend
open https://www.concordbroker.com
```

---

## 📈 Monitoring

### Meilisearch Indexing Progress
Check index status:
```bash
curl -H "Authorization: Bearer concordbroker-meili-railway-prod-key-2025" \
  https://meilisearch-concordbrokerproduction.up.railway.app/indexes/florida_properties/stats
```

Expected completion: ~2 hours from start
Current rate: ~250-300 properties/second

### Railway Logs
```bash
cd railway-deploy
railway logs -s ConcordBroker
railway logs -s meilisearch
```

---

## 🐛 Troubleshooting

### API Returns "Application not found"
- **Cause**: DNS not yet propagated or pointing to wrong environment
- **Solution**: Use direct Railway URL: `https://dtd0xw9s.up.railway.app`

### Meilisearch Not Responding
- **Check health**: `curl https://meilisearch-concordbrokerproduction.up.railway.app/health`
- **Check Railway logs**: `railway logs -s meilisearch`

### Frontend Can't Connect to API
- **Verify DNS**: https://dnschecker.org/#CNAME/api.concordbroker.com
- **Check CORS**: API has `allow_origins=["*"]` enabled
- **Verify env vars**: Check `apps/web/.env.local` has correct URLs

---

## 📝 Documentation Updated

- ✅ `railway-deploy/DEPLOYMENT_GUIDE.md` - Full deployment procedures
- ✅ `railway-deploy/DEPLOYMENT_STATUS.txt` - Current deployment status
- ✅ `railway-deploy/MEILISEARCH_URL.txt` - Meilisearch connection info
- ✅ `CLAUDE.md` - Added Railway Deployment Rules section
- ✅ `start-session.bat` - Updated with Railway service URLs

---

## 🎯 Success Criteria

All services operational when:
- [ ] DNS CNAME added for api.concordbroker.com
- [ ] `curl https://api.concordbroker.com/health` returns 200 OK
- [ ] Meilisearch index shows ~9.1M documents
- [ ] Frontend can search properties via api.concordbroker.com
- [ ] Search results return in <100ms

---

**Last Updated**: 2025-10-01 07:06 UTC
**Meilisearch Indexing Started**: 2025-10-01 07:06 UTC
**Estimated Completion**: 2025-10-01 09:06 UTC
