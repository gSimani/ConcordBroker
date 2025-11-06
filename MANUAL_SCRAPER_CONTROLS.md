# 📋 Manual Scraper Controls - User Guide

**Date**: November 6, 2025, 12:30 PM
**Status**: ✅ **OPERATIONAL**
**Location**: `/admin/scrapers`

---

## 🎯 Overview

Manual Scraper Controls provide a user-friendly interface for triggering automated data extraction workflows on-demand from the admin dashboard. This feature allows administrators to:

- Manually trigger scheduled scrapers without waiting for automated runs
- Test scrapers in dry-run mode before production execution
- View real-time status and results
- Access workflow logs directly from the UI

---

## 🚀 Quick Start

### Accessing the Controls

1. Log in to the admin dashboard at `/admin/dashboard`
2. Click the **"Data Scrapers"** card (purple with Database icon)
3. Or navigate directly to `/admin/scrapers`

### Triggering a Scraper

1. **Select Mode**:
   - Toggle **Dry Run Mode** ON for testing (no database changes)
   - Toggle OFF for production run (will write to database)

2. **Choose Scraper**:
   - **Property Data Update**: Florida property data from 67 counties
   - **Sunbiz Data Update**: Florida business entity data from SFTP

3. **Click "Trigger" Button**:
   - Button will show "Triggering..." with spinner
   - Status message appears when complete
   - Success messages auto-clear after 10 seconds
   - Error messages auto-clear after 15 seconds

4. **View Logs**:
   - Click "View Workflow Logs →" link
   - Opens GitHub Actions in new tab
   - See detailed execution logs and artifacts

---

## 📦 Available Scrapers

### 1. Property Data Update

**Description**: Downloads and processes Florida property data from the Florida Revenue Portal.

**Data Sources**:
- 268 files across 67 counties
- Types: NAL (names/addresses), NAP (characteristics), NAV (values), SDF (sales)

**Expected Updates**: 1,000-5,000 records daily

**Duration**: 30-120 minutes

**Schedule**: Daily at 2:00 AM EST (automatic)

**Workflow File**: `daily-property-update.yml`

**Database Tables**:
- `florida_parcels`
- `property_sales_history`

---

### 2. Sunbiz Data Update

**Description**: Connects to Florida Department of State SFTP server to download daily business entity files.

**Data Sources**:
- SFTP: sftp.floridados.gov
- Files: Corporate (c), Events (ce), Fictitious Names (fn)
- Format: Fixed-width text files

**Expected Updates**: 500-2,000 records daily

**Duration**: 15-60 minutes

**Schedule**: Daily at 3:00 AM EST (automatic)

**Workflow File**: `daily-sunbiz-update.yml`

**Database Tables**:
- `sunbiz_corporate`
- `sunbiz_events`
- `sunbiz_fictitious`

---

## ⚙️ Dry Run Mode

### What It Does

- Executes all workflow steps **EXCEPT** database writes
- Perfect for testing and verification
- Safe to run at any time
- No impact on production data

### When to Use

✅ **Use Dry Run Mode When**:
- Testing new workflow changes
- Verifying data sources are available
- Checking for errors without side effects
- Training new administrators
- Troubleshooting issues

❌ **Don't Use Dry Run Mode When**:
- You need to actually update production data
- Forcing an immediate data refresh
- Recovering from failed automated runs

---

## 🔍 Status Messages

### Success (Green)
```
✅ Workflow triggered successfully! (Dry Run Mode)
Last triggered: 2025-11-06, 12:15:30 PM
```

### Error (Red)
```
❌ Failed to trigger workflow: 403 Forbidden
```

### Pending (Blue)
```
🔄 Triggering workflow...
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` | Invalid GitHub API token | Verify `GITHUB_API_TOKEN` in `.env.mcp` |
| `404 Not Found` | Workflow file doesn't exist | Check workflow file name is correct |
| `Network Error` | MCP server not running | Start MCP server: `node claude-code-ultimate-init.cjs` |
| `Timeout` | Request took too long | Check network connection, retry |

---

## 🔐 Security & Permissions

### Required Permissions

**GitHub Personal Access Token** needs:
- `repo` scope (full repository access)
- `workflow` scope (trigger GitHub Actions)

**Admin Authentication** required:
- Must be logged in to admin dashboard
- Session expires after inactivity
- Redirects to `/Gate14` if not authenticated

### API Security

- All requests use MCP server API key
- Requests include `x-api-key` header
- CORS restricted in production
- Rate limiting enabled (120 requests/minute)

---

## 🌐 API Integration

### Endpoint Used

```
POST http://localhost:3005/api/github/workflows/{workflowFile}/trigger
```

