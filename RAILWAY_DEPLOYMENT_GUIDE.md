# 🚂 Railway Deployment Guide - Cloud Orchestrator

**Status:** Ready to Deploy
**Estimated Time:** 15 minutes
**Cost:** ~$5-10/month

---

## 📋 Quick Start

### What You're Deploying:
A cloud-based orchestrator that coordinates with your PC agents through Supabase.

### Files Needed:
- ✅ `railway-orchestrator.py` (cloud orchestrator code)
- ✅ `railway.json` (Railway configuration)  
- ✅ `requirements-railway.txt` (Python dependencies)

---

## 🚀 Deployment Steps

### Step 1: Create Railway Project

1. Go to: https://railway.app/dashboard
2. Click "New Project" → "Empty Project"
3. Name: "concordbroker-orchestrator"

### Step 2: Deploy Files

**Option A - GitHub (Recommended):**
```bash
git add railway-orchestrator.py railway.json requirements-railway.txt
git commit -m "feat: add Railway cloud orchestrator"
git push
```
Then in Railway: New Service → Deploy from GitHub → Select your repo

**Option B - Railway CLI:**
```bash
npm install -g @railway/cli
railway login
railway link
railway up
```

### Step 3: Set Environment Variables

In Railway Dashboard → Service → Variables:

```bash
POSTGRES_URL_NON_POOLING=<from .env.mcp>
SUPABASE_URL=<from .env.mcp>
SUPABASE_SERVICE_ROLE_KEY=<from .env.mcp>
ENVIRONMENT=railway
```

### Step 4: Verify Deployment

**Check Railway Logs:**
Look for:
```
🚂 RAILWAY CLOUD ORCHESTRATOR
✅ Connected to Supabase
✅ Registered as cloud orchestrator
✅ Railway orchestrator operational
```

**Check from PC:**
```bash
python check_agent_activity.py
```

Should show:
```
✅ Railway Cloud Orchestrator
   Status: online
```

---

## ✅ Success Criteria

- ✅ Railway shows "Deployed" status
- ✅ Agent registered in Supabase
- ✅ Heartbeats updating every 30s
- ✅ No errors in logs

---

## 🧪 Test Communication

**PC → Cloud:**
```bash
python << 'EOF'
import os, json
from dotenv import load_dotenv
load_dotenv('.env.mcp')
import psycopg2

conn = psycopg2.connect(os.getenv('POSTGRES_URL_NON_POOLING'))
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO agent_messages (
        from_agent_id, to_agent_id, message_type, payload, priority
    ) VALUES (%s, %s, %s, %s::jsonb, %s);
""", (
    "local-orchestrator-VENGEANCE",
    "railway-orchestrator-cloud",
    "query",
    json.dumps({"test": "PC to Cloud"}),
    5
))

print("✅ Message sent PC → Cloud")
cursor.close()
conn.close()
EOF
```

Check Railway logs for: `📨 MESSAGE FROM local-orchestrator`

---

## 🔧 Troubleshooting

**Build fails:** Ensure requirements-railway.txt exists and contains psycopg2-binary

**Connection fails:** Verify POSTGRES_URL_NON_POOLING is correct

**No heartbeats:** Check Railway service is running and database accessible

---

## 📊 Monitoring

**View logs:**
```bash
railway logs  # CLI
# Or: Dashboard → Service → Logs
```

**Check health:**
```bash
python check_agent_activity.py | grep railway
```

---

## 💰 Cost

- Free tier: $5 credit/month
- Orchestrator: ~$5-10/month
- Monitor usage in Railway dashboard

---

## 🎯 Next Steps

After Railway deployment:
1. Set up GitHub Actions (`.github/workflows/agent-health-check.yml`)
2. Test PC ↔ Cloud ↔ GitHub communication
3. Deploy additional cloud agents
4. Set up monitoring dashboard

---

**🎉 Once deployed: Distributed agent mesh operational!**
