# 🚀 Quick Start: Project Audit Cleanup

**Status**: 🔴 CRITICAL - Credentials exposed in git history
**Time Required**: 1 hour
**Last Updated**: 2025-11-07

---

## 🎯 TL;DR - What You Need to Do

1. ✅ Run cleanup script (5 minutes)
2. 🔴 Rotate credentials (40 minutes) **REQUIRED**
3. ✅ Commit changes (5 minutes)
4. ✅ Verify everything works (10 minutes)

**Start here**: Run the cleanup script, then follow the checklist it generates.

---

## ⚡ Quick Action (Right Now)

### Option 1: Windows (Recommended)
```cmd
cleanup_audit_files.bat
```

### Option 2: Git Bash / WSL
```bash
chmod +x cleanup_audit_files.sh
./cleanup_audit_files.sh
```

**What this does**:
- ✅ Backs up all files before deletion
- ✅ Deletes files with hardcoded credentials
- ✅ Deletes obsolete files
- ✅ Reorganizes keeper files
- ✅ Updates .gitignore
- ✅ Checks if credentials are in git history
- ✅ Creates a checklist if rotation is needed

---

## 🔴 CRITICAL: Credential Rotation (REQUIRED)

**Why**: Two files with credentials were found in git history:
- `apply_security_fixes.py` - Database password: `West@Boca613!`
- `apply_optimizations.py` - Supabase service role key

**Anyone with access to your git repository can see these credentials.**

### Step 1: Rotate Database Password (15 minutes)

1. Go to: https://supabase.com/dashboard
2. Select your project: `pmispwtdngkcmsrsjwbp`
3. Click: **Settings** (left sidebar) → **Database**
4. Click: **"Change password"**
5. Generate a strong password (use password manager)
6. Click: **"Update password"**

**Update password in these locations**:
```
📁 .env.mcp
   DATABASE_URL=postgresql://postgres.[project]:[NEW_PASSWORD]@...

📁 apps/api/.env
   DATABASE_URL=postgresql://postgres.[project]:[NEW_PASSWORD]@...

📁 apps/web/.env
   VITE_SUPABASE_URL=... (check if needed)

🚂 Railway Dashboard
   - Go to your ConcordBroker project
   - Variables tab
   - Update DATABASE_URL

▲ Vercel Dashboard
   - Go to your ConcordBroker project
   - Settings → Environment Variables
   - Update DATABASE_URL (if used)
```

---

### Step 2: Regenerate Service Role Key (15 minutes)

1. Go to: https://supabase.com/dashboard
2. Select your project: `pmispwtdngkcmsrsjwbp`
3. Click: **Settings** → **API**
4. Find: **Service role key** section
5. Click: **"Regenerate key"** (confirm the action)
6. Copy the new key

**Update key in these locations**:
```
📁 .env.mcp
   SUPABASE_SERVICE_ROLE_KEY=eyJ... (new key)

📁 apps/api/.env
   SUPABASE_SERVICE_ROLE_KEY=eyJ... (new key)

🚂 Railway Dashboard
   - Variables tab
   - Update SUPABASE_SERVICE_ROLE_KEY

▲ Vercel Dashboard
   - Settings → Environment Variables
   - Update SUPABASE_SERVICE_ROLE_KEY
```

---

### Step 3: Verify Everything Works (10 minutes)

#### Local Development
```bash
# Start the dev server
npm run dev

# Should start without errors
# Check: http://localhost:5191
```

#### API Health Check
```bash
# Test MCP server
curl http://localhost:3005/health

# Should return: {"status": "healthy"}
```

#### Database Connection
```bash
# Test a simple query
# In your app: Load properties page
# Should see properties loading without 401/403 errors
```

#### Check Console
- Open browser console (F12)
- Look for errors related to Supabase
- Should see NO authentication errors

---

## 📋 Verification Checklist

Use this checklist to ensure everything is complete:

### Cleanup
- [ ] Ran cleanup script (`cleanup_audit_files.bat` or `cleanup_audit_files.sh`)
- [ ] Verified backup folder was created
- [ ] Checked that files were deleted from working directory

### Credential Rotation
- [ ] Changed Supabase database password
- [ ] Regenerated Supabase service role key
- [ ] Updated `.env.mcp` file
- [ ] Updated `apps/api/.env` file
- [ ] Updated `apps/web/.env` file (if needed)
- [ ] Updated Railway environment variables
- [ ] Updated Vercel environment variables

### Testing
- [ ] Local dev server starts: `npm run dev`
- [ ] MCP health check passes: `curl http://localhost:3005/health`
- [ ] Properties load in UI
- [ ] No authentication errors in console
- [ ] Railway deployment works
- [ ] Vercel deployment works

### Git
- [ ] Reviewed git status: `git status`
- [ ] Committed changes with proper message
- [ ] Pushed to remote: `git push origin master`

---

## 🎉 You're Done When...

