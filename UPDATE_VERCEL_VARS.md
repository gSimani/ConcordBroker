# 🚨 URGENT: Update Vercel Environment Variables

## Quick Access Links
- **Vercel Dashboard**: https://vercel.com/admin-westbocaexecs-projects/concord-broker/settings/environment-variables
- **Supabase Dashboard**: https://supabase.com/dashboard

---

## Step 1: Get New Credentials from Services

### 1.1 Supabase (CRITICAL - Do First!)
1. Go to https://supabase.com/dashboard
2. Select your project
3. **Reset Database Password**:
   - Settings → Database → Database Password → Reset Password
   - Copy the new password
4. **Get New API Keys**:
   - Settings → API
   - Copy the `anon` public key
   - Copy the `service_role` secret key
5. **Get Connection String**:
   - Settings → Database → Connection String
   - Copy the connection string (with new password)

### 1.2 GitHub Token
1. Go to https://github.com/settings/tokens
2. **DELETE** the old token `github_pat_11A7NMXPA0...` immediately
3. Click "Generate new token (classic)"
4. Name: "ConcordBroker-Vercel"
5. Select scopes: `repo`, `workflow`
6. Generate and copy token

### 1.3 OpenAI
1. Go to https://platform.openai.com/api-keys
2. Find and DELETE key starting with `sk-proj-FtzmZ88...`
3. Create new secret key
4. Copy the new key

### 1.4 Anthropic
1. Go to https://console.anthropic.com/settings/keys
2. Find and REVOKE key starting with `sk-ant-api03-t_ORe0...`
3. Create new key
4. Copy the new key

---

## Step 2: Add to Vercel via CLI

Run these commands with your new values:

```bash
# Database
vercel env add DATABASE_URL production
# Paste your new Supabase connection string

vercel env add SUPABASE_URL production
# Paste: https://[your-project].supabase.co

vercel env add SUPABASE_ANON_KEY production
# Paste your new anon key

vercel env add SUPABASE_SERVICE_ROLE_KEY production
# Paste your new service role key

# JWT (use the generated ones from .env.new)
vercel env add JWT_SECRET production
# Paste: OfvmCPZbxe+nH7rk8C6DJKYnQwv0CsKV+FbbUF3liM2KZn+11xyYTD81JV9yln5ad9EOfA+MIkef3oD6uNjHZg==

vercel env add SUPABASE_JWT_SECRET production
# Paste: 00C1Zdlm0bFuVvQ83LEDKuPTF3M344YK/PzvkKoYe4LZferU0Z1Gp02M+shYwsInokz0R7Er6QhZ0PL6F4vegQ==

# API Keys
vercel env add GITHUB_TOKEN production
# Paste your new GitHub token

vercel env add OPENAI_API_KEY production
# Paste your new OpenAI key

vercel env add ANTHROPIC_API_KEY production
# Paste your new Anthropic key

# Add to preview and development too
vercel env add DATABASE_URL preview development
vercel env add SUPABASE_URL preview development
# ... repeat for all variables
```

---

## Step 3: Via Vercel Dashboard (Alternative)

1. Go to: https://vercel.com/admin-westbocaexecs-projects/concord-broker/settings/environment-variables
2. For each variable:
   - Click "Add Variable"
   - Enter the key name
   - Paste the new value
   - Select environments: Production, Preview, Development
   - Click "Save"

### Required Variables:
- `DATABASE_URL` - Full Postgres connection string
- `SUPABASE_URL` - https://[project].supabase.co
- `SUPABASE_ANON_KEY` - Public anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (secret)
- `JWT_SECRET` - From .env.new
- `SUPABASE_JWT_SECRET` - From .env.new
- `GITHUB_TOKEN` - New GitHub PAT
- `OPENAI_API_KEY` - New OpenAI key
- `ANTHROPIC_API_KEY` - New Anthropic key
- `NEXT_PUBLIC_SUPABASE_URL` - Same as SUPABASE_URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Same as SUPABASE_ANON_KEY

---

## Step 4: Verify

```bash
# Check that variables are set
vercel env ls

# Deploy to test
vercel --prod

# Check deployment
vercel inspect [deployment-url]
```

---

## Step 5: Clean Up

```bash
# Remove backup folder after confirming everything works
Remove-Item -Recurse -Force env_backup_*

# Ensure no .env files remain
Get-ChildItem -Path . -Filter .env* -Recurse

# Clear git cache
git rm --cached .env* --ignore-unmatch
```

---

## ⚠️ CRITICAL REMINDERS

1. **OLD CREDENTIALS ARE STILL ACTIVE** - They must be revoked in each service
2. **DO NOT SKIP** rotating any credential - all were exposed
3. **ENABLE 2FA** on all service accounts after rotation
4. **TEST EVERYTHING** after updating to ensure services work

---

## Need Help?

- Vercel Support: https://vercel.com/support
- Supabase Support: https://supabase.com/support
- Check deployment logs: `vercel logs`

---

**Time Required**: ~30 minutes
**Priority**: 🔴 CRITICAL - Do immediately