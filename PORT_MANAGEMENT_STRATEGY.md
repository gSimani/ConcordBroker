# Port Management & Work Coordination Strategy

## 🚨 CURRENT SITUATION (As of October 10, 2025)

### Multiple Dev Servers Running
We currently have **3 development servers** running simultaneously on different ports:

| Port | Process ID | Purpose | Status |
|------|-----------|---------|--------|
| **5177** | 45128 | Legacy/Old dev server | ⚠️ ZOMBIE - Should stop |
| **5178** | 24808 | Previous test server | ⚠️ ZOMBIE - Should stop |
| **5191** | 73068 | **CURRENT ACTIVE** | ✅ KEEP THIS |

### 8+ Background MCP Servers
Multiple MCP server instances are also running, which is normal due to the robust initialization system.

---

## ⚠️ THE PROBLEM

**Duplicate Work Risk:**
- Different ports may be testing different versions of code
- Changes tested on one port might not reflect on another
- Git commits from port 5191 might not be visible on port 5177/5178
- Playwright tests reference different ports (causing confusion)

**Example from This Session:**
- Test file `audit_property_filters.spec.ts` was updated from port 5177 → 5178 → 5191
- Each change could have created test inconsistencies

---

## ✅ SOLUTION: Single Source of Truth Strategy

### 1. **Port Consolidation (IMMEDIATE)**

#### Stop Zombie Ports
```bash
# Kill old dev servers
taskkill /F /PID 45128  # Port 5177
taskkill /F /PID 24808  # Port 5178

# Keep only the current one
# Port 5191 - PID 73068 (KEEP RUNNING)
```

#### Standardize on ONE Port
**Decision: Use Port 5191 as the standard development port**

Update all configuration files:
```typescript
// tests/*.spec.ts - Update ALL test files
const BASE_URL = 'http://localhost:5191';

// playwright.config.ts
baseURL: 'http://localhost:5191',

// apps/web/vite.config.ts
server: {
  port: 5191,
  strictPort: true  // Fail if port unavailable
}
```

---

### 2. **Git-Based Work Coordination**

#### Single Branch Strategy
**Current Branch:** `feature/ui-consolidation-unified`

**Rules:**
1. ✅ **ALWAYS** work on the same git branch
2. ✅ **ALWAYS** commit changes immediately after verification
3. ✅ **NEVER** have uncommitted changes when switching tasks
4. ✅ **ALWAYS** pull latest before starting new work

#### Commit Workflow
```bash
# Before starting ANY new work
git status              # Check for uncommitted changes
git pull --rebase       # Get latest changes

# After completing ANY task
git add <files>
git commit -m "descriptive message"
git push origin feature/ui-consolidation-unified

# Verify it's committed
git log --oneline -1
```

---

### 3. **Automated Port Conflict Detection**

Create a startup script that enforces single-port policy:

```javascript
// scripts/ensure-single-dev-server.js
const { execSync } = require('child_process');
const STANDARD_PORT = 5191;

function checkPort(port) {
  try {
    const result = execSync(`netstat -ano | findstr :${port} | findstr LISTENING`, { encoding: 'utf8' });
    return result.trim().length > 0;
  } catch {
    return false;
  }
}

function killOtherPorts() {
  const ports = [5177, 5178, 5179, 5180];
  ports.forEach(port => {
    if (port === STANDARD_PORT) return;

    if (checkPort(port)) {
      console.log(`⚠️  WARNING: Found dev server on port ${port}`);
      console.log(`   Killing it to prevent conflicts...`);

      try {
        execSync(`FOR /F "tokens=5" %P IN ('netstat -ano ^| findstr :${port} ^| findstr LISTENING') DO taskkill /F /PID %P`, { stdio: 'inherit' });
      } catch (err) {
        console.log(`   Could not kill port ${port} automatically`);
      }
    }
  });
}

console.log(`🔍 Checking for port conflicts...`);
killOtherPorts();

if (checkPort(STANDARD_PORT)) {
  console.log(`✅ Port ${STANDARD_PORT} is already in use (good!)`);
} else {
  console.log(`📡 Starting dev server on port ${STANDARD_PORT}...`);
}
```

**Usage:**
```json
// package.json
{
  "scripts": {
    "dev": "node scripts/ensure-single-dev-server.js && vite --port 5191",
    "dev:clean": "npm run kill-all && npm run dev"
  }
}
```

---

### 4. **Session Coordination System**

#### Session Lock File
Create a lock file that tracks the active development session:

```javascript
// .dev-session.json (add to .gitignore)
{
  "activePort": 5191,
  "sessionId": "2025-10-10-15-30-45",
  "lastCommit": "e124f36",
  "uncommittedFiles": [],
  "workInProgress": "Fixing property search filters"
}
```

**Benefits:**
- Claude Code can check this file before starting work
- Prevents duplicate efforts across sessions
- Tracks what's in progress vs. completed

---

### 5. **Work Verification Checklist**

Before considering ANY work "complete":

```markdown
## Completion Checklist

- [ ] **Tested on STANDARD PORT (5191)**
- [ ] **All changes committed to git**
- [ ] **Playwright tests updated to use port 5191**
- [ ] **Verified with automated test (not manual)**
- [ ] **No zombie processes running on other ports**
- [ ] **Session lock file updated**
- [ ] **Pushed to remote branch**
```