All these are true:
1. ✅ Cleanup script has run successfully
2. ✅ Database password has been rotated
3. ✅ Service role key has been regenerated
4. ✅ All environment variables updated
5. ✅ Local dev environment works
6. ✅ API health check passes
7. ✅ Properties load in UI
8. ✅ Railway deployment works
9. ✅ Vercel deployment works
10. ✅ Changes committed and pushed

---

## 🆘 Troubleshooting

### "Cleanup script won't run"
**Windows**: Run `cleanup_audit_files.bat`
**Git Bash**: Run `bash cleanup_audit_files.sh`
**WSL**: Run `./cleanup_audit_files.sh`

### "Can't find Supabase dashboard"
Go to: https://supabase.com/dashboard
Login with your account
Select project: `pmispwtdngkcmsrsjwbp`

### "Database password change not working"
1. Make sure you're in the correct project
2. Copy the new password carefully (no extra spaces)
3. Update ALL locations listed above
4. Restart your dev server: `npm run dev`

### "Service role key regeneration not working"
1. Make sure you clicked "Regenerate" (not just viewing)
2. Copy the FULL key (it's very long)
3. Update ALL locations listed above
4. Wait 5 minutes for changes to propagate

### "Properties not loading after changes"
1. Check browser console for errors (F12)
2. Verify Supabase URL is correct
3. Verify service role key is correct
4. Try clearing browser cache
5. Restart dev server

### "Railway deployment failing"
1. Check Railway dashboard logs
2. Verify environment variables are set
3. Wait 5-10 minutes for propagation
4. Try manual redeploy

### "Can't commit changes"
```bash
# Check what's staged
git status

# Add all changes
git add .

# Commit
git commit -m "security: Remove files with hardcoded credentials"

# Push
git push origin master
```

---

## 📞 Still Need Help?

If you're stuck:

1. **Check the backup folder**: All deleted files are backed up
   - `security_cleanup_backup_[timestamp]/`

2. **Read the full report**: `PROJECT_AUDIT_REPORT.md`
   - Detailed analysis of every file
   - Step-by-step instructions
   - Troubleshooting tips

3. **Check the rotation checklist**:
   - `security_cleanup_backup_[timestamp]/ROTATE_CREDENTIALS_CHECKLIST.txt`

4. **Review the cleanup summary**:
   - `security_cleanup_backup_[timestamp]/CLEANUP_SUMMARY.txt`

---

## 📚 Additional Documents

| Document | Purpose |
|----------|---------|
| `PROJECT_AUDIT_REPORT.md` | Complete audit with detailed analysis |
| `cleanup_audit_files.bat` | Windows cleanup script |
| `cleanup_audit_files.sh` | Bash cleanup script |
| `AUDIT_QUICK_START.md` | This guide |

---

## ⏱️ Time Breakdown

| Task | Time |
|------|------|
| Run cleanup script | 5 minutes |
| Rotate database password | 15 minutes |
| Regenerate service role key | 15 minutes |
| Update environment variables | 10 minutes |
| Test everything | 10 minutes |
| Commit and push | 5 minutes |
| **TOTAL** | **~60 minutes** |

---

## 🔒 Security Notes

**Why this is important**:
- Your database password was in git history
- Your service role key was in git history
- Anyone with repo access could see them
- Service role key has FULL database access

**What happens if you don't rotate**:
- ⚠️ Your database could be compromised
- ⚠️ Someone could read all your data
- ⚠️ Someone could modify or delete data
- ⚠️ Your API could be abused

**After rotation**:
- ✅ Old credentials become useless
- ✅ New credentials are secure
- ✅ Only you have access
- ✅ Database is protected

---

## ✅ Final Checklist

Before considering this complete:

```
CLEANUP
[ ] Backup folder created successfully
[ ] Files with credentials deleted
[ ] Obsolete files deleted
[ ] Keeper files reorganized
[ ] .gitignore updated

CREDENTIAL ROTATION
[ ] Database password changed in Supabase
[ ] Service role key regenerated in Supabase
[ ] .env.mcp updated
[ ] apps/api/.env updated
[ ] apps/web/.env updated (if needed)
[ ] Railway variables updated
[ ] Vercel variables updated (if needed)

TESTING
[ ] npm run dev works
[ ] MCP health check passes
[ ] Properties load in UI
[ ] No auth errors in console
[ ] Railway deployment works
[ ] Vercel deployment works

GIT
[ ] git status checked
[ ] Changes committed
[ ] Changes pushed to remote

VERIFICATION
[ ] Read backup folder summary
[ ] Confirmed old credentials no longer work
[ ] Confirmed new credentials work
[ ] All services running normally
```

---

**🎯 Remember**: Don't skip credential rotation! Your security depends on it.

**🚀 Ready?** Run the cleanup script and follow the checklist it generates!

---

*Generated: 2025-11-07 | Priority: CRITICAL | Time: ~1 hour*
