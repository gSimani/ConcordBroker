# PERMANENT MEMORY: Work Coordination & Single UI Rules

## 🔒 CRITICAL RULES - NEVER VIOLATE

### Rule 1: ONE UI Website - ONE Port - ONE Branch
**PERMANENT RULE:** There is only ONE ConcordBroker website UI.
- **Port:** 5191 (STANDARD - never change)
- **Branch:** feature/ui-consolidation-unified (or main/master)
- **Location:** apps/web/
- **Build Command:** `npm run dev` (from root) or `cd apps/web && npm run dev`

**ENFORCEMENT:**
- Run `npm run port:clean` at start of EVERY session
- Kill ANY dev server not on port 5191
- If multiple ports detected → ERROR → kill all except 5191

---

### Rule 2: Continuous Merge - Commit Immediately
**PERMANENT RULE:** Work merges continuously through git commits.

**WORKFLOW (MANDATORY):**
```bash
# After EVERY feature/fix (no matter how small):
git add <files>
git commit -m "descriptive message"
git push origin <branch>

# NEVER wait to commit multiple features at once
# NEVER have uncommitted changes at end of session
```

**WHY:** Git is the single source of truth. Immediate commits prevent:
- ❌ Work loss
- ❌ Duplicate work across sessions
- ❌ Merge conflicts
- ❌ "Which version is latest?" confusion

---

### Rule 3: Pull Before Starting ANY Work
**PERMANENT RULE:** Always pull latest changes before starting work.

```bash
# At start of EVERY session:
git checkout feature/ui-consolidation-unified  # (or main/master)
git pull --rebase
npm run port:clean
npm run dev
```

**WHY:** Ensures you're working on the latest code, not an old version.

---

### Rule 4: Verify Work Complete Before Ending Session
**PERMANENT RULE:** Run verification before considering work "done."

```bash
# Before ending session or saying "I'm done":
npm run verify:complete

# Must show:
# ✅ All changes committed to git
# ✅ All commits pushed to remote
# ✅ No zombie dev servers running
```

**WHY:** Prevents losing work between sessions.

---

## 🎯 SINGLE UI WEBSITE ARCHITECTURE

### The Only Frontend
```
apps/web/
├── src/
│   ├── pages/
│   │   ├── properties/PropertySearch.tsx    ← Main search page
│   │   └── property/EnhancedPropertyProfile.tsx  ← Property detail page
│   ├── components/
│   │   ├── property/MiniPropertyCard.tsx    ← Property cards
│   │   └── OptimizedSearchBar.tsx          ← Search bar
│   └── hooks/
│       ├── useSalesData.ts                  ← Sales data hook
│       └── useOptimizedPropertySearch.ts    ← Search hook
├── package.json
└── vite.config.ts                           ← Port: 5191 (configured)
```

**CRITICAL:** This is the ONLY UI. There are NO other frontends.

---

## 🔧 AUTOMATED ENFORCEMENT SYSTEMS

### 1. Port Management (ensure-single-dev-server.cjs)
**What it does:**
- Scans ports 5177-5180 for zombie dev servers
- Kills any dev server NOT on port 5191
- Updates .dev-session.json with current status
- Shows port registry of all active services

**When to run:**
- Start of every session: `npm run port:clean`
- Before starting dev server: `npm run dev:clean`
- If experiencing weird behavior: `npm run port:check`

---

### 2. Work Verification (verify-work-completion.cjs)
**What it checks:**
1. ✅ Git status (uncommitted files)
2. ✅ Unpushed commits
3. ✅ Port consistency in test files
4. ✅ Zombie dev servers
5. ✅ Session lock file exists
6. ✅ Correct branch (feature/ui-consolidation-unified)

**When to run:**
- End of work session: `npm run verify:complete`
- Before marking task "complete": `npm run verify:complete`
- Daily standup check: `npm run verify:complete`

---

### 3. Session Lock File (.dev-session.json)
**Auto-generated on every `npm run port:clean`:**
```json
{
  "activePort": 5191,
  "sessionId": "2025-10-10T15-08-50",
  "git": {
    "branch": "feature/ui-consolidation-unified",
    "commit": "fc8fff1",
    "hasUncommittedChanges": false
  },
  "ports": {
    "standard": 5191,
    "active": true,
    "zombies": []
  }
}
```

**Purpose:** AI agents and future sessions can check this file to:
- Know what port to use
- See current git status
- Detect zombie processes
- Resume work from correct state

---

## 📋 DAILY CHECKLIST (MANDATORY)

### Morning - Session Start
```bash
☐ git pull --rebase                    # Get latest work
☐ npm run port:clean                   # Kill zombies, verify port 5191
☐ npm run dev                          # Start dev server
☐ Open browser: http://localhost:5191  # Verify UI loads
```

### During Work - After Each Feature
```bash
☐ Test feature works                   # Manual or automated test
☐ git add <files>                      # Stage changes
☐ git commit -m "description"          # Commit immediately
☐ git push                             # Push immediately
```

### Evening - Session End
```bash
☐ npm run verify:complete              # Check all work saved
☐ git status                           # Should be clean
☐ git log --oneline -5                 # Review commits
☐ Close browser/dev server             # Clean shutdown
```

---

## 🚨 COMMON MISTAKES TO AVOID

### ❌ MISTAKE 1: Multiple Dev Servers
**Problem:** Running `npm run dev` in multiple terminals creates duplicate servers.
**Solution:** Always run `npm run port:clean` first to kill zombies.

### ❌ MISTAKE 2: Uncommitted Work at End of Day
**Problem:** Forgetting to commit means work may be lost.
**Solution:** Run `npm run verify:complete` - it will FAIL if uncommitted work exists.

### ❌ MISTAKE 3: Working on Old Code
**Problem:** Not pulling latest before starting work.
**Solution:** ALWAYS `git pull --rebase` at session start.

### ❌ MISTAKE 4: Testing on Wrong Port
**Problem:** Test files referencing localhost:5177, 5178, etc.
**Solution:** `npm run verify:complete` detects this and shows which files need fixing.

### ❌ MISTAKE 5: Creating New Frontend Projects
**Problem:** Someone creates apps/web2/ or apps/new-ui/
**Solution:** There is ONLY ONE UI: apps/web/. Never create another.

---

## 💾 PERMANENT MEMORY STORAGE

### For AI Agent Memory System
Store these facts in permanent memory:

```json
{
  "project_name": "ConcordBroker",
  "ui_architecture": {
    "frontend_count": 1,
    "frontend_location": "apps/web/",
    "dev_port": 5191,
    "production_url": "https://www.concordbroker.com",
    "framework": "React + Vite + TypeScript"
  },
  "coordination_rules": {
    "standard_port": 5191,
    "standard_branch": "feature/ui-consolidation-unified",
    "commit_frequency": "immediately after each feature",
    "verification_command": "npm run verify:complete",
    "port_cleanup_command": "npm run port:clean"
  },
  "critical_files": {
    "main_search_page": "apps/web/src/pages/properties/PropertySearch.tsx",
    "property_detail_page": "apps/web/src/pages/property/EnhancedPropertyProfile.tsx",
    "mini_card_component": "apps/web/src/components/property/MiniPropertyCard.tsx",
    "vite_config": "apps/web/vite.config.ts"
  },
  "database": {
    "provider": "Supabase",
    "main_table": "florida_parcels",
    "total_properties": 9113150,
    "counties": 67
  },
  "backend_services": {
    "api_port": 8000,
    "api_file": "apps/api/property_live_api.py",
    "framework": "FastAPI",
    "mcp_port": 3001
  },
  "session_workflow": {
    "start": ["git pull --rebase", "npm run port:clean", "npm run dev"],
    "during": ["test", "git add", "git commit", "git push"],
    "end": ["npm run verify:complete", "git status"]
  },
  "zombie_prevention": {
    "automated_killer": "scripts/ensure-single-dev-server.cjs",
    "old_ports_to_kill": [5177, 5178, 5179, 5180],
    "enforcement": "Run on every session start"
  }
}
```

---

## 📊 CRITICAL METRICS TO TRACK

