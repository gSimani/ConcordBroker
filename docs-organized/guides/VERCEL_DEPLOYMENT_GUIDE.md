# Vercel Deployment Guide for ConcordBroker

## Overview
This guide documents the complete Vercel integration and MCP Server setup for the ConcordBroker project.

## Project Configuration

### Vercel Project Details
- **Project ID**: `prj_l6jgk7483iwPCcaYarq7sMgt2m7L`
- **Organization ID**: `team_OIAQ7q0bQTblRPZrnKhU4BGF`
- **Domain**: https://www.concordbroker.com
- **Alternative Domain**: https://concordbroker.com
- **API Domain**: https://api.concordbroker.com
- **Vercel App URL**: https://concord-broker.vercel.app

### API Configuration
- **Vercel API Token**: `t9AK4qQ51TyAc0K0ZLk7tN0H`
- **API Version**: v13 (deployments), v9 (projects), v10 (env vars)

## MCP Server Structure

The MCP (Model Context Protocol) Server has been implemented with the following components:

```
mcp-server/
├── package.json          # Dependencies and scripts
├── vercel-config.json    # Configuration file
├── index.js              # Main MCP server implementation
├── setup-vercel.js       # One-time setup script
├── deploy.js             # Deployment automation
├── monitor.js            # Real-time deployment monitoring
└── test.js               # API connection tests
```

## Environment Variables

The following environment variables have been configured in Vercel:

### Required Variables
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VITE_API_URL` - Backend API URL (Railway)
- `VERCEL_PROJECT_ID` - Vercel project identifier
- `VERCEL_ORG_ID` - Vercel organization identifier

### Feature Flags
- `VITE_ENABLE_ANALYTICS` - Enable analytics (production)
- `VITE_ENABLE_NOTIFICATIONS` - Enable notifications
- `VITE_ENABLE_PROPERTY_PROFILES` - Enable property profiles

## Deployment Process

### 1. Initial Setup (One-time)
```bash
# Navigate to MCP server directory
cd mcp-server

# Install dependencies
npm install

# Run setup script to configure Vercel
node setup-vercel.js
```

### 2. Manual Deployment
```bash
# From the web app directory
cd apps/web

# Deploy to production
vercel --prod

# Deploy to preview
vercel
```

### 3. Automated Deployment via MCP Server
```bash
# From MCP server directory
cd mcp-server

# Deploy to production
node deploy.js production

# Deploy to preview
node deploy.js preview
```

### 4. Monitoring Deployments
```bash
# Start the deployment monitor
cd mcp-server
node monitor.js
```

## Vercel Dashboard Configuration

### Build & Development Settings
- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Install Command**: `npm install`
- **Development Command**: `npm run dev`
- **Root Directory**: `apps/web`

### Domains
1. **www.concordbroker.com** (Primary) - Verified ✅
2. **concordbroker.com** - Verified ✅
3. **api.concordbroker.com** - For API endpoints
4. **concord-broker.vercel.app** - Default Vercel domain

### Git Integration
- **Repository**: ConcordBroker
- **Production Branch**: `main`
- **Auto-deploy**: Enabled for production branch

## API Proxy Configuration

The Vercel configuration routes API calls to the Railway backend:

```json
{
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "https://concordbroker-railway-production.up.railway.app/api/$1"
    }
  ]
}
```

## MCP Server Features

### 1. Deployment Management
- Create new deployments programmatically
- Track deployment status in real-time
- Rollback to previous deployments
- View deployment logs

### 2. Environment Management
- Update environment variables
- Manage secrets securely
- Configure per-environment settings

### 3. Monitoring
- Real-time deployment tracking
- Health checks for deployed apps
- Performance metrics
- Error logging

### 4. Testing
- API connection validation
- Environment variable verification
- Domain configuration checks
- Build settings validation

## Testing the Setup

### 1. Run API Tests
```bash
cd mcp-server
node test.js
```

### 2. Check Deployment Status
```bash
cd mcp-server
node monitor.js
```

### 3. Verify Website
- Production: https://www.concordbroker.com
- Preview: https://concord-broker.vercel.app
- API Health: https://www.concordbroker.com/api/health

## Troubleshooting

### Common Issues

#### 1. 404 Errors on Deployment
- Ensure `dist` folder is built correctly
- Check `vercel.json` routes configuration
- Verify build command in Vercel dashboard

#### 2. Environment Variables Not Loading
- Variables must be prefixed with `VITE_` for Vite
- Redeploy after adding new variables
- Check variable targets (production/preview/development)

#### 3. API Proxy Not Working
- Verify Railway API is running
- Check CORS configuration
- Ensure proper route configuration in `vercel.json`

#### 4. Domain Not Accessible
- DNS propagation can take up to 48 hours
- Verify domain ownership in Vercel dashboard
- Check SSL certificate status

## Additional Vercel Settings to Configure

### In Vercel Dashboard (vercel.com):

1. **Security Headers** (Settings → Security)
   - Enable HSTS
   - Add CSP headers if needed
   - Configure X-Frame-Options

2. **Speed Insights** (Settings → Speed Insights)
   - Enable Web Analytics
   - Set up Real User Monitoring

3. **Functions** (Settings → Functions)
   - Configure region (recommend: iad1 for US East)
   - Set memory limit if using serverless functions

4. **Integrations** (Settings → Integrations)
   - Consider adding:
     - GitHub integration for auto-deploy
     - Slack for deployment notifications
     - Monitoring tools (Datadog, New Relic)

5. **Advanced** (Settings → Advanced)
   - Configure build cache
   - Set deployment protection rules
   - Configure preview deployments

## Next Steps

1. **Set up CI/CD Pipeline**
   - Configure GitHub Actions for automated testing
   - Add pre-deployment checks
   - Set up staging environment

2. **Monitoring & Alerting**
   - Configure uptime monitoring
   - Set up error tracking (Sentry)
   - Add performance monitoring

3. **Optimization**
   - Enable Edge Functions for faster response
   - Configure CDN settings
   - Optimize build output

4. **Security**
   - Add rate limiting
   - Configure WAF rules
   - Set up secret rotation

## Support

- **Vercel Documentation**: https://vercel.com/docs
- **Vercel Status**: https://www.vercel-status.com
- **Support**: https://vercel.com/support

## Commands Reference

```bash
# MCP Server Commands
npm start              # Start MCP server
npm run monitor        # Start deployment monitor
npm run deploy         # Run deployment
npm test              # Run API tests

# Vercel CLI Commands
vercel                # Deploy to preview
vercel --prod         # Deploy to production
vercel env ls         # List environment variables
vercel domains ls     # List domains
vercel logs           # View function logs
```

## Version History

- **v1.0.0** - Initial MCP Server implementation
  - Vercel API integration
  - Deployment automation
  - Environment management
  - Monitoring capabilities

---

Last Updated: September 5, 2025
MCP Server Version: 1.0.0
Vercel API Version: v13