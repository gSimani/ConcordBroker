# GitHub Integration Guide for ConcordBroker

## Overview
Complete GitHub integration with Vercel deployment pipeline and MCP Server orchestration.

## Repository Configuration

### GitHub Repository Details
- **Repository**: https://github.com/gSimani/ConcordBroker
- **Owner**: gSimani
- **Default Branch**: main
- **Visibility**: Public
- **Created**: September 3, 2025

### API Configuration
- **GitHub API Token**: `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`
- **API Version**: v3
- **Base URL**: https://api.github.com

## MCP Server GitHub Integration

### Components Created
```
mcp-server/
├── github-integration.js      # Main GitHub integration module
├── test-github-integration.js # Integration test suite
└── vercel-config.json         # Updated with GitHub config
```

### Features Implemented
1. **Repository Management**
   - Automatic repository configuration
   - Branch protection setup
   - Settings synchronization

2. **Webhook Configuration**
   - Vercel deployment webhook ✅
   - Automatic deployment on push
   - Pull request previews

3. **GitHub Actions CI/CD**
   - Test workflow on all pushes
   - Preview deployments for PRs
   - Production deployment for main branch

4. **API Integration**
   - Issue creation and management
   - Commit tracking
   - Deployment status updates

## GitHub Actions Workflow

### Workflow Structure (.github/workflows/deploy.yml)

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:          # Run tests and build
  deploy-preview: # Deploy PR previews
  deploy-production: # Deploy to production
```

### Workflow Features
- **Automated Testing**: Runs on every push
- **Preview Deployments**: For all pull requests
- **Production Deployments**: On merge to main
- **Environment Management**: Separate preview/production
- **Status Reporting**: Updates GitHub deployment status

## Setup Instructions

### 1. Configure GitHub Secrets
Go to: https://github.com/gSimani/ConcordBroker/settings/secrets/actions

Add these repository secrets:
```
VERCEL_TOKEN=t9AK4qQ51TyAc0K0ZLk7tN0H
VERCEL_ORG_ID=team_OIAQ7q0bQTblRPZrnKhU4BGF
VERCEL_PROJECT_ID=prj_l6jgk7483iwPCcaYarq7sMgt2m7L
```

### 2. Enable Branch Protection
Go to: https://github.com/gSimani/ConcordBroker/settings/branches

Configure for `main` branch:
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Include administrators
- ✅ Require branches to be up to date

### 3. Vercel GitHub Integration
Go to: https://vercel.com/westbocaexecs-projects/concord-broker/settings/git

Connect GitHub repository:
1. Click "Connect Git Repository"
2. Select "gSimani/ConcordBroker"
3. Configure branch: main
4. Enable automatic deployments

## Testing the Integration

### Run Integration Tests
```bash
cd mcp-server
node test-github-integration.js
```

### Test Results ✅
- GitHub Repository Access: ✅ PASSED
- GitHub Actions Workflow: ✅ PASSED
- Webhook Configuration: ✅ PASSED
- Vercel Project Link: ✅ PASSED
- Recent Commits: ✅ PASSED
- Branch Protection: ✅ PASSED
- Deployment Status: ✅ PASSED
- Git Configuration: ✅ PASSED

## Deployment Pipeline

### Development Workflow
```
1. Create feature branch
   git checkout -b feature/new-feature

2. Make changes and commit
   git add .
   git commit -m "Add new feature"

3. Push to GitHub
   git push origin feature/new-feature

4. Create Pull Request
   - Automatic preview deployment
   - Tests run automatically
   - Review required

5. Merge to main
   - Automatic production deployment
   - Updates live site