### Request Format

```json
{
  "ref": "master",
  "inputs": {
    "dry_run": "true" | "false"
  }
}
```

### Response Format

```json
{
  "success": true,
  "data": {
    "status": "triggered"
  }
}
```

### Environment Variables

```bash
# Frontend (.env or .env.local)
VITE_MCP_SERVER_URL=http://localhost:3005
VITE_MCP_API_KEY=concordbroker-mcp-key-claude

# Backend (.env.mcp)
GITHUB_API_TOKEN=ghp_your_token_here
MCP_API_KEY=concordbroker-mcp-key-claude
```

---

## 📊 Monitoring & Logs

### Real-time Status

- Status updates appear immediately in UI
- Color-coded alerts (green/red/blue)
- Automatic message clearing
- Last triggered timestamp tracking

### GitHub Actions Logs

1. Click "View Workflow Logs →" button
2. See all runs for that workflow
3. Filter by status (success/failure/in progress)
4. Download log artifacts (retained 30 days)

### Email Notifications

**Automated runs** send emails on completion:
- ✅ Success: Subject "✅ Daily Property Update Completed"
- ❌ Failure: Subject "❌ Daily Property Update FAILED"
- Includes: Run number, duration, logs link

**Manual runs** use same notification system.

---

## 🚨 Troubleshooting

### Scraper Won't Trigger

1. **Check MCP Server**:
   ```bash
   curl http://localhost:3005/health
   ```
   Should return: `{"status":"ok"}`

2. **Verify API Key**:
   - Check `.env.mcp` has `GITHUB_API_TOKEN`
   - Verify token has `workflow` scope
   - Test token: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

3. **Check Admin Auth**:
   - Are you logged into admin dashboard?
   - Try logging out and back in
   - Session may have expired

4. **Review Browser Console**:
   - Open DevTools (F12)
   - Check Console tab for errors
   - Look for network request failures

### Workflow Triggers But Nothing Happens

1. **Check GitHub Actions Status**:
   - Visit: https://github.com/gSimani/ConcordBroker/actions
   - Look for new workflow run
   - Check if workflow is queued/running

2. **Verify Secrets Configured**:
   - Visit: https://github.com/gSimani/ConcordBroker/settings/secrets/actions
   - Required secrets:
     - `SUPABASE_URL`
     - `SUPABASE_SERVICE_ROLE_KEY`
     - `SUNBIZ_SFTP_PASSWORD`
     - `EMAIL_USERNAME`
     - `EMAIL_PASSWORD`
     - `ADMIN_EMAIL`

3. **Check Workflow File**:
   ```bash
   cat .github/workflows/daily-property-update.yml
   cat .github/workflows/daily-sunbiz-update.yml
   ```
   Verify they exist and have `workflow_dispatch` trigger.

### Dry Run Mode Doesn't Work

- Dry run mode is passed to the workflow as input
- Workflow script must check `DRY_RUN` environment variable
- Verify orchestrator script respects `--dry-run` flag
- Check logs to confirm database operations were skipped

---

## 📚 Technical Details

### Component Architecture

```
/admin/scrapers
├── scrapers.tsx (Page wrapper)
└── ScraperControls.tsx (Main component)
    ├── Scraper cards (Property, Sunbiz)
    ├── Dry run toggle
    ├── Status alerts
    └── API integration
```

### State Management

```typescript
interface ScraperStatus {
  running: boolean;
  lastRun?: string;
  status?: 'success' | 'error' | 'pending';
  message?: string;
}
```

### Workflow Configuration

```typescript
interface ScraperConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  workflowFile: string;
  color: string;
  bgColor: string;
  schedule: string;
}
```

---

## 🔄 Workflow Execution Flow

### Trigger Sequence

1. User clicks "Trigger" button
2. UI shows "Triggering..." with spinner
3. Frontend sends POST request to MCP server
4. MCP server authenticates with GitHub API
5. GitHub creates new workflow run
6. Workflow queues in GitHub Actions
7. GitHub Actions executes workflow steps
8. UI shows success/error message
9. User can view logs in GitHub Actions

### Dry Run Execution

```
User enables dry run →
Frontend sets inputs.dry_run = 'true' →
Workflow receives DRY_RUN=true env var →
Orchestrator script runs with --dry-run flag →
All steps execute except database writes →
Logs show "DRY RUN" mode
```

---

## 📝 Best Practices

### General Guidelines

1. **Always test with dry run first** when making workflow changes
2. **Check logs immediately** after triggering to verify execution
3. **Don't trigger multiple times** if workflow is already running
4. **Use scheduled runs** for regular updates (manual is for exceptions)
5. **Monitor email notifications** for automated runs

### Production Triggers

- Only trigger production runs during business hours
- Verify data sources are available before triggering
- Check database capacity before large updates
- Coordinate with team to avoid conflicts
- Document any manual interventions

### Troubleshooting Workflow

1. Try dry run first
2. Check logs for specific errors
3. Verify all secrets are configured
4. Test API connectivity
5. Review recent commits for changes
6. Consult documentation for error codes

---

## 📅 Maintenance

### Regular Checks

- **Weekly**: Verify automated runs are completing successfully
- **Monthly**: Review failed workflow runs
- **Quarterly**: Update GitHub API token if expiring
- **Annual**: Audit scraper schedules and data sources

### Updates

When updating scrapers:
1. Test changes in dev environment
2. Deploy workflow changes to master
3. Test with dry run from UI
4. Monitor first production run
5. Update documentation

---

## 🎓 Training

### For New Admins

1. **Watch Automated Run**:
   - Monitor GitHub Actions tomorrow morning
   - Property scraper at 2 AM EST
   - Sunbiz scraper at 3 AM EST

2. **Practice Dry Run**:
   - Log into admin dashboard
   - Navigate to Data Scrapers
   - Enable dry run mode
   - Trigger both scrapers
   - Review logs

3. **Understand Workflows**:
   - Read workflow YAML files
   - Review orchestrator scripts
   - Check database schemas
   - Study error handling

---

## 🆘 Emergency Procedures

### If Scrapers Fail Repeatedly

1. **Immediate Actions**:
   ```bash
   # Check GitHub Actions
   open https://github.com/gSimani/ConcordBroker/actions

   # Test locally
   cd C:\Users\gsima\Documents\MyProject\ConcordBroker
   python scripts/daily_property_update.py --dry-run
   python scripts/daily_sunbiz_update.py --dry-run
   ```

2. **Verify Environment**:
   ```bash
   # Check .env.mcp has all variables
   cat .env.mcp | grep -E "SUPABASE|GITHUB|EMAIL"
   ```

3. **Manual Recovery**:
   ```bash
   # Run upload directly (bypasses orchestrator)
   python upload_remaining_counties.py
   ```

4. **Contact Support**:
   - GitHub Issues: https://github.com/gSimani/ConcordBroker/issues
   - Include: Error logs, screenshot, last successful run

---

## 📊 Success Metrics

### Key Performance Indicators

- **Trigger Success Rate**: >99% (should rarely fail)
- **Workflow Completion Rate**: >95% (some data source issues expected)
- **Average Response Time**: <2 seconds (trigger to confirmation)
- **User Satisfaction**: Intuitive interface, clear feedback

### Monitoring

- Track trigger attempts vs successes
- Monitor workflow duration trends
- Review error patterns
- Analyze usage frequency

---

## 🔗 Related Documentation

- **All Scrapers Operational**: `ALL_SCRAPERS_OPERATIONAL.md`
- **Scraper Fixes Report**: `SCRAPER_FIXES_COMPLETE_REPORT.md`
- **Daily Property Update**: `DAILY_PROPERTY_UPDATE_SYSTEM.md`
- **Sunbiz System**: `SUNBIZ_DAILY_UPDATE_SYSTEM.md`
- **Property Update Agent**: `.claude/agents/property-update-agent.json`
- **Sunbiz Update Agent**: `.claude/agents/sunbiz-update-agent.json`

---

## 📞 Support

### Quick Reference

| Issue | Documentation | Contact |
|-------|--------------|---------|
| Can't trigger workflow | This file, "Troubleshooting" section | Check MCP server, GitHub token |
| Workflow fails | `SCRAPER_FIXES_COMPLETE_REPORT.md` | Check GitHub Actions logs |
| Data not updating | `ALL_SCRAPERS_OPERATIONAL.md` | Verify secrets, check SFTP |
| UI not loading | Check browser console | Verify frontend is running |

### Getting Help

1. Search this documentation
2. Check related markdown files
3. Review GitHub Actions logs
4. Check browser console for errors
5. Test API endpoints manually
6. Create GitHub issue with details

---

*Documentation generated: November 6, 2025, 12:30 PM*
*Feature implemented by: Claude Code + User*
*Status: ✅ Operational and ready for production use*
*Next review: After first manual trigger in production*

---

## 🎉 Feature Complete!

Your manual scraper controls are now:
- ✅ **Integrated** into admin dashboard
- ✅ **Tested** and ready for use
- ✅ **Documented** comprehensively
- ✅ **Monitored** with real-time status
- ✅ **Secure** with API authentication

**Start using it now at** `/admin/scrapers`! 🚀
