# 🔐 Credential Rotation Checklist

**⚠️ CRITICAL: Complete ALL items immediately to secure your application**

## Quick Reference Links

| Service | Console URL | Priority |
|---------|------------|----------|
| Supabase | https://supabase.com/dashboard | 🔴 CRITICAL |
| GitHub | https://github.com/settings/tokens | 🔴 CRITICAL |
| OpenAI | https://platform.openai.com/api-keys | 🔴 CRITICAL |
| Anthropic | https://console.anthropic.com/ | 🔴 CRITICAL |
| Google Cloud | https://console.cloud.google.com/ | 🔴 CRITICAL |
| Cloudflare | https://dash.cloudflare.com/profile/api-tokens | 🟡 HIGH |
| Vercel | https://vercel.com/account/tokens | 🟡 HIGH |
| Railway | https://railway.app/account/tokens | 🟡 HIGH |
| Sentry | https://sentry.io/settings/account/api/auth-tokens/ | 🟢 MEDIUM |

---

## Step-by-Step Rotation Guide

### 1️⃣ Database & Supabase (CRITICAL)

- [ ] **Login to Supabase Dashboard**
  - URL: https://supabase.com/dashboard
  - Project: Select your ConcordBroker project

- [ ] **Reset Database Password**
  - Navigate to: Settings → Database
  - Click "Reset Database Password"
  - Generate a strong password (use password manager)
  - Save the new password securely

- [ ] **Rotate Service Role Key**
  - Navigate to: Settings → API
  - Click "Reveal" next to service_role key
  - Click "Roll" to generate new key
  - Copy the new key

- [ ] **Generate New JWT Secret**
  - Navigate to: Settings → API → JWT Settings
  - Click "Generate New Secret"
  - Copy the new secret

- [ ] **Update Connection Strings**
  - Get new connection strings from Settings → Database
  - Note both pooler and direct connection URLs

### 2️⃣ API Keys (CRITICAL)

#### OpenAI
- [ ] Go to https://platform.openai.com/api-keys
- [ ] Find key starting with `sk-proj-FtzmZ88...`
- [ ] Click "Delete" (trash icon)
- [ ] Click "Create new secret key"
- [ ] Name it: "ConcordBroker-Production"
- [ ] Copy and save the new key

#### Anthropic
- [ ] Go to https://console.anthropic.com/settings/keys
- [ ] Find key starting with `sk-ant-api03-t_ORe0...`
- [ ] Click "Revoke"
- [ ] Click "Create Key"
- [ ] Name it: "ConcordBroker-Production"
- [ ] Copy and save the new key

#### Google AI
- [ ] Go to https://console.cloud.google.com/apis/credentials
- [ ] Find key `AIzaSyBZ9Zqs...`
- [ ] Click on it, then "DELETE"
- [ ] Click "CREATE CREDENTIALS" → "API key"
- [ ] Restrict the key to specific APIs
- [ ] Copy and save the new key

### 3️⃣ GitHub Token (CRITICAL)

- [ ] Go to https://github.com/settings/tokens
- [ ] Find token `github_pat_11A7NMXPA0...`
- [ ] Click "Delete" immediately
- [ ] Click "Generate new token (classic)"
- [ ] Name: "ConcordBroker-MCP-Server"
- [ ] Select minimal required scopes:
  - [ ] repo (if needed for private repos)
  - [ ] workflow (if using GitHub Actions)
- [ ] Set expiration to 90 days
- [ ] Copy and save the new token

### 4️⃣ Update Vercel Environment Variables

```bash
# Use the migration script
.\scripts\migrate-env-vars.ps1

# Or manually via CLI
vercel env add DATABASE_URL production
vercel env add SUPABASE_URL production
vercel env add SUPABASE_SERVICE_ROLE_KEY production
vercel env add JWT_SECRET production
vercel env add GITHUB_TOKEN production
vercel env add OPENAI_API_KEY production
vercel env add ANTHROPIC_API_KEY production
```

### 5️⃣ Update Railway Environment Variables

```bash
# Login to Railway
railway login

# Set each variable
railway variables set DATABASE_URL="your_new_database_url"
railway variables set SUPABASE_URL="your_new_supabase_url"
railway variables set SUPABASE_SERVICE_ROLE_KEY="your_new_service_key"
# ... continue for all variables
```

### 6️⃣ Clean Local Environment

```powershell
# Remove all .env files
Remove-Item .env* -Force -Recurse
Remove-Item apps\*\.env* -Force -Recurse

# Verify removal
Get-ChildItem -Path . -Filter .env* -Recurse
```

### 7️⃣ Clean Git History

```bash
# Clone a fresh copy for safety
git clone --mirror https://github.com/yourusername/ConcordBroker.git ConcordBroker-backup

# Remove sensitive files from history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env* apps/*/.env*' \
  --prune-empty --tag-name-filter cat -- --all

# Force push changes
git push --force --all
git push --force --tags
```

---

## Verification Checklist

### Local Environment
- [ ] No .env files in project directory
- [ ] No .env files in subdirectories
- [ ] .gitignore properly configured
- [ ] No hardcoded credentials in code

### Version Control
- [ ] Sensitive files removed from git history
- [ ] No credentials in recent commits
- [ ] GitHub secret scanning enabled
- [ ] Branch protection rules enabled

### Production Environment
- [ ] Vercel env vars updated
- [ ] Railway env vars updated
- [ ] Application still functional
- [ ] No exposed credentials in logs

### Security Measures
- [ ] All old credentials revoked
- [ ] New credentials are unique
- [ ] Credentials stored securely
- [ ] Team notified of changes

---

## Post-Rotation Tasks

1. **Test Everything**
   ```bash
   # Test database connection
   cd apps/api
   python supabase_client.py
   
   # Test API endpoints
   curl http://localhost:8000/health
   
   # Test frontend
   cd apps/web
   npm run dev
   ```

2. **Update Documentation**
   - [ ] Update team wiki/docs
   - [ ] Update deployment guides
   - [ ] Update onboarding docs

3. **Set Up Monitoring**
   - [ ] Enable Supabase audit logs
   - [ ] Set up Sentry error tracking
   - [ ] Configure uptime monitoring

4. **Schedule Regular Rotations**
   - [ ] Set calendar reminder for 90-day rotation
   - [ ] Document rotation procedure
   - [ ] Assign rotation responsibilities

---

## Emergency Response Plan

If you suspect credentials have been compromised:

1. **Immediate (Within 5 minutes)**
   - Rotate affected credentials
   - Check access logs
   - Disable suspicious accounts

2. **Short-term (Within 1 hour)**
   - Audit all recent access
   - Check for unauthorized changes
   - Notify team members

3. **Follow-up (Within 24 hours)**
   - Complete security audit
   - Update security procedures
   - Document incident

---

## Notes

- Keep this checklist updated
- Never skip verification steps
- Always use strong, unique passwords
- Enable 2FA wherever possible
- Use a password manager

---

**Created:** September 5, 2025  
**Status:** 🔴 URGENT - Complete immediately  
**Next Review:** After completion, then quarterly