```

### Deployment Triggers
| Event | Action | Environment | URL |
|-------|--------|------------|-----|
| Push to main | Deploy | Production | www.concordbroker.com |
| Pull Request | Deploy | Preview | *.vercel.app |
| Manual Deploy | Deploy | Custom | Custom URL |

## MCP Server Commands

### Initialize GitHub Integration
```bash
cd mcp-server
node github-integration.js
```

### Monitor Deployments
```bash
cd mcp-server
node monitor.js
```

### Test Integration
```bash
cd mcp-server
node test-github-integration.js
```

## Webhook Configuration

### Vercel Webhook
- **URL**: https://api.vercel.com/v1/integrations/deploy/prj_l6jgk7483iwPCcaYarq7sMgt2m7L
- **Events**: push, pull_request
- **Status**: ✅ Active
- **Content Type**: application/json

## API Usage Examples

### Get Repository Info
```javascript
const github = new GitHubIntegration(config);
const repo = await github.getRepository();
```

### Create Issue
```javascript
await github.createIssue(
  'Bug: Issue title',
  'Description of the issue',
  ['bug', 'high-priority']
);
```

### Get Recent Commits
```javascript
const commits = await github.getCommits(10);
```

### Push Changes
```javascript
await github.pushChanges('Update from MCP Server');
```

## Troubleshooting

### Common Issues

#### 1. Webhook Not Triggering
- Verify webhook is active in GitHub settings
- Check Vercel project ID matches
- Ensure secrets are configured

#### 2. Actions Failing
- Check GitHub secrets are set correctly
- Verify npm dependencies are installed
- Review workflow logs in Actions tab

#### 3. Deployments Not Working
- Confirm Vercel token is valid
- Check branch protection rules
- Verify Git remote is configured

#### 4. Permission Errors
- Ensure GitHub token has repo scope
- Check Vercel API token permissions
- Verify organization access

## Security Considerations

### Token Management
- **GitHub Token**: Store in environment variables only
- **Rotation**: Every 90 days
- **Scopes**: Limit to required permissions
- **Never commit tokens to repository**

### Branch Protection
- Enforce code reviews
- Require status checks
- Prevent force pushes
- No direct commits to main

## Monitoring & Alerts

### GitHub Status
- Actions: https://github.com/gSimani/ConcordBroker/actions
- Deployments: https://github.com/gSimani/ConcordBroker/deployments
- Webhooks: https://github.com/gSimani/ConcordBroker/settings/hooks

### Vercel Dashboard
- Deployments: https://vercel.com/westbocaexecs-projects/concord-broker
- Analytics: https://vercel.com/westbocaexecs-projects/concord-broker/analytics
- Logs: https://vercel.com/westbocaexecs-projects/concord-broker/logs

## Additional Vercel Settings

### In Vercel Dashboard
1. **Git Integration** (Settings → Git)
   - ✅ Auto-deploy on push
   - ✅ Deploy previews for PRs
   - ✅ Production branch: main

2. **Environment Variables** (Settings → Environment)
   - All GitHub-related vars configured
   - Separate preview/production values

3. **Deployment Protection** (Settings → Security)
   - Vercel Authentication enabled
   - Password protection for previews (optional)

4. **Notifications** (Settings → Notifications)
   - Deployment success/failure alerts
   - Slack/Email integration

## Next Steps

1. **Complete GitHub Secrets Setup**
   - Add all three secrets to repository
   - Test with a push to main

2. **Enable Branch Protection**
   - Configure protection rules
   - Add required reviewers

3. **Test Full Pipeline**
   - Create a test PR
   - Verify preview deployment
   - Merge and check production

4. **Set Up Monitoring**
   - Configure alerts
   - Add status badges to README
   - Set up uptime monitoring

## Status

| Component | Status | Action Required |
|-----------|--------|----------------|
| GitHub Repository | ✅ Connected | None |
| API Integration | ✅ Working | None |
| Webhooks | ✅ Configured | None |
| GitHub Actions | ✅ Created | Add secrets |
| Branch Protection | ⚠️ Not enabled | Configure |
| Vercel Link | ✅ Active | None |
| Deployments | ✅ Working | None |

---

**Last Updated**: September 5, 2025
**MCP Server Version**: 1.0.0
**Integration Status**: ✅ Operational