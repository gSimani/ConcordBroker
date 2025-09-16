#!/bin/bash
# Vercel Deployment Script with HuggingFace Integration
# ConcordBroker - Real Estate Intelligence Platform

echo "🚀 Starting Vercel Deployment for ConcordBroker..."
echo "=============================================="

# Load environment variables
if [ -f ".env.vercel" ]; then
    source .env.vercel
fi

if [ -f ".env.huggingface" ]; then
    source .env.huggingface
fi

# Ensure required variables are set
if [ -z "$VERCEL_API_TOKEN" ]; then
    echo "❌ Error: VERCEL_API_TOKEN not set. Please set it in .env.vercel"
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Set environment variables for Vercel deployment
echo "⚙️ Setting environment variables..."

# Core Application Settings
vercel env add VITE_SUPABASE_URL production < <(echo "$SUPABASE_URL")
vercel env add VITE_SUPABASE_ANON_KEY production < <(echo "$SUPABASE_ANON_KEY")
vercel env add VITE_API_URL production < <(echo "https://concordbroker-railway-production.up.railway.app")

# HuggingFace Integration
echo "🤖 Configuring HuggingFace AI integration..."
vercel env add VITE_HUGGINGFACE_API_TOKEN production < <(echo "$HUGGINGFACE_API_TOKEN")
vercel env add VITE_HF_EMBEDDING_MODEL production < <(echo "$HF_EMBEDDING_MODEL")
vercel env add VITE_HF_TEXT_MODEL production < <(echo "$HF_TEXT_MODEL")
vercel env add VITE_HF_PROPERTY_DESC_MODEL production < <(echo "$HF_PROPERTY_DESC_MODEL")

# Feature Flags
vercel env add VITE_ENABLE_AI_FEATURES production < <(echo "true")
vercel env add VITE_ENABLE_PROPERTY_PROFILES production < <(echo "true")
vercel env add VITE_ENABLE_MARKET_ANALYSIS production < <(echo "true")

# Railway Backend Connection
vercel env add RAILWAY_API_URL production < <(echo "https://concordbroker-railway-production.up.railway.app")
vercel env add RAILWAY_INTERNAL_URL production < <(echo "http://concordbroker.railway.internal")

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
cd apps/web

# Build and deploy
vercel --prod --token $VERCEL_API_TOKEN

# Get deployment URL
DEPLOYMENT_URL=$(vercel ls --token $VERCEL_API_TOKEN | grep "concordbroker" | head -n 1 | awk '{print $2}')

echo ""
echo "✅ Deployment Complete!"
echo "========================"
echo "📍 Production URL: $DEPLOYMENT_URL"
echo "📍 Project Dashboard: https://vercel.com/concord-broker/concordbroker"
echo ""
echo "🤖 HuggingFace AI Features:"
echo "  - Property Description Generation: Enabled"
echo "  - Market Sentiment Analysis: Enabled"
echo "  - Smart Property Search: Enabled"
echo ""
echo "🔗 Integrated Services:"
echo "  - Railway Backend: Connected"
echo "  - Supabase Database: Connected"
echo "  - HuggingFace AI: Connected"
echo ""