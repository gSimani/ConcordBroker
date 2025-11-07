# Renovate Installation Guide

**Repository:** ConcordBroker
**Status:** Configuration Ready ✅
**App Status:** Not Yet Installed ⏳

---

## Overview

Renovate is a dependency update automation tool that:
- Groups related updates together
- Auto-merges low-risk updates (minor/patch devDependencies)
- Creates a dependency dashboard PR
- Provides more configuration options than Dependabot

**Your Configuration:** Already set up in `.github/renovate.json` ✅

---

## Installation Steps

### Step 1: Visit Renovate App Page

Go to: https://github.com/apps/renovate

Or search "Renovate" in GitHub Marketplace.

### Step 2: Install for Your Account

1. Click **"Install"** or **"Configure"** button
2. Select your GitHub account: **gSimani**
3. Choose repository access:
   - **Option A (Recommended):** Select specific repositories
     - Check: ✅ **ConcordBroker**
   - **Option B:** All repositories (if you want Renovate everywhere)

### Step 3: Approve Permissions

Renovate needs:
- ✅ Read access to code
- ✅ Write access to pull requests
- ✅ Write access to issues (for dashboard)
- ✅ Read access to repository metadata

Click **"Install"** to approve.

### Step 4: Initial Configuration PR

Within 1-2 minutes, Renovate will:
1. Detect your existing config (`.github/renovate.json`)
2. Open a PR titled: **"Configure Renovate"**
3. Show you what it found

**What to do:**
- Review the PR
- Check that it detected your config correctly
- Merge the PR to activate Renovate

### Step 5: Verify Installation

After merging the configuration PR:

1. **Check for Dependency Dashboard**
   - A new issue or PR will be created: "Dependency Dashboard"
   - Shows all available updates

2. **Wait for First PRs**
   - Renovate runs every few hours
   - First PRs typically appear within 1-4 hours
   - Will be grouped according to your config

3. **Verify Auto-Merge Works**
   - PRs for devDependencies (minor/patch) will have automerge in description
   - Check that they get the "automerge" label (you may need to add manually first time)
   - After checks pass → should merge automatically

---

## Your Current Configuration

**File:** `.github/renovate.json`

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    ":semanticCommits",
    ":separateMultipleMajorReleases",
    ":dependencyDashboard"
  ],
  "rangeStrategy": "bump",
  "labels": ["deps", "renovate"],
  "prHourlyLimit": 2,
  "packageRules": [
    {
      "matchManagers": ["npm"],
      "groupName": "frontend deps",
      "matchPaths": ["apps/web/**"]
    },
    {
      "matchManagers": ["pip"],
      "groupName": "python deps",
      "matchPaths": ["scripts/**", "**/*.py"]
    },
    {
      "matchManagers": ["github-actions"],
      "groupName": "actions"
    },
    {
      "matchDepTypes": ["devDependencies"],
      "automerge": true,
      "automergeType": "pr",
      "matchUpdateTypes": ["minor", "patch", "digest"]
    }
  ]
}
```

### What This Does

**Extends:**
- `config:recommended` - Sensible defaults
- `:semanticCommits` - Uses conventional commit format
- `:separateMultipleMajorReleases` - Breaks up major updates
- `:dependencyDashboard` - Creates dashboard issue

**Grouping:**
- **Frontend deps:** All npm packages in `apps/web/`
- **Python deps:** All pip packages in `scripts/` and `*.py` files
- **Actions:** All GitHub Actions updates

**Auto-Merge:**
- ✅ devDependencies only
- ✅ minor updates (e.g., 1.2.0 → 1.3.0)
- ✅ patch updates (e.g., 1.2.3 → 1.2.4)
- ✅ digest updates (e.g., Docker SHA updates)
- ❌ Major updates (require manual review)

**Rate Limiting:**
- Max 2 PRs per hour (prevents spam)

---

## Expected Behavior After Installation

### First Run (1-4 hours after installation)

**You'll see:**
1. **Dependency Dashboard** issue/PR created
   - Lists all dependencies
   - Shows available updates
   - Links to update PRs

2. **Grouped Update PRs:**
   - "Update frontend deps" - All web app dependencies
   - "Update python deps" - All Python dependencies
   - "Update actions" - All GitHub Actions

3. **Auto-Merge Candidates:**
   - PRs with devDependencies (minor/patch)
   - Will say "automerge" in description
   - Add "automerge" label → merges when checks pass

### Ongoing Updates

**Schedule:** Renovate runs every few hours

**What it does:**
1. Checks for new dependency versions
2. Groups updates according to config
3. Opens PRs with detailed changelogs
4. For auto-merge candidates → auto-merges on green checks

**Your dashboard updates:**
- Shows open update PRs
- Shows pending updates (not yet PRed)
- Shows ignored updates
- Shows security advisories

---

## Comparison: Renovate vs Dependabot

### What You Have Now

**Dependabot** (Active):
- ✅ Already running
- ✅ Opens individual PRs per dependency
- ✅ Weekly schedule
- ✅ Good for security updates
- ❌ No auto-merge built-in
- ❌ No grouping
- ❌ Less configuration

**Renovate** (Configured, not installed):
- ⏳ Waiting for app installation
- ✅ Groups related updates
- ✅ Built-in auto-merge
- ✅ Dependency dashboard
- ✅ Highly configurable
- ✅ Runs more frequently
- ✅ Better for monorepos

### Recommendation

**Run both!**
- Keep Dependabot for security alerts (it's native to GitHub)
- Use Renovate for bulk dependency management
- Renovate's auto-merge + grouping saves significant time

If you prefer only one:
- Choose **Renovate** for better automation and fewer PRs
- Keep Dependabot config but disable if Renovate coverage is complete

---

## Managing Both Renovate and Dependabot

### Strategy 1: Both Active (Recommended)

**Dependabot handles:**
- Security updates (comes fast via GitHub Security)
- Individual critical fixes

**Renovate handles:**
- Grouped updates
- Auto-merge for low-risk updates
- Dependency dashboard

**Coordination:**
- Both will detect same updates
- Renovate typically opens first (runs more often)
- If Renovate already has PR open, Dependabot won't duplicate
- If Dependabot opens first, Renovate will detect and skip

### Strategy 2: Renovate Only

**Disable Dependabot:**
```yaml
# In .github/dependabot.yml, comment out or remove:
# version: 2
# updates:
#   ...
```

**Ensure Renovate covers:**
- npm dependencies ✅ (configured)
- pip dependencies ✅ (configured)
- GitHub Actions ✅ (configured)

**Pros:**
- Single source of dependency updates
- Fewer duplicate PRs
- Consistent formatting

**Cons:**
- Lose native GitHub Security integration
- Dependabot alerts are convenient

---

## Troubleshooting

### "Renovate hasn't opened any PRs"

**Possible reasons:**
1. **Too soon** - Wait 1-4 hours after installation
2. **Dependencies already up-to-date** - Check dashboard
3. **Rate limit reached** - prHourlyLimit: 2 (by design)
4. **No updates available** - All dependencies current

**Check:**
```bash
# View Renovate logs in installed app settings
# GitHub → Settings → Applications → Renovate → View logs
```

### "Auto-merge not working for Renovate PRs"

**Fix:**
1. Ensure PR has "automerge" label
   ```bash
   # Add via GitHub UI or CLI
   # (Renovate should add automatically for devDeps)
   ```

2. Verify auto-merge workflow is active
   ```bash
   ls .github/workflows/auto-merge.yml
   # Should exist on main branch
   ```

3. Check that PR checks are passing
   - All 4 required checks must be green

### "Dependency Dashboard not appearing"

**Fix:**
1. Check if issue already exists:
   - Go to: Issues → Search "Dependency Dashboard"

2. Check Renovate config:
   ```json
   "extends": [
     ":dependencyDashboard"  // Must be present
   ]
   ```

3. Re-run Renovate manually:
   - GitHub → Settings → Applications → Renovate
   - Click "Trigger run now"

### "Too many PRs from Renovate"

**Adjust rate limit:**
```json
// In .github/renovate.json
"prHourlyLimit": 1,  // Reduce from 2 to 1
```

**Or add more grouping:**
```json
"packageRules": [
  {
    "groupName": "all non-major dependencies",
    "matchUpdateTypes": ["minor", "patch"]
  }
]
```

---

## Advanced Configuration

### Enable Auto-Merge for More Updates

**Current:** Only devDependencies (minor/patch)

**Add regular dependencies:**
```json
{
  "packageRules": [
    {
      "matchDepTypes": ["devDependencies", "dependencies"],
      "automerge": true,
      "matchUpdateTypes": ["patch"]
    }
  ]
}
```

### Schedule Updates

**Run only on weekdays:**
```json
{
  "schedule": ["after 10pm every weekday", "before 5am every weekday"]
}
```

### Pin Specific Versions

**Never update a dependency:**
```json
{
  "packageRules": [
    {
      "matchPackageNames": ["react"],
      "enabled": false
    }
  ]
}
```

### Notification Settings

**Slack/Discord notifications:**
```json
{
  "onboarding": false,
  "dependencyDashboard": true,
  "notifications": {
    "channel": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  }
}
```

---

## Quick Reference

### Renovate Commands (in PR comments)

```
@renovate rebase        # Rebase the PR
@renovate retry         # Retry failed checks
@renovate recreate      # Close and recreate PR
```

### Useful Links

- **Renovate Docs:** https://docs.renovatebot.com/
- **Your Config:** `.github/renovate.json`
- **GitHub App:** https://github.com/apps/renovate
- **Renovate Dashboard:** https://developer.mend.io/

### Status Check

```bash
# Is Renovate installed?
# Check: https://github.com/settings/installations

# Are PRs being opened?
# Check: https://github.com/gSimani/ConcordBroker/pulls?q=is%3Apr+author%3Aapp%2Frenovate

# Is dashboard present?
# Check: https://github.com/gSimani/ConcordBroker/issues
```

---

## Summary

**Status:** Configuration complete ✅, App installation pending ⏳

**Next Steps:**
1. Install Renovate app: https://github.com/apps/renovate
2. Select ConcordBroker repository
3. Merge configuration PR
4. Wait 1-4 hours for first PRs
5. Add "automerge" label to auto-merge candidates
6. Enjoy automated dependency management! 🎉

**Estimated Time:** 5 minutes to install, 1-4 hours for first PRs

---

*Last Updated: November 6, 2025*
*Maintained by: @gSimani*
