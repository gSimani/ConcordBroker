#!/bin/bash
# Railway Orchestrator Quick Deploy Script
# Run this after `railway login` and `railway link`

echo "🚂 Railway Orchestrator Deployment"
echo "===================================="
echo ""

# Check if logged in
if ! railway whoami > /dev/null 2>&1; then
    echo "❌ Not logged in to Railway"
    echo "Please run: railway login"
    exit 1
fi

echo "✅ Railway CLI authenticated"
echo ""

# Set environment variables
echo "📝 Setting environment variables..."
railway variables --set SUPABASE_HOST=aws-1-us-east-1.pooler.supabase.com
railway variables --set SUPABASE_DB=postgres
railway variables --set SUPABASE_USER=postgres.pmispwtdngkcmsrsjwbp
railway variables --set SUPABASE_PASSWORD="West@Boca613!"
railway variables --set SUPABASE_PORT=5432
railway variables --set DB_POOL_MIN=5
railway variables --set DB_POOL_MAX=20
railway variables --set PYTHONUNBUFFERED=1

echo "✅ Environment variables set"
echo ""

# Deploy
echo "🚀 Deploying orchestrator..."
railway up

echo ""
echo "===================================="
echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Check status: railway status"
echo "2. View logs: railway logs"
echo "3. Monitor: railway logs --follow"
echo ""
