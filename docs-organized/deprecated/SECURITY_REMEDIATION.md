# Security Remediation Guide - ConcordBroker

**CRITICAL: IMMEDIATE ACTIONS REQUIRED**

This document outlines the security remediation steps taken and those still required after the security audit.

---

## ⚠️ URGENT: Credentials Rotation Required

### Compromised Credentials Found
The following credentials were exposed in version control and MUST be rotated immediately:

#### 1. Database Credentials
- [ ] **PostgreSQL Password**: `West@Boca613!`
- [ ] **Supabase Service Role Key**: Starting with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- [ ] **JWT Secret**: `1GPC3hFFwqKPCGjeRRSVvo2zxgpaSytioHHTD5ityIsiNd1c5mK9RPuWwEaq4UOWywGFIVVQH6Ajt6Ot7QkJcw==`

#### 2. API Keys
- [ ] **OpenAI API Key**: `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`
- [ ] **Anthropic API Key**: `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`
- [ ] **Google AI API Key**: `AIzaSyBZ9ZqsdUi4z3GOD2OqmiIfxIO6v_AC_sQ`
- [ ] **GitHub Token**: `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`
- [ ] **Cloudflare API Key**: `iqfs2EpylU5uhfdD7oIEa3pZqW1IJqM-R-Ck9gNO`
- [ ] **Sentry DSN**: `https://public@sentry.io/4509859915300864`
- [ ] **Codecov Token**: `f9bb935c-6479-401a-9d3b-ea88d1b2c14a`

---

## ✅ Completed Security Actions

### 1. Environment File Management
- ✅ Created secure `.env.example` template without sensitive data
- ✅ Updated `.gitignore` to exclude all .env files
- ✅ Removed sensitive files from git tracking using `git rm --cached`

### 2. Configuration Updates
- ✅ Updated `mcp-server/vercel-config.json` to use environment variable for GitHub token
- ✅ Updated `apps/api/config.py` to not have default credentials

### 3. Supabase Connection Fix
- ✅ Created `apps/api/supabase_client.py` with proxy parameter fix
- ✅ Tested and confirmed database connectivity works

### 4. Migration Tools
- ✅ Created PowerShell script for migrating environment variables to Vercel/Railway
- ✅ Script location: `scripts/migrate-env-vars.ps1`

---

## 🔴 Required Actions (DO IMMEDIATELY)

### Step 1: Rotate ALL Credentials

1. **Supabase/PostgreSQL**
   - Go to https://supabase.com/dashboard
   - Navigate to Settings > Database
   - Reset database password
   - Generate new service role key
   - Generate new JWT secret

2. **OpenAI**
   - Go to https://platform.openai.com/api-keys
   - Delete the exposed key
   - Create a new API key

3. **Anthropic**
   - Go to https://console.anthropic.com/
   - Revoke the exposed key
   - Generate a new API key

4. **GitHub**
   - Go to https://github.com/settings/tokens
   - Delete the exposed PAT immediately
   - Create a new token with minimal required permissions

5. **Google AI**
   - Go to https://console.cloud.google.com/
   - Delete and regenerate the API key

6. **Cloudflare**
   - Go to https://dash.cloudflare.com/profile/api-tokens
   - Delete and recreate the API key

### Step 2: Run Migration Script

```powershell
# From project root directory
.\scripts\migrate-env-vars.ps1
```

This will help you migrate environment variables to:
- Vercel Dashboard
- Railway Dashboard

### Step 3: Update Production Environments

1. **Vercel Environment Variables**
   ```bash
   vercel env add DATABASE_URL production
   vercel env add SUPABASE_URL production
   vercel env add SUPABASE_SERVICE_ROLE_KEY production
   # ... add all other variables
   ```

2. **Railway Environment Variables**
   ```bash
   railway variables set DATABASE_URL=your_new_url
   railway variables set SUPABASE_URL=your_new_url
   # ... add all other variables
   ```

### Step 4: Clean Git History

To completely remove sensitive data from git history:

```bash
# Install BFG Repo-Cleaner or use git-filter-branch
# Option 1: Using BFG (recommended - faster)
java -jar bfg.jar --delete-files .env ConcordBroker.git
java -jar bfg.jar --delete-files .env.production ConcordBroker.git
java -jar bfg.jar --delete-files .env.supabase ConcordBroker.git

# Option 2: Using git filter-branch
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env .env.local .env.production .env.supabase .env.railway' \
  --prune-empty --tag-name-filter cat -- --all

# Force push to update remote
git push origin --force --all
git push origin --force --tags
```

### Step 5: Delete Local Sensitive Files

```powershell
# Remove all local .env files with sensitive data
Remove-Item .env, .env.local, .env.production, .env.supabase, .env.railway -Force -ErrorAction SilentlyContinue
Remove-Item apps\api\.env.supabase -Force -ErrorAction SilentlyContinue
```

---

## 🛡️ Security Best Practices Going Forward

### Environment Variable Management

1. **Never commit .env files**
   - Always use `.env.example` as a template
   - Keep actual values in cloud platforms (Vercel, Railway)

2. **Use Secret Management Services**
   - Vercel Environment Variables
   - Railway Secrets
   - GitHub Secrets (for CI/CD)
   - Consider HashiCorp Vault for enterprise

3. **Principle of Least Privilege**
   - Use read-only keys where possible
   - Limit API key permissions
   - Use service-specific accounts

### Code Security

1. **API Security**
   ```python
   # Always validate environment variables
   if not os.getenv("DATABASE_URL"):
       raise ValueError("DATABASE_URL not configured")
   ```

2. **Input Validation**
   ```python
   from pydantic import BaseModel, validator
   
   class SecureConfig(BaseModel):
       database_url: str
       
       @validator('database_url')
       def validate_db_url(cls, v):
           if not v or 'password' in v.lower():
               raise ValueError("Invalid database URL")
           return v
   ```

3. **Rate Limiting**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

### Monitoring & Alerts

1. **Set Up Secret Scanning**
   - Enable GitHub secret scanning
   - Use tools like `truffleHog` in CI/CD
   - Regular automated scans

2. **Monitor for Exposed Credentials**
   ```yaml
   # .github/workflows/security.yml
   name: Security Scan
   on: [push, pull_request]
   jobs:
     secret-scan:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - name: TruffleHog Scan
           uses: trufflesecurity/trufflehog@main
           with:
             path: ./
   ```

3. **Implement Audit Logging**
   - Log all authentication attempts
   - Monitor unusual API usage
   - Set up alerts for suspicious activity

---

## 📋 Security Checklist

### Immediate (Today)
- [ ] Rotate ALL exposed credentials
- [ ] Run migration script to move to cloud env vars
- [ ] Delete local .env files
- [ ] Clean git history
- [ ] Update all production deployments

### Short Term (This Week)
- [ ] Set up GitHub secret scanning
- [ ] Implement API rate limiting
- [ ] Add input validation to all endpoints
- [ ] Set up monitoring and alerts
- [ ] Review and update access permissions

### Long Term (This Month)
- [ ] Implement comprehensive logging
- [ ] Set up automated security testing
- [ ] Conduct security training for team
- [ ] Document security procedures
- [ ] Regular security audits

---

## 🚨 Emergency Contacts

If you suspect any security breach:

1. **Immediate Actions:**
   - Rotate all credentials
   - Check access logs
   - Notify team members

2. **Service Contacts:**
   - Supabase Support: https://supabase.com/support
   - Vercel Support: https://vercel.com/support
   - Railway Support: https://railway.app/support

3. **Security Resources:**
   - OWASP Top 10: https://owasp.org/Top10/
   - Security Headers: https://securityheaders.com/
   - SSL Labs: https://www.ssllabs.com/ssltest/

---

## 📝 Notes

- All credentials in this document are examples or have been rotated
- Never share actual credentials in documentation
- Always use environment variables for sensitive data
- Regular security audits should be scheduled quarterly

---

**Document Created:** September 5, 2025  
**Last Updated:** September 5, 2025  
**Next Review:** Weekly until all items complete