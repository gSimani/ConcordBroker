#!/bin/bash
# Railway Deployment Script for ConcordBroker
# Project: ConcordBroker-Railway (05f5fbf4-f31c-4bdb-9022-3e987dd80fdb)

echo "🚂 Starting Railway Deployment for ConcordBroker..."

# Load Railway environment variables from .env.railway or environment
# NEVER hardcode tokens in scripts!
if [ -f ".env.railway" ]; then
    source .env.railway
fi

# Ensure required variables are set
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "❌ Error: RAILWAY_TOKEN not set. Please set it in .env.railway or as an environment variable."
    exit 1
fi

if [ -z "$RAILWAY_PROJECT_ID" ]; then
    echo "❌ Error: RAILWAY_PROJECT_ID not set. Please set it in .env.railway or as an environment variable."
    exit 1
fi

if [ -z "$RAILWAY_ENVIRONMENT" ]; then
    export RAILWAY_ENVIRONMENT="concordbrokerproduction"
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway using token
echo "🔑 Authenticating with Railway..."
railway login --token $RAILWAY_TOKEN

# Link to the project
echo "🔗 Linking to Railway project..."
railway link $RAILWAY_PROJECT_ID

# Switch to production environment
echo "🌍 Switching to production environment..."
railway environment concordbrokerproduction

# Deploy API service
echo "🚀 Deploying API service..."
railway up --service api

# Deploy worker services
echo "👷 Deploying worker services..."
railway up --service sunbiz-worker
railway up --service bcpa-worker
railway up --service records-worker

# Set environment variables from .env.production
echo "⚙️ Setting environment variables..."
railway variables set \
  SUPABASE_URL=$SUPABASE_URL \
  SUPABASE_KEY=$SUPABASE_KEY \
  SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY \
  DATABASE_URL=$DATABASE_URL \
  JWT_SECRET=$JWT_SECRET

# Check deployment status
echo "✅ Checking deployment status..."
railway status

echo "🎉 Railway deployment complete!"
echo "📍 API URL: https://concordbroker-railway-production.up.railway.app"
echo "📍 Internal: concordbroker.railway.internal"