### Session Health Indicators
```yaml
Good Session:
  - zombie_ports: 0
  - active_port: 5191
  - uncommitted_files: 0
  - unpushed_commits: 0
  - test_port_inconsistencies: 0

Bad Session:
  - zombie_ports: > 0          # Run npm run port:clean
  - active_port: != 5191       # WRONG PORT - kill and restart
  - uncommitted_files: > 0     # Commit your work!
  - unpushed_commits: > 0      # Push your work!
  - test_port_inconsistencies: > 0  # Update test files
```

---

## 🎯 FUTURE SESSIONS - WHAT TO REMEMBER

### When Claude Code Starts a New Session
1. **Read .dev-session.json first**
   - Check activePort (should be 5191)
   - Check git.hasUncommittedChanges (should be false)
   - Check ports.zombies (should be empty array)

2. **Run verification immediately**
   - `npm run verify:complete`
   - If it passes → proceed with work
   - If it fails → fix issues before starting new work

3. **Pull latest code**
   - `git pull --rebase`
   - Get all work from previous sessions

4. **Start clean**
   - `npm run port:clean` (kill zombies)
   - `npm run dev` (start on 5191)

### When User Reports "Nothing is Working"
**Checklist:**
1. Is dev server running on port 5191? (`netstat -ano | findstr :5191`)
2. Are there zombie ports? (`npm run port:check`)
3. Is code up to date? (`git status`, `git pull`)
4. Did you commit your changes? (`git log --oneline -5`)
5. Is browser pointing to correct port? (http://localhost:5191)

---

## 🔐 ENFORCEMENT MECHANISMS

### 1. Pre-commit Hook (Future Enhancement)
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Verify only port 5191 in test files
if grep -r "localhost:517[0-8]" tests/ apps/web/tests/; then
  echo "❌ ERROR: Test files reference old ports (5177, 5178)"
  echo "   Update to localhost:5191"
  exit 1
fi
```

### 2. CI/CD Validation (Future Enhancement)
```yaml
# .github/workflows/validate-coordination.yml
name: Validate Work Coordination Rules
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check for zombie port references
        run: |
          if grep -r "localhost:517[0-8]" tests/ apps/web/tests/; then
            echo "ERROR: Old port references found"
            exit 1
          fi
      - name: Verify single UI frontend
        run: |
          if [ $(find apps/ -name "vite.config.ts" | wc -l) -gt 1 ]; then
            echo "ERROR: Multiple UI frontends detected"
            exit 1
          fi
```

### 3. AI Agent Enforcement
**Before starting ANY work:**
```python
# In AI agent initialization
session_lock = read_file('.dev-session.json')
if session_lock['activePort'] != 5191:
    error("WRONG PORT: Expected 5191, found " + session_lock['activePort'])
    run_command('npm run port:clean')

if session_lock['ports']['zombies'].length > 0:
    error("ZOMBIE PORTS DETECTED: " + session_lock['ports']['zombies'])
    run_command('npm run port:clean')
```

---

## 📝 SUMMARY FOR PERMANENT MEMORY

**Store this statement in permanent memory:**

> "ConcordBroker has ONE UI website at apps/web/ running on port 5191. All work merges continuously through immediate git commits. Every session starts with 'git pull && npm run port:clean && npm run dev'. Every session ends with 'npm run verify:complete'. There are NO other frontends. There are NO other development ports. Zombie ports (5177-5180) are killed automatically. The session lock file (.dev-session.json) tracks current state. Verification is mandatory before marking work complete."

**Critical Commands (Always Available):**
- `npm run port:clean` - Kill zombies, show status
- `npm run dev:clean` - Kill zombies + start dev server
- `npm run verify:complete` - Verify work is saved and merged
- `git pull --rebase` - Get latest merged work
- `git add -A && git commit -m "..." && git push` - Merge your work

**Golden Rule:**
"If it's not committed and pushed to git, it doesn't exist. If there's a zombie port, kill it. If it's not on port 5191, it's wrong."

---

**Last Updated:** 2025-10-10T16:00:00Z
**Status:** PERMANENT - DO NOT DELETE
**Importance:** CRITICAL - READ ON EVERY SESSION START
