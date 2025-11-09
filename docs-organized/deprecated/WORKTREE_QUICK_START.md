# Git Worktree Quick Start Guide

## 🎯 Goal
Run multiple Claude Code instances simultaneously on different features without conflicts.

## ⚡ 3-Minute Setup

### Step 1: Create a Worktree (30 seconds)

```bash
# Windows
worktree-manager.bat create feature/ui-consolidation

# Linux/Mac
bash worktree-manager.sh create feature/ui-consolidation
```

### Step 2: Configure Port (30 seconds)

```bash
# Navigate to new worktree
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-feature-ui-consolidation

# Auto-configure port (Windows)
.\scripts\setup-worktree-ports.bat

# Auto-configure port (Linux/Mac)
bash scripts/setup-worktree-ports.sh
```

### Step 3: Install & Start (2 minutes)

```bash
# Install dependencies (if needed)
npm install

# Start dev server
cd apps/web
npm run dev
```

**✅ Done!** Server running on http://localhost:5192

### Step 4: Open in Claude Code (30 seconds)

1. Open **new Claude Code window**
2. File → Open Folder
3. Select: `C:\Users\gsima\Documents\MyProject\ConcordBroker-feature-ui-consolidation`

## 🎨 Common Scenarios

### Scenario 1: Work on UI + API simultaneously

```bash
# Create UI worktree (port 5192)
worktree-manager.bat create feature/ui-consolidation
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-feature-ui-consolidation
.\scripts\setup-worktree-ports.bat
npm install
cd apps/web && npm run dev

# Create API worktree (port 5193)
worktree-manager.bat create feature/api-enhancements
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-feature-api-enhancements
.\scripts\setup-worktree-ports.bat
npm install
cd apps/web && npm run dev

# Open 2 Claude Code windows - one for each worktree
```

**Result:**
- Claude #1 working on UI (port 5192)
- Claude #2 working on API (port 5193)
- Zero conflicts!

### Scenario 2: Emergency hotfix during feature work

```bash
# Create hotfix worktree (port 5196)
worktree-manager.bat create hotfix/production
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-hotfix-production
.\scripts\setup-worktree-ports.bat
npm install
cd apps/web && npm run dev

# Open in Claude Code, fix bug, deploy
# Continue feature work in original worktree
```

### Scenario 3: Test experimental changes

```bash
# Create experimental worktree (port 5197)
worktree-manager.bat create experimental/new-features
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-experimental-new-features
.\scripts\setup-worktree-ports.bat
npm install
cd apps/web && npm run dev

# Experiment freely
# If successful: merge to feature branch
# If not: worktree-manager.bat remove experimental/new-features
```

## 📊 Port Reference Card

**Print this and keep near your desk:**

```
┌─────────────────────────────────────────────────┐
│        ConcordBroker Port Assignments           │
├─────────────────────────────────────────────────┤
│ master                            → 5191        │
│ feature/ui-consolidation          → 5192        │
│ feature/api-enhancements          → 5193        │
│ feature/database-optimization     → 5194        │
│ feature/agent-development         → 5195        │
│ hotfix/production                 → 5196        │
│ experimental/new-features         → 5197        │
│ testing/integration               → 5198        │
└─────────────────────────────────────────────────┘
```

## 🛠️ Essential Commands

```bash
# View all worktrees
worktree-manager.bat list

# See port assignments
worktree-manager.bat ports

# Create worktree
worktree-manager.bat create BRANCH_NAME

# Remove worktree
worktree-manager.bat remove BRANCH_NAME

# Auto-configure port (run inside worktree)
.\scripts\setup-worktree-ports.bat
```

## ⚠️ Important Rules

### ✅ DO:
- Use assigned ports for each worktree
- Commit and push changes regularly
- Open separate Claude Code windows for each worktree
- Run `npm install` in each new worktree

### ❌ DON'T:
- Use the same port for multiple worktrees
- Delete worktree folders manually (use `worktree-manager.bat remove`)
- Open same worktree in multiple Claude Code instances
- Forget to commit before removing a worktree

## 🐛 Quick Troubleshooting

### "Port already in use"
```bash
# Find what's using the port
netstat -ano | findstr :5192

# Kill the process or use different port
```

### "Worktree not found"
```bash
# Clean stale references
git worktree prune

# Recreate
worktree-manager.bat create BRANCH_NAME
```

### "Changes not syncing between worktrees"
```bash
# Worktrees are isolated by design!
# Share changes via git:
git add .
git commit -m "message"
git push origin BRANCH_NAME

# In other worktree:
git pull origin BRANCH_NAME
```

## 📚 Full Documentation

For detailed information, see: [GIT_WORKTREE_GUIDE.md](./GIT_WORKTREE_GUIDE.md)

## 🎓 Example Multi-Instance Setup

**Perfect 4-instance setup:**

| Window | Location | Branch | Port | Purpose |
|--------|----------|--------|------|---------|
| 🔵 Claude #1 | ConcordBroker | master | 5191 | Main development |
| 🟢 Claude #2 | ConcordBroker-feature-ui | feature/ui-consolidation | 5192 | UI work |
| 🟡 Claude #3 | ConcordBroker-feature-api | feature/api-enhancements | 5193 | Backend API |
| 🔴 Claude #4 | ConcordBroker-hotfix | hotfix/production | 5196 | Hotfixes |

**Start all 4 dev servers:**
```bash
# Terminal 1
cd C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\web && npm run dev

# Terminal 2
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-feature-ui\apps\web && npm run dev

# Terminal 3
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-feature-api\apps\web && npm run dev

# Terminal 4
cd C:\Users\gsima\Documents\MyProject\ConcordBroker-hotfix\apps\web && npm run dev
```

**Access each instance:**
- http://localhost:5191 (master)
- http://localhost:5192 (UI)
- http://localhost:5193 (API)
- http://localhost:5196 (hotfix)

## 🚀 Pro Tips

1. **Create PowerShell alias:**
   ```powershell
   Set-Alias wt worktree-manager.bat
   # Now use: wt list, wt create, etc.
   ```

2. **Quick worktree navigation:**
   ```powershell
   function gwt($branch) {
       cd "C:\Users\gsima\Documents\MyProject\ConcordBroker-$($branch -replace '/','-')"
   }
   # Usage: gwt feature-ui
   ```

3. **Batch install dependencies:**
   ```bash
   # Update all worktrees after package.json change
   cd C:\Users\gsima\Documents\MyProject
   for /d %d in (ConcordBroker*) do cd %d && npm install && cd ..
   ```

---

**Questions?** See full guide: [GIT_WORKTREE_GUIDE.md](./GIT_WORKTREE_GUIDE.md)