---

### 6. **Merge Strategy for Multiple Workstreams**

If you must work on multiple features simultaneously:

#### Feature Branch Workflow
```bash
# Main development branch
feature/ui-consolidation-unified  (PORT 5191)

# For parallel work (if absolutely necessary)
feature/new-feature-x            (Use DIFFERENT port: 5192)
feature/new-feature-y            (Use DIFFERENT port: 5193)
```

**Rules:**
1. Each feature branch gets a **dedicated port**
2. Port number documented in branch README
3. **Merge back to main development branch frequently**
4. **Never work on same files across branches**

#### Daily Merge Process
```bash
# End of each work session
git checkout feature/ui-consolidation-unified
git pull --rebase
git merge feature/new-feature-x
git push

# This ensures all work is consolidated into main development branch
```

---

### 7. **Port Registry System**

Create a central registry of all active development work:

```yaml
# .active-ports.yml
ports:
  5191:
    branch: feature/ui-consolidation-unified
    purpose: Main property search development
    owner: Claude Code Session 2025-10-10
    status: ACTIVE
    last_updated: 2025-10-10T15:30:00Z

  5192:
    status: AVAILABLE

  5193:
    status: AVAILABLE

  8000:
    purpose: FastAPI Backend
    status: ACTIVE

  3001:
    purpose: MCP Server (Primary)
    status: ACTIVE
```

**Automated Validation:**
```javascript
// scripts/validate-ports.js
// Checks that only registered ports are in use
// Alerts if zombie processes found
// Kills unauthorized ports automatically
```

---

### 8. **AI Agent Memory Integration**

Leverage the Agent Memory System (already implemented):

```python
# Before starting work
memory.get_context("current_development_focus")
# Returns: { "port": 5191, "branch": "feature/ui-consolidation-unified", "last_commit": "e124f36" }

# After completing work
memory.store_context("last_completed_task", {
    "description": "Enabled 9.1M property search",
    "commit": "e124f36",
    "port": 5191,
    "verified": True
})
```

**Benefits:**
- Claude Code sessions can check what previous sessions accomplished
- Prevents re-doing completed work
- Tracks verification status

---

## 🎯 IMMEDIATE ACTION ITEMS

### Phase 1: Clean Up Current Situation (NOW)
```bash
# 1. Kill zombie dev servers
taskkill /F /PID 45128  # Port 5177
taskkill /F /PID 24808  # Port 5178

# 2. Verify only port 5191 is running
netstat -ano | findstr LISTENING | findstr ":51"

# 3. Commit current uncommitted work
git add -A
git commit -m "chore: Consolidate to single development port (5191)"
git push
```

### Phase 2: Standardize Configuration (NEXT 30 MIN)
```bash
# Update all test files to use port 5191
grep -r "localhost:51" tests/ apps/web/tests/
# Manually update each file found

# Update vite config
# Update playwright config

# Commit
git commit -am "config: Standardize all tests to port 5191"
```

### Phase 3: Implement Port Management System (NEXT SESSION)
```bash
# Create port management scripts
node scripts/ensure-single-dev-server.js
node scripts/validate-ports.js
node scripts/kill-zombie-ports.js

# Add to package.json scripts
npm run dev:clean  # Kills zombies + starts clean
```

---

## 📊 VERIFICATION

After implementing this strategy:

### Daily Checks
```bash
# 1. Port audit
netstat -ano | findstr LISTENING | findstr ":51"
# Should only show port 5191

# 2. Git status
git status
# Should be clean (no uncommitted changes)

# 3. Session status
cat .dev-session.json
# Should show current session info

# 4. Test consistency
grep -r "localhost:" tests/ apps/web/tests/ | grep -v "5191"
# Should return NOTHING (all tests use 5191)
```

---

## 🚀 BENEFITS OF THIS APPROACH

1. ✅ **No Duplicate Work** - Single source of truth (port 5191 + git branch)
2. ✅ **No Lost Work** - Everything committed immediately
3. ✅ **Easy Verification** - Tests always run on same port
4. ✅ **Clear Progress** - Git log shows all completed work
5. ✅ **Session Continuity** - AI Agent Memory tracks context
6. ✅ **Fast Debugging** - No "which port has the latest code?" confusion

---

## 📝 CURRENT STATUS SUMMARY

### ✅ COMPLETED (This Session)
- Commit e124f36: Enable 9.1M properties (PORT 5191) ✅
- Commit a7d2e54: Fix dor_uc column error (PORT 5191) ✅
- Commit 13165bb: Enable autocomplete (PORT 5191) ✅
- Commit 194b716: Add sale filters (PORT 5191) ✅

### ⚠️ NEEDS CLEANUP
- Port 5177 (PID 45128) - ZOMBIE - Kill immediately
- Port 5178 (PID 24808) - ZOMBIE - Kill immediately
- Multiple MCP servers - OK (robust init system handles this)

### 📋 TODO NEXT
- [ ] Kill zombie ports
- [ ] Update ALL test files to port 5191
- [ ] Create port management scripts
- [ ] Update session lock file
- [ ] Push all changes to remote

---

**Last Updated:** 2025-10-10T15:45:00Z
**Current Active Port:** 5191
**Current Branch:** feature/ui-consolidation-unified
**Latest Commit:** e124f